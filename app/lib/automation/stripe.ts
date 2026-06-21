/**
 * STRIPE PAYMENT AUTOMATION ENGINE
 *
 * Complete Stripe integration for:
 * - Subscription management (create, update, cancel)
 * - One-time payments (payment intents, charges)
 * - Sponsorship tracking and invoicing
 * - Webhook processing (payment, subscription, invoice events)
 * - Revenue tracking and analytics
 * - Customer management and data sync
 * - Subscription renewal handling
 * - Automatic refund processing
 * - Tax calculation and compliance
 *
 * Environment Requirements:
 * - STRIPE_SECRET_KEY: Stripe API secret key
 * - STRIPE_WEBHOOK_SECRET: Webhook signing secret
 * - STRIPE_PRODUCT_IDs: Comma-separated product IDs (optional)
 * - REVENUE_TRACKING_DB: Database for tracking (mongodb | postgres | sqlite)
 * - WEBHOOK_VERIFY_TIMESTAMP: Enable timestamp verification (default: true)
 * - WEBHOOK_TIMESTAMP_TOLERANCE_SEC: Tolerance in seconds (default: 300)
 */

import Stripe from 'stripe';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface Customer {
  stripeCustomerId: string;
  email: string;
  name?: string;
  metadata?: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface SubscriptionRecord {
  stripeSubscriptionId: string;
  stripeCustomerId: string;
  stripePriceId: string;
  status: 'active' | 'past_due' | 'unpaid' | 'canceled' | 'trialing';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAt?: string;
  canceledAt?: string;
  amount: number;
  currency: string;
  interval: 'month' | 'year';
  metadata?: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface PaymentRecord {
  stripePaymentIntentId: string;
  stripeCustomerId?: string;
  amount: number;
  currency: string;
  status: 'succeeded' | 'processing' | 'requires_action' | 'requires_payment_method' | 'canceled';
  type: 'one_time' | 'subscription' | 'sponsorship';
  metadata?: Record<string, string>;
  createdAt: string;
  succeededAt?: string;
  failedAt?: string;
  refunded: boolean;
  refundAmount?: number;
}

export interface RevenueRecord {
  id: string;
  stripePaymentIntentId?: string;
  stripeSubscriptionId?: string;
  stripeInvoiceId?: string;
  type: 'payment' | 'subscription' | 'refund' | 'sponsorship';
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  customerEmail: string;
  customerName?: string;
  description?: string;
  metadata?: Record<string, string>;
  createdAt: string;
  recordedAt: string;
}

export interface StripeAutomationResult {
  success: boolean;
  data?: unknown;
  error?: string;
  timestamp: string;
}

export interface WebhookEvent {
  id: string;
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
  processed: boolean;
  error?: string;
}

// ============================================================================
// STRIPE CLIENT FACTORY
// ============================================================================

function getStripeClient(): Stripe {
  const stripeKey = process.env.STRIPE_SECRET_KEY;
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY environment variable not configured');
  }
  return new Stripe(stripeKey, {
    apiVersion: '2023-10-16',
    typescript: true,
  });
}

// ============================================================================
// CUSTOMER MANAGEMENT
// ============================================================================

export async function createOrUpdateCustomer(
  email: string,
  name?: string,
  metadata?: Record<string, string>
): Promise<Customer> {
  const stripe = getStripeClient();

  try {
    // Check if customer exists
    const customers = await stripe.customers.list({ email, limit: 1 });

    let customer: Stripe.Customer;

    if (customers.data.length > 0) {
      // Update existing customer
      customer = await stripe.customers.update(customers.data[0].id, {
        name: name || customers.data[0].name || undefined,
        metadata: metadata || customers.data[0].metadata || undefined,
      });
    } else {
      // Create new customer
      customer = await stripe.customers.create({
        email,
        name,
        metadata,
      });
    }

    return {
      stripeCustomerId: customer.id,
      email: customer.email || email,
      name: customer.name || undefined,
      metadata: customer.metadata || undefined,
      createdAt: new Date(customer.created * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to create/update customer: ${message}`);
  }
}

export async function getCustomer(stripeCustomerId: string): Promise<Customer> {
  const stripe = getStripeClient();

  try {
    const customer = await stripe.customers.retrieve(stripeCustomerId);

    return {
      stripeCustomerId: customer.id,
      email: customer.email || '',
      name: customer.name || undefined,
      metadata: customer.metadata || undefined,
      createdAt: new Date(customer.created * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to retrieve customer: ${message}`);
  }
}

// ============================================================================
// SUBSCRIPTION MANAGEMENT
// ============================================================================

export interface CreateSubscriptionParams {
  stripeCustomerId: string;
  stripePriceId: string;
  metadata?: Record<string, string>;
  trialDays?: number;
  autoAdvance?: boolean;
}

export async function createSubscription(
  params: CreateSubscriptionParams
): Promise<SubscriptionRecord> {
  const stripe = getStripeClient();
  const {
    stripeCustomerId,
    stripePriceId,
    metadata,
    trialDays,
    autoAdvance = true,
  } = params;

  try {
    const subscription = await stripe.subscriptions.create({
      customer: stripeCustomerId,
      items: [{ price: stripePriceId }],
      metadata,
      trial_period_days: trialDays,
      automatic_tax: { enabled: true },
      payment_settings: {
        save_default_payment_method: 'on_subscription',
        default_mandate_id: undefined,
      },
      expand: ['latest_invoice', 'pending_setup_intent'],
    });

    const price = subscription.items.data[0].price;
    const priceData = price as Stripe.Price;

    return {
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: subscription.customer as string,
      stripePriceId: stripePriceId,
      status: subscription.status as SubscriptionRecord['status'],
      currentPeriodStart: new Date(subscription.current_period_start * 1000).toISOString(),
      currentPeriodEnd: new Date(subscription.current_period_end * 1000).toISOString(),
      amount: ((priceData.unit_amount || 0) / 100),
      currency: priceData.currency || 'usd',
      interval: (priceData.recurring?.interval || 'month') as 'month' | 'year',
      metadata: subscription.metadata || undefined,
      createdAt: new Date(subscription.created * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to create subscription: ${message}`);
  }
}

export async function updateSubscription(
  subscriptionId: string,
  params: {
    stripePriceId?: string;
    trialDays?: number;
    metadata?: Record<string, string>;
  }
): Promise<SubscriptionRecord> {
  const stripe = getStripeClient();

  try {
    let updateParams: Stripe.SubscriptionUpdateParams = {};

    if (params.metadata) {
      updateParams.metadata = params.metadata;
    }

    if (params.stripePriceId || params.trialDays !== undefined) {
      updateParams.items = [
        {
          id: '', // Will be filled from subscription
          price: params.stripePriceId,
        },
      ];
    }

    const subscription = await stripe.subscriptions.retrieve(subscriptionId);
    if (subscription.items.data[0]) {
      (updateParams.items as Stripe.SubscriptionUpdateParams.Item[])[0].id =
        subscription.items.data[0].id;
    }

    const updated = await stripe.subscriptions.update(subscriptionId, updateParams);

    const price = updated.items.data[0].price;
    const priceData = price as Stripe.Price;

    return {
      stripeSubscriptionId: updated.id,
      stripeCustomerId: updated.customer as string,
      stripePriceId: priceData.id,
      status: updated.status as SubscriptionRecord['status'],
      currentPeriodStart: new Date(updated.current_period_start * 1000).toISOString(),
      currentPeriodEnd: new Date(updated.current_period_end * 1000).toISOString(),
      amount: ((priceData.unit_amount || 0) / 100),
      currency: priceData.currency || 'usd',
      interval: (priceData.recurring?.interval || 'month') as 'month' | 'year',
      metadata: updated.metadata || undefined,
      createdAt: new Date(updated.created * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to update subscription: ${message}`);
  }
}

export async function cancelSubscription(subscriptionId: string): Promise<SubscriptionRecord> {
  const stripe = getStripeClient();

  try {
    const subscription = await stripe.subscriptions.del(subscriptionId);

    const price = subscription.items.data[0].price;
    const priceData = price as Stripe.Price;

    return {
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: subscription.customer as string,
      stripePriceId: priceData.id,
      status: subscription.status as SubscriptionRecord['status'],
      currentPeriodStart: new Date(subscription.current_period_start * 1000).toISOString(),
      currentPeriodEnd: new Date(subscription.current_period_end * 1000).toISOString(),
      canceledAt: new Date().toISOString(),
      amount: ((priceData.unit_amount || 0) / 100),
      currency: priceData.currency || 'usd',
      interval: (priceData.recurring?.interval || 'month') as 'month' | 'year',
      metadata: subscription.metadata || undefined,
      createdAt: new Date(subscription.created * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to cancel subscription: ${message}`);
  }
}

export async function getSubscription(subscriptionId: string): Promise<SubscriptionRecord> {
  const stripe = getStripeClient();

  try {
    const subscription = await stripe.subscriptions.retrieve(subscriptionId);

    const price = subscription.items.data[0].price;
    const priceData = price as Stripe.Price;

    return {
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: subscription.customer as string,
      stripePriceId: priceData.id,
      status: subscription.status as SubscriptionRecord['status'],
      currentPeriodStart: new Date(subscription.current_period_start * 1000).toISOString(),
      currentPeriodEnd: new Date(subscription.current_period_end * 1000).toISOString(),
      cancelAt: subscription.cancel_at ? new Date(subscription.cancel_at * 1000).toISOString() : undefined,
      amount: ((priceData.unit_amount || 0) / 100),
      currency: priceData.currency || 'usd',
      interval: (priceData.recurring?.interval || 'month') as 'month' | 'year',
      metadata: subscription.metadata || undefined,
      createdAt: new Date(subscription.created * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to retrieve subscription: ${message}`);
  }
}

// ============================================================================
// ONE-TIME PAYMENT HANDLING
// ============================================================================

export interface CreatePaymentParams {
  stripeCustomerId?: string;
  amount: number;
  currency?: string;
  type: 'one_time' | 'sponsorship';
  description?: string;
  metadata?: Record<string, string>;
  receiptEmail?: string;
}

export async function createPaymentIntent(params: CreatePaymentParams): Promise<PaymentRecord> {
  const stripe = getStripeClient();
  const {
    stripeCustomerId,
    amount,
    currency = 'usd',
    type,
    description,
    metadata,
    receiptEmail,
  } = params;

  try {
    const paymentIntent = await stripe.paymentIntents.create({
      amount: Math.round(amount * 100), // Convert to cents
      currency,
      customer: stripeCustomerId,
      description,
      metadata: {
        ...metadata,
        type,
      },
      receipt_email: receiptEmail,
      automatic_tax: { enabled: true },
    });

    return {
      stripePaymentIntentId: paymentIntent.id,
      stripeCustomerId: paymentIntent.customer as string | undefined,
      amount,
      currency,
      status: paymentIntent.status as PaymentRecord['status'],
      type,
      metadata: paymentIntent.metadata || undefined,
      createdAt: new Date(paymentIntent.created * 1000).toISOString(),
      refunded: paymentIntent.amount_refunded > 0,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to create payment intent: ${message}`);
  }
}

export async function getPaymentIntent(paymentIntentId: string): Promise<PaymentRecord> {
  const stripe = getStripeClient();

  try {
    const paymentIntent = await stripe.paymentIntents.retrieve(paymentIntentId);

    return {
      stripePaymentIntentId: paymentIntent.id,
      stripeCustomerId: paymentIntent.customer as string | undefined,
      amount: paymentIntent.amount / 100,
      currency: paymentIntent.currency,
      status: paymentIntent.status as PaymentRecord['status'],
      type: (paymentIntent.metadata?.type as 'one_time' | 'sponsorship') || 'one_time',
      metadata: paymentIntent.metadata || undefined,
      createdAt: new Date(paymentIntent.created * 1000).toISOString(),
      succeededAt: paymentIntent.status === 'succeeded'
        ? new Date().toISOString()
        : undefined,
      failedAt: paymentIntent.status === 'requires_payment_method'
        ? new Date().toISOString()
        : undefined,
      refunded: paymentIntent.amount_refunded > 0,
      refundAmount: paymentIntent.amount_refunded / 100,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to retrieve payment intent: ${message}`);
  }
}

// ============================================================================
// REFUND PROCESSING
// ============================================================================

export async function createRefund(
  paymentIntentId: string,
  amount?: number,
  reason?: 'duplicate' | 'fraudulent' | 'requested_by_customer'
): Promise<{ refundId: string; amount: number; status: string }> {
  const stripe = getStripeClient();

  try {
    const refund = await stripe.refunds.create({
      payment_intent: paymentIntentId,
      amount: amount ? Math.round(amount * 100) : undefined,
      reason,
    });

    return {
      refundId: refund.id,
      amount: refund.amount / 100,
      status: refund.status,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to create refund: ${message}`);
  }
}

// ============================================================================
// REVENUE TRACKING
// ============================================================================

export async function recordRevenue(revenue: RevenueRecord): Promise<void> {
  try {
    const dataDir = process.env.REVENUE_DATA_DIR || '.runtime/revenue';

    // Ensure directory exists
    if (!existsSync(dataDir)) {
      await mkdir(dataDir, { recursive: true });
    }

    // Append to revenue log
    const logPath = path.join(dataDir, 'revenue.jsonl');
    const logEntry = JSON.stringify(revenue);
    const existingLog = existsSync(logPath) ? await readFile(logPath, 'utf-8') : '';
    await writeFile(logPath, existingLog + logEntry + '\n');

    // Update daily summary
    const date = new Date(revenue.createdAt).toISOString().split('T')[0];
    const summaryPath = path.join(dataDir, `daily-${date}.json`);

    let summary: Record<string, unknown> = { date, total: 0, count: 0, records: [] };
    if (existsSync(summaryPath)) {
      const content = await readFile(summaryPath, 'utf-8');
      summary = JSON.parse(content);
    }

    (summary.records as RevenueRecord[]) = [
      ...(summary.records as RevenueRecord[]),
      revenue,
    ];
    summary.total = (summary.records as RevenueRecord[]).reduce((sum, r) => sum + r.amount, 0);
    summary.count = (summary.records as RevenueRecord[]).length;

    await writeFile(summaryPath, JSON.stringify(summary, null, 2));
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Failed to record revenue: ${message}`);
  }
}

export async function getRevenueReport(date?: string): Promise<{
  date: string;
  total: number;
  count: number;
  byType: Record<string, number>;
}> {
  try {
    const dataDir = process.env.REVENUE_DATA_DIR || '.runtime/revenue';
    const reportDate = date || new Date().toISOString().split('T')[0];
    const summaryPath = path.join(dataDir, `daily-${reportDate}.json`);

    if (!existsSync(summaryPath)) {
      return { date: reportDate, total: 0, count: 0, byType: {} };
    }

    const content = await readFile(summaryPath, 'utf-8');
    const summary = JSON.parse(content) as {
      records: RevenueRecord[];
      total: number;
      count: number;
    };

    const byType: Record<string, number> = {};
    for (const record of summary.records) {
      byType[record.type] = (byType[record.type] || 0) + record.amount;
    }

    return {
      date: reportDate,
      total: summary.total,
      count: summary.count,
      byType,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Failed to get revenue report: ${message}`);
    return { date: date || new Date().toISOString().split('T')[0], total: 0, count: 0, byType: {} };
  }
}

// ============================================================================
// WEBHOOK VERIFICATION & PROCESSING
// ============================================================================

export function verifyWebhookSignature(
  body: string,
  signature: string,
  secret?: string
): Stripe.Event {
  const stripe = getStripeClient();
  const webhookSecret = secret || process.env.STRIPE_WEBHOOK_SECRET;

  if (!webhookSecret) {
    throw new Error('STRIPE_WEBHOOK_SECRET not configured');
  }

  try {
    const event = stripe.webhooks.constructEvent(body, signature, webhookSecret);

    // Verify timestamp if enabled
    const verifyTimestamp = process.env.WEBHOOK_VERIFY_TIMESTAMP !== 'false';
    if (verifyTimestamp) {
      const tolerance = parseInt(process.env.WEBHOOK_TIMESTAMP_TOLERANCE_SEC || '300', 10);
      const now = Math.floor(Date.now() / 1000);
      const eventTime = event.created;

      if (Math.abs(now - eventTime) > tolerance) {
        throw new Error(
          `Webhook timestamp too old: ${now - eventTime} seconds. Tolerance: ${tolerance}s`
        );
      }
    }

    return event;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Webhook verification failed: ${message}`);
  }
}

export async function handlePaymentSucceeded(
  paymentIntent: Stripe.PaymentIntent
): Promise<RevenueRecord> {
  const revenue: RevenueRecord = {
    id: `revenue-${Date.now()}`,
    stripePaymentIntentId: paymentIntent.id,
    type: (paymentIntent.metadata?.type as 'one_time' | 'sponsorship') || 'payment',
    amount: paymentIntent.amount / 100,
    currency: paymentIntent.currency,
    status: 'completed',
    customerEmail: paymentIntent.receipt_email || paymentIntent.customer?.toString() || 'unknown',
    description: paymentIntent.description || undefined,
    metadata: paymentIntent.metadata || undefined,
    createdAt: new Date(paymentIntent.created * 1000).toISOString(),
    recordedAt: new Date().toISOString(),
  };

  await recordRevenue(revenue);
  return revenue;
}

export async function handleInvoicePaid(
  invoice: Stripe.Invoice
): Promise<RevenueRecord> {
  const revenue: RevenueRecord = {
    id: `revenue-${Date.now()}`,
    stripeInvoiceId: invoice.id,
    stripeSubscriptionId: invoice.subscription?.toString(),
    type: 'subscription',
    amount: (invoice.amount_paid || 0) / 100,
    currency: invoice.currency,
    status: 'completed',
    customerEmail: invoice.customer_email || '',
    metadata: invoice.metadata || undefined,
    createdAt: new Date(invoice.created * 1000).toISOString(),
    recordedAt: new Date().toISOString(),
  };

  await recordRevenue(revenue);
  return revenue;
}

export async function handleChargeRefunded(
  charge: Stripe.Charge
): Promise<RevenueRecord> {
  const revenue: RevenueRecord = {
    id: `revenue-${Date.now()}`,
    type: 'refund',
    amount: (charge.amount_refunded || 0) / 100,
    currency: charge.currency,
    status: 'refunded',
    customerEmail: charge.receipt_email || 'unknown',
    metadata: charge.metadata || undefined,
    createdAt: new Date(charge.created * 1000).toISOString(),
    recordedAt: new Date().toISOString(),
  };

  await recordRevenue(revenue);
  return revenue;
}

// ============================================================================
// SUBSCRIPTION RENEWAL HANDLING
// ============================================================================

export async function handleSubscriptionRenewal(
  subscription: Stripe.Subscription
): Promise<StripeAutomationResult> {
  try {
    // Get customer info
    const customer = await getCustomer(subscription.customer as string);

    // Record revenue from the latest invoice
    if (subscription.latest_invoice) {
      const invoice = subscription.latest_invoice as Stripe.Invoice;
      const revenue: RevenueRecord = {
        id: `revenue-${Date.now()}`,
        stripeInvoiceId: invoice.id,
        stripeSubscriptionId: subscription.id,
        type: 'subscription',
        amount: (invoice.amount_paid || 0) / 100,
        currency: invoice.currency,
        status: invoice.paid ? 'completed' : 'pending',
        customerEmail: customer.email,
        customerName: customer.name,
        metadata: {
          ...subscription.metadata,
          invoiceId: invoice.id,
        },
        createdAt: new Date(subscription.current_period_start * 1000).toISOString(),
        recordedAt: new Date().toISOString(),
      };

      await recordRevenue(revenue);
    }

    return {
      success: true,
      data: {
        subscriptionId: subscription.id,
        customerId: subscription.customer,
        status: subscription.status,
      },
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return {
      success: false,
      error: message,
      timestamp: new Date().toISOString(),
    };
  }
}

// ============================================================================
// BATCH OPERATIONS
// ============================================================================

export async function listSubscriptions(
  stripeCustomerId?: string,
  limit = 10
): Promise<SubscriptionRecord[]> {
  const stripe = getStripeClient();

  try {
    const subscriptions = await stripe.subscriptions.list({
      customer: stripeCustomerId,
      limit,
      expand: ['data.default_payment_method'],
    });

    return subscriptions.data.map((sub) => {
      const price = sub.items.data[0].price as Stripe.Price;
      return {
        stripeSubscriptionId: sub.id,
        stripeCustomerId: sub.customer as string,
        stripePriceId: price.id,
        status: sub.status as SubscriptionRecord['status'],
        currentPeriodStart: new Date(sub.current_period_start * 1000).toISOString(),
        currentPeriodEnd: new Date(sub.current_period_end * 1000).toISOString(),
        amount: ((price.unit_amount || 0) / 100),
        currency: price.currency,
        interval: (price.recurring?.interval || 'month') as 'month' | 'year',
        metadata: sub.metadata || undefined,
        createdAt: new Date(sub.created * 1000).toISOString(),
        updatedAt: new Date().toISOString(),
      };
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to list subscriptions: ${message}`);
  }
}

export async function listPaymentIntents(
  limit = 10
): Promise<PaymentRecord[]> {
  const stripe = getStripeClient();

  try {
    const intents = await stripe.paymentIntents.list({ limit });

    return intents.data.map((intent) => ({
      stripePaymentIntentId: intent.id,
      stripeCustomerId: intent.customer as string | undefined,
      amount: intent.amount / 100,
      currency: intent.currency,
      status: intent.status as PaymentRecord['status'],
      type: (intent.metadata?.type as 'one_time' | 'sponsorship') || 'one_time',
      metadata: intent.metadata || undefined,
      createdAt: new Date(intent.created * 1000).toISOString(),
      refunded: intent.amount_refunded > 0,
      refundAmount: intent.amount_refunded / 100,
    }));
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to list payment intents: ${message}`);
  }
}

// ============================================================================
// ANALYTICS & REPORTING
// ============================================================================

export async function getMonthlyRecurringRevenue(): Promise<number> {
  const stripe = getStripeClient();

  try {
    const subscriptions = await stripe.subscriptions.list({
      status: 'active',
      limit: 100,
    });

    let mrr = 0;
    for (const sub of subscriptions.data) {
      const price = sub.items.data[0].price as Stripe.Price;
      if (price.recurring?.interval === 'month') {
        mrr += (price.unit_amount || 0) / 100;
      } else if (price.recurring?.interval === 'year') {
        mrr += ((price.unit_amount || 0) / 100) / 12;
      }
    }

    return mrr;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Failed to calculate MRR: ${message}`);
    return 0;
  }
}

export async function getChurnRate(daysBack = 30): Promise<number> {
  const stripe = getStripeClient();

  try {
    const cutoffTime = Math.floor((Date.now() - daysBack * 24 * 60 * 60 * 1000) / 1000);

    const canceledSubs = await stripe.subscriptions.list({
      status: 'canceled',
      limit: 100,
    });

    const recentlyCanceled = canceledSubs.data.filter(
      (sub) => (sub.canceled_at || 0) > cutoffTime
    ).length;

    const activeSubs = await stripe.subscriptions.list({
      status: 'active',
      limit: 100,
    });

    const activeCount = activeSubs.data.length;
    const churnRate = activeCount > 0 ? (recentlyCanceled / activeCount) * 100 : 0;

    return churnRate;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Failed to calculate churn rate: ${message}`);
    return 0;
  }
}

export async function getCustomerLifetimeValue(stripeCustomerId: string): Promise<number> {
  const stripe = getStripeClient();

  try {
    // Get all invoices for the customer
    const invoices = await stripe.invoices.list({
      customer: stripeCustomerId,
      limit: 100,
    });

    let totalAmount = 0;
    for (const invoice of invoices.data) {
      if (invoice.paid) {
        totalAmount += (invoice.amount_paid || 0) / 100;
      }
    }

    // Add one-time payments
    const paymentIntents = await stripe.paymentIntents.list({
      customer: stripeCustomerId,
      limit: 100,
    });

    for (const intent of paymentIntents.data) {
      if (intent.status === 'succeeded') {
        totalAmount += intent.amount / 100;
      }
    }

    return totalAmount;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Failed to calculate customer LTV: ${message}`);
    return 0;
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export { Stripe };

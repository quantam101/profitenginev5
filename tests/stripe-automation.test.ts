/**
 * STRIPE AUTOMATION TEST SUITE
 *
 * Comprehensive tests for Stripe payment automation:
 * - Customer management
 * - Subscription lifecycle
 * - Payment handling
 * - Revenue tracking
 * - Webhook processing
 * - Analytics functions
 *
 * Note: These tests mock Stripe API calls. In production, use test mode
 * Stripe keys and test webhook secrets.
 */

import {
  createOrUpdateCustomer,
  getCustomer,
  createSubscription,
  updateSubscription,
  cancelSubscription,
  getSubscription,
  createPaymentIntent,
  getPaymentIntent,
  createRefund,
  recordRevenue,
  getRevenueReport,
  listSubscriptions,
  listPaymentIntents,
  getMonthlyRecurringRevenue,
  getChurnRate,
  getCustomerLifetimeValue,
  verifyWebhookSignature,
  handlePaymentSucceeded,
  handleInvoicePaid,
  handleChargeRefunded,
} from '@/lib/automation/stripe';
import Stripe from 'stripe';

describe('Stripe Payment Automation', () => {
  // Mock environment variables
  beforeEach(() => {
    process.env.STRIPE_SECRET_KEY = 'sk_test_mock123';
    process.env.STRIPE_WEBHOOK_SECRET = 'whsec_test_mock123';
    process.env.REVENUE_DATA_DIR = '.runtime/revenue';
  });

  describe('Customer Management', () => {
    test('should create a new customer', async () => {
      const result = await createOrUpdateCustomer(
        'john@example.com',
        'John Doe',
        { tier: 'premium' }
      );

      expect(result).toHaveProperty('stripeCustomerId');
      expect(result.email).toBe('john@example.com');
      expect(result.name).toBe('John Doe');
      expect(result.metadata?.tier).toBe('premium');
    });

    test('should update existing customer', async () => {
      // Create customer first
      const created = await createOrUpdateCustomer(
        'jane@example.com',
        'Jane Doe'
      );

      // Update the same customer
      const updated = await createOrUpdateCustomer(
        'jane@example.com',
        'Jane Smith',
        { tier: 'enterprise' }
      );

      expect(updated.stripeCustomerId).toBe(created.stripeCustomerId);
      expect(updated.name).toBe('Jane Smith');
    });

    test('should retrieve customer by ID', async () => {
      const created = await createOrUpdateCustomer('test@example.com', 'Test User');
      const retrieved = await getCustomer(created.stripeCustomerId);

      expect(retrieved.email).toBe('test@example.com');
    });
  });

  describe('Subscription Management', () => {
    test('should create a subscription', async () => {
      const customer = await createOrUpdateCustomer('sub@example.com', 'Sub Customer');

      const subscription = await createSubscription({
        stripeCustomerId: customer.stripeCustomerId,
        stripePriceId: 'price_monthly_pro',
        trialDays: 14,
        metadata: { plan: 'professional' }
      });

      expect(subscription).toHaveProperty('stripeSubscriptionId');
      expect(subscription.status).toBe('trialing');
      expect(subscription.amount).toBeGreaterThan(0);
      expect(subscription.interval).toBe('month');
    });

    test('should update subscription', async () => {
      const customer = await createOrUpdateCustomer('update@example.com', 'Update User');
      const subscription = await createSubscription({
        stripeCustomerId: customer.stripeCustomerId,
        stripePriceId: 'price_monthly_pro',
      });

      const updated = await updateSubscription(
        subscription.stripeSubscriptionId,
        { stripePriceId: 'price_monthly_enterprise' }
      );

      expect(updated.stripeSubscriptionId).toBe(subscription.stripeSubscriptionId);
    });

    test('should get subscription details', async () => {
      const customer = await createOrUpdateCustomer('get@example.com', 'Get User');
      const created = await createSubscription({
        stripeCustomerId: customer.stripeCustomerId,
        stripePriceId: 'price_monthly_pro',
      });

      const retrieved = await getSubscription(created.stripeSubscriptionId);
      expect(retrieved.stripeSubscriptionId).toBe(created.stripeSubscriptionId);
      expect(retrieved.status).toBeDefined();
    });

    test('should cancel subscription', async () => {
      const customer = await createOrUpdateCustomer('cancel@example.com', 'Cancel User');
      const subscription = await createSubscription({
        stripeCustomerId: customer.stripeCustomerId,
        stripePriceId: 'price_monthly_pro',
      });

      const canceled = await cancelSubscription(subscription.stripeSubscriptionId);
      expect(canceled.status).toBe('canceled');
    });

    test('should list customer subscriptions', async () => {
      const customer = await createOrUpdateCustomer('list@example.com', 'List User');

      // Create two subscriptions
      await createSubscription({
        stripeCustomerId: customer.stripeCustomerId,
        stripePriceId: 'price_monthly_pro',
      });

      const subscriptions = await listSubscriptions(customer.stripeCustomerId, 10);
      expect(Array.isArray(subscriptions)).toBe(true);
      expect(subscriptions.length).toBeGreaterThan(0);
    });
  });

  describe('Payment Handling', () => {
    test('should create one-time payment intent', async () => {
      const customer = await createOrUpdateCustomer('payment@example.com', 'Payment User');

      const payment = await createPaymentIntent({
        stripeCustomerId: customer.stripeCustomerId,
        amount: 99.99,
        currency: 'usd',
        type: 'one_time',
        description: 'Premium Feature Pack',
        receiptEmail: customer.email
      });

      expect(payment).toHaveProperty('stripePaymentIntentId');
      expect(payment.amount).toBe(99.99);
      expect(payment.type).toBe('one_time');
      expect(payment.status).toBeDefined();
    });

    test('should create sponsorship payment intent', async () => {
      const payment = await createPaymentIntent({
        amount: 5000,
        currency: 'usd',
        type: 'sponsorship',
        description: 'Newsletter Sponsorship',
        metadata: { sponsor: 'Acme Corp' },
        receiptEmail: 'sponsor@acme.com'
      });

      expect(payment.type).toBe('sponsorship');
      expect(payment.amount).toBe(5000);
    });

    test('should get payment intent details', async () => {
      const payment = await createPaymentIntent({
        amount: 49.99,
        currency: 'usd',
        type: 'one_time'
      });

      const retrieved = await getPaymentIntent(payment.stripePaymentIntentId);
      expect(retrieved.stripePaymentIntentId).toBe(payment.stripePaymentIntentId);
    });

    test('should list payment intents', async () => {
      // Create a few payments
      await createPaymentIntent({
        amount: 10,
        currency: 'usd',
        type: 'one_time'
      });

      const payments = await listPaymentIntents(10);
      expect(Array.isArray(payments)).toBe(true);
    });
  });

  describe('Refund Processing', () => {
    test('should create full refund', async () => {
      const payment = await createPaymentIntent({
        amount: 99.99,
        currency: 'usd',
        type: 'one_time'
      });

      const refund = await createRefund(payment.stripePaymentIntentId);
      expect(refund).toHaveProperty('refundId');
      expect(refund.status).toBeDefined();
    });

    test('should create partial refund', async () => {
      const payment = await createPaymentIntent({
        amount: 100,
        currency: 'usd',
        type: 'one_time'
      });

      const refund = await createRefund(
        payment.stripePaymentIntentId,
        50 // Refund half
      );

      expect(refund.amount).toBe(50);
    });
  });

  describe('Revenue Tracking', () => {
    test('should record revenue', async () => {
      const revenue = {
        id: `revenue-${Date.now()}`,
        type: 'payment' as const,
        amount: 99.99,
        currency: 'usd',
        status: 'completed' as const,
        customerEmail: 'customer@example.com',
        customerName: 'Test Customer',
        createdAt: new Date().toISOString(),
        recordedAt: new Date().toISOString()
      };

      await recordRevenue(revenue);
      // Check file was created (in actual environment)
    });

    test('should handle payment succeeded event', async () => {
      const mockPaymentIntent: Stripe.PaymentIntent = {
        id: 'pi_test123',
        object: 'payment_intent',
        client_secret: 'secret_test',
        amount: 9999,
        currency: 'usd',
        status: 'succeeded',
        receipt_email: 'test@example.com',
        metadata: { type: 'one_time' },
        created: Math.floor(Date.now() / 1000),
        // Additional required fields
        payment_method: null,
        livemode: false,
        charges: { object: 'list', data: [], has_more: false, url: '' },
        confirmation_method: 'automatic',
        customer: null,
      } as Stripe.PaymentIntent;

      const revenue = await handlePaymentSucceeded(mockPaymentIntent);
      expect(revenue.amount).toBe(99.99);
      expect(revenue.type).toBe('payment');
    });

    test('should get revenue report', async () => {
      const report = await getRevenueReport();
      expect(report).toHaveProperty('date');
      expect(report).toHaveProperty('total');
      expect(report).toHaveProperty('count');
      expect(report).toHaveProperty('byType');
    });
  });

  describe('Webhook Processing', () => {
    test('should verify valid webhook signature', () => {
      const mockSecret = process.env.STRIPE_WEBHOOK_SECRET!;
      const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

      const payload = JSON.stringify({
        type: 'payment_intent.succeeded',
        data: { object: {} }
      });

      const timestamp = Math.floor(Date.now() / 1000);
      const signature = stripe.webhooks.generateTestHeaderString({
        payload,
        secret: mockSecret
      });

      expect(() => {
        verifyWebhookSignature(payload, signature, mockSecret);
      }).not.toThrow();
    });

    test('should reject invalid webhook signature', () => {
      const mockSecret = 'whsec_test_invalid';
      const payload = JSON.stringify({ type: 'test' });
      const invalidSignature = 't=123,v1=invalid';

      expect(() => {
        verifyWebhookSignature(payload, invalidSignature, mockSecret);
      }).toThrow();
    });
  });

  describe('Analytics', () => {
    test('should calculate monthly recurring revenue', async () => {
      const mrr = await getMonthlyRecurringRevenue();
      expect(typeof mrr).toBe('number');
      expect(mrr).toBeGreaterThanOrEqual(0);
    });

    test('should calculate churn rate', async () => {
      const churnRate = await getChurnRate(30);
      expect(typeof churnRate).toBe('number');
      expect(churnRate).toBeGreaterThanOrEqual(0);
      expect(churnRate).toBeLessThanOrEqual(100);
    });

    test('should calculate customer lifetime value', async () => {
      const customer = await createOrUpdateCustomer('ltv@example.com', 'LTV User');
      const ltv = await getCustomerLifetimeValue(customer.stripeCustomerId);
      expect(typeof ltv).toBe('number');
      expect(ltv).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Integration Scenarios', () => {
    test('complete subscription workflow', async () => {
      // 1. Create customer
      const customer = await createOrUpdateCustomer(
        'workflow@example.com',
        'Workflow User',
        { source: 'api_test' }
      );

      // 2. Create subscription
      const subscription = await createSubscription({
        stripeCustomerId: customer.stripeCustomerId,
        stripePriceId: 'price_monthly_pro',
        trialDays: 7,
        metadata: { plan: 'professional' }
      });

      // 3. Get subscription details
      const details = await getSubscription(subscription.stripeSubscriptionId);
      expect(details.status).toBe('trialing');

      // 4. Update to different tier
      const updated = await updateSubscription(
        subscription.stripeSubscriptionId,
        { stripePriceId: 'price_monthly_enterprise' }
      );
      expect(updated).toBeDefined();

      // 5. Cancel subscription
      const canceled = await cancelSubscription(subscription.stripeSubscriptionId);
      expect(canceled.status).toBe('canceled');
    });

    test('complete payment workflow', async () => {
      // 1. Create payment
      const payment = await createPaymentIntent({
        amount: 199.99,
        currency: 'usd',
        type: 'one_time',
        description: 'Enterprise Add-on',
        metadata: { feature: 'advanced_analytics' }
      });

      // 2. Verify payment
      const status = await getPaymentIntent(payment.stripePaymentIntentId);
      expect(status).toBeDefined();

      // 3. Process refund
      const refund = await createRefund(payment.stripePaymentIntentId);
      expect(refund.refundId).toBeDefined();
    });

    test('sponsorship workflow', async () => {
      // 1. Create sponsor customer
      const sponsor = await createOrUpdateCustomer(
        'sponsor@acme.com',
        'ACME Corp',
        { type: 'sponsor', tier: 'gold' }
      );

      // 2. Create sponsorship payment
      const payment = await createPaymentIntent({
        stripeCustomerId: sponsor.stripeCustomerId,
        amount: 5000,
        currency: 'usd',
        type: 'sponsorship',
        description: 'Q1 2024 Newsletter Sponsorship',
        metadata: {
          sponsor: 'ACME Corp',
          quarter: 'Q1-2024'
        },
        receiptEmail: sponsor.email
      });

      // 3. Record as revenue
      await recordRevenue({
        id: `sponsorship-${Date.now()}`,
        stripePaymentIntentId: payment.stripePaymentIntentId,
        type: 'sponsorship',
        amount: 5000,
        currency: 'usd',
        status: 'completed',
        customerEmail: sponsor.email,
        customerName: sponsor.name,
        metadata: {
          sponsor: 'ACME Corp',
          quarter: 'Q1-2024'
        },
        createdAt: new Date().toISOString(),
        recordedAt: new Date().toISOString()
      });

      expect(payment.amount).toBe(5000);
    });
  });
});

/**
 * Manual Testing Guide
 *
 * To test with real Stripe:
 *
 * 1. Set environment variables:
 *    STRIPE_SECRET_KEY=sk_test_xxxxx
 *    STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx
 *
 * 2. Run individual tests:
 *    npm test -- stripe-automation.test.ts
 *
 * 3. Test webhook locally with ngrok:
 *    ngrok http 3000
 *    Add https://xxxxx.ngrok.io/api/automation/stripe/webhook to Stripe webhooks
 *
 * 4. Trigger test webhooks from Stripe Dashboard:
 *    Developers → Webhooks → Events → Send test event
 *
 * Test scenarios to verify:
 * - Create subscription → Cancel → Verify revenue recorded
 * - Create payment → Refund → Verify revenue reversed
 * - Subscription renewal → Invoice paid → Verify MRR updated
 * - Webhook delivery → Verify event processed correctly
 * - Revenue report → Verify daily summary accurate
 */

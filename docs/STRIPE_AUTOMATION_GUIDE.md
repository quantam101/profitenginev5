# Stripe Payment Automation Guide

Complete implementation for handling subscriptions, one-time payments, sponsorships, webhook processing, revenue tracking, customer management, and subscription renewal.

## Table of Contents

1. [Configuration](#configuration)
2. [Customer Management](#customer-management)
3. [Subscription Management](#subscription-management)
4. [Payment Handling](#payment-handling)
5. [Revenue Tracking](#revenue-tracking)
6. [Webhook Processing](#webhook-processing)
7. [Analytics & Reporting](#analytics--reporting)
8. [API Examples](#api-examples)

## Configuration

### Environment Variables

```bash
# Required
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Optional
REVENUE_DATA_DIR=.runtime/revenue
WEBHOOK_VERIFY_TIMESTAMP=true
WEBHOOK_TIMESTAMP_TOLERANCE_SEC=300
```

### Setup Stripe Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Create a new endpoint with URL: `https://yourdomain.com/api/automation/stripe/webhook`
3. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.created`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.refunded`
   - `invoice.finalized`
4. Copy the signing secret to `STRIPE_WEBHOOK_SECRET`

## Customer Management

### Create or Update Customer

```typescript
import { createOrUpdateCustomer } from '@/lib/automation/stripe';

const customer = await createOrUpdateCustomer(
  'customer@example.com',
  'John Doe',
  { tier: 'premium', source: 'newsletter' }
);

// Returns:
// {
//   stripeCustomerId: 'cus_xxxxx',
//   email: 'customer@example.com',
//   name: 'John Doe',
//   metadata: { tier: 'premium', source: 'newsletter' },
//   createdAt: '2024-01-15T10:30:00Z',
//   updatedAt: '2024-01-15T10:30:00Z'
// }
```

### Retrieve Customer

```typescript
import { getCustomer } from '@/lib/automation/stripe';

const customer = await getCustomer('cus_xxxxx');
```

## Subscription Management

### Create Subscription

```typescript
import { createSubscription } from '@/lib/automation/stripe';

const subscription = await createSubscription({
  stripeCustomerId: 'cus_xxxxx',
  stripePriceId: 'price_monthly_pro',
  trialDays: 14,
  metadata: {
    plan: 'professional',
    billingCycle: 'monthly'
  }
});

// Returns subscription record with:
// - stripeSubscriptionId
// - status ('active', 'past_due', 'unpaid', 'canceled', 'trialing')
// - currentPeriodStart & currentPeriodEnd
// - amount and interval
```

### Update Subscription

```typescript
import { updateSubscription } from '@/lib/automation/stripe';

const updated = await updateSubscription('sub_xxxxx', {
  stripePriceId: 'price_monthly_enterprise',
  metadata: { plan: 'enterprise' }
});
```

### Cancel Subscription

```typescript
import { cancelSubscription } from '@/lib/automation/stripe';

const canceled = await cancelSubscription('sub_xxxxx');
```

### Get Subscription

```typescript
import { getSubscription } from '@/lib/automation/stripe';

const subscription = await getSubscription('sub_xxxxx');
```

### List Subscriptions

```typescript
import { listSubscriptions } from '@/lib/automation/stripe';

// Get all subscriptions for a customer
const subscriptions = await listSubscriptions('cus_xxxxx', 10);

// Get all active subscriptions
const allSubscriptions = await listSubscriptions(undefined, 100);
```

## Payment Handling

### Create Payment Intent

```typescript
import { createPaymentIntent } from '@/lib/automation/stripe';

// One-time payment
const payment = await createPaymentIntent({
  stripeCustomerId: 'cus_xxxxx',
  amount: 99.99,
  currency: 'usd',
  type: 'one_time',
  description: 'Premium Feature Pack',
  metadata: {
    feature: 'advanced_analytics',
    source: 'mobile_app'
  },
  receiptEmail: 'customer@example.com'
});

// Sponsorship payment
const sponsorship = await createPaymentIntent({
  amount: 250,
  currency: 'usd',
  type: 'sponsorship',
  description: 'Newsletter Sponsorship - Q1 2024',
  metadata: {
    sponsor: 'Acme Corp',
    duration: '1 month'
  },
  receiptEmail: 'sponsor@example.com'
});
```

### Get Payment Intent

```typescript
import { getPaymentIntent } from '@/lib/automation/stripe';

const payment = await getPaymentIntent('pi_xxxxx');
```

### List Payment Intents

```typescript
import { listPaymentIntents } from '@/lib/automation/stripe';

const payments = await listPaymentIntents(10);
```

### Create Refund

```typescript
import { createRefund } from '@/lib/automation/stripe';

const refund = await createRefund(
  'pi_xxxxx',
  99.99, // Optional: full refund if omitted
  'requested_by_customer'
);
```

## Revenue Tracking

### Record Revenue

```typescript
import { recordRevenue } from '@/lib/automation/stripe';

await recordRevenue({
  id: 'revenue-12345',
  stripePaymentIntentId: 'pi_xxxxx',
  type: 'payment',
  amount: 99.99,
  currency: 'usd',
  status: 'completed',
  customerEmail: 'customer@example.com',
  customerName: 'John Doe',
  description: 'Premium Feature Pack',
  metadata: {
    feature: 'advanced_analytics'
  },
  createdAt: new Date().toISOString(),
  recordedAt: new Date().toISOString()
});
```

### Get Revenue Report

```typescript
import { getRevenueReport } from '@/lib/automation/stripe';

// Get today's revenue
const todayReport = await getRevenueReport();

// Get specific date's revenue
const dateReport = await getRevenueReport('2024-01-15');

// Returns:
// {
//   date: '2024-01-15',
//   total: 5432.10,
//   count: 12,
//   byType: {
//     payment: 2500,
//     subscription: 2432.10,
//     sponsorship: 500
//   }
// }
```

## Webhook Processing

### Webhook Handler

The webhook endpoint automatically processes:

1. **Payment Intent Events**
   - `payment_intent.succeeded` → Records revenue, updates payment status
   - `payment_intent.payment_failed` → Logs failure, triggers retry notifications

2. **Subscription Events**
   - `customer.subscription.created` → Creates subscription record
   - `customer.subscription.updated` → Updates subscription data
   - `customer.subscription.deleted` → Marks subscription as canceled

3. **Invoice Events**
   - `invoice.created` → Logs invoice creation
   - `invoice.payment_succeeded` → Records revenue, updates payment status
   - `invoice.payment_failed` → Logs failure, triggers retry notifications
   - `invoice.finalized` → Confirms invoice ready for payment

4. **Refund Events**
   - `charge.refunded` → Records refund, updates revenue

### Example Webhook Signature

```typescript
import { verifyWebhookSignature } from '@/lib/automation/stripe';

try {
  const event = verifyWebhookSignature(
    rawBody,
    signature,
    process.env.STRIPE_WEBHOOK_SECRET
  );
  console.log(`Webhook verified: ${event.type}`);
} catch (error) {
  console.error('Invalid webhook:', error.message);
}
```

## Analytics & Reporting

### Monthly Recurring Revenue (MRR)

```typescript
import { getMonthlyRecurringRevenue } from '@/lib/automation/stripe';

const mrr = await getMonthlyRecurringRevenue();
console.log(`MRR: $${mrr.toFixed(2)}`);
```

### Churn Rate

```typescript
import { getChurnRate } from '@/lib/automation/stripe';

// Churn rate for last 30 days
const churnRate = await getChurnRate(30);
console.log(`30-day churn: ${churnRate.toFixed(2)}%`);
```

### Customer Lifetime Value (LTV)

```typescript
import { getCustomerLifetimeValue } from '@/lib/automation/stripe';

const ltv = await getCustomerLifetimeValue('cus_xxxxx');
console.log(`Customer LTV: $${ltv.toFixed(2)}`);
```

## API Examples

### Create Subscription via API

```bash
curl -X POST "https://yourdomain.com/api/automation/stripe?action=subscription-create" \
  -H "Content-Type: application/json" \
  -d '{
    "stripeCustomerId": "cus_xxxxx",
    "stripePriceId": "price_monthly_pro",
    "trialDays": 14,
    "metadata": {
      "plan": "professional"
    }
  }'
```

### Create One-Time Payment via API

```bash
curl -X POST "https://yourdomain.com/api/automation/stripe?action=payment-create" \
  -H "Content-Type: application/json" \
  -d '{
    "stripeCustomerId": "cus_xxxxx",
    "amount": 99.99,
    "currency": "usd",
    "type": "one_time",
    "description": "Premium Feature Pack",
    "receiptEmail": "customer@example.com"
  }'
```

### Cancel Subscription via API

```bash
curl -X POST "https://yourdomain.com/api/automation/stripe?action=subscription-cancel" \
  -H "Content-Type: application/json" \
  -d '{
    "subscriptionId": "sub_xxxxx"
  }'
```

### List Subscriptions via API

```bash
curl "https://yourdomain.com/api/automation/stripe?query=subscriptions&customer_id=cus_xxxxx&limit=10"
```

### Get Revenue Report via API

```bash
curl "https://yourdomain.com/api/automation/stripe?query=revenue-report&date=2024-01-15"
```

### Get MRR via API

```bash
curl "https://yourdomain.com/api/automation/stripe?query=mrr"
```

### Get Churn Rate via API

```bash
curl "https://yourdomain.com/api/automation/stripe?query=churn&days=30"
```

### Get Customer LTV via API

```bash
curl "https://yourdomain.com/api/automation/stripe?query=ltv&customer_id=cus_xxxxx"
```

## Integration Examples

### Sponsorship Workflow

```typescript
// 1. Create customer
const sponsor = await createOrUpdateCustomer(
  'sponsor@acme.com',
  'ACME Corporation',
  { type: 'sponsor', tier: 'gold' }
);

// 2. Create payment intent
const payment = await createPaymentIntent({
  stripeCustomerId: sponsor.stripeCustomerId,
  amount: 5000,
  currency: 'usd',
  type: 'sponsorship',
  description: 'Quarterly Newsletter Sponsorship',
  metadata: {
    sponsor: 'ACME Corp',
    period: 'Q1-2024'
  },
  receiptEmail: sponsor.email
});

// 3. Return client secret to frontend for payment form
console.log('Client secret:', payment.stripePaymentIntentId);
```

### Subscription Renewal Handling

```typescript
// When webhook receives invoice.payment_succeeded
const handleInvoicePaid = async (invoice: Stripe.Invoice) => {
  // 1. Record revenue
  await recordRevenue({
    id: `revenue-${Date.now()}`,
    stripeInvoiceId: invoice.id,
    stripeSubscriptionId: invoice.subscription?.toString(),
    type: 'subscription',
    amount: (invoice.amount_paid || 0) / 100,
    currency: invoice.currency,
    status: 'completed',
    customerEmail: invoice.customer_email || '',
    createdAt: new Date(invoice.created * 1000).toISOString(),
    recordedAt: new Date().toISOString()
  });

  // 2. Send renewal confirmation email
  // await sendRenewalEmail(invoice.customer_email, invoice.amount_paid / 100);

  // 3. Update customer in CRM
  // await updateCRMCustomer(invoice.customer, { lastPaymentDate: new Date() });
};
```

## Production Checklist

- [ ] Set `STRIPE_SECRET_KEY` in production environment
- [ ] Set `STRIPE_WEBHOOK_SECRET` in production environment
- [ ] Configure webhook endpoint in Stripe Dashboard
- [ ] Test webhook signature verification
- [ ] Set up revenue tracking database (optional but recommended)
- [ ] Configure email notifications for payment failures
- [ ] Set up alerts for MRR changes and high churn rates
- [ ] Enable automatic tax calculation in Stripe
- [ ] Test subscription renewal flow end-to-end
- [ ] Test refund processing and revenue reversal
- [ ] Monitor webhook delivery and retry handling
- [ ] Set up daily revenue reports and reconciliation

## Troubleshooting

### Webhook Not Processing

1. Check `STRIPE_WEBHOOK_SECRET` is correct
2. Verify webhook endpoint is publicly accessible
3. Check webhook delivery logs in Stripe Dashboard
4. Ensure server logs show received webhook events

### Payments Not Recording

1. Verify `STRIPE_SECRET_KEY` is correct
2. Check revenue data directory exists and is writable
3. Review error logs for payment intent failures
4. Verify payment intent metadata is being set correctly

### Subscription Issues

1. Check customer exists in Stripe before creating subscription
2. Verify price ID is active and matches account
3. Check trial days configuration if using trials
4. Review Stripe Dashboard for billing issues

### Revenue Tracking Issues

1. Ensure `.runtime/revenue` directory is writable
2. Check disk space for revenue log files
3. Verify date format is ISO 8601
4. Review daily summary JSON files for data integrity

---

For more information, see the [Stripe API documentation](https://stripe.com/docs/api).

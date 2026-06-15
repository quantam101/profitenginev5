# Payment Integration Plan — Already Here LLC

## Revenue Streams & Payment Processors

### 1. **STRIPE** (Primary) — B2B + Daily Work Intake
**Use Case:** Job payments, contractor invoicing, retainer contracts

| Revenue Stream | Processor | Flow | Settlement |
|---|---|---|---|
| **Daily Work Intake** | Stripe Payment Intent | Customer → Job → Payment → Contractor | Next day ACH |
| **B2B Retainer** | Stripe Invoicing API | Create invoice → Send to client → Auto-charge | Monthly or weekly |
| **Contractor Payouts** | Stripe Connect | Contractors connect own Stripe → Direct deposits | Configurable |

**Setup Required:**
- [ ] Stripe API keys (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY)
- [ ] Stripe Connect account for contractor payouts
- [ ] Webhook endpoints: payment.success, payment.failed, invoice.overdue
- [ ] Tax calculation (Stripe Tax API)

**Implementation:**
```typescript
// Daily job payment flow
POST /api/jobs/{id}/payment
  → Create Stripe PaymentIntent
  → Customer pays via Stripe Hosted Checkout
  → On success: mark job completed, initiate payout to contractor

// B2B retainer invoice flow
POST /api/prospects/{id}/invoice
  → Create Stripe Invoice
  → Send email to prospect contact
  → Auto-charge after due date
  → Track payment status on /prospects dashboard
```

---

### 2. **GUMROAD** (Digital Products) — Affiliate Bundles & Guides
**Use Case:** E-books, affiliate link collections, templates, courses

| Product Type | Price | Commission | Monthly Potential |
|---|---|---|---|
| Affiliate bundle (curated links) | $29-49 | 70% Gumroad fee | $1,500-3,000 |
| Service guide (how-to) | $19-29 | 70% Gumroad fee | $500-1,000 |
| Contractor templates | $9-19 | 70% Gumroad fee | $300-500 |

**Setup Required:**
- [ ] Gumroad API key
- [ ] Product pages (3-5 digital products ready to sell)
- [ ] Affiliate link bundles curated (already-here-llc specific)
- [ ] Email capture to mailing list

**Implementation:**
```typescript
// Link digital products from main site
GET /api/products/gumroad
  → Fetch Gumroad products via API
  → Display on alreadyherellc.com/shop
  → Auto-update when Gumroad inventory changes

// Track Gumroad conversions
POST /api/conversions
  → Log gumroad product sales
  → Update revenue dashboard
```

---

### 3. **ETSY** (Physical Products) — Optional
**Status:** Lower priority (digital-first approach recommended)

| Product | Cost | Margin | Setup |
|---|---|---|---|
| Affiliate merch (shirts, hats) | $15-30 print cost | 50-100% | Print-on-demand via Printful |
| Local service guides (printed) | $5-15 print cost | 200-300% | POD via Printful |

**Recommendation:** Start with Gumroad digital products first. Scale to Etsy/POD only after proving digital product market.

---

## Implementation Priority

### **Phase 1: Stripe (Critical Path)**
**Timeline:** This week
- [ ] Add STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY to GitHub Secrets
- [ ] Create `/api/payments/intent` endpoint (create PaymentIntent)
- [ ] Add Stripe Checkout button to `/work` job board
- [ ] Wire job completion → contractor payout flow
- [ ] Add `/api/webhooks/stripe` for payment confirmation
- [ ] Test: Post job → Customer pays → Contractor notified

**Expected Result:** Customers can pay for jobs, contractors get paid next day

### **Phase 2: Gumroad (Revenue Diversification)**
**Timeline:** Next week
- [ ] Create 3-5 Gumroad products (affiliate bundles, guides)
- [ ] Add Gumroad API key to secrets
- [ ] Build `/shop` page with Gumroad embeds
- [ ] Set up email capture on product pages
- [ ] Track sales via webhook

**Expected Result:** $500-2,000/month digital product revenue

### **Phase 3: Etsy / Print-on-Demand (Growth)**
**Timeline:** Month 2+
- [ ] Design 3 POD products (shirts, hats, guides)
- [ ] Set up Printful integration
- [ ] Connect to Etsy
- [ ] Market to existing audience

---

## Environment Variables Required

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CONNECT_CLIENT_ID=ca_...

# Gumroad
GUMROAD_API_KEY=...

# Etsy (if added)
ETSY_API_KEY=...
ETSY_API_SECRET=...

# Contractor info
CONTRACTOR_BANK_ACCOUNT=...  # For payout setup
CONTRACTOR_STRIPE_CONNECT_ID=...
```

---

## API Endpoints to Build

### Stripe Endpoints
```
POST   /api/payments/intent         Create PaymentIntent for job
POST   /api/payments/confirm        Confirm payment (webhook)
GET    /api/payments/status/{jobId} Check payment status
POST   /api/payouts/create          Create payout to contractor
GET    /api/payouts/{contractorId}  View payout history
```

### Gumroad Endpoints
```
GET    /api/products/gumroad        List Gumroad products
POST   /api/sales/gumroad           Log Gumroad sale (webhook)
GET    /api/sales/report            Revenue report (Gumroad + Stripe)
```

### Invoice Endpoints (B2B)
```
POST   /api/invoices/create         Create Stripe Invoice for prospect
GET    /api/invoices/{prospectId}   View invoice status
PATCH  /api/invoices/{id}/pay       Mark paid manually
POST   /api/invoices/send           Email invoice to prospect
```

---

## Webhook Flow

```
Stripe Payment Webhook
├─ payment.intent.succeeded
│  ├─ Update job status → "paid"
│  ├─ Notify contractor
│  ├─ Create payout (ACH next day)
│  └─ Add to revenue dashboard
│
├─ payment.intent.payment_failed
│  ├─ Notify customer
│  └─ Keep job as "pending_payment"
│
└─ charge.refunded
   ├─ Reverse payout
   └─ Mark job as "refunded"

Gumroad Webhook
├─ sale.completed
│  ├─ Send product link
│  ├─ Add email to mailing list
│  └─ Update /products dashboard

Stripe Invoice Webhook
├─ invoice.payment_succeeded
│  ├─ Update prospect as "paid"
│  ├─ Mark deal as "won + closed"
│  └─ Add to B2B retainer pipeline
```

---

## Testing Checklist

- [ ] Create test job on `/work`
- [ ] Use Stripe test card (4242 4242 4242 4242)
- [ ] Verify payment succeeds in Stripe Dashboard
- [ ] Check job marked as "paid"
- [ ] Confirm contractor receives payout notification
- [ ] Test refund flow
- [ ] Test failed payment retry
- [ ] Verify webhooks fire correctly
- [ ] Check `/prospects` updates for B2B invoice payments

---

## Revenue Projections

### Conservative (Month 1)
- Daily work intake: 2 jobs × $350 margin × 5 days = **$3,500**
- B2B retainer (1 contract): $2,000/month = **$2,000** (partial)
- Gumroad products: 10 sales × $35 avg = **$350**
- **Month 1 Total: ~$5,850**

### Realistic (Month 2-3)
- Daily work: 4 jobs/day × $350 × 15 days = **$21,000**
- B2B retainer (3 contracts): 3 × $2,000 = **$6,000**
- Gumroad: 50 sales × $35 = **$1,750**
- **Month 2-3 Total: ~$28,750/month**

### Aggressive (Month 3+)
- Daily work: 10 jobs/day × $350 × 20 days = **$70,000**
- B2B retainer (10 contracts): 10 × $2,000 = **$20,000**
- Gumroad: 200 sales × $35 = **$7,000**
- Etsy/POD: 50 sales × $40 margin = **$2,000**
- **Month 3+ Total: ~$99,000/month**

---

## Next Actions

1. **Gather Stripe credentials** (API keys from live account)
2. **Decide on B2B invoice frequency** (weekly, monthly, retainer)
3. **Design 3-5 Gumroad products** (list titles + descriptions)
4. **Set contractor payout terms** (daily, weekly, monthly ACH)
5. **Begin Phase 1 implementation** (Stripe job payments)

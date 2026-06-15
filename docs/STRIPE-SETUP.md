# Stripe Payment Setup — Already Here LLC

## Quick Start (5 minutes)

### Step 1: Get Stripe API Keys

1. Go to **https://dashboard.stripe.com**
2. Sign in (or create account with email)
3. Click **Developers** (top right) → **API keys**
4. Copy these keys:
   - **Secret Key** (starts with `sk_live_...`)
   - **Publishable Key** (starts with `pk_live_...`)

### Step 2: Get Webhook Secret

1. Still in Developers → **Webhooks**
2. Click **+ Add endpoint**
3. **Endpoint URL**: `https://api.alreadyherellc.com/api/webhooks/stripe`
   - (Or your Vercel production URL if different)
4. **Events to send**: Select:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. In the endpoint details, copy **Signing secret** (starts with `whsec_...`)

### Step 3: Add to GitHub Secrets

```bash
# Add Stripe keys to profitenginev5 GitHub Secrets
gh secret set STRIPE_SECRET_KEY -R quantam101/profitenginev5 --body "sk_live_..."
gh secret set STRIPE_PUBLISHABLE_KEY -R quantam101/profitenginev5 --body "pk_live_..."
gh secret set STRIPE_WEBHOOK_SECRET -R quantam101/profitenginev5 --body "whsec_..."
gh secret set NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY -R quantam101/profitenginev5 --body "pk_live_..."
```

### Step 4: Add to `.env.local` (Local Development)

Create `C:\Users\alrea\Downloads\profitengine-v5-final (1)\.env.local`:

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Step 5: Test Payment Flow

1. Start dev server: `npm run dev`
2. Navigate to `http://localhost:3000/work`
3. Click "Pay for this job" (once implemented)
4. Use test card: **4242 4242 4242 4242**
   - Expiry: Any future date (e.g., 12/25)
   - CVC: Any 3 digits (e.g., 123)
5. Check Stripe Dashboard → **Payments** to see the transaction

---

## Testing Checklist

### Test Cards (Stripe)
```
✅ Successful payment:
   Card: 4242 4242 4242 4242
   Expiry: 12/25
   CVC: 123

❌ Payment declined:
   Card: 4000 0000 0000 0002
   Expiry: 12/25
   CVC: 123

⚠️ Require authentication (3D Secure):
   Card: 4000 0025 0000 3155
   Expiry: 12/25
   CVC: 123
```

### Payment Flow Test
- [ ] Create job on `/work`
- [ ] Click "Pay for job"
- [ ] Enter test card (4242...)
- [ ] Verify payment in Stripe Dashboard
- [ ] Check job marked as "paid"
- [ ] Confirm contractor notified
- [ ] Test refund via Stripe Dashboard

### Webhook Test
```bash
# Test webhook locally using Stripe CLI
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# In another terminal, trigger a test payment
stripe trigger payment_intent.succeeded
```

---

## Production Checklist

### Before Going Live
- [ ] Switch to **live Stripe keys** (not test keys)
- [ ] Update webhook endpoint to production domain
- [ ] Test with real payment method (or get Stripe to whitelist)
- [ ] Enable 3D Secure for high-value transactions
- [ ] Set up tax calculation (Stripe Tax API)
- [ ] Configure payment success/failure email templates
- [ ] Set up Stripe Radar for fraud detection
- [ ] Document refund policy
- [ ] Enable PCI DSS compliance monitoring

### Security
- [ ] Never commit Stripe keys to git (use GitHub Secrets)
- [ ] Keep STRIPE_SECRET_KEY server-side only
- [ ] Use NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY for client
- [ ] Verify webhook signatures (already done in `/api/webhooks/stripe`)
- [ ] Use HTTPS only (Vercel handles this)
- [ ] Enable Stripe's fraud detection

---

## Revenue Flows

### Daily Work Intake Flow
```
1. Customer posts job on /work
   → Title: "Junk removal", Pay: $350, Miles: 8
   
2. Contractor accepts job
   → Status: "accepted"
   
3. After job completion, customer pays
   → Click "Pay for job"
   → Stripe checkout modal
   → Customer pays $350
   
4. Webhook confirms payment
   → payment_intent.succeeded
   → Update job status → "paid"
   → Create payout to contractor ($350 - 2.9% fee = $339.85)
   → Deposit to contractor account next day (ACH)
   
5. Contractor gets paid
   → Email notification
   → Funds appear in bank account
```

### B2B Retainer Flow
```
1. Prospect agrees to $2,000/month retainer
   → Sales team confirms terms
   
2. Create invoice
   → POST /api/invoices/create
   → Stripe Invoice for $2,000
   
3. Send invoice to prospect
   → Email with payment link
   → Auto-charge after due date
   
4. Webhook confirms payment
   → invoice.payment_succeeded
   → Update prospect status → "won + closed"
   → Mark retainer as active
   → Schedule next month's invoice
```

---

## Troubleshooting

### "Stripe not loaded"
- Check NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY is set
- Clear `.next` cache: `rm -rf .next`
- Restart dev server

### Payment fails silently
- Check browser console for errors
- Verify webhook endpoint is registered in Stripe Dashboard
- Check STRIPE_WEBHOOK_SECRET is correct
- Look at Stripe Dashboard → Events for webhook failures

### Webhook not firing
- Verify endpoint URL is correct
- Check webhook secret matches
- Use `stripe listen` to test locally
- Check Stripe Dashboard → Webhooks → click endpoint → "API logs"

### Customer sees "Card declined" but card is valid
- May be 3D Secure required
- Test with card ending in 3155 to simulate 3DS
- In production, enable 3DS for payments over $50

---

## Support

- **Stripe Docs**: https://stripe.com/docs
- **API Reference**: https://stripe.com/docs/api
- **Testing**: https://stripe.com/docs/testing
- **Dashboard**: https://dashboard.stripe.com


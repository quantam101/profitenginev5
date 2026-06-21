# STRIPE WEBHOOK LIVE TEST - PHASE 2
**EXECUTION: 2026-06-21**
**OBJECTIVE:** End-to-end real Stripe transaction test with webhook verification

## CURRENT STATE

### Stripe Account
- **Live Key**: `sk_live_51TbKf7LCbDeoJgUR...` (configured in `.env`)
- **Webhook Secret**: `whsec_wvU9MC3D8IC2uZiX8MuGyPRaFEmcBWn3` (configured in `.env`)
- **Status**: Live mode enabled

### Deployment Status
- **Frontend**: https://profitengine-tau.vercel.app (Vercel)
- **Webhook Endpoint**: `/api/webhooks/stripe` (built into Next.js app)
- **Build Status**: ✅ All routes compile successfully including webhook

### Code Status
- **Webhook Handler**: `app/api/webhooks/stripe/route.ts` - Handles:
  - `payment_intent.succeeded`
  - `payment_intent.payment_failed`
  - `charge.refunded`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`

---

## EXECUTION STEPS

### STEP 1: Verify Stripe Webhook Endpoint Live
- [ ] Test endpoint: GET https://profitengine-tau.vercel.app/api/webhooks/stripe
- [ ] Expected: 405 (GET not allowed is OK - means POST endpoint exists)
- [ ] Verify STRIPE_WEBHOOK_SECRET in Vercel env
- [ ] Verify STRIPE_API_KEY in Vercel env (live key sk_live_*)

**FINDING:** Vercel may need redeploy if endpoint returns 404

---

### STEP 2: Configure Stripe Dashboard
**URL:** https://dashboard.stripe.com/test/webhooks
**ACTION:**
1. Click: "Add an endpoint" button
2. URL: `https://profitengine-tau.vercel.app/api/webhooks/stripe`
3. Select events:
   - `charge.succeeded`
   - `charge.failed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Create endpoint
5. **Copy signing secret** (format: `whsec_...`)
6. Verify it matches `.env` STRIPE_WEBHOOK_SECRET

**CRITICAL:** If signing secrets don't match, update Vercel env var immediately

---

### STEP 3: Test Webhook via Stripe Dashboard
**ACTION:**
1. Find webhook endpoint in dashboard
2. Click "Send test event"
3. Select: `charge.succeeded`
4. Send event
5. Check Stripe webhook logs for delivery status

**SUCCESS CRITERIA:**
- Event shows "delivered" in Stripe logs
- HTTP status 200 from endpoint

---

### STEP 4: Make REAL Test Charge
**SETUP:**
1. Find a Gumroad product (use existing $0.99 product or create test product)
2. Navigate to product page
3. Click "Buy now" button

**CARD DETAILS (Stripe test card):**
- Card number: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., `12/26`)
- CVC: Any 3 digits (e.g., `123`)
- Name: `Test`
- Email: `test@example.com`
- Click "Pay"

**VERIFICATION (immediately after payment):**
1. Stripe dashboard shows charge → Status: "succeeded"
2. Amount: $0.99
3. Webhook log shows `charge.succeeded` event **sent** (check delivery status)

---

### STEP 5: Verify Complete Flow
**CHECK ALL:**
- [ ] Stripe dashboard: Charge appears, status = "succeeded"
- [ ] Stripe webhook log: Event delivered (check status icon)
- [ ] System logs: Webhook received (check Vercel logs)
- [ ] Transaction JSONL: Entry logged to `.runtime/revenue/transactions.jsonl`
- [ ] Dashboard API: `/api/revenue/summary` shows transaction
- [ ] Amount correct: $0.99
- [ ] Timestamp captured
- [ ] Customer email captured: test@example.com

---

### STEP 6: Screenshot Evidence
**CAPTURE THREE SCREENSHOTS:**
1. **Stripe Dashboard - Charge:**
   - Shows charge ID, amount $0.99, status "succeeded"
   - Date/time
   - Payment method

2. **Stripe Webhook Log:**
   - Event type: `charge.succeeded`
   - Delivery status: ✅ Delivered
   - HTTP response code: 200
   - Timestamp

3. **System Dashboard / Logs:**
   - Transaction visible in UI OR
   - Vercel function logs showing webhook received OR
   - Transaction JSONL file with entry

---

## SUCCESS CRITERIA

✅ **COMPLETE FLOW:**
- Real $0.99 charge processed on Stripe
- Webhook received by system within 5-10 seconds
- Transaction logged in system
- Dashboard displays transaction
- All data captured: amount, timestamp, customer email
- Timeline: under 10 seconds total

---

## FAILURE RECOVERY

| Issue | Action |
|-------|--------|
| Endpoint 404 | Redeploy Vercel: `vercel deploy --prod` |
| Webhook signing secret mismatch | Update Vercel env var to match Stripe dashboard |
| Webhook not received | Check Vercel logs for signature verification errors |
| Transaction not logged | Check .runtime/revenue/transactions.jsonl exists and is writable |
| Dashboard doesn't update | Check /api/revenue/summary endpoint |

---

## FINAL STATUS

| Result | Status |
|--------|--------|
| Charge processed | ⏳ Pending |
| Webhook received | ⏳ Pending |
| Data complete | ⏳ Pending |
| **OVERALL** | ⏳ **NOT STARTED** |

---

## NOTES
- Stripe live key confirmed in `.env`
- Webhook signing secret confirmed in `.env`
- No placeholder values detected
- System ready for live test

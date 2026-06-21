# 🚀 START STRIPE WEBHOOK LIVE TEST - QUICK START

**Status:** ✅ System Ready for Phase 2 Live Testing  
**Created:** 2026-06-21  
**Type:** Manual browser-based test with real $0.99 charge  
**Duration:** ~45 minutes  
**Risk Level:** Low (test card, Stripe-managed)

---

## THREE QUICK CHECKS BEFORE YOU START

### ✅ Check 1: Is Stripe Webhook Endpoint Live?
```
GET https://profitengine-tau.vercel.app/api/webhooks/stripe
Expected: 405 (Method Not Allowed)
This means: Endpoint exists and is deployed ✅
```

### ✅ Check 2: Do You Have Stripe Dashboard Access?
- [ ] Can log in to https://dashboard.stripe.com
- [ ] Account is in LIVE mode (not test mode)
- [ ] Can create webhooks

### ✅ Check 3: Do You Have a Gumroad Product?
- [ ] Product exists at any price
- [ ] "Buy" button works
- [ ] Redirects to Stripe checkout

---

## QUICK START - 3 STEPS

### Step 1: Open Three Browser Tabs (2 min)
1. Tab 1: Stripe Webhooks Dashboard  
   `https://dashboard.stripe.com/test/webhooks`

2. Tab 2: Stripe Payments  
   `https://dashboard.stripe.com/test/payments`

3. Tab 3: Your Gumroad Product  
   `https://gumroad.com/l/...` (your product link)

### Step 2: Configure Webhook (5 min)
**In Tab 1 (Stripe Webhooks):**
1. Click "Add an endpoint"
2. Paste URL: `https://profitengine-tau.vercel.app/api/webhooks/stripe`
3. Select 6 events:
   - ✓ charge.succeeded
   - ✓ charge.failed
   - ✓ payment_intent.succeeded
   - ✓ payment_intent.payment_failed
   - ✓ invoice.payment_succeeded
   - ✓ invoice.payment_failed
4. Click "Create endpoint"
5. **Copy the signing secret** (whsec_...) and keep it for verification

### Step 3: Make Real $0.99 Payment (5 min)
**In Tab 3 (Gumroad):**
1. Click "Buy now"
2. Fill Stripe checkout:
   - Card: `4242 4242 4242 4242`
   - Expiry: `12/26`
   - CVC: `123`
   - Name: `Test`
   - Email: `test@example.com`
3. Click "Pay"
4. Wait for success page
5. **Note the timestamp** when payment succeeded

---

## THEN VERIFY IN 4 STEPS

### Verify 1: Stripe Webhook Event Delivered (2 min)
**In Tab 1:**
1. Refresh page or scroll to event log
2. Find `charge.succeeded` event
3. Click it to expand
4. Check: Status = ✅ "Delivered" & Response = `200`
5. **Screenshot this!**

### Verify 2: Real Payment in Stripe (1 min)
**In Tab 2 (Stripe Payments):**
1. Refresh page
2. Find $0.99 charge at top
3. Status should be "Succeeded"
4. **Screenshot this!**

### Verify 3: System Logs (5 min)
**Option A - Check Vercel Logs:**
1. Go to: `https://vercel.com/dashboard`
2. Click project: `profitenginev5`
3. Click "Functions" tab
4. Filter for `/api/webhooks/stripe`
5. Look for log: `✅ Payment succeeded: ch_...`
6. **Screenshot this!**

**Option B - Check Local Transaction Log:**
1. Terminal: SSH to OCI if you have access
   ```bash
   ssh opc@129.146.236.177
   cat .runtime/revenue/transactions.jsonl | tail -5
   ```
2. Should show entry with amount: `0.99`
3. **Screenshot this!**

### Verify 4: Dashboard API (2 min)
1. New browser tab: `https://profitengine-tau.vercel.app/api/revenue/summary`
2. Look for transaction with amount: `0.99`
3. Should include:
   - `id`: charge ID
   - `amount`: 0.99
   - `source`: stripe
4. **Screenshot this!**

---

## FINAL CHECKLIST - Mark These Off

**BEFORE TEST:**
- [ ] Endpoint responds 405
- [ ] Can access Stripe dashboard
- [ ] Have Gumroad product link
- [ ] Know webhook signing secret

**DURING TEST:**
- [ ] Webhook configured
- [ ] $0.99 payment successful
- [ ] Email received (test@example.com) or check Stripe
- [ ] Timestamp noted

**AFTER TEST:**
- [ ] Stripe event shows "Delivered" + 200
- [ ] Vercel logs show webhook received
- [ ] Transaction logged in system
- [ ] /api/revenue/summary shows charge

**COLLECTED:**
- [ ] Screenshot 1: Endpoint 405
- [ ] Screenshot 2: Webhook configured
- [ ] Screenshot 3: Payment success
- [ ] Screenshot 4: Event delivered
- [ ] Screenshot 5: Vercel logs
- [ ] Screenshot 6: Transaction log
- [ ] Screenshot 7: Revenue API
- [ ] Screenshot 8: Final verification

---

## EXPECTED RESULTS

If everything works:
```
Charge ID: ch_...
Amount: $0.99
Status: Succeeded
Webhook Delivered: ✅ 200
System Logged: ✅
Timeline: Charged → Webhook → Logged (under 10 seconds)
Result: ✅ PASS
```

---

## TROUBLESHOOTING - QUICK FIXES

| Problem | Fix | Time |
|---------|-----|------|
| Endpoint returns 404 | `vercel deploy --prod` | 2 min |
| Webhook shows ❌ Failed | Verify signing secret matches | 1 min |
| No Vercel logs | Check function logs tab | 1 min |
| No transaction file | Create: `mkdir -p .runtime/revenue` | 1 min |
| API returns 500 | Check Vercel error logs | 2 min |

---

## DETAILED DOCUMENTS

For more information, see:
- **Manual Execution Guide:** `STRIPE_WEBHOOK_LIVE_TEST_MANUAL.md` (step-by-step with details)
- **Readiness Report:** `PHASE2_TEST_READINESS_REPORT.md` (full technical verification)
- **Webhook Code:** `app/api/webhooks/stripe/route.ts` (implementation details)

---

## REAL WORLD IMPACT

This test processes **REAL MONEY:**
- Amount: $0.99 (actual charge, not test)
- Processing: Stripe charges the test card
- Money: Transferred to your Stripe account (minus fees)
- Refund: Can be issued manually in Stripe dashboard if needed
- Audit: Transaction stays in logs forever (compliance trail)

---

## SUCCESS = PRODUCTION READY

When this test PASSES:
1. Webhook integration is verified working
2. System can handle real payments
3. Transaction logging is confirmed
4. Dashboard API is functional
5. Ready to enable public payments
6. Stripe integration production-approved

---

## RUN THE TEST

1. **Open this file:** `STRIPE_WEBHOOK_LIVE_TEST_MANUAL.md`
2. **Follow each phase** (7 phases total, ~45 min)
3. **Collect screenshots** (mark checkboxes)
4. **Report results** (PASS/FAIL + evidence)

---

## QUESTIONS?

Check these sections in the manual:
- **Phase not working?** → See "Troubleshooting" section
- **Need more details?** → See "Readiness Report" for full technical info
- **Code questions?** → See `app/api/webhooks/stripe/route.ts`

---

**Ready?** Open `STRIPE_WEBHOOK_LIVE_TEST_MANUAL.md` and start Phase 1! 🎯

---

## COMMAND REFERENCE

```bash
# Verify build succeeded
npm run build

# Check webhook code
cat app/api/webhooks/stripe/route.ts

# Check environment variables
cat .env | grep STRIPE

# Create runtime directory (if needed)
mkdir -p .runtime/revenue

# Check transaction log (if server access)
ssh opc@129.146.236.177 "cat .runtime/revenue/transactions.jsonl | tail -5"
```

---

**Status:** ✅ System Ready  
**Confidence:** High (all components verified)  
**Next Action:** Execute manual test phases 1-7  
**Expected Outcome:** PASS (webhook integration confirmed working)

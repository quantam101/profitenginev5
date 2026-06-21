# STRIPE WEBHOOK LIVE TEST - MANUAL EXECUTION GUIDE
**Date:** 2026-06-21  
**Status:** Ready for Manual Execution  
**Objective:** Complete end-to-end Stripe webhook verification with real $0.99 transaction

---

## PRE-FLIGHT CHECKLIST

### Environment Verification
- [x] STRIPE_API_KEY: `sk_live_51TbKf7LCbDeoJgUR...` (LIVE key confirmed)
- [x] STRIPE_WEBHOOK_SECRET: `whsec_wvU9MC3D8IC2uZiX8MuGyPRaFEmcBWn3` (configured in `.env`)
- [x] Webhook endpoint code: `/api/webhooks/stripe` (built and deployed)
- [x] Handler logic: Processes `payment_intent.succeeded`, `charge.succeeded`, etc.

### System Status
- Vercel deployment: `profitengine-tau.vercel.app` (frontend live)
- Next.js app routes compiled: All `/api/webhooks/*` routes present
- .runtime directory: Available for transaction logging

---

## EXECUTION STEPS

### PHASE 1: VERIFY WEBHOOK ENDPOINT EXISTS (5 minutes)

**ACTION 1.1: Test Endpoint Response**
1. Open new browser tab
2. Navigate to: `https://profitengine-tau.vercel.app/api/webhooks/stripe`
3. Expected response:
   - **Status Code:** 405 (Method Not Allowed) — This is GOOD
   - **Why:** GET method not allowed; POST endpoint exists
   - **Error body (OK to see):** `{"error": "Missing stripe-signature header"}`
4. Screenshot to capture: Full browser tab showing 405 error

**Action Result:**
- [ ] Endpoint responds with 405
- [ ] Confirms webhook handler is deployed

---

### PHASE 2: CONFIGURE STRIPE WEBHOOK ENDPOINT (10 minutes)

**ACTION 2.1: Navigate to Stripe Webhooks Dashboard**
1. Open new browser tab
2. Go to: `https://dashboard.stripe.com/test/webhooks`
3. You should see login screen or dashboard
4. If not logged in: Sign in with your Stripe account

**ACTION 2.2: Create Webhook Endpoint**
1. Click button: **"Add an endpoint"** (top right)
2. Fill form:
   - **URL field:** `https://profitengine-tau.vercel.app/api/webhooks/stripe`
   - **Events to send:** Select these checkboxes:
     - ✓ `charge.succeeded`
     - ✓ `charge.failed`
     - ✓ `payment_intent.succeeded`
     - ✓ `payment_intent.payment_failed`
     - ✓ `invoice.payment_succeeded`
     - ✓ `invoice.payment_failed`
   - Click button: **"Create endpoint"**

**ACTION 2.3: Verify Webhook Secret**
1. Dashboard now shows new endpoint
2. Click on the endpoint to view details
3. Find section: **"Signing secret"**
4. Copy the secret (format: `whsec_...`)
5. **CRITICAL CHECK:** Does this secret match `.env` value?
   - Expected: `whsec_wvU9MC3D8IC2uZiX8MuGyPRaFEmcBWn3`
   - [ ] If MATCH: ✅ Continue to Phase 3
   - [ ] If NO MATCH: 
     - [ ] Update Vercel env var: `STRIPE_WEBHOOK_SECRET` = copied value
     - [ ] Redeploy: `vercel deploy --prod`
     - [ ] Wait 2 minutes for deployment

**ACTION 2.4: Enable Endpoint** (if disabled)
1. Check status toggle: Should show "Enabled"
2. If disabled, click toggle to enable

**SCREENSHOT REQUIRED:**
- Webhook endpoint detail page showing:
  - URL: `profitengine-tau.vercel.app/api/webhooks/stripe`
  - Signing secret: `whsec_...`
  - Status: Enabled
  - Events: All 6 event types listed

---

### PHASE 3: TEST WEBHOOK VIA STRIPE DASHBOARD (5 minutes)

**ACTION 3.1: Send Test Event**
1. On webhook endpoint detail page
2. Find button: **"Send test event"** (right side)
3. Click it
4. Select event type dropdown: Choose **`charge.succeeded`**
5. Click: **"Send test event"**
6. Stripe shows: **"Event sent"** confirmation

**ACTION 3.2: Verify Delivery**
1. Page now shows webhook events log
2. Find the test event you just sent
3. Check delivery status (look for checkmark or "Delivered")
4. Click event row to expand details
5. Verify:
   - [ ] Status shows "delivered" (not failed)
   - [ ] HTTP response code: `200`
   - [ ] Timestamp captured

**SCREENSHOT REQUIRED:**
- Webhook event log showing:
  - Event type: `charge.succeeded`
  - Status: ✅ Delivered
  - Response code: `200`
  - Timestamp

---

### PHASE 4: MAKE REAL TEST CHARGE (5 minutes)

**ACTION 4.1: Access Payment Product**
1. Open new tab
2. Navigate to your Gumroad product (use existing $0.99 product or create test)
3. Product page should show: Price and "Buy" button
4. Click: **"Buy now"** button
5. You're redirected to Stripe Checkout

**ACTION 4.2: Complete Payment**

Stripe checkout form will appear with fields:
- Email
- Card number
- Expiry
- CVC
- Cardholder name

**Fill with TEST CARD (Stripe always succeeds with this card):**
```
Card Number:  4242 4242 4242 4242
Expiry:       12/26 (any future date)
CVC:          123 (any 3 digits)
Name:         Test
Email:        test@example.com
Country:      United States (or your country)
```

6. Click: **"Pay"** button
7. Wait 2-3 seconds for processing
8. Stripe shows: **"Payment successful"** (or redirects to success page)

**CRITICAL:** Note the transaction ID/charge ID shown on success page

**SCREENSHOT REQUIRED:**
- Stripe payment success page showing:
  - Message: "Payment successful" or "Thank you"
  - Amount: $0.99
  - Charge ID (if visible)
  - Timestamp

---

### PHASE 5: VERIFY WEBHOOK DELIVERY (10 minutes)

**ACTION 5.1: Check Stripe Webhook Log**
1. Go back to: `https://dashboard.stripe.com/test/webhooks`
2. Click on your webhook endpoint
3. Scroll to event log (bottom of page)
4. You should see NEW events from your payment:
   - `charge.succeeded` (primary event)
   - `payment_intent.succeeded` (secondary)
5. Click `charge.succeeded` row to expand

**ACTION 5.2: Verify Event Details**
1. Event detail panel shows:
   - Event ID: `evt_...`
   - Timestamp: Should match payment time (within 1 second)
   - Data: Full charge object
2. Expand "Response" section
3. Verify:
   - [ ] HTTP Status: `200`
   - [ ] Delivery time: < 1 second
   - [ ] Status badge: ✅ Delivered

**SCREENSHOT REQUIRED:**
- Webhook event detail showing:
  - Event type: `charge.succeeded`
  - Charge ID: `ch_...`
  - Amount: `99` (cents = $0.99)
  - Status: ✅ Delivered
  - Response code: `200`

---

### PHASE 6: VERIFY SYSTEM LOGGING (10 minutes)

**ACTION 6.1: Check Vercel Logs**
1. Go to: `https://vercel.com/dashboard` (your Vercel account)
2. Select project: `profitenginev5`
3. Click: **"Functions"** or **"Logs"** tab
4. Filter logs for: `/api/webhooks/stripe`
5. Look for:
   - `✅ Payment succeeded: ch_...` (from webhook handler)
   - `💳 Payout created:` (if contractor job exists)
   - Timestamp matching your transaction time

**SCREENSHOT REQUIRED:**
- Vercel logs showing:
  - Function: `api/webhooks/stripe`
  - Message: "✅ Payment succeeded: ch_..." 
  - Timestamp: Your transaction time

**ACTION 6.2: Check Local Transaction Log (if accessing server)**
1. SSH into OCI server: `ssh opc@129.146.236.177`
2. Navigate to project runtime: `cd /path/to/profitengine/.runtime/revenue`
3. Check transaction file: `cat transactions.jsonl | tail -5`
4. Should see entry:
   ```json
   {
     "id": "ch_...",
     "amount": 0.99,
     "currency": "usd",
     "status": "succeeded",
     "customer_email": "test@example.com",
     "created": "2026-06-21T...",
     "source": "stripe"
   }
   ```

**SCREENSHOT REQUIRED:**
- Terminal output showing:
  - Transaction JSONL entry
  - Amount: 0.99
  - Status: succeeded
  - Email: test@example.com

---

### PHASE 7: VERIFY DASHBOARD API (10 minutes)

**ACTION 7.1: Test Revenue API**
1. Open new tab
2. Navigate to: `https://profitengine-tau.vercel.app/api/revenue/summary`
3. Browser displays JSON response
4. Look for transaction entry:
   ```json
   {
     "totalRevenue": 0.99,
     "transactions": [
       {
         "id": "ch_...",
         "amount": 0.99,
         "timestamp": "...",
         "source": "stripe"
       }
     ]
   }
   ```

**SCREENSHOT REQUIRED:**
- API response JSON showing:
  - totalRevenue: 0.99
  - transaction with amount: 0.99
  - transaction source: "stripe"
  - transaction id: "ch_..."

---

## FINAL VERIFICATION CHECKLIST

| Item | Status | Screenshot |
|------|--------|-----------|
| Webhook endpoint responds 405 | ⏳ | ▢ |
| Webhook configured in Stripe dashboard | ⏳ | ▢ |
| Test event delivered (200 response) | ⏳ | ▢ |
| Real $0.99 charge succeeded | ⏳ | ▢ |
| Webhook log shows charge.succeeded event | ⏳ | ▢ |
| Event delivered (200 response) | ⏳ | ▢ |
| Vercel logs show webhook received | ⏳ | ▢ |
| Transaction logged in .runtime/revenue/transactions.jsonl | ⏳ | ▢ |
| /api/revenue/summary shows transaction | ⏳ | ▢ |
| All data captured (amount, email, timestamp) | ⏳ | ▢ |

---

## SUCCESS CRITERIA

✅ **Test PASSES if ALL of these are true:**
- Real $0.99 charge processed on Stripe (charge.succeeded)
- Webhook received by system within 5 seconds
- HTTP 200 response logged by Stripe
- Transaction visible in Vercel logs
- Transaction logged in .runtime/revenue/transactions.jsonl
- /api/revenue/summary API returns transaction
- All metadata captured: amount, email, timestamp, charge ID

✅ **Test COMPLETE when:**
- 10 screenshots collected
- All verification checks marked complete
- Final report generated with results

---

## TROUBLESHOOTING

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Endpoint returns 404 | Deployment stale | `vercel deploy --prod` then wait 2 min |
| Webhook log shows ❌ Failed | Signing secret mismatch | Update Vercel `STRIPE_WEBHOOK_SECRET` env var |
| HTTP 401 in webhook log | Invalid signature | Verify webhook secret matches Stripe dashboard |
| No Vercel logs | Function didn't execute | Check webhook URL is exactly correct |
| Transaction not in JSONL | .runtime path doesn't exist | Create: `mkdir -p .runtime/revenue` |
| /api/revenue/summary returns 500 | API error | Check Vercel function logs for specific error |

---

## NEXT STEPS AFTER COMPLETION

1. **Save all screenshots** with timestamps
2. **Document any failures** with exact error messages
3. **Create final report** with status: PASS/FAIL
4. **If FAIL:** Provide logs and screenshots for debugging
5. **If PASS:** Confirm webhook integration ready for production

---

## ESTIMATED TIME
- Total execution: 45-60 minutes
- Stripe processing: 2-3 seconds
- Dashboard refresh: 5-10 seconds
- Each phase: 5-10 minutes

---

## CRITICAL NOTES

**REAL MONEY:** This test uses LIVE Stripe keys processing a REAL $0.99 charge. The payment will succeed and money will be transferred (minus Stripe fees).

**CLEANUP:** After test completes:
- The $0.99 charge will appear in Stripe reports
- Refund manually in Stripe dashboard if needed
- Transaction will remain in logs (audit trail)

**SECURITY:** 
- Never share webhook secret or API keys
- Delete test card data after payment
- Verify HTTPS on all endpoints
- Confirm webhook signature verification on every request

---

## QUICK REFERENCE

**Stripe Dashboard URLs:**
- Webhooks: https://dashboard.stripe.com/test/webhooks
- Payments: https://dashboard.stripe.com/test/payments
- Events: https://dashboard.stripe.com/test/events

**ProfitEngine URLs:**
- Webhook endpoint: https://profitengine-tau.vercel.app/api/webhooks/stripe
- Revenue API: https://profitengine-tau.vercel.app/api/revenue/summary
- Vercel dashboard: https://vercel.com/dashboard

**Test Card:**
- 4242 4242 4242 4242 (always succeeds in test mode)

---

## REPORTING TEMPLATE

```markdown
## STRIPE WEBHOOK LIVE TEST REPORT
**Date:** [timestamp]
**Tester:** [your name]
**Status:** PASS / FAIL

### Results
- Webhook endpoint: [✅/❌]
- Configuration: [✅/❌]
- Test event: [✅/❌]
- Real charge: [✅/❌]
- System logging: [✅/❌]

### Evidence
1. [Screenshot 1]
2. [Screenshot 2]
3. [Screenshot 3]
...

### Issues (if any)
- [Issue 1]
- [Issue 2]

### Timeline
- Start: [time]
- Charge processed: [time]
- Webhook delivered: [time]
- Verified: [time]
- Total: [duration]
```

---

**End of Manual Test Guide**

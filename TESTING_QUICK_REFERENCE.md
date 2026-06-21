# ProfitEngine v5 — Testing Quick Reference Card
## For Account Owner (Stephen Franklin)

**Keep this at hand during testing**

---

## 30-Second System Check

```bash
# Health check (should return "ok": true)
curl https://profitengine-tau.vercel.app/api/health | jq .ok

# Revenue check (should return current revenue)
curl https://profitengine-tau.vercel.app/api/income | jq '.total'

# Both show errors? → check Vercel deployment status
# First shows OK, second shows error? → check OCI backend (129.146.236.177:8000)
```

---

## Test Sequence (In Order)

1. **TEST 1: Stripe Webhook** (5 min)
   - Stripe dashboard → Test Webhooks → Send test event
   - Check Vercel logs for: `✅ Payment succeeded`

2. **TEST 2: Gumroad Webhook** (5 min)
   - Gumroad dashboard → Integrations → Send test event
   - Check logs for: `Webhook received from Gumroad`

3. **TEST 3: Real Transaction** (Optional, 10 min)
   - Buy your own $0.99 test product from Gumroad
   - Verify dashboard shows $0.99

4. **TEST 4: Dashboard** (2 min)
   - Open: https://profitengine-tau.vercel.app
   - Check: Revenue displays correctly

5. **TEST 5: Health Check** (1 min)
   - Open: https://profitengine-tau.vercel.app/api/health
   - Check: All components show "✅"

6. **TEST 6: Content Publishing** (15 min)
   - Publish test article to Dev.to or other platform
   - Verify appears in public feed

---

## Webhook Setup (One-Time)

### Stripe
- URL: `https://profitengine-tau.vercel.app/api/webhooks/stripe`
- Secret: `STRIPE_WEBHOOK_SECRET` (Vercel env var)
- Events: `charge.succeeded`, `payment_intent.succeeded`, `charge.refunded`

### Gumroad
- URL: `https://profitengine-tau.vercel.app/api/webhooks/gumroad`
- Token: `GUMROAD_API_TOKEN` (Vercel env var)
- Events: `sale.created`, `sale.completed`, `refund.created`

### Dispatch
- URL: `https://profitengine-tau.vercel.app/api/webhooks/dispatch`
- Token: `PROFITENGINE_WEBHOOK_TOKEN` (Vercel env var)
- Source: CMS at alreadyherellc.com

---

## Critical Environment Variables

**Must be set in Vercel (Production env):**

```
STRIPE_SECRET_KEY         = sk_live_xxx (from Stripe dashboard)
STRIPE_WEBHOOK_SECRET     = whsec_xxx (from Stripe webhook settings)
GUMROAD_API_TOKEN         = xxx (from Gumroad account settings)
RUNTIME_API_URL           = https://api.profitengine.alreadyherellc.com
PROFITENGINE_WEBHOOK_TOKEN = xxxx (random, shared with CMS)
```

**Not in code, set on OCI server only:**

```
ANTHROPIC_API_KEY         = sk-ant-xxx (for AI features)
GITHUB_CONTENT_TOKEN      = ghp_xxx (for content publishing)
MONGO_URL                 = mongodb+srv://...
```

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| **Webhook: 401 Unauthorized** | Check webhook secret matches Stripe/Gumroad dashboard |
| **Webhook: 404 Not Found** | Check URL is exactly `https://profitengine-tau.vercel.app/api/webhooks/[name]` |
| **Dashboard: $0 revenue** | Webhooks not received yet; complete TEST 1 & TEST 2 |
| **Health check: 503 Service Unavailable** | OCI backend not running; check server logs |
| **Content won't publish** | API key wrong; verify in Vercel env vars |

---

## Important URLs

| Service | URL |
|---------|-----|
| **Dashboard** | https://profitengine-tau.vercel.app |
| **Health Check** | https://profitengine-tau.vercel.app/api/health |
| **Revenue API** | https://profitengine-tau.vercel.app/api/income |
| **Stripe Dashboard** | https://dashboard.stripe.com/test/webhooks |
| **Gumroad Dashboard** | https://app.gumroad.com/dashboard |
| **Vercel Deployment** | https://vercel.com/dashboard |
| **OCI Server** | 129.146.236.177 (requires VPN/whitelist) |

---

## Test Credentials

**Stripe Test Card:**
- Number: `4242 4242 4242 4242`
- Expiry: `12/99`
- CVC: `123`

**Gumroad Test Product:**
- Name: `Test Product — Do Not Buy`
- Price: `$0.99`
- Type: Digital

---

## Production Checklist (Before Going Live)

- [ ] All 6 tests passed
- [ ] No error messages in Vercel logs
- [ ] Health endpoint returns "ok": true
- [ ] Revenue dashboard displays data
- [ ] Content published to ≥1 platform
- [ ] SSL certificate valid (HTTPS)
- [ ] Webhook signatures validated
- [ ] API keys NOT hardcoded (all in env vars)
- [ ] FTC disclosures included (if affiliate content)
- [ ] Team notified of live status

---

## Emergency Contacts

| Issue | Action |
|-------|--------|
| **Vercel deployment down** | Check: https://status.vercel.com |
| **Stripe webhook failing** | Check: https://dashboard.stripe.com/test/webhooks → delivery status |
| **OCI server unreachable** | SSH to: `opc@129.146.236.177` → check processes |
| **Content publishing fails** | Verify API key in Vercel env vars |
| **Other issues** | File GitHub issue with error message |

---

## Monitoring Checklist (After Going Live)

**Daily:**
- [ ] Dashboard loads without errors
- [ ] Revenue updates in real-time
- [ ] No 5xx errors in Vercel logs

**Weekly:**
- [ ] Send test webhook from Stripe/Gumroad
- [ ] Publish test article to platform
- [ ] Review transaction logs

**Monthly:**
- [ ] Run full test suite: `npm run test:full`
- [ ] Audit API usage and costs
- [ ] Review security scan: `npm run security:scan`

---

**Status: READY FOR PRODUCTION**

Last Updated: 2026-06-21  
Account Owner: Stephen Franklin (dispatch@alreadyherellc.com)

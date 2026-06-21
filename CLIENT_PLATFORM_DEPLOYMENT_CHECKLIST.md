# Multi-Tenant Client Platform - Deployment Checklist

Complete this checklist before going to production. All items must be verified.

## Pre-Deployment (Development)

- [ ] All 8 API endpoints implemented and tested locally
- [ ] Client database schema verified (app/lib/client-db.ts)
- [ ] Commission calculation logic reviewed
- [ ] Webhook routing enhancement merged into Stripe handler
- [ ] UI components created (onboarding, dashboard, docs)
- [ ] TypeScript compilation passes (`npm run typecheck`)
- [ ] ESLint passes (`npm run lint`)
- [ ] Tests pass (`npm test`)

## Environment Configuration

### Required Environment Variables

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_live_...
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Commission Job Security (optional but recommended)
CRON_SECRET=your-secret-token-for-cron-jobs

# Optional: For production notifications
SENDGRID_API_KEY=...
SLACK_WEBHOOK_URL=...
```

- [ ] `STRIPE_SECRET_KEY` configured in production environment
- [ ] `STRIPE_API_KEY` configured (can be same as above)
- [ ] `STRIPE_WEBHOOK_SECRET` configured
- [ ] `CRON_SECRET` configured for scheduled jobs
- [ ] Verified no secrets hardcoded in code
- [ ] Verified all secrets are in GitHub Secrets (not in .env)

## Database & Storage

- [ ] `.runtime/` directory will be created on first run
- [ ] Verified write permissions for `.runtime/clients/`
- [ ] Verified write permissions for `.runtime/payouts/`
- [ ] Verified read permissions for transaction logs
- [ ] Plan for data backup (git backup, automated snapshots, etc.)
- [ ] Documented backup/restore procedures

## Stripe Integration

### Stripe Account Setup

- [ ] Stripe account is created and verified
- [ ] Stripe API keys are generated
- [ ] Webhook endpoint created in Stripe Dashboard:
  - [ ] Endpoint URL: `https://your-domain.com/api/webhooks/stripe`
  - [ ] Events enabled: `charge.succeeded`, `charge.failed`, `charge.refunded`
  - [ ] Signing secret saved to `STRIPE_WEBHOOK_SECRET`
- [ ] Stripe Connected Account flow available for clients
- [ ] Test mode keys available for client testing
- [ ] Production mode keys ready for go-live

### Stripe Dashboard Configuration

- [ ] Webhook endpoint is active and responding
- [ ] Webhook events are being delivered
- [ ] No webhook failures in logs
- [ ] Stripe account is in production mode
- [ ] API keys have proper permissions (charges, webhooks)

## API Endpoints - Verification

### Endpoint 1: POST /api/client/register
- [ ] Endpoint exists at `/api/client/register`
- [ ] Accepts `email` and `business_name`
- [ ] Returns `client_id`, `api_key`, and `status`
- [ ] Validates email format
- [ ] Prevents duplicate registrations
- [ ] Returns 201 on success
- [ ] Rate limiting configured (optional but recommended)

### Endpoint 2: POST /api/client/[id]/oauth-callback
- [ ] Endpoint exists with dynamic client_id
- [ ] Accepts `stripe_account_id` in format `acct_*`
- [ ] Validates Stripe account ID format
- [ ] Updates client status to `stripe_connected`
- [ ] Returns 200 on success
- [ ] Returns 404 for non-existent clients

### Endpoint 3: POST /api/client/[id]/test-transaction
- [ ] Endpoint creates real Stripe charges
- [ ] Accepts optional `amount` parameter
- [ ] Defaults to 99 cents ($0.99)
- [ ] Creates charge on client's Stripe account
- [ ] Logs transaction with correct ID
- [ ] Returns 201 on success
- [ ] Updates client status to `testing`

### Endpoint 4: GET /api/client/[id]/transaction/[txn_id]
- [ ] Endpoint retrieves transaction details
- [ ] Returns webhook delivery status
- [ ] Returns response codes from webhook
- [ ] Returns 200 on success
- [ ] Returns 404 for non-existent transactions

### Endpoint 5: POST /api/client/[id]/configure-webhook
- [ ] Endpoint accepts webhook URL
- [ ] Validates HTTPS requirement
- [ ] Stores webhook URL in client record
- [ ] Returns webhook configuration
- [ ] Returns 200 on success

### Endpoint 6: GET /api/client/[id]/configure-webhook
- [ ] Endpoint retrieves webhook configuration
- [ ] Returns current webhook URL
- [ ] Returns configured status
- [ ] Returns 200 on success

### Endpoint 7: GET /api/client/[id]/dashboard
- [ ] Endpoint returns complete dashboard data
- [ ] Includes client info
- [ ] Includes setup progress
- [ ] Includes revenue statistics
- [ ] Includes webhook logs
- [ ] Includes go-live checklist
- [ ] All calculations are correct
- [ ] Returns 200 on success

### Endpoint 8: POST /api/client/[id]/go-live
- [ ] Endpoint transitions client to production
- [ ] Requires Stripe connected
- [ ] Requires webhook URL configured
- [ ] Requires successful test transaction
- [ ] Returns 200 on success
- [ ] Returns 400 with detailed errors when prerequisites not met
- [ ] Cannot be called twice (idempotent)

## Webhook Routing - Verification

- [ ] Stripe webhook handler enhanced with multi-tenant routing
- [ ] Webhook identifies client by `stripe_account`
- [ ] Commission calculated as 2.5% of charge amount
- [ ] Client webhook URL called with full event payload
- [ ] Client webhook delivery tracked in transaction logs
- [ ] Webhook failures logged for audit
- [ ] Retry logic in place for failed webhooks
- [ ] Test webhook delivery works end-to-end

## Commission System - Verification

- [ ] Daily commission payout job endpoint exists
- [ ] Commission calculated as 2.5% of transaction amount
- [ ] Payout job runs daily at 00:00 UTC
- [ ] Payout logs created in `.runtime/payouts/`
- [ ] Commission only calculated for "succeeded" transactions
- [ ] Only live clients included in payout job
- [ ] Payout logs are auditable
- [ ] Historic commission totals retrievable

## Scheduled Jobs - Verification

### Vercel Cron Setup

If using Vercel, add to `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/jobs/commission-payout",
      "schedule": "0 0 * * *"
    }
  ]
}
```

- [ ] `vercel.json` includes cron job configuration
- [ ] Cron schedule is correct (daily at 00:00 UTC)
- [ ] CRON_SECRET environment variable set
- [ ] Cron job is authorized with CRON_SECRET
- [ ] Manual invocation works with proper auth

### Alternative: External Cron Service

If not using Vercel, set up external cron:

- [ ] External service configured (e.g., cron-job.org, AWS EventBridge)
- [ ] Service calls `/api/jobs/commission-payout` daily
- [ ] Authorization header includes CRON_SECRET
- [ ] Cron execution logged

## UI Components - Verification

### Onboarding Flow (/client/onboard)

- [ ] Page displays all 5 steps
- [ ] Form validation works
- [ ] Progress bar updates correctly
- [ ] Each step completes and advances
- [ ] API calls are successful
- [ ] Error messages display clearly
- [ ] Final success page shows client ID and API key

### Client Dashboard (/client/[id]/dashboard)

- [ ] Dashboard loads client data
- [ ] All statistics display correctly
- [ ] Setup progress shows accurate status
- [ ] Revenue totals are correct
- [ ] Transaction table shows recent events
- [ ] Webhook status displays correctly
- [ ] Go-live checklist updates correctly
- [ ] Links to next steps work

### Documentation Portal (/client/docs)

- [ ] All tabs load correctly (Quick Start, API, Webhooks, Node.js, FAQ)
- [ ] Code examples are correct
- [ ] Links work properly
- [ ] Information is accurate
- [ ] Formatting displays well on mobile

## Security - Verification

### API Key Security

- [ ] API keys generated on client registration
- [ ] API keys stored securely in client records
- [ ] API keys not logged or exposed in errors
- [ ] API keys rotatable (documented procedure)
- [ ] API keys transmitted only over HTTPS

### Webhook Security

- [ ] All webhook URLs must be HTTPS
- [ ] HTTP URLs rejected with error
- [ ] Webhook events include client identification
- [ ] Client API key included in webhook headers
- [ ] Clients validate webhook headers before processing

### Data Security

- [ ] Client email addresses not exposed in APIs
- [ ] Stripe account IDs not exposed in public responses
- [ ] Transaction details not exposed to unauthorized clients
- [ ] Payout logs access restricted
- [ ] Audit logging in place for all state changes

### CORS & Rate Limiting

- [ ] CORS configured appropriately
- [ ] Rate limiting on registration endpoint
- [ ] Rate limiting on webhook endpoint
- [ ] DDoS protection enabled (if using Vercel/CloudFlare)

## Monitoring & Logging

- [ ] All API endpoints log activity
- [ ] Webhook delivery logged with timestamps
- [ ] Commission calculations logged
- [ ] Failed transactions logged
- [ ] Errors logged with context
- [ ] Logs searchable and organized
- [ ] Log retention policy defined

### Alerting

- [ ] Alert on webhook failures
- [ ] Alert on commission payout failures
- [ ] Alert on registration spike (potential attack)
- [ ] Alert on API errors exceeding threshold
- [ ] Slack/Email notifications configured (optional)

## Documentation

- [ ] CLIENT_PLATFORM_GUIDE.md complete and accurate
- [ ] API endpoint documentation in place
- [ ] Webhook integration examples provided
- [ ] Node.js example includes error handling
- [ ] FAQ covers common issues
- [ ] Deployment instructions documented
- [ ] Troubleshooting guide created

## Testing

- [ ] All 8 endpoints pass unit tests
- [ ] Integration tests pass end-to-end
- [ ] Test suite runs successfully: `npm test`
- [ ] Load testing performed (optional)
- [ ] Edge cases tested (duplicate registration, invalid input, etc.)
- [ ] Error handling verified

### Manual Testing Checklist

Before production go-live:

1. [ ] Register test client
   ```bash
   curl -X POST https://your-domain.com/api/client/register \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "business_name": "Test Co"}'
   ```

2. [ ] Connect test Stripe account
   ```bash
   curl -X POST https://your-domain.com/api/client/[ID]/oauth-callback \
     -H "Content-Type: application/json" \
     -d '{"stripe_account_id": "acct_..."}'
   ```

3. [ ] Create test transaction
   ```bash
   curl -X POST https://your-domain.com/api/client/[ID]/test-transaction \
     -H "Content-Type: application/json" \
     -d '{"amount": 99}'
   ```

4. [ ] Configure test webhook
   ```bash
   curl -X POST https://your-domain.com/api/client/[ID]/configure-webhook \
     -H "Content-Type: application/json" \
     -d '{"webhook_url": "https://webhook.site/test"}'
   ```

5. [ ] Go live
   ```bash
   curl -X POST https://your-domain.com/api/client/[ID]/go-live \
     -H "Content-Type: application/json" \
     -d '{"confirmation": "I am ready for live customer payments"}'
   ```

6. [ ] View dashboard
   ```bash
   curl https://your-domain.com/api/client/[ID]/dashboard
   ```

7. [ ] Verify webhook delivery in transaction logs

8. [ ] Test commission payout job
   ```bash
   curl -X POST https://your-domain.com/api/jobs/commission-payout \
     -H "Authorization: Bearer YOUR_CRON_SECRET"
   ```

## Post-Deployment

### Day 1
- [ ] Monitor error logs hourly
- [ ] Verify webhook delivery working
- [ ] Test all endpoints from production
- [ ] Check commission payout logs

### Week 1
- [ ] Onboard 5-10 test clients
- [ ] Verify complete flow for each
- [ ] Monitor performance metrics
- [ ] Review security logs
- [ ] Check for any missing features

### Month 1
- [ ] Monitor client onboarding success rate
- [ ] Collect user feedback
- [ ] Optimize based on feedback
- [ ] Plan scaling improvements
- [ ] Document any bugs/fixes

## Rollback Plan

If critical issues found:

1. [ ] Keep previous deployment available for 30 days
2. [ ] Document rollback procedures
3. [ ] Have database backup strategy
4. [ ] Can revert Stripe webhook endpoint if needed
5. [ ] Client data saved independently

## Sign-Off

- [ ] Technical Lead: _________________ Date: _______
- [ ] Product Manager: _________________ Date: _______
- [ ] Security Review: _________________ Date: _______

## Deployment Command

```bash
# Verify all tests pass
npm run typecheck
npm run lint
npm test

# Build for production
npm run build

# Deploy to Vercel (if using Vercel)
vercel --prod

# Or deploy to your hosting provider
# (Follow your platform's deployment procedure)
```

## Success Criteria

Production deployment is successful when:

✅ All 8 API endpoints responding correctly
✅ Webhook routing works end-to-end
✅ Commission calculated and logged daily
✅ Clients can complete onboarding flow
✅ Dashboard displays correct statistics
✅ Zero critical errors in logs
✅ Stripe integration working
✅ All security checks passed

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Status:** [ ] Ready [ ] Pending [ ] Blocked

**Blockers (if any):**
- 
- 
- 


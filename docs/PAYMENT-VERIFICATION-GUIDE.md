# Payment Integration & Verification Guide

## ✅ Implementation Complete

All three critical components have been successfully implemented:

### 1. ✅ PostgreSQL Database Integration
- **Migration files created**: `migrations/001_create_jobs_table.sql`, `migrations/002_create_payouts_table.sql`
- **Database library**: `lib/db.ts` with connection pooling
- **API endpoints wired**: `/api/jobs` (GET/POST), `/api/jobs/[id]` (GET/PATCH)
- **Database schema**:
  - `jobs` table with margin calculation, status tracking, contractor assignment
  - `contractor_accounts` table for Stripe Connect account mapping
  - `payouts` table for transfer history and status tracking

### 2. ✅ Stripe Payment Integration with Payouts
- **PaymentIntent API**: `/api/payments/intent` (POST/GET)
- **Stripe Connect payouts**: `/api/payouts` (POST/GET)
- **Webhook handler**: `/api/webhooks/stripe` with auto-payout trigger
- **Contractor onboarding**: `getContractorOnboardingLink()` for Stripe Express account setup
- **Payout flow**: 70% of job pay goes to contractor, 30% platform fee

### 3. ✅ Contractor Payout Flow
- **Automatic payout creation** on payment success
- **Stripe Express accounts** created per contractor
- **Transfer tracking** with Stripe transfer IDs
- **Error recovery** with status logging

---

## 🚀 Production Deployment Steps

### Step 1: Choose Database Provider
Pick one:

**Option A: Vercel Postgres (Recommended)**
```bash
# Go to Vercel Dashboard → Storage → Create Postgres
# Copy connection string
# Add to Vercel Production env var: DATABASE_URL
```

**Option B: Neon PostgreSQL**
```bash
# https://console.neon.tech → Create project
# Get connection string, add to Vercel as DATABASE_URL
```

**Option C: Render PostgreSQL**
```bash
# https://render.com → Create PostgreSQL
# Get connection URL, add to Vercel as DATABASE_URL
```

### Step 2: Run Migrations
```bash
# Option 1: Via psql CLI (one-time)
psql $DATABASE_URL < migrations/001_create_jobs_table.sql
psql $DATABASE_URL < migrations/002_create_payouts_table.sql

# Option 2: Via npm script
npm run db:init

# Verify
npm run db:test
```

### Step 3: Verify Stripe Environment Variables
Confirm these exist in Vercel Production → Settings → Environment Variables:
- [ ] `STRIPE_SECRET_KEY` (from GitHub Secrets)
- [ ] `STRIPE_WEBHOOK_SECRET` (from Stripe Dashboard)
- [ ] `DATABASE_URL` (newly added)

### Step 4: Deploy to Production
```bash
# Commit changes
git add -A
git commit -m "feat: wire database and implement Stripe Connect payouts"

# Push to main (triggers Vercel auto-deployment)
git push origin main

# Monitor deployment
vercel logs
```

### Step 5: Test End-to-End Payment Flow

#### 5a. Create a Job
```bash
curl -X POST https://your-app.vercel.app/api/jobs \
  -H "Content-Type: application/json" \
  -H "x-user-id: test-user-123" \
  -d '{
    "title": "Test Job",
    "category": "Junk Removal",
    "location": "Test City",
    "pay": 350,
    "miles": 5,
    "description": "Test job for payment verification"
  }'
```

Response: Job created with `id`, `margin` calculated (350 - 5*0.72 = 346.40)

#### 5b. Accept Job (as Contractor)
```bash
curl -X PATCH https://your-app.vercel.app/api/jobs/{job_id} \
  -H "Content-Type: application/json" \
  -H "x-user-id: contractor-456" \
  -d '{"action": "accept"}'
```

Response: Job status changed to `accepted`

#### 5c. Create Payment Intent
```bash
curl -X POST https://your-app.vercel.app/api/payments/intent \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "{job_id}",
    "jobTitle": "Test Job",
    "pay": 350,
    "contractorId": "contractor-456",
    "customerEmail": "customer@example.com"
  }'
```

Response: `{ clientSecret, intentId, amount: 350 }`

#### 5d. Test Payment with Stripe Test Card
Use Stripe's test card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/26)
- CVC: Any 3 digits (e.g., 123)

Go to Stripe Dashboard → Test Mode → Payments and confirm success.

#### 5e. Verify Payout Created
```bash
curl https://your-app.vercel.app/api/payouts?contractorId=contractor-456
```

Response: Array of payouts including:
- `status: "completed"` (payout sent)
- `stripe_transfer_id` (Stripe Transfer ID)
- `amount: 245` (70% of $350)

#### 5f. Check Webhook Received
```bash
# Vercel Production Logs
vercel logs

# Look for: "✅ Payment succeeded" and "💳 Payout created"
```

---

## 📋 Checklist Before Going Live

- [ ] Database migration successful: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM jobs"`
- [ ] Stripe webhook configured: Vercel URL registered in Stripe Dashboard
- [ ] Payment test successful: Card charged, payout created
- [ ] Contractor receiving Stripe onboarding emails
- [ ] Error logs reviewed (check Vercel logs for any STRIPE_SECRET_KEY errors)
- [ ] Contractor can accept job and complete it
- [ ] Revenue tracking: 70/30 split verified in Stripe Dashboard
- [ ] All environment variables set in Vercel Production (not just Development)
- [ ] Database backup strategy configured

---

## 🔍 Monitoring in Production

### Daily Checks
```bash
# Monitor payout status
curl https://your-app.vercel.app/api/payouts?contractorId={id}

# Check API response time
curl -w "@curl-format.txt" -o /dev/null -s https://your-app.vercel.app/api/jobs
```

### Database Health
```sql
-- Active connections
SELECT datname, usename, count(*) FROM pg_stat_activity GROUP BY datname, usename;

-- Slow jobs
SELECT * FROM jobs WHERE status = 'accepted' AND accepted_at < NOW() - INTERVAL '24 hours';

-- Failed payouts
SELECT * FROM payouts WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;
```

### Vercel Monitoring
- **Deployment**: Vercel Dashboard → Deployments
- **Logs**: `vercel logs` or Dashboard → Logs
- **Performance**: Vercel Analytics (if enabled)
- **Errors**: Configure alerts for 500-level errors

---

## 🛠️ Troubleshooting

### Issue: Database Connection Failed
```
Error: ECONNREFUSED 127.0.0.1:5432
```
**Fix**: Verify DATABASE_URL in Vercel Production env vars
```bash
vercel env pull  # Download current env vars
echo $DATABASE_URL  # Confirm it's not empty
```

### Issue: Stripe Secret Key Not Available at Build Time
```
Error: STRIPE_SECRET_KEY or STRIPE_API_KEY not configured
```
**Expected**: Build-time is before env vars available. Fixed by lazy-loading Stripe in request handlers.
- Verify in production: `curl https://your-app.vercel.app/api/payments/intent` returns 400 (missing fields, not 500)

### Issue: Payout Creation Failed
```
{status: "failed", error_message: "No connected account found"}
```
**Fix**: Contractor needs to complete Stripe onboarding
```bash
# Get onboarding link for contractor
curl -X POST https://your-app.vercel.app/api/contractor/onboarding \
  -d '{"contractorId": "id", "contractorEmail": "email@test.com", "returnUrl": "https://your-app.vercel.app/work"}'
```

### Issue: Too Many Connections
```
FATAL: too many connections for role
```
**Fix**: Reduce connection pool in `lib/db.ts`
```typescript
max: 10,  // Reduce from 20
idleTimeoutMillis: 15000,  // Close idle faster
```

---

## 📞 Support

For issues:
1. Check Vercel logs: `vercel logs --tail`
2. Verify Stripe webhook deliveries: Stripe Dashboard → Webhooks
3. Review database: `psql $DATABASE_URL -c "SELECT * FROM payouts ORDER BY created_at DESC LIMIT 5"`
4. Check GitHub Actions for migration failures

---

## Next Steps

1. **Production deployment** (follow steps above)
2. **Load testing** (test with 10+ concurrent jobs)
3. **Scaling** (connection pooling, database indexing)
4. **Payout automation** (batch transfer processing)
5. **Reporting** (revenue dashboard, contractor earnings reports)

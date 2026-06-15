# PostgreSQL Database Setup Guide

## Overview

ProfitEngine uses PostgreSQL for:
- Job listings and contractor assignments
- Payment tracking and Stripe transaction records
- Contractor Stripe Connect account management
- Payout history and status tracking

## Local Development Setup

### Prerequisites
- PostgreSQL 13+ installed locally
- `psql` CLI available
- Node.js 18+

### 1. Create Local Database

```bash
# Create the profitengine database and user
createuser -P profitengine  # When prompted, enter password
createdb -O profitengine profitengine
```

### 2. Run Migrations

Option A: Using TypeScript script
```bash
DATABASE_URL="postgres://profitengine:password@localhost:5432/profitengine" \
npx ts-node scripts/init-db.ts
```

Option B: Manual migration
```bash
psql postgresql://profitengine:password@localhost:5432/profitengine < migrations/001_create_jobs_table.sql
psql postgresql://profitengine:password@localhost:5432/profitengine < migrations/002_create_payouts_table.sql
```

### 3. Set Local Environment

Create `.env.local`:
```env
DATABASE_URL="postgres://profitengine:password@localhost:5432/profitengine"
```

### 4. Verify Setup

```bash
npm run dev
# Then in another terminal:
curl http://localhost:3000/api/jobs
```

Expected response (empty array or seed data):
```json
[]
```

## Production Setup on Vercel

### Option 1: Vercel Postgres (Recommended)

1. **Create Vercel Postgres database:**
   - Go to Vercel Dashboard → Storage
   - Create → Postgres
   - Copy the connection string

2. **Add to Vercel Environment Variables:**
   ```
   Environment: Production
   Name: DATABASE_URL
   Value: postgres://user:password@host:5432/dbname
   ```

3. **Run migrations in production:**
   ```bash
   # Option A: Vercel CLI
   vercel env pull  # Download env vars
   DATABASE_URL="$(cat .env.local | grep DATABASE_URL | cut -d= -f2)" \
   npx ts-node scripts/init-db.ts

   # Option B: Manual via psql
   psql $DATABASE_URL < migrations/001_create_jobs_table.sql
   psql $DATABASE_URL < migrations/002_create_payouts_table.sql
   ```

### Option 2: Neon (PostgreSQL as a Service)

1. **Create Neon project:**
   - Go to https://console.neon.tech
   - Create new project
   - Get connection string

2. **Configure Vercel:**
   ```
   DATABASE_URL=postgres://user:password@host/dbname
   ```

3. **Run migrations:**
   ```bash
   psql $DATABASE_URL < migrations/001_create_jobs_table.sql
   psql $DATABASE_URL < migrations/002_create_payouts_table.sql
   ```

### Option 3: Render (PostgreSQL)

1. **Create Render PostgreSQL:**
   - Go to https://render.com
   - Create new PostgreSQL database
   - Get connection URL

2. **Add to Vercel:**
   ```
   DATABASE_URL=postgres://render:password@hostname/dbname
   ```

3. **Run migrations:**
   ```bash
   psql $DATABASE_URL < migrations/001_create_jobs_table.sql
   psql $DATABASE_URL < migrations/002_create_payouts_table.sql
   ```

## Connection Pooling

For production, use a connection pooling service like PgBouncer:

```env
# Vercel Postgres automatically provides pooling
# For Neon: append ?sslmode=require to connection string
DATABASE_URL="postgres://user:password@host/dbname?sslmode=require"
```

## Database Schema

### jobs table
- `id` (BIGSERIAL) - Primary key
- `title` (VARCHAR 200) - Job title
- `category` (VARCHAR 50) - Job category
- `location` (VARCHAR 200) - Job location
- `pay` (NUMERIC 10,2) - Job payment in USD
- `miles` (NUMERIC 5,2) - Distance in miles
- `margin` (NUMERIC 10,2) - Generated: pay - (miles * 0.72)
- `description` (TEXT) - Job details
- `photos` (JSONB) - Photo URLs
- `status` (VARCHAR 20) - open|accepted|completed|cancelled
- `created_by_id` (UUID) - Job poster
- `accepted_by_id` (UUID) - Contractor
- `created_at`, `accepted_at`, `completed_at` (TIMESTAMP)
- `source` (VARCHAR 50) - web|api|seed
- `notes` (TEXT) - Internal notes

### contractor_accounts table
- `contractor_id` (UUID) - Primary key
- `contractor_stripe_account` (VARCHAR 255) - Stripe Connect account ID
- `created_at`, `updated_at` (TIMESTAMP)

### payouts table
- `id` (BIGSERIAL) - Primary key
- `job_id` (BIGINT) - Foreign key → jobs
- `contractor_id` (UUID) - Foreign key → contractor_accounts
- `contractor_stripe_account` (VARCHAR 255) - Stripe account at time of payout
- `amount` (NUMERIC 10,2) - Payout amount in USD
- `currency` (VARCHAR 3) - Currency code
- `stripe_transfer_id` (VARCHAR 255) - Stripe Transfer ID
- `status` (VARCHAR 20) - pending|processing|completed|failed
- `error_message` (TEXT) - Error details if failed
- `created_at`, `completed_at` (TIMESTAMP)
- `metadata` (JSONB) - Additional data

## Verification Checklist

- [ ] Database connection works: `psql $DATABASE_URL -c "SELECT 1"`
- [ ] All migrations applied: `psql $DATABASE_URL -c "\dt"` (should see jobs, contractor_accounts, payouts tables)
- [ ] Indexes created: `psql $DATABASE_URL -c "\di"` (should see idx_jobs_*, idx_payouts_*)
- [ ] Production deployment succeeds: `vercel deploy`
- [ ] API endpoint responds: `curl https://your-app.vercel.app/api/jobs`
- [ ] Stripe webhook configured in Dashboard
- [ ] Payout testing complete (see PAYMENT-INTEGRATION-PLAN.md)

## Troubleshooting

### Connection refused
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in `.env.local`

### Migration failed
```
ERROR:  column "margin" already exists
```
- Migration already applied. Check for idempotency.
- Migrations use `IF NOT EXISTS` to prevent re-running.

### Vercel production env not available to build step
```
Error: STRIPE_SECRET_KEY or STRIPE_API_KEY not configured
```
- This is expected during build (env vars not available yet)
- Fixed by lazy-loading Stripe inside request handlers
- Verify in prod deployment that API calls work (not the build step)

### Too many connections
```
FATAL: too many connections for role
```
- Check max_connections setting: `psql $DATABASE_URL -c "SHOW max_connections"`
- Use connection pooling (Vercel Postgres includes this)
- Reduce max pool size in lib/db.ts if needed

## Monitoring

### Check active connections
```sql
SELECT datname, usename, state, count(*) FROM pg_stat_activity GROUP BY datname, usename, state;
```

### View slow queries
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

### Backup strategy
```bash
# Daily backups (schedule via cron or GitHub Actions)
pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip < backup-20260614.sql.gz | psql $DATABASE_URL
```

## Next Steps

1. Choose your hosting option (Vercel Postgres recommended)
2. Run migrations
3. Test API endpoints with curl
4. Complete Stripe payment testing (see PAYMENT-INTEGRATION-PLAN.md)
5. Deploy to production with `git push`

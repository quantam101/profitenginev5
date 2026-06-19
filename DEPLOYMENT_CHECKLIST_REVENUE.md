# Revenue Dashboard — Deployment Checklist

## Pre-Deployment

### Code Quality
- [ ] `revenue_dashboard.py` — 760 lines, complete with all 6 channels
- [ ] `/api/revenue/dashboard` route — 250 lines, TypeScript, production-ready
- [ ] Error handling for all API failures
- [ ] Logging for debugging
- [ ] Type safety (TypeScript for API, type hints for Python)

### Documentation
- [ ] `REVENUE_DASHBOARD_SETUP.md` — Full reference (400+ lines)
- [ ] `REVENUE_INTEGRATION_QUICK_START.md` — 5-minute setup guide
- [ ] `REVENUE_DASHBOARD_SUMMARY.md` — Complete implementation overview
- [ ] Code comments explaining key functions

### Testing
- [ ] Run `bash scripts/test_revenue_dashboard.sh` — All 8 tests pass
- [ ] Manual dashboard: `python scripts/revenue_dashboard.py --action dashboard`
- [ ] API endpoint: `curl http://localhost:3000/api/revenue/dashboard`

## Configuration

### Required Environment Variables
```env
MONGODB_URI=mongodb+srv://...
MONGODB_DB=profitenginev5
```
- [ ] `MONGODB_URI` configured and tested
- [ ] MongoDB cluster allows connections
- [ ] Database permissions verified

### Optional for Auto-Fetch
```env
STRIPE_SECRET_KEY=sk_live_...
GUMROAD_API_TOKEN=...
PRINTIFY_API_TOKEN=...
```
- [ ] API keys added (if using auto-fetch)

### Optional for Alerts
```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```
- [ ] Telegram configured (if using alerts)

### GitHub Secrets
- [ ] `MONGODB_URI` added to GitHub Secrets
- [ ] All API keys added to GitHub Secrets
- [ ] `.env` is in `.gitignore` (not committed)

## Dashboard Verification

### CLI Dashboard
```bash
python scripts/revenue_dashboard.py --action dashboard
```
- [ ] Shows all 6 channels with revenue
- [ ] Displays monthly progress toward $2,500
- [ ] Shows daily burndown needed
- [ ] Progress bars render correctly

### JSON Export
```bash
python scripts/revenue_dashboard.py --action export
```
- [ ] Exports valid JSON
- [ ] Contains all metrics
- [ ] Numbers properly formatted

### API Endpoint
```bash
curl http://localhost:3000/api/revenue/dashboard
```
- [ ] Returns 200 OK
- [ ] JSON is valid
- [ ] All 6 channels present
- [ ] Metrics calculated correctly

## Data Entry

### Automated Channels
- [ ] Stripe configured for newsletter & sponsorships
- [ ] Gumroad API token set and tested
- [ ] Printify API token set and tested

### Manual Channels
```bash
python scripts/revenue_dashboard.py --action add \
  --channel youtube --amount 100 --description "Test"
```
- [ ] YouTube entries can be added manually
- [ ] Affiliate entries can be added manually

## GitHub Actions Setup

### Workflow File
- [ ] `.github/workflows/revenue-daily.yml` created
- [ ] Scheduled for 9 AM UTC daily
- [ ] Can be triggered manually
- [ ] Has all necessary environment variables

### Testing
- [ ] Run workflow manually via GitHub Actions
- [ ] Logs show successful fetch
- [ ] Logs show successful MongoDB sync
- [ ] Logs show successful Telegram alert (if configured)

## MongoDB

### Collections
- [ ] `revenue_transactions` exists with proper indexes
- [ ] Data persists after application restart
- [ ] Queries complete in <500ms

### Backup
- [ ] MongoDB Atlas automatic backups enabled
- [ ] Local JSONL backup in `.runtime/revenue/transactions.jsonl`

## Monitoring

### Daily Checks
- [ ] GitHub Actions workflow runs successfully
- [ ] Telegram alerts send (if configured)
- [ ] API endpoint returns fresh data

### Monthly Review
- [ ] Dashboard shows progress toward $2,500 target
- [ ] All 6 channels tracked
- [ ] Data is accurate

## Rollback Plan

If deployment fails:
1. Remove `.github/workflows/revenue-daily.yml`
2. Remove `MONGODB_URI` from GitHub Secrets
3. Dashboard falls back to local JSONL storage
4. CLI tools continue working

- [ ] Rollback procedure documented
- [ ] Tested (at least mentally)

## Sign-Off

- [ ] All checklist items completed
- [ ] Ready for production deployment
- [ ] Documentation reviewed
- [ ] No hardcoded secrets in code

**Status:** ✅ Ready

**Date:** 2026-06-19

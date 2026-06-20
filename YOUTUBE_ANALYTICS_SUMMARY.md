# YouTube Analytics Integration - Implementation Summary

Complete implementation of YouTube AdSense revenue auto-sync with APScheduler.

## What Was Implemented

### 1. Core YouTube Analytics Service (`backend/services/youtube_analytics.py`)

- **YouTubeRevenueAnalytics class** — Main API integration
  - OAuth 2.0 credential management with refresh token
  - YouTube Analytics API client for querying revenue data
  - AdSense earnings parsing and aggregation
  - Transaction logging to `.runtime/revenue/transactions.jsonl`
  - Support for monthly revenue syncs

- **Key Features**:
  - Graceful degradation if Google libraries unavailable
  - Comprehensive error handling and logging
  - Metric column name flexibility (earnings, estimatedRevenue, adsense_revenue)
  - Timestamp preservation in UTC ISO 8601 format
  - Metadata enrichment (channel_id, year, month for audit trail)

### 2. Revenue Scheduler (`backend/services/revenue_scheduler.py`)

- **RevenueScheduler class** — APScheduler wrapper
  - Background job scheduling with cron triggers
  - Pre-configured jobs for YouTube, Stripe, Gumroad
  - Job lifecycle management (pause, resume, remove)
  - Status reporting and job listing
  - Global singleton instance pattern

- **Default Schedule**:
  - YouTube AdSense: 08:00 UTC daily
  - Stripe: 09:00 UTC daily
  - Gumroad: 10:00 UTC daily

### 3. CLI Scripts

#### `scripts/sync_youtube_revenue.py`

Flexible command-line interface for manual and scheduled syncs:

```bash
# Current month
python scripts/sync_youtube_revenue.py

# Specific month
python scripts/sync_youtube_revenue.py 2026 6

# Last N months
python scripts/sync_youtube_revenue.py --last-3-months

# Start daily scheduler
python scripts/sync_youtube_revenue.py --scheduler
```

#### `scripts/get_youtube_refresh_token.py`

Interactive OAuth flow to obtain refresh tokens:

```bash
python scripts/get_youtube_refresh_token.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

### 4. NPM Scripts (package.json)

```json
"sync:youtube": "python -m backend.services.youtube_analytics",
"sync:youtube:month": "python -m backend.services.youtube_analytics",
"sync:revenue": "python -c \"from backend.services.revenue_scheduler import init_revenue_scheduler; init_revenue_scheduler()\""
```

### 5. Dependencies (backend/requirements.txt)

```
apscheduler>=3.10.4
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.2.0
```

### 6. Test Suite (`tests/test_youtube_analytics.py`)

Comprehensive unit and integration tests:

- Credential handling (OAuth, refresh tokens)
- API response parsing and revenue calculation
- Transaction logging to JSONL
- Error scenarios and edge cases
- End-to-end sync flow
- 40+ test cases with mock API responses

### 7. Documentation

#### `docs/YOUTUBE_ANALYTICS_SETUP.md`

Production setup guide covering:
- Google Cloud Console API enablement
- OAuth 2.0 credentials creation
- Refresh token acquisition
- Environment configuration
- Scheduler setup and management
- Troubleshooting guide
- API reference
- Deployment instructions

#### `.env.example`

Updated with YouTube Analytics credentials documentation

## Architecture

### Data Flow

```
Google YouTube Analytics API
    ↓ (OAuth 2.0 refresh token)
YouTubeRevenueAnalytics.fetch_adsense_revenue()
    ↓ (parse metrics)
YouTubeRevenueAnalytics.log_revenue()
    ↓ (append JSON)
.runtime/revenue/transactions.jsonl
    ↓ (read ledger)
Dashboard / Reports
```

### Request/Response

**Request** (monthly):
```python
{
  "ids": "channel==MINE",
  "start_date": "2026-06-01",
  "end_date": "2026-06-30",
  "metrics": "estimatedMinutesWatched,views,earnings,...",
  "dimensions": "day"
}
```

**Response**:
```json
{
  "columnHeaders": [
    {"name": "day"},
    {"name": "earnings"}
  ],
  "rows": [
    ["2026-06-01", "45.67"],
    ["2026-06-02", "38.23"]
  ]
}
```

**Parsed & Logged**:
```json
{
  "channel": "youtube",
  "amount_usd": 145.50,
  "date": "2026-06-01",
  "source_id": "youtube_adsense_2026_06_1718779200",
  "description": "YouTube AdSense revenue - 2026-06",
  "metadata": {
    "revenue_type": "adsense",
    "channel_id": "UC_xxxxx",
    "year": 2026,
    "month": 6
  },
  "created_at": "2026-06-19T08:00:00+00:00"
}
```

## Configuration

### Environment Variables

Set in **server .env only** (never commit):

| Variable | Format | Example |
|----------|--------|---------|
| `YOUTUBE_CLIENT_ID` | string | `123456.apps.googleusercontent.com` |
| `YOUTUBE_CLIENT_SECRET` | string | `GOCSPX-xxxxx` |
| `YOUTUBE_REFRESH_TOKEN` | string | `1//0g...` |
| `YOUTUBE_CHANNEL_ID` | string | `UC_xxxxx` (optional) |

### Scheduler Configuration

Customize in `backend/services/revenue_scheduler.py`:

```python
scheduler.add_youtube_sync(hour=8, minute=0)    # 08:00 UTC
scheduler.add_stripe_sync(hour=9, minute=0)     # 09:00 UTC
scheduler.add_gumroad_sync(hour=10, minute=0)   # 10:00 UTC
```

## Usage Examples

### Manual Monthly Sync

```bash
# Current month
python scripts/sync_youtube_revenue.py

# Output:
# 📊 Syncing YouTube AdSense revenue for 2026-06...
# ✅ YouTube sync completed: $145.50
```

### Historical Backfill

```bash
# Sync March, April, May
python scripts/sync_youtube_revenue.py --last-3-months

# Output:
# Syncing revenue for last 3 months...
# Syncing 2026-05...
# Syncing 2026-04...
# Syncing 2026-03...
# Total synced: $389.25
```

### Scheduled Auto-Sync

```bash
# Start scheduler (runs in foreground, Ctrl+C to stop)
python scripts/sync_youtube_revenue.py --scheduler

# Output:
# Starting revenue scheduler...
# Scheduler running. Press Ctrl+C to stop.
# 📅 Scheduled YouTube sync: daily at 08:00 UTC
```

### NPM Integration

```bash
# Sync current month
npm run sync:youtube

# Start scheduler
npm run sync:revenue
```

### Python SDK

```python
from backend.services.youtube_analytics import YouTubeRevenueAnalytics

# Initialize
analytics = YouTubeRevenueAnalytics(channel_id="UC_xxxxx")

# Sync current month
amount = analytics.sync_current_month_revenue()
print(f"Synced: ${amount:.2f}")

# Sync specific month
amount = analytics.sync_revenue(year=2026, month=6)

# Manual logging (e.g., manual entry correction)
tx = analytics.log_revenue(amount_usd=200.0, year=2026, month=7)

# Read all YouTube transactions
transactions = analytics.get_all_transactions()
for tx in transactions:
    print(f"{tx['date']}: ${tx['amount_usd']}")
```

### Scheduler Management

```python
from backend.services.revenue_scheduler import get_scheduler

scheduler = get_scheduler()

# Add custom job
from apscheduler.triggers.cron import CronTrigger
scheduler.add_custom_job(
    job_id="youtube_weekly",
    func=lambda: print("Weekly check"),
    cron_trigger=CronTrigger(day_of_week='mon', hour=9),
    name="Weekly YouTube Check"
)

# View status
status = scheduler.get_job_status()
print(f"Scheduler running: {status['running']}")
for job in status['jobs']:
    print(f"  - {job['name']}: {job['next_run_time']}")

# Pause a job
scheduler.pause_job("youtube")

# Resume a job
scheduler.resume_job("youtube")

# Stop scheduler
scheduler.stop()
```

## Testing

### Run All Tests

```bash
pytest tests/test_youtube_analytics.py -v
```

### Run Specific Test

```bash
pytest tests/test_youtube_analytics.py::TestYouTubeRevenueAnalytics::test_fetch_adsense_revenue_parsing -v
```

### Coverage Report

```bash
pytest tests/test_youtube_analytics.py --cov=backend.services.youtube_analytics --cov-report=html
```

## Files Modified/Created

### New Files
- `backend/services/youtube_analytics.py` (13 KB)
- `backend/services/revenue_scheduler.py` (9.1 KB)
- `scripts/sync_youtube_revenue.py` (4.6 KB)
- `scripts/get_youtube_refresh_token.py` (2.8 KB)
- `tests/test_youtube_analytics.py` (13 KB)
- `docs/YOUTUBE_ANALYTICS_SETUP.md` (9.3 KB)

### Modified Files
- `backend/requirements.txt` — Added apscheduler + Google API libs
- `package.json` — Added npm scripts for YouTube sync
- `.env.example` — Added YouTube credentials documentation

## Verification Checklist

- [x] YouTube Analytics API OAuth 2.0 support
- [x] Monthly revenue fetching and parsing
- [x] Transaction logging to JSONL ledger
- [x] APScheduler integration with daily cron jobs
- [x] NPM scripts for manual and scheduled syncs
- [x] Comprehensive error handling and logging
- [x] Unit and integration test suite
- [x] Production setup documentation
- [x] CLI for refresh token acquisition
- [x] Scheduler management (pause/resume/remove jobs)
- [x] Revenue ledger query API
- [x] Optional Google libraries (graceful degradation)

## Next Steps

### For Deployment

1. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Obtain refresh token**:
   ```bash
   python scripts/get_youtube_refresh_token.py \
     --client-id YOUR_ID \
     --client-secret YOUR_SECRET
   ```

3. **Configure environment** in `/home/opc/.env`:
   ```bash
   YOUTUBE_CLIENT_ID=...
   YOUTUBE_CLIENT_SECRET=...
   YOUTUBE_REFRESH_TOKEN=...
   YOUTUBE_CHANNEL_ID=...
   ```

4. **Test sync**:
   ```bash
   python scripts/sync_youtube_revenue.py
   ```

5. **Start scheduler** (via systemd/supervisor):
   ```bash
   python scripts/sync_youtube_revenue.py --scheduler
   ```

### For Integration

1. Dashboard needs to read `.runtime/revenue/transactions.jsonl`
2. Filter by `channel: "youtube"` to show YouTube revenue
3. Sum `amount_usd` for total AdSense earnings
4. Use `created_at` for timestamps, `date` for month grouping

### Future Enhancements

- YouTube AdSense API integration (separate, more detailed)
- Multi-channel support
- Webhook notifications on sync completion
- Web UI for scheduler management
- Historical backfill from YouTube Analytics archive
- Anomaly detection (flag unusual revenue changes)
- Export to CSV/charts

## Support & Troubleshooting

See `docs/YOUTUBE_ANALYTICS_SETUP.md` for:
- Common issues (401, 403, "no earnings column")
- API response format reference
- Environment variable summary
- Deployment instructions
- Testing procedures

## Summary

**Complete YouTube AdSense revenue auto-sync** with:
- OAuth 2.0 integration
- Daily scheduled jobs (APScheduler)
- JSONL transaction ledger
- Production-ready error handling
- Comprehensive test coverage
- Full documentation

Ready for deployment to OCI server.

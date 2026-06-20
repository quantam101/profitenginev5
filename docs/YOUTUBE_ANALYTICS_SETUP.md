# YouTube Analytics API Setup Guide

Auto-sync AdSense revenue from YouTube Analytics API to ProfitEngine revenue ledger.

## Quick Start

### 1. Enable YouTube Analytics API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** → **Library**
4. Search for "YouTube Analytics API"
5. Click **Enable**

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth 2.0 Client ID**
3. Choose **Desktop application** as the application type
4. Click **Create**
5. Download the credentials as JSON (you'll use `client_id` and `client_secret`)

### 3. Obtain Refresh Token

The refresh token grants offline access to YouTube Analytics API. There are two ways:

#### Option A: Quick OAuth Flow (Recommended)

Run this Python script to get a refresh token:

```bash
python scripts/get_youtube_refresh_token.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

This will open your browser for authorization. After you authorize, the script prints your refresh token.

#### Option B: Manual OAuth Flow

```python
from google.auth.oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    SCOPES
)
creds = flow.run_local_server(port=0)
print(creds.refresh_token)  # Copy this value
```

### 4. Configure Environment Variables

Set these in your server `.env` file (never commit them):

```bash
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_REFRESH_TOKEN=your_refresh_token_here
YOUTUBE_CHANNEL_ID=UC_your_channel_id_here  # Optional: for reference
```

Find your channel ID:
- YouTube Studio → Settings → Channel → Channel ID

### 5. Test the Connection

```bash
# Sync current month
npm run sync:youtube

# Or with Python directly
python scripts/sync_youtube_revenue.py

# Sync specific month
python scripts/sync_youtube_revenue.py 2026 6  # June 2026

# Sync last 3 months
python scripts/sync_youtube_revenue.py --last-3-months
```

Check `.runtime/revenue/transactions.jsonl` for logged transactions:

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

### 6. Start Daily Auto-Sync Scheduler

The scheduler runs revenue syncs on a fixed schedule:

```bash
# Start scheduler (daily at 08:00 UTC for YouTube)
python scripts/sync_youtube_revenue.py --scheduler

# Or via npm
npm run sync:revenue
```

Schedule defaults:
- **YouTube AdSense**: 08:00 UTC daily
- **Stripe**: 09:00 UTC daily (when configured)
- **Gumroad**: 10:00 UTC daily (when configured)

## Architecture

### Data Flow

```
YouTube Analytics API
    ↓
youtube_analytics.py (fetch + parse)
    ↓
transactions.jsonl (JSONL ledger)
    ↓
Revenue Dashboard (frontend)
```

### Files

- **`backend/services/youtube_analytics.py`** — Core YouTube Analytics client
  - OAuth credential management
  - API query execution
  - Revenue parsing & aggregation
  - Transaction logging

- **`backend/services/revenue_scheduler.py`** — APScheduler integration
  - Job scheduling (YouTube, Stripe, Gumroad)
  - Lifecycle management (start, stop, pause, resume)
  - Status reporting

- **`scripts/sync_youtube_revenue.py`** — CLI for manual/scheduled syncs
  - Current month sync
  - Historical batch sync
  - Scheduler daemon mode

- **`tests/test_youtube_analytics.py`** — Unit & integration tests
  - Credential handling
  - API response parsing
  - Transaction logging
  - Error scenarios

### Classes

#### YouTubeRevenueAnalytics

Main class for YouTube Analytics integration.

```python
from backend.services.youtube_analytics import YouTubeRevenueAnalytics

analytics = YouTubeRevenueAnalytics(channel_id="UC_xxxxx")

# Sync current month
amount = analytics.sync_current_month_revenue()

# Sync specific month
amount = analytics.sync_revenue(year=2026, month=6)

# Manually fetch raw API data
response = analytics.fetch_analytics_data("2026-06-01", "2026-06-30")

# Parse AdSense revenue for a month
revenue_usd = analytics.fetch_adsense_revenue(year=2026, month=6)

# Log a transaction
tx = analytics.log_revenue(amount_usd=145.50, year=2026, month=6)

# Read all YouTube transactions from ledger
transactions = analytics.get_all_transactions()
```

#### RevenueScheduler

Background scheduler for periodic syncs.

```python
from backend.services.revenue_scheduler import get_scheduler

scheduler = get_scheduler()

# Add YouTube sync (daily at 08:00 UTC)
scheduler.add_youtube_sync(hour=8, minute=0)

# Start scheduler
scheduler.start()

# List scheduled jobs
jobs = scheduler.list_jobs()

# Pause a job
scheduler.pause_job("youtube")

# Resume a job
scheduler.resume_job("youtube")

# Remove a job
scheduler.remove_job("youtube")

# Stop scheduler
scheduler.stop()

# Get full status
status = scheduler.get_job_status()
```

## API Reference

### YouTube Analytics API Metrics

The YouTube Analytics API returns these revenue-related metrics:

| Metric | Description |
|--------|-------------|
| `earnings` | AdSense revenue (USD) |
| `estimatedRevenue` | Estimated YouTube revenue |
| `adsense_revenue` | Alternative AdSense column name |
| `views` | Video views |
| `estimatedMinutesWatched` | Minutes watched by viewers |

If your account doesn't expose `earnings`, check YouTube AdSense API instead (separate setup).

### Response Format

```json
{
  "columnHeaders": [
    {"name": "day", "columnType": "DIMENSION", "dataType": "STRING"},
    {"name": "earnings", "columnType": "METRIC", "dataType": "CURRENCY"},
    {"name": "views", "columnType": "METRIC", "dataType": "INTEGER"}
  ],
  "rows": [
    ["2026-06-01", "45.67", "1234"],
    ["2026-06-02", "38.23", "987"],
    ["2026-06-03", "52.10", "1456"]
  ]
}
```

## Troubleshooting

### 401 Unauthorized

**Problem**: `HttpError 401 Unauthorized`

**Solutions**:
1. Check `YOUTUBE_REFRESH_TOKEN` is valid (may have expired)
2. Re-authorize: `python scripts/get_youtube_refresh_token.py --client-id ... --client-secret ...`
3. Verify `YOUTUBE_CLIENT_ID` and `YOUTUBE_CLIENT_SECRET` are correct

### 403 Forbidden

**Problem**: `HttpError 403 Forbidden - YouTube Analytics API has not been used`

**Solutions**:
1. Enable YouTube Analytics API in Google Cloud Console
2. Wait 5-10 minutes for API to be active
3. Verify OAuth credentials have YouTube Analytics scope

### No earnings column found

**Problem**: Revenue is 0 even though YouTube shows AdSense earnings

**Solutions**:
1. Ensure your channel has AdSense enabled (YouTube Studio → Earnings → AdSense account)
2. AdSense earnings appear after 24 hours of activity
3. Try fetching a full month to get cumulative earnings
4. Check YouTube AdSense API as alternative (separate setup)

### Scheduler not starting

**Problem**: `apscheduler.schedulers.base.SchedulerAlreadyRunningError`

**Solutions**:
1. Call `scheduler.stop()` before creating a new one
2. Use global instance: `from backend.services.revenue_scheduler import get_scheduler`
3. Check logs for other errors

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `YOUTUBE_CLIENT_ID` | Yes | OAuth 2.0 Client ID from Google Console |
| `YOUTUBE_CLIENT_SECRET` | Yes | OAuth 2.0 Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | Yes | Refresh token for offline access |
| `YOUTUBE_CHANNEL_ID` | No | Channel ID for reference (metadata only) |

## Testing

Run the test suite:

```bash
# All YouTube Analytics tests
pytest tests/test_youtube_analytics.py -v

# Specific test
pytest tests/test_youtube_analytics.py::TestYouTubeRevenueAnalytics::test_fetch_adsense_revenue_parsing -v

# With coverage
pytest tests/test_youtube_analytics.py --cov=backend.services.youtube_analytics
```

## Deployment

### On OCI Server

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Set environment variables in `/home/opc/.env`:
   ```bash
   YOUTUBE_CLIENT_ID=...
   YOUTUBE_CLIENT_SECRET=...
   YOUTUBE_REFRESH_TOKEN=...
   ```

3. Start scheduler via systemd (or supervisor):
   ```bash
   python scripts/sync_youtube_revenue.py --scheduler
   ```

### On Vercel (Frontend Only)

YouTube Analytics sync runs on the backend server (OCI), not Vercel. Vercel only displays results from `.runtime/revenue/transactions.jsonl`.

## Future Enhancements

- [ ] YouTube AdSense API (separate from Analytics API, more detailed)
- [ ] Multi-channel support (sync multiple channels)
- [ ] Custom metrics export (CSV, charts)
- [ ] Anomaly detection (flag unusual revenue changes)
- [ ] Webhook notifications on sync completion
- [ ] Web UI for scheduler management
- [ ] Historical data backfill from YouTube Analytics

## References

- [YouTube Analytics API Docs](https://developers.google.com/youtube/reporting)
- [YouTube Analytics Metrics](https://developers.google.com/youtube/reporting/v1/reports_metrics)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

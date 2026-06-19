# Unified Revenue Tracking Dashboard

## Overview

This dashboard provides real-time tracking of all 6 revenue channels toward the $2,500/month target:

1. **Newsletter** ($300-500/mo) — Email sponsorships + paid subscribers (Stripe)
2. **Gumroad** ($300-500/mo) — eBooks, templates, guides (Gumroad API)
3. **Printify POD** ($800-1200/mo) — T-shirts, hoodies, prints (Printify API) [PRIMARY]
4. **YouTube AdSense** ($300-500/mo) — Video ad revenue (Manual + YouTube Analytics)
5. **Affiliate Commissions** ($300-500/mo) — Amazon Associates + partners (Manual + Tracking)
6. **Sponsorships** ($300+/mo) — Brand partnerships (Stripe + Manual)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Revenue Sources (APIs + Manual Entry)                       │
├──────────────────────────────────────────────────────────────┤
│ Stripe (Newsletter, Sponsorships) → /fetch-stripe           │
│ Gumroad eBooks → /fetch-gumroad                             │
│ Printify POD Sales → /fetch-printify                        │
│ YouTube/Affiliate → Manual entry                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │ Python Pipeline      │
        │ revenue_dashboard.py │
        └──────────────────┬───┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ↓                 ↓                 ↓
    Local Cache      MongoDB Store      Telegram Alerts
    (JSONL)         (Production)
         │                 │
         └─────────┬───────┘
                   │
                   ↓
    ┌──────────────────────────────────┐
    │ Next.js API Route                │
    │ /api/revenue/dashboard           │
    ├──────────────────────────────────┤
    │ GET → Dashboard JSON             │
    │ Real-time aggregates from MongoDB│
    └──────────────────────────────────┘
                   │
                   ↓
    ┌──────────────────────────────────┐
    │ Frontend (Dashboard UI)           │
    │ Real-time charts, progress bars  │
    │ Mobile-responsive design         │
    └──────────────────────────────────┘
```

## Installation

### 1. Install MongoDB Driver

```bash
pip install pymongo python-dotenv
```

### 2. Configure Environment Variables

Add to `.env` (or GitHub Secrets for production):

```env
# MongoDB
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true
MONGODB_DB=profitenginev5

# API Keys (for automatic fetching)
STRIPE_SECRET_KEY=sk_live_xxxxx
GUMROAD_API_TOKEN=xxxxx
PRINTIFY_API_TOKEN=xxxxx
YOUTUBE_API_KEY=xxxxx
MAILCHIMP_API_KEY=xxxxx

# Manual tracking URLs
AFFILIATE_TRACKING_URL=https://track.alreadyherellc.com

# Telegram Alerts (optional)
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx
```

### 3. Verify MongoDB Connection

Test connection and create collections:

```bash
python scripts/revenue_dashboard.py --action sync-mongodb
```

Expected output:
```
[INFO] Connected to MongoDB (profitenginev5)
[INFO] Created revenue_transactions collection with indexes
[OK] Synced 0 transactions to MongoDB
```

## Usage

### 1. View Dashboard (CLI)

```bash
python scripts/revenue_dashboard.py --action dashboard
```

Example output:
```
======================================================================
ALREADY HERE LLC — UNIFIED REVENUE DASHBOARD
======================================================================

SNAPSHOT
  Period:          2026-06
  Updated:         2026-06-19T14:30:00+00:00
  Active Channels: 4/6

TODAY & YESTERDAY
  Today:           $   158.42
  Yesterday:       $    92.15
  Week (7d):       $  1,245.60

MONTHLY PROGRESS
  Target:          $     2,500
  Actual:          $  1,842.33  (73.7%)
  Projected End:   $  2,341.15
  Days Remaining:  11
  Daily Needed:    $    60.33
  On Track:        ✓ YES

BY CHANNEL (This Month)
  👕 Printify POD
     Revenue:       $   823.50 / $1,000.00
     Progress:      ████████░░  82.4%
  📚 Gumroad eBooks
     Revenue:       $   345.25 / $400.00
     Progress:      ██████████  86.3%
  📧 Newsletter Sponsorships
     Revenue:       $   388.98 / $400.00
     Progress:      ██████████  97.2%
  🔗 Affiliate Commissions
     Revenue:       $   284.60 / $400.00
     Progress:      ███████░░░  71.2%

CUSTOMER METRICS
  LTV per Sub:     $     0.92
  Subscribers:     2,000

======================================================================
```

### 2. Export to JSON (for dashboards/reports)

```bash
python scripts/revenue_dashboard.py --action export --output reports/June_2026.json
```

Output: `reports/June_2026.json`

```json
{
  "timestamp": "2026-06-19T14:30:00+00:00",
  "period": "2026-06",
  "today_revenue": 158.42,
  "month_revenue": 1842.33,
  "monthly_progress_pct": 73.7,
  "will_hit_target": true,
  "by_channel": {
    "printify": {
      "channel": "printify",
      "total_revenue": 823.50,
      "target": 1000.0,
      "progress_pct": 82.4,
      "trend": "↗"
    },
    ...
  }
}
```

### 3. Send Telegram Alert

```bash
python scripts/revenue_dashboard.py --action telegram
```

Telegram message:
```
📊 Revenue Update — 2026-06

Today:     $158.42
Week:      $1,245.60
Month:     $1,842.33 (73.7%)

Target:    $2,500
Forecast:  $2,341.15
Status:    ✅ ON TRACK

Burndown:  $60.33/day needed
Days Left: 11

Active Channels: 4/6
LTV per Sub: $0.92
```

### 4. Add Manual Entry

For YouTube AdSense, affiliate commissions, or manual tracking:

```bash
python scripts/revenue_dashboard.py --action add \
  --channel youtube \
  --amount 125.50 \
  --description "YouTube AdSense - June earnings" \
  --date 2026-06-15
```

Or for today's date:

```bash
python scripts/revenue_dashboard.py --action add \
  --channel affiliate \
  --amount 45.00 \
  --description "Amazon Associates commission"
```

### 5. Sync Local Data to MongoDB

If using local JSONL storage initially, sync to MongoDB:

```bash
python scripts/revenue_dashboard.py --action sync-mongodb --days 90
```

This copies the last 90 days of transactions from local storage to MongoDB.

### 6. Fetch from APIs

Automatically fetch from configured APIs:

```bash
python scripts/revenue_dashboard.py --action fetch --days 30
```

This fetches:
- Last 30 days from Stripe (newsletter, sponsorships)
- Last 30 days from Gumroad (ebooks)
- Last 30 days from Printify (POD orders)

## API Endpoint

### GET /api/revenue/dashboard

Fetch real-time dashboard data from the frontend.

**Example Request:**
```bash
curl https://profitengine-tau.vercel.app/api/revenue/dashboard
```

**Response (200 OK):**
```json
{
  "timestamp": "2026-06-19T14:30:00+00:00",
  "period": "2026-06",
  "today_revenue": 158.42,
  "yesterday_revenue": 92.15,
  "week_revenue": 1245.60,
  "month_revenue": 1842.33,
  "monthly_target": 2500,
  "monthly_progress_pct": 73.7,
  "daily_goal": 83.33,
  "days_remaining": 11,
  "by_channel": {
    "printify": {
      "channel": "printify",
      "month": "2026-06",
      "total_revenue": 823.50,
      "daily_average": 61.04,
      "target": 1000.0,
      "progress_pct": 82.4,
      "rank": 1,
      "trend": "↗"
    },
    "gumroad": {
      "total_revenue": 345.25,
      "progress_pct": 86.3,
      "rank": 2
    },
    "newsletter": {
      "total_revenue": 388.98,
      "progress_pct": 97.2,
      "rank": 3
    },
    "affiliate": {
      "total_revenue": 284.60,
      "progress_pct": 71.2,
      "rank": 4
    },
    "youtube": {
      "total_revenue": 0,
      "progress_pct": 0,
      "rank": 5
    },
    "sponsorships": {
      "total_revenue": 0,
      "progress_pct": 0,
      "rank": 6
    }
  },
  "ltv_per_subscriber": 0.92,
  "estimated_subscribers": 2000,
  "daily_burndown_needed": 60.33,
  "projected_month_end": 2341.15,
  "will_hit_target": true,
  "active_channels": 4,
  "health": {
    "status": "healthy",
    "channels_responding": 4,
    "data_freshness_minutes": 0
  }
}
```

**Error Response (503):**
```json
{
  "error": "revenue_storage_not_configured",
  "message": "Revenue storage is not configured. Set MONGODB_URI to a MongoDB connection string."
}
```

## Database Schema

MongoDB collections automatically created:

### `revenue_transactions`
Individual transactions from all channels.

```json
{
  "_id": "2026-06-19_printify_ord_12345",
  "channel": "printify",
  "amount_usd": 125.50,
  "date": "2026-06-19",
  "source_id": "ord_12345",
  "description": "Printify order - t-shirt",
  "content_id": "prod_123",
  "created_at": "2026-06-19T14:30:00+00:00",
  "metadata": {
    "price": 175.00,
    "cost": 49.50,
    "items": 2
  }
}
```

**Indexes:**
- `date` — Fast daily queries
- `channel` — Channel filtering
- `[date, channel]` — Combined queries

### `revenue_daily` (future)
Pre-aggregated daily totals (for performance).

### `revenue_monthly` (future)
Pre-aggregated monthly totals.

## Scheduled Updates

### GitHub Actions Workflow

Create `.github/workflows/revenue-daily.yml`:

```yaml
name: Revenue Dashboard — Daily Update
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:

jobs:
  update-revenue:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pymongo python-dotenv requests

      - name: Fetch revenue from APIs
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
          STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
          GUMROAD_API_TOKEN: ${{ secrets.GUMROAD_API_TOKEN }}
          PRINTIFY_API_TOKEN: ${{ secrets.PRINTIFY_API_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python scripts/revenue_dashboard.py --action fetch --days 30

      - name: Sync to MongoDB
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
        run: |
          python scripts/revenue_dashboard.py --action sync-mongodb

      - name: Export dashboard
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
        run: |
          python scripts/revenue_dashboard.py --action export --output revenue_report.json

      - name: Send Telegram alert
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
        run: |
          python scripts/revenue_dashboard.py --action telegram

      - name: Commit changes
        run: |
          git config --local user.email "bot@alreadyherellc.com"
          git config --local user.name "Revenue Bot"
          git add revenue_report.json
          git commit -m "chore: update revenue dashboard" || true
          git push || true
```

## Frontend Integration

### React Component Example

```tsx
import { useEffect, useState } from 'react';

interface DashboardData {
  month_revenue: number;
  monthly_target: number;
  monthly_progress_pct: number;
  by_channel: Record<string, any>;
  will_hit_target: boolean;
  days_remaining: number;
}

export default function RevenueDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await fetch('/api/revenue/dashboard');
        const json = await res.json();
        setData(json);
      } catch (error) {
        console.error('Failed to fetch dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading revenue dashboard...</div>;
  if (!data) return <div>Error loading dashboard</div>;

  return (
    <div className="revenue-dashboard">
      <h1>Revenue Tracker</h1>

      <div className="metric">
        <h3>Monthly Progress</h3>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${data.monthly_progress_pct}%` }}
          />
        </div>
        <p>
          ${data.month_revenue.toFixed(2)} / ${data.monthly_target.toFixed(2)}
          ({data.monthly_progress_pct.toFixed(1)}%)
        </p>
      </div>

      <div className="status">
        {data.will_hit_target ? (
          <p>✅ On track to hit $2,500 target</p>
        ) : (
          <p>⚠️ Behind target — {data.days_remaining} days left</p>
        )}
      </div>

      <div className="channels">
        <h3>By Channel</h3>
        {Object.entries(data.by_channel).map(([channel, metrics]: any) => (
          <div key={channel} className="channel">
            <h4>{channel}</h4>
            <p>${metrics.total_revenue.toFixed(2)} / ${metrics.target.toFixed(2)}</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${metrics.progress_pct}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Key Metrics Explained

### Daily Revenue
Total revenue for today across all channels.

### Monthly Progress %
`(Month Revenue / $2,500 Target) × 100`
- **0-30%** — Behind, needs focus
- **30-70%** — On track
- **70-100%** — Strong progress
- **100%+** — Target exceeded

### LTV per Subscriber
`Monthly Revenue / Estimated Active Subscribers`
- Helps estimate per-customer value
- Default: 2,000 active subscribers (configurable)

### Daily Burndown Needed
`(Target - Current Month Revenue) / Days Remaining`
- Minimum daily revenue needed to hit $2,500 target
- Updates daily based on actual progress

### Projected Month End
`Current Month Revenue + (Daily Needed × Days Remaining)`
- Forecast of month-end total if trend continues

### Channel Rank
Channels ranked by monthly revenue (1 = highest).

## Troubleshooting

### "MongoDB connection failed"
- Verify `MONGODB_URI` environment variable is set
- Check MongoDB cluster allows connections from current IP
- Ensure database user has read/write permissions

### "No valid Stripe key"
- Stripe key must start with `sk_` (not `sk_test_`)
- For testing, use test keys but ensure environment variable is set

### Missing revenue data
- Run `fetch` action to pull from APIs
- Verify API tokens are valid
- Check date format in manual entries (YYYY-MM-DD)

### Telegram alerts not sending
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Test bot token via: `curl https://api.telegram.org/bot{TOKEN}/getMe`
- Ensure bot is added to the target Telegram chat

## Next Steps

1. **Set environment variables** in `.env` and GitHub Secrets
2. **Test API fetch** with: `python scripts/revenue_dashboard.py --action fetch`
3. **Configure Telegram alerts** if using Telegram notifications
4. **Set up GitHub Actions** workflow for daily updates
5. **Add frontend dashboard** using React component example above
6. **Monitor live** via `/api/revenue/dashboard` endpoint

## Files Created

```
scripts/
  └── revenue_dashboard.py (Main tracking engine — 750+ lines)

app/api/revenue/dashboard/
  └── route.ts (Next.js API endpoint — 250+ lines)

REVENUE_DASHBOARD_SETUP.md (This file)
```

## Support

For issues or feature requests related to revenue tracking, create a GitHub issue with:
- Current month revenue so far
- Active channels
- Latest error from logs

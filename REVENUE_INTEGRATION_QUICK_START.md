# Revenue Dashboard — Quick Start (5 minutes)

## TL;DR

You have a new unified revenue dashboard that tracks all 6 channels in real-time, stores in MongoDB, and exposes a JSON API.

**Files created:**
- `scripts/revenue_dashboard.py` — Python tracking engine (750+ lines)
- `app/api/revenue/dashboard/route.ts` — Next.js API endpoint
- `REVENUE_DASHBOARD_SETUP.md` — Full documentation

## Step 1: Install Python Dependencies (1 min)

```bash
pip install pymongo python-dotenv
```

## Step 2: Add Environment Variables (2 min)

Add to `.env` file in project root:

```env
# Required: MongoDB
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true
MONGODB_DB=profitenginev5

# Optional: API Keys (for auto-fetch)
STRIPE_SECRET_KEY=sk_live_xxxxx
GUMROAD_API_TOKEN=xxxxx
PRINTIFY_API_TOKEN=xxxxx

# Optional: Telegram alerts
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx
```

## Step 3: Test Dashboard (1 min)

```bash
python scripts/revenue_dashboard.py --action dashboard
```

Expected output:
```
======================================================================
ALREADY HERE LLC — UNIFIED REVENUE DASHBOARD
======================================================================

TODAY & YESTERDAY
  Today:           $   158.42
  Yesterday:       $    92.15

MONTHLY PROGRESS
  Target:          $  2,500
  Actual:          $  1,842.33  (73.7%)
  Projected End:   $  2,341.15
  On Track:        ✓ YES
```

## Step 4: Test API Endpoint (1 min)

```bash
curl http://localhost:3000/api/revenue/dashboard
```

Response:
```json
{
  "timestamp": "2026-06-19T14:30:00+00:00",
  "month_revenue": 1842.33,
  "monthly_progress_pct": 73.7,
  "will_hit_target": true,
  "by_channel": { ... }
}
```

## Common Commands

### View Dashboard
```bash
python scripts/revenue_dashboard.py --action dashboard
```

### Export to JSON
```bash
python scripts/revenue_dashboard.py --action export --output report.json
```

### Add Manual Entry (YouTube, Affiliate, etc.)
```bash
python scripts/revenue_dashboard.py --action add \
  --channel youtube \
  --amount 125.50 \
  --description "YouTube AdSense June earnings"
```

### Send Telegram Alert
```bash
python scripts/revenue_dashboard.py --action telegram
```

### Fetch from APIs
```bash
python scripts/revenue_dashboard.py --action fetch --days 30
```

## 6 Revenue Channels

| Channel | Monthly Target | Status | API |
|---------|---|---|---|
| 👕 Printify POD | $800-1200 | Live | ✓ Printify API |
| 📚 Gumroad eBooks | $300-500 | Live | ✓ Gumroad API |
| 📧 Newsletter Sponsorships | $300-500 | Live | ✓ Stripe |
| 🔗 Affiliate Commissions | $300-500 | Manual | ⚠️ Manual entry |
| 📺 YouTube AdSense | $300-500 | Manual | ⚠️ Manual entry |
| 💼 Sponsorships | $300+ | Live | ✓ Stripe |
| | | | |
| **TOTAL TARGET** | **$2,500/mo** | Live | - |

**Manual Channels:** Add with `--action add` command above.

## Key Metrics

| Metric | Meaning |
|--------|---------|
| **Today Revenue** | Revenue generated today across all channels |
| **Monthly Progress %** | How close you are to $2,500 target (100% = $2,500) |
| **Daily Needed** | Minimum revenue per day to hit target by month-end |
| **Projected End** | Forecast total at end of month if trend continues |
| **LTV per Sub** | Average lifetime value per subscriber ($0.92 = $0.92 per person) |

## API Response Format

```json
{
  "timestamp": "2026-06-19T14:30:00+00:00",
  "period": "2026-06",
  "today_revenue": 158.42,
  "month_revenue": 1842.33,
  "monthly_target": 2500,
  "monthly_progress_pct": 73.7,
  "daily_goal": 83.33,
  "days_remaining": 11,
  "by_channel": {
    "printify": {
      "total_revenue": 823.50,
      "target": 1000.0,
      "progress_pct": 82.4,
      "trend": "↗"
    },
    ...
  },
  "will_hit_target": true,
  "daily_burndown_needed": 60.33,
  "projected_month_end": 2341.15
}
```

## GitHub Actions Automation (Optional)

To run daily updates automatically, add to `.github/workflows/revenue-daily.yml`:

```yaml
name: Revenue Dashboard — Daily
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pymongo python-dotenv
      - run: python scripts/revenue_dashboard.py --action fetch
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
          STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
      - run: python scripts/revenue_dashboard.py --action telegram
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## Data Storage

All revenue data stored in MongoDB with automatic schema:

```
profitenginev5 (database)
  └── revenue_transactions (collection)
      └── {channel, amount_usd, date, source_id, description, ...}
```

Each entry indexed by date and channel for fast queries.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "MongoDB connection failed" | Set `MONGODB_URI` in `.env` |
| No revenue showing | Run `python scripts/revenue_dashboard.py --action fetch` |
| API endpoint returns 503 | Ensure `MONGODB_URI` is in GitHub Secrets |
| Telegram alert fails | Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |

## Next: Frontend Dashboard

To build a visual dashboard, fetch from `/api/revenue/dashboard` endpoint and display:

```tsx
const res = await fetch('/api/revenue/dashboard');
const data = await res.json();

// Display:
// - Progress bar: data.monthly_progress_pct
// - Channel ranking: data.by_channel sorted by total_revenue
// - Forecast: data.projected_month_end
// - Status: data.will_hit_target
```

See `REVENUE_DASHBOARD_SETUP.md` for React component example.

## Support

Questions? Check `REVENUE_DASHBOARD_SETUP.md` for:
- Full API documentation
- Database schema details
- Environment variable reference
- All command options
- Frontend integration examples

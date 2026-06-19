# Revenue Tracker for Already Here LLC

A comprehensive revenue tracking system that measures profit from all 6 monetization channels and provides real-time dashboards, ROI analysis, and Telegram alerts.

## Features

### 1. Multi-Channel Revenue Tracking
- **Newsletter** ($300-500/month) — Paid subscriber fees, sponsorship revenue
- **Gumroad** ($300-500/month) — Ebook sales, templates, guides, bundles
- **Printify** ($800-1200/month) — Print-on-demand products (t-shirts, hoodies, prints)
- **YouTube** ($300-500/month) — AdSense revenue from video content
- **Affiliate Links** ($300-500/month) — Amazon Associates, affiliate network commissions
- **Sponsorships** (Variable) — Email sponsors, brand partnerships, collaborations

### 2. Real-Time Dashboards
- Daily, weekly, monthly revenue summaries
- Revenue breakdown by channel
- Progress toward monthly targets ($2,500 goal)
- Best-performing content with ROI per hour
- Lifetime value (LTV) per subscriber
- Burndown forecast showing daily revenue needed to hit target

### 3. Data Integrations
- **Stripe API** — Payment tracking (newsletter, direct sales)
- **Gumroad API** — Product sales and license key tracking
- **Printify API** — POD order tracking with profit calculation
- **YouTube Analytics API** — AdSense revenue (optional)
- **Mailchimp API** — Subscriber metrics (optional)
- **Telegram API** — Automated daily/weekly alerts

### 4. Manual Entry & Imports
- Add revenue manually via CLI
- Import from spreadsheets
- Support for content metadata tracking

### 5. ROI & Performance Analysis
- ROI per hour of content creation
- Top-performing content by revenue
- Channel profitability comparison
- Content type conversion analysis

---

## Installation

### Requirements
- Python 3.8+
- `urllib` (standard library)
- Optional: `httpx` for enhanced API requests

### Setup

1. **Copy `.env.example` to `.env`** and add your API keys:

```bash
# Revenue Tracker API Keys
STRIPE_SECRET_KEY=sk_live_xxxxx
GUMROAD_API_TOKEN=xxxxx
GUMROAD_CREATOR_ID=alreadyhere
YOUTUBE_API_KEY=xxxxx
PRINTIFY_API_TOKEN=xxxxx
MAILCHIMP_API_KEY=xxxxx

# Telegram Alerts
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx

# Storage
CONTENT_DATABASE_PATH=.runtime/content_metrics.json
```

2. **Install optional dependencies** (for enhanced API support):

```bash
pip install httpx python-dotenv
```

---

## Usage

### CLI Commands

#### 1. View Dashboard
```bash
python scripts/revenue_tracker.py --action dashboard
```

Output:
```
=== REVENUE DASHBOARD ===
Timestamp: 2026-06-19T17:48:43.778801+00:00

DAILY SNAPSHOT
  Daily Total:  $1,214.50
  Weekly Total: $1,214.50
  Monthly Total: $1,214.50

MONTHLY PROGRESS
  Target: $2,500
  Progress: 48.6%
  Burndown: $116.86/day needed

BY CHANNEL
  GUMROAD
    Daily: $245.00
    Monthly: $245.00
    Target: $400.00
    Progress: 61.3%
    Transactions: 1
  ...
```

#### 2. Add Manual Entry
```bash
python scripts/revenue_tracker.py \
  --action add \
  --channel newsletter \
  --amount 150 \
  --description "Monthly sponsorship fee"
```

#### 3. Export Report to JSON
```bash
python scripts/revenue_tracker.py \
  --action export \
  --output revenue_report.json
```

Generates JSON file with complete metrics:
```json
{
  "timestamp": "2026-06-19T17:48:46.843423+00:00",
  "daily_total": 1214.5,
  "monthly_total": 1214.5,
  "monthly_progress_pct": 48.58,
  "by_channel": {...},
  "top_content": [...]
}
```

#### 4. Fetch from All Channels
```bash
python scripts/revenue_tracker.py --action fetch --days 30
```

Output:
```
[OK] Fetched 15 transactions from 6 channels
  stripe: 3 transactions, $450.00
  gumroad: 4 transactions, $980.00
  printify: 5 transactions, $2,900.00
  youtube: 0 transactions, $0.00
  affiliate: 2 transactions, $256.00
  sponsorships: 1 transactions, $500.00
```

#### 5. Send Telegram Alert
```bash
python scripts/revenue_tracker.py --action telegram
```

Sends formatted message to Telegram:
```
📊 Revenue Update

Daily: $1,214.50
Weekly: $1,214.50
Monthly: $1,214.50 (48.6%)

Target: $2,500.00
Burndown: $116.86/day

Top Channel: printify

Updated: 2026-06-19T17:48:43.778801+00:00
```

---

## Python API

### Basic Usage

```python
from revenue_tracker import RevenueTracker

# Initialize tracker
tracker = RevenueTracker()

# Get metrics
daily = tracker.get_daily_revenue()      # Dict[channel -> float]
weekly = tracker.get_weekly_revenue()    # Dict[channel -> float]
monthly = tracker.get_monthly_revenue()  # Dict[channel -> float]

# Generate dashboard
dashboard = tracker.generate_dashboard()
print(f"Monthly: ${dashboard.monthly_total:,.2f}")
print(f"Progress: {dashboard.monthly_progress_pct:.1f}%")
print(f"LTV/Subscriber: ${dashboard.ltv_per_subscriber:.2f}")

# Export report
tracker.export_report("output.json")

# Send alerts
tracker.send_telegram_alert()
```

### Advanced Examples

#### Add Manual Entry
```python
tracker.add_manual_entry(
    channel="sponsorships",
    amount=500.0,
    description="Q2 email sponsor payment",
    content_id="newsletter_issue_42"
)
```

#### Get Top Performing Content
```python
top_content = tracker.get_top_content(limit=10)
for content in top_content:
    print(f"{content.title}: ${content.revenue_generated} (${content.roi_per_hour:.2f}/hr)")
```

#### Fetch from Specific Channel
```python
gumroad_sales = tracker.fetch_gumroad_revenue(days=30)
for sale in gumroad_sales:
    print(f"{sale.description}: ${sale.amount_usd}")
```

#### Get Channel Metrics
```python
metrics = tracker.calculate_channel_metrics()
for channel, m in metrics.items():
    print(f"{channel}")
    print(f"  Monthly: ${m.monthly_revenue:,.2f}")
    print(f"  Target: ${m.target:,.2f}")
    print(f"  Progress: {m.progress_pct:.1f}%")
    print(f"  Avg transaction: ${m.average_transaction_value:.2f}")
```

#### Get ROI Analysis
```python
roi = tracker.get_roi_analysis()
# Returns: Dict[channel -> avg_roi_per_hour]
for channel, roi_per_hour in roi.items():
    print(f"{channel}: ${roi_per_hour:.2f}/hr")
```

---

## Integration Examples

### Daily Cron Job

Add to GitHub Actions (`.github/workflows/revenue-daily.yml`):

```yaml
name: Daily Revenue Report

on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM UTC daily

jobs:
  revenue:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run revenue tracker
        env:
          STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
          GUMROAD_API_TOKEN: ${{ secrets.GUMROAD_API_TOKEN }}
          PRINTIFY_API_TOKEN: ${{ secrets.PRINTIFY_API_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python scripts/revenue_tracker.py --action fetch
          python scripts/revenue_tracker.py --action dashboard
          python scripts/revenue_tracker.py --action export
          python scripts/revenue_tracker.py --action telegram
```

### Import from Spreadsheet

```python
import csv
from revenue_tracker import RevenueTracker

tracker = RevenueTracker()

with open("revenue_data.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        tracker.add_manual_entry(
            channel=row["Channel"],
            amount=float(row["Amount"]),
            description=row["Description"],
            content_id=row.get("Content ID")
        )

dashboard = tracker.generate_dashboard()
tracker.export_report("imported_report.json")
```

### Dashboard in Next.js Frontend

```javascript
// pages/api/revenue/dashboard.js
import { exec } from 'child_process';

export default async function handler(req, res) {
  exec('python scripts/revenue_tracker.py --action export --output /tmp/revenue.json', (error) => {
    if (error) return res.status(500).json({ error: error.message });
    
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('/tmp/revenue.json', 'utf-8'));
    res.json(data);
  });
}
```

---

## API Key Setup

### Stripe API
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Developers** → **API Keys**
3. Copy **Secret Key** (starts with `sk_live_` or `sk_test_`)
4. Add to `.env`: `STRIPE_SECRET_KEY=sk_live_xxxxx`

### Gumroad API
1. Log in to [Gumroad](https://gumroad.com)
2. Go to **Account** → **Creator Settings** → **API**
3. Copy **Access Token**
4. Add to `.env`:
   ```
   GUMROAD_API_TOKEN=xxxxx
   GUMROAD_CREATOR_ID=your_username
   ```

### Printify API
1. Go to [Printify Dashboard](https://www.printify.com)
2. Navigate to **Account** → **Connected Accounts** → **Printify API**
3. Generate API token
4. Add to `.env`: `PRINTIFY_API_TOKEN=xxxxx`

### YouTube API (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **YouTube Analytics API**
3. Create OAuth 2.0 credentials
4. Add to `.env`: `YOUTUBE_API_KEY=xxxxx`

### Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create new bot: `/newbot`
3. Copy **Bot Token**
4. Get chat ID:
   - Message your bot
   - Go to `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find `chat.id`
5. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=xxxxx
   TELEGRAM_CHAT_ID=123456789
   ```

---

## Monthly Goals Breakdown

Target: **$2,500/month**

| Channel | Target | Status | Notes |
|---------|--------|--------|-------|
| Newsletter | $300-500 | On track | Sponsorships + subscriber fees |
| Gumroad | $300-500 | Moderate | Promote ebook bundles |
| Printify | $800-1200 | Primary revenue | Focus: t-shirt & hoodie designs |
| YouTube/Aff | $300-500 | Growing | Increase upload frequency |
| Sponsorships | $300+ | Variable | 1-2 sponsors/month |
| **TOTAL** | **$2,500** | | |

---

## Data Structure

### Transaction Format (JSONL)
```json
{
  "channel": "gumroad",
  "amount_usd": 245.0,
  "timestamp": "2026-06-19T17:48:35.815817+00:00",
  "source_id": "abc123",
  "description": "Ebook: Trading Guide Vol 2",
  "content_id": "trading-guide-2",
  "metadata": {
    "product_name": "Trading Guide Vol 2",
    "buyer": "user@example.com"
  }
}
```

### Content Metrics Format (JSON)
```json
{
  "content_id": "trading-guide-2",
  "title": "Trading Guide Volume 2",
  "channel": "gumroad",
  "creation_time_hours": 40.0,
  "publish_date": "2026-06-15",
  "revenue_generated": 2450.0,
  "views": 5200,
  "clicks": 150,
  "conversions": 10,
  "roi_per_hour": 61.25
}
```

---

## Troubleshooting

### "No valid Stripe key"
- Ensure `STRIPE_SECRET_KEY` starts with `sk_live_` or `sk_test_`
- Check `.env` file is loaded
- Verify key is not expired

### Telegram alert not sending
```bash
# Debug
python -c "
import os
from revenue_tracker import RevenueTracker
print(f'Bot Token: {os.getenv(\"TELEGRAM_BOT_TOKEN\", \"NOT SET\")}')
print(f'Chat ID: {os.getenv(\"TELEGRAM_CHAT_ID\", \"NOT SET\")}')
tracker = RevenueTracker()
tracker.send_telegram_alert()
"
```

### Missing transactions
- Check `.runtime/revenue/transactions.jsonl` exists
- Verify API credentials are correct
- Check network connectivity for API calls

### LTV calculation seems wrong
- LTV uses estimated subscriber count (default: 2,000)
- Adjust calculation in `get_ltv_per_subscriber()` method
- Track actual subscriber count in content database

---

## Extending the Tracker

### Add Custom Channel

```python
def fetch_custom_channel(self, days: int = 30) -> List[RevenueEntry]:
    """Fetch from custom revenue source."""
    entries = []
    # Your logic here
    return entries
```

### Add Content Analytics

```python
def track_content_roi(self, content_id: str, hours: float, revenue: float):
    """Track ROI for a specific content piece."""
    content_data = json.loads(self.content_db_file.read_text())
    content_data[content_id] = {
        "creation_time_hours": hours,
        "revenue_generated": revenue,
        "roi_per_hour": revenue / hours if hours > 0 else 0,
    }
    self.content_db_file.write_text(json.dumps(content_data, indent=2))
```

---

## FAQ

**Q: How often should I run the tracker?**  
A: Daily via cron job (GitHub Actions recommended). Dashboard caches last 30 days.

**Q: Can I use staging API keys?**  
A: Yes, use `sk_test_*` keys for development. Switch to `sk_live_*` for production.

**Q: Where is revenue data stored?**  
A: `.runtime/revenue/transactions.jsonl` (append-only log) and `.runtime/revenue_dashboard.json` (export snapshots)

**Q: How do I reset all data?**  
A: Delete `.runtime/revenue/` directory and re-initialize with `RevenueTracker()`

**Q: Can I export historical data?**  
A: Yes, modify `load_transactions(days=365)` to get yearly data.

---

## Support

For issues or questions:
1. Check logs in `.runtime/revenue/` directory
2. Run `python scripts/revenue_tracker.py --help` for CLI options
3. Review integration examples above
4. Check API key permissions in service dashboards

---

## License

Part of ProfitEngine v5 by Already Here LLC

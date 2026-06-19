# Revenue Tracker Quick Start Guide

Get up and running with revenue tracking in 5 minutes.

## Step 1: Set Up Environment Variables

Copy the example config:
```bash
cp scripts/revenue_tracker.env.example .env
```

Edit `.env` and add your API keys (in order of priority):

**Minimum Setup (just Stripe):**
```bash
STRIPE_SECRET_KEY=sk_live_xxxxx
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx
```

**Full Setup (all 6 channels):**
```bash
STRIPE_SECRET_KEY=sk_live_xxxxx
GUMROAD_API_TOKEN=xxxxx
GUMROAD_CREATOR_ID=alreadyhere
PRINTIFY_API_TOKEN=xxxxx
YOUTUBE_API_KEY=xxxxx
MAILCHIMP_API_KEY=xxxxx
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx
```

## Step 2: Run First Report

```bash
# View dashboard
python scripts/revenue_tracker.py --action dashboard

# Export to JSON
python scripts/revenue_tracker.py --action export

# Send Telegram alert
python scripts/revenue_tracker.py --action telegram
```

Expected output:
```
=== REVENUE DASHBOARD ===
Timestamp: 2026-06-19T...

DAILY SNAPSHOT
  Daily Total:  $1,214.50
  Weekly Total: $1,214.50
  Monthly Total: $1,214.50
```

## Step 3: Add Manual Data

```bash
# Add newsletter sponsorship
python scripts/revenue_tracker.py \
  --action add \
  --channel newsletter \
  --amount 150 \
  --description "Monthly sponsorship fee"

# Add Gumroad sale
python scripts/revenue_tracker.py \
  --action add \
  --channel gumroad \
  --amount 245 \
  --description "Ebook: Trading Guide"

# Add Printify POD sale
python scripts/revenue_tracker.py \
  --action add \
  --channel printify \
  --amount 580 \
  --description "T-shirt and hoodie sales"

# Add affiliate commission
python scripts/revenue_tracker.py \
  --action add \
  --channel affiliate \
  --amount 89.50 \
  --description "Amazon Associates clicks"
```

View updated dashboard:
```bash
python scripts/revenue_tracker.py --action dashboard
```

## Step 4: Set Up Telegram Alerts

### Get Bot Token:
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`
3. Follow prompts (name, username)
4. Copy the **API Token** (looks like `123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabc`)

### Get Chat ID:
1. Message your new bot
2. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Find the `chat.id` value
4. Add both to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabc
   TELEGRAM_CHAT_ID=987654321
   ```

### Test:
```bash
python scripts/revenue_tracker.py --action telegram
```

Should receive message in Telegram with current revenue summary.

## Step 5: Set Up Daily Automation

### Option A: GitHub Actions (Recommended)

1. Add secrets to GitHub:
   - Go to repo Settings → Secrets and variables → Actions
   - Add:
     - `STRIPE_SECRET_KEY`
     - `GUMROAD_API_TOKEN`
     - `GUMROAD_CREATOR_ID`
     - `PRINTIFY_API_TOKEN`
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_CHAT_ID`

2. Workflow already exists at `.github/workflows/revenue-daily.yml`

3. It will:
   - Run daily at 8 AM UTC
   - Fetch from all channels
   - Generate dashboard
   - Send Telegram alert
   - Commit report to repo

### Option B: Local Cron

On your server:

```bash
# Edit crontab
crontab -e

# Add this line (8 AM daily):
0 8 * * * cd /path/to/profitengine-v5 && python scripts/revenue_tracker.py --action fetch --days 30 && python scripts/revenue_tracker.py --action telegram
```

### Option C: Scheduled Python Task

```python
from apscheduler.schedulers.background import BackgroundScheduler
from revenue_tracker import RevenueTracker

scheduler = BackgroundScheduler()
tracker = RevenueTracker()

def daily_report():
    tracker.fetch_all_channels(days=30)
    tracker.send_telegram_alert()

scheduler.add_job(daily_report, 'cron', hour=8, minute=0)
scheduler.start()
```

## Step 6: Monitor Progress

### Daily Check:
```bash
# Quick view
python scripts/revenue_tracker.py --action dashboard

# JSON export
python scripts/revenue_tracker.py --action export --output daily_report.json
```

### Monthly Goals (Target: $2,500):

| Channel | Target | Track Via | Notes |
|---------|--------|-----------|-------|
| Newsletter | $300-500 | Stripe | Sponsorships + subscriber fees |
| Gumroad | $300-500 | API fetch | Ebook/template sales |
| Printify | $800-1200 | API fetch | T-shirts, hoodies, prints |
| YouTube | $300-500 | Manual | AdSense revenue |
| Affiliate | $300-500 | Manual | Amazon Associates |
| Sponsorships | Variable | Manual | Email sponsors |

### Check Status:
```bash
# Show all channels with progress
python scripts/revenue_tracker.py --action dashboard

# Look for "Progress: XX.X%" for each channel
```

---

## Common Tasks

### Add Historical Data from CSV

Create `revenue_data.csv`:
```csv
Channel,Amount,Description,Date
newsletter,150.00,Sponsorship fee,2026-06-19
gumroad,245.00,Ebook sales,2026-06-19
printify,580.00,POD sales,2026-06-19
```

Import:
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
            description=row["Description"]
        )

tracker.export_report("imported.json")
```

### Create Custom Report

```python
from revenue_tracker import RevenueTracker
import json

tracker = RevenueTracker()

# Get metrics
daily = tracker.get_daily_revenue()
monthly = tracker.get_monthly_revenue()
metrics = tracker.calculate_channel_metrics()

# Custom report
report = {
    "summary": {
        "daily_total": sum(daily.values()),
        "monthly_total": sum(monthly.values()),
        "target": 2500,
    },
    "by_channel": {
        channel: {
            "daily": daily.get(channel, 0),
            "monthly": monthly.get(channel, 0),
            "transactions": m.transaction_count,
        }
        for channel, m in metrics.items()
    }
}

with open("custom_report.json", "w") as f:
    json.dump(report, f, indent=2)
```

### Query Transactions Programmatically

```python
from revenue_tracker import RevenueTracker

tracker = RevenueTracker()
transactions = tracker.load_transactions(days=30)

# Filter by channel
gumroad_sales = [tx for tx in transactions if tx.channel == "gumroad"]

# Sum by channel
by_channel = {}
for tx in transactions:
    by_channel[tx.channel] = by_channel.get(tx.channel, 0) + tx.amount_usd

# Get high-value transactions
big_sales = [tx for tx in transactions if tx.amount_usd > 500]

print(f"Total transactions: {len(transactions)}")
print(f"Gumroad sales: {len(gumroad_sales)}")
print(f"Revenue by channel: {by_channel}")
print(f"Big sales (>$500): {len(big_sales)}")
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'dotenv'"

Solution:
```bash
pip install python-dotenv
```

### Issue: "No valid Stripe key"

Check:
```bash
# See if API key is set
grep STRIPE_SECRET_KEY .env

# Verify it starts with sk_
# Should be: sk_live_xxxxx or sk_test_xxxxx
```

### Issue: Telegram alert not sending

Debug:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print(f'Token: {os.getenv(\"TELEGRAM_BOT_TOKEN\", \"NOT SET\")}')
print(f'Chat ID: {os.getenv(\"TELEGRAM_CHAT_ID\", \"NOT SET\")}')

# Test connection
from revenue_tracker import RevenueTracker
tracker = RevenueTracker()
result = tracker.send_telegram_alert()
print(f'Send result: {result}')
"
```

### Issue: No transactions showing up

Check:
```bash
# Verify transaction log exists
ls -la .runtime/revenue/transactions.jsonl

# View content
cat .runtime/revenue/transactions.jsonl
```

---

## Next Steps

1. **Set up GitHub Actions** for daily automation
2. **Add webhook** to receive real-time Stripe notifications
3. **Track content ROI** by channel
4. **Create dashboard** in Next.js frontend
5. **Archive reports** to Google Sheets for analysis

See `REVENUE_TRACKER_README.md` for detailed documentation.

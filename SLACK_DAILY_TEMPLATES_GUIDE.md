# Slack Daily Update Templates — Copy-Paste Guide

**File location:** `pipeline/slack_daily_templates.py`

Complete production-ready templates for:
- **8 AM Morning Briefing** — daily kickoff with engagement & targets
- **6 PM Evening Metrics** — end-of-day close-out with deal details
- **Sunday Weekly Summary** — 7-day aggregate & wins
- **Monthly Completion Report** — full month P&L & strategy

---

## Quick Start

### Install Dependencies
```bash
pip install aiohttp
```

### Set Environment Variables
```bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
export SLACK_REVENUE_CHANNEL="C0B8VN2S89Y"  # defaults to #revenue-ops
```

### Test All Templates (Demo Mode)
```bash
python pipeline/slack_daily_templates.py
```
Prints all templates to terminal if `SLACK_BOT_TOKEN` not set.

---

## Template 1: 8 AM Morning Briefing

**Purpose:** Daily kickoff with engagement metrics, YTD progress, pipeline status.

**Fields Required:**
| Field | Type | Example |
|-------|------|---------|
| `date_str` | str | `"2026-06-25"` |
| `opens_24h` | int | `42` |
| `clicks_24h` | int | `18` |
| `sales_24h` | int | `2` |
| `revenue_24h_usd` | float | `3500.00` |
| `ytd_revenue_usd` | float | `45000.00` |
| `ytd_target_usd` | float | `100000.00` |
| `active_leads` | int | `8` |
| `pipeline_value_usd` | float | `22500.00` |
| `status` | str | `"ON_TRACK"` or `"BEHIND"` or `"ALERT"` or `"CRITICAL"` |
| `channel` | str | Slack channel ID (optional, defaults to `#revenue-ops`) |

### Code Block — 8 AM Briefing

```python
import asyncio
from pipeline.slack_daily_templates import send_morning_briefing

async def post_8am_briefing():
    await send_morning_briefing(
        date_str="2026-06-25",
        opens_24h=42,
        clicks_24h=18,
        sales_24h=2,
        revenue_24h_usd=3500.00,
        ytd_revenue_usd=45000.00,
        ytd_target_usd=100000.00,
        active_leads=8,
        pipeline_value_usd=22500.00,
        status="ON_TRACK",
        channel="C0B8VN2S89Y",  # #revenue-ops
    )

asyncio.run(post_8am_briefing())
```

### Integration — Dashboard Data Source

Extract from `production_mesh_edge.db`:
```sql
-- Get 24h engagement stats
SELECT 
    COUNT(DISTINCT email_id) as opens_24h,
    COUNT(DISTINCT click_id) as clicks_24h,
    COUNT(DISTINCT deal_id) as sales_24h,
    SUM(deal_amount) as revenue_24h_usd
FROM analytics
WHERE created_at >= datetime('now', '-1 day');

-- Get YTD revenue
SELECT 
    SUM(deal_amount) as ytd_revenue_usd,
    (SELECT CAST(100000.00 AS FLOAT)) as ytd_target_usd
FROM analytics
WHERE created_at >= datetime('now', 'start of year');

-- Get pipeline
SELECT 
    COUNT(*) as active_leads,
    SUM(quote_value) as pipeline_value_usd
FROM leads
WHERE status = 'ACTIVE';
```

### Slack Output (Example)

```
┌─────────────────────────────────────────────────────┐
│ 🟢 DAILY BRIEFING — 2026-06-25                      │
│                                                       │
│ Good morning. 08:15 UTC — daily metrics and targets  │
│ ───────────────────────────────────────────────────  │
│                                                       │
│ 📊 ENGAGEMENT (24h)                                  │
│ Opens: 42              Clicks: 18                    │
│ Sales: 2               Revenue Collected: $3,500.00 │
│                                                       │
│ 📈 YTD PROGRESS                                      │
│ YTD Revenue: $45,000.00    YTD Target: $100,000.00  │
│ Achievement %: 45.0%       Remaining Gap: $55,000   │
│                                                       │
│ 📈 PIPELINE                                          │
│ Active Leads: 8            Total Pipeline Value: ... │
│                                                       │
│ Status: ON_TRACK | Next update: 6 PM                │
└─────────────────────────────────────────────────────┘
```

---

## Template 2: 6 PM Evening Metrics

**Purpose:** Daily close-out with deal details, sales/revenue vs. targets, pipeline update.

**Fields Required:**
| Field | Type | Example |
|-------|------|---------|
| `date_str` | str | `"2026-06-25"` |
| `opens_24h` | int | `42` |
| `clicks_24h` | int | `18` |
| `click_rate_pct` | float | `42.9` |
| `sales_24h` | int | `2` |
| `sales_target_24h` | int | `2` |
| `revenue_24h_usd` | float | `3500.00` |
| `revenue_target_24h_usd` | float | `3500.00` |
| `deals_closed_detail` | list[dict] | `[{"company": "CompanyA", "amount": 1500.00, "service": "audit"}]` |
| `leads_added` | int | `1` |
| `active_leads` | int | `8` |
| `status` | str | `"ON_TRACK"` or `"BEHIND"` or `"ALERT"` or `"CRITICAL"` |
| `channel` | str | Slack channel ID (optional) |

### Code Block — 6 PM Metrics

```python
import asyncio
from pipeline.slack_daily_templates import send_evening_metrics

async def post_6pm_metrics():
    await send_evening_metrics(
        date_str="2026-06-25",
        opens_24h=42,
        clicks_24h=18,
        click_rate_pct=42.9,
        sales_24h=2,
        sales_target_24h=2,
        revenue_24h_usd=3500.00,
        revenue_target_24h_usd=3500.00,
        deals_closed_detail=[
            {"company": "CompanyA", "amount": 1500.00, "service": "audit"},
            {"company": "CompanyB", "amount": 2000.00, "service": "drone"},
        ],
        leads_added=1,
        active_leads=8,
        status="ON_TRACK",
        channel="C0B8VN2S89Y",  # #revenue-ops
    )

asyncio.run(post_6pm_metrics())
```

### Integration — Dashboard Data Source

```sql
-- Get 24h deal details
SELECT 
    company_name as company,
    deal_amount as amount,
    service_type as service,
    closed_date
FROM deals
WHERE closed_date = DATE('now')
  AND status = 'CLOSED';

-- Get click-to-open rate
SELECT 
    CAST(COUNT(DISTINCT click_id) AS FLOAT) * 100 / 
    COUNT(DISTINCT email_id) as click_rate_pct
FROM analytics
WHERE created_at >= datetime('now', '-1 day');

-- Get leads added today
SELECT COUNT(*) as leads_added
FROM leads
WHERE created_at >= datetime('now')
  AND created_at < datetime('now', '+1 day');
```

### Slack Output (Example)

```
┌─────────────────────────────────────────────────────┐
│ 🟢 DAILY CLOSE-OUT — 2026-06-25                     │
│                                                       │
│ 18:00 UTC — end-of-day summary. Status: ON_TRACK   │
│ ───────────────────────────────────────────────────  │
│                                                       │
│ 📧 ENGAGEMENT                                        │
│ Opens: 42              Clicks: 18                    │
│ Click-to-Open Rate: 42.9%                           │
│                                                       │
│ 💰 SALES & REVENUE                                  │
│ Sales Closed: 2 / 2 (100%)                          │
│ Revenue: $3,500.00 / $3,500.00 (100%)              │
│                                                       │
│ 💸 DEALS CLOSED TODAY                               │
│   • CompanyA — $1,500.00 (audit)                    │
│   • CompanyB — $2,000.00 (drone)                    │
│                                                       │
│ 📈 PIPELINE                                          │
│ New Leads Today: 1     Active Pipeline Leads: 8     │
│                                                       │
│ Status: ON_TRACK | Next update: 8 AM tomorrow       │
└─────────────────────────────────────────────────────┘
```

---

## Template 3: Sunday Weekly Summary

**Purpose:** 7-day aggregate metrics, key wins, pipeline status, top performer.

**Fields Required:**
| Field | Type | Example |
|-------|------|---------|
| `week_end_date` | str | `"2026-06-28"` |
| `week_opens` | int | `280` |
| `week_clicks` | int | `95` |
| `week_sales` | int | `12` |
| `week_revenue_usd` | float | `21000.00` |
| `week_target_usd` | float | `20000.00` |
| `daily_avg_revenue` | float | `3000.00` |
| `leads_added_week` | int | `5` |
| `deals_detail` | list[dict] | `[{"company": "...", "amount": 1500.00, "date": "2026-06-24"}]` |
| `active_leads` | int | `12` |
| `pipeline_value_usd` | float | `35000.00` |
| `top_performer` | str (optional) | `"Alice Smith"` |
| `notes` | str (optional) | `"Strong week driven by..."` |
| `channel` | str | Slack channel ID (optional) |

### Code Block — Sunday Summary

```python
import asyncio
from pipeline.slack_daily_templates import send_weekly_summary

async def post_sunday_summary():
    await send_weekly_summary(
        week_end_date="2026-06-28",
        week_opens=280,
        week_clicks=95,
        week_sales=12,
        week_revenue_usd=21000.00,
        week_target_usd=20000.00,
        daily_avg_revenue=3000.00,
        leads_added_week=5,
        deals_detail=[
            {"company": "CompanyA", "amount": 1500.00, "date": "2026-06-24"},
            {"company": "CompanyB", "amount": 2000.00, "date": "2026-06-25"},
            {"company": "CompanyC", "amount": 1800.00, "date": "2026-06-26"},
        ],
        active_leads=12,
        pipeline_value_usd=35000.00,
        top_performer="Alice Smith",
        notes="Strong week driven by drone service adoption. One logistics deal pending.",
        channel="C0B8VN2S89Y",  # #revenue-ops
    )

asyncio.run(post_sunday_summary())
```

### Integration — Dashboard Data Source

```sql
-- Get 7-day metrics
SELECT 
    COUNT(DISTINCT email_id) as week_opens,
    COUNT(DISTINCT click_id) as week_clicks,
    COUNT(DISTINCT deal_id) as week_sales,
    SUM(deal_amount) as week_revenue_usd,
    AVG(deal_amount) as daily_avg_revenue
FROM analytics
WHERE created_at >= datetime('now', '-7 days')
  AND created_at < datetime('now');

-- Get 7-day deals
SELECT 
    company_name as company,
    deal_amount as amount,
    closed_date as date
FROM deals
WHERE closed_date >= date('now', '-7 days')
  AND status = 'CLOSED'
ORDER BY closed_date DESC;

-- Get leads added this week
SELECT COUNT(*) as leads_added_week
FROM leads
WHERE created_at >= datetime('now', '-7 days');

-- Get top performer (by deals closed this week)
SELECT 
    owner_name as top_performer
FROM deals
WHERE closed_date >= date('now', '-7 days')
  AND status = 'CLOSED'
GROUP BY owner_name
ORDER BY COUNT(*) DESC
LIMIT 1;
```

### Slack Output (Example)

```
┌─────────────────────────────────────────────────────┐
│ 📈 WEEKLY SUMMARY — Week Ending 2026-06-28          │
│                                                       │
│ Complete 7-day performance review and next-week     │
│ outlook.                                             │
│ ───────────────────────────────────────────────────  │
│                                                       │
│ 📊 ENGAGEMENT (7 days)                              │
│ Opens: 280             Clicks: 95                    │
│ Sales Closed: 12                                     │
│                                                       │
│ 💰 REVENUE PERFORMANCE                              │
│ Weekly Revenue: $21,000.00   Weekly Target: $20k   │
│ Achievement: 105%            Daily Average: $3k     │
│                                                       │
│ 💸 DEALS CLOSED THIS WEEK                           │
│   • 2026-06-24 — CompanyA — $1,500.00              │
│   • 2026-06-25 — CompanyB — $2,000.00              │
│   • 2026-06-26 — CompanyC — $1,800.00              │
│                                                       │
│ 📈 PIPELINE STATUS                                  │
│ New Leads (week): 5        Active Pipeline: 12      │
│ Total Pipeline Value: $35,000.00                    │
│                                                       │
│ ⭐ TOP PERFORMER                                    │
│ Alice Smith                                          │
│                                                       │
│ 📝 NOTES                                            │
│ Strong week driven by drone service adoption. One   │
│ logistics deal pending.                             │
└─────────────────────────────────────────────────────┘
```

---

## Template 4: Monthly Completion Report

**Purpose:** Full month P&L, financial summary, strategic outlook, 3 biggest deals.

**Fields Required:**
| Field | Type | Example |
|-------|------|---------|
| `month_year` | str | `"June 2026"` |
| `month_opens` | int | `1200` |
| `month_clicks` | int | `380` |
| `month_sales` | int | `42` |
| `month_revenue_usd` | float | `87500.00` |
| `month_target_usd` | float | `100000.00` |
| `month_spend_usd` | float | `12000.00` |
| `month_net_profit_usd` | float | `75500.00` |
| `total_leads_added` | int | `28` |
| `deals_closed_count` | int | `42` |
| `deals_detail` | list[dict] | `[{"company": "...", "amount": 5000.00, "date": "2026-06-15"}]` |
| `avg_deal_size_usd` | float | `2083.33` |
| `pipeline_value_usd` | float | `45000.00` |
| `active_leads` | int | `15` |
| `key_wins` | list[str] (optional) | `["Drone service launched — 12 jobs", "..."]` |
| `challenges` | list[str] (optional) | `["Lead scoring needs work", "..."]` |
| `next_month_focus` | str (optional) | `"Scale audit services to 5-state region"` |
| `channel` | str | Slack channel ID (optional) |

### Code Block — Monthly Report

```python
import asyncio
from pipeline.slack_daily_templates import send_monthly_report

async def post_monthly_report():
    await send_monthly_report(
        month_year="June 2026",
        month_opens=1200,
        month_clicks=380,
        month_sales=42,
        month_revenue_usd=87500.00,
        month_target_usd=100000.00,
        month_spend_usd=12000.00,
        month_net_profit_usd=75500.00,
        total_leads_added=28,
        deals_closed_count=42,
        deals_detail=[
            {"company": "BigCorp", "amount": 5000.00, "date": "2026-06-15"},
            {"company": "TechCo", "amount": 3500.00, "date": "2026-06-18"},
            {"company": "LocalBiz", "amount": 2200.00, "date": "2026-06-22"},
        ],
        avg_deal_size_usd=2083.33,
        pipeline_value_usd=45000.00,
        active_leads=15,
        key_wins=[
            "Drone service launched — 12 jobs completed",
            "Established cabling partnership with regional contractor",
            "Logistics brokerage revenue exceeded 2x target",
        ],
        challenges=[
            "Lead scoring algorithm needs refinement — false positives in finance sector",
            "Email open rates declined mid-month (platform algorithm change)",
        ],
        next_month_focus="Scale audit services to 5-state region; test YouTube content strategy.",
        channel="C0B8VN2S89Y",  # #revenue-ops
    )

asyncio.run(post_monthly_report())
```

### Integration — Dashboard Data Source

```sql
-- Get monthly metrics (adjust MONTH/YEAR as needed)
SELECT 
    COUNT(DISTINCT email_id) as month_opens,
    COUNT(DISTINCT click_id) as month_clicks,
    COUNT(DISTINCT deal_id) as month_sales,
    SUM(deal_amount) as month_revenue_usd,
    (SELECT CAST(100000.00 AS FLOAT)) as month_target_usd
FROM analytics
WHERE YEAR(created_at) = 2026 
  AND MONTH(created_at) = 6;

-- Get spend and profit
SELECT 
    SUM(spend_amount) as month_spend_usd,
    (SELECT SUM(deal_amount) FROM deals WHERE YEAR(closed_date) = 2026 AND MONTH(closed_date) = 6)
      - SUM(spend_amount) as month_net_profit_usd
FROM expenses
WHERE YEAR(created_at) = 2026 
  AND MONTH(created_at) = 6;

-- Get top 3 deals
SELECT 
    company_name as company,
    deal_amount as amount,
    closed_date as date
FROM deals
WHERE YEAR(closed_date) = 2026 
  AND MONTH(closed_date) = 6
  AND status = 'CLOSED'
ORDER BY deal_amount DESC
LIMIT 3;

-- Get leads added this month
SELECT COUNT(*) as total_leads_added
FROM leads
WHERE YEAR(created_at) = 2026 
  AND MONTH(created_at) = 6;

-- Get average deal size
SELECT 
    AVG(deal_amount) as avg_deal_size_usd
FROM deals
WHERE YEAR(closed_date) = 2026 
  AND MONTH(closed_date) = 6
  AND status = 'CLOSED';

-- Get next-month pipeline
SELECT 
    COUNT(*) as active_leads,
    SUM(quote_value) as pipeline_value_usd
FROM leads
WHERE status = 'ACTIVE'
  AND expected_close_month >= 7;
```

### Slack Output (Example)

```
┌──────────────────────────────────────────────────────┐
│ 📅 MONTHLY REPORT — June 2026                        │
│                                                        │
│ Complete monthly performance review, P&L analysis,   │
│ and next-month strategy.                             │
│ ──────────────────────────────────────────────────── │
│                                                        │
│ 📊 EXECUTIVE SUMMARY                                 │
│ Revenue: $87,500.00        Target: $100,000.00       │
│ Achievement: 87.5%         Status: 🟡 BEHIND TARGET │
│                                                        │
│ 📧 ENGAGEMENT METRICS                                │
│ Opens: 1,200               Clicks: 380               │
│ Sales Closed: 42                                      │
│                                                        │
│ 💰 FINANCIAL SUMMARY                                 │
│ Revenue: $87,500.00        Spend: $12,000.00         │
│ Net Profit: $75,500.00     ROI: 529%                 │
│                                                        │
│ 💸 DEAL METRICS                                      │
│ Deals Closed: 42           Avg Deal Size: $2,083.33 │
│ New Leads: 28                                         │
│                                                        │
│ 📈 BIGGEST DEALS                                     │
│   • BigCorp — $5,000.00 (2026-06-15)                │
│   • TechCo — $3,500.00 (2026-06-18)                 │
│   • LocalBiz — $2,200.00 (2026-06-22)               │
│                                                        │
│ 📈 PIPELINE OUTLOOK                                  │
│ Active Leads: 15           Total Pipeline Value: ... │
│                                                        │
│ ⭐ KEY WINS                                          │
│   • Drone service launched — 12 jobs completed      │
│   • Established cabling partnership with regional... │
│   • Logistics brokerage revenue exceeded 2x target  │
│                                                        │
│ ⚠️ CHALLENGES                                        │
│   • Lead scoring algorithm needs refinement ...     │
│   • Email open rates declined mid-month ...         │
│                                                        │
│ 🚀 NEXT MONTH FOCUS                                 │
│ Scale audit services to 5-state region; test       │
│ YouTube content strategy.                            │
└──────────────────────────────────────────────────────┘
```

---

## Automation — Schedule with GitHub Actions

### Setup Cron Triggers

Create `.github/workflows/daily-slack-updates.yml`:

```yaml
name: Daily Slack Updates

on:
  schedule:
    # 8 AM UTC
    - cron: '0 8 * * *'
    # 6 PM UTC
    - cron: '0 18 * * *'
    # 10 AM UTC Sunday (weekly)
    - cron: '0 10 * * 0'
    # 12 AM UTC on 1st of month (monthly)
    - cron: '0 0 1 * *'

jobs:
  morning-briefing:
    if: github.event.schedule == '0 8 * * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install aiohttp
      - run: python -c "
          import asyncio
          from pipeline.slack_daily_templates import send_morning_briefing
          from backend.dashboard import get_metrics
          
          metrics = get_metrics()
          asyncio.run(send_morning_briefing(**metrics))
        "
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_REVENUE_CHANNEL: C0B8VN2S89Y

  evening-metrics:
    if: github.event.schedule == '0 18 * * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install aiohttp
      - run: python -c "
          import asyncio
          from pipeline.slack_daily_templates import send_evening_metrics
          from backend.dashboard import get_evening_metrics
          
          metrics = get_evening_metrics()
          asyncio.run(send_evening_metrics(**metrics))
        "
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_REVENUE_CHANNEL: C0B8VN2S89Y

  weekly-summary:
    if: github.event.schedule == '0 10 * * 0'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install aiohttp
      - run: python -c "
          import asyncio
          from pipeline.slack_daily_templates import send_weekly_summary
          from backend.dashboard import get_weekly_metrics
          
          metrics = get_weekly_metrics()
          asyncio.run(send_weekly_summary(**metrics))
        "
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_REVENUE_CHANNEL: C0B8VN2S89Y

  monthly-report:
    if: github.event.schedule == '0 0 1 * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install aiohttp
      - run: python -c "
          import asyncio
          from pipeline.slack_daily_templates import send_monthly_report
          from backend.dashboard import get_monthly_metrics
          
          metrics = get_monthly_metrics()
          asyncio.run(send_monthly_report(**metrics))
        "
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_REVENUE_CHANNEL: C0B8VN2S89Y
```

---

## Field Definitions & Calculations

### Engagement Metrics
- **Opens (24h):** Unique email opens in last 24 hours
- **Clicks (24h):** Unique email clicks in last 24 hours
- **Click-to-Open Rate %:** `(clicks / opens) × 100`
- **Opens (week):** Sum of opens for all 7 days
- **Clicks (week):** Sum of clicks for all 7 days

### Sales & Revenue
- **Sales (24h):** Number of deals closed in last 24 hours
- **Revenue (24h):** Sum of deal amounts closed in last 24 hours
- **Sales Target (24h):** Daily sales goal (e.g., 2 deals)
- **Revenue Target (24h):** Daily revenue goal (e.g., $3,500)
- **Achievement %:** `(actual / target) × 100`

### Pipeline
- **Active Leads:** Count of leads with status = "ACTIVE"
- **Pipeline Value:** Sum of quote values for all active leads
- **Leads Added (day/week):** Count of leads created in that period

### Financial (Monthly)
- **Spend:** Total operational spend (marketing, salaries, etc.)
- **Net Profit:** Revenue - Spend
- **ROI %:** `(net_profit / spend) × 100`
- **Avg Deal Size:** `revenue / deals_closed`

### Status Indicators
- **ON_TRACK:** Achievement % >= 100% (or specific threshold)
- **BEHIND:** 85% <= Achievement % < 100%
- **ALERT:** 70% <= Achievement % < 85%
- **CRITICAL:** Achievement % < 70%

---

## Slack Channel IDs (Update as Needed)

| Channel | ID |
|---------|-----|
| #revenue-ops | `C0B8VN2S89Y` |
| #deals-won | `C0B8VN2RQBC` |
| #general | `C0B1XSBS2AF` |
| #sales | (use your ID) |

---

## Testing Locally (No Token Required)

All functions print to stdout if `SLACK_BOT_TOKEN` not set:

```bash
# Test 8 AM template
python -c "
import asyncio
from pipeline.slack_daily_templates import send_morning_briefing

asyncio.run(send_morning_briefing(
    date_str='2026-06-25',
    opens_24h=42,
    clicks_24h=18,
    sales_24h=2,
    revenue_24h_usd=3500.00,
    ytd_revenue_usd=45000.00,
    ytd_target_usd=100000.00,
    active_leads=8,
    pipeline_value_usd=22500.00,
))
"
```

Output:
```
[Slack/no-token] Channel C0B8VN2S89Y:
[
  {
    "type": "header",
    "text": { ... }
  },
  ...
]
```

---

## Troubleshooting

### No Message Posted
1. Check `SLACK_BOT_TOKEN` is set: `echo $SLACK_BOT_TOKEN`
2. Check bot has "chat:write" permission in Slack workspace
3. Check channel ID is correct
4. Run test locally (see above) to verify template structure

### Missing Metrics
- Ensure database query runs before calling template function
- Check database connection string
- Verify table/column names match your schema

### Status Emoji Not Showing
- Ensure Slack workspace supports emoji
- Check message posted successfully (no errors in logs)

---

## Quick Deployment Checklist

- [ ] Set `SLACK_BOT_TOKEN` in GitHub Secrets
- [ ] Set `SLACK_REVENUE_CHANNEL` in GitHub Secrets (default: `C0B8VN2S89Y`)
- [ ] Create `.github/workflows/daily-slack-updates.yml` with cron schedule
- [ ] Test locally: `python pipeline/slack_daily_templates.py`
- [ ] Create dashboard functions: `get_metrics()`, `get_evening_metrics()`, etc.
- [ ] Wire database queries to each function
- [ ] Deploy and verify first 8 AM message posts

---

## Support

For issues, check:
1. `pipeline/slack_daily_templates.py` — Template source code
2. `pipeline/slack_notifier.py` — Existing Slack integration patterns
3. Slack API docs: https://api.slack.com/reference/block-kit/blocks

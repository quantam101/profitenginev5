# ProfitEngine Upsell Intelligence System

## Overview

The **Upsell Intelligence System** is an automated scoring algorithm that identifies high-value trading clients ready for premium monetization tiers. It analyzes client trading performance metrics and recommends tier upgrades (Hybrid → White-Label → Enterprise) based on proven behavioral signals.

**Files:**
- `runtime/upsell_intelligence.py` — Core scoring engine (production-ready)
- `runtime/examples_upsell_integration.py` — Integration examples and usage patterns

---

## Tier Structure & Monetization

### Premium Tiers

| Tier | Win Rate | AUM Fee | Annual Value @ $10K | Use Case |
|------|----------|---------|-------------------|----------|
| **Free** | < 70% | None | $0 | New traders, learning |
| **Hybrid** | >= 70% | 0.50% | $50 | Reliable traders, light support |
| **White-Label** | >= 70% + score >= 50 | 1.0% | $100 | Advanced traders, premium support |
| **Enterprise** | >= 85% + consistency | 1.5% | $150 | Top performers, custom features |

---

## Scoring System (0-100 Points)

The algorithm uses **4 independent components**, each worth 0-25 points:

### 1. Win Rate Score (0-25 pts)

Measures trading consistency and profitability.

```
Score >= 85% win rate:       25 pts (Enterprise-ready)
Score >= 70% win rate:       20 pts (Hybrid-ready)
Score 50-70% win rate:       0-15 pts (Partial credit)
Score < 50% win rate:        0 pts (Not ready)
```

**Why it matters:** High win rate demonstrates profitable strategy and discipline.

### 2. Balance Growth Score (0-25 pts)

Measures account growth trajectory (7-day rolling window).

```
Growth >= 50% in 7 days:     25 pts (Exceptional growth)
Growth 25-50%:               12-24 pts (Good trajectory)
Growth 0-25%:                0-11 pts (Slow growth)
Negative growth:             0 pts (Losing money)
```

**Why it matters:** Rapid balance growth indicates high-value customers with scaling potential.

### 3. Consistency Score (0-25 pts)

Measures consecutive winning days (emotional discipline).

```
>= 5 consecutive wins:       25 pts (Very consistent)
3-4 consecutive wins:        15-20 pts (Consistent)
1-2 consecutive wins:        5-10 pts (Choppy/volatile)
0 consecutive wins:          0 pts (On losing streak)
```

**Why it matters:** Traders with consistent wins are less likely to blow up accounts and more likely to stay subscribed.

### 4. Engagement Score (0-25 pts)

Measures trading activity (trades per day).

```
>= 10 trades/day:            25 pts (High-volume, active)
5-10 trades/day:             10-20 pts (Regular activity)
1-5 trades/day:              3-9 pts (Low activity)
< 1 trade/day:               0 pts (Dormant)
```

**Why it matters:** Active traders generate more commission and are more likely to upgrade.

---

## Tier Assignment Logic

| Condition | Tier | Notes |
|-----------|------|-------|
| Win rate >= 85% + consistency >= 15 + engagement >= 15 | **Enterprise** | Top performers |
| Win rate >= 70% + base score >= 50 | **White-Label** | Advanced traders |
| Win rate >= 70% | **Hybrid** | Reliable traders |
| Win rate < 70% | **Free** | Not ready for upsell |

---

## Quick Start

### 1. Basic Usage (Command Line)

```bash
cd runtime
python upsell_intelligence.py
```

This runs the built-in example with sample data and outputs:

```
================================================================================
UPSELL INTELLIGENCE — Daily Scoring Run
================================================================================

Campaign Generated: 2024-01-15T08:30:00.123456
Total Clients Scored: 5
Pipeline Value: $2,150.00

Enterprise Candidates: 1
WHITE-LABEL CANDIDATES: 1
Hybrid Candidates: 3

ENTERPRISE CANDIDATES:
  • diana_pro (Score: 88.5/100)
    Est. Annual Value: $750.00

...
```

### 2. Programmatic Usage (Python)

```python
from runtime.upsell_intelligence import generate_daily_upsell_report

# Generate daily report
report = generate_daily_upsell_report("clients.db")

# Access candidates by tier
print(f"Enterprise: {len(report['enterprise_candidates'])} clients")
print(f"Pipeline Value: ${report['pipeline_value_usd']:,.2f}")

# Get individual candidate details
for candidate in report["enterprise_candidates"]:
    print(f"{candidate['username']}: {candidate['sales_message']}")
```

### 3. Export for Sales Team (CSV)

```python
from runtime.upsell_intelligence import UpsellScorer, export_campaign_csv

scorer = UpsellScorer("clients.db")
campaign = scorer.score_all_clients()
export_campaign_csv(campaign, "upsell_targets.csv")
```

Output CSV columns:
- `priority_rank` — Sort by this for outreach priority
- `username` — Customer name
- `tier_recommendation` — Hybrid / White-Label / Enterprise
- `base_score` — 0-100 overall score
- `estimated_upsell_value_usd` — Annual revenue potential
- `sales_message` — Personalized pitch

---

## Database Schema

The system expects a SQLite database with three tables:

### `clients` Table

```sql
CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    account_balance REAL NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_trade_at TIMESTAMP,
    subscription_tier TEXT DEFAULT 'free'
);
```

### `trades` Table

```sql
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    symbol TEXT,
    side TEXT,
    entry_price REAL,
    exit_price REAL,
    shares INTEGER,
    pnl_usd REAL,              -- Must be filled for scoring
    win BOOLEAN,               -- Must be filled for scoring
    executed_at TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
```

### `daily_snapshots` Table (Optional for Balance History)

```sql
CREATE TABLE daily_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    balance REAL,              -- Daily balance snapshot
    trade_count INTEGER,
    daily_pnl REAL,
    captured_at TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
```

---

## Integration Patterns

### Pattern 1: Daily Cron Job

Run scoring every morning at 8 AM and email results to sales team:

```bash
# crontab -e
0 8 * * * cd /app && python scripts/daily_upsell_cron.py
```

```python
# scripts/daily_upsell_cron.py
from runtime.upsell_intelligence import generate_daily_upsell_report
from runtime.upsell_email_service import send_daily_upsell_email

report = generate_daily_upsell_report()
send_daily_upsell_email("sales@alreadyherellc.com")
print(f"[{datetime.now()}] Sent upsell report to sales team")
```

### Pattern 2: FastAPI REST Endpoint

```python
# runtime/api.py
from fastapi import FastAPI
from runtime.upsell_intelligence import generate_daily_upsell_report

app = FastAPI()

@app.get("/api/sales/upsell-report")
async def get_upsell_report(tier: str = None):
    """Get daily upsell campaign by tier"""
    report = generate_daily_upsell_report()
    
    if tier == "enterprise":
        return report["enterprise_candidates"]
    elif tier == "white_label":
        return report["white_label_candidates"]
    return report

# curl http://localhost:8000/api/sales/upsell-report?tier=enterprise
```

### Pattern 3: Webhook Notification

```python
# Trigger on new trade or weekly
import httpx

async def notify_sales_team():
    report = generate_daily_upsell_report()
    
    payload = {
        "channel": "#sales",
        "text": f"Upsell Report: {len(report['enterprise_candidates'])} Enterprise leads ready",
        "blocks": [...]
    }
    
    # Send to Slack
    await httpx.post("https://hooks.slack.com/services/YOUR/WEBHOOK/URL", json=payload)
```

### Pattern 4: Mobile Dashboard Integration

```python
# Show real-time pipeline value on mobile dashboard
from runtime.mobile_dashboard_api import MobileDashboardAPI
from runtime.upsell_intelligence import generate_daily_upsell_report

class EnhancedMobileDashboard(MobileDashboardAPI):
    
    @app.get("/api/sales/pipeline")
    async def get_sales_pipeline(self):
        """Get upsell pipeline for sales dashboard"""
        report = generate_daily_upsell_report()
        return {
            "total_pipeline_usd": report["pipeline_value_usd"],
            "enterprise_leads": report["enterprise_count"],
            "white_label_leads": report["white_label_count"],
            "hybrid_leads": report["hybrid_count"],
        }
```

---

## Configuration & Thresholds

All scoring thresholds can be customized by editing `UpsellScorer` class:

```python
class UpsellScorer:
    # Tier Thresholds
    MIN_WIN_RATE_HYBRID = 0.70          # 70% for Hybrid tier
    MIN_WIN_RATE_ENTERPRISE = 0.85      # 85% for Enterprise tier
    MIN_BALANCE_GROWTH_7D = 0.50        # 50% growth required
    MIN_CONSECUTIVE_WINS = 5            # Days
    MIN_DAILY_TRADES = 10               # Engagement threshold
    MIN_ACCOUNT_AGE_DAYS = 7            # Must be active 1 week

    # Monetization Tier Pricing (annual)
    HYBRID_AUM_FEE_BPS = 50             # 0.50% annually
    WHITE_LABEL_AUM_FEE_BPS = 100       # 1.0% annually
    ENTERPRISE_AUM_FEE_BPS = 150        # 1.5% annually
```

Adjust these based on your product strategy and customer base.

---

## Running the Examples

```bash
# Run all integration examples with test data
python runtime/examples_upsell_integration.py

# Creates test_clients.db with 5 sample traders:
#   - alice_trader (88% win rate, Hybrid candidate)
#   - bob_scalper (90% win rate, White-Label candidate)
#   - charlie_swing (50% win rate, Free tier)
#   - diana_pro (86% win rate, Enterprise candidate)
#   - eve_newbie (40% win rate, Free tier)
```

Output includes:

1. **Setup Test Database** — Creates sample trading clients
2. **Basic Scoring** — Shows tier breakdown and pipeline value
3. **Detailed Breakdown** — Shows scoring math for top candidate
4. **CSV Export** — Generates `upsell_campaign_example.csv`
5. **Cron Integration** — Code example for scheduled jobs
6. **FastAPI Integration** — REST endpoint example
7. **Email Integration** — Daily email to sales team
8. **Scoring Reference** — Detailed tier thresholds

---

## Output Formats

### JSON Report (REST API)

```json
{
  "generated_at": "2024-01-15T08:30:00",
  "total_clients": 5,
  "pipeline_value_usd": 2150.00,
  "enterprise_count": 1,
  "white_label_count": 1,
  "hybrid_count": 3,
  "enterprise_candidates": [
    {
      "client_id": "client_004",
      "username": "diana_pro",
      "base_score": 88.5,
      "win_rate_score": 25.0,
      "growth_score": 20.5,
      "consistency_score": 25.0,
      "engagement_score": 18.0,
      "tier_recommendation": "enterprise",
      "estimated_upsell_value_usd": 750.00,
      "priority_rank": 1,
      "signals": [
        ["high_win_rate", "Enterprise-tier win rate: 86.0%"],
        ["consistency", "5 consecutive winning days"]
      ],
      "sales_message": "Hi diana_pro,\n\nYour trading performance is exceptional..."
    }
  ]
}
```

### CSV Export (Sales Team)

```csv
priority_rank,username,client_id,tier_recommendation,base_score,estimated_upsell_value_usd,sales_message
1,diana_pro,client_004,enterprise,88.5,$750.00,Hi diana_pro, Your trading performance is exceptional...
2,bob_scalper,client_002,white_label,82.0,$250.00,Hi bob_scalper, You've achieved 90.0% win rate...
3,alice_trader,client_001,hybrid,70.5,$50.00,Hi alice_trader, Your 88.0% win rate shows strong...
```

---

## Common Use Cases

### Use Case 1: Daily Sales Outreach (Email Blast)

```python
# Send personalized emails to enterprise candidates every morning
report = generate_daily_upsell_report()

for candidate in report["enterprise_candidates"]:
    email = f"""
    To: {candidate['username']}@profitengine.com
    Subject: Your Trading Performance is Exceptional
    
    {candidate['sales_message']}
    
    Schedule a call: https://calendly.com/sales/30min
    """
    send_email(email)
```

### Use Case 2: Sales Dashboard (Real-Time Pipeline)

```python
# Display upsell pipeline on sales dashboard
report = generate_daily_upsell_report()

dashboard_data = {
    "total_mrr_potential": report["pipeline_value_usd"] / 12,  # Monthly recurring
    "enterprise_opportunities": report["enterprise_count"],
    "conversion_target": report["enterprise_count"] * 0.50,      # 50% conversion
    "revenue_at_50pct": (report["pipeline_value_usd"] / 12) * 0.50,
}
```

### Use Case 3: Account-Based Marketing (ABM)

```python
# Create ABM campaigns for enterprise tier clients
enterprise_leads = report["enterprise_candidates"]

for lead in enterprise_leads:
    # Create LinkedIn outreach campaign
    create_linkedin_campaign(lead["username"], lead["client_id"])
    
    # Add to Salesforce
    create_salesforce_lead(
        name=lead["username"],
        account_value=lead["estimated_upsell_value_usd"],
        tier=lead["tier_recommendation"]
    )
```

### Use Case 4: Churn Prevention

```python
# Monitor clients who fall below thresholds
report = generate_daily_upsell_report()

for candidate in report["hybrid_candidates"]:
    if candidate["base_score"] < 50:
        # At risk of churning
        send_retention_email(
            candidate["username"],
            message="We noticed your win rate dipped. Let's discuss strategy adjustments."
        )
```

---

## Best Practices

### 1. Update Daily

Run scoring once per day (morning recommended) to ensure fresh data for sales team.

```bash
0 8 * * * python -m runtime.upsell_intelligence
```

### 2. Verify Data Quality

Before scoring, ensure:
- All trades have `pnl_usd` and `win` fields populated
- `executed_at` timestamps are accurate
- Client `created_at` is set
- `account_balance` is up-to-date

### 3. Personalize Sales Messages

The system generates templated messages. Customize them for your voice:

```python
# Override sales messages by tier
SALES_TEMPLATES = {
    "enterprise": "Your trading edge is remarkable. Let's discuss ...",
    "white_label": "You're crushing it. Ready to ...",
    "hybrid": "Great progress! Interested in ...",
}
```

### 4. Monitor Conversion Rates

Track which tiers convert best:

```
Enterprise: X% conversion → $Y revenue
White-Label: X% conversion → $Y revenue
Hybrid: X% conversion → $Y revenue
```

Adjust targeting accordingly.

### 5. Seasonal Adjustments

Adjust thresholds during market volatility:

```python
# Crisis mode: lower win rate threshold
if market_regime == "CRISIS":
    MIN_WIN_RATE_HYBRID = 0.60  # Easier to qualify
    MIN_BALANCE_GROWTH_7D = 0.25  # Growth harder in bear market
```

---

## Troubleshooting

### Issue: "No candidates found"

**Check:**
1. Database has trades with `pnl_usd` and `win` populated
2. Client accounts are > 7 days old
3. Thresholds are not too strict

### Issue: "Pipeline value seems low"

**Check:**
1. Account balances are realistic
2. No data truncation happening
3. AUM fee percentages are correct

### Issue: "Scores not changing day-to-day"

**Check:**
1. New trades are being recorded
2. `executed_at` timestamps are current
3. Daily snapshots are being captured

---

## Advanced Features

### Feature 1: Custom Scoring Weights

```python
class CustomUpsellScorer(UpsellScorer):
    def _score_client(self, metrics):
        score = super()._score_client(metrics)
        
        # Boost score for high-balance accounts
        if float(metrics.account_balance) > 50000:
            score.base_score *= 1.1
        
        return score
```

### Feature 2: Cohort Analysis

```python
# Score by cohort (e.g., by registration date or strategy)
def score_cohort(cohort_name: str):
    conn = sqlite3.connect("clients.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT client_id FROM clients WHERE cohort = ?",
        (cohort_name,)
    )
    # ... score this cohort
```

### Feature 3: A/B Testing Sales Messages

```python
# Test different messaging for white-label tier
variant_a = "You've proven yourself. Enterprise tier awaits."
variant_b = "Your win rate qualifies you for white-label features."

# Randomly assign to candidates and track conversion
```

---

## API Reference

### `generate_daily_upsell_report(db_path: str) -> Dict`

Generate complete daily upsell report.

**Returns:**
```python
{
    "generated_at": str,
    "total_clients": int,
    "pipeline_value_usd": float,
    "enterprise_count": int,
    "white_label_count": int,
    "hybrid_count": int,
    "enterprise_candidates": List[Dict],
    "white_label_candidates": List[Dict],
    "hybrid_candidates": List[Dict],
}
```

### `UpsellScorer.score_all_clients() -> UpsellCampaign`

Score all clients and return campaign object.

**Returns:** `UpsellCampaign` with sorted candidates by tier.

### `export_campaign_csv(campaign: UpsellCampaign, output_path: str)`

Export campaign to CSV for CRM import.

---

## Support & Questions

For issues or feature requests:
1. Check `/examples_upsell_integration.py` for usage examples
2. Review scoring thresholds in `upsell_intelligence.py`
3. Verify database schema matches expected format
4. Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`

---

## Version History

- **v1.0.0** (2024-01-15) — Initial release with 4-component scoring system
  - Win Rate, Balance Growth, Consistency, Engagement scores
  - 3 premium tiers: Hybrid, White-Label, Enterprise
  - CSV export and REST API ready

---

## License

Part of ProfitEngine v5 trading platform.

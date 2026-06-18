# Tier Upgrade System — Quick Reference

## 5-Minute Quick Start

### Installation

```bash
pip install stripe>=12.0.0
export STRIPE_API_KEY=sk_live_YOUR_KEY
```

### Initialize

```python
from payment_processor import StripePaymentProcessor
processor = StripePaymentProcessor()
# Database tables auto-created
```

### Run Daily Cycle

```python
from tier_upgrade_automation import daily_upgrade_cycle
results = daily_upgrade_cycle()
print(f"Upgrades: {results['upgrades_processed']}")
```

---

## API Endpoints Cheat Sheet

### Get Subscription Status

```bash
curl -H "X-API-Key: YOUR_KEY" \
  "http://localhost:8000/api/billing/subscription?client_id=CLIENT-001"
```

Response:
```json
{
  "current_tier": "white_label",
  "monthly_charge_usd": 125.00,
  "next_billing_date": "2024-07-01"
}
```

### Request Tier Upgrade

```bash
curl -X POST -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"client_id":"CLIENT-001","target_tier":"enterprise"}' \
  http://localhost:8000/api/billing/upgrade
```

### Admin: Get Revenue Report

```bash
curl -H "X-Admin-API-Key: ADMIN_KEY" \
  "http://localhost:8000/api/admin/revenue-report?year_month=2024-06"
```

Response:
```json
{
  "period": "2024-06",
  "mrr_usd": 12500.00,
  "total_charges_usd": 10500.00,
  "net_revenue_usd": 12105.00
}
```

---

## Python Code Examples

### Upgrade Client

```python
from payment_processor import StripePaymentProcessor
from decimal import Decimal

processor = StripePaymentProcessor()

result = processor.upgrade_client_tier(
    client_id="CLIENT-001",
    username="alice_trader",
    new_tier="white_label",
    account_balance=Decimal("150000.00")
)

print(f"Monthly charge: ${result['monthly_charge_usd']:.2f}")
```

### Process Monthly Charges

```python
processor = StripePaymentProcessor()
results = processor.process_monthly_charges()
print(f"Success: {results['successful']}/{results['total_attempted']}")
```

### Get Revenue Report

```python
report = processor.generate_revenue_report("2024-06")
print(f"MRR: ${report['mrr_usd']:.2f}")
print(f"Tier breakdown: {report['tier_breakdown']}")
```

### Get Billing History

```python
history = processor.get_billing_history(
    client_id="CLIENT-001",
    limit=50
)

for entry in history:
    print(f"{entry['created_at']}: ${entry['total_usd']:.2f} ({entry['status']})")
```

### Run Daily Upgrade Cycle

```python
from tier_upgrade_automation import TierUpgradeAutomation

engine = TierUpgradeAutomation()
results = engine.run_daily_upgrade_cycle()

print(f"Upgrades: {results['upgrades_processed']}")
print(f"Downgrades: {results['downgrades_processed']}")
print(f"Emails: {results['emails_sent']}")
```

---

## Database Queries

### Check Client's Subscription

```sql
SELECT t.client_id, c.username, t.current_tier, s.next_billing_date
FROM upsell_tracking t
JOIN clients c ON t.client_id = c.client_id
LEFT JOIN subscriptions s ON t.client_id = s.client_id
WHERE t.client_id = 'CLIENT-001';
```

### Monthly Revenue by Tier

```sql
SELECT tier, COUNT(*) as client_count,
       SUM(charge_amount_usd) as total_charges,
       SUM(charge_amount_usd + tax_amount_usd) as total_with_tax
FROM billing_history
WHERE strftime('%Y-%m', created_at) = '2024-06'
  AND status = 'success'
GROUP BY tier;
```

### Failed Charges Needing Retry

```sql
SELECT charge_id, client_id, failure_reason, retry_count
FROM billing_history
WHERE status = 'failed' AND retry_count < 3
ORDER BY created_at ASC;
```

### Downgrade Warnings Sent

```sql
SELECT client_id, downgrade_warning_sent_at
FROM upsell_tracking
WHERE downgrade_warning_sent_at IS NOT NULL
  AND downgrade_warning_sent_at > datetime('now', '-7 days');
```

---

## Environment Variables

```bash
# Required
STRIPE_API_KEY=sk_live_YOUR_KEY

# Optional
CLIENTS_DB_PATH=/var/lib/profitengine/clients.db
BILLING_API_KEY=your-api-key
BILLING_ADMIN_API_KEY=your-admin-key
SEND_UPGRADE_EMAIL=true
SUPPORT_EMAIL=support@profitengine.com
```

---

## Tier Pricing Reference

| Tier | Score | Annual Fee | Monthly ($100K AUM) |
|------|-------|-----------|-------------------|
| Free | <50 | 0% | $0.00 |
| Hybrid | 50-74 | 0.5% | $41.67 |
| White-Label | 75-89 | 1.0% | $83.33 |
| Enterprise | 90-100 | 1.5% | $125.00 |

*All includes 8% tax by default (configurable)*

---

## Common Commands

### Start API Server

```bash
uvicorn tier_upgrade_api:app --host 0.0.0.0 --port 8000
```

### Test Stripe Connection

```python
import stripe
stripe.api_key = "YOUR_KEY"
try:
    stripe.Account.retrieve()
    print("✓ Connected")
except Exception as e:
    print(f"✗ Error: {e}")
```

### View Audit Logs

```bash
tail -f /var/log/profitengine/audit.jsonl | jq '.details'
```

### Backup Database

```bash
sqlite3 /var/lib/profitengine/clients.db \
  ".backup '/var/backups/clients-$(date +%Y%m%d).db'"
```

### Check Services

```bash
sudo systemctl list-units | grep profitengine
sudo systemctl status profitengine-api
sudo systemctl list-timers profitengine-*.timer
```

---

## Troubleshooting

### Stripe API Error

```python
import stripe
stripe.api_key = os.environ.get('STRIPE_API_KEY')

try:
    # Your operation
    pass
except stripe.error.AuthenticationError:
    print("Invalid API key")
except stripe.error.StripeError as e:
    print(f"Stripe error: {e.user_message}")
```

### Database Locked

```bash
# Check processes
lsof | grep clients.db

# Restart to unlock
sudo systemctl restart profitengine-api
```

### Failed Charges Not Retrying

```python
processor = StripePaymentProcessor()
result = processor.retry_failed_charges()
print(f"Retried: {result['total_retried']}")
print(f"Success: {result['successful']}")
```

### Revenue Report Empty

```python
from datetime import datetime

# Check if charges exist for month
processor = StripePaymentProcessor()
report = processor.generate_revenue_report()

if report['mrr_usd'] == 0:
    print("No charges processed yet")
else:
    print(f"MRR: ${report['mrr_usd']:.2f}")
```

---

## Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Score all clients (1000) | 30-45s | Includes DB queries |
| Upgrade client | 2-3s | Stripe API call |
| Process 500 monthly charges | 45-60s | Parallel processing |
| Retry failed charges | 20-30s | Up to 3 attempts each |
| Generate revenue report | <1s | In-memory calculation |

---

## File Locations

```
Core Modules:
  payment_processor.py              # Payment processing
  tier_upgrade_automation.py        # Daily automation
  tier_upgrade_api.py               # REST API

Documentation:
  TIER_UPGRADE_README.md            # Full guide
  TIER_UPGRADE_DEPLOYMENT.md        # Deployment
  TIER_UPGRADE_INTEGRATION.md       # Integration
  TIER_UPGRADE_SYSTEM_SUMMARY.md    # Overview
  QUICK_REFERENCE.md                # This file

Templates:
  email_templates/upgrade_confirmation.html
  email_templates/downgrade_warning.html

Database:
  /var/lib/profitengine/clients.db

Logs:
  /var/log/profitengine/audit.jsonl
  /var/log/profitengine/tier_upgrade.log

Backups:
  /var/backups/profitengine/clients-*.db.gz
```

---

## Links & Resources

- **Stripe API:** https://stripe.com/docs/api
- **Stripe Testing:** https://stripe.com/docs/testing
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLite Docs:** https://www.sqlite.org/docs.html
- **Python Docs:** https://docs.python.org/3/

---

## Support Channels

- **Email:** support@profitengine.com
- **Docs:** See TIER_UPGRADE_README.md
- **Issues:** Check troubleshooting section
- **Debug:** Enable logging and check audit trail

---

**Quick Reference v1.0** | Last Updated: June 2024

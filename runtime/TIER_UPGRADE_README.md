# ProfitEngine v5 — Automated Tier Upgrade System

## Overview

Complete automated customer tier upgrade system with payment processing, designed for production use with real Stripe integration.

### Features

- **Automatic Tier Upgrades** - Daily performance-based upgrades (Hybrid, White-Label, Enterprise)
- **Automatic Downgrades** - Performance drop detection with warning system
- **Stripe Payment Processing** - Real payment integration with retry logic
- **Recurring Monthly Charges** - AUM-based fee billing with tax calculation
- **Refund Management** - Automatic and manual refund processing
- **Email Notifications** - Upgrade confirmations, downgrade warnings
- **Audit Logging** - Complete transaction history for compliance
- **REST API** - Admin and customer endpoints for tier management
- **Revenue Reporting** - MRR tracking, tier breakdown, monthly reports

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Daily Upgrade Cycle                        │
│          (5 PM MST / 11 PM UTC via cron)                    │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │ Upsell Scorer    │  Scores clients based on:
        │                  │  • Win rate (25 pts)
        │ • Metrics fetch  │  • Balance growth (25 pts)
        │ • Score calc     │  • Consistency (25 pts)
        │ • Thresholds     │  • Engagement (25 pts)
        └────────┬─────────┘
                 │
    ┌────────────▼──────────────┐
    │                           │
    ▼                           ▼
┌──────────────┐        ┌───────────────┐
│ Tier Upgrade │        │ Tier Downgrade│
│ Automation   │        │ Detection     │
│              │        │               │
│ • Upgrade    │        │ • Check scores│
│ • Payment    │        │ • Warning     │
│ • Email      │        │ • 7-day wait  │
│ • Audit log  │        │ • Auto-down   │
└──────┬───────┘        └───────┬───────┘
       │                        │
       └────────────┬───────────┘
                    │
           ┌────────▼──────────┐
           │ Payment Processor │
           │                  │
           │ • Subscribe      │
           │ • Monthly charge │
           │ • Retry logic    │
           │ • Refund process │
           └────────┬─────────┘
                    │
           ┌────────▼──────────┐
           │  Stripe API       │
           │                  │
           │ • Create/update   │
           │ • Charge          │
           │ • Refund          │
           └──────────────────┘
```

## Installation

### 1. Add Stripe Dependency

```bash
pip install stripe
```

Update `requirements.txt`:
```
stripe>=12.0.0
```

### 2. Set Environment Variables

**Production (.env):**
```bash
# Stripe API
STRIPE_API_KEY=sk_live_YOUR_PRODUCTION_KEY_HERE
STRIPE_API_VERSION=2024-06-20

# Database
CLIENTS_DB_PATH=/var/lib/profitengine/clients.db
BILLING_DB_PATH=/var/lib/profitengine/clients.db

# Email
SEND_UPGRADE_EMAIL=true
SEND_DOWNGRADE_EMAIL=true
SUPPORT_EMAIL=support@profitengine.com

# API Keys
BILLING_API_KEY=your-api-key-here
BILLING_ADMIN_API_KEY=your-admin-key-here

# Audit
AUDIT_LOG_PATH=/var/log/profitengine/audit.jsonl
```

**Testing (.env.test):**
```bash
# Stripe Test Mode
STRIPE_API_KEY=sk_test_YOUR_TEST_KEY_HERE

# Test Database
CLIENTS_DB_PATH=test_clients.db
BILLING_DB_PATH=test_clients.db

SEND_UPGRADE_EMAIL=false
SEND_DOWNGRADE_EMAIL=false
```

### 3. Initialize Database

The payment processor auto-initializes on first run:

```python
from payment_processor import StripePaymentProcessor

processor = StripePaymentProcessor("clients.db")
# Tables created automatically:
# - billing_history
# - refunds
# - subscriptions
# - revenue_tracking
# - upsell_tracking
```

## Usage

### Tier Upgrade Automation (Daily Cron)

Run automatically daily at 5 PM MST (11 PM UTC):

```python
from tier_upgrade_automation import daily_upgrade_cycle

results = daily_upgrade_cycle()
print(f"Upgrades: {results['upgrades_processed']}")
print(f"Downgrades: {results['downgrades_processed']}")
print(f"Emails sent: {results['emails_sent']}")
```

**Cron Schedule:**
```bash
# Linux/macOS crontab
0 23 * * * cd /opt/profitengine && python -c "from tier_upgrade_automation import daily_upgrade_cycle; daily_upgrade_cycle()"

# Or use systemd timer (preferred)
```

### Monthly Billing Run

Process monthly tier fees for all active subscriptions:

```python
from payment_processor import StripePaymentProcessor

processor = StripePaymentProcessor()
results = processor.process_monthly_charges()

print(f"Charged: {results['successful']}/{results['total_attempted']}")
print(f"Failed: {results['failed']} (retry scheduled)")
```

### Manual Tier Management

```python
from payment_processor import StripePaymentProcessor
from decimal import Decimal

processor = StripePaymentProcessor()

# Upgrade client
result = processor.upgrade_client_tier(
    client_id="CLIENT-001",
    username="alice_trader",
    new_tier="white_label",
    account_balance=Decimal("150000.00")
)

# Downgrade client
result = processor.downgrade_client_tier(
    client_id="CLIENT-001",
    new_tier="hybrid",
    account_balance=Decimal("150000.00")
)
```

### REST API

Start the FastAPI server:

```bash
python tier_upgrade_api.py
```

#### Customer Endpoints

All customer endpoints require `X-API-Key` header.

**Get Subscription Info:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/billing/subscription?client_id=CLIENT-001"
```

Response:
```json
{
  "client_id": "CLIENT-001",
  "username": "alice_trader",
  "current_tier": "white_label",
  "next_billing_date": "2024-07-01",
  "monthly_charge_usd": 125.00,
  "annual_charge_usd": 1500.00,
  "status": "active"
}
```

**Get Billing History:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/billing/history?client_id=CLIENT-001&limit=50"
```

**Request Upgrade:**
```bash
curl -X POST -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"client_id":"CLIENT-001","target_tier":"enterprise"}' \
  http://localhost:8000/api/billing/upgrade
```

#### Admin Endpoints

All admin endpoints require `X-Admin-API-Key` header.

**Get Upgrade Candidates:**
```bash
curl -H "X-Admin-API-Key: your-admin-key" \
  http://localhost:8000/api/admin/tier-candidates
```

**Get Revenue Report:**
```bash
curl -H "X-Admin-API-Key: your-admin-key" \
  "http://localhost:8000/api/admin/revenue-report?year_month=2024-06"
```

**Run Upgrade Cycle:**
```bash
curl -X POST -H "X-Admin-API-Key: your-admin-key" \
  http://localhost:8000/api/admin/run-upgrade-cycle
```

**Process Monthly Charges:**
```bash
curl -X POST -H "X-Admin-API-Key: your-admin-key" \
  http://localhost:8000/api/admin/process-monthly-charges
```

## Tier Structure

### Scoring Thresholds

```
Score 0-49:     FREE tier (no charge)
Score 50-74:    HYBRID tier (0.5% annual AUM)
Score 75-89:    WHITE-LABEL tier (1.0% annual AUM)
Score 90-100:   ENTERPRISE tier (1.5% annual AUM)
```

### Score Calculation

Each component is 0-25 points (total 100):

**Win Rate (25 pts)**
- ≥85% win rate → 25 pts (Enterprise candidate)
- ≥70% win rate → 20 pts (Hybrid minimum)
- <70% → proportional (0-19 pts)

**Balance Growth (25 pts)**
- ≥50% growth in 7 days → 25 pts
- Proportional scaling up to 50%

**Consistency (25 pts)**
- ≥5 consecutive winning days → 25 pts
- Proportional to consecutive wins

**Engagement (25 pts)**
- ≥10 trades/day average → 25 pts
- Proportional to trading activity

### Monthly Fee Calculation

```
Monthly Charge = (Account Balance × Annual Fee %) / 12
Tax = Monthly Charge × Tax Rate (default 8%)
Total = Monthly Charge + Tax

Example (White-Label, $150,000 AUM):
Monthly Charge = ($150,000 × 1.0%) / 12 = $125.00
Tax = $125.00 × 0.08 = $10.00
Total = $135.00
```

## Downgrade Process

Automatic downgrade occurs when:

1. **Performance drops** - Score falls below minimum for tier
2. **Warning sent** - Client notified with 7-day grace period
3. **7 days pass** - Downgrade triggered automatically
4. **Refund processed** - Prorated refund issued (if applicable)
5. **Email sent** - Notification of downgrade
6. **Audit logged** - All changes recorded

### Downgrade Timeline

```
Day 0: Score drops below threshold
       → Warning email sent
       → 7-day window starts

Day 7: If score still below threshold
       → Auto-downgrade triggered
       → Subscription cancelled
       → Refund processed
       → Downgrade email sent
       → Audit log entry

Day 8-10: Client can re-upgrade if performance recovers
```

## Payment Processing

### Stripe Integration

All payments go through Stripe API with:

- **PCI Compliance** - Never store full card details
- **Payment Method Tokenization** - Stripe handles card storage
- **Automatic Retries** - Failed charges retry with exponential backoff
- **Webhooks** - Optional event notifications for payment status
- **Tax Handling** - Configurable tax rate (default 8%)

### Charge Flow

```
1. Monthly charge scheduled
   ↓
2. Stripe invoice created/charged
   ↓
3. Transaction ID recorded
   ↓
4. Success? → billing_history marked SUCCESS
   │
   └─ Failure? → billing_history marked FAILED
                 Retry scheduled (5 min, 30 min, 4 hrs)

5. Retry attempts up to 3 times
   ↓
   Success? → Mark SUCCESS
   │
   └─ Final failure? → Admin notification
```

### Refund Flow

```
1. Refund request created
   ↓
2. Stripe processes refund
   ↓
3. Refund ID recorded
   ↓
4. Status tracked (pending → refunded)
```

## Email System

### Upgrade Confirmation

Sent when tier upgrade is processed:

- **To:** Client email
- **Subject:** Congratulations! You've Been Upgraded
- **Contents:**
  - New tier and benefits
  - Monthly charge amount
  - Next billing date
  - Links to dashboard and settings

**Template:** `email_templates/upgrade_confirmation.html`

### Downgrade Warning

Sent when performance drops below threshold:

- **To:** Client email
- **Subject:** Account Performance Notice
- **Contents:**
  - Current score vs. threshold
  - 7-day warning period
  - Options to improve or keep tier
  - Support contact info

**Template:** `email_templates/downgrade_warning.html`

## Audit Logging

All financial transactions logged to `data/audit.jsonl`:

```json
{
  "event_type": "info",
  "actor": "tier_upgrade_automation",
  "action": "upgrade",
  "status": "ok",
  "details": {
    "client_id": "CLIENT-001",
    "username": "alice_trader",
    "previous_tier": "free",
    "new_tier": "white_label",
    "score": 78.5,
    "monthly_charge_usd": 125.00,
    "subscription_id": "SUB-1234567890-abc123"
  },
  "timestamp": 1719849600.0
}
```

**Auditable Events:**
- `upgrade` - Tier upgrade processed
- `downgrade` - Tier downgrade processed
- `charge` - Monthly charge attempt
- `refund` - Refund issued
- `failed_charge` - Charge failure
- `retry_charge` - Charge retry attempt

## Monitoring & Alerts

### Key Metrics to Track

```python
# Monthly recurring revenue
mrr = revenue_processor.generate_revenue_report()['mrr_usd']

# Failed charges
failed = processor.get_billing_history(status='failed')

# Pending refunds
pending_refunds = cursor.execute(
    "SELECT COUNT(*) FROM refunds WHERE status='pending'"
)

# Upcoming billing
upcoming = cursor.execute(
    "SELECT COUNT(*) FROM subscriptions WHERE next_billing_date=DATE('now')"
)
```

### Alert Conditions

Set up alerts for:

1. **Failed Charges** - Any charge failure (manual review required)
2. **High Refund Rate** - Refunds > 5% of charges (quality issue)
3. **Processing Backlog** - Pending charges > 10 (system issue)
4. **Stripe API Errors** - Any StripeError exceptions (check API status)

## Security Checklist

- [x] Never log full card numbers (Stripe handles)
- [x] API keys stored in environment variables
- [x] Admin endpoints require separate auth key
- [x] All financial transactions audited
- [x] Tax calculations compliant with jurisdiction
- [x] PCI compliance via Stripe
- [x] HTTPS required for production API
- [x] Rate limiting on sensitive endpoints (production)
- [x] Webhook signature verification (if using webhooks)

## Production Deployment

### Pre-Production Checklist

- [ ] Stripe production API key configured
- [ ] Database backup strategy in place
- [ ] Cron jobs scheduled for:
  - Daily upgrade cycle (5 PM MST)
  - Monthly charge processing (1st of month)
  - Failed charge retries (hourly)
- [ ] Email service configured (SendGrid, SES, etc.)
- [ ] Monitoring and alerting set up
- [ ] Audit log retention policy defined
- [ ] Tax rate configured for jurisdiction
- [ ] Test with small customer cohort first

### Database Backups

```bash
# Daily backup
0 2 * * * sqlite3 /var/lib/profitengine/clients.db ".backup '/var/backups/clients-$(date +%Y%m%d).db'"

# Weekly cleanup (keep 4 weeks)
0 3 0 * * find /var/backups/ -name "clients-*.db" -mtime +28 -delete
```

### Logging & Monitoring

```bash
# Monitor tier upgrades
tail -f /var/log/profitengine/audit.jsonl | grep "upgrade"

# Check failed charges
sqlite3 /var/lib/profitengine/clients.db \
  "SELECT client_id, username, failure_reason FROM billing_history WHERE status='failed'"

# Revenue report
python -c "
from payment_processor import StripePaymentProcessor
p = StripePaymentProcessor()
r = p.generate_revenue_report('2024-06')
print(f'MRR: \${r[\"mrr_usd\"]:.2f}')
"
```

## Troubleshooting

### Stripe Connection Issues

```python
import stripe

# Test connection
try:
    stripe.Account.retrieve()
    print("✓ Stripe connection OK")
except Exception as e:
    print(f"✗ Stripe error: {e}")
```

### Failed Charges Not Retrying

Check retry schedule in `payment_processor.py`:
```python
RETRY_DELAY_MINUTES = [5, 30, 240]  # 5 min, 30 min, 4 hours
```

Manually trigger retry:
```python
processor = StripePaymentProcessor()
processor.retry_failed_charges()
```

### Downgrade Not Triggering

Verify warning was sent:
```sql
SELECT client_id, downgrade_warning_sent_at FROM upsell_tracking
WHERE client_id = 'CLIENT-001';
```

Check if 7 days have passed:
```python
from datetime import datetime, timedelta

warning_sent = datetime.fromisoformat(...)
if (datetime.utcnow() - warning_sent).days >= 7:
    print("Ready for downgrade")
```

## Files

- **`payment_processor.py`** - Core payment processing engine
- **`tier_upgrade_automation.py`** - Daily upgrade/downgrade automation
- **`tier_upgrade_api.py`** - FastAPI REST endpoints
- **`email_templates/upgrade_confirmation.html`** - Upgrade email
- **`email_templates/downgrade_warning.html`** - Warning email
- **`TIER_UPGRADE_README.md`** - This file

## Support

For issues or questions:

1. Check audit logs: `tail -f data/audit.jsonl`
2. Review database: `sqlite3 clients.db`.schema
3. Test Stripe connection: See Troubleshooting above
4. Contact: support@profitengine.com

---

**Version:** 1.0.0  
**Last Updated:** June 2024  
**Status:** Production Ready

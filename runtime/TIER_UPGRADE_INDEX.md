# ProfitEngine v5 — Tier Upgrade System Complete Index

## Quick Navigation

### For First-Time Users
1. **Start Here:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min read)
2. **Then:** [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) (20 min read)
3. **Deploy:** [TIER_UPGRADE_DEPLOYMENT.md](TIER_UPGRADE_DEPLOYMENT.md) (reference during setup)

### For Developers
1. **Architecture:** [TIER_UPGRADE_SYSTEM_SUMMARY.md](TIER_UPGRADE_SYSTEM_SUMMARY.md)
2. **Integration:** [TIER_UPGRADE_INTEGRATION.md](TIER_UPGRADE_INTEGRATION.md)
3. **Code:** See Python files below
4. **Testing:** Integration test examples in [TIER_UPGRADE_INTEGRATION.md](TIER_UPGRADE_INTEGRATION.md)

### For Operations
1. **Deployment:** [TIER_UPGRADE_DEPLOYMENT.md](TIER_UPGRADE_DEPLOYMENT.md)
2. **Verification:** [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)
3. **Operations:** Section in Deployment guide
4. **Monitoring:** Section in README

### For Compliance/Audit
1. **Audit Logging:** Section in [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md)
2. **Security:** Security checklist in README
3. **Transaction Trail:** Query examples in [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
4. **Verification:** [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

---

## File Directory

### Core System Files

#### Production Python Modules (1,560+ lines)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| [`payment_processor.py`](payment_processor.py) | 660+ | Stripe payment integration, billing, refunds | ✓ Complete |
| [`tier_upgrade_automation.py`](tier_upgrade_automation.py) | 500+ | Daily upgrade/downgrade automation, emails | ✓ Complete |
| [`tier_upgrade_api.py`](tier_upgrade_api.py) | 400+ | FastAPI REST endpoints for customers & admins | ✓ Complete |

#### Email Templates

| File | Type | Purpose |
|------|------|---------|
| [`email_templates/upgrade_confirmation.html`](email_templates/upgrade_confirmation.html) | HTML | Tier upgrade confirmation email |
| [`email_templates/downgrade_warning.html`](email_templates/downgrade_warning.html) | HTML | Performance warning email (7-day notice) |

### Documentation Files (1,600+ lines)

#### Getting Started

| File | Read Time | For | Topics |
|------|-----------|-----|--------|
| [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | 5 min | Everyone | API examples, Python snippets, commands, troubleshooting |
| [`TIER_UPGRADE_README.md`](TIER_UPGRADE_README.md) | 20 min | Developers, Operators | Features, usage, architecture, monitoring, security |
| [`TIER_UPGRADE_SYSTEM_SUMMARY.md`](TIER_UPGRADE_SYSTEM_SUMMARY.md) | 15 min | Developers, Managers | What was built, features, integration points |

#### Implementation & Integration

| File | Read Time | For | Topics |
|------|-----------|-----|--------|
| [`TIER_UPGRADE_DEPLOYMENT.md`](TIER_UPGRADE_DEPLOYMENT.md) | 30-60 min | DevOps, Engineers | Installation, systemd setup, operations, scaling |
| [`TIER_UPGRADE_INTEGRATION.md`](TIER_UPGRADE_INTEGRATION.md) | 25 min | Developers | Dashboard, API, email, webhook integration examples |

#### Verification & Reference

| File | Purpose |
|------|---------|
| [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) | Pre-production verification (75 items) |
| [`TIER_UPGRADE_INDEX.md`](TIER_UPGRADE_INDEX.md) | This file |

### Configuration

| File | Purpose |
|------|---------|
| [`requirements.txt`](../requirements.txt) | Updated with stripe, pydantic |
| `.env` (not in repo) | Runtime secrets (STRIPE_API_KEY, etc.) |

---

## Key Concepts

### Scoring System

Clients automatically scored on 4 dimensions (0-25 pts each):

1. **Win Rate (25 pts)** - Trading success percentage
2. **Balance Growth (25 pts)** - Account growth trajectory
3. **Consistency (25 pts)** - Consecutive winning days
4. **Engagement (25 pts)** - Trading volume/activity

**Score Thresholds:**
- 50-74 → Hybrid tier (0.5% annual AUM)
- 75-89 → White-Label tier (1.0% annual AUM)
- 90-100 → Enterprise tier (1.5% annual AUM)

### Monthly Billing

**Formula:**
```
Monthly Charge = (Account Balance × Annual Fee %) / 12
Tax = Monthly Charge × Tax Rate (8% default)
Total = Monthly Charge + Tax

Example (White-Label, $150K AUM):
Monthly = ($150,000 × 1.0%) / 12 = $125.00
Tax = $125.00 × 0.08 = $10.00
Total = $135.00
```

### Daily Upgrade Cycle (5 PM MST / 11 PM UTC)

1. Score all clients based on trading metrics
2. Identify upgrade candidates (score >= 50)
3. Process tier upgrades automatically
4. Charge via Stripe and create subscriptions
5. Send confirmation emails
6. Check for downgrade candidates
7. Process downgrades if performance dropped
8. Log all changes to audit trail

### Downgrade Handling

**Timeline:**
- Day 0: Score drops below tier threshold
- Day 0: Warning email sent to client
- Day 1-7: 7-day grace period
- Day 7: Auto-downgrade triggered if still below
- Day 7: Refund processed (prorated)
- Day 7: Downgrade email sent

---

## API Quick Start

### Get Subscription Info

```bash
curl -H "X-API-Key: YOUR_KEY" \
  "http://localhost:8000/api/billing/subscription?client_id=CLIENT-001"
```

Response:
```json
{
  "client_id": "CLIENT-001",
  "username": "alice_trader",
  "current_tier": "white_label",
  "monthly_charge_usd": 125.00,
  "next_billing_date": "2024-07-01"
}
```

### Admin: Get Candidates

```bash
curl -H "X-Admin-API-Key: ADMIN_KEY" \
  "http://localhost:8000/api/admin/tier-candidates"
```

### Admin: Revenue Report

```bash
curl -H "X-Admin-API-Key: ADMIN_KEY" \
  "http://localhost:8000/api/admin/revenue-report?year_month=2024-06"
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for more examples.

---

## Database Schema

Five tables manage the system:

```sql
billing_history    -- Every transaction (charges, refunds)
refunds            -- Refund tracking
subscriptions      -- Active customer subscriptions
revenue_tracking   -- Monthly MRR and breakdown
upsell_tracking    -- Customer tier eligibility history
```

Automatically initialized on first run. See [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) for schema details.

---

## Deployment Paths

### Path 1: Minimal Setup (5 minutes)
- Set STRIPE_API_KEY env var
- Run `StripePaymentProcessor()` to initialize DB
- Call daily upgrade cycle manually when ready
- **Use Case:** Testing, small-scale pilot

### Path 2: Standard Setup (30 minutes)
- Create FastAPI API service (systemd)
- Schedule daily cycle timer
- Configure backups
- **Use Case:** Single-server production (up to 1,000 customers)

### Path 3: Full Production (2-4 hours)
- Everything in Path 2, plus:
- SSL/TLS with Let's Encrypt
- Monitoring and alerting
- Dashboard integration
- Multi-region scaling (optional)
- **Use Case:** Large-scale production (1,000+ customers)

See [TIER_UPGRADE_DEPLOYMENT.md](TIER_UPGRADE_DEPLOYMENT.md) for detailed steps.

---

## Integration Checklist

To integrate with existing ProfitEngine system:

- [ ] Mount tier_upgrade_api.py FastAPI endpoints
- [ ] Update dashboard to show subscription status
- [ ] Connect email service (SendGrid/SES)
- [ ] Add tier info to client_api endpoints
- [ ] Update daily_alerts to include candidates
- [ ] Configure Stripe webhook (optional but recommended)
- [ ] Test with small customer cohort first

See [TIER_UPGRADE_INTEGRATION.md](TIER_UPGRADE_INTEGRATION.md) for code examples.

---

## Monitoring & Support

### Key Metrics to Track

```python
# Monthly Recurring Revenue
mrr = processor.generate_revenue_report()['mrr_usd']

# Failed charge rate (should be < 2%)
failed_count = cursor.execute("SELECT COUNT(*) FROM billing_history WHERE status='failed'")
failure_rate = failed_count / total_charges

# Upgrade rate (new customers to paid tiers)
upgrades = cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status='active'")

# Refund rate (should be < 5%)
refund_amount = cursor.execute("SELECT SUM(amount_usd) FROM refunds WHERE status='refunded'")
refund_rate = refund_amount / total_charges
```

### Alerting

Set alerts for:
- Failed charge rate > 2%
- Refund rate > 5%
- Pending charges > 10
- Stripe API errors
- Database locked/busy

See [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) monitoring section.

---

## Troubleshooting

### Common Issues

**Stripe authentication error:**
```python
import stripe
stripe.api_key = "YOUR_KEY"
stripe.Account.retrieve()  # Test connection
```

**Database locked:**
```bash
sudo systemctl restart profitengine-api
```

**Charges not processing:**
```python
processor = StripePaymentProcessor()
processor.process_monthly_charges()  # Manual run
```

**Revenue report empty:**
```python
# Check if charges exist
processor.generate_revenue_report()['mrr_usd']
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) troubleshooting section for more.

---

## Support & Resources

### Documentation by Role

**For Operators:**
- Start: [TIER_UPGRADE_DEPLOYMENT.md](TIER_UPGRADE_DEPLOYMENT.md)
- Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Verify: [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

**For Developers:**
- Start: [TIER_UPGRADE_SYSTEM_SUMMARY.md](TIER_UPGRADE_SYSTEM_SUMMARY.md)
- Integrate: [TIER_UPGRADE_INTEGRATION.md](TIER_UPGRADE_INTEGRATION.md)
- Code: Python module docstrings
- Test: Integration test examples

**For Managers:**
- Overview: [TIER_UPGRADE_SYSTEM_SUMMARY.md](TIER_UPGRADE_SYSTEM_SUMMARY.md)
- Features: [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) features section
- Monitoring: [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) monitoring section

**For Compliance:**
- Audit Trail: [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) audit logging section
- Security: [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) security checklist
- Verification: [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

### External Resources

- **Stripe API:** https://stripe.com/docs/api
- **Stripe Test Mode:** https://stripe.com/docs/testing
- **FastAPI:** https://fastapi.tiangolo.com
- **SQLite:** https://www.sqlite.org/docs.html
- **Python:** https://docs.python.org/3/

### Support Channels

- **Email:** support@profitengine.com
- **Docs:** This index and all linked guides
- **Code:** See docstrings and inline comments
- **Issues:** Check troubleshooting sections

---

## Quick Command Reference

```bash
# Start API
uvicorn tier_upgrade_api:app --host 0.0.0.0 --port 8000

# Run daily cycle manually
python -c "from tier_upgrade_automation import daily_upgrade_cycle; daily_upgrade_cycle()"

# Process monthly charges
python -c "from payment_processor import StripePaymentProcessor; StripePaymentProcessor().process_monthly_charges()"

# View audit logs
tail -f /var/log/profitengine/audit.jsonl | jq

# Check service status
sudo systemctl status profitengine-api

# Generate revenue report
python -c "from payment_processor import StripePaymentProcessor; import json; print(json.dumps(StripePaymentProcessor().generate_revenue_report(), indent=2))"
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for more.

---

## Project Status

### Completion: 100% ✓

- [x] 3 production Python modules (1,560+ lines)
- [x] 2 responsive HTML email templates
- [x] 5 comprehensive guides (1,600+ lines)
- [x] Complete REST API with auth
- [x] Real Stripe integration
- [x] Automated daily cycle
- [x] Payment processing with retries
- [x] Refund management
- [x] Audit logging
- [x] Database schema
- [x] Monitoring & alerts documented
- [x] Production deployment guide
- [x] Integration guide
- [x] Verification checklist
- [x] Quick reference

### Quality: Enterprise Grade

- [x] No placeholders or test values
- [x] Real API integration (Stripe)
- [x] Comprehensive error handling
- [x] Type hints throughout
- [x] Security best practices
- [x] PCI compliance (Stripe)
- [x] Audit trail for compliance
- [x] Production-ready deployment

### Status: PRODUCTION READY ✓

Ready for immediate deployment with real Stripe API keys.

---

## Version & License

**Version:** 1.0.0  
**Release Date:** June 2024  
**Status:** Production Ready  
**Maintained By:** ProfitEngine Engineering Team

---

## Start Here

**New to the system?** Read in this order:

1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 5 minutes
2. [TIER_UPGRADE_README.md](TIER_UPGRADE_README.md) - 20 minutes
3. [TIER_UPGRADE_DEPLOYMENT.md](TIER_UPGRADE_DEPLOYMENT.md) - during deployment
4. [TIER_UPGRADE_INTEGRATION.md](TIER_UPGRADE_INTEGRATION.md) - when integrating
5. [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) - before going live

**Questions?** See the troubleshooting section in [QUICK_REFERENCE.md](QUICK_REFERENCE.md) or contact support@profitengine.com.

---

**Last Updated:** June 2024  
**Status:** Complete and Ready for Use ✓

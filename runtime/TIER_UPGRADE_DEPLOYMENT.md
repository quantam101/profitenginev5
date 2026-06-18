# Tier Upgrade System — Production Deployment Guide

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
pip install stripe==12.3.0 pydantic fastapi uvicorn
```

### 2. Set Environment Variables

```bash
export STRIPE_API_KEY=sk_live_YOUR_PRODUCTION_KEY
export CLIENTS_DB_PATH=/var/lib/profitengine/clients.db
export BILLING_DB_PATH=/var/lib/profitengine/clients.db
export BILLING_API_KEY=your-secure-random-api-key
export BILLING_ADMIN_API_KEY=your-secure-random-admin-key
```

### 3. Initialize Database

```bash
python -c "from payment_processor import StripePaymentProcessor; StripePaymentProcessor()"
```

### 4. Run Daily Upgrade Cycle

```bash
python -c "from tier_upgrade_automation import daily_upgrade_cycle; daily_upgrade_cycle()"
```

Done! The system is ready. Schedule the daily cycle in cron (see below).

---

## Full Production Setup

### Prerequisites

- Python 3.10+
- SQLite3
- Stripe account (production or test)
- Email service (SendGrid, AWS SES, etc.)
- Linux/macOS server or Docker container

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│            ProfitEngine Production Cluster              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI Tier Upgrade API (port 8000)            │   │
│  │  - /api/billing/* endpoints                      │   │
│  │  - /api/admin/* endpoints                        │   │
│  │  - Runs 24/7                                     │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SQLite Database (clients.db)                    │   │
│  │  - billing_history                              │   │
│  │  - subscriptions                                │   │
│  │  - refunds                                       │   │
│  │  - upsell_tracking                              │   │
│  │  - revenue_tracking                             │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↑                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Scheduled Tasks (via cron/systemd)             │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │ Daily 5 PM MST: run_daily_upgrade_cycle    │ │   │
│  │  │ Hourly: process_monthly_charges            │ │   │
│  │  │ Every 5 min: retry_failed_charges          │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  External Services                              │   │
│  │  ├─ Stripe API (payments)                       │   │
│  │  ├─ Email Service (notifications)               │   │
│  │  └─ Audit Log Storage (compliance)              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Step 1: Environment Setup

Create `.env` file in `/opt/profitengine/runtime/.env`:

```bash
# Stripe (CRITICAL - never hardcode)
STRIPE_API_KEY=sk_live_YOUR_PRODUCTION_KEY_HERE
STRIPE_API_VERSION=2024-06-20

# Database Paths
CLIENTS_DB_PATH=/var/lib/profitengine/clients.db
BILLING_DB_PATH=/var/lib/profitengine/clients.db

# API Keys (generate with: openssl rand -hex 32)
BILLING_API_KEY=your-generated-random-key-here
BILLING_ADMIN_API_KEY=your-generated-admin-key-here

# Email Configuration
SEND_UPGRADE_EMAIL=true
SEND_DOWNGRADE_EMAIL=true
SUPPORT_EMAIL=support@profitengine.com
EMAIL_TEMPLATES_DIR=/opt/profitengine/runtime/email_templates

# Audit Logging
AUDIT_LOG_PATH=/var/log/profitengine/audit.jsonl

# Tax Configuration (adjust for jurisdiction)
TIER_UPGRADE_TAX_RATE=0.08  # 8% for US

# Database Backup (production)
DB_BACKUP_PATH=/var/backups/profitengine
```

### Step 2: Directory Structure

```bash
/opt/profitengine/
├── runtime/
│   ├── payment_processor.py
│   ├── tier_upgrade_automation.py
│   ├── tier_upgrade_api.py
│   ├── TIER_UPGRADE_README.md
│   ├── TIER_UPGRADE_DEPLOYMENT.md
│   ├── email_templates/
│   │   ├── upgrade_confirmation.html
│   │   └── downgrade_warning.html
│   └── .env (not in git)
│
├── logs/
│   ├── tier_upgrade.log
│   └── audit.jsonl
│
└── backups/
    └── clients-*.db (daily)

/var/lib/profitengine/
└── clients.db

/var/log/profitengine/
└── audit.jsonl
```

Create directories:

```bash
mkdir -p /opt/profitengine/runtime
mkdir -p /var/lib/profitengine
mkdir -p /var/log/profitengine
mkdir -p /var/backups/profitengine

# Set permissions
chmod 700 /var/lib/profitengine
chmod 700 /var/log/profitengine
chmod 700 /var/backups/profitengine
```

### Step 3: Install Dependencies

```bash
cd /opt/profitengine/runtime

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install stripe fastapi uvicorn pydantic
```

Update `requirements.txt`:

```
stripe>=12.0.0
fastapi>=0.124.0
uvicorn[standard]>=0.38.0
pydantic>=2.0.0
httpx>=0.28.0
```

### Step 4: Initialize Database

```bash
cd /opt/profitengine/runtime

# Load environment
export $(cat .env | xargs)

# Initialize
python -c "
from payment_processor import StripePaymentProcessor
processor = StripePaymentProcessor()
print('✓ Database initialized')
"
```

Verify tables:

```bash
sqlite3 /var/lib/profitengine/clients.db ".tables"
# Output: billing_history clients daily_snapshots refunds revenue_tracking subscriptions trades upsell_tracking
```

### Step 5: Configure Systemd Services

#### 5a. FastAPI API Server (runs 24/7)

Create `/etc/systemd/system/profitengine-api.service`:

```ini
[Unit]
Description=ProfitEngine Tier Upgrade API
After=network.target

[Service]
Type=simple
User=profitengine
WorkingDirectory=/opt/profitengine/runtime
EnvironmentFile=/opt/profitengine/runtime/.env
ExecStart=/opt/profitengine/runtime/venv/bin/uvicorn tier_upgrade_api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable profitengine-api
sudo systemctl start profitengine-api
sudo systemctl status profitengine-api
```

#### 5b. Daily Upgrade Cycle (runs at 5 PM MST)

Create `/etc/systemd/system/profitengine-upgrade.timer`:

```ini
[Unit]
Description=ProfitEngine Daily Tier Upgrade Cycle
Requires=profitengine-upgrade.service

[Timer]
OnCalendar=*-*-* 23:00:00  # 11 PM UTC = 5 PM MST
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/profitengine-upgrade.service`:

```ini
[Unit]
Description=Run ProfitEngine Tier Upgrade Cycle
After=network.target

[Service]
Type=oneshot
User=profitengine
WorkingDirectory=/opt/profitengine/runtime
EnvironmentFile=/opt/profitengine/runtime/.env
ExecStart=/opt/profitengine/runtime/venv/bin/python -c "from tier_upgrade_automation import daily_upgrade_cycle; daily_upgrade_cycle()"
StandardOutput=journal
StandardError=journal
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable profitengine-upgrade.timer
sudo systemctl start profitengine-upgrade.timer
sudo systemctl list-timers profitengine-upgrade.timer
```

#### 5c. Monthly Billing Run (1st of month at 2 AM UTC)

Create `/etc/systemd/system/profitengine-billing.service`:

```ini
[Unit]
Description=Process Monthly Tier Charges
After=network.target

[Service]
Type=oneshot
User=profitengine
WorkingDirectory=/opt/profitengine/runtime
EnvironmentFile=/opt/profitengine/runtime/.env
ExecStart=/opt/profitengine/runtime/venv/bin/python -c "from payment_processor import StripePaymentProcessor; StripePaymentProcessor().process_monthly_charges()"
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/profitengine-billing.timer`:

```ini
[Unit]
Description=Monthly Billing Run
Requires=profitengine-billing.service

[Timer]
OnCalendar=1 *-*-* 02:00:00  # 1st of month, 2 AM UTC
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl enable profitengine-billing.timer
sudo systemctl start profitengine-billing.timer
```

#### 5d. Retry Failed Charges (every 5 minutes)

Create `/etc/systemd/system/profitengine-retry.timer`:

```ini
[Unit]
Description=Retry Failed Charges
Requires=profitengine-retry.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/profitengine-retry.service`:

```ini
[Unit]
Description=Retry Failed Charges
After=network.target

[Service]
Type=oneshot
User=profitengine
WorkingDirectory=/opt/profitengine/runtime
EnvironmentFile=/opt/profitengine/runtime/.env
ExecStart=/opt/profitengine/runtime/venv/bin/python -c "from payment_processor import StripePaymentProcessor; StripePaymentProcessor().retry_failed_charges()"
StandardOutput=journal
StandardError=journal
```

Enable:

```bash
sudo systemctl enable profitengine-retry.timer
sudo systemctl start profitengine-retry.timer
```

### Step 6: Backup Strategy

Create `/usr/local/bin/backup-profitengine.sh`:

```bash
#!/bin/bash

BACKUP_DIR=/var/backups/profitengine
DB_PATH=/var/lib/profitengine/clients.db
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/clients-$DATE.db'"

# Compress
gzip "$BACKUP_DIR/clients-$DATE.db"

# Keep only last 30 days
find $BACKUP_DIR -name "clients-*.db.gz" -mtime +30 -delete

echo "✓ Backup created: $BACKUP_DIR/clients-$DATE.db.gz"
```

Make executable:

```bash
chmod +x /usr/local/bin/backup-profitengine.sh
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-profitengine.sh >> /var/log/profitengine/backup.log 2>&1
```

### Step 7: SSL/TLS for API (if public)

Using Let's Encrypt with Certbot:

```bash
sudo certbot certonly --standalone -d billing.profitengine.com

# Add to API server config (nginx reverse proxy)
server {
    listen 443 ssl;
    server_name billing.profitengine.com;
    
    ssl_certificate /etc/letsencrypt/live/billing.profitengine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/billing.profitengine.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Step 8: Monitoring & Alerts

#### Prometheus Metrics (optional)

```python
# Add to tier_upgrade_api.py
from prometheus_client import Counter, Gauge, Histogram

upgrade_counter = Counter('tier_upgrades_total', 'Total tier upgrades')
charge_counter = Counter('charges_total', 'Total charges processed')
failed_charge_counter = Counter('charges_failed', 'Failed charge attempts')
```

#### Logging Configuration

Create `/opt/profitengine/runtime/logging_config.py`:

```python
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {funcName}:{lineno} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/profitengine/tier_upgrade.log',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

#### Health Check Endpoint

```bash
# Monitor API health
watch -n 30 'curl -s http://localhost:8000/health | jq'
```

### Step 9: Test the System

```bash
#!/bin/bash
# test-tier-system.sh

echo "Testing ProfitEngine Tier Upgrade System..."

# 1. Database
echo "✓ Database connection"
sqlite3 /var/lib/profitengine/clients.db "SELECT COUNT(*) FROM billing_history" || exit 1

# 2. API health
echo "✓ API health check"
curl -s http://localhost:8000/health | jq '.' || exit 1

# 3. Stripe connection
echo "✓ Stripe API connection"
python -c "
import stripe
import os
stripe.api_key = os.environ.get('STRIPE_API_KEY')
try:
    stripe.Account.retrieve()
    print('Stripe connected')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
"

# 4. Run test upgrade cycle (dry-run)
echo "✓ Test upgrade cycle"
python -c "
from tier_upgrade_automation import TierUpgradeAutomation
engine = TierUpgradeAutomation()
print('System ready for daily cycle')
"

echo ""
echo "All tests passed! System ready for production."
```

Run:

```bash
cd /opt/profitengine/runtime
source venv/bin/activate
bash test-tier-system.sh
```

### Step 10: Verify Production Readiness

Checklist:

- [ ] `.env` file created with production keys (NOT in git)
- [ ] Database initialized at `/var/lib/profitengine/clients.db`
- [ ] All systemd services enabled and running
- [ ] Daily upgrade cycle scheduled for 5 PM MST (11 PM UTC)
- [ ] Monthly billing run scheduled for 1st of month
- [ ] Backups running daily
- [ ] Email service configured
- [ ] Audit logging enabled
- [ ] API accessible and healthy
- [ ] Stripe API key verified (production, not test)
- [ ] All tests passing

---

## Operations

### View Logs

```bash
# API logs
sudo journalctl -u profitengine-api -f

# Upgrade cycle logs
sudo journalctl -u profitengine-upgrade.service -n 100

# All systemd services
sudo systemctl list-units | grep profitengine

# Audit log
tail -f /var/log/profitengine/audit.jsonl | jq
```

### Common Commands

```bash
# Check service status
sudo systemctl status profitengine-api

# Restart API
sudo systemctl restart profitengine-api

# View next scheduled upgrade cycle
sudo systemctl list-timers profitengine-upgrade.timer

# Manually run upgrade cycle (for testing)
cd /opt/profitengine/runtime && \
  source venv/bin/activate && \
  python -c "from tier_upgrade_automation import daily_upgrade_cycle; daily_upgrade_cycle()"

# Check database size
du -h /var/lib/profitengine/clients.db

# View revenue report
cd /opt/profitengine/runtime && python -c "
from payment_processor import StripePaymentProcessor
p = StripePaymentProcessor()
import json
report = p.generate_revenue_report()
print(json.dumps(report, indent=2))
"
```

### Troubleshooting

#### API won't start

```bash
# Check syntax
python -m py_compile tier_upgrade_api.py

# Check dependencies
pip list | grep -E 'stripe|fastapi|uvicorn'

# Check port availability
netstat -tuln | grep 8000

# Check logs
sudo journalctl -u profitengine-api -n 50 -e
```

#### Stripe authentication error

```bash
# Verify API key
echo $STRIPE_API_KEY | head -c 20
# Should start with 'sk_live_' or 'sk_test_'

# Test connection
python -c "
import stripe
stripe.api_key = '$STRIPE_API_KEY'
try:
    acct = stripe.Account.retrieve()
    print(f'✓ Connected as: {acct.email}')
except stripe.error.AuthenticationError as e:
    print(f'✗ Auth error: {e}')
"
```

#### Database locked

```bash
# Check for running processes
lsof | grep clients.db

# Restart service to release lock
sudo systemctl restart profitengine-api
```

---

## Scaling Considerations

### For 1,000+ Customers

- **Database:** Consider PostgreSQL instead of SQLite
- **API:** Add load balancer (nginx) with multiple uvicorn workers
- **Caching:** Add Redis for subscription lookups
- **Batch Processing:** Use job queue (Celery) for bulk upgrades

### Migration from SQLite to PostgreSQL

```python
# pg_migrate.py - Migrate to PostgreSQL
import sqlite3
import psycopg2

# Read from SQLite
sqlite_conn = sqlite3.connect('clients.db')
sqlite_cursor = sqlite_conn.cursor()

# Write to PostgreSQL
pg_conn = psycopg2.connect("dbname=profitengine user=postgres")
pg_cursor = pg_conn.cursor()

# Migrate billing_history
sqlite_cursor.execute("SELECT * FROM billing_history")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute("INSERT INTO billing_history VALUES (%s, %s, ...)", row)

pg_conn.commit()
```

---

## Support & Maintenance

### SLA Targets

- **API Uptime:** 99.9%
- **Charge Processing:** Within 24 hours of billing date
- **Email Delivery:** Within 5 minutes of event
- **Refund Processing:** Within 5-10 business days (Stripe processing time)

### Contact Information

- **Billing Issues:** billing@profitengine.com
- **Technical Support:** support@profitengine.com
- **Emergency Hotline:** (on-call phone number)

---

**Version:** 1.0.0  
**Last Updated:** June 2024  
**Status:** Production Ready  
**Maintained By:** Engineering Team

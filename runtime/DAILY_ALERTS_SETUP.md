# ProfitEngine Daily Alerts Setup Guide

## Overview

The Daily Alerts system automatically sends email reports every day at 5 PM MST (market close) with:
- Top 5 traders (by P&L and win rate)
- New customer signups
- Upsell opportunities (hybrid/enterprise candidates)
- System health status
- Aggregate daily P&L

**Alert Recipient:** `dispatch@alreadyherellc.com` (configurable via env var)

---

## Quick Start

### 1. Install Dependencies

```bash
# Core requirements (already in runtime)
pip install python-dateutil

# Optional: For SendGrid support
pip install sendgrid

# Optional: For AWS SES support
pip install boto3

# Optional: For Telegram/Slack alerts
pip install requests
```

### 2. Configure Environment Variables

Create or update `.env` in the runtime directory:

```bash
# Email Provider Selection (gmail, sendgrid, or aws_ses)
EMAIL_PROVIDER=gmail

# Gmail Configuration (if using Gmail)
GMAIL_USER=your-gmail@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password from https://myaccount.google.com/apppasswords

# SendGrid Configuration (if using SendGrid)
SENDGRID_API_KEY=SG.xxx...

# AWS SES Configuration (if using SES)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SES_REGION=us-east-1

# Alert Recipient Email
ALERT_EMAIL=dispatch@alreadyherellc.com

# Database Path
CLIENTS_DB_PATH=/path/to/clients.db

# Optional: Telegram Alerts
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789

# Optional: Slack Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. Test the Alert System

**Dry run (generate alert without sending):**
```bash
python3 daily_alerts.py --dry-run --verbose
```

**Send a test alert:**
```bash
python3 daily_alerts.py --verbose
```

**Specify custom email recipient:**
```bash
python3 daily_alerts.py --email test@example.com
```

---

## Scheduling

### Option A: Cron Job (Linux/OCI)

The simplest approach. Add to `crontab -e`:

```cron
# Run daily at 5 PM MST (23:00 UTC during daylight saving)
0 23 * * * cd /home/opc/profitengine/runtime && /usr/bin/python3 daily_alerts.py >> daily_alerts.log 2>&1

# Alternative: 6 PM MST (00:00 UTC during standard time)
# 0 0 * * * cd /home/opc/profitengine/runtime && /usr/bin/python3 daily_alerts.py >> daily_alerts.log 2>&1
```

**Verify cron is running:**
```bash
# List your cron jobs
crontab -l

# Check cron logs
sudo journalctl -u cron
# or
tail -f /var/log/syslog | grep CRON
```

### Option B: Systemd Timer (Linux/OCI - Preferred)

More robust alternative to cron.

**Install the timer:**
```bash
# Copy service files to systemd directory
sudo cp daily_alerts.service /etc/systemd/system/
sudo cp daily_alerts.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the timer to start on boot
sudo systemctl enable daily_alerts.timer

# Start the timer
sudo systemctl start daily_alerts.timer
```

**Verify timer is active:**
```bash
# List active timers
sudo systemctl list-timers daily_alerts.timer

# Check timer status
sudo systemctl status daily_alerts.timer

# View next trigger time
sudo systemctl list-timers --all daily_alerts.timer

# View service logs
sudo journalctl -u daily_alerts.service -f
```

**Manual trigger for testing:**
```bash
# Trigger the service immediately
sudo systemctl start daily_alerts.service

# Watch the execution
sudo journalctl -u daily_alerts.service -f
```

**Adjust schedule:**

Edit `/etc/systemd/system/daily_alerts.timer` and change the `OnCalendar` line:

```bash
# 5 PM MST (summer/daylight saving)
OnCalendar=*-*-* 23:00:00

# 6 PM MST (winter/standard time)
OnCalendar=*-*-* 00:00:00

# Multiple times per day (optional)
# OnCalendar=*-*-* 09:30,16:00  # 9:30 AM and 4 PM ET (during trading hours)
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart daily_alerts.timer
```

### Option C: GitHub Actions (Cloud-based)

If you want alerts to run regardless of OCI server status:

Create `.github/workflows/daily-alerts.yml`:

```yaml
name: ProfitEngine Daily Alerts

on:
  schedule:
    - cron: '0 23 * * *'  # 5 PM MST daily
  workflow_dispatch:  # Manual trigger

jobs:
  daily-alert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install requests
      
      - name: Run daily alerts
        env:
          EMAIL_PROVIDER: ${{ secrets.EMAIL_PROVIDER }}
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          ALERT_EMAIL: dispatch@alreadyherellc.com
          CLIENTS_DB_PATH: runtime/clients.db
        run: |
          cd runtime
          python3 daily_alerts.py
```

---

## Email Provider Setup

### Gmail (Simplest)

1. Enable 2-factor authentication on your Gmail account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or your device)
4. Generate a 16-character app password
5. Use that password in `GMAIL_APP_PASSWORD` (with or without spaces)

**Example:**
```bash
GMAIL_USER=profitengine@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```

### SendGrid

1. Create a free account at https://sendgrid.com
2. Go to Settings → API Keys
3. Create a new API key with "Mail Send" permission
4. Copy the key to `SENDGRID_API_KEY`

### AWS SES

1. Create AWS account and verify domain/email
2. Create IAM user with SES permission:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "ses:SendEmail",
         "Resource": "*"
       }
     ]
   }
   ```
3. Generate access key and secret
4. Set environment variables

---

## Telegram & Slack Integration (Optional)

### Telegram Alerts

1. Create a Telegram bot via @BotFather
2. Create a group/channel for alerts
3. Add your bot to the group
4. Get chat ID:
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   # Find "chat": { "id": XXXXX }
   ```
5. Set environment variables:
   ```bash
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

### Slack Alerts

1. Create a Slack Incoming Webhook:
   https://api.slack.com/messaging/webhooks
2. Copy the webhook URL to:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```

---

## Logs

### View Alert Logs

```bash
# Real-time logs
tail -f runtime/daily_alerts.log

# Last 50 lines
tail -50 runtime/daily_alerts.log

# Search for errors
grep ERROR runtime/daily_alerts.log

# Count alerts sent
grep "Email sent successfully" runtime/daily_alerts.log | wc -l
```

### Log Rotation (Optional)

Add to `/etc/logrotate.d/profitengine`:

```
/home/opc/profitengine/runtime/daily_alerts.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 opc opc
    sharedscripts
}
```

---

## Database Schema

The alerts query these tables from `clients.db`:

### `clients`
```sql
CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    username TEXT,
    email TEXT,
    account_balance REAL,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    created_at TIMESTAMP,
    last_trade_at TIMESTAMP,
    subscription_tier TEXT
);
```

### `trades`
```sql
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    client_id TEXT,
    symbol TEXT,
    side TEXT,
    entry_price REAL,
    exit_price REAL,
    shares INTEGER,
    pnl_usd REAL,
    win BOOLEAN,
    executed_at TIMESTAMP
);
```

---

## Alert Content

### Email Template

The daily alert includes:

1. **Header** — Date, time, branding
2. **Daily Summary** — P&L, trades, active users, customer count, health
3. **Top 5 Performers** — Table with win rate, P&L, trade count, tier
4. **New Customers** — List of signups from today
5. **Upsell Opportunities** — High-win-rate traders ready for premium
6. **System Health** — Database status (healthy/degraded/error)
7. **Footer** — Contact info, timestamp

### Alert Triggers

Alerts are sent even if:
- No trades today (shows "No trading activity")
- Database is degraded (marks health as red)
- Telegram/Slack fails (email still sent)

Email always succeeds unless sender misconfigured.

---

## Troubleshooting

### Alert not sent

**Check:**
1. Is cron/systemd timer active?
   ```bash
   crontab -l  # for cron
   sudo systemctl status daily_alerts.timer  # for systemd
   ```

2. Is `ALERT_EMAIL` set correctly?
   ```bash
   echo $ALERT_EMAIL
   ```

3. Are credentials configured?
   ```bash
   python3 -c "import os; print('Gmail:', os.getenv('GMAIL_USER'))"
   ```

4. Is the database at the right path?
   ```bash
   ls -la $(echo $CLIENTS_DB_PATH)
   ```

5. Check logs:
   ```bash
   tail -100 daily_alerts.log | grep ERROR
   ```

### Email provider fails

**Gmail:**
```
Error: (535, b'5.7.8 Username and password not accepted')
```
→ Check app password at https://myaccount.google.com/apppasswords

**SendGrid:**
```
Error: Invalid API key
```
→ Verify API key has "Mail Send" permission

**AWS SES:**
```
Error: An error occurred (MessageRejected) when calling the SendEmail operation
```
→ Verify email domain is verified and not in sandbox

### Database errors

```
Error querying daily P&L: database is locked
```

→ Close any other connections to clients.db or check for concurrent access

### Time zone issues

The system uses UTC internally. Cron times are:
- **5 PM MST (summer)** = 23:00 UTC
- **6 PM MST (winter)** = 00:00 UTC

Check your current offset:
```bash
date +%Z
# MST (summer daylight) or MDT (winter standard) — may be labeled opposite in some timezones
```

---

## Manual Alert Trigger

To send an alert outside the scheduled time:

```bash
# From the runtime directory
python3 daily_alerts.py

# With verbose output
python3 daily_alerts.py --verbose

# To a different email
python3 daily_alerts.py --email alert-test@example.com

# Dry run (no send)
python3 daily_alerts.py --dry-run

# Inspect generated alert
python3 -c "
from daily_alerts import DailyAlertOrchestrator
o = DailyAlertOrchestrator('clients.db')
a = o.generate_alert()
print(f'P&L: \${a.total_daily_pnl:,.2f}')
print(f'Trades: {a.total_daily_trades}')
print(f'Performers: {len(a.top_performers)}')
"
```

---

## Production Checklist

Before deploying to production:

- [ ] Email provider configured and tested
- [ ] `ALERT_EMAIL` set to `dispatch@alreadyherellc.com` (no placeholders)
- [ ] Database path correct (`CLIENTS_DB_PATH`)
- [ ] Scheduler running (cron or systemd)
- [ ] Manual test alert sent successfully
- [ ] Log files have write permissions
- [ ] Backup `.env` file (never commit secrets)
- [ ] Monitoring in place to detect alert failures
- [ ] Telegram/Slack webhooks tested (optional)
- [ ] Email templates reviewed for branding

---

## Support

For issues:
1. Check `daily_alerts.log`
2. Run `python3 daily_alerts.py --verbose` for debug output
3. Verify environment variables: `env | grep -E "EMAIL|ALERT|TELEGRAM|SLACK"`
4. Test email provider directly (see Email Provider Setup)

---

## Files Generated

- `daily_alerts.py` — Main alert engine
- `daily_alerts.log` — Execution log (auto-created)
- `daily_alerts_cron.sh` — Cron job script
- `daily_alerts.service` — Systemd service file
- `daily_alerts.timer` — Systemd timer (5 PM MST)
- `.env` — Configuration (create manually)

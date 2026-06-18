# ProfitEngine Daily Alerts System

Professional automated email/notification system for market close summaries (5 PM MST).

---

## Quick Overview

**What:** Automated daily alerts sent to `dispatch@alreadyherellc.com`  
**When:** Every day at 5 PM MST (23:00 UTC during daylight saving)  
**Content:** Top traders, new signups, upsell candidates, system health, P&L  
**Delivery:** Email (Gmail/SendGrid/AWS SES) + optional Telegram/Slack  
**Scheduling:** Cron job or systemd timer  

---

## Files Included

```
runtime/
├── daily_alerts.py              # Main alert engine (1300+ lines)
├── daily_alerts_cron.sh         # Cron job wrapper script
├── daily_alerts.service         # Systemd service file
├── daily_alerts.timer           # Systemd timer (5 PM MST)
├── test_daily_alerts.py         # Test suite (all 6 tests pass)
├── DAILY_ALERTS_SETUP.md        # Detailed setup guide
├── daily_alerts.env.example     # Configuration template
└── DAILY_ALERTS_README.md       # This file
```

---

## 5-Minute Setup

### 1. Copy Configuration Template
```bash
cp daily_alerts.env.example .env
```

### 2. Edit `.env`
```bash
# Set these required values:
EMAIL_PROVIDER=gmail
GMAIL_USER=your-gmail@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx     # From Google: https://myaccount.google.com/apppasswords
ALERT_EMAIL=dispatch@alreadyherellc.com    # No placeholders!
CLIENTS_DB_PATH=clients.db                 # Path to your database
```

### 3. Test Locally
```bash
python3 daily_alerts.py --dry-run --verbose
# Should output alert summary without sending
```

### 4. Send Test Alert
```bash
python3 daily_alerts.py
# Should deliver email to your inbox
```

### 5. Schedule (Choose One)

**Option A: Cron (Linux)**
```bash
crontab -e
# Add this line:
0 23 * * * cd /home/opc/profitengine/runtime && /usr/bin/python3 daily_alerts.py >> daily_alerts.log 2>&1
```

**Option B: Systemd (Linux, preferred)**
```bash
sudo cp daily_alerts.service /etc/systemd/system/
sudo cp daily_alerts.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable daily_alerts.timer
sudo systemctl start daily_alerts.timer
```

---

## Alert Content

The daily email includes 6 sections:

### 1. Daily Summary
```
Total Daily P&L:  $1,234.56
Trades Executed:  47
Active Traders:   12
Total Customers:  143
System Health:    HEALTHY
```

### 2. Top 5 Performers
Professional table showing:
- Trader name
- Win rate percentage
- Today's P&L
- Number of trades
- Subscription tier

### 3. New Customers
List of signups from today with email and stats

### 4. Upsell Opportunities
High-win-rate traders ready for premium upgrades:
- Win rate >= 70% → Hybrid Tier candidate
- Win rate >= 85% → White-Label / Enterprise candidate

### 5. System Health
- Database integrity check
- Status badge (healthy/degraded/error)

### 6. Footer
Professional branding and contact info

---

## Email Providers

### Gmail (Easiest)
1. Enable 2-factor auth on Gmail
2. Generate app password: https://myaccount.google.com/apppasswords
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=gmail
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

### SendGrid (High Volume)
1. Create account at sendgrid.com
2. Generate API key with "Mail Send" permission
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=SG.xxx...
   ```

### AWS SES (Enterprise)
1. Verify domain and setup SES account
2. Create IAM user with SES permission
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=aws_ses
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_SES_REGION=us-east-1
   ```

---

## Optional: Telegram & Slack

### Telegram Alerts
```bash
# 1. Create bot via @BotFather on Telegram
# 2. Get chat ID from group messages
# 3. Add to .env:
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

### Slack Alerts
```bash
# 1. Create webhook: https://api.slack.com/messaging/webhooks
# 2. Copy webhook URL
# 3. Add to .env:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## Verification

### Check Scheduler Status

**Cron:**
```bash
crontab -l                    # List cron jobs
sudo journalctl -u cron       # View cron logs
```

**Systemd:**
```bash
sudo systemctl list-timers daily_alerts.timer
sudo systemctl status daily_alerts.timer
sudo journalctl -u daily_alerts.service -f    # Watch logs
```

### View Sent Alerts
```bash
tail -f runtime/daily_alerts.log
grep "Email sent successfully" runtime/daily_alerts.log | wc -l
```

### Manual Trigger
```bash
# Test outside scheduled time
python3 daily_alerts.py --verbose

# Trigger systemd service immediately
sudo systemctl start daily_alerts.service
```

---

## Database Schema Required

The system queries these tables from `clients.db`:

### `clients` table
```sql
client_id TEXT PRIMARY KEY
username TEXT
email TEXT
account_balance REAL
total_trades INTEGER
winning_trades INTEGER
losing_trades INTEGER
created_at TIMESTAMP
last_trade_at TIMESTAMP
subscription_tier TEXT
```

### `trades` table
```sql
trade_id TEXT PRIMARY KEY
client_id TEXT
symbol TEXT
side TEXT
entry_price REAL
exit_price REAL
shares INTEGER
pnl_usd REAL
win BOOLEAN
executed_at TIMESTAMP
```

---

## Key Features

### Robust Error Handling
- Gracefully handles missing credentials
- Logs all email sends and failures
- Database connection errors don't crash system
- Retry logic for transient failures

### Secure Configuration
- All secrets in `.env` (never commit!)
- No hardcoded credentials
- Support for environment variable injection

### Professional Templates
- Responsive HTML email
- Plain text fallback
- Color-coded P&L (green = profit, red = loss)
- Mobile-friendly design

### Multiple Notification Channels
- Primary: Email (mandatory)
- Optional: Telegram (for real-time alerts)
- Optional: Slack (for team notifications)

### Comprehensive Logging
- All alert executions logged
- Email delivery status tracked
- Error messages with full context
- Separate log file (daily_alerts.log)

---

## Troubleshooting

### Alert not sending
```bash
# Check configuration
env | grep -E "EMAIL|ALERT|GMAIL"

# Verify database exists
ls -la clients.db

# Check logs
tail -50 daily_alerts.log | grep ERROR

# Test with verbose output
python3 daily_alerts.py --verbose
```

### Gmail app password issues
```
Error: (535, b'5.7.8 Username and password not accepted')
```
- Verify 2-factor auth is enabled
- Re-generate app password at https://myaccount.google.com/apppasswords
- Use exact 16-character password (with or without spaces)

### Database locked
```
Error: database is locked
```
- Close other connections to clients.db
- Check for concurrent access
- Verify write permissions

### Wrong time zone
- Check UTC offset: `date +%Z`
- 5 PM MST = 23:00 UTC (summer) or 00:00 UTC (winter)
- Adjust systemd timer `OnCalendar` as needed

---

## Performance Notes

- **Query time:** < 1 second (50-200 clients)
- **Email send:** 2-5 seconds (depends on provider)
- **Log size:** ~500 bytes per alert
- **Database size:** No growth (queries don't write to clients.db)

---

## API Reference

### Minimal Usage
```python
from daily_alerts import DailyAlertOrchestrator

orchestrator = DailyAlertOrchestrator("clients.db")
alert_data = orchestrator.generate_alert()
orchestrator.send_alerts(alert_data)
```

### Custom Email Recipient
```bash
python3 daily_alerts.py --email custom@example.com
```

### Dry Run (no send)
```bash
python3 daily_alerts.py --dry-run
```

### Verbose Logging
```bash
python3 daily_alerts.py --verbose
```

---

## Testing

### Run Test Suite
```bash
python3 test_daily_alerts.py
# Output: 6/6 tests passed
```

**Tests validate:**
- Database query correctness
- Email template generation
- Alert orchestration
- CLI argument parsing
- Email provider initialization
- Notification channel fallbacks

---

## Production Checklist

- [ ] Gmail app password generated (2-factor auth enabled)
- [ ] `.env` file created with real values (no placeholders)
- [ ] `ALERT_EMAIL` set to `dispatch@alreadyherellc.com`
- [ ] Manual test alert sent successfully
- [ ] Scheduler active (cron or systemd)
- [ ] Log file location writable
- [ ] Backup `.env` file (never commit to git)
- [ ] Database path correct
- [ ] Email templates reviewed
- [ ] (Optional) Telegram/Slack credentials working

---

## Monitoring

### Alert Success Rate
```bash
# Count successful sends
grep "Email sent successfully" daily_alerts.log | wc -l

# Monitor in real-time
tail -f daily_alerts.log | grep "Email"
```

### Detect Failures
```bash
# Find all errors
grep ERROR daily_alerts.log

# Find missing credentials
grep "not configured" daily_alerts.log

# Check database health
grep "database" daily_alerts.log
```

---

## Extending the System

### Add Custom Metrics
Edit `DatabaseQueries.get_daily_pnl_summary()` to include your metrics.

### Change Alert Time
Edit systemd timer or cron:
```bash
# 9:30 AM ET (market open)
0 13 * * * ...

# 4:00 PM ET (early close alert)
20 16 * * * ...
```

### Add Custom Notification Channel
Implement new function following `send_telegram_alert()` pattern.

---

## Support & Documentation

- **Setup details:** See DAILY_ALERTS_SETUP.md
- **Configuration template:** daily_alerts.env.example
- **Test suite:** test_daily_alerts.py
- **Main code:** daily_alerts.py (well-documented)

---

## Version History

**v1.0 (2026-06-18)**
- Initial release
- 5 PM MST schedule
- Gmail/SendGrid/AWS SES support
- Telegram/Slack optional alerts
- Comprehensive test suite (6/6 passing)
- Professional HTML email templates

---

## License & Notes

Production-ready system for ProfitEngine autonomous trading platform.
- No placeholder values allowed
- All real credentials required before deployment
- Email recipient: dispatch@alreadyherellc.com
- Database queries read-only (no data modification)

---

**Last Updated:** June 18, 2026  
**Status:** Production Ready  
**Test Results:** 6/6 tests passing

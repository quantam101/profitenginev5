# Daily Trading Alerts — Setup Complete ✓

## What Was Missing

Your 5 PM trading alert system existed but had **two missing pieces**:

1. **No scheduler** ❌ → **FIXED** ✓ (added `.github/workflows/daily-alerts.yml`)
2. **Email not configured** ❌ → **NEEDS SETUP** (add GitHub Secrets)

---

## ✓ What's Now Running

**Daily Alert Workflow**: Runs **Monday–Friday at 5 PM MST** (midnight UTC next day)

- **File**: `.github/workflows/daily-alerts.yml`
- **Trigger**: Cron `0 0 * * 1-5` (5 PM MST)
- **Database**: Downloads latest `clients.db` from `PROFITENGINE_DB_URL` secret
- **Action**: Generates and sends email alert via Gmail, SendGrid, or AWS SES

---

## 🔧 Database Schema Fixed

Updated `runtime/daily_alerts.py` to use correct column names:
- `user_id` (was: `client_id`)
- `pnl_dollars` (was: `pnl_usd`)
- `daily_trades` table (was: `trades`)

---

## ⚡ Setup Required: Email Provider

Choose **one** email provider and add these GitHub Secrets:

### Option 1: Gmail (Recommended)
1. Go to [Google Account > App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Windows Computer"
3. Copy the generated password
4. Add to GitHub Secrets:
   ```
   GMAIL_USER = your-email@gmail.com
   GMAIL_APP_PASSWORD = [paste 16-char password]
   ```

### Option 2: SendGrid
1. Go to [SendGrid API Keys](https://app.sendgrid.com/settings/api_keys)
2. Create a new API key
3. Add to GitHub Secrets:
   ```
   SENDGRID_API_KEY = [paste key]
   EMAIL_PROVIDER = sendgrid
   ```

### Option 3: AWS SES
Add to GitHub Secrets:
```
AWS_ACCESS_KEY_ID = [your key]
AWS_SECRET_ACCESS_KEY = [your secret]
AWS_SES_REGION = us-east-1
EMAIL_PROVIDER = aws_ses
```

### All Options: Recipient Email
Add to GitHub Secrets:
```
ALERT_EMAIL = dispatch@alreadyherellc.com
```

---

## 📊 Alert Contents (5 PM MST)

The email includes:

1. **Daily Summary**
   - Total P&L for the day
   - Number of trades executed
   - Active traders count
   - System health status

2. **Top 5 Performers**
   - Win rate, daily P&L, trade count, subscription tier

3. **New Customer Signups**
   - Count and details of new registrations

4. **Upsell Opportunities**
   - High-performing clients ready for tier upgrades
   - Sales messaging per tier

5. **Alternative Channels** (optional)
   - Telegram: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
   - Slack: `SLACK_WEBHOOK_URL`

---

## 🧪 Test It Now

Run manually (before committing):
```bash
python runtime/daily_alerts.py --dry-run
```

Or with email send:
```bash
GMAIL_USER=your@gmail.com \
GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx" \
ALERT_EMAIL=dispatch@alreadyherellc.com \
python runtime/daily_alerts.py
```

---

## 📅 Schedule Reference

| Time | Action | Status |
|------|--------|--------|
| 5 PM MST (12 AM UTC) | Daily Trading Alert | ✓ Scheduled |
| 6 PM MST (1 AM UTC) | Daily Metrics Report | ✓ Scheduled |
| 7 AM UTC | Content Pipeline | ✓ Scheduled |

---

## Next Steps

1. **Add Gmail credentials to GitHub Secrets**
   - Go to repository Settings → Secrets and variables → Actions
   - Add `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL`

2. **Test the workflow** (optional)
   - Go to Actions → Daily Trading Alert
   - Click "Run workflow" → "Run workflow"
   - Check the logs for success/failure

3. **Wait for 5 PM MST tomorrow** to receive the first automated alert

---

Generated: 2026-06-18 by Claude Code

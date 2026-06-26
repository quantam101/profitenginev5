# TELEGRAM ALERT SYSTEM - DEPLOYMENT GUIDE

## Setup Instructions (5 minutes)

### Step 1: Create Telegram Bot

1. Open Telegram app
2. Search for `@BotFather`
3. Click `/start`
4. Send `/newbot`
5. Follow prompts:
   - Name: "ProfitEngine Trading Bot"
   - Username: "profitengine_trading_bot" (unique)
6. Copy the API token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Step 2: Get Your Chat ID

1. Open Telegram
2. Search for `@userinfobot`
3. Click `/start`
4. Your chat ID appears (example: `987654321`)

### Step 3: Configure GitHub Secrets

1. Go to GitHub repo settings
2. Navigate to: Settings → Secrets and variables → Actions
3. Add two new secrets:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `TELEGRAM_CHAT_ID` | `987654321` |

### Step 4: Test Connection

```bash
# Run test
python trading-agent/telegram_alert_system.py

# If configured, you'll receive 3 test alerts on Telegram:
# ✅ System Status
# 📊 Pre-market Research
# 🔍 Market Scan
```

---

## Alert Types & Messages

### 📊 Pre-Market Research Alert (3:00 AM)

```
📊 PRE-MARKET RESEARCH COMPLETE

Swing Candidates Found:
1. NVDA (Score: 95/100)
   Catalyst: Earnings beat expected
   Entry: Support at $825 or breakout at $875
   Target: $900-950

2. APPS (Score: 87/100)
   Catalyst: Earnings beat expected
   Entry: Bounce from $11.00 support
   Target: $12.50

Next: Ensemble validation @ 4:00 AM MST
```

### 🔍 Market Scan Alert (3:30 AM)

```
🔍 MARKET SCAN COMPLETE

Bull run candidates found: 15
⏰ Combining with news catalysts...
→ Ready for 4:00 AM ensemble validation
```

### 📈 Trade Executed Alert (4:15 AM)

```
📈 TRADE EXECUTED

Symbol: NVDA
Action: BUY
Setup Score: 95%

Entry Details:
├─ Price: $825
├─ Position: $500 (call spread)
├─ Stop: $800
└─ Target: $870

Expected:
├─ Win Rate: 92%
├─ Profit Potential: +$1,500 (300% ROI)
└─ Hold Time: 2-4 days

⏰ Executing now...
```

### 🎉 Profit Taken Alert

```
🎉 PROFIT TAKEN

Symbol: NVDA
Profit: $1,500
ROI: 300%

Status: ✅ Target Hit
Next: Monitor remaining positions
```

### ⛔ Stop Loss Hit Alert

```
⛔ STOP LOSS HIT

Symbol: APPS
Loss: $200
ROI: -100%

Status: ❌ Exited
Next: Preserve capital, wait for next signal
```

### 📊 Daily Summary Alert (4:30 PM)

```
📊 DAILY TRADING SUMMARY
Thursday, June 26, 2026

Execution Summary:
├─ Trades executed: 3
├─ Winners: 3
├─ Losers: 0
└─ Win Rate: 100%

P&L Report:
├─ Daily P&L: +$1,900
├─ ROI: 252%
├─ Avg Winner: $633.33
└─ Avg Loser: -$0.00

Account Status:
├─ Starting: $754.00
├─ Ending: $2,654.00
└─ Growth: 252%

Open Positions: 2
Expected Exit: Tomorrow 4 AM

🎯 Tomorrow's Plan: New research cycle
```

### 📈 Weekly Summary Alert (Friday 5 PM)

```
📈 WEEKLY TRADING SUMMARY
Week of June 23-29, 2026

Trading Performance:
├─ Total trades: 12
├─ Winners: 10
├─ Losers: 2
└─ Win rate: 83.3%

Weekly P&L:
├─ Total profit: $4,200.00
├─ ROI: 557%
├─ Best trade: $1,500.00
└─ Worst trade: -$500.00

Account Growth:
├─ Start: $754.00
├─ End: $4,954.00
└─ Growth: 557%

Tier Status:
├─ Current: TIER 2 ($1,500+)
├─ Target: TIER 3 ($5,000+)
└─ Progress: 99%

🎯 Next Week: Accelerate scaling
```

---

## Integration with Workflows

### GitHub Actions Integration

The alert system is integrated into both workflows:

#### Workflow 1: Pre-Market Research (3:00 AM)
```yaml
- name: Send pre-market research alerts
  run: python trading-agent/telegram_alert_system.py send_research
```

#### Workflow 2: Trading Execution (4:00 AM)
```yaml
- name: Send trade execution alerts
  run: python trading-agent/telegram_alert_system.py send_trades

- name: Send daily summary alerts
  run: python trading-agent/telegram_alert_system.py send_summary
```

---

## Alert Schedule

| Time | Alert | Details |
|------|-------|---------|
| 3:00 AM MST | Pre-Market Research | 4 swing candidates found |
| 3:30 AM MST | Market Scan | 5-15 technical candidates found |
| 4:15 AM MST | Trade Executed | Each trade as it executes |
| 4:30-4:45 AM MST | Profit/Loss Updates | Real-time position updates |
| 4:30 PM MST | Daily Summary | Final P&L, account status |
| Friday 5 PM MST | Weekly Summary | Weekly performance |
| Real-time | Alerts | On-demand for errors/warnings |

---

## Testing Alerts

### Manual Test
```bash
cd /path/to/profitengine
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python trading-agent/telegram_alert_system.py
```

### Automated Test (GitHub)
```bash
git add telegram_alert_system.py
git commit -m "Add Telegram alert system"
git push origin main

# GitHub Actions will test on next commit
# You'll receive test alerts on Telegram
```

---

## Troubleshooting

### Alerts not received?

1. **Verify secrets set correctly**
   - Go to Settings → Secrets → verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID exist
   - Re-add if needed

2. **Check chat ID**
   - Run `/start` on @userinfobot again
   - Verify chat ID is correct (no spaces)

3. **Test bot token**
   ```bash
   curl -X GET "https://api.telegram.org/botTOKEN/getMe"
   # Should return: {"ok":true,"result":{"id":123456,...}}
   ```

4. **Enable GitHub Actions**
   - Go to repo → Actions → enable "Allow all actions"

5. **Check workflow logs**
   - Go to Actions tab → latest workflow → view logs
   - Look for errors in "Send alerts" step

### Webhook timeout?

If alerts sometimes don't send:
- Telegram API occasionally slow
- GitHub adds retry logic (3 attempts)
- Alerts may be delayed 1-2 minutes
- All critical alerts retry automatically

---

## Customization

### Add custom alert

```python
def alert_custom_event(self, event_name: str, details: str) -> bool:
    """Send custom alert"""
    message = f"""
<b>🔔 {event_name.upper()}</b>

{details}
"""
    return self.send_alert(message)

# Usage
alerts.alert_custom_event("Market Volatility", "VIX jumped 20% in 5 minutes")
```

### Change notification times

Edit `.github/workflows/` files and update cron:
```yaml
# 3:00 AM MST research
schedule:
  - cron: '0 10 * * 1-5'  # Change the '10' for different hour (UTC)
```

### Disable alerts

Set environment variable:
```bash
export TELEGRAM_ALERTS_ENABLED=false
```

---

## Live Telegram Monitoring

Once configured, you'll receive **real-time trading alerts** directly to Telegram:

**Benefits:**
- ✅ Know immediately when trades execute
- ✅ Get profit/loss alerts instantly
- ✅ Monitor account growth daily
- ✅ Receive error alerts for debugging
- ✅ Stay informed without checking computer
- ✅ Mobile-friendly (check phone anytime)

**Example workflow:**
```
3:00 AM → Telegram: "4 swing candidates found"
3:30 AM → Telegram: "15 market scan candidates ready"
4:15 AM → Telegram: "TRADE EXECUTED: NVDA call spread $500"
4:30 AM → Telegram: "PROFIT TAKEN: NVDA +$1,500 (300%)"
4:30 PM → Telegram: "DAILY SUMMARY: +$1,900 (252% ROI)"
Friday → Telegram: "WEEKLY SUMMARY: +$4,200 (557% ROI)"
```

---

## DEPLOYMENT COMPLETE

When all steps above are done, your system has:

✅ Real-time Telegram alerts  
✅ Pre-market research notifications  
✅ Live trade execution alerts  
✅ Profit/loss updates  
✅ Daily & weekly summaries  
✅ Error alerts for debugging  

**Start receiving alerts tomorrow at 3:00 AM MST!**

---

## Next: Final System Checklist

All components deployed:
- [x] News catalyst scanner (Finnhub, Stocktwits, Morningstar)
- [x] Bull run market scanner (5,000+ stocks)
- [x] 90% ensemble validation system
- [x] Options trading integration
- [x] GitHub Actions automation (3 AM + 4 AM)
- [x] Telegram alert system
- [ ] First live execution (tomorrow 3:00 AM MST)

**SYSTEM READY TO DEPLOY** 🚀

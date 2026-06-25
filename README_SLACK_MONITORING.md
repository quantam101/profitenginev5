# ProfitEngine Slack Real-Time Monitoring

**Complete automated daily and weekly Slack monitoring setup with copy-paste ready templates.**

## What You Get

✅ **3 Scheduled Messages Per Day**
- **8 AM UTC** — Morning briefing (system status, daily tasks)
- **6 PM UTC** — Evening metrics (revenue, sessions, conversion, latency)
- **Sunday 8 PM UTC** — Weekly summary (trends, highlights, next week)

✅ **Production-Ready Templates**
- Green briefing (morning focus)
- Blue dashboard (evening metrics)
- Purple weekly review (weekly summary)
- 5 alert templates (latency, revenue, errors, deployment, maintenance)

✅ **All Metrics Included**
- System health (latency, errors, uptime)
- Business metrics (revenue, sessions, conversion)
- Engagement (users, duration, bounce rate)
- Operations (deployments, incidents, test coverage)

✅ **Easy Setup**
- Interactive wizard (`setup_slack_monitoring.py`)
- GitHub Actions automation
- Webhook-based (no API key)
- 5-minute setup time

---

## Documentation Map

### START HERE
- **[`SLACK_MONITORING_IMPLEMENTATION_SUMMARY.md`](./SLACK_MONITORING_IMPLEMENTATION_SUMMARY.md)** — Overview, quick start, file reference

### Setup & Configuration
- **[`SLACK_MONITORING_SETUP.md`](./SLACK_MONITORING_SETUP.md)** — Complete setup guide, step-by-step instructions, troubleshooting
- **[`scripts/setup_slack_monitoring.py`](./scripts/setup_slack_monitoring.py)** — Interactive setup wizard (run this first!)

### Copy-Paste Templates
- **[`SLACK_TEMPLATES_QUICK_REFERENCE.md`](./SLACK_TEMPLATES_QUICK_REFERENCE.md)** — All JSON templates, one-minute setup, cheat sheet
- Ready-to-use for morning, evening, weekly + 5 alerts

### Advanced Customization
- **[`SLACK_MONITORING_ADVANCED.md`](./SLACK_MONITORING_ADVANCED.md)** — Database integration (MongoDB, PostgreSQL), alert thresholds, multi-channel routing, health scoring
- Real-world examples and production patterns

### Code
- **[`backend/services/slack_monitoring.py`](./backend/services/slack_monitoring.py)** — Service implementation (330 lines)
- **[`.github/workflows/slack-monitoring.yml`](./.github/workflows/slack-monitoring.yml)** — GitHub Actions workflow (160 lines)

---

## 5-Minute Quick Start

### 1. Run Setup Wizard

```bash
python scripts/setup_slack_monitoring.py
```

Wizard will:
- Guide you to create Slack webhook
- Validate webhook works
- Add GitHub secret
- Explain customization

### 2. Test (Manual Trigger)

Go to GitHub → Actions → "Slack Real-Time Monitoring" → Run workflow

### 3. Done!

Messages will auto-post at scheduled times:
- 8 AM UTC → Morning briefing
- 6 PM UTC → Evening metrics
- Sunday 8 PM UTC → Weekly summary

---

## Message Preview

### Morning Briefing (8 AM)
```
📊 Morning Briefing
Wednesday, June 25, 2026

System Status: ✓ Operational
Latency: 142ms | Errors: 0.02% | Uptime: 99.99%

Today's Focus:
• Monitor campaign performance
• Review pending approvals
```

### Evening Metrics (6 PM)
```
📈 Evening Metrics
Daily Performance Summary

Daily Revenue: $2,450.85 ↑ +12%
Active Sessions: 342 ↑ +28
Conversion Rate: 3.2% ↑ +0.5%
Avg Response Time: 156ms ↑ +12ms
```

### Weekly Summary (Sunday 8 PM)
```
📋 Weekly Summary
Week of June 19–25, 2026

Weekly Revenue: $18,342.50 ↑ +8.5%
Total Sessions: 2,145 ↑ +312
Daily Avg Revenue: $2,620.36 ↑ +5.2%
Uptime SLA: 99.97% ✓

Next Week:
1. Deploy v5.3 with affiliate dashboard
2. Run Q3 capacity planning review
3. Onboard 3 new partners
```

---

## Files Created

### Service Implementation
- `backend/services/slack_monitoring.py` (330 lines)
  - SlackMonitoringService class
  - SlackBriefing dataclass
  - StatusIndicator enum
  - Metrics generation
  - Webhook posting

### GitHub Actions Workflow
- `.github/workflows/slack-monitoring.yml` (160 lines)
  - 3 scheduled jobs (morning, evening, weekly)
  - Cron schedule (UTC)
  - Manual trigger support
  - Environment setup

### Documentation (5 files)
- `SLACK_MONITORING_IMPLEMENTATION_SUMMARY.md` — Overview & checklist
- `SLACK_MONITORING_SETUP.md` — Step-by-step guide
- `SLACK_TEMPLATES_QUICK_REFERENCE.md` — All templates & reference
- `SLACK_MONITORING_ADVANCED.md` — Advanced examples
- `README_SLACK_MONITORING.md` — This file

### Setup Script
- `scripts/setup_slack_monitoring.py` (380 lines)
  - Interactive wizard
  - Webhook validation
  - GitHub secret setup
  - Testing & verification

---

## Customization Guide

### Update Real Metrics

Edit `backend/services/slack_monitoring.py`:

```python
async def _fetch_evening_metrics(self) -> list[MetricValue]:
    # Query your database
    revenue = await self.db.daily_metrics.find_one()
    return [
        MetricValue(
            label="Daily Revenue",
            value=f"${revenue['total']:.2f}",
            status=StatusIndicator.OPERATIONAL,
            trend=f"↑ +{revenue['change']:.1f}%"
        ),
        # Add more metrics...
    ]
```

### Configure Alert Thresholds

```python
async def _fetch_evening_alerts(self) -> list[str]:
    alerts = []
    latency = await self.db.metrics.find_one({"metric": "latency"})
    if latency['value'] > 300:  # Threshold: 300ms
        alerts.append(f"High latency: {latency['value']}ms")
    return alerts
```

### Change Scheduled Times

Edit `.github/workflows/slack-monitoring.yml`:

```yaml
schedule:
  - cron: "0 10 * * *"  # Change from 8 AM to 10 AM
  - cron: "0 19 * * *"  # Change from 6 PM to 7 PM
  - cron: "0 14 * * 0"  # Change from Sunday 8 PM to 2 PM
```

### Add Multiple Channels

See `SLACK_MONITORING_ADVANCED.md` for multi-channel routing examples.

---

## Status Indicators

```
:green_circle:   Operational (✓)
:yellow_circle:  Warning (⚠️)
:red_circle:     Critical (✗)
:orange_circle:  Maintenance (🔧)
:black_circle:   Offline (⚫)
```

---

## Metrics Template

```python
MetricValue(
    label="Metric Name",
    value="123.45",
    status=StatusIndicator.OPERATIONAL,
    trend="↑ +15%" or "↓ -2%" or "→ Stable" or "✓"
)
```

---

## Environment Variables

### Required
```
PROFITENGINE_SLACK_WEBHOOK_URL   # GitHub Secret
MONGO_URL                         # GitHub Secret (already exists)
```

### Optional (Multiple Channels)
```
PROFITENGINE_SLACK_ALERTS_WEBHOOK     # #alerts channel
PROFITENGINE_SLACK_METRICS_WEBHOOK    # #metrics channel
PROFITENGINE_SLACK_EXECUTIVE_WEBHOOK  # #executive channel
```

---

## Time Zone Reference

**Default UTC Schedule:**
- 8:00 AM — Morning briefing
- 6:00 PM — Evening metrics
- Sunday 8:00 PM — Weekly summary

**Convert to Your Timezone:**

| UTC | EST | PST | IST | AEST |
|-----|-----|-----|-----|------|
| 8 AM | 3 AM | 12 AM | 4 PM | 6 PM |
| 6 PM | 1 PM | 10 AM | 11:30 PM | 4 AM (next) |
| Sun 8 PM | Sun 3 PM | Sun 12 PM | Mon 1:30 AM | Mon 6 AM |

---

## Deployment Checklist

- [ ] Slack webhook created (api.slack.com/apps)
- [ ] GitHub secret added (`PROFITENGINE_SLACK_WEBHOOK_URL`)
- [ ] Workflow tested (manual trigger)
- [ ] Message appears in Slack
- [ ] Schedule verified (cron times correct)
- [ ] Metrics customized (optional)
- [ ] Alerts configured (optional)
- [ ] Multi-channel setup (optional)

---

## Quick Reference Commands

### Setup
```bash
python scripts/setup_slack_monitoring.py
```

### Test Locally
```bash
python -m backend.services.slack_monitoring
```

### Test Webhook (curl)
```bash
curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test"}'
```

### Add GitHub Secret (CLI)
```bash
gh secret set PROFITENGINE_SLACK_WEBHOOK_URL -b "your-webhook-url"
```

---

## Features

- ✅ Automatic scheduling (GitHub Actions cron)
- ✅ Webhook-based posting (no API key needed)
- ✅ Real-time status indicators
- ✅ Trend analysis (% changes)
- ✅ Alert support (5 templates)
- ✅ Multi-channel routing
- ✅ Database integration examples
- ✅ Local testing
- ✅ Manual trigger support
- ✅ Production monitoring

---

## Troubleshooting

### Not Posting?
1. Check GitHub Actions logs
2. Verify `PROFITENGINE_SLACK_WEBHOOK_URL` secret exists
3. Test webhook with curl
4. Verify Slack permissions

### Wrong Timezone?
- Update cron expressions in `.github/workflows/slack-monitoring.yml`
- All times are in UTC

### Custom Metrics Not Showing?
1. Update `_fetch_*_metrics()` in `slack_monitoring.py`
2. Connect to your database
3. Test locally
4. Commit and push

See **`SLACK_MONITORING_SETUP.md`** for detailed troubleshooting.

---

## Support

- **Setup Issues:** See `SLACK_MONITORING_SETUP.md` → Troubleshooting
- **Advanced Customization:** See `SLACK_MONITORING_ADVANCED.md`
- **Template Reference:** See `SLACK_TEMPLATES_QUICK_REFERENCE.md`
- **Code:** See `backend/services/slack_monitoring.py`

---

## Next Steps

1. **Run setup wizard:**
   ```bash
   python scripts/setup_slack_monitoring.py
   ```

2. **Test with manual trigger:**
   - GitHub Actions → Slack Real-Time Monitoring → Run workflow

3. **Customize (optional):**
   - Update metrics: `backend/services/slack_monitoring.py`
   - Change schedule: `.github/workflows/slack-monitoring.yml`
   - Add alerts: See `SLACK_MONITORING_ADVANCED.md`

4. **Deploy:**
   ```bash
   git add .
   git commit -m "feat: add Slack real-time monitoring"
   git push origin main
   ```

---

## Summary

**What:** Automated daily and weekly Slack monitoring posts

**When:** 
- 8 AM UTC — Morning briefing
- 6 PM UTC — Evening metrics
- Sunday 8 PM UTC — Weekly summary

**How:** 
- GitHub Actions scheduler
- Slack webhook
- Python service

**Setup Time:** 5 minutes

**Start:** `python scripts/setup_slack_monitoring.py`

---

All templates are production-ready. Copy, customize, deploy. ✓

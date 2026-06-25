# Slack Real-Time Monitoring — START HERE

**Complete real-time Slack monitoring setup with automated daily (8 AM, 6 PM) and weekly (Sunday 8 PM) posts.**

## What You're Getting

✅ **Fully Automated**
- 8 AM UTC → Morning briefing (system status)
- 6 PM UTC → Evening metrics (revenue, sessions)
- Sunday 8 PM UTC → Weekly summary (trends, priorities)

✅ **Production Ready**
- All templates included (copy-paste)
- All metrics examples provided
- All alert templates ready
- GitHub Actions workflow configured

✅ **No Code Required**
- Setup wizard handles everything
- Just paste webhook URL
- Automated scheduling
- Database integration optional

---

## Step-by-Step Setup (5 Minutes)

### Step 1: Create Slack Webhook

```
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. App Name: "ProfitEngine Monitoring"
4. Select your workspace
5. Sidebar → "Incoming Webhooks"
6. Toggle "Activate Incoming Webhooks" → ON
7. "Add New Webhook to Workspace"
8. Select channel (e.g., #profitengine-alerts)
9. Click "Allow"
10. Copy the Webhook URL
```

Webhook URL looks like:
```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

### Step 2: Run Setup Wizard

```bash
python scripts/setup_slack_monitoring.py
```

Wizard will:
- Ask for webhook URL (paste from Step 1)
- Test webhook connection
- Add GitHub secret `PROFITENGINE_SLACK_WEBHOOK_URL`
- Verify workflow setup
- Show customization options

### Step 3: Test (Manual Trigger)

1. Go to GitHub → **Actions** tab
2. Select **"Slack Real-Time Monitoring"** workflow
3. Click **"Run workflow"** dropdown
4. Select briefing type: `morning` or `evening` or `weekly`
5. Click **"Run workflow"**
6. Check Slack channel within 30 seconds

**Success:** Test message appears in Slack!

### Step 4: Done!

Messages will auto-post at scheduled times:
- **8:00 AM UTC** — Morning briefing
- **6:00 PM UTC** — Evening metrics
- **Sunday 8:00 PM UTC** — Weekly summary

---

## What Each Message Shows

### Morning Briefing (8 AM)

```
📊 Morning Briefing
Wednesday, June 25, 2026

Status: ✓ Operational        Latency: 142ms avg
Errors: 0.02%                Uptime: 99.99%

Today's Focus:
• Monitor campaign performance
• Review pending approvals
• Check affiliate metrics
```

### Evening Metrics (6 PM)

```
📈 Evening Metrics
Daily Performance Summary

Daily Revenue: $2,450.85 ↑ +12%
Active Sessions: 342 ↑ +28
Conversion Rate: 3.2% ↑ +0.5%
Avg Response Time: 156ms ↑ +12ms

Highlights:
• Revenue up 12% from yesterday
• Peak sessions: 487 concurrent users
• Zero critical errors
```

### Weekly Summary (Sunday 8 PM)

```
📋 Weekly Summary
Week of June 19–25, 2026

Weekly Revenue: $18,342.50 ↑ +8.5%
Total Sessions: 2,145 ↑ +312
Daily Avg Revenue: $2,620.36 ↑ +5.2%
Uptime SLA: 99.97% ✓

Week Highlights:
• Best day: Thursday (+18% revenue)
• Slowest: Tuesday (2m latency spike)
• Zero P1 incidents
• Conversion: 3.1% (stable)

Next Week:
1. Deploy v5.3 with affiliate dashboard
2. Run Q3 capacity planning review
3. Onboard 3 new partners
```

---

## All Files Included

### 📋 Core Implementation
1. **`backend/services/slack_monitoring.py`** (330 lines)
   - Service class with metrics generation
   - Webhook posting
   - Example metrics (ready for database)

2. **`.github/workflows/slack-monitoring.yml`** (160 lines)
   - GitHub Actions cron scheduler
   - 3 jobs: morning, evening, weekly
   - Manual trigger support

### 🚀 Setup & Automation
3. **`scripts/setup_slack_monitoring.py`** (380 lines)
   - Interactive setup wizard
   - Webhook validation
   - GitHub secret setup
   - Testing & verification

### 📚 Documentation
4. **`README_SLACK_MONITORING.md`**
   - Overview & quick reference
   - File map
   - Troubleshooting

5. **`SLACK_MONITORING_SETUP.md`** (420 lines)
   - Complete step-by-step guide
   - Customization examples
   - Metric reference
   - Alert templates
   - Troubleshooting

6. **`SLACK_TEMPLATES_QUICK_REFERENCE.md`** (320 lines)
   - All JSON templates (copy-paste)
   - Morning, evening, weekly templates
   - 5 alert templates
   - Status indicators
   - Cheat sheet

7. **`SLACK_MONITORING_ADVANCED.md`** (400 lines)
   - Real database integration (MongoDB, PostgreSQL)
   - Alert thresholds
   - Multi-channel routing
   - Health scoring
   - Production patterns

8. **`SLACK_MONITORING_IMPLEMENTATION_SUMMARY.md`**
   - Feature overview
   - File reference
   - Deployment checklist
   - All metrics by category

---

## Copy-Paste Quick Start

### Command: Run Setup
```bash
python scripts/setup_slack_monitoring.py
```

### Command: Test Locally
```bash
python -m backend.services.slack_monitoring
```

### Command: Test Webhook (curl)
```bash
curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'
```

### Command: Add GitHub Secret
```bash
gh secret set PROFITENGINE_SLACK_WEBHOOK_URL -b "your-webhook-url"
```

---

## Customization in 5 Minutes

### Add Real Metrics

Edit `backend/services/slack_monitoring.py`:

```python
async def _fetch_evening_metrics(self) -> list[MetricValue]:
    """Query your database."""
    doc = await self.db.daily_metrics.find_one()
    return [
        MetricValue(
            label="Daily Revenue",
            value=f"${doc['revenue']:.2f}",
            status=StatusIndicator.OPERATIONAL,
            trend=f"↑ +{doc['change']:.1f}%"
        )
    ]
```

### Add Alerts

```python
async def _fetch_evening_alerts(self) -> list[str]:
    """Check thresholds."""
    alerts = []
    latency = await self.db.metrics.find_one({"metric": "latency"})
    if latency['value'] > 300:
        alerts.append(f"High latency: {latency['value']}ms")
    return alerts
```

### Change Schedule Times

Edit `.github/workflows/slack-monitoring.yml`:

```yaml
schedule:
  - cron: "0 10 * * *"  # 10 AM UTC (instead of 8 AM)
  - cron: "0 19 * * *"  # 7 PM UTC (instead of 6 PM)
  - cron: "0 14 * * 0"  # Sun 2 PM UTC (instead of 8 PM)
```

---

## Environment Variables

### Required (Set in GitHub Secrets)

```
PROFITENGINE_SLACK_WEBHOOK_URL
```

Get from: https://api.slack.com/apps → Incoming Webhooks

### Optional (For Multiple Channels)

```
PROFITENGINE_SLACK_ALERTS_WEBHOOK      # #alerts channel
PROFITENGINE_SLACK_METRICS_WEBHOOK     # #metrics channel
PROFITENGINE_SLACK_EXECUTIVE_WEBHOOK   # #executive channel
```

---

## Time Zone Quick Reference

**Default times (UTC):**
- 8 AM → Morning briefing
- 6 PM → Evening metrics
- Sunday 8 PM → Weekly summary

**Convert to your timezone:**

| UTC Time | EST | PST | IST | AEST |
|----------|-----|-----|-----|------|
| 8 AM | 3 AM | 12 AM | 4 PM | 6 PM |
| 6 PM | 1 PM | 10 AM | 11:30 PM | 4 AM (next) |
| Sun 8 PM | Sun 3 PM | Sun 12 PM | Mon 1:30 AM | Mon 6 AM |

---

## Troubleshooting in 30 Seconds

| Problem | Solution |
|---------|----------|
| Not posting | Check `PROFITENGINE_SLACK_WEBHOOK_URL` GitHub secret |
| Wrong time | Update `cron` in `.github/workflows/slack-monitoring.yml` (UTC) |
| Wrong metrics | Update `_fetch_*_metrics()` in `slack_monitoring.py` |
| Test failed | Run `curl` command above to validate webhook |
| View logs | GitHub Actions → Slack Real-Time Monitoring → Latest run |

---

## Message Templates (Ready to Copy)

### Quick Test Template

```json
{
  "text": "Slack webhook is working!",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "✓ ProfitEngine Slack Monitoring Connected!"
      }
    }
  ]
}
```

### All Templates

See **`SLACK_TEMPLATES_QUICK_REFERENCE.md`** for:
- Morning briefing (complete JSON)
- Evening metrics (complete JSON)
- Weekly summary (complete JSON)
- 5 alert templates
- All status indicators
- All metric examples

---

## Status Indicators

```
:green_circle:   Operational (everything good)
:yellow_circle:  Warning (degraded, check soon)
:red_circle:     Critical (incident in progress)
:orange_circle:  Maintenance (scheduled downtime)
:black_circle:   Offline (service down)
```

---

## What's Included

✅ Service implementation (asyncio + motor + aiohttp)
✅ GitHub Actions workflow (automated cron scheduling)
✅ Setup wizard (interactive with validation)
✅ All templates (morning, evening, weekly, alerts)
✅ All documentation (guides, examples, troubleshooting)
✅ Real database examples (MongoDB, PostgreSQL)
✅ Alert integration (threshold-based)
✅ Multi-channel support (different channels per message)
✅ Health scoring (composite metrics)
✅ Production patterns (incident response, etc.)

---

## Next Steps

### Today (5 minutes)
1. Create Slack webhook (api.slack.com/apps)
2. Run setup wizard: `python scripts/setup_slack_monitoring.py`
3. Test with manual trigger: GitHub Actions → Run workflow

### This Week (30 minutes, optional)
1. Update metrics with real database queries
2. Configure alert thresholds
3. Change scheduled times if needed
4. Customize colors/emojis

### This Month (optional)
1. Add multi-channel routing
2. Implement health scoring
3. Connect incident management
4. Set up on-call alerting

---

## Quick File Reference

| Need | File |
|------|------|
| **Quick Start** | This file (SLACK_MONITORING_START_HERE.md) |
| **Full Guide** | SLACK_MONITORING_SETUP.md |
| **Templates** | SLACK_TEMPLATES_QUICK_REFERENCE.md |
| **Code Examples** | SLACK_MONITORING_ADVANCED.md |
| **Setup Wizard** | scripts/setup_slack_monitoring.py |
| **Service Code** | backend/services/slack_monitoring.py |
| **Workflow** | .github/workflows/slack-monitoring.yml |

---

## Commands You'll Need

```bash
# Run setup wizard (do this first!)
python scripts/setup_slack_monitoring.py

# Test locally
python -m backend.services.slack_monitoring

# Test webhook (paste your webhook URL)
export WEBHOOK="https://hooks.slack.com/services/..."
curl -X POST $WEBHOOK -H 'Content-Type: application/json' \
  -d '{"text":"Test"}'

# Add GitHub secret (if using gh CLI)
gh secret set PROFITENGINE_SLACK_WEBHOOK_URL -b "your-webhook-url"
```

---

## Support

- **Questions?** Check SLACK_MONITORING_SETUP.md
- **Need templates?** See SLACK_TEMPLATES_QUICK_REFERENCE.md
- **Want advanced setup?** Read SLACK_MONITORING_ADVANCED.md
- **Looking for code?** See backend/services/slack_monitoring.py
- **Stuck?** Review troubleshooting section above

---

## Summary

**What:** Automated Slack monitoring posts
**When:** Daily (8 AM, 6 PM) + Weekly (Sunday 8 PM)
**How:** GitHub Actions + Slack webhook + Python service
**Setup:** 5 minutes with setup wizard
**Cost:** Free (GitHub Actions + Slack webhook)

**Start now:**
```bash
python scripts/setup_slack_monitoring.py
```

---

**All templates are production-ready. Copy, customize, deploy.** ✓

*Last updated: June 25, 2026*

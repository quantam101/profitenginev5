# Slack Real-Time Monitoring — Implementation Summary

Complete real-time Slack monitoring setup with automated daily (8 AM, 6 PM) and weekly (Sunday 8 PM) posts.

---

## What You Get

✓ **Automated Scheduling**
- 8 AM UTC: Morning briefing (system status, daily tasks)
- 6 PM UTC: Evening metrics (revenue, sessions, conversion, latency)
- Sunday 8 PM UTC: Weekly summary (trends, highlights, next week priorities)

✓ **Production-Ready**
- GitHub Actions workflow with cron scheduling
- Slack incoming webhook integration
- Status indicators (green/yellow/red/orange)
- Trend analysis (↑ +12%, ↓ -2%, etc.)
- Custom alert support

✓ **Copy-Paste Ready**
- 3 complete message templates
- 5 alert templates
- All status indicators
- All metric examples

✓ **Easy Customization**
- Python service (asyncio + motor + aiohttp)
- Database integration examples (MongoDB, PostgreSQL)
- Alert thresholds
- Multi-channel routing
- Metrics computation

---

## Files Created

### Core Implementation

**1. `backend/services/slack_monitoring.py` (330 lines)**
   - Service class for Slack monitoring
   - SlackBriefing dataclass for message structure
   - StatusIndicator enum (green/yellow/red/orange/black)
   - MetricValue dataclass for metrics
   - Methods: `morning_briefing()`, `evening_metrics()`, `weekly_summary()`
   - Webhook posting with aiohttp
   - Example metrics (ready for database integration)

**2. `.github/workflows/slack-monitoring.yml` (160 lines)**
   - GitHub Actions workflow
   - 3 separate jobs: morning, evening, weekly
   - Cron schedule (UTC):
     - `0 8 * * *` — Morning at 8 AM
     - `0 18 * * *` — Evening at 6 PM
     - `0 20 * * 0` — Weekly Sunday at 8 PM
   - Manual trigger support (workflow_dispatch)
   - Python environment setup
   - Error handling with exit codes

### Documentation

**3. `SLACK_MONITORING_SETUP.md` (420 lines)**
   - Complete quick-start guide (5 minutes)
   - Step-by-step Slack webhook creation
   - GitHub Actions secret setup
   - Testing instructions
   - Customization examples (Python code)
   - Metrics reference (all metrics by category)
   - Alert templates (5 examples)
   - Troubleshooting guide
   - Production checklist

**4. `SLACK_TEMPLATES_QUICK_REFERENCE.md` (320 lines)**
   - Copy-paste ready JSON templates
   - Morning briefing template (green)
   - Evening metrics template (blue)
   - Weekly summary template (purple)
   - 5 alert templates (high latency, revenue drop, errors, deployment, maintenance)
   - Status indicators reference
   - Trend indicators reference
   - Metric examples (all categories)
   - 1-minute setup cheat sheet

**5. `SLACK_MONITORING_ADVANCED.md` (400 lines)**
   - Real database integration (MongoDB, PostgreSQL)
   - Advanced alert implementation (threshold-based)
   - Multi-channel routing (different channels)
   - Metric aggregation (weekly trends)
   - Incident response integration
   - Automated health checks (composite scoring)
   - Local testing script
   - Production monitoring checklist

### Setup Automation

**6. `scripts/setup_slack_monitoring.py` (380 lines)**
   - Interactive setup wizard
   - Colored terminal output
   - Step-by-step guidance
   - Slack webhook URL validation
   - Webhook testing (local curl or aiohttp)
   - GitHub secret setup (gh CLI or manual)
   - Metrics customization guide
   - Schedule verification
   - Manual trigger walkthrough
   - Next steps checklist

---

## Quick Start (5 minutes)

### 1. Run Setup Wizard

```bash
python scripts/setup_slack_monitoring.py
```

Wizard will:
- Guide you to create Slack incoming webhook
- Test webhook connection
- Add GitHub secret `PROFITENGINE_SLACK_WEBHOOK_URL`
- Verify workflow is enabled
- Show customization options

### 2. Test Workflow (Manual Trigger)

1. Go to GitHub → Actions → "Slack Real-Time Monitoring"
2. Click "Run workflow" → Select `morning` / `evening` / `weekly`
3. Click "Run workflow"
4. Check Slack channel within 30 seconds

### 3. Verify Automated Schedule

Messages will auto-post at:
- **8 AM UTC** → Morning briefing
- **6 PM UTC** → Evening metrics
- **Sunday 8 PM UTC** → Weekly summary

To verify cron is working:
```bash
# Check GitHub Actions logs
# Settings → Actions → see workflow runs
```

---

## Files to Customize

### Update Metrics (Real Data)

Edit `backend/services/slack_monitoring.py`:

```python
async def _fetch_evening_metrics(self) -> list[MetricValue]:
    """Query your database for real metrics."""
    revenue_doc = await self.db.daily_metrics.find_one()  # Your query
    return [
        MetricValue(
            label="Daily Revenue",
            value=f"${revenue_doc['total']:.2f}",
            status=StatusIndicator.OPERATIONAL,
            trend=f"↑ +{revenue_doc['percent_change']:.1f}%"
        ),
        # Add more...
    ]
```

### Update Alert Thresholds

Edit same file:

```python
async def _fetch_evening_alerts(self) -> list[str]:
    """Check thresholds and return alerts."""
    alerts = []
    latency = await self.db.metrics.find_one({"metric": "latency"})
    if latency['value'] > 300:  # Threshold
        alerts.append(f"High latency: {latency['value']}ms")
    return alerts
```

### Change Scheduled Times

Edit `.github/workflows/slack-monitoring.yml`:

```yaml
schedule:
  - cron: "0 10 * * *"  # Change from 8 AM to 10 AM
  - cron: "0 19 * * *"  # Change from 6 PM to 7 PM
  - cron: "0 14 * * 0"  # Change from Sun 8 PM to Sun 2 PM
```

---

## Message Preview

### Morning Briefing (8 AM)

```
📊 Morning Briefing
Wednesday, June 25, 2026

Status: ✓ Operational    Latency: 142ms
Errors: 0.02%            Uptime: 99.99%

Today's Focus:
• Monitor campaign performance
• Review pending approvals
• Check affiliate metrics
```

### Evening Metrics (6 PM)

```
📈 Evening Metrics
Daily Performance Summary

Revenue: $2,450.85 ↑ +12%   Sessions: 342 ↑ +28
Conversion: 3.2% ↑ +0.5%    Response: 156ms ↑ +12ms

Highlights:
• Revenue up 12% from yesterday
• Peak sessions: 487 concurrent at 2:30 PM
• Zero critical errors
```

### Weekly Summary (Sunday 8 PM)

```
📋 Weekly Summary
Week of June 19–25, 2026

Revenue: $18,342.50 ↑ +8.5%   Sessions: 2,145 ↑ +312
Daily Avg: $2,620.36 ↑ +5.2%  Uptime: 99.97% ✓

Week Highlights:
• Best day: Thursday (+18% revenue)
• Slowest: Tuesday (2m latency spike)
• Zero P1 incidents
• Conversion: 3.1% (stable)

Next Week:
1. Deploy v5.3 with new affiliate dashboard
2. Run Q3 capacity planning review
3. Onboard 3 new affiliate partners
```

---

## Metrics Template

Copy-paste any of these:

```python
MetricValue(
    label="Daily Revenue",
    value="$2,450.85",
    status=StatusIndicator.OPERATIONAL,
    trend="↑ +12%"
)

MetricValue(
    label="Active Sessions",
    value="342",
    status=StatusIndicator.OPERATIONAL,
    trend="↑ +28"
)

MetricValue(
    label="Error Rate",
    value="0.02%",
    status=StatusIndicator.OPERATIONAL,
    trend="↓ -0.01%"
)
```

---

## Status Indicators

```python
StatusIndicator.OPERATIONAL    # ✓ Green circle
StatusIndicator.WARNING        # ⚠️ Yellow circle
StatusIndicator.CRITICAL       # ✗ Red circle
StatusIndicator.MAINTENANCE    # 🔧 Orange circle
StatusIndicator.OFFLINE        # ⚫ Black circle
```

---

## Environment Variables

### Required (GitHub Secrets)

```
PROFITENGINE_SLACK_WEBHOOK_URL   # https://hooks.slack.com/services/...
MONGO_URL                         # mongodb://...  (already exists)
```

### Optional

```
PROFITENGINE_SLACK_ALERTS_WEBHOOK     # For #alerts channel
PROFITENGINE_SLACK_METRICS_WEBHOOK    # For #metrics channel
PROFITENGINE_SLACK_EXECUTIVE_WEBHOOK  # For #executive channel
```

---

## Deployment Checklist

- [ ] **Webhook Created**
  - Slack: api.slack.com/apps → Incoming Webhooks
  - Channel selected
  - URL copied

- [ ] **GitHub Secret Added**
  - Name: `PROFITENGINE_SLACK_WEBHOOK_URL`
  - Value: Webhook URL
  - Verified in Settings → Secrets

- [ ] **Workflow Tested**
  - Manual trigger runs without errors
  - Message appears in Slack
  - Metrics display correctly

- [ ] **Metrics Customized** (Optional)
  - Updated `_fetch_*_metrics()` methods
  - Connected to real database
  - Tested locally with `python backend/services/slack_monitoring.py`

- [ ] **Alerts Configured** (Optional)
  - Set thresholds in `_fetch_*_alerts()`
  - Tested alert messages
  - Verified alert display in templates

- [ ] **Schedule Verified**
  - Cron times match desired timezone
  - GitHub Actions enabled
  - No other blocking jobs

---

## Support & Debugging

### Workflow Not Posting?

1. Check GitHub Actions logs:
   - Settings → Secrets: Verify `PROFITENGINE_SLACK_WEBHOOK_URL` exists
   - Actions → Slack Real-Time Monitoring → Latest run
   - View "Post * to Slack" step for error details

2. Test webhook locally:
   ```bash
   export PROFITENGINE_SLACK_WEBHOOK_URL="your-webhook-url"
   curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test"}'
   ```

3. Verify Slack permissions:
   - Webhook must have permission to post in channel
   - Channel must exist and be accessible

### Wrong Timezone?

Times in cron are UTC. Convert to your timezone:
- **EST** = UTC -5 (EDT -4)
- **PST** = UTC -8 (PDT -7)
- **IST** = UTC +5:30
- **AEST** = UTC +10

Adjust `cron` expressions accordingly.

### Custom Metrics Not Showing?

1. Update `_fetch_*_metrics()` in `slack_monitoring.py`
2. Connect to database (MongoDB example in SLACK_MONITORING_ADVANCED.md)
3. Test locally:
   ```bash
   python -m backend.services.slack_monitoring
   ```
4. Commit and push (workflow auto-updates)

---

## Next Steps

### Short Term (Today)

1. Run `python scripts/setup_slack_monitoring.py`
2. Create Slack webhook
3. Add GitHub secret
4. Test with manual trigger

### Medium Term (This Week)

1. Update metrics with real database queries
2. Configure alert thresholds
3. Customize message colors and emojis
4. Test automated schedule

### Long Term (This Month)

1. Add multi-channel routing
2. Implement health scoring
3. Connect incident management
4. Set up on-call alerting

---

## Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `backend/services/slack_monitoring.py` | Service implementation | 330 |
| `.github/workflows/slack-monitoring.yml` | GitHub Actions workflow | 160 |
| `SLACK_MONITORING_SETUP.md` | Complete setup guide | 420 |
| `SLACK_TEMPLATES_QUICK_REFERENCE.md` | Copy-paste templates | 320 |
| `SLACK_MONITORING_ADVANCED.md` | Advanced customization | 400 |
| `scripts/setup_slack_monitoring.py` | Interactive setup wizard | 380 |

---

## Features at a Glance

- ✓ Automatic scheduling (GitHub Actions cron)
- ✓ Webhook-based posting (no API key needed)
- ✓ Real-time status indicators (green/yellow/red)
- ✓ Trend analysis (percentage changes)
- ✓ Alert support (5 templates included)
- ✓ Multi-channel routing (different channels)
- ✓ Database integration (MongoDB/PostgreSQL examples)
- ✓ Local testing (preview messages before post)
- ✓ Manual trigger support (test anytime)
- ✓ Production monitoring (health checks)

---

## Time Zones & Scheduling

**Default UTC Times:**
- **8:00 AM** — Morning briefing
- **6:00 PM** — Evening metrics
- **Sunday 8:00 PM** — Weekly summary

**Conversion Examples:**
| Time | EST | PST | IST | AEST |
|------|-----|-----|-----|------|
| 8 AM UTC | 3 AM | 12 AM | 4 PM | 6 PM |
| 6 PM UTC | 1 PM | 10 AM | 11:30 PM | 4 AM (next) |
| Sun 8 PM UTC | Sun 3 PM | Sun 12 PM | Mon 1:30 AM | Mon 6 AM |

Edit `.github/workflows/slack-monitoring.yml` to adjust cron expressions.

---

## Copy-Paste Commands

### Setup
```bash
python scripts/setup_slack_monitoring.py
```

### Local Test
```bash
python -m backend.services.slack_monitoring
```

### Add GitHub Secret (CLI)
```bash
gh secret set PROFITENGINE_SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/..."
```

### Test Webhook (curl)
```bash
curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test"}'
```

---

## All Done!

Your Slack real-time monitoring is ready to go.

**Next:** Run the setup wizard and post your first message! 🚀

```bash
python scripts/setup_slack_monitoring.py
```

Questions? Check:
- `SLACK_MONITORING_SETUP.md` — Full guide
- `SLACK_TEMPLATES_QUICK_REFERENCE.md` — Templates
- `SLACK_MONITORING_ADVANCED.md` — Advanced examples

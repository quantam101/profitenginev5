# Slack Real-Time Monitoring Setup — Complete Guide

Automated daily and weekly Slack posts with metrics, status indicators, and custom alerts. All templates are copy-paste ready.

---

## Quick Start (5 minutes)

### Step 1: Create Slack Incoming Webhook

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. **Create New App** → **From scratch**
3. App Name: `ProfitEngine Monitoring`
4. Development Workspace: Select your workspace
5. In sidebar, click **Incoming Webhooks**
6. Toggle **Activate Incoming Webhooks** to **On**
7. Click **Add New Webhook to Workspace**
8. Select channel (e.g., `#profitengine-alerts` or `#metrics`)
9. **Allow** permission request
10. Copy the **Webhook URL** (looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

### Step 2: Add GitHub Secret

1. Go to GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `PROFITENGINE_SLACK_WEBHOOK_URL`
4. Value: Paste your webhook URL
5. Click **Add secret**

### Step 3: Deploy (Auto-Scheduled)

The workflow file is ready at `.github/workflows/slack-monitoring.yml`. It automatically:
- **8 AM UTC** → Morning briefing
- **6 PM UTC** → Evening metrics
- **Sunday 8 PM UTC** → Weekly summary

To test manually:
1. Go to **Actions** tab in GitHub
2. Select **Slack Real-Time Monitoring**
3. Click **Run workflow** → dropdown **briefing_type**
4. Choose `morning`, `evening`, or `weekly`
5. Click **Run workflow**

---

## Message Templates (Copy-Paste Ready)

All templates below are production-ready. Paste into your Slack workspace to test formatting.

### Template 1: Morning Briefing (8 AM)

**Post this as:** Incoming Webhook via GitHub Actions

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📊 ProfitEngine Morning Briefing",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Wednesday, June 25, 2026*\nDaily overview & action items"
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*System Status*\n:green_circle: Operational\nAll systems nominal ✓"
        },
        {
          "type": "mrkdwn",
          "text": "*API Latency*\n:green_circle: Operational\n142ms avg ↓ -8ms"
        },
        {
          "type": "mrkdwn",
          "text": "*Error Rate*\n:green_circle: Operational\n0.02% ↓ -0.01%"
        },
        {
          "type": "mrkdwn",
          "text": "*Uptime*\n:green_circle: Operational\n99.99% ✓"
        }
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Today's Tasks*\n• Deploy v5.2.1 to production\n• Review pending approvals (12)\n• Monitor campaign performance"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "ProfitEngine v5 Real-Time Monitoring | 2026-06-25 08:00:00 UTC"
        }
      ]
    }
  ],
  "attachments": [
    {
      "color": "#36a64f",
      "footer": "ProfitEngine v5 Real-Time Monitoring"
    }
  ]
}
```

**Preview:**
- Green header with calendar emoji
- Status grid (4 columns): System, Latency, Errors, Uptime
- Daily action items
- Timestamp footer

---

### Template 2: Evening Metrics (6 PM)

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📈 ProfitEngine Evening Metrics",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Daily Performance Summary*\nEnd-of-day snapshot"
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Daily Revenue*\n:green_circle: Operational\n$2,450.85 ↑ +12%"
        },
        {
          "type": "mrkdwn",
          "text": "*Active Sessions*\n:green_circle: Operational\n342 sessions ↑ +28"
        },
        {
          "type": "mrkdwn",
          "text": "*Conversion Rate*\n:green_circle: Operational\n3.2% ↑ +0.5%"
        },
        {
          "type": "mrkdwn",
          "text": "*Avg Response Time*\n:green_circle: Operational\n156ms ↑ +12ms"
        }
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Key Highlights*\n:chart_with_upwards_trend: Revenue +12% from yesterday\n:people: Peak sessions: 2:30 PM (487 concurrent)\n:gear: Zero critical errors"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "ProfitEngine v5 Real-Time Monitoring | 2026-06-25 18:00:00 UTC"
        }
      ]
    }
  ],
  "attachments": [
    {
      "color": "#0099ff",
      "footer": "ProfitEngine v5 Real-Time Monitoring"
    }
  ]
}
```

**Preview:**
- Blue header with upward chart emoji
- Revenue, sessions, conversion, latency metrics
- Key highlights (trends, peak times, errors)
- Timestamp footer

---

### Template 3: Weekly Summary (Sunday 8 PM)

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📋 ProfitEngine Weekly Summary",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Week of June 19 – June 25, 2026*"
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Weekly Revenue*\n:green_circle: Operational\n$18,342.50 ↑ +8.5%"
        },
        {
          "type": "mrkdwn",
          "text": "*Total Sessions*\n:green_circle: Operational\n2,145 sessions ↑ +312"
        },
        {
          "type": "mrkdwn",
          "text": "*Avg Daily Revenue*\n:green_circle: Operational\n$2,620.36 ↑ +5.2%"
        },
        {
          "type": "mrkdwn",
          "text": "*Uptime SLA*\n:green_circle: Operational\n99.97% ✓"
        }
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Weekly Performance*\n:arrow_up: *Best Day:* Thursday (+18% revenue)\n:arrow_down: *Slowest Day:* Tuesday (2 min latency spike)\n:white_check_mark: *Zero P1 Incidents*\n:bar_chart: *Avg Conversion:* 3.1% (stable)"
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Next Week Priorities*\n1. Deploy v5.3 with new affiliate dashboard\n2. Run Q3 capacity planning review\n3. Onboard 3 new affiliate partners"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "ProfitEngine v5 Real-Time Monitoring | 2026-06-25 20:00:00 UTC"
        }
      ]
    }
  ],
  "attachments": [
    {
      "color": "#9c27b0",
      "footer": "ProfitEngine v5 Real-Time Monitoring"
    }
  ]
}
```

**Preview:**
- Purple header with clipboard emoji
- Weekly revenue, sessions, daily avg, uptime SLA
- Performance highlights (best/worst days, incidents)
- Next week priorities
- Timestamp footer

---

## Metrics Reference

### Status Indicators (Always Use These)

```
:green_circle: Operational    — All systems normal
:yellow_circle: Warning       — Degraded performance
:red_circle: Critical         — Incident in progress
:orange_circle: Maintenance   — Scheduled downtime
:black_circle: Offline        — Service unavailable
```

### Trend Arrows

```
↑ +X%    — Positive trend (revenue, sessions)
↓ -X%    — Improvement (latency, errors)
→ Stable — No significant change
✓        — Target met / No action needed
⚠️       — Alert / Review needed
```

### Metric Examples by Category

#### System Health
- API Latency: `142ms avg` (target: <200ms)
- Error Rate: `0.02%` (target: <0.1%)
- Uptime: `99.99%` (target: >99.9%)
- CPU Load: `45%` (target: <70%)
- Memory: `62%` (target: <80%)

#### Revenue & Business
- Daily Revenue: `$2,450.85`
- Weekly Revenue: `$18,342.50`
- Average Daily Revenue: `$2,620.36`
- Conversion Rate: `3.2%`
- Revenue per Session: `$7.15`

#### Engagement
- Active Sessions: `342`
- Total Daily Users: `1,245`
- Weekly Sessions: `2,145`
- Average Session Duration: `4m 32s`
- Bounce Rate: `18.3%`

#### Deployment & Operations
- Last Deploy: `2 hours ago`
- P1 Incidents (7d): `0`
- Mean Time to Recovery: `12m`
- Deploy Success Rate: `99.2%`
- Test Coverage: `87%`

---

## Custom Alert Templates

### Alert: High Latency

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":yellow_circle: *ALERT: High Latency*\nAPI response time spiked to 450ms (normal: 150ms)\nInvestigation in progress. ETA: 5 minutes."
  }
}
```

### Alert: Revenue Drop

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":red_circle: *CRITICAL: Revenue Drop*\nRevenue down 35% in last hour vs. daily average\nCampaign status check recommended."
  }
}
```

### Alert: Deployment Rollback

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":orange_circle: *Rollback Initiated*\nv5.2.1 deployment rolled back due to 2% error rate increase\nRolled back to v5.2.0. Investigating root cause."
  }
}
```

### Alert: Scheduled Maintenance

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":orange_circle: *Scheduled Maintenance*\nBackend database migration: Thursday 2 AM – 4 AM UTC\nExpected downtime: 30 minutes. Notifications will follow."
  }
}
```

---

## Implementation Examples

### Adding Custom Metrics (Python)

Edit `backend/services/slack_monitoring.py` to add your metrics:

```python
async def _fetch_evening_metrics(self) -> list[MetricValue]:
    """Fetch metrics for evening post."""
    try:
        # Query your database
        revenue_doc = await self.db.daily_metrics.find_one(
            {"date": {"$gte": datetime.now() - timedelta(days=1)}}
        )
        
        metrics = [
            MetricValue(
                label="Daily Revenue",
                value=f"${revenue_doc['total']:.2f}",
                status=StatusIndicator.OPERATIONAL,
                trend=f"↑ +{revenue_doc['percent_change']:.1f}%"
            ),
            # Add more metrics...
        ]
        return metrics
    except Exception as e:
        print(f"Error: {e}")
        return []
```

### Adding Custom Alerts

```python
async def _fetch_evening_alerts(self) -> list[str]:
    """Fetch alerts for evening post."""
    try:
        alerts = []
        
        # Check for high latency
        latency_doc = await self.db.metrics.find_one(
            {"metric": "latency", "timestamp": {"$gte": datetime.now() - timedelta(minutes=10)}}
        )
        if latency_doc and latency_doc['value'] > 300:
            alerts.append(f"API latency high: {latency_doc['value']}ms (target: <200ms)")
        
        # Check for deployment issues
        deploy_doc = await self.db.deployments.find_one(
            {"status": "failed", "timestamp": {"$gte": datetime.now() - timedelta(hours=1)}}
        )
        if deploy_doc:
            alerts.append(f"Deploy failed: {deploy_doc['version']} — {deploy_doc['error']}")
        
        return alerts
    except Exception as e:
        print(f"Error: {e}")
        return []
```

---

## Testing Your Setup

### Test via curl (Locally)

```bash
curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Test message",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "✓ Slack webhook is working!"
        }
      }
    ]
  }'
```

### Manually Trigger Workflow (GitHub)

1. Go to **Actions** → **Slack Real-Time Monitoring**
2. Click **Run workflow** dropdown
3. Select briefing type
4. Click **Run workflow**
5. Check Slack channel within 30 seconds

### Verify Cron Schedule

The workflow runs on UTC times. To convert to your timezone:
- **8 AM UTC** = 3 AM EST / 12 AM PST / 4 PM IST
- **6 PM UTC** = 1 PM EST / 10 AM PST / 11:30 PM IST
- **Sunday 8 PM UTC** = Sunday 3 PM EST / 12 PM PST / Monday 1:30 AM IST

To change times, edit `.github/workflows/slack-monitoring.yml` and update the `cron` expressions.

---

## Customization Guide

### Change Notification Times

Edit `.github/workflows/slack-monitoring.yml`:

```yaml
schedule:
  # Morning: 8 AM UTC → change to "0 10 * * *" for 10 AM UTC
  - cron: "0 10 * * *"
  # Evening: 6 PM UTC → change to "0 19 * * *" for 7 PM UTC
  - cron: "0 19 * * *"
  # Weekly: Sunday 8 PM UTC → change to "0 14 * * 0" for Sunday 2 PM UTC
  - cron: "0 14 * * 0"
```

### Change Slack Channel

1. Create a new Slack webhook in a different channel
2. Update the GitHub secret `PROFITENGINE_SLACK_WEBHOOK_URL`
3. Or: Create multiple webhook secrets and update the workflow to use them

### Add Multiple Channels

Create separate workflows for each channel:

```yaml
jobs:
  slack-morning-alerts:
    # Posts to #alerts channel
    env:
      PROFITENGINE_SLACK_WEBHOOK_URL: ${{ secrets.SLACK_ALERTS_WEBHOOK }}
    # ... rest of job ...
  
  slack-morning-metrics:
    # Posts to #metrics channel
    env:
      PROFITENGINE_SLACK_WEBHOOK_URL: ${{ secrets.SLACK_METRICS_WEBHOOK }}
    # ... rest of job ...
```

### Customize Message Colors

Edit `backend/services/slack_monitoring.py`:

```python
# Change color based on status
if overall_status == StatusIndicator.CRITICAL:
    color = "#ff0000"  # Red
elif overall_status == StatusIndicator.WARNING:
    color = "#ffaa00"  # Orange
else:
    color = "#36a64f"  # Green
```

---

## Troubleshooting

### Webhook not posting

1. **Check webhook URL**: Verify `PROFITENGINE_SLACK_WEBHOOK_URL` is correct in GitHub Secrets
2. **Test locally**: Use `curl` command above to test manually
3. **Check permissions**: Webhook must have permission to post in the channel
4. **Check logs**: Go to **Actions** → **Slack Real-Time Monitoring** → latest run → **View logs**

### Wrong timezone

GitHub Actions runs in UTC. Check your local timezone offset:
- EST = UTC -5 / EDT = UTC -4
- PST = UTC -8 / PDT = UTC -7
- IST = UTC +5:30
- AEST = UTC +10

Adjust `cron` expressions accordingly.

### Database connection errors

1. Verify `MONGO_URL` is set in GitHub Secrets
2. Check MongoDB is accessible from GitHub Actions (may require IP allowlist)
3. Fallback: Use hardcoded metrics if database unavailable

### Metrics not updating

The templates include placeholder metrics. To show real metrics:

1. Update `_fetch_*_metrics()` methods in `slack_monitoring.py`
2. Query your database (MongoDB, PostgreSQL, etc.)
3. Test locally with `python -m backend.services.slack_monitoring`

---

## Production Checklist

- [ ] Slack webhook URL added to GitHub Secrets as `PROFITENGINE_SLACK_WEBHOOK_URL`
- [ ] MongoDB connection string in GitHub Secrets as `MONGO_URL`
- [ ] Workflow file tested with manual trigger
- [ ] Metrics methods updated with real database queries
- [ ] Alert thresholds tuned for your business
- [ ] Team members invited to Slack channel
- [ ] Alerting rules reviewed by ops team
- [ ] Log retention configured (GitHub Actions → Settings → Logs)
- [ ] Backup webhook (secondary Slack channel) configured
- [ ] On-call rotation documentation updated

---

## Quick Reference

**Files Modified:**
- `backend/services/slack_monitoring.py` — Service implementation
- `.github/workflows/slack-monitoring.yml` — Scheduler & cron jobs
- `.env.example` — Environment variables (documentation)

**Secrets to Add (GitHub):**
- `PROFITENGINE_SLACK_WEBHOOK_URL` — Slack incoming webhook
- `MONGO_URL` — MongoDB connection (already exists)

**Scheduled Posts:**
- Daily 8 AM UTC: Morning briefing (system status)
- Daily 6 PM UTC: Evening metrics (revenue, sessions)
- Weekly Sunday 8 PM UTC: Weekly summary (trends, priorities)

**Status Indicators:**
- Green `:green_circle:` — Operational
- Yellow `:yellow_circle:` — Warning
- Red `:red_circle:` — Critical
- Orange `:orange_circle:` — Maintenance
- Black `:black_circle:` — Offline

---

## Support

For issues or customization:
1. Check GitHub Actions logs (Actions → Slack Real-Time Monitoring)
2. Test webhook locally with `curl`
3. Review `slack_monitoring.py` metrics methods
4. Check Slack channel permissions

Questions? Update the service class and redeploy on next git push (workflow auto-triggers with code changes).

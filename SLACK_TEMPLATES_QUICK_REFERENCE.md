# Slack Monitoring Templates — Quick Reference Card

Copy-paste templates for all standard Slack messages. **All templates are production-ready.**

---

## POST THIS TO SLACK TO TEST

### Test Message (to verify webhook works)

```json
{
  "text": "Test message from ProfitEngine",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "✓ Slack webhook connected!\n*ProfitEngine v5 Monitoring*"
      }
    }
  ]
}
```

**How to post:** Save as `test.json`, then:
```bash
curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL -H 'Content-Type: application/json' -d @test.json
```

---

## MORNING BRIEFING (8 AM)

**Emoji:** 📊 | **Color:** Green `#36a64f` | **Duration:** 30 seconds to read

### Copy-Paste Template

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📊 Morning Briefing",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Wednesday, June 25, 2026*"
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
          "text": "*Status*\n:green_circle: Operational"
        },
        {
          "type": "mrkdwn",
          "text": "*Latency*\n142ms avg"
        },
        {
          "type": "mrkdwn",
          "text": "*Errors*\n0.02%"
        },
        {
          "type": "mrkdwn",
          "text": "*Uptime*\n99.99%"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Today's Focus*\n• Monitor campaign performance\n• Review pending approvals\n• Check affiliate metrics"
      }
    }
  ],
  "attachments": [
    {
      "color": "#36a64f"
    }
  ]
}
```

### Customize These Fields

```json
{
  "label": "*Status*",
  "value": "Replace 'Operational' with actual status",
  "metrics": {
    "latency": "Replace '142ms' with real value",
    "error_rate": "Replace '0.02%' with real value",
    "uptime": "Replace '99.99%' with real value"
  },
  "tasks": [
    "Replace with your daily priorities",
    "List up to 3-5 key items"
  ]
}
```

---

## EVENING METRICS (6 PM)

**Emoji:** 📈 | **Color:** Blue `#0099ff` | **Duration:** 45 seconds to read

### Copy-Paste Template

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📈 Evening Metrics",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Daily Performance Summary*"
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
          "text": "*Revenue*\n$2,450.85\n↑ +12%"
        },
        {
          "type": "mrkdwn",
          "text": "*Sessions*\n342\n↑ +28"
        },
        {
          "type": "mrkdwn",
          "text": "*Conversion*\n3.2%\n↑ +0.5%"
        },
        {
          "type": "mrkdwn",
          "text": "*Response*\n156ms\n↑ +12ms"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Highlights*\n:chart_with_upwards_trend: Revenue up 12%\n:people: Peak: 487 concurrent users\n:gear: Zero critical errors"
      }
    }
  ],
  "attachments": [
    {
      "color": "#0099ff"
    }
  ]
}
```

### Customize These Fields

```json
{
  "revenue": "Replace '$2,450.85' with daily total",
  "revenue_trend": "Replace '+12%' with actual % change",
  "sessions": "Replace '342' with session count",
  "session_trend": "Replace '+28' with session change",
  "conversion": "Replace '3.2%' with conversion rate",
  "conversion_trend": "Replace '+0.5%' with rate change",
  "latency": "Replace '156ms' with avg response time",
  "latency_trend": "Replace '+12ms' with latency change",
  "highlights": [
    "Replace with your key metrics",
    "3-4 lines, most important first"
  ]
}
```

---

## WEEKLY SUMMARY (Sunday 8 PM)

**Emoji:** 📋 | **Color:** Purple `#9c27b0` | **Duration:** 1 minute to read

### Copy-Paste Template

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📋 Weekly Summary",
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
          "text": "*Revenue*\n$18,342.50\n↑ +8.5%"
        },
        {
          "type": "mrkdwn",
          "text": "*Sessions*\n2,145\n↑ +312"
        },
        {
          "type": "mrkdwn",
          "text": "*Daily Avg*\n$2,620.36\n↑ +5.2%"
        },
        {
          "type": "mrkdwn",
          "text": "*Uptime*\n99.97%\n✓"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Week Highlights*\n:arrow_up: Best day: Thursday (+18%)\n:arrow_down: Slowest: Tuesday (2m latency spike)\n:white_check_mark: Zero P1 incidents\n:bar_chart: Conversion: 3.1% (stable)"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Next Week*\n1. Deploy v5.3 with new dashboard\n2. Run capacity planning review\n3. Onboard 3 new partners"
      }
    }
  ],
  "attachments": [
    {
      "color": "#9c27b0"
    }
  ]
}
```

### Customize These Fields

```json
{
  "week_range": "Replace dates with actual week",
  "weekly_revenue": "Replace '$18,342.50' with weekly total",
  "revenue_trend": "Replace '+8.5%' with actual %",
  "weekly_sessions": "Replace '2,145' with session count",
  "session_trend": "Replace '+312' with session change",
  "daily_avg_revenue": "Replace '$2,620.36' with daily average",
  "daily_avg_trend": "Replace '+5.2%' with %",
  "uptime": "Replace '99.97%' with weekly uptime",
  "highlights": [
    "Best day: describe performance",
    "Slowest day: describe issue",
    "Incident count and status",
    "Other key metric"
  ],
  "next_week_priorities": [
    "Replace with next week tasks",
    "1-3 key action items"
  ]
}
```

---

## ALERT TEMPLATES

Use these for critical situations. Include in the `alerts` array.

### High Latency Alert

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":yellow_circle: API latency spiked to 450ms (normal: 150ms)\nInvestigation in progress. ETA: 5 minutes."
  }
}
```

### Revenue Drop Alert

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":red_circle: CRITICAL: Revenue down 35% in last hour\nCampaign status check recommended."
  }
}
```

### Error Rate Alert

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":red_circle: Error rate increased to 2.1% (threshold: 1%)\nServer logs: https://dashboard.render.com"
  }
}
```

### Deployment Alert

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":orange_circle: v5.2.1 rollback initiated due to error spike\nRolled back to v5.2.0. Investigating root cause."
  }
}
```

### Maintenance Alert

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": ":orange_circle: Scheduled maintenance: Database migration\nThursday 2 AM – 4 AM UTC. Expected downtime: 30 minutes."
  }
}
```

---

## STATUS INDICATORS (Always Use These)

```
:green_circle:  Operational      — All systems normal
:yellow_circle: Warning          — Degraded performance / Review needed
:red_circle:    Critical         — Incident in progress / Action required
:orange_circle: Maintenance      — Scheduled downtime / In progress
:black_circle:  Offline          — Service unavailable
```

## TREND INDICATORS

```
↑ +X%   Positive trend (revenue, sessions, conversion)
↓ -X%   Improvement (latency, errors)
→       Stable / No significant change
✓       Target met / No action needed
⚠️      Alert / Review needed
```

---

## METRIC EXAMPLES

### System Health
- API Latency: `142ms avg` | Target: `<200ms`
- Error Rate: `0.02%` | Target: `<0.1%`
- Uptime: `99.99%` | Target: `>99.9%`
- CPU Load: `45%` | Target: `<70%`
- Memory: `62%` | Target: `<80%`

### Revenue & Business
- Daily Revenue: `$2,450.85`
- Weekly Revenue: `$18,342.50`
- Average Daily Revenue: `$2,620.36`
- Conversion Rate: `3.2%`
- Revenue per Session: `$7.15`

### Engagement
- Active Sessions: `342`
- Daily Users: `1,245`
- Weekly Sessions: `2,145`
- Avg Session Duration: `4m 32s`
- Bounce Rate: `18.3%`

### Operations
- Last Deploy: `2 hours ago`
- P1 Incidents (7d): `0`
- Mean Time to Recovery: `12m`
- Deploy Success Rate: `99.2%`
- Test Coverage: `87%`

---

## TEST TEMPLATE (Run first)

Save as `test.json`:

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "✓ Test Message",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Slack webhook is connected and working!"
      }
    }
  ]
}
```

Post with:
```bash
curl -X POST $PROFITENGINE_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d @test.json
```

---

## ONE-MINUTE SETUP

1. Create Slack webhook: https://api.slack.com/apps → Incoming Webhooks
2. Copy webhook URL
3. Add to GitHub: Settings → Secrets → `PROFITENGINE_SLACK_WEBHOOK_URL`
4. Workflow auto-posts daily (8 AM, 6 PM, Sunday 8 PM)
5. Test: Actions → Slack Real-Time Monitoring → Run workflow

---

## CHEAT SHEET

| When | Message | Emoji | Color |
|------|---------|-------|-------|
| 8 AM | Morning Briefing | 📊 | `#36a64f` (Green) |
| 6 PM | Evening Metrics | 📈 | `#0099ff` (Blue) |
| Sun 8 PM | Weekly Summary | 📋 | `#9c27b0` (Purple) |

| Status | Indicator | Use When |
|--------|-----------|----------|
| Operational | `:green_circle:` | All systems normal |
| Warning | `:yellow_circle:` | Degraded / Review needed |
| Critical | `:red_circle:` | Incident in progress |
| Maintenance | `:orange_circle:` | Scheduled downtime |
| Offline | `:black_circle:` | Service unavailable |

---

## FULL WORKFLOW EXAMPLE

**Step 1:** Morning briefing posts at 8 AM
```
"📊 Morning Briefing — Wednesday, June 25"
Status: ✓ Operational
Latency: 142ms | Errors: 0.02% | Uptime: 99.99%
Tasks: Monitor campaigns, review approvals
```

**Step 2:** Evening metrics post at 6 PM
```
"📈 Evening Metrics"
Revenue: $2,450.85 ↑ +12%
Sessions: 342 ↑ +28
Conversion: 3.2% ↑ +0.5%
Peak: 487 concurrent users at 2:30 PM
```

**Step 3:** Weekly summary posts Sunday 8 PM
```
"📋 Weekly Summary — June 19–25"
Weekly Revenue: $18,342.50 ↑ +8.5%
Best Day: Thursday (+18% revenue)
Uptime: 99.97% | Incidents: 0
Next Week: Deploy v5.3, capacity review, 3 new partners
```

---

## WHERE TO CUSTOMIZE

- **Metrics values:** `backend/services/slack_monitoring.py` → `_fetch_*_metrics()`
- **Alert thresholds:** `backend/services/slack_monitoring.py` → `_fetch_*_alerts()`
- **Scheduled times:** `.github/workflows/slack-monitoring.yml` → `cron` expressions
- **Colors & emojis:** Any template above (customize `color` & `text`)
- **Slack channel:** Create new webhook in different channel + update GitHub secret

---

## TROUBLESHOOTING IN 30 SECONDS

| Issue | Fix |
|-------|-----|
| Not posting | Check `PROFITENGINE_SLACK_WEBHOOK_URL` in GitHub Secrets |
| Wrong time | Adjust `cron` in `.github/workflows/slack-monitoring.yml` (UTC) |
| Wrong metrics | Update `_fetch_*_metrics()` in `slack_monitoring.py` |
| Test locally | `curl -X POST $WEBHOOK_URL -d @test.json` |
| View logs | GitHub Actions → Slack Real-Time Monitoring → Run logs |

---

**All templates are production-ready. Copy, customize, deploy.** ✓

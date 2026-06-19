# ProfitEngine v5 Sync — Quick Reference Card

## One-Minute Setup

```bash
# 1. Set environment variables
export GITHUB_PROFITENGINEV5_TOKEN=ghp_xxxx
export PROFITENGINEV5_LOCAL_PATH=/tmp/profitenginev5

# 2. Test it
python3 runtime/profitenginev5_sync_daily.py

# 3. Schedule it (cron example)
crontab -e
# Add: 0 0 * * * cd /opt/profitengine && python3 runtime/profitenginev5_sync_daily.py
```

## Common Tasks

### Sync Daily Metrics

```python
from runtime.profitenginev5_sync import ProfitEngineV5Sync

sync = ProfitEngineV5Sync()
sync.initialize()
sync.metrics.sync_daily_metrics(1250.50, 67.5, 12, 450, 8900)
sync.sync()
```

### Sync Blog Post

```python
sync.content.sync_blog_post(
    title="Markets Hit Record High",
    content="# Market Update\n\nToday...",
)
sync.sync()
```

### Sync Case Study

```python
sync.case_studies.sync_case_study(
    customer_id="cust_001",
    anonymized_name="Client A",
    roi_percent=45.5,
    strategy="Day Trading",
    testimonial="Great results!",
    results={"Starting": "$10,000", "Ending": "$14,550"},
)
sync.sync()
```

### Sync All Data Types

```python
# Metrics
sync.metrics.sync_daily_metrics(1250.50, 67.5, 12, 450, 8900)

# Blog
sync.content.sync_blog_post("Title", "Content...")

# Case study
sync.case_studies.sync_case_study(...)

# Social
sync.social.sync_engagement_summary({"twitter": {...}})

# Landing page
sync.landing_page.sync_hero_metrics(450, 8900, 4500000, 67.5)

# Email
sync.email.sync_template("daily-alert", html, text, metadata)

# Commit all
sync.sync()
```

## File Locations

After setup, files will be in:

```
profitenginev5 repo (cloned to /tmp/profitenginev5):
  ├── content/trading-results/
  │   └── 2026-06-18-market-update.md
  ├── metrics/
  │   └── 2026-06-18-metrics.json
  ├── case-studies/
  │   ├── cust_001.md
  │   └── cust_001.json
  ├── landing-page/
  │   ├── hero-metrics.json
  │   ├── testimonials.json
  │   └── conversions/
  ├── analytics/
  │   ├── social-engagement.jsonl
  │   └── 2026-06-18-summary.json
  └── emails/
      ├── daily-alert.html
      ├── daily-alert.txt
      ├── daily-alert.json
      └── segments.json
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `git not found` | `apt-get install git` |
| `GitHub API 401` | Check `GITHUB_PROFITENGINEV5_TOKEN` is valid |
| `repo not found` | Verify `PROFITENGINEV5_REPO_URL` |
| `permission denied` | Check write access to `PROFITENGINEV5_LOCAL_PATH` |
| `merge conflict` | Sync auto-rebases; check logs if it fails |

## Environment Variables

```bash
# Required
GITHUB_PROFITENGINEV5_TOKEN=ghp_xxxx

# Optional (defaults shown)
PROFITENGINEV5_REPO_URL=https://github.com/quantam101/profitenginev5.git
PROFITENGINEV5_LOCAL_PATH=/tmp/profitenginev5
PROFITENGINEV5_BRANCH=main
GITHUB_PROFITENGINEV5_USER=profitengine-sync
GITHUB_PROFITENGINEV5_EMAIL=sync@profitengine.local
```

## Check Logs

```bash
# Cron job
tail -f /var/log/profitenginev5-sync.log

# systemd service
journalctl -u profitenginev5-sync.service -f

# Check commits
cd /tmp/profitenginev5
git log --oneline -10
```

## Verify Sync Worked

```bash
# Check repo was cloned
ls -la /tmp/profitenginev5

# Check latest commits
cd /tmp/profitenginev5 && git log --oneline -5

# Check file was created
ls profitenginev5/metrics/
cat profitenginev5/metrics/2026-06-18-metrics.json
```

## Daily Integration

Add to your existing daily script:

```python
# In DAILY_RESULTS.py, after generating report
from runtime.profitenginev5_sync import ProfitEngineV5Sync

sync = ProfitEngineV5Sync()
if sync.initialize():
    sync.metrics.sync_daily_metrics(
        pnl_dollars=report["pnl"],
        win_rate=report["win_rate"],
        trades_count=report["trades"],
        customer_count=report["customers"],
        revenue_dollars=report["revenue"],
    )
    sync.sync()
```

## Schedule (Choose One)

### Cron (Simple)
```bash
crontab -e
# Add: 0 0 * * * cd /opt/profitengine && python3 runtime/profitenginev5_sync_daily.py
```

### systemd (Modern Linux)
```bash
sudo cp runtime/profitenginev5-sync.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now profitenginev5-sync.timer
```

### GitHub Actions (Cloud)
Create `.github/workflows/sync.yml` with:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 runtime/profitenginev5_sync_daily.py
        env:
          GITHUB_PROFITENGINEV5_TOKEN: ${{ secrets.GITHUB_PROFITENGINEV5_TOKEN }}
```

## API Methods

```python
# Metrics
sync.metrics.sync_daily_metrics(pnl, rate, trades, customers, revenue, date)
sync.metrics.sync_metrics_batch(list_of_dicts)

# Content
sync.content.sync_blog_post(title, content, date)
sync.content.sync_blog_posts_batch(list_of_posts)

# Cases
sync.case_studies.sync_case_study(id, name, roi, strategy, testimonial, results)

# Social
sync.social.sync_social_metrics(platform, post_id, title, engagement, date)
sync.social.sync_engagement_summary(summary, date)

# Landing Page
sync.landing_page.sync_hero_metrics(customers, trades, aum, success_rate)
sync.landing_page.sync_testimonials(list_of_testimonials)
sync.landing_page.sync_conversion_data(data_dict)

# Email
sync.email.sync_template(name, html, text, metadata)
sync.email.sync_segments(segments_dict)
sync.email.sync_engagement_tracking(campaign_id, opens, clicks, conversions, unsubs)

# Commit & Push
sync.sync(commit_message, push=True)
```

## Monitoring

```bash
# Is scheduler active?
systemctl status profitenginev5-sync.timer
systemctl list-timers

# When will it run next?
systemctl status profitenginev5-sync.timer | grep Trigger

# Recent runs?
journalctl -u profitenginev5-sync.service --since "2 hours ago"

# Any errors?
journalctl -u profitenginev5-sync.service -p err
```

## GitHub Access

1. Create PAT at https://github.com/settings/tokens
2. Select "repo" scope
3. Copy token
4. Set as `GITHUB_PROFITENGINEV5_TOKEN`
5. Rotate every 90 days

## Support

- Full docs: `PROFITENGINEV5_SYNC_README.md`
- Setup guide: `INSTALL_SYNC_SCHEDULER.md`
- Integration: `SYNC_INTEGRATION_GUIDE.md`
- Delivery: `SYNC_ENGINE_DELIVERY.md`

---

**Version:** 1.0  
**Updated:** June 18, 2026  
**Status:** Production Ready

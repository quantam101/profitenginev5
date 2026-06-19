# ProfitEngine v5 — Centralized Sync Engine

## Overview

The `profitenginev5_sync.py` module provides a complete sync engine that pushes all content, metrics, and updates from the autonomous trading system to the **profitenginev5** main repository for centralized distribution.

**Key benefit:** One source of truth for all trading data, case studies, metrics, and marketing content.

## Architecture

```
Autonomous Trading System
    ├── Blog Posts (content_generator.py)
    ├── Daily Metrics (trading results)
    ├── Case Studies (customer wins)
    ├── Social Performance (engagement)
    ├── Landing Page Data (hero metrics, testimonials)
    └── Email Templates (campaigns, segments)
                    ↓
            [profitenginev5_sync.py]
                    ↓
    profitenginev5 Repository (GitHub)
                    ↓
    GitHub Pages Auto-Deploy
                    ↓
    Live on profitengine.alreadyherellc.com
```

## Setup

### 1. Environment Variables

Set these in your server `.env` file or GitHub Secrets:

```bash
# GitHub Repository Configuration
PROFITENGINEV5_REPO_URL=https://github.com/quantam101/profitenginev5.git
PROFITENGINEV5_LOCAL_PATH=/tmp/profitenginev5
PROFITENGINEV5_BRANCH=main

# GitHub Authentication
GITHUB_PROFITENGINEV5_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Personal access token
GITHUB_PROFITENGINEV5_USER=profitengine-sync                   # Commit author name
GITHUB_PROFITENGINEV5_EMAIL=sync@profitengine.local            # Commit author email
```

### 2. Personal Access Token (PAT)

Create a GitHub personal access token with `repo` scope:

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select `repo` scope
4. Set expiration (recommended: 90 days)
5. Copy token and set as `GITHUB_PROFITENGINEV5_TOKEN` on server

**Rotation:** Regenerate every 90 days and update the server secret.

### 3. Repository Permissions

Ensure the profitenginev5 repo allows push from automation:

- **If using a bot account:** Ensure bot has write access to the repo
- **If using your personal token:** You must have write access to profitenginev5
- **Branch protection:** Disable "Require pull request reviews" for `main` (or automation can't push directly)

## Usage

### Basic Initialization

```python
from runtime.profitenginev5_sync import ProfitEngineV5Sync

sync = ProfitEngineV5Sync()

# Initialize (clones repo if needed, configures git)
if not sync.initialize():
    print("Sync initialization failed")
    exit(1)
```

### Blog Post Sync

```python
sync.content.sync_blog_post(
    title="Markets Hit Record High Today",
    content="""# Markets Hit Record High

Today was a great day for trading. The S&P 500 closed up 2.3%...
""",
    date="2026-06-18"  # optional, defaults to today
)
```

**Where it goes:**
- `profitenginev5/content/trading-results/2026-06-18-markets-hit-record-high-today.md`
- Auto-deploys via GitHub Pages

### Metrics Sync

```python
sync.metrics.sync_daily_metrics(
    pnl_dollars=1250.50,
    win_rate=67.5,         # percentage 0-100
    trades_count=12,
    customer_count=450,
    revenue_dollars=8900.00,
    date="2026-06-18"      # optional
)
```

**Where it goes:**
- `profitenginev5/metrics/2026-06-18-metrics.json`
- Used for dashboard, reporting, and hero section numbers

### Case Study Sync

```python
sync.case_studies.sync_case_study(
    customer_id="cust_12345",
    anonymized_name="Client A",
    roi_percent=45.5,
    strategy="Day Trading",
    testimonial="ProfitEngine helped me increase my returns by 45%!",
    results={
        "Starting Balance": "$10,000",
        "Ending Balance": "$14,550",
        "Trades": "125",
        "Average Win": "$45.50",
    }
)
```

**Where it goes:**
- `profitenginev5/case-studies/cust_12345.md` (markdown)
- `profitenginev5/case-studies/cust_12345.json` (metadata)

### Social Performance Sync

```python
# Single post metrics
sync.social.sync_social_metrics(
    platform="twitter",
    post_id="tweet_12345",
    title="New trading strategy revealed",
    engagement={
        "likes": 250,
        "retweets": 75,
        "replies": 30,
        "views": 5000,
    },
    date="2026-06-18"
)

# Daily engagement summary
sync.social.sync_engagement_summary(
    summary={
        "twitter": {"total_likes": 1200, "total_retweets": 300},
        "linkedin": {"total_likes": 450, "total_shares": 80},
        "youtube": {"total_views": 25000, "total_subs_gained": 150},
    },
    date="2026-06-18"
)
```

**Where it goes:**
- `profitenginev5/analytics/social-engagement.jsonl` (append-only log)
- `profitenginev5/analytics/2026-06-18-summary.json` (daily summary)

### Landing Page Data Sync

```python
# Hero section metrics
sync.landing_page.sync_hero_metrics(
    customers_active=450,
    trades_executed=8900,
    dollars_managed=4500000.00,
    success_rate=67.5,
)

# Testimonials
sync.landing_page.sync_testimonials([
    {
        "name": "Client A",
        "quote": "This tool changed my trading completely",
        "role": "Day Trader",
        "image_url": "/images/testimonials/client-a.jpg",
    },
    {
        "name": "Client B",
        "quote": "Consistent returns month after month",
        "role": "Swing Trader",
        "image_url": "/images/testimonials/client-b.jpg",
    }
])

# Conversion analytics
sync.landing_page.sync_conversion_data({
    "visits": 12500,
    "signups": 350,
    "conversion_rate": 2.8,
    "avg_session_duration": "4m 23s",
    "bounce_rate": 32.1,
})
```

**Where it goes:**
- `profitenginev5/landing-page/hero-metrics.json`
- `profitenginev5/landing-page/testimonials.json`
- `profitenginev5/landing-page/conversions/2026-06-18-conversions.json`

### Email Template Sync

```python
# Store an email template
sync.email.sync_template(
    template_name="daily-alert",
    html_content="""
    <html>
        <h1>Your Daily Trading Alert</h1>
        <p>Today's P&L: +$1,250.50</p>
    </html>
    """,
    text_content="Your Daily Trading Alert\n\nToday's P&L: +$1,250.50",
    metadata={
        "subject": "Your Daily Trading Alert",
        "preview_text": "Check your daily trading results",
        "from_name": "ProfitEngine Team",
        "reply_to": "support@profitengine.local",
    }
)

# Store customer segments
sync.email.sync_segments({
    "vip_traders": ["cust_001", "cust_002", "cust_005"],
    "active_traders": ["cust_001", "cust_002", "cust_003", "cust_004"],
    "inactive_traders": ["cust_006", "cust_007"],
})

# Track campaign engagement
sync.email.sync_engagement_tracking(
    campaign_id="campaign_june_18",
    opens=1240,
    clicks=340,
    conversions=45,
    unsubscribes=12,
)
```

**Where it goes:**
- `profitenginev5/emails/daily-alert.html`
- `profitenginev5/emails/daily-alert.txt`
- `profitenginev5/emails/daily-alert.json`
- `profitenginev5/emails/segments.json`
- `profitenginev5/emails/engagement/2026-06-18-campaign_june_18.json`

### Commit and Push

```python
# Commit all staged changes and push
if sync.sync(
    commit_message="chore: sync daily trading results and metrics",
    push=True  # Set to False to commit without pushing
):
    print("Sync successful!")
else:
    print("Sync failed")
```

**Commit behavior:**
- Fetches latest from origin first (pull model)
- Commits all staged changes
- Handles merge conflicts gracefully via rebase
- Pushes to configured branch
- Logs all sync events

## Daily Sync Schedule

To run the sync automatically every day at 5 PM MST:

### Linux/macOS (cron)

```bash
# Add to crontab -e
# Run at 5 PM MST (12 AM UTC) every day
0 0 * * * cd /opt/profitengine && python3 -c "from runtime.profitenginev5_sync import ProfitEngineV5Sync; sync = ProfitEngineV5Sync(); sync.initialize(); sync.metrics.sync_daily_metrics(1250, 67.5, 12, 450, 8900); sync.sync()"
```

### systemd Timer

Create `/etc/systemd/system/profitenginev5-sync.timer`:

```ini
[Unit]
Description=ProfitEngine v5 Daily Sync Timer
Requires=profitenginev5-sync.service

[Timer]
# Every day at 5 PM MST (midnight UTC, accounting for DST)
OnCalendar=*-*-* 00:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/profitenginev5-sync.service`:

```ini
[Unit]
Description=ProfitEngine v5 Sync Service
After=network.target

[Service]
Type=oneshot
User=profitengine
WorkingDirectory=/opt/profitengine
ExecStart=/usr/bin/python3 /opt/profitengine/runtime/profitenginev5_sync.py
EnvironmentFile=/opt/profitengine/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable profitenginev5-sync.timer
sudo systemctl start profitenginev5-sync.timer
```

### Python Script Integration

Integrate with existing cron/scheduler:

```python
# In your daily results reporting script (DAILY_RESULTS.py)
from runtime.profitenginev5_sync import ProfitEngineV5Sync

def sync_daily_results_to_profitenginev5(report):
    """Called from DAILY_RESULTS.py after generating daily metrics."""
    sync = ProfitEngineV5Sync()
    
    if not sync.initialize():
        logger.error("Sync init failed")
        return False
    
    # Sync metrics
    system_a = report.get("system_a", {})
    sync.metrics.sync_daily_metrics(
        pnl_dollars=system_a.get("pnl_dollars", 0),
        win_rate=system_a.get("win_rate", 0),
        trades_count=system_a.get("trades_today", 0),
        customer_count=report.get("customer_count", 0),
        revenue_dollars=report.get("revenue_dollars", 0),
        date=report.get("date"),
    )
    
    # Sync blog post if generated
    if report.get("blog_post_content"):
        sync.content.sync_blog_post(
            title=report.get("blog_post_title", "Daily Results"),
            content=report.get("blog_post_content"),
            date=report.get("date"),
        )
    
    # Commit and push
    return sync.sync()
```

## Conflict Resolution

The sync engine handles merge conflicts gracefully:

1. **Non-fast-forward push detected:** Automatically pulls and rebases
2. **Rebase successful:** Retry push
3. **Rebase fails:** Logs error, aborts sync

In case of persistent conflicts:

```bash
# Manual resolution
cd /tmp/profitenginev5
git status
git rebase --abort
git pull origin main
# Resolve conflicts manually
git add .
git commit -m "Merge conflict resolution"
git push origin main
```

## Monitoring & Logging

The sync engine logs all operations:

```
2026-06-18 17:00:00 [INFO] Synced blog post: content/trading-results/2026-06-18-markets-high.md
2026-06-18 17:00:01 [INFO] Synced metrics: metrics/2026-06-18-metrics.json
2026-06-18 17:00:02 [INFO] Committed: chore: sync daily trading results and metrics
2026-06-18 17:00:03 [INFO] Push successful
2026-06-18 17:00:03 [INFO] Sync event: {"timestamp": "2026-06-18T...", "status": "success", ...}
```

**Log locations:**
- Console: stdout/stderr
- Files: Configure in your deployment (e.g., Docker logs, systemd journal)
- JSON events: Available for structured logging integration

## Verify Deployment

After syncing, verify data arrived in profitenginev5:

```bash
# Check latest commits
cd /tmp/profitenginev5
git log --oneline -5

# List synced content
ls profitenginev5/content/trading-results/
ls profitenginev5/metrics/

# Check metrics file
cat profitenginev5/metrics/2026-06-18-metrics.json
```

Or via GitHub API:

```bash
curl -s https://api.github.com/repos/quantam101/profitenginev5/commits?per_page=5 \
  | jq '.[].commit.message'
```

## Troubleshooting

### Authentication Failures

```
RuntimeError: GitHub API error 401: Bad credentials
```

**Fix:**
- Verify `GITHUB_PROFITENGINEV5_TOKEN` is set and valid
- Check token hasn't expired
- Regenerate new token and update server secret

### Repository Cloning Issues

```
subprocess.CalledProcessError: git clone failed
```

**Fix:**
- Verify repo URL is correct
- Check network connectivity to GitHub
- Ensure `PROFITENGINEV5_LOCAL_PATH` parent directory exists
- Check disk space

### Merge Conflicts

```
[WARNING] Push rejected (non-fast-forward). Attempting rebase.
[ERROR] Conflict resolution failed
```

**Fix:**
- Check if another process is pushing simultaneously
- Review recent commits to profitenginev5 repo
- Manually resolve if persistent

### Missing Files in Repo

```
Failed to sync blog post: content/trading-results/...
```

**Fix:**
- Verify directory structure in cloned repo
- Check write permissions on local path
- Ensure sufficient disk space

## Performance

- **Sync time:** ~2-5 seconds per 100 files (depends on network)
- **Storage:** ~500 KB per day (metrics + blog post)
- **Bandwidth:** Minimal (pulls only changed files)

## Security

- **Token storage:** Never commit PAT to code, always use environment variables
- **Audit trail:** All commits logged with message and timestamp
- **Access control:** GitHub branch protection rules apply
- **Rotation:** Regenerate PAT every 90 days

## Next Steps

1. Set environment variables on your server
2. Test with `python3 runtime/profitenginev5_sync.py`
3. Integrate with your daily results pipeline
4. Schedule via cron/systemd
5. Monitor logs for sync events
6. Verify deployment to live site

---

## API Reference

### `ProfitEngineV5Sync`

Main orchestrator class.

**Methods:**
- `initialize()` → bool: Initialize (clone repo if needed)
- `sync(commit_message, push)` → bool: Execute sync
- `.content` → ContentSyncModule
- `.metrics` → MetricsSyncModule
- `.case_studies` → CaseStudySyncModule
- `.social` → SocialPerformanceSyncModule
- `.landing_page` → LandingPageSyncModule
- `.email` → EmailTemplateSyncModule

### Content Module

```python
sync.content.sync_blog_post(title, content, date) → bool
sync.content.sync_blog_posts_batch(posts) → int
```

### Metrics Module

```python
sync.metrics.sync_daily_metrics(pnl_dollars, win_rate, trades_count, 
                                customer_count, revenue_dollars, date) → bool
sync.metrics.sync_metrics_batch(metrics_list) → int
```

### Case Studies Module

```python
sync.case_studies.sync_case_study(customer_id, anonymized_name, roi_percent, 
                                  strategy, testimonial, results) → bool
```

### Social Performance Module

```python
sync.social.sync_social_metrics(platform, post_id, title, engagement, date) → bool
sync.social.sync_engagement_summary(summary, date) → bool
```

### Landing Page Module

```python
sync.landing_page.sync_hero_metrics(customers_active, trades_executed, 
                                    dollars_managed, success_rate) → bool
sync.landing_page.sync_testimonials(testimonials) → bool
sync.landing_page.sync_conversion_data(conversion_data) → bool
```

### Email Module

```python
sync.email.sync_template(template_name, html_content, text_content, metadata) → bool
sync.email.sync_segments(segments) → bool
sync.email.sync_engagement_tracking(campaign_id, opens, clicks, 
                                    conversions, unsubscribes) → bool
```

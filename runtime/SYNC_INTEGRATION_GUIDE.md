# ProfitEngine v5 Sync — Integration Guide

This guide shows how to integrate the sync engine with your existing trading system, content pipeline, and business operations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│          Autonomous Trading System                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  DAILY_RESULTS.py → Daily P&L, win rates, customer #  │
│  content_generator.py → Blog posts, market insights   │
│  upsell_intelligence.py → Case studies, customer wins │
│  live_trading_api.py → Real-time trading metrics     │
│  payment_processor.py → Revenue, customer segments   │
│  robinhood_webhook_handler.py → Trading fills       │
│                                                         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Sync Engine         │
        │  (profitenginev5_    │
        │   sync.py)           │
        │                      │
        │  • Collect data      │
        │  • Format for repo   │
        │  • Commit & push     │
        │  • Handle conflicts  │
        │  • Log events        │
        └──────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  profitenginev5 Repo │
        │  (GitHub)            │
        │                      │
        │  /content/           │
        │  /metrics/           │
        │  /case-studies/      │
        │  /landing-page/      │
        │  /analytics/         │
        │  /emails/            │
        └──────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  GitHub Actions      │
        │  Auto-Deploy         │
        │                      │
        │  Triggers on push    │
        │  Builds & deploys    │
        │  Updates live site   │
        └──────────────────────┘
                   │
                   ↓
        profitengine.alreadyherellc.com
```

## Integration Points

### 1. Daily Metrics (from DAILY_RESULTS.py)

**Current code in DAILY_RESULTS.py:**

```python
def store_daily_results(report, db_path="clients.db"):
    """Stores results in clients.db"""
    # ... existing code ...
    conn.commit()
```

**Integration:**

```python
# At the end of DAILY_RESULTS.py, after storing to database

from runtime.profitenginev5_sync import ProfitEngineV5Sync

def sync_results_to_profitenginev5(report):
    """Sync daily results to profitenginev5 repo."""
    sync = ProfitEngineV5Sync()

    if not sync.initialize():
        logger.error("Failed to initialize sync")
        return False

    # Extract metrics
    system_a = report.get("system_a", {})
    system_b = report.get("system_b", {})

    # Calculate totals
    total_pnl = system_a.get("pnl_dollars", 0) + system_b.get("pnl_dollars", 0)
    total_trades = system_a.get("trades_today", 0) + system_b.get("trades_today", 0)

    # Sync metrics
    if total_trades > 0:
        sync.metrics.sync_daily_metrics(
            pnl_dollars=total_pnl,
            win_rate=system_a.get("win_rate", 0),  # Use System A as representative
            trades_count=total_trades,
            customer_count=report.get("total_active_customers", 0),
            revenue_dollars=report.get("daily_revenue", 0),
            date=report.get("date"),
        )

    # Sync blog post if generated (optional)
    if report.get("generated_blog_post"):
        sync.content.sync_blog_post(
            title=report.get("blog_title", "Daily Trading Results"),
            content=report.get("blog_content", ""),
            date=report.get("date"),
        )

    # Commit and push
    return sync.sync()

# Call this after storing to database
if __name__ == "__main__":
    report = generate_daily_report()  # your existing function
    store_daily_results(report)        # your existing function
    sync_results_to_profitenginev5(report)  # NEW
```

### 2. Blog Posts (from content_generator.py)

**Integration:**

```python
# In your content generation pipeline

from runtime.profitenginev5_sync import ProfitEngineV5Sync

def publish_blog_post(title, content, tags):
    """Publish blog post to both BeHiiv and profitenginev5."""

    # 1. Publish to BeHiiv (existing code)
    beehiiv_url = publish_to_beehiiv(title, content, tags)

    # 2. Sync to profitenginev5 (NEW)
    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.content.sync_blog_post(title, content)
        sync.sync(commit_message=f"feat: publish blog post '{title}'")

    return beehiiv_url
```

### 3. Case Studies (from customer success)

**Integration:**

```python
# When customer successfully completes a trade/milestone

from runtime.profitenginev5_sync import ProfitEngineV5Sync

def log_customer_win(customer_id, starting_balance, ending_balance, strategy):
    """Log customer win and sync to profitenginev5."""

    roi_percent = ((ending_balance - starting_balance) / starting_balance) * 100

    # Get customer details (anonymized)
    customer = get_customer(customer_id)
    anonymized_name = f"Client {customer_id[-3:]}"  # e.g., "Client 123"

    # Create case study
    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.case_studies.sync_case_study(
            customer_id=customer_id,
            anonymized_name=anonymized_name,
            roi_percent=roi_percent,
            strategy=strategy,
            testimonial=customer.get("testimonial", "Great results!"),
            results={
                "Starting Balance": f"${starting_balance:,.2f}",
                "Ending Balance": f"${ending_balance:,.2f}",
                "Profit": f"${ending_balance - starting_balance:,.2f}",
                "ROI": f"{roi_percent:.1f}%",
                "Trading Period": "30 days",
            }
        )
        sync.sync(commit_message=f"docs: add case study for {anonymized_name}")
```

### 4. Social Media Performance

**Integration:**

```python
# In your social media posting/scheduling system

from runtime.profitenginev5_sync import ProfitEngineV5Sync

def track_social_post(platform, post_id, title, initial_metrics):
    """Track social post and sync daily metrics."""

    # Store in your local DB
    store_in_social_db(platform, post_id, title, initial_metrics)

    # Sync to profitenginev5
    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.social.sync_social_metrics(
            platform=platform,  # "twitter", "linkedin", etc.
            post_id=post_id,
            title=title,
            engagement=initial_metrics,  # {"likes": 100, "retweets": 30, ...}
        )
        sync.sync(commit_message=f"analytics: track {platform} post performance")

def aggregate_daily_social_metrics():
    """Aggregate daily social metrics and sync summary."""

    summary = {
        "twitter": get_twitter_summary(),
        "linkedin": get_linkedin_summary(),
        "youtube": get_youtube_summary(),
    }

    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.social.sync_engagement_summary(summary)
        sync.sync(commit_message="analytics: daily social engagement summary")
```

### 5. Landing Page Data

**Integration:**

```python
# In your metrics/dashboard system

from runtime.profitenginev5_sync import ProfitEngineV5Sync

def update_landing_page_metrics():
    """Update landing page with current metrics."""

    # Fetch current metrics
    active_customers = count_active_customers()
    total_trades = count_total_trades()
    aum = sum_assets_under_management()
    success_rate = calculate_success_rate()

    # Sync to profitenginev5
    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.landing_page.sync_hero_metrics(
            customers_active=active_customers,
            trades_executed=total_trades,
            dollars_managed=aum,
            success_rate=success_rate,
        )

        # Also update testimonials
        testimonials = fetch_customer_testimonials()
        sync.landing_page.sync_testimonials(testimonials)

        # And conversion data
        conversions = get_analytics_summary()
        sync.landing_page.sync_conversion_data(conversions)

        sync.sync(commit_message="chore: update landing page metrics")
```

### 6. Email Campaigns

**Integration:**

```python
# In your email campaign system

from runtime.profitenginev5_sync import ProfitEngineV5Sync

def sync_email_template(name, html, text, metadata):
    """Sync email template to profitenginev5."""

    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.email.sync_template(
            template_name=name,
            html_content=html,
            text_content=text,
            metadata=metadata,
        )
        sync.sync(commit_message=f"chore: update email template '{name}'")

def sync_customer_segments(segments_dict):
    """Sync customer segments for email targeting."""

    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.email.sync_segments(segments_dict)
        sync.sync(commit_message="chore: update customer email segments")

def track_campaign_engagement(campaign_id, opens, clicks, conversions, unsubscribes):
    """Track email campaign engagement."""

    sync = ProfitEngineV5Sync()
    if sync.initialize():
        sync.email.sync_engagement_tracking(
            campaign_id=campaign_id,
            opens=opens,
            clicks=clicks,
            conversions=conversions,
            unsubscribes=unsubscribes,
        )
        sync.sync(commit_message=f"analytics: campaign {campaign_id} engagement")
```

## Full Daily Workflow Example

Here's a complete example of a daily workflow that syncs everything:

```python
#!/usr/bin/env python3
"""
Complete daily workflow with sync.

Run this at 5 PM MST every day via cron/systemd.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add runtime to path
sys.path.insert(0, str(Path(__file__).parent))

from runtime.profitenginev5_sync import ProfitEngineV5Sync
from DAILY_RESULTS import generate_daily_report, store_daily_results
from runtime.upsell_intelligence import get_today_customer_wins


def main():
    """Execute complete daily workflow."""

    print(f"[{datetime.now()}] Starting daily workflow...")

    # Step 1: Generate daily report
    print("Step 1: Generating daily report...")
    report = generate_daily_report()
    store_daily_results(report)

    # Step 2: Initialize sync engine
    print("Step 2: Initializing sync engine...")
    sync = ProfitEngineV5Sync()
    if not sync.initialize():
        print("ERROR: Sync initialization failed")
        return False

    # Step 3: Sync metrics
    print("Step 3: Syncing metrics...")
    system_a = report.get("system_a", {})
    sync.metrics.sync_daily_metrics(
        pnl_dollars=system_a.get("pnl_dollars", 0),
        win_rate=system_a.get("win_rate", 0),
        trades_count=system_a.get("trades_today", 0),
        customer_count=report.get("total_customers", 0),
        revenue_dollars=report.get("daily_revenue", 0),
        date=report.get("date"),
    )

    # Step 4: Sync blog post (if generated)
    if report.get("blog_generated"):
        print("Step 4: Syncing blog post...")
        sync.content.sync_blog_post(
            title=report.get("blog_title"),
            content=report.get("blog_content"),
            date=report.get("date"),
        )

    # Step 5: Sync case studies (customer wins)
    print("Step 5: Syncing case studies...")
    wins = get_today_customer_wins()
    for win in wins:
        sync.case_studies.sync_case_study(
            customer_id=win["customer_id"],
            anonymized_name=win["anonymized_name"],
            roi_percent=win["roi_percent"],
            strategy=win["strategy"],
            testimonial=win["testimonial"],
            results=win["results"],
        )

    # Step 6: Update landing page metrics
    print("Step 6: Updating landing page metrics...")
    sync.landing_page.sync_hero_metrics(
        customers_active=report.get("active_customers", 0),
        trades_executed=report.get("total_trades", 0),
        dollars_managed=report.get("aum", 0),
        success_rate=report.get("success_rate", 0),
    )

    # Step 7: Sync social metrics (if available)
    if report.get("social_summary"):
        print("Step 7: Syncing social metrics...")
        sync.social.sync_engagement_summary(report.get("social_summary"))

    # Step 8: Commit and push all changes
    print("Step 8: Committing and pushing changes...")
    if sync.sync(commit_message="chore: sync daily trading results and metrics"):
        print(f"[{datetime.now()}] ✓ Daily workflow completed successfully")
        return True
    else:
        print(f"[{datetime.now()}] ✗ Daily workflow failed at sync step")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## Testing Integration

### Test 1: Manual Sync

```bash
cd /opt/profitengine
python3 -c "
from runtime.profitenginev5_sync import ProfitEngineV5Sync
sync = ProfitEngineV5Sync()
sync.initialize()
sync.metrics.sync_daily_metrics(100.50, 65.0, 10, 100, 500)
sync.sync()
"
```

**Expected output:**
```
Synced metrics: metrics/2026-06-18-metrics.json
Committed: chore: sync daily trading results and metrics
Push successful
```

### Test 2: Verify GitHub

```bash
# Check commits on profitenginev5
cd /tmp/profitenginev5
git log --oneline -5

# Check file contents
cat metrics/2026-06-18-metrics.json
```

### Test 3: Live Site

Visit your profitenginev5 deployed site:
- Check if metrics appear on landing page
- Verify blog posts are published
- Check case studies are visible

## Performance Considerations

### Sync Time

Typical sync times:
- Small sync (metrics only): 2-3 seconds
- Medium sync (metrics + blog): 4-6 seconds
- Large sync (metrics + blog + case studies): 7-10 seconds

### Storage

Typical storage per day:
- Metrics JSON: 500 bytes
- Blog post: 2-5 KB
- Case study: 1-2 KB
- Social metrics: 300 bytes
- **Total:** ~10 KB/day

Monthly: ~300 KB
Yearly: ~3.6 MB (negligible)

### Network

- Git operations: Minimal bandwidth (only changed files)
- Push: ~100 KB typical (compressed)
- **Frequency:** Once per day

## Error Handling

The sync engine gracefully handles errors:

```python
# If sync fails, log it but don't crash the daily workflow
try:
    sync.sync()
except Exception as e:
    logger.error(f"Sync failed: {e}")
    # Continue with other operations
    # The sync will retry the next day
```

## Monitoring

### Monitor Sync Health

Create a dashboard endpoint that shows:

```python
def sync_health_status():
    """Return current sync health."""
    repo_path = Path("/tmp/profitenginev5")

    return {
        "last_commit": get_last_commit_time(),
        "commits_today": count_commits_today(),
        "repo_size_mb": get_repo_size(),
        "files_changed_today": count_changed_files(),
        "health": "OK" if is_recent_sync() else "WARNING",
    }
```

### Alert on Failures

Send notification if sync fails:

```python
def notify_on_sync_failure(error_msg):
    """Send alert if sync fails."""
    send_email(
        to="ops@alreadyherellc.com",
        subject="ProfitEngine v5 Sync Failed",
        body=f"Sync error: {error_msg}",
    )
```

## Next Steps

1. **Review:** Understand the architecture above
2. **Choose:** Pick which data sources to sync first
3. **Integrate:** Add sync calls to your existing code
4. **Test:** Run manual tests as shown above
5. **Deploy:** Enable scheduler (cron/systemd)
6. **Monitor:** Watch logs for first few runs
7. **Iterate:** Add more data sources as needed

---

See also:
- `PROFITENGINEV5_SYNC_README.md` — Complete API reference
- `INSTALL_SYNC_SCHEDULER.md` — Scheduler setup guide
- `profitenginev5_sync.py` — Main sync engine code

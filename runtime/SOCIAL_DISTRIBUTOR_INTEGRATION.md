# Social Distributor — Integration Guide

## Overview

The Social Distributor integrates with the ProfitEngine runtime to automatically distribute trading content to 6 platforms. It's designed to work seamlessly with:

1. **Content Generator** (`agent_impls/content_gen.py`) — generates blog articles
2. **Daily Alerts** (`daily_alerts.py`) — sends performance summaries
3. **Blog Publisher** (`agent_impls/blog_publisher.py`) — publishes to GitHub/Dev.to
4. **Existing Social Engine** (`eaos/social_engine.py`) — handles platform APIs

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Content Sources                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Content  │  │ Daily    │  │ Trading  │              │
│  │ Generator│  │ Alerts   │  │ Results  │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
└───────┼─────────────┼─────────────┼───────────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────▼──────────────┐
        │  Social Distributor        │
        │  (social_distributor.py)   │
        │                            │
        │ • Duplicate detection      │
        │ • Format per platform      │
        │ • Schedule posts           │
        │ • Track engagement         │
        │ • Cache offline            │
        └──────┬─────────────────────┘
               │
   ┌───────────┼───────────┬────────────┬────────┬──────────┐
   │           │           │            │        │          │
▼──▼──┐  ▼─────▼───┐  ▼──────┐  ▼─────▼──┐  ▼──▼──┐  ▼────▼──┐
│Twitter│  │LinkedIn │  │TikTok │  │YouTube │  │Reddit│  │Email │
└───────┘  └─────────┘  └───────┘  └────────┘  └─────┘  └───────┘
```

## Integration Points

### 1. Content Generator Integration

**File:** `runtime/agent_impls/content_gen.py`

The content generator produces blog articles in JSON format. The Social Distributor can automatically publish these articles to all platforms:

```python
import json
import asyncio
from runtime.agent_impls.content_gen import Agent as ContentGen
from runtime.social_distributor import SocialDistributor

async def generate_and_distribute():
    # Step 1: Generate article
    gen = ContentGen()
    result = gen.run(
        objective="AI Trading Strategies",
        context="Recent market analysis and results",
        connectors=[]
    )
    
    # Step 2: Extract JSON
    article_json = result.output.split("ARTICLE_JSON:")[1]
    article = json.loads(article_json)
    
    # Step 3: Distribute
    distributor = SocialDistributor()
    results = await distributor.post_all_platforms(
        content_id=article["slug"],
        title=article["title"],
        body=article["body"][:1000],  # Use first 1000 chars
        link=f"https://profitengine.alreadyherellc.com/blog/{article['slug']}",
        platforms=["twitter", "linkedin", "reddit"],
        hashtags=article.get("tags", ["trading", "ai", "alreadyhere"]),
    )
    
    return results

asyncio.run(generate_and_distribute())
```

**Integration Pattern:** Webhook at `/api/webhooks/blog` triggers distribution after article is published.

### 2. Daily Alerts Integration

**File:** `runtime/daily_alerts.py`

Daily alerts generate performance summaries that can be distributed as social posts:

```python
from runtime.daily_alerts import Daily_AlertsEngine
from runtime.social_distributor import SocialDistributor

async def distribute_daily_alert():
    # Step 1: Generate alert
    alerts = Daily_AlertsEngine()
    summary = alerts.generate_summary()  # Contains top performers, P&L, etc.
    
    # Step 2: Create social post from alert
    distributor = SocialDistributor()
    
    # Extract key metrics
    top_performer = summary.get("top_performers", [{}])[0]
    pnl = summary.get("daily_pnl", "+$0")
    
    results = await distributor.post_all_platforms(
        content_id=f"daily_alert_{datetime.now().strftime('%Y%m%d')}",
        title=f"Daily Results: {pnl} P&L",
        body=f"Today's trading performance: {top_performer.get('description', '')}",
        link="https://profitengine.alreadyherellc.com/dashboard",
        platforms=["twitter", "linkedin"],
        hashtags=["trading", "results", "daytrading", "passive_income"],
    )
    
    return results
```

**Integration Pattern:** Daily alerts cron job (5 PM MST) triggers social posts after alert is sent.

### 3. Blog Publisher Integration

**File:** `runtime/agent_impls/blog_publisher.py`

Blog publisher posts articles to GitHub Pages and Dev.to. Social Distributor broadcasts them further:

```python
from runtime.agent_impls.blog_publisher import publish_to_github, publish_to_devto
from runtime.social_distributor import SocialDistributor

async def full_publishing_pipeline(article):
    # Step 1: Publish to GitHub & Dev.to
    github_url = publish_to_github(article)
    devto_url = publish_to_devto(article)
    
    # Step 2: Distribute to social platforms
    distributor = SocialDistributor()
    
    # Use GitHub Pages URL as canonical link
    results = await distributor.post_all_platforms(
        content_id=article["slug"],
        title=article["title"],
        body=article["body"][:1000],
        link=github_url,
        platforms=["twitter", "linkedin", "reddit", "tiktok"],
        hashtags=article.get("tags", []),
        image_url=article.get("featured_image"),
        video_path=article.get("video_path"),
    )
    
    return {
        "github": github_url,
        "devto": devto_url,
        "social": results,
    }
```

**Integration Pattern:** Webhook at `/api/webhooks/blog` triggers after GitHub publication.

### 4. Existing Social Engine Integration

**File:** `runtime/eaos/social_engine.py`

The Social Distributor uses the existing `ProductionSocialEngine` for low-level platform API calls:

```python
# social_distributor.py uses this internally:
from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost

engine = ProductionSocialEngine()

# Create native SocialPost object
post = SocialPost(
    db_id=None,
    platform="TWITTER",
    text_content="Tweet text here",
    media_path=None,
    extra={"thread_tweets": [...]},
)

# Publish to platform
await engine.publish(post)

# Or blast to all platforms
await engine.publish_all_platforms(
    text="Content here",
    url="https://...",
    tags=["tag1", "tag2"],
    thread_tweets=[...],
    video_path="/path/to/video.mp4",
)
```

**Key Integration:** Social Distributor wraps ProductionSocialEngine to add:
- Database tracking
- Duplicate detection
- Engagement metrics
- Scheduling
- Email digests

## API Integration

### FastAPI Routes

The Social Distributor registers these routes on the main ProfitEngine API:

```python
# In runtime/api.py or where you initialize FastAPI:
from runtime.social_distributor import register_routes

app = FastAPI()
register_routes(app)
```

Available endpoints:

```
POST   /api/social/distribute     — Distribute to platforms
GET    /api/social/posts          — List posts by platform
GET    /api/social/engagement     — Top posts by engagement
POST   /api/social/digest         — Send email digest
```

### Example: Webhook Handler

```python
from fastapi import APIRouter, Request, HTTPException
from runtime.social_distributor import SocialDistributor

router = APIRouter()
distributor = SocialDistributor()

@router.post("/webhooks/blog")
async def blog_published(request: Request):
    """
    Triggered when blog article is published to GitHub Pages.
    Automatically distributes to social platforms.
    """
    payload = await request.json()
    
    # Verify webhook signature
    if not verify_webhook_signature(request, payload):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Extract article details
    article = payload["article"]
    
    # Distribute to platforms
    results = await distributor.post_all_platforms(
        content_id=article["slug"],
        title=article["title"],
        body=article["body"][:1000],
        link=payload["url"],
        platforms=["twitter", "linkedin", "reddit"],
        hashtags=article.get("tags", []),
    )
    
    return {"ok": True, "results": results}
```

## Scheduling Integration

### Initialize Scheduler

```python
from runtime.social_distributor import SocialDistributor

# In your main app startup:
distributor = SocialDistributor()
distributor.schedule_daily_posts()

# Schedule now runs in background thread
# Posts will fire automatically at scheduled times
```

### Integration with APScheduler Middleware

```python
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()
scheduler = BackgroundScheduler()

@app.on_event("startup")
async def startup():
    # Initialize social distributor scheduler
    from runtime.social_distributor import SocialDistributor
    distributor = SocialDistributor()
    distributor.schedule_daily_posts()
    
    print("Social distributor scheduler started")

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
```

## Database Integration

### Sharing Database

The Social Distributor uses its own SQLite database (`datacenter/social_distributor.db`) but can query data from other services:

```python
from runtime.social_distributor import SocialDistributor
from runtime.daily_alerts import Database as AlertsDB

distributor = SocialDistributor()

# Get top posts
top_posts = distributor.db.get_top_posts_by_engagement(days=7)

# Cross-reference with alerts
alerts_db = AlertsDB()
for post in top_posts:
    # Check if this post's date has alert data
    alert_data = alerts_db.get_alert_for_date(post.created_at)
    print(f"{post.title}: {alert_data}")
```

### Database Tables

**social_posts:**
- Core post data (title, body, link, platform, status)
- Engagement metrics (likes, retweets, comments, views)
- Scheduling info (scheduled_at, posted_at)
- Error tracking (error_message, retry_count)

**engagement_metrics:**
- Per-platform engagement snapshots
- Updated periodically via API polls
- Used for analytics and reporting

**post_schedule:**
- Configured posting times per platform
- Frequency (daily, weekly, etc.)
- Enable/disable flags

## Monitoring & Observability

### Logging Integration

```python
import logging

# Social Distributor logs to social_distributor.log
# Also streams to stdout for monitoring

logger = logging.getLogger("social_distributor")

# Monitor posting activities
logger.info("[Twitter] Posted tweet id=12345")
logger.error("[LinkedIn] Post failed: rate limit exceeded")
logger.warning("[Reddit] Post cached — offline journal")
```

### Metrics Collection

```python
from runtime.social_distributor import SocialDistributor

distributor = SocialDistributor()

# Get metrics
top_posts = distributor.db.get_top_posts_by_engagement()
metrics = {
    "total_posts": len(distributor.db.list_posts_by_platform("twitter")),
    "top_posts_engagement": sum(
        p.engagement_likes + p.engagement_retweets
        for p in top_posts
    ),
    "platforms_active": len(set(
        p.platform for p in distributor.db.list_posts_by_platform("twitter")
    )),
}
```

### Health Check Endpoint

```python
@app.get("/health/social")
def social_distributor_health():
    """Check social distributor status."""
    distributor = SocialDistributor()
    
    # Check database
    try:
        test_post = distributor.db.get_post(1)
        db_ok = True
    except Exception as e:
        db_ok = False
    
    # Check credentials
    creds_ok = bool(os.getenv("TWITTER_API_KEY"))
    
    # Recent activity
    recent = distributor.db.list_posts_by_platform("twitter", "posted")
    
    return {
        "ok": db_ok and creds_ok,
        "database": db_ok,
        "credentials": creds_ok,
        "recent_posts": len(recent),
        "scheduler_running": distributor.scheduler is not None,
    }
```

## Deployment

### Docker Integration

```dockerfile
# In your Dockerfile
RUN pip install apscheduler requests

# Social distributor runs automatically with your app
CMD ["uvicorn", "runtime.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### GitHub Actions

```yaml
# In .github/workflows/publish.yml
- name: Distribute to social platforms
  if: github.ref == 'refs/heads/main'
  run: |
    python -c "
    import asyncio
    from runtime.social_distributor import SocialDistributor
    
    async def main():
        dist = SocialDistributor()
        # Trigger distribution of today's posts
        
    asyncio.run(main())
    "
```

### Environment Secrets

Set in GitHub Secrets:
```
TWITTER_API_KEY
TWITTER_API_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_SECRET
LINKEDIN_ACCESS_TOKEN
LINKEDIN_PERSON_URN
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USERNAME
REDDIT_PASSWORD
TIKTOK_ACCESS_TOKEN
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
GMAIL_USER
GMAIL_APP_PASSWORD
ALERT_EMAIL
```

## Testing

### Unit Tests

```python
import pytest
from runtime.social_distributor import SocialDistributor, SocialPost

def test_duplicate_detection():
    distributor = SocialDistributor()
    
    # First post
    posts1 = distributor.create_post(
        content_id="test_001",
        title="Test Post",
        body="Test body",
        link="https://example.com",
        platforms=["twitter"],
    )
    assert len(posts1) == 1
    
    # Duplicate attempt
    posts2 = distributor.create_post(
        content_id="test_001",
        title="Test Post",
        body="Test body",
        link="https://example.com",
        platforms=["twitter"],
    )
    assert len(posts2) == 0

def test_platform_formatting():
    post = SocialPost(
        platform="twitter",
        title="Test",
        body="Body",
        link="https://example.com",
        hashtags=["test"],
    )
    
    from runtime.social_distributor import PlatformFormatter
    text = PlatformFormatter.format_twitter(post)
    assert len(text) <= 280
    assert "#test" in text
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_distribution_pipeline():
    distributor = SocialDistributor()
    
    results = await distributor.post_all_platforms(
        content_id="test_full_001",
        title="Integration Test Post",
        body="Testing full distribution pipeline",
        link="https://profitengine.alreadyherellc.com",
        platforms=["twitter", "linkedin"],
    )
    
    # Verify posts were created
    twitter_posts = distributor.db.list_posts_by_platform("twitter")
    assert len(twitter_posts) > 0
```

## Troubleshooting

### Posts not scheduling

1. Check if APScheduler is installed: `pip list | grep apscheduler`
2. Verify scheduler is initialized: `print(distributor.scheduler)`
3. Check logs: `tail -f social_distributor.log`

### Credentials not loading

1. Verify variables are in server `.env` (not `.env.example`)
2. Check for hidden BOM characters: `od -c .env | head`
3. Restart service: `docker restart profitengine-runtime`

### Database locks

1. Check if multiple processes access DB: `lsof datacenter/social_distributor.db`
2. Clear locks: `rm -f datacenter/social_distributor.db-*`
3. Verify WAL mode: `sqlite3 datacenter/social_distributor.db "PRAGMA journal_mode;"`

## Performance Optimization

### Batch Distribution

For high-volume posting, use batch mode:

```python
async def batch_distribute(articles: List[dict]):
    distributor = SocialDistributor()
    
    tasks = []
    for article in articles:
        task = distributor.post_all_platforms(
            content_id=article["slug"],
            title=article["title"],
            body=article["body"][:1000],
            link=article["link"],
            platforms=["twitter", "linkedin"],
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### Engagement Polling

Update engagement metrics periodically:

```python
async def poll_engagement():
    """Background job to poll engagement metrics every hour."""
    distributor = SocialDistributor()
    
    while True:
        posts = distributor.db.list_posts_by_platform("twitter", "posted")
        for post in posts:
            # Query Twitter API for engagement
            # Update: distributor.db.update_engagement(...)
            pass
        
        await asyncio.sleep(3600)  # 1 hour
```

---

**Next Steps:**
1. Review [SOCIAL_DISTRIBUTOR_SETUP.md](SOCIAL_DISTRIBUTOR_SETUP.md) for platform setup
2. Check [social_distributor_examples.py](social_distributor_examples.py) for code examples
3. Run integration tests
4. Deploy and monitor

# Analytics Tracking - Quick Reference Card

## Import & Initialize

```python
from lib.analytics_tracker import (
    AnalyticsTrackingManager,
    PublishPlatform,
    EngagementType,
)

analytics = AnalyticsTrackingManager()
```

## Platforms

```python
PublishPlatform.BLOG
PublishPlatform.TWITTER
PublishPlatform.REDDIT
PublishPlatform.FACEBOOK
PublishPlatform.LINKEDIN
PublishPlatform.INSTAGRAM
PublishPlatform.TIKTOK
PublishPlatform.TELEGRAM
PublishPlatform.MASTODON
PublishPlatform.BLUESKY
PublishPlatform.YOUTUBE
PublishPlatform.NEWSLETTER
PublishPlatform.DEVTO
PublishPlatform.HASHNODE
PublishPlatform.BEEHIIV
PublishPlatform.GUMROAD
PublishPlatform.PRINTIFY
```

## Engagement Types

```python
EngagementType.LIKE
EngagementType.SHARE
EngagementType.COMMENT
EngagementType.RETWEET
EngagementType.SAVE
EngagementType.CLICK
EngagementType.VIEW
EngagementType.WATCH
```

## Log Article Published

```python
article_id = analytics.log_article_published(
    title="Article Title",
    topic="automation",
    slug="article-slug",
    word_count=1500,
    tags=["tag1", "tag2"],
    quality_score=0.85  # Optional, 0.0-1.0
)
```

## Log Platform Distribution

```python
success = analytics.log_platform_distribution(
    article_id=article_id,
    platform=PublishPlatform.TWITTER,
    url="https://twitter.com/...",
    status="success",  # "pending", "success", "failed", "skipped"
    error_message="Error details if failed",  # Optional
    metadata={"custom": "data"}  # Optional
)
```

## Log User Engagement

```python
success = analytics.log_user_engagement(
    article_id=article_id,
    platform=PublishPlatform.BLOG,
    engagement_type=EngagementType.CLICK,
    is_conversion=False,
    conversion_value_usd=None,  # Optional
    user_country="US",  # Optional
    user_device="mobile",  # Optional
    click_source="social"  # "social", "search", "direct", "affiliate"
)
```

## Log Conversion

```python
success = analytics.log_user_engagement(
    article_id=article_id,
    platform=PublishPlatform.GUMROAD,
    engagement_type=EngagementType.CLICK,
    is_conversion=True,
    conversion_value_usd=4.99,
    click_source="affiliate"
)
```

## Log Channel Revenue

```python
success = analytics.log_channel_revenue(
    article_id=article_id,
    platform=PublishPlatform.GUMROAD,
    channel="ebook",  # "affiliate", "ebook", "pod", "direct"
    revenue_usd=4.99,
    transaction_count=1  # Optional, default 1
)
```

## Log Social Metrics

```python
success = analytics.log_social_metrics(
    article_id=article_id,
    platform=PublishPlatform.TWITTER,
    post_id="tweet-id",
    likes=42,  # Optional
    shares=8,  # Optional
    comments=3,  # Optional
    saves=0,  # Optional
    impressions=500,  # Optional
    reach=300  # Optional
)
```

## Log Video Metrics

```python
success = analytics.log_video_metrics(
    article_id=article_id,
    platform=PublishPlatform.YOUTUBE,
    video_id="video-id",
    video_title="Video Title",
    views=1000,  # Optional
    watch_time_minutes=500.0,  # Optional
    clicks=50,  # Optional
    shares=10  # Optional
)
```

## Get Analytics Summary

```python
report = analytics.get_analytics_summary(article_id)

# Returns dict with:
# {
#   "article_id": "...",
#   "timestamp": "...",
#   "mongodb": {
#     "article": {...},
#     "distributions": [...],
#     "engagements": [...],
#     "revenue": [...],
#     "social_engagement": [...],
#     "video_metrics": [...],
#     "totals": {...}
#   },
#   "postgresql": {
#     "revenue_summary": {...},
#     "platform_performance": [...]
#   }
# }
```

## Close Connections

```python
analytics.close()
```

## Publisher Integration Hook

```python
from lib.analytics_integration import create_analytics_hook

hook = create_analytics_hook()

# Log article generation
article_id = hook.on_article_generated(article_dict, topic)

# Log GitHub publication
hook.on_github_published(article_id, canonical_url)

# Log social distribution
hook.on_social_distribution_complete(article_id, social_results)

# Log e-commerce distribution
hook.on_ecommerce_distribution_complete(article_id, ecommerce_results)

# Log user click
hook.on_user_click(article_id, "twitter")

# Log conversion
hook.on_conversion(article_id, "gumroad", 4.99)

# Log social engagement
hook.on_social_engagement_update(
    article_id, "twitter", "post-id",
    likes=42, shares=8, impressions=500
)

# Log video metrics
hook.on_video_published(
    article_id, "youtube", "video-id", "Title",
    views=1000, watch_time_minutes=500
)

# Get report
report = hook.generate_analytics_report(article_id)

hook.close()
```

## Common MongoDB Queries

```python
# Get article
db.articles.find_one({"article_id": article_id})

# Get distributions
db.platform_distributions.find({"article_id": article_id})

# Get engagements
db.user_engagements.find({"article_id": article_id})

# Get revenue
db.channel_revenue.aggregate([
    {"$match": {"article_id": article_id}},
    {"$group": {"_id": "$platform", "total": {"$sum": "$revenue_usd"}}}
])
```

## Common PostgreSQL Queries

```sql
-- Get article with stats
SELECT a.*, COUNT(DISTINCT pd.platform) as platforms
FROM articles a
LEFT JOIN platform_distributions pd ON a.article_id = pd.article_id
WHERE a.article_id = %s
GROUP BY a.article_id;

-- Get revenue by platform
SELECT platform, SUM(revenue_usd) as total
FROM channel_revenue
WHERE article_id = %s
GROUP BY platform;

-- Get conversion rate
SELECT
    COUNT(*) as total_engagements,
    SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END) as conversions,
    ROUND(100.0 * SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END) / COUNT(*), 2) as conversion_rate_percent
FROM user_engagements
WHERE article_id = %s;

-- Get social performance
SELECT
    platform,
    SUM(likes) as likes,
    SUM(shares) as shares,
    SUM(impressions) as impressions,
    AVG(engagement_rate) as avg_engagement_rate
FROM social_engagement
WHERE article_id = %s
GROUP BY platform;
```

## Environment Variables

```bash
# Required for MongoDB tracking
export MONGODB_URL="mongodb://user:password@host:27017/profitengine"

# Required for PostgreSQL tracking
export DATABASE_URL="postgresql://user:password@localhost:5432/profitengine"
```

## Common Patterns

### Pattern 1: Track Complete Article Lifecycle

```python
# 1. Log article
article_id = analytics.log_article_published(...)

# 2. Log distribution to platform
analytics.log_platform_distribution(article_id, PublishPlatform.BLOG, url, "success")

# 3. Log user interactions
analytics.log_user_engagement(article_id, PublishPlatform.BLOG, EngagementType.CLICK)

# 4. Log revenue
analytics.log_channel_revenue(article_id, PublishPlatform.GUMROAD, "ebook", 4.99)

# 5. Get report
report = analytics.get_analytics_summary(article_id)
```

### Pattern 2: Track Social Campaign

```python
for platform in [PublishPlatform.TWITTER, PublishPlatform.REDDIT]:
    analytics.log_platform_distribution(
        article_id,
        platform,
        post_url,
        "success"
    )

# Later: update metrics
analytics.log_social_metrics(
    article_id,
    PublishPlatform.TWITTER,
    post_id,
    likes=42,
    impressions=500
)
```

### Pattern 3: Track Revenue Streams

```python
# Affiliate revenue
analytics.log_channel_revenue(article_id, PublishPlatform.BLOG, "affiliate", 2.50)

# Ebook revenue
analytics.log_channel_revenue(article_id, PublishPlatform.GUMROAD, "ebook", 4.99)

# POD revenue
analytics.log_channel_revenue(article_id, PublishPlatform.PRINTIFY, "pod_tshirt", 15.00)

# Get summary
summary = analytics.get_analytics_summary(article_id)
total_revenue = summary["mongodb"]["totals"]["total_revenue"]
```

## Debugging

```python
# Check if databases connected
if analytics.mongo:
    print("MongoDB connected")
if analytics.postgres:
    print("PostgreSQL connected")

# Get raw analytics
report = analytics.get_analytics_summary(article_id)
print(json.dumps(report, indent=2, default=str))

# Check specific platform
from pprint import pprint
platform_perf = analytics.postgres.get_platform_performance(article_id)
pprint(platform_perf)
```

## Error Handling

```python
try:
    analytics = AnalyticsTrackingManager()
    
    article_id = analytics.log_article_published(...)
    
    if not article_id:
        print("Failed to log article")
        
    success = analytics.log_platform_distribution(...)
    
    if not success:
        print("Failed to log distribution")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    analytics.close()
```

## Testing

```bash
# Run all tests
pytest tests/test_analytics_tracking.py -v

# Run specific test
pytest tests/test_analytics_tracking.py::TestAnalyticsTrackingManager::test_log_article_published -v

# Run with coverage
pytest tests/test_analytics_tracking.py --cov=lib/analytics_tracker --cov-report=html
```

## Performance Tips

1. **Batch operations** - Log multiple events before calling `get_analytics_summary()`
2. **Use connection pooling** - PostgreSQL uses pooling by default
3. **Archive old data** - Remove records older than 1 year
4. **Filter by article_id** - Always include in queries
5. **Close connections** - Call `analytics.close()` when done

## References

- Full docs: `lib/ANALYTICS_README.md`
- Schema: `lib/DATABASE_SCHEMA.md`
- Implementation: `lib/ANALYTICS_IMPLEMENTATION_SUMMARY.md`
- Tests: `tests/test_analytics_tracking.py`
- Integration: `lib/analytics_integration.py`
- Usage script: `scripts/publish_article_with_analytics.py`

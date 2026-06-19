# ProfitEngine Analytics Tracking System

## Overview

The ProfitEngine analytics tracking system provides comprehensive, real-time tracking of article publication, distribution, engagement, and revenue across all platforms (blog, social media, e-commerce).

The system uses two complementary databases:
- **MongoDB** - Flexible document storage for event-based tracking
- **PostgreSQL** - Structured relational database for analytics and reporting

Both are synchronized automatically through the `AnalyticsTrackingManager`.

## Quick Start

### 1. Installation

Add required dependencies to `requirements.txt`:

```bash
pymongo>=4.0.0
psycopg2-binary>=2.9.0
```

Install:
```bash
pip install -r requirements.txt
```

### 2. Configuration

Set environment variables:

```bash
# MongoDB
export MONGODB_URL="mongodb://user:password@host:27017/profitengine"

# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/profitengine"
```

### 3. Basic Usage

```python
from lib.analytics_tracker import AnalyticsTrackingManager, PublishPlatform

# Initialize
analytics = AnalyticsTrackingManager()

# Log article publication
article_id = analytics.log_article_published(
    title="How to Automate Your Business",
    topic="automation",
    slug="automate-business",
    word_count=1500,
    tags=["automation", "revenue", "smallbusiness"],
    quality_score=0.85
)

# Log platform distribution
analytics.log_platform_distribution(
    article_id=article_id,
    platform=PublishPlatform.TWITTER,
    url="https://twitter.com/...",
    status="success"
)

# Log user engagement
analytics.log_user_engagement(
    article_id=article_id,
    platform=PublishPlatform.BLOG,
    engagement_type=EngagementType.CLICK,
    is_conversion=True,
    conversion_value_usd=4.99
)

# Get analytics summary
summary = analytics.get_analytics_summary(article_id)
print(summary)

# Clean up
analytics.close()
```

## Architecture

### Component: `analytics_tracker.py`

Core tracking module with:
- Data models (ArticleMetadata, PlatformDistribution, UserEngagement, etc.)
- MongoDB tracker (MongoAnalyticsTracker)
- PostgreSQL tracker (PostgreSQLAnalyticsTracker)
- Unified manager (AnalyticsTrackingManager)

### Component: `analytics_integration.py`

Integration hooks for `publish_article_resilient.py`:
- `PublishingAnalyticsHook` - Event hooks for publishing workflow
- `create_analytics_hook()` - Factory function

### Component: `publish_article_with_analytics.py`

Enhanced publisher that automatically logs all events:
```bash
python scripts/publish_article_with_analytics.py "Article Topic"
```

## Data Models

### ArticleMetadata

```python
@dataclass
class ArticleMetadata:
    article_id: str              # UUID
    title: str                   # Article title
    topic: str                   # Topic/category
    slug: str                    # URL slug
    publish_date: str            # ISO 8601 timestamp
    word_count: int              # Word count
    tags: List[str]              # Content tags
    quality_score: Optional[float]  # 0.0-1.0
    author: str                  # Author name
    category: str                # Content category
    featured: bool               # Featured flag
    created_at: str              # Timestamp
```

### PlatformDistribution

```python
@dataclass
class PlatformDistribution:
    distribution_id: str         # UUID
    article_id: str              # Reference to article
    platform: PublishPlatform    # Platform enum
    published_at: str            # Publish timestamp
    url: str                     # Content URL
    status: str                  # "pending", "success", "failed"
    error_message: Optional[str] # Error details
    metadata: Dict[str, Any]     # Platform-specific data
    created_at: str              # Timestamp
```

### UserEngagement

```python
@dataclass
class UserEngagement:
    engagement_id: str           # UUID
    article_id: str              # Reference to article
    platform: PublishPlatform    # Platform enum
    engagement_type: EngagementType  # Enum: click, view, like, share, etc.
    user_id: Optional[str]       # Anonymous user ID
    user_country: Optional[str]  # Country code
    user_device: Optional[str]   # Device type
    click_source: Optional[str]  # "social", "search", "direct", "affiliate"
    is_conversion: bool          # Conversion flag
    conversion_value_usd: Optional[float]  # Conversion value
    created_at: str              # Timestamp
```

### ChannelRevenue

```python
@dataclass
class ChannelRevenue:
    revenue_id: str              # UUID
    article_id: str              # Reference to article
    platform: PublishPlatform    # Platform enum
    channel: str                 # "affiliate", "ebook", "pod", "direct"
    revenue_usd: float           # Revenue amount
    currency: str                # Currency code (default: "USD")
    transaction_count: int       # Number of transactions
    created_at: str              # Timestamp
    metadata: Dict[str, Any]     # Additional data
```

### SocialEngagement

```python
@dataclass
class SocialEngagement:
    metric_id: str               # UUID
    article_id: str              # Reference to article
    platform: PublishPlatform    # Platform enum
    post_id: str                 # Platform post ID
    likes: int                   # Like count
    shares: int                  # Share count
    comments: int                # Comment count
    saves: int                   # Save count
    impressions: int             # Impression count
    reach: int                   # Total reach
    engagement_rate: Optional[float]  # Calculated %
    created_at: str              # Timestamp
    updated_at: str              # Last update
```

### VideoMetrics

```python
@dataclass
class VideoMetrics:
    video_id: str                # UUID
    article_id: str              # Reference to article
    platform: PublishPlatform    # Platform enum
    video_title: str             # Video title
    views: int                   # View count
    watch_time_minutes: float    # Watch time
    watch_time_percentage: Optional[float]  # Calculated %
    clicks: int                  # Click count
    shares: int                  # Share count
    created_at: str              # Timestamp
    updated_at: str              # Last update
```

## Publishing Integration

### Manual Integration

```python
from lib.analytics_integration import create_analytics_hook

# Create hook
hook = create_analytics_hook()

# Log article generation
article_id = hook.on_article_generated(
    article=article_dict,
    topic="Article Topic"
)

# Log GitHub publication
hook.on_github_published(article_id, canonical_url)

# Log social distribution
hook.on_social_distribution_complete(article_id, social_results)

# Log e-commerce distribution
hook.on_ecommerce_distribution_complete(article_id, ecommerce_results)

# Get analytics report
report = hook.generate_analytics_report(article_id)

# Clean up
hook.close()
```

### Automated Integration

Use `publish_article_with_analytics.py`:

```bash
python scripts/publish_article_with_analytics.py "Your Article Topic"
```

This automatically:
1. Logs article metadata
2. Tracks GitHub publication
3. Monitors social distribution
4. Tracks e-commerce monetization
5. Generates comprehensive analytics report

## Platform Support

### Supported Platforms

- **Social Media**: Twitter, Reddit, Facebook, LinkedIn, Instagram, TikTok, Telegram, Mastodon, Bluesky
- **Publishing**: Dev.to, Hashnode, Beehiiv, Blog (GitHub Pages)
- **E-Commerce**: Gumroad (ebooks), Printify (POD products)
- **Video**: YouTube, TikTok, Instagram Reels
- **Email**: Newsletter platforms

### Engagement Types

- `LIKE` - Like/favorite action
- `SHARE` - Share action
- `COMMENT` - Comment/reply action
- `RETWEET` - Retweet/quote action
- `SAVE` - Save/bookmark action
- `CLICK` - Click action
- `VIEW` - View/impression action
- `WATCH` - Video watch action

## Revenue Tracking

### Channel Types

- **affiliate** - Affiliate link clicks and referrals
- **ebook** - E-book sales via Gumroad
- **pod** - Print-on-demand product sales (Printify)
- **direct** - Direct sales or sponsorships

### Revenue Logging

```python
# Log Gumroad ebook revenue
analytics.log_channel_revenue(
    article_id=article_id,
    platform=PublishPlatform.GUMROAD,
    channel="ebook",
    revenue_usd=4.99,
    transaction_count=1
)

# Log POD product revenue
analytics.log_channel_revenue(
    article_id=article_id,
    platform=PublishPlatform.PRINTIFY,
    channel="pod_tshirt",
    revenue_usd=15.00,
    transaction_count=1
)

# Log affiliate revenue
analytics.log_channel_revenue(
    article_id=article_id,
    platform=PublishPlatform.BLOG,
    channel="affiliate",
    revenue_usd=2.50,
    transaction_count=1
)
```

## Analytics Queries

### MongoDB Examples

```python
# Get all articles
articles = db.articles.find({})

# Top articles by quality
top = db.articles.find().sort("quality_score", -1).limit(10)

# Articles by topic
automation = db.articles.find({"topic": "automation"})

# Recent articles
recent = db.articles.find().sort("publish_date", -1).limit(5)
```

### PostgreSQL Examples

```sql
-- Total revenue by platform
SELECT platform, SUM(revenue_usd) as total_revenue
FROM channel_revenue
GROUP BY platform
ORDER BY total_revenue DESC;

-- Conversion rate by platform
SELECT
    p.platform,
    COUNT(DISTINCT p.article_id) as articles,
    COUNT(DISTINCT ue.engagement_id) as engagements,
    COUNT(DISTINCT CASE WHEN ue.is_conversion THEN ue.engagement_id END) as conversions,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN ue.is_conversion THEN ue.engagement_id END) /
        NULLIF(COUNT(DISTINCT ue.engagement_id), 0),
        2
    ) as conversion_rate_percent
FROM platform_distributions p
LEFT JOIN user_engagements ue ON p.article_id = ue.article_id
GROUP BY p.platform
ORDER BY conversion_rate_percent DESC;

-- Revenue per article
SELECT
    a.title,
    SUM(cr.revenue_usd) as revenue,
    COUNT(DISTINCT cr.platform) as platforms,
    ROUND(AVG(cr.revenue_usd), 2) as avg_per_platform
FROM articles a
LEFT JOIN channel_revenue cr ON a.article_id = cr.article_id
GROUP BY a.article_id, a.title
ORDER BY revenue DESC;
```

## Reporting

### Generate Article Report

```python
analytics = AnalyticsTrackingManager()

# Get comprehensive summary
report = analytics.get_analytics_summary(article_id)

# Report structure:
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
#     "totals": {
#       "platforms": 10,
#       "engagements": 150,
#       "total_revenue": 25.50,
#       "total_social_likes": 500,
#       "total_video_views": 2000
#     }
#   },
#   "postgresql": {
#     "revenue_summary": {...},
#     "platform_performance": [...]
#   }
# }
```

## Testing

Run tests:

```bash
pytest tests/test_analytics_tracking.py -v
```

Test coverage includes:
- Data model creation and validation
- MongoDB tracking
- PostgreSQL tracking
- Unified manager operations
- Integration with publisher
- Data integrity checks
- Enum validation

## Error Handling

The system handles errors gracefully:

```python
try:
    analytics = AnalyticsTrackingManager()
    
    # Track events...
    article_id = analytics.log_article_published(...)
    
except Exception as e:
    print(f"Analytics error: {e}")
    # System continues even if tracking fails
finally:
    analytics.close()
```

### Connection Failures

- MongoDB: Connection pooling with auto-reconnect
- PostgreSQL: Connection pool management with timeout handling
- Both: Graceful degradation if database unavailable

## Performance Considerations

### Optimization Tips

1. **Batch Operations**: Group multiple log operations
2. **Indexing**: Ensure indexes are created before bulk inserts
3. **Connection Pooling**: PostgreSQL uses connection pooling (default: 5)
4. **Archival**: Archive data older than 1 year
5. **Query Filtering**: Always filter by article_id first

### Recommended Configuration

```python
# Initialize with custom pool size
manager = PostgreSQLAnalyticsTracker(
    database_url=os.getenv("DATABASE_URL"),
    pool_size=10  # Adjust based on throughput
)
```

## Maintenance

### MongoDB Maintenance

```bash
# Rebuild indexes
db.articles.reIndex()
db.platform_distributions.reIndex()

# Compact database (admin only)
db.runCommand({compact: "articles"})
```

### PostgreSQL Maintenance

```sql
-- Analyze tables for query optimization
ANALYZE articles;
ANALYZE platform_distributions;

-- Vacuum to reclaim space
VACUUM ANALYZE;

-- View index sizes
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_indexes
WHERE schemaname != 'pg_catalog'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Troubleshooting

### MongoDB Connection Issues

```python
# Check connection
try:
    client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("Connected!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### PostgreSQL Connection Issues

```python
# Check connection
import psycopg2
try:
    conn = psycopg2.connect(database_url)
    conn.close()
    print("Connected!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Data Integrity Issues

```sql
-- Check for orphaned records
SELECT * FROM platform_distributions
WHERE article_id NOT IN (SELECT article_id FROM articles);

-- Check for duplicate articles
SELECT article_id, COUNT(*)
FROM articles
GROUP BY article_id
HAVING COUNT(*) > 1;
```

## Security Considerations

1. **Connection Strings**: Store in environment variables, never commit
2. **Database Users**: Use limited-privilege accounts for application
3. **SQL Injection**: All queries use parameterized statements (safe from injection)
4. **MongoDB Injection**: All writes use typed dataclasses
5. **Data Encryption**: Enable SSL/TLS for database connections
6. **Access Control**: Restrict database access by IP/firewall

### Secure Configuration Example

```bash
# Use environment variables
export MONGODB_URL="mongodb+srv://user:password@cluster.mongodb.net/profitengine?retryWrites=true&w=majority"
export DATABASE_URL="postgresql://user:secure_password@prod-db.example.com:5432/profitengine?sslmode=require"
```

## Roadmap

Future enhancements:
- [ ] Real-time dashboard (WebSocket updates)
- [ ] Automated report generation (daily/weekly)
- [ ] Machine learning for engagement prediction
- [ ] Revenue forecasting
- [ ] A/B testing framework
- [ ] Content recommendation engine
- [ ] Audience segmentation
- [ ] Retention analysis

## Support

For issues or questions:
1. Check DATABASE_SCHEMA.md for detailed schema documentation
2. Review test files in tests/test_analytics_tracking.py
3. Check analytics_integration.py for integration examples
4. Review error logs in MongoDB/PostgreSQL

## License

Same as ProfitEngine project.

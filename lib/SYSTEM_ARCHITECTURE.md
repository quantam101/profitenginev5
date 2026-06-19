# MongoDB & PostgreSQL Analytics System Architecture

## System Overview Diagram

The analytics tracking system is a multi-layer architecture:

```
┌─ Application Layer ─────────────────────────────────────────┐
│ publish_article_resilient.py                                │
│ (generates articles, distributes to platforms)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─ Integration Layer ─────────────────────────────────────────┐
│ analytics_integration.py (PublishingAnalyticsHook)          │
│ (converts events to analytics tracking calls)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─ Tracking Layer ──────────────────────────────────────────┐
│ analytics_tracker.py (AnalyticsTrackingManager)           │
│ (unified manager for both MongoDB and PostgreSQL)         │
├─────────────────────┬─────────────────────────────────────┤
│ MongoAnalytics      │ PostgreSQLAnalytics                 │
│ - 6 collections     │ - 6 tables with FK constraints      │
│ - Auto-indexing     │ - Connection pooling                │
│ - Document storage  │ - Relational storage                │
└─────────────────────┴─────────────────────────────────────┘
        │                              │
        ▼                              ▼
   MongoDB Database           PostgreSQL Database
```

## Key Components

### 1. analytics_tracker.py
- **Data Models**: 6 dataclasses for all tracking events
- **MongoDB Tracker**: Document-based event storage
- **PostgreSQL Tracker**: Relational analytics database
- **Unified Manager**: Synchronizes writes to both databases

### 2. analytics_integration.py
- **PublishingAnalyticsHook**: High-level event hooks
- **Factory Functions**: Create hooks with auto-initialization
- **11 Event Methods**: Cover all publishing activities

### 3. publish_article_with_analytics.py
- **Wrapper Script**: Auto-instruments publisher
- **Event Wrapping**: Intercepts all publishing calls
- **Report Generation**: Creates analytics summary

## Data Flow Diagram

### Publishing Flow
```
Article Created
    ↓
on_article_generated()
    ├→ MongoDB: articles collection
    └→ PostgreSQL: articles table
    ↓
Article Published to Blog
    ↓
on_github_published()
    ├→ MongoDB: platform_distributions
    └→ PostgreSQL: platform_distributions
    ↓
Distributed to Social (9 platforms)
    ↓
on_social_distribution_complete()
    ├→ Log for each: TWITTER, REDDIT, FACEBOOK, LINKEDIN, etc.
    └→ Status: success/failed/pending
    ↓
Monetized (Gumroad + Printify)
    ↓
on_ecommerce_distribution_complete()
    ├→ Gumroad ebook (log_channel_revenue: ebook, $4.99)
    └→ Printify POD (log_channel_revenue: pod_*, $5-20)
    ↓
Newsletter Sent
    ↓
on_newsletter_sent()
    └→ Log newsletter distribution
```

### Engagement Tracking Flow
```
User Clicks Article
    ↓
on_user_click()
    ├→ MongoDB: user_engagements
    └→ PostgreSQL: user_engagements
    ↓
User Purchases (Conversion)
    ↓
on_conversion()
    ├→ Log engagement with is_conversion=true
    └→ Log revenue in channel_revenue
    ↓
Social Engagement Updates
    ↓
on_social_engagement_update()
    ├→ MongoDB: social_engagement
    └→ PostgreSQL: social_engagement (upsert)
    ↓
Video Performance
    ↓
on_video_published()
    ├→ MongoDB: video_metrics
    └→ PostgreSQL: video_metrics
```

## Database Schema Overview

### MongoDB Collections (6)

| Collection | Purpose | Records per Article |
|---|---|---|
| articles | Article metadata | 1 |
| platform_distributions | Publishing events | 10-17 |
| user_engagements | User interactions | 10-100+ |
| channel_revenue | Revenue events | 1-5 |
| social_engagement | Social metrics | 10-17 |
| video_metrics | Video performance | 0-3 |

### PostgreSQL Tables (6)

| Table | Purpose | Keys |
|---|---|---|
| articles | Normalized article data | PK: article_id |
| platform_distributions | Distribution records | PK: distribution_id, FK: article_id |
| user_engagements | Engagement events | PK: engagement_id, FK: article_id |
| channel_revenue | Revenue tracking | PK: revenue_id, FK: article_id |
| social_engagement | Social metrics | PK: metric_id, FK: article_id |
| video_metrics | Video metrics | PK: video_id, FK: article_id |

## Supported Platforms (17 Total)

**Social Media (9):**
- Twitter, Reddit, Facebook, LinkedIn, Instagram, TikTok, Telegram, Mastodon, Bluesky

**Publishing Platforms (4):**
- Blog (GitHub Pages), Dev.to, Hashnode, Beehiiv

**E-Commerce (2):**
- Gumroad (ebooks), Printify (print-on-demand)

**Video (2):**
- YouTube, TikTok

## Tracking Metrics by Platform

### Blog
- Clicks: yes
- Conversions: yes
- Affiliate revenue: yes
- Social shares: no

### Social Media
- Platform distribution: yes
- Post engagement: likes, shares, comments, impressions
- Click-through: yes
- Conversions: yes (with UTM parameters)
- Revenue: affiliate revenue only

### E-Commerce
- Gumroad: ebook sales, price, product ID
- Printify: POD product sales, product type, price

### Video
- Views: yes
- Watch time: yes (minutes)
- Watch percentage: calculated
- Clicks: yes
- Shares: yes

## Event Types Tracked (8)

1. **LIKE** - Social like/favorite
2. **SHARE** - Social share/retweet
3. **COMMENT** - Social comment/reply
4. **RETWEET** - Retweet action
5. **SAVE** - Save/bookmark action
6. **CLICK** - Link click
7. **VIEW** - Page view/impression
8. **WATCH** - Video watch

## Revenue Channels (4)

1. **affiliate** - Affiliate link conversions
2. **ebook** - Gumroad e-book sales
3. **pod** - Print-on-demand product sales
4. **direct** - Direct sales/sponsorships

## Performance Characteristics

### Write Performance
- Single event: 1-5ms (to both databases)
- Bulk operations: batching recommended
- Network latency: included in timing

### Read Performance
- Single article: 5-20ms
- Aggregations: 50-200ms (depends on data volume)
- Range queries: 10-50ms (with indexes)

### Storage Efficiency
- Per-article: 1-60KB total
- Per-engagement: ~200 bytes
- Per-social-metric: ~500 bytes
- Per-video-metric: ~500 bytes

## Graceful Degradation

The system handles database failures gracefully:

```
Request to log event
    ↓
Try MongoDB
    ├→ Success: continue
    ├→ Failure: log warning, continue
    └→ Unavailable: skip, continue
    ↓
Try PostgreSQL
    ├→ Success: continue
    ├→ Failure: log warning, continue
    └→ Unavailable: skip, continue
    ↓
Return success if at least one DB wrote
```

## Environment Configuration

```
Application Environment Variables:
├─ MONGODB_URL
│  mongodb://user:password@host:27017/profitengine
│
└─ DATABASE_URL
   postgresql://user:password@localhost:5432/profitengine
```

## Security Architecture

```
Secrets Management:
├─ Development: .env file (gitignored)
├─ CI/CD: GitHub Secrets
└─ Production: Container Secrets

Connection Security:
├─ Parameterized queries (all databases)
├─ SSL/TLS support (recommended)
├─ Limited-privilege accounts (recommended)
└─ Firewall restrictions (recommended)

Data Security:
├─ No logging of sensitive data
├─ Encrypted connection strings
└─ Audit trail (optional)
```

## Scalability Path

### Current (Single Region)
- MongoDB: 1 cluster, 1 database
- PostgreSQL: 1 instance, 1 database
- Application: Single publisher instance

### Phase 1: HA
- MongoDB: Replica set (3 nodes)
- PostgreSQL: Read replicas
- Connection pooling: increase from 5 to 20

### Phase 2: Geo-Distribution
- MongoDB: Sharded clusters per region
- PostgreSQL: Distributed read replicas
- CDN for static content

### Phase 3: Real-Time
- Event streaming (Kafka/Pub-Sub)
- WebSocket dashboard
- Real-time aggregations

## Integration Patterns

### Pattern 1: Manual Hook Integration
```python
from lib.analytics_integration import create_analytics_hook
hook = create_analytics_hook()
article_id = hook.on_article_generated(article, topic)
hook.on_github_published(article_id, url)
report = hook.generate_analytics_report(article_id)
hook.close()
```

### Pattern 2: Direct Manager Usage
```python
from lib.analytics_tracker import AnalyticsTrackingManager
manager = AnalyticsTrackingManager()
article_id = manager.log_article_published(...)
manager.log_platform_distribution(...)
manager.close()
```

### Pattern 3: Automated (Wrapper Script)
```bash
python scripts/publish_article_with_analytics.py "Topic"
```

## Monitoring & Alerting

### Key Metrics to Monitor
1. Article publication rate
2. Platform distribution success rate
3. User engagement rate
4. Revenue per article
5. Database query latency
6. Connection pool utilization

### Alert Thresholds
- Publication success < 80%
- Query latency > 500ms
- Connection pool > 80% utilization
- Daily revenue < baseline - 30%

## Testing Coverage

- 5 data model tests
- 6 MongoDB tracker tests
- 6 PostgreSQL tracker tests
- 8 unified manager tests
- 2 enum validation tests
- 2 integration tests
- 3 data integrity tests

Total: 32 unit tests

## Deployment Checklist

- [ ] Install dependencies: `pip install pymongo psycopg2-binary`
- [ ] Set environment variables: `MONGODB_URL`, `DATABASE_URL`
- [ ] Create databases and collections/tables
- [ ] Run tests: `pytest tests/test_analytics_tracking.py`
- [ ] Test manual integration with hook
- [ ] Deploy analytics_tracker.py
- [ ] Deploy analytics_integration.py
- [ ] Deploy publish_article_with_analytics.py
- [ ] Monitor logs for errors
- [ ] Verify data in both databases

## File Sizes

- analytics_tracker.py: ~750 lines
- analytics_integration.py: ~400 lines
- publish_article_with_analytics.py: ~100 lines
- DATABASE_SCHEMA.md: ~500 lines
- ANALYTICS_README.md: ~600 lines
- QUICK_REFERENCE.md: ~200 lines
- SYSTEM_ARCHITECTURE.md: this file

**Total: 2,750+ lines of production code + documentation**

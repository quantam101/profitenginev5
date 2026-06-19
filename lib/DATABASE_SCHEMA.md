# ProfitEngine Analytics Database Schema

## Overview

The analytics tracking layer uses two complementary databases:

1. **MongoDB** - Document storage for flexible, event-based tracking
2. **PostgreSQL** - Relational database for structured analytics and reporting

Both databases are synchronized through the `AnalyticsTrackingManager` which logs events to both systems simultaneously.

## MongoDB Schema

### Collection: `articles`

Stores article metadata for every published article.

```javascript
{
  _id: ObjectId,
  article_id: UUID,           // Unique article identifier
  title: String,              // Article title
  topic: String,              // Article topic/category
  slug: String,               // URL-friendly slug
  publish_date: ISODate,      // ISO 8601 timestamp
  word_count: Number,         // Total word count
  tags: [String],             // Article tags/categories
  quality_score: Number,      // 0.0-1.0 quality score
  author: String,             // Author name
  category: String,           // Content category
  featured: Boolean,          // Featured article flag
  created_at: ISODate         // Record creation timestamp
}
```

**Indexes:**
- `article_id` (unique)
- `publish_date` (descending)
- `topic`
- `slug`

### Collection: `platform_distributions`

Tracks article distribution to each platform.

```javascript
{
  _id: ObjectId,
  distribution_id: UUID,      // Unique distribution record ID
  article_id: UUID,           // References articles.article_id
  platform: String,           // Platform name (twitter, reddit, etc.)
  published_at: ISODate,      // When distributed to platform
  url: String,                // Platform post/content URL
  status: String,             // "pending", "success", "failed", "skipped"
  error_message: String,      // Error details if failed
  metadata: Object,           // Platform-specific metadata
  created_at: ISODate         // Record creation timestamp
}
```

**Indexes:**
- `article_id`
- `platform`
- `published_at` (descending)

### Collection: `user_engagements`

Tracks individual user interactions with article content.

```javascript
{
  _id: ObjectId,
  engagement_id: UUID,        // Unique engagement record ID
  article_id: UUID,           // References articles.article_id
  platform: String,           // Platform where engagement occurred
  engagement_type: String,    // "like", "share", "comment", "click", "view", etc.
  user_id: String,            // Optional anonymous/platform user ID
  user_country: String,       // 2-letter country code
  user_device: String,        // Device type (mobile, desktop, tablet)
  click_source: String,       // "social", "search", "direct", "affiliate"
  is_conversion: Boolean,     // Whether engagement led to conversion
  conversion_value_usd: Number, // Conversion value in USD
  created_at: ISODate         // Event timestamp
}
```

**Indexes:**
- `article_id`
- `platform`
- `engagement_type`
- `created_at` (descending)

### Collection: `channel_revenue`

Tracks revenue generated from each article per platform/channel.

```javascript
{
  _id: ObjectId,
  revenue_id: UUID,           // Unique revenue record ID
  article_id: UUID,           // References articles.article_id
  platform: String,           // Platform generating revenue
  channel: String,            // Channel type (affiliate, ebook, pod, direct)
  revenue_usd: Number,        // Revenue amount in USD
  currency: String,           // Currency code (default: USD)
  transaction_count: Number,  // Number of transactions
  metadata: Object,           // Additional transaction data
  created_at: ISODate         // Record creation timestamp
}
```

**Indexes:**
- `article_id`
- `platform`
- `channel`

### Collection: `social_engagement`

Tracks aggregated social media metrics per post.

```javascript
{
  _id: ObjectId,
  metric_id: UUID,            // Unique metric record ID
  article_id: UUID,           // References articles.article_id
  platform: String,           // Platform (twitter, reddit, etc.)
  post_id: String,            // Platform-specific post ID
  likes: Number,              // Like count
  shares: Number,             // Share count
  comments: Number,           // Comment count
  saves: Number,              // Save count
  impressions: Number,        // Impression count
  reach: Number,              // Total reach
  engagement_rate: Number,    // Calculated engagement %
  created_at: ISODate,        // Record creation timestamp
  updated_at: ISODate         // Last update timestamp
}
```

**Indexes:**
- `article_id`
- `platform`
- `post_id`

### Collection: `video_metrics`

Tracks video performance metrics.

```javascript
{
  _id: ObjectId,
  video_id: UUID,             // Unique video identifier
  article_id: UUID,           // References articles.article_id
  platform: String,           // Platform (youtube, tiktok, etc.)
  video_title: String,        // Video title
  views: Number,              // View count
  watch_time_minutes: Number, // Total watch time in minutes
  watch_time_percentage: Number, // Average watch time %
  clicks: Number,             // Click count (CTR)
  shares: Number,             // Share count
  created_at: ISODate,        // Record creation timestamp
  updated_at: ISODate         // Last update timestamp
}
```

**Indexes:**
- `article_id`
- `platform`
- `video_id`

## PostgreSQL Schema

### Table: `articles`

Normalized article metadata.

```sql
CREATE TABLE articles (
    article_id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    publish_date TIMESTAMP NOT NULL,
    word_count INTEGER NOT NULL,
    tags TEXT[] DEFAULT '{}',
    quality_score FLOAT,
    author VARCHAR(255) DEFAULT 'Already Here LLC',
    category VARCHAR(100) DEFAULT 'automation',
    featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_articles_publish_date ON articles(publish_date DESC);
CREATE INDEX idx_articles_topic ON articles(topic);
```

### Table: `platform_distributions`

Article distribution records with foreign key to articles.

```sql
CREATE TABLE platform_distributions (
    distribution_id VARCHAR(255) PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
    platform VARCHAR(50) NOT NULL,
    published_at TIMESTAMP NOT NULL,
    url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_distributions_article ON platform_distributions(article_id);
CREATE INDEX idx_distributions_platform ON platform_distributions(platform);
```

### Table: `user_engagements`

User interaction tracking with denormalized article reference.

```sql
CREATE TABLE user_engagements (
    engagement_id VARCHAR(255) PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
    platform VARCHAR(50) NOT NULL,
    engagement_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    user_country VARCHAR(2),
    user_device VARCHAR(50),
    click_source VARCHAR(50),
    is_conversion BOOLEAN DEFAULT FALSE,
    conversion_value_usd FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_engagements_article ON user_engagements(article_id);
CREATE INDEX idx_engagements_conversions ON user_engagements(is_conversion, conversion_value_usd);
```

### Table: `channel_revenue`

Revenue tracking per article and channel.

```sql
CREATE TABLE channel_revenue (
    revenue_id VARCHAR(255) PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
    platform VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    revenue_usd FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_count INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_revenue_article ON channel_revenue(article_id);
CREATE INDEX idx_revenue_platform ON channel_revenue(platform);
```

### Table: `social_engagement`

Aggregated social media metrics.

```sql
CREATE TABLE social_engagement (
    metric_id VARCHAR(255) PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    engagement_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_social_article ON social_engagement(article_id);
CREATE INDEX idx_social_engagement_rate ON social_engagement(engagement_rate DESC);
```

### Table: `video_metrics`

Video performance metrics.

```sql
CREATE TABLE video_metrics (
    video_id VARCHAR(255) PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
    platform VARCHAR(50) NOT NULL,
    video_title TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    watch_time_minutes FLOAT DEFAULT 0,
    watch_time_percentage FLOAT,
    clicks INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_video_article ON video_metrics(article_id);
CREATE INDEX idx_video_views ON video_metrics(views DESC);
```

## Common Queries

### MongoDB

#### Get article analytics summary
```javascript
db.articles.findOne({article_id: "..."})
db.platform_distributions.find({article_id: "..."})
db.user_engagements.find({article_id: "..."})
db.channel_revenue.aggregate([
  {$match: {article_id: "..."}},
  {$group: {_id: "$platform", total_revenue: {$sum: "$revenue_usd"}}}
])
```

#### Top performing articles
```javascript
db.articles.aggregate([
  {$lookup: {
    from: "channel_revenue",
    localField: "article_id",
    foreignField: "article_id",
    as: "revenue"
  }},
  {$addFields: {total_revenue: {$sum: "$revenue.revenue_usd"}}},
  {$sort: {total_revenue: -1}},
  {$limit: 10}
])
```

### PostgreSQL

#### Platform performance report
```sql
SELECT
    p.platform,
    p.status,
    COUNT(*) as total_articles,
    COUNT(DISTINCT p.article_id) as unique_articles,
    SUM(CASE WHEN p.status = 'success' THEN 1 ELSE 0 END) as successful,
    ROUND(AVG(CASE WHEN cr.revenue_usd IS NOT NULL THEN cr.revenue_usd ELSE 0 END), 2) as avg_revenue
FROM platform_distributions p
LEFT JOIN channel_revenue cr ON p.article_id = cr.article_id AND p.platform = cr.platform
GROUP BY p.platform, p.status
ORDER BY total_articles DESC;
```

#### Revenue by article
```sql
SELECT
    a.title,
    a.publish_date,
    SUM(cr.revenue_usd) as total_revenue,
    COUNT(DISTINCT cr.platform) as platforms,
    COUNT(DISTINCT CASE WHEN ue.is_conversion THEN ue.engagement_id END) as conversions
FROM articles a
LEFT JOIN channel_revenue cr ON a.article_id = cr.article_id
LEFT JOIN user_engagements ue ON a.article_id = ue.article_id
GROUP BY a.article_id, a.title, a.publish_date
ORDER BY total_revenue DESC;
```

#### Social engagement trends
```sql
SELECT
    DATE(se.created_at) as date,
    SUM(se.likes) as total_likes,
    SUM(se.shares) as total_shares,
    SUM(se.comments) as total_comments,
    AVG(se.engagement_rate) as avg_engagement_rate,
    COUNT(DISTINCT se.metric_id) as posts
FROM social_engagement se
WHERE se.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(se.created_at)
ORDER BY date DESC;
```

## Environment Configuration

### Required Environment Variables

```bash
# MongoDB connection
export MONGODB_URL="mongodb://user:password@host:port/database"

# PostgreSQL connection
export DATABASE_URL="postgresql://user:password@host:5432/profitengine"
```

### Connection Pooling

- **MongoDB**: Single client connection (auto-reconnect enabled)
- **PostgreSQL**: Connection pool (default 5 connections, configurable)

## Data Retention & Archival

### Recommended Retention Policies

- **Articles**: Keep indefinitely
- **Platform Distributions**: Keep 2 years
- **User Engagements**: Keep 1 year (aggregate older data)
- **Channel Revenue**: Keep indefinitely
- **Social Engagement**: Keep 1 year (archive historical metrics)
- **Video Metrics**: Keep 1 year (archive older metrics)

### Archival Example

```sql
-- Archive old engagement records to separate table
CREATE TABLE user_engagements_archive AS
SELECT * FROM user_engagements
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM user_engagements
WHERE created_at < NOW() - INTERVAL '1 year';
```

## Performance Considerations

### MongoDB Optimizations

- Ensure indexes are created before bulk inserts
- Use write acknowledgment level `1` for distributed writes
- Enable compression for large documents

### PostgreSQL Optimizations

- Use connection pooling (recommended: 5-20 connections)
- Set `shared_buffers = 25% of RAM`
- Enable `log_min_duration_statement = 1000` for slow query logging
- Regular `ANALYZE` and `VACUUM` maintenance

### Query Performance Tips

1. Always filter by `article_id` first
2. Use date range filters to narrow result sets
3. Archive data older than 1 year
4. Use aggregation pipelines (MongoDB) or GROUP BY (PostgreSQL)
5. Pre-calculate common metrics

## Backup & Recovery

### MongoDB Backup

```bash
mongodump --uri="mongodb://..." --out=./backup_$(date +%Y%m%d)
```

### PostgreSQL Backup

```bash
pg_dump --clean --verbose postgresql://user:password@host/profitengine > backup_$(date +%Y%m%d).sql
```

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Publication Success Rate**: % of platform_distributions with status='success'
2. **Revenue Per Article**: SUM(revenue_usd) / COUNT(articles)
3. **Engagement Rate**: SUM(engagement events) / SUM(impressions)
4. **Video Performance**: Views and watch time trends
5. **Database Query Performance**: Average response time

### Alert Thresholds

- Publication success rate < 80%
- Average daily engagements < baseline - 30%
- Database connection pool at >80% capacity
- Query response time > 5 seconds

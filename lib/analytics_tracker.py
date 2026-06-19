"""
MongoDB & PostgreSQL Analytics Tracking Layer for ProfitEngine Content.

Tracks:
- Article metadata (title, topic, publish date, quality score)
- Platform distribution (which platforms got which articles)
- User clicks and conversions per article
- Revenue per article per channel
- Social media engagement (likes, shares, comments)
- Video view counts and watch time
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, OperationFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor
    from psycopg2.pool import SimpleConnectionPool
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


class PublishPlatform(str, Enum):
    """Publishing platforms."""
    BLOG = "blog"
    TWITTER = "twitter"
    REDDIT = "reddit"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"
    MASTODON = "mastodon"
    BLUESKY = "bluesky"
    YOUTUBE = "youtube"
    NEWSLETTER = "newsletter"
    DEVTO = "devto"
    HASHNODE = "hashnode"
    BEEHIIV = "beehiiv"
    GUMROAD = "gumroad"
    PRINTIFY = "printify"


class EngagementType(str, Enum):
    """Social media engagement types."""
    LIKE = "like"
    SHARE = "share"
    COMMENT = "comment"
    RETWEET = "retweet"
    SAVE = "save"
    CLICK = "click"
    VIEW = "view"
    WATCH = "watch"


@dataclass
class ArticleMetadata:
    """Article metadata for tracking."""
    article_id: str
    title: str
    topic: str
    slug: str
    publish_date: str
    word_count: int
    tags: List[str]
    quality_score: Optional[float] = None
    author: str = "Already Here LLC"
    category: str = "automation"
    featured: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class PlatformDistribution:
    """Track which platforms received which articles."""
    distribution_id: str
    article_id: str
    platform: PublishPlatform
    published_at: str
    url: str
    status: str  # "pending", "success", "failed", "skipped"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserEngagement:
    """Track user clicks and conversions."""
    engagement_id: str
    article_id: str
    platform: PublishPlatform
    engagement_type: EngagementType
    user_id: Optional[str] = None
    user_country: Optional[str] = None
    user_device: Optional[str] = None
    click_source: Optional[str] = None  # "social", "search", "direct", "affiliate"
    is_conversion: bool = False
    conversion_value_usd: Optional[float] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ChannelRevenue:
    """Track revenue per article per channel."""
    revenue_id: str
    article_id: str
    platform: PublishPlatform
    channel: str  # "affiliate", "ebook", "pod", "direct"
    revenue_usd: float
    currency: str = "USD"
    transaction_count: int = 1
    created_at: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
@dataclass
class SocialEngagement:
    """Track social media engagement metrics."""
    metric_id: str
    article_id: str
    platform: PublishPlatform
    post_id: str
    likes: int = 0
    shares: int = 0
    comments: int = 0
    saves: int = 0
    impressions: int = 0
    reach: int = 0
    engagement_rate: Optional[float] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()
        # Calculate engagement rate if not provided and we have impressions
        if self.engagement_rate is None and self.impressions > 0:
            total_engagements = self.likes + self.shares + self.comments + self.saves
            self.engagement_rate = (total_engagements / self.impressions) * 100


@dataclass
class VideoMetrics:
    """Track video view counts and watch time."""
    video_id: str
    article_id: str
    platform: PublishPlatform  # "youtube", "tiktok", "instagram", "twitter"
    video_title: str
    views: int = 0
    watch_time_minutes: float = 0.0
    watch_time_percentage: Optional[float] = None
    clicks: int = 0
    shares: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()
        # Calculate watch time percentage if not provided and we have views
        if self.watch_time_percentage is None and self.views > 0:
            percentage = (self.watch_time_minutes / self.views) * 100
            self.watch_time_percentage = min(percentage, 100.0)  # Cap at 100%


class MongoAnalyticsTracker:
    """MongoDB tracker for article analytics."""

    def __init__(self, mongodb_url: str) -> None:
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo is not installed. Install with: pip install pymongo")

        self.mongodb_url = mongodb_url
        self.client: Optional[Any] = None
        self.db: Optional[Any] = None
        self._connect()

    def _connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client["profitengine"]
            self._init_collections()
            print("[MONGO] Connected successfully")
        except ConnectionFailure as e:
            print(f"[MONGO][ERROR] Connection failed: {e}")
            raise

    def _init_collections(self) -> None:
        """Initialize MongoDB collections and indexes."""
        if not self.db:
            return

        collections = {
            "articles": [
                ("article_id", ASCENDING),
                ("publish_date", DESCENDING),
                ("topic", ASCENDING),
                ("slug", ASCENDING),
            ],
            "platform_distributions": [
                ("article_id", ASCENDING),
                ("platform", ASCENDING),
                ("published_at", DESCENDING),
            ],
            "user_engagements": [
                ("article_id", ASCENDING),
                ("platform", ASCENDING),
                ("engagement_type", ASCENDING),
                ("created_at", DESCENDING),
            ],
            "channel_revenue": [
                ("article_id", ASCENDING),
                ("platform", ASCENDING),
                ("channel", ASCENDING),
            ],
            "social_engagement": [
                ("article_id", ASCENDING),
                ("platform", ASCENDING),
                ("post_id", ASCENDING),
            ],
            "video_metrics": [
                ("article_id", ASCENDING),
                ("platform", ASCENDING),
                ("video_id", ASCENDING),
            ],
        }

        for collection_name, indexes in collections.items():
            collection = self.db[collection_name]
            for field, direction in indexes:
                collection.create_index([(field, direction)])

    def log_article(self, metadata: ArticleMetadata) -> bool:
        """Log article metadata."""
        if not self.db:
            return False
        try:
            self.db.articles.insert_one(asdict(metadata))
            return True
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to log article: {e}")
            return False

    def log_distribution(self, distribution: PlatformDistribution) -> bool:
        """Log platform distribution."""
        if not self.db:
            return False
        try:
            self.db.platform_distributions.insert_one(asdict(distribution))
            return True
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to log distribution: {e}")
            return False

    def log_engagement(self, engagement: UserEngagement) -> bool:
        """Log user engagement."""
        if not self.db:
            return False
        try:
            self.db.user_engagements.insert_one(asdict(engagement))
            return True
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to log engagement: {e}")
            return False

    def log_revenue(self, revenue: ChannelRevenue) -> bool:
        """Log channel revenue."""
        if not self.db:
            return False
        try:
            self.db.channel_revenue.insert_one(asdict(revenue))
            return True
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to log revenue: {e}")
            return False

    def log_social_engagement(self, social: SocialEngagement) -> bool:
        """Log social media engagement."""
        if not self.db:
            return False
        try:
            self.db.social_engagement.insert_one(asdict(social))
            return True
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to log social engagement: {e}")
            return False

    def log_video_metrics(self, video: VideoMetrics) -> bool:
        """Log video metrics."""
        if not self.db:
            return False
        try:
            self.db.video_metrics.insert_one(asdict(video))
            return True
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to log video metrics: {e}")
            return False

    def get_article_analytics(self, article_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for an article."""
        if not self.db:
            return {}
        try:
            article = self.db.articles.find_one({"article_id": article_id})
            distributions = list(self.db.platform_distributions.find({"article_id": article_id}))
            engagements = list(self.db.user_engagements.find({"article_id": article_id}))
            revenue = list(self.db.channel_revenue.find({"article_id": article_id}))
            social = list(self.db.social_engagement.find({"article_id": article_id}))
            videos = list(self.db.video_metrics.find({"article_id": article_id}))

            return {
                "article": article,
                "distributions": distributions,
                "engagements": engagements,
                "revenue": revenue,
                "social_engagement": social,
                "video_metrics": videos,
                "totals": {
                    "platforms": len(distributions),
                    "engagements": len(engagements),
                    "total_revenue": sum(r.get("revenue_usd", 0) for r in revenue),
                    "total_social_likes": sum(s.get("likes", 0) for s in social),
                    "total_video_views": sum(v.get("views", 0) for v in videos),
                },
            }
        except Exception as e:
            print(f"[MONGO][ERROR] Failed to get analytics: {e}")
            return {}

    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()


class PostgreSQLAnalyticsTracker:
    """PostgreSQL tracker for relational analytics data."""

    def __init__(self, database_url: str, pool_size: int = 5) -> None:
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("psycopg2 is not installed. Install with: pip install psycopg2-binary")

        self.database_url = database_url
        self.pool: Optional[Any] = None
        self._connect(pool_size)

    def _connect(self, pool_size: int) -> None:
        """Connect to PostgreSQL."""
        try:
            self.pool = SimpleConnectionPool(1, pool_size, self.database_url)
            self._init_tables()
            print("[POSTGRES] Connected successfully")
        except psycopg2.Error as e:
            print(f"[POSTGRES][ERROR] Connection failed: {e}")
            raise

    def _get_connection(self):
        """Get connection from pool."""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        return self.pool.getconn()

    def _release_connection(self, conn) -> None:
        """Release connection back to pool."""
        if self.pool:
            self.pool.putconn(conn)

    def _init_tables(self) -> None:
        """Initialize PostgreSQL tables."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Articles table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
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
                    )
                """)

                # Platform distributions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS platform_distributions (
                        distribution_id VARCHAR(255) PRIMARY KEY,
                        article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
                        platform VARCHAR(50) NOT NULL,
                        published_at TIMESTAMP NOT NULL,
                        url TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        error_message TEXT,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # User engagements table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_engagements (
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
                    )
                """)

                # Channel revenue table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS channel_revenue (
                        revenue_id VARCHAR(255) PRIMARY KEY,
                        article_id VARCHAR(255) NOT NULL REFERENCES articles(article_id),
                        platform VARCHAR(50) NOT NULL,
                        channel VARCHAR(50) NOT NULL,
                        revenue_usd FLOAT NOT NULL,
                        currency VARCHAR(3) DEFAULT 'USD',
                        transaction_count INTEGER DEFAULT 1,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Social engagement table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS social_engagement (
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
                    )
                """)

                # Video metrics table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS video_metrics (
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
                    )
                """)

                # Create indexes
                cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_publish_date ON articles(publish_date DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_distributions_article ON platform_distributions(article_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_distributions_platform ON platform_distributions(platform)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_engagements_article ON user_engagements(article_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_revenue_article ON channel_revenue(article_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_social_article ON social_engagement(article_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_video_article ON video_metrics(article_id)")

                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Table initialization failed: {e}")
        finally:
            self._release_connection(conn)

    def log_article(self, metadata: ArticleMetadata) -> bool:
        """Log article metadata."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO articles
                    (article_id, title, topic, slug, publish_date, word_count, tags, quality_score, author, category, featured, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (article_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        quality_score = EXCLUDED.quality_score
                """, (
                    metadata.article_id, metadata.title, metadata.topic, metadata.slug,
                    metadata.publish_date, metadata.word_count, metadata.tags,
                    metadata.quality_score, metadata.author, metadata.category,
                    metadata.featured, metadata.created_at
                ))
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Failed to log article: {e}")
            return False
        finally:
            self._release_connection(conn)

    def log_distribution(self, distribution: PlatformDistribution) -> bool:
        """Log platform distribution."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO platform_distributions
                    (distribution_id, article_id, platform, published_at, url, status, error_message, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    distribution.distribution_id, distribution.article_id,
                    distribution.platform.value, distribution.published_at,
                    distribution.url, distribution.status,
                    distribution.error_message, Json(distribution.metadata or {}),
                    distribution.created_at
                ))
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Failed to log distribution: {e}")
            return False
        finally:
            self._release_connection(conn)

    def log_engagement(self, engagement: UserEngagement) -> bool:
        """Log user engagement."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_engagements
                    (engagement_id, article_id, platform, engagement_type, user_id, user_country, user_device, click_source, is_conversion, conversion_value_usd, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    engagement.engagement_id, engagement.article_id,
                    engagement.platform.value, engagement.engagement_type.value,
                    engagement.user_id, engagement.user_country,
                    engagement.user_device, engagement.click_source,
                    engagement.is_conversion, engagement.conversion_value_usd,
                    engagement.created_at
                ))
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Failed to log engagement: {e}")
            return False
        finally:
            self._release_connection(conn)

    def log_revenue(self, revenue: ChannelRevenue) -> bool:
        """Log channel revenue."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO channel_revenue
                    (revenue_id, article_id, platform, channel, revenue_usd, currency, transaction_count, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    revenue.revenue_id, revenue.article_id,
                    revenue.platform.value, revenue.channel,
                    revenue.revenue_usd, revenue.currency,
                    revenue.transaction_count, Json(revenue.metadata or {}),
                    revenue.created_at
                ))
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Failed to log revenue: {e}")
            return False
        finally:
            self._release_connection(conn)

    def log_social_engagement(self, social: SocialEngagement) -> bool:
        """Log social media engagement."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO social_engagement
                    (metric_id, article_id, platform, post_id, likes, shares, comments, saves, impressions, reach, engagement_rate, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (metric_id) DO UPDATE SET
                        likes = EXCLUDED.likes,
                        shares = EXCLUDED.shares,
                        comments = EXCLUDED.comments,
                        saves = EXCLUDED.saves,
                        impressions = EXCLUDED.impressions,
                        reach = EXCLUDED.reach,
                        engagement_rate = EXCLUDED.engagement_rate,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    social.metric_id, social.article_id,
                    social.platform.value, social.post_id,
                    social.likes, social.shares, social.comments,
                    social.saves, social.impressions, social.reach,
                    social.engagement_rate, social.created_at, social.updated_at
                ))
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Failed to log social engagement: {e}")
            return False
        finally:
            self._release_connection(conn)

    def log_video_metrics(self, video: VideoMetrics) -> bool:
        """Log video metrics."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO video_metrics
                    (video_id, article_id, platform, video_title, views, watch_time_minutes, watch_time_percentage, clicks, shares, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (video_id) DO UPDATE SET
                        views = EXCLUDED.views,
                        watch_time_minutes = EXCLUDED.watch_time_minutes,
                        watch_time_percentage = EXCLUDED.watch_time_percentage,
                        clicks = EXCLUDED.clicks,
                        shares = EXCLUDED.shares,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    video.video_id, video.article_id,
                    video.platform.value, video.video_title,
                    video.views, video.watch_time_minutes,
                    video.watch_time_percentage, video.clicks,
                    video.shares, video.created_at, video.updated_at
                ))
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"[POSTGRES][ERROR] Failed to log video metrics: {e}")
            return False
        finally:
            self._release_connection(conn)

    def get_article_revenue_summary(self, article_id: str) -> Dict[str, Any]:
        """Get revenue summary for an article."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        platform,
                        channel,
                        SUM(revenue_usd) as total_revenue,
                        COUNT(*) as transaction_count,
                        AVG(revenue_usd) as avg_transaction
                    FROM channel_revenue
                    WHERE article_id = %s
                    GROUP BY platform, channel
                    ORDER BY total_revenue DESC
                """, (article_id,))
                results = cur.fetchall()
                return {row['platform']: {
                    'channels': [dict(r) for r in results if r['platform'] == row['platform']]
                } for row in results}
        except psycopg2.Error as e:
            print(f"[POSTGRES][ERROR] Failed to get revenue summary: {e}")
            return {}
        finally:
            self._release_connection(conn)

    def get_platform_performance(self, article_id: str) -> Dict[str, Any]:
        """Get performance metrics by platform."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        p.platform,
                        p.status,
                        p.published_at,
                        p.url,
                        COUNT(DISTINCT ue.engagement_id) as total_engagements,
                        COUNT(DISTINCT CASE WHEN ue.is_conversion THEN ue.engagement_id END) as conversions,
                        SUM(cr.revenue_usd) as total_revenue,
                        COUNT(DISTINCT se.metric_id) as social_posts
                    FROM platform_distributions p
                    LEFT JOIN user_engagements ue ON p.article_id = ue.article_id AND p.platform = ue.platform
                    LEFT JOIN channel_revenue cr ON p.article_id = cr.article_id AND p.platform = cr.platform
                    LEFT JOIN social_engagement se ON p.article_id = se.article_id AND p.platform = se.platform
                    WHERE p.article_id = %s
                    GROUP BY p.platform, p.status, p.published_at, p.url
                    ORDER BY total_revenue DESC NULLS LAST
                """, (article_id,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"[POSTGRES][ERROR] Failed to get platform performance: {e}")
            return []
        finally:
            self._release_connection(conn)

    def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            self.pool.closeall()


class AnalyticsTrackingManager:
    """Unified manager for both MongoDB and PostgreSQL tracking."""

    def __init__(
        self,
        mongodb_url: Optional[str] = None,
        postgresql_url: Optional[str] = None,
    ) -> None:
        """Initialize trackers with environment URLs if not provided."""
        if mongodb_url is None:
            mongodb_url = os.getenv("MONGODB_URL", "")
        if postgresql_url is None:
            postgresql_url = os.getenv("DATABASE_URL", "")

        self.mongo: Optional[MongoAnalyticsTracker] = None
        self.postgres: Optional[PostgreSQLAnalyticsTracker] = None

        if mongodb_url:
            try:
                self.mongo = MongoAnalyticsTracker(mongodb_url)
            except Exception as e:
                print(f"[TRACKER] MongoDB initialization failed: {e}")

        if postgresql_url:
            try:
                self.postgres = PostgreSQLAnalyticsTracker(postgresql_url)
            except Exception as e:
                print(f"[TRACKER] PostgreSQL initialization failed: {e}")

    def log_article_published(
        self,
        title: str,
        topic: str,
        slug: str,
        word_count: int,
        tags: List[str],
        quality_score: Optional[float] = None,
    ) -> str:
        """Log a published article to both databases."""
        article_id = str(uuid4())
        publish_date = datetime.now(timezone.utc).isoformat()

        metadata = ArticleMetadata(
            article_id=article_id,
            title=title,
            topic=topic,
            slug=slug,
            publish_date=publish_date,
            word_count=word_count,
            tags=tags,
            quality_score=quality_score,
        )

        if self.mongo:
            self.mongo.log_article(metadata)
        if self.postgres:
            self.postgres.log_article(metadata)

        return article_id

    def log_platform_distribution(
        self,
        article_id: str,
        platform: PublishPlatform,
        url: str,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log platform distribution event."""
        distribution = PlatformDistribution(
            distribution_id=str(uuid4()),
            article_id=article_id,
            platform=platform,
            published_at=datetime.now(timezone.utc).isoformat(),
            url=url,
            status=status,
            error_message=error_message,
            metadata=metadata,
        )

        success = True
        if self.mongo:
            success &= self.mongo.log_distribution(distribution)
        if self.postgres:
            success &= self.postgres.log_distribution(distribution)

        return success

    def log_user_engagement(
        self,
        article_id: str,
        platform: PublishPlatform,
        engagement_type: EngagementType,
        is_conversion: bool = False,
        conversion_value_usd: Optional[float] = None,
        **kwargs
    ) -> bool:
        """Log user engagement event."""
        engagement = UserEngagement(
            engagement_id=str(uuid4()),
            article_id=article_id,
            platform=platform,
            engagement_type=engagement_type,
            is_conversion=is_conversion,
            conversion_value_usd=conversion_value_usd,
            **kwargs
        )

        success = True
        if self.mongo:
            success &= self.mongo.log_engagement(engagement)
        if self.postgres:
            success &= self.postgres.log_engagement(engagement)

        return success

    def log_channel_revenue(
        self,
        article_id: str,
        platform: PublishPlatform,
        channel: str,
        revenue_usd: float,
        transaction_count: int = 1,
    ) -> bool:
        """Log channel revenue."""
        revenue = ChannelRevenue(
            revenue_id=str(uuid4()),
            article_id=article_id,
            platform=platform,
            channel=channel,
            revenue_usd=revenue_usd,
            transaction_count=transaction_count,
        )

        success = True
        if self.mongo:
            success &= self.mongo.log_revenue(revenue)
        if self.postgres:
            success &= self.postgres.log_revenue(revenue)

        return success

    def log_social_metrics(
        self,
        article_id: str,
        platform: PublishPlatform,
        post_id: str,
        likes: int = 0,
        shares: int = 0,
        comments: int = 0,
        saves: int = 0,
        impressions: int = 0,
        reach: int = 0,
    ) -> bool:
        """Log social media engagement metrics."""
        engagement_rate = None
        if impressions > 0:
            total_engagement = likes + shares + comments + saves
            engagement_rate = (total_engagement / impressions) * 100

        social = SocialEngagement(
            metric_id=str(uuid4()),
            article_id=article_id,
            platform=platform,
            post_id=post_id,
            likes=likes,
            shares=shares,
            comments=comments,
            saves=saves,
            impressions=impressions,
            reach=reach,
            engagement_rate=engagement_rate,
        )

        success = True
        if self.mongo:
            success &= self.mongo.log_social_engagement(social)
        if self.postgres:
            success &= self.postgres.log_social_engagement(social)

        return success

    def log_video_metrics(
        self,
        article_id: str,
        platform: PublishPlatform,
        video_id: str,
        video_title: str,
        views: int = 0,
        watch_time_minutes: float = 0.0,
        clicks: int = 0,
        shares: int = 0,
    ) -> bool:
        """Log video metrics."""
        watch_time_percentage = None
        if views > 0 and watch_time_minutes > 0:
            watch_time_percentage = min(100, (watch_time_minutes / 10) * 100)

        video = VideoMetrics(
            video_id=video_id,
            article_id=article_id,
            platform=platform,
            video_title=video_title,
            views=views,
            watch_time_minutes=watch_time_minutes,
            watch_time_percentage=watch_time_percentage,
            clicks=clicks,
            shares=shares,
        )

        success = True
        if self.mongo:
            success &= self.mongo.log_video_metrics(video)
        if self.postgres:
            success &= self.postgres.log_video_metrics(video)

        return success

    def get_analytics_summary(self, article_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics summary for an article."""
        summary = {
            "article_id": article_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mongodb": {},
            "postgresql": {},
        }

        if self.mongo:
            summary["mongodb"] = self.mongo.get_article_analytics(article_id)

        if self.postgres:
            summary["postgresql"] = {
                "revenue_summary": self.postgres.get_article_revenue_summary(article_id),
                "platform_performance": self.postgres.get_platform_performance(article_id),
            }

        return summary

    def close(self) -> None:
        """Close all database connections."""
        if self.mongo:
            self.mongo.close()
        if self.postgres:
            self.postgres.close()

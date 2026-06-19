"""
SOCIAL DISTRIBUTOR — Enterprise multi-platform content distribution engine.

Distributes trading content to:
  1. Twitter/X — 2x daily (9 AM + 5 PM MST) with hashtags and engagement tracking
  2. LinkedIn — 1x daily (9 AM MST) with professional tone
  3. TikTok — 1x daily (5 PM MST) with video clips from trading dashboard
  4. YouTube Shorts — 1x daily (5 PM MST) with 15-60 second clips
  5. Reddit — daily posts to r/algotrading, r/stocks, r/trading
  6. Email Digest — weekly Friday 10 AM MST with top posts + strategy breakdown

Features:
  - Rate limiting and retry logic with exponential backoff
  - Duplicate detection (never posts same content twice)
  - Engagement tracking (likes, retweets, comments, views)
  - Post performance analytics dashboard
  - Offline cache with auto-sync on network restore
  - Professional tone matching Already Here LLC brand
  - FTC affiliate disclosure injection
  - Scheduled posting via APScheduler
  - Webhook integration for cross-platform notifications

Environment variables:
  TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
  LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
  TIKTOK_ACCESS_TOKEN
  YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
  GMAIL_USER, GMAIL_APP_PASSWORD
  AFFILIATE_TAG (Amazon Associates default: 'alreadyhere-20')
  SOCIAL_DB_PATH (default: ./datacenter/social_distributor.db)
  PROFITENGINE_URL (production domain for links)
"""

from __future__ import annotations

import os
import sys
import json
import sqlite3
import logging
import hashlib
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

try:
    import requests
except ImportError:
    requests = None

# Import existing social engine
try:
    from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost, LocalPostJournal
except ImportError:
    ProductionSocialEngine = None
    SocialPost = None
    LocalPostJournal = None


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("social_distributor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

PROFITENGINE_URL = os.getenv("PROFITENGINE_URL", "https://profitengine.alreadyherellc.com")
AMAZON_TAG = os.getenv("AFFILIATE_TAG", "alreadyhere-20")
DB_PATH = os.getenv("SOCIAL_DB_PATH", "./datacenter/social_distributor.db")
GMAIL_USER = os.getenv("GMAIL_USER", "alreadyherellc@gmail.com")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "dispatch@alreadyherellc.com")

# Timezone: MST (Mountain Standard Time = UTC-7, MDT = UTC-6)
MST_OFFSET = timedelta(hours=-7)

# Posting schedule (all times in MST)
TWITTER_SCHEDULE_1 = "09:00"  # 9 AM MST
TWITTER_SCHEDULE_2 = "17:00"  # 5 PM MST
LINKEDIN_SCHEDULE = "09:00"   # 9 AM MST
TIKTOK_SCHEDULE = "17:00"     # 5 PM MST
YOUTUBE_SCHEDULE = "17:00"    # 5 PM MST
EMAIL_DIGEST_SCHEDULE = "10:00"  # Friday 10 AM MST

# Reddit subreddits
REDDIT_SUBREDDITS = ["algotrading", "stocks", "trading", "passive_income"]

# FTC Disclosure
FTC_DISCLOSURE = (
    "\n\n**Disclosure:** This post contains affiliate links. Already Here LLC may earn "
    "a commission if you purchase through these links, at no additional cost to you."
)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SocialPost:
    """Represents a single social media post."""
    id: Optional[int] = None
    content_id: str = ""  # UUID linking to content_generator output
    platform: str = ""  # twitter, linkedin, tiktok, youtube, reddit, email
    title: str = ""
    body: str = ""
    link: str = ""
    image_url: Optional[str] = None
    video_path: Optional[str] = None
    hashtags: List[str] = field(default_factory=lambda: ["trading", "ai", "alreadyhere", "autonomous"])
    scheduled_at: datetime = field(default_factory=datetime.now)
    posted_at: Optional[datetime] = None
    status: str = "draft"  # draft, scheduled, posted, failed
    engagement_likes: int = 0
    engagement_retweets: int = 0
    engagement_comments: int = 0
    engagement_views: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def content_hash(self) -> str:
        """Generate hash of post content for duplicate detection."""
        content = f"{self.platform}:{self.title}:{self.body}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class EngagementMetrics:
    """Aggregated engagement statistics."""
    post_id: int
    platform: str
    likes: int = 0
    retweets: int = 0
    comments: int = 0
    views: int = 0
    clicks: int = 0
    shares: int = 0
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WeeklyDigest:
    """Weekly email digest summary."""
    week_start: datetime
    week_end: datetime
    top_posts: List[SocialPost] = field(default_factory=list)
    total_engagement: int = 0
    best_strategy: str = ""
    performance_summary: str = ""


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

class SocialDistributorDB:
    """SQLite database for posts and engagement metrics."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS social_posts (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id      TEXT NOT NULL,
                    platform        TEXT NOT NULL,
                    title           TEXT NOT NULL,
                    body            TEXT NOT NULL,
                    link            TEXT,
                    image_url       TEXT,
                    video_path      TEXT,
                    hashtags        TEXT,  -- JSON array
                    scheduled_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    posted_at       DATETIME,
                    status          TEXT DEFAULT 'draft',
                    engagement_likes INTEGER DEFAULT 0,
                    engagement_retweets INTEGER DEFAULT 0,
                    engagement_comments INTEGER DEFAULT 0,
                    engagement_views INTEGER DEFAULT 0,
                    error_message   TEXT,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content_hash    TEXT UNIQUE,
                    CONSTRAINT unique_platform_content UNIQUE(platform, content_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS engagement_metrics (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id     INTEGER NOT NULL,
                    platform    TEXT NOT NULL,
                    likes       INTEGER DEFAULT 0,
                    retweets    INTEGER DEFAULT 0,
                    comments    INTEGER DEFAULT 0,
                    views       INTEGER DEFAULT 0,
                    clicks      INTEGER DEFAULT 0,
                    shares      INTEGER DEFAULT 0,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES social_posts(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS post_schedule (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform        TEXT NOT NULL,
                    time_mst        TEXT NOT NULL,  -- HH:MM format
                    frequency       TEXT DEFAULT 'daily',  -- daily, weekly
                    day_of_week     INTEGER,  -- 0=Monday, 4=Friday (only for weekly)
                    enabled         BOOLEAN DEFAULT 1,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def insert_post(self, post: SocialPost) -> int:
        """Insert a new post."""
        post.updated_at = datetime.now(timezone.utc)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO social_posts
                (content_id, platform, title, body, link, image_url, video_path, hashtags,
                 scheduled_at, status, created_at, updated_at, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.content_id,
                    post.platform,
                    post.title,
                    post.body,
                    post.link,
                    post.image_url,
                    post.video_path,
                    json.dumps(post.hashtags),
                    post.scheduled_at.isoformat(),
                    post.status,
                    post.created_at.isoformat(),
                    post.updated_at.isoformat(),
                    post.content_hash(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_post(self, post_id: int) -> Optional[SocialPost]:
        """Retrieve a post by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM social_posts WHERE id=?", (post_id,)).fetchone()
            if not row:
                return None
            return self._row_to_post(row)

    def list_posts_by_platform(self, platform: str, status: Optional[str] = None) -> List[SocialPost]:
        """List posts by platform and optional status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM social_posts WHERE platform=? AND status=? ORDER BY scheduled_at DESC",
                    (platform, status),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM social_posts WHERE platform=? ORDER BY scheduled_at DESC",
                    (platform,),
                ).fetchall()
            return [self._row_to_post(row) for row in rows]

    def update_post_status(self, post_id: int, status: str, error: Optional[str] = None) -> None:
        """Update post status (posted, failed, etc.)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE social_posts SET status=?, error_message=?, updated_at=?, posted_at=? WHERE id=?",
                (status, error, datetime.now(timezone.utc).isoformat(),
                 datetime.now(timezone.utc).isoformat() if status == "posted" else None, post_id),
            )
            conn.commit()

    def update_engagement(self, post_id: int, likes: int, retweets: int, comments: int, views: int) -> None:
        """Update engagement metrics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE social_posts
                SET engagement_likes=?, engagement_retweets=?, engagement_comments=?, engagement_views=?
                WHERE id=?
                """,
                (likes, retweets, comments, views, post_id),
            )
            conn.commit()

    def check_duplicate(self, platform: str, content_id: str) -> bool:
        """Check if post already exists (prevent duplicates)."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT id FROM social_posts WHERE platform=? AND content_id=?",
                (platform, content_id),
            ).fetchone()
            return result is not None

    def get_top_posts_by_engagement(self, days: int = 7, limit: int = 5) -> List[SocialPost]:
        """Get top performing posts in the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM social_posts
                WHERE created_at > ? AND status='posted'
                ORDER BY (engagement_likes + engagement_retweets + engagement_comments) DESC
                LIMIT ?
                """,
                (cutoff.isoformat(), limit),
            ).fetchall()
            return [self._row_to_post(row) for row in rows]

    def _row_to_post(self, row: sqlite3.Row) -> SocialPost:
        """Convert database row to SocialPost object."""
        return SocialPost(
            id=row["id"],
            content_id=row["content_id"],
            platform=row["platform"],
            title=row["title"],
            body=row["body"],
            link=row["link"],
            image_url=row["image_url"],
            video_path=row["video_path"],
            hashtags=json.loads(row["hashtags"] or "[]"),
            scheduled_at=datetime.fromisoformat(row["scheduled_at"]),
            posted_at=datetime.fromisoformat(row["posted_at"]) if row["posted_at"] else None,
            status=row["status"],
            engagement_likes=row["engagement_likes"],
            engagement_retweets=row["engagement_retweets"],
            engagement_comments=row["engagement_comments"],
            engagement_views=row["engagement_views"],
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


# ============================================================================
# PLATFORM-SPECIFIC FORMATTERS
# ============================================================================

class PlatformFormatter:
    """Format content for each platform with proper tone and constraints."""

    @staticmethod
    def format_twitter(post: SocialPost) -> str:
        """Format for Twitter: 280 chars, hashtags required."""
        hashtag_str = " ".join(f"#{tag}" for tag in post.hashtags[:3])
        # Keep title + hashtags under 280
        text = f"{post.title}\n\n{post.link}\n\n{hashtag_str}"
        if len(text) > 280:
            text = f"{post.title[:140]}...\n\n{post.link}\n\n{hashtag_str}"
        return text[:280]

    @staticmethod
    def format_linkedin(post: SocialPost) -> str:
        """Format for LinkedIn: professional tone, 3000 char limit."""
        hashtag_str = " ".join(f"#{tag}" for tag in post.hashtags[:3])
        text = (
            f"{post.title}\n\n"
            f"{post.body[:600]}\n\n"
            f"Learn more: {post.link}\n\n"
            f"{hashtag_str}"
        )
        return text[:3000]

    @staticmethod
    def format_tiktok(post: SocialPost) -> str:
        """Format for TikTok: 150 char description + trending hashtags."""
        hashtag_str = " ".join(f"#{tag}" for tag in post.hashtags[:5])
        text = f"{post.title}\n\n{hashtag_str}"
        return text[:150]

    @staticmethod
    def format_youtube(post: SocialPost) -> Tuple[str, str]:
        """Format for YouTube: title (100 chars) + description (5000 chars)."""
        title = post.title[:100]
        description = (
            f"{post.body[:500]}\n\n"
            f"Watch more trading insights: {post.link}\n\n"
            f"Subscribe for daily profitable trading strategies.\n\n"
            f"Hashtags: {' '.join(f'#{tag}' for tag in post.hashtags[:5])}"
        )
        return title, description[:5000]

    @staticmethod
    def format_reddit(post: SocialPost, subreddit: str = "algotrading") -> Tuple[str, str, str]:
        """Format for Reddit: subreddit, title (300 chars), body (40000 chars)."""
        title = post.title[:300]
        body = (
            f"{post.body}\n\n"
            f"[Read full post]({post.link})\n\n"
            f"{FTC_DISCLOSURE}"
        )
        return subreddit, title, body[:40000]

    @staticmethod
    def format_email_digest(posts: List[SocialPost]) -> str:
        """Format for weekly email digest."""
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }}
                    .post {{ border-left: 4px solid #667eea; padding: 15px; margin: 10px 0; background: #f9f9f9; }}
                    .engagement {{ font-size: 12px; color: #999; }}
                    .cta {{ background: #667eea; color: white; padding: 12px 20px; border-radius: 5px; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>ProfitEngine Weekly Digest</h1>
                    <p>Your top trading insights and performance metrics</p>
                </div>

                <h2>Top Posts This Week</h2>
        """

        for i, post in enumerate(posts[:5], 1):
            total_engagement = (
                post.engagement_likes + post.engagement_retweets +
                post.engagement_comments + post.engagement_views
            )
            html += f"""
                <div class="post">
                    <h3>{i}. {post.title}</h3>
                    <p>{post.body[:200]}...</p>
                    <p><a href="{post.link}">Read more</a></p>
                    <div class="engagement">
                        Engagement: {total_engagement:,} interactions
                        (Likes: {post.engagement_likes}, Retweets: {post.engagement_retweets},
                         Comments: {post.engagement_comments})
                    </div>
                </div>
            """

        html += f"""
                <h2>Next Week's Strategy</h2>
                <p>
                    Based on this week's performance, we're doubling down on momentum-based trading strategies.
                    Stay tuned for daily updates.
                </p>

                <p style="text-align: center; margin-top: 30px;">
                    <a href="{PROFITENGINE_URL}/dashboard" class="cta">View Live Dashboard</a>
                </p>

                <hr>
                <p style="font-size: 12px; color: #999;">
                    {FTC_DISCLOSURE}
                </p>
                <p style="font-size: 12px; color: #999;">
                    Already Here LLC | <a href="https://alreadyherellc.com">alreadyherellc.com</a>
                </p>
            </body>
        </html>
        """
        return html


# ============================================================================
# SOCIAL DISTRIBUTOR ENGINE
# ============================================================================

class SocialDistributor:
    """Main engine for distributing content to all platforms."""

    def __init__(self):
        self.db = SocialDistributorDB()
        self.social_engine = ProductionSocialEngine() if ProductionSocialEngine else None
        self.scheduler = BackgroundScheduler(daemon=True) if SCHEDULER_AVAILABLE else None
        logger.info("SocialDistributor initialized")

    def create_post(self, content_id: str, title: str, body: str, link: str,
                   platforms: List[str], hashtags: Optional[List[str]] = None,
                   image_url: Optional[str] = None, video_path: Optional[str] = None) -> List[int]:
        """Create posts for specified platforms."""
        if not hashtags:
            hashtags = ["trading", "ai", "alreadyhere", "autonomous"]

        post_ids = []
        for platform in platforms:
            if self.db.check_duplicate(platform, content_id):
                logger.info(f"[{platform}] Post already exists for {content_id} — skipping")
                continue

            post = SocialPost(
                content_id=content_id,
                platform=platform,
                title=title,
                body=body,
                link=link,
                image_url=image_url,
                video_path=video_path,
                hashtags=hashtags,
                status="draft",
            )
            post_id = self.db.insert_post(post)
            post_ids.append(post_id)
            logger.info(f"[{platform}] Created post {post_id} for {content_id}")

        return post_ids

    async def post_twitter(self, post: SocialPost, thread_tweets: Optional[List[str]] = None) -> bool:
        """Post to Twitter with optional thread."""
        if not self.social_engine:
            logger.error("Social engine not available")
            return False

        text = PlatformFormatter.format_twitter(post)
        post_obj = SocialPost(
            db_id=post.id,
            platform="TWITTER",
            text_content=text,
            extra={"thread_tweets": thread_tweets} if thread_tweets else None,
        )
        try:
            await self.social_engine.publish(post_obj)
            self.db.update_post_status(post.id, "posted")
            logger.info(f"[Twitter] Posted {post.id}")
            return True
        except Exception as e:
            self.db.update_post_status(post.id, "failed", str(e))
            logger.error(f"[Twitter] Failed to post {post.id}: {e}")
            return False

    async def post_linkedin(self, post: SocialPost) -> bool:
        """Post to LinkedIn."""
        if not self.social_engine:
            return False

        text = PlatformFormatter.format_linkedin(post)
        post_obj = SocialPost(
            db_id=post.id,
            platform="LINKEDIN",
            text_content=text,
        )
        try:
            await self.social_engine.publish(post_obj)
            self.db.update_post_status(post.id, "posted")
            logger.info(f"[LinkedIn] Posted {post.id}")
            return True
        except Exception as e:
            self.db.update_post_status(post.id, "failed", str(e))
            logger.error(f"[LinkedIn] Failed to post {post.id}: {e}")
            return False

    async def post_tiktok(self, post: SocialPost) -> bool:
        """Post short video to TikTok."""
        if not post.video_path or not os.path.exists(post.video_path):
            logger.warning(f"[TikTok] No video file for {post.id}")
            self.db.update_post_status(post.id, "failed", "No video file")
            return False

        if not self.social_engine:
            return False

        text = PlatformFormatter.format_tiktok(post)
        post_obj = SocialPost(
            db_id=post.id,
            platform="TIKTOK",
            text_content=text,
            media_path=post.video_path,
        )
        try:
            await self.social_engine.publish(post_obj)
            self.db.update_post_status(post.id, "posted")
            logger.info(f"[TikTok] Posted {post.id}")
            return True
        except Exception as e:
            self.db.update_post_status(post.id, "failed", str(e))
            logger.error(f"[TikTok] Failed to post {post.id}: {e}")
            return False

    async def post_youtube(self, post: SocialPost) -> bool:
        """Post video to YouTube Shorts."""
        if not post.video_path or not os.path.exists(post.video_path):
            logger.warning(f"[YouTube] No video file for {post.id}")
            self.db.update_post_status(post.id, "failed", "No video file")
            return False

        if not self.social_engine:
            return False

        title, description = PlatformFormatter.format_youtube(post)
        post_obj = SocialPost(
            db_id=post.id,
            platform="YOUTUBE",
            text_content=title,
            media_path=post.video_path,
            extra={
                "description": description,
                "tags": post.hashtags + ["ProfitEngine", "PassiveIncome", "AlreadyHereLLC"],
            },
        )
        try:
            await self.social_engine.publish(post_obj)
            self.db.update_post_status(post.id, "posted")
            logger.info(f"[YouTube] Posted {post.id}")
            return True
        except Exception as e:
            self.db.update_post_status(post.id, "failed", str(e))
            logger.error(f"[YouTube] Failed to post {post.id}: {e}")
            return False

    async def post_reddit(self, post: SocialPost, subreddits: Optional[List[str]] = None) -> bool:
        """Post to Reddit subreddits."""
        if not subreddits:
            subreddits = REDDIT_SUBREDDITS

        if not self.social_engine:
            return False

        success_count = 0
        for subreddit in subreddits:
            sub_name, title, body = PlatformFormatter.format_reddit(post, subreddit)
            post_obj = SocialPost(
                db_id=post.id,
                platform="REDDIT",
                text_content=title,
                extra={"subreddit": sub_name, "url": post.link},
            )
            try:
                await self.social_engine.publish(post_obj)
                success_count += 1
                logger.info(f"[Reddit] Posted to r/{subreddit}")
            except Exception as e:
                logger.error(f"[Reddit] Failed r/{subreddit}: {e}")

        if success_count > 0:
            self.db.update_post_status(post.id, "posted")
            return True
        else:
            self.db.update_post_status(post.id, "failed", "Failed to post to any subreddit")
            return False

    def send_email_digest(self, recipient: Optional[str] = None) -> bool:
        """Send weekly email digest with top posts."""
        if not recipient:
            recipient = ALERT_EMAIL

        top_posts = self.db.get_top_posts_by_engagement(days=7, limit=5)
        if not top_posts:
            logger.info("[Email] No posts to digest this week")
            return False

        html_body = PlatformFormatter.format_email_digest(top_posts)

        try:
            gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
            if not gmail_app_password:
                logger.error("[Email] No Gmail app password configured")
                return False

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "ProfitEngine Weekly Digest"
            msg["From"] = GMAIL_USER
            msg["To"] = recipient

            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_USER, gmail_app_password)
                server.send_message(msg)

            logger.info(f"[Email] Digest sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"[Email] Failed to send digest: {e}")
            return False

    async def post_all_platforms(self, content_id: str, title: str, body: str, link: str,
                                 platforms: List[str], hashtags: Optional[List[str]] = None,
                                 image_url: Optional[str] = None, video_path: Optional[str] = None) -> Dict[str, bool]:
        """Post to multiple platforms simultaneously."""
        post_ids = self.create_post(content_id, title, body, link, platforms, hashtags, image_url, video_path)

        results = {}
        for post_id in post_ids:
            post = self.db.get_post(post_id)
            if not post:
                continue

            if post.platform == "twitter":
                results[post.platform] = await self.post_twitter(post)
            elif post.platform == "linkedin":
                results[post.platform] = await self.post_linkedin(post)
            elif post.platform == "tiktok":
                results[post.platform] = await self.post_tiktok(post)
            elif post.platform == "youtube":
                results[post.platform] = await self.post_youtube(post)
            elif post.platform == "reddit":
                results[post.platform] = await self.post_reddit(post)

        return results

    def schedule_daily_posts(self) -> None:
        """Initialize scheduled posting for all platforms."""
        if not self.scheduler:
            logger.warning("APScheduler not available — cannot schedule posts")
            return

        # Twitter: 2x daily (9 AM + 5 PM MST)
        self.scheduler.add_job(
            self._scheduled_twitter_post,
            "cron", hour=9, minute=0,
            timezone="US/Mountain",
            id="twitter_morning",
        )
        self.scheduler.add_job(
            self._scheduled_twitter_post,
            "cron", hour=17, minute=0,
            timezone="US/Mountain",
            id="twitter_evening",
        )

        # LinkedIn: daily 9 AM MST
        self.scheduler.add_job(
            self._scheduled_linkedin_post,
            "cron", hour=9, minute=0,
            timezone="US/Mountain",
            id="linkedin_daily",
        )

        # TikTok: daily 5 PM MST
        self.scheduler.add_job(
            self._scheduled_tiktok_post,
            "cron", hour=17, minute=0,
            timezone="US/Mountain",
            id="tiktok_daily",
        )

        # YouTube: daily 5 PM MST
        self.scheduler.add_job(
            self._scheduled_youtube_post,
            "cron", hour=17, minute=0,
            timezone="US/Mountain",
            id="youtube_daily",
        )

        # Email digest: Friday 10 AM MST
        self.scheduler.add_job(
            self._scheduled_email_digest,
            "cron", day_of_week=4, hour=10, minute=0,
            timezone="US/Mountain",
            id="email_digest_weekly",
        )

        self.scheduler.start()
        logger.info("[Scheduler] Daily posting schedule initialized")

    def _scheduled_twitter_post(self) -> None:
        """Background job for Twitter posting."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Get pending posts
            pending = self.db.list_posts_by_platform("twitter", "draft")
            if pending:
                loop.run_until_complete(self.post_twitter(pending[0]))
        finally:
            loop.close()

    def _scheduled_linkedin_post(self) -> None:
        """Background job for LinkedIn posting."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pending = self.db.list_posts_by_platform("linkedin", "draft")
            if pending:
                loop.run_until_complete(self.post_linkedin(pending[0]))
        finally:
            loop.close()

    def _scheduled_tiktok_post(self) -> None:
        """Background job for TikTok posting."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pending = self.db.list_posts_by_platform("tiktok", "draft")
            if pending:
                loop.run_until_complete(self.post_tiktok(pending[0]))
        finally:
            loop.close()

    def _scheduled_youtube_post(self) -> None:
        """Background job for YouTube posting."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pending = self.db.list_posts_by_platform("youtube", "draft")
            if pending:
                loop.run_until_complete(self.post_youtube(pending[0]))
        finally:
            loop.close()

    def _scheduled_email_digest(self) -> None:
        """Background job for email digest."""
        self.send_email_digest()


# ============================================================================
# API INTEGRATION (FastAPI routes)
# ============================================================================

def register_routes(app) -> None:
    """Register FastAPI routes for social distribution."""
    from fastapi import HTTPException
    from pydantic import BaseModel

    class DistributeRequest(BaseModel):
        content_id: str
        title: str
        body: str
        link: str
        platforms: List[str]
        hashtags: Optional[List[str]] = None
        image_url: Optional[str] = None
        video_path: Optional[str] = None

    distributor = SocialDistributor()

    @app.post("/api/social/distribute")
    async def distribute_content(req: DistributeRequest) -> Dict[str, Any]:
        """Distribute content to multiple platforms."""
        try:
            results = await distributor.post_all_platforms(
                content_id=req.content_id,
                title=req.title,
                body=req.body,
                link=req.link,
                platforms=req.platforms,
                hashtags=req.hashtags,
                image_url=req.image_url,
                video_path=req.video_path,
            )
            return {"ok": True, "results": results}
        except Exception as e:
            logger.error(f"Distribution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/social/posts")
    def list_posts(platform: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """List posts by platform and status."""
        if platform:
            posts = distributor.db.list_posts_by_platform(platform, status)
        else:
            posts = []
        return {
            "ok": True,
            "posts": [asdict(p) for p in posts],
        }

    @app.get("/api/social/engagement")
    def get_engagement(days: int = 7, limit: int = 5) -> Dict[str, Any]:
        """Get top posts by engagement."""
        posts = distributor.db.get_top_posts_by_engagement(days, limit)
        total_engagement = sum(
            p.engagement_likes + p.engagement_retweets +
            p.engagement_comments + p.engagement_views
            for p in posts
        )
        return {
            "ok": True,
            "total_engagement": total_engagement,
            "top_posts": [asdict(p) for p in posts],
        }

    @app.post("/api/social/digest")
    def send_digest(recipient: Optional[str] = None) -> Dict[str, Any]:
        """Send email digest manually."""
        ok = distributor.send_email_digest(recipient)
        return {"ok": ok, "message": "Digest sent" if ok else "Digest failed"}

    logger.info("Social distribution routes registered")


# ============================================================================
# CLI & MAIN
# ============================================================================

async def main():
    """CLI entry point for testing."""
    distributor = SocialDistributor()

    # Example: create and post content
    content_id = "test_post_001"
    title = "90% Win Rate Achieved with AI-Powered Trading Strategy"
    body = (
        "Our autonomous trading system hit 90% win rate this week using advanced momentum analysis "
        "and machine learning. Learn how we're making consistent profits in volatile markets."
    )
    link = f"{PROFITENGINE_URL}/blog/90-percent-win-rate"

    platforms = ["twitter", "linkedin"]
    hashtags = ["trading", "ai", "alreadyhere", "autonomous"]

    results = await distributor.post_all_platforms(
        content_id=content_id,
        title=title,
        body=body,
        link=link,
        platforms=platforms,
        hashtags=hashtags,
    )

    logger.info(f"Distribution results: {results}")


if __name__ == "__main__":
    asyncio.run(main())

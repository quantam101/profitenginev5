#!/usr/bin/env python3
"""
Email List Manager for ProfitEngine v5
Subscriber management with SQLite backend, segmentation, double opt-in, and engagement tracking.
"""

import sqlite3
import os
import json
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SubscriberStatus(Enum):
    """Subscriber status lifecycle"""
    PENDING = "pending"  # Awaiting confirmation email
    ACTIVE = "active"  # Confirmed and subscribed
    PAUSED = "paused"  # Temporarily unsubscribed
    UNSUBSCRIBED = "unsubscribed"  # Permanently unsubscribed
    BOUNCED = "bounced"  # Hard bounce detected


class SegmentType(Enum):
    """Segment categories"""
    FREE = "free"
    PAID = "paid"
    VIP = "vip"
    SPONSOR = "sponsor"
    INACTIVE = "inactive"
    HIGH_ENGAGEMENT = "high_engagement"
    LOW_ENGAGEMENT = "low_engagement"


@dataclass
class Subscriber:
    """Subscriber data model"""
    email: str
    name: str
    status: str
    segment: str
    interests: Optional[List[str]] = None
    date_joined: Optional[str] = None
    last_engagement: Optional[str] = None
    confirmation_token: Optional[str] = None
    unsubscribe_token: Optional[str] = None
    subscriber_id: Optional[str] = None
    open_count: int = 0
    click_count: int = 0
    referral_count: int = 0
    custom_fields: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['interests'] = json.dumps(self.interests) if self.interests else None
        data['custom_fields'] = json.dumps(self.custom_fields) if self.custom_fields else None
        return data


class EmailListManager:
    """
    Comprehensive email list management system.
    Handles subscribers, segments, opt-in flows, and engagement tracking.
    """

    def __init__(self, db_path: str = "profitengine_subscribers.db"):
        """Initialize the email list manager with SQLite backend"""
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize SQLite database with all required tables"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            # Subscribers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    subscriber_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    segment TEXT NOT NULL DEFAULT 'free',
                    interests TEXT,
                    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_engagement TIMESTAMP,
                    confirmation_token TEXT,
                    unsubscribe_token TEXT,
                    open_count INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    referral_count INTEGER DEFAULT 0,
                    custom_fields TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Email segments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS segments (
                    segment_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    segment_type TEXT NOT NULL,
                    criteria TEXT NOT NULL,
                    subscriber_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Email campaigns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    segment_id TEXT,
                    sent_count INTEGER DEFAULT 0,
                    open_count INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(segment_id) REFERENCES segments(segment_id)
                )
            """)

            # Engagement tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engagement (
                    engagement_id TEXT PRIMARY KEY,
                    subscriber_id TEXT NOT NULL,
                    campaign_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    link_url TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(subscriber_id) REFERENCES subscribers(subscriber_id),
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
                )
            """)

            # Double opt-in confirmations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS confirmations (
                    confirmation_id TEXT PRIMARY KEY,
                    subscriber_id TEXT NOT NULL,
                    confirmation_token TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(subscriber_id) REFERENCES subscribers(subscriber_id)
                )
            """)

            # Unsubscribe preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    preference_id TEXT PRIMARY KEY,
                    subscriber_id TEXT NOT NULL,
                    email_frequency TEXT DEFAULT 'weekly',
                    newsletter BOOLEAN DEFAULT 1,
                    product_updates BOOLEAN DEFAULT 1,
                    promotions BOOLEAN DEFAULT 1,
                    account_notifications BOOLEAN DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(subscriber_id) REFERENCES subscribers(subscriber_id)
                )
            """)

            # Referral tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    referral_id TEXT PRIMARY KEY,
                    referrer_id TEXT NOT NULL,
                    referred_email TEXT NOT NULL,
                    referral_token TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    reward_claimed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY(referrer_id) REFERENCES subscribers(subscriber_id)
                )
            """)

            # Lead magnets table (free ebook offers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lead_magnets (
                    lead_magnet_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    file_url TEXT,
                    download_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Lead magnet downloads
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS magnet_downloads (
                    download_id TEXT PRIMARY KEY,
                    subscriber_id TEXT,
                    lead_magnet_id TEXT NOT NULL,
                    email TEXT,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(subscriber_id) REFERENCES subscribers(subscriber_id),
                    FOREIGN KEY(lead_magnet_id) REFERENCES lead_magnets(lead_magnet_id)
                )
            """)

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON subscribers(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON subscribers(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_segment ON subscribers(segment)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaign_id ON engagement(campaign_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriber_id ON engagement(subscriber_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_confirmation_token ON confirmations(confirmation_token)")

            self.conn.commit()
            logger.info(f"Database initialized: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def _generate_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def add_subscriber(
        self,
        email: str,
        name: str,
        interests: Optional[List[str]] = None,
        segment: str = SegmentType.FREE.value,
        custom_fields: Optional[Dict] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Add a new subscriber with double opt-in flow.
        Returns: (success, message, subscriber_id)
        """
        if not self._validate_email(email):
            return False, "Invalid email format", None

        try:
            cursor = self.conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT subscriber_id FROM subscribers WHERE email = ?", (email,))
            existing = cursor.fetchone()
            if existing:
                return False, f"Subscriber {email} already exists", None

            subscriber_id = str(uuid.uuid4())
            confirmation_token = self._generate_token()
            unsubscribe_token = self._generate_token()

            subscriber = Subscriber(
                subscriber_id=subscriber_id,
                email=email,
                name=name,
                status=SubscriberStatus.PENDING.value,
                segment=segment,
                interests=interests or [],
                confirmation_token=confirmation_token,
                unsubscribe_token=unsubscribe_token,
                custom_fields=custom_fields
            )

            data = subscriber.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            cursor.execute(
                f"INSERT INTO subscribers ({columns}) VALUES ({placeholders})",
                tuple(data.values())
            )

            # Create confirmation record
            confirmation_id = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            cursor.execute("""
                INSERT INTO confirmations
                (confirmation_id, subscriber_id, confirmation_token, email, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (confirmation_id, subscriber_id, confirmation_token, email, expires_at))

            # Create default preferences
            preference_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO preferences (preference_id, subscriber_id)
                VALUES (?, ?)
            """, (preference_id, subscriber_id))

            self.conn.commit()
            logger.info(f"Subscriber added (pending): {email} (ID: {subscriber_id})")
            return True, f"Confirmation email sent to {email}", subscriber_id

        except sqlite3.Error as e:
            logger.error(f"Error adding subscriber: {e}")
            return False, f"Database error: {str(e)}", None

    def confirm_subscription(self, confirmation_token: str) -> Tuple[bool, str]:
        """
        Confirm double opt-in subscription via confirmation token.
        Returns: (success, message)
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT subscriber_id, expires_at FROM confirmations
                WHERE confirmation_token = ? AND confirmed_at IS NULL
            """, (confirmation_token,))
            result = cursor.fetchone()

            if not result:
                return False, "Invalid or expired confirmation token"

            subscriber_id, expires_at = result
            if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
                return False, "Confirmation token has expired"

            # Update subscriber status
            cursor.execute("""
                UPDATE subscribers SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE subscriber_id = ?
            """, (SubscriberStatus.ACTIVE.value, subscriber_id))

            # Mark confirmation as completed
            cursor.execute("""
                UPDATE confirmations SET confirmed_at = CURRENT_TIMESTAMP
                WHERE subscriber_id = ?
            """, (subscriber_id,))

            self.conn.commit()
            logger.info(f"Subscription confirmed for subscriber: {subscriber_id}")
            return True, "Subscription confirmed successfully"

        except sqlite3.Error as e:
            logger.error(f"Error confirming subscription: {e}")
            return False, f"Database error: {str(e)}"

    def unsubscribe(self, unsubscribe_token: str) -> Tuple[bool, str]:
        """
        Unsubscribe via token (supports email footer links).
        Returns: (success, message)
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE subscribers SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE unsubscribe_token = ?
            """, (SubscriberStatus.UNSUBSCRIBED.value, unsubscribe_token))

            if cursor.rowcount == 0:
                return False, "Invalid unsubscribe token"

            self.conn.commit()
            logger.info(f"Subscriber unsubscribed via token")
            return True, "You have been unsubscribed"

        except sqlite3.Error as e:
            logger.error(f"Error unsubscribing: {e}")
            return False, f"Database error: {str(e)}"

    def update_preferences(
        self,
        subscriber_id: str,
        email_frequency: Optional[str] = None,
        newsletter: Optional[bool] = None,
        product_updates: Optional[bool] = None,
        promotions: Optional[bool] = None,
        account_notifications: Optional[bool] = None
    ) -> Tuple[bool, str]:
        """Update subscriber email preferences"""
        try:
            cursor = self.conn.cursor()

            updates = ["updated_at = CURRENT_TIMESTAMP"]
            params = []

            if email_frequency:
                updates.append("email_frequency = ?")
                params.append(email_frequency)
            if newsletter is not None:
                updates.append("newsletter = ?")
                params.append(newsletter)
            if product_updates is not None:
                updates.append("product_updates = ?")
                params.append(product_updates)
            if promotions is not None:
                updates.append("promotions = ?")
                params.append(promotions)
            if account_notifications is not None:
                updates.append("account_notifications = ?")
                params.append(account_notifications)

            params.append(subscriber_id)

            cursor.execute(f"""
                UPDATE preferences SET {', '.join(updates)}
                WHERE subscriber_id = ?
            """, params)

            if cursor.rowcount == 0:
                return False, "Subscriber not found"

            self.conn.commit()
            logger.info(f"Preferences updated for subscriber: {subscriber_id}")
            return True, "Preferences updated successfully"

        except sqlite3.Error as e:
            logger.error(f"Error updating preferences: {e}")
            return False, f"Database error: {str(e)}"

    def create_segment(
        self,
        name: str,
        segment_type: str,
        criteria: Dict
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create an email segment based on criteria.
        Criteria can include: status, min_opens, min_clicks, subscription_days, etc.
        """
        try:
            cursor = self.conn.cursor()

            # Check if segment exists
            cursor.execute("SELECT segment_id FROM segments WHERE name = ?", (name,))
            if cursor.fetchone():
                return False, f"Segment '{name}' already exists", None

            segment_id = str(uuid.uuid4())
            criteria_json = json.dumps(criteria)

            cursor.execute("""
                INSERT INTO segments (segment_id, name, segment_type, criteria)
                VALUES (?, ?, ?, ?)
            """, (segment_id, name, segment_type, criteria_json))

            self.conn.commit()
            logger.info(f"Segment created: {name} ({segment_type})")
            return True, f"Segment '{name}' created", segment_id

        except sqlite3.Error as e:
            logger.error(f"Error creating segment: {e}")
            return False, f"Database error: {str(e)}", None

    def get_active_subscribers(
        self,
        segment: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get active subscribers, optionally filtered by segment.
        Returns list of active subscriber records.
        """
        try:
            cursor = self.conn.cursor()

            query = """
                SELECT subscriber_id, email, name, segment, open_count, click_count, last_engagement
                FROM subscribers
                WHERE status = ?
            """
            params = [SubscriberStatus.ACTIVE.value]

            if segment:
                query += " AND segment = ?"
                params.append(segment)

            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [dict(row) for row in results]

        except sqlite3.Error as e:
            logger.error(f"Error fetching active subscribers: {e}")
            return []

    def get_segment_subscribers(self, segment_id: str) -> List[Dict]:
        """Get all subscribers in a specific segment"""
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT segment_id, name, segment_type FROM segments WHERE segment_id = ?
            """, (segment_id,))
            segment = cursor.fetchone()

            if not segment:
                logger.warning(f"Segment not found: {segment_id}")
                return []

            # Build query based on segment criteria
            criteria = json.loads(segment['criteria'])

            query = "SELECT * FROM subscribers WHERE status = ?"
            params = [SubscriberStatus.ACTIVE.value]

            if 'min_opens' in criteria:
                query += " AND open_count >= ?"
                params.append(criteria['min_opens'])

            if 'min_clicks' in criteria:
                query += " AND click_count >= ?"
                params.append(criteria['min_clicks'])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(f"Error fetching segment subscribers: {e}")
            return []

    def track_open(
        self,
        email: str,
        campaign_id: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> Tuple[bool, str]:
        """Track email open event"""
        try:
            cursor = self.conn.cursor()

            # Find subscriber
            cursor.execute("SELECT subscriber_id FROM subscribers WHERE email = ?", (email,))
            result = cursor.fetchone()

            if not result:
                return False, "Subscriber not found"

            subscriber_id = result['subscriber_id']
            engagement_id = str(uuid.uuid4())

            # Record engagement
            cursor.execute("""
                INSERT INTO engagement
                (engagement_id, subscriber_id, campaign_id, event_type, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (engagement_id, subscriber_id, campaign_id, 'open', user_agent, ip_address))

            # Update subscriber open count and last engagement
            cursor.execute("""
                UPDATE subscribers
                SET open_count = open_count + 1, last_engagement = CURRENT_TIMESTAMP
                WHERE subscriber_id = ?
            """, (subscriber_id,))

            # Update campaign open count
            cursor.execute("""
                UPDATE campaigns
                SET open_count = open_count + 1
                WHERE campaign_id = ?
            """, (campaign_id,))

            self.conn.commit()
            logger.info(f"Open tracked: {email} / {campaign_id}")
            return True, "Open tracked"

        except sqlite3.Error as e:
            logger.error(f"Error tracking open: {e}")
            return False, f"Database error: {str(e)}"

    def track_click(
        self,
        email: str,
        campaign_id: str,
        link_url: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> Tuple[bool, str]:
        """Track email click event"""
        try:
            cursor = self.conn.cursor()

            # Find subscriber
            cursor.execute("SELECT subscriber_id FROM subscribers WHERE email = ?", (email,))
            result = cursor.fetchone()

            if not result:
                return False, "Subscriber not found"

            subscriber_id = result['subscriber_id']
            engagement_id = str(uuid.uuid4())

            # Record engagement
            cursor.execute("""
                INSERT INTO engagement
                (engagement_id, subscriber_id, campaign_id, event_type, link_url, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (engagement_id, subscriber_id, campaign_id, 'click', link_url, user_agent, ip_address))

            # Update subscriber click count and last engagement
            cursor.execute("""
                UPDATE subscribers
                SET click_count = click_count + 1, last_engagement = CURRENT_TIMESTAMP
                WHERE subscriber_id = ?
            """, (subscriber_id,))

            # Update campaign click count
            cursor.execute("""
                UPDATE campaigns
                SET click_count = click_count + 1
                WHERE campaign_id = ?
            """, (campaign_id,))

            self.conn.commit()
            logger.info(f"Click tracked: {email} / {campaign_id} -> {link_url}")
            return True, "Click tracked"

        except sqlite3.Error as e:
            logger.error(f"Error tracking click: {e}")
            return False, f"Database error: {str(e)}"

    def create_campaign(
        self,
        name: str,
        subject: str,
        segment_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Create an email campaign"""
        try:
            cursor = self.conn.cursor()

            campaign_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO campaigns (campaign_id, name, subject, segment_id)
                VALUES (?, ?, ?, ?)
            """, (campaign_id, name, subject, segment_id))

            self.conn.commit()
            logger.info(f"Campaign created: {name} ({campaign_id})")
            return True, f"Campaign '{name}' created", campaign_id

        except sqlite3.Error as e:
            logger.error(f"Error creating campaign: {e}")
            return False, f"Database error: {str(e)}", None

    def get_campaign_stats(self, campaign_id: str) -> Optional[Dict]:
        """Get engagement statistics for a campaign"""
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT campaign_id, name, sent_count, open_count, click_count,
                       ROUND(100.0 * open_count / NULLIF(sent_count, 0), 2) as open_rate,
                       ROUND(100.0 * click_count / NULLIF(open_count, 0), 2) as ctr
                FROM campaigns
                WHERE campaign_id = ?
            """, (campaign_id,))

            result = cursor.fetchone()
            return dict(result) if result else None

        except sqlite3.Error as e:
            logger.error(f"Error fetching campaign stats: {e}")
            return None

    def add_lead_magnet(
        self,
        name: str,
        description: str,
        file_url: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Add a free lead magnet (ebook, template, etc.)"""
        try:
            cursor = self.conn.cursor()

            lead_magnet_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO lead_magnets (lead_magnet_id, name, description, file_url)
                VALUES (?, ?, ?, ?)
            """, (lead_magnet_id, name, description, file_url))

            self.conn.commit()
            logger.info(f"Lead magnet added: {name}")
            return True, f"Lead magnet '{name}' created", lead_magnet_id

        except sqlite3.Error as e:
            logger.error(f"Error adding lead magnet: {e}")
            return False, f"Database error: {str(e)}", None

    def track_magnet_download(
        self,
        lead_magnet_id: str,
        email: Optional[str] = None,
        subscriber_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Track lead magnet download"""
        try:
            cursor = self.conn.cursor()

            download_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO magnet_downloads
                (download_id, subscriber_id, lead_magnet_id, email)
                VALUES (?, ?, ?, ?)
            """, (download_id, subscriber_id, lead_magnet_id, email))

            # Update download count
            cursor.execute("""
                UPDATE lead_magnets SET download_count = download_count + 1
                WHERE lead_magnet_id = ?
            """, (lead_magnet_id,))

            self.conn.commit()
            logger.info(f"Magnet download tracked: {lead_magnet_id}")
            return True, "Download tracked"

        except sqlite3.Error as e:
            logger.error(f"Error tracking download: {e}")
            return False, f"Database error: {str(e)}"

    def create_referral(
        self,
        referrer_id: str,
        referred_email: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Create a referral link for growth automation"""
        try:
            cursor = self.conn.cursor()

            # Verify referrer exists
            cursor.execute(
                "SELECT subscriber_id FROM subscribers WHERE subscriber_id = ?",
                (referrer_id,)
            )
            if not cursor.fetchone():
                return False, "Referrer not found", None

            referral_id = str(uuid.uuid4())
            referral_token = self._generate_token()

            cursor.execute("""
                INSERT INTO referrals
                (referral_id, referrer_id, referred_email, referral_token)
                VALUES (?, ?, ?, ?)
            """, (referral_id, referrer_id, referred_email, referral_token))

            self.conn.commit()
            logger.info(f"Referral created: {referrer_id} -> {referred_email}")
            return True, "Referral created", referral_token

        except sqlite3.Error as e:
            logger.error(f"Error creating referral: {e}")
            return False, f"Database error: {str(e)}", None

    def complete_referral(self, referral_token: str, subscriber_id: str) -> Tuple[bool, str]:
        """Mark referral as complete when referred user subscribes"""
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE referrals
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE referral_token = ?
            """, ('completed', referral_token))

            if cursor.rowcount == 0:
                return False, "Referral not found"

            # Increment referrer's referral count
            cursor.execute("""
                UPDATE subscribers
                SET referral_count = referral_count + 1
                WHERE subscriber_id = (
                    SELECT referrer_id FROM referrals WHERE referral_token = ?
                )
            """, (referral_token,))

            self.conn.commit()
            logger.info(f"Referral completed: {referral_token}")
            return True, "Referral completed and reward available"

        except sqlite3.Error as e:
            logger.error(f"Error completing referral: {e}")
            return False, f"Database error: {str(e)}"

    def get_engagement_metrics(self) -> Dict:
        """Get overall engagement metrics"""
        try:
            cursor = self.conn.cursor()

            # Total subscribers
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as unsubscribed
                FROM subscribers
            """, (
                SubscriberStatus.ACTIVE.value,
                SubscriberStatus.PENDING.value,
                SubscriberStatus.UNSUBSCRIBED.value
            ))

            stats = dict(cursor.fetchone())

            # Engagement stats
            cursor.execute("""
                SELECT
                    AVG(open_count) as avg_opens,
                    AVG(click_count) as avg_clicks,
                    MAX(open_count) as max_opens,
                    MAX(click_count) as max_clicks
                FROM subscribers
                WHERE status = ?
            """, (SubscriberStatus.ACTIVE.value,))

            engagement = dict(cursor.fetchone())
            stats.update(engagement)

            # Segment breakdown
            cursor.execute("""
                SELECT segment, COUNT(*) as count
                FROM subscribers
                WHERE status = ?
                GROUP BY segment
            """, (SubscriberStatus.ACTIVE.value,))

            stats['by_segment'] = {row['segment']: row['count'] for row in cursor.fetchall()}

            return stats

        except sqlite3.Error as e:
            logger.error(f"Error fetching engagement metrics: {e}")
            return {}

    def export_subscribers(
        self,
        segment: Optional[str] = None,
        export_format: str = "json"
    ) -> Optional[str]:
        """
        Export subscribers to JSON or CSV format.
        Supports integration with Beehiiv, Resend, or other email services.
        """
        try:
            cursor = self.conn.cursor()

            query = """
                SELECT
                    email, name, status, segment,
                    interests, open_count, click_count,
                    date_joined, last_engagement
                FROM subscribers
                WHERE status = ?
            """
            params = [SubscriberStatus.ACTIVE.value]

            if segment:
                query += " AND segment = ?"
                params.append(segment)

            query += " ORDER BY date_joined DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return None

            if export_format == "json":
                data = []
                for row in rows:
                    data.append({
                        'email': row['email'],
                        'name': row['name'],
                        'segment': row['segment'],
                        'interests': json.loads(row['interests']) if row['interests'] else [],
                        'open_count': row['open_count'],
                        'click_count': row['click_count'],
                        'date_joined': row['date_joined'],
                        'last_engagement': row['last_engagement']
                    })
                return json.dumps(data, indent=2)

            elif export_format == "csv":
                import csv
                from io import StringIO

                output = StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=['email', 'name', 'segment', 'interests', 'open_count', 'click_count']
                )
                writer.writeheader()

                for row in rows:
                    writer.writerow({
                        'email': row['email'],
                        'name': row['name'],
                        'segment': row['segment'],
                        'interests': json.loads(row['interests']) if row['interests'] else [],
                        'open_count': row['open_count'],
                        'click_count': row['click_count']
                    })

                return output.getvalue()

            return None

        except sqlite3.Error as e:
            logger.error(f"Error exporting subscribers: {e}")
            return None

    def get_subscriber_by_email(self, email: str) -> Optional[Dict]:
        """Fetch a single subscriber by email"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM subscribers WHERE email = ?", (email,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching subscriber: {e}")
            return None

    def pause_subscription(self, subscriber_id: str) -> Tuple[bool, str]:
        """Temporarily pause a subscription"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE subscribers SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE subscriber_id = ?
            """, (SubscriberStatus.PAUSED.value, subscriber_id))

            if cursor.rowcount == 0:
                return False, "Subscriber not found"

            self.conn.commit()
            logger.info(f"Subscription paused: {subscriber_id}")
            return True, "Subscription paused"

        except sqlite3.Error as e:
            logger.error(f"Error pausing subscription: {e}")
            return False, f"Database error: {str(e)}"

    def resume_subscription(self, subscriber_id: str) -> Tuple[bool, str]:
        """Resume a paused subscription"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE subscribers SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE subscriber_id = ?
            """, (SubscriberStatus.ACTIVE.value, subscriber_id))

            if cursor.rowcount == 0:
                return False, "Subscriber not found"

            self.conn.commit()
            logger.info(f"Subscription resumed: {subscriber_id}")
            return True, "Subscription resumed"

        except sqlite3.Error as e:
            logger.error(f"Error resuming subscription: {e}")
            return False, f"Database error: {str(e)}"

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Demo/testing function
def demo():
    """Demonstrate email list manager functionality"""
    manager = EmailListManager()

    print("\n=== ProfitEngine Email List Manager Demo ===\n")

    # 1. Add subscribers
    print("1. Adding subscribers...")
    subscribers = [
        ("alice@example.com", "Alice Johnson", ["investing", "growth"]),
        ("bob@example.com", "Bob Smith", ["passive-income", "affiliate"]),
        ("charlie@example.com", "Charlie Brown", ["trading", "options"]),
    ]

    subscriber_ids = []
    for email, name, interests in subscribers:
        success, msg, sub_id = manager.add_subscriber(email, name, interests, segment="free")
        print(f"  {email}: {msg}")
        if sub_id:
            subscriber_ids.append((sub_id, email))

    # 2. Confirm subscriptions
    print("\n2. Confirming subscriptions...")
    cursor = manager.conn.cursor()
    for sub_id, email in subscriber_ids:
        cursor.execute(
            "SELECT confirmation_token FROM confirmations WHERE subscriber_id = ?",
            (sub_id,)
        )
        result = cursor.fetchone()
        if result:
            token = result[0]
            success, msg = manager.confirm_subscription(token)
            print(f"  {email}: {msg}")

    # 3. Create segments
    print("\n3. Creating segments...")
    segments = [
        ("High Engagement", "high_engagement", {"min_opens": 5}),
        ("Free Subscribers", "free", {"status": "active"}),
    ]

    for name, seg_type, criteria in segments:
        success, msg, seg_id = manager.create_segment(name, seg_type, criteria)
        print(f"  {name}: {msg}")

    # 4. Create campaign
    print("\n4. Creating campaign...")
    success, msg, campaign_id = manager.create_campaign(
        "Weekly Newsletter",
        "Your weekly profit engine update"
    )
    print(f"  {msg}")

    # 5. Track engagement
    print("\n5. Tracking email engagement...")
    if campaign_id and subscriber_ids:
        email = subscriber_ids[0][1]
        success, msg = manager.track_open(email, campaign_id, user_agent="Mozilla/5.0")
        print(f"  Open: {msg}")

        success, msg = manager.track_click(
            email,
            campaign_id,
            "https://alreadyherellc.com/article",
            user_agent="Mozilla/5.0"
        )
        print(f"  Click: {msg}")

    # 6. Get active subscribers
    print("\n6. Fetching active subscribers...")
    active = manager.get_active_subscribers()
    print(f"  Found {len(active)} active subscribers")

    # 7. Get engagement metrics
    print("\n7. Engagement metrics...")
    metrics = manager.get_engagement_metrics()
    print(f"  Total: {metrics.get('total', 0)}")
    print(f"  Active: {metrics.get('active', 0)}")
    print(f"  Avg opens: {metrics.get('avg_opens', 0):.1f}")
    print(f"  Avg clicks: {metrics.get('avg_clicks', 0):.1f}")

    # 8. Export subscribers
    print("\n8. Exporting subscribers...")
    json_export = manager.export_subscribers(export_format="json")
    if json_export:
        data = json.loads(json_export)
        print(f"  Exported {len(data)} subscribers")

    # 9. Lead magnet
    print("\n9. Adding lead magnet...")
    success, msg, magnet_id = manager.add_lead_magnet(
        "Passive Income Guide",
        "Free guide to generating passive income",
        "https://cdn.alreadyherellc.com/ebook-passive-income.pdf"
    )
    print(f"  {msg}")

    if magnet_id and subscriber_ids:
        success, msg = manager.track_magnet_download(
            magnet_id,
            subscriber_id=subscriber_ids[0][0]
        )
        print(f"  Download tracked: {msg}")

    # 10. Referral system
    print("\n10. Testing referral system...")
    if subscriber_ids:
        success, msg, ref_token = manager.create_referral(
            subscriber_ids[0][0],
            "newuser@example.com"
        )
        print(f"  Referral created: {msg}")

    print("\n=== Demo Complete ===\n")
    manager.close()


if __name__ == "__main__":
    demo()

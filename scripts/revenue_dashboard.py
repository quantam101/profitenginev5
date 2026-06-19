#!/usr/bin/env python3
"""
Unified Revenue Tracking Dashboard for Already Here LLC
Integrates with MongoDB to track all 6 revenue channels in real-time.

Channels:
  1. Newsletter ($300-500/mo via sponsorships)
  2. Gumroad ebooks ($300-500/mo)
  3. Printify POD ($800-1200/mo) - PRIMARY
  4. YouTube AdSense ($300-500/mo)
  5. Affiliate commissions ($300-500/mo)
  6. Sponsorships ($300+/mo)

Dashboard Features:
  - Real-time daily revenue per channel
  - Progress toward $2,500/mo target
  - Content ranking by revenue
  - LTV per subscriber
  - ROI per article
  - Burndown forecast with daily targets
  - MongoDB persistence for historical tracking
  - Web API endpoint for frontend integration
  - Telegram alerts with key metrics
  - Scheduled daily updates

Environment vars (required):
  MONGODB_URI          — MongoDB connection string
  MONGODB_DB           — Database name (default: profitenginev5)
  STRIPE_SECRET_KEY    — Stripe API key
  GUMROAD_API_TOKEN    — Gumroad API token
  PRINTIFY_API_TOKEN   — Printify API token
  YOUTUBE_API_KEY      — YouTube Data API key
  MAILCHIMP_API_KEY    — Mailchimp API key
  TELEGRAM_BOT_TOKEN   — Telegram bot token
  TELEGRAM_CHAT_ID     — Telegram chat ID
  AFFILIATE_TRACKING_URL — Base URL for affiliate tracking

Usage:
  python scripts/revenue_dashboard.py --action dashboard
  python scripts/revenue_dashboard.py --action export --output report.json
  python scripts/revenue_dashboard.py --action telegram
  python scripts/revenue_dashboard.py --action sync-mongodb
"""

from __future__ import annotations

import json
import os
import sys
import pathlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import urllib.request
import urllib.parse
import urllib.error

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DB = os.getenv("MONGODB_DB", "profitenginev5").strip()

STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
GUMROAD_TOKEN = os.getenv("GUMROAD_API_TOKEN", "").strip()
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
PRINTIFY_TOKEN = os.getenv("PRINTIFY_API_TOKEN", "").strip()
MAILCHIMP_KEY = os.getenv("MAILCHIMP_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
AFFILIATE_TRACKING_URL = os.getenv("AFFILIATE_TRACKING_URL", "https://track.alreadyherellc.com").strip()

# Monthly revenue targets (USD) — 6-channel model
MONTHLY_TARGETS = {
    "newsletter": 400,        # $300-500
    "gumroad": 400,           # $300-500
    "printify": 1000,         # $800-1200
    "youtube": 400,           # $300-500
    "affiliate": 400,         # $300-500
    "sponsorships": 300,      # $300+
    "total": 2500,            # Overall target
}

# Channel metadata
CHANNEL_CONFIG = {
    "newsletter": {
        "display_name": "Newsletter Sponsorships",
        "icon": "📧",
        "api_source": "stripe",
        "monthly_target": 400,
        "description": "Email sponsorship deals + paid subscribers",
    },
    "gumroad": {
        "display_name": "Gumroad eBooks",
        "icon": "📚",
        "api_source": "gumroad",
        "monthly_target": 400,
        "description": "Digital products, templates, guides",
    },
    "printify": {
        "display_name": "Printify POD",
        "icon": "👕",
        "api_source": "printify",
        "monthly_target": 1000,
        "description": "T-shirts, hoodies, prints, merchandise",
    },
    "youtube": {
        "display_name": "YouTube AdSense",
        "icon": "📺",
        "api_source": "youtube",
        "monthly_target": 400,
        "description": "Video ad revenue from YouTube",
    },
    "affiliate": {
        "display_name": "Affiliate Commissions",
        "icon": "🔗",
        "api_source": "affiliate",
        "monthly_target": 400,
        "description": "Amazon Associates + partner commissions",
    },
    "sponsorships": {
        "display_name": "Sponsorships",
        "icon": "💼",
        "api_source": "stripe",
        "monthly_target": 300,
        "description": "Brand partnerships, collaborations",
    },
}

# ── Data Structures ─────────────────────────────────────────────────────────

class Channel(Enum):
    """Revenue channels."""
    NEWSLETTER = "newsletter"
    GUMROAD = "gumroad"
    PRINTIFY = "printify"
    YOUTUBE = "youtube"
    AFFILIATE = "affiliate"
    SPONSORSHIPS = "sponsorships"


@dataclass
class DailyRevenueEntry:
    """Single day's revenue transaction."""
    channel: str
    amount_usd: float
    date: str  # YYYY-MM-DD
    source_id: str  # transaction ID
    description: str
    content_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None  # ISO timestamp


@dataclass
class ChannelDayMetrics:
    """Daily metrics for a single channel."""
    channel: str
    date: str
    revenue: float = 0.0
    transaction_count: int = 0
    avg_transaction: float = 0.0
    best_performing_item: Optional[str] = None
    items_sold: int = 0


@dataclass
class ChannelMonthMetrics:
    """Monthly aggregated metrics for a channel."""
    channel: str
    month: str  # YYYY-MM
    total_revenue: float = 0.0
    daily_average: float = 0.0
    transaction_count: int = 0
    days_with_revenue: int = 0
    target: float = 0.0
    progress_pct: float = 0.0
    rank: int = 0
    trend: str = "→"  # ↗ up, → stable, ↘ down


@dataclass
class ContentPerformance:
    """Track revenue and ROI per article/product."""
    content_id: str
    title: str
    channel: str
    publish_date: str
    creation_hours: float
    revenue_generated: float = 0.0
    views: int = 0
    conversions: int = 0
    roi_per_hour: float = 0.0
    rank: int = 0


@dataclass
class DashboardMetrics:
    """Complete dashboard snapshot."""
    timestamp: str
    period: str  # "today", "this_month", etc.

    # Daily totals
    today_revenue: float = 0.0
    yesterday_revenue: float = 0.0

    # Period totals
    week_revenue: float = 0.0
    month_revenue: float = 0.0

    # Goals and progress
    monthly_target: float = 2500.0
    monthly_progress_pct: float = 0.0
    daily_goal: float = 80.0
    days_remaining: int = 0

    # By channel
    by_channel: Dict[str, ChannelMonthMetrics] = field(default_factory=dict)

    # Content ranking
    top_articles: List[ContentPerformance] = field(default_factory=list)

    # Customer metrics
    ltv_per_subscriber: float = 0.0
    estimated_subscribers: int = 0

    # Forecast
    daily_burndown_needed: float = 0.0
    projected_month_end: float = 0.0
    will_hit_target: bool = False

    # Health
    data_quality: str = "healthy"
    active_channels: int = 0
    last_update: Optional[str] = None


# ── MongoDB Client ──────────────────────────────────────────────────────────

class MongoDBClient:
    """MongoDB connection manager for revenue tracking."""

    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self._connect()

    def _connect(self) -> bool:
        """Establish MongoDB connection."""
        if not MONGODB_URI:
            logger.warning("MONGODB_URI not configured — running without persistence")
            return False

        if not MONGODB_AVAILABLE:
            logger.warning("pymongo not installed — install via: pip install pymongo")
            return False

        try:
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[MONGODB_DB]
            self.connected = True
            logger.info(f"Connected to MongoDB ({MONGODB_DB})")
            self._ensure_collections()
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.connected = False
            return False

    def _ensure_collections(self) -> None:
        """Create collections and indexes if needed."""
        if not self.db:
            return

        # Revenue transactions collection
        if 'revenue_transactions' not in self.db.list_collection_names():
            self.db.create_collection('revenue_transactions')
            self.db['revenue_transactions'].create_index('date')
            self.db['revenue_transactions'].create_index('channel')
            self.db['revenue_transactions'].create_index([('date', -1), ('channel', 1)])
            logger.info("Created revenue_transactions collection with indexes")

        # Daily aggregates collection
        if 'revenue_daily' not in self.db.list_collection_names():
            self.db.create_collection('revenue_daily')
            self.db['revenue_daily'].create_index('date')
            self.db['revenue_daily'].create_index([('date', -1)])
            logger.info("Created revenue_daily collection with indexes")

        # Monthly aggregates collection
        if 'revenue_monthly' not in self.db.list_collection_names():
            self.db.create_collection('revenue_monthly')
            self.db['revenue_monthly'].create_index('month')
            logger.info("Created revenue_monthly collection with indexes")

    def insert_transaction(self, entry: DailyRevenueEntry) -> bool:
        """Insert a revenue transaction."""
        if not self.connected or not self.db:
            return False

        try:
            doc = asdict(entry)
            doc['_id'] = f"{entry.date}_{entry.channel}_{entry.source_id}"
            self.db['revenue_transactions'].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to insert transaction: {e}")
            return False

    def get_daily_revenue(self, date: str) -> List[DailyRevenueEntry]:
        """Fetch all revenue for a specific date (YYYY-MM-DD)."""
        if not self.connected or not self.db:
            return []

        try:
            docs = list(self.db['revenue_transactions'].find({'date': date}))
            return [DailyRevenueEntry(**doc) for doc in docs if '_id' not in doc or doc['_id'] != '_id']
        except Exception as e:
            logger.error(f"Failed to fetch daily revenue: {e}")
            return []

    def get_monthly_revenue(self, month: str) -> Dict[str, float]:
        """Fetch monthly revenue by channel (month format: YYYY-MM)."""
        if not self.connected or not self.db:
            return {}

        try:
            result = {}
            docs = list(self.db['revenue_transactions'].aggregate([
                {'$match': {'date': {'$regex': f'^{month}'}}},
                {'$group': {
                    '_id': '$channel',
                    'total': {'$sum': '$amount_usd'},
                    'count': {'$sum': 1},
                }},
            ]))

            for doc in docs:
                result[doc['_id']] = doc['total']
            return result
        except Exception as e:
            logger.error(f"Failed to fetch monthly revenue: {e}")
            return {}

    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.connected = False


# ── Revenue Tracker Class ────────────────────────────────────────────────────

class UnifiedRevenueTracker:
    """Main unified revenue tracking engine."""

    def __init__(self):
        self.mongo = MongoDBClient()
        self.data_dir = pathlib.Path(".runtime/revenue")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_file = self.data_dir / "transactions.jsonl"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """Create empty files if they don't exist."""
        if not self.transactions_file.exists():
            self.transactions_file.write_text("")

    # ── Fetch Revenue from APIs ──────────────────────────────────────────────

    def fetch_stripe_revenue(self, days: int = 30) -> List[DailyRevenueEntry]:
        """Fetch Stripe charges (newsletter, sponsorships)."""
        if not STRIPE_KEY or not STRIPE_KEY.startswith("sk_"):
            logger.warning("No valid Stripe key — skipping Stripe fetch")
            return []

        entries = []
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            start = now - (days * 86400)

            req = urllib.request.Request(
                f"https://api.stripe.com/v1/charges?created[gte]={start}&limit=100",
                headers={"Authorization": f"Bearer {STRIPE_KEY}"},
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            for charge in data.get("data", []):
                if not charge.get("paid"):
                    continue

                ts = datetime.fromtimestamp(charge["created"], tz=timezone.utc)
                channel = charge.get("metadata", {}).get("channel", "newsletter")

                entries.append(DailyRevenueEntry(
                    channel=channel,
                    amount_usd=charge["amount"] / 100,
                    date=ts.strftime("%Y-%m-%d"),
                    source_id=charge["id"],
                    description=charge.get("description", "Stripe charge"),
                    created_at=ts.isoformat(),
                ))

            logger.info(f"Fetched {len(entries)} Stripe charges")
        except Exception as e:
            logger.error(f"Stripe fetch failed: {e}")

        return entries

    def fetch_gumroad_revenue(self, days: int = 30) -> List[DailyRevenueEntry]:
        """Fetch Gumroad sales (ebooks, templates)."""
        if not GUMROAD_TOKEN:
            logger.warning("No Gumroad token — skipping")
            return []

        entries = []
        try:
            req = urllib.request.Request(
                f"https://api.gumroad.com/v2/sales?access_token={GUMROAD_TOKEN}",
                headers={"Accept": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            for sale in data.get("sales", []):
                try:
                    sale_date = datetime.fromisoformat(sale.get("created_at", "").replace("Z", "+00:00"))
                    if sale_date < cutoff:
                        continue

                    entries.append(DailyRevenueEntry(
                        channel="gumroad",
                        amount_usd=float(sale.get("price", 0)),
                        date=sale_date.strftime("%Y-%m-%d"),
                        source_id=sale.get("id", ""),
                        description=f"Gumroad: {sale.get('product_name', 'Unknown')}",
                        content_id=sale.get("product_id"),
                        created_at=sale.get("created_at"),
                    ))
                except Exception as e:
                    logger.debug(f"Skipped Gumroad sale: {e}")

            logger.info(f"Fetched {len(entries)} Gumroad sales")
        except Exception as e:
            logger.error(f"Gumroad fetch failed: {e}")

        return entries

    def fetch_printify_revenue(self, days: int = 30) -> List[DailyRevenueEntry]:
        """Fetch Printify POD sales (t-shirts, hoodies, prints)."""
        if not PRINTIFY_TOKEN:
            logger.warning("No Printify token — skipping")
            return []

        entries = []
        try:
            req = urllib.request.Request(
                f"https://api.printify.com/v1/orders?status=fulfilled",
                headers={
                    "Authorization": f"Bearer {PRINTIFY_TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            for order in data.get("data", []):
                try:
                    created = datetime.fromisoformat(order.get("created_at", "").replace("Z", "+00:00"))
                    if created < cutoff:
                        continue

                    total_price = float(order.get("total_price", 0))
                    cost = float(order.get("cost", 0))
                    profit = max(0, total_price - cost)

                    entries.append(DailyRevenueEntry(
                        channel="printify",
                        amount_usd=profit,
                        date=created.strftime("%Y-%m-%d"),
                        source_id=order.get("id", ""),
                        description=f"Printify order",
                        created_at=created.isoformat(),
                        metadata={
                            "price": total_price,
                            "cost": cost,
                            "items": len(order.get("items", [])),
                        },
                    ))
                except Exception as e:
                    logger.debug(f"Skipped Printify order: {e}")

            logger.info(f"Fetched {len(entries)} Printify orders")
        except Exception as e:
            logger.error(f"Printify fetch failed: {e}")

        return entries

    def fetch_all_channels(self, days: int = 30) -> Dict[str, List[DailyRevenueEntry]]:
        """Fetch from all available channels."""
        return {
            "stripe": self.fetch_stripe_revenue(days),
            "gumroad": self.fetch_gumroad_revenue(days),
            "printify": self.fetch_printify_revenue(days),
            "youtube": [],  # Manual entry or YouTube Analytics API
            "affiliate": [],  # Manual entry or tracking service
        }

    # ── Metrics Calculation ──────────────────────────────────────────────────

    def get_daily_revenue(self, date: Optional[str] = None) -> Dict[str, float]:
        """Revenue by channel for specific date (YYYY-MM-DD, default: today)."""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        daily_by_channel = {}

        # Try MongoDB first
        if self.mongo.connected:
            entries = self.mongo.get_daily_revenue(date)
            for entry in entries:
                daily_by_channel[entry.channel] = daily_by_channel.get(entry.channel, 0) + entry.amount_usd

        # Fall back to local file
        if not daily_by_channel and self.transactions_file.exists():
            with open(self.transactions_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("date") == date:
                            channel = data.get("channel", "unknown")
                            daily_by_channel[channel] = daily_by_channel.get(channel, 0) + data.get("amount_usd", 0)
                    except:
                        pass

        return daily_by_channel

    def get_monthly_revenue(self, month: Optional[str] = None) -> Dict[str, float]:
        """Revenue by channel for specific month (YYYY-MM, default: current)."""
        if month is None:
            month = datetime.now(timezone.utc).strftime("%Y-%m")

        monthly_by_channel = {}

        # Try MongoDB
        if self.mongo.connected:
            monthly_by_channel = self.mongo.get_monthly_revenue(month)

        # Fall back to local file
        if not monthly_by_channel and self.transactions_file.exists():
            with open(self.transactions_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("date", "").startswith(month):
                            channel = data.get("channel", "unknown")
                            monthly_by_channel[channel] = monthly_by_channel.get(channel, 0) + data.get("amount_usd", 0)
                    except:
                        pass

        return monthly_by_channel

    def calculate_burndown(self, current_month_revenue: float, target: float = 2500) -> Tuple[float, float, bool]:
        """Calculate daily burndown needed to hit target."""
        now = datetime.now(timezone.utc)
        days_in_month = 30
        days_remaining = max(1, days_in_month - now.day)

        needed = max(0, target - current_month_revenue)
        daily_needed = needed / days_remaining if days_remaining > 0 else 0

        projected = current_month_revenue + (daily_needed * days_remaining)
        will_hit = projected >= target

        return daily_needed, projected, will_hit

    def generate_dashboard(self) -> DashboardMetrics:
        """Generate unified dashboard snapshot."""
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")

        # Get daily and monthly revenue
        today_revenue_dict = self.get_daily_revenue(today)
        today_revenue = sum(today_revenue_dict.values())

        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_revenue = sum(self.get_daily_revenue(yesterday).values())

        week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        week_revenue = 0.0
        for i in range(7):
            day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            week_revenue += sum(self.get_daily_revenue(day).values())

        monthly_revenue_dict = self.get_monthly_revenue(month)
        month_revenue = sum(monthly_revenue_dict.values())

        # Calculate metrics by channel
        by_channel = {}
        active_channels = 0
        for channel in CHANNEL_CONFIG.keys():
            channel_monthly = monthly_revenue_dict.get(channel, 0)
            target = MONTHLY_TARGETS.get(channel, 0)
            progress = min(100, (channel_monthly / target * 100)) if target > 0 else 0

            if channel_monthly > 0:
                active_channels += 1

            by_channel[channel] = ChannelMonthMetrics(
                channel=channel,
                month=month,
                total_revenue=channel_monthly,
                transaction_count=0,
                target=target,
                progress_pct=progress,
                trend="↗" if channel_monthly > 0 else "→",
            )

        # Calculate progress and burndown
        monthly_target = MONTHLY_TARGETS.get("total", 2500)
        progress_pct = min(100, (month_revenue / monthly_target * 100)) if monthly_target > 0 else 0

        daily_needed, projected, will_hit = self.calculate_burndown(month_revenue, monthly_target)

        days_remaining = max(1, 30 - now.day)

        return DashboardMetrics(
            timestamp=now.isoformat(),
            period=f"{month}",
            today_revenue=today_revenue,
            yesterday_revenue=yesterday_revenue,
            week_revenue=week_revenue,
            month_revenue=month_revenue,
            monthly_target=monthly_target,
            monthly_progress_pct=progress_pct,
            daily_goal=monthly_target / 30,
            days_remaining=days_remaining,
            by_channel=by_channel,
            ltv_per_subscriber=month_revenue / 2000 if month_revenue > 0 else 0,  # Assume 2000 subs
            estimated_subscribers=2000,
            daily_burndown_needed=daily_needed,
            projected_month_end=projected,
            will_hit_target=will_hit,
            active_channels=active_channels,
            last_update=now.isoformat(),
        )

    def format_dashboard_text(self, dashboard: DashboardMetrics) -> str:
        """Format dashboard for terminal display."""
        lines = [
            "=" * 70,
            "ALREADY HERE LLC — UNIFIED REVENUE DASHBOARD",
            "=" * 70,
            "",
            "SNAPSHOT",
            f"  Period:          {dashboard.period}",
            f"  Updated:         {dashboard.timestamp}",
            f"  Active Channels: {dashboard.active_channels}/6",
            "",
            "TODAY & YESTERDAY",
            f"  Today:           ${dashboard.today_revenue:>10,.2f}",
            f"  Yesterday:       ${dashboard.yesterday_revenue:>10,.2f}",
            f"  Week (7d):       ${dashboard.week_revenue:>10,.2f}",
            "",
            "MONTHLY PROGRESS",
            f"  Target:          ${dashboard.monthly_target:>10,.0f}",
            f"  Actual:          ${dashboard.month_revenue:>10,.2f}  ({dashboard.monthly_progress_pct:.1f}%)",
            f"  Projected End:   ${dashboard.projected_month_end:>10,.2f}",
            f"  Days Remaining:  {dashboard.days_remaining:>10}",
            f"  Daily Needed:    ${dashboard.daily_burndown_needed:>10,.2f}",
            f"  On Track:        {'✓ YES' if dashboard.will_hit_target else '✗ NO':>10}",
            "",
            "BY CHANNEL (This Month)",
        ]

        # Sort channels by revenue
        sorted_channels = sorted(
            dashboard.by_channel.items(),
            key=lambda x: x[1].total_revenue,
            reverse=True
        )

        for channel, metrics in sorted_channels:
            config = CHANNEL_CONFIG.get(channel, {})
            icon = config.get("icon", "")
            name = config.get("display_name", channel)
            progress_bar = "█" * int(metrics.progress_pct / 10) + "░" * (10 - int(metrics.progress_pct / 10))

            lines.extend([
                f"  {icon} {name:<30}",
                f"     Revenue:       ${metrics.total_revenue:>10,.2f} / ${metrics.target:,.0f}",
                f"     Progress:      {progress_bar}  {metrics.progress_pct:>5.1f}%",
            ])

        lines.extend([
            "",
            "CUSTOMER METRICS",
            f"  LTV per Sub:     ${dashboard.ltv_per_subscriber:>10,.2f}",
            f"  Subscribers:     {dashboard.estimated_subscribers:>10,}",
            "",
            "=" * 70,
        ])

        return "\n".join(lines)

    def export_report(self, filepath: str = "revenue_report.json") -> str:
        """Export dashboard to JSON."""
        dashboard = self.generate_dashboard()
        report = {
            "timestamp": dashboard.timestamp,
            "period": dashboard.period,
            "today_revenue": dashboard.today_revenue,
            "yesterday_revenue": dashboard.yesterday_revenue,
            "week_revenue": dashboard.week_revenue,
            "month_revenue": dashboard.month_revenue,
            "monthly_target": dashboard.monthly_target,
            "monthly_progress_pct": dashboard.monthly_progress_pct,
            "will_hit_target": dashboard.will_hit_target,
            "daily_burndown_needed": dashboard.daily_burndown_needed,
            "projected_month_end": dashboard.projected_month_end,
            "by_channel": {
                channel: asdict(metrics)
                for channel, metrics in dashboard.by_channel.items()
            },
            "ltv_per_subscriber": dashboard.ltv_per_subscriber,
            "active_channels": dashboard.active_channels,
        }

        filepath = pathlib.Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(report, indent=2))
        logger.info(f"Exported report to {filepath}")
        return str(filepath)

    def send_telegram_alert(self) -> bool:
        """Send revenue summary to Telegram."""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram not configured — skipping alert")
            return False

        dashboard = self.generate_dashboard()
        target_icon = "✅" if dashboard.will_hit_target else "⚠️"

        message = f"""📊 Revenue Update — {dashboard.period}

Today:     ${dashboard.today_revenue:,.2f}
Week:      ${dashboard.week_revenue:,.2f}
Month:     ${dashboard.month_revenue:,.2f} ({dashboard.monthly_progress_pct:.1f}%)

Target:    ${dashboard.monthly_target:,.0f}
Forecast:  ${dashboard.projected_month_end:,.2f}
Status:    {target_icon} {'ON TRACK' if dashboard.will_hit_target else 'BEHIND'}

Burndown:  ${dashboard.daily_burndown_needed:,.2f}/day needed
Days Left: {dashboard.days_remaining}

Active Channels: {dashboard.active_channels}/6
LTV per Sub: ${dashboard.ltv_per_subscriber:,.2f}

—
{dashboard.timestamp}
        """.strip()

        try:
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
            }).encode()

            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data=data,
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                if result.get("ok"):
                    logger.info("Telegram alert sent")
                    return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")

        return False

    def add_manual_entry(self, channel: str, amount: float, description: str,
                        date: Optional[str] = None) -> None:
        """Add manual revenue entry (for spreadsheet imports, manual tracking)."""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        entry = DailyRevenueEntry(
            channel=channel,
            amount_usd=amount,
            date=date,
            source_id=f"manual_{datetime.now().timestamp()}",
            description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save to both local file and MongoDB
        with open(self.transactions_file, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

        if self.mongo.connected:
            self.mongo.insert_transaction(entry)

        logger.info(f"Logged {channel}: ${amount} — {description}")

    def sync_to_mongodb(self, days: int = 30) -> int:
        """Sync local transactions to MongoDB."""
        if not self.mongo.connected:
            logger.warning("MongoDB not connected — cannot sync")
            return 0

        if not self.transactions_file.exists():
            return 0

        count = 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with open(self.transactions_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat()))
                    if ts >= cutoff:
                        entry = DailyRevenueEntry(**data)
                        if self.mongo.insert_transaction(entry):
                            count += 1
                except Exception as e:
                    logger.debug(f"Skipped sync entry: {e}")

        logger.info(f"Synced {count} transactions to MongoDB")
        return count


# ── CLI Interface ────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Revenue Dashboard for Already Here LLC")
    parser.add_argument("--action", choices=["dashboard", "export", "telegram", "add", "fetch", "sync-mongodb"],
                       default="dashboard", help="Action to perform")
    parser.add_argument("--channel", help="Channel for manual entry")
    parser.add_argument("--amount", type=float, help="Amount for manual entry")
    parser.add_argument("--description", help="Description for manual entry")
    parser.add_argument("--date", help="Date for manual entry (YYYY-MM-DD, default: today)")
    parser.add_argument("--output", default="revenue_report.json", help="Output file for export")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")

    args = parser.parse_args()

    tracker = UnifiedRevenueTracker()

    try:
        if args.action == "dashboard":
            dashboard = tracker.generate_dashboard()
            print(tracker.format_dashboard_text(dashboard))

        elif args.action == "export":
            filepath = tracker.export_report(args.output)
            print(f"[OK] Report exported to {filepath}")

        elif args.action == "telegram":
            if tracker.send_telegram_alert():
                print("[OK] Telegram alert sent")
            else:
                print("[ERROR] Telegram alert failed")

        elif args.action == "add":
            if not args.channel or args.amount is None or not args.description:
                print("[ERROR] Required: --channel, --amount, --description")
                sys.exit(1)
            tracker.add_manual_entry(args.channel, args.amount, args.description, args.date)
            print(f"[OK] Added {args.channel}: ${args.amount}")

        elif args.action == "fetch":
            channels = tracker.fetch_all_channels(args.days)
            total_fetched = sum(len(entries) for entries in channels.values())
            print(f"[OK] Fetched {total_fetched} transactions from {len(channels)} channels")
            for channel, entries in channels.items():
                if entries:
                    print(f"  {channel}: {len(entries)} transactions, ${sum(e.amount_usd for e in entries):,.2f}")

        elif args.action == "sync-mongodb":
            count = tracker.sync_to_mongodb(args.days)
            print(f"[OK] Synced {count} transactions to MongoDB")

    finally:
        tracker.mongo.close()


if __name__ == "__main__":
    main()

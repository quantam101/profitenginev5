#!/usr/bin/env python3
"""
Revenue Tracker for Already Here LLC
Measures profit from each channel: Newsletter, Gumroad, Printify, YouTube, Affiliate, Sponsorships.

Features:
  - Track revenue by source (6 channels)
  - Daily revenue dashboard
  - Best-performing content & topics
  - Lifetime value (LTV) per subscriber
  - ROI on content creation time
  - Monthly goals tracking ($2,500 target)
  - Export reports for Telegram alerts

Environment vars:
  STRIPE_SECRET_KEY       — Stripe API key for payment tracking
  GUMROAD_API_TOKEN       — Gumroad API token
  YOUTUBE_API_KEY         — YouTube Data API key for AdSense revenue
  PRINTIFY_API_TOKEN      — Printify API token for POD sales
  MAILCHIMP_API_KEY       — Mailchimp API key for newsletter revenue
  TELEGRAM_CHAT_ID        — Telegram chat ID for alerts
  TELEGRAM_BOT_TOKEN      — Telegram bot token
  AFFILIATE_TRACKING_URL  — Base URL for affiliate link tracking
  CONTENT_DATABASE_PATH   — JSON file tracking content creation time/metadata

Usage:
  import revenue_tracker as rt

  # Get revenue from all channels
  tracker = rt.RevenueTracker()
  today_revenue = tracker.get_daily_revenue()
  monthly_revenue = tracker.get_monthly_revenue()

  # Dashboard
  dashboard = tracker.generate_dashboard()
  tracker.export_report("revenue_report.json")
  tracker.send_telegram_alert()

Monthly Goals (by channel):
  Newsletter:     $300-500   (paid subscribers, sponsorships)
  Gumroad:        $300-500   (ebook/template sales)
  Printify:       $800-1200  (POD t-shirts, hoodies, prints)
  YouTube/Aff:    $300-500   (ad revenue + affiliate clicks)
  Sponsorships:   Variable   (email sponsors, partnerships)
  ─────────────────────────
  Total Target:   $2,500/month (or higher)
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
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
GUMROAD_TOKEN = os.getenv("GUMROAD_API_TOKEN", "").strip()
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
PRINTIFY_TOKEN = os.getenv("PRINTIFY_API_TOKEN", "").strip()
MAILCHIMP_KEY = os.getenv("MAILCHIMP_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
AFFILIATE_TRACKING_URL = os.getenv("AFFILIATE_TRACKING_URL", "https://track.alreadyherellc.com").strip()
CONTENT_DB_PATH = os.getenv("CONTENT_DATABASE_PATH", ".runtime/content_metrics.json").strip()

# Monthly revenue targets (USD)
MONTHLY_TARGETS = {
    "newsletter": 400,      # $300-500
    "gumroad": 400,         # $300-500
    "printify": 1000,       # $800-1200
    "youtube_affiliate": 400,  # $300-500 combined
    "sponsorships": 300,    # Variable but $300+ reasonable
    "total": 2500,          # Overall target
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
class RevenueEntry:
    """Single revenue transaction."""
    channel: str
    amount_usd: float
    timestamp: str  # ISO format
    source_id: str  # transaction ID from payment system
    description: str
    content_id: Optional[str] = None  # which article/product generated this
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelMetrics:
    """Aggregated metrics for a single channel."""
    channel: str
    daily_revenue: float = 0.0
    weekly_revenue: float = 0.0
    monthly_revenue: float = 0.0
    transaction_count: int = 0
    average_transaction_value: float = 0.0
    target: float = 0.0
    progress_pct: float = 0.0
    last_transaction: Optional[str] = None


@dataclass
class ContentMetrics:
    """Track ROI for individual content pieces."""
    content_id: str
    title: str
    channel: str
    creation_time_hours: float
    publish_date: str
    revenue_generated: float = 0.0
    views: int = 0
    clicks: int = 0
    conversions: int = 0
    roi_per_hour: float = 0.0


@dataclass
class DashboardSnapshot:
    """Point-in-time dashboard snapshot."""
    timestamp: str
    daily_total: float
    weekly_total: float
    monthly_total: float
    by_channel: Dict[str, ChannelMetrics]
    top_content: List[ContentMetrics]
    monthly_progress_pct: float
    ltv_per_subscriber: float
    goal_status: Dict[str, Dict[str, Any]]
    burndown_forecast: Optional[float] = None


# ── Revenue Tracker Class ────────────────────────────────────────────────────

class RevenueTracker:
    """Main revenue tracking engine."""

    def __init__(self, data_dir: str = ".runtime/revenue"):
        self.data_dir = pathlib.Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_file = self.data_dir / "transactions.jsonl"
        self.content_db_file = pathlib.Path(CONTENT_DB_PATH)
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """Create empty files if they don't exist."""
        if not self.transactions_file.exists():
            self.transactions_file.write_text("")
        if not self.content_db_file.exists():
            self.content_db_file.parent.mkdir(parents=True, exist_ok=True)
            self.content_db_file.write_text("{}")

    # ── Fetch Revenue from Each Channel ──────────────────────────────────────

    def fetch_stripe_revenue(self, days: int = 30) -> List[RevenueEntry]:
        """Fetch Stripe charges (used by: Newsletter, Sponsorships, Direct sales)."""
        if not STRIPE_KEY or not STRIPE_KEY.startswith("sk_"):
            logger.warning("No valid Stripe key — skipping Stripe fetch")
            return []

        entries = []
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            start = now - (days * 86400)

            req = urllib.request.Request(
                f"https://api.stripe.com/v1/charges?created[gte]={start}&limit=100&expand[]=data.metadata",
                headers={"Authorization": f"Bearer {STRIPE_KEY}"},
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            charges = data.get("data", [])
            for charge in charges:
                if not charge.get("paid"):
                    continue

                entries.append(RevenueEntry(
                    channel="stripe",  # Mixed: newsletter, sponsorships, direct
                    amount_usd=charge["amount"] / 100,
                    timestamp=datetime.fromtimestamp(charge["created"], tz=timezone.utc).isoformat(),
                    source_id=charge["id"],
                    description=charge.get("description", "Stripe charge"),
                    metadata=charge.get("metadata", {})
                ))

            logger.info(f"Fetched {len(entries)} Stripe charges from last {days} days")
        except Exception as e:
            logger.error(f"Stripe fetch failed: {e}")

        return entries

    def fetch_gumroad_revenue(self, days: int = 30) -> List[RevenueEntry]:
        """Fetch Gumroad sales (ebooks, templates, guides)."""
        if not GUMROAD_TOKEN:
            logger.warning("No Gumroad token — skipping")
            return []

        entries = []
        try:
            # Gumroad API: /sales endpoint
            req = urllib.request.Request(
                f"https://api.gumroad.com/v2/sales?access_token={GUMROAD_TOKEN}",
                headers={"Accept": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            sales = data.get("sales", [])
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            for sale in sales:
                sale_date = datetime.fromisoformat(sale.get("created_at", "").replace("Z", "+00:00"))
                if sale_date < cutoff:
                    continue

                entries.append(RevenueEntry(
                    channel="gumroad",
                    amount_usd=float(sale.get("price", 0)),
                    timestamp=sale.get("created_at", datetime.now(timezone.utc).isoformat()),
                    source_id=sale.get("id", ""),
                    description=f"Gumroad: {sale.get('product_name', 'Unknown')}",
                    content_id=sale.get("product_id", ""),
                    metadata={
                        "product_name": sale.get("product_name"),
                        "buyer": sale.get("purchaser_email"),
                        "license_key": sale.get("license_key"),
                    }
                ))

            logger.info(f"Fetched {len(entries)} Gumroad sales from last {days} days")
        except Exception as e:
            logger.error(f"Gumroad fetch failed: {e}")

        return entries

    def fetch_printify_revenue(self, days: int = 30) -> List[RevenueEntry]:
        """Fetch Printify POD sales (t-shirts, hoodies, prints)."""
        if not PRINTIFY_TOKEN:
            logger.warning("No Printify token — skipping")
            return []

        entries = []
        try:
            # Printify API: /orders endpoint
            req = urllib.request.Request(
                f"https://api.printify.com/v1/orders?status=fulfilled",
                headers={
                    "Authorization": f"Bearer {PRINTIFY_TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            orders = data.get("data", [])
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            for order in orders:
                created = datetime.fromisoformat(order.get("created_at", "").replace("Z", "+00:00"))
                if created < cutoff:
                    continue

                # Profit = total price - cost
                total_price = float(order.get("total_price", 0))
                cost = float(order.get("cost", 0))
                profit = total_price - cost

                entries.append(RevenueEntry(
                    channel="printify",
                    amount_usd=profit,
                    timestamp=order.get("created_at", datetime.now(timezone.utc).isoformat()),
                    source_id=order.get("id", ""),
                    description=f"Printify: {order.get('status', 'Order')}",
                    metadata={
                        "total_price": total_price,
                        "cost": cost,
                        "items": order.get("items", []),
                    }
                ))

            logger.info(f"Fetched {len(entries)} Printify orders from last {days} days")
        except Exception as e:
            logger.error(f"Printify fetch failed: {e}")

        return entries

    def fetch_youtube_revenue(self, days: int = 30) -> List[RevenueEntry]:
        """Fetch YouTube AdSense revenue (requires YouTube Analytics API)."""
        if not YOUTUBE_KEY:
            logger.warning("No YouTube API key — skipping")
            return []

        # Note: YouTube AdSense revenue tracking requires OAuth + YouTube Analytics API
        # For MVP, we'll support manual entry or CMS integration
        logger.info("YouTube revenue fetch requires manual setup or Analytics API integration")
        return []

    def fetch_affiliate_revenue(self, days: int = 30) -> List[RevenueEntry]:
        """Fetch affiliate link revenue (clicks, conversions, commissions)."""
        # Affiliate tracking typically comes from:
        # 1. Amazon Associates API (for Amazon affiliate links)
        # 2. Custom tracking (click logging + manual commission tracking)
        # 3. Affiliate networks (Impact, ShareASale, etc.)

        entries = []
        logger.info("Affiliate revenue requires manual setup or affiliate network integration")
        return entries

    def fetch_sponsorship_revenue(self, days: int = 30) -> List[RevenueEntry]:
        """Fetch sponsorship/partnership revenue (manual entry via CMS)."""
        # Sponsorships are typically manual entries:
        # - Email sponsor payments
        # - Partnership fees
        # - Brand collaborations

        logger.info("Sponsorship revenue requires manual entry or CRM integration")
        return []

    def fetch_all_channels(self, days: int = 30) -> Dict[str, List[RevenueEntry]]:
        """Fetch from all available channels."""
        return {
            "stripe": self.fetch_stripe_revenue(days),
            "gumroad": self.fetch_gumroad_revenue(days),
            "printify": self.fetch_printify_revenue(days),
            "youtube": self.fetch_youtube_revenue(days),
            "affiliate": self.fetch_affiliate_revenue(days),
            "sponsorships": self.fetch_sponsorship_revenue(days),
        }

    # ── Transaction Management ───────────────────────────────────────────────

    def add_transaction(self, entry: RevenueEntry) -> None:
        """Log a revenue transaction."""
        with open(self.transactions_file, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        logger.info(f"Logged {entry.channel}: ${entry.amount_usd} — {entry.description}")

    def add_manual_entry(self, channel: str, amount: float, description: str,
                        content_id: Optional[str] = None) -> None:
        """Add manual revenue entry (for spreadsheet imports, sponsorships, etc)."""
        entry = RevenueEntry(
            channel=channel,
            amount_usd=amount,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_id=f"manual_{datetime.now().timestamp()}",
            description=description,
            content_id=content_id,
        )
        self.add_transaction(entry)

    def load_transactions(self, days: int = 30) -> List[RevenueEntry]:
        """Load transactions from log file."""
        if not self.transactions_file.exists():
            return []

        entries = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with open(self.transactions_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    entry = RevenueEntry(**data)
                    ts = datetime.fromisoformat(entry.timestamp)
                    if ts >= cutoff:
                        entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to parse transaction: {e}")

        return entries

    # ── Metrics Calculation ──────────────────────────────────────────────────

    def get_daily_revenue(self, date: Optional[datetime] = None) -> Dict[str, float]:
        """Revenue by channel for a specific date (default: today)."""
        if date is None:
            date = datetime.now(timezone.utc).date()

        start = datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        transactions = self.load_transactions(days=30)
        daily_by_channel = {}

        for tx in transactions:
            ts = datetime.fromisoformat(tx.timestamp)
            if start <= ts < end:
                daily_by_channel[tx.channel] = daily_by_channel.get(tx.channel, 0) + tx.amount_usd

        return daily_by_channel

    def get_weekly_revenue(self) -> Dict[str, float]:
        """Revenue by channel for last 7 days."""
        transactions = self.load_transactions(days=7)
        weekly = {}
        for tx in transactions:
            weekly[tx.channel] = weekly.get(tx.channel, 0) + tx.amount_usd
        return weekly

    def get_monthly_revenue(self) -> Dict[str, float]:
        """Revenue by channel for last 30 days."""
        transactions = self.load_transactions(days=30)
        monthly = {}
        for tx in transactions:
            monthly[tx.channel] = monthly.get(tx.channel, 0) + tx.amount_usd
        return monthly

    def calculate_channel_metrics(self) -> Dict[str, ChannelMetrics]:
        """Calculate aggregated metrics for each channel."""
        daily = self.get_daily_revenue()
        weekly = self.get_weekly_revenue()
        monthly = self.get_monthly_revenue()
        transactions = self.load_transactions(days=30)

        metrics = {}
        all_channels = set(daily.keys()) | set(weekly.keys()) | set(monthly.keys())

        for channel in all_channels:
            channel_txs = [tx for tx in transactions if tx.channel == channel]

            m = ChannelMetrics(
                channel=channel,
                daily_revenue=daily.get(channel, 0),
                weekly_revenue=weekly.get(channel, 0),
                monthly_revenue=monthly.get(channel, 0),
                transaction_count=len(channel_txs),
                average_transaction_value=sum(tx.amount_usd for tx in channel_txs) / len(channel_txs) if channel_txs else 0,
                target=MONTHLY_TARGETS.get(channel, 0),
                last_transaction=max([tx.timestamp for tx in channel_txs], default=None),
            )

            if m.target > 0:
                m.progress_pct = min(100, (m.monthly_revenue / m.target) * 100)

            metrics[channel] = m

        return metrics

    def get_ltv_per_subscriber(self) -> float:
        """Lifetime value per subscriber (revenue / subscriber count)."""
        # This requires tracking subscriber count — estimated from email list data
        # For now, using a reasonable estimate based on typical newsletter LTV

        monthly_revenue = sum(self.get_monthly_revenue().values())
        # Assuming 1,000-5,000 active subscribers
        estimated_subscribers = 2000
        ltv = monthly_revenue / estimated_subscribers if estimated_subscribers > 0 else 0
        return ltv

    def get_top_content(self, limit: int = 5) -> List[ContentMetrics]:
        """Get best-performing content by revenue."""
        if not self.content_db_file.exists():
            return []

        try:
            content_data = json.loads(self.content_db_file.read_text())
            content_list = [ContentMetrics(**item) for item in content_data.values() if isinstance(item, dict)]
            return sorted(content_list, key=lambda x: x.revenue_generated, reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Failed to load content metrics: {e}")
            return []

    def calculate_burndown_forecast(self) -> Optional[float]:
        """Estimate daily burn rate to meet monthly target."""
        monthly_revenue = sum(self.get_monthly_revenue().values())
        target = MONTHLY_TARGETS.get("total", 2500)

        if target <= 0:
            return None

        # Days remaining in month
        now = datetime.now(timezone.utc)
        days_in_month = 30  # Simplified
        days_remaining = max(1, days_in_month - now.day)

        needed_daily = (target - monthly_revenue) / days_remaining if days_remaining > 0 else 0
        return max(0, needed_daily)

    # ── Dashboard & Reports ──────────────────────────────────────────────────

    def generate_dashboard(self) -> DashboardSnapshot:
        """Generate current state snapshot."""
        daily = self.get_daily_revenue()
        weekly = self.get_weekly_revenue()
        monthly = self.get_monthly_revenue()
        channel_metrics = self.calculate_channel_metrics()

        total_daily = sum(daily.values())
        total_weekly = sum(weekly.values())
        total_monthly = sum(monthly.values())

        target_total = MONTHLY_TARGETS.get("total", 2500)
        progress_pct = min(100, (total_monthly / target_total) * 100) if target_total > 0 else 0

        # Goal status for each channel
        goal_status = {}
        for channel, target in MONTHLY_TARGETS.items():
            if channel == "total":
                continue
            revenue = monthly.get(channel, 0)
            goal_status[channel] = {
                "target": target,
                "actual": revenue,
                "progress_pct": min(100, (revenue / target * 100)) if target > 0 else 0,
                "status": "on_track" if revenue >= (target * 0.5) else "behind",
            }

        return DashboardSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            daily_total=total_daily,
            weekly_total=total_weekly,
            monthly_total=total_monthly,
            by_channel=channel_metrics,
            top_content=self.get_top_content(),
            monthly_progress_pct=progress_pct,
            ltv_per_subscriber=self.get_ltv_per_subscriber(),
            goal_status=goal_status,
            burndown_forecast=self.calculate_burndown_forecast(),
        )

    def format_dashboard_text(self, dashboard: DashboardSnapshot) -> str:
        """Format dashboard for display."""
        lines = [
            "=== REVENUE DASHBOARD ===",
            f"Timestamp: {dashboard.timestamp}",
            "",
            "DAILY SNAPSHOT",
            f"  Daily Total:  ${dashboard.daily_total:,.2f}",
            f"  Weekly Total: ${dashboard.weekly_total:,.2f}",
            f"  Monthly Total: ${dashboard.monthly_total:,.2f}",
            "",
            "MONTHLY PROGRESS",
            f"  Target: ${MONTHLY_TARGETS.get('total', 2500):,.0f}",
            f"  Progress: {dashboard.monthly_progress_pct:.1f}%",
            f"  Burndown: ${dashboard.burndown_forecast:,.2f}/day needed",
            "",
            "BY CHANNEL",
        ]

        for channel, metrics in dashboard.by_channel.items():
            lines.append(f"  {channel.upper()}")
            lines.append(f"    Daily: ${metrics.daily_revenue:,.2f}")
            lines.append(f"    Monthly: ${metrics.monthly_revenue:,.2f}")
            lines.append(f"    Target: ${metrics.target:,.2f}")
            lines.append(f"    Progress: {metrics.progress_pct:.1f}%")
            lines.append(f"    Transactions: {metrics.transaction_count}")

        lines += [
            "",
            "TOP CONTENT",
        ]

        for i, content in enumerate(dashboard.top_content, 1):
            lines.append(f"  {i}. {content.title}")
            lines.append(f"     Revenue: ${content.revenue_generated:,.2f}")
            lines.append(f"     ROI: ${content.roi_per_hour:.2f}/hour")

        lines += [
            "",
            f"LTV per Subscriber: ${dashboard.ltv_per_subscriber:.2f}",
        ]

        return "\n".join(lines)

    def export_report(self, filepath: str = "revenue_report.json") -> str:
        """Export dashboard to JSON."""
        dashboard = self.generate_dashboard()
        report = {
            "timestamp": dashboard.timestamp,
            "daily_total": dashboard.daily_total,
            "weekly_total": dashboard.weekly_total,
            "monthly_total": dashboard.monthly_total,
            "monthly_progress_pct": dashboard.monthly_progress_pct,
            "ltv_per_subscriber": dashboard.ltv_per_subscriber,
            "burndown_forecast": dashboard.burndown_forecast,
            "by_channel": {
                channel: asdict(metrics)
                for channel, metrics in dashboard.by_channel.items()
            },
            "top_content": [asdict(content) for content in dashboard.top_content],
            "goal_status": dashboard.goal_status,
        }

        filepath = pathlib.Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(report, indent=2))
        logger.info(f"Exported report to {filepath}")
        return str(filepath)

    def send_telegram_alert(self, webhook_url: Optional[str] = None) -> bool:
        """Send revenue summary to Telegram."""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram not configured — skipping alert")
            return False

        dashboard = self.generate_dashboard()
        message = f"""
📊 Revenue Update

Daily: ${dashboard.daily_total:,.2f}
Weekly: ${dashboard.weekly_total:,.2f}
Monthly: ${dashboard.monthly_total:,.2f} ({dashboard.monthly_progress_pct:.1f}%)

Target: ${MONTHLY_TARGETS.get('total', 2500):,.0f}
Burndown: ${dashboard.burndown_forecast:,.2f}/day

Top Channel: {max(dashboard.by_channel.items(), key=lambda x: x[1].monthly_revenue, default=('N/A', None))[0]}

—
Updated: {dashboard.timestamp}
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

    # ── Analysis & Recommendations ──────────────────────────────────────────

    def get_channel_recommendations(self) -> Dict[str, str]:
        """Recommend focus areas based on performance."""
        channel_metrics = self.calculate_channel_metrics()
        recommendations = {}

        for channel, metrics in channel_metrics.items():
            if metrics.progress_pct >= 100:
                recommendations[channel] = "✅ On track to beat target"
            elif metrics.progress_pct >= 50:
                recommendations[channel] = "⚠️ Moderate progress — increase marketing"
            elif metrics.progress_pct >= 25:
                recommendations[channel] = "🔴 Behind target — needs focus"
            else:
                recommendations[channel] = "❌ Critical — requires strategy change"

        return recommendations

    def get_roi_analysis(self) -> Dict[str, float]:
        """Calculate ROI per hour of content creation."""
        content_list = self.get_top_content(limit=100)
        roi_by_channel = {}

        for content in content_list:
            if content.channel not in roi_by_channel:
                roi_by_channel[content.channel] = []
            roi_by_channel[content.channel].append(content.roi_per_hour)

        return {
            channel: sum(hours) / len(hours) if hours else 0
            for channel, hours in roi_by_channel.items()
        }


# ── CLI Interface ────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Revenue Tracker for Already Here LLC")
    parser.add_argument("--action", choices=["dashboard", "export", "telegram", "add", "fetch"],
                       default="dashboard", help="Action to perform")
    parser.add_argument("--channel", help="Channel for manual entry")
    parser.add_argument("--amount", type=float, help="Amount for manual entry")
    parser.add_argument("--description", help="Description for manual entry")
    parser.add_argument("--output", default="revenue_report.json", help="Output file for export")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")

    args = parser.parse_args()

    tracker = RevenueTracker()

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
        tracker.add_manual_entry(args.channel, args.amount, args.description)
        print(f"[OK] Added {args.channel}: ${args.amount}")

    elif args.action == "fetch":
        channels = tracker.fetch_all_channels(args.days)
        total_fetched = sum(len(entries) for entries in channels.values())
        print(f"[OK] Fetched {total_fetched} transactions from {len(channels)} channels")
        for channel, entries in channels.items():
            if entries:
                print(f"  {channel}: {len(entries)} transactions, ${sum(e.amount_usd for e in entries):,.2f}")


if __name__ == "__main__":
    main()

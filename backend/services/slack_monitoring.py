"""
Slack Real-Time Monitoring Service.

Handles scheduled daily (8 AM morning briefing, 6 PM evening metrics) and weekly
(Sunday 8 PM summary) posts with metrics, status indicators, and formatted templates.

Integrates with PROFITENGINE_SLACK_WEBHOOK_URL for incoming webhook posts.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from dataclasses import dataclass
import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase


class StatusIndicator(str, Enum):
    """Real-time status indicators for Slack blocks."""
    OPERATIONAL = ":green_circle: Operational"
    WARNING = ":yellow_circle: Warning"
    CRITICAL = ":red_circle: Critical"
    MAINTENANCE = ":orange_circle: Maintenance"
    OFFLINE = ":black_circle: Offline"


@dataclass
class MetricValue:
    """Single metric with label and status."""
    label: str
    value: str
    status: StatusIndicator
    trend: str = ""  # e.g., "↑ +15%", "↓ -2%"

    def to_slack_field(self) -> dict[str, str]:
        """Convert to Slack field block format."""
        trend_suffix = f" {self.trend}" if self.trend else ""
        return {
            "type": "mrkdwn",
            "text": f"*{self.label}*\n{self.status}\n{self.value}{trend_suffix}"
        }


@dataclass
class SlackBriefing:
    """Complete Slack message briefing."""
    title: str
    subtitle: str
    metrics: list[MetricValue]
    alerts: list[str] = None
    footer: str = "ProfitEngine v5 Real-Time Monitoring"
    color: str = "#36a64f"  # Green for operational

    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []

    def to_slack_payload(self) -> dict[str, Any]:
        """Convert to Slack incoming webhook payload."""
        blocks = []

        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": self.title,
                "emoji": True
            }
        })

        # Subtitle
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": self.subtitle
            }
        })

        # Divider
        blocks.append({"type": "divider"})

        # Metrics grid (4 columns)
        metric_fields = [m.to_slack_field() for m in self.metrics]
        if metric_fields:
            blocks.append({
                "type": "section",
                "fields": metric_fields
            })

        # Alerts section (if any)
        if self.alerts:
            blocks.append({"type": "divider"})
            alert_text = "\n".join([f"⚠️ {alert}" for alert in self.alerts])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Alerts*\n{alert_text}"
                }
            })

        # Footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{self.footer} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })

        return {
            "blocks": blocks,
            "attachments": [
                {
                    "color": self.color,
                    "footer": self.footer
                }
            ]
        }


class SlackMonitoringService:
    """Service for scheduled Slack monitoring posts."""

    def __init__(self, db: AsyncIOMotorDatabase, webhook_url: str = None):
        self.db = db
        self.webhook_url = webhook_url or os.environ.get("PROFITENGINE_SLACK_WEBHOOK_URL")
        self.session = None

    async def init(self):
        """Initialize aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()

    async def send_webhook(self, payload: dict[str, Any]) -> bool:
        """Send message via Slack incoming webhook."""
        if not self.webhook_url:
            print("PROFITENGINE_SLACK_WEBHOOK_URL not set; skipping Slack post")
            return False

        try:
            await self.init()
            async with self.session.post(self.webhook_url, json=payload) as resp:
                if resp.status == 200:
                    return True
                else:
                    print(f"Slack webhook failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"Slack webhook error: {e}")
            return False

    async def send_briefing(self, briefing: SlackBriefing) -> bool:
        """Send a briefing via Slack."""
        return await self.send_webhook(briefing.to_slack_payload())

    async def morning_briefing(self) -> SlackBriefing:
        """Generate 8 AM morning briefing."""
        return SlackBriefing(
            title="📊 ProfitEngine Morning Briefing",
            subtitle=f"*{datetime.now(timezone.utc).strftime('%A, %B %d, %Y')}*\nDaily overview & action items",
            metrics=await self._fetch_morning_metrics(),
            alerts=await self._fetch_morning_alerts(),
            color="#36a64f"  # Green
        )

    async def evening_metrics(self) -> SlackBriefing:
        """Generate 6 PM evening metrics post."""
        return SlackBriefing(
            title="📈 ProfitEngine Evening Metrics",
            subtitle="*Daily Performance Summary*\nEnd-of-day snapshot",
            metrics=await self._fetch_evening_metrics(),
            alerts=await self._fetch_evening_alerts(),
            color="#0099ff"  # Blue
        )

    async def weekly_summary(self) -> SlackBriefing:
        """Generate Sunday 8 PM weekly summary."""
        return SlackBriefing(
            title="📋 ProfitEngine Weekly Summary",
            subtitle=f"*Week of {(datetime.now(timezone.utc) - timedelta(days=6)).strftime('%B %d')} – {datetime.now(timezone.utc).strftime('%B %d, %Y')}*",
            metrics=await self._fetch_weekly_metrics(),
            alerts=await self._fetch_weekly_alerts(),
            color="#9c27b0"  # Purple
        )

    # ── Revenue helpers ──────────────────────────────────────────────────────────

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def _revenue_window(self, days: int) -> dict[str, Any]:
        """Return paid revenue + transaction counts for the trailing N days."""
        now = self._utc_now()
        start = (now - timedelta(days=days)).isoformat()
        coll = self.db.payment_transactions

        paid = 0
        revenue = 0.0
        try:
            cursor = coll.find({"payment_status": "paid", "updated_at": {"$gte": start}})
            async for doc in cursor:
                paid += 1
                revenue += float(doc.get("amount", 0) or 0)
        except Exception as exc:
            print(f"[slack_monitoring] revenue aggregation error: {exc}")
            return {"paid": 0, "total": 0, "revenue": 0.0, "success_rate": 0.0}

        try:
            total = await coll.count_documents({"created_at": {"$gte": start}})
        except Exception as exc:
            print(f"[slack_monitoring] transaction count error: {exc}")
            total = paid

        success_rate = (paid / total * 100) if total else 0.0
        return {"paid": paid, "total": total, "revenue": revenue, "success_rate": success_rate}

    async def _stuck_transactions(self) -> int:
        """Payments that have been pending/initiated for more than an hour."""
        now = self._utc_now()
        cutoff = (now - timedelta(hours=1)).isoformat()
        try:
            return await self.db.payment_transactions.count_documents({
                "payment_status": {"$in": ["initiated", "pending"]},
                "created_at": {"$lt": cutoff},
            })
        except Exception as exc:
            print(f"[slack_monitoring] stuck transaction query error: {exc}")
            return 0

    def _revenue_metrics(self, window: dict[str, Any], trailing_days: int, trailing_label: str) -> list[MetricValue]:
        revenue = window["revenue"]
        paid = window["paid"]
        total = window["total"]
        success_rate = window["success_rate"]
        avg_ticket = (revenue / paid) if paid else 0.0

        revenue_status = StatusIndicator.OPERATIONAL if revenue > 0 else StatusIndicator.WARNING
        conversion_status = (
            StatusIndicator.OPERATIONAL if success_rate >= 80
            else StatusIndicator.WARNING if success_rate >= 50
            else StatusIndicator.CRITICAL
        )

        return [
            MetricValue(
                label="Revenue",
                value=f"${revenue:,.2f}",
                status=revenue_status,
                trend=f"{paid} paid / {total} total",
            ),
            MetricValue(
                label="Success Rate",
                value=f"{success_rate:.1f}%",
                status=conversion_status,
            ),
            MetricValue(
                label="Avg Ticket",
                value=f"${avg_ticket:,.2f}",
                status=StatusIndicator.OPERATIONAL,
            ),
            MetricValue(
                label=trailing_label,
                value="loading…",
                status=StatusIndicator.OPERATIONAL,
            ),
        ]

    async def _alerts(self) -> list[str]:
        """Shared alert logic for all briefings."""
        alerts: list[str] = []
        stuck = await self._stuck_transactions()
        if stuck:
            alerts.append(f"{stuck} payment session(s) stuck in initiated/pending for >1 hour")
        return alerts

    async def _fetch_morning_metrics(self) -> list[MetricValue]:
        """Fetch metrics for morning briefing."""
        try:
            window_24h = await self._revenue_window(1)
            window_30d = await self._revenue_window(30)
            metrics = self._revenue_metrics(window_24h, 30, "30-Day Revenue")
            metrics[3].value = f"${window_30d['revenue']:,.2f}"
            return metrics
        except Exception as e:
            print(f"Error fetching morning metrics: {e}")
            return []

    async def _fetch_morning_alerts(self) -> list[str]:
        """Fetch alerts for morning briefing."""
        try:
            return await self._alerts()
        except Exception as e:
            print(f"Error fetching morning alerts: {e}")
            return []

    async def _fetch_evening_metrics(self) -> list[MetricValue]:
        """Fetch metrics for evening post."""
        try:
            window_24h = await self._revenue_window(1)
            window_7d = await self._revenue_window(7)
            metrics = self._revenue_metrics(window_24h, 7, "7-Day Revenue")
            metrics[3].value = f"${window_7d['revenue']:,.2f}"
            return metrics
        except Exception as e:
            print(f"Error fetching evening metrics: {e}")
            return []

    async def _fetch_evening_alerts(self) -> list[str]:
        """Fetch alerts for evening post."""
        try:
            return await self._alerts()
        except Exception as e:
            print(f"Error fetching evening alerts: {e}")
            return []

    async def _fetch_weekly_metrics(self) -> list[MetricValue]:
        """Fetch metrics for weekly summary."""
        try:
            window_7d = await self._revenue_window(7)
            window_30d = await self._revenue_window(30)
            metrics = self._revenue_metrics(window_7d, 30, "30-Day Revenue")
            metrics[3].value = f"${window_30d['revenue']:,.2f}"
            return metrics
        except Exception as e:
            print(f"Error fetching weekly metrics: {e}")
            return []

    async def _fetch_weekly_alerts(self) -> list[str]:
        """Fetch alerts for weekly summary."""
        try:
            return await self._alerts()
        except Exception as e:
            print(f"Error fetching weekly alerts: {e}")
            return []


async def test_slack_briefings():
    """Quick test function to preview Slack messages."""
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_url = os.environ.get("MONGO_URL")
    if not mongo_url:
        print("MONGO_URL not configured — skipping test_slack_briefings")
        return
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get("DB_NAME", "profitengine_test")]

    service = SlackMonitoringService(db)

    # Test morning briefing
    morning = await service.morning_briefing()
    print("MORNING BRIEFING:")
    print(json.dumps(morning.to_slack_payload(), indent=2))
    print("\n" + "=" * 80 + "\n")

    # Test evening metrics
    evening = await service.evening_metrics()
    print("EVENING METRICS:")
    print(json.dumps(evening.to_slack_payload(), indent=2))
    print("\n" + "=" * 80 + "\n")

    # Test weekly summary
    weekly = await service.weekly_summary()
    print("WEEKLY SUMMARY:")
    print(json.dumps(weekly.to_slack_payload(), indent=2))
    print("\n" + "=" * 80 + "\n")

    await service.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_slack_briefings())

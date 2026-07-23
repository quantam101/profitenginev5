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

    async def _fetch_morning_metrics(self) -> list[MetricValue]:
        """Fetch metrics for morning briefing."""
        try:
            # Example: pull from database or API
            metrics = [
                MetricValue(
                    label="System Status",
                    value="All systems operational",
                    status=StatusIndicator.OPERATIONAL,
                    trend="✓"
                ),
                MetricValue(
                    label="API Latency",
                    value="142ms avg",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↓ -8ms"
                ),
                MetricValue(
                    label="Error Rate",
                    value="0.02%",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↓ -0.01%"
                ),
                MetricValue(
                    label="Uptime",
                    value="99.99%",
                    status=StatusIndicator.OPERATIONAL,
                    trend="✓"
                ),
            ]
            return metrics
        except Exception as e:
            print(f"Error fetching morning metrics: {e}")
            return []

    async def _fetch_morning_alerts(self) -> list[str]:
        """Fetch alerts for morning briefing."""
        try:
            # Example: check for critical issues
            alerts = []
            # Add logic to fetch real alerts from database
            return alerts
        except Exception as e:
            print(f"Error fetching morning alerts: {e}")
            return []

    async def _fetch_evening_metrics(self) -> list[MetricValue]:
        """Fetch metrics for evening post."""
        try:
            metrics = [
                MetricValue(
                    label="Daily Revenue",
                    value="$2,450.85",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +12%"
                ),
                MetricValue(
                    label="Active Sessions",
                    value="342",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +28"
                ),
                MetricValue(
                    label="Conversion Rate",
                    value="3.2%",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +0.5%"
                ),
                MetricValue(
                    label="Avg Response Time",
                    value="156ms",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +12ms"
                ),
            ]
            return metrics
        except Exception as e:
            print(f"Error fetching evening metrics: {e}")
            return []

    async def _fetch_evening_alerts(self) -> list[str]:
        """Fetch alerts for evening post."""
        try:
            alerts = []
            # Add logic to fetch real alerts from database
            return alerts
        except Exception as e:
            print(f"Error fetching evening alerts: {e}")
            return []

    async def _fetch_weekly_metrics(self) -> list[MetricValue]:
        """Fetch metrics for weekly summary."""
        try:
            metrics = [
                MetricValue(
                    label="Weekly Revenue",
                    value="$18,342.50",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +8.5%"
                ),
                MetricValue(
                    label="Total Sessions",
                    value="2,145",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +312"
                ),
                MetricValue(
                    label="Avg Daily Revenue",
                    value="$2,620.36",
                    status=StatusIndicator.OPERATIONAL,
                    trend="↑ +5.2%"
                ),
                MetricValue(
                    label="Uptime SLA",
                    value="99.97%",
                    status=StatusIndicator.OPERATIONAL,
                    trend="✓"
                ),
            ]
            return metrics
        except Exception as e:
            print(f"Error fetching weekly metrics: {e}")
            return []

    async def _fetch_weekly_alerts(self) -> list[str]:
        """Fetch alerts for weekly summary."""
        try:
            alerts = []
            # Add logic to fetch real alerts from database
            return alerts
        except Exception as e:
            print(f"Error fetching weekly alerts: {e}")
            return []


async def test_slack_briefings():
    """Quick test function to preview Slack messages."""
    from motor.motor_asyncio import AsyncIOMotorClient

    # Mock database
    mongo_url = os.environ.get("MONGO_URL", "mongodb://mongo:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["profitengine_test"]

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

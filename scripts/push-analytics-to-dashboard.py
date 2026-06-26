#!/usr/bin/env python3
"""
Push Analytics to Dashboard
Syncs OCI analytics logs to Vercel dashboard every minute
Runs as cron job: * * * * * /home/ubuntu/scripts/push-analytics-to-dashboard.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import httpx


class AnalyticsPusher:
    """Push analytics from OCI logs to Vercel dashboard"""

    def __init__(self):
        self.dashboard_url = os.getenv('DASHBOARD_URL', 'https://profitengine-tau.vercel.app/api/analytics/sync')
        self.dashboard_token = os.getenv('DASHBOARD_API_TOKEN', '')
        self.analytics_log = "/home/ubuntu/analytics.log"
        self.revenue_log = "/home/ubuntu/revenue_attribution.json"

    def read_recent_logs(self, minutes=1):
        """Read analytics from past N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        entries = []

        try:
            with open(self.analytics_log, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        ts = datetime.fromisoformat(entry["timestamp"])
                        if ts >= cutoff:
                            entries.append(entry)
                    except:
                        pass
        except:
            pass

        return entries

    def read_recent_revenue(self, minutes=1):
        """Read revenue from past N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        entries = []

        try:
            with open(self.revenue_log, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        ts = datetime.fromisoformat(entry["timestamp"])
                        if ts >= cutoff:
                            entries.append(entry)
                    except:
                        pass
        except:
            pass

        return entries

    def aggregate_data(self, analytics, revenue):
        """Aggregate recent data by platform"""
        platform_stats = defaultdict(lambda: {
            "posts": 0,
            "reach": 0,
            "revenue": 0.0
        })

        for entry in analytics:
            platform = entry.get("platform", "Unknown")
            platform_stats[platform]["posts"] += 1
            platform_stats[platform]["reach"] += entry.get("expected_reach", 0)

        for entry in revenue:
            platform = entry.get("platform", "Unknown")
            platform_stats[platform]["revenue"] += entry.get("revenue_usd", 0)

        return dict(platform_stats)

    async def push_to_dashboard(self):
        """Push aggregated analytics to dashboard"""
        analytics = self.read_recent_logs(minutes=1)
        revenue = self.read_recent_revenue(minutes=1)

        if not analytics and not revenue:
            return  # Nothing to push

        platform_stats = self.aggregate_data(analytics, revenue)

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "analytics_data": {
                "posts": len(analytics),
                "platforms": platform_stats
            },
            "revenue_data": {
                "total": sum(p["revenue"] for p in platform_stats.values()),
                "by_platform": {p: s["revenue"] for p, s in platform_stats.items()}
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.dashboard_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.dashboard_token}",
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code == 200:
                    print(f"[✅] Dashboard synced: {len(analytics)} posts, ${payload['revenue_data']['total']:.2f} revenue")
                else:
                    print(f"[⚠️] Dashboard sync failed: {response.status_code}")

        except Exception as e:
            print(f"[❌] Failed to push to dashboard: {e}")


async def main():
    """Main execution"""
    pusher = AnalyticsPusher()
    await pusher.push_to_dashboard()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

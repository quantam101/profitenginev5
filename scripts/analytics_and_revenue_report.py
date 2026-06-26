#!/usr/bin/env python3
"""
Analytics & Revenue Attribution System
Real-time tracking of posts, engagement, and revenue per platform
Daily/Weekly/Monthly reporting
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import sys


class AnalyticsEngine:
    """Track and report platform performance and revenue"""

    def __init__(self):
        self.analytics_log = "/home/ubuntu/analytics.log"
        self.revenue_log = "/home/ubuntu/revenue_attribution.json"
        self.report_dir = "/home/ubuntu/reports"

        # Create reports directory
        os.makedirs(self.report_dir, exist_ok=True)

    def read_logs(self, days=1):
        """Read analytics logs for past N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
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

    def read_revenue(self, days=1):
        """Read revenue logs for past N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
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

    def generate_daily_report(self):
        """Generate daily analytics report"""
        analytics = self.read_logs(days=1)
        revenue = self.read_revenue(days=1)

        # Aggregate by platform
        platform_stats = defaultdict(lambda: {
            "posts": 0,
            "reach": 0,
            "revenue": 0.0
        })

        for entry in analytics:
            platform = entry["platform"]
            platform_stats[platform]["posts"] += 1
            platform_stats[platform]["reach"] += entry.get("expected_reach", 0)

        for entry in revenue:
            platform = entry["platform"]
            platform_stats[platform]["revenue"] += entry["revenue_usd"]

        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "daily",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "summary": {
                "total_posts": sum(p["posts"] for p in platform_stats.values()),
                "total_reach": sum(p["reach"] for p in platform_stats.values()),
                "total_revenue": sum(p["revenue"] for p in platform_stats.values()),
                "platforms_active": len(platform_stats)
            },
            "platforms": dict(platform_stats)
        }

        # Save report
        report_file = f"{self.report_dir}/daily_{datetime.utcnow().strftime('%Y%m%d')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def generate_weekly_report(self):
        """Generate weekly analytics report"""
        analytics = self.read_logs(days=7)
        revenue = self.read_revenue(days=7)

        # Aggregate by platform and day
        daily_platforms = defaultdict(lambda: defaultdict(lambda: {
            "posts": 0,
            "reach": 0,
            "revenue": 0.0
        }))

        for entry in analytics:
            day = datetime.fromisoformat(entry["timestamp"]).strftime("%A")
            platform = entry["platform"]
            daily_platforms[day][platform]["posts"] += 1
            daily_platforms[day][platform]["reach"] += entry.get("expected_reach", 0)

        for entry in revenue:
            day = datetime.fromisoformat(entry["timestamp"]).strftime("%A")
            platform = entry["platform"]
            daily_platforms[day][platform]["revenue"] += entry["revenue_usd"]

        # Best performing times
        hourly_stats = defaultdict(int)
        for entry in analytics:
            hour = datetime.fromisoformat(entry["timestamp"]).strftime("%H:00")
            hourly_stats[hour] += 1

        best_hours = sorted(hourly_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "weekly",
            "week_of": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "summary": {
                "total_posts": sum(
                    p["posts"] for day in daily_platforms.values()
                    for p in day.values()
                ),
                "total_reach": sum(
                    p["reach"] for day in daily_platforms.values()
                    for p in day.values()
                ),
                "total_revenue": sum(
                    p["revenue"] for day in daily_platforms.values()
                    for p in day.values()
                ),
            },
            "daily_breakdown": {day: dict(platforms) for day, platforms in daily_platforms.items()},
            "best_posting_hours": best_hours
        }

        # Save report
        report_file = f"{self.report_dir}/weekly_{datetime.utcnow().strftime('%Y_W%U')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def generate_monthly_report(self):
        """Generate monthly analytics report"""
        analytics = self.read_logs(days=30)
        revenue = self.read_revenue(days=30)

        # Aggregate by platform
        platform_stats = defaultdict(lambda: {
            "posts": 0,
            "reach": 0,
            "revenue": 0.0,
            "avg_reach_per_post": 0.0,
            "revenue_per_post": 0.0
        })

        for entry in analytics:
            platform = entry["platform"]
            platform_stats[platform]["posts"] += 1
            platform_stats[platform]["reach"] += entry.get("expected_reach", 0)

        for entry in revenue:
            platform = entry["platform"]
            platform_stats[platform]["revenue"] += entry["revenue_usd"]

        # Calculate averages
        for platform in platform_stats:
            posts = platform_stats[platform]["posts"]
            if posts > 0:
                platform_stats[platform]["avg_reach_per_post"] = (
                    platform_stats[platform]["reach"] / posts
                )
                platform_stats[platform]["revenue_per_post"] = (
                    platform_stats[platform]["revenue"] / posts
                )

        # Top performers
        top_platform = max(
            platform_stats.items(),
            key=lambda x: x[1]["revenue"],
            default=("None", {})
        )

        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "monthly",
            "month": datetime.utcnow().strftime("%B %Y"),
            "summary": {
                "total_posts": sum(p["posts"] for p in platform_stats.values()),
                "total_reach": sum(p["reach"] for p in platform_stats.values()),
                "total_revenue": sum(p["revenue"] for p in platform_stats.values()),
                "avg_posts_per_day": sum(p["posts"] for p in platform_stats.values()) / 30,
                "avg_revenue_per_day": sum(p["revenue"] for p in platform_stats.values()) / 30,
            },
            "platforms": dict(platform_stats),
            "top_performer": {
                "platform": top_platform[0],
                "revenue": top_platform[1].get("revenue", 0)
            }
        }

        # Projection
        daily_avg = report["summary"]["avg_revenue_per_day"]
        report["projections"] = {
            "monthly_at_current_rate": daily_avg * 30,
            "annual_at_current_rate": daily_avg * 365
        }

        # Save report
        report_file = f"{self.report_dir}/monthly_{datetime.utcnow().strftime('%Y_%m')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def print_report(self, report):
        """Pretty print report"""
        print(f"\n{'='*70}")
        print(f"  {report['type'].upper()} ANALYTICS REPORT")
        print(f"{'='*70}\n")

        if report["type"] == "daily":
            print(f"Date: {report['date']}")
            print(f"Posts: {report['summary']['total_posts']}")
            print(f"Total Reach: {report['summary']['total_reach']:,}")
            print(f"Revenue: ${report['summary']['total_revenue']:.2f}")
            print(f"\nPlatform Breakdown:")
            for platform, stats in report["platforms"].items():
                print(f"  {platform:12} | Posts: {stats['posts']:2} | Reach: {stats['reach']:>7,} | Revenue: ${stats['revenue']:>7.2f}")

        elif report["type"] == "weekly":
            print(f"Week of: {report['week_of']}")
            print(f"Posts: {report['summary']['total_posts']}")
            print(f"Total Reach: {report['summary']['total_reach']:,}")
            print(f"Revenue: ${report['summary']['total_revenue']:.2f}")
            print(f"\nBest Posting Hours:")
            for hour, count in report["best_posting_hours"]:
                print(f"  {hour}: {count} posts")

        elif report["type"] == "monthly":
            print(f"Month: {report['month']}")
            print(f"Total Posts: {report['summary']['total_posts']}")
            print(f"Total Reach: {report['summary']['total_reach']:,}")
            print(f"Total Revenue: ${report['summary']['total_revenue']:.2f}")
            print(f"Daily Average: ${report['summary']['avg_revenue_per_day']:.2f}")
            print(f"\nTop Performer: {report['top_performer']['platform']} (${report['top_performer']['revenue']:.2f})")
            print(f"\nProjections:")
            print(f"  Monthly: ${report['projections']['monthly_at_current_rate']:.2f}")
            print(f"  Annual: ${report['projections']['annual_at_current_rate']:.2f}")

        print(f"\n{'='*70}\n")


async def main():
    """Generate all reports"""
    engine = AnalyticsEngine()

    print("[Daily Report]")
    daily = engine.generate_daily_report()
    engine.print_report(daily)

    print("[Weekly Report]")
    weekly = engine.generate_weekly_report()
    engine.print_report(weekly)

    print("[Monthly Report]")
    monthly = engine.generate_monthly_report()
    engine.print_report(monthly)

    print(f"Reports saved to: {engine.report_dir}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

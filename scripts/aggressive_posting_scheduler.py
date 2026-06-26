#!/usr/bin/env python3
"""
Aggressive Multi-Post Scheduler (3-5x daily)
Strategic timing based on platform analytics
Real-time revenue attribution & analytics tracking
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from runtime.eaos.video_engine import UltimateVideoEngine
from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost


# Optimal posting times per platform (UTC)
POSTING_SCHEDULE = {
    "aggressive": {  # 3-5x daily
        "TikTok": {
            "times": ["06:00", "12:00", "15:00", "19:00"],  # 4x daily
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "weight": 5  # highest priority
        },
        "Twitter": {
            "times": ["08:00", "12:00", "17:00"],  # 3x daily
            "days": ["Monday", "Wednesday", "Friday"],
            "weight": 4
        },
        "YouTube": {
            "times": ["09:00"],  # 1x daily (evergreen content)
            "days": ["Friday", "Saturday", "Sunday"],
            "weight": 3
        },
        "LinkedIn": {
            "times": ["07:00", "12:00", "17:00"],  # 3x daily (weekdays only)
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "weight": 3
        },
        "Instagram": {
            "times": ["11:00", "19:00"],  # 2x daily
            "days": ["Tuesday", "Wednesday", "Thursday"],
            "weight": 4
        },
        "Facebook": {
            "times": ["13:00", "19:00"],  # 2x daily
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "weight": 2
        },
        "Telegram": {
            "times": ["09:00", "14:00", "20:00"],  # 3x daily
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "weight": 2
        }
    }
}


class AnalyticsTracker:
    """Track video performance and revenue attribution"""

    def __init__(self):
        self.log_file = "/home/ubuntu/analytics.log"
        self.revenue_file = "/home/ubuntu/revenue_attribution.json"

    def log_post(self, platform, video_id, timestamp, expected_reach):
        """Log post with analytics data"""
        entry = {
            "timestamp": timestamp.isoformat(),
            "platform": platform,
            "video_id": video_id,
            "posting_time_utc": timestamp.strftime("%H:%M"),
            "expected_reach": expected_reach,
            "status": "posted"
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"[Analytics] {platform} post logged: {video_id}")

    def track_revenue(self, platform, revenue_estimate, source="organic"):
        """Track revenue attribution per platform"""
        timestamp = datetime.utcnow()

        data = {
            "timestamp": timestamp.isoformat(),
            "platform": platform,
            "revenue_usd": revenue_estimate,
            "source": source,
            "hour": timestamp.hour,
            "day": timestamp.strftime("%A")
        }

        try:
            with open(self.revenue_file, "a") as f:
                f.write(json.dumps(data) + "\n")
        except:
            pass


class AggressivePostingEngine:
    """Generate and post videos 3-5x daily with strategic timing"""

    def __init__(self):
        self.video_engine = UltimateVideoEngine()
        self.social_engine = ProductionSocialEngine()
        self.analytics = AnalyticsTracker()
        self.schedule = POSTING_SCHEDULE["aggressive"]

    async def should_post_now(self) -> dict:
        """Check if it's time to post (strategic timing)"""
        now = datetime.utcnow()
        current_hour = now.strftime("%H:%M")
        current_day = now.strftime("%A")

        platforms_to_post = {}

        for platform, config in self.schedule.items():
            # Check if today is a posting day
            if current_day not in config["days"]:
                continue

            # Check if current time matches posting time
            if current_hour in config["times"]:
                platforms_to_post[platform] = {
                    "weight": config["weight"],
                    "time": current_hour
                }

        return platforms_to_post

    async def generate_video(self, platform: str) -> str:
        """Generate video optimized for platform"""
        topic = os.getenv("ARTICLE_TOPIC", "Best AI Tools for Passive Income in 2026")

        # Platform-specific optimization
        duration = {
            "TikTok": 8,
            "Twitter": 5,
            "YouTube": 60,
            "LinkedIn": 10,
            "Instagram": 7,
            "Facebook": 12,
            "Telegram": 5
        }.get(platform, 8)

        print(f"[{platform}] Generating {duration}s video...")

        try:
            video_path = await self.video_engine.produce_article_video(
                title=topic,
                body=f"Best practices for {platform}",
                canonical_url=os.getenv("CANONICAL_URL", "https://quantam101.github.io/content")
            )
            return video_path
        except Exception as e:
            print(f"[{platform}] Generation failed: {e}")
            return None

    async def post_to_platform(self, platform: str, video_path: str):
        """Post video with aggressive timing"""
        caption = os.getenv("ARTICLE_TOPIC", "AI Automation") + "\n\n#ProfitEngine #PassiveIncome"

        try:
            await self.social_engine.publish(
                SocialPost(
                    None,
                    platform,
                    caption,
                    media_path=video_path
                )
            )

            # Track analytics
            expected_reach = {
                "TikTok": 50000,
                "Twitter": 10000,
                "YouTube": 5000,
                "LinkedIn": 8000,
                "Instagram": 15000,
                "Facebook": 12000,
                "Telegram": 5000
            }.get(platform, 5000)

            self.analytics.log_post(platform, video_path, datetime.utcnow(), expected_reach)

            print(f"[✅] {platform}: Posted successfully")

        except Exception as e:
            print(f"[❌] {platform}: Failed - {e}")

    async def run_aggressive_cycle(self):
        """Run 3-5x daily aggressive posting"""
        platforms = await self.should_post_now()

        if not platforms:
            return

        print(f"\n[AGGRESSIVE CYCLE] {len(platforms)} platforms to post")

        # Generate video once, post to all platforms in parallel
        video_path = await self.generate_video("All")

        if not video_path:
            print("[ERROR] Video generation failed")
            return

        # Post to all platforms concurrently
        tasks = []
        for platform in platforms.keys():
            tasks.append(self.post_to_platform(platform, video_path))

        await asyncio.gather(*tasks)

        print("[CYCLE COMPLETE] Aggressive posting finished")


async def main():
    """Main execution loop"""
    engine = AggressivePostingEngine()

    print("════════════════════════════════════════════════")
    print("  PROFITENGINE v5 - AGGRESSIVE POSTING ENGINE")
    print("  3-5x Daily with Strategic Timing")
    print("════════════════════════════════════════════════")
    print("")

    # Run aggressive cycle
    await engine.run_aggressive_cycle()


if __name__ == "__main__":
    asyncio.run(main())

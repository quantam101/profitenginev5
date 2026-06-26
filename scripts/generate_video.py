#!/usr/bin/env python3
"""
EAOS video generation script — runs in GitHub Actions after daily-content publish.
Generates a slideshow video from the latest article topic and uploads to configured
video/social platforms. Falls back gracefully if ffmpeg is unavailable.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from runtime.eaos.video_engine import UltimateVideoEngine
from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost

TOPIC = os.getenv("ARTICLE_TOPIC", "Best AI Tools for Passive Income in 2026")
CANONICAL_URL = os.getenv("CANONICAL_URL", "https://quantam101.github.io/content")


async def main() -> None:
    engine = UltimateVideoEngine()
    print(f"[Video] Generating video for: {TOPIC}")

    body = (
        f"{TOPIC}. "
        "Artificial intelligence is transforming how we earn online. "
        "Automated content pipelines now generate and publish articles daily. "
        "Print-on-demand storefronts run without human intervention. "
        "Social media accounts post around the clock. "
        "The future of passive income is already here. "
        "Already Here LLC builds and ships these systems so you don't have to. "
        "Visit alreadyherellc.com to learn more."
    )

    video_path = await engine.produce_article_video(
        title=TOPIC,
        body=body,
        canonical_url=CANONICAL_URL,
    )

    if not video_path or not os.path.exists(video_path):
        print("[Video] No video produced — ffmpeg may not be available")
        return

    print(f"[Video] Master ready: {video_path}")

    # Check which platforms have credentials
    credentials = {
        "TIKTOK": os.getenv("TIKTOK_ACCESS_TOKEN", ""),
        "TWITTER": all([
            os.getenv("TWITTER_API_KEY", ""),
            os.getenv("TWITTER_API_SECRET", ""),
            os.getenv("TWITTER_ACCESS_TOKEN", ""),
            os.getenv("TWITTER_ACCESS_SECRET", ""),
        ]),
        "LINKEDIN": all([
            os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
            os.getenv("LINKEDIN_PERSON_URN", ""),
        ]),
        "INSTAGRAM": all([
            os.getenv("IG_USER_ID", ""),
            os.getenv("IG_PAGE_ACCESS_TOKEN", ""),
        ]),
        "FACEBOOK": all([
            os.getenv("FB_PAGE_ID", ""),
            os.getenv("FB_PAGE_ACCESS_TOKEN", ""),
        ]),
        "YOUTUBE": all([
            os.getenv("YOUTUBE_CLIENT_ID", ""),
            os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            os.getenv("YOUTUBE_REFRESH_TOKEN", ""),
        ]),
        "TELEGRAM": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    }

    active_platforms = [p for p, has_creds in credentials.items() if has_creds]

    if not active_platforms:
        print("[Video] No social credentials configured — video saved locally only")
        return

    print(f"[Video] Auto-posting to {len(active_platforms)} platforms: {', '.join(active_platforms)}")

    social = ProductionSocialEngine()
    caption = f"{TOPIC}\n\n#ProfitEngine #PassiveIncome #AITools #AlreadyHereLLC"

    # Post to all configured platforms
    for platform in active_platforms:
        try:
            if platform == "TIKTOK":
                await social.publish(SocialPost(None, "TIKTOK", caption, media_path=video_path))
                print(f"✅ Posted to TikTok")

            elif platform == "TWITTER":
                await social.publish(SocialPost(None, "TWITTER", caption, media_path=video_path))
                print(f"✅ Posted to Twitter")

            elif platform == "LINKEDIN":
                await social.publish(SocialPost(
                    None,
                    "LINKEDIN",
                    caption,
                    media_path=video_path,
                    extra={"title": TOPIC[:100]}
                ))
                print(f"✅ Posted to LinkedIn")

            elif platform == "INSTAGRAM":
                await social.publish(SocialPost(None, "INSTAGRAM", caption, media_path=video_path))
                print(f"✅ Posted to Instagram")

            elif platform == "FACEBOOK":
                await social.publish(SocialPost(None, "FACEBOOK", caption, media_path=video_path))
                print(f"✅ Posted to Facebook")

            elif platform == "YOUTUBE":
                await social.publish(SocialPost(
                    None,
                    "YOUTUBE",
                    TOPIC[:100],
                    media_path=video_path,
                    extra={
                        "description": f"{TOPIC}\n\n{CANONICAL_URL}\n\n{caption}",
                        "tags": ["ProfitEngine", "PassiveIncome", "AITools", "AlreadyHereLLC"],
                    },
                ))
                print(f"✅ Posted to YouTube")

            elif platform == "TELEGRAM":
                await social.publish(SocialPost(None, "TELEGRAM", f"New video: {caption}"))
                print(f"✅ Posted to Telegram")

        except Exception as e:
            print(f"⚠️  Failed to post to {platform}: {e}")


if __name__ == "__main__":
    asyncio.run(main())

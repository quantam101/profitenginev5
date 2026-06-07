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

    tiktok_token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    youtube_ready = all([
        os.getenv("YOUTUBE_CLIENT_ID", ""),
        os.getenv("YOUTUBE_CLIENT_SECRET", ""),
        os.getenv("YOUTUBE_REFRESH_TOKEN", ""),
    ])

    if tiktok_token or telegram_token or youtube_ready:
        social = ProductionSocialEngine()
        caption = f"{TOPIC}\n\n#ProfitEngine #PassiveIncome #AITools #AlreadyHereLLC"
        if tiktok_token:
            await social.publish(SocialPost(None, "TIKTOK", caption, media_path=video_path))
        if youtube_ready:
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
        if telegram_token:
            await social.publish(SocialPost(None, "TELEGRAM", f"New video: {caption}"))
    else:
        print("[Video] No social credentials — video saved as artifact only")


if __name__ == "__main__":
    asyncio.run(main())

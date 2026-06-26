#!/usr/bin/env python3
"""
OCI Server: Video Generation + Multi-Platform Upload
Runs on OCI Always Free tier (129.146.236.177)
- Lightweight: FFmpeg slideshow only (no Wan, no heavy models)
- Triggered by GitHub Actions webhook or cron job
- Generates video and auto-posts to all platforms
"""
import asyncio
import os
import sys
import pathlib
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from runtime.eaos.video_engine import UltimateVideoEngine
from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost

async def main():
    """Generate video from latest article and post to all platforms."""

    # Get article topic (from GitHub Actions or environment)
    article_topic = os.getenv("ARTICLE_TOPIC", "Best AI Tools for Passive Income in 2026")
    canonical_url = os.getenv("CANONICAL_URL", "https://quantam101.github.io/content")

    print(f"[OCI Video] Starting video generation for: {article_topic}")
    print(f"[OCI Video] Time: {datetime.utcnow().isoformat()}Z")

    # === STEP 1: Generate Video ===
    # On OCI: Use FFmpeg slideshow only (no GPU, no heavy models)
    engine = UltimateVideoEngine()

    body = (
        f"{article_topic}. "
        "Artificial intelligence is transforming how we earn online. "
        "Automated content pipelines now generate and publish articles daily. "
        "Print-on-demand storefronts run without human intervention. "
        "Social media accounts post around the clock. "
        "The future of passive income is already here. "
        "Already Here LLC builds and ships these systems so you don't have to. "
        "Visit alreadyherellc.com to learn more."
    )

    try:
        video_path = await engine.produce_article_video(
            title=article_topic,
            body=body,
            canonical_url=canonical_url,
        )
    except Exception as e:
        print(f"[OCI Video] Generation failed: {e}")
        return

    if not video_path or not os.path.exists(video_path):
        print("[OCI Video] No video produced")
        return

    print(f"[OCI Video] ✅ Video ready: {video_path}")
    print(f"[OCI Video] File size: {os.path.getsize(video_path) / 1024 / 1024:.1f}MB")

    # === STEP 2: Post to All Platforms ===
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
        print("[OCI Video] No social credentials configured")
        return

    print(f"[OCI Video] Posting to {len(active_platforms)} platforms: {', '.join(active_platforms)}")

    social = ProductionSocialEngine()
    caption = f"{article_topic}\n\n#ProfitEngine #PassiveIncome #AITools #AlreadyHereLLC"

    # Post to all configured platforms
    results = {}
    for platform in active_platforms:
        try:
            if platform == "TIKTOK":
                await social.publish(SocialPost(None, "TIKTOK", caption, media_path=video_path))
                results["TIKTOK"] = "✅"
                print(f"[OCI Video] ✅ Posted to TikTok")

            elif platform == "TWITTER":
                await social.publish(SocialPost(None, "TWITTER", caption, media_path=video_path))
                results["TWITTER"] = "✅"
                print(f"[OCI Video] ✅ Posted to Twitter")

            elif platform == "LINKEDIN":
                await social.publish(SocialPost(
                    None, "LINKEDIN", caption, media_path=video_path,
                    extra={"title": article_topic[:100]}
                ))
                results["LINKEDIN"] = "✅"
                print(f"[OCI Video] ✅ Posted to LinkedIn")

            elif platform == "INSTAGRAM":
                await social.publish(SocialPost(None, "INSTAGRAM", caption, media_path=video_path))
                results["INSTAGRAM"] = "✅"
                print(f"[OCI Video] ✅ Posted to Instagram")

            elif platform == "FACEBOOK":
                await social.publish(SocialPost(None, "FACEBOOK", caption, media_path=video_path))
                results["FACEBOOK"] = "✅"
                print(f"[OCI Video] ✅ Posted to Facebook")

            elif platform == "YOUTUBE":
                await social.publish(SocialPost(
                    None, "YOUTUBE", article_topic[:100], media_path=video_path,
                    extra={
                        "description": f"{article_topic}\n\n{canonical_url}\n\n{caption}",
                        "tags": ["ProfitEngine", "PassiveIncome", "AITools", "AlreadyHereLLC"],
                    },
                ))
                results["YOUTUBE"] = "✅"
                print(f"[OCI Video] ✅ Posted to YouTube")

            elif platform == "TELEGRAM":
                await social.publish(SocialPost(None, "TELEGRAM", f"New video: {caption}"))
                results["TELEGRAM"] = "✅"
                print(f"[OCI Video] ✅ Posted to Telegram")

        except Exception as e:
            results[platform] = f"❌ {e}"
            print(f"[OCI Video] ❌ Failed to post to {platform}: {e}")

    # === STEP 3: Summary ===
    print("\n" + "="*60)
    print("[OCI Video] SUMMARY")
    print("="*60)
    for platform, status in results.items():
        print(f"  {platform}: {status}")
    print(f"[OCI Video] Time: {datetime.utcnow().isoformat()}Z")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

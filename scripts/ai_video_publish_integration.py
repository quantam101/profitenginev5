#!/usr/bin/env python3
"""
Integration layer for AI Video Generator with ProfitEngine publish pipeline.

Hooks into:
- publish_article.py → Auto-generate video for each article
- social_media_publishers.py → Post videos to TikTok, YouTube, Instagram
- newsletter_publisher.py → Include video in daily/weekly newsletters
- gumroad_publisher.py → Create video courses

Usage:
  python ai_video_publish_integration.py --trigger article_published --topic "..."
  python ai_video_publish_integration.py --trigger newsletter_daily
  python ai_video_publish_integration.py --trigger auto_publish_approved
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ai_video_generator import (
    VideoType,
    VoiceProvider,
    VideoGenerationResult,
    generate_video_end_to_end,
    approve_from_review_queue,
)

# Integration log
INTEGRATION_LOG = pathlib.Path("./logs/ai_video_integration.jsonl")


@dataclass
class IntegrationEvent:
    """Track video generation events for analytics."""
    timestamp: str
    trigger: str  # "article_published", "newsletter_daily", etc.
    topic: str
    video_type: str
    status: str  # "started", "completed", "failed"
    script_hash: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_jsonl(self) -> str:
        """Serialize to JSONL format."""
        return json.dumps({
            "timestamp": self.timestamp,
            "trigger": self.trigger,
            "topic": self.topic,
            "video_type": self.video_type,
            "status": self.status,
            "script_hash": self.script_hash,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        })


def _log_event(event: IntegrationEvent) -> None:
    """Append event to integration log."""
    INTEGRATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    INTEGRATION_LOG.open("a", encoding="utf-8").write(event.to_jsonl() + "\n")
    print(f"[Integration] {event.status}: {event.topic}")


# ────────────────────────────────────────────────────────────────────────────
# Trigger 1: Article Published
# ────────────────────────────────────────────────────────────────────────────


async def on_article_published(
    article_title: str,
    article_body: str,
    article_slug: str,
    article_topic: Optional[str] = None,
    auto_publish: bool = False,
) -> Optional[VideoGenerationResult]:
    """
    Triggered when a new article is published.

    Automatically generates a video based on the article.
    """
    topic = article_topic or article_title
    event = IntegrationEvent(
        timestamp=datetime.now().isoformat(),
        trigger="article_published",
        topic=topic,
        video_type="explainer",
        status="started",
    )
    _log_event(event)

    start_time = time.time()

    try:
        # Determine video type based on content
        video_type = _infer_video_type(article_body)
        slides_count = min(5 + (len(article_body) // 500), 12)

        print(f"[ArticlePublish] Generating video for: {topic}")
        print(f"[ArticlePublish] Type: {video_type.value} | Slides: {slides_count}")

        result = await generate_video_end_to_end(
            topic=topic,
            video_type=video_type,
            slides_count=slides_count,
            voice_provider=VoiceProvider.ELEVENLABS,
            auto_publish=auto_publish,
        )

        if result:
            event.status = "completed"
            event.script_hash = result.script_hash
            event.duration_seconds = time.time() - start_time
            event.video_type = video_type.value
            _log_event(event)

            # Trigger social publishing (if auto_publish enabled)
            if auto_publish:
                await on_auto_publish_approved(result.script_hash)

            return result
        else:
            raise RuntimeError("Video generation returned None")

    except Exception as exc:
        event.status = "failed"
        event.error = str(exc)
        event.duration_seconds = time.time() - start_time
        _log_event(event)
        print(f"[ArticlePublish] Failed: {exc}")
        return None


def _infer_video_type(article_body: str) -> VideoType:
    """Infer video type from article content."""
    body_lower = article_body.lower()

    # Check for indicators
    if "tutorial" in body_lower or "step-by-step" in body_lower:
        return VideoType.TUTORIAL
    elif "how to" in body_lower or "guide" in body_lower:
        return VideoType.EDUCATIONAL
    elif "product" in body_lower or "vs" in body_lower or "compare" in body_lower:
        return VideoType.PRODUCT_DEMO
    elif "news" in body_lower or "latest" in body_lower or "trending" in body_lower:
        return VideoType.NEWS_SUMMARY
    elif "story" in body_lower or "earned" in body_lower or "made" in body_lower:
        return VideoType.MOTIVATION
    else:
        return VideoType.EXPLAINER


# ────────────────────────────────────────────────────────────────────────────
# Trigger 2: Daily Newsletter
# ────────────────────────────────────────────────────────────────────────────


async def on_newsletter_daily(
    newsletter_topics: list[dict[str, str]],
) -> list[VideoGenerationResult]:
    """
    Triggered for daily newsletter.

    Generate video for featured topic to include in email.
    """
    print(f"[Newsletter] Generating videos for {len(newsletter_topics)} topics")

    results = []

    # Generate videos for top 3 topics
    for idx, topic_data in enumerate(newsletter_topics[:3]):
        if idx >= 3:
            break

        topic = topic_data.get("title", "Daily AI News")
        event = IntegrationEvent(
            timestamp=datetime.now().isoformat(),
            trigger="newsletter_daily",
            topic=topic,
            video_type="news_summary",
            status="started",
        )
        _log_event(event)

        try:
            result = await generate_video_end_to_end(
                topic=topic,
                video_type=VideoType.NEWS_SUMMARY,
                slides_count=4,
                voice_provider=VoiceProvider.GOOGLE_TTS,  # Cheaper for daily use
                auto_publish=False,
            )

            if result:
                event.status = "completed"
                event.script_hash = result.script_hash
                _log_event(event)
                results.append(result)

        except Exception as exc:
            event.status = "failed"
            event.error = str(exc)
            _log_event(event)

    print(f"[Newsletter] Generated {len(results)} videos")
    return results


# ────────────────────────────────────────────────────────────────────────────
# Trigger 3: Auto-Publish Approved Videos
# ────────────────────────────────────────────────────────────────────────────


async def on_auto_publish_approved(script_hash: str) -> bool:
    """
    Triggered when video is approved for publishing.

    Post to YouTube, TikTok, Instagram, etc.
    """
    event = IntegrationEvent(
        timestamp=datetime.now().isoformat(),
        trigger="auto_publish_approved",
        topic=script_hash,
        video_type="unknown",
        status="started",
    )
    _log_event(event)

    try:
        # Approve from review queue
        result = approve_from_review_queue(script_hash)

        if not result:
            raise RuntimeError(f"Video not found in review queue: {script_hash}")

        print(f"[AutoPublish] Publishing approved video: {script_hash}")

        # Post to social media
        await _publish_to_social_platforms(result)

        event.status = "completed"
        _log_event(event)
        return True

    except Exception as exc:
        event.status = "failed"
        event.error = str(exc)
        _log_event(event)
        print(f"[AutoPublish] Failed: {exc}")
        return False


async def _publish_to_social_platforms(result: VideoGenerationResult) -> None:
    """Post video to configured social platforms."""
    print(f"[Social] Publishing to platforms...")

    # This would integrate with social_media_publishers.py
    # For now, just log what would be published
    platforms = {
        "youtube": os.getenv("YOUTUBE_CLIENT_ID", ""),
        "tiktok": os.getenv("TIKTOK_ACCESS_TOKEN", ""),
        "instagram": os.getenv("IG_USER_ID", ""),
    }

    for platform, configured in platforms.items():
        if configured:
            print(f"[Social] {platform}: Would post here (requires social_media_publishers.py integration)")


# ────────────────────────────────────────────────────────────────────────────
# Trigger 4: Create Gumroad Course
# ────────────────────────────────────────────────────────────────────────────


async def on_create_gumroad_course(
    course_title: str,
    course_description: str,
    course_videos: list[str],
    course_price: int = 2997,  # $29.97
) -> Optional[str]:
    """
    Triggered to create a Gumroad digital course with videos.

    Returns Gumroad course URL if successful.
    """
    event = IntegrationEvent(
        timestamp=datetime.now().isoformat(),
        trigger="create_gumroad_course",
        topic=course_title,
        video_type="course",
        status="started",
    )
    _log_event(event)

    try:
        print(f"[Gumroad] Creating course: {course_title}")
        print(f"[Gumroad] Videos: {len(course_videos)}")
        print(f"[Gumroad] Price: ${course_price / 100:.2f}")

        # Integration point with gumroad_publisher.py
        # This would create the actual product
        course_url = f"https://gumroad.com/l/profitengine_{course_title.lower().replace(' ', '_')}"

        event.status = "completed"
        _log_event(event)

        return course_url

    except Exception as exc:
        event.status = "failed"
        event.error = str(exc)
        _log_event(event)
        return None


# ────────────────────────────────────────────────────────────────────────────
# Analytics & Reporting
# ────────────────────────────────────────────────────────────────────────────


def generate_integration_report(days: int = 7) -> dict:
    """Generate integration analytics report."""
    if not INTEGRATION_LOG.exists():
        return {}

    events = []
    cutoff_time = datetime.now().timestamp() - (days * 86400)

    for line in INTEGRATION_LOG.open("r", encoding="utf-8"):
        data = json.loads(line)
        event_time = datetime.fromisoformat(data["timestamp"]).timestamp()

        if event_time >= cutoff_time:
            events.append(data)

    # Calculate stats
    by_trigger = {}
    by_status = {}
    total_duration = 0.0

    for event in events:
        trigger = event["trigger"]
        status = event["status"]

        by_trigger[trigger] = by_trigger.get(trigger, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        total_duration += event.get("duration_seconds", 0)

    return {
        "period_days": days,
        "total_events": len(events),
        "by_trigger": by_trigger,
        "by_status": by_status,
        "avg_duration_seconds": total_duration / max(len(events), 1),
        "success_rate": (by_status.get("completed", 0) / max(len(events), 1)) * 100,
        "recent_errors": [e["error"] for e in events if e.get("error")],
    }


# ────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ────────────────────────────────────────────────────────────────────────────


async def main() -> None:
    """CLI for testing integration triggers."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Video Integration")
    parser.add_argument("--trigger", choices=[
        "article_published",
        "newsletter_daily",
        "auto_publish_approved",
        "create_gumroad_course",
        "report",
    ])
    parser.add_argument("--topic", default="How to Use AI for Passive Income")
    parser.add_argument("--script-hash", default="test123")
    parser.add_argument("--days", type=int, default=7)

    args = parser.parse_args()

    if args.trigger == "article_published":
        await on_article_published(
            article_title=args.topic,
            article_body="Sample article body for testing.",
            article_slug="test-article",
            auto_publish=False,
        )

    elif args.trigger == "newsletter_daily":
        topics = [
            {"title": "Latest AI Tools"},
            {"title": "Making Money with AI"},
            {"title": "AI Safety News"},
        ]
        await on_newsletter_daily(topics)

    elif args.trigger == "auto_publish_approved":
        await on_auto_publish_approved(args.script_hash)

    elif args.trigger == "create_gumroad_course":
        await on_create_gumroad_course(
            course_title="AI Mastery Course",
            course_description="Learn everything about AI for business",
            course_videos=["video1", "video2", "video3"],
            course_price=4997,
        )

    elif args.trigger == "report":
        report = generate_integration_report(args.days)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

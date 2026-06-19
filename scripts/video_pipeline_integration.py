#!/usr/bin/env python3
"""
Video Generation Pipeline Integration for ProfitEngine.

Full end-to-end pipeline: Article → Script → Audio → Video → YouTube Upload

Integrates:
1. Article metadata extraction (title, description, body)
2. AI script generation (from ai_video_generator.py)
3. Voice-over synthesis (ElevenLabs, Google TTS, or Pyttsx3)
4. Video rendering (slideshow with images and audio)
5. YouTube publishing (OAuth 2.0 with refresh token)

This module provides a unified interface to:
- Generate videos from articles
- Manage the entire pipeline with quality gates
- Handle failures gracefully with fallbacks
- Track video generation history and metrics
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Import video generation and publishing modules
try:
    from scripts.ai_video_generator import (
        VideoType,
        VoiceProvider,
        VoiceQuality,
        VideoGenerationResult,
        topic_to_script,
        script_to_voiceover,
        generate_ai_video,
        publish_to_youtube,
        move_to_review_queue,
        upload_video_to_github,
    )
except ImportError as e:
    print(f"[WARNING] Video generation modules not available: {e}")
    VideoType = None
    VoiceProvider = None

try:
    from scripts.social_media_publishers import publish_youtube as publish_youtube_social
except ImportError as e:
    print(f"[WARNING] Social media publishers not available: {e}")
    publish_youtube_social = None

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────

VIDEO_PIPELINE_LOG = pathlib.Path(os.getenv(
    "VIDEO_PIPELINE_LOG",
    "./datacenter/ai_video_pipeline/pipeline.log"
))
VIDEO_PIPELINE_LOG.parent.mkdir(parents=True, exist_ok=True)

# Quality gates
MIN_ARTICLE_LENGTH = int(os.getenv("MIN_ARTICLE_LENGTH", "500"))
MAX_ARTICLE_LENGTH = int(os.getenv("MAX_ARTICLE_LENGTH", "50000"))
MIN_SCRIPT_LENGTH = int(os.getenv("MIN_SCRIPT_LENGTH", "500"))
MAX_SCRIPT_LENGTH = int(os.getenv("MAX_SCRIPT_LENGTH", "2000"))

# Video generation preferences
DEFAULT_VIDEO_TYPE = os.getenv("DEFAULT_VIDEO_TYPE", "explainer").lower()
DEFAULT_VOICE_PROVIDER = os.getenv("DEFAULT_VOICE_PROVIDER", "elevenlabs").lower()
DEFAULT_SLIDES = int(os.getenv("DEFAULT_SLIDES", "5"))

# YouTube auto-publish settings
AUTO_PUBLISH_TO_YOUTUBE = os.getenv("AUTO_PUBLISH_TO_YOUTUBE", "false").lower() == "true"

# ────────────────────────────────────────────────────────────────────────────
# Data Classes
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class Article:
    """Article metadata for video generation."""
    title: str
    meta_description: str
    body: str
    tags: list[str] | None = None
    featured_image_url: str = ""
    canonical_url: str = ""
    author: str = ""
    published_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility."""
        return {
            "title": self.title,
            "meta_description": self.meta_description,
            "body": self.body,
            "tags": self.tags or [],
            "featured_image_url": self.featured_image_url,
            "canonical_url": self.canonical_url,
            "author": self.author,
            "published_date": self.published_date,
        }


@dataclass
class VideoPipelineResult:
    """Result of end-to-end video pipeline."""
    article_title: str
    script_hash: str
    video_path: str
    video_size_bytes: int
    video_duration_seconds: float
    youtube_url: Optional[str] = None
    github_url: Optional[str] = None
    voice_provider: str = ""
    needs_review: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ────────────────────────────────────────────────────────────────────────────
# Quality Gates
# ────────────────────────────────────────────────────────────────────────────


def validate_article(article: Article) -> tuple[bool, str]:
    """
    Validate article for video generation.

    Returns: (is_valid, error_message)
    """
    if not article.title or len(article.title) < 10:
        return False, "Title too short (min 10 chars)"

    if not article.meta_description or len(article.meta_description) < 20:
        return False, "Meta description too short (min 20 chars)"

    body_length = len(article.body)
    if body_length < MIN_ARTICLE_LENGTH:
        return False, f"Article too short ({body_length} < {MIN_ARTICLE_LENGTH} chars)"

    if body_length > MAX_ARTICLE_LENGTH:
        return False, f"Article too long ({body_length} > {MAX_ARTICLE_LENGTH} chars)"

    return True, ""


# ────────────────────────────────────────────────────────────────────────────
# Video Generation Pipeline
# ────────────────────────────────────────────────────────────────────────────


async def article_to_video(
    article: Article,
    video_type: str = DEFAULT_VIDEO_TYPE,
    voice_provider: str = DEFAULT_VOICE_PROVIDER,
    slides_count: int = DEFAULT_SLIDES,
    auto_publish: bool = AUTO_PUBLISH_TO_YOUTUBE,
    publish_to_youtube_flag: bool = True,
) -> VideoPipelineResult:
    """
    Full end-to-end pipeline: Article → Script → Voice → Video → YouTube.

    This is the main entry point for generating videos from articles.

    Args:
        article: Article data with title, description, body
        video_type: Type of video (explainer, tutorial, news_summary, etc.)
        voice_provider: Voice service (elevenlabs, google_tts, pyttsx3)
        slides_count: Number of slides to generate (3-12)
        auto_publish: Whether to automatically publish after generation
        publish_to_youtube_flag: Whether to attempt YouTube upload

    Returns:
        VideoPipelineResult with video path, URLs, and metadata

    Raises:
        ValueError: If article validation fails
        RuntimeError: If pipeline steps fail
    """
    # Step 0: Validate article
    logger.info(f"[VIDEO] Starting pipeline for article: {article.title}")
    is_valid, error_msg = validate_article(article)
    if not is_valid:
        logger.error(f"[VIDEO] Article validation failed: {error_msg}")
        return VideoPipelineResult(
            article_title=article.title,
            script_hash="",
            video_path="",
            video_size_bytes=0,
            video_duration_seconds=0,
            error=f"Article validation failed: {error_msg}",
            needs_review=True,
        )

    try:
        # Map string enums to actual types
        if VideoType is None:
            raise RuntimeError("Video generation modules not available")

        video_type_enum = VideoType(video_type.lower())
        voice_provider_enum = VoiceProvider(voice_provider.lower())

        # Step 1: Generate script from article title/description
        logger.info("[VIDEO] Step 1: Generating AI script...")
        script = await topic_to_script(
            topic=article.title,
            video_type=video_type_enum,
            slides_count=slides_count,
        )
        logger.info(f"[VIDEO] Script generated: {script.hash} ({len(script.slides)} slides)")

        # Step 2: Generate voice-over from script
        logger.info(f"[VIDEO] Step 2: Generating voice-over ({voice_provider})...")
        voice = await script_to_voiceover(
            script=script,
            provider=voice_provider_enum,
            quality=VoiceQuality.STANDARD,
        )
        logger.info(f"[VIDEO] Voice-over generated: {voice.duration_seconds:.1f}s ({voice.provider})")

        # Step 3: Render video (slides + audio)
        logger.info("[VIDEO] Step 3: Rendering video...")
        video_result = await generate_ai_video(
            script=script,
            voice=voice,
            topic=article.title,
        )
        logger.info(f"[VIDEO] Video rendered: {video_result.video_path} ({video_result.size_bytes / 1024 / 1024:.1f}MB)")

        # Step 4: Upload to GitHub for hosting
        logger.info("[VIDEO] Step 4: Uploading to GitHub...")
        github_url = await upload_video_to_github(video_result)
        if github_url:
            video_result.public_url = github_url
            logger.info(f"[VIDEO] GitHub upload successful: {github_url}")

        # Step 5: Publish to YouTube
        youtube_url = None
        if publish_to_youtube_flag:
            logger.info("[VIDEO] Step 5: Publishing to YouTube...")
            # Convert article to dict format for YouTube publisher
            article_dict = article.to_dict()
            try:
                youtube_url = await publish_to_youtube(
                    video_result=video_result,
                    title=article.title,
                    description=article.meta_description,
                    tags=article.tags or ["finance", "investing", "profitengine"],
                )
                if youtube_url:
                    logger.info(f"[VIDEO] YouTube upload successful: {youtube_url}")
                else:
                    logger.warning("[VIDEO] YouTube upload returned no URL")
            except Exception as e:
                logger.warning(f"[VIDEO] YouTube upload failed: {e}")

        # Step 6: Move to review queue if needed
        if video_result.needs_review:
            logger.info("[VIDEO] Moving to review queue...")
            move_to_review_queue(
                video_result,
                reason="Auto-generated video ready for review"
            )

        # Build result
        pipeline_result = VideoPipelineResult(
            article_title=article.title,
            script_hash=video_result.script_hash,
            video_path=video_result.video_path,
            video_size_bytes=video_result.size_bytes,
            video_duration_seconds=video_result.duration_seconds,
            youtube_url=youtube_url,
            github_url=github_url,
            voice_provider=voice.provider,
            needs_review=video_result.needs_review,
        )

        logger.info("[VIDEO] Pipeline complete!")
        logger.info(f"[VIDEO] Result: {json.dumps(pipeline_result.to_dict(), indent=2)}")
        return pipeline_result

    except Exception as e:
        logger.error(f"[VIDEO] Pipeline failed: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[VIDEO] Traceback: {traceback.format_exc()}")

        return VideoPipelineResult(
            article_title=article.title,
            script_hash="",
            video_path="",
            video_size_bytes=0,
            video_duration_seconds=0,
            error=f"Pipeline failed: {str(e)}",
            needs_review=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# Batch Processing
# ────────────────────────────────────────────────────────────────────────────


async def process_articles_batch(
    articles: list[Article],
    video_type: str = DEFAULT_VIDEO_TYPE,
    voice_provider: str = DEFAULT_VOICE_PROVIDER,
    max_concurrent: int = 1,  # Don't overwhelm YouTube/Google APIs
) -> list[VideoPipelineResult]:
    """
    Process multiple articles concurrently (with rate limiting).

    Args:
        articles: List of Article objects
        video_type: Video type for all articles
        voice_provider: Voice provider for all articles
        max_concurrent: Max concurrent pipeline runs

    Returns:
        List of VideoPipelineResult objects
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(article: Article) -> VideoPipelineResult:
        async with semaphore:
            return await article_to_video(
                article=article,
                video_type=video_type,
                voice_provider=voice_provider,
            )

    logger.info(f"[VIDEO] Processing {len(articles)} articles (max {max_concurrent} concurrent)")
    results = await asyncio.gather(
        *[process_with_semaphore(article) for article in articles],
        return_exceptions=False,
    )

    successful = sum(1 for r in results if r.error is None)
    logger.info(f"[VIDEO] Batch complete: {successful}/{len(articles)} successful")

    return results


# ────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ────────────────────────────────────────────────────────────────────────────


async def main() -> None:
    """CLI interface for video pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Video Generation Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    # Generate command
    gen = subparsers.add_parser("generate", help="Generate video from article")
    gen.add_argument("--title", required=True, help="Article title")
    gen.add_argument("--meta", required=True, help="Meta description")
    gen.add_argument("--body", required=True, help="Article body (or file path)")
    gen.add_argument("--type", default=DEFAULT_VIDEO_TYPE, help="Video type")
    gen.add_argument("--voice", default=DEFAULT_VOICE_PROVIDER, help="Voice provider")
    gen.add_argument("--slides", type=int, default=DEFAULT_SLIDES)
    gen.add_argument("--no-youtube", action="store_true", help="Skip YouTube upload")

    args = parser.parse_args()

    if args.command == "generate":
        # Load body from file if it looks like a path
        body_text = args.body
        if pathlib.Path(args.body).exists():
            body_text = pathlib.Path(args.body).read_text()

        article = Article(
            title=args.title,
            meta_description=args.meta,
            body=body_text,
        )

        result = await article_to_video(
            article=article,
            video_type=args.type,
            voice_provider=args.voice,
            slides_count=args.slides,
            publish_to_youtube_flag=not args.no_youtube,
        )

        print(json.dumps(result.to_dict(), indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(name)s: %(message)s",
    )
    asyncio.run(main())

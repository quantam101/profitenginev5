#!/usr/bin/env python3
"""
AI Video Generator Examples & Integration Patterns.

Demonstrates:
1. End-to-end video generation pipeline
2. Batch video generation from article queue
3. Integration with email & social systems
4. Review queue automation
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from dataclasses import asdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ai_video_generator import (
    VideoType,
    VoiceProvider,
    generate_video_end_to_end,
    approve_from_review_queue,
)


# ────────────────────────────────────────────────────────────────────────────
# Example 1: Simple Explainer Video
# ────────────────────────────────────────────────────────────────────────────


async def example_simple_explainer() -> None:
    """Generate a simple explainer video about AI automation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Simple Explainer Video")
    print("=" * 80)

    result = await generate_video_end_to_end(
        topic="How to Automate Your Email Marketing with AI",
        video_type=VideoType.EXPLAINER,
        slides_count=5,
        voice_provider=VoiceProvider.ELEVENLABS,
        auto_publish=False,
    )

    if result:
        print("\nGeneration successful!")
        print(json.dumps(asdict(result), indent=2, default=str))


# ────────────────────────────────────────────────────────────────────────────
# Example 2: Tutorial Video with Multiple Slides
# ────────────────────────────────────────────────────────────────────────────


async def example_tutorial_video() -> None:
    """Generate a detailed tutorial video."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Tutorial Video (8 Slides)")
    print("=" * 80)

    result = await generate_video_end_to_end(
        topic="Complete Guide to Building AI Chatbots for Your Business",
        video_type=VideoType.TUTORIAL,
        slides_count=8,
        voice_provider=VoiceProvider.GOOGLE_TTS,  # Fallback to Google TTS
        auto_publish=False,
    )

    if result:
        print("\nTutorial video generated!")
        print(f"Video: {result.video_path}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"Size: {result.size_bytes / 1024 / 1024:.1f} MB")


# ────────────────────────────────────────────────────────────────────────────
# Example 3: Product Demo Video
# ────────────────────────────────────────────────────────────────────────────


async def example_product_demo() -> None:
    """Generate a product demo/comparison video."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Product Demo Video")
    print("=" * 80)

    result = await generate_video_end_to_end(
        topic="Top 5 AI Writing Tools Compared: Which is Best for Your Business?",
        video_type=VideoType.PRODUCT_DEMO,
        slides_count=6,
        voice_provider=VoiceProvider.PYTTSX3,  # Free local option
        auto_publish=False,
    )

    if result:
        print(f"\nProduct demo video ready!")
        print(f"Script hash: {result.script_hash}")
        if result.public_url:
            print(f"Public URL: {result.public_url}")


# ────────────────────────────────────────────────────────────────────────────
# Example 4: News Summary Video
# ────────────────────────────────────────────────────────────────────────────


async def example_news_summary() -> None:
    """Generate a trending news summary video."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: News Summary Video")
    print("=" * 80)

    result = await generate_video_end_to_end(
        topic="Latest AI Breakthroughs This Week (GPT-5, Multimodal Models)",
        video_type=VideoType.NEWS_SUMMARY,
        slides_count=5,
        voice_provider=VoiceProvider.ELEVENLABS,
        auto_publish=True,  # Schedule for auto-publish
    )

    if result:
        print(f"\nNews summary video queued for auto-publish!")
        print(f"Needs review: {result.needs_review}")


# ────────────────────────────────────────────────────────────────────────────
# Example 5: Batch Generation from Article Queue
# ────────────────────────────────────────────────────────────────────────────


async def example_batch_from_queue() -> None:
    """Generate multiple videos from article queue."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Batch Video Generation from Article Queue")
    print("=" * 80)

    articles = [
        {
            "topic": "10 AI Tools That Replaced My Entire Marketing Team",
            "type": VideoType.EXPLAINER,
            "slides": 6,
        },
        {
            "topic": "How I Made $10K With AI-Generated Digital Products",
            "type": VideoType.MOTIVATION,
            "slides": 5,
        },
        {
            "topic": "Complete ChatGPT Prompt Library for Passive Income",
            "type": VideoType.EDUCATIONAL,
            "slides": 8,
        },
    ]

    results = []
    for article in articles:
        print(f"\nGenerating video for: {article['topic']}")

        result = await generate_video_end_to_end(
            topic=article["topic"],
            video_type=article["type"],
            slides_count=article["slides"],
            voice_provider=VoiceProvider.ELEVENLABS,
            auto_publish=False,
        )

        if result:
            results.append(result)
            print(f"✓ Generated: {result.script_hash}")

    print(f"\n✓ Batch complete: {len(results)} videos generated")
    print(json.dumps([asdict(r) for r in results], indent=2, default=str))


# ────────────────────────────────────────────────────────────────────────────
# Example 6: Review Queue Management
# ────────────────────────────────────────────────────────────────────────────


async def example_review_workflow() -> None:
    """Demonstrate review queue workflow."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Review Queue Workflow")
    print("=" * 80)

    # Step 1: Generate video
    print("\nStep 1: Generating video...")
    result = await generate_video_end_to_end(
        topic="The Future of AI in Business 2026",
        video_type=VideoType.EDUCATIONAL,
        slides_count=5,
        voice_provider=VoiceProvider.ELEVENLABS,
        auto_publish=False,
    )

    if not result:
        print("Generation failed!")
        return

    print(f"✓ Video generated: {result.script_hash}")

    # Step 2: Simulate manual review (wait for approval)
    print("\nStep 2: Video moved to review queue")
    print(f"Script hash: {result.script_hash}")
    print("Waiting for manual approval...")
    print("(In production, a human reviews video quality)")

    # Step 3: Approve from review queue
    print("\nStep 3: Approving video...")
    approved = approve_from_review_queue(result.script_hash)

    if approved:
        print(f"✓ Video approved!")
        print(f"Ready for publishing: {approved.video_path}")


# ────────────────────────────────────────────────────────────────────────────
# Example 7: Integration with Email Campaigns
# ────────────────────────────────────────────────────────────────────────────


async def example_email_integration() -> None:
    """Generate videos optimized for email promotion."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Email Campaign Video Generation")
    print("=" * 80)

    print("Generating video optimized for email promotion...")

    result = await generate_video_end_to_end(
        topic="Exclusive: How to Use AI for Affiliate Marketing (Email Subscribers Only)",
        video_type=VideoType.EDUCATIONAL,
        slides_count=7,
        voice_provider=VoiceProvider.ELEVENLABS,
        auto_publish=False,
    )

    if result:
        # Create email campaign data
        email_campaign = {
            "campaign_name": "AI Affiliate Marketing Exclusive",
            "video_title": "How to Use AI for Affiliate Marketing",
            "video_url": result.public_url or result.video_path,
            "thumbnail_url": None,  # Would be generated from first slide
            "video_duration": f"{result.duration_seconds:.0f}s",
            "description": "Discover AI-powered techniques to increase affiliate revenue.",
            "cta_text": "Watch Video",
            "email_subject": "New video: Make $5K/month with AI + affiliate marketing",
        }

        print("\nEmail campaign metadata:")
        print(json.dumps(email_campaign, indent=2))


# ────────────────────────────────────────────────────────────────────────────
# Example 8: Voice Provider Comparison
# ────────────────────────────────────────────────────────────────────────────


async def example_voice_provider_comparison() -> None:
    """Compare different voice providers for same topic."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Voice Provider Comparison")
    print("=" * 80)

    topic = "5 AI Tools That Save Me 10 Hours Weekly"
    providers = [
        VoiceProvider.ELEVENLABS,
        VoiceProvider.GOOGLE_TTS,
        VoiceProvider.PYTTSX3,
    ]

    results = {}

    for provider in providers:
        print(f"\nGenerating with {provider.value}...")

        result = await generate_video_end_to_end(
            topic=topic,
            video_type=VideoType.EXPLAINER,
            slides_count=5,
            voice_provider=provider,
            auto_publish=False,
        )

        if result:
            results[provider.value] = {
                "file_size_mb": result.size_bytes / 1024 / 1024,
                "duration_seconds": result.duration_seconds,
                "video_path": result.video_path,
            }

    print("\n=== Comparison Results ===")
    print(json.dumps(results, indent=2))


# ────────────────────────────────────────────────────────────────────────────
# Example 9: Video Type Comparison
# ────────────────────────────────────────────────────────────────────────────


async def example_video_type_comparison() -> None:
    """Generate same topic as different video types."""
    print("\n" + "=" * 80)
    print("EXAMPLE 9: Video Type Comparison")
    print("=" * 80)

    base_topic = "Making Money with AI"
    types = [
        (VideoType.EXPLAINER, 5),
        (VideoType.TUTORIAL, 8),
        (VideoType.MOTIVATION, 4),
        (VideoType.NEWS_SUMMARY, 6),
    ]

    results = {}

    for video_type, slides in types:
        print(f"\nGenerating {video_type.value}...")

        result = await generate_video_end_to_end(
            topic=f"{base_topic} ({video_type.value})",
            video_type=video_type,
            slides_count=slides,
            voice_provider=VoiceProvider.ELEVENLABS,
            auto_publish=False,
        )

        if result:
            results[video_type.value] = {
                "slides": slides,
                "duration_seconds": result.duration_seconds,
                "file_size_mb": result.size_bytes / 1024 / 1024,
            }

    print("\n=== Video Type Comparison ===")
    print(json.dumps(results, indent=2))


# ────────────────────────────────────────────────────────────────────────────
# Example 10: Motivation/Inspiration Video
# ────────────────────────────────────────────────────────────────────────────


async def example_motivation_video() -> None:
    """Generate an inspiring success story video."""
    print("\n" + "=" * 80)
    print("EXAMPLE 10: Motivation/Inspiration Video")
    print("=" * 80)

    result = await generate_video_end_to_end(
        topic="From $0 to $50K/Month: My Complete AI Business Story",
        video_type=VideoType.MOTIVATION,
        slides_count=7,
        voice_provider=VoiceProvider.ELEVENLABS,
        auto_publish=False,
    )

    if result:
        print("\n✓ Motivation video generated!")
        print("Perfect for:")
        print("  - YouTube channel growth")
        print("  - Email list building")
        print("  - Social media engagement")
        print("  - Lead generation campaigns")


# ────────────────────────────────────────────────────────────────────────────
# Main Menu
# ────────────────────────────────────────────────────────────────────────────


async def main() -> None:
    """Interactive example menu."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  AI VIDEO GENERATOR — EXAMPLES & INTEGRATION PATTERNS".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")

    examples = [
        ("Simple Explainer Video", example_simple_explainer),
        ("Tutorial Video (8 slides)", example_tutorial_video),
        ("Product Demo Video", example_product_demo),
        ("News Summary Video", example_news_summary),
        ("Batch Generation from Queue", example_batch_from_queue),
        ("Review Queue Workflow", example_review_workflow),
        ("Email Campaign Integration", example_email_integration),
        ("Voice Provider Comparison", example_voice_provider_comparison),
        ("Video Type Comparison", example_video_type_comparison),
        ("Motivation/Inspiration Video", example_motivation_video),
    ]

    print("\nAvailable Examples:\n")
    for idx, (name, _) in enumerate(examples, 1):
        print(f"  {idx}. {name}")

    print("\nUsage:")
    print("  python scripts/ai_video_examples.py <number>")
    print("  python scripts/ai_video_examples.py 1    # Run example 1")
    print("  python scripts/ai_video_examples.py all  # Run all examples")

    import sys
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg.lower() == "all":
            for name, func in examples:
                try:
                    await func()
                except Exception as e:
                    print(f"\n✗ Example failed: {e}")
            print("\n" + "=" * 80)
            print("All examples completed!")
        else:
            try:
                idx = int(arg) - 1
                if 0 <= idx < len(examples):
                    await examples[idx][1]()
                else:
                    print(f"Invalid example number: {arg}")
            except ValueError:
                print(f"Invalid argument: {arg}")


if __name__ == "__main__":
    asyncio.run(main())

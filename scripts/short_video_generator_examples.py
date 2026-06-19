#!/usr/bin/env python3
"""Examples and recipes for short_video_generator.py

Demonstrates common usage patterns and integration scenarios.
"""

from pathlib import Path
from scripts.short_video_generator import (
    article_to_keypoints,
    generate_short_video,
    VideoConfig,
    add_to_queue,
    list_queue,
    update_queue_status,
)


# ============================================================================
# Example 1: Simple Tips Video
# ============================================================================


def example_simple_tips():
    """Generate a quick tips video from an article."""
    print("\n=== Example 1: Simple Tips Video ===\n")

    article = """
    # 5 Easy Investment Tips for Beginners

    Starting to invest can feel overwhelming, but these simple tips can help:

    ## Tip 1: Start Small
    **You don't need a lot of money to begin investing.** Many platforms let you start with just $1.
    This removes the biggest barrier: the psychological weight of a large commitment.

    ## Tip 2: Automate Your Investments
    **Set up automatic deposits.** Consistency matters more than timing.
    A small monthly investment beats waiting for the perfect moment.

    ## Tip 3: Diversify Your Portfolio
    **Don't put all eggs in one basket.** A mix of stocks, bonds, and other assets reduces risk.
    Index funds make diversification simple for beginners.

    ## Tip 4: Keep Costs Low
    **Pay attention to fees.** High fees erode returns over time.
    Choose low-cost index funds or ETFs when possible.

    ## Tip 5: Think Long-Term
    **Don't panic during market dips.** History shows markets recover and grow over time.
    The longer you stay invested, the better your returns tend to be.
    """

    config = VideoConfig(
        style="tips",
        duration_sec=30,
        background_music=True,
        voice_gender="neutral"
    )

    output_dir = Path("videos/example_tips")
    results = generate_short_video(
        article=article,
        article_title="5 Investment Tips for Beginners",
        output_dir=output_dir,
        config=config,
        formats=["reels", "shorts"]
    )

    print(f"Generated videos:")
    for fmt, path in results.items():
        print(f"  ✓ {fmt}: {path}")

    # Add to queue for review
    queue_ids = add_to_queue(results, "investment_tips.md", Path("videos/queue"))
    print(f"\nQueued for review: {queue_ids}")

    return results


# ============================================================================
# Example 2: Tutorial Video (Longer Format)
# ============================================================================


def example_tutorial_video():
    """Generate a tutorial video with step-by-step instructions."""
    print("\n=== Example 2: Tutorial Video ===\n")

    article = """
    # How to Open an Investment Account in 5 Minutes

    Opening an investment account is easier than ever. Here's exactly what to do:

    **Step 1: Choose a Platform**
    Popular beginner-friendly platforms include Fidelity, Vanguard, Charles Schwab, and Acorns.
    Most offer free accounts with no minimum deposit.

    **Step 2: Create Your Account**
    Visit the platform's website and click "Sign Up" or "Get Started".
    You'll need your email, Social Security number, and basic identification.

    **Step 3: Verify Your Identity**
    Most platforms verify your identity instantly.
    You may need to take a photo of your ID for security.

    **Step 4: Link Your Bank Account**
    Connect the checking or savings account where you'll fund investments.
    This usually takes 1-2 business days.

    **Step 5: Make Your First Investment**
    Choose a low-cost index fund or target-date fund.
    Even $1 counts! The important part is getting started.
    """

    config = VideoConfig(
        style="tutorial",
        duration_sec=45,
        background_music=True,
        voice_gender="female",
        voice_speed=1.0
    )

    output_dir = Path("videos/example_tutorial")
    results = generate_short_video(
        article=article,
        article_title="How to Open an Investment Account",
        output_dir=output_dir,
        config=config,
        formats=["youtube", "reels"]
    )

    print(f"Generated tutorial videos:")
    for fmt, path in results.items():
        print(f"  ✓ {fmt}: {path}")

    return results


# ============================================================================
# Example 3: Quote/Inspiration Video
# ============================================================================


def example_quote_video():
    """Generate a short inspirational quote video."""
    print("\n=== Example 3: Quote/Inspiration Video ===\n")

    article = """
    # Warren Buffett's Investment Wisdom

    **"The most important thing is your behavior as an investor. The ones who do well are the ones
    who don't panic during corrections."**

    This simple insight contains decades of market wisdom. Here's why it matters:

    Market corrections (10-20% declines) happen every few years. Historically, they're temporary.
    Investors who sell during corrections lock in losses.

    Those who stay calm and hold steady—or even buy more—end up with significantly higher returns.

    The psychological challenge of investing is bigger than the technical challenge.

    Start small. Stay consistent. Don't panic. That's the formula.
    """

    config = VideoConfig(
        style="quote",
        duration_sec=20,
        background_music=True,
        voice_gender="male"
    )

    output_dir = Path("videos/example_quote")
    results = generate_short_video(
        article=article,
        article_title="Investment Wisdom from Warren Buffett",
        output_dir=output_dir,
        config=config,
        formats=["reels", "tiktok", "instagram_square"]
    )

    print(f"Generated quote videos:")
    for fmt, path in results.items():
        print(f"  ✓ {fmt}: {path}")

    return results


# ============================================================================
# Example 4: News/Update Video
# ============================================================================


def example_news_video():
    """Generate a news/update video about market trends."""
    print("\n=== Example 4: News/Update Video ===\n")

    article = """
    # Market Update: What Recent Fed Decisions Mean for Your Portfolio

    The Federal Reserve recently announced changes to interest rates. Here's what that means:

    **Interest Rates Going Down**
    Lower rates typically boost stock and bond prices. Borrowing becomes cheaper.
    This generally helps companies with existing debt and consumers with mortgages.

    **What This Means for Stocks**
    Historically, falling rates have supported stock market growth.
    However, the timing and magnitude matter significantly.

    **What This Means for Bonds**
    Bond prices rise when rates fall. This is good news if you own bonds.
    New bonds will offer lower interest payments.

    **Your Action Plan**
    1. Don't overreact to short-term changes
    2. Stay diversified across asset types
    3. Remember your long-term investment goals
    4. Consider rebalancing if needed

    Market changes are normal. Your strategy should stay consistent.
    """

    config = VideoConfig(
        style="news",
        duration_sec=40,
        background_music=True,
        voice_gender="neutral"
    )

    output_dir = Path("videos/example_news")
    results = generate_short_video(
        article=article,
        article_title="Understanding Fed Interest Rate Changes",
        output_dir=output_dir,
        config=config,
        formats=["youtube", "shorts"]
    )

    print(f"Generated news videos:")
    for fmt, path in results.items():
        print(f"  ✓ {fmt}: {path}")

    return results


# ============================================================================
# Example 5: Queue Management Workflow
# ============================================================================


def example_queue_workflow():
    """Demonstrate the review queue workflow."""
    print("\n=== Example 5: Queue Management Workflow ===\n")

    queue_dir = Path("videos/queue")

    # List all queued videos
    print("Current queue:")
    items = list_queue(queue_dir)

    if not items:
        print("  (queue is empty)")
        return

    pending_count = 0
    approved_count = 0

    for item in items:
        status_icon = "⏳" if item.status == "pending_review" else "✓"
        print(f"  {status_icon} {item.video_id}")
        print(f"     Format: {item.format_type} | Status: {item.status}")

        if item.status == "pending_review":
            pending_count += 1
        elif item.status == "approved":
            approved_count += 1

    print(f"\nSummary: {pending_count} pending, {approved_count} approved")

    # Simulate approving a video
    if pending_count > 0:
        first_pending = next(item for item in items if item.status == "pending_review")
        print(f"\nApproving: {first_pending.video_id}")
        update_queue_status(queue_dir, first_pending.video_id, "approved",
                          notes="Good quality, ready for posting")


# ============================================================================
# Example 6: Key Point Extraction Only
# ============================================================================


def example_extract_keypoints():
    """Extract and display key points without generating video."""
    print("\n=== Example 6: Key Point Extraction ===\n")

    article = """
    # The Power of Compound Interest

    **Compound interest is one of the most powerful forces in investing.**

    Here's the concept: when you earn returns on your investments, those returns earn their own
    returns. Money multiplies on top of itself.

    ## How It Works

    Start with $1,000 earning 10% annually.

    Year 1: $1,000 → $1,100 (earned $100)
    Year 2: $1,100 → $1,210 (earned $110, not $100!)
    Year 3: $1,210 → $1,331 (earned $121)

    Notice how the gain increases each year? That's compounding.

    ## Time is Your Greatest Asset

    A 25-year-old investing $500 monthly for 40 years will have significantly more than
    a 45-year-old investing $500 monthly for 20 years, even though the latter invests more total.

    This is because time allows compounding to work its magic.

    ## The Bottom Line

    Start investing early, even with small amounts.
    Stay invested for the long term.
    Let compound interest do the heavy lifting.
    """

    keypoints = article_to_keypoints(article, max_points=5)

    print(f"Extracted {len(keypoints)} key points:\n")
    for i, point in enumerate(keypoints, 1):
        print(f"{i}. {point.title}")
        if point.description:
            print(f"   → {point.description[:60]}...")
        print(f"   Duration: {point.duration_sec}s\n")


# ============================================================================
# Example 7: Batch Processing Multiple Articles
# ============================================================================


def example_batch_processing():
    """Generate videos for multiple articles in sequence."""
    print("\n=== Example 7: Batch Processing ===\n")

    articles = [
        {
            "title": "5 Investment Tips",
            "style": "tips",
            "duration": 30,
            "content": "Tip 1: Start small\nTip 2: Be consistent\nTip 3: Diversify\nTip 4: Keep costs low\nTip 5: Think long-term"
        },
        {
            "title": "How to Get Started",
            "style": "tutorial",
            "duration": 45,
            "content": "Step 1: Choose platform\nStep 2: Create account\nStep 3: Verify identity\nStep 4: Link bank\nStep 5: Invest"
        },
        {
            "title": "Investment Quote",
            "style": "quote",
            "duration": 20,
            "content": "\"The best time to invest was yesterday. The second best time is now.\""
        }
    ]

    all_results = {}

    for article in articles:
        print(f"\nProcessing: {article['title']}...")

        config = VideoConfig(
            style=article['style'],
            duration_sec=article['duration'],
            background_music=True
        )

        output_dir = Path("videos/batch") / article['title'].lower().replace(" ", "_")

        results = generate_short_video(
            article=article['content'],
            article_title=article['title'],
            output_dir=output_dir,
            config=config,
            formats=["reels", "shorts"]
        )

        all_results[article['title']] = results
        print(f"  ✓ Generated {len(results)} formats")

    print(f"\n=== Batch Complete ===")
    print(f"Total videos generated: {sum(len(r) for r in all_results.values())}")


# ============================================================================
# Main
# ============================================================================


if __name__ == "__main__":
    import sys

    examples = {
        "1": ("Simple tips video", example_simple_tips),
        "2": ("Tutorial video", example_tutorial_video),
        "3": ("Quote video", example_quote_video),
        "4": ("News video", example_news_video),
        "5": ("Queue workflow", example_queue_workflow),
        "6": ("Key point extraction", example_extract_keypoints),
        "7": ("Batch processing", example_batch_processing),
    }

    if len(sys.argv) > 1 and sys.argv[1] in examples:
        _, func = examples[sys.argv[1]]
        try:
            func()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Short Video Generator - Examples")
        print("=" * 50)
        for num, (name, _) in examples.items():
            print(f"  {num}. {name}")
        print(f"\nUsage: python scripts/short_video_generator_examples.py <example_number>")
        print(f"\nExample: python scripts/short_video_generator_examples.py 1")

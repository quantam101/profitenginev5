"""
SOCIAL DISTRIBUTOR EXAMPLES
Practical usage patterns for the multi-platform content distribution engine.
"""

import asyncio
import json
from datetime import datetime, timedelta
from runtime.social_distributor import SocialDistributor, SocialPost, PlatformFormatter


# ============================================================================
# EXAMPLE 1: Single Blog Post to All Platforms
# ============================================================================

async def example_distribute_blog_post():
    """
    Publish a blog post to Twitter, LinkedIn, Reddit simultaneously.
    """
    distributor = SocialDistributor()

    # Simulate content from content_gen.py
    blog_post = {
        "title": "90% Win Rate Achieved: Our AI Trading Strategy Breakdown",
        "slug": "90-percent-win-rate-ai-trading",
        "body": (
            "We've achieved a 90% win rate using momentum-based algorithms combined with "
            "machine learning sentiment analysis. Here's how our autonomous trading system works:\n\n"
            "1. **Data Collection** — Real-time market data from 50+ exchanges\n"
            "2. **Signal Generation** — AI models identify high-probability entry points\n"
            "3. **Risk Management** — Automatic stop-loss and position sizing\n"
            "4. **Execution** — Instant order placement via API\n"
            "5. **Monitoring** — 24/7 portfolio oversight\n\n"
            "The system processes 100,000+ data points daily to find profitable opportunities. "
            "Results are audited and available on our live dashboard."
        ),
        "tags": ["trading", "ai", "momentum", "strategy"],
        "meta_description": "How we achieved 90% win rate with AI-powered autonomous trading.",
    }

    # Distribute to platforms
    results = await distributor.post_all_platforms(
        content_id=blog_post["slug"],
        title=blog_post["title"],
        body=blog_post["body"],
        link="https://profitengine.alreadyherellc.com/blog/90-percent-win-rate-ai-trading",
        platforms=["twitter", "linkedin", "reddit"],
        hashtags=blog_post["tags"],
    )

    print("Distribution Results:")
    for platform, success in results.items():
        status = "✓ Posted" if success else "✗ Failed"
        print(f"  {platform.capitalize()}: {status}")

    return results


# ============================================================================
# EXAMPLE 2: Twitter Thread with Multiple Tweets
# ============================================================================

async def example_twitter_thread():
    """
    Post a Twitter thread with automated linking between replies.
    """
    distributor = SocialDistributor()

    thread_tweets = [
        "🧵 Thread: How to Build a 90%+ Win Rate Trading Bot\n\nIn the last 30 days, our AI-powered trading system hit a 90% win rate. Here's exactly what we did:",
        "1️⃣ DATA: We started by collecting 100,000+ data points daily from 50+ exchanges. Real-time price, volume, and sentiment data.",
        "2️⃣ SIGNALS: Our AI models identify high-probability entry points using momentum analysis + ML-based sentiment scoring.",
        "3️⃣ EXECUTION: Automated order placement via API within milliseconds of signals. Precision matters at scale.",
        "4️⃣ RISK: Automatic stop-loss placement + position sizing based on volatility. We never risk more than 1% per trade.",
        "5️⃣ RESULTS: 90% win rate across 500+ trades. Average profit per trade: +$250. See the live dashboard: https://profitengine.alreadyherellc.com",
        "Want to learn more? Join our community and get daily trading insights. #trading #ai #alreadyhere #autonomous",
    ]

    # Create the first tweet
    posts = distributor.create_post(
        content_id="twitter_thread_001",
        title=thread_tweets[0],
        body="Twitter thread on AI trading strategies",
        link="https://profitengine.alreadyherellc.com/blog/90-percent-win-rate-ai-trading",
        platforms=["twitter"],
        hashtags=["trading", "ai", "strategy", "alreadyhere"],
    )

    if posts:
        post = distributor.db.get_post(posts[0])
        # Post thread with sequential replies
        await distributor.post_twitter(post, thread_tweets=thread_tweets)

    return posts


# ============================================================================
# EXAMPLE 3: Video Post to TikTok and YouTube
# ============================================================================

async def example_video_distribution():
    """
    Post short video clips to TikTok and YouTube Shorts.
    Typically: screen recording of trading dashboard + performance metrics.
    """
    distributor = SocialDistributor()

    # Simulate generated video (in real scenario, this comes from FFmpeg/video generation)
    video_path = "/tmp/trading_dashboard_demo.mp4"

    results = await distributor.post_all_platforms(
        content_id="video_demo_001",
        title="Daily Trading Results: +$1,200 Profit",
        body=(
            "Watch our autonomous trading system execute 50+ profitable trades in real-time. "
            "This is what consistent passive income looks like. 🚀"
        ),
        link="https://profitengine.alreadyherellc.com",
        platforms=["tiktok", "youtube"],
        hashtags=["trading", "daytrading", "stocks", "passive_income", "ai"],
        video_path=video_path,
    )

    return results


# ============================================================================
# EXAMPLE 4: Reddit Post with Subreddit-Specific Content
# ============================================================================

async def example_reddit_distribution():
    """
    Post to multiple relevant subreddits with customized titles.
    """
    distributor = SocialDistributor()

    subreddit_content = {
        "algotrading": "Achieved 90% win rate with momentum-based algorithms",
        "stocks": "Automated trading system achieves 90% win rate",
        "trading": "How we built a 90% win rate AI trading bot",
        "passive_income": "Earning $5k/month from passive trading income",
    }

    for subreddit, title in subreddit_content.items():
        posts = await distributor.post_all_platforms(
            content_id=f"reddit_{subreddit}_001",
            title=title,
            body=(
                "Our team developed an autonomous trading system that combines "
                "real-time market data, AI signal detection, and automatic execution. "
                "90% of trades are profitable. Live dashboard: "
                "https://profitengine.alreadyherellc.com"
            ),
            link="https://profitengine.alreadyherellc.com/blog/90-percent-win-rate-ai-trading",
            platforms=["reddit"],
            hashtags=["trading", "automation", "passive_income"],
        )
        print(f"Posted to r/{subreddit}")

    return True


# ============================================================================
# EXAMPLE 5: Scheduled Weekly Digest Email
# ============================================================================

def example_schedule_email_digest():
    """
    Send automated weekly email digest every Friday at 10 AM MST.
    """
    distributor = SocialDistributor()

    # Get top 5 posts from the past week
    top_posts = distributor.db.get_top_posts_by_engagement(
        days=7,
        limit=5
    )

    # Format HTML digest
    html = PlatformFormatter.format_email_digest(top_posts)

    # Send to mailing list
    success = distributor.send_email_digest(
        recipient="dispatch@alreadyherellc.com"
    )

    print(f"Weekly digest sent: {success}")
    print(f"Top posts included: {len(top_posts)}")

    return success


# ============================================================================
# EXAMPLE 6: Schedule Automatic Daily Posting
# ============================================================================

def example_init_scheduler():
    """
    Initialize automatic posting schedule.
    Posts are created in 'draft' status and posted at scheduled times.
    """
    distributor = SocialDistributor()

    # Start scheduler (posts will run in background)
    distributor.schedule_daily_posts()

    print("Posting schedule initialized:")
    print("  Twitter: 9:00 AM & 5:00 PM MST")
    print("  LinkedIn: 9:00 AM MST")
    print("  TikTok: 5:00 PM MST")
    print("  YouTube: 5:00 PM MST")
    print("  Email Digest: Friday 10:00 AM MST")

    # Main thread continues — scheduler runs in background
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped")


# ============================================================================
# EXAMPLE 7: Monitor Engagement & Top Posts
# ============================================================================

def example_engagement_analytics():
    """
    Query engagement metrics and identify top-performing content.
    """
    distributor = SocialDistributor()

    # Get top posts from last 7 days
    top_posts = distributor.db.get_top_posts_by_engagement(
        days=7,
        limit=10
    )

    print("Top 10 Posts (Last 7 Days)")
    print("=" * 80)

    for rank, post in enumerate(top_posts, 1):
        total_engagement = (
            post.engagement_likes +
            post.engagement_retweets +
            post.engagement_comments +
            post.engagement_views
        )

        print(f"\n{rank}. {post.title}")
        print(f"   Platform: {post.platform.upper()}")
        print(f"   Posted: {post.posted_at}")
        print(f"   Likes: {post.engagement_likes}")
        print(f"   Retweets: {post.engagement_retweets}")
        print(f"   Comments: {post.engagement_comments}")
        print(f"   Views: {post.engagement_views}")
        print(f"   Total Engagement: {total_engagement}")

    # Calculate metrics
    total_posts = len(top_posts)
    avg_engagement = sum(
        (p.engagement_likes + p.engagement_retweets +
         p.engagement_comments + p.engagement_views)
        for p in top_posts
    ) / max(total_posts, 1)

    print(f"\n{'=' * 80}")
    print(f"Summary: {total_posts} posts, avg engagement {avg_engagement:.0f}")

    return top_posts


# ============================================================================
# EXAMPLE 8: Duplicate Detection & Prevention
# ============================================================================

def example_duplicate_detection():
    """
    Demonstrate how duplicate detection prevents posting same content twice.
    """
    distributor = SocialDistributor()

    content_id = "trading_101_001"
    title = "5 Signals for Profitable Trading"
    body = "Learn the 5 key signals that predict profitable trades with 90% accuracy."
    link = "https://profitengine.alreadyherellc.com/blog/5-trading-signals"

    # First post
    posts_1 = distributor.create_post(
        content_id=content_id,
        title=title,
        body=body,
        link=link,
        platforms=["twitter", "linkedin"],
    )
    print(f"First post created: {len(posts_1)} posts")

    # Try to post same content again
    posts_2 = distributor.create_post(
        content_id=content_id,
        title=title,
        body=body,
        link=link,
        platforms=["twitter", "linkedin"],  # Will be skipped
    )
    print(f"Second post attempt: {len(posts_2)} posts (should be 0)")

    # Check directly
    for platform in ["twitter", "linkedin"]:
        is_dup = distributor.db.check_duplicate(platform, content_id)
        print(f"  {platform}: duplicate = {is_dup}")

    return True


# ============================================================================
# EXAMPLE 9: Platform-Specific Formatting
# ============================================================================

def example_platform_formatting():
    """
    Show how content is formatted for each platform.
    """
    post = SocialPost(
        platform="twitter",
        title="90% Win Rate Trading Bot",
        body="Learn how our AI system achieves 90% win rate with real-time data analysis",
        link="https://profitengine.alreadyherellc.com",
        hashtags=["trading", "ai", "alreadyhere", "autonomous"],
    )

    print("Platform-Specific Formatting")
    print("=" * 80)

    # Twitter
    twitter_text = PlatformFormatter.format_twitter(post)
    print(f"\nTwitter ({len(twitter_text)} chars):")
    print(twitter_text)

    # LinkedIn
    linkedin_text = PlatformFormatter.format_linkedin(post)
    print(f"\nLinkedIn ({len(linkedin_text)} chars):")
    print(linkedin_text[:200] + "...")

    # TikTok
    tiktok_text = PlatformFormatter.format_tiktok(post)
    print(f"\nTikTok ({len(tiktok_text)} chars):")
    print(tiktok_text)

    # YouTube
    yt_title, yt_desc = PlatformFormatter.format_youtube(post)
    print(f"\nYouTube:")
    print(f"  Title ({len(yt_title)} chars): {yt_title}")
    print(f"  Description ({len(yt_desc)} chars): {yt_desc[:100]}...")

    # Reddit
    subreddit, reddit_title, reddit_body = PlatformFormatter.format_reddit(post)
    print(f"\nReddit (r/{subreddit}):")
    print(f"  Title: {reddit_title}")
    print(f"  Body: {reddit_body[:100]}...")

    return True


# ============================================================================
# EXAMPLE 10: Integration with Content Generator
# ============================================================================

async def example_content_gen_integration():
    """
    Full pipeline: Generate content → Distribute to all platforms.
    """
    # Import content generator
    try:
        from runtime.agent_impls.content_gen import Agent as ContentGen
    except ImportError:
        print("ContentGen not available — skipping example")
        return

    # Step 1: Generate blog article
    content_gen = ContentGen()
    result = content_gen.run(
        objective="AI Trading Strategies for Consistent Passive Income",
        context="90% win rate achieved, momentum-based algorithms, machine learning sentiment analysis",
        connectors=[]
    )

    # Step 2: Parse generated article
    article_json_str = result.output.split("ARTICLE_JSON:")[1]
    article = json.loads(article_json_str)

    # Step 3: Distribute to platforms
    distributor = SocialDistributor()

    results = await distributor.post_all_platforms(
        content_id=article["slug"],
        title=article["title"],
        body=article["body"],
        link=f"https://profitengine.alreadyherellc.com/blog/{article['slug']}",
        platforms=["twitter", "linkedin", "reddit"],
        hashtags=article.get("tags", ["trading", "ai", "alreadyhere"]),
    )

    print("Content Generation → Distribution Complete")
    print(f"Article: {article['title']}")
    print(f"Distribution results: {results}")

    return results


# ============================================================================
# CLI RUNNER
# ============================================================================

async def main():
    """
    Run all examples.
    """
    examples = [
        ("1. Blog Post Distribution", example_distribute_blog_post),
        ("2. Twitter Thread", example_twitter_thread),
        ("3. Video Distribution", example_video_distribution),
        ("4. Reddit Posting", example_reddit_distribution),
        ("6. Engagement Analytics", example_engagement_analytics),
        ("8. Duplicate Detection", example_duplicate_detection),
        ("9. Platform Formatting", example_platform_formatting),
    ]

    print("SOCIAL DISTRIBUTOR EXAMPLES")
    print("=" * 80)

    for name, example_fn in examples:
        print(f"\n{name}")
        print("-" * 80)
        try:
            if asyncio.iscoroutinefunction(example_fn):
                await example_fn()
            else:
                example_fn()
        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 80)
    print("Examples complete!")


if __name__ == "__main__":
    asyncio.run(main())

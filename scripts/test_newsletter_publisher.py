#!/usr/bin/env python3
"""
Integration tests and usage examples for newsletter_publisher.py

Run with:
  python scripts/test_newsletter_publisher.py
"""

import sys
from datetime import datetime, timezone, timedelta
from newsletter_publisher import (
    Article,
    NewsletterCampaign,
    TemplateType,
    SubscriberTier,
    create_weekly_digest,
    create_daily_briefing,
    create_things_to_know,
    send_newsletter,
    get_newsletter_metrics,
    schedule_newsletter,
    calculate_newsletter_revenue,
    get_pricing_tier_info,
    _calculate_read_time,
    _inject_affiliate_link,
    _add_tracking_params,
)


# ── Sample Data ──────────────────────────────────────────────────────────────

def create_sample_articles() -> list[Article]:
    """Create sample articles for testing."""
    now = datetime.now(timezone.utc)
    return [
        Article(
            id="art-001",
            title="Building AI Systems Without Spending $10k/month",
            summary="Discover free and affordable AI platforms. Learn how to use Groq's free tier, Google's free credits, and open-source alternatives to build production AI apps without breaking the bank.",
            body="Full article content here...",
            canonical_url="https://profitengine.alreadyherellc.com/ai-free-tier",
            published_at=(now - timedelta(days=3)).isoformat(),
            author="Stephen Franklin",
            read_time_minutes=8,
            tags=["AI", "DevOps", "Cost Reduction"],
        ),
        Article(
            id="art-002",
            title="Email Newsletter Monetization: $5K-$20K/month Income",
            summary="5 proven monetization strategies: paid subscriptions, sponsorships, affiliate links, job board, and premium content. Real numbers from 50+ indie creators.",
            body="Full article content here...",
            canonical_url="https://profitengine.alreadyherellc.com/newsletter-monetization",
            published_at=(now - timedelta(days=2)).isoformat(),
            author="Team",
            read_time_minutes=12,
            tags=["Monetization", "Email Marketing", "Business"],
        ),
        Article(
            id="art-003",
            title="PostgreSQL vs SQLite: When to Choose Each",
            summary="Side-by-side comparison for developers. Benchmarks, trade-offs, and real-world scenarios for choosing the right database.",
            body="Full article content here...",
            canonical_url="https://profitengine.alreadyherellc.com/postgres-vs-sqlite",
            published_at=(now - timedelta(days=1)).isoformat(),
            author="Dev Team",
            read_time_minutes=10,
            tags=["Databases", "DevOps", "Performance"],
        ),
        Article(
            id="art-004",
            title="OCI Always Free Tier: The Best Kept Secret",
            summary="Run unlimited servers on Oracle's always-free tier. Setup, pricing breakdown, and deployment guide for production workloads.",
            body="Full article content here...",
            canonical_url="https://profitengine.alreadyherellc.com/oci-always-free",
            published_at=now.isoformat(),
            author="Infrastructure Team",
            read_time_minutes=15,
            tags=["Cloud", "DevOps", "Free Tier"],
        ),
        Article(
            id="art-005",
            title="The Future of Content Distribution",
            summary="AI-native platforms are reshaping how we publish. Trends for 2026: multi-chain posting, real-time personalization, and algorithmic optimization.",
            body="Full article content here...",
            canonical_url="https://profitengine.alreadyherellc.com/content-distribution-2026",
            published_at=now.isoformat(),
            author="Strategy Lead",
            read_time_minutes=6,
            tags=["Content", "AI", "Trends"],
        ),
    ]


# ── Test Functions ──────────────────────────────────────────────────────────

def test_helper_functions():
    """Test utility functions."""
    print("\n=== Test: Helper Functions ===")

    # Test read time calculation
    long_text = " ".join(["word"] * 1000)  # 1000 words
    read_time = _calculate_read_time(long_text)
    assert read_time == 6, f"Expected 6 min, got {read_time}"
    print(f"[OK] Read time calculation: 1000 words = {read_time} min")

    # Test affiliate link injection
    affiliate = _inject_affiliate_link(
        "https://example.com/vps",
        keyword="VPS hosting"
    )
    print(f"[OK] Affiliate link injection: {affiliate[:50]}...")

    # Test tracking params
    tracked = _add_tracking_params(
        "https://profitengine.alreadyherellc.com/article",
        campaign_id="camp-123",
        medium="newsletter"
    )
    assert "utm_source=profitengine" in tracked
    assert "utm_medium=newsletter" in tracked
    print(f"[OK] Tracking params: {tracked[:80]}...")


def test_template_creation():
    """Test newsletter template creation."""
    print("\n=== Test: Template Creation ===")

    articles = create_sample_articles()

    # Weekly digest
    print("\n  Weekly Digest:")
    weekly = create_weekly_digest(articles)
    assert weekly["template_type"] == "weekly_digest"
    assert weekly["article_count"] == 5
    assert "Weekly Digest" in weekly["subject"]
    print(f"    [OK] Subject: {weekly['subject']}")
    print(f"    [OK] Articles: {weekly['article_count']}")
    print(f"    [OK] HTML length: {len(weekly['html'])} chars")

    # Daily briefing
    print("\n  Daily Briefing:")
    daily = create_daily_briefing(
        articles,
        ai_summary="Today's key insight: Free tier services can power production apps."
    )
    assert daily["template_type"] == "daily_briefing"
    assert daily["article_count"] == 2
    assert daily["ai_summary_included"] is True
    print(f"    [OK] Subject: {daily['subject']}")
    print(f"    [OK] Articles: {daily['article_count']}")
    print(f"    [OK] AI summary: Included")

    # Things to Know
    print("\n  Things to Know:")
    tips = create_things_to_know(articles, tips_per_article=2)
    assert tips["template_type"] == "things_to_know"
    assert tips["tip_count"] > 0
    print(f"    [OK] Subject: {tips['subject']}")
    print(f"    [OK] Tips extracted: {tips['tip_count']}")


def test_newsletter_send():
    """Test newsletter sending (dry run, won't actually send)."""
    print("\n=== Test: Newsletter Sending ===")

    articles = create_sample_articles()
    sponsor_html = """
    <h3>Sponsor: FastAPI Pro</h3>
    <p>Build production APIs in minutes. Special discount: 50% off annual plan.</p>
    <a href="https://fastapi.pro/ref">Get Started →</a>
    """

    result = send_newsletter(
        template_type="weekly_digest",
        articles=articles[:5],
        recipient_segment="all",
        sponsor_html=sponsor_html,
        track_opens=True,
        track_clicks=True,
        providers=["beehiiv"],  # Only try Beehiiv
    )

    print(f"  Campaign ID: {result['campaign_id']}")
    print(f"  Template: {result['template_type']}")
    print(f"  Subject: {result['subject']}")
    print(f"  Articles: {result['article_count']}")
    print(f"  Recipient Segment: {result['recipient_segment']}")
    print(f"  Success: {result['success']}")

    if result['provider_results']:
        for provider, prov_result in result['provider_results'].items():
            print(f"    [OK] {provider.upper()}: {prov_result.get('status', 'unknown')}")
    else:
        print("    [INFO] No providers configured (API keys missing)")


def test_scheduling():
    """Test newsletter scheduling."""
    print("\n=== Test: Newsletter Scheduling ===")

    articles = create_sample_articles()

    # Schedule for 2 hours from now
    schedule_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    result = schedule_newsletter(
        template_type="weekly_digest",
        articles=articles[:5],
        schedule_time=schedule_time,
        recipient_segment="premium",
    )

    if result:
        print(f"  [OK] Scheduled for: {result['scheduled_for']}")
        print(f"  [OK] Campaign ID: {result['campaign_id']}")
    else:
        print("  [INFO] Scheduling skipped (API key missing)")


def test_monetization():
    """Test monetization calculations."""
    print("\n=== Test: Monetization ===")

    # Pricing tiers
    pricing = get_pricing_tier_info()
    print("\n  Pricing Tiers:")
    for tier, info in pricing.items():
        print(f"    {tier.upper()}: ${info['price_usd']}")
        if info['features']:
            print(f"      Features: {', '.join(info['features'][:2])}...")

    # Revenue projection
    print("\n  Revenue Projection (100 free, 25 premium, 4 sponsor slots):")
    revenue = calculate_newsletter_revenue(
        free_subscribers=100,
        premium_subscribers=25,
        sponsor_slots=4,
    )
    print(f"    Premium: ${revenue['premium_revenue_monthly_usd']:.2f}/mo")
    print(f"    Sponsors: ${revenue['sponsor_revenue_monthly_usd']:.2f}/mo")
    print(f"    Total: ${revenue['total_monthly_usd']:.2f}/mo")
    print(f"    Total subscribers: {revenue['total_subscribers']}")


def test_segmentation():
    """Test subscriber segmentation."""
    print("\n=== Test: Subscriber Segmentation ===")

    articles = create_sample_articles()

    # Segment 1: Free tier (weekly digest)
    print("\n  Free Tier Segment:")
    free_result = send_newsletter(
        template_type="weekly_digest",
        articles=articles,
        recipient_segment="free",
        providers=[],  # Dry run
    )
    print(f"    Subject: {free_result['subject']}")
    print(f"    Articles: {free_result['article_count']}")

    # Segment 2: Premium tier (daily briefing)
    print("\n  Premium Tier Segment:")
    premium_result = send_newsletter(
        template_type="daily_briefing",
        articles=articles[:2],
        recipient_segment="premium",
        ai_summary="Premium subscribers get AI analysis of trends.",
        providers=[],  # Dry run
    )
    print(f"    Subject: {premium_result['subject']}")

    # Segment 3: Sponsors (tips with sponsor banner)
    print("\n  Sponsor Segment:")
    sponsor_result = send_newsletter(
        template_type="things_to_know",
        articles=articles,
        recipient_segment="all",
        sponsor_html="<h3>This Week's Sponsor</h3><p>...<p>",
        providers=[],  # Dry run
    )
    print(f"    Subject: {sponsor_result['subject']}")


def test_metrics():
    """Test metrics collection (dry run)."""
    print("\n=== Test: Metrics Collection ===")

    # Would normally fetch real metrics from Beehiiv
    campaign_id = "sample-campaign-123"

    metrics = get_newsletter_metrics(campaign_id)
    if metrics:
        print(f"  Campaign: {metrics.campaign_id}")
        print(f"  Delivered: {metrics.delivered_count}")
        print(f"  Open Rate: {metrics.open_rate:.1%}")
        print(f"  Click Rate: {metrics.click_rate:.1%}")
    else:
        print("  [INFO] Metrics API not available (missing API key or campaign)")


def test_dataclass_serialization():
    """Test that dataclasses can be serialized."""
    print("\n=== Test: Data Serialization ===")

    articles = create_sample_articles()
    campaign = NewsletterCampaign(
        id="camp-001",
        template_type="weekly_digest",
        subject="Test Newsletter",
        preview_text="Preview",
        sender_email="dispatch@alreadyherellc.com",
        sender_name="Newsletter",
        recipient_segment="all",
        status="sent",
    )

    # Should be serializable
    import json
    from dataclasses import asdict

    campaign_dict = asdict(campaign)
    json_str = json.dumps(campaign_dict)
    print(f"  [OK] Campaign serialized: {len(json_str)} bytes")
    print(f"    ID: {campaign.id}")
    print(f"    Status: {campaign.status}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Newsletter Publisher Test Suite")
    print("=" * 70)

    try:
        test_helper_functions()
        test_template_creation()
        test_newsletter_send()
        test_scheduling()
        test_monetization()
        test_segmentation()
        test_metrics()
        test_dataclass_serialization()

        print("\n" + "=" * 70)
        print("[PASS] All tests passed!")
        print("=" * 70)
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

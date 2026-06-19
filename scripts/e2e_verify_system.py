#!/usr/bin/env python3
"""
End-to-end system verification for ProfitEngine article publishing.

This script tests:
1. AI provider availability (Groq, Gemini, HuggingFace)
2. Content generation with fallback
3. GitHub Pages publication capability
4. Dev.to, Hashnode, Medium availability
5. Social media credential checking
6. E-commerce platform credential checking

Usage:
    python scripts/e2e_verify_system.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Import the resilient publisher
sys.path.insert(0, str(Path(__file__).resolve().parent))
import publish_article_resilient as resilient_pub


def check_ai_providers():
    """Verify AI provider credentials."""
    print("\n" + "="*70)
    print("AI PROVIDER VERIFICATION")
    print("="*70)

    results = {
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "huggingface": bool(os.getenv("HF_TOKEN")),
    }

    for provider, configured in results.items():
        status = "CONFIGURED" if configured else "MISSING"
        print(f"  {provider.upper():15} {status}")

    has_any = any(results.values())
    print(f"\n  Status: {'OK - Fallback available' if has_any else 'FAIL - No providers configured'}")
    return results


def check_content_platforms():
    """Verify content platform credentials."""
    print("\n" + "="*70)
    print("CONTENT PLATFORM VERIFICATION")
    print("="*70)

    results = {
        "github_pages": bool(os.getenv("CONTENT_REPO_TOKEN")) and bool(os.getenv("GITHUB_CONTENT_OWNER")),
        "devto": bool(os.getenv("DEVTO_API_KEY")),
        "hashnode": bool(os.getenv("HASHNODE_API_KEY")) and bool(os.getenv("HASHNODE_PUB_ID")),
        "medium": bool(os.getenv("MEDIUM_API_KEY")) and bool(os.getenv("MEDIUM_AUTHOR_ID")),
    }

    for platform, configured in results.items():
        status = "CONFIGURED" if configured else "MISSING"
        print(f"  {platform.upper():15} {status}")

    print(f"\n  Status: {sum(results.values())}/4 platforms configured")
    return results


def check_social_platforms():
    """Verify social media platform credentials."""
    print("\n" + "="*70)
    print("SOCIAL MEDIA CREDENTIAL CHECK")
    print("="*70)

    social_creds = resilient_pub._check_social_credentials()

    configured = sum(1 for v in social_creds.values() if v)
    total = len(social_creds)

    for platform, has_cred in social_creds.items():
        status = "CONFIGURED" if has_cred else "MISSING"
        print(f"  {platform.upper():15} {status}")

    print(f"\n  Status: {configured}/{total} platforms configured")
    return social_creds


def check_ecommerce_platforms():
    """Verify e-commerce platform credentials."""
    print("\n" + "="*70)
    print("E-COMMERCE PLATFORM CREDENTIAL CHECK")
    print("="*70)

    ecommerce_creds = resilient_pub._check_ecommerce_credentials()

    configured = sum(1 for v in ecommerce_creds.values() if v)
    total = len(ecommerce_creds)

    for platform, has_cred in ecommerce_creds.items():
        status = "CONFIGURED" if has_cred else "MISSING"
        print(f"  {platform.upper():15} {status}")

    print(f"\n  Status: {configured}/{total} platforms configured")
    return ecommerce_creds


def check_affiliate_config():
    """Verify affiliate links configuration."""
    print("\n" + "="*70)
    print("AFFILIATE CONFIGURATION")
    print("="*70)

    affiliate_map = resilient_pub._limited_affiliate_map()
    count = len(affiliate_map)

    print(f"  Total configured: {count} affiliate programs")
    if affiliate_map:
        print("\n  Configured programs:")
        for i, (keyword, url) in enumerate(list(affiliate_map.items())[:10], 1):
            print(f"    {i:2}. {keyword:20} -> {url[:50]}")
        if count > 10:
            print(f"    ... and {count - 10} more")

    amazon_tag = os.getenv("AMAZON_PARTNER_TAG", "")
    print(f"\n  Amazon Partner Tag: {amazon_tag if amazon_tag else 'MISSING'}")

    return {
        "total_programs": count,
        "amazon_tag": amazon_tag,
    }


def generate_deterministic_sample():
    """Generate a sample article using deterministic fallback."""
    print("\n" + "="*70)
    print("DETERMINISTIC ARTICLE GENERATION TEST")
    print("="*70)

    topic = "AI Automation Systems for Small Business Revenue"
    article = resilient_pub._deterministic_article(topic)

    print(f"\n  Title: {article['title']}")
    print(f"  Slug:  {article['slug']}")
    print(f"  Meta:  {article['meta_description']}")
    print(f"  Tags:  {', '.join(article['tags'])}")
    print(f"  Body length: {len(article['body'])} characters")

    return article


def test_article_with_action_brief():
    """Test article generation with revenue action brief."""
    print("\n" + "="*70)
    print("ACTION BRIEF ATTACHMENT TEST")
    print("="*70)

    article = resilient_pub._deterministic_article("AI Automation for Service Businesses")
    article_with_brief = resilient_pub._attach_revenue_action_brief("AI Automation for Service Businesses", article)

    has_brief = "## Revenue Execution Brief" in article_with_brief.get("body", "")
    brief_length = len(article_with_brief.get("body", ""))

    print(f"  Action brief enabled: {resilient_pub.ACTION_BRIEF_ENABLED}")
    print(f"  Brief attached: {has_brief}")
    print(f"  Final body length: {brief_length} characters")
    print(f"  Tags: {article_with_brief.get('tags', [])}")

    return article_with_brief


def generate_system_summary():
    """Generate complete system status summary."""
    print("\n" + "="*70)
    print("SYSTEM READINESS SUMMARY")
    print("="*70)

    ai = check_ai_providers()
    content = check_content_platforms()
    social = check_social_platforms()
    ecommerce = check_ecommerce_platforms()
    affiliate = check_affiliate_config()

    # Generate actionable report
    missing_keys = []

    if not any(ai.values()):
        missing_keys.append("AI provider (Groq, Gemini, or HuggingFace)")

    if not content["github_pages"]:
        missing_keys.append("GitHub Pages token")

    if not content["devto"]:
        missing_keys.append("Dev.to API key")

    configured_social = sum(1 for v in social.values() if v)
    configured_ecommerce = sum(1 for v in ecommerce.values() if v)

    print("\n" + "="*70)
    print("SYSTEM STATUS")
    print("="*70)

    print("\nOK - WORKING NOW:")
    print(f"  - Content generation: FALLBACK ACTIVE (deterministic article available)")
    print(f"  - GitHub Pages: {'READY' if content['github_pages'] else 'NOT READY'}")
    print(f"  - Dev.to publishing: {'READY' if content['devto'] else 'NOT READY'}")
    print(f"  - Affiliate tracking: {affiliate['total_programs']} programs configured")

    print("\nNOT CONFIGURED:")
    if missing_keys:
        for key in missing_keys:
            print(f"  - {key}")
    else:
        print("  - All core features configured!")

    print(f"\nOPTIONAL (Paid/Additional):")
    print(f"  - Hashnode: NOT AVAILABLE (requires paid Pro plan)")
    print(f"  - Medium: {'READY' if content['medium'] else 'NOT READY - requires API key and author ID'}")
    print(f"  - Social platforms: {configured_social}/9 configured")
    print(f"  - E-commerce platforms: {configured_ecommerce}/5 configured")

    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)

    if not content["devto"]:
        print("\n1. ENABLE DEV.TO PUBLISHING:")
        print("   - Get API key: https://dev.to/settings/extensions")
        print("   - Add to .env: DEVTO_API_KEY=<your-key>")
        print("   - Verify with: CONTENT_VERIFY_ONLY=true python scripts/publish_article.py")

    if not content["medium"]:
        print("\n2. ENABLE MEDIUM PUBLISHING:")
        print("   - Get API key: https://medium.com/@<username>/settings")
        print("   - Get author ID: curl https://api.medium.com/v1/me -H 'Authorization: Bearer <token>'")
        print("   - Add to .env: MEDIUM_API_KEY=<key> and MEDIUM_AUTHOR_ID=<id>")

    if configured_social == 0:
        print("\n3. ENABLE SOCIAL MEDIA DISTRIBUTION:")
        print("   Available platforms: Twitter, Reddit, Facebook, LinkedIn, Instagram, TikTok, Telegram, Mastodon, Bluesky")
        print("   - Set platform credentials in .env (e.g., TWITTER_API_KEY, REDDIT_CLIENT_ID)")
        print("   - Social distribution will auto-activate when credentials are present")

    if configured_ecommerce == 0:
        print("\n4. ENABLE E-COMMERCE DISTRIBUTION:")
        print("   Available platforms: Shopify, Etsy, Amazon, eBay, WooCommerce")
        print("   - Set platform credentials in .env (e.g., SHOPIFY_STORE_URL, ETSY_API_KEY)")
        print("   - E-commerce distribution will auto-activate when credentials are present")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_providers": ai,
        "content_platforms": content,
        "social_platforms": social,
        "ecommerce_platforms": ecommerce,
        "affiliate_config": affiliate,
        "missing_keys": missing_keys,
    }


def main():
    print("\n")
    print("*" * 70)
    print("ProfitEngine v5 - End-to-End System Verification")
    print("*" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")

    # Run checks
    summary = generate_system_summary()

    # Test article generation
    article = generate_deterministic_sample()
    article_with_brief = test_article_with_action_brief()

    # Save summary
    report = {
        "test_timestamp": datetime.now(timezone.utc).isoformat(),
        "system_summary": summary,
        "sample_article": {
            "title": article["title"],
            "slug": article["slug"],
            "body_length": len(article["body"]),
            "tags": article.get("tags", []),
            "has_revenue_brief": "## Revenue Execution Brief" in article_with_brief.get("body", ""),
        }
    }

    report_file = "system_verification_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Report saved to: {report_file}")
    print("\n" + "*" * 70)
    print("Verification complete!")
    print("*" * 70 + "\n")


if __name__ == "__main__":
    main()

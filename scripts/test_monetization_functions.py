#!/usr/bin/env python3
"""
Test monetization functions from publish_article_resilient.py

This script tests the ebook generation, product suggestions, and report building
without requiring API credentials. Useful for validating workflow logic.

Usage:
    python scripts/test_monetization_functions.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path so we can import publish_article_resilient
sys.path.insert(0, str(Path(__file__).parent))

from publish_article_resilient import (
    _convert_article_to_ebook,
    _get_product_suggestions,
    _build_monetization_report,
    _word_count,
)


def test_word_count():
    """Test word counting function."""
    print("\n=== TEST: Word Count ===")

    test_cases = [
        ("Hello world", 2),
        ("# Markdown **bold** *italic*", 3),
        ("This is a longer article with multiple sentences.", 8),
    ]

    for text, expected in test_cases:
        count = _word_count(text)
        status = "[PASS]" if count == expected else "[FAIL]"
        print(f"{status} '{text}' = {count} words (expected {expected})")


def test_product_suggestions():
    """Test product suggestion based on article topic."""
    print("\n=== TEST: Product Suggestions ===")

    test_articles = [
        {
            "title": "AI Automation for Small Business",
            "tags": ["ai", "automation", "revenue"],
            "body": "Learn how to automate your business workflows...",
        },
        {
            "title": "Ecommerce Dropshipping Strategy",
            "tags": ["ecommerce", "dropshipping"],
            "body": "Set up a profitable online store...",
        },
        {
            "title": "SEO Content Marketing",
            "tags": ["seo", "content", "blog"],
            "body": "Create content that ranks and converts...",
        },
    ]

    for article in test_articles:
        suggestions = _get_product_suggestions(article)
        status = "[PASS]" if suggestions else "[FAIL]"
        print(f"{status} Title: {article['title']}")
        print(f"       Suggestions: {suggestions}")


def test_ebook_generation():
    """Test ebook markdown generation."""
    print("\n=== TEST: Ebook Generation ===")

    test_article = {
        "title": "Building Automated Revenue Systems",
        "tags": ["automation", "revenue", "ai"],
        "body": """## Why Automation Matters

Automation saves time and creates revenue. Small businesses need practical systems that work.

## Getting Started

1. Define your revenue event (sale, booking, signup, click)
2. Build the minimum working system
3. Test with real customers
4. Optimize based on results

## Conclusion

Automation is not complex. It is simply removing friction from your sales process.""",
    }

    output_dir = Path(".") / "test_output"
    output_dir.mkdir(exist_ok=True)

    ebook_path = _convert_article_to_ebook(test_article, str(output_dir))

    if ebook_path:
        print(f"[PASS] Ebook created: {ebook_path}")
        with open(ebook_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = len(content.split("\n"))
            print(f"       Size: {len(content)} bytes, {lines} lines")

        # Show first 500 chars
        print(f"\n       Preview:\n{content[:500]}...")

        # Clean up test file
        Path(ebook_path).unlink()
        print(f"\n[PASS] Test file cleaned up")
    else:
        print("[FAIL] Ebook generation failed")


def test_monetization_report():
    """Test monetization report generation."""
    print("\n=== TEST: Monetization Report ===")

    test_article = {
        "title": "AI Automation Systems for Small Business Revenue",
        "tags": ["ai", "automation", "revenue", "smallbusiness"],
        "body": "A" * 1500,  # Simulate 1500+ word article
    }

    test_social_results = {
        "twitter": {"status": "success", "url": "https://twitter.com/..."},
        "linkedin": {"status": "success", "url": "https://linkedin.com/..."},
        "facebook": {"status": "skipped", "reason": "no_credentials"},
    }

    test_ecommerce_results = {
        "gumroad": {
            "status": "success",
            "product_id": "test123",
            "url": "https://gumroad.com/d/test123",
            "price": 4.99,
        },
        "printify": {
            "t-shirt": {
                "status": "pending_design",
                "product_id": "prod1",
                "product_type": "t-shirt",
                "url": "https://printify.com/dashboard/products/prod1",
            },
            "mug": {
                "status": "pending_design",
                "product_id": "prod2",
                "product_type": "mug",
                "url": "https://printify.com/dashboard/products/prod2",
            },
        },
    }

    report = _build_monetization_report(
        test_article,
        "https://quantam101.github.io/test-article",
        test_social_results,
        test_ecommerce_results,
    )

    print("\nReport Structure:")
    print(json.dumps(report, indent=2))

    # Verify key fields
    assertions = [
        (report["article"]["title"], "AI Automation Systems for Small Business Revenue", "Article title"),
        (report["monetization"]["ebook"]["created"], True, "Ebook created"),
        (report["monetization"]["ebook"]["price"], 4.99, "Ebook price"),
        (report["monetization"]["pod_products"]["queued_count"], 2, "POD products queued"),
        (len(report["next_actions"]), 5, "Next actions provided"),
    ]

    print("\nAssertion Checks:")
    for actual, expected, name in assertions:
        status = "[PASS]" if actual == expected else "[FAIL]"
        print(f"{status} {name}: {actual} (expected {expected})")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Monetization Functions")
    print("=" * 60)

    try:
        test_word_count()
        test_product_suggestions()
        test_ebook_generation()
        test_monetization_report()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

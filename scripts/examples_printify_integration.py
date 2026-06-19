"""
Printify POD Publisher Integration Examples

This module demonstrates practical usage patterns for the Printify product
publisher in various scenarios:

1. Single article publishing
2. Batch article processing
3. Content recommendations
4. Sales reporting
5. Error handling
6. Workflow integration
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from printify_product_publisher import PrintifyPublisher, PRODUCT_TEMPLATES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Single Article Publishing
# ────────────────────────────────────────────────────────────────────────────


def example_single_article():
    """Publish POD products for a single article."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Single Article Publishing")
    print("=" * 70)

    publisher = PrintifyPublisher()

    # Example article data
    article = {
        "title": "How to Build a Profitable AI Side Hustle in 2026",
        "summary": (
            "Learn how to leverage free AI tools to create multiple income streams. "
            "This guide covers ChatGPT for content creation, image generation with DALL-E, "
            "and automation with Make.com. Realistic earning expectations: $500-$2000/month."
        ),
        "keywords": ["AI", "side hustle", "passive income", "ChatGPT", "automation"],
        "url": "https://alreadyherellc.com/blog/ai-side-hustle",
        "content": "Full article content would go here...",
    }

    print(f"\nPublishing article: {article['title']}")
    print(f"Keywords: {', '.join(article['keywords'])}")

    # Get product recommendations
    recommendations = publisher.recommend_products(
        keywords=article["keywords"],
        article_topic=article["title"],
    )
    print(f"\nRecommended products: {recommendations}")

    # Publish in draft mode first
    result = publisher.publish_article(
        title=article["title"],
        summary=article["summary"],
        keywords=article["keywords"],
        article_url=article["url"],
        auto_publish=False,  # Review first
    )

    print(f"\nPublish Result:")
    print(f"  Success: {result.success}")
    print(f"  Products Created: {len(result.products)}")

    for product in result.products:
        print(f"\n  • {product.title}")
        print(f"    Price: ${product.price_usd}")
        print(f"    Cost: ${product.cost_usd}")
        print(f"    Profit: ${product.price_usd - product.cost_usd}")
        print(f"    Margin: {product.profit_margin_pct}%")
        print(f"    Status: {product.status}")

    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  ✗ {error}")


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Batch Processing Multiple Articles
# ────────────────────────────────────────────────────────────────────────────


def example_batch_publishing():
    """Publish POD products for multiple articles."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Batch Publishing Multiple Articles")
    print("=" * 70)

    publisher = PrintifyPublisher()

    articles = [
        {
            "title": "10 Free AI Tools to Build Passive Income",
            "summary": "Top 10 free AI tools that can generate $500-$5000/month...",
            "keywords": ["AI", "passive income", "free tools"],
            "url": "https://example.com/ai-tools",
        },
        {
            "title": "SaaS Pricing Strategies for Maximum Revenue",
            "summary": "How to price your SaaS product for growth and profitability...",
            "keywords": ["SaaS", "pricing", "revenue", "business"],
            "url": "https://example.com/saas-pricing",
        },
        {
            "title": "Building Your First Niche Blog in 2026",
            "summary": "Complete guide to selecting a niche and publishing your first blog...",
            "keywords": ["blog", "niche", "SEO", "content"],
            "url": "https://example.com/blog-guide",
        },
    ]

    results = []
    total_products = 0

    for article in articles:
        print(f"\nProcessing: {article['title']}")

        result = publisher.publish_article(
            title=article["title"],
            summary=article["summary"],
            keywords=article["keywords"],
            article_url=article["url"],
            auto_publish=False,  # Review all before publishing
        )

        results.append(result)
        total_products += len(result.products)
        print(f"  ✓ Created {len(result.products)} products")

    print(f"\n" + "-" * 70)
    print(f"BATCH SUMMARY")
    print(f"-" * 70)
    print(f"Total Articles: {len(articles)}")
    print(f"Total Products: {total_products}")

    # Show breakdown by product type
    product_counts = {}
    for result in results:
        for product in result.products:
            ptype = product.product_type
            product_counts[ptype] = product_counts.get(ptype, 0) + 1

    print(f"\nProduct Breakdown:")
    for ptype, count in sorted(product_counts.items()):
        template = PRODUCT_TEMPLATES[ptype]
        profit_per = template["price"] - template["cost"]
        total_profit = profit_per * count
        print(
            f"  {ptype.title():15} {count:2} units  "
            f"${profit_per:.2f}/unit = ${total_profit:.2f} total profit"
        )


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Smart Product Recommendations
# ────────────────────────────────────────────────────────────────────────────


def example_recommendations():
    """Demonstrate smart product recommendations for different content types."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Smart Product Recommendations")
    print("=" * 70)

    publisher = PrintifyPublisher()

    content_types = [
        {
            "topic": "Using ChatGPT for Content Creation",
            "keywords": ["AI", "ChatGPT", "content", "automation"],
            "expected": ["tshirt", "hoodie"],
        },
        {
            "topic": "Building a $100K SaaS Business",
            "keywords": ["SaaS", "startup", "founder", "revenue"],
            "expected": ["tshirt", "hoodie", "book"],
        },
        {
            "topic": "12 Passive Income Streams",
            "keywords": ["passive income", "affiliate", "monetize"],
            "expected": ["tshirt", "hoodie", "book"],
        },
        {
            "topic": "SEO Guide for 2026",
            "keywords": ["SEO", "blog", "keywords", "ranking"],
            "expected": ["tshirt", "mug"],
        },
        {
            "topic": "React Performance Optimization",
            "keywords": ["React", "JavaScript", "developer", "code"],
            "expected": ["tshirt", "hoodie"],
        },
    ]

    for content in content_types:
        recommendations = publisher.recommend_products(
            keywords=content["keywords"],
            article_topic=content["topic"],
        )

        match = all(r in content["expected"] for r in recommendations)
        status = "✓" if match else "✗"

        print(f"\n{status} {content['topic']}")
        print(f"  Keywords: {', '.join(content['keywords'])}")
        print(f"  Recommended: {recommendations}")
        print(f"  Expected: {content['expected']}")


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 4: Inventory and Sales Tracking
# ────────────────────────────────────────────────────────────────────────────


def example_inventory_tracking():
    """Track inventory and generate sales reports."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Inventory & Sales Tracking")
    print("=" * 70)

    publisher = PrintifyPublisher()

    # Get stats
    stats = publisher.get_inventory_stats()

    print(f"\nInventory Summary:")
    print(f"  Total Products:    {stats['total_products']}")
    print(f"  Draft:             {stats['draft_products']}")
    print(f"  Published:         {stats['published_products']}")
    print(f"  Total Sales:       {stats['total_sales']} units")
    print(f"  Potential Profit:  ${stats['total_potential_profit']:.2f}")

    if stats["products_by_type"]:
        print(f"\nBy Product Type:")
        for ptype, count in stats["products_by_type"].items():
            print(f"  {ptype.title():15} {count:3} products")

    # Generate sales report
    report = publisher.get_sales_report()

    print(f"\n" + "-" * 70)
    print(f"SALES REPORT")
    print(f"-" * 70)
    print(f"Total Revenue:     ${report['total_revenue']:.2f}")
    print(f"Total Costs:       ${report['total_costs']:.2f}")
    print(f"Total Profit:      ${report['total_profit']:.2f}")
    print(f"Avg Profit Margin: {report['average_profit_margin_pct']:.1f}%")

    if report["best_performing"]:
        print(f"\nBest Performing Products:")
        for i, product in enumerate(report["best_performing"], 1):
            print(
                f"  {i}. {product['title']}"
                f" - {product['sales']} sales, ${product['profit']:.2f} profit"
            )

    if report["by_product_type"]:
        print(f"\nBy Product Type:")
        for ptype, stats in report["by_product_type"].items():
            if stats["count"] > 0:
                avg_profit = stats["profit"] / stats["count"]
                print(
                    f"  {ptype.title():15} {stats['count']:3} products  "
                    f"${stats['revenue']:.2f} revenue, ${avg_profit:.2f} avg profit"
                )


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 5: Filtering and Listing Products
# ────────────────────────────────────────────────────────────────────────────


def example_product_filtering():
    """Filter and list products by type and status."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Product Filtering & Listing")
    print("=" * 70)

    publisher = PrintifyPublisher()

    # List all products
    all_products = publisher.list_products()
    print(f"\nAll Products ({len(all_products)} total):")
    for product in all_products[:5]:  # Show first 5
        print(f"  • {product.title}")

    # Filter by product type
    print(f"\nT-Shirt Products:")
    tshirts = publisher.list_products(product_type="tshirt")
    print(f"  Found {len(tshirts)} t-shirt products")
    for tshirt in tshirts[:3]:
        print(f"    • {tshirt.title}")

    # Filter by status
    print(f"\nDraft Products:")
    drafts = publisher.list_products(status="draft")
    print(f"  Found {len(drafts)} draft products")

    print(f"\nPublished Products:")
    published = publisher.list_products(status="published")
    print(f"  Found {len(published)} published products")


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 6: Workflow Integration (GitHub Actions)
# ────────────────────────────────────────────────────────────────────────────


def example_github_actions_integration():
    """Example payload from GitHub Actions workflow."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: GitHub Actions Integration")
    print("=" * 70)

    # Simulated GitHub Actions payload
    payload = {
        "action": "article_published",
        "article": {
            "title": "How to Start a Profitable Niche Blog",
            "summary": "Step-by-step guide to niche selection, content strategy, and monetization",
            "keywords": ["blog", "niche", "passive income", "SEO"],
            "url": "https://alreadyherellc.com/blog/niche-blog-guide",
            "published_at": datetime.now(UTC).isoformat(),
        },
    }

    print(f"\nGitHub Actions Payload:")
    print(json.dumps(payload, indent=2))

    print(f"\nProcessing via Workflow...")

    publisher = PrintifyPublisher()

    result = publisher.publish_article(
        title=payload["article"]["title"],
        summary=payload["article"]["summary"],
        keywords=payload["article"]["keywords"],
        article_url=payload["article"]["url"],
        auto_publish=False,
    )

    print(f"\nWorkflow Result:")
    print(f"  Status: {'Success' if result.success else 'Failed'}")
    print(f"  Products: {len(result.products)}")

    # Output for workflow
    output = {
        "workflow_status": "success" if result.success else "failed",
        "article_title": result.article_title,
        "products_created": len(result.products),
        "product_details": [
            {
                "type": p.product_type,
                "title": p.title,
                "price": p.price_usd,
                "profit": p.price_usd - p.cost_usd,
            }
            for p in result.products
        ],
    }

    print(f"\nWorkflow Output (for CI/CD):")
    print(json.dumps(output, indent=2))


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 7: Error Handling
# ────────────────────────────────────────────────────────────────────────────


def example_error_handling():
    """Demonstrate error handling patterns."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Error Handling Patterns")
    print("=" * 70)

    # Pattern 1: Missing credentials
    print(f"\nPattern 1: Missing Credentials")
    try:
        from printify_product_publisher import PrintifyPublisher as PP

        # This will fail without env vars set
        publisher = PP(api_token=None, shop_id=None)
    except ValueError as e:
        print(f"  Expected error: {e}")

    # Pattern 2: Empty keywords
    print(f"\nPattern 2: Empty Keywords (Fallback to Defaults)")
    publisher = PrintifyPublisher()

    result = publisher.publish_article(
        title="Article with No Keywords",
        summary="Summary",
        keywords=[],
        article_url="https://example.com",
    )

    print(f"  Articles with empty keywords still works!")
    print(f"  Created {len(result.products)} products with fallback recommendations")

    # Pattern 3: API failures gracefully handled
    print(f"\nPattern 3: API Failures (Graceful Degradation)")
    print(f"  If Printify API fails:")
    print(f"    - Products still created in draft mode locally")
    print(f"    - external_id remains None until API recovers")
    print(f"    - Can retry publishing with auto_publish=True later")


# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE 8: Profit Analysis
# ────────────────────────────────────────────────────────────────────────────


def example_profit_analysis():
    """Analyze profitability by product type and topic."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Profit Analysis")
    print("=" * 70)

    print(f"\nProduct Profitability Breakdown:")
    print(f"\n{'Product':<15} {'Price':>8} {'Cost':>8} {'Profit':>8} {'Margin':>8}")
    print(f"{'-' * 50}")

    total_profit_per_unit = 0
    for ptype, template in PRODUCT_TEMPLATES.items():
        price = template["price"]
        cost = template["cost"]
        profit = price - cost
        margin = (profit / price) * 100

        print(
            f"{ptype.title():<15} ${price:>7.2f} ${cost:>7.2f} "
            f"${profit:>7.2f} {margin:>7.1f}%"
        )

        total_profit_per_unit += profit

    avg_profit = total_profit_per_unit / len(PRODUCT_TEMPLATES)
    print(f"{'-' * 50}")
    print(f"{'Average':<15} {'':<8} {'':<8} ${avg_profit:>7.2f}")

    print(f"\nProjected Revenue (10 articles × 4 products each):")
    articles = 10
    products_per = 4
    avg_price = sum(t["price"] for t in PRODUCT_TEMPLATES.values()) / len(
        PRODUCT_TEMPLATES
    )
    total_revenue = articles * products_per * avg_price

    print(f"  {articles} articles × {products_per} products × ${avg_price:.2f} = ${total_revenue:.2f}")

    print(f"\nProjected Profit (assuming 100 units sold):")
    units_sold = 100
    total_profit = units_sold * avg_profit
    print(
        f"  {units_sold} units × ${avg_profit:.2f} avg profit = ${total_profit:.2f}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────


def main():
    """Run all examples."""
    examples = [
        ("Single Article", example_single_article),
        ("Batch Publishing", example_batch_publishing),
        ("Smart Recommendations", example_recommendations),
        ("Inventory Tracking", example_inventory_tracking),
        ("Product Filtering", example_product_filtering),
        ("GitHub Actions", example_github_actions_integration),
        ("Error Handling", example_error_handling),
        ("Profit Analysis", example_profit_analysis),
    ]

    print("\n" + "=" * 70)
    print("PRINTIFY POD PUBLISHER — INTEGRATION EXAMPLES")
    print("=" * 70)

    # Run examples that don't require API credentials
    safe_examples = [
        "Smart Recommendations",
        "Profit Analysis",
        "Error Handling",
        "GitHub Actions",
    ]

    for name, func in examples:
        try:
            if name in safe_examples or name == "Single Article":
                func()
            else:
                print(f"\n⊘ Skipping '{name}' (requires Printify credentials)")
        except Exception as e:
            logger.error(f"Error in {name}: {e}")

    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nTo use the publisher in your code:")
    print("  from scripts.printify_product_publisher import PrintifyPublisher")
    print("  publisher = PrintifyPublisher()")
    print("  result = publisher.publish_article(...)")


if __name__ == "__main__":
    main()

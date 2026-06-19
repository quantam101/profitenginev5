#!/usr/bin/env python3
"""
Gumroad Publisher — Usage Examples

Demonstrates how to use gumroad_publisher.py for:
  1. Converting blog articles to ebooks (PDF)
  2. Publishing ebooks to Gumroad with optimal pricing
  3. Publishing manuals/guides with templates
  4. Publishing courses with modules and worksheets
  5. Injecting affiliate links into product descriptions
  6. Tracking sales and revenue per product
  7. Generating sales reports

Usage:
  python scripts/gumroad_publisher_examples.py

Environment Setup:
  1. Set GUMROAD_API_TOKEN in .env or server environment
  2. Set GUMROAD_CREATOR_ID (e.g. 'alreadyhere')
  3. (Optional) AFFILIATE_LINKS for automatic link injection
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gumroad_publisher as gp
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ── Example 1: Convert Blog Article to Ebook ─────────────────────────────────
def example_article_to_ebook():
    """
    Example: Convert a blog article to PDF ebook.

    This example:
    - Takes markdown article content
    - Generates a formatted PDF
    - Returns path for upload to Gumroad
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Convert Blog Article to Ebook")
    print("=" * 70)

    # Sample blog article content (markdown format)
    article_markdown = """
# The Complete Guide to Vehicle Recovery & Flipping

## Introduction

Vehicle flipping is one of the fastest ways to generate consistent,
high-margin income. Buy cars cheap, fix them for minimal cost, and sell
at 2-3x markup. This guide covers the proven system.

## Chapter 1: How to Source Cheap Cars

### Method 1: Craigslist & Facebook Marketplace
- Best for: Quick turnarounds, competitive sourcing
- Time commitment: 2-3 hours daily
- Average acquisition cost: $400-$800

### Method 2: Auto Auctions
- Copart.com and IAA.com
- Requires auction account + inspection
- Deals average 40-60% below book value

### Method 3: Estate Sales & Liquidation
- Facebook marketplace ('estate sale')
- Often less competitive than auctions
- 50-70% of book value common

## Chapter 2: Deal Evaluation Scorecard

Before buying ANY car, score it on these 5 metrics:

**Mechanical Condition** (0-25 points)
- Engine runs: 10 points
- Transmission smooth: 8 points
- Steering responsive: 4 points
- Brakes good: 3 points

**Body & Paint** (0-20 points)
- No major rust: 12 points
- Minor dents only: 5 points
- Interior clean: 3 points

**Title Status** (0-15 points)
- Clean title: 15 points
- Salvage/rebuilt: -5 points
- Lien issues: -10 points

**Market Demand** (0-20 points)
- Popular model: 15 points
- Good color: 5 points

**Acquisition Cost** (0-20 points)
- <$500: 20 points
- $500-$700: 15 points
- $700-$1000: 10 points
- >$1000: 5 points

**Scoring:**
- 80+ points = BUY
- 60-80 points = NEGOTIATE
- <60 points = PASS

## Chapter 3: Repair Budget & Timeline

### Typical $1,500 Repair Budget

Parts & Materials: $900
- Brakes (front pads + rotor): $150
- Oil change (full) + filters: $60
- Belts/hoses: $80
- Coolant flush: $40
- Tires (used, quality): $300
- Windshield wipers: $20
- Paint touch-up: $50
- Miscellaneous: $100

Labor (DIY or contractor): $600
- Estimated 15-20 hours @ $40-50/hour
- Some repairs are owner-DIY to save

### Timeline: 5-7 Days Average
Day 1: Acquisition & initial inspection
Day 2: Order parts, schedule contractor
Days 3-5: Repairs & detailing
Day 6: Professional detailing & photos
Day 7: List & first inquiries

## Chapter 4: Where to Sell

### Facebook Marketplace
- Pros: Large audience, no fees, local buyers
- Cons: Takes time, cash-only usually
- Average sale: 5-10 days

### Craigslist
- Pros: Buyer intent is high
- Cons: Safety concerns, meetings
- Average sale: 7-14 days

### Local Dealers/Wholesalers
- Pros: Immediate cash, no hassle
- Cons: Lowest profit margin (typically 20-30%)
- Average payout: $4,500-$5,500 on $7,000 list

### OfferUp & Letgo
- Pros: Growing audience
- Cons: Younger buyers (reliability concern)

## Profit Examples

### Example 1: Sedan Flip
- Acquisition: $550
- Repairs: $1,200
- Detailing: $150
- Total investment: $1,900
- Selling price: $5,500
- **Profit: $3,600 (189% ROI)**

### Example 2: Truck Flip
- Acquisition: $700
- Repairs: $1,400
- Detailing: $200
- Total investment: $2,300
- Selling price: $7,200
- **Profit: $4,900 (213% ROI)**

### Example 3: SUV Flip
- Acquisition: $800
- Repairs: $1,300
- Detailing: $200
- Total investment: $2,300
- Selling price: $6,500
- **Profit: $4,200 (183% ROI)**

## Scaling to 8-12 Cars/Month

### Timeline
- Month 1: 2 cars ($7,200 profit)
- Month 2: 4 cars ($16,200 profit)
- Month 3: 6 cars ($22,800 profit)
- Month 4: 8 cars ($30,400 profit)

### Key to Scaling:
1. Build relationships with 2-3 contractors (parallel repairs)
2. Automate sourcing (daily Craigslist/FB alerts)
3. Create photo templates for faster listings
4. Develop standard messaging for buyers

## Conclusion

Vehicle flipping is legitimate, scalable, and profitable. Start with
2-3 cars to learn the process, then scale to 8-12/month. At that volume,
you're earning $25K-$50K monthly profit without employees or inventory.
"""

    # Convert to ebook (will generate HTML template in temp folder if reportlab not installed)
    pdf_path = gp.article_to_ebook(
        article_content=article_markdown,
        title="The Complete Guide to Vehicle Recovery & Flipping",
        author="Already Here LLC",
        format_type="markdown",
    )

    print(f"Generated ebook: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 'N/A'} bytes")

    return pdf_path


# ── Example 2: Publish Ebook ─────────────────────────────────────────────────
def example_publish_ebook(pdf_path):
    """
    Example: Publish ebook to Gumroad.

    Requires GUMROAD_API_TOKEN to be set.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Publish Ebook to Gumroad")
    print("=" * 70)

    product = gp.publish_ebook(
        title="The Complete Guide to Vehicle Recovery & Flipping",
        description="""Master the complete system for buying cars cheap, repairing them
for minimal cost, and flipping for 2-3x profit.

INCLUDES:
- Sourcing strategies (5 channels)
- Deal evaluation scorecard
- Repair budget breakdown ($1,500 max)
- Realistic profit examples
- Scaling playbook (8-12 cars/month)
- Timeline for each flip

RESULTS:
- $3,600-$4,900 profit per car
- 180-220% ROI per flip
- Scale to $25K-$50K monthly

Perfect for: Side hustlers, entrepreneurs, anyone looking for
high-margin income without inventory risk.""",
        pdf_path=pdf_path,
        author="Already Here LLC",
        content_type="manual",
        word_count=3500,
        price=7.99,  # Optional: override recommended price
        source_article_url="https://quantam101.github.io/content/",
    )

    if product:
        print(f"\n[OK] Published: {product.name}")
        print(f"    Price: ${product.price:.2f}")
        print(f"    Type: {product.content_type}")
        print(f"    ID: {product.gumroad_id}")
        print(f"    URL: {product.product_url}")
        return product
    else:
        print("[ERROR] Failed to publish ebook")
        return None


# ── Example 3: Get Price Recommendation ──────────────────────────────────────
def example_pricing_recommendations():
    """
    Example: Get automatic pricing recommendations based on content type.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Pricing Recommendations")
    print("=" * 70)

    test_cases = [
        # (content_type, word_count, has_templates, has_worksheets, is_bestseller)
        ("ebook", 5000, False, False, False),
        ("ebook", 15000, True, False, False),
        ("ebook", 25000, True, True, True),
        ("manual", 10000, False, False, False),
        ("manual", 20000, True, True, False),
        ("manual", 35000, True, True, True),
        ("course", 20000, True, False, False),
        ("course", 50000, True, True, False),
        ("course", 80000, True, True, True),
        ("bundle", 30000, True, False, False),
        ("bundle", 75000, True, True, False),
        ("bundle", 150000, True, True, True),
    ]

    print(f"\n{'Content Type':<12} {'Words':<8} {'Templates':<12} {'Worksheets':<12} {'Bestseller':<12} {'Price':<8}")
    print("-" * 80)

    for content_type, word_count, has_templates, has_worksheets, is_bestseller in test_cases:
        price = gp.get_recommended_price(
            content_type,
            word_count,
            has_templates=has_templates,
            has_worksheets=has_worksheets,
            is_bestseller=is_bestseller,
        )

        templates_str = "Yes" if has_templates else "No"
        worksheets_str = "Yes" if has_worksheets else "No"
        bestseller_str = "Yes" if is_bestseller else "No"

        print(f"{content_type:<12} {word_count:<8} {templates_str:<12} {worksheets_str:<12} {bestseller_str:<12} ${price:<7.2f}")


# ── Example 4: Publish Manual with Templates ─────────────────────────────────
def example_publish_manual(pdf_path):
    """
    Example: Publish a manual/guide with templates and checklists.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Publish Manual with Templates")
    print("=" * 70)

    product = gp.publish_manual(
        title="Institutional Partnerships Playbook",
        description="""Complete system for landing nonprofit and government contracts.

INSIDE:
- 26+ qualified prospects in Phoenix (contact list included)
- Email scripts that get responses (copy-paste ready)
- Sales call framework with objection handling
- Proposal templates (customizable)
- Deal evaluation checklist
- First 30 days post-close playbook

TEMPLATES INCLUDED:
- Prospect research template
- Email outreach scripts (5 variations)
- Phone call scripts
- Proposal template with examples
- Contract evaluation checklist
- Implementation timeline

RESULTS:
- Land first $25K contract in 60 days
- Build recurring revenue stream
- Typical contracts: $25K-$75K annually

Your first quarter: $25K contract landed and operational.""",
        pdf_path=pdf_path,
        author="Already Here LLC",
        includes_templates=True,
        includes_checklists=True,
        word_count=8500,
        source_article_url="https://quantam101.github.io/content/",
    )

    if product:
        print(f"\n[OK] Manual published: {product.name}")
        print(f"    Price: ${product.price:.2f}")
        print(f"    URL: {product.product_url}")
        return product
    else:
        print("[ERROR] Failed to publish manual")
        return None


# ── Example 5: Publish Course ────────────────────────────────────────────────
def example_publish_course(pdf_path):
    """
    Example: Publish a comprehensive course.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Publish Course")
    print("=" * 70)

    product = gp.publish_course(
        title="4-Stream Business System: $600K in 90 Days",
        description="""Complete blueprint for building a $600K+ business in 90 days.

5-MODULE COURSE:
Module 1: Why 4 Streams (not 1) — diversification strategy
Module 2: Institutional Partnerships ($210K/year recurring)
Module 3: Vehicle Recovery & Flipping ($300K/year profit)
Module 4: Gig Work Integration ($100K/year with margins)
Module 5: Content Monetization Engine ($825K+/year)

INCLUDES:
- 7 video lessons (total 2.5 hours)
- Complete implementation workbooks
- Real-world case studies with numbers
- 90-day action plan with weekly breakdown
- Daily task checklist
- Month 1 results documentation

CERTIFICATES:
- Complete all 5 modules
- Earn verified completion certificate
- Access to exclusive alumni community

REAL NUMBERS FROM DAY 1:
- Month 1: $4,700 revenue (all 4 streams)
- Month 2: $15,200 revenue
- Month 3: $28,500 revenue
- Scaling path to $50K+/month""",
        content_file_path=pdf_path,
        author="Already Here LLC",
        modules_count=5,
        includes_video=True,
        includes_worksheets=True,
        estimated_hours=12.5,
        word_count=45000,
        price=49.99,
    )

    if product:
        print(f"\n[OK] Course published: {product.name}")
        print(f"    Price: ${product.price:.2f}")
        print(f"    URL: {product.product_url}")
        return product
    else:
        print("[ERROR] Failed to publish course")
        return None


# ── Example 6: Update with Affiliate Links ───────────────────────────────────
def example_update_affiliate_links(product_id):
    """
    Example: Inject affiliate links into product description.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Update Product with Affiliate Links")
    print("=" * 70)

    affiliate_links = {
        "Python": "https://amzn.to/python-course",
        "Business book": "https://amzn.to/business-book",
        "Software tools": "https://affiliate.tools.com",
    }

    if product_id:
        success = gp.update_product_with_affiliate_links(
            gumroad_id=product_id,
            content_type="course",
            affiliate_links=affiliate_links,
        )

        if success:
            print("[OK] Affiliate links updated")
        else:
            print("[ERROR] Failed to update affiliate links")
    else:
        print("[INFO] Skipping — no product ID provided")


# ── Example 7: Fetch Sales Data ──────────────────────────────────────────────
def example_fetch_sales(product_id):
    """
    Example: Fetch sales data for a product.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Fetch Product Sales Data")
    print("=" * 70)

    if product_id:
        sales_data = gp.fetch_product_sales(product_id)

        if sales_data:
            print(f"[OK] Sales data for {sales_data['name']}:")
            print(f"    Sales count: {sales_data['sales_count']}")
            print(f"    Price: ${sales_data['price']:.2f}")
            print(f"    Revenue: ${sales_data['revenue_usd']:.2f}")
            print(f"    URL: {sales_data['url']}")
        else:
            print("[ERROR] Failed to fetch sales data")
    else:
        print("[INFO] Skipping — no product ID provided")


# ── Example 8: Generate Sales Report ─────────────────────────────────────────
def example_sales_report():
    """
    Example: Generate sales report for all products.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Generate Sales Report")
    print("=" * 70)

    # In practice, you'd load your GumroadProduct list
    # For demo, create sample products
    products = [
        gp.GumroadProduct(
            gumroad_id="sample-1",
            name="Vehicle Flipping Guide",
            description="Complete guide to buying cheap cars and flipping",
            price=7.99,
            content_type="manual",
            sales_count=42,
            product_url="https://alreadyhere.gumroad.com/l/vehicle-flip",
        ),
        gp.GumroadProduct(
            gumroad_id="sample-2",
            name="Institutional Partnerships Playbook",
            description="Land nonprofit/government contracts system",
            price=12.99,
            content_type="manual",
            sales_count=28,
            product_url="https://alreadyhere.gumroad.com/l/partnerships",
        ),
        gp.GumroadProduct(
            gumroad_id="sample-3",
            name="4-Stream Business System",
            description="Complete $600K in 90 days blueprint",
            price=49.99,
            content_type="course",
            sales_count=15,
            product_url="https://alreadyhere.gumroad.com/l/4streams",
        ),
    ]

    report = gp.generate_sales_report(products)
    print(report)


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("GUMROAD PUBLISHER — USAGE EXAMPLES")
    print("=" * 70)

    # Show pricing recommendations
    example_pricing_recommendations()

    # Example 1: Convert article to ebook
    pdf_path = example_article_to_ebook()

    # Example 2: Publish ebook (requires API token)
    if os.getenv("GUMROAD_API_TOKEN"):
        product = example_publish_ebook(pdf_path)
        product_id = product.gumroad_id if product else None

        # Example 4: Publish manual
        manual = example_publish_manual(pdf_path)

        # Example 5: Publish course
        course = example_publish_course(pdf_path)

        # Example 6: Update with affiliate links
        if product_id:
            example_update_affiliate_links(product_id)

        # Example 7: Fetch sales
        if product_id:
            example_fetch_sales(product_id)
    else:
        print("\n[INFO] GUMROAD_API_TOKEN not set — skipping API examples")
        print("       Set this env var to test publishing functionality")

    # Example 8: Sales report (demo with sample data)
    example_sales_report()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70 + "\n")

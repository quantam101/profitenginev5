#!/usr/bin/env python3
"""
GUMROAD COMPLETE AUTOMATION
Creates 4 products on Gumroad with all details ready
Run: python gumroad-complete-automation.py
"""

import requests
import json
import os
from datetime import datetime

# Configuration
GUMROAD_TOKEN = os.environ.get("GUMROAD_API_KEY", "")
GUMROAD_USERNAME = os.environ.get("GUMROAD_USERNAME", "alreadyhere")
API_URL = "https://api.gumroad.com/v2"

if not GUMROAD_TOKEN:
    raise ValueError("GUMROAD_API_KEY environment variable not set")

# Product definitions
PRODUCTS = [
    {
        "name": "Master Blueprint: Build a $600K Business in 90 Days",
        "description": """The complete 4-stream business system with everything you need to build a $600K+ business.

✓ 7 chapters covering all revenue streams
✓ Real numbers from Month 1 ($4,700 revenue)
✓ Institutional partnership scripts (26 prospects identified)
✓ Vehicle recovery sourcing & flipping guide
✓ Gig work contractor model (75% margins)
✓ Content monetization strategy ($825K+ potential)
✓ 90-day action plan with weekly breakdown
✓ Real case studies & examples

What's inside:
- Chapter 1: Why 4 streams work (not 1)
- Chapter 2: Institutional partnerships ($210K/year recurring)
- Chapter 3: Vehicle recovery & flipping ($300K/year profit)
- Chapter 4: Gig work integration ($100K/year)
- Chapter 5: Content engine ($825K+/year)
- Chapter 6: Complete 90-day action plan
- Chapter 7: Real Month 1 numbers

No theory. Just real numbers and proven systems that work.""",
        "price": 12700,
        "summary": "Complete 4-stream business system with proven playbooks and real numbers"
    },
    {
        "name": "Institutional Partnerships Playbook",
        "description": """Complete system for landing nonprofit/government fleet maintenance contracts.

✓ 26 Phoenix organizations (contact info + research template)
✓ Email scripts that get responses
✓ Phone call framework
✓ Proposal templates (customizable)
✓ Objection handling (5 common objections with responses)
✓ Deal evaluation checklist
✓ First 30 days onboarding plan
✓ Real contract examples

Land your first $25K contract in 60 days. All templates included.

What's included:
- Complete prospect list with research template
- Copy-paste email scripts
- Sales call framework and scripts
- Proposal template with real examples
- Objection handling guide
- Closing techniques
- Post-close onboarding checklist""",
        "price": 7200,
        "summary": "26 prospects + sales scripts to land your first $25K nonprofit fleet contract"
    },
    {
        "name": "Vehicle Recovery & Fix-and-Flip: The Complete Guide",
        "description": """How to find cheap cars, repair them for $1,500, and flip for $3,500-$6,000 profit.

✓ 5 ways to source cars (Craigslist, auctions, estate sales, etc.)
✓ Deal evaluation scorecard
✓ Repair budget breakdown ($1,500 max)
✓ Where to find parts cheap
✓ Sales strategies (Facebook, Craigslist, dealers)
✓ Real examples (3 car flips with actual numbers)
✓ Scaling to 8-12 cars/month
✓ Profit calculator spreadsheet

8-12 vehicles/month = $25K-$50K monthly profit. Here's exactly how.

What's included:
- Sourcing guide (5 channels to find cheap cars)
- Deal evaluation scorecard
- Repair budget checklist
- Sales channel guide
- Real flip examples with actual numbers
- Scaling playbook
- Profit calculator spreadsheet""",
        "price": 5700,
        "summary": "Find cars for $500, flip for $5,000+. Complete sourcing + flipping guide"
    },
    {
        "name": "Gig Work System: High-Margin Jobs + Scaling to 50/Month",
        "description": """The complete system for 75%+ margin gig work.

✓ 5 high-margin job types (junk removal, moving, estate cleanout)
✓ Pricing strategy for $800-$1,500 jobs
✓ Contractor recruitment & vetting templates
✓ Two-tier contractor model (flexible vs. dedicated)
✓ Demand generation across 5 channels
✓ Fleet economics (why company vehicles = 5x profit)
✓ Operations checklist
✓ Scaling to 30-50 jobs/month

$600-$1,500 per job × 30 jobs/month = $18K-$45K gross profit.

What's included:
- High-margin job types guide
- Pricing calculator
- Contractor recruitment templates
- Contractor agreement template
- Demand generation playbook (5 channels)
- Operations checklist
- Scaling from 5 to 50 jobs/month
- Profit projections by month""",
        "price": 5700,
        "summary": "High-margin jobs with contractors. Scale from 0 to 50 jobs/month"
    }
]

def create_product(product_data):
    """Create a product on Gumroad"""
    try:
        payload = {
            "name": product_data["name"],
            "description": product_data["description"],
            "price": product_data["price"],
            "currency": "usd",
            "summary": product_data["summary"]
        }

        response = requests.post(
            f"{API_URL}/products",
            headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"},
            data=payload,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "name": product_data["name"],
                "price": product_data["price"] / 100,
                "url": result.get("product", {}).get("url", ""),
                "id": result.get("product", {}).get("id", "")
            }
        else:
            return {
                "success": False,
                "name": product_data["name"],
                "error": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "name": product_data["name"],
            "error": str(e)
        }

def main():
    print("\n" + "="*60)
    print("🚀 GUMROAD PRODUCT AUTOMATION")
    print("="*60)
    print(f"\n📍 Store: https://{GUMROAD_USERNAME}.gumroad.com")
    print(f"👤 User: Already Here LLC")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-"*60)

    results = []

    for i, product in enumerate(PRODUCTS, 1):
        print(f"\n📦 Creating Product {i}/4: {product['name'][:40]}...")
        result = create_product(product)
        results.append(result)

        if result["success"]:
            print(f"   ✅ Success! Price: ${result['price']}")
        else:
            print(f"   ❌ Failed: {result['error']}")

    print("\n" + "-"*60)
    print("\n📊 SUMMARY")
    print("-"*60)

    successful = sum(1 for r in results if r["success"])
    total_value = sum(p["price"] for p in PRODUCTS) / 100

    print(f"\n✅ Successfully created: {successful}/4 products")
    print(f"💰 Total product value: ${total_value:.2f}")
    print(f"\n📍 View all products at:")
    print(f"   https://{GUMROAD_USERNAME}.gumroad.com")

    print("\n" + "="*60)
    print("⚠️  NEXT STEPS")
    print("="*60)
    print("""
1. Go to: https://alreadyhere.gumroad.com
2. For EACH product:
   - Click the product
   - Upload the PDF file
   - Check "Deliver automatically"
   - Save
3. Share your store URL with your network:
   https://alreadyhere.gumroad.com

4. SECURITY: Rotate your API token!
   - Go to Gumroad → Settings → API
   - Regenerate token
   - Update any automation scripts
""")

    print("="*60)
    print("✨ Automation complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

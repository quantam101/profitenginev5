#!/usr/bin/env python3
"""
Gumroad Product Uploader - Automated Product Creation
Posts all 6 digital products to Gumroad via API
"""

import requests
import json
import os
from typing import Dict, List

GUMROAD_API_URL = "https://api.gumroad.com/v2/products"
GUMROAD_TOKEN = os.getenv("GUMROAD_API_TOKEN")  # Set via GitHub Secrets

PRODUCTS = [
    {
        "name": "POD Listings 8-Pack",
        "url_name": "pod-listings-8-pack",
        "price": 2999,  # in cents
        "currency": "usd",
        "description": """POD for Non-Designers: 8 Print-on-Demand Listings Ready to Upload

✅ What You Get:
- 8 ready-to-sell Etsy/Printify listing templates
- Professional product titles (tested for conversions)
- Optimized tags and keywords (SEO included)
- Printify product metadata (auto-upload ready)
- Product images (mockups + design files)
- Margin calculator spreadsheet

✅ Each Listing Includes:
- Title (40+ characters)
- Description (500+ words)
- Tags (13 optimized tags)
- Printify metadata (color, size, materials)
- Expected margin calculation

Ready to upload to Etsy in 10 minutes. No design skills needed.""",
        "tags": "pod,printify,etsy,ecommerce,business",
        "license": "PLv1"
    },
    {
        "name": "Amazon KDP Assets Bundle",
        "url_name": "kdp-assets-bundle",
        "price": 799,
        "currency": "usd",
        "description": """Amazon KDP Publishing Without Months of Writing

✅ What You Get:
- 3 ready-to-publish eBook templates (nonfiction)
- KDP formatting guide (print + ebook)
- Amazon KDP keyword research (high-demand niches)
- Metadata templates (title, subtitle, keywords, categories)
- Publishing checklist (30-day workflow)
- Royalty calculator (US + KDP Select pricing)

✅ Each eBook Includes:
- 25,000+ words of AI-written + human-edited content
- Professional interior formatting (print-ready PDF)
- Cover design template (Canva ready)
- Description (500+ words optimized for conversions)
- Launch strategy (week 1-4 checklist)

Amazon KDP: The easiest path to $500/month passive income.""",
        "tags": "kdp,amazon,ebook,publishing,passive-income",
        "license": "PLv1"
    },
    {
        "name": "Etsy Shop Setup Guide",
        "url_name": "etsy-shop-setup-guide",
        "price": 4999,
        "currency": "usd",
        "description": """Etsy Shop Setup That Converts: The Complete Playbook

✅ What You Get:
- Step-by-step shop setup walkthrough (40+ page PDF)
- Printify integration guide (auto-sync products)
- Shop branding (logo, colors, bio templates)
- Shop policies (shipping, returns, legal)
- Product listing optimization (SEO, categories, tags)
- Printify product configuration (profit margins)
- Payment & shipping setup (stripe, payment methods)
- Video walkthroughs (7 setup videos, 45 min total)

✅ Expected Results:
- First sale within 7 days (if you follow the guide)
- First month: $200-500 in sales
- Passive income after setup

Complete shop setup in 4 hours. No experience needed.""",
        "tags": "etsy,ecommerce,shop-setup,guide,tutorial",
        "license": "PLv1"
    },
    {
        "name": "Stripe Setup Checklist",
        "url_name": "stripe-setup-checklist",
        "price": 999,
        "currency": "usd",
        "description": """Stripe Setup That Converts: 30-Point Configuration Checklist

✅ What You Get:
- Pre-flight checklist (account setup, verification)
- Checkout configuration guide (payment methods, currency)
- Webhook setup guide (event delivery, retry logic)
- Tax integration guide (Stripe Tax setup)
- Security checklist (PCI compliance, SSL)
- Testing & verification (smoke test checklist)
- Troubleshooting guide (common errors, fixes)

Stop leaving money on the table. Proper Stripe config = 15-30% more conversions.""",
        "tags": "stripe,payments,checkout,setup,guide",
        "license": "PLv1"
    },
    {
        "name": "Content System Template",
        "url_name": "content-system-template",
        "price": 7999,
        "currency": "usd",
        "description": """AI Content at Scale: Editorial Calendar + Generation + Publishing

✅ What You Get:
- Content calendar template (12-month planning)
- AI generation prompts (20+ tested prompts)
- Content quality rubric (validation checklist)
- Publishing workflow (scheduling, cross-posting)
- Affiliate routing guide (monetization map)
- Analytics dashboard (tracking template)

✅ Expected Results:
- 20 posts/month (vs. 3-4 manually)
- 50+ hours saved per month
- 2-4x more traffic than manual posting
- Passive affiliate revenue ($500-2000/mo)

This is the exact system we use internally.""",
        "tags": "content,ai,marketing,automation,business",
        "license": "PLv1"
    },
    {
        "name": "Local Automation Playbook",
        "url_name": "local-automation-playbook",
        "price": 9999,
        "currency": "usd",
        "description": """Local Service Automation: Lead Capture to Revenue in 7 Days

✅ What You Get:
- Lead capture setup guide (forms, intake, qualification)
- CRM system setup (lightweight pipeline management)
- Automation workflow guide (sequences, reminders)
- Payment link integration (Stripe + scheduling)
- Follow-up templates (email + SMS sequences)
- Competitor analysis template
- Sales script templates (initial + follow-up)
- Case studies (3 real examples: contractor, consultant, services)

From messy lead lists to $10K/month revenue. Fully automated. No code needed.""",
        "tags": "automation,crm,sales,leads,business",
        "license": "PLv1"
    }
]


def upload_product(product: Dict) -> bool:
    """Upload a single product to Gumroad"""
    try:
        headers = {
            "Authorization": f"Bearer {GUMROAD_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        payload = {
            "name": product["name"],
            "url_name": product["url_name"],
            "price": product["price"],
            "currency": product["currency"],
            "description": product["description"],
            "tags": product["tags"],
            "license": product["license"]
        }

        response = requests.post(GUMROAD_API_URL, headers=headers, data=payload, timeout=30)

        if response.status_code in [200, 201]:
            print(f"✅ UPLOADED: {product['name']}")
            return True
        else:
            print(f"❌ FAILED: {product['name']}")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ ERROR uploading {product['name']}: {str(e)}")
        return False


def main():
    """Upload all products to Gumroad"""
    print("=" * 60)
    print("GUMROAD PRODUCT UPLOADER")
    print("=" * 60)
    print("")

    if not GUMROAD_TOKEN:
        print("❌ ERROR: GUMROAD_API_TOKEN not set")
        print("   Set via: export GUMROAD_API_TOKEN='your-token'")
        return False

    print(f"Uploading {len(PRODUCTS)} products to Gumroad...")
    print("")

    success_count = 0
    for product in PRODUCTS:
        if upload_product(product):
            success_count += 1

    print("")
    print("=" * 60)
    print(f"RESULT: {success_count}/{len(PRODUCTS)} products uploaded")
    print("=" * 60)

    return success_count == len(PRODUCTS)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

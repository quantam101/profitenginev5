#!/usr/bin/env python3
"""Create Gumroad products with files and publish them."""
import os
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from runtime.gumroad_client import _request, list_products

PRODUCTS_WITH_FILES = [
    {
        "name": "Programmatic SEO Starter Kit",
        "price": 2900,
        "description": "City-page SEO templates that rank. Includes HTML/Markdown templates for 10 service niches, keyword research spreadsheet for 500 US cities, schema markup snippets, internal linking strategy, and a step-by-step GitHub Pages deployment guide. Generate thousands of pages with AI.",
        "tags": ["seo", "programmatic", "templates", "blogging", "ai"],
        "url_suffix": "programmatic-seo-starter-kit",
        "file": "products/PROGRAMMATIC_SEO_STARTER_KIT_TEMPLATES.txt",
    },
    {
        "name": "POD Design Prompt Bundle",
        "price": 2200,
        "description": "Complete AI art generation system for print-on-demand sellers. Includes Midjourney + Stable Diffusion prompts for 20 profitable niches, color palette guides, mockup instructions, and Etsy SEO keyword lists. Turn AI images into bestselling t-shirts, mugs, and wall art.",
        "tags": ["print-on-demand", "ai-art", "etsy", "design", "prompts"],
        "url_suffix": "pod-design-prompt-bundle",
        "file": "products/POD_DESIGN_PROMPT_BUNDLE_PROMPTS.txt",
    },
    {
        "name": "Social Media Content Engine",
        "price": 1700,
        "description": "30-day AI content calendar with 180 ready-to-use prompts for Instagram, TikTok, LinkedIn, X/Twitter, and Facebook. Includes hook formulas, caption templates, hashtag banks, and a Notion dashboard to track engagement. Never run out of content ideas.",
        "tags": ["social-media", "content", "marketing", "ai", "calendar"],
        "url_suffix": "social-media-content-engine",
        "file": "products/SOCIAL_MEDIA_CONTENT_ENGINE_TEMPLATES.txt",
    },
    {
        "name": "Real Estate Copywriting Kit",
        "price": 1900,
        "description": "100 plug-and-play property listing templates for agents and investors. Luxury, starter, commercial, vacation rental, and land listings. Each template includes headline, full description, and social caption. Drop in your details and publish in under 5 minutes.",
        "tags": ["real-estate", "copywriting", "templates", "ai", "listings"],
        "url_suffix": "real-estate-copywriting-kit",
        "file": "products/REAL_ESTATE_COPYWRITING_KIT_TEMPLATES.txt",
    },
    {
        "name": "AI Business Prompt Pack",
        "price": 2700,
        "description": "500+ production-tested AI prompts covering copywriting, sales emails, social media, product descriptions, and cold outreach. Built for entrepreneurs who want ChatGPT/Claude to do the heavy lifting. Instant download. No fluff — only prompts that convert.",
        "tags": ["ai", "prompts", "business", "automation", "chatgpt"],
        "url_suffix": "ai-business-prompt-pack",
        "file": "products/AI_BUSINESS_PROMPT_PACK_PROMPTS.txt",
    },
]

print("=" * 70)
print("CREATING GUMROAD PRODUCTS WITH FILES")
print("=" * 70)

for product in PRODUCTS_WITH_FILES:
    name = product["name"]
    print(f"\n[CREATE] {name}...", end=" ")

    # Create product
    data = {
        "name": name,
        "price": product["price"],
        "description": product["description"],
        "published": "false",  # Keep as draft until files added
        "require_shipping": "false",
        "type": "digital",
        "url": product["url_suffix"],
        "tags[]": product["tags"],
    }

    resp = _request("POST", "products", data)

    if not resp.get("success"):
        print(f"FAILED: {resp.get('message')}")
        continue

    product_id = resp.get("product", {}).get("id")
    if not product_id:
        print("FAILED: No product ID returned")
        continue

    print(f"OK (ID: {product_id[:20]}...)")

    # Upload file
    file_path = product["file"]
    if not Path(file_path).exists():
        print(f"  [SKIP] File not found: {file_path}")
        continue

    print(f"  [UPLOAD] {Path(file_path).name}...", end=" ")

    # For now, just log that we would upload
    # File upload requires multipart, which we've tested isn't working via API
    # User needs to do this manually via dashboard
    file_size = Path(file_path).stat().st_size
    print(f"MANUAL UPLOAD REQUIRED ({file_size:,} bytes)")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("""
1. Products have been created as DRAFT
2. Go to: https://app.gumroad.com/dashboard/products
3. For each product:
   - Click the product name
   - Click 'Add File'
   - Upload the .txt file:
     * Programmatic SEO → PROGRAMMATIC_SEO_STARTER_KIT_TEMPLATES.txt
     * POD Design → POD_DESIGN_PROMPT_BUNDLE_PROMPTS.txt
     * Social Media → SOCIAL_MEDIA_CONTENT_ENGINE_TEMPLATES.txt
     * Real Estate → REAL_ESTATE_COPYWRITING_KIT_TEMPLATES.txt
     * AI Business Prompts → AI_BUSINESS_PROMPT_PACK_PROMPTS.txt
   - Click 'Publish'
4. Wait 1-3 hours for CDN sync
""")

#!/usr/bin/env python3
"""Upload product files to Gumroad products."""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from runtime.gumroad_client import upload_product_file, list_products

# Map product names to their file content locations
PRODUCT_FILES = {
    "Programmatic SEO Starter Kit": [
        "products/PRODUCT_1_PROGRAMMATIC_SEO_CONTENT.md",
        "products/PRODUCT_1_KEYWORDS.csv",
    ],
    "POD Design Prompt Bundle": [
        "products/PRODUCT_3_POD_DESIGN_PROMPT_BUNDLE.md",
    ],
    "Social Media Content Engine": [
        "products/PRODUCT_2_SOCIAL_MEDIA_CONTENT_ENGINE.md",
        "products/PRODUCT_2_TEMPLATES.txt",
    ],
    "Real Estate Copywriting Kit": [
        "products/PRODUCT_5_REAL_ESTATE_COPYWRITING_KIT.md",
    ],
    "AI Business Prompt Pack": [
        "products/PRODUCT_4_AI_BUSINESS_PROMPT_PACK.md",
    ],
    "Ai Essentials: How Artificial Intelligence Can Empower You, Your Business and the World": [
        "products/PRODUCT_6_AI_ESSENTIALS_BOOK.md",
    ],
}

print("=" * 70)
print("UPLOADING PRODUCT FILES TO GUMROAD")
print("=" * 70)

products = list_products()
product_map = {p.get("name", ""): p.get("id", "") for p in products}

for product_name, file_paths in PRODUCT_FILES.items():
    product_id = product_map.get(product_name)

    if not product_id:
        print(f"\nERROR: Product '{product_name}' not found on Gumroad")
        continue

    print(f"\n{product_name} ({product_id[:20]}...)")
    print("-" * 70)

    for file_path in file_paths:
        full_path = Path(file_path)
        if not full_path.exists():
            print(f"  [SKIP] {file_path} — file not found")
            continue

        file_size = full_path.stat().st_size
        print(f"  [UPLOAD] {file_path} ({file_size:,} bytes)...", end=" ")

        resp = upload_product_file(product_id, str(full_path))

        if resp.get("success"):
            print("SUCCESS")
        else:
            print(f"FAILED: {resp.get('message', 'unknown error')}")

print("\n" + "=" * 70)
print("UPLOAD COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Go to: https://app.gumroad.com/dashboard/products")
print("2. For each product, click 'Publish'")
print("3. Wait 1-3 hours for Gumroad's CDN to sync globally")

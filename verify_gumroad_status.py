#!/usr/bin/env python3
"""Verify Gumroad product publication status."""
import os
from dotenv import load_dotenv

load_dotenv()

from runtime.gumroad_client import _request, list_products

print("=" * 70)
print("GUMROAD PRODUCT PUBLICATION STATUS CHECK")
print("=" * 70)

products = list_products()

if not products:
    print("\nERROR: No products found!")
    exit(1)

print(f"\nTotal products: {len(products)}\n")

for i, p in enumerate(products, 1):
    name = p.get('name', '?')
    product_id = p.get('id', '?')
    published = p.get('published', False)
    url = p.get('short_url', p.get('url', '?'))
    price = p.get('price', 0) / 100

    status = "PUBLISHED" if published else "DRAFT"

    print(f"{i}. {name}")
    print(f"   ID:        {product_id}")
    print(f"   Price:     ${price:.2f}")
    print(f"   Status:    {status}")
    print(f"   URL:       {url}")
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
published_count = sum(1 for p in products if p.get('published'))
draft_count = len(products) - published_count

print(f"Published: {published_count}")
print(f"Draft:     {draft_count}")

if draft_count > 0:
    print("\nNOTE: Products in DRAFT status need to be published manually.")
    print("      Go to: https://app.gumroad.com/dashboard/products")
    print("      Then click 'Publish' on each draft product.")
else:
    print("\nSUCCESS: All products are published!")

#!/usr/bin/env python3
"""Publish all draft Gumroad products using POST requests."""
import os
from dotenv import load_dotenv

load_dotenv()

from runtime.gumroad_client import _request, list_products

print("=" * 70)
print("PUBLISHING DRAFT GUMROAD PRODUCTS")
print("=" * 70)

products = list_products()
draft_products = [p for p in products if not p.get('published')]

if not draft_products:
    print("\nAll products are already published!")
    exit(0)

print(f"\nFound {len(draft_products)} draft products to publish:\n")

for p in draft_products:
    name = p.get('name', '?')
    product_id = p.get('id', '?')

    print(f"Publishing: {name}...", end=" ")

    # Try POST request to publish endpoint
    resp = _request("POST", f"products/{product_id}/publish", {})

    if resp.get('success'):
        print("SUCCESS")
    else:
        error = resp.get('message', 'unknown error')
        print(f"FAILED: {error}")

        # Try alternative: POST with published=true parameter
        if 'not found' in str(error).lower() or 'endpoint' in str(error).lower():
            print(f"         Trying alternative endpoint...", end=" ")
            resp = _request("POST", "products", {
                "id": product_id,
                "published": "true"
            })
            if resp.get('success'):
                print("SUCCESS")
            else:
                print(f"FAILED: {resp.get('message', 'unknown error')}")

print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

# Verify all products are now published
products = list_products()
published_count = sum(1 for p in products if p.get('published'))
draft_count = len(products) - published_count

print(f"\nPublished: {published_count}")
print(f"Draft:     {draft_count}")

if draft_count == 0:
    print("\nSUCCESS: All products are now published!")
else:
    print(f"\nNOTE: {draft_count} products need manual publishing.")
    print("Visit: https://app.gumroad.com/dashboard/products")
    print("Click the 'Publish' button for each draft product.\n")
    for p in [pr for pr in products if not pr.get('published')]:
        print(f"  - {p.get('name', '?')}")

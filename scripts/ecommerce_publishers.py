#!/usr/bin/env python3
"""
E-Commerce Publishers for ProfitEngine

Distributes content to:
- Etsy (listing updates and descriptions)
- Gumroad (product updates and cross-promotion)
- Printify (POD product updates)
"""
from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional, List
import httpx

# ── Environment Variables ──────────────────────────────────────────────────────

ETSY_SHOP_ID = os.getenv("ETSY_SHOP_ID", "").strip()
ETSY_API_KEY = os.getenv("ETSY_API_KEY", "").strip()

GUMROAD_API_TOKEN = os.getenv("GUMROAD_API_TOKEN", "").strip()
GUMROAD_CREATOR_ID = os.getenv("GUMROAD_CREATOR_ID", "").strip()

PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_TOKEN", "").strip() or os.getenv("PRINTIFY_API_KEY", "").strip()
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID", "").strip()

# ── Etsy Integration ────────────────────────────────────────────────────────

def get_etsy_listings() -> List[Dict[str, Any]]:
    """Fetch all Etsy shop listings"""
    if not all([ETSY_SHOP_ID, ETSY_API_KEY]):
        return []

    try:
        headers = {"x-api-key": ETSY_API_KEY}
        r = httpx.get(
            f"https://openapi.etsy.com/v3/application/shops/{ETSY_SHOP_ID}/listings/active",
            headers=headers,
            timeout=30,
        )

        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    except Exception as e:
        print(f"[WARN] Could not fetch Etsy listings: {e}")
        return []


def update_etsy_listing_description(listing_id: str, article: Dict[str, Any]) -> Optional[str]:
    """Update Etsy listing description with article content"""
    if not all([ETSY_SHOP_ID, ETSY_API_KEY]):
        print("[SKIP] Etsy credentials not configured")
        return None

    try:
        title = article.get("title", "")
        body = article.get("body", "")[:1000]
        tags = article.get("tags", [])

        description = f"{body}\n\n## Related Blog Post\n\n{title}"

        payload = {
            "description": description,
            "tags": tags[:13],  # Etsy allows max 13 tags
        }

        headers = {
            "x-api-key": ETSY_API_KEY,
            "Content-Type": "application/json",
        }

        r = httpx.patch(
            f"https://openapi.etsy.com/v3/application/shops/{ETSY_SHOP_ID}/listings/{listing_id}",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if r.status_code in (200, 204):
            print(f"[OK] Updated Etsy listing {listing_id}")
            return f"https://www.etsy.com/shop/{ETSY_SHOP_ID}/listing/{listing_id}"
        else:
            print(f"[FAIL] Etsy {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        print(f"[FAIL] Etsy: {e}")
        return None


def publish_etsy_cross_promotion(article: Dict[str, Any]) -> Optional[str]:
    """Post article promotion to Etsy shop"""
    if not ETSY_SHOP_ID:
        print("[SKIP] ETSY_SHOP_ID not configured")
        return None

    listings = get_etsy_listings()
    if not listings:
        return None

    # Update first 3 listings with article cross-promotion
    updated = 0
    for listing in listings[:3]:
        listing_id = listing.get("listing_id", "")
        result = update_etsy_listing_description(listing_id, article)
        if result:
            updated += 1

    if updated > 0:
        print(f"[OK] Cross-promoted to {updated} Etsy listings")
        return f"https://www.etsy.com/shop/{ETSY_SHOP_ID}"

    return None


# ── Gumroad Integration ──────────────────────────────────────────────────────

def get_gumroad_products() -> List[Dict[str, Any]]:
    """Fetch all Gumroad products"""
    if not GUMROAD_API_TOKEN:
        return []

    try:
        headers = {"Authorization": f"Bearer {GUMROAD_API_TOKEN}"}
        r = httpx.get(
            "https://api.gumroad.com/v2/products",
            headers=headers,
            timeout=30,
        )

        if r.status_code == 200:
            return r.json().get("products", [])
        return []
    except Exception as e:
        print(f"[WARN] Could not fetch Gumroad products: {e}")
        return []


def update_gumroad_product_description(product_id: str, article: Dict[str, Any]) -> Optional[str]:
    """Update Gumroad product description with article content"""
    if not GUMROAD_API_TOKEN:
        print("[SKIP] Gumroad API token not configured")
        return None

    try:
        title = article.get("title", "")
        body = article.get("body", "")[:500]
        meta = article.get("meta_description", "")

        # Build rich description
        description = f"{meta}\n\nRelated article: {title}\n\n{body}"

        payload = {
            "description": description,
        }

        headers = {
            "Authorization": f"Bearer {GUMROAD_API_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        r = httpx.post(
            f"https://api.gumroad.com/v2/products/{product_id}",
            data=payload,
            headers=headers,
            timeout=30,
        )

        if r.status_code == 200:
            print(f"[OK] Updated Gumroad product {product_id}")
            data = r.json()
            url = data.get("product", {}).get("url", "")
            return url
        else:
            print(f"[FAIL] Gumroad {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        print(f"[FAIL] Gumroad: {e}")
        return None


def publish_gumroad_cross_promotion(article: Dict[str, Any]) -> Optional[str]:
    """Cross-promote article on Gumroad products"""
    if not GUMROAD_API_TOKEN:
        print("[SKIP] Gumroad API token not configured")
        return None

    products = get_gumroad_products()
    if not products:
        return None

    # Update first 2 products with article
    updated = 0
    for product in products[:2]:
        product_id = product.get("id", "")
        result = update_gumroad_product_description(product_id, article)
        if result:
            updated += 1

    if updated > 0:
        print(f"[OK] Cross-promoted to {updated} Gumroad products")
        return f"https://gumroad.com"

    return None


# ── Printify Integration ──────────────────────────────────────────────────────

def get_printify_products() -> List[Dict[str, Any]]:
    """Fetch all Printify products"""
    if not all([PRINTIFY_API_KEY, PRINTIFY_SHOP_ID]):
        return []

    try:
        headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
        r = httpx.get(
            f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products.json",
            headers=headers,
            timeout=30,
        )

        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        print(f"[WARN] Could not fetch Printify products: {e}")
        return []


def update_printify_product_description(product_id: str, article: Dict[str, Any]) -> Optional[str]:
    """Update Printify product description with article content"""
    if not all([PRINTIFY_API_KEY, PRINTIFY_SHOP_ID]):
        print("[SKIP] Printify credentials not configured")
        return None

    try:
        title = article.get("title", "")
        body = article.get("body", "")[:300]

        description = f"{body}\n\nInspired by: {title}"

        payload = {
            "description": description,
        }

        headers = {
            "Authorization": f"Bearer {PRINTIFY_API_KEY}",
            "Content-Type": "application/json",
        }

        r = httpx.put(
            f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products/{product_id}.json",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if r.status_code in (200, 201):
            print(f"[OK] Updated Printify product {product_id}")
            return f"https://printify.com/products/{product_id}"
        else:
            print(f"[FAIL] Printify {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        print(f"[FAIL] Printify: {e}")
        return None


def publish_printify_cross_promotion(article: Dict[str, Any]) -> Optional[str]:
    """Cross-promote article on Printify products"""
    if not all([PRINTIFY_API_KEY, PRINTIFY_SHOP_ID]):
        print("[SKIP] Printify credentials not configured")
        return None

    products = get_printify_products()
    if not products:
        return None

    # Update first product with article
    updated = 0
    for product in products[:1]:
        product_id = product.get("id", "")
        result = update_printify_product_description(product_id, article)
        if result:
            updated += 1

    if updated > 0:
        print(f"[OK] Cross-promoted to {updated} Printify products")
        return f"https://printify.com"

    return None


# ── Summary of All E-Commerce Platforms ────────────────────────────────────

ECOMMERCE_PUBLISHERS = {
    "etsy": publish_etsy_cross_promotion,
    "gumroad": publish_gumroad_cross_promotion,
    "printify": publish_printify_cross_promotion,
}


def publish_to_all_ecommerce(article: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Publish article cross-promotions to all configured e-commerce platforms

    Returns dict of {platform: url}
    """
    results = {}

    for platform, publisher in ECOMMERCE_PUBLISHERS.items():
        results[platform] = publisher(article)

    return results

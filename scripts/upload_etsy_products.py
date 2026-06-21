#!/usr/bin/env python3
"""
Etsy Product Uploader - Automated POD Listing Creation
Posts all 8 POD products to Etsy via API
Requires: Etsy API token + Shop ID
"""

import requests
import json
import os
from typing import Dict, List

ETSY_API_URL = "https://openapi.etsy.com/v3/application/shops"
ETSY_ACCESS_TOKEN = os.getenv("ETSY_ACCESS_TOKEN")  # Set via GitHub Secrets
ETSY_SHOP_ID = os.getenv("ETSY_SHOP_ID")  # Already Here LLC shop

PRODUCTS = [
    {
        "title": "Fly Culture Movement Graphic Tee - Inspire the Culture",
        "description": "100% cotton, premium quality tee. Unisex fit. Available in black, navy, white. Perfect for anyone passionate about cultural movement and inspired lifestyles. Features original artwork celebrating the journey of building culture.",
        "price": 2499,  # in cents
        "currency_code": "USD",
        "tags": ["culture", "graphic-tee", "mens", "womens", "unisex", "apparel", "movement", "inspiration"],
        "category_id": 68,  # Clothing > T-Shirts
        "quantity": 999,  # Unlimited via Printify
        "printify_sync": True
    },
    {
        "title": "Fly Culture Hoodie - Premium Comfort Wear",
        "description": "Ultra-soft, premium hoodie. Kangaroo pocket. Double-lined. Runs true to size. Perfect for those building in public and proud of the journey. Celebrate culture with comfortable, everyday wear.",
        "price": 5499,
        "currency_code": "USD",
        "tags": ["hoodie", "sweatshirt", "mens", "womens", "comfort", "culture", "apparel", "movement"],
        "category_id": 69,  # Clothing > Hoodies
        "quantity": 999,
        "printify_sync": True
    },
    {
        "title": "Fly Culture Movement Art Print - Inspirational Poster",
        "description": "High-quality art print (A3 size, 11x17\"). Unframed, poster quality. Perfect for offices, studios, creative spaces. Celebrates the journey of building. Inspire others with this original artwork.",
        "price": 1999,
        "currency_code": "USD",
        "tags": ["art", "print", "poster", "wall-art", "motivation", "inspiration", "culture", "design"],
        "category_id": 70,  # Home & Living > Wall Art
        "quantity": 999,
        "printify_sync": True
    },
    {
        "title": "Fly Culture Sticker Pack - 5 Designs, High Quality",
        "description": "5 high-quality vinyl stickers. Waterproof, weatherproof. Perfect for laptops, water bottles, car windows. Premium material. Show your culture pride everywhere you go.",
        "price": 799,
        "currency_code": "USD",
        "tags": ["stickers", "vinyl", "decals", "pack", "waterproof", "culture", "bundle", "designs"],
        "category_id": 71,  # Office & School > Stickers
        "quantity": 999,
        "printify_sync": True
    },
    {
        "title": "Fly Culture Coffee Mug - Daily Inspiration",
        "description": "11oz ceramic mug, microwave & dishwasher safe. Original artwork. Perfect coffee companion for morning inspiration. Great gift for anyone passionate about culture and building.",
        "price": 1299,
        "currency_code": "USD",
        "tags": ["mug", "coffee", "ceramic", "gift", "office", "culture", "drinkware", "inspiration"],
        "category_id": 72,  # Home & Kitchen > Tableware > Mugs
        "quantity": 999,
        "printify_sync": True
    },
    {
        "title": "Fly Culture Trucker Hat - Adjustable Snapback",
        "description": "Adjustable snapback, mesh back, breathable. Unisex fit. Perfect for outdoor activities, casual wear. Embroidered logo. Show your culture pride anywhere, anytime.",
        "price": 2699,
        "currency_code": "USD",
        "tags": ["hat", "trucker", "snapback", "cap", "unisex", "apparel", "culture", "mesh"],
        "category_id": 73,  # Clothing > Hats & Caps
        "quantity": 999,
        "printify_sync": True
    },
    {
        "title": "Fly Culture Tote Bag - Sustainable Cotton Carrier",
        "description": "100% cotton, large capacity. Natural canvas tote. Eco-friendly, sustainable, durable. Perfect for daily use. Carry your culture pride everywhere.",
        "price": 1899,
        "currency_code": "USD",
        "tags": ["tote", "bag", "canvas", "eco-friendly", "sustainable", "culture", "cotton", "reusable"],
        "category_id": 74,  # Bags & Purses > Tote Bags
        "quantity": 999,
        "printify_sync": True
    },
    {
        "title": "Fly Culture Crewneck Sweatshirt - Comfortable & Warm",
        "description": "Premium crewneck sweatshirt. Soft fleece lining, comfortable fit. Unisex sizing. Perfect for casual wear, comfort, and culture celebration. Wear your journey with pride.",
        "price": 3999,
        "currency_code": "USD",
        "tags": ["sweatshirt", "crewneck", "apparel", "mens", "womens", "culture", "comfort", "fleece"],
        "category_id": 69,  # Clothing > Hoodies & Sweatshirts
        "quantity": 999,
        "printify_sync": True
    }
]


def create_listing(product: Dict) -> bool:
    """Create a single listing on Etsy"""
    try:
        headers = {
            "Authorization": f"Bearer {ETSY_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "x-api-version": "v3"
        }

        payload = {
            "title": product["title"],
            "description": product["description"],
            "price": product["price"],
            "currency_code": product["currency_code"],
            "quantity": product["quantity"],
            "tags": product["tags"],
            "category_id": product["category_id"],
            "type": "physical",
            "state": "active"
        }

        url = f"{ETSY_API_URL}/{ETSY_SHOP_ID}/listings"
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            listing_id = response.json().get("data", {}).get("listing_id")
            print(f"✅ CREATED: {product['title']}")
            print(f"   Listing ID: {listing_id}")

            # If printify_sync enabled, connect to Printify
            if product.get("printify_sync"):
                print(f"   ℹ️  Will sync to Printify (requires manual setup)")

            return True
        else:
            print(f"❌ FAILED: {product['title']}")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ ERROR creating {product['title']}: {str(e)}")
        return False


def main():
    """Create all listings on Etsy"""
    print("=" * 60)
    print("ETSY PRODUCT UPLOADER")
    print("=" * 60)
    print("")

    if not ETSY_ACCESS_TOKEN:
        print("❌ ERROR: ETSY_ACCESS_TOKEN not set")
        print("   Set via: export ETSY_ACCESS_TOKEN='your-token'")
        return False

    if not ETSY_SHOP_ID:
        print("❌ ERROR: ETSY_SHOP_ID not set")
        print("   Set via: export ETSY_SHOP_ID='shop-id'")
        return False

    print(f"Creating {len(PRODUCTS)} listings on Etsy...")
    print(f"Shop ID: {ETSY_SHOP_ID}")
    print("")

    success_count = 0
    for product in PRODUCTS:
        if create_listing(product):
            success_count += 1

    print("")
    print("=" * 60)
    print(f"RESULT: {success_count}/{len(PRODUCTS)} listings created")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("1. Connect Printify to your Etsy shop")
    print("2. Products will auto-sync to Printify")
    print("3. Auto-fulfillment ready!")

    return success_count == len(PRODUCTS)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

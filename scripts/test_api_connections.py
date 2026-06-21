#!/usr/bin/env python3
"""
API Connection Test - Verify tokens work before running full automation
Tests: Gumroad, Etsy, Printify connections
"""

import requests
import os
import json
from typing import Dict, Tuple

def test_gumroad() -> Tuple[bool, str]:
    """Test Gumroad API connection"""
    token = os.getenv("GUMROAD_API_TOKEN")

    if not token:
        return False, "❌ GUMROAD_API_TOKEN not set"

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Test with simple request to get account info
        response = requests.get(
            "https://api.gumroad.com/v2/me",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            user_data = response.json().get("data", {})
            email = user_data.get("email", "unknown")
            return True, f"✅ GUMROAD: Connected as {email}"
        else:
            return False, f"❌ GUMROAD: Invalid token (status {response.status_code})"

    except Exception as e:
        return False, f"❌ GUMROAD: Connection failed ({str(e)})"


def test_etsy() -> Tuple[bool, str]:
    """Test Etsy API connection"""
    token = os.getenv("ETSY_ACCESS_TOKEN")
    shop_id = os.getenv("ETSY_SHOP_ID")

    if not token:
        return False, "❌ ETSY_ACCESS_TOKEN not set"
    if not shop_id:
        return False, "❌ ETSY_SHOP_ID not set"

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-version": "v3"
        }

        # Test with shop info request
        response = requests.get(
            f"https://openapi.etsy.com/v3/application/shops/{shop_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            shop_data = response.json().get("data", {})
            shop_name = shop_data.get("shop_name", "unknown")
            return True, f"✅ ETSY: Connected to shop '{shop_name}'"
        else:
            return False, f"❌ ETSY: Invalid credentials (status {response.status_code})"

    except Exception as e:
        return False, f"❌ ETSY: Connection failed ({str(e)})"


def test_printify() -> Tuple[bool, str]:
    """Test Printify API connection (optional)"""
    token = os.getenv("PRINTIFY_API_TOKEN")

    if not token:
        return True, "ℹ️  PRINTIFY: Token not set (optional)"

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Test with shops request
        response = requests.get(
            "https://api.printify.com/v1/shops",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            shops = response.json().get("data", [])
            shop_count = len(shops)
            return True, f"✅ PRINTIFY: Connected ({shop_count} shops found)"
        else:
            return False, f"❌ PRINTIFY: Invalid token (status {response.status_code})"

    except Exception as e:
        return False, f"❌ PRINTIFY: Connection failed ({str(e)})"


def main():
    """Run all API tests"""
    print("=" * 70)
    print("API CONNECTION TEST - Verify tokens and credentials")
    print("=" * 70)
    print()

    tests = [
        ("Gumroad", test_gumroad),
        ("Etsy", test_etsy),
        ("Printify", test_printify),
    ]

    results = []
    for name, test_func in tests:
        success, message = test_func()
        results.append((success, message))
        print(message)
        print()

    # Summary
    print("=" * 70)
    passed = sum(1 for success, _ in results if success)
    total = len(results)

    print(f"RESULT: {passed}/{total} API connections verified")
    print("=" * 70)
    print()

    if all(success for success, _ in results):
        print("✅ ALL TESTS PASSED - Ready to run product upload automation!")
        return True
    else:
        print("❌ SOME TESTS FAILED - Fix errors above before running automation:")
        print()
        for success, message in results:
            if not success:
                print(f"  {message}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

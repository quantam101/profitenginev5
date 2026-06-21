#!/usr/bin/env python3
"""Test Gumroad token and bootstrap catalog."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Check if token is set
token = os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip()
if token:
    print(f"[OK] GUMROAD_ACCESS_TOKEN loaded: {token[:20]}...")
else:
    print("[FAIL] GUMROAD_ACCESS_TOKEN not found")

# Import and test bootstrap
from runtime.gumroad_client import bootstrap_catalog, list_products

print("\n[TEST] Bootstrapping catalog...\n")
result = bootstrap_catalog()

print("Results:")
for r in result:
    name = r.get('name', '?')
    if r.get('ok') and not r.get('skipped'):
        status = f"CREATED (id: {r.get('id', '?')[:20]}...)"
    elif r.get('skipped'):
        status = f"EXISTS (id: {r.get('id', '?')[:20]}...)"
    else:
        status = f"ERROR: {r.get('error', 'unknown')}"
    print(f"  {name:40} {status}")

print("\n[CHECK] Current products on Gumroad:")
products = list_products()
print(f"Total: {len(products)} products\n")
for p in products:
    name = p.get('name', '?')
    price = p.get('price', 0) / 100
    url = p.get('short_url', p.get('url', '?'))
    print(f"  - {name} (${price:.2f})")
    print(f"    URL: {url}")

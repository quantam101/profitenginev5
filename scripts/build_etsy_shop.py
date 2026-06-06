"""Build the Etsy-ready POD shop pack for Already Here LLC."""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.eaos.image_factory import SKU_CATALOG, ProductionImageFactory

ROOT = Path(os.environ.get("EAOS_POD_ROOT", "./datacenter/pod_factory"))
PACK_DIR = ROOT / "etsy_shop_pack"
ART_DIR = ROOT / "render_cache"
SHOP_URLS = {
    "etsy": "https://www.etsy.com/shop/AlreadyHereLLC",
    "printify": "https://fly-culture-shop.printify.me",
    "shopify": "https://flydesignvault.com",
}


def _csv_tags(tags: list[str]) -> str:
    return ", ".join(tags[:13])


def _listing_rows() -> list[dict[str, str]]:
    rows = []
    for item in SKU_CATALOG:
        art_path = ART_DIR / f"{item['sku']}_artwork.png"
        rows.append({
            "sku": item["sku"],
            "title": item["etsy_title"],
            "description": item["description"],
            "price_usd": "29.99",
            "quantity": "999",
            "product_type": "physical",
            "who_made": "i_did",
            "when_made": "made_to_order",
            "taxonomy_hint": "T-shirts",
            "tags": _csv_tags(item["tags"]),
            "materials": "cotton, polyester, water based ink, direct to garment print",
            "image_file": str(art_path),
            "printify_shop": SHOP_URLS["printify"],
            "etsy_shop": SHOP_URLS["etsy"],
            "shopify_store": SHOP_URLS["shopify"],
        })
    return rows


def _write_shop_profile() -> None:
    profile = f"""# Already Here LLC Etsy Shop Pack

Generated: {datetime.now(UTC).isoformat()}

## Shop Positioning

Already Here LLC sells proof-first builder apparel for founders, creators, operators, AI builders, designers, and small business owners. The tone is direct, useful, and non-hype: receipts before claims, systems before noise, and finished work over endless planning.

## Public Store Links

- Etsy: {SHOP_URLS["etsy"]}
- Printify storefront: {SHOP_URLS["printify"]}
- Fly Design Vault: {SHOP_URLS["shopify"]}

## Shop Announcement

Proof-first builder apparel for founders, creators, operators, and AI builders. Made to order, designed around useful work, verified momentum, and systems that actually ship.

## About Section

Already Here LLC builds practical systems, design assets, and proof-first products for operators who care about finished work. This shop is the apparel side of that engine: clean statement pieces for founders, creators, AI builders, designers, and business owners who are building in public, testing ideas, and shipping.

## Customer Note

Thanks for supporting Already Here LLC. Each item is made to order, which helps avoid waste and keeps the shop lean. Check sizing before ordering, and reach out if anything arrives damaged or incorrect.

## Shipping Policy

Items are made to order through a production partner. Processing and shipping times vary by product and destination. Tracking is provided when available.

## Return Policy

Because items are made to order, returns and exchanges are not accepted for size preference or buyer remorse. If an item arrives damaged, misprinted, or incorrect, contact the shop with photos so it can be reviewed and corrected.

## Manual Launch Checklist

1. Confirm Printify store is connected to Etsy.
2. Push products from Printify or create Etsy listings using `etsy_listings.csv`.
3. Set production partner as Printify in Etsy listing settings.
4. Check titles, tags, pricing, shipping profiles, and mockups.
5. Publish the first 8 listings.
6. Add store links to Already Here social/content CTAs.
"""
    (PACK_DIR / "shop_profile.md").write_text(profile, encoding="utf-8")


def build() -> None:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    ProductionImageFactory(str(ROOT)).render_full_catalog()
    rows = _listing_rows()

    (PACK_DIR / "etsy_listings.json").write_text(
        json.dumps({"generated_at": datetime.now(UTC).isoformat(), "items": rows}, indent=2),
        encoding="utf-8",
    )
    with (PACK_DIR / "etsy_listings.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    _write_shop_profile()

    print(f"Built Etsy shop pack: {PACK_DIR.resolve()}")
    print(f"Rendered artwork: {ART_DIR.resolve()}")
    print(f"Listings: {len(rows)}")


if __name__ == "__main__":
    build()

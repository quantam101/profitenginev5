#!/usr/bin/env python3
"""List one generated technical product on Gumroad (idempotent).

Usage: python scripts/list_product_on_gumroad.py <product-dir>

Reads <dir>/product.json + checkout.json, calls gumroad_client.create_product,
and writes the returned short_url/product_id back into checkout.json so the
newsletter composer can feature the live listing. Skips quietly when
GUMROAD_ACCESS_TOKEN is unset or a listing_url already exists.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.gumroad_client import create_product  # noqa: E402


def main() -> int:
    product_dir = Path(sys.argv[1])
    checkout_path = product_dir / "checkout.json"
    manifest_path = product_dir / "product.json"
    if not checkout_path.exists() or not manifest_path.exists():
        print(f"{product_dir.name}: missing manifests — skipped")
        return 0

    checkout = json.loads(checkout_path.read_text())
    if checkout.get("listing_url"):
        print(f"{product_dir.name}: already listed at {checkout['listing_url']}")
        return 0

    manifest = json.loads(manifest_path.read_text())
    strategy = manifest.get("strategy") or {}
    title = str(checkout.get("title") or strategy.get("title") or product_dir.name)
    price_cents = int(round(float(checkout.get("price_usd") or 19) * 100))
    description = str(
        strategy.get("storefront_copy") or strategy.get("seo_description") or title
    )

    result = create_product({
        "name": title,
        "price": price_cents,
        "description": description,
        "url_suffix": str(checkout.get("sku") or product_dir.name),
        "tags": ["automation", "operations", "it-teams"],
    })
    if not result.get("ok"):
        print(f"{product_dir.name}: listing failed — {result.get('error', 'unknown')}")
        return 1

    checkout["listing_url"] = result.get("short_url") or ""
    checkout["gumroad_product_id"] = result.get("id") or ""
    checkout["published"] = bool(result.get("published"))
    if result.get("manual_step"):
        checkout["manual_step"] = result["manual_step"]
    else:
        checkout.pop("manual_step", None)
    checkout_path.write_text(json.dumps(checkout, indent=2) + "\n")
    if checkout["published"]:
        print(f"{product_dir.name}: listed LIVE → {checkout['listing_url'] or 'id ' + str(result.get('id'))}")
    else:
        print(f"{product_dir.name}: created but still DRAFT — {checkout.get('manual_step', 'publish manually')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

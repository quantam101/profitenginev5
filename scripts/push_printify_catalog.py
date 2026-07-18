from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.eaos.image_factory import SKU_CATALOG
from runtime.eaos.printify_client import _request_json, _resolve_shop_id, push_product


async def _run() -> int:
    token = os.getenv("PRINTIFY_API_TOKEN", "").strip()
    shop_id = os.getenv("PRINTIFY_SHOP_ID", "").strip()

    if not token or not shop_id:
        print("[Printify] ERROR: PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID are required")
        return 1

    pod_root = os.getenv("EAOS_POD_ROOT", "./datacenter/pod_factory")
    render_dir = Path(pod_root) / "render_cache"
    target_sku = os.getenv("TARGET_SKU", "").strip()
    catalog = [item for item in SKU_CATALOG if not target_sku or item["sku"] == target_sku]

    if target_sku and not catalog:
        print(f"[Printify] ERROR: target SKU {target_sku!r} was not found in SKU_CATALOG")
        return 1

    # dedupe against what's already live — the weekly cron should be a
    # cheap no-op once the catalog is published, not a 50MB re-upload
    shop_id = _resolve_shop_id(shop_id, token)
    existing_titles: set[str] = set()
    try:
        listing = _request_json(f"/shops/{shop_id}/products.json?limit=50", token)
        rows = listing.get("data", []) if isinstance(listing, dict) else []
        existing_titles = {str(p.get("title", "")).strip().lower() for p in rows}
        print(f"[Printify] shop {shop_id} has {len(rows)} existing products")
    except Exception as exc:
        print(f"[Printify] listing failed ({exc}) - pushing without dedupe")

    pushed = 0
    skipped = 0
    for item in catalog:
        live_title = str(item.get("etsy_title") or item.get("title") or "").strip().lower()
        if live_title and live_title in existing_titles:
            skipped += 1
            print(f"[Printify] {item['sku']} already live, skipping")
            continue
        img_path = render_dir / f"{item['sku']}_artwork.png"
        if not img_path.exists():
            print(f"[Printify] {item['sku']} - artwork not found at {img_path}, skipping")
            continue
        ok = await push_product(
            file_path=str(img_path),
            meta={
                "sku": item["sku"],
                "title": item["title"],
                "subtitle": item["subtitle"],
                "etsy_title": item.get("etsy_title"),
                "description": item.get("description"),
                "tags": item.get("tags", []),
                "product_type": item.get("product_type", "unisex_tee"),
                "shop_id": shop_id,
            },
            token=token,
        )
        if ok:
            pushed += 1
            print(f"[Printify] {item['sku']} pushed")
        else:
            print(f"[Printify] {item['sku']} push failed")

    print(f"Done: {pushed} pushed, {skipped} already live, of {len(catalog)} catalog items")
    if pushed + skipped != len(catalog):
        print(f"[Printify] ERROR: {len(catalog) - pushed - skipped} item(s) neither live nor pushed")
        return 1
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())

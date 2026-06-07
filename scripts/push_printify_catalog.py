from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.eaos.image_factory import SKU_CATALOG
from runtime.eaos.printify_client import push_product


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

    pushed = 0
    for item in catalog:
        img_path = render_dir / f"{item['sku']}_artwork.png"
        if not img_path.exists():
            print(f"[Printify] {item['sku']} - artwork not found, skipping")
            continue
        ok = await push_product(
            file_path=str(img_path),
            meta={
                "title": item["title"],
                "subtitle": item["subtitle"],
                "etsy_title": item.get("etsy_title"),
                "description": item.get("description"),
                "tags": item.get("tags", []),
                "product_type": "unisex_tee",
                "shop_id": shop_id,
            },
            token=token,
        )
        if ok:
            pushed += 1
            print(f"[Printify] {item['sku']} pushed")
        else:
            print(f"[Printify] {item['sku']} push failed")

    print(f"Done: {pushed}/{len(catalog)} products pushed to Printify")
    if pushed != len(catalog):
        print(f"[Printify] ERROR: expected {len(catalog)} pushes, got {pushed}")
        return 1
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())

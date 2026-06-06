#!/usr/bin/env python3
"""
EAOS Printify push script — pushes rendered SKUs to Printify as live products.
Run by eaos-pod-render.yml GitHub Actions workflow.
"""
from __future__ import annotations
import asyncio, os, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

token   = os.getenv("PRINTIFY_API_TOKEN", "").strip()
shop_id = os.getenv("PRINTIFY_SHOP_ID", "").strip()

if not token or not shop_id:
    print("[Printify] PRINTIFY_API_TOKEN or PRINTIFY_SHOP_ID not set — skipping push")
    sys.exit(0)

from runtime.eaos.printify_client import push_product
from runtime.eaos.image_factory import SKU_CATALOG

pod_root   = os.getenv("EAOS_POD_ROOT", "./datacenter/pod_factory")
render_dir = os.path.join(pod_root, "render_cache")
target_sku = os.getenv("TARGET_SKU", "").strip()
catalog    = [i for i in SKU_CATALOG if not target_sku or i["sku"] == target_sku]


async def run() -> None:
    pushed = 0
    for item in catalog:
        img_path = os.path.join(render_dir, f"{item['sku']}_artwork.png")
        if not os.path.exists(img_path):
            print(f"[Printify] {item['sku']} — artwork not found, skipping")
            continue
        ok = await push_product(
            file_path=img_path,
            meta={"title": item["title"], "subtitle": item["subtitle"],
                  "product_type": "unisex_tee", "shop_id": shop_id},
            token=token,
        )
        status = "pushed ✓" if ok else "FAILED"
        print(f"[Printify] {item['sku']} {status}")
        if ok:
            pushed += 1
    print(f"\nDone: {pushed}/{len(catalog)} products pushed to Printify")


asyncio.run(run())

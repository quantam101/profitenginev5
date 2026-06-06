#!/usr/bin/env python3
"""
EAOS POD render script — renders all 8 SKUs or a specific one.
Run by eaos-pod-render.yml GitHub Actions workflow.
"""
from __future__ import annotations
import os, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from runtime.eaos.image_factory import ProductionImageFactory, SKU_CATALOG

factory = ProductionImageFactory()
target = os.getenv("TARGET_SKU", "").strip()

if target:
    item = next((i for i in SKU_CATALOG if i["sku"] == target), None)
    if not item:
        print(f"SKU {target} not found in catalog")
        sys.exit(1)
    path = factory.construct_apparel_artwork(
        item["sku"], item["title"], item["subtitle"], item["palette"]
    )
    print(f"Rendered: {path}")
else:
    paths = factory.render_full_catalog()
    print(f"Rendered {len(paths)}/{len(SKU_CATALOG)} SKUs")
    for p in paths:
        print(f"  {p}")

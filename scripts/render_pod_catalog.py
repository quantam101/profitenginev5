from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.eaos.image_factory import ProductionImageFactory, SKU_CATALOG


def main() -> int:
    factory = ProductionImageFactory()
    target = os.getenv("TARGET_SKU", "").strip()

    if target:
        item = next((row for row in SKU_CATALOG if row["sku"] == target), None)
        if not item:
            print(f"SKU {target} not found")
            return 1
        path = factory.construct_apparel_artwork(item["sku"], item["title"], item["subtitle"], item["palette"])
        print(f"Rendered: {path}")
        return 0

    paths = factory.render_full_catalog()
    print(f"Rendered {len(paths)} SKUs")
    for path in paths:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

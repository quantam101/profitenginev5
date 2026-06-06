from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

PRINTIFY_API = "https://api.printify.com/v1"


@dataclass(frozen=True)
class PrintifyConfig:
    token: str
    shop_id: str


def _request(path: str, config: PrintifyConfig) -> dict[str, Any] | list[dict[str, Any]]:
    req = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
        f"{PRINTIFY_API}{path}",
        headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed Printify HTTPS API endpoint
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Printify API HTTP {exc.code}: {detail[:500]}") from exc


def _config_from_env() -> PrintifyConfig:
    token = os.getenv("PRINTIFY_API_TOKEN", "").strip()
    shop_id = os.getenv("PRINTIFY_SHOP_ID", "").strip()
    if not token or not shop_id:
        raise RuntimeError("PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID are required")
    return PrintifyConfig(token=token, shop_id=shop_id)


def fetch_status(config: PrintifyConfig) -> dict[str, Any]:
    shops = _request("/shops.json", config)
    if not isinstance(shops, list):
        raise RuntimeError("Unexpected Printify shops response")
    shop = next((item for item in shops if str(item.get("id")) == config.shop_id), None)
    if not shop:
        raise RuntimeError(f"PRINTIFY_SHOP_ID {config.shop_id} was not found in this Printify account")

    products = _request(f"/shops/{config.shop_id}/products.json?limit=100", config)
    product_rows = products.get("data", []) if isinstance(products, dict) else []
    published = [
        product for product in product_rows
        if product.get("visible") is True or product.get("is_locked") is False
    ]
    platform = str(shop.get("sales_channel") or shop.get("platform") or "").lower()
    disconnected = platform in {"", "disconnected", "none", "null"}
    return {
        "ok": True,
        "shop": {
            "id": shop.get("id"),
            "title": shop.get("title") or shop.get("name"),
            "sales_channel": shop.get("sales_channel") or shop.get("platform") or "unknown",
            "disconnected": disconnected,
        },
        "products": {
            "total": len(product_rows),
            "published_or_visible": len(published),
            "sample_titles": [str(product.get("title", ""))[:100] for product in product_rows[:5]],
        },
        "etsy_expected_shop": "https://www.etsy.com/shop/AlreadyHereLLC",
        "next_action": (
            "Connect this Printify shop to Etsy, then rerun EAOS POD Render & Printify Push."
            if disconnected
            else "Printify shop is connected; rerun push if Etsy listings are still missing."
        ),
    }


def main() -> int:
    try:
        status = fetch_status(_config_from_env())
        print(json.dumps(status, indent=2))
        if status["shop"]["disconnected"]:
            print("::error::Printify shop is disconnected from a sales channel. Connect Etsy in Printify before publishing.", file=sys.stderr)
            return 2
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

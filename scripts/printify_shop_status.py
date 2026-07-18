from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

PRINTIFY_API = "https://api.printify.com/v1"
REQUIRED_PUBLISH_SCOPES = {"shops.read", "products.read", "products.write", "uploads.write"}
USER_AGENT = "ProfitEngine/5.0"


@dataclass(frozen=True)
class PrintifyConfig:
    token: str
    shop_id: str


def _request(path: str, config: PrintifyConfig) -> dict[str, Any] | list[dict[str, Any]]:
    req = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
        f"{PRINTIFY_API}{path}",
        headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed Printify HTTPS API endpoint
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Printify API HTTP {exc.code}: {detail[:500]}") from exc


def verify_upload_permission(config: PrintifyConfig) -> dict[str, Any]:
    body = json.dumps({
        "file_name": "profitengine-permission-check.png",
        "contents": (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
            "AAAADUlEQVR42mP8z8BQDwAFgwJ/lM2GAAAAAABJRU5ErkJggg=="
        ),
    }).encode()
    req = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
        f"{PRINTIFY_API}/uploads/images.json",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "upload_id": data.get("id", "")}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "error": detail[:500],
            "next_action": "Regenerate PRINTIFY_API_TOKEN with uploads.write scope and update the GitHub Actions secret.",
        }


def _config_from_env() -> PrintifyConfig:
    token = os.getenv("PRINTIFY_API_TOKEN", "").strip()
    shop_id = os.getenv("PRINTIFY_SHOP_ID", "").strip()
    if not token or not shop_id:
        raise RuntimeError("PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID are required")
    return PrintifyConfig(token=token, shop_id=shop_id)


def token_scopes(token: str) -> set[str]:
    parts = token.split(".")
    if len(parts) < 2:
        return set()
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        decoded = json.loads(base64.urlsafe_b64decode(payload.encode()).decode("utf-8"))
    except Exception:
        return set()
    scopes = decoded.get("scopes") or decoded.get("scope") or []
    if isinstance(scopes, str):
        return set(scopes.split())
    if isinstance(scopes, list):
        return {str(scope) for scope in scopes}
    return set()


def fetch_status(config: PrintifyConfig) -> dict[str, Any]:
    scopes = token_scopes(config.token)
    missing_scopes = sorted(REQUIRED_PUBLISH_SCOPES - scopes) if scopes else []
    shops = _request("/shops.json", config)
    if not isinstance(shops, list):
        raise RuntimeError("Unexpected Printify shops response")
    shop = next((item for item in shops if str(item.get("id")) == config.shop_id), None)
    resolved_note = None
    if not shop:
        available = [{"id": item.get("id"), "title": item.get("title") or item.get("name")} for item in shops]
        if not shops:
            raise RuntimeError(
                f"PRINTIFY_SHOP_ID {config.shop_id} not found and the account has no shops")
        # auto-heal: configured id is stale (e.g. a slug, or pre-migration
        # value) — fall back to the account's first shop and say so
        shop = shops[0]
        config = PrintifyConfig(token=config.token, shop_id=str(shop.get("id")))
        resolved_note = (
            f"configured PRINTIFY_SHOP_ID was not found; auto-resolved to "
            f"{shop.get('id')} ({shop.get('title') or shop.get('name')}). "
            f"Available shops: {available}. Update the PRINTIFY_SHOP_ID secret "
            f"to silence this note.")

    # Printify API rejects limit>50 (error 8150) since 2026
    products = _request(f"/shops/{config.shop_id}/products.json?limit=50", config)
    product_rows = products.get("data", []) if isinstance(products, dict) else []
    published = [
        product for product in product_rows
        if product.get("visible") is True or product.get("is_locked") is False
    ]
    platform = str(shop.get("sales_channel") or shop.get("platform") or "").lower()
    disconnected = platform in {"", "disconnected", "none", "null"}
    return {
        "ok": True,
        "shop_id_note": resolved_note,
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
        "token": {
            "scopes_decoded": sorted(scopes),
            "required_for_publish": sorted(REQUIRED_PUBLISH_SCOPES),
            "missing_for_publish": missing_scopes,
        },
        "etsy_expected_shop": "https://www.etsy.com/shop/AlreadyHereLLC",
        "next_action": (
            "Connect this Printify shop to Etsy, then rerun EAOS POD Render & Printify Push."
            if disconnected
            else "Create a new Printify token with uploads.write and products.write, then update PRINTIFY_API_TOKEN."
            if missing_scopes
            else "Printify shop is connected; rerun push if Etsy listings are still missing."
        ),
    }


def main() -> int:
    try:
        config = _config_from_env()
        status = fetch_status(config)
        if os.getenv("PRINTIFY_VERIFY_UPLOAD", "false").lower() == "true":
            status["upload_permission"] = verify_upload_permission(config)
        print(json.dumps(status, indent=2))
        if status["shop"]["disconnected"]:
            print("::error::Printify shop is disconnected from a sales channel. Connect Etsy in Printify before publishing.", file=sys.stderr)
            return 2
        if status["token"]["missing_for_publish"]:
            print(
                "::error::Printify token is missing required publish scopes: "
                + ", ".join(status["token"]["missing_for_publish"]),
                file=sys.stderr,
            )
            return 3
        if status.get("upload_permission", {}).get("ok") is False:
            print(
                "::error::Printify token cannot upload images. Regenerate PRINTIFY_API_TOKEN with uploads.write scope.",
                file=sys.stderr,
            )
            return 4
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

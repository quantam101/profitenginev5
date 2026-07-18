"""EAOS Printify client - push rendered POD artwork to Printify."""
from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger("EAOS.Printify")
logging.basicConfig(level=os.getenv("EAOS_LOG_LEVEL", "INFO"))

PRINTIFY_API = "https://api.printify.com/v1"
USER_AGENT = "ProfitEngine/5.0"

DEFAULT_VARIANT_IDS = [17887, 17888, 17889, 17890, 17891]

# Blueprint IDs (Printify catalog). Provider and variant IDs can change by account/region,
# so runtime catalog lookup is used before this fallback is applied.
BLUEPRINTS = {
    "unisex_tee": {"blueprint_id": 6, "print_provider_id": int(os.getenv("PRINTIFY_TEE_PROVIDER_ID", "99"))},
    "premium_tee": {"blueprint_id": 145, "print_provider_id": int(os.getenv("PRINTIFY_PREMIUM_TEE_PROVIDER_ID", "99"))},
    "hoodie": {"blueprint_id": 77, "print_provider_id": int(os.getenv("PRINTIFY_HOODIE_PROVIDER_ID", "99"))},
    "poster_18x24": {"blueprint_id": 527, "print_provider_id": int(os.getenv("PRINTIFY_POSTER_PROVIDER_ID", "99"))},
    "mug_11oz": {"blueprint_id": 560, "print_provider_id": int(os.getenv("PRINTIFY_MUG_PROVIDER_ID", "99"))},
}


def _request_json(path: str, token: str, *, method: str = "GET", payload: Optional[dict[str, Any]] = None, timeout: int = 30) -> dict[str, Any] | list[dict[str, Any]]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
        f"{PRINTIFY_API}{path}",
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Printify API HTTP {exc.code} on {method} {path}: {detail[:800]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Printify API network error on {method} {path}: {exc}") from exc


def _upload_image(file_path: str, token: str) -> Optional[str]:
    """Upload PNG to Printify image library, return image_id."""
    with open(file_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    payload = {
        "file_name": os.path.basename(file_path),
        "contents": img_b64,
    }
    try:
        resp = _request_json("/uploads/images.json", token, method="POST", payload=payload, timeout=60)
        if not isinstance(resp, dict):
            raise RuntimeError(f"Unexpected upload response type: {type(resp).__name__}")
        img_id = str(resp.get("id", "")).strip()
        if not img_id:
            raise RuntimeError(f"Printify upload response did not include an image id: {str(resp)[:500]}")
        logger.info("[Printify] Image uploaded: id=%s", img_id)
        return img_id
    except Exception as exc:
        logger.error("[Printify] Image upload failed for %s: %s", file_path, exc)
        return None


def _catalog_variant_ids(token: str, blueprint: Dict[str, int]) -> list[int]:
    override = os.getenv("PRINTIFY_VARIANT_IDS", "").strip()
    if override:
        ids = [int(item.strip()) for item in override.split(",") if item.strip()]
        if ids:
            return ids

    blueprint_id = blueprint["blueprint_id"]
    provider_id = blueprint["print_provider_id"]
    try:
        data = _request_json(
            f"/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json",
            token,
            timeout=30,
        )
        variants = data.get("variants", []) if isinstance(data, dict) else []
        enabled = [int(item["id"]) for item in variants if item.get("id") and item.get("is_enabled", True)]
        if enabled:
            logger.info("[Printify] Using %s catalog variants for blueprint=%s provider=%s", len(enabled), blueprint_id, provider_id)
            return enabled[:5]
    except Exception as exc:
        logger.warning("[Printify] Catalog variant lookup failed; using fallback variants: %s", exc)
    return DEFAULT_VARIANT_IDS


def _build_product_payload(
    title: str,
    description: str,
    img_id: str,
    blueprint: Dict[str, int],
    token: str,
    tags: Optional[list[str]] = None,
) -> Dict[str, Any]:
    variant_ids = _catalog_variant_ids(token, blueprint)
    price_cents = int(os.getenv("PRINTIFY_PRICE_CENTS", "2999"))
    return {
        "title": title[:255],
        "description": description,
        "tags": (tags or [])[:13],
        "blueprint_id": blueprint["blueprint_id"],
        "print_provider_id": blueprint["print_provider_id"],
        "variants": [
            {"id": variant_id, "price": price_cents, "is_enabled": True}
            for variant_id in variant_ids
        ],
        "print_areas": [
            {
                "variant_ids": variant_ids,
                "placeholders": [
                    {
                        "position": "front",
                        "images": [
                            {"id": img_id, "x": 0.5, "y": 0.5, "scale": 1.0, "angle": 0}
                        ],
                    }
                ],
            }
        ],
    }


def _resolve_shop_id(shop_id: str, token: str) -> str:
    """Validate shop_id against the account; fall back to the first shop
    when the configured value is stale (auto-heals slug/pre-migration ids)."""
    try:
        shops = _request_json("/shops.json", token)
    except Exception as exc:
        logger.warning("[Printify] shop listing failed (%s) - using configured id", exc)
        return shop_id
    if not isinstance(shops, list) or not shops:
        return shop_id
    if any(str(s.get("id")) == shop_id for s in shops):
        return shop_id
    resolved = str(shops[0].get("id", "")).strip()
    logger.warning("[Printify] configured shop id %r not in account - using %s (%s)",
                   shop_id, resolved, shops[0].get("title"))
    return resolved or shop_id


async def push_product(file_path: str, meta: Dict[str, Any], token: str) -> bool:
    shop_id = os.environ.get("PRINTIFY_SHOP_ID", "").strip() or str(meta.get("shop_id", "")).strip()
    if not shop_id:
        logger.error("[Printify] PRINTIFY_SHOP_ID not set - cannot push product")
        return False
    shop_id = _resolve_shop_id(shop_id, token)

    img_id = _upload_image(file_path, token)
    if not img_id:
        return False

    blueprint_key = str(meta.get("product_type", "unisex_tee"))
    blueprint = BLUEPRINTS.get(blueprint_key, BLUEPRINTS["unisex_tee"])
    title = str(meta.get("etsy_title") or meta.get("title") or "Already Here LLC")
    description = str(meta.get("description") or meta.get("subtitle") or "Proof-first builder apparel")
    tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    payload = _build_product_payload(title, description, img_id, blueprint, token, tags)

    try:
        resp = _request_json(
            f"/shops/{shop_id}/products.json",
            token,
            method="POST",
            payload=payload,
            timeout=45,
        )
        if not isinstance(resp, dict):
            raise RuntimeError(f"Unexpected product response type: {type(resp).__name__}")
        product_id = str(resp.get("id", "")).strip()
        if not product_id:
            raise RuntimeError(f"Printify product create response did not include a product id: {str(resp)[:800]}")
        logger.info("[Printify] Product created: id=%s title=%r", product_id, title)

        publish_payload = {"title": True, "description": True, "images": True, "variants": True, "tags": True}
        _request_json(
            f"/shops/{shop_id}/products/{product_id}/publish.json",
            token,
            method="POST",
            payload=publish_payload,
            timeout=30,
        )
        logger.info("[Printify] Product %s published to store", product_id)
        return True
    except Exception as exc:
        logger.error("[Printify] Product push failed for %s: %s", meta.get("sku") or title, exc)
        return False

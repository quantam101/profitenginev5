"""EAOS Printify client - push rendered POD artwork to Printify."""
import os
import json
import base64
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger("EAOS.Printify")

PRINTIFY_API = "https://api.printify.com/v1"
SHOP_ID      = os.environ.get("PRINTIFY_SHOP_ID", "")

# Blueprint IDs (Printify standard)
BLUEPRINTS = {
    "unisex_tee":     {"blueprint_id": 6,   "print_provider_id": 99},  # Bella+Canvas 3001
    "premium_tee":    {"blueprint_id": 145,  "print_provider_id": 99},
    "hoodie":         {"blueprint_id": 77,   "print_provider_id": 99},
    "poster_18x24":   {"blueprint_id": 527,  "print_provider_id": 99},
    "mug_11oz":       {"blueprint_id": 560,  "print_provider_id": 99},
}


def _upload_image(file_path: str, token: str) -> Optional[str]:
    """Upload PNG to Printify image library, return image_id."""
    with open(file_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "file_name": os.path.basename(file_path),
        "contents":  img_b64,
    }).encode()
    try:
        req = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
            f"{PRINTIFY_API}/uploads/images.json",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())  # noqa: S310
        img_id = resp.get("id", "")
        logger.info(f"[Printify] Image uploaded: id={img_id}")
        return img_id
    except Exception as exc:
        logger.error(f"[Printify] Image upload failed: {exc}")
        return None


def _build_product_payload(title: str, description: str, img_id: str,
                            blueprint: Dict, tags: Optional[list[str]] = None) -> Dict[str, Any]:
    return {
        "title":       title,
        "description": description,
        "tags": tags or [],
        "blueprint_id":       blueprint["blueprint_id"],
        "print_provider_id":  blueprint["print_provider_id"],
        "variants": [
            {"id": 17887, "price": 2999, "is_enabled": True},  # S
            {"id": 17888, "price": 2999, "is_enabled": True},  # M
            {"id": 17889, "price": 2999, "is_enabled": True},  # L
            {"id": 17890, "price": 2999, "is_enabled": True},  # XL
            {"id": 17891, "price": 3199, "is_enabled": True},  # 2XL
        ],
        "print_areas": [{
            "variant_ids": [17887, 17888, 17889, 17890, 17891],
            "placeholders": [{"position": "front", "images": [
                {"id": img_id, "x": 0.5, "y": 0.5, "scale": 1.0, "angle": 0}
            ]}],
        }],
    }


async def push_product(file_path: str, meta: Dict[str, Any], token: str) -> bool:
    shop_id = SHOP_ID or meta.get("shop_id", "")
    if not shop_id:
        logger.warning("[Printify] PRINTIFY_SHOP_ID not set - skipping push")
        return False

    img_id = _upload_image(file_path, token)
    if not img_id:
        return False

    blueprint_key = meta.get("product_type", "unisex_tee")
    blueprint     = BLUEPRINTS.get(blueprint_key, BLUEPRINTS["unisex_tee"])
    title         = meta.get("etsy_title") or meta.get("title", "Already Here LLC")
    description   = meta.get("description") or meta.get("subtitle", "Proof-first builder apparel")
    tags          = meta.get("tags") or []
    payload       = _build_product_payload(title, description, img_id, blueprint, tags)

    try:
        body = json.dumps(payload).encode()
        req  = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
            f"{PRINTIFY_API}/shops/{shop_id}/products.json",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())  # noqa: S310
        product_id = resp.get("id", "")
        logger.info(f"[Printify] Product created: id={product_id} title='{title}'")
        # Publish immediately
        pub_req = urllib.request.Request(  # noqa: S310 - fixed Printify HTTPS API endpoint
            f"{PRINTIFY_API}/shops/{shop_id}/products/{product_id}/publish.json",
            data=json.dumps({"title": True, "description": True, "images": True,
                              "variants": True, "tags": True}).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        urllib.request.urlopen(pub_req, timeout=15)  # noqa: S310
        logger.info(f"[Printify] Product {product_id} published to store")
        return True
    except Exception as exc:
        logger.error(f"[Printify] Product push failed: {exc}")
        return False

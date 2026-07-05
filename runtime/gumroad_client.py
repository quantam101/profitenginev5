"""
Gumroad Digital Products Client — Income Stream 3
==================================================
Creates, prices, and tracks AI-generated digital products on Gumroad.
Fulfillment is 100% automated by Gumroad — zero marginal cost per sale.

Product catalog (auto-created on first run):
  1. AI Business Prompt Pack (500+ production prompts)     $27
  2. Real Estate Copywriting Kit (100 property templates)  $19
  3. Social Media Content Engine (30-day prompt calendar)  $17
  4. POD Design Prompt Bundle (AI art generation system)   $22
  5. Programmatic SEO Starter Kit (city-page templates)    $29

Revenue model:
  Gumroad takes 10% + $0.50/sale (free plan) or flat 10% (Pro $10/mo)
  Net margin: ~88% on every sale — no inventory, no shipping

Environment variables:
  GUMROAD_ACCESS_TOKEN   — from https://app.gumroad.com/settings/advanced → Access token

API reference: https://app.gumroad.com/api
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("GumroadClient")

_BASE = "https://api.gumroad.com/v2"

# ── Product catalog ────────────────────────────────────────────────────────────

PRODUCT_CATALOG: List[Dict[str, Any]] = [
    {
        "name":        "AI Business Prompt Pack",
        "price":       2700,           # cents ($27.00)
        "description": (
            "500+ production-tested AI prompts covering copywriting, sales emails, "
            "social media, product descriptions, and cold outreach. Built for "
            "entrepreneurs who want ChatGPT/Claude to do the heavy lifting. "
            "Instant download. No fluff — only prompts that convert."
        ),
        "tags":        ["ai", "prompts", "business", "automation", "chatgpt"],
        "url_suffix":  "ai-business-prompt-pack",
    },
    {
        "name":        "Real Estate Copywriting Kit",
        "price":       1900,
        "description": (
            "100 plug-and-play property listing templates for agents and investors. "
            "Luxury, starter, commercial, vacation rental, and land listings. "
            "Each template includes headline, full description, and social caption. "
            "Drop in your details and publish in under 5 minutes."
        ),
        "tags":        ["real-estate", "copywriting", "templates", "ai", "listings"],
        "url_suffix":  "real-estate-copywriting-kit",
    },
    {
        "name":        "Social Media Content Engine",
        "price":       1700,
        "description": (
            "30-day AI content calendar with 180 ready-to-use prompts for "
            "Instagram, TikTok, LinkedIn, X/Twitter, and Facebook. "
            "Includes hook formulas, caption templates, hashtag banks, and "
            "a Notion dashboard to track engagement. Never run out of content ideas."
        ),
        "tags":        ["social-media", "content", "marketing", "ai", "calendar"],
        "url_suffix":  "social-media-content-engine",
    },
    {
        "name":        "POD Design Prompt Bundle",
        "price":       2200,
        "description": (
            "Complete AI art generation system for print-on-demand sellers. "
            "Includes Midjourney + Stable Diffusion prompts for 20 profitable niches, "
            "color palette guides, mockup instructions, and Etsy SEO keyword lists. "
            "Turn AI images into bestselling t-shirts, mugs, and wall art."
        ),
        "tags":        ["print-on-demand", "ai-art", "etsy", "design", "prompts"],
        "url_suffix":  "pod-design-prompt-bundle",
    },
    {
        "name":        "Programmatic SEO Starter Kit",
        "price":       2900,
        "description": (
            "City-page SEO templates that rank. Includes HTML/Markdown templates "
            "for 10 service niches, keyword research spreadsheet for 500 US cities, "
            "schema markup snippets, internal linking strategy, and a step-by-step "
            "GitHub Pages deployment guide. Generate thousands of pages with AI."
        ),
        "tags":        ["seo", "programmatic", "templates", "blogging", "ai"],
        "url_suffix":  "programmatic-seo-starter-kit",
    },
]


# ── Auth ───────────────────────────────────────────────────────────────────────

def _token() -> str:
    return os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip()


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _request(method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    token = _token()
    if not token:
        return {"success": False, "message": "GUMROAD_ACCESS_TOKEN not set"}

    url  = f"{_BASE}/{path}"
    payload = urllib.parse.urlencode({**(data or {}), "access_token": token}, doseq=True)

    if method == "GET":
        sep = "&" if "?" in url else "?"
        req = urllib.request.Request(f"{url}{sep}{payload}", method="GET")
    else:
        req = urllib.request.Request(
            url,
            data  = payload.encode(),
            method = method,
            headers = {"Content-Type": "application/x-www-form-urlencoded"},
        )

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        body_err = exc.read().decode(errors="replace")[:300]
        logger.error(f"[Gumroad] {method} {path} → HTTP {exc.code}: {body_err}")
        return {"success": False, "message": f"HTTP {exc.code}: {body_err}"}
    except Exception as exc:
        logger.error(f"[Gumroad] {method} {path} error: {exc}")
        return {"success": False, "message": str(exc)}


# ── Product management ─────────────────────────────────────────────────────────

def list_products() -> List[Dict[str, Any]]:
    resp = _request("GET", "products")
    return resp.get("products", []) if resp.get("success") else []


def _product_exists(name: str) -> Optional[str]:
    """Return product_id if a product with this name already exists."""
    for p in list_products():
        if p.get("name", "").strip().lower() == name.strip().lower():
            return p.get("id")
    return None


def create_product(catalog_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Idempotently create a Gumroad product.
    Skips creation if a product with the same name already exists.
    Returns the product dict (including id and short_url).
    """
    name = catalog_entry["name"]
    existing_id = _product_exists(name)
    if existing_id:
        logger.info(f"[Gumroad] Product already exists: {name} ({existing_id})")
        return {"ok": True, "id": existing_id, "skipped": True, "name": name}

    data = {
        "name":            name,
        "price":           catalog_entry["price"],
        "description":     catalog_entry["description"],
        "published":       "true",
        "require_shipping": "false",
        "type":            "digital",
        "url":             catalog_entry.get("url_suffix", ""),
        "tags[]":          catalog_entry.get("tags", []),
    }
    resp = _request("POST", "products", data)
    if resp.get("success"):
        product = resp.get("product", {})
        pid     = product.get("id", "")
        url     = product.get("short_url", "")
        logger.info(f"[Gumroad] Created: {name} → id={pid} url={url}")
        return {"ok": True, "id": pid, "short_url": url, "name": name, "price_cents": catalog_entry["price"]}
    else:
        logger.error(f"[Gumroad] Create failed for {name}: {resp.get('message')}")
        return {"ok": False, "name": name, "error": resp.get("message", "unknown")}


def bootstrap_catalog() -> List[Dict[str, Any]]:
    """
    Ensure all 5 products exist on Gumroad.
    Idempotent — safe to call on every deploy.
    Returns list of results.
    """
    results = []
    for entry in PRODUCT_CATALOG:
        result = create_product(entry)
        results.append(result)
    created = sum(1 for r in results if r.get("ok") and not r.get("skipped"))
    skipped = sum(1 for r in results if r.get("skipped"))
    logger.info(f"[Gumroad] Catalog bootstrap: {created} created, {skipped} already existed")
    return results


def get_sales(product_id: Optional[str] = None, after: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch recent sales. Returns total_revenue_usd and sale count.
    after: ISO date string e.g. '2026-01-01'
    """
    params: Dict[str, Any] = {}
    if after:
        params["after"] = after
    resp = _request("GET", "sales", params)
    if not resp.get("success"):
        return {"ok": False, "error": resp.get("message", "unknown")}

    sales = resp.get("sales", [])
    if product_id:
        sales = [s for s in sales if s.get("product_id") == product_id]

    total_cents = sum(int(s.get("price", 0)) for s in sales)
    return {
        "ok":                True,
        "sale_count":        len(sales),
        "total_revenue_usd": round(total_cents / 100, 2),
        "sales":             sales[:50],
    }


def revenue_summary() -> Dict[str, Any]:
    """Aggregate revenue across all products."""
    products = list_products()
    today    = datetime.now(timezone.utc).strftime("%Y-%m-01")   # month start
    month_sales = get_sales(after=today)
    return {
        "ok":              True,
        "products":        len(products),
        "month_sales":     month_sales.get("sale_count", 0),
        "month_revenue_usd": month_sales.get("total_revenue_usd", 0),
        "catalog":         [{"name": p.get("name"), "id": p.get("id")} for p in products],
    }

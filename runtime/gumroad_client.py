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
    # ── Bookable field services (Arizona) — checkout online, fulfillment
    #    scheduled by dispatch. Priced per 2026 MSP-assessment benchmarks
    #    ($1,500–$5,000 standalone assessments).
    {
        "name":        "Phoenix Network Health Assessment (On-Site)",
        "price":       75000,          # $750.00
        "description": (
            "Book a professional on-site network assessment anywhere in the "
            "Phoenix metro. A field engineer reviews your switching, cabling, "
            "rack condition, Wi-Fi coverage, and ISP handoff, and you receive "
            "a findings report with photo documentation and a prioritized fix "
            "list within 3 business days of the visit. How it works: after "
            "checkout, Already Here LLC contacts you within 1 business day to "
            "schedule (visits typically within 5 business days). Full refund "
            "if we cannot schedule your site. Details and our published rate "
            "card: https://www.alreadyherellc.com/services-catalog — "
            "questions: dispatch@alreadyherellc.com."
        ),
        "tags":        ["network-assessment", "phoenix", "arizona", "it-services", "field-service"],
        "url_suffix":  "phoenix-network-assessment",
    },
    {
        "name":        "Arizona Infrastructure Assessment (Full Site, On-Site)",
        "price":       150000,         # $1,500.00
        "description": (
            "A comprehensive one-day on-site technology assessment for one "
            "Arizona site: network, power and racks, endpoints, wiring "
            "closets, and physical security (cameras and access control). "
            "Deliverables: an executive report, full photo documentation, an "
            "asset snapshot, and a prioritized remediation roadmap you can "
            "hand to any vendor. After checkout we contact you within 1 "
            "business day to schedule; full refund if we cannot schedule "
            "your site. Rate card and scope details: "
            "https://www.alreadyherellc.com/services-catalog — "
            "questions: dispatch@alreadyherellc.com."
        ),
        "tags":        ["infrastructure", "assessment", "arizona", "phoenix", "it-audit"],
        "url_suffix":  "arizona-infrastructure-assessment",
    },
    {
        "name":        "Smart Hands Half-Day Block — Phoenix (4 Hours On-Site)",
        "price":       40000,          # $400.00
        "description": (
            "Four hours of directed on-site technical work in the Phoenix "
            "metro under your remote team's guidance: rack and stack, cable "
            "moves, device swaps, equipment verification, data center smart "
            "hands. Every visit includes a work log and photo documentation. "
            "After checkout we contact you within 1 business day to schedule "
            "(same-week visits are typical). Full refund if we cannot "
            "schedule. Full 42-service catalog: "
            "https://www.alreadyherellc.com/services-catalog — "
            "questions: dispatch@alreadyherellc.com."
        ),
        "tags":        ["smart-hands", "phoenix", "data-center", "field-service", "arizona"],
        "url_suffix":  "phoenix-smart-hands-half-day",
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


def _find_product(name: str) -> Optional[Dict[str, Any]]:
    """Return the product dict if a product with this name already exists."""
    for p in list_products():
        if p.get("name", "").strip().lower() == name.strip().lower():
            return p
    return None


# Gumroad's v2 API accepts published=true on create but still lands products
# in draft — an explicit PUT is required afterwards. Even the PUT can be
# refused when the product has no deliverable file, and the API cannot upload
# files, so we report that honestly instead of claiming success.
_MANUAL_STEP = (
    "manual publish required in Gumroad dashboard — most likely the product "
    "has no content file attached (the v2 API cannot upload files)"
)


def publish_product(product_id: str) -> Dict[str, Any]:
    """
    Flip one product live via PUT /v2/products/:id published=true.
    Returns {"ok", "published"}; when the API refuses (or the product stays
    draft), ok=False and manual_step explains the remaining manual action.
    """
    if not product_id:
        return {"ok": False, "published": False, "error": "no product id"}
    resp = _request("PUT", f"products/{product_id}", {"published": "true"})
    published = bool(resp.get("success") and resp.get("product", {}).get("published"))
    if published:
        return {"ok": True, "published": True}
    return {
        "ok":          False,
        "published":   False,
        "error":       resp.get("message", "still draft after publish PUT"),
        "manual_step": _MANUAL_STEP,
    }


def publish_all_drafts() -> List[Dict[str, Any]]:
    """
    Attempt to publish every unpublished product in the account.
    Returns a per-product status list — drafts that can't be published via
    the API are reported as still_draft with a manual_step, never as success.
    """
    results = []
    for p in list_products():
        name, pid = p.get("name", "?"), p.get("id", "")
        if p.get("published"):
            results.append({"name": name, "id": pid, "status": "live",
                            "short_url": p.get("short_url", "")})
            continue
        pub = publish_product(pid)
        results.append({
            "name":       name,
            "id":         pid,
            "status":     "published" if pub.get("published") else "still_draft",
            "short_url":  p.get("short_url", ""),
            **({"error": pub.get("error"), "manual_step": pub.get("manual_step")}
               if not pub.get("published") else {}),
        })
    return results


def create_product(catalog_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Idempotently create a Gumroad product and attempt to publish it.
    Skips creation if a product with the same name already exists (but still
    tries to publish it if it is sitting in draft).
    Returns the product dict (including id and short_url) plus an honest
    published flag and, when the API can't publish, a manual_step note.
    """
    name = catalog_entry["name"]
    existing = _find_product(name)
    if existing:
        pid = existing.get("id", "")
        logger.info(f"[Gumroad] Product already exists: {name} ({pid})")
        result: Dict[str, Any] = {
            "ok": True, "id": pid, "skipped": True, "name": name,
            "short_url": existing.get("short_url", ""),
        }
        if existing.get("published"):
            result["published"] = True
        else:
            pub = publish_product(pid)
            result["published"] = bool(pub.get("published"))
            if not result["published"]:
                result["manual_step"] = pub.get("manual_step")
                logger.warning(f"[Gumroad] {name} still draft: {pub.get('error')}")
        return result

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
        result = {"ok": True, "id": pid, "short_url": url, "name": name,
                  "price_cents": catalog_entry["price"]}
        if product.get("published"):
            result["published"] = True
        else:
            pub = publish_product(pid)
            result["published"] = bool(pub.get("published"))
            if not result["published"]:
                result["manual_step"] = pub.get("manual_step")
                logger.warning(f"[Gumroad] {name} created but still draft: {pub.get('error')}")
        return result
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
    live    = sum(1 for r in results if r.get("published"))
    drafts  = sum(1 for r in results if r.get("ok") and not r.get("published"))
    logger.info(
        f"[Gumroad] Catalog bootstrap: {created} created, {skipped} already existed, "
        f"{live} live, {drafts} still draft"
    )
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
    if not _token():
        return {"ok": False, "error": "GUMROAD_ACCESS_TOKEN not set"}
    products = list_products()
    today    = datetime.now(timezone.utc).strftime("%Y-%m-01")   # month start
    month_sales = get_sales(after=today)
    if not month_sales.get("ok"):
        return {"ok": False, "error": month_sales.get("error", "unknown"), "products": len(products)}
    live   = sum(1 for p in products if p.get("published"))
    return {
        "ok":              True,
        "products":        len(products),
        "live":            live,
        "drafts":          len(products) - live,
        "month_sales":     month_sales.get("sale_count", 0),
        "month_revenue_usd": month_sales.get("total_revenue_usd", 0),
        "catalog":         [{"name": p.get("name"), "id": p.get("id"),
                             "published": bool(p.get("published"))} for p in products],
    }

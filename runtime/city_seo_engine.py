"""
Programmatic SEO City-Page Engine — Income Stream 10
=====================================================
Generates hundreds of location-targeted service pages at scale and
commits them to the GitHub content repo for GitHub Pages hosting.

Revenue model:
  Display ads (Mediavine/Ezoic) once traffic > 10k/mo: $15–$40 RPM
  Hyper-local affiliate sponsorships per city niche
  Lead capture for AAA chatbot/automation service upsell

Architecture:
  1. Template engine: Markdown + frontmatter per city × service
  2. Inference cascade: generates unique body copy (no duplicate content)
  3. GitHub commit: publishes via existing github_client.py
  4. Sitemap update: appends new URLs to sitemap.xml

Niches supported (configurable via CITY_SEO_NICHES env var):
  it-support, automation-agency, dog-grooming, coffee-shops,
  roofers, plumbers, accountants, real-estate-agents, ai-chatbots,
  social-media-management

Scale: 500 US cities × 10 niches = 5,000 indexed pages
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("CitySEOEngine")

# ── Top 500 US cities (state, city, population tier) ──────────────────────────
# Tier A = top 50 (highest search volume), B = 51-200, C = 201-500

_CITIES: List[Tuple[str, str, str]] = [
    # Tier A — highest traffic potential
    ("New York", "NY", "A"),
    ("Los Angeles", "CA", "A"),
    ("Chicago", "IL", "A"),
    ("Houston", "TX", "A"),
    ("Phoenix", "AZ", "A"),
    ("Philadelphia", "PA", "A"),
    ("San Antonio", "TX", "A"),
    ("San Diego", "CA", "A"),
    ("Dallas", "TX", "A"),
    ("San Jose", "CA", "A"),
    ("Austin", "TX", "A"),
    ("Jacksonville", "FL", "A"),
    ("Fort Worth", "TX", "A"),
    ("Columbus", "OH", "A"),
    ("Charlotte", "NC", "A"),
    ("Indianapolis", "IN", "A"),
    ("San Francisco", "CA", "A"),
    ("Seattle", "WA", "A"),
    ("Denver", "CO", "A"),
    ("Nashville", "TN", "A"),
    ("Oklahoma City", "OK", "A"),
    ("El Paso", "TX", "A"),
    ("Washington", "DC", "A"),
    ("Boston", "MA", "A"),
    ("Las Vegas", "NV", "A"),
    ("Memphis", "TN", "A"),
    ("Louisville", "KY", "A"),
    ("Baltimore", "MD", "A"),
    ("Milwaukee", "WI", "A"),
    ("Albuquerque", "NM", "A"),
    ("Tucson", "AZ", "A"),
    ("Fresno", "CA", "A"),
    ("Sacramento", "CA", "A"),
    ("Mesa", "AZ", "A"),
    ("Kansas City", "MO", "A"),
    ("Atlanta", "GA", "A"),
    ("Omaha", "NE", "A"),
    ("Colorado Springs", "CO", "A"),
    ("Raleigh", "NC", "A"),
    ("Long Beach", "CA", "A"),
    ("Virginia Beach", "VA", "A"),
    ("Minneapolis", "MN", "A"),
    ("Tampa", "FL", "A"),
    ("New Orleans", "LA", "A"),
    ("Arlington", "TX", "A"),
    ("Bakersfield", "CA", "A"),
    ("Honolulu", "HI", "A"),
    ("Anaheim", "CA", "A"),
    ("Aurora", "CO", "A"),
    ("Santa Ana", "CA", "A"),
    # Tier B
    ("Corpus Christi", "TX", "B"),
    ("Riverside", "CA", "B"),
    ("Lexington", "KY", "B"),
    ("St. Louis", "MO", "B"),
    ("Pittsburgh", "PA", "B"),
    ("Stockton", "CA", "B"),
    ("Anchorage", "AK", "B"),
    ("Cincinnati", "OH", "B"),
    ("St. Paul", "MN", "B"),
    ("Greensboro", "NC", "B"),
    ("Toledo", "OH", "B"),
    ("Newark", "NJ", "B"),
    ("Plano", "TX", "B"),
    ("Henderson", "NV", "B"),
    ("Lincoln", "NE", "B"),
    ("Buffalo", "NY", "B"),
    ("Fort Wayne", "IN", "B"),
    ("Jersey City", "NJ", "B"),
    ("Chula Vista", "CA", "B"),
    ("Orlando", "FL", "B"),
    ("St. Petersburg", "FL", "B"),
    ("Norfolk", "VA", "B"),
    ("Chandler", "AZ", "B"),
    ("Laredo", "TX", "B"),
    ("Madison", "WI", "B"),
    ("Durham", "NC", "B"),
    ("Lubbock", "TX", "B"),
    ("Winston-Salem", "NC", "B"),
    ("Garland", "TX", "B"),
    ("Glendale", "AZ", "B"),
    ("Hialeah", "FL", "B"),
    ("Reno", "NV", "B"),
    ("Baton Rouge", "LA", "B"),
    ("Irvine", "CA", "B"),
    ("Chesapeake", "VA", "B"),
    ("Irving", "TX", "B"),
    ("Scottsdale", "AZ", "B"),
    ("North Las Vegas", "NV", "B"),
    ("Fremont", "CA", "B"),
    ("Gilbert", "AZ", "B"),
    ("San Bernardino", "CA", "B"),
    ("Birmingham", "AL", "B"),
    ("Rochester", "NY", "B"),
    ("Richmond", "VA", "B"),
    ("Spokane", "WA", "B"),
    ("Des Moines", "IA", "B"),
    ("Montgomery", "AL", "B"),
    ("Modesto", "CA", "B"),
    ("Fayetteville", "NC", "B"),
    ("Tacoma", "WA", "B"),
    ("Shreveport", "LA", "B"),
    # Tier C — long-tail, lower competition
    ("Akron", "OH", "C"),
    ("Aurora", "IL", "C"),
    ("Yonkers", "NY", "C"),
    ("Columbus", "GA", "C"),
    ("Glendale", "CA", "C"),
    ("Huntington Beach", "CA", "C"),
    ("Little Rock", "AR", "C"),
    ("Knoxville", "TN", "C"),
    ("Oxnard", "CA", "C"),
    ("Providence", "RI", "C"),
    ("Garden Grove", "CA", "C"),
    ("Chattanooga", "TN", "C"),
    ("Oceanside", "CA", "C"),
    ("Fort Lauderdale", "FL", "C"),
    ("Rancho Cucamonga", "CA", "C"),
    ("Santa Clarita", "CA", "C"),
    ("Grand Rapids", "MI", "C"),
    ("Overland Park", "KS", "C"),
    ("Tallahassee", "FL", "C"),
    ("Worcester", "MA", "C"),
    ("Cape Coral", "FL", "C"),
    ("Tempe", "AZ", "C"),
    ("Ontario", "CA", "C"),
    ("Vancouver", "WA", "C"),
    ("Sioux Falls", "SD", "C"),
    ("Peoria", "IL", "C"),
    ("Springfield", "MO", "C"),
    ("Elk Grove", "CA", "C"),
    ("Pembroke Pines", "FL", "C"),
    ("Salem", "OR", "C"),
    ("Eugene", "OR", "C"),
    ("Corona", "CA", "C"),
    ("Cary", "NC", "C"),
    ("Fort Collins", "CO", "C"),
    ("Jackson", "MS", "C"),
    ("Alexandria", "VA", "C"),
    ("Hayward", "CA", "C"),
    ("Clarksville", "TN", "C"),
    ("Lancaster", "CA", "C"),
    ("Salinas", "CA", "C"),
    ("Sunnyvale", "CA", "C"),
    ("Pomona", "CA", "C"),
    ("Escondido", "CA", "C"),
    ("Kansas City", "KS", "C"),
    ("Palmdale", "CA", "C"),
    ("Rockford", "IL", "C"),
    ("Paterson", "NJ", "C"),
    ("Torrance", "CA", "C"),
    ("Bridgeport", "CT", "C"),
    ("McAllen", "TX", "C"),
]

# ── Niches ─────────────────────────────────────────────────────────────────────

_NICHES: Dict[str, Dict[str, str]] = {
    "it-support": {
        "title": "Best IT Support Services in {city}, {state} ({year})",
        "h1": "Top IT Support Companies in {city}, {state}",
        "keyword": "IT support {city}",
        "category": "Technology",
        "cta": "Get a Free IT Audit",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "ai-chatbots": {
        "title": "AI Chatbot Services for {city}, {state} Businesses ({year})",
        "h1": "Custom AI Chatbots for {city} Small Businesses",
        "keyword": "AI chatbot {city}",
        "category": "Technology",
        "cta": "Get Your Free Chatbot Demo",
        "cta_url": "https://alreadyherellc.com/chatbot",
    },
    "automation-agency": {
        "title": "Business Automation Agency in {city}, {state} — Already Here LLC",
        "h1": "AI Workflow Automation for {city} Businesses",
        "keyword": "business automation {city}",
        "category": "Business Services",
        "cta": "Automate Your Business Today",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "social-media-management": {
        "title": "Social Media Management Services in {city}, {state} ({year})",
        "h1": "Affordable Social Media Management in {city}",
        "keyword": "social media management {city}",
        "category": "Marketing",
        "cta": "Get a Free Content Audit",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "roofers": {
        "title": "Best Roofers in {city}, {state} — Top-Rated Roofing Companies ({year})",
        "h1": "Find Trusted Roofing Contractors in {city}, {state}",
        "keyword": "roofers {city}",
        "category": "Home Services",
        "cta": "Get 3 Free Roofing Quotes",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "plumbers": {
        "title": "Best Plumbers in {city}, {state} — Licensed & Insured ({year})",
        "h1": "Top Plumbing Services in {city}, {state}",
        "keyword": "plumbers {city}",
        "category": "Home Services",
        "cta": "Get Emergency Plumbing Help",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "accountants": {
        "title": "Best Accountants & CPAs in {city}, {state} ({year})",
        "h1": "Top-Rated Accountants in {city}, {state}",
        "keyword": "accountants {city}",
        "category": "Finance",
        "cta": "Book a Free Tax Consultation",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "real-estate-agents": {
        "title": "Best Real Estate Agents in {city}, {state} ({year})",
        "h1": "Top Real Estate Agents in {city}, {state}",
        "keyword": "real estate agents {city}",
        "category": "Real Estate",
        "cta": "Find Your Agent Today",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "dog-grooming": {
        "title": "Best Dog Groomers in {city}, {state} — Top-Rated ({year})",
        "h1": "Dog Grooming Services in {city}, {state}",
        "keyword": "dog grooming {city}",
        "category": "Pet Services",
        "cta": "Book a Grooming Appointment",
        "cta_url": "https://alreadyherellc.com/contact",
    },
    "coffee-shops": {
        "title": "Best Coffee Shops in {city}, {state} ({year}) — Local Guide",
        "h1": "Top Coffee Shops in {city}, {state}",
        "keyword": "coffee shops {city}",
        "category": "Food & Drink",
        "cta": "Discover {city} Coffee Culture",
        "cta_url": "https://alreadyherellc.com",
    },
}

_FTC = (
    "*Disclosure: This page may contain affiliate links. "
    "Already Here LLC may earn a commission on qualifying referrals. "
    "[FTC Disclosure](https://alreadyherellc.com/disclosure)*"
)


def _schema_json(h1: str, description: str, city: str, state: str, slug: str) -> str:
    """JSON-LD Article schema for the editorial roundup page.

    These pages are curated guides, not the business entity itself, so
    ``Article`` (not ``LocalBusiness``) is the accurate type — a mismatched
    LocalBusiness claim on a directory page is a structured-data violation.
    Built with json.dumps so quotes in titles/descriptions escape correctly."""
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": h1,
            "description": description,
            "author": {
                "@type": "Organization",
                "name": "Already Here LLC",
                "url": "https://alreadyherellc.com",
            },
            "publisher": {
                "@type": "Organization",
                "name": "Already Here LLC",
                "url": "https://alreadyherellc.com",
            },
            "about": {
                "@type": "City",
                "name": city,
                "containedInPlace": {"@type": "State", "name": state},
            },
            "mainEntityOfPage": f"https://alreadyherellc.com/city-pages/{slug}",
        },
        indent=2,
    )


# ── Page generator ─────────────────────────────────────────────────────────────


@dataclass
class CityPage:
    city: str
    state: str
    niche: str
    slug: str
    title: str
    h1: str
    keyword: str
    body_md: str
    schema_json: str
    file_path: str  # relative path in content repo
    word_count: int


def _slug(city: str, niche: str) -> str:
    city_slug = re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")
    niche_slug = niche.replace("_", "-")
    return f"{niche_slug}/{city_slug}"


def _gen_body(city: str, state: str, niche_cfg: Dict[str, str], year: int) -> str:
    """
    Generate a unique body paragraph per city via the inference cascade.
    Falls back to a template-only version if LLM unavailable.
    """
    keyword = niche_cfg["keyword"].format(city=city, state=state)
    cta = niche_cfg["cta"].format(city=city)
    cta_url = niche_cfg["cta_url"]

    try:
        from runtime.inference_cascade import infer

        system = (
            "You are an SEO content writer producing genuinely useful local service guides. "
            "Write factual, locally-relevant Markdown body content — no H1, no preamble. "
            "Use ## headings, short paragraphs, and bullet lists where they aid scanning. "
            "Total word count: 420-560 words. Be specific and actionable; never pad."
        )
        prompt = (
            f"Write a helpful local guide about '{keyword}' for {city}, {state} (year {year}).\n"
            "Required structure:\n"
            f"## What {city} {keyword.split()[0].title()} Services Cover\n"
            "  1-2 paragraphs on typical offerings in this niche.\n"
            "## How to Choose a Provider\n"
            "  Bulleted checklist: licensing/insurance verification, reviews, written estimates, "
            "response time, warranties.\n"
            "## Typical Costs and What Affects Price\n"
            "  Qualitative pricing guidance (ranges allowed only as broad typical bands; "
            "never fabricate precise local prices).\n"
            "## Questions to Ask Before Hiring\n"
            "  3-5 bullets.\n"
            f"End with a short paragraph and this call to action: {cta}"
        )
        body, _ = infer(system, prompt, max_tokens=900)
        if body.startswith("INFERENCE_STUB") or len(body) < 300:
            raise ValueError("inference unavailable")
        return body
    except Exception:
        # Deterministic fallback — structured, still useful at zero inference cost
        service = niche_cfg["keyword"].split()[0]
        return (
            f"## What {city} {service.title()} Services Cover\n\n"
            f"Finding reliable {service} services in {city}, {state} means comparing "
            f"providers on more than price. Local {service} professionals in {city} "
            "typically handle everything from routine work to urgent same-day calls, "
            "and the right choice depends on response time, credentials, and fit for "
            "your specific job.\n\n"
            "## How to Choose a Provider\n\n"
            "- Verify current licensing and insurance before any work begins.\n"
            "- Check recent reviews on at least two independent platforms.\n"
            "- Get written estimates from 2-3 providers — compare scope, not just price.\n"
            "- Ask about warranties or guarantees on completed work.\n"
            "- Confirm who actually performs the work (employees vs. subcontractors).\n\n"
            "## Typical Costs and What Affects Price\n\n"
            f"In {city}, pricing for {service} work varies with job complexity, materials, "
            "urgency, and provider experience. Emergency or after-hours service usually "
            "costs more. Always request an itemized quote so you can compare providers "
            "on equal terms — the cheapest quote is not always the best value.\n\n"
            "## Questions to Ask Before Hiring\n\n"
            "- How long have you served the "
            f"{city} area?\n"
            "- Can you provide proof of licensing and insurance?\n"
            "- What does the estimate include — and exclude?\n"
            "- What is the expected timeline, and how are delays handled?\n\n"
            f"Already Here LLC connects {city} residents and businesses with vetted, "
            f"top-rated {service} providers. "
            f"[{cta}]({cta_url}) — free, no obligation."
        )


def generate_page(
    city: str,
    state: str,
    niche: str,
    tier: str = "B",
) -> Optional[CityPage]:
    """Generate one city × niche page. Returns None if niche not found."""
    niche_cfg = _NICHES.get(niche)
    if not niche_cfg:
        logger.warning(f"[CitySEO] Unknown niche: {niche}")
        return None

    year = datetime.now(timezone.utc).year
    fmt = {"city": city, "state": state, "year": year}
    title = niche_cfg["title"].format(**fmt)
    h1 = niche_cfg["h1"].format(**fmt)
    kw = niche_cfg["keyword"].format(**fmt)
    slug = _slug(city, niche)
    body = _gen_body(city, state, niche_cfg, year)
    desc = f"Find the best {kw} providers in {city}, {state}. Curated by AI, updated {year}."

    schema = _schema_json(h1, desc[:150], city, state, slug)

    md = f"""---
title: "{title}"
description: "{desc}"
date: "{datetime.now(timezone.utc).strftime("%Y-%m-%d")}"
keywords: ["{kw}", "{city} {niche}", "{city} {state}"]
schema: |
{chr(10).join("  " + line for line in schema.splitlines())}
---

# {h1}

{body}

---

**[{niche_cfg["cta"].format(city=city)}]({niche_cfg["cta_url"]})**

{_FTC}
"""
    file_path = f"city-pages/{slug}.md"
    word_count = len(md.split())

    return CityPage(
        city=city,
        state=state,
        niche=niche,
        slug=slug,
        title=title,
        h1=h1,
        keyword=kw,
        body_md=md,
        schema_json=schema,
        file_path=file_path,
        word_count=word_count,
    )


# ── Batch publisher ────────────────────────────────────────────────────────────


def generate_batch(
    niches: Optional[List[str]] = None,
    tiers: Optional[List[str]] = None,
    limit: int = 50,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Generate and commit city pages to the GitHub content repo.

    Parameters
    ----------
    niches  : List of niche keys (default: all niches).
    tiers   : City tiers to include — "A", "B", "C" (default: all).
    limit   : Max pages per run (stay under GitHub rate limits).
    dry_run : If True, generate pages but don't commit.

    Returns summary dict with pages generated, committed, errors.
    """
    from runtime.github_client import commit_file

    active_niches = niches or list(_NICHES.keys())
    active_tiers = tiers or ["A", "B", "C"]

    env_niches = os.environ.get("CITY_SEO_NICHES", "").strip()
    if env_niches:
        active_niches = [n.strip() for n in env_niches.split(",") if n.strip()]

    cities = [(c, s, t) for c, s, t in _CITIES if t in active_tiers]

    # Optional Google Trends demand ranking (CITY_SEO_TRENDS_RANK=1). Reorders
    # cities by measured search interest for the first active niche; on any
    # Trends failure it silently keeps static tier order (failover rule).
    if os.environ.get("CITY_SEO_TRENDS_RANK", "").strip() in {"1", "true", "yes"}:
        try:
            from runtime.trend_regions import prioritize_cities

            cities = prioritize_cities(cities, active_niches[0].replace("-", " "))
        except Exception as exc:
            logger.warning(f"[CitySEO] Trends ranking unavailable ({exc}) — static order")

    pages_generated = 0
    pages_committed = 0
    errors: List[str] = []

    for city, state, tier in cities:
        for niche in active_niches:
            if pages_generated >= limit:
                break

            # Dedup check via deterministic slug
            page = generate_page(city, state, niche, tier)
            if not page:
                continue

            pages_generated += 1

            if dry_run:
                logger.info(
                    f"[CitySEO] DRY RUN: {page.file_path} ({page.word_count} words)"
                )
                continue

            try:
                ok = commit_file(
                    path=page.file_path,
                    content=page.body_md,
                    message=f"seo: add city page {city}, {state} — {niche}",
                )
                if ok:
                    pages_committed += 1
                    logger.info(f"[CitySEO] Committed: {page.file_path}")
                else:
                    errors.append(f"commit failed: {page.file_path}")
            except Exception as exc:
                errors.append(f"{page.file_path}: {exc}")

        if pages_generated >= limit:
            break

    return {
        "ok": len(errors) == 0,
        "pages_generated": pages_generated,
        "pages_committed": pages_committed,
        "errors": errors[:20],
        "dry_run": dry_run,
        "niches": active_niches,
        "tiers": active_tiers,
    }

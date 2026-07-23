"""Deterministic profitability model for ProfitEngine revenue agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PROOF_THRESHOLD_USD = 25_000.0

STORE_LINKS = {
    "etsy": "https://www.etsy.com/shop/AlreadyHereLLC",
    "printify": "https://fly-culture-shop.printify.me",
    "shopify": "https://flydesignvault.com",
    "profitengine": "https://app.alreadyherellc.com",
}


@dataclass(frozen=True)
class Offer:
    id: str
    name: str
    stream: str
    price_usd: float
    cost_usd: float
    fulfillment_hours: float
    channel: str
    proof_required: bool
    cta: str
    notes: str


OFFERS: list[Offer] = [
    Offer(
        "etsy-pod-shirt",
        "Proof-first builder apparel",
        "pod",
        29.99,
        16.50,
        0.05,
        "Etsy + Printify",
        False,
        STORE_LINKS["etsy"],
        "Publish the 8 prepared POD listings and route content traffic to them.",
    ),
    Offer(
        "etsy-printify-build",
        "Etsy/Printify store build",
        "service",
        499.0,
        25.0,
        5.0,
        "DM, local business, founder communities",
        False,
        "mailto:dispatch@alreadyherellc.com?subject=Etsy%20Printify%20Store%20Build",
        "Productized setup service using the same store pack process built for Already Here LLC.",
    ),
    Offer(
        "stripe-payment-setup",
        "Stripe payment setup",
        "service",
        349.0,
        10.0,
        3.0,
        "small business outreach",
        False,
        "mailto:dispatch@alreadyherellc.com?subject=Stripe%20Payment%20Setup",
        "Set up checkout, webhook readiness, smoke test, and basic payment reporting.",
    ),
    Offer(
        "ai-content-system",
        "AI content system setup",
        "service",
        799.0,
        35.0,
        8.0,
        "creator/operator outreach",
        False,
        "mailto:dispatch@alreadyherellc.com?subject=AI%20Content%20System%20Setup",
        "Build a content calendar, generation workflow, affiliate injection, and manual publishing pack.",
    ),
    Offer(
        "local-automation",
        "Local business automation",
        "service",
        999.0,
        50.0,
        10.0,
        "Phoenix local service outreach",
        False,
        "mailto:dispatch@alreadyherellc.com?subject=Local%20Business%20Automation",
        "Lead intake, follow-up templates, lightweight CRM, and payment links for a local operator.",
    ),
    Offer(
        "printify-affiliate-content",
        "Printify education affiliate funnel",
        "affiliate",
        0.0,
        0.0,
        1.0,
        "blog, short-form, Reddit, Pinterest",
        False,
        STORE_LINKS["printify"],
        "Create honest tutorials from the actual shop build; do not imply guaranteed earnings.",
    ),
    Offer(
        "profitengine-hosted-beta",
        "ProfitEngine hosted beta",
        "saas",
        149.0,
        20.0,
        2.0,
        "waitlist",
        True,
        f"{STORE_LINKS['profitengine']}#waitlist",
        "Keep waitlist-only until the proof ledger reaches $25,000 verified revenue.",
    ),
]


def margin_for_offer(offer: Offer) -> dict[str, Any]:
    gross = offer.price_usd
    platform_fee = 0.20 + gross * 0.065 if offer.stream == "pod" else 0.0
    payment_fee = gross * 0.03 + 0.25 if gross > 0 else 0.0
    net = gross - offer.cost_usd - platform_fee - payment_fee
    margin_pct = (net / gross * 100.0) if gross else 0.0
    return {
        "offer_id": offer.id,
        "name": offer.name,
        "stream": offer.stream,
        "price_usd": round(gross, 2),
        "estimated_cost_usd": round(offer.cost_usd, 2),
        "estimated_platform_fee_usd": round(platform_fee, 2),
        "estimated_payment_fee_usd": round(payment_fee, 2),
        "estimated_net_usd": round(net, 2),
        "estimated_margin_pct": round(margin_pct, 1),
        "fulfillment_hours": offer.fulfillment_hours,
        "net_per_hour_usd": round(net / offer.fulfillment_hours, 2) if offer.fulfillment_hours else 0,
        "proof_required": offer.proof_required,
        "cta": offer.cta,
        "notes": offer.notes,
    }


def ranked_offers() -> list[dict[str, Any]]:
    rows = [margin_for_offer(offer) for offer in OFFERS]
    return sorted(rows, key=lambda item: (item["proof_required"], -item["net_per_hour_usd"], -item["estimated_net_usd"]))


def proof_status(verified_revenue_usd: float = 0.0) -> dict[str, Any]:
    remaining = max(0.0, PROOF_THRESHOLD_USD - verified_revenue_usd)
    return {
        "threshold_usd": PROOF_THRESHOLD_USD,
        "verified_revenue_usd": round(verified_revenue_usd, 2),
        "remaining_usd": round(remaining, 2),
        "unlocked": verified_revenue_usd >= PROOF_THRESHOLD_USD,
        "rule": "Command OS/ProfitEngine paid offers stay waitlist-only until verified revenue reaches $25,000.",
    }


def traffic_pack() -> list[dict[str, str]]:
    return [
        {
            "channel": "Etsy/Pinterest",
            "asset": "Proof First shirt pin",
            "copy": "No hype. Ledger before launch. Builder apparel for operators who show receipts.",
            "url": STORE_LINKS["etsy"],
        },
        {
            "channel": "LinkedIn",
            "asset": "service offer post",
            "copy": "We built our own Etsy/Printify launch pack. Now we are taking 3 setup clients for store builds, Stripe checkout, and content systems.",
            "url": "mailto:dispatch@alreadyherellc.com?subject=Setup%20Client",
        },
        {
            "channel": "Blog",
            "asset": "tutorial CTA",
            "copy": "How we built a proof-first POD shop with Printify, Etsy metadata, and margin checks.",
            "url": STORE_LINKS["profitengine"],
        },
        {
            "channel": "Short-form video",
            "asset": "behind-the-build script",
            "copy": "I am not selling the software yet. I am using it to build the proof first: products, services, and a public ledger.",
            "url": STORE_LINKS["profitengine"],
        },
    ]


def listing_optimization_rules() -> dict[str, Any]:
    return {
        "title_rule": "Lead with buyer-search terms, keep the phrase readable, and avoid keyword soup.",
        "tag_rule": "Use all 13 tags with multi-word phrases covering buyer, occasion, style, and niche.",
        "photo_rule": "Use readable mockups first, then detail crops, size chart, and production partner/shipping note.",
        "conversion_rule": "Improve listing quality with clear sizing, production time, return policy, and benefit-led first paragraph.",
    }

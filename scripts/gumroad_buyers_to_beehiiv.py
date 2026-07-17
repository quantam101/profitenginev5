#!/usr/bin/env python3
"""Post-purchase automation, $0 and serverless: pull recent Gumroad sales and
subscribe each buyer to the Beehiiv newsletter (tagged by utm so they're
distinguishable from organic subscribers). Buyers then get the Monday issue —
the nurture sequence — automatically.

Runs from the daily revenue workflow. Stateless + idempotent: we only look at
the last N days of sales and Beehiiv dedupes by email (reactivate_existing),
so re-runs are harmless. Every failure is soft — this must never break the
revenue job.

Env: GUMROAD_ACCESS_TOKEN, BEEHIIV_API_KEY, BEEHIIV_PUBLICATION_ID
Usage: python scripts/gumroad_buyers_to_beehiiv.py [--days 7]
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import requests

GUMROAD_API = "https://api.gumroad.com/v2"
BEEHIIV_API = "https://api.beehiiv.com/v2"


def recent_buyer_emails(token: str, days: int) -> list[dict]:
    """All sales in the window as [{email, product_name}], paginated."""
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    out, page_key = [], None
    for _ in range(20):  # hard page cap — safety against pagination loops
        params = {"after": after}
        if page_key:
            params["page_key"] = page_key
        r = requests.get(f"{GUMROAD_API}/sales", params=params, timeout=30,
                         headers={"Authorization": f"Bearer {token}"})
        if r.status_code != 200:
            print(f"gumroad sales fetch failed: {r.status_code} {r.text[:200]}")
            break
        d = r.json()
        for s in d.get("sales", []):
            email = (s.get("email") or "").strip().lower()
            if email and not s.get("refunded") and not s.get("chargedback"):
                out.append({"email": email,
                            "product": s.get("product_name", "")})
        page_key = d.get("next_page_key")
        if not page_key:
            break
    # de-dupe within the window, keep first product seen
    seen, unique = set(), []
    for b in out:
        if b["email"] not in seen:
            seen.add(b["email"])
            unique.append(b)
    return unique


def subscribe(key: str, pub_id: str, buyer: dict) -> bool:
    """Add one buyer to Beehiiv. Existing subscribers are reactivated, not
    duplicated. No welcome email — they already got the Gumroad receipt."""
    r = requests.post(
        f"{BEEHIIV_API}/publications/{pub_id}/subscriptions",
        json={"email": buyer["email"], "reactivate_existing": True,
              "send_welcome_email": False, "utm_source": "gumroad",
              "utm_medium": "customer", "utm_campaign": buyer["product"][:80]},
        headers={"Authorization": f"Bearer {key}"}, timeout=30)
    if r.status_code in (200, 201):
        return True
    print(f"beehiiv subscribe failed for buyer: {r.status_code} {r.text[:200]}")
    return False


def main() -> None:
    days = 7
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    gum = os.getenv("GUMROAD_ACCESS_TOKEN", "").strip()
    key = os.getenv("BEEHIIV_API_KEY", "").strip()
    pub = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()
    missing = [n for n, v in [("GUMROAD_ACCESS_TOKEN", gum),
                              ("BEEHIIV_API_KEY", key),
                              ("BEEHIIV_PUBLICATION_ID", pub)] if not v]
    if missing:
        print(f"skipping buyer sync — missing env: {', '.join(missing)}")
        return  # fail soft: never break the revenue job

    try:
        buyers = recent_buyer_emails(gum, days)
    except Exception as e:  # noqa: BLE001 — network layer fails soft by design
        print(f"gumroad fetch error: {str(e)[:200]}")
        return
    if not buyers:
        print(f"no new buyers in the last {days} days")
        return

    ok = 0
    for b in buyers:
        try:
            ok += subscribe(key, pub, b)
        except Exception as e:  # noqa: BLE001
            print(f"beehiiv error: {str(e)[:200]}")
    print(f"buyer sync: {ok}/{len(buyers)} subscribed to the newsletter")


if __name__ == "__main__":
    main()

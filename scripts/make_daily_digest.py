#!/usr/bin/env python3
"""Daily newsletter composer. Builds the digest from real pipeline data —
trending_topics.json + youtube_uploads.json (video pipeline artifacts) and the
live Gumroad catalog — then POSTs it to the runtime /newsletter/publish
endpoint (Resend broadcast).

Replaces the hardcoded sections that previously lived in income-streams.yml,
which sent the identical email every day with no external links.

If no fresh data source is available at all, the send is SKIPPED (exit 0 with
a warning) rather than falling back to canned copy — repeat content is worse
than a missed day.

Env:
  RUNTIME_API_URL        — required; Render runtime base URL
  GUMROAD_ACCESS_TOKEN   — optional; enables the rotating product spotlight
  OPENROUTER/GROQ/...    — optional; free-LLM keys for the daily insight line

Usage:  python scripts/make_daily_digest.py [--dry-run]
"""
from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_shorts import ai_complete  # noqa: E402

PAGES_BASE = "https://quantam101.github.io/content"
BLUEPRINT_URL = f"{PAGES_BASE}/ebooks/blueprint/"
EBOOK_URL = f"{PAGES_BASE}/ebooks/zero-dollar-content-engine/"


def utm(url: str, campaign: str = "daily-digest") -> str:
    """Append UTM params to our own / partner links (not third-party YouTube)."""
    sep = "&" if "?" in url else "?"
    return (f"{url}{sep}utm_source=newsletter&utm_medium=email"
            f"&utm_campaign={urllib.parse.quote(campaign)}")


def _load(name: str):
    p = Path(name)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def gumroad_products() -> list[dict]:
    """Live product list (name, short_url, price) from the Gumroad API."""
    token = os.getenv("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        return []
    try:
        req = urllib.request.Request(
            f"https://api.gumroad.com/v2/products?access_token={token}",
            headers={"User-Agent": "already-here-digest/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        return [p for p in data.get("products", [])
                if p.get("published") and p.get("short_url")]
    except Exception as e:
        print(f"gumroad fetch failed ({str(e)[:80]}) — skipping product spotlight")
        return []


def compose() -> tuple[str, list[dict], str] | None:
    """Returns (headline, sections, cta_url), or None when there is nothing
    fresh to say (caller should skip the send)."""
    today = time.strftime("%B %d, %Y", time.gmtime())
    trending = (_load("trending_topics.json") or [])[:3]
    uploads = [u for u in (_load("youtube_uploads.json") or [])
               if u.get("status") == "success"]
    manifest = {v["program"]: v for v in (_load("videos_manifest.json") or [])}
    products = gumroad_products()

    if not (trending or uploads or products):
        return None

    sections: list[dict] = []

    insight = ai_complete(
        "Write a 2-3 sentence practical daily insight for small-business "
        "owners about automating content, lead capture, or customer service "
        "with free AI tools. Concrete and specific, plain text, no emojis, "
        "no hashtags.", min_len=60, max_len=500)
    if insight:
        sections.append({"heading": "Today's automation insight",
                         "body": html.escape(insight)})

    if uploads:
        items = []
        for u in uploads[:5]:
            m = manifest.get(u.get("program", ""), {})
            title = html.escape(m.get("title", u.get("program", "New video")))
            url = u.get("url") or \
                f"https://www.youtube.com/shorts/{u.get('video_id', '')}"
            items.append(f'&bull; <a href="{url}">{title}</a>')
        sections.append({"heading": "Fresh from our channel",
                         "body": "<br>".join(items)})

    if trending:
        items = []
        for t in trending:
            title = html.escape(t.get("title", "")[:80])
            url = t.get("url", "")
            vpd = t.get("views_per_day")
            stat = f" — ~{vpd:,} views/day" if vpd else ""
            items.append(f'&bull; <a href="{url}">{title}</a>{stat}')
        sections.append({
            "heading": "What's pulling views right now",
            "body": ("Top performers in our niches, live from today's "
                     "trend scan:<br>" + "<br>".join(items))})

    cta_url = utm(BLUEPRINT_URL)
    if products:
        # rotate the spotlight daily so no two consecutive issues match
        pick = products[int(time.strftime("%j")) % len(products)]
        name = html.escape(pick.get("name", ""))
        price = pick.get("formatted_price") or ""
        link = utm(pick["short_url"], campaign="daily-digest-product")
        sections.append({
            "heading": "From our toolkit",
            "body": (f'<a href="{link}">{name}</a>'
                     f'{f" — {html.escape(str(price))}" if price else ""}. '
                     f'Built from the same automation stack that writes this '
                     f'email. The full build manual is in '
                     f'<a href="{utm(BLUEPRINT_URL)}">the Complete Blueprint</a>, '
                     f'and the free intro is '
                     f'<a href="{utm(EBOOK_URL)}">The $0 Content Engine</a>.')})

    headline = f"AI Income Digest — {today}"
    return headline, sections[:10], cta_url


def publish(headline: str, sections: list[dict], cta_url: str) -> dict:
    base = os.environ["RUNTIME_API_URL"].rstrip("/")
    payload = {"headline": headline, "sections": sections,
               "tags": ["ai", "automation", "already-here"],
               "cta_url": cta_url}
    req = urllib.request.Request(
        f"{base}/newsletter/publish", data=json.dumps(payload).encode(),
        method="POST", headers={"Content-Type": "application/json",
                                "User-Agent": "already-here-digest/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main() -> None:
    composed = compose()
    if not composed:
        print("::warning::no fresh data (trends/uploads/products all empty) — "
              "skipping today's send to avoid repeat content")
        return
    headline, sections, cta_url = composed
    print(f"headline: {headline}")
    for s in sections:
        print(f"  section: {s['heading']}")
    if "--dry-run" in sys.argv:
        Path("daily_digest_preview.json").write_text(
            json.dumps({"headline": headline, "sections": sections,
                        "cta_url": cta_url}, indent=2), encoding="utf-8")
        print("dry run — wrote daily_digest_preview.json, nothing sent")
        return
    result = publish(headline, sections, cta_url)
    print(json.dumps(result))
    if not result.get("ok"):
        print(f"::error::newsletter publish failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

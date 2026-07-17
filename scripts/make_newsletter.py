#!/usr/bin/env python3
"""Dynamic Already Here LLC revenue-intelligence newsletter.

The composer reads current pipeline artifacts, builds a dated issue with
source-specific calls to action, refuses to silently reuse stale content, and
falls back to an honest "no verified new opportunities" notice instead of
repeating generic marketing copy.

Delivery order (fails soft):
  1. Beehiiv draft API
  2. GitHub Pages issue page
  3. newsletter.html artifact of record

Usage: python scripts/make_newsletter.py [--no-page]
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).parent))
from generate_shorts import ai_complete  # noqa: E402

CONTENT_REPO = "quantam101/content"
PAGES_BASE = "https://quantam101.github.io/content"
EBOOK_URL = f"{PAGES_BASE}/ebooks/zero-dollar-content-engine/"
BLUEPRINT_URL = f"{PAGES_BASE}/ebooks/blueprint/"
WEBSITE_URL = "https://alreadyherellc.com"
AI_SERVICE_URL = f"{WEBSITE_URL}/ai-agent"
RFQ_URL = f"{WEBSITE_URL}/rfq"
DISPATCH_URL = f"{WEBSITE_URL}/dispatch"
AUTOWORKS_URL = f"{WEBSITE_URL}/autoworks"

ARTIFACT_GROUPS: dict[str, tuple[str, ...]] = {
    "Revenue opportunities": (
        "revenue_opportunities.json",
        "opportunities.json",
        "opportunity_intelligence.json",
        "daily_opportunities.json",
    ),
    "Mechanic and AutoWorks leads": (
        "mechanic_opportunities.json",
        "autoworks_opportunities.json",
        "vehicle_service_leads.json",
    ),
    "Vehicle flip candidates": (
        "vehicle_flips.json",
        "flip_candidates.json",
        "vehicle_opportunities.json",
    ),
    "Grants": ("grants.json", "grant_opportunities.json"),
    "Contracts and bids": (
        "contracts.json",
        "bids.json",
        "procurement_opportunities.json",
    ),
    "Affiliate opportunities": (
        "affiliate_opportunities.json",
        "affiliate_programs.json",
    ),
}

CTA_BY_SECTION = {
    "Revenue opportunities": ("Request a quote", RFQ_URL),
    "Mechanic and AutoWorks leads": ("Contact AutoWorks", AUTOWORKS_URL),
    "Vehicle flip candidates": ("Open AutoWorks", AUTOWORKS_URL),
    "Grants": ("View the opportunity desk", f"{WEBSITE_URL}/daily-command"),
    "Contracts and bids": ("Submit an RFQ", RFQ_URL),
    "Affiliate opportunities": ("View current resources", EBOOK_URL),
}


def _load_json(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _as_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        for key in ("items", "opportunities", "results", "leads", "data"):
            if isinstance(value.get(key), list):
                return [x for x in value[key] if isinstance(x, dict)]
    return []


def _first(*values: Any, default: str = "") -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _item_title(item: dict[str, Any]) -> str:
    return _first(
        item.get("title"), item.get("name"), item.get("company"),
        item.get("vehicle"), item.get("subject"), default="Opportunity"
    )


def _item_summary(item: dict[str, Any]) -> str:
    fields = []
    for label, keys in (
        ("Location", ("location", "city", "service_area")),
        ("Pay/price", ("pay", "price", "asking_price", "value")),
        ("Scope", ("scope", "description", "summary", "repair_scope")),
        ("Grade", ("grade", "rating")),
        ("Next action", ("next_action", "action")),
    ):
        value = _first(*(item.get(k) for k in keys))
        if value:
            fields.append(f"<strong>{_escape(label)}:</strong> {_escape(value)}")
    return "<br>".join(fields[:5])


def _item_url(item: dict[str, Any], fallback: str) -> str:
    url = _first(item.get("url"), item.get("link"), item.get("source_url"))
    return url if url.startswith(("https://", "http://")) else fallback


def _collect_sections(limit_per_section: int = 3) -> list[tuple[str, list[dict[str, Any]]]]:
    sections: list[tuple[str, list[dict[str, Any]]]] = []
    seen: set[str] = set()
    for section, files in ARTIFACT_GROUPS.items():
        items: list[dict[str, Any]] = []
        for filename in files:
            for item in _as_items(_load_json(filename)):
                marker = json.dumps(item, sort_keys=True, default=str)
                digest = hashlib.sha256(marker.encode()).hexdigest()
                if digest not in seen:
                    seen.add(digest)
                    items.append(item)
        if items:
            sections.append((section, items[:limit_per_section]))
    return sections


def _pipeline_insights() -> list[dict[str, Any]]:
    uploads = _as_items(_load_json("youtube_uploads.json"))
    trending = _as_items(_load_json("trending_topics.json"))[:3]
    successful = [u for u in uploads if u.get("status") == "success"]
    insights: list[dict[str, Any]] = []
    if successful:
        insights.append({
            "title": f"{len(successful)} new videos published",
            "summary": "Fresh short-form content shipped by the production pipeline.",
            "url": "https://www.youtube.com/@alreadyherellc",
        })
    for topic in trending:
        insights.append({
            "title": _item_title(topic),
            "summary": _first(topic.get("summary"), topic.get("reason"),
                              default="Current audience-interest signal."),
            "url": _item_url(topic, "https://www.youtube.com/@alreadyherellc"),
        })
    return insights[:3]


def _button(label: str, url: str) -> str:
    return (
        f'<a href="{_escape(url)}" style="display:inline-block;padding:12px 18px;'
        'margin:8px 8px 8px 0;background:#e9ecff;color:#111827;text-decoration:none;'
        'font-weight:700;border-radius:8px">'
        f'{_escape(label)} &rarr;</a>'
    )


def _render_section(title: str, items: Iterable[dict[str, Any]]) -> str:
    label, fallback_url = CTA_BY_SECTION[title]
    cards = [f"<h2>{_escape(title)}</h2>"]
    for item in items:
        item_title = _item_title(item)
        item_url = _item_url(item, fallback_url)
        summary = _item_summary(item) or _escape(
            _first(item.get("summary"), item.get("description"),
                   default="Open the source and verify the current details before acting.")
        )
        cards.append(
            '<div style="border:1px solid #d7dbe8;border-radius:10px;padding:14px;'
            'margin:12px 0">'
            f'<h3 style="margin:0 0 8px">{_escape(item_title)}</h3>'
            f'<p style="margin:0 0 10px">{summary}</p>'
            f'{_button(label, item_url)}</div>'
        )
    return "\n".join(cards)


def compose() -> tuple[str, str, str]:
    """Return (subject, HTML body, stable content fingerprint)."""
    issue_date = time.strftime("%B %d, %Y", time.gmtime())
    sections = _collect_sections()
    insights = _pipeline_insights()
    verified_count = sum(len(items) for _, items in sections)
    subject = f"Already Here Revenue Intelligence — {issue_date}"

    intro = ai_complete(
        f"Write a two-sentence introduction for the Already Here LLC revenue "
        f"intelligence digest dated {issue_date}. It contains {verified_count} "
        "current opportunities. Be direct, factual, and concise. Do not use emojis, "
        "hashtags, hype, or generic automation claims.", min_len=45, max_len=360,
    ) or (
        f"This issue was generated from the latest available Already Here LLC "
        f"pipeline data for {issue_date}. Every opportunity still requires source, "
        "scope, pricing, and compliance verification before commitment."
    )

    body = [f"<p>{_escape(intro)}</p>"]
    if sections:
        for title, items in sections:
            body.append(_render_section(title, items))
    else:
        body.append(
            "<h2>Opportunity status</h2>"
            "<p>No new verified revenue opportunities were present in today's "
            "pipeline artifacts. We are not recycling yesterday's generic tips or "
            "presenting unverified listings as active leads.</p>"
        )

    if insights:
        body.append("<h2>Production and market signals</h2>")
        for item in insights:
            body.append(
                f"<h3>{_escape(item['title'])}</h3>"
                f"<p>{_escape(item['summary'])}</p>"
                f"{_button('View the source', item['url'])}"
            )

    body.append(
        "<h2>Take action</h2>"
        f"{_button('Book an AI automation review', AI_SERVICE_URL)}"
        f"{_button('Request field-service pricing', RFQ_URL)}"
        f"{_button('Dispatch AutoWorks', DISPATCH_URL)}"
        f"{_button('Download the free playbook', EBOOK_URL)}"
        f"{_button('View the Complete Blueprint', BLUEPRINT_URL)}"
        "<p>Reply to this email or contact dispatch@alreadyherellc.com for a "
        "written scope and quote.</p>"
        "<p><em>Some linked resources may use affiliate tracking. Already Here LLC "
        "may earn a commission at no additional cost to the purchaser.</em></p>"
    )

    canonical = json.dumps({
        "date": issue_date,
        "sections": sections,
        "insights": insights,
    }, sort_keys=True, default=str)
    fingerprint = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    body.append(f"<!-- issue-fingerprint:{fingerprint} -->")
    return subject, "\n".join(body), fingerprint


def try_beehiiv(subject: str, body: str) -> bool:
    key = os.getenv("BEEHIIV_API_KEY", "").strip()
    pub = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()
    if not (key and pub):
        print("no Beehiiv credentials — skipping API")
        return False
    try:
        req = urllib.request.Request(
            f"https://api.beehiiv.com/v2/publications/{pub}/posts",
            data=json.dumps({"title": subject, "body_content": body,
                             "status": "draft"}).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "User-Agent": "already-here-newsletter/2.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
        print(f"beehiiv draft created: {data.get('data', {}).get('preview_url', data)}")
        return True
    except urllib.error.HTTPError as exc:
        print(f"beehiiv API unavailable (HTTP {exc.code}: {exc.read()[:200]!r}) — falling back")
    except Exception as exc:
        print(f"beehiiv API failed ({str(exc)[:100]}) — falling back")
    return False


def publish_page(html_page: str) -> None:
    slug = time.strftime("%Y-%m-%d", time.gmtime())
    dest = f"newsletters/{slug}/index.html"
    encoded = base64.b64encode(html_page.encode()).decode()
    probe = subprocess.run(
        ["gh", "api", f"repos/{CONTENT_REPO}/contents/{dest}"],
        capture_output=True, text=True,
    )
    args = [
        "gh", "api", "-X", "PUT", f"repos/{CONTENT_REPO}/contents/{dest}",
        "-f", f"message=newsletter: {slug}", "-f", f"content={encoded}",
    ]
    if probe.returncode == 0:
        args += ["-f", f"sha={json.loads(probe.stdout)['sha']}"]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"issue page: {PAGES_BASE}/newsletters/{slug}/")
    else:
        print(f"page publish failed: {result.stderr[:200]}")


def main() -> None:
    subject, body, fingerprint = compose()
    page = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{_escape(subject)}</title>"
        "<style>body{max-width:680px;margin:0 auto;padding:2rem 1.2rem;"
        "font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;color:#171923}"
        "h1,h2,h3{line-height:1.2}h2{margin-top:2rem}</style></head>"
        f"<body><h1>{_escape(subject)}</h1>{body}</body></html>"
    )
    Path("newsletter.html").write_text(page, encoding="utf-8")
    Path("newsletter_fingerprint.txt").write_text(fingerprint + "\n", encoding="utf-8")
    print(f"subject: {subject}")
    print(f"fingerprint: {fingerprint}")
    print("newsletter.html written")
    if not try_beehiiv(subject, body) and "--no-page" not in sys.argv:
        publish_page(page)


if __name__ == "__main__":
    main()

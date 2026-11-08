#!/usr/bin/env python3
"""Dynamic Already Here LLC revenue-intelligence newsletter.

The composer reads current pipeline artifacts, builds a dated issue with
source-specific calls to action, refuses to silently reuse stale content, and
falls back to an honest "no verified new opportunities" notice instead of
repeating generic marketing copy.

Delivery:
  1. Resend broadcast to the newsletter audience (RESEND_API_KEY) — the
     actual email send. Beehiiv's create-post API is Enterprise-only
     (403 SEND_API_NOT_ENTERPRISE_PLAN) and is no longer attempted.
  2. GitHub Pages issue page — permanent web archive, always attempted.
  3. newsletter.html artifact of record, always written.

Usage:
  python scripts/make_newsletter.py compose [--out issue.json]
      Build the issue and write a JSON payload (dataDate, opportunities,
      signals, fingerprint, previous issue) for scripts/newsletter-guard.mjs.
  python scripts/make_newsletter.py deliver --issue issue.json --decision send|brief [--no-page]
      Send a guard-approved issue. Any other decision is refused.
  python scripts/make_newsletter.py [--no-page]
      Legacy one-shot compose + deliver (no guard).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))  # for the runtime pkg
from generate_shorts import ai_complete  # noqa: E402
from youtube_publication import verified_youtube_uploads  # noqa: E402

CONTENT_REPO = "quantam101/content"
FEATURED_INDEX = "newsletters/featured-products.json"
LAST_ISSUE_INDEX = "newsletters/last-issue.json"
SOURCE_RUNS_FILE = "source_runs.json"   # written by the workflow's sourcing step
ISSUE_SCHEMA = "already-here-issue/1"
SENDABLE_DECISIONS = ("send", "brief")
PAGES_BASE = "https://quantam101.github.io/content"
_UTM = "utm_source=newsletter&utm_medium=email&utm_campaign=weekly-digest"
EBOOK_URL = f"{PAGES_BASE}/ebooks/zero-dollar-content-engine/?{_UTM}"
BLUEPRINT_URL = f"{PAGES_BASE}/ebooks/blueprint/?{_UTM}"
WEBSITE_URL = "https://www.alreadyherellc.com"
AI_SERVICE_URL = f"{WEBSITE_URL}/ai-agent?{_UTM}"
RFQ_URL = f"{WEBSITE_URL}/rfq?{_UTM}"
DISPATCH_URL = f"{WEBSITE_URL}/dispatch?{_UTM}"
GUMROAD_STORE_URL = "https://alreadyhere.gumroad.com?utm_source=newsletter&utm_medium=email&utm_campaign=weekly-digest&utm_content=store"
# no /autoworks page exists yet — route AutoWorks CTAs to the dispatch page
AUTOWORKS_URL = f"{WEBSITE_URL}/dispatch?{_UTM}"

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
    "New digital products": ("View the store", GUMROAD_STORE_URL),
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


def _read_content_json(path: str) -> tuple[Any, str | None]:
    """(parsed JSON, blob sha) for a file in the content repo; (None, None) if absent."""
    try:
        probe = subprocess.run(
            ["gh", "api", f"repos/{CONTENT_REPO}/contents/{path}"],
            capture_output=True, text=True, timeout=60)
        if probe.returncode != 0:
            return None, None
        doc = json.loads(probe.stdout)
        return json.loads(base64.b64decode(doc["content"]).decode()), doc.get("sha")
    except Exception:
        return None, None


def _write_content_json(path: str, payload: Any, sha: str | None, message: str) -> bool:
    encoded = base64.b64encode(json.dumps(payload, indent=2, sort_keys=True).encode()).decode()
    args = ["gh", "api", "-X", "PUT", f"repos/{CONTENT_REPO}/contents/{path}",
            "-f", f"message={message}", "-f", f"content={encoded}"]
    if sha:
        args += ["-f", f"sha={sha}"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"{path} update failed: {result.stderr[:200]}")
    return result.returncode == 0


def _featured_slugs() -> set[str]:
    """Slugs already featured in a prior issue, persisted in the content repo."""
    data, _sha = _read_content_json(FEATURED_INDEX)
    return set(data if isinstance(data, list) else [])


def _record_featured(slugs: list[str]) -> None:
    """Append this issue's featured slugs to the persistent index."""
    if not slugs:
        return
    prior, sha = _read_content_json(FEATURED_INDEX)
    merged = sorted(set(prior if isinstance(prior, list) else []) | set(slugs))
    _write_content_json(FEATURED_INDEX, merged, sha,
                        "newsletter: update featured product index")


def _previous_issue() -> dict[str, Any]:
    """Record of the last issue actually emailed (fingerprint, dataDate, sentAt)."""
    data, _sha = _read_content_json(LAST_ISSUE_INDEX)
    return data if isinstance(data, dict) else {}


def _record_last_issue(record: dict[str, Any]) -> None:
    _prior, sha = _read_content_json(LAST_ISSUE_INDEX)
    _write_content_json(LAST_ISSUE_INDEX, record, sha,
                        f"newsletter: last issue {record.get('dataDate', '')}")


def _data_date() -> str | None:
    """YYYY-MM-DD of the newest pipeline run the artifacts came from.

    The workflow records every source run it downloaded in source_runs.json;
    ISSUE_DATA_DATE overrides for manual runs. None means the issue has no
    provable data date and the guard must refuse it.
    """
    dates: list[str] = []
    for run in _as_items(_load_json(SOURCE_RUNS_FILE)):
        created = str(run.get("created_at") or run.get("createdAt") or "")[:10]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", created):
            dates.append(created)
    override = os.getenv("ISSUE_DATA_DATE", "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", override):
        dates.append(override)
    return max(dates) if dates else None


def _product_items(limit: int = 3) -> list[dict[str, Any]]:
    """Newly generated, actually-listed technical products from the latest run.

    The workflow downloads the run's artifact tree into the workspace, so each
    product lands under technical-products/<slug>/product.json (+checkout.json).
    Only products carrying a real listing URL are featured — the pipeline runs
    with publish:false, so unlisted products are never linked to the store.
    Slugs already featured in a prior issue are skipped via the persistent
    newsletters/featured-products.json index in the content repo.
    """
    items: list[dict[str, Any]] = []
    root = Path("technical-products")
    if not root.is_dir():
        return items
    seen = _featured_slugs()
    for product_json in sorted(root.glob("*/product.json"), reverse=True):
        slug = product_json.parent.name
        if slug in seen:
            continue
        product = _load_json(str(product_json))
        if not isinstance(product, dict):
            continue
        strategy = product.get("strategy") or {}
        checkout = _load_json(str(product_json.parent / "checkout.json")) or {}
        listing = _first(checkout.get("url"), checkout.get("listing_url"))
        title = _first(strategy.get("title"), checkout.get("title"))
        if not title or not listing:
            continue  # unlisted product — nothing purchasable to send readers to
        price = checkout.get("price_usd") or strategy.get("suggested_price_usd")
        items.append({
            "title": title,
            "_slug": slug,
            "summary": _first(
                strategy.get("storefront_copy"), strategy.get("seo_description"),
                strategy.get("promise"), default="New technical guide from the product pipeline.",
            ) + (f" — ${price}" if price else ""),
            "url": listing,
        })
        if len(items) >= limit:
            break
    return items


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
    products = _product_items()
    if products:
        sections.append(("New digital products", products))
    return sections


def _pipeline_insights() -> list[dict[str, Any]]:
    uploads = _as_items(_load_json("youtube_uploads.json"))
    trending = _as_items(_load_json("trending_topics.json"))[:3]
    verified_uploads = verified_youtube_uploads(uploads)
    unverified_successes = sum(1 for u in uploads if u.get("status") == "success") - len(verified_uploads)
    insights: list[dict[str, Any]] = []
    if verified_uploads:
        count = len(verified_uploads)
        noun = "video" if count == 1 else "videos"
        insights.append({
            "title": f"{count} verified public {noun}",
            "summary": (
                "Each linked upload was independently verified as accessible on YouTube "
                "before inclusion in this issue."
            ),
            "url": "https://www.youtube.com/@alreadyherellc",
        })
    if unverified_successes > 0:
        print(
            f"youtube verification: suppressed {unverified_successes} artifact "
            "success record(s) that could not be independently verified public"
        )
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


def compose(
    sections: list[tuple[str, list[dict[str, Any]]]] | None = None,
    insights: list[dict[str, Any]] | None = None,
) -> tuple[str, str, str]:
    """Return (subject, HTML body, stable content fingerprint)."""
    issue_date = time.strftime("%B %d, %Y", time.gmtime())
    if sections is None:
        sections = _collect_sections()
    if insights is None:
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

    fingerprint = _data_fingerprint(sections, insights)
    body.append(f"<!-- issue-fingerprint:{fingerprint} -->")
    return subject, "\n".join(body), fingerprint


def _data_fingerprint(sections: Any, insights: Any) -> str:
    """Fingerprint of the issue's *content* only.

    Deliberately excludes the issue date: two issues built from the same
    artifacts on different days are the same issue, and the guard must be able
    to see that.
    """
    canonical = json.dumps({"sections": sections, "insights": insights},
                           sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def build_issue() -> dict[str, Any]:
    """Compose the issue and return the guard payload."""
    sections = _collect_sections()
    insights = _pipeline_insights()
    subject, body, fingerprint = compose(sections, insights)
    opportunities = [
        {
            "section": title,
            "title": _item_title(item),
            "url": _item_url(item, CTA_BY_SECTION[title][1]),
        }
        for title, items in sections for item in items
    ]
    signals = [{"title": i["title"], "url": i["url"]} for i in insights]
    featured = [
        i["_slug"] for title, items in sections
        if title == "New digital products" for i in items if i.get("_slug")
    ]
    return {
        "schema": ISSUE_SCHEMA,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataDate": _data_date(),
        "subject": subject,
        "html": body,
        "fingerprint": fingerprint,
        "opportunities": opportunities,
        "signals": signals,
        "featuredSlugs": featured,
        "previous": _previous_issue(),
    }


def try_resend(subject: str, body: str) -> bool:
    """Send the issue as a Resend broadcast (the real email delivery)."""
    if not os.getenv("RESEND_API_KEY", "").strip():
        print("no RESEND_API_KEY — email send skipped")
        return False
    try:
        from runtime.resend_newsletter import publish_digest
        result = publish_digest(subject, body)
        if result.ok:
            print(f"resend broadcast sent: id={result.post_id}")
            return True
        print(f"resend broadcast failed: {result.error[:200]}")
    except Exception as exc:
        print(f"resend send failed ({str(exc)[:150]})")
    return False


def publish_page(html_page: str) -> None:
    slug = time.strftime("%Y-%m-%d", time.gmtime())
    dest = f"newsletters/{slug}/index.html"
    encoded = base64.b64encode(html_page.encode()).decode()
    probe = subprocess.run(
        ["gh", "api", f"repos/{CONTENT_REPO}/contents/{dest}"],
        capture_output=True, text=True, timeout=60,
    )
    args = [
        "gh", "api", "-X", "PUT", f"repos/{CONTENT_REPO}/contents/{dest}",
        "-f", f"message=newsletter: {slug}", "-f", f"content={encoded}",
    ]
    if probe.returncode == 0:
        args += ["-f", f"sha={json.loads(probe.stdout)['sha']}"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print(f"issue page: {PAGES_BASE}/newsletters/{slug}/")
    else:
        print(f"page publish failed: {result.stderr[:200]}")


def _page_html(subject: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{_escape(subject)}</title>"
        "<style>body{max-width:680px;margin:0 auto;padding:2rem 1.2rem;"
        "font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;color:#171923}"
        "h1,h2,h3{line-height:1.2}h2{margin-top:2rem}</style></head>"
        f"<body><h1>{_escape(subject)}</h1>{body}</body></html>"
    )


def deliver(issue: dict[str, Any], decision: str, *, page: bool = True) -> bool:
    """Email a guard-approved issue; archive it; record what was sent.

    Returns True only when the broadcast was actually sent. A refused decision
    is a hard error — the guard, not the sender, decides what goes out.
    """
    if decision not in SENDABLE_DECISIONS:
        raise SystemExit(f"refusing to deliver: decision={decision!r} is not one of "
                         f"{SENDABLE_DECISIONS}")
    if issue.get("schema") != ISSUE_SCHEMA or not issue.get("dataDate"):
        raise SystemExit("refusing to deliver: issue payload is not a guard-validated "
                         f"{ISSUE_SCHEMA} document with a dataDate")
    subject, body = str(issue["subject"]), str(issue["html"])
    html_page = _page_html(subject, body)
    Path("newsletter.html").write_text(html_page, encoding="utf-8")
    Path("newsletter_fingerprint.txt").write_text(str(issue["fingerprint"]) + "\n", encoding="utf-8")
    print(f"subject: {subject}")
    print(f"decision: {decision}  dataDate: {issue['dataDate']}  fingerprint: {issue['fingerprint']}")
    sent = try_resend(subject, body)
    if page:
        publish_page(html_page)   # web archive, regardless of email outcome
    if sent:
        _record_featured([s for s in issue.get("featuredSlugs", []) if isinstance(s, str)])
        _record_last_issue({
            "schema": ISSUE_SCHEMA,
            "decision": decision,
            "dataDate": issue["dataDate"],
            "fingerprint": issue["fingerprint"],
            "subject": subject,
            "sentAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "opportunities": len(issue.get("opportunities", [])),
            "signals": len(issue.get("signals", [])),
        })
    else:
        print("::error::issue was NOT emailed — page archive only")
    return sent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-page", action="store_true", help="skip the web archive")
    sub = parser.add_subparsers(dest="command")
    p_compose = sub.add_parser("compose", help="write the guard payload")
    p_compose.add_argument("--out", default="issue.json")
    p_deliver = sub.add_parser("deliver", help="send a guard-approved issue")
    p_deliver.add_argument("--issue", default="issue.json")
    p_deliver.add_argument("--decision", required=True)
    p_deliver.add_argument("--no-page", action="store_true", dest="no_page_sub")
    args = parser.parse_args(argv)
    no_page = args.no_page or getattr(args, "no_page_sub", False)

    if args.command == "compose":
        issue = build_issue()
        Path(args.out).write_text(json.dumps(issue, indent=2, sort_keys=True), encoding="utf-8")
        print(f"issue payload: {args.out}  dataDate={issue['dataDate']}  "
              f"opportunities={len(issue['opportunities'])}  signals={len(issue['signals'])}  "
              f"fingerprint={issue['fingerprint']}")
        return 0
    if args.command == "deliver":
        issue = _load_json(args.issue)
        if not isinstance(issue, dict):
            raise SystemExit(f"refusing to deliver: {args.issue} is not a JSON object")
        return 0 if deliver(issue, args.decision, page=not no_page) else 1
    # legacy one-shot path (no guard)
    issue = build_issue()
    return 0 if deliver(issue, "send", page=not no_page) else 1


if __name__ == "__main__":
    raise SystemExit(main())

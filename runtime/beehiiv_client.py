"""
Beehiiv Newsletter Client — Income Stream 8
============================================
Publishes AI-generated daily digests to Beehiiv, manages subscriber
automations, and tracks paid subscription conversions.

Revenue model:
  Free tier  → ad-supported digest (auto-published daily)
  Premium    → paid subscription via Beehiiv native billing ($7–$15/mo)
  Sponsorship → inject sponsor block into every 5th issue

Environment variables:
  BEEHIIV_API_KEY          — Bearer token from app.beehiiv.com → Settings → API
  BEEHIIV_PUBLICATION_ID   — from same page (starts with pub_)
  BEEHIIV_SPONSOR_NAME     — Optional sponsor name injected every 5th issue
  BEEHIIV_SPONSOR_URL      — Optional sponsor link
  BEEHIIV_SPONSOR_COPY     — Optional sponsor ad copy (≤ 150 chars)

API reference: https://developers.beehiiv.com/docs/v2
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .resilience import urlopen_with_retries

logger = logging.getLogger("BeehiivClient")

_BASE = "https://api.beehiiv.com/v2"
_ISSUE_COUNTER_FILE = os.path.join(
    os.environ.get("PROFITENGINE_CORE_DIR", ".core_mesh_data"),
    "beehiiv_issue_counter.json",
)


# ── Config ─────────────────────────────────────────────────────────────────────

def _api_key() -> str:
    return os.environ.get("BEEHIIV_API_KEY", "").strip()

def _pub_id() -> str:
    return os.environ.get("BEEHIIV_PUBLICATION_ID", "").strip()

def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ── Data models ────────────────────────────────────────────────────────────────

@dataclass
class NewsletterIssue:
    subject:    str
    body_html:  str
    body_text:  str
    preview:    str                    # 90-char preview shown in inbox
    tags:       List[str] = field(default_factory=list)
    send_now:   bool = True
    audience:   str = "free"          # "free" | "premium" | "all"


@dataclass
class BeehiivResult:
    ok:         bool
    post_id:    str = ""
    web_url:    str = ""
    status:     str = ""
    error:      str = ""


# ── Issue counter (sponsor injection every 5th issue) ──────────────────────────

def _load_counter() -> int:
    try:
        with open(_ISSUE_COUNTER_FILE) as f:
            return int(json.load(f).get("count", 0))
    except (FileNotFoundError, ValueError):
        return 0


def _save_counter(n: int) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(_ISSUE_COUNTER_FILE)), exist_ok=True)
    with open(_ISSUE_COUNTER_FILE, "w") as f:
        json.dump({"count": n, "updated": datetime.now(timezone.utc).isoformat()}, f)


# ── Sponsor block ──────────────────────────────────────────────────────────────

def _sponsor_html() -> str:
    name = os.environ.get("BEEHIIV_SPONSOR_NAME", "").strip()
    url  = os.environ.get("BEEHIIV_SPONSOR_URL",  "").strip()
    copy = os.environ.get("BEEHIIV_SPONSOR_COPY", "").strip()
    if not (name and url):
        return ""
    copy_line = f"<p>{copy}</p>" if copy else ""
    return (
        f'<hr style="margin:32px 0;border:1px solid #e5e7eb;">'
        f'<p style="font-size:11px;color:#6b7280;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:4px;">SPONSOR</p>'
        f'<p><strong><a href="{url}">{name}</a></strong></p>'
        f'{copy_line}'
        f'<hr style="margin:32px 0;border:1px solid #e5e7eb;">'
    )


# ── HTML builder ───────────────────────────────────────────────────────────────

_FTC = (
    '<p style="font-size:11px;color:#6b7280;margin-top:40px;">'
    "This newsletter may contain affiliate links. Already Here LLC earns a commission "
    "on qualifying purchases at no extra cost to you. "
    "<a href='https://alreadyherellc.com/disclosure'>FTC Disclosure</a></p>"
)

_STYLE = (
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
    "max-width:600px;margin:0 auto;color:#111827;"
)


def build_digest_html(
    headline: str,
    sections: List[Dict[str, str]],   # [{"heading": ..., "body": ...}]
    cta_url: str = "https://alreadyherellc.com",
    cta_label: str = "Read more →",
    include_sponsor: bool = True,
) -> tuple[str, str]:
    """
    Build (html, plain_text) for a digest issue.
    Injects sponsor every 5th issue automatically.
    """
    issue_n = _load_counter() + 1
    _save_counter(issue_n)
    sponsor = _sponsor_html() if (include_sponsor and issue_n % 5 == 0) else ""

    section_html = ""
    section_text = ""
    for s in sections:
        h = s.get("heading", "")
        b = s.get("body", "")
        section_html += (
            f'<h2 style="font-size:18px;margin:28px 0 8px;">{h}</h2>'
            f'<p style="line-height:1.7;margin:0 0 20px;">{b}</p>'
        )
        section_text += f"\n\n{h}\n{b}"

    html = f"""<!DOCTYPE html>
<html><body style="{_STYLE}">
<h1 style="font-size:24px;font-weight:700;margin-bottom:4px;">{headline}</h1>
<p style="font-size:12px;color:#6b7280;margin-top:0;">Issue #{issue_n} · Already Here LLC</p>
{sponsor}
{section_html}
<p style="margin-top:32px;">
  <a href="{cta_url}" style="background:#111827;color:#fff;padding:12px 24px;
     border-radius:6px;text-decoration:none;font-weight:600;">{cta_label}</a>
</p>
{_FTC}
</body></html>"""

    plain = (
        f"{headline}\nIssue #{issue_n} · Already Here LLC\n"
        f"{section_text}\n\n{cta_url}\n\n"
        "This newsletter may contain affiliate links. FTC Disclosure: https://alreadyherellc.com/disclosure"
    )

    return html, plain


# ── API client ─────────────────────────────────────────────────────────────────

def _http_post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    import urllib.request, urllib.error
    key = _api_key()
    pub = _pub_id()
    if not key or not pub:
        return {"error": "BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID not set"}
    url  = f"{_BASE}/{path}"
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urlopen_with_retries(req, timeout=20, label=f"beehiiv POST {path}") as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}"}
    except Exception as exc:
        return {"error": str(exc)}


def _http_get(path: str) -> Dict[str, Any]:
    import urllib.request, urllib.error
    key = _api_key()
    pub = _pub_id()
    if not key or not pub:
        return {"error": "credentials missing"}
    url  = f"{_BASE}/{path}"
    req  = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urlopen_with_retries(req, timeout=15, label=f"beehiiv GET {path}") as r:
            return json.loads(r.read())
    except Exception as exc:
        return {"error": str(exc)}


# ── Public API ─────────────────────────────────────────────────────────────────

def publish_post(issue: NewsletterIssue) -> BeehiivResult:
    """
    Create and optionally send a Beehiiv post.
    Returns BeehiivResult with post_id and web_url on success.
    """
    pub = _pub_id()
    if not pub:
        return BeehiivResult(ok=False, error="BEEHIIV_PUBLICATION_ID not set")

    payload: Dict[str, Any] = {
        # Beehiiv posts API requires "title" (400 NOT_EXIST_REQUIRED_KEY
        # without it); legacy keys kept for backward/forward compatibility.
        "title":        issue.subject,
        "subtitle":     issue.preview[:90],
        "subject":      issue.subject,
        "preview_text": issue.preview[:90],
        "content_html": issue.body_html,
        "content_text": issue.body_text,
        "status":       "confirmed" if issue.send_now else "draft",
        "send_at":      None,
        "audience":     issue.audience,
    }
    if issue.tags:
        payload["tags"] = issue.tags[:10]

    resp = _http_post(f"publications/{pub}/posts", payload)
    if "error" in resp:
        logger.error(f"[Beehiiv] publish failed: {resp['error']}")
        return BeehiivResult(ok=False, error=resp["error"])

    data    = resp.get("data", {})
    post_id = data.get("id", "")
    web_url = data.get("web_url", "")
    status  = data.get("status", "")
    logger.info(f"[Beehiiv] Published post={post_id} status={status} url={web_url}")
    return BeehiivResult(ok=True, post_id=post_id, web_url=web_url, status=status)


def get_subscribers(limit: int = 100) -> Dict[str, Any]:
    """Return subscriber list with free/premium breakdown."""
    pub  = _pub_id()
    resp = _http_get(f"publications/{pub}/subscriptions?limit={min(limit, 100)}")
    if "error" in resp:
        return {"ok": False, "error": resp["error"]}
    data  = resp.get("data", [])
    free  = sum(1 for s in data if s.get("tier") == "free")
    paid  = sum(1 for s in data if s.get("tier") == "premium")
    return {
        "ok":    True,
        "total": len(data),
        "free":  free,
        "paid":  paid,
        "mrr_estimate_usd": paid * 9,   # $9/mo average
    }


def get_stats() -> Dict[str, Any]:
    """Publication-level stats: subscribers, posts, open rate."""
    pub  = _pub_id()
    resp = _http_get(f"publications/{pub}")
    if "error" in resp:
        return {"ok": False, "error": resp["error"]}
    data = resp.get("data", {})
    return {
        "ok":                True,
        "publication_id":    pub,
        "name":              data.get("name", ""),
        "total_subscribers": data.get("total_active_subscriptions", 0),
        "web_subscribers":   data.get("total_active_web_subscriptions", 0),
    }


def publish_digest_from_sections(
    headline: str,
    sections: List[Dict[str, str]],
    tags: Optional[List[str]] = None,
    cta_url: str = "https://alreadyherellc.com",
) -> BeehiivResult:
    """
    One-call convenience: build HTML + publish.
    Used by the daily content pipeline.
    """
    html, text = build_digest_html(headline, sections, cta_url=cta_url)
    preview    = sections[0].get("body", headline)[:90] if sections else headline[:90]
    issue = NewsletterIssue(
        subject   = headline,
        body_html = html,
        body_text = text,
        preview   = preview,
        tags      = tags or ["ai", "automation", "income"],
        send_now  = True,
    )
    return publish_post(issue)

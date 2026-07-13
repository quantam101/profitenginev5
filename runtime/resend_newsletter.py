"""
Resend Broadcasts newsletter client (income stream 8).

Replaces Beehiiv API publishing, which is gated behind their Enterprise plan
(403 SEND_API_NOT_ENTERPRISE_PLAN, discovered 2026-07-13). Resend broadcasts
are available on the free tier and the alreadyherellc.com domain is already
verified in Resend (the uptime alerts send through it).

Env:
  RESEND_API_KEY          — required
  RESEND_AUDIENCE_ID      — optional; discovered/created by name when unset
  NEWSLETTER_FROM         — default "Already Here <dispatch@alreadyherellc.com>"
  NEWSLETTER_SEED_EMAIL   — contact added when the audience is first created
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("resend_newsletter")

_BASE = "https://api.resend.com"
_AUDIENCE_NAME = "Already Here Newsletter"


def _key() -> str:
    return os.environ.get("RESEND_API_KEY", "").strip()


def _request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    req = urllib.request.Request(
        f"{_BASE}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {_key()}",
            "Content-Type": "application/json",
            # Cloudflare 403s the default Python-urllib agent (error 1010)
            "User-Agent": "already-here-llc-newsletter/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail[:300]}") from None


def ensure_audience() -> str:
    """Return the newsletter audience id, creating the audience if needed."""
    env_id = os.environ.get("RESEND_AUDIENCE_ID", "").strip()
    if env_id:
        return env_id
    listing = _request("GET", "/audiences")
    for aud in listing.get("data", []):
        if aud.get("name") == _AUDIENCE_NAME:
            return aud["id"]
    created = _request("POST", "/audiences", {"name": _AUDIENCE_NAME})
    audience_id = created["id"]
    seed = os.environ.get("NEWSLETTER_SEED_EMAIL", "dispatch@alreadyherellc.com").strip()
    if seed:
        try:
            subscribe(seed, audience_id=audience_id)
        except RuntimeError as exc:
            logger.warning("seed subscribe failed: %s", exc)
    logger.info("created Resend audience %s (%s)", _AUDIENCE_NAME, audience_id)
    return audience_id


def subscribe(email: str, first_name: str = "", audience_id: Optional[str] = None) -> Dict[str, Any]:
    """Add a contact to the newsletter audience (idempotent on Resend's side)."""
    aud = audience_id or ensure_audience()
    return _request("POST", f"/audiences/{aud}/contacts", {
        "email": email,
        "first_name": first_name or None,
        "unsubscribed": False,
    })


@dataclass
class BroadcastResult:
    ok: bool
    post_id: str = ""
    web_url: str = ""
    status: str = ""
    error: str = ""


_FOOTER = (
    '<hr style="margin-top:32px;border:none;border-top:1px solid #ddd">'
    '<p style="font-size:12px;color:#888">Already Here LLC — '
    '<a href="https://alreadyherellc.com">alreadyherellc.com</a> · '
    '<a href="{{{RESEND_UNSUBSCRIBE_URL}}}">Unsubscribe</a></p>'
)


def publish_digest(subject: str, body_html: str, body_text: str = "") -> BroadcastResult:
    """Create and send a broadcast to the newsletter audience."""
    if not _key():
        return BroadcastResult(ok=False, error="RESEND_API_KEY not set")
    try:
        audience_id = ensure_audience()
        created = _request("POST", "/broadcasts", {
            "audience_id": audience_id,
            "from": os.environ.get("NEWSLETTER_FROM",
                                   "Already Here <dispatch@alreadyherellc.com>"),
            "subject": subject,
            "html": body_html + _FOOTER,
            "text": body_text or None,
            "name": subject[:80],
        })
        broadcast_id = created.get("id", "")
        _request("POST", f"/broadcasts/{broadcast_id}/send", {})
        logger.info("broadcast sent id=%s subject=%r", broadcast_id, subject)
        return BroadcastResult(ok=True, post_id=broadcast_id, status="sent")
    except RuntimeError as exc:
        logger.error("broadcast failed: %s", exc)
        return BroadcastResult(ok=False, error=str(exc))


def audience_stats() -> Dict[str, Any]:
    """Contact counts for the newsletter audience."""
    if not _key():
        return {"ok": False, "error": "RESEND_API_KEY not set"}
    try:
        aud = ensure_audience()
        contacts = _request("GET", f"/audiences/{aud}/contacts").get("data", [])
        active = [c for c in contacts if not c.get("unsubscribed")]
        return {"ok": True, "provider": "resend", "audience_id": aud,
                "total_subscribers": len(active),
                "unsubscribed": len(contacts) - len(active)}
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

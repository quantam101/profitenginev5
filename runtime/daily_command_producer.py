"""
Daily Command event producer.

Emits HMAC-signed events to daily-command-os (the operator control plane)
so detected opportunities, system failures, and leads land in the approval
queue. No-op when DC_WEBHOOK_URL / WEBHOOK_SECRET are unset, so profitenginev5
runs unchanged until Daily Command is wired.

Env:
  DC_WEBHOOK_URL   — e.g. https://daily-command-os.vercel.app/api/events/webhook
  WEBHOOK_SECRET   — shared HMAC secret (same value as in daily-command-os)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger("dc_producer")


def _config() -> Optional[tuple[str, str]]:
    url = os.environ.get("DC_WEBHOOK_URL", "").strip()
    secret = os.environ.get("WEBHOOK_SECRET", "").strip()
    if not url or not secret:
        return None
    return url, secret


def emit(event_type: str, data: Dict[str, Any], *,
         source: str = "profitenginev5",
         idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """Send one signed event. Returns {ok, ...}; never raises (fail-soft)."""
    cfg = _config()
    if cfg is None:
        return {"ok": False, "skipped": True, "reason": "DC not configured"}
    url, secret = cfg
    payload: Dict[str, Any] = {"event_type": event_type, "source": source, "data": data}
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    body = json.dumps(payload).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "x-dc-signature": sig,
        "User-Agent": "profitenginev5-producer/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        logger.warning("DC emit %s -> HTTP %s: %s", event_type, exc.code, detail[:200])
        return {"ok": False, "error": f"HTTP {exc.code}: {detail[:200]}"}
    except Exception as exc:
        logger.warning("DC emit %s failed: %s", event_type, exc)
        return {"ok": False, "error": str(exc)}


def emit_opportunity(*, company: str, grade: str = "C",
                     external_id: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
    """Convenience wrapper for revenue_opportunity.detected.

    None-valued fields are dropped: the DC webhook's Zod contract wants
    optional fields absent, not null (null -> 422 schema validation failed)."""
    data = {"company": company, "grade": grade,
            **{k: v for k, v in fields.items() if v is not None}}
    if external_id:
        data["external_id"] = external_id
    return emit("revenue_opportunity.detected", data, idempotency_key=external_id)


def emit_system_failed(*, service: str, severity: str = "critical",
                       blocking_revenue: bool = True, error: str = "",
                       external_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper for revenue_system.failed."""
    data: Dict[str, Any] = {
        "service": service, "severity": severity,
        "blocking_revenue": blocking_revenue, "error": error,
    }
    if external_id:
        data["external_id"] = external_id
    return emit("revenue_system.failed", data, idempotency_key=external_id)

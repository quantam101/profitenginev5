"""
Daily Command event producer.

Emits HMAC-signed events to daily-command-os (the operator control plane)
so detected opportunities, system failures, and leads land in the approval
queue. No-op when DC_WEBHOOK_URL / WEBHOOK_SECRET are unset, so profitenginev5
runs unchanged until Daily Command is wired.

Events that fail delivery after bounded retries are appended to a local
outbox (JSONL). Every subsequent emit first drains the outbox, so a DC
outage or network partition delays events instead of dropping them —
failover is part of the producer, not an afterthought.

Env:
  DC_WEBHOOK_URL   — e.g. https://daily-command-os.vercel.app/api/events/webhook
  WEBHOOK_SECRET   — shared HMAC secret (same value as in daily-command-os)
  DC_OUTBOX_PATH   — outbox file (default ./data/dc_outbox.jsonl); set to
                     empty to disable spooling
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from .resilience import classify_exception, urlopen_with_retries

logger = logging.getLogger("dc_producer")

_OUTBOX_MAX_REPLAY = int(os.getenv("DC_OUTBOX_MAX_REPLAY", "50"))


def _config() -> Optional[tuple[str, str]]:
    url = os.environ.get("DC_WEBHOOK_URL", "").strip()
    secret = os.environ.get("WEBHOOK_SECRET", "").strip()
    if not url or not secret:
        return None
    return url, secret


def _outbox_path() -> Optional[Path]:
    raw = os.environ.get("DC_OUTBOX_PATH", "./data/dc_outbox.jsonl").strip()
    return Path(raw) if raw else None


def _spool(event_type: str, data: Dict[str, Any],
           source: str, idempotency_key: Optional[str]) -> None:
    """Append a failed event to the outbox for replay by later emits."""
    path = _outbox_path()
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event_type": event_type,
            "source": source,
            "data": data,
            "idempotency_key": idempotency_key,
            "spooled_at": time.time(),
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        logger.warning("DC emit %s spooled to %s for later replay", event_type, path)
    except Exception as exc:  # never let the safety net take the caller down
        logger.error("DC outbox spool failed: %s", exc)


def _deliver(url: str, secret: str, event_type: str, data: Dict[str, Any],
             source: str, idempotency_key: Optional[str]) -> Dict[str, Any]:
    """POST one signed event with bounded retry on transient failures.

    Returns the parsed response on 2xx; raises HTTPError/URLError otherwise
    so the caller can decide between reporting and spooling.
    """
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
    with urlopen_with_retries(req, timeout=20, label=f"DC emit {event_type}") as r:
        return json.loads(r.read() or b"{}")


def _drain_outbox(url: str, secret: str, limit: int = _OUTBOX_MAX_REPLAY) -> int:
    """Replay queued events, oldest first. Returns count delivered.

    Delivery honors the stored idempotency_key, so an event that actually
    reached DC before a response was lost is deduplicated server-side
    rather than double-counted.
    """
    path = _outbox_path()
    if path is None or not path.exists():
        return 0
    try:
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception as exc:
        logger.error("DC outbox read failed: %s", exc)
        return 0
    if not lines:
        return 0

    delivered = 0
    remaining = lines[:]
    for i, line in enumerate(lines[:limit]):
        try:
            record = json.loads(line)
            _deliver(
                url, secret,
                str(record.get("event_type") or ""),
                dict(record.get("data") or {}),
                str(record.get("source") or "profitenginev5"),
                record.get("idempotency_key"),
            )
            delivered += 1
            remaining.pop(0)
        except Exception as exc:
            # Keep the failed line (and everything after it, to preserve
            # ordering) for the next drain attempt.
            logger.warning("DC outbox replay stopped at %d: %s", i, exc)
            break
    try:
        if remaining:
            path.write_text("\n".join(remaining) + "\n", encoding="utf-8")
        else:
            path.unlink()
    except Exception as exc:
        logger.error("DC outbox rewrite failed: %s", exc)
    if delivered:
        logger.info("DC outbox drained %d queued event(s)", delivered)
    return delivered


def emit(event_type: str, data: Dict[str, Any], *,
         source: str = "profitenginev5",
         idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """Send one signed event. Returns {ok, ...}; never raises (fail-soft).

    Transient failures (timeouts, connection errors, 429, 5xx) are retried
    with backoff; a still-failing event is spooled to the local outbox and
    replayed by the next emit, so an outage delays delivery instead of
    silently dropping revenue events.
    """
    cfg = _config()
    if cfg is None:
        return {"ok": False, "skipped": True, "reason": "DC not configured"}
    url, secret = cfg
    try:
        result = _deliver(url, secret, event_type, data, source, idempotency_key)
        _drain_outbox(url, secret)
        return result
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        logger.warning("DC emit %s -> HTTP %s: %s", event_type, exc.code, detail[:200])
        # Only transient failures belong in the outbox — a 4xx (bad payload,
        # dead credential) would replay forever and fail identically every run.
        spooled = classify_exception(exc).retryable
        if spooled:
            _spool(event_type, data, source, idempotency_key)
        return {"ok": False, "error": f"HTTP {exc.code}: {detail[:200]}", "spooled": spooled}
    except Exception as exc:
        logger.warning("DC emit %s failed: %s", event_type, exc)
        _spool(event_type, data, source, idempotency_key)
        return {"ok": False, "error": str(exc), "spooled": True}


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

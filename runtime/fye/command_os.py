"""
Command OS client for FYE — pinned to confirmed contract values:
hex HMAC signature on POST /api/events/webhook, pending-only approvals
list read, and journaled-decision verification via GET /api/approvals/{id}.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from ..daily_command_producer import emit
from .config import FyeConfig

logger = logging.getLogger("fye.command_os")


def request_publish_approval(cfg: FyeConfig, *, package_id: str, title: str,
                             description: str = "", channel: str = "",
                             manifest_url: str = "", duration_s: int = 0,
                             shot_count: int = 0, human_reviewed: bool = False,
                             risk_level: str = "medium") -> Dict[str, Any]:
    """Emit fye.publish_requested → Command OS creates a pending Approval.
    Returns the emit result; the approval id lands in result['id']."""
    if not cfg.dc_configured:
        return {"ok": False, "skipped": True, "reason": "DC not configured"}
    data: Dict[str, Any] = {
        "package_id": package_id,
        "title": title,
        "synthetic_media": True,   # FYE output is always AI-generated.
        "human_reviewed": human_reviewed,
        "risk_level": risk_level,
    }
    if description:
        data["description"] = description[:2000]
    if channel:
        data["channel"] = channel
    if manifest_url:
        data["manifest_url"] = manifest_url
    if duration_s:
        data["duration_s"] = duration_s
    if shot_count:
        data["shot_count"] = shot_count
    return emit("fye.publish_requested", data, source="profitenginev5",
                idempotency_key=f"fye-{package_id}")


def _get_json(url: str, timeout: float = 20.0,
              sign_payload: Optional[str] = None,
              cfg: Optional[FyeConfig] = None) -> Optional[Dict[str, Any]]:
    headers = {
        "User-Agent": "profitenginev5-fye/1.0",
        "Accept": "application/json",
    }
    if sign_payload is not None and cfg is not None and cfg.webhook_secret:
        headers["x-dc-signature"] = hmac.new(
            cfg.webhook_secret.encode(), sign_payload.encode(),
            hashlib.sha256).hexdigest()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as exc:
        logger.warning("DC GET %s -> HTTP %s", url, exc.code)
        return None
    except Exception as exc:
        logger.warning("DC GET %s failed: %s", url, exc)
        return None


def pending_approvals(cfg: FyeConfig) -> Optional[List[Dict[str, Any]]]:
    """Pending-only read: GET /api/approvals returns status=pending only."""
    if not cfg.dc_configured:
        return None
    res = _get_json(f"{cfg.dc_base_url}/api/approvals")
    if res is None:
        return None
    return res.get("approvals", [])


def journaled_decision(cfg: FyeConfig, approval_id: str) -> Optional[Dict[str, Any]]:
    """Verify a journaled verdict: GET /api/approvals/{id} returns the full
    record (status approved|rejected|pending|expired, approvedBy, approvedAt)
    once it leaves the pending-only list. None when unreachable/not found."""
    if not cfg.dc_configured or not approval_id:
        return None
    res = _get_json(f"{cfg.dc_base_url}/api/approvals/{approval_id}",
                    sign_payload=approval_id, cfg=cfg)
    if res is None:
        return None
    return res.get("approval")


def job_events(cfg: FyeConfig, job_id: str) -> Optional[List[Dict[str, Any]]]:
    """Journaled lifecycle events for one FYE job, oldest-first:
    GET /api/events?type=fye.job_event&job_id=<id>, signed like the
    approvals read (HMAC of the job_id). The worker emits these from the
    runner, so this is the control plane's read-back channel."""
    if not cfg.dc_configured or not job_id:
        return None
    res = _get_json(
        f"{cfg.dc_base_url}/api/events?type=fye.job_event&job_id={job_id}",
        sign_payload=job_id, cfg=cfg)
    if res is None:
        return None
    return res.get("events", [])


def pending_package_ids(cfg: FyeConfig) -> Optional[List[str]]:
    """Pending FYE package ids, derived from approval targets `fye:<id>`."""
    rows = pending_approvals(cfg)
    if rows is None:
        return None
    return [
        r["target"][4:]
        for r in rows
        if str(r.get("target", "")).startswith("fye:")
    ]

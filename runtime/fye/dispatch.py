"""
Authenticated GitHub Actions dispatch for FYE jobs.

Replaces the retired merge/push trigger: an approved Command OS decision
produces an immutable job record, then this module fires
``workflow_dispatch`` carrying job_id + approval_id + payload_hash. The
worker re-verifies all three before rendering — the git push surface can
no longer authorize a production run.

Credential: FYE_DISPATCH_TOKEN — a fine-grained PAT or GitHub App
installation token with ONLY the Actions:write repository permission on
the dispatch repo. Anything broader is out of policy.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .config import FyeConfig
from .jobs import JobError, canonical_payload, payload_hash

logger = logging.getLogger("fye.dispatch")

_API = "https://api.github.com"


def dispatch_inputs(fields: Dict[str, Any]) -> Dict[str, str]:
    """workflow_dispatch inputs are strings; encode the render params."""
    p = canonical_payload(fields)
    return {k: json.dumps(v) if isinstance(v, (dict, list))
            else str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in p.items()}


def dispatch_job(cfg: FyeConfig, job: Dict[str, Any]) -> Dict[str, Any]:
    """POST /repos/{repo}/actions/workflows/{wf}/dispatches.

    Fail-closed: without a dispatch token or an APPROVED job this is a
    refusal, never a silent local run."""
    if not cfg.dispatch_token:
        return {"ok": False, "error": "FYE_DISPATCH_TOKEN not configured"}
    if job.get("status") not in ("APPROVED", "QUEUED"):
        return {"ok": False, "error":
                f"job {job.get('job_id')} is {job.get('status')}, not approved"}

    inputs = dispatch_inputs(job.get("payload", {}))
    inputs.update({
        "job_id": job["job_id"],
        "approval_id": job.get("approval_id", ""),
        "payload_hash": job["payload_hash"],
    })
    body = json.dumps({"ref": cfg.dispatch_ref, "inputs": inputs}).encode()
    url = (f"{_API}/repos/{cfg.dispatch_repo}/actions/workflows/"
           f"{cfg.dispatch_workflow}/dispatches")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {cfg.dispatch_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "profitenginev5-fye-dispatch/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            # 204 No Content on success.
            return {"ok": True, "status": r.status, "job_id": job["job_id"]}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        logger.warning("dispatch HTTP %s: %s", exc.code, detail[:200])
        return {"ok": False,
                "error": f"HTTP {exc.code}: {detail[:200]}"}
    except Exception as exc:
        logger.warning("dispatch failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def verify_dispatch_request(cfg: FyeConfig, job_store: Any, *,
                            job_id: str, approval_id: str,
                            expected_hash: str,
                            fields: Dict[str, Any],
                            command_os: Optional[Any] = None
                            ) -> Dict[str, Any]:
    """Store-backed fail-closed gate (durable FYE_ROOT deployments).
    Every check must pass before any render work starts."""
    job = job_store.verify_payload(job_id, fields)
    if expected_hash != job["payload_hash"]:
        raise JobError("payload_hash input does not match stored job")
    if approval_id != job.get("approval_id"):
        raise JobError("approval_id input does not match stored job")
    if job_store.is_expired(job):
        try:
            job_store.transition(job_id, "EXPIRED")
        except Exception:
            logger.warning("could not mark job %s expired", job_id)
        raise JobError("job approval expired")
    if int(job.get("attempts", 0)) >= cfg.max_attempts:
        raise JobError("job exceeded retry budget")
    verify_approval(cfg, job_id=job_id, approval_id=approval_id,
                    command_os=command_os)
    return job


def verify_approval(cfg: FyeConfig, *, job_id: str, approval_id: str,
                    command_os: Optional[Any] = None) -> None:
    """The Command OS journaled decision must say 'approved' for the
    target `fye:<job_id>` — the only authorization that counts."""
    if command_os is None:
        from . import command_os as command_os  # noqa: PLC0415
    if not cfg.dc_configured:
        raise JobError("Command OS not configured — failing closed")
    decision = command_os.journaled_decision(cfg, approval_id)
    if decision is None:
        raise JobError("approval decision unavailable — failing closed")
    if decision.get("status") != "approved":
        raise JobError(f"approval {approval_id} is "
                       f"{decision.get('status')}, not approved")
    target = decision.get("target", "")
    if target and target != f"fye:{job_id}":
        raise JobError(f"approval {approval_id} targets {target}, "
                       f"not fye:{job_id}")


def verify_worker_inputs(cfg: FyeConfig, *, job_id: str, approval_id: str,
                         expected_hash: str, fields: Dict[str, Any],
                         command_os: Optional[Any] = None
                         ) -> Dict[str, Any]:
    """Fail-closed gate for stateless workers (the GitHub Actions runner
    has no durable job store): the payload hash must self-verify against
    the dispatched inputs, and Command OS must hold an approved decision
    for exactly this job_id. Returns the recomputed hash record."""
    if not job_id or not approval_id or not expected_hash:
        raise JobError("job_id, approval_id and payload_hash are required")
    recomputed = payload_hash(fields)
    if recomputed != expected_hash:
        raise JobError("payload altered: inputs do not match payload_hash")
    verify_approval(cfg, job_id=job_id, approval_id=approval_id,
                    command_os=command_os)
    return {"job_id": job_id, "payload_hash": recomputed,
            "approval_id": approval_id, "payload": canonical_payload(fields)}

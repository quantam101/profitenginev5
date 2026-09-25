"""
Channel publishing for FYE — separated from rendering by design.

generate/render may produce artifacts automatically after approval;
publish requires its own PUBLISH_APPROVED authorization. A missing or
failed channel credential refuses the publish and must NOT invalidate
the rendered asset or trigger another render.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .config import FyeConfig
from .jobs import FyeJobStore, JobError

logger = logging.getLogger("fye.publish")


class PublishRefused(JobError):
    """Credential missing or channel declined — the job stays READY."""


class ChannelPublisher:
    """Interface: one channel post per job, keyed by publish idempotency."""

    name = "abstract"

    def publish(self, job: Dict[str, Any], *, idempotency_key: str
                ) -> Dict[str, Any]:
        """One channel post per job. Adapters MUST pass idempotency_key
        to the channel's dedupe mechanism where one exists so a retried
        side effect cannot double-post.

        Contract: raise PublishRefused ONLY when no post was attempted
        (missing credential, channel declined before upload). Any other
        exception means the outcome is uncertain — the channel may have
        accepted a post — and the job is held in PUBLISHING, never
        rolled back to a state that would silently retry."""
        raise NotImplementedError

    def lookup(self, idempotency_key: str) -> Optional[str]:
        """Query the channel for a post created under idempotency_key;
        returns its post_id or None when unknown/absent. Adapters whose
        channel supports dedupe lookup implement this to resolve
        uncertain publish results; the default 'I don't know' answer
        keeps the job held rather than risking a second post."""
        return None


class DryRunPublisher(ChannelPublisher):
    """Zero-spend publisher used when FYE_PUBLISH_DRY_RUN=1 — records a
    deterministic post id without touching a channel. Real channel
    adapters implement ChannelPublisher.publish()."""

    name = "dry-run"

    def publish(self, job: Dict[str, Any], *, idempotency_key: str
                ) -> Dict[str, Any]:
        return {"post_id": f"dryrun-{job['job_id']}",
                "channel": job["attribution"].get("channel_id", ""),
                "dry_run": True}


def publisher_for(cfg: FyeConfig) -> ChannelPublisher:
    """Fail-closed adapter selection. A real channel adapter requires its
    own credential (e.g. FYE_YOUTUBE_TOKEN); without one, only the
    explicit dry-run mode is available — no silent fallback."""
    import os
    if os.environ.get("FYE_PUBLISH_DRY_RUN", "").lower() == "true":
        return DryRunPublisher()
    raise PublishRefused(
        "no channel publisher configured — set FYE_PUBLISH_DRY_RUN=1 for "
        "a dry run or provide channel credentials")


def publish_job(cfg: FyeConfig, store: FyeJobStore, job_id: str, *,
                publisher: Optional[ChannelPublisher] = None
                ) -> Dict[str, Any]:
    """Publish one READY→PUBLISH_APPROVED job. Idempotent: a second call
    for an already-PUBLISHED job returns the recorded post — never a
    second channel post."""
    job = store.get(job_id)
    if job is None:
        raise JobError(f"unknown job {job_id}")
    if job["status"] == "PUBLISHED":
        return {"ok": True, "replayed": True,
                "post_id": job["publish"]["post_id"]}
    if store.is_expired(job):
        store.transition(job_id, "EXPIRED")
        raise PublishRefused(f"job {job_id} approval expired")

    pub = publisher if publisher is not None else publisher_for(cfg)

    # A job already in PUBLISHING means an earlier attempt's outcome is
    # uncertain — the channel may have accepted a post whose response
    # was lost. Ask the adapter to resolve it by idempotency key; if it
    # can't, refuse rather than risk a second channel post.
    if job["status"] == "PUBLISHING":
        idem = job["publish"]["idempotency_key"]
        found = pub.lookup(idem)
        if found:
            store.record_publish(job_id, found)
            return {"ok": True, "replayed": True, "post_id": found,
                    "resolved_uncertain": True}
        raise PublishRefused(
            f"job {job_id} has an uncertain publish in flight — adapter "
            "could not confirm or deny the post by idempotency key, "
            "holding PUBLISHING to prevent a duplicate")

    if job["status"] != "PUBLISH_APPROVED":
        raise PublishRefused(
            f"job {job_id} is {job['status']} — publish requires its own "
            "PUBLISH_APPROVED authorization")

    # Single-flight lease BEFORE the channel call: a concurrent caller
    # sees PUBLISHING (handled above), so two callers can never both
    # reach the adapter for the same job.
    lease = store.begin_publish(job_id)
    if lease.get("replayed"):
        return {"ok": True, "replayed": True,
                "post_id": lease["publish"]["post_id"]}
    idem = job["publish"]["idempotency_key"]

    try:
        result = pub.publish(job, idempotency_key=idem)
        post_id = result.get("post_id")
        if not post_id:
            raise PublishRefused("publisher returned no post id")
        store.record_publish(job_id, post_id)
    except PublishRefused:
        # Refused before any channel write — safe to release the lease
        # so a retry with working credentials can re-lease it.
        store.end_publish_failure(job_id, "refused")
        raise
    except Exception as exc:
        # Uncertain outcome: the adapter call may have landed a post.
        # Hold PUBLISHING — the next publish attempt resolves it via
        # lookup() instead of blindly retrying.
        raise PublishRefused(
            f"publish outcome uncertain (held in PUBLISHING): {exc}"
        ) from exc
    return {"ok": True, "post_id": post_id,
            "idempotency_key": idem,
            "dry_run": bool(result.get("dry_run"))}


def published_event(job: Dict[str, Any]) -> Dict[str, Any]:
    """fye.job_event payload carrying the #95 attribution spine:
    asset_id → channel_id → campaign → source."""
    return {
        "job_id": job["job_id"],
        "state": job["status"],
        "asset_id": job["attribution"]["asset_id"],
        "channel_id": job["attribution"].get("channel_id", ""),
        "campaign": job["attribution"].get("campaign", ""),
        "source": job["attribution"].get("source", "fye"),
        "post_id": (job.get("publish") or {}).get("post_id"),
        "artifacts": {k: v.get("sha256") for k, v in
                      (job.get("artifacts") or {}).items()},
        "at": time.time(),
    }

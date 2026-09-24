#!/usr/bin/env python3
"""
FYE worker — runs ONE approved job on the Actions runner.

Fail-closed gate before any render work:
  1. payload_hash must self-verify against the dispatched inputs
     (altered payload -> rejected);
  2. Command OS must hold an approved journaled decision for exactly
     fye:<job_id> (missing/expired/mismatched -> refused);
  3. the job lease must be claimable (one active worker per job_id).

Then render → QA → READY, with artifact SHA256 recorded and every
transition journaled + emitted to Command OS as fye.job_event.

Usage:
  python scripts/fye_worker.py --job-id <id> --approval-id <id> \
      --payload-hash <sha256> --topic "..." [--niche ...]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.daily_command_producer import emit  # noqa: E402
from runtime.fye import FyeOrchestrator, command_os, dispatch  # noqa: E402
from runtime.fye.config import FyeConfig  # noqa: E402
from runtime.fye.jobs import FyeJobStore, JobError  # noqa: E402


def _fields(args: argparse.Namespace) -> dict:
    return {
        "topic": args.topic,
        "niche": args.niche,
        "title": args.title,
        "channel": args.channel,
        "monthly_views_target": args.monthly_views_target,
        "subscribers": args.subscribers,
        "watch_hours": args.watch_hours,
        "shorts_views": args.shorts_views,
        "human_reviewed": args.human_reviewed,
    }


def _emit_state(job: dict, detail: str = "") -> None:
    """Mirror lifecycle into the Command OS audit ledger. Fail-soft —
    the local journal is authoritative."""
    data = {"job_id": job["job_id"], "state": job["status"],
            "asset_id": job.get("attribution", {}).get("asset_id", job["job_id"]),
            "channel_id": job.get("attribution", {}).get("channel_id", ""),
            "campaign": job.get("attribution", {}).get("campaign", ""),
            "source": job.get("attribution", {}).get("source", "fye")}
    if detail:
        data["detail"] = detail[:500]
    emit("fye.job_event", data, source="profitenginev5",
         idempotency_key=f"fye-{job['job_id']}-{job['status']}-"
                         f"{len(job.get('history', []))}")


def main() -> int:
    ap = argparse.ArgumentParser(description="FYE worker")
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--approval-id", required=True)
    ap.add_argument("--payload-hash", required=True)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--niche", default="science-explainer")
    ap.add_argument("--title", default="")
    ap.add_argument("--channel", default="")
    ap.add_argument("--monthly-views-target", type=int, default=100_000)
    ap.add_argument("--subscribers", type=int, default=0)
    ap.add_argument("--watch-hours", type=float, default=0.0)
    ap.add_argument("--shorts-views", type=int, default=0)
    ap.add_argument("--human-reviewed", action="store_true")
    args = ap.parse_args()

    cfg = FyeConfig()
    store = FyeJobStore(cfg)
    worker = os.environ.get("GITHUB_RUN_ID") or f"pid-{os.getpid()}"
    fields = _fields(args)

    try:
        # Stateless gate: hash self-verification + journaled approval.
        dispatch.verify_worker_inputs(
            cfg, job_id=args.job_id, approval_id=args.approval_id,
            expected_hash=args.payload_hash, fields=fields,
            command_os=command_os)

        # Local ledger: on a durable FYE_ROOT this is the control-plane
        # record; on the ephemeral runner it is the run's audit artifact.
        job = store.get(args.job_id) or store.create(
            job_id=args.job_id, approval_id=args.approval_id,
            fields=fields)
        if job["status"] in ("READY", "PUBLISH_APPROVED", "PUBLISHED"):
            # Duplicate dispatch of a finished render — replay, don't redo.
            print(json.dumps({"ok": True, "replayed": True,
                              "status": job["status"],
                              "artifacts": job["artifacts"]}, indent=2))
            return 0
        if not store.claim(args.job_id, worker):
            raise JobError(f"job {args.job_id} lease held by another worker")

        store.transition(args.job_id, "RENDERING")
        _emit_state(store.get(args.job_id))

        orch = FyeOrchestrator(cfg)
        # Resource ceiling: the render must finish inside
        # FYE_RENDER_TIMEOUT_S; an interrupt leaves the job in a
        # recoverable CLAIMED/RENDERING state (lease expiry → re-claim).
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(
                orch.run,
                topic=fields["topic"], niche=fields["niche"],
                title=fields["title"] or "",
                monthly_views_target=fields["monthly_views_target"],
                subscribers=fields["subscribers"],
                watch_hours=fields["watch_hours"],
                shorts_views=fields["shorts_views"],
                human_reviewed=fields["human_reviewed"],
                package_id=args.job_id,
            )
            result = fut.result(timeout=cfg.render_timeout_s)

        if not result.get("ok"):
            raise JobError(f"render failed: {result.get('error') or result.get('issues')}")

        store.transition(args.job_id, "QA")
        master = result["master"]
        # QA gate: artifact exists, is non-trivial, inside size limit,
        # SHA256 pinned into the job record.
        store.record_artifact(args.job_id, master)
        store.transition(args.job_id, "READY")
        _emit_state(store.get(args.job_id), detail="render complete")
        print(json.dumps({"ok": True, "job_id": args.job_id,
                          "status": "READY",
                          "artifacts": store.get(args.job_id)["artifacts"]},
                         indent=2))
        return 0
    except JobError as exc:
        job = store.get(args.job_id)
        if job and job["status"] not in ("FAILED", "EXPIRED",
                                         "REJECTED", "CANCELLED",
                                         "READY", "PUBLISHED"):
            try:
                store.transition(args.job_id, "FAILED", error=str(exc))
                _emit_state(store.get(args.job_id), detail=str(exc))
            except JobError:
                pass
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())

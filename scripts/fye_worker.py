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
import json
import multiprocessing as mp
import os
import shutil
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


def _render_child(q: "mp.Queue", fields: dict, job_id: str) -> None:
    """Subprocess target: run the render and hand the result dict back.
    Fork inherits the parent's env, so FyeConfig() reads identically."""
    from runtime.fye import FyeOrchestrator  # noqa: E402
    from runtime.fye.config import FyeConfig  # noqa: E402
    orch = FyeOrchestrator(FyeConfig())
    try:
        q.put(orch.run(
            topic=fields["topic"], niche=fields["niche"],
            title=fields.get("title") or "",
            monthly_views_target=fields["monthly_views_target"],
            subscribers=fields["subscribers"],
            watch_hours=fields["watch_hours"],
            shorts_views=fields["shorts_views"],
            human_reviewed=fields["human_reviewed"],
            package_id=job_id))
    except Exception as exc:  # report, don't crash silently
        q.put({"ok": False, "error": f"render subprocess: {exc}"})


def _render_killable(fields: dict, job_id: str,
                     timeout_s: int) -> dict:
    """Run the render in a child process with a hard deadline.

    A thread can't be killed — a timed-out render would keep burning the
    Actions timeout while the worker waits on executor shutdown. A
    subprocess is terminated for real; the job stays in a recoverable
    CLAIMED/RENDERING state (lease expiry → re-claim).
    """
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    proc = ctx.Process(target=_render_child,
                       args=(q, fields, job_id))
    proc.start()
    proc.join(timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(10)
        if proc.is_alive():
            proc.kill()
        return {"ok": False,
                "error": f"render exceeded {timeout_s}s — terminated"}
    try:
        return q.get_nowait()
    except Exception:
        return {"ok": False,
                "error": f"render subprocess exited {proc.exitcode} "
                         "with no result"}


def _emit_state(job: dict, detail: str = "") -> None:
    """Mirror lifecycle into the Command OS audit ledger. Fail-soft —
    the local journal is authoritative."""
    data = {"job_id": job["job_id"], "state": job["status"],
            "payload_hash": job.get("payload_hash", ""),
            "asset_id": job.get("attribution", {}).get("asset_id", job["job_id"]),
            "channel_id": job.get("attribution", {}).get("channel_id", ""),
            "campaign": job.get("attribution", {}).get("campaign", ""),
            "source": job.get("attribution", {}).get("source", "fye")}
    if detail:
        data["detail"] = detail[:500]
    if job.get("artifacts"):
        # Carry verified artifact metadata so the control plane can
        # reconcile hashes it will never see on the runner filesystem.
        data["artifacts"] = job["artifacts"]
    emit("fye.job_event", data, source="profitenginev5",
         idempotency_key=f"fye-{job['job_id']}-{job['status']}-"
                         f"{len(job.get('history', []))}")


def main() -> int:
    ap = argparse.ArgumentParser(description="FYE worker")
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--approval-id", required=True)
    ap.add_argument("--payload-hash", required=True)
    ap.add_argument("--payload", default="",
                    help="JSON canonical render payload (from dispatch)")
    ap.add_argument("--topic", default="")
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
    try:
        fields = dispatch.unpack_payload(args.payload) if args.payload \
            else _fields(args)
    except JobError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    if not fields.get("topic"):
        print(json.dumps({"ok": False,
                          "error": "topic required (via --payload or --topic)"}))
        return 1

    try:
        # Gate: hash self-verification + journaled approval + (when the
        # store has a record) live-status/expiry/retry-budget checks — a
        # cancelled or expired job never re-executes even though its
        # approval stays 'approved' in Command OS.
        dispatch.verify_worker_inputs(
            cfg, job_id=args.job_id, approval_id=args.approval_id,
            expected_hash=args.payload_hash, fields=fields,
            command_os=command_os, job_store=store)

        # Local ledger: on a durable FYE_ROOT this is the control-plane
        # record; on the ephemeral runner it is the run's audit artifact.
        # Durable replay: the runner filesystem is ephemeral, so a
        # finished job's record lives in the Command OS event ledger —
        # not here. If the ledger already reports READY (or beyond),
        # replay instead of rendering the same job twice.
        prior = command_os.job_events(cfg, args.job_id) or []
        if any(e.get("state") in ("READY", "PUBLISH_APPROVED",
                                  "PUBLISHING", "PUBLISHED")
               for e in prior):
            print(json.dumps({"ok": True, "replayed": True,
                              "status": "READY"}, indent=2))
            return 0

        job = store.get(args.job_id) or store.create(
            job_id=args.job_id, approval_id=args.approval_id,
            fields=fields)
        if job["status"] in ("READY", "PUBLISH_APPROVED", "PUBLISHED"):
            # Duplicate dispatch of a finished render — replay, don't redo.
            print(json.dumps({"ok": True, "replayed": True,
                              "status": job["status"],
                              "artifacts": job["artifacts"]}, indent=2))
            return 0
        # A fresh runner creates the record in DRAFT — the approval was
        # already verified above, so advance it through the legal path
        # (DRAFT→APPROVED→QUEUED) before claiming the render lease.
        if job["status"] == "DRAFT":
            store.approve(args.job_id, approved_by=worker)
            store.enqueue(args.job_id)
        elif job["status"] == "APPROVED":
            store.enqueue(args.job_id)
        if not store.claim(args.job_id, worker):
            raise JobError(f"job {args.job_id} lease held by another worker")

        store.transition(args.job_id, "RENDERING")
        _emit_state(store.get(args.job_id))

        # Resource ceiling: the render runs in a killable subprocess —
        # a timed-out FFmpeg pipeline is actually terminated (unlike a
        # thread, which Python cannot cancel) and the job is left in a
        # recoverable CLAIMED/RENDERING state (lease expiry → re-claim).
        result = _render_killable(fields, args.job_id,
                                  cfg.render_timeout_s)

        if not result.get("ok"):
            raise JobError(f"render failed: {result.get('error') or result.get('issues')}")

        store.transition(args.job_id, "QA")
        # The video engine writes the master outside the package dir
        # (datacenter/video_pipeline/distribution_masters) — copy it
        # into the job package so the artifact upload and any later
        # consumer see one self-contained bundle.
        pkg_dir = Path(cfg.root) / args.job_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        # The upgraded assembly writes the master inside the package dir
        # already — skip the copy instead of copy2-ing a file onto itself.
        src, dst = Path(result["master"]).resolve(), (pkg_dir / Path(result["master"]).name).resolve()
        master = src if src == dst else shutil.copy2(src, dst)
        # QA gate: artifact exists, is non-trivial, inside size limit,
        # SHA256 pinned into the job record.
        store.record_artifact(args.job_id, os.fspath(master))
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

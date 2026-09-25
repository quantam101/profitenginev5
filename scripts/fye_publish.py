#!/usr/bin/env python3
"""
FYE publisher — the publish side of the render/publish split.

A READY asset needs its own publish authorization: an operator approves
the `fye:<job_id>-publish` approval in Command OS, then this script
verifies the journaled decision, moves READY → PUBLISH_APPROVED →
PUBLISHED through the channel adapter, and emits fye.job_event with the
#95 attribution spine (asset_id → channel_id → campaign).

Usage:
  python scripts/fye_publish.py request --job-id fye-job-...
  python scripts/fye_publish.py publish --job-id fye-job-... \
      --publish-approval-id appr_2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.fye import command_os, dispatch, publish  # noqa: E402
from runtime.fye.config import FyeConfig  # noqa: E402
from runtime.fye.jobs import FyeJobStore, JobError  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="FYE publisher")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("request", "publish"):
        p = sub.add_parser(name)
        p.add_argument("--job-id", required=True)
        p.add_argument("--publish-approval-id", default="")
    args = ap.parse_args()

    cfg = FyeConfig()
    store = FyeJobStore(cfg)

    try:
        job = store.get(args.job_id)
        if job is None:
            raise JobError(f"unknown job {args.job_id}")

        # The render ran on an ephemeral GHA runner — its transitions only
        # exist there and in Command OS fye.job_event records. Reconcile so
        # a runner-side READY reaches the control-plane store before any
        # publish decision.
        try:
            job = dispatch.reconcile_job(cfg, store, args.job_id,
                                         command_os=command_os)
        except Exception as exc:
            print(json.dumps({"warning": f"reconcile failed: {exc}"}),
                  file=sys.stderr)

        if args.cmd == "request":
            if job["status"] != "READY":
                raise JobError(f"job {args.job_id} is {job['status']}, "
                               "publish requests require READY")
            res = command_os.request_publish_approval(
                cfg,
                package_id=f"{args.job_id}-publish",
                title=f"Publish {args.job_id}",
                channel=job["attribution"].get("channel_id", ""),
                risk_level=job.get("payload", {}).get("risk_level", "medium"),
            )
            print(json.dumps(res, indent=2))
            return 0 if res.get("ok") or res.get("skipped") else 1

        # publish
        approval_id = args.publish_approval_id
        if not approval_id:
            raise JobError("--publish-approval-id required")
        dispatch.verify_approval(
            cfg, job_id=f"{args.job_id}-publish",
            approval_id=approval_id, command_os=command_os)
        if job["status"] == "READY":
            store.transition(args.job_id, "PUBLISH_APPROVED",
                             approval_id=approval_id)
        res = publish.publish_job(cfg, store, args.job_id)
        # Emit the #95 attribution event — durable asset→revenue spine.
        from runtime.daily_command_producer import emit
        emit("fye.job_event", publish.published_event(store.get(args.job_id)),
             source="profitenginev5",
             idempotency_key=f"fye-published-{args.job_id}")
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 1
    except JobError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())

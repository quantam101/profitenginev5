#!/usr/bin/env python3
"""
FYE job control plane — create, approve, and dispatch immutable jobs.

Replaces push-triggered execution: a Command OS approval is verified
against the journaled decision, the job record is created (idempotent on
job_id + payload_hash), then the worker is fired via authenticated
workflow_dispatch using FYE_DISPATCH_TOKEN (fine-grained, Actions:write
only).

Usage:
  python scripts/fye_dispatch.py create --topic "..." --approval-id appr_1 \
      [--niche personal-finance] [--channel @channel] [--campaign cmp_1]
  python scripts/fye_dispatch.py approve --job-id fye-job-...
  python scripts/fye_dispatch.py dispatch --job-id fye-job-...
  python scripts/fye_dispatch.py show --job-id fye-job-...
  python scripts/fye_dispatch.py list [--status READY]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.fye import command_os, dispatch  # noqa: E402
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


def main() -> int:
    ap = argparse.ArgumentParser(description="FYE job control plane")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("--job-id", default="")
    c.add_argument("--approval-id", required=True)
    c.add_argument("--topic", required=True)
    c.add_argument("--niche", default="science-explainer")
    c.add_argument("--title", default="")
    c.add_argument("--channel", default="")
    c.add_argument("--campaign", default="")
    c.add_argument("--monthly-views-target", type=int, default=100_000)
    c.add_argument("--subscribers", type=int, default=0)
    c.add_argument("--watch-hours", type=float, default=0.0)
    c.add_argument("--shorts-views", type=int, default=0)
    c.add_argument("--human-reviewed", action="store_true")

    a = sub.add_parser("approve")
    a.add_argument("--job-id", required=True)

    d = sub.add_parser("dispatch")
    d.add_argument("--job-id", required=True)

    s = sub.add_parser("show")
    s.add_argument("--job-id", required=True)

    li = sub.add_parser("list")
    li.add_argument("--status", default=None)

    args = ap.parse_args()
    cfg = FyeConfig()
    store = FyeJobStore(cfg)

    try:
        if args.cmd == "create":
            job = store.create(
                job_id=args.job_id or None,
                approval_id=args.approval_id,
                fields=_fields(args),
                attribution={"campaign": args.campaign},
            )
            print(json.dumps(job, indent=2))
            return 0

        if args.cmd == "approve":
            job = store.get(args.job_id)
            if job is None:
                raise JobError(f"unknown job {args.job_id}")
            # Verify the journaled verdict before approving locally —
            # fail closed when Command OS disagrees or is unreachable.
            dispatch.verify_approval(cfg, job_id=args.job_id,
                                   approval_id=job["approval_id"],
                                   command_os=command_os)
            job = store.approve(args.job_id)
            store.enqueue(args.job_id)
            print(json.dumps(store.get(args.job_id), indent=2))
            return 0

        if args.cmd == "dispatch":
            job = store.get(args.job_id)
            if job is None:
                raise JobError(f"unknown job {args.job_id}")
            res = dispatch.dispatch_job(cfg, job)
            print(json.dumps(res, indent=2))
            return 0 if res.get("ok") else 1

        if args.cmd == "show":
            job = store.get(args.job_id)
            if job is None:
                raise JobError(f"unknown job {args.job_id}")
            print(json.dumps(job, indent=2))
            return 0

        if args.cmd == "list":
            print(json.dumps(store.list(status=args.status), indent=2))
            return 0
    except JobError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

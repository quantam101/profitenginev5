#!/usr/bin/env python3
"""
FYE pipeline CLI — runs one faceless-video package end to end.

Usage:
  python scripts/fye_run.py --topic "Compound interest" --niche personal-finance
  python scripts/fye_run.py --status          # journal + wiring status
  python scripts/fye_run.py --pending         # pending FYE approvals in Command OS
  python scripts/fye_run.py --decision <approval_id>   # verify journaled verdict
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.fye import FyeOrchestrator  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="FYE pipeline")
    ap.add_argument("--topic")
    ap.add_argument("--niche", default="science-explainer")
    ap.add_argument("--title", default="")
    ap.add_argument("--monthly-views-target", type=int, default=100_000)
    ap.add_argument("--subscribers", type=int, default=0)
    ap.add_argument("--watch-hours", type=float, default=0.0)
    ap.add_argument("--shorts-views", type=int, default=0)
    ap.add_argument("--human-reviewed", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--decision", metavar="APPROVAL_ID")
    args = ap.parse_args()

    orch = FyeOrchestrator()

    if args.status:
        print(json.dumps(orch.status(), indent=2))
        return 0
    if args.pending:
        print(json.dumps(orch.pending_packages(), indent=2))
        return 0
    if args.decision:
        print(json.dumps(orch.verify_decision(args.decision), indent=2))
        return 0
    if not args.topic:
        ap.error("--topic required (or use --status/--pending/--decision)")

    def log(agent: str, result: dict) -> None:
        print(f"[{agent}] ok")

    result = orch.run(
        topic=args.topic, niche=args.niche, title=args.title,
        monthly_views_target=args.monthly_views_target,
        subscribers=args.subscribers, watch_hours=args.watch_hours,
        shorts_views=args.shorts_views, human_reviewed=args.human_reviewed,
        on_agent=log,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

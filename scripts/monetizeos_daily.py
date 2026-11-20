#!/usr/bin/env python3
"""One-shot daily Study -> Self-Repair simulation -> status report.

Read-only against production state and source: this runner executes checks,
diagnoses failures and writes a structured report. It never changes source,
merges PRs, deploys, spends money or sends external messages. Repair actions
requiring a code edit remain review-gated.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.opportunity_relevance import assess_relevance  # noqa: E402
from runtime.monetizeos.contracts import redact_text  # noqa: E402


CHECKS = (
    "tests/test_opportunity_relevance.py",
    "tests/test_opportunity_intelligence.py",
    "tests/test_monetizeos.py",
    "tests/test_monetizeos_ha.py",
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_head(root: Path) -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                            capture_output=True, text=True, timeout=5, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def study(root: Path) -> dict[str, Any]:
    """Inspect real local artifacts and exercise positive/negative signal controls."""
    expected = [
        "runtime/monetizeos/director.py",
        "runtime/monetizeos/store.py",
        "runtime/monetizeos/standby.py",
        "runtime/opportunity_relevance.py",
        *CHECKS,
    ]
    missing = [p for p in expected if not (root / p).is_file()]
    high = assess_relevance("Install Aruba access points, pull Cat6 and test VLANs")
    low = assess_relevance("Network marketing credit repair sales lead")
    controls_pass = high.accepted and not low.accepted
    return {
        "phase": "Study",
        "at": _utc(),
        "repo_head": _git_head(root),
        "files_checked": len(expected),
        "missing_files": missing,
        "positive_control": {"accepted": high.accepted, "score": high.score},
        "negative_control": {"accepted": low.accepted, "reasons": list(low.reasons)},
        "passed": not missing and controls_pass,
    }


def self_repair_simulation(root: Path, timeout_s: int) -> dict[str, Any]:
    """Run concrete verification and prepare bounded remediation if checks fail.

    This is a simulation of repair selection, not automatic application.
    """
    command = [sys.executable, "-m", "pytest", "-q", *CHECKS]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        p = subprocess.run(command, cwd=root, capture_output=True, text=True,
                           env=env, timeout=timeout_s, check=False)
        code = p.returncode
        output = redact_text((p.stdout + "\n" + p.stderr)[-7000:])
        timeout = False
    except subprocess.TimeoutExpired as exc:
        code = 124
        output = redact_text(str(exc)[-2000:])
        timeout = True

    passed = code == 0
    repair_plan: list[str] = []
    if not passed:
        repair_plan = [
            "Do not deploy or merge this branch.",
            "Review the failing test and its captured output.",
            "Create a minimal source patch with a regression test.",
            "Rerun this daily gate before requesting human approval.",
        ]
    return {
        "phase": "Self-Repair",
        "mode": "simulation_no_source_mutation",
        "at": _utc(),
        "command": command,
        "exit_code": code,
        "timed_out": timeout,
        "passed": passed,
        "captured_output": output,
        "repair_plan": repair_plan,
        "automatic_changes": [],
    }


def run_daily(root: Path, report_path: Path, timeout_s: int = 180) -> dict[str, Any]:
    began = time.monotonic()
    result: dict[str, Any] = {
        "schema": "monetizeos.daily/1",
        "started_at": _utc(),
        "source": str(root),
        "external_actions": [],
        "stages": {},
    }
    try:
        result["stages"]["study"] = study(root)
        if result["stages"]["study"]["passed"]:
            result["stages"]["self_repair"] = self_repair_simulation(root, timeout_s)
        else:
            result["stages"]["self_repair"] = {
                "phase": "Self-Repair",
                "mode": "blocked_by_study",
                "passed": False,
                "repair_plan": ["Restore missing required files before verification."],
                "automatic_changes": [],
            }
        good = all(stage["passed"] for stage in result["stages"].values())
        result["status"] = "PASS" if good else "NEEDS_REVIEW"
    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = redact_text(f"{type(exc).__name__}: {exc}")
    finally:
        result["ended_at"] = _utc()
        result["duration_seconds"] = round(time.monotonic() - began, 3)
        result["stages"]["status_report"] = {
            "phase": "Status Report",
            "at": result["ended_at"],
            "status": result["status"],
            "human_approval_required_for_edits": True,
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--report", type=Path, default=Path("reports/monetizeos-daily.json"))
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--simulate", action="store_true",
                   help="Explicitly acknowledge no automatic source edits (default behavior)")
    args = p.parse_args()
    if args.timeout < 1:
        p.error("timeout must be >= 1")
    result = run_daily(args.repo_root.resolve(), args.report.resolve(), args.timeout)
    summary = {"status": result["status"],
               "report": str(args.report.resolve()),
               "steps": list(result["stages"])}
    print(json.dumps(summary, sort_keys=True))
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as fh:
            fh.write("### MonetizeOS Daily Simulation\n\n")
            fh.write(f"Result: **{result['status']}**\n\n")
            for stage in result["stages"]:
                fh.write(f"- {stage}: {result['stages'][stage].get('phase')}\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

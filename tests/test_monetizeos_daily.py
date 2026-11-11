"""Daily simulation contract tests: no false success or source mutation."""
from __future__ import annotations

import json
from pathlib import Path

from scripts import monetizeos_daily as daily


def test_study_refuses_missing_canonical_files(tmp_path):
    result = daily.study(tmp_path)
    assert not result["passed"]
    assert "runtime/monetizeos/director.py" in result["missing_files"]


def test_failed_study_reports_blocked_repair_and_nonzero_status(tmp_path):
    target = tmp_path / "out" / "report.json"
    result = daily.run_daily(tmp_path, target, timeout_s=1)
    assert result["status"] == "NEEDS_REVIEW"
    assert result["stages"]["self_repair"]["mode"] == "blocked_by_study"
    assert result["stages"]["self_repair"]["automatic_changes"] == []
    assert json.loads(target.read_text())["status"] == "NEEDS_REVIEW"


def test_successful_study_executes_real_scope_controls():
    root = Path(__file__).resolve().parents[1]
    result = daily.study(root)
    assert result["passed"]
    assert result["positive_control"]["accepted"]
    assert not result["negative_control"]["accepted"]


def test_repair_command_records_failure_without_claiming_fix(monkeypatch, tmp_path):
    class FailedRun:
        returncode = 1
        stdout = "FAILED test_something"
        stderr = "assert False"

    def fake_run(command, **kwargs):
        return FailedRun()

    monkeypatch.setattr(daily.subprocess, "run", fake_run)
    result = daily.self_repair_simulation(tmp_path, timeout_s=5)
    assert not result["passed"]
    assert result["exit_code"] == 1
    assert result["repair_plan"]
    assert result["automatic_changes"] == []

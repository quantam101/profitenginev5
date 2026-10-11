"""Tests for the measured agent eval loop (runtime/agent_evals.py)."""
import json
from pathlib import Path

from runtime.agent_evals import (
    collect_markdown,
    load_cases,
    main,
    run_check,
    run_suite,
    score_case,
)


def good_article() -> dict:
    sections = "\n\n".join(
        f"## Section {i}\n\n"
        + "Useful evidence-based guidance with concrete steps and examples. " * 40
        for i in range(1, 7)
    )
    return {
        "title": "How to Audit a Site",
        "meta_description": "A practical, evidence-aware guide to technical SEO audits, workflows, and verification steps for site owners and bloggers.",
        "body": sections
        + "\n\n[GSC](https://developers.google.com/search)\n\n## Sources\n\nLinked above.\n",
    }


def test_score_case_expect_pass():
    r = score_case(
        {
            "id": "good",
            "output": good_article(),
            "checks": ["seo_quality", "no_placeholders", "min_words:1000"],
            "expect_pass": True,
        }
    )
    assert r.passed and r.checks_ok
    assert r.metrics["words"] > 1000


def test_score_case_expect_fail_caught():
    case = {
        "id": "bad",
        "output": {"title": "Thin", "body": "tiny. [insert link]"},
        "checks": ["seo_quality", "no_placeholders"],
        "expect_pass": False,
    }
    r = score_case(case)
    # checks fail AND that was expected -> case passes (gate caught the bad output)
    assert r.passed and not r.checks_ok


def test_score_case_expect_fail_missed():
    # gate fails to catch a bad output it should catch -> case fails
    case = {
        "id": "bad-missed",
        "output": {"title": "Thin", "body": "tiny"},
        "checks": ["min_words:1"],
        "expect_pass": False,
    }
    r = score_case(case)
    assert not r.passed


def test_unknown_check_fails():
    r = run_check({"body": "x"}, "nonexistent_check")
    assert not r.ok


def test_json_extract_check():
    ok = run_check('pre {"a": 1} post', "json_extract:a")
    assert ok.ok
    bad = run_check("no json", "json_extract:a")
    assert not bad.ok


def test_suite_and_baseline(tmp_path: Path):
    suite = tmp_path / "suite.jsonl"
    cases = [
        {"id": "g", "output": good_article(), "checks": ["seo_quality"], "expect_pass": True},
        {"id": "b", "output": {"title": "t", "body": "x"}, "checks": ["seo_quality"], "expect_pass": False},
    ]
    suite.write_text("\n".join(json.dumps(c) for c in cases))
    loaded = load_cases(suite)
    assert len(loaded) == 2
    report = run_suite("t", loaded)
    assert report.total == 2 and report.passed == 2 and report.pass_rate == 1.0


def test_collect_markdown(tmp_path: Path):
    md = tmp_path / "post.md"
    md.write_text("# Real Post\n\nBody text.\n")
    cases = list(collect_markdown(str(tmp_path / "*.md")))
    assert len(cases) == 1
    assert cases[0]["provenance"] == "live"
    assert cases[0]["output"]["title"] == "Real Post"


def test_main_end_to_end(tmp_path: Path, capsys):
    suite = tmp_path / "s.jsonl"
    suite.write_text(
        json.dumps(
            {
                "id": "g",
                "output": good_article(),
                "checks": ["seo_quality"],
                "expect_pass": True,
            }
        )
    )
    report = tmp_path / "report.json"
    code = main(["--suite", str(suite), "--report", str(report)])
    assert code == 0
    saved = json.loads(report.read_text())
    assert saved["pass_rate"] == 1.0

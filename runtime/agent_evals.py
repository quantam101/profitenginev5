"""Measured eval loop for agent outputs — deterministic, zero-cost.

Scores agent outputs against deterministic checks (the same gates used in
production), records real metrics per case, and compares the suite pass
rate against a stored baseline so regressions fail CI instead of shipping
quietly.

Case format (JSONL, one object per line):
    {
      "id": "content-good-01",
      "agent": "content-gen",               # informational grouping
      "expect_pass": true,                  # whether the checks SHOULD pass
      "provenance": "fixture",              # fixture | live | recorded
      "output": { ... article-ish dict or raw string ... },
      "checks": ["seo_quality", "min_words:1000", "no_placeholders"]
    }

A case "passes" when EVERY check's actual result equals ``expect_pass``
(individually, not just in aggregate) — a bad-output fixture must trip
every check it names, so one gate silently breaking can't hide behind
another check's failure. That makes the
suite a regression test for the gates themselves AND a measured quality
loop over real outputs (``--collect`` scores real markdown posts).

CLI:
    ~/.pyenv/shims/python -m runtime.agent_evals \
        --suite evals/content_gen.jsonl \
        [--collect "content/**/*.md"] \
        [--report data/evals/latest.json] \
        [--baseline data/evals/baseline.json] \
        [--min-pass-rate 0.9]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from runtime.structured_output import extract_json


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class CaseResult:
    id: str
    agent: str
    provenance: str
    expect_pass: bool
    passed: bool  # actual == expected
    checks_ok: bool
    checks: list[CheckResult] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class EvalReport:
    suite: str
    total: int
    passed: int
    pass_rate: float
    metrics: dict[str, float]
    cases: list[CaseResult]


def _article(output: Any) -> dict[str, Any]:
    if isinstance(output, dict):
        return output
    return {"title": "", "body": str(output)}


def _check_seo_quality(output: Any, _arg: str) -> CheckResult:
    from scripts.seo_content_quality import validate_article_quality

    r = validate_article_quality(_article(output))
    return CheckResult("seo_quality", r.ok, "; ".join(r.errors) or f"warnings={len(r.warnings)}")


_PLACEHOLDER = re.compile(
    r"\[(?:insert|placeholder|todo|tbd|edit)[^\]]*\]|lorem ipsum|example\.com|"
    r"\[(?:AFFILIATE|AMAZON_LINK)(?::[^\]]+)?\]",
    re.I,
)


def _check_no_placeholders(output: Any, _arg: str) -> CheckResult:
    a = _article(output)
    text = f"{a.get('title', '')}\n{a.get('body', '')}\n{a.get('meta_description', '')}"
    hit = _PLACEHOLDER.search(text)
    return CheckResult("no_placeholders", hit is None, hit.group(0) if hit else "")


def _check_min_words(output: Any, arg: str) -> CheckResult:
    body = str(_article(output).get("body") or "")
    n = len(re.findall(r"\b[\w’'-]+\b", body))
    need = int(arg)
    return CheckResult(f"min_words:{arg}", n >= need, f"{n} words")


def _check_max_words(output: Any, arg: str) -> CheckResult:
    body = str(_article(output).get("body") or "")
    n = len(re.findall(r"\b[\w’'-]+\b", body))
    cap = int(arg)
    return CheckResult(f"max_words:{arg}", n <= cap, f"{n} words")


def _check_sources_section(output: Any, _arg: str) -> CheckResult:
    body = str(_article(output).get("body") or "")
    ok = bool(re.search(r"^##\s+(?:Sources|Official references|References)\b", body, re.I | re.M))
    return CheckResult("sources_section", ok)


def _check_meta_length(output: Any, _arg: str) -> CheckResult:
    meta = str(_article(output).get("meta_description") or "")
    if not meta:
        return CheckResult("meta_length", False, "no meta_description")
    ok = 120 <= len(meta) <= 170
    return CheckResult("meta_length", ok, f"{len(meta)} chars")


def _check_json_extract(output: Any, arg: str) -> CheckResult:
    keys = [k for k in arg.split(",") if k]
    raw = output if isinstance(output, str) else json.dumps(output)
    r = extract_json(raw, required_keys=keys)
    return CheckResult(f"json_extract:{arg}", r.ok)


def _check_regex_absent(output: Any, arg: str) -> CheckResult:
    a = _article(output)
    text = f"{a.get('title', '')}\n{a.get('body', '')}"
    hit = re.search(arg, text, re.I)
    return CheckResult(f"regex_absent:{arg}", hit is None, hit.group(0) if hit else "")


_CHECK_DISPATCH: dict[str, Callable[[Any, str], CheckResult]] = {
    "seo_quality": _check_seo_quality,
    "no_placeholders": _check_no_placeholders,
    "min_words": _check_min_words,
    "max_words": _check_max_words,
    "sources_section": _check_sources_section,
    "meta_length": _check_meta_length,
    "json_extract": _check_json_extract,
    "regex_absent": _check_regex_absent,
}


def run_check(output: Any, spec: str) -> CheckResult:
    name, _, arg = spec.partition(":")
    fn = _CHECK_DISPATCH.get(name)
    if fn is None:
        return CheckResult(spec, False, f"unknown check: {name}")
    return fn(output, arg)


def score_case(case: dict[str, Any]) -> CaseResult:
    checks_spec = case.get("checks") or ["seo_quality"]
    results = [run_check(case.get("output"), c) for c in checks_spec]
    expect = bool(case.get("expect_pass", True))
    # Per-check expectation: for expect_pass=false, EVERY named check must
    # fail. Aggregate-only comparison would let a broken gate hide behind
    # a sibling check that still rejects the fixture.
    checks_ok = all(c.ok for c in results)
    a = _article(case.get("output"))
    body = str(a.get("body") or "")
    metrics = {"words": float(len(re.findall(r"\b[\w’'-]+\b", body)))}
    # An unknown check name must never satisfy expect_pass=false — a
    # misspelled gate would otherwise "fail" as expected and the suite
    # would pass without exercising the intended check.
    unknown = any(c.detail.startswith("unknown check") for c in results)
    return CaseResult(
        id=str(case.get("id") or "unnamed"),
        agent=str(case.get("agent") or "unknown"),
        provenance=str(case.get("provenance") or "fixture"),
        expect_pass=expect,
        passed=(not unknown) and all(c.ok == expect for c in results),
        checks_ok=checks_ok,
        checks=results,
        metrics=metrics,
    )


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            cases.append(json.loads(line))
    return cases


def collect_markdown(pattern: str) -> Iterable[dict[str, Any]]:
    """Build eval cases from real markdown files (provenance=live)."""
    for p in sorted(glob.glob(pattern, recursive=True)):
        path = Path(p)
        text = path.read_text(encoding="utf-8", errors="replace")
        # Strip YAML front matter — published Jekyll posts carry metadata
        # (layout, tags, dates) that would otherwise be scored as article
        # body, inflating word counts and tripping placeholder rules.
        text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, flags=re.S)
        title = ""
        m = re.search(r"^#\s+(.+)$", text, re.M) or re.search(r'^title:\s*"?([^"\n]+)"?', text, re.M)
        if m:
            title = m.group(1).strip()
        yield {
            "id": f"live:{path}",
            "agent": "published-content",
            "expect_pass": True,
            "provenance": "live",
            "output": {"title": title, "body": text},
            "checks": ["seo_quality", "no_placeholders", "regex_absent:\\[(?:insert|todo|tbd)[^\\]]*\\]"],
        }


def run_suite(name: str, cases: list[dict[str, Any]]) -> EvalReport:
    results = [score_case(c) for c in cases]
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    words = [r.metrics["words"] for r in results if "words" in r.metrics]
    metrics = {
        "mean_words": round(sum(words) / len(words), 1) if words else 0.0,
        "cases_expected_fail": sum(1 for r in results if not r.expect_pass),
    }
    return EvalReport(
        suite=name,
        total=total,
        passed=passed,
        pass_rate=(passed / total) if total else 0.0,
        metrics=metrics,
        cases=results,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--suite", type=Path, help="JSONL eval case file")
    ap.add_argument("--collect", type=str, help="glob of real markdown files to score (provenance=live)")
    ap.add_argument("--report", type=Path, help="write JSON report here")
    ap.add_argument("--baseline", type=Path, help="baseline report JSON for regression comparison")
    ap.add_argument("--min-pass-rate", type=float, default=1.0)
    args = ap.parse_args(argv)

    cases: list[dict[str, Any]] = []
    if args.suite:
        cases.extend(load_cases(args.suite))
    if args.collect:
        cases.extend(collect_markdown(args.collect))
    if not cases:
        print("no eval cases (provide --suite and/or --collect)", file=sys.stderr)
        return 2

    report = run_suite(args.suite.stem if args.suite else "collected", cases)

    for c in report.cases:
        status = "PASS" if c.passed else "FAIL"
        failed = [f"{x.name}({x.detail})" for x in c.checks if not x.ok]
        print(f"{status} {c.id} [{c.provenance}]" + (f"  ← {', '.join(failed)}" if failed else ""))
    print(f"\n{report.passed}/{report.total} cases passed ({report.pass_rate:.0%})")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(asdict(report), indent=2) + "\n")

    exit_code = 0
    if report.pass_rate < args.min_pass_rate:
        print(f"pass_rate {report.pass_rate:.2%} < min {args.min_pass_rate:.0%}", file=sys.stderr)
        exit_code = 1
    if args.baseline and args.baseline.exists():
        base = json.loads(args.baseline.read_text())
        base_rate = float(base.get("pass_rate", 0.0))
        if report.pass_rate < base_rate:
            print(f"regression: pass_rate {report.pass_rate:.2%} < baseline {base_rate:.2%}", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

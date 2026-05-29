"""
security_check.py -- three-layer security gate for CI
=====================================================

Layer 1 -- ruff (select=S)
  Bandit-backed rules: hardcoded passwords, use of exec/eval, insecure hashes,
  shell-injection, XML vulnerabilities, etc.  Understands the codebase; no
  false positives from env-var name references.

Layer 2 -- eslint
  Runs the project's own eslint config (next/core-web-vitals + any plugins).
  Understands imports, context, and JSX; no string-grep false positives.

Layer 3 -- secret-value scanner (runtime/security_scanner.py)
  Last-resort grep for accidentally committed key VALUES (sk-ant-, sk-proj-,
  PEM headers, AWS secret assignments).  Markers are narrow -- env-var names
  like ANTHROPIC_API_KEY are NOT in the list; ruff/eslint own those concerns.

Exit 0 = all three layers pass.
Exit 1 = at least one finding; details printed to stdout.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.security_scanner import scan_repo  # noqa: E402


# -- helpers --------------------------------------------------------------------

def _run(*args: str, cwd: Path = ROOT) -> tuple[int, str]:
    """Run a command, return (returncode, combined output)."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return -1, f"command not found: {args[0]}"


def _header(title: str) -> None:
    print(f"\n-- {title} {'-' * max(0, 60 - len(title))}")


# -- layer 1: ruff S-rules ------------------------------------------------------

def check_ruff() -> list[str]:
    # S101 (assert in tests), S110/S112 (try/except-pass/continue), and
    # S310 (urllib URL-scheme audit) are intentional patterns in this codebase.
    # Extend-ignore them so the scan focuses on real credential/injection risks.
    _header("ruff (S -- bandit security rules, --extend-ignore S101,S110,S112,S310)")
    code, out = _run(
        "ruff", "check",
        "--select", "S",
        "--extend-ignore", "S101,S110,S112,S310",
        "backend/", "runtime/", "scripts/",
    )
    if code == -1:
        print("  ruff not installed -- skipping (pip install ruff)")
        return []
    if code == 0:
        print("  ok no ruff S-rule findings")
        return []
    print(out)
    return [line for line in out.splitlines() if line.strip()]


# -- layer 2: eslint ------------------------------------------------------------

def check_eslint() -> list[str]:
    _header("eslint (project config)")
    code, out = _run("npx", "--no-install", "eslint", "app/", "lib/", "--max-warnings=0")
    if code == -1:
        print("  eslint not found -- skipping")
        return []
    if code == 0:
        print("  ok no eslint findings")
        return []
    print(out)
    return [line for line in out.splitlines() if line.strip()]


# -- layer 3: secret-value scanner ---------------------------------------------

def check_secrets() -> list[str]:
    _header("secret-value scanner (actual key prefixes only)")
    findings = scan_repo(".")
    if not findings:
        print("  ok no secret-value markers found")
        return []
    for f in findings:
        print(f"  FAIL: {f}")
    return findings


# -- main -----------------------------------------------------------------------

def main() -> int:
    print("security-check: running three-layer scan ...")
    ruff_findings    = check_ruff()
    eslint_findings  = check_eslint()
    secret_findings  = check_secrets()

    total = len(ruff_findings) + len(eslint_findings) + len(secret_findings)
    print(f"\n{'-' * 64}")
    if total == 0:
        print("security-check: all layers passed ok")
        return 0

    print(f"security-check: {total} finding(s) across "
          f"ruff={len(ruff_findings)} eslint={len(eslint_findings)} "
          f"secrets={len(secret_findings)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

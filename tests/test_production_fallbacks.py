"""Regression test for forbidden production fallback values.

Runs the same scan used by `npm run security:scan` so any reintroduction of
dead OCI IPs, fake backend domains, or placeholder strings breaks the build.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.production_fallback_validator import scan_fallbacks  # noqa: E402


def test_no_forbidden_production_fallbacks():
    findings = scan_fallbacks(str(ROOT))
    assert not findings, "\n".join(findings)

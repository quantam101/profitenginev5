"""ProfitEngine backend API integration tests.

Tests cover /api/health, /api/merge, /api/score, /api/waitlist,
/api/stats and /api/demo.
"""
import os
import uuid
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
# Fallback to /app/frontend/.env if env not set in shell
if not BASE_URL:
    from pathlib import Path
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
            break

assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

API = f"{BASE_URL}/api"
TIMEOUT = 30


# --- health ----------------------------------------------------------------
def test_health_ok():
    r = requests.get(f"{API}/health", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "profitengine"


# --- merge (python) --------------------------------------------------------
PY_BASE = '''
def parse(x):
    return int(x)
'''

PY_TARGET = '''
def parse(x: str) -> int:
    """Parse value to int with safety."""
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0
'''

def test_merge_python_upgrades_function():
    r = requests.post(f"{API}/merge", json={
        "language": "python",
        "base": PY_BASE,
        "target": PY_TARGET,
    }, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "merged" in data
    assert isinstance(data["upgrades"], list)
    assert len(data["upgrades"]) >= 1
    names = [u["name"] for u in data["upgrades"]]
    assert "parse" in names
    # Merged source should contain try/except now
    assert "try:" in data["merged"]


def test_merge_python_invalid_syntax_returns_400():
    r = requests.post(f"{API}/merge", json={
        "language": "python",
        "base": "def broken(:\n    pass",
        "target": PY_TARGET,
    }, timeout=TIMEOUT)
    assert r.status_code == 400


# --- merge (js) ------------------------------------------------------------
JS_BASE = """
function parse(x) {
  return parseInt(x);
}
"""

JS_TARGET = """
/**
 * Parse value to integer safely.
 * @param {string} x
 * @returns {number}
 */
function parse(x) {
  try {
    return parseInt(x, 10);
  } catch (e) {
    return 0;
  }
}
"""

def test_merge_js_upgrades_function():
    r = requests.post(f"{API}/merge", json={
        "language": "js",
        "base": JS_BASE,
        "target": JS_TARGET,
    }, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data["upgrades"], list)
    assert len(data["upgrades"]) >= 1
    assert "try" in data["merged"]


# --- score -----------------------------------------------------------------
def test_score_returns_rows():
    src = '''
def good(x: int) -> int:
    """Square it."""
    try:
        return x * x
    except Exception:
        return 0

def bad(x):
    return x
'''
    r = requests.post(f"{API}/score", json={"source": src}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    names = {row["name"] for row in data}
    assert {"good", "bad"} <= names
    for row in data:
        assert "total" in row
        assert "complexity" in row
        assert isinstance(row["complexity"], int)
        assert isinstance(row["total"], (int, float))


# --- waitlist --------------------------------------------------------------
def test_waitlist_signup_and_idempotent():
    email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
    r1 = requests.post(f"{API}/waitlist", json={"email": email}, timeout=TIMEOUT)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert "id" in d1
    assert "position" in d1
    assert isinstance(d1["position"], int)
    assert d1["position"] >= 1

    # Second submission with same email -> same id
    r2 = requests.post(f"{API}/waitlist", json={"email": email}, timeout=TIMEOUT)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["id"] == d1["id"]
    assert d2["position"] == d1["position"]


def test_waitlist_invalid_email_returns_422():
    r = requests.post(f"{API}/waitlist", json={"email": "not-an-email"}, timeout=TIMEOUT)
    assert r.status_code == 422


# --- stats -----------------------------------------------------------------
def test_stats_returns_integers_and_increments():
    r0 = requests.get(f"{API}/stats", timeout=TIMEOUT)
    assert r0.status_code == 200
    s0 = r0.json()
    for k in ("files_merged_total", "devs_joined", "upgrades_applied", "repos_analyzed"):
        assert k in s0
        assert isinstance(s0[k], int)

    # Trigger one merge + one waitlist
    requests.post(f"{API}/merge", json={
        "language": "python",
        "base": PY_BASE,
        "target": PY_TARGET,
    }, timeout=TIMEOUT)
    requests.post(f"{API}/waitlist", json={
        "email": f"TEST_stats_{uuid.uuid4().hex[:8]}@example.com",
    }, timeout=TIMEOUT)
    time.sleep(0.3)

    r1 = requests.get(f"{API}/stats", timeout=TIMEOUT)
    s1 = r1.json()
    assert s1["files_merged_total"] >= s0["files_merged_total"] + 1
    assert s1["devs_joined"] >= s0["devs_joined"] + 1


# --- demo ------------------------------------------------------------------
def test_demo_report_returned():
    r = requests.get(f"{API}/demo", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "files_merged" in data
    assert isinstance(data["files_merged"], list)
    assert len(data["files_merged"]) >= 1

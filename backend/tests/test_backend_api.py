"""ProfitEngine v5 backend API integration tests.

Covers marketing endpoints (health, stats, waitlist), the dashboard
command-center endpoints (agents, approvals, content, revenue, cycle),
and the AST merger endpoints (merge, score, demo).
"""
import os
import uuid
import time
from pathlib import Path

import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
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
    assert data["service"] == "profitengine-v5"


# --- agents (dashboard) ----------------------------------------------------
def test_agents_six_with_required_fields():
    r = requests.get(f"{API}/agents", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 6
    ids = {a["id"] for a in data}
    assert ids == {"scout", "content", "video", "social", "revenue", "guard"}
    for a in data:
        for key in ("name", "role", "status", "success_rate", "runs_today", "description"):
            assert key in a, f"missing {key} in agent {a.get('id')}"
        assert a["status"] in {"online", "thinking", "paused", "offline"}
        assert isinstance(a["success_rate"], (int, float))
        assert isinstance(a["runs_today"], int)


# --- approvals -------------------------------------------------------------
def test_approvals_four_items_risk_levels():
    r = requests.get(f"{API}/approvals", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 4
    risks = {x["risk"] for x in data}
    assert risks <= {"low", "medium", "high"}
    # ensure variety: at least one low, one high somewhere in fixture
    assert "low" in risks
    assert "medium" in risks or "high" in risks


# --- content ---------------------------------------------------------------
def test_content_recent_has_required_fields():
    r = requests.get(f"{API}/content/recent", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1
    for c in data:
        for key in ("title", "channel", "status", "revenue"):
            assert key in c
        assert c["status"] in {"draft", "queued", "published"}
        assert isinstance(c["revenue"], (int, float))


# --- revenue series --------------------------------------------------------
def test_revenue_series_default_30_returns_31_points():
    r = requests.get(f"{API}/revenue/series", params={"days": 30}, timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 31  # inclusive: today + 30 prior
    for p in data:
        assert "date" in p and "amount" in p
        assert isinstance(p["amount"], (int, float))


def test_revenue_series_invalid_days_returns_400():
    r0 = requests.get(f"{API}/revenue/series", params={"days": 0}, timeout=TIMEOUT)
    assert r0.status_code == 400
    r1 = requests.get(f"{API}/revenue/series", params={"days": 400}, timeout=TIMEOUT)
    assert r1.status_code == 400


# --- cycle status ----------------------------------------------------------
def test_cycle_status_shape():
    r = requests.get(f"{API}/cycle/status", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    for key in ("state", "current_step", "step_index", "step_total", "approval_required"):
        assert key in data, f"missing {key}"
    assert isinstance(data["step_index"], int)
    assert isinstance(data["step_total"], int)
    assert isinstance(data["approval_required"], bool)


# --- stats -----------------------------------------------------------------
def test_stats_endpoint_numbers_positive():
    r = requests.get(f"{API}/stats", timeout=TIMEOUT)
    assert r.status_code == 200
    s = r.json()
    for key in ("revenue_30d", "posts_published", "agents_online", "devs_joined"):
        assert key in s, f"missing {key}"
        assert isinstance(s[key], (int, float))
    assert s["revenue_30d"] > 0
    assert s["posts_published"] >= 0
    assert s["agents_online"] >= 0
    assert s["devs_joined"] >= 0


# --- waitlist --------------------------------------------------------------
def test_waitlist_signup_and_idempotent():
    email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
    r1 = requests.post(f"{API}/waitlist", json={"email": email}, timeout=TIMEOUT)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert "id" in d1 and "position" in d1
    assert isinstance(d1["position"], int) and d1["position"] >= 1

    r2 = requests.post(f"{API}/waitlist", json={"email": email}, timeout=TIMEOUT)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["id"] == d1["id"]
    assert d2["position"] == d1["position"]


def test_waitlist_invalid_email_returns_422():
    r = requests.post(f"{API}/waitlist", json={"email": "not-an-email"}, timeout=TIMEOUT)
    assert r.status_code == 422


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
    assert isinstance(data, list) and len(data) == 2
    for row in data:
        assert "name" in row and "total" in row and "complexity" in row
        assert isinstance(row["complexity"], int)


# --- demo ------------------------------------------------------------------
def test_demo_report_returned():
    r = requests.get(f"{API}/demo", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "files_merged" in data
    assert isinstance(data["files_merged"], list)
    assert len(data["files_merged"]) >= 1

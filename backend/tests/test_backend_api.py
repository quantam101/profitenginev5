"""ProfitEngine v5 — backend API regression suite (iteration 3).

Covers all 27 endpoints from the v5 surface: health, stats, agents (7),
sovereign, approvals, advisor, revenue/ledger, scout/content/books/audit/
builds/deployments/proposals/secrets/cost/proof-of-work/distillation/
analytics/cycle, code merger.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_AGENTS = {
    "sovereign-v1", "scout-agent", "content-agent", "video-agent",
    "social-agent", "revenue-agent", "guard-agent",
}


@pytest.fixture(scope="module")
def s() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ── Health ─────────────────────────────────────────────────────
class TestHealth:
    def test_health(self, s):
        r = s.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "profitengine-v5"


# ── Agents (7) ─────────────────────────────────────────────────
class TestAgents:
    def test_list_seven_agents(self, s):
        r = s.get(f"{API}/agents", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 7
        ids = {a["id"] for a in data}
        assert ids == EXPECTED_AGENTS, f"missing: {EXPECTED_AGENTS - ids}"

    def test_sovereign_is_orchestrator(self, s):
        data = s.get(f"{API}/agents", timeout=15).json()
        sov = next(a for a in data if a["id"] == "sovereign-v1")
        assert sov["tier"] == "sovereign"
        assert sov["type"] == "orchestrator"

    def test_execute_known_agent(self, s):
        r = s.post(f"{API}/agents/scout-agent/execute", json={}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "run_id" in body and body["agent_id"] == "scout-agent"

    def test_execute_unknown_agent_404(self, s):
        r = s.post(f"{API}/agents/does-not-exist/execute", json={}, timeout=15)
        assert r.status_code == 404


# ── Sovereign ──────────────────────────────────────────────────
class TestSovereign:
    def test_status(self, s):
        r = s.get(f"{API}/sovereign/status", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "model" in body
        assert "next_cycle_in_min" in body
        assert "safety" in body
        assert "circuit_breaker" in body["safety"]

    def test_decisions(self, s):
        r = s.get(f"{API}/sovereign/decisions", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 4
        for d in data:
            assert d["verdict"] in ("approve", "veto", "hold")
            assert "confidence" in d and "rationale" in d


# ── Approvals ──────────────────────────────────────────────────
class TestApprovals:
    def test_list(self, s):
        r = s.get(f"{API}/approvals", timeout=15)
        assert r.status_code == 200
        assert len(r.json()) == 5

    def test_decide_approve(self, s):
        r = s.post(f"{API}/approvals/apr_001/decide",
                   json={"decision": "approve"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["decision"] == "approve"

    def test_decide_bogus_returns_400(self, s):
        r = s.post(f"{API}/approvals/apr_001/decide",
                   json={"decision": "bogus"}, timeout=15)
        assert r.status_code == 400

    def test_decide_missing_id_returns_404(self, s):
        r = s.post(f"{API}/approvals/apr_999/decide",
                   json={"decision": "approve"}, timeout=15)
        assert r.status_code == 404


# ── Advisor ────────────────────────────────────────────────────
class TestAdvisor:
    def test_ask(self, s):
        r = s.post(f"{API}/advisor/ask",
                   json={"question": "How should I allocate budget?"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["agent"] == "sovereign-v1"
        assert len(body["answer"]) > 0

    def test_empty_question_400(self, s):
        r = s.post(f"{API}/advisor/ask", json={"question": ""}, timeout=15)
        assert r.status_code == 400


# ── Revenue + ledger ───────────────────────────────────────────
class TestRevenue:
    def test_streams(self, s):
        r = s.get(f"{API}/revenue/streams", timeout=15)
        assert r.status_code == 200
        assert len(r.json()) == 5

    def test_stats(self, s):
        r = s.get(f"{API}/revenue/stats", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "active_streams" in body and "best_stream" in body

    def test_ledger_progress(self, s):
        r = s.get(f"{API}/ledger/progress", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["goal_usd"] == 25000
        assert 0.0 <= body["pct"] <= 1.0


# ── Ops endpoints (must all return 200) ────────────────────────
class TestOps:
    @pytest.mark.parametrize("path", [
        "/scout/opportunities", "/deployments", "/builds", "/audit",
        "/books", "/proposals", "/secrets", "/cost", "/proof-of-work",
        "/distillation/status", "/analytics", "/cycle/status",
    ])
    def test_ops_endpoint_200(self, s, path):
        r = s.get(f"{API}{path}", timeout=15)
        assert r.status_code == 200, f"{path} → {r.status_code}"

    def test_scout_opportunities_shape(self, s):
        opps = s.get(f"{API}/scout/opportunities", timeout=15).json()
        assert len(opps) >= 4
        for o in opps:
            assert "velocity" in o and "estimated_yield_usd" in o

    def test_audit_minimum_rows(self, s):
        assert len(s.get(f"{API}/audit", timeout=15).json()) >= 7

    def test_distillation_routing(self, s):
        d = s.get(f"{API}/distillation/status", timeout=15).json()
        routing = d["tier_routing"]
        assert {"local", "groq", "gemini", "claude"} <= set(routing)

    def test_cost_categories(self, s):
        c = s.get(f"{API}/cost", timeout=15).json()
        assert "categories" in c and len(c["categories"]) >= 4

    def test_secrets_six_rows(self, s):
        sec = s.get(f"{API}/secrets", timeout=15).json()
        assert len(sec) == 6
        # values are never returned
        for row in sec:
            assert "value" not in row

    def test_deployments_five(self, s):
        assert len(s.get(f"{API}/deployments", timeout=15).json()) == 5

    def test_builds_five(self, s):
        b = s.get(f"{API}/builds", timeout=15).json()
        assert len(b) == 5
        statuses = {x["status"] for x in b}
        assert statuses & {"success", "failed"}

    def test_books_three(self, s):
        assert len(s.get(f"{API}/books", timeout=15).json()) == 3

    def test_proposals_three(self, s):
        assert len(s.get(f"{API}/proposals", timeout=15).json()) == 3

    def test_proof_of_work_metrics(self, s):
        p = s.get(f"{API}/proof-of-work", timeout=15).json()
        for key in ("score", "uptime_pct", "passed_cycles_24h",
                    "failed_cycles_24h", "signed_assets_24h", "guard_blocks_24h"):
            assert key in p


# ── Stats ──────────────────────────────────────────────────────
class TestStats:
    def test_stats_includes_sovereign_and_pow(self, s):
        r = s.get(f"{API}/stats", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "sovereign_decisions_today" in body
        assert "proof_of_work_score" in body
        assert body["devs_joined"] > 0


# ── Code merger ────────────────────────────────────────────────
_WEAK = """
def add(a, b):
    return a + b
"""
_STRONG = """
def add(a: int, b: int) -> int:
    \"\"\"Return a + b with input validation.\"\"\"
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("numeric expected")
    return a + b
"""


class TestMerger:
    def test_python_weak_to_strong_yields_upgrade(self, s):
        r = s.post(f"{API}/merge",
                   json={"language": "python", "base": _WEAK, "target": _STRONG},
                   timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert len(body["upgrades"]) >= 1

    def test_bad_syntax_returns_400(self, s):
        r = s.post(f"{API}/merge",
                   json={"language": "python", "base": "def x(:\n  pass",
                         "target": "def x(): pass"},
                   timeout=15)
        assert r.status_code == 400

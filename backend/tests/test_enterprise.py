"""ProfitEngineV5 enterprise blueprint endpoints — autonomy, lifelong, manifest."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ── Autonomy ────────────────────────────────────────────────────
class TestAutonomy:
    def test_get_autonomy_default_or_persisted(self, s):
        # Reset to L3 first to make the default test deterministic
        s.put(f"{API}/autonomy", json={"level": "L3"}, timeout=10)
        r = s.get(f"{API}/autonomy", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["level"] == "L3"
        assert body["mode"] == "Bounded Autonomy"
        assert "meaning" in body
        assert set(body["levels"].keys()) == {"L0", "L1", "L2", "L3", "L4", "L5"}
        assert isinstance(body["approval_required_for"], list)
        assert len(body["approval_required_for"]) == 8

    def test_set_autonomy_persists(self, s):
        r = s.put(f"{API}/autonomy", json={"level": "L4"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["level"] == "L4"
        assert r.json()["mode"] == "Enterprise Autonomy"
        # GET reflects change
        g = s.get(f"{API}/autonomy", timeout=10).json()
        assert g["level"] == "L4"
        # restore L3
        s.put(f"{API}/autonomy", json={"level": "L3"}, timeout=10)

    def test_invalid_level_422(self, s):
        r = s.put(f"{API}/autonomy", json={"level": "L9"}, timeout=10)
        assert r.status_code == 422


# ── Lifelong issues ─────────────────────────────────────────────
class TestLifelong:
    REQUIRED_FIELDS = {
        "id", "detected_issue", "root_cause", "business_impact",
        "recommended_correction", "assigned_agent", "risk_level",
        "expected_improvement", "status", "result_after_correction",
        "detected_at",
    }

    def test_returns_seeded_issues(self, s):
        r = s.get(f"{API}/lifelong/issues", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        for row in data:
            assert self.REQUIRED_FIELDS <= set(row.keys()), f"missing: {self.REQUIRED_FIELDS - set(row.keys())}"

    def test_limit_too_high_returns_400(self, s):
        r = s.get(f"{API}/lifelong/issues?limit=201", timeout=10)
        assert r.status_code == 400


# ── Enterprise manifest ────────────────────────────────────────
class TestManifest:
    def test_manifest_shape(self, s):
        r = s.get(f"{API}/enterprise/manifest", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["system"]["name"] == "ProfitEngineV5"
        assert body["system"]["autonomy_level"] == "L3"
        assert body["system"]["security_model"] == "zero_trust_hardened"
        assert isinstance(body["objectives"]["primary"], list)
        assert isinstance(body["objectives"]["blocked"], list)
        assert "revenue_equation" in body
        assert isinstance(body["loop"], list) and len(body["loop"]) >= 5


# ── Agent rename regression ────────────────────────────────────
class TestAgentRenames:
    def test_prime_orchestrator_name(self, s):
        agents = s.get(f"{API}/agents", timeout=10).json()
        sov = next(a for a in agents if a["id"] == "sovereign-orchestrator")
        assert sov["name"] == "Prime Orchestrator"

    def test_failure_analysis_agent_name(self, s):
        agents = s.get(f"{API}/agents", timeout=10).json()
        lcc = next(a for a in agents if a["id"] == "lifelong-catch-correct")
        assert lcc["name"] == "Failure Analysis Agent"

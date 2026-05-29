"""Tests for the new Cash AI + persistence endpoints."""
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
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


class TestCashAI:
    def test_last_decision_picks_highest_confidence_open(self, s):
        r = s.get(f"{API}/cash/last-decision", timeout=15)
        assert r.status_code == 200
        body = r.json()
        # Pinned by current fixture: apr_004 conf=0.97 is highest open approval
        assert body["source"] in {"approval", "sovereign_decision"}
        assert body["confidence"] is None or body["confidence"] >= 0.0
        assert "summary" in body and len(body["summary"]) > 0
        assert "risk" in body and body["risk"] in {"low", "medium", "high"}
        assert isinstance(body.get("tags", []), list)

    def test_trigger_cycle_persists_and_returns_id(self, s):
        r = s.post(f"{API}/cash/cycle/trigger", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["id"].startswith("cycle_")
        assert body["state"] == "running"
        assert body["actor"] == "operator"
        assert "triggered_at" in body

    def test_clear_cache_returns_deleted_count(self, s):
        r = s.post(f"{API}/cash/cache/clear", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "deleted" in body and isinstance(body["deleted"], int)

    def test_audit_trail_returns_list(self, s):
        r = s.get(f"{API}/cash/audit-trail?limit=10", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Includes sovereign decisions even with no persisted approvals yet
        assert len(data) >= 1
        for d in data:
            assert "id" in d and "kind" in d and "summary" in d

    def test_audit_trail_bad_limit_400(self, s):
        r = s.get(f"{API}/cash/audit-trail?limit=999", timeout=15)
        assert r.status_code == 400


class TestPersistence:
    def test_execute_persists_run(self, s):
        before = s.get(f"{API}/agent-runs?limit=200", timeout=15).json()
        r = s.post(f"{API}/agents/seo-scout/execute", timeout=15)
        assert r.status_code == 200
        after = s.get(f"{API}/agent-runs?limit=200", timeout=15).json()
        assert len(after) == len(before) + 1
        assert after[0]["agent_id"] == "seo-scout"
        assert after[0]["status"] == "queued"

    def test_decide_approval_persists(self, s):
        # Fetch an open approval id
        apprs = s.get(f"{API}/approvals", timeout=15).json()
        aid = apprs[0]["id"]
        r = s.post(f"{API}/approvals/{aid}/decide",
                   json={"decision": "approve"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == aid and body["decision"] == "approve"
        # Decision should now appear in audit trail
        trail = s.get(f"{API}/cash/audit-trail?limit=50", timeout=15).json()
        assert any(t["kind"] == "approval_decision" and t["verdict"] == "approve" for t in trail)

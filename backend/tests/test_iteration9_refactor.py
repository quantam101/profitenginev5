"""Iteration 9 — verify post-refactor behaviour of launch_router & distillation.

These tests hit the LIVE preview URL (REACT_APP_BACKEND_URL) and validate the
public contracts that the refactor must preserve.
"""
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to local supervisor backend for in-container runs
    BASE_URL = "http://localhost:8001"


# ---------- launch_router refactor ----------
class TestLaunchRouterRefactor:
    def test_checkout_packages_three(self):
        r = requests.get(f"{BASE_URL}/api/checkout/packages", timeout=15)
        assert r.status_code == 200
        data = r.json()
        # API returns {"packages": {id: {...}, ...}}
        packages = data.get("packages", data)
        if isinstance(packages, dict):
            ids = set(packages.keys())
        else:
            ids = {p["id"] for p in packages}
        assert {"studio_monthly", "studio_annual", "holding_deposit"}.issubset(ids)

    def test_checkout_session_invalid_package_400(self):
        r = requests.post(
            f"{BASE_URL}/api/checkout/session",
            json={"package_id": "bogus", "origin_url": "https://example.com"},
            timeout=15,
        )
        assert r.status_code == 400

    def test_checkout_session_invalid_origin_400(self):
        r = requests.post(
            f"{BASE_URL}/api/checkout/session",
            json={"package_id": "studio_monthly", "origin_url": "not-a-url"},
            timeout=15,
        )
        assert r.status_code == 400

    def test_checkout_session_valid_returns_url(self):
        r = requests.post(
            f"{BASE_URL}/api/checkout/session",
            json={
                "package_id": "studio_monthly",
                "origin_url": "https://example.com",
            },
            timeout=20,
        )
        # 200 happy path, or 502 if stripe unreachable in preview
        assert r.status_code in (200, 502)
        if r.status_code == 200:
            body = r.json()
            assert "url" in body or "session_id" in body

    def test_webhook_missing_signature_400(self):
        r = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        assert r.status_code in (400, 401)

    def test_social_proof_shape(self):
        r = requests.get(f"{BASE_URL}/api/launch/social-proof", timeout=15)
        assert r.status_code == 200
        body = r.json()
        for k in (
            "operators_joined",
            "paid_subscribers",
            "agent_runs_total",
            "cycles_ran_total",
            "merges_total",
            "engine_status",
            "uptime_pct",
            "at",
        ):
            assert k in body, f"missing {k}"
        assert body["engine_status"] == "operational"

    def test_cohort_shape(self):
        r = requests.get(f"{BASE_URL}/api/launch/cohort", timeout=15)
        assert r.status_code == 200
        body = r.json()
        for k in ("label", "total_seats", "claimed", "remaining", "closes_at", "pct_full"):
            assert k in body

    def test_referral_empty_400(self):
        r = requests.post(f"{BASE_URL}/api/referral/track", json={"code": ""}, timeout=15)
        assert r.status_code == 400

    def test_referral_too_long_400(self):
        r = requests.post(f"{BASE_URL}/api/referral/track", json={"code": "x" * 65}, timeout=15)
        assert r.status_code == 400

    def test_referral_valid_then_stats(self):
        code = f"TESTREF{int(time.time())}"
        r = requests.post(f"{BASE_URL}/api/referral/track", json={"code": code}, timeout=15)
        assert r.status_code == 200
        s = requests.get(f"{BASE_URL}/api/referral/stats/{code}", timeout=15)
        assert s.status_code == 200
        b = s.json()
        for k in ("code", "clicks", "conversions", "conversion_rate"):
            assert k in b
        assert b["code"] == code

    def test_subscriptions_me_unknown(self):
        r = requests.get(
            f"{BASE_URL}/api/subscriptions/me",
            params={"email": "noone@example.com"},
            timeout=15,
        )
        assert r.status_code == 200
        b = r.json()
        assert b.get("active") is False
        assert b.get("tier") == "operator"


# ---------- distillation refactor ----------
class TestDistillationRefactor:
    def test_distillation_run_envelope(self):
        # The live route is /api/distillation/distill with {prompt, task}
        payload = {"prompt": "Summarize refactor verification quickly.", "task": "summarize"}
        r = requests.post(f"{BASE_URL}/api/distillation/distill", json=payload, timeout=90)
        assert r.status_code == 200, r.text
        body = r.json()
        # Must include tier and notes per refactor contract
        assert "tier" in body
        assert body["tier"] in ("cache", "cheap", "expensive", "errored")
        for k in ("tokens_in", "tokens_out", "cost_usd", "latency_ms", "notes"):
            assert k in body, f"missing {k}"

    def test_distillation_stats(self):
        r = requests.get(f"{BASE_URL}/api/distillation/stats", timeout=15)
        assert r.status_code == 200
        body = r.json()
        # Aggregate counts present
        assert isinstance(body, dict)


# ---------- Cash AI / Enterprise smoke ----------
class TestCashAndEnterprise:
    def test_cash_last_decision(self):
        # Try both naming variants
        for path in ("/api/cash/last-decision", "/api/cash-ai/last-decision"):
            r = requests.get(f"{BASE_URL}{path}", timeout=15)
            if r.status_code == 200:
                assert isinstance(r.json(), dict)
                return
        pytest.fail("Neither /api/cash/last-decision nor /api/cash-ai/last-decision returned 200")

    def test_cash_audit(self):
        r = requests.get(f"{BASE_URL}/api/cash/audit-trail", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, (list, dict))

    def test_cash_trigger(self):
        r = requests.post(f"{BASE_URL}/api/cash/cycle/trigger", json={}, timeout=30)
        assert r.status_code == 200, r.text

    def test_enterprise_manifest(self):
        r = requests.get(f"{BASE_URL}/api/enterprise/manifest", timeout=15)
        assert r.status_code == 200

    def test_enterprise_agents(self):
        r = requests.get(f"{BASE_URL}/api/agents", timeout=15)
        assert r.status_code == 200
        agents = r.json()
        items = agents if isinstance(agents, list) else agents.get("agents", [])
        assert len(items) >= 1

    def test_agent_execute_smoke(self):
        r = requests.get(f"{BASE_URL}/api/agents", timeout=15)
        agents = r.json()
        items = agents if isinstance(agents, list) else agents.get("agents", [])
        assert items
        agent_id = items[0].get("id") or items[0].get("agent_id")
        ex = requests.post(
            f"{BASE_URL}/api/agents/{agent_id}/execute",
            json={"prompt": "smoke"},
            timeout=60,
        )
        assert ex.status_code in (200, 202), ex.text

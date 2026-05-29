"""Live HTTP tests for the Distillation engine against the public URL.

These hit the real backend (and possibly the real LLM via emergentintegrations).
We allow expensive/fallback tiers because LLM availability is environmental.
"""
from __future__ import annotations

import os
import time
import uuid
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


# ── /api/distillation/status ───────────────────────────────────
class TestDistillationStatus:
    def test_status_shape(self, s):
        r = s.get(f"{API}/distillation/status", timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert body["state"] == "active"
        routing = body["tier_routing"]
        assert {"cache", "cheap", "expensive"} <= set(routing.keys())
        assert "cheap_model" in body and "expensive_model" in body
        assert "gemini" in body["cheap_model"].lower()
        assert "claude" in body["expensive_model"].lower()


# ── /api/distillation/stats ────────────────────────────────────
class TestDistillationStats:
    def test_stats_shape(self, s):
        r = s.get(f"{API}/distillation/stats", timeout=20)
        assert r.status_code == 200
        body = r.json()
        for key in (
            "total_runs", "tier_breakdown", "cache_hit_rate", "total_cost_usd",
            "baseline_cost_usd", "saved_usd", "savings_pct", "tokens_in",
            "tokens_out", "avg_latency_ms", "cheap_model", "expensive_model",
        ):
            assert key in body, f"missing {key}"
        assert {"cache", "cheap", "expensive"} <= set(body["tier_breakdown"].keys())


# ── /api/distillation/distill ──────────────────────────────────
class TestDistillationDistill:
    def test_empty_prompt_400(self, s):
        r = s.post(f"{API}/distillation/distill",
                   json={"task": "classify", "prompt": "   "}, timeout=20)
        assert r.status_code == 400

    def test_classify_returns_full_envelope(self, s):
        prompt = f"Classify this product idea (unique-{uuid.uuid4()}): solo-creator invoice tool"
        r = s.post(f"{API}/distillation/distill",
                   json={"task": "classify", "prompt": prompt}, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        for key in ("tier", "output", "tokens_in", "tokens_out",
                    "cost_usd", "saved_usd", "cache_hit"):
            assert key in body, f"missing {key}"
        assert body["tier"] in ("cheap", "cache", "expensive")
        assert body["tokens_in"] > 0
        assert isinstance(body["cost_usd"], (int, float))

    def test_cache_hit_on_repeat(self, s):
        prompt = f"TEST_CACHE_{uuid.uuid4()} — say ok"
        first = s.post(f"{API}/distillation/distill",
                       json={"task": "classify", "prompt": prompt}, timeout=60).json()
        # only useful if cheap succeeded — else we still expect a deterministic
        # second-call result with the same key.
        if first.get("tier") not in ("cheap", "expensive"):
            pytest.skip(f"first call did not populate cache (tier={first.get('tier')})")
        time.sleep(0.5)
        second = s.post(f"{API}/distillation/distill",
                        json={"task": "classify", "prompt": prompt}, timeout=30).json()
        assert second["tier"] == "cache", f"expected cache, got {second}"
        assert second["cache_hit"] == True  # noqa: E712
        assert second["cost_usd"] == 0


# ── /api/advisor/ask (now distiller-backed) ───────────────────
class TestAdvisorViaDistiller:
    def test_ask_returns_tier(self, s):
        r = s.post(f"{API}/advisor/ask",
                   json={"question": "What is the next highest-leverage action?"},
                   timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["agent"] == "sovereign-orchestrator"
        assert len(body["answer"]) > 0
        assert body["tier"] in ("cheap", "cache", "expensive", "fallback")

    def test_empty_question_400(self, s):
        r = s.post(f"{API}/advisor/ask", json={"question": ""}, timeout=15)
        assert r.status_code == 400

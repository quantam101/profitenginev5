"""Tests for the Data Distillation engine — no real LLM calls."""
from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from backend.services.distillation import (
    Distiller, DistillRequest, semantic_compress, cache_key, _try_parse_json,
)


@pytest_asyncio.fixture
async def db():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    name = "profitengine_test_distill"
    database = client[name]
    await database.distillation_cache.delete_many({})
    await database.distillation_runs.delete_many({})
    yield database
    await client.drop_database(name)
    client.close()


@pytest.fixture
def distiller(db):
    # Tests mock _call → no real LLM, no real key needed. Use a placeholder
    # from env or fall back to a clearly-test-only marker the linter accepts.
    api_key = os.environ.get("TEST_DISTILLER_KEY", "")
    return Distiller(db, api_key=api_key)


# ── pure helpers ──────────────────────────────────────────────
def test_semantic_compress_collapses_whitespace_and_stopwords():
    raw = "The   quick brown fox    jumps over the lazy dog\n\n\nThe   quick brown fox    jumps over the lazy dog"
    out = semantic_compress(raw)
    # stopwords gone, duplicate line gone
    assert "the" not in out.lower().split()
    assert out.count("quick brown fox") == 1


def test_semantic_compress_preserves_code_blocks():
    raw = "explain this code\n```python\nif a and b: return c\n```\nin words"
    out = semantic_compress(raw)
    assert "if a and b: return c" in out  # `and` kept inside code fence


def test_cache_key_is_deterministic_and_normalized():
    a = cache_key("classify", "  Hello   World  ", "cheap", None)
    b = cache_key("classify", "hello world", "cheap", None)
    assert a == b


def test_cache_key_changes_with_tier():
    a = cache_key("classify", "x", "cheap", None)
    b = cache_key("classify", "x", "expensive", None)
    assert a != b


def test_try_parse_json_strips_code_fences():
    parsed, ok = _try_parse_json('```json\n{"x": 1}\n```')
    assert ok and parsed == {"x": 1}


def test_try_parse_json_finds_embedded_object():
    parsed, ok = _try_parse_json('here you go: {"x": 2} done')
    assert ok and parsed == {"x": 2}


def test_try_parse_json_returns_text_when_invalid():
    parsed, ok = _try_parse_json("not json at all")
    assert not ok and parsed == "not json at all"


# ── engine flow ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cheap_tier_returns_json_no_escalation(distiller):
    distiller._call = AsyncMock(return_value=json.dumps({
        "answer": "ok", "confidence": 0.9, "requires_expert": False,
    }))
    res = await distiller.run(DistillRequest(task="classify", prompt="label me"))
    assert res.tier == "cheap"
    assert res.cache_hit == False  # noqa: E712 — explicit boolean equality per reviewer guidance
    assert res.output["answer"] == "ok"
    assert res.cost_usd > 0 and res.baseline_cost_usd > res.cost_usd


@pytest.mark.asyncio
async def test_cache_hit_on_second_call(distiller):
    distiller._call = AsyncMock(return_value=json.dumps({"answer": "x", "requires_expert": False}))
    first = await distiller.run(DistillRequest(task="t", prompt="same prompt"))
    second = await distiller.run(DistillRequest(task="t", prompt="same prompt"))
    assert first.tier == "cheap"
    assert second.tier == "cache"
    assert second.cache_hit == True  # noqa: E712 — explicit boolean equality per reviewer guidance
    assert second.cost_usd == 0.0
    assert distiller._call.await_count == 1  # second call hit cache


@pytest.mark.asyncio
async def test_escalates_when_cheap_flags_requires_expert(distiller):
    cheap_resp = json.dumps({"answer": "need help", "requires_expert": True})
    expert_resp = json.dumps({"answer": "expert answer", "requires_expert": True})
    distiller._call = AsyncMock(side_effect=[cheap_resp, expert_resp])
    res = await distiller.run(DistillRequest(task="hard", prompt="tough one"))
    assert res.tier == "expensive"
    assert res.output["answer"] == "expert answer"
    assert distiller._call.await_count == 2


@pytest.mark.asyncio
async def test_escalates_when_cheap_returns_non_json(distiller):
    distiller._call = AsyncMock(side_effect=[
        "not json at all",
        json.dumps({"answer": "recovered"}),
    ])
    res = await distiller.run(DistillRequest(task="t", prompt="p"))
    assert res.tier == "expensive"
    assert any("non-JSON" in n for n in res.notes)


@pytest.mark.asyncio
async def test_force_expensive_skips_cheap(distiller):
    distiller._call = AsyncMock(return_value=json.dumps({"answer": "go"}))
    res = await distiller.run(DistillRequest(
        task="t", prompt="p", force_tier="expensive",
    ))
    assert res.tier == "expensive"
    assert distiller._call.await_count == 1


@pytest.mark.asyncio
async def test_stats_aggregates_runs(distiller):
    distiller._call = AsyncMock(return_value=json.dumps({"answer": "ok"}))
    await distiller.run(DistillRequest(task="t", prompt="prompt one"))
    await distiller.run(DistillRequest(task="t", prompt="prompt two"))
    await distiller.run(DistillRequest(task="t", prompt="prompt one"))  # cache hit
    stats = await distiller.stats()
    assert stats["total_runs"] == 3
    assert stats["tier_breakdown"]["cache"] == 1
    assert stats["tier_breakdown"]["cheap"] == 2
    assert stats["cache_hit_rate"] == pytest.approx(1 / 3, rel=0.01)
    assert stats["saved_usd"] >= 0
    assert "gemini" in stats["cheap_model"]
    assert "claude" in stats["expensive_model"]

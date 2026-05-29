"""Unit tests for the distillation engine — runs in CI Stage 1."""
import pytest

from distillation import (
    DistillationCache,
    DistillationEngine,
    compress,
    count_tokens,
    route_tier,
    strip_html,
    yaml_vs_json,
)
from distillation.router import Tier


# ── compression ──────────────────────────────────────────────────
def test_strip_html_removes_tags_and_comments():
    raw = "<p>hello <b>world</b><!-- secret --></p>"
    assert "hello" in strip_html(raw) and "<" not in strip_html(raw)


def test_compress_reduces_tokens():
    raw = "The quick brown fox is in the very small box and the dog is happy."
    compressed, stats = compress(raw)
    assert stats.compressed_tokens < stats.original_tokens
    assert stats.savings_pct > 0


def test_compress_can_handle_empty_string():
    out, stats = compress("")
    assert out == "" and stats.original_tokens == 0


def test_count_tokens_basic():
    assert count_tokens("") == 0
    assert count_tokens("abcd") == 1
    assert count_tokens("a" * 100) == 25


def test_yaml_vs_json_returns_token_diff():
    res = yaml_vs_json({"a": 1, "b": [1, 2, 3], "c": {"nested": True}})
    assert "json_tokens" in res and "yaml_tokens" in res
    assert res["yaml_tokens"] <= res["json_tokens"] or res["yaml_savings_pct"] >= -0.1


# ── router ───────────────────────────────────────────────────────
def test_router_low_for_deterministic_task():
    d = route_tier("name: bob", task="format")
    assert d.tier is Tier.LOW
    assert d.estimated_cost_usd == 0.0


def test_router_high_for_reasoning_task():
    d = route_tier("design a kubernetes cluster", task="architect")
    assert d.tier is Tier.HIGH


def test_router_escalates_on_huge_input():
    big = "word " * 1500
    d = route_tier(big, task="summarize")
    assert d.tier is Tier.HIGH


def test_router_mid_for_normal_summary():
    d = route_tier("ten lines of normal text", task="summarize")
    assert d.tier is Tier.MID


# ── cache ────────────────────────────────────────────────────────
def test_cache_hit_after_put():
    c = DistillationCache()
    c.put("summary", "hello world", value={"out": "hi"}, saved_tokens=120)
    assert c.get("summary", "hello world") == {"out": "hi"}
    assert c.stats()["hits"] == 1
    assert c.stats()["tokens_saved"] == 120


def test_cache_miss_for_different_task():
    c = DistillationCache()
    c.put("summary", "x", value=1)
    assert c.get("translate", "x") is None
    assert c.stats()["misses"] == 1


def test_cache_evicts_lru_when_full():
    c = DistillationCache(max_entries=2)
    c.put("t", "a", 1)
    c.put("t", "b", 2)
    c.put("t", "c", 3)
    assert c.get("t", "a") is None
    assert c.get("t", "c") == 3


# ── engine end-to-end ────────────────────────────────────────────
def test_engine_distill_returns_compressed_text_and_routing():
    eng = DistillationEngine()
    r = eng.distill("<p>The very long text about a quick fox</p>", task="summarize")
    assert r.compression.savings_pct > 0
    assert r.tier in {"low", "mid", "high"}
    assert "JSON" in r.suggested_system_prompt
    assert r.cache_hit is False


def test_engine_remember_then_cache_hit():
    eng = DistillationEngine()
    eng.remember("summary", "hello world", {"out": "hi"})
    r = eng.distill("hello world", task="summary")
    assert r.cache_hit is True
    assert r.served_value == {"out": "hi"}
    assert r.estimated_cost_usd == 0.0


def test_engine_metrics_expose_hit_rate():
    eng = DistillationEngine()
    eng.remember("t", "a", 1)
    eng.distill("a", task="t")  # hit
    eng.distill("b", task="t")  # miss
    m = eng.metrics()
    assert m["hits"] == 1 and m["misses"] == 1
    assert m["hit_rate"] == 0.5

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pandas as pd
import pytest

import runtime.regional_trends as rt


def _install_fake_pytrends(monkeypatch, interest_by_region_df=None, side_effect=None):
    """Inject a fake ``pytrends`` module whose TrendReq is a mock."""
    fake_pkg = ModuleType("pytrends")
    fake_req_mod = ModuleType("pytrends.request")
    trend_req = MagicMock(name="TrendReq")
    instance = trend_req.return_value
    if side_effect is not None:
        instance.interest_by_region.side_effect = side_effect
    else:
        instance.interest_by_region.return_value = interest_by_region_df
    fake_req_mod.TrendReq = trend_req
    monkeypatch.setitem(sys.modules, "pytrends", fake_pkg)
    monkeypatch.setitem(sys.modules, "pytrends.request", fake_req_mod)
    return trend_req


def _df(values: dict) -> pd.DataFrame:
    """One-column interest frame: {region: interest} for keyword 'kw'."""
    return pd.DataFrame({"kw": pd.Series(values)})


def test_interest_by_region_returns_sorted_cities(monkeypatch):
    df = _df({"Phoenix": 100, "Tucson": 60, "Mesa": 80})
    _install_fake_pytrends(monkeypatch, interest_by_region_df=df)

    ranked = rt.interest_by_region("kw")

    assert ranked[0] == ("Phoenix", 100.0)
    assert [r for r, _ in ranked] == ["Phoenix", "Mesa", "Tucson"]


def test_rank_by_regional_interest_orders_keywords(monkeypatch):
    def fake_interest(keyword, geo="US", timeframe="today 12-m"):
        data = {"alpha": [("Phoenix", 10.0)], "beta": [("Phoenix", 90.0)]}
        return data.get(keyword, [])

    monkeypatch.setattr(rt, "interest_by_region", fake_interest)
    monkeypatch.setattr(rt, "_CALL_DELAY_S", 0)

    ranked = rt.rank_by_regional_interest(["alpha", "beta", "gamma"])

    assert ranked == ["beta", "alpha", "gamma"]


def test_rank_by_regional_interest_degrades_to_input_order(monkeypatch):
    # No pytrends module installed → interest_by_region returns []
    monkeypatch.setattr(rt, "_load_trendreq", lambda: None)

    keywords = ["one", "two", "three"]
    assert rt.rank_by_regional_interest(keywords) == keywords


def test_interest_by_region_handles_rate_limit(monkeypatch):
    _install_fake_pytrends(monkeypatch, side_effect=Exception("HTTP 429"))

    assert rt.interest_by_region("kw") == []


def test_rank_cities_by_interest(monkeypatch):
    monkeypatch.setattr(
        rt,
        "interest_by_region",
        lambda kw, geo="US", timeframe="today 12-m": [
            ("Phoenix", 100.0), ("Tucson", 50.0)
        ],
    )

    cities = [("Tucson", "AZ"), ("Mesa", "AZ"), ("Phoenix", "AZ")]
    ranked = rt.rank_cities_by_interest("it support", cities)

    assert ranked[0] == ("Phoenix", "AZ")
    assert ranked[1] == ("Tucson", "AZ")


def test_trend_scanner_reranks_via_regional_signal(monkeypatch):
    """Agent wires the optional signal in and reports the metric."""
    from runtime.agent_impls import trend_scanner as ts

    monkeypatch.setattr(ts, "_hackernews_topics", lambda: ["topic a", "topic b"])
    monkeypatch.setattr(ts, "_reddit_topics", lambda: [])
    monkeypatch.setattr(ts, "_github_trending_topics", lambda: [])
    monkeypatch.setattr(ts, "infer", lambda *a, **k: ("[]", 0))

    calls = {}

    def fake_rank(topics, geo="US", timeframe="today 12-m"):
        calls["topics"] = list(topics)
        return list(reversed(topics))

    monkeypatch.setattr(rt, "rank_by_regional_interest", fake_rank)

    execution = ts.Agent().run("objective", "context", [])

    assert calls["topics"] == ["topic a", "topic b"]
    assert execution.metrics["regional_ranked"] is True

"""Tests for runtime.learning_signals — the measured-results feedback loop."""

import json
from datetime import date
from pathlib import Path

from runtime.learning_signals import (
    collect_signals,
    topic_hint,
    write_signals,
)


def _concluded_ledger(base: Path) -> Path:
    ledger = base / "data" / "experiments" / "ledger.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {"type": "created", "id": "exp-1", "hypothesis": "question titles beat statements",
         "metric": "ctr", "variants": ["topic:statement-style", "topic:question-style"], "at": "2026-01-01"},
        {"type": "started", "id": "exp-1", "at": "2026-01-01"},
        *[{"type": "observation", "id": "exp-1", "variant": "topic:statement-style",
           "value": v, "at": "2026-01-02"} for v in (0.02, 0.03, 0.025)],
        *[{"type": "observation", "id": "exp-1", "variant": "topic:question-style",
           "value": v, "at": "2026-01-02"} for v in (0.05, 0.06, 0.055)],
        {"type": "concluded", "id": "exp-1", "winner": "topic:question-style",
         "reason": "question-style mean 0.055 > statement-style 0.025", "at": "2026-01-03"},
    ]
    ledger.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return base


def test_empty_state_yields_empty_signals(tmp_path):
    signals = collect_signals(tmp_path)
    assert signals["winning_variants"] == []
    assert signals["topic_hints"] == []
    assert signals["top_revenue_sources"] == []
    assert topic_hint(tmp_path, on_date=date(2026, 1, 5)) is None


def test_concluded_experiment_surfaces_winner(tmp_path):
    _concluded_ledger(tmp_path)
    signals = collect_signals(tmp_path)
    assert len(signals["winning_variants"]) == 1
    w = signals["winning_variants"][0]
    assert w["winner"] == "topic:question-style"
    assert w["winner_mean"] is not None
    assert signals["topic_hints"] == ["question-style"]
    # 1-hint pool has len+1 = 2 slots: even idx → hint, odd idx → rotation.
    hint_day = next(d for d in range(1, 8) if date(2026, 1, d).toordinal() % 2 == 0)
    rest_day = next(d for d in range(1, 8) if date(2026, 1, d).toordinal() % 2 == 1)
    assert topic_hint(tmp_path, on_date=date(2026, 1, hint_day)) == "question-style"
    assert topic_hint(tmp_path, on_date=date(2026, 1, rest_day)) is None


def test_unconcluded_experiments_do_not_leak(tmp_path):
    _concluded_ledger(tmp_path)
    ledger = tmp_path / "data" / "experiments" / "ledger.jsonl"
    with ledger.open("a") as f:
        f.write(json.dumps({"type": "created", "id": "exp-2", "hypothesis": "x",
                            "metric": "ctr", "variants": ["topic:a", "topic:b"],
                            "at": "2026-01-04"}) + "\n")
    signals = collect_signals(tmp_path)
    assert signals["topic_hints"] == ["question-style"]  # only the concluded one


def test_revenue_report_ranks_sources(tmp_path):
    (tmp_path / "daily_revenue_2026-01-05.json").write_text(json.dumps({
        "metrics": {
            "gumroad": {"total_revenue": 42.0, "last_24h": {"revenue": 3.5}},
            "stripe": {"total_revenue": 100.0},
            "youtube": {"revenue_24h": 7.0},
            "email": {"revenue_from_email": 12.0},
        }
    }))
    sources = collect_signals(tmp_path)["top_revenue_sources"]
    assert [s["source"] for s in sources] == ["stripe", "gumroad", "email", "youtube"]
    assert sources[0]["total_usd"] == 100.0


def test_write_signals_persists_json(tmp_path):
    _concluded_ledger(tmp_path)
    out = write_signals(tmp_path)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["signals_version"] == 1
    assert data["topic_hints"] == ["question-style"]


def test_committed_signals_are_preferred_over_local(tmp_path):
    """A fresh runner with only the committed file uses it — no ledger needed."""
    committed = tmp_path / "data" / "strategy" / "signals.json"
    committed.parent.mkdir(parents=True)
    committed.write_text(json.dumps({
        "signals_version": 1, "winning_variants": [],
        "topic_hints": ["committed-topic"], "channel_hints": [],
        "top_revenue_sources": []}))
    assert collect_signals(tmp_path)["topic_hints"] == ["committed-topic"]


def test_write_signals_recomputes_past_committed(tmp_path):
    """refresh must not freeze: it recomputes from data, not the old file."""
    committed = tmp_path / "data" / "strategy" / "signals.json"
    committed.parent.mkdir(parents=True)
    committed.write_text(json.dumps({"signals_version": 1, "topic_hints": ["stale"],
                                    "winning_variants": [], "channel_hints": [],
                                    "top_revenue_sources": []}))
    _concluded_ledger(tmp_path)
    out = write_signals(tmp_path)
    assert json.loads(out.read_text())["topic_hints"] == ["question-style"]


def test_corrupt_revenue_report_is_ignored(tmp_path):
    (tmp_path / "daily_revenue_bad.json").write_text("{not json")
    assert collect_signals(tmp_path)["top_revenue_sources"] == []

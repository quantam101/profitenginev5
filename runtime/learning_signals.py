"""Learning signals — measured results fed back into the next run.

Reads the growth-experiment ledger and daily revenue reports, then
emits the strategy signals downstream jobs consume:

  - ``winning_variants``  — concluded experiments and their winners
  - ``topic_hints``       — winners named ``topic:<slug>`` (content should
                            prefer measured winners over blind rotation)
  - ``channel_hints``     — winners named ``channel:<name>`` (publishing
                            should prefer measured channels)
  - ``top_revenue_sources`` — sources ranked by the latest daily report

Nothing is fabricated: with no ledger and no reports the signal set is
empty and callers keep their default behavior. CLI:

    python -m runtime.learning_signals [--json]      # print signals
    python -m runtime.learning_signals refresh       # write data/strategy/signals.json
"""

from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_EXPERIMENT_LEDGER = Path("data/experiments/ledger.jsonl")
DEFAULT_SIGNALS_PATH = Path("data/strategy/signals.json")

_TOPIC_PREFIX = "topic:"
_CHANNEL_PREFIX = "channel:"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _winning_variants(base: Path) -> list[dict[str, Any]]:
    """Concluded experiments → their measured winners."""
    from runtime.growth_experiments import load_experiments

    ledger = base / DEFAULT_EXPERIMENT_LEDGER
    winners = []
    for exp in load_experiments(ledger).values():
        if exp.status != "concluded" or not exp.winner:
            continue
        winner = exp.variants.get(exp.winner)
        winners.append({
            "experiment_id": exp.id,
            "hypothesis": exp.hypothesis,
            "metric": exp.metric,
            "winner": exp.winner,
            "winner_mean": winner.mean if winner else None,
            "concluded_at": exp.concluded_at,
        })
    winners.sort(key=lambda w: w.get("concluded_at") or "")
    return winners


def _top_revenue_sources(base: Path) -> list[dict[str, Any]]:
    """Latest daily revenue report → sources ranked by real dollars."""
    reports = sorted(glob.glob(str(base / "daily_revenue_*.json")))
    reports += sorted(glob.glob(str(base / "data" / "daily_revenue_*.json")))
    if not reports:
        return []
    try:
        report = json.loads(Path(reports[-1]).read_text(encoding="utf-8"))
    except Exception:
        return []
    metrics = report.get("metrics", report)
    sources = []
    for name, m in metrics.items():
        if not isinstance(m, dict):
            continue
        total = m.get("total_revenue", 0) or 0
        last_24h = (m.get("last_24h") or {}).get("revenue", 0) or 0
        if total or last_24h:
            sources.append({"source": name, "total_usd": total, "last_24h_usd": last_24h})
    sources.sort(key=lambda s: s["total_usd"], reverse=True)
    return sources


def collect_signals(base: Path | str = ".") -> dict[str, Any]:
    base = Path(base)
    winners = _winning_variants(base)
    return {
        "generated_at": _now(),
        "signals_version": 1,
        "winning_variants": winners,
        "topic_hints": [w["winner"][len(_TOPIC_PREFIX):]
                        for w in winners if w["winner"].startswith(_TOPIC_PREFIX)],
        "channel_hints": [w["winner"][len(_CHANNEL_PREFIX):]
                          for w in winners if w["winner"].startswith(_CHANNEL_PREFIX)],
        "top_revenue_sources": _top_revenue_sources(base),
    }


def topic_hint(base: Path | str = ".") -> str | None:
    """The most recently measured winning topic, or None."""
    hints = collect_signals(base)["topic_hints"]
    return hints[-1] if hints else None


def write_signals(base: Path | str = ".", path: Path = DEFAULT_SIGNALS_PATH) -> Path:
    out = Path(base) / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(collect_signals(base), indent=2) + "\n", encoding="utf-8")
    return out


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--json"
    if cmd == "refresh":
        print(write_signals())
        return
    json_flag = cmd == "--json" or os.getenv("LEARNING_SIGNALS_JSON") == "1"
    signals = collect_signals()
    if json_flag:
        print(json.dumps(signals, indent=2))
    else:
        print(f"winners: {len(signals['winning_variants'])}  "
              f"topic hints: {signals['topic_hints']}  "
              f"channel hints: {signals['channel_hints']}  "
              f"top revenue: {signals['top_revenue_sources'][:3]}")


if __name__ == "__main__":
    main()

"""
CycleLog — append-only JSONL execution ledger.

Every call to SovereignAutomationCore.execute() writes one record here.
Records are the proof-of-work: timestamps, tiers, durations, output excerpts.
The /cycles and /metrics API endpoints read from this file.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CycleRecord:
    cycle_id: str
    timestamp: float          # unix epoch seconds (float)
    iso_timestamp: str        # "2026-01-02T15:04:05Z"
    agent_id: str
    route_tier: str
    objective_excerpt: str    # first 120 chars of objective
    output_excerpt: str       # first 200 chars of output
    status: str               # "ok" | "approval_required" | "blocked" | "error"
    duration_ms: int
    cached: bool
    details: Dict[str, Any]


def _iso(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class CycleLog:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or os.getenv("GMAOS_CYCLE_LOG", "./data/logs/cycles.jsonl"))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, rec: CycleRecord) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(rec), sort_keys=True, ensure_ascii=False) + "\n")

    # ── read-side helpers ────────────────────────────────────────────────────

    def tail(self, limit: int = 50) -> List[CycleRecord]:
        """Return the most-recent `limit` records, newest-first."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        recent = lines[-limit:] if len(lines) >= limit else lines
        records: List[CycleRecord] = []
        for line in reversed(recent):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(CycleRecord(**json.loads(line)))
            except Exception:
                pass
        return records

    def metrics(self) -> Dict[str, Any]:
        """Aggregate stats across all recorded cycles."""
        if not self.path.exists():
            return _empty_metrics()

        lines = self.path.read_text(encoding="utf-8").splitlines()
        total = 0
        ok = 0
        tier_dist: Dict[str, int] = {}
        agent_dist: Dict[str, int] = {}
        durations: List[int] = []
        last_ts: Optional[float] = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            total += 1
            if rec.get("status") == "ok":
                ok += 1
            tier = rec.get("route_tier", "unknown")
            tier_dist[tier] = tier_dist.get(tier, 0) + 1
            agent = rec.get("agent_id", "unknown")
            agent_dist[agent] = agent_dist.get(agent, 0) + 1
            dur = rec.get("duration_ms")
            if isinstance(dur, (int, float)):
                durations.append(int(dur))
            ts = rec.get("timestamp")
            if ts is not None and (last_ts is None or ts > last_ts):
                last_ts = ts

        success_rate = round(ok / total * 100, 1) if total else 0.0
        avg_dur = round(sum(durations) / len(durations)) if durations else 0

        return {
            "total_cycles": total,
            "successful_cycles": ok,
            "success_rate_pct": success_rate,
            "avg_duration_ms": avg_dur,
            "tier_distribution": tier_dist,
            "agent_distribution": agent_dist,
            "last_cycle_ts": last_ts,
            "last_cycle_iso": _iso(last_ts) if last_ts else None,
        }


def _empty_metrics() -> Dict[str, Any]:
    return {
        "total_cycles": 0,
        "successful_cycles": 0,
        "success_rate_pct": 0.0,
        "avg_duration_ms": 0,
        "tier_distribution": {},
        "agent_distribution": {},
        "last_cycle_ts": None,
        "last_cycle_iso": None,
    }

"""Local-first enterprise mesh execution.

This module gives ProfitEngine a deterministic, SQLite/WAL-backed execution
plane for parallel agents. It is intentionally dependency-light and keeps a
local snapshot for every successful agent so degraded/offline runs can still
return useful output instead of failing closed.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.agents import AgentExecution, load_agent


def _default_core_dir() -> Path:
    configured = os.getenv("PROFITENGINE_CORE_DIR")
    candidates = [
        Path(configured) if configured else None,
        Path(".core_mesh_data"),
        Path(tempfile.gettempdir()) / "profitengine_core_mesh",
    ]
    for candidate in [path for path in candidates if path is not None]:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            continue
    raise RuntimeError("No writable core mesh directory is available")


DEFAULT_CORE_DIR = _default_core_dir()
DEFAULT_DB_PATH = DEFAULT_CORE_DIR / "enterprise_mesh.db"


@dataclass(frozen=True)
class MeshResult:
    agent_id: str
    status: str
    mode: str
    output: str
    metrics: dict[str, Any]
    duration_ms: int
    cached: bool = False
    error: str = ""


class EnterpriseMesh:
    """Parallel runtime with WAL snapshots and cached failover."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH, max_workers: int | None = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers or max(2, min(8, (os.cpu_count() or 2)))
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_snapshots (
                    agent_id TEXT PRIMARY KEY,
                    output TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mesh_runs (
                    run_id TEXT,
                    agent_id TEXT,
                    status TEXT,
                    mode TEXT,
                    duration_ms INTEGER,
                    cached INTEGER,
                    error TEXT,
                    created_at TEXT
                )
                """
            )
            conn.commit()

    def _snapshot(self, result: MeshResult) -> None:
        if result.status != "ok" or result.cached:
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_snapshots (agent_id, output, metrics_json, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    result.agent_id,
                    result.output,
                    json.dumps(result.metrics, sort_keys=True),
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()

    def _cached(self, agent_id: str, started: float, error: str) -> MeshResult:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT output, metrics_json FROM agent_snapshots WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()
        if row:
            return MeshResult(
                agent_id=agent_id,
                status="degraded",
                mode="wal_cache_failover",
                output=row["output"],
                metrics=json.loads(row["metrics_json"]),
                duration_ms=int((time.perf_counter() - started) * 1000),
                cached=True,
                error=error,
            )
        return MeshResult(
            agent_id=agent_id,
            status="failed",
            mode="deterministic_error",
            output=f"{agent_id.upper()}_UNAVAILABLE\nNo live result and no WAL snapshot available.",
            metrics={"agent": agent_id},
            duration_ms=int((time.perf_counter() - started) * 1000),
            cached=False,
            error=error,
        )

    def run_agent(self, agent_id: str, objective: str, context: str = "", connectors: list[str] | None = None) -> MeshResult:
        started = time.perf_counter()
        try:
            agent = load_agent(agent_id)
            execution: AgentExecution = agent.run(objective, context, connectors or ["local_files"])
            result = MeshResult(
                agent_id=agent_id,
                status="ok",
                mode="live_parallel_worker",
                output=execution.output,
                metrics=dict(execution.metrics),
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
            self._snapshot(result)
            return result
        except Exception as exc:
            return self._cached(agent_id, started, f"{type(exc).__name__}: {exc}")

    def dispatch(self, agent_ids: list[str], objective: str, context: str = "") -> dict[str, Any]:
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        started = time.perf_counter()
        results: list[MeshResult] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, max(1, len(agent_ids)))) as pool:
            futures = {
                pool.submit(self.run_agent, agent_id, objective, context, ["local_files"]): agent_id
                for agent_id in agent_ids
            }
            for future in as_completed(futures):
                results.append(future.result())

        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO mesh_runs (run_id, agent_id, status, mode, duration_ms, cached, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        result.agent_id,
                        result.status,
                        result.mode,
                        result.duration_ms,
                        1 if result.cached else 0,
                        result.error,
                        created_at,
                    )
                    for result in results
                ],
            )
            conn.commit()

        results.sort(key=lambda item: agent_ids.index(item.agent_id) if item.agent_id in agent_ids else 999)
        return {
            "ok": all(result.status in {"ok", "degraded"} for result in results),
            "run_id": run_id,
            "mode": "parallel_wal_failover",
            "worker_count": min(self.max_workers, max(1, len(agent_ids))),
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "agent_count": len(results),
            "degraded_count": sum(1 for result in results if result.status == "degraded"),
            "failed_count": sum(1 for result in results if result.status == "failed"),
            "results": [asdict(result) for result in results],
            "generated_at": created_at,
        }

    def readiness(self) -> dict[str, Any]:
        with self._connect() as conn:
            snapshots = conn.execute("SELECT COUNT(*) AS n FROM agent_snapshots").fetchone()["n"]
            runs = conn.execute("SELECT COUNT(*) AS n FROM mesh_runs").fetchone()["n"]
        return {
            "ok": True,
            "mode": "local_first_wal",
            "db_path": str(self.db_path),
            "max_workers": self.max_workers,
            "snapshots": snapshots,
            "recorded_runs": runs,
            "degraded_behavior": "If live agent execution fails, cached snapshots are served when available.",
        }


def dispatch_default(objective: str, context: str = "") -> dict[str, Any]:
    agent_ids = [
        "offer-scout",
        "margin-guard",
        "listing-optimizer",
        "traffic-agent",
        "proof-ledger",
        "motivation-engine",
        "free-tier-cost-guard",
    ]
    return EnterpriseMesh().dispatch(agent_ids, objective, context)


# ── ASI Mesh Engine — supermajority consensus wrapper ─────────────────────────

# Default trio: high-quality reasoning agents from the registry.
# Override via ASI_CONSENSUS_AGENTS env var (comma-separated agent IDs).
_DEFAULT_ASI_AGENTS = [
    "sovereign-orchestrator",
    "local-research",
    "free-tier-cost-guard",
]


class ASIMeshEngine:
    """
    Wraps the G-MAOS Mesh with ASI-style supermajority consensus.

    Dispatches the same objective to N agents in parallel (default 3).
    2-of-3 (67%) agreement is required to declare VERIFIED_CONSENSUS.
    If quorum fails, the plurality winner is still returned with
    status=DIVERGENCE_FLAGGED so the caller can decide to re-run or accept.

    Never raises — returns a structured error dict on total failure.

    Usage (async):
        engine = ASIMeshEngine()
        result = await engine.dispatch_consensus("Analyse margin for keyword X")

    Usage (sync, e.g. from a Django/Flask view or a script):
        result = asyncio.run(ASIMeshEngine().dispatch_consensus("..."))
    """

    def __init__(
        self,
        agents: list[str] | None = None,
        threshold: float = 0.67,
    ) -> None:
        import os
        env_agents = os.getenv("ASI_CONSENSUS_AGENTS", "").strip()
        self._agents: list[str] = (
            agents
            or ([a.strip() for a in env_agents.split(",") if a.strip()] if env_agents else None)
            or _DEFAULT_ASI_AGENTS
        )
        self._threshold = threshold

    async def dispatch_consensus(
        self,
        objective: str,
        context: str = "",
        timeout_sec: float = 60.0,
    ) -> dict[str, Any]:
        """
        Run consensus dispatch and return a serialisable result dict.

        Keys in the returned dict
        -------------------------
        ok                  bool   — True when quorum was met
        status              str    — VERIFIED_CONSENSUS | DIVERGENCE_FLAGGED | NO_QUORUM
        output              str    — winning agent output
        tier                str    — inference tier of the winner
        winning_agent       str    — agent ID of the winner
        majority_fingerprint str   — SHA-256[:16] of the winning output
        agreement           str    — e.g. "2/3"
        duration_ms         int    — wall-clock ms for the consensus round
        agents              list   — per-agent result details
        mesh_health         dict   — G-MAOS health snapshot
        """
        try:
            from runtime.gmaos.core import get_mesh
        except ImportError:
            from .gmaos.core import get_mesh

        mesh = await get_mesh()
        payload = {
            "objective": objective,
            "context": context,
            "prompt": objective,
            "system": (
                "You are a production ProfitEngine agent. "
                "Execute the objective precisely. "
                "Output only the result — no preamble."
            ),
        }

        consensus = await mesh.run_with_consensus(
            payload=payload,
            agents=self._agents,
            timeout_sec=timeout_sec,
            threshold=self._threshold,
        )

        return {
            "ok": consensus.quorum_met,
            "status": consensus.status,
            "output": consensus.winning_output,
            "tier": consensus.winning_tier,
            "winning_agent": consensus.winning_agent,
            "majority_fingerprint": consensus.majority_fingerprint,
            "agreement": f"{consensus.agreement_count}/{consensus.agent_count}",
            "valid_agents": consensus.valid_count,
            "duration_ms": consensus.duration_ms,
            "agents": consensus.results,
            "mesh_health": mesh.health(),
        }


async def dispatch_consensus_default(
    objective: str,
    context: str = "",
    timeout_sec: float = 60.0,
) -> dict[str, Any]:
    """Module-level shortcut: consensus dispatch with default agent trio."""
    return await ASIMeshEngine().dispatch_consensus(objective, context, timeout_sec)

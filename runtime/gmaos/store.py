"""
G-MAOS Storage Layer
====================
Three-tier persistence:

  L1  In-memory dict          — microsecond reads, lost on restart
  L2  SQLite WAL              — millisecond reads, survives crashes
  L3  Redis Streams (optional)— shared across replicas, auto-expires

Write-through: L1 ← L2 ← L3 (or L2 only if Redis absent).
Read-through:  L1 → L2 → L3 on misses.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("gmaos.store")


class _SqliteWAL:
    """Thread-safe SQLite store in WAL mode."""

    DDL = """
    CREATE TABLE IF NOT EXISTS task_state (
        task_id     TEXT PRIMARY KEY,
        agent       TEXT NOT NULL,
        status      TEXT NOT NULL,
        payload     TEXT NOT NULL DEFAULT '{}',
        output      TEXT NOT NULL DEFAULT '',
        tier        TEXT NOT NULL DEFAULT '',
        retry_count INTEGER NOT NULL DEFAULT 0,
        error       TEXT NOT NULL DEFAULT '',
        tokens_in   INTEGER NOT NULL DEFAULT 0,
        tokens_out  INTEGER NOT NULL DEFAULT 0,
        distilled   INTEGER NOT NULL DEFAULT 0,
        created_at  REAL NOT NULL,
        updated_at  REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_status     ON task_state(status);
    CREATE INDEX IF NOT EXISTS idx_updated_at ON task_state(updated_at);

    CREATE TABLE IF NOT EXISTS agent_snapshots (
        agent_id    TEXT PRIMARY KEY,
        output      TEXT NOT NULL,
        tier        TEXT NOT NULL DEFAULT '',
        distilled   INTEGER NOT NULL DEFAULT 0,
        tokens_in   INTEGER NOT NULL DEFAULT 0,
        tokens_out  INTEGER NOT NULL DEFAULT 0,
        captured_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS distill_log (
        log_id      TEXT PRIMARY KEY,
        task_id     TEXT NOT NULL,
        agent       TEXT NOT NULL,
        summary     TEXT NOT NULL,
        raw_tokens  INTEGER NOT NULL,
        out_tokens  INTEGER NOT NULL,
        ratio       REAL NOT NULL,
        created_at  REAL NOT NULL
    );
    """

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._lock = threading.Lock()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._bootstrap()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-8000")   # 8 MB page cache
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _bootstrap(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(self.DDL)

    # ── task_state ────────────────────────────────────────────────────────

    def upsert_task(self, task_id: str, agent: str, status: str,
                    payload: dict, output: str = "", tier: str = "",
                    retry_count: int = 0, error: str = "",
                    tokens_in: int = 0, tokens_out: int = 0,
                    distilled: bool = False) -> None:
        now = time.time()
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT INTO task_state
                    (task_id, agent, status, payload, output, tier,
                     retry_count, error, tokens_in, tokens_out, distilled,
                     created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status=excluded.status,
                    output=excluded.output,
                    tier=excluded.tier,
                    retry_count=excluded.retry_count,
                    error=excluded.error,
                    tokens_in=excluded.tokens_in,
                    tokens_out=excluded.tokens_out,
                    distilled=excluded.distilled,
                    updated_at=excluded.updated_at
            """, (task_id, agent, status, json.dumps(payload), output, tier,
                  retry_count, error, tokens_in, tokens_out, int(distilled),
                  now, now))

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM task_state WHERE task_id=?", (task_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_dlq(self, limit: int = 100) -> list[dict]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM task_state WHERE status='DLQ' ORDER BY updated_at LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── agent_snapshots ───────────────────────────────────────────────────

    def snapshot_agent(self, agent_id: str, output: str, tier: str,
                       distilled: bool, tokens_in: int, tokens_out: int) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT INTO agent_snapshots
                    (agent_id, output, tier, distilled, tokens_in, tokens_out, captured_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    output=excluded.output,
                    tier=excluded.tier,
                    distilled=excluded.distilled,
                    tokens_in=excluded.tokens_in,
                    tokens_out=excluded.tokens_out,
                    captured_at=excluded.captured_at
            """, (agent_id, output, tier, int(distilled), tokens_in, tokens_out, time.time()))

    def get_snapshot(self, agent_id: str) -> Optional[dict]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_snapshots WHERE agent_id=?", (agent_id,)
            ).fetchone()
            return dict(row) if row else None

    # ── distill_log ───────────────────────────────────────────────────────

    def write_distill_log(self, log_id: str, task_id: str, agent: str,
                          summary: str, raw_tokens: int, out_tokens: int,
                          ratio: float) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO distill_log
                    (log_id, task_id, agent, summary, raw_tokens, out_tokens,
                     ratio, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (log_id, task_id, agent, summary, raw_tokens, out_tokens,
                  ratio, time.time()))

    def prune_old(self, max_age_sec: float = 7 * 86400) -> int:
        cutoff = time.time() - max_age_sec
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM task_state WHERE updated_at < ? AND status NOT IN ('PENDING','QUEUED','RUNNING')",
                (cutoff,)
            )
            return cur.rowcount


class _RedisStreams:
    """Optional Redis-backed store; silently disabled when Redis is unavailable."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client: Any = None
        self._available = False
        self._try_connect()

    def _try_connect(self) -> None:
        try:
            import redis  # type: ignore[import]
            client = redis.from_url(self._url, socket_connect_timeout=2,
                                     socket_timeout=2, decode_responses=True)
            client.ping()
            self._client = client
            self._available = True
            log.info("gmaos.store: Redis connected at %s", self._url)
        except Exception as exc:
            log.info("gmaos.store: Redis unavailable (%s) — WAL-only mode", exc)

    @property
    def available(self) -> bool:
        return self._available

    def publish(self, stream: str, data: dict) -> None:
        if not self._available:
            return
        try:
            self._client.xadd(stream, {k: json.dumps(v) for k, v in data.items()},
                               maxlen=10_000, approximate=True)
        except Exception as exc:
            log.debug("Redis publish error: %s", exc)
            self._available = False   # degrade gracefully

    def read_pending(self, stream: str, count: int = 50) -> list[dict]:
        if not self._available:
            return []
        try:
            entries = self._client.xrange(stream, count=count)
            return [dict(v) for _, v in entries]
        except Exception:
            return []

    def set_kv(self, key: str, value: str, ex: int = 3600) -> None:
        if not self._available:
            return
        try:
            self._client.set(key, value, ex=ex)
        except Exception:
            pass

    def get_kv(self, key: str) -> Optional[str]:
        if not self._available:
            return None
        try:
            return self._client.get(key)
        except Exception:
            return None


class StateStore:
    """
    Unified three-tier store.
    Usage: instantiate once per process; thread-safe.
    """

    def __init__(self, db_path: Optional[Path] = None, redis_url: Optional[str] = None) -> None:
        _base = Path(os.getenv("PROFITENGINE_CORE_DIR", ".core_mesh_data"))
        self._sqlite = _SqliteWAL(db_path or (_base / "gmaos.db"))
        self._redis  = _RedisStreams(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        self._l1: dict[str, dict] = {}          # hot in-memory cache
        self._l1_lock = threading.Lock()

    # ── unified write ─────────────────────────────────────────────────────

    def save_task(self, task_id: str, agent: str, status: str,
                  payload: dict, **kw) -> None:
        self._sqlite.upsert_task(task_id, agent, status, payload, **kw)
        record = dict(task_id=task_id, agent=agent, status=status, **kw)
        with self._l1_lock:
            self._l1[task_id] = record
        self._redis.publish("gmaos:tasks", record)

    # ── unified read ──────────────────────────────────────────────────────

    def load_task(self, task_id: str) -> Optional[dict]:
        with self._l1_lock:
            if task_id in self._l1:
                return self._l1[task_id]
        return self._sqlite.get_task(task_id)

    # ── snapshots ─────────────────────────────────────────────────────────

    def save_snapshot(self, agent_id: str, output: str, tier: str,
                      distilled: bool = False, tokens_in: int = 0,
                      tokens_out: int = 0) -> None:
        self._sqlite.snapshot_agent(agent_id, output, tier, distilled,
                                    tokens_in, tokens_out)
        self._redis.set_kv(f"gmaos:snap:{agent_id}",
                           json.dumps({"output": output[:4096], "tier": tier}),
                           ex=86400)

    def load_snapshot(self, agent_id: str) -> Optional[str]:
        # Try Redis first (fastest, shared across replicas)
        cached = self._redis.get_kv(f"gmaos:snap:{agent_id}")
        if cached:
            try:
                return json.loads(cached)["output"]
            except Exception:
                pass
        snap = self._sqlite.get_snapshot(agent_id)
        return snap["output"] if snap else None

    # ── DLQ ───────────────────────────────────────────────────────────────

    def get_dlq(self, limit: int = 100) -> list[dict]:
        return self._sqlite.get_dlq(limit)

    # ── housekeeping ─────────────────────────────────────────────────────

    def prune(self, max_age_sec: float = 7 * 86400) -> int:
        n = self._sqlite.prune_old(max_age_sec)
        with self._l1_lock:
            self._l1.clear()
        return n

    def distill_log(self, log_id: str, task_id: str, agent: str,
                    summary: str, raw_tokens: int, out_tokens: int) -> None:
        ratio = out_tokens / max(raw_tokens, 1)
        self._sqlite.write_distill_log(log_id, task_id, agent, summary,
                                       raw_tokens, out_tokens, ratio)

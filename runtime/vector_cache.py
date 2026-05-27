"""
VectorCache — SQLite-backed semantic similarity cache for agent outputs.

Enhancements over v1:
  • TTL support  — stale entries are ignored on read and pruned on commit
  • Output dedup — avoids committing identical or near-identical outputs
                   (saves disk space and keeps cosine search fast)
  • Schema migration — adds ttl_days column to existing databases

Env vars:
  GMAOS_VECTOR_CACHE          path to SQLite file  (default ./data/vector_cache.sqlite3)
  GMAOS_EMBEDDING_DIM         int                  (default 384)
  GMAOS_SEMANTIC_MATCH_FLOOR  float 0-1            (default 0.96)
  GMAOS_CACHE_TTL_DAYS        int, 0=forever       (default 7)
  GMAOS_OUTPUT_DEDUP_FLOOR    float 0-1            (default 0.95, Jaccard on output words)
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class CacheHit:
    output:    str
    confidence: float
    record_id: str


class VectorCache:
    def __init__(
        self,
        path: str | None = None,
        embedding_dim: int | None = None,
        match_floor: float | None = None,
        ttl_days: int | None = None,
        output_dedup_floor: float | None = None,
    ) -> None:
        self.path      = Path(path or os.getenv("GMAOS_VECTOR_CACHE", "./data/vector_cache.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.embedding_dim      = embedding_dim      if embedding_dim      is not None else int(os.getenv("GMAOS_EMBEDDING_DIM", "384"))
        self.match_floor        = match_floor        if match_floor        is not None else float(os.getenv("GMAOS_SEMANTIC_MATCH_FLOOR", "0.96"))
        self.ttl_days           = ttl_days           if ttl_days           is not None else int(os.getenv("GMAOS_CACHE_TTL_DAYS", "7"))
        self.output_dedup_floor = output_dedup_floor if output_dedup_floor is not None else float(os.getenv("GMAOS_OUTPUT_DEDUP_FLOOR", "0.95"))

        self._init_db()

    # ── database setup ────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS intent_cache (
                    id TEXT PRIMARY KEY,
                    vector_json TEXT NOT NULL,
                    execution_output TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 0,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at REAL NOT NULL,
                    ttl_days INTEGER NOT NULL DEFAULT 7
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_intent_cache_namespace ON intent_cache(namespace)")
            # Schema migration: add ttl_days column to existing databases
            try:
                con.execute("ALTER TABLE intent_cache ADD COLUMN ttl_days INTEGER NOT NULL DEFAULT 7")
            except sqlite3.OperationalError:
                pass   # column already exists

    # ── validation ───────────────────────────────────────────────────────────

    def _validate(self, vector: List[float]) -> None:
        if not isinstance(vector, list):
            raise ValueError("Embedding must be a list of floats.")
        if len(vector) != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected={self.embedding_dim}, actual={len(vector)}")
        for value in vector:
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError("Embedding contains non-numeric or non-finite value.")

    # ── similarity ───────────────────────────────────────────────────────────

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na  = math.sqrt(sum(x * x for x in a))
        nb  = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _is_expired(self, created_at: float, ttl_days: int) -> bool:
        """Return True if this record is past its TTL. ttl_days=0 means forever."""
        if ttl_days == 0 or self.ttl_days == 0:
            return False
        effective_ttl = ttl_days if ttl_days > 0 else self.ttl_days
        age_days = (time.time() - created_at) / 86_400
        return age_days > effective_ttl

    # ── output dedup ─────────────────────────────────────────────────────────

    @staticmethod
    def _output_jaccard(a: str, b: str) -> float:
        """Word-level Jaccard similarity between two output strings."""
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / len(wa | wb)

    def _is_output_duplicate(self, output: str, namespace: str) -> bool:
        """
        Returns True if an existing verified record has output that is
        ≥ output_dedup_floor similar to *output*.
        """
        if self.output_dedup_floor >= 1.0:
            return False  # dedup disabled
        with self._connect() as con:
            rows = con.execute(
                "SELECT execution_output FROM intent_cache WHERE namespace = ? AND verified = 1",
                (namespace,),
            ).fetchall()
        for (existing_output,) in rows:
            if self._output_jaccard(output, existing_output) >= self.output_dedup_floor:
                return True
        return False

    # ── public API ────────────────────────────────────────────────────────────

    def search(self, vector: List[float], namespace: str = "default") -> Optional[CacheHit]:
        """
        Return the best matching verified cache entry, or None.
        Expired entries are silently skipped (not deleted here for performance).
        """
        self._validate(vector)
        best: Optional[CacheHit] = None
        with self._connect() as con:
            rows = con.execute(
                "SELECT id, vector_json, execution_output, created_at, ttl_days "
                "FROM intent_cache WHERE namespace = ? AND verified = 1",
                (namespace,),
            ).fetchall()

        for record_id, vector_json, output, created_at, ttl_days in rows:
            if self._is_expired(created_at, ttl_days):
                continue
            existing   = json.loads(vector_json)
            confidence = self._cosine(vector, existing)
            if confidence >= self.match_floor and (best is None or confidence > best.confidence):
                best = CacheHit(output=output, confidence=confidence, record_id=record_id)

        return best

    def commit(
        self,
        record_id: str,
        vector: List[float],
        output: str,
        verified: bool = False,
        namespace: str = "default",
        ttl_days: int | None = None,
        skip_dedup: bool = False,
    ) -> bool:
        """
        Persist a record to the cache.

        Parameters
        ----------
        ttl_days   : Override instance ttl_days for this record.
        skip_dedup : If True, bypass output-similarity dedup check.

        Returns
        -------
        True if committed, False if skipped (dedup hit).
        """
        self._validate(vector)

        if not skip_dedup and verified and self._is_output_duplicate(output, namespace):
            return False   # near-identical output already cached — skip

        effective_ttl = ttl_days if ttl_days is not None else self.ttl_days
        with self._connect() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO intent_cache
                    (id, vector_json, execution_output, verified, namespace, created_at, ttl_days)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    json.dumps([float(x) for x in vector]),
                    output,
                    int(verified),
                    namespace,
                    time.time(),
                    effective_ttl,
                ),
            )
        return True

    def prune_expired(self, namespace: str | None = None) -> int:
        """
        Delete expired records. Returns the number of rows deleted.
        Call periodically (e.g. from a cron or after each cycle) to keep
        the SQLite file compact.
        """
        if self.ttl_days == 0:
            return 0  # TTL disabled globally
        cutoff = time.time() - (self.ttl_days * 86_400)
        with self._connect() as con:
            if namespace:
                cur = con.execute(
                    "DELETE FROM intent_cache WHERE namespace = ? AND ttl_days > 0 AND created_at < ?",
                    (namespace, cutoff),
                )
            else:
                cur = con.execute(
                    "DELETE FROM intent_cache WHERE ttl_days > 0 AND created_at < ?",
                    (cutoff,),
                )
        return cur.rowcount

    def stats(self, namespace: str | None = None) -> dict:
        """Return cache statistics for monitoring."""
        with self._connect() as con:
            if namespace:
                total = con.execute(
                    "SELECT COUNT(*) FROM intent_cache WHERE namespace = ?", (namespace,)
                ).fetchone()[0]
                verified = con.execute(
                    "SELECT COUNT(*) FROM intent_cache WHERE namespace = ? AND verified = 1", (namespace,)
                ).fetchone()[0]
            else:
                total    = con.execute("SELECT COUNT(*) FROM intent_cache").fetchone()[0]
                verified = con.execute("SELECT COUNT(*) FROM intent_cache WHERE verified = 1").fetchone()[0]
        return {
            "total_records":    total,
            "verified_records": verified,
            "unverified":       total - verified,
            "namespace":        namespace or "all",
            "ttl_days":         self.ttl_days,
            "match_floor":      self.match_floor,
        }

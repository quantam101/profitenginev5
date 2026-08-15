"""Signed local edge failover queue for ProfitEngine.

The edge failover engine is intentionally local-first: it validates payloads,
stores them in SQLite WAL before processing, distills oversized context, and
replays staged work through the enterprise mesh when the runtime is available.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.enterprise_mesh import DEFAULT_CORE_DIR, EnterpriseMesh

DEFAULT_EDGE_DB_PATH = DEFAULT_CORE_DIR / "edge_failover.db"
DEFAULT_DISTILLATION_BUDGET = 3_000


@dataclass(frozen=True)
class EdgeTenant:
    tenant_id: str
    signing_secret: str
    compliance_tier: str = "proof_first"
    max_token_budget: int = DEFAULT_DISTILLATION_BUDGET


def payload_digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def signature_base(tenant_id: str, tracking_id: str, payload: str) -> str:
    return f"{tenant_id}.{tracking_id}.{payload_digest(payload)}"


def sign_payload(tenant: EdgeTenant, tracking_id: str, payload: str) -> str:
    return hmac.new(
        tenant.signing_secret.encode("utf-8"),
        signature_base(tenant.tenant_id, tracking_id, payload).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_payload_signature(tenant: EdgeTenant, tracking_id: str, payload: str, signature: str) -> bool:
    expected = sign_payload(tenant, tracking_id, payload)
    supplied = signature.removeprefix("sha256=").strip()
    return hmac.compare_digest(expected, supplied)


def distill_payload(payload: str, token_budget: int = DEFAULT_DISTILLATION_BUDGET) -> str:
    words = [word.strip() for word in payload.split() if len(word.strip()) > 1]
    if len(words) <= token_budget:
        return " ".join(words)
    head_count = max(1, int(token_budget * 0.7))
    tail_count = max(1, int(token_budget * 0.2))
    return " ".join(words[:head_count] + ["[DISTILLATION_GAP_REDACTED]"] + words[-tail_count:])


def tenants_from_env() -> dict[str, EdgeTenant]:
    raw = os.getenv("PROFITENGINE_EDGE_TENANTS_JSON", "").strip()
    if raw:
        values = json.loads(raw)
        return {
            item["tenant_id"]: EdgeTenant(
                tenant_id=item["tenant_id"],
                signing_secret=item["signing_secret"],
                compliance_tier=item.get("compliance_tier", "proof_first"),
                max_token_budget=int(item.get("max_token_budget", DEFAULT_DISTILLATION_BUDGET)),
            )
            for item in values
        }

    tenant_id = os.getenv("PROFITENGINE_EDGE_TENANT_ID", "").strip()
    signing_secret = os.getenv("PROFITENGINE_EDGE_SIGNING_SECRET", "").strip()
    if tenant_id and signing_secret:
        return {
            tenant_id: EdgeTenant(
                tenant_id=tenant_id,
                signing_secret=signing_secret,
                compliance_tier=os.getenv("PROFITENGINE_EDGE_COMPLIANCE_TIER", "proof_first"),
                max_token_budget=int(os.getenv("PROFITENGINE_EDGE_TOKEN_BUDGET", str(DEFAULT_DISTILLATION_BUDGET))),
            )
        }
    return {}


class EdgeFailoverEngine:
    """Durable signed ingress queue with local replay."""

    def __init__(
        self,
        tenants: dict[str, EdgeTenant] | None = None,
        db_path: str | Path = DEFAULT_EDGE_DB_PATH,
        mesh: EnterpriseMesh | None = None,
    ):
        self.tenants = tenants if tenants is not None else tenants_from_env()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.mesh = mesh or EnterpriseMesh()
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
                CREATE TABLE IF NOT EXISTS edge_events (
                    tracking_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    distilled_payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    runtime_mode TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NOT NULL DEFAULT '',
                    result_json TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def ingest(
        self,
        tenant_id: str,
        tracking_id: str,
        payload: str,
        signature: str,
        server_online: bool,
    ) -> dict[str, Any]:
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise PermissionError("unknown tenant")
        if not verify_payload_signature(tenant, tracking_id, payload, signature):
            raise PermissionError("invalid signature")

        distilled = distill_payload(payload, tenant.max_token_budget)
        now = datetime.now(timezone.utc).isoformat()
        runtime_mode = "cloud_primary" if server_online else "local_wal_failover"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO edge_events (
                    tracking_id, tenant_id, payload_hash, payload, distilled_payload, status,
                    runtime_mode, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'staged', ?, ?, ?)
                ON CONFLICT(tracking_id) DO UPDATE SET
                    payload_hash = excluded.payload_hash,
                    payload = excluded.payload,
                    distilled_payload = excluded.distilled_payload,
                    status = 'staged',
                    runtime_mode = excluded.runtime_mode,
                    updated_at = excluded.updated_at
                """,
                (tracking_id, tenant_id, payload_digest(payload), payload, distilled, runtime_mode, now, now),
            )
            conn.commit()

        if server_online:
            return self.process_one(tracking_id)
        return {
            "ok": True,
            "tracking_id": tracking_id,
            "status": "staged",
            "runtime_mode": runtime_mode,
            "payload_hash": payload_digest(payload),
        }

    def process_one(self, tracking_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM edge_events WHERE tracking_id = ?", (tracking_id,)).fetchone()
        if row is None:
            return {"ok": False, "tracking_id": tracking_id, "error": "not_found"}

        started = time.perf_counter()
        try:
            result = self.mesh.dispatch(
                [
                    "offer-scout",
                    "margin-guard",
                    "traffic-agent",
                    "proof-ledger",
                    "motivation-engine",
                    "free-tier-cost-guard",
                ],
                objective=f"Process edge payload {tracking_id} for tenant {row['tenant_id']}",
                context=row["distilled_payload"],
            )
            status = "processed" if result.get("ok") else "dead"
            last_error = "" if result.get("ok") else "enterprise mesh returned failed status"
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE edge_events
                    SET status = ?, attempt_count = attempt_count + 1, last_error = ?,
                        result_json = ?, updated_at = ?
                    WHERE tracking_id = ?
                    """,
                    (status, last_error, json.dumps(result, sort_keys=True), datetime.now(timezone.utc).isoformat(), tracking_id),
                )
                conn.commit()
            return {
                "ok": bool(result.get("ok")),
                "tracking_id": tracking_id,
                "status": status,
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "mesh": result,
            }
        except Exception as exc:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE edge_events
                    SET status = 'staged', attempt_count = attempt_count + 1,
                        last_error = ?, updated_at = ?
                    WHERE tracking_id = ?
                    """,
                    (f"{type(exc).__name__}: {exc}", datetime.now(timezone.utc).isoformat(), tracking_id),
                )
                conn.commit()
            return {"ok": False, "tracking_id": tracking_id, "status": "staged", "error": f"{type(exc).__name__}: {exc}"}

    def replay(self, limit: int = 25) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT tracking_id FROM edge_events
                WHERE status = 'staged'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        results = [self.process_one(row["tracking_id"]) for row in rows]
        return {
            "ok": all(result.get("ok") for result in results),
            "attempted": len(results),
            "processed": sum(1 for result in results if result.get("status") == "processed"),
            "remaining": self.status()["status_counts"].get("staged", 0),
            "results": results,
        }

    def status(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS n FROM edge_events GROUP BY status").fetchall()
            total = conn.execute("SELECT COUNT(*) AS n FROM edge_events").fetchone()["n"]
        return {
            "ok": True,
            "mode": "sqlite_wal_edge_failover",
            "db_path": str(self.db_path),
            "tenant_count": len(self.tenants),
            "total_events": total,
            "status_counts": {row["status"]: row["n"] for row in rows},
        }

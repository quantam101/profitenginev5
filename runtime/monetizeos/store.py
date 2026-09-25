"""Durable SQLite store for MonetizeOS orchestration (spec §4).

Single-host transactional store (WAL).  Persists projects, tasks,
dependency edges, leases/heartbeats, attempts, artifacts, decisions,
outbox events, cost/usage events and incidents.

Concurrency model
-----------------
* Task delivery is at-least-once; side effects are idempotent:
  ``tasks.idempotency_key`` is UNIQUE (create returns the existing row),
  and the outbox dedupes on ``dedupe_key``.
* Exactly one active Director per project via ``directors`` — acquiring
  the lease increments a fencing token; every Director-issued mutation
  re-checks it inside the same transaction (stale Director ⇒ rejected).
* Worker leases: a task row carries ``lease_owner``/``lease_expires_at``;
  expired leases are swept back to a schedulable state on every claim.
* All transitions go through one UPDATE ``... WHERE state = ?`` so two
  workers cannot both move the same task.
"""
from __future__ import annotations

import json
import os
import random
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from runtime.monetizeos.contracts import CompletionReport, TaskContract
from runtime.monetizeos.states import IllegalTransition, check


class FencingStale(RuntimeError):
    pass


class LeaseConflict(RuntimeError):
    pass


class DuplicateIdempotencyKey(RuntimeError):
    """Same key, different contract fingerprint — a genuinely different task."""
    pass


SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_json TEXT NOT NULL DEFAULT '{}',
    baseline_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    contract_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    state TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    idempotency_key TEXT UNIQUE,
    lease_owner TEXT,
    lease_expires_at REAL,
    fencing INTEGER NOT NULL DEFAULT 0,
    attempt INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL,
    cancel_requested INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_sched ON tasks(state, priority, next_attempt_at);
CREATE TABLE IF NOT EXISTS edges (
    task_id TEXT NOT NULL,
    depends_on TEXT NOT NULL,
    PRIMARY KEY (task_id, depends_on)
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    worker TEXT NOT NULL,
    started_at REAL NOT NULL,
    ended_at REAL,
    status TEXT,
    report_json TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    ref TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    fencing INTEGER NOT NULL,
    kind TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    dedupe_key TEXT UNIQUE NOT NULL,
    task_id TEXT,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    delivered_at REAL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS cost_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    task_id TEXT,
    kind TEXT NOT NULL,
    tokens INTEGER NOT NULL DEFAULT 0,
    usd REAL NOT NULL DEFAULT 0,
    detail_json TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    task_id TEXT,
    kind TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at REAL NOT NULL,
    resolved_at REAL
);
CREATE TABLE IF NOT EXISTS directors (
    project_id TEXT PRIMARY KEY,
    holder TEXT NOT NULL,
    fencing INTEGER NOT NULL,
    lease_expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS changelog (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    fencing INTEGER NOT NULL,
    entry TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""

DEFAULT_DB = Path(os.getenv("MONETIZEOS_DB", "data/monetizeos.db"))

# Secret-looking values in specialist reports must never persist to disk
# (spec §6: redact secrets and sensitive data from logs/shared context).
_REDACT_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                   # AWS access key
    re.compile(r"(?:sk|pk|rk|ghp|gho|ghu|ghs|ghr|glpat|xox[baprs])-[A-Za-z0-9_-]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"),  # JWT
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[^-]*-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)(bearer|token|api[_-]?key|secret|password|passwd)"
               r"(\s*[:=]\s*|\s+)(['\"]?)[^\s'\"]{8,}\3"),
]


def redact_text(text: str) -> str:
    """Replace credential-shaped substrings with a fixed marker."""
    for pat in _REDACT_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def _now() -> float:
    return time.time()


class Store:
    def __init__(self, path: str | Path = DEFAULT_DB) -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        conn = self._conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise

    # ----- projects -----
    def create_project(self, project_id: str, name: str, spec: dict, baseline: dict) -> None:
        now = _now()
        with self.tx() as c:
            c.execute(
                "INSERT OR IGNORE INTO projects(project_id,name,spec_json,baseline_json,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?)",
                (project_id, name, json.dumps(spec, sort_keys=True),
                 json.dumps(baseline, sort_keys=True), now, now),
            )

    def update_baseline(self, project_id: str, baseline: dict) -> None:
        with self.tx() as c:
            c.execute(
                "UPDATE projects SET baseline_json=?, updated_at=? WHERE project_id=?",
                (json.dumps(baseline, sort_keys=True), _now(), project_id),
            )

    def get_project(self, project_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["spec"] = json.loads(d.pop("spec_json"))
        d["baseline"] = json.loads(d.pop("baseline_json"))
        return d

    # ----- director lease + fencing -----
    def acquire_director(self, project_id: str, holder: str, ttl_s: float = 60.0) -> int:
        """Acquire/renew the Director lease.  Returns the fencing token.
        Raises LeaseConflict if another live Director holds the lease."""
        now = _now()
        with self.tx() as c:
            row = c.execute("SELECT * FROM directors WHERE project_id=?", (project_id,)).fetchone()
            if row is None:
                c.execute(
                    "INSERT INTO directors(project_id,holder,fencing,lease_expires_at) VALUES(?,?,?,?)",
                    (project_id, holder, 1, now + ttl_s),
                )
                return 1
            if row["holder"] != holder and row["lease_expires_at"] > now:
                raise LeaseConflict(
                    f"project {project_id} is supervised by {row['holder']} "
                    f"(lease expires {row['lease_expires_at']:.0f})"
                )
            fencing = row["fencing"] + 1
            c.execute(
                "UPDATE directors SET holder=?, fencing=?, lease_expires_at=? WHERE project_id=?",
                (holder, fencing, now + ttl_s, project_id),
            )
            return fencing

    def _check_fencing(self, c: sqlite3.Connection, project_id: str, fencing: int) -> None:
        row = c.execute("SELECT fencing, lease_expires_at, holder FROM directors WHERE project_id=?",
                        (project_id,)).fetchone()
        if row is None or row["fencing"] != fencing or row["lease_expires_at"] <= _now():
            raise FencingStale(
                f"stale or expired Director fencing token for {project_id}: "
                f"have {fencing}, live {row['fencing'] if row else None}"
            )

    # ----- tasks -----
    def create_task(self, project_id: str, contract: TaskContract,
                    fencing: int | None = None, priority: int = 100) -> str:
        """Idempotent on contract.idempotency_key (or task_id).  Returns task_id.
        Raises DuplicateIdempotencyKey when the key exists with a different payload."""
        errors = contract.validate()
        if errors:
            raise ValueError(f"invalid contract: {'; '.join(errors)}")
        fingerprint = contract.fingerprint()
        # Scope the dedupe key to the project — two projects may legitimately
        # use the same human-meaningful key without sharing tasks.
        key = f"{project_id}:{contract.idempotency_key or f'task:{contract.task_id}'}"
        now = _now()
        with self.tx() as c:
            if fencing is not None:
                self._check_fencing(c, project_id, fencing)
            existing = c.execute(
                "SELECT task_id, fingerprint FROM tasks WHERE idempotency_key=?", (key,)
            ).fetchone()
            if existing:
                if existing["fingerprint"] != fingerprint:
                    raise DuplicateIdempotencyKey(
                        f"idempotency_key {key} already bound to task {existing['task_id']} "
                        "with a different contract"
                    )
                return existing["task_id"]
            if not contract.dependencies:
                state = "ready"
            else:
                # Deps may already be complete (task enqueued late) — count
                # any dependency that is not completed; unknown dep ids also
                # keep the task pending until something creates them.
                ph = ",".join("?" * len(contract.dependencies))
                incomplete = c.execute(
                    f"SELECT COUNT(*) n FROM tasks WHERE task_id IN ({ph})"  # noqa: S608
                    " AND state != 'completed'",
                    tuple(contract.dependencies),
                ).fetchone()["n"]
                missing = len(set(contract.dependencies)) - c.execute(
                    f"SELECT COUNT(*) n FROM tasks WHERE task_id IN ({ph})",  # noqa: S608
                    tuple(contract.dependencies),
                ).fetchone()["n"]
                state = "ready" if (incomplete == 0 and missing == 0) else "pending"
            c.execute(
                "INSERT INTO tasks(task_id,project_id,contract_json,fingerprint,state,priority,"
                "idempotency_key,fencing,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (contract.task_id, project_id, json.dumps(contract.__dict__, sort_keys=True),
                 fingerprint, state, priority, key, fencing or 0, now, now),
            )
            for dep in contract.dependencies:
                c.execute("INSERT INTO edges(task_id,depends_on) VALUES(?,?)", (contract.task_id, dep))
            return contract.task_id

    def get_task(self, task_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["contract"] = json.loads(d.pop("contract_json"))
        return d

    def list_tasks(self, project_id: str, states: tuple[str, ...] | None = None) -> list[dict]:
        sql = "SELECT task_id,state,attempt,lease_owner,priority,next_attempt_at FROM tasks WHERE project_id=?"
        params: list[Any] = [project_id]
        if states:
            sql += f" AND state IN ({','.join('?' * len(states))})"
            params.extend(states)
        sql += " ORDER BY priority, created_at"
        return [dict(r) for r in self._conn.execute(sql, params)]

    def _sweep(self, c: sqlite3.Connection) -> None:
        """Recover expired retry_wait tasks and dead worker leases."""
        now = _now()
        # Worker vanished or timed out: apply the same attempt-limit /
        # dead-letter policy as a failed attempt — an expired lease still
        # consumes one attempt of the retry budget.
        for r in c.execute(
            "SELECT task_id, project_id, attempt, contract_json FROM tasks"
            " WHERE state IN ('running','verifying') AND lease_expires_at IS NOT NULL"
            " AND lease_expires_at<=?",
            (now,),
        ).fetchall():
            contract = json.loads(r["contract_json"])
            if r["attempt"] <= contract.get("retry_limit", 0):
                c.execute(
                    "UPDATE tasks SET state='retry_wait', lease_owner=NULL,"
                    " lease_expires_at=NULL, next_attempt_at=?, updated_at=? WHERE task_id=?",
                    (now, now, r["task_id"]),
                )
            else:
                c.execute(
                    "UPDATE tasks SET state='failed', lease_owner=NULL,"
                    " lease_expires_at=NULL, updated_at=? WHERE task_id=?",
                    (now, r["task_id"]),
                )
                c.execute(
                    "INSERT INTO incidents(project_id,task_id,kind,detail_json,created_at)"
                    " VALUES(?,?,?,?,?)",
                    (r["project_id"], r["task_id"], "dead_letter",
                     json.dumps({"reason": "lease expired after retry budget exhausted",
                                 "attempts": r["attempt"]}), now),
                )
                for dep in c.execute("SELECT task_id FROM edges WHERE depends_on=?",
                                     (r["task_id"],)).fetchall():
                    c.execute(
                        "UPDATE tasks SET state='blocked', updated_at=? WHERE task_id=?"
                        " AND state IN ('pending','ready','blocked')",
                        (now, dep["task_id"]),
                    )
        c.execute(
            "UPDATE tasks SET state='ready', updated_at=? WHERE state='retry_wait' AND next_attempt_at<=?",
            (now, now),
        )

    def claim(self, project_id: str, worker: str, ttl_s: float = 300.0) -> dict | None:
        """Claim the highest-priority schedulable task.  One active lease per task."""
        now = _now()
        with self.tx() as c:
            self._sweep(c)
            row = c.execute(
                "SELECT * FROM tasks WHERE project_id=? AND state='ready' AND cancel_requested=0"
                " ORDER BY priority, created_at LIMIT 1",
                (project_id,),
            ).fetchone()
            if row is None:
                return None
            cur = c.execute(
                "UPDATE tasks SET state='running', lease_owner=?, lease_expires_at=?,"
                " attempt=attempt+1, updated_at=? WHERE task_id=? AND state='ready'",
                (worker, now + ttl_s, now, row["task_id"]),
            )
            if cur.rowcount != 1:
                return None
            c.execute(
                "INSERT INTO attempts(task_id,attempt_no,worker,started_at) VALUES(?,?,?,?)",
                (row["task_id"], row["attempt"] + 1, worker, now),
            )
            return self.get_task(row["task_id"])

    def _transition(self, c: sqlite3.Connection, task_id: str, dst: str,
                    expected: tuple[str, ...] | None = None) -> None:
        row = c.execute("SELECT state FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        src = row["state"]
        if expected and src not in expected:
            raise IllegalTransition(task_id, src, dst)
        check(task_id, src, dst)
        cur = c.execute(
            "UPDATE tasks SET state=?, updated_at=? WHERE task_id=? AND state=?",
            (dst, _now(), task_id, src),
        )
        if cur.rowcount != 1:
            raise IllegalTransition(task_id, src, dst)
        if dst == "completed":
            self._unblock_dependents(c, task_id)
            self._check_blocked(c, task_id)

    def _unblock_dependents(self, c: sqlite3.Connection, task_id: str) -> None:
        """pending tasks whose dependencies are ALL completed → ready."""
        for r in c.execute("SELECT task_id FROM edges WHERE depends_on=?", (task_id,)):
            tid = r["task_id"]
            remaining = c.execute(
                "SELECT COUNT(*) n FROM edges e JOIN tasks t ON t.task_id=e.depends_on"
                " WHERE e.task_id=? AND t.state!='completed'",
                (tid,),
            ).fetchone()["n"]
            if remaining == 0:
                c.execute(
                    "UPDATE tasks SET state='ready', updated_at=? WHERE task_id=? AND state IN ('pending','blocked')",
                    (_now(), tid),
                )

    def _check_blocked(self, c: sqlite3.Connection, task_id: str) -> None:
        """No-op hook: dependents of a failed task are marked blocked by fail()."""
        return

    def submit_report(self, task_id: str, worker: str, report: CompletionReport,
                      artifacts: list[dict] | None = None) -> None:
        """Worker → verifying (then Director verifies via accept()/reject())."""
        errors = report.validate()
        if errors:
            raise ValueError(f"invalid completion report: {'; '.join(errors)}")
        now = _now()
        with self.tx() as c:
            row = c.execute("SELECT state, lease_owner FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            if row["lease_owner"] != worker:
                raise LeaseConflict(f"task {task_id} is not leased by {worker}")
            self._transition(c, task_id, "verifying", expected=("running",))
            c.execute(
                "UPDATE attempts SET ended_at=?, status=?, report_json=? WHERE task_id=?"
                " AND ended_at IS NULL",
                # Reports cross agent trust boundaries — strip credential-shaped
                # values before they land in durable storage.
                (now, report.status, redact_text(report.to_json()), task_id),
            )
            for a in artifacts or []:
                fp = c.execute("SELECT fingerprint FROM tasks WHERE task_id=?", (task_id,)).fetchone()
                c.execute(
                    "INSERT OR REPLACE INTO artifacts(artifact_id,task_id,kind,ref,fingerprint,created_at)"
                    " VALUES(?,?,?,?,?,?)",
                    (a["artifact_id"], task_id, a.get("kind", "output"),
                     redact_text(a["ref"]), fp["fingerprint"], now),
                )

    def accept(self, task_id: str, fencing: int | None = None) -> None:
        """Director/verifier accepts evidence → completed.  Records cost events."""
        with self.tx() as c:
            row = c.execute("SELECT project_id, contract_json FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            if fencing is not None:
                self._check_fencing(c, row["project_id"], fencing)
            self._transition(c, task_id, "completed", expected=("verifying",))
            report = c.execute(
                "SELECT report_json FROM attempts WHERE task_id=? AND status='completed'"
                " ORDER BY id DESC LIMIT 1", (task_id,)).fetchone()
            if report:
                r = json.loads(report["report_json"])
                c.execute(
                    "INSERT INTO cost_events(project_id,task_id,kind,tokens,usd,created_at)"
                    " VALUES(?,?,?,?,?,?)",
                    (row["project_id"], task_id, "task_completed",
                     r.get("tokens_used", 0), r.get("cost_usd", 0.0), _now()),
                )
            c.execute("UPDATE tasks SET lease_owner=NULL, lease_expires_at=NULL WHERE task_id=?", (task_id,))

    def reject(self, task_id: str, reason: str, fencing: int | None = None) -> str:
        """Verification failed → retry or dead-letter."""
        return self._fail_common(task_id, reason, fencing, from_verifying=True)

    def fail(self, task_id: str, reason: str, fencing: int | None = None) -> str:
        return self._fail_common(task_id, reason, fencing, from_verifying=False)

    def _fail_common(self, task_id: str, reason: str, fencing: int | None,
                     from_verifying: bool) -> str:
        now = _now()
        with self.tx() as c:
            row = c.execute("SELECT project_id, attempt, contract_json, state FROM tasks WHERE task_id=?",
                            (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            if fencing is not None:
                self._check_fencing(c, row["project_id"], fencing)
            contract = json.loads(row["contract_json"])
            c.execute(
                "UPDATE attempts SET ended_at=?, status='failed', error=?"
                " WHERE task_id=? AND ended_at IS NULL",
                (now, reason, task_id),
            )
            if row["attempt"] <= contract.get("retry_limit", 0):
                backoff = min(60.0, 2.0 ** row["attempt"]) + random.uniform(0, 0.5)  # noqa: S311 — retry jitter, not crypto
                self._transition(c, task_id, "retry_wait",
                                 expected=("verifying",) if from_verifying else ("running", "verifying"))
                c.execute(
                    "UPDATE tasks SET next_attempt_at=?, lease_owner=NULL, lease_expires_at=NULL"
                    " WHERE task_id=?", (now + backoff, task_id),
                )
                outcome = "retry_wait"
            else:
                self._transition(c, task_id, "failed",
                                 expected=("verifying",) if from_verifying else ("running", "verifying", "retry_wait"))
                c.execute(
                    "UPDATE tasks SET lease_owner=NULL, lease_expires_at=NULL WHERE task_id=?", (task_id,)
                )
                c.execute(
                    "INSERT INTO incidents(project_id,task_id,kind,detail_json,created_at)"
                    " VALUES(?,?,?,?,?)",
                    (row["project_id"], task_id, "dead_letter",
                     json.dumps({"reason": reason, "attempts": row["attempt"]}), now),
                )
                # Dependents can never run → block them.
                for dep in c.execute("SELECT task_id FROM edges WHERE depends_on=?", (task_id,)):
                    c.execute(
                        "UPDATE tasks SET state='blocked', updated_at=? WHERE task_id=? AND state IN ('pending','ready','blocked')",
                        (now, dep["task_id"]),
                    )
                outcome = "failed"
            return outcome

    def cancel(self, task_id: str, fencing: int | None = None) -> None:
        with self.tx() as c:
            row = c.execute("SELECT project_id, state FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            if fencing is not None:
                self._check_fencing(c, row["project_id"], fencing)
            # Flag first so a running worker can observe and abort cleanly.
            c.execute("UPDATE tasks SET cancel_requested=1 WHERE task_id=?", (task_id,))
            self._transition(c, task_id, "cancelled")

    def cancel_requested(self, task_id: str) -> bool:
        row = self._conn.execute("SELECT cancel_requested FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return bool(row and row["cancel_requested"])

    # ----- decisions / changelog / outbox -----
    def record_decision(self, project_id: str, fencing: int, kind: str, detail: dict) -> int:
        with self.tx() as c:
            self._check_fencing(c, project_id, fencing)
            cur = c.execute(
                "INSERT INTO decisions(project_id,fencing,kind,detail_json,created_at) VALUES(?,?,?,?,?)",
                (project_id, fencing, kind, json.dumps(detail, sort_keys=True), _now()),
            )
            c.execute(
                "INSERT INTO changelog(project_id,fencing,entry,created_at) VALUES(?,?,?,?)",
                (project_id, fencing, f"decision:{kind} {json.dumps(detail, sort_keys=True)}", _now()),
            )
            return int(cur.lastrowid)

    def emit(self, dedupe_key: str, kind: str, payload: dict, task_id: str | None = None) -> bool:
        """Durable outbox.  Returns True when the event was new (dedupe_key unseen)."""
        with self.tx() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO outbox(dedupe_key,task_id,kind,payload_json,created_at)"
                " VALUES(?,?,?,?,?)",
                (dedupe_key, task_id, kind, json.dumps(payload, sort_keys=True), _now()),
            )
            return cur.rowcount == 1

    def outbox_pending(self, limit: int = 100) -> list[dict]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM outbox WHERE delivered_at IS NULL ORDER BY seq LIMIT ?", (limit,))]

    def outbox_mark_delivered(self, seq: int) -> None:
        with self.tx() as c:
            c.execute("UPDATE outbox SET delivered_at=? WHERE seq=?", (_now(), seq))

    # ----- incidents / costs / status -----
    def record_incident(self, project_id: str, kind: str, detail: dict,
                        task_id: str | None = None) -> int:
        with self.tx() as c:
            cur = c.execute(
                "INSERT INTO incidents(project_id,task_id,kind,detail_json,created_at) VALUES(?,?,?,?,?)",
                (project_id, task_id, kind, json.dumps(detail, sort_keys=True), _now()),
            )
            return int(cur.lastrowid)

    def record_cost(self, project_id: str, kind: str, tokens: int = 0, usd: float = 0.0,
                    task_id: str | None = None, detail: dict | None = None) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO cost_events(project_id,task_id,kind,tokens,usd,detail_json,created_at)"
                " VALUES(?,?,?,?,?,?,?)",
                (project_id, task_id, kind, tokens, usd, json.dumps(detail or {}, sort_keys=True), _now()),
            )

    def status(self, project_id: str) -> dict:
        c = self._conn
        by_state = {r["state"]: r["n"] for r in c.execute(
            "SELECT state, COUNT(*) n FROM tasks WHERE project_id=? GROUP BY state", (project_id,))}
        costs = c.execute(
            "SELECT COALESCE(SUM(tokens),0) tokens, COALESCE(SUM(usd),0) usd FROM cost_events"
            " WHERE project_id=?", (project_id,)).fetchone()
        attempts = c.execute(
            "SELECT COUNT(*) n, COALESCE(AVG(ended_at-started_at),0) avg_s FROM attempts a"
            " JOIN tasks t ON t.task_id=a.task_id WHERE t.project_id=?", (project_id,)).fetchone()
        director = c.execute("SELECT * FROM directors WHERE project_id=?", (project_id,)).fetchone()
        return {
            "project_id": project_id,
            "tasks": by_state,
            "director": dict(director) if director else None,
            "open_incidents": c.execute(
                "SELECT COUNT(*) n FROM incidents WHERE project_id=? AND status='open'", (project_id,)).fetchone()["n"],
            "pending_outbox": c.execute("SELECT COUNT(*) n FROM outbox WHERE delivered_at IS NULL").fetchone()["n"],
            "tokens": costs["tokens"],
            "usd": costs["usd"],
            "attempts": attempts["n"],
            "avg_attempt_seconds": round(attempts["avg_s"], 3),
        }

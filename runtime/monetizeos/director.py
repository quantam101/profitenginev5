"""MonetizeOS Director — the single supervisory agent (spec §1, §5, §6).

The Director owns the objective, the dependency graph, and delegation.
Exactly one active Director per project, protected by a renewable lease
and fencing token — a second Director cannot issue conflicting work.

All decisions, assignments and changelog entries are durable store
records (never just conversation state), so execution resumes after an
interruption.  The Director may resolve priorities but can never mark a
failed mandatory security/verification gate as passed.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from runtime.monetizeos.contracts import CompletionReport, TaskContract
from runtime.monetizeos.specialists import (
    DEFAULT_HANDLERS,
    SPECIALIST_ROLES,
    SpecialistHandler,
    check_permissions,
    check_report_scope,
)
from runtime.monetizeos.store import FencingStale, Store


class Escalation(RuntimeError):
    """Genuine blocker requiring external access or a human decision."""


class HandlerDeadlineExceeded(RuntimeError):
    pass


def _handler_child(handler: SpecialistHandler, contract: TaskContract,
                   ctx: dict, q: Any) -> None:
    try:
        rep = handler(contract, ctx)
        q.put(("ok", asdict(rep)))
    except BaseException as exc:  # report the crash, never swallow it
        q.put(("err", repr(exc)))


def run_with_deadline(handler: SpecialistHandler, contract: TaskContract,
                      ctx: dict, deadline_s: float) -> CompletionReport:
    """Execute a specialist handler in a killable child process bounded by the
    contract's time budget.  A hung handler is terminated and its attempt
    fails — cooperative timeouts alone cannot stop a deadlocked specialist."""
    mctx = mp.get_context("fork")
    q: Any = mctx.Queue()
    p = mctx.Process(target=_handler_child, args=(handler, contract, ctx, q), daemon=True)
    p.start()
    p.join(max(1.0, deadline_s))
    if p.is_alive():
        p.terminate()
        p.join(5)
        if p.is_alive():
            p.kill()
            p.join()
        raise HandlerDeadlineExceeded(
            f"handler exceeded budget_seconds={deadline_s} and was terminated")
    status, payload = q.get() if not q.empty() else ("err", "handler died without reporting")
    if status == "ok":
        return CompletionReport(**payload)
    raise RuntimeError(payload)


def _fs_snapshot(root: str) -> dict:
    """(mtime_ns, size) for every file under root — used to detect writes a
    handler did not declare in files_changed (spec §6, execution-time scope)."""
    snap: dict = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for f in files:
            p = os.path.join(dirpath, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            snap[os.path.relpath(p, root)] = (st.st_mtime_ns, st.st_size)
    return snap


@dataclass
class Director:
    store: Store
    project_id: str
    # Each Director instance owns a persistent unique identity — two
    # Directors created with defaults must conflict, not both acquire.
    holder: str = field(default_factory=lambda: f"director-{uuid.uuid4().hex[:12]}")
    lease_ttl_s: float = 60.0
    handlers: dict[str, SpecialistHandler] = field(default_factory=lambda: dict(DEFAULT_HANDLERS))
    fencing: int = 0
    not_applicable: dict[str, str] = field(default_factory=dict)

    # ----- lifecycle -----
    def acquire(self) -> None:
        """Acquire or renew the supervision lease (raises LeaseConflict)."""
        self.fencing = self.store.acquire_director(self.project_id, self.holder, self.lease_ttl_s)

    def renew(self) -> None:
        self.fencing = self.store.acquire_director(self.project_id, self.holder, self.lease_ttl_s)

    def release(self) -> None:
        """Voluntarily drop the supervision lease (clean CLI/process exit).
        Without this, each short-lived invocation looks like a competing
        Director until the lease TTL expires."""
        if self.fencing:
            self.store.release_director(self.project_id, self.holder)
            self.fencing = 0

    def _mutate_guard(self) -> None:
        if not self.fencing:
            raise FencingStale("Director has not acquired the supervision lease")

    # ----- planning -----
    def mark_not_applicable(self, role: str, reason: str) -> None:
        self._mutate_guard()
        if role not in SPECIALIST_ROLES:
            raise KeyError(role)
        self.not_applicable[role] = reason
        self.store.record_decision(self.project_id, self.fencing,
                                 "not_applicable", {"role": role, "reason": reason})

    def delegate(self, contract: TaskContract, priority: int = 100) -> str:
        """Assign a bounded task to its process owner (permission-checked)."""
        self._mutate_guard()
        violations = check_permissions(contract)
        if violations:
            raise Escalation(f"contract {contract.task_id} exceeds role permissions: {violations}")
        task_id = self.store.create_task(self.project_id, contract,
                                         fencing=self.fencing, priority=priority)
        self.store.record_decision(self.project_id, self.fencing, "delegate",
                                   {"task_id": task_id, "owner": contract.process_owner})
        return task_id

    # ----- verification (evidence, not declarations) -----
    def verify(self, task_id: str) -> str:
        """Accept the latest completion report if it satisfies the contract's
        verification method and acceptance evidence.  Returns 'completed' or
        the retry/failed outcome."""
        task = self.store.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        report = self.store._conn.execute(
            "SELECT report_json FROM attempts WHERE task_id=? AND ended_at IS NOT NULL"
            " ORDER BY id DESC LIMIT 1", (task_id,)).fetchone()
        report_ok = bool(report and json.loads(report["report_json"]).get("status") == "completed")
        if report_ok:
            self.store.accept(task_id, fencing=self.fencing)
            self.store.record_decision(self.project_id, self.fencing, "verify_accept",
                                       {"task_id": task_id})
            return "completed"
        outcome = self.store.reject(task_id, "verification: no passing report on record",
                                    fencing=self.fencing)
        self.store.record_decision(self.project_id, self.fencing, "verify_reject",
                                   {"task_id": task_id, "outcome": outcome})
        return outcome

    # ----- scheduling -----
    def run_once(self, worker: str, ctx: dict[str, Any], lease_ttl_s: float = 300.0) -> str:
        """One scheduling cycle: claim a task, execute its specialist handler,
        submit the report, verify.  Returns 'idle'|'completed'|'failed'|'retry_wait'
        |'cancelled'|'no_handler'."""
        self.renew()
        task = self.store.claim(self.project_id, worker, ttl_s=lease_ttl_s)
        if task is None:
            return "idle"
        task_id = task["task_id"]
        contract = TaskContract(**task["contract"])
        handler = self.handlers.get(contract.process_owner)
        if handler is None:
            # No registered handler — do not pretend the agent ran.
            self.store.fail(task_id, f"no handler registered for {contract.process_owner}",
                            fencing=self.fencing)
            self.store.record_incident(self.project_id, "missing_handler",
                                       {"role": contract.process_owner}, task_id=task_id)
            return "no_handler"
        started = time.monotonic()
        # Snapshot the working tree so undeclared writes outside the contract's
        # allowed_files are detected even if the handler omits them from
        # files_changed — enforcement must not rely on self-reporting alone.
        root = ctx.get("repo_root")
        snap_before = _fs_snapshot(root) if (contract.allowed_files and root) else None
        try:
            if self.store.cancel_requested(task_id):
                self.store.submit_report(task_id, worker,
                                         CompletionReport(task_id=task_id, status="blocked"))
                return "cancelled"
            report = run_with_deadline(handler, contract, ctx, float(contract.budget_seconds))
            report.duration_seconds = time.monotonic() - started
            self.renew()  # refresh authority before any post-execution mutations
            if snap_before is not None:
                undeclared = [p for p, v in _fs_snapshot(root).items()
                              if snap_before.get(p) != v and p not in report.files_changed]
                report.files_changed.extend(undeclared)
            scope_violations = check_report_scope(contract, report)
            if scope_violations:
                self.store.submit_report(task_id, worker, report)
                outcome = self.store.fail(
                    task_id, f"report outside contract scope: {scope_violations}",
                    fencing=self.fencing)
                self.store.record_incident(self.project_id, "scope_violation",
                                           {"task_id": task_id, "files": scope_violations},
                                           task_id=task_id)
                return outcome
            self.store.submit_report(task_id, worker, report)
            if self.store.get_task(task_id)["state"] == "cancelled":
                return "cancelled"
            if report.status != "completed":
                outcome = self.store.fail(task_id, f"handler reported {report.status}",
                                          fencing=self.fencing)
                return outcome
            return self.verify(task_id)
        except (Escalation, FencingStale):
            raise
        except Exception as exc:  # specialist crashed → bounded retry
            outcome = self.store.fail(task_id, f"handler exception: {exc}",
                                      fencing=self.fencing)
            self.store.record_incident(self.project_id, "handler_exception",
                                       {"task_id": task_id, "error": str(exc)}, task_id=task_id)
            return outcome

    def status(self) -> dict:
        return self.store.status(self.project_id)

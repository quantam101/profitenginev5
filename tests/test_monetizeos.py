"""MonetizeOS orchestration tests: durability, leases/fencing, duplicate
delivery, retries/dead-letter, cancellation, gates, and recovery."""
from __future__ import annotations

import time

import pytest

from runtime.monetizeos import (
    CompletionReport, Director, DuplicateIdempotencyKey, FencingStale,
    GateBoard, IllegalTransition, LeaseConflict, Store, TaskContract,
)


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "mos.db")
    s.create_project("p1", "proj", {}, {})
    yield s
    s.close()


def contract(tid="t1", **kw):
    kw.setdefault("task_id", tid)
    kw.setdefault("process_owner", "core_product_engineer")
    kw.setdefault("objective", "do the thing")
    kw.setdefault("business_purpose", "money")
    kw.setdefault("verification_method", "run the test")
    return TaskContract(**kw)


def report(tid="t1", status="completed", tests=None):
    return CompletionReport(
        task_id=tid, status=status,
        tests_run=tests if tests is not None else [{"name": "x", "command": "x", "result": "passed"}],
    )


def director(store, holder="d1"):
    d = Director(store=store, project_id="p1", holder=holder)
    d.acquire()
    return d


class TestContracts:
    def test_contract_requires_fields(self):
        c = TaskContract(task_id="", process_owner="", objective="",
                         business_purpose="", verification_method="")
        assert len(c.validate()) >= 4

    def test_completed_report_requires_passing_tests(self):
        r = CompletionReport(task_id="t", status="completed", tests_run=[])
        assert r.validate()
        r2 = CompletionReport(task_id="t", status="completed",
                              tests_run=[{"name": "x", "command": "x", "result": "failed"}])
        assert r2.validate()


class TestTaskStore:
    def test_idempotent_create_returns_existing(self, store):
        c = contract(idempotency_key="k1")
        assert store.create_task("p1", c) == "t1"
        assert store.create_task("p1", c) == "t1"  # same key+payload → same task
        assert len(store.list_tasks("p1")) == 1

    def test_duplicate_key_different_payload_rejected(self, store):
        store.create_task("p1", contract(idempotency_key="k1"))
        with pytest.raises(DuplicateIdempotencyKey):
            store.create_task("p1", contract("t2", idempotency_key="k1",
                                             objective="different"))

    def test_illegal_transition_rejected(self, store):
        store.create_task("p1", contract())
        with pytest.raises(IllegalTransition):
            store._transition(store._conn, "t1", "completed")

    def test_dependency_gating(self, store):
        store.create_task("p1", contract("a"))
        store.create_task("p1", contract("b", dependencies=["a"]))
        assert store.get_task("b")["state"] == "pending"
        t = store.claim("p1", "w1")
        assert t["task_id"] == "a"
        assert store.claim("p1", "w2") is None  # b still gated
        store.submit_report("a", "w1", report("a"))
        store.accept("a")
        assert store.get_task("b")["state"] == "ready"
        assert store.claim("p1", "w2")["task_id"] == "b"

    def test_single_lease_per_task(self, store):
        store.create_task("p1", contract())
        assert store.claim("p1", "w1") is not None
        assert store.claim("p1", "w2") is None  # second worker gets nothing

    def test_submit_requires_lease_ownership(self, store):
        store.create_task("p1", contract())
        store.claim("p1", "w1")
        with pytest.raises(LeaseConflict):
            store.submit_report("t1", "intruder", report())

    def test_lease_expiry_recovers_task(self, store):
        store.create_task("p1", contract())
        store.claim("p1", "w1", ttl_s=0.01)
        time.sleep(0.02)
        t2 = store.claim("p1", "w2")
        assert t2 is not None and t2["task_id"] == "t1"  # recovered for w2

    def test_retry_then_dead_letter_and_blocked_dependents(self, store):
        c = contract(retry_limit=1)
        store.create_task("p1", c)
        store.create_task("p1", contract("b", dependencies=["t1"]))
        store.claim("p1", "w1")
        assert store.fail("t1", "boom") == "retry_wait"
        # Force the retry eligible and crash again → dead-letter.
        store._conn.execute("UPDATE tasks SET next_attempt_at=0 WHERE task_id='t1'")
        store.claim("p1", "w2")
        assert store.fail("t1", "boom again") == "failed"
        assert store.get_task("t1")["state"] == "failed"
        assert store.get_task("b")["state"] == "blocked"
        inc = store._conn.execute("SELECT COUNT(*) n FROM incidents").fetchone()["n"]
        assert inc == 1

    def test_cancel(self, store):
        store.create_task("p1", contract())
        store.claim("p1", "w1")
        store.cancel("t1")
        assert store.get_task("t1")["state"] == "cancelled"
        assert store.cancel_requested("t1")


class TestOutbox:
    def test_dedupe(self, store):
        assert store.emit("k", "x", {"a": 1}) is True
        assert store.emit("k", "x", {"a": 1}) is False  # duplicate suppressed
        assert len(store.outbox_pending()) == 1
        store.outbox_mark_delivered(store.outbox_pending()[0]["seq"])
        assert store.outbox_pending() == []


class TestDirectorFencing:
    def test_single_live_director(self, store):
        director(store, "d1")
        d2 = Director(store=store, project_id="p1", holder="d2")
        with pytest.raises(LeaseConflict):
            d2.acquire()

    def test_failover_after_lease_expiry_and_stale_fencing_rejected(self, store):
        d1 = director(store, "d1")
        store._conn.execute(
            "UPDATE directors SET lease_expires_at=0 WHERE project_id='p1'")
        d2 = Director(store=store, project_id="p1", holder="d2")
        d2.acquire()  # fencing=2, d1 is now stale
        with pytest.raises(FencingStale):
            store.create_task("p1", contract(), fencing=d1.fencing)
        # New director can still delegate.
        assert d2.delegate(contract()) == "t1"

    def test_delegate_permission_check(self, store):
        d = director(store)
        with pytest.raises(Exception):
            d.delegate(contract(allowed_tools=["root_shell"]))


class TestDirectorRunOnce:
    def test_no_handler_fails_closed(self, store):
        d = director(store)
        d.delegate(contract())
        assert d.run_once("w1", {"repo_root": "."}) == "no_handler"
        assert store.get_task("t1")["state"] in ("failed", "retry_wait")

    def test_handler_completes_task(self, store):
        d = director(store)
        d.handlers["core_product_engineer"] = lambda c, ctx: report(c.task_id)
        d.delegate(contract())
        assert d.run_once("w1", {"repo_root": "."}) == "completed"
        assert store.get_task("t1")["state"] == "completed"
        st = d.status()
        assert st["tasks"]["completed"] == 1

    def test_handler_crash_retries(self, store):
        d = director(store)
        calls = []

        def bad(c, ctx):
            calls.append(1)
            raise RuntimeError("crash")
        d.handlers["core_product_engineer"] = bad
        d.delegate(contract(retry_limit=1))
        assert d.run_once("w1", {"repo_root": "."}) == "retry_wait"
        store._conn.execute("UPDATE tasks SET next_attempt_at=0")
        assert d.run_once("w1", {"repo_root": "."}) == "failed"
        assert len(calls) == 2

    def test_persistence_across_reopen(self, store, tmp_path):
        d = director(store)
        d.delegate(contract())
        store.close()
        s2 = Store(tmp_path / "mos.db")
        assert s2.get_task("t1")["state"] == "ready"
        # Lease expired check: reopen shows director row persisted.
        assert s2.status("p1")["director"]["holder"] == "d1"
        s2.close()


class TestGates:
    def test_ordered_gates_and_evidence(self, store):
        d = director(store)
        board = GateBoard(store, "p1")
        with pytest.raises(RuntimeError):  # must pass earlier gates first
            board.mark_passed("core_implementation_complete", d.fencing)
        board.mark_passed("repo_access_verified", d.fencing)
        board.mark_passed("monetizable_hypothesis_documented", d.fencing)
        board.mark_passed("product_contract_reviewed", d.fencing)
        board.mark_passed("core_implementation_complete", d.fencing)
        with pytest.raises(RuntimeError):  # mandatory evidence gate
            board.mark_passed("independent_e2e_verification_passed", d.fencing)
        board.mark_passed("auth_isolation_billing_passed", d.fencing, {"passed": True})
        board.mark_passed("independent_e2e_verification_passed", d.fencing, {"passed": True})
        assert board.state()["next_gate"] == "release_artifacts_signed"

    def test_test_transaction_not_revenue(self, store):
        d = director(store)
        board = GateBoard(store, "p1")
        with pytest.raises(RuntimeError):
            board.reach_milestone("live_payment_verified", d.fencing,
                                  {"test_transaction": True})
        board.reach_milestone("live_payment_verified", d.fencing,
                              {"stripe_payment_id": "pi_real"})
        assert board.state()["milestones"]["live_payment_verified"]["reached"]


class TestFencingOnMutations:
    def test_stale_director_cannot_cancel(self, store):
        d1 = director(store, "d1")
        d1.delegate(contract())
        store._conn.execute("UPDATE directors SET lease_expires_at=0 WHERE project_id='p1'")
        Director(store=store, project_id="p1", holder="d2").acquire()
        with pytest.raises(FencingStale):
            store.cancel("t1", fencing=d1.fencing)

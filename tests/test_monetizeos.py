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
        tests_run=tests if tests is not None else [
            {"name": "x", "command": "x", "result": "passed", "output": "ok"}],
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
                              tests_run=[{"name": "x", "command": "x", "result": "failed",
                                          "output": "boom"}])
        assert r2.validate()

    def test_bare_passed_label_is_not_evidence(self):
        r = CompletionReport(task_id="t", status="completed",
                             tests_run=[{"name": "x", "command": "x", "result": "passed"}])
        assert r.validate()  # missing output/evidence

    def test_contract_rejects_embedded_secrets(self):
        c = contract(objective="deploy with token ghp_abcdef1234567890")
        assert any("credential" in e for e in c.validate())


class TestTaskStore:
    def test_idempotent_create_returns_existing(self, store):
        d = director(store)
        c = contract(idempotency_key="k1")
        assert store.create_task("p1", c, fencing=d.fencing) == "t1"
        assert store.create_task("p1", c, fencing=d.fencing) == "t1"  # same key+payload → same task
        assert len(store.list_tasks("p1")) == 1

    def test_duplicate_key_different_payload_rejected(self, store):
        d = director(store)
        store.create_task("p1", contract(idempotency_key="k1"), fencing=d.fencing)
        with pytest.raises(DuplicateIdempotencyKey):
            store.create_task("p1", contract("t2", idempotency_key="k1",
                                             objective="different"), fencing=d.fencing)

    def test_illegal_transition_rejected(self, store):
        store.create_task("p1", contract(), fencing=director(store).fencing)
        with pytest.raises(IllegalTransition):
            store._transition(store._conn, "t1", "completed")

    def test_dependency_gating(self, store):
        d = director(store)
        store.create_task("p1", contract("a"), fencing=d.fencing)
        store.create_task("p1", contract("b", dependencies=["a"]), fencing=d.fencing)
        assert store.get_task("b")["state"] == "pending"
        t = store.claim("p1", "w1")
        assert t["task_id"] == "a"
        assert store.claim("p1", "w2") is None  # b still gated
        store.submit_report("a", "w1", report("a"))
        store.accept("a", fencing=d.fencing)
        assert store.get_task("b")["state"] == "ready"
        assert store.claim("p1", "w2")["task_id"] == "b"

    def test_single_lease_per_task(self, store):
        store.create_task("p1", contract(), fencing=director(store).fencing)
        assert store.claim("p1", "w1") is not None
        assert store.claim("p1", "w2") is None  # second worker gets nothing

    def test_submit_requires_lease_ownership(self, store):
        store.create_task("p1", contract(), fencing=director(store).fencing)
        store.claim("p1", "w1")
        with pytest.raises(LeaseConflict):
            store.submit_report("t1", "intruder", report())

    def test_lease_expiry_recovers_task(self, store):
        store.create_task("p1", contract(), fencing=director(store).fencing)
        store.claim("p1", "w1", ttl_s=0.01)
        time.sleep(0.02)
        t2 = store.claim("p1", "w2")
        assert t2 is not None and t2["task_id"] == "t1"  # recovered for w2

    def test_retry_then_dead_letter_and_blocked_dependents(self, store):
        d = director(store)
        store.create_task("p1", contract(retry_limit=1), fencing=d.fencing)
        store.create_task("p1", contract("b", dependencies=["t1"]), fencing=d.fencing)
        store.claim("p1", "w1")
        assert store.fail("t1", "boom", fencing=d.fencing) == "retry_wait"
        # Force the retry eligible and crash again → dead-letter.
        store._conn.execute("UPDATE tasks SET next_attempt_at=0 WHERE task_id='t1'")
        store.claim("p1", "w2")
        assert store.fail("t1", "boom again", fencing=d.fencing) == "failed"
        assert store.get_task("t1")["state"] == "failed"
        assert store.get_task("b")["state"] == "blocked"
        inc = store._conn.execute("SELECT COUNT(*) n FROM incidents").fetchone()["n"]
        assert inc == 1

    def test_cancel_running_task_defers_terminalization(self, store):
        """Cancelling a running task flags it; the worker's report finalizes
        the attempt — no IllegalTransition race."""
        d = director(store)
        store.create_task("p1", contract(), fencing=d.fencing)
        store.claim("p1", "w1")
        store.cancel("t1", fencing=d.fencing)
        assert store.cancel_requested("t1")
        assert store.get_task("t1")["state"] == "running"
        store.submit_report("t1", "w1", report())
        assert store.get_task("t1")["state"] == "cancelled"

    def test_cancel_pending_task_terminalizes(self, store):
        d = director(store)
        store.create_task("p1", contract(), fencing=d.fencing)
        store.cancel("t1", fencing=d.fencing)
        assert store.get_task("t1")["state"] == "cancelled"


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

        def bad(c, ctx):
            raise RuntimeError("crash")
        d.handlers["core_product_engineer"] = bad
        d.delegate(contract(retry_limit=1))
        assert d.run_once("w1", {"repo_root": "."}) == "retry_wait"
        store._conn.execute("UPDATE tasks SET next_attempt_at=0")
        assert d.run_once("w1", {"repo_root": "."}) == "failed"
        n = store._conn.execute(
            "SELECT COUNT(*) n FROM attempts WHERE task_id='t1'").fetchone()["n"]
        assert n == 2  # handler actually ran (and crashed) twice

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
        ev = {"passed": True, "ref": "ci://run/123"}
        board.mark_passed("auth_isolation_billing_passed", d.fencing, ev)
        board.mark_passed("independent_e2e_verification_passed", d.fencing, ev)
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


class TestReviewHardening:
    def test_default_directors_conflict(self, store):
        """Two Director instances with default identity must not both acquire."""
        d1 = Director(store=store, project_id="p1")
        d1.acquire()
        assert d1.holder != "director" and d1.holder.startswith("director-")
        with pytest.raises(LeaseConflict):
            Director(store=store, project_id="p1").acquire()

    def test_long_task_outlives_director_ttl(self, store):
        """A handler slower than the Director TTL still verifies: the lease
        is extended to cover the contract's budget window."""
        d = Director(store=store, project_id="p1", holder="d1", lease_ttl_s=0.2)
        d.acquire()
        d.delegate(contract(budget_seconds=5.0))
        calls = {"n": 0}

        def slow_handler(c, ctx):
            calls["n"] += 1
            time.sleep(0.3)  # exceeds the 0.2s director TTL
            return report(c.task_id)

        d.handlers["core_product_engineer"] = slow_handler
        assert d.run_once("w1", {}) == "completed"

    def test_sweep_respects_retry_limit(self, store):
        """Expired running leases past the retry budget dead-letter, not retry."""
        d = director(store)
        d.delegate(contract(retry_limit=0))
        task = store.claim("p1", "w1", ttl_s=0.01)
        assert task is not None
        time.sleep(0.02)
        assert store.claim("p1", "w2") is None  # swept to failed, not retry_wait
        assert store.get_task("t1")["state"] == "failed"
        inc = store._conn.execute(
            "SELECT kind FROM incidents WHERE task_id='t1'").fetchone()
        assert inc["kind"] == "dead_letter"

    def test_late_dependent_starts_ready(self, store):
        """A task created after its deps completed must not stay pending."""
        d = director(store)
        d.delegate(contract("a"))
        store.claim("p1", "w")
        store.submit_report("a", "w", report("a"))
        store.accept("a", fencing=d.fencing)
        d.delegate(contract("b", dependencies=["a"]))
        assert store.get_task("b")["state"] == "ready"

    def test_idempotency_key_scoped_to_project(self, store):
        store.create_project("p2", "proj2", {}, {})
        d = director(store)
        d2 = Director(store=store, project_id="p2", holder="d-p2")
        d2.acquire()
        d.delegate(contract("a", idempotency_key="k"))
        # Same key + same fingerprint in another project → its own task.
        store.create_task("p2", contract("b", idempotency_key="k"), fencing=d2.fencing)
        assert store.get_task("b")["project_id"] == "p2"

    def test_changed_contract_reuses_nothing(self, store):
        d = director(store)
        d.delegate(contract("a", idempotency_key="k", budget_seconds=60))
        with pytest.raises(DuplicateIdempotencyKey):
            d.delegate(contract("a2", idempotency_key="k", budget_seconds=600))

    def test_positive_budget_rejected(self, store):
        d = director(store)
        with pytest.raises(ValueError, match="budget_usd"):
            store.create_task("p1", contract(budget_usd=5.0), fencing=d.fencing)

    def test_scope_violation_fails_task(self, store):
        d = director(store)
        d.delegate(contract(allowed_files=["src/"]))

        def out_of_scope(c, ctx):
            r = report(c.task_id)
            r.files_changed = ["etc/passwd"]
            return r

        d.handlers["core_product_engineer"] = out_of_scope
        outcome = d.run_once("w1", {})
        assert outcome in ("retry_wait", "failed")
        inc = store._conn.execute(
            "SELECT kind FROM incidents WHERE task_id='t1'").fetchone()
        assert inc["kind"] == "scope_violation"

    def test_undeclared_write_detected_by_fs_snapshot(self, store, tmp_path):
        """A handler that writes outside allowed_files but omits it from
        files_changed is still caught via the fs diff."""
        root = tmp_path / "repo"
        (root / "src").mkdir(parents=True)
        (root / "src" / "ok.py").write_text("x=1")
        d = director(store)
        d.delegate(contract(allowed_files=["src/"]))

        def sneaky(c, ctx):
            (root / "evil.py").write_text("bad")
            return report(c.task_id)  # does NOT declare the write

        d.handlers["core_product_engineer"] = sneaky
        outcome = d.run_once("w1", {"repo_root": str(root)})
        assert outcome in ("retry_wait", "failed")
        inc = store._conn.execute(
            "SELECT kind, detail_json FROM incidents WHERE task_id='t1'").fetchone()
        assert inc["kind"] == "scope_violation"
        assert "evil.py" in inc["detail_json"]

    def test_handler_deadline_kills_hung_task(self, store):
        """A handler that exceeds budget_seconds is terminated and the attempt
        consumes a retry instead of blocking the scheduler forever."""
        d = director(store)
        d.delegate(contract(budget_seconds=0.1, retry_limit=0))

        def hung(c, ctx):
            time.sleep(30)
            return report(c.task_id)

        d.handlers["core_product_engineer"] = hung
        outcome = d.run_once("w1", {})
        assert outcome == "failed"

    def test_release_frees_lease_for_next_invocation(self, store):
        """Sequential CLI-style Directors: release() lets the next one acquire
        immediately instead of LeaseConflict until TTL expiry."""
        d1 = director(store)
        d1.release()
        d2 = Director(store=store, project_id="p1", holder="d2")
        d2.acquire()  # no conflict

    def test_report_secrets_redacted(self, store):
        d = director(store)
        d.delegate(contract())
        store.claim("p1", "w")
        r = report("t1")
        r.limitations = ["uses token ghp_abcdef1234567890"]
        store.submit_report("t1", "w", r, artifacts=[{
            "artifact_id": "a1", "ref": "s3://bucket?key=AKIAIOSFODNN7EXAMPLE"}])
        row = store._conn.execute(
            "SELECT report_json FROM attempts WHERE task_id='t1'").fetchone()
        assert "ghp_" not in row["report_json"]
        art = store._conn.execute("SELECT ref FROM artifacts").fetchone()
        assert "AKIA" not in art["ref"]

    def test_decisions_and_incidents_redacted(self, store):
        d = director(store)
        store.record_decision("p1", d.fencing, "deploy",
                              {"note": "used key ghp_abcdef1234567890"})
        store.record_incident("p1", "leak", {"err": "bearer eyJhbGciOiJIUzI1NiJ9.e30.sig"})
        drow = store._conn.execute("SELECT detail_json FROM decisions").fetchone()
        crow = store._conn.execute("SELECT entry FROM changelog").fetchone()
        irow = store._conn.execute("SELECT detail_json FROM incidents").fetchone()
        assert "ghp_" not in drow["detail_json"]
        assert "ghp_" not in crow["entry"]
        assert "eyJ" not in irow["detail_json"]

    def test_mutations_require_fencing(self, store):
        with pytest.raises(TypeError):
            store.create_task("p1", contract())  # fencing is required

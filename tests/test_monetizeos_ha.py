"""Independent-process HA acceptance tests (no simulated shared-memory locks)."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from runtime.monetizeos import (
    CompletionReport, Director, FencingStale, LeaseConflict, Store, TaskContract,
)


def _until(predicate, seconds=7.0):
    limit = time.monotonic() + seconds
    while time.monotonic() < limit:
        result = predicate()
        if result:
            return result
        time.sleep(0.08)
    raise AssertionError("condition not reached before timeout")


def test_old_epoch_cannot_release_current_lease(tmp_path):
    s = Store(tmp_path / "epoch.db")
    s.create_project("epoch", "epoch", {}, {})
    d = Director(store=s, project_id="epoch", holder="same-holder", lease_ttl_s=5)
    d.acquire()
    old = d.fencing
    d.renew()
    assert d.fencing > old
    assert not s.release_director("epoch", "same-holder", old)
    assert s.status("epoch")["director"]["fencing"] == d.fencing
    d.release()
    s.close()


def test_heartbeat_prevents_takeover_during_long_handler(tmp_path):
    s = Store(tmp_path / "heartbeat.db")
    s.create_project("heartbeat", "heartbeat", {}, {})
    d = Director(store=s, project_id="heartbeat", holder="primary", lease_ttl_s=0.45)
    d.acquire()
    c = TaskContract(task_id="slow", process_owner="core_product_engineer",
                     objective="bounded slow validation", business_purpose="reliability",
                     verification_method="passing child report", budget_seconds=3)
    d.delegate(c)

    def handler(contract, _ctx):
        time.sleep(0.75)  # outlives both Director and short worker TTLs
        observer = Store(tmp_path / "heartbeat.db")
        try:
            assert observer.claim("heartbeat", "intruder") is None, (
                "worker lease expired while the specialist was still running"
            )
        finally:
            observer.close()
        time.sleep(0.25)
        return CompletionReport(task_id=contract.task_id, status="completed",
                                tests_run=[{"name": "slow", "command": "sleep",
                                            "result": "passed", "output": "completed"}])

    d.handlers["core_product_engineer"] = handler
    assert d.run_once("primary-worker", {"repo_root": str(tmp_path)},
                      lease_ttl_s=0.4) == "completed"
    assert s.get_task("slow")["state"] == "completed"
    d.release()
    s.close()


@pytest.mark.skipif(sys.platform != "linux", reason="service integration targets Linux hosts")
def test_real_two_process_standby_waits_then_takes_over(tmp_path):
    db = tmp_path / "ha.db"
    s = Store(db)
    s.create_project("ha", "ha", {}, {})

    base = [sys.executable, "-m", "runtime.monetizeos.standby",
            "--db", str(db), "--project-id", "ha",
            "--ttl", "1.0", "--poll", "0.12", "--run-seconds", "12"]
    env = dict(os.environ)
    root = str(Path(__file__).resolve().parents[1])
    env["PYTHONPATH"] = root
    primary = subprocess.Popen(base + ["--mode", "primary"], cwd=root, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    standby = None
    try:
        first = _until(lambda: s.status("ha")["director"])
        first_holder = first["holder"]
        standby = subprocess.Popen(base + ["--mode", "standby"], cwd=root, env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        time.sleep(0.45)
        assert s.status("ha")["director"]["holder"] == first_holder
        assert standby.poll() is None, "standby must remain alive while lease is active"

        # SIGKILL skips clean release. Standby must wait for the lease to expire.
        primary.kill()
        primary.wait(timeout=3)
        replacement = _until(lambda: (
            row if (row := s.status("ha")["director"]) is not None
            and row["holder"] != first_holder else None
        ), seconds=6)
        assert replacement["fencing"] > first["fencing"]
        assert standby.poll() is None
        with pytest.raises(FencingStale):
            s.record_decision("ha", first["fencing"], "stale_write", {})
    finally:
        if primary.poll() is None:
            primary.kill()
        primary.wait(timeout=3)
        if standby is not None:
            if standby.poll() is None:
                standby.terminate()
            standby.wait(timeout=3)
        s.close()


@pytest.mark.skipif(sys.platform != "linux", reason="service integration targets Linux hosts")
def test_standby_started_first_does_not_seize_lease(tmp_path):
    db = tmp_path / "no-primary.db"
    root = str(Path(__file__).resolve().parents[1])
    env = dict(os.environ, PYTHONPATH=root)
    cmd = [sys.executable, "-m", "runtime.monetizeos.standby", "--db", str(db),
           "--project-id", "no-primary", "--mode", "standby", "--ttl", "0.8",
           "--poll", "0.1", "--run-seconds", "0.5"]
    result = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    s = Store(db)
    try:
        assert s.status("no-primary")["director"] is None
    finally:
        s.close()


def test_stale_director_epoch_cannot_claim_task(tmp_path):
    s = Store(tmp_path / "claim-fence.db")
    s.create_project("p", "p", {}, {})
    old = Director(store=s, project_id="p", holder="old")
    old.acquire()
    contract = TaskContract(task_id="claimable", process_owner="repository_auditor",
                            objective="check", business_purpose="proof",
                            verification_method="verify")
    old.delegate(contract)
    s._conn.execute("UPDATE directors SET lease_expires_at=0 WHERE project_id='p'")
    replacement = Director(store=s, project_id="p", holder="replacement")
    replacement.acquire()
    with pytest.raises(FencingStale):
        s.claim("p", "old-worker", fencing=old.fencing)
    assert s.claim("p", "new-worker", fencing=replacement.fencing) is not None
    replacement.release()
    s.close()


def test_live_lease_rejects_competing_process_identity(tmp_path):
    s = Store(tmp_path / "conflict.db")
    s.create_project("test", "test", {}, {})
    a = Director(store=s, project_id="test", holder="a")
    b = Director(store=s, project_id="test", holder="b")
    a.acquire()
    with pytest.raises(LeaseConflict):
        b.acquire()
    a.release()
    s.close()

"""One agent call per process: result, failure, crash and deadline kill."""
import asyncio
import operator
import os
import time

import pytest

from runtime.gmaos import Plan, PlanNode, PlanRunner
from runtime.gmaos.isolation import IsolatedCallError, call_in_process, isolation_enabled


def test_returns_result_from_another_process():
    assert call_in_process(operator.add, 2, 3, timeout=30) == 5
    assert call_in_process(os.getpid, timeout=30) != os.getpid()


def test_child_exception_is_reported():
    with pytest.raises(IsolatedCallError, match="ValueError"):
        call_in_process(int, "not a number", timeout=30)


def test_child_crash_is_reported():
    with pytest.raises(IsolatedCallError, match="CRASHED: exit code 7"):
        call_in_process(os._exit, 7, timeout=30)


def test_hung_child_is_killed_at_deadline():
    t0 = time.monotonic()
    with pytest.raises(IsolatedCallError, match="TIMEOUT"):
        call_in_process(time.sleep, 60, timeout=1)
    assert time.monotonic() - t0 < 15


def test_isolation_is_opt_in(monkeypatch):
    monkeypatch.delenv("GMAOS_AGENT_ISOLATION", raising=False)
    assert not isolation_enabled()
    monkeypatch.setenv("GMAOS_AGENT_ISOLATION", "process")
    assert isolation_enabled()


def test_mesh_runs_each_llm_call_in_its_own_process_when_enabled(tmp_path, monkeypatch):
    import runtime.gmaos.executor as executor
    import runtime.inference_cascade as cascade
    from runtime.gmaos.core import Mesh
    from runtime.gmaos.store import StateStore

    monkeypatch.setenv("GMAOS_AGENT_ISOLATION", "process")
    monkeypatch.setattr(cascade, "infer", lambda s, p, **_: ('{"summary":"ok"}', "groq"))
    spawned = []

    def fake_call_in_process(fn, *args, timeout, **kwargs):
        spawned.append((fn.__name__, timeout))
        return fn(*args, **kwargs)

    monkeypatch.setattr(executor, "call_in_process", fake_call_in_process)

    async def go():
        mesh = Mesh(store=StateStore(db_path=tmp_path / "m.db",
                                     redis_url="redis://127.0.0.1:9999/99"))
        await mesh.start()
        try:
            nodes = tuple(
                PlanNode(id=i, wave=0, tier="T1", out_schema={"summary": "str"},
                         budget=2000, agent="plan_probe_agent", task="summarise")
                for i in ("a", "b")
            )
            return await PlanRunner(mesh).run(Plan(nodes=nodes, max_tokens=4000, max_nodes=2))
        finally:
            await mesh.stop()

    assert asyncio.run(go())["status"] == "OK"
    assert len(spawned) == 2 and all(t > 0 for _, t in spawned)

"""Plan runner: waves, projected handoffs, verify gates, budgets, HALTED."""
from __future__ import annotations

import asyncio
import json

from runtime.gmaos.plan import Plan, PlanNode, PlanRunner, validate_plan
from runtime.gmaos.schema import MeshResult, TaskStatus


class FakeMesh:
    """Replies with queued outputs per agent and records every task."""

    def __init__(self, replies: dict[str, list]):
        self.replies = {k: list(v) for k, v in replies.items()}
        self.tasks = []

    async def run(self, tasks):
        out = []
        for t in tasks:
            self.tasks.append(t)
            reply = self.replies[t.agent].pop(0)
            if isinstance(reply, MeshResult):
                out.append(reply)
                continue
            out.append(MeshResult(
                task_id=t.id, agent=t.agent, status=TaskStatus.COMPLETED,
                output=reply, tier="fake", duration_ms=1, retry_count=0,
                cached=False, trace_id=t.trace_id))
        return out


def run(plan, mesh=None):
    return asyncio.run(PlanRunner(mesh).run(plan))


def t0(id, wave, fn, schema, inputs=(), verify=None, budget=10):
    return PlanNode(id=id, wave=wave, tier="T0", fn=fn, out_schema=schema,
                    inputs=tuple(inputs), verify=verify, budget=budget)


def llm(id, wave, schema, inputs=(), verify=None, budget=400, agent="writer"):
    return PlanNode(id=id, wave=wave, tier="T1", agent=agent, task="summarise",
                    out_schema=schema, inputs=tuple(inputs), verify=verify, budget=budget)


def test_t0_only_plan_needs_no_mesh_and_spends_no_tokens():
    plan = Plan(
        nodes=(
            t0("a", 0, lambda i: {"n": i["mission.x"] + 1}, {"n": "int"}, ["mission.x"]),
            t0("b", 1, lambda i: {"n": i["a.n"] * 2}, {"n": "int"}, ["a.n"]),
        ),
        max_tokens=100, max_nodes=2, mission={"x": 1},
    )
    assert run(plan) == {"status": "OK", "artifacts": {"a": {"n": 2}, "b": {"n": 4}},
                         "tokens": 0, "nodes": 2}


def test_handoff_passes_only_projected_fields_as_minified_json():
    mesh = FakeMesh({"writer": ['{"summary":"ok"}']})
    plan = Plan(
        nodes=(
            t0("a", 0, lambda i: {"keep": "K", "drop": "SECRET_INTERMEDIATE"},
               {"keep": "str", "drop": "str"}),
            llm("b", 1, {"summary": "str"}, ["a.keep"]),
        ),
        max_tokens=1000, max_nodes=2,
    )
    result = run(plan, mesh)
    assert result["status"] == "OK"
    payload = mesh.tasks[0].payload
    assert "SECRET_INTERMEDIATE" not in json.dumps(payload)
    assert json.loads(payload["prompt"])["inputs"] == {"a.keep": "K"}
    assert ": " not in payload["prompt"] and ", " not in payload["prompt"]
    assert mesh.tasks[0].max_retries == 0


def test_system_prompt_is_static_across_different_inputs():
    systems = []
    for x in ("one", "two"):
        mesh = FakeMesh({"writer": ['{"summary":"ok"}']})
        plan = Plan(nodes=(llm("b", 0, {"summary": "str"}, ["mission.x"]),),
                    max_tokens=1000, max_nodes=1, mission={"x": x})
        assert run(plan, mesh)["status"] == "OK"
        systems.append(mesh.tasks[0].payload["system"])
    assert systems[0] == systems[1]


def test_same_wave_nodes_run_in_parallel():
    started = []

    async def slow(_):
        started.append(1)
        await asyncio.sleep(0.05)
        return {"seen": len(started)}

    plan = Plan(nodes=(t0("a", 0, slow, {"seen": "int"}), t0("b", 0, slow, {"seen": "int"})),
                max_tokens=100, max_nodes=2)
    result = run(plan)
    assert [result["artifacts"][k]["seen"] for k in "ab"] == [2, 2]


def test_one_retry_carries_only_inputs_and_error_then_succeeds():
    mesh = FakeMesh({"writer": ["not json at all", '{"summary":"fixed"}']})
    plan = Plan(nodes=(llm("b", 0, {"summary": "str"}, ["mission.x"]),),
                max_tokens=1000, max_nodes=1, mission={"x": "in"})
    result = run(plan, mesh)
    assert result["status"] == "OK" and result["artifacts"]["b"] == {"summary": "fixed"}
    assert len(mesh.tasks) == 2
    retry = json.loads(mesh.tasks[1].payload["prompt"])
    assert retry == {"task": "summarise", "inputs": {"mission.x": "in"},
                     "previous_error": "OUTPUT_NOT_JSON"}
    assert mesh.tasks[1].payload["system"] == mesh.tasks[0].payload["system"]


def test_second_failure_halts_and_never_propagates_downstream():
    ran = []
    mesh = FakeMesh({"writer": ['{"summary":""}', '{"summary":""}']})
    plan = Plan(
        nodes=(
            t0("a", 0, lambda i: {"n": 1}, {"n": "int"}),
            llm("b", 0, {"summary": "str"},
                verify=lambda o: None if o["summary"] else "summary empty"),
            t0("c", 1, lambda i: ran.append(1) or {"n": 2}, {"n": "int"}, ["b.summary"]),
        ),
        max_tokens=1000, max_nodes=3,
    )
    assert run(plan, mesh) == {"status": "HALTED", "node": "b",
                               "blocker": "VERIFY_FAILED: summary empty", "partial": ["a"]}
    assert len(mesh.tasks) == 2 and ran == []


def test_schema_type_mismatch_halts():
    plan = Plan(nodes=(t0("a", 0, lambda i: {"n": "1"}, {"n": "int"}),),
                max_tokens=10, max_nodes=1)
    result = run(plan)
    assert result["status"] == "HALTED"
    assert result["blocker"] == "OUTPUT_FIELD_TYPE: n: expected int, got str"


def test_node_exception_is_contained_as_halt():
    def boom(_):
        raise RuntimeError("disk full")
    plan = Plan(nodes=(t0("a", 0, boom, {"n": "int"}),), max_tokens=10, max_nodes=1)
    assert run(plan)["blocker"] == "NODE_RAISED: RuntimeError: disk full"


def test_stale_snapshot_from_mesh_is_rejected():
    stale = MeshResult(task_id="x", agent="writer", status=TaskStatus.COMPLETED_LOCAL,
                       output='{"summary":"old"}', tier="snapshot_err", duration_ms=1,
                       retry_count=0, cached=True, trace_id="t")
    mesh = FakeMesh({"writer": [stale, stale]})
    plan = Plan(nodes=(llm("b", 0, {"summary": "str"}),), max_tokens=1000, max_nodes=1)
    assert run(plan, mesh)["blocker"] == "STALE_SNAPSHOT_REJECTED"


def test_node_budget_is_enforced_without_retry():
    mesh = FakeMesh({"writer": ['{"summary":"' + "x" * 4000 + '"}']})
    plan = Plan(nodes=(llm("b", 0, {"summary": "str"}, budget=300),),
                max_tokens=1000, max_nodes=1)
    result = run(plan, mesh)
    assert result["status"] == "HALTED" and result["node"] == "b"
    assert result["blocker"].startswith("NODE_BUDGET_EXCEEDED")
    assert len(mesh.tasks) == 1
    assert mesh.tasks[0].payload["max_tokens"] < 300


def test_retry_output_cap_subtracts_first_attempt_spend():
    mesh = FakeMesh({"writer": ["x" * 400, '{"summary":"ok"}']})
    plan = Plan(nodes=(llm("b", 0, {"summary": "str"}, budget=400),),
                max_tokens=1000, max_nodes=1)
    result = run(plan, mesh)
    assert result["status"] == "OK" and result["tokens"] <= 400
    first, retry = (t.payload["max_tokens"] for t in mesh.tasks)
    assert retry < first - 100


def test_plan_limits_and_refs_are_checked_before_anything_runs():
    ran = []

    def fn(_):
        ran.append(1)
        return {"n": 1}

    a, b = t0("a", 0, fn, {"n": "int"}), t0("b", 1, fn, {"n": "int"}, ["a.n"])
    cases = {
        "MAX_NODES_EXCEEDED: 2 > 1": Plan(nodes=(a, b), max_tokens=100, max_nodes=1),
        "MAX_TOKENS_EXCEEDED: 20 > 5": Plan(nodes=(a, b), max_tokens=5, max_nodes=2),
        "INPUT_REF_NOT_UPSTREAM: b: 'a.n'": Plan(
            nodes=(a, t0("b", 0, fn, {"n": "int"}, ["a.n"])), max_tokens=100, max_nodes=2),
        "INPUT_REF_UNKNOWN: b: 'a.zzz'": Plan(
            nodes=(a, t0("b", 1, fn, {"n": "int"}, ["a.zzz"])), max_tokens=100, max_nodes=2),
        "T0_NODE_NEEDS_FN: a": Plan(
            nodes=(PlanNode(id="a", wave=0, tier="T0", out_schema={"n": "int"}, budget=1),),
            max_tokens=100, max_nodes=1),
    }
    for blocker, plan in cases.items():
        assert run(plan) == {"status": "HALTED", "node": "plan", "blocker": blocker,
                             "partial": []}
    assert ran == []
    assert run(Plan(nodes=(llm("b", 0, {"s": "str"}),), max_tokens=1000, max_nodes=1)
               )["blocker"] == "MESH_REQUIRED_FOR_LLM_NODES"


def test_from_dict_resolves_names_from_registries_only():
    data = {
        "max_tokens": 100, "max_nodes": 1, "mission": {"x": 2},
        "nodes": [{"id": "a", "wave": 0, "tier": "T0", "fn": "double", "verify": "positive",
                   "inputs": ["mission.x"], "out_schema": {"n": "int"}, "budget": 10}],
    }
    plan = Plan.from_dict(
        data,
        fns={"double": lambda i: {"n": i["mission.x"] * 2}},
        verifiers={"positive": lambda o: None if o["n"] > 0 else "not positive"},
    )
    assert validate_plan(plan) is None
    assert run(plan)["artifacts"] == {"a": {"n": 4}}
    try:
        Plan.from_dict(data)
    except ValueError as exc:
        assert "unknown fn 'double'" in str(exc)
    else:
        raise AssertionError("unregistered fn must be rejected")


def test_llm_node_runs_through_the_real_mesh(tmp_path, monkeypatch):
    import runtime.inference_cascade as cascade
    from runtime.gmaos.core import Mesh
    from runtime.gmaos.store import StateStore

    calls = []

    def fake_infer(system, prompt, max_tokens=1024, **_):
        calls.append((system, prompt, max_tokens))
        return 'Here you go: {"summary":"three"}', "groq"

    monkeypatch.setattr(cascade, "infer", fake_infer)

    async def go():
        mesh = Mesh(store=StateStore(db_path=tmp_path / "m.db",
                                     redis_url="redis://127.0.0.1:9999/99"))
        await mesh.start()
        try:
            plan = Plan(
                nodes=(
                    t0("a", 0, lambda i: {"n": 3}, {"n": "int"}),
                    llm("b", 1, {"summary": "str"}, ["a.n"], agent="plan_probe_agent"),
                ),
                max_tokens=1000, max_nodes=2,
            )
            return await PlanRunner(mesh).run(plan)
        finally:
            await mesh.stop()

    result = asyncio.run(go())
    assert result["status"] == "OK", result
    assert result["artifacts"] == {"a": {"n": 3}, "b": {"summary": "three"}}
    assert 0 < result["tokens"] <= 400
    assert len(calls) == 1 and '"a.n":3' in calls[0][1] and calls[0][2] < 400


def test_mesh_does_not_distill_plan_prompts(tmp_path, monkeypatch):
    import runtime.inference_cascade as cascade
    from runtime.gmaos.core import Mesh
    from runtime.gmaos.store import StateStore

    calls = []

    def fake_infer(system, prompt, max_tokens=1024, **_):
        calls.append(prompt)
        return '{"summary":"ok"}', "groq"

    monkeypatch.setattr(cascade, "infer", fake_infer)
    url = "https://alreadyherellc.com/content/post"
    long_text = "plain words " * 2000

    async def go():
        mesh = Mesh(store=StateStore(db_path=tmp_path / "m.db",
                                     redis_url="redis://127.0.0.1:9999/99"))
        await mesh.start()
        try:
            plan = Plan(nodes=(llm("b", 0, {"summary": "str"}, ["mission.url", "mission.doc"],
                                   agent="plan_probe_agent", budget=20000),),
                        max_tokens=20000, max_nodes=1,
                        mission={"url": url, "doc": long_text})
            return await PlanRunner(mesh).run(plan)
        finally:
            await mesh.stop()

    assert asyncio.run(go())["status"] == "OK"
    assert len(calls) == 1
    assert json.loads(calls[0])["inputs"] == {"mission.url": url, "mission.doc": long_text}


def _only_tiers(monkeypatch, cascade, replies):
    """Replace every cascade tier with a recorder; replies maps tier -> reply."""
    seen = []

    def make(tier):
        def call(system, prompt, max_tokens=1024):
            seen.append((tier, prompt))
            return replies.get(tier)
        return call

    monkeypatch.setattr(cascade, "_TIERS", [(make(t), t) for _, t in cascade._TIERS])
    return seen


def test_cascade_skips_paid_tier_unless_enabled(monkeypatch):
    import runtime.inference_cascade as cascade

    monkeypatch.delenv("GMAOS_PAID_ADAPTERS_ENABLED", raising=False)
    seen = _only_tiers(monkeypatch, cascade, {"claude_api": "paid", "pollinations": "free"})
    assert cascade.infer("s", "p") == ("free", "pollinations")
    assert "claude_api" not in [t for t, _ in seen]

    monkeypatch.setenv("GMAOS_PAID_ADAPTERS_ENABLED", "true")
    assert cascade.infer("s", "p") == ("paid", "claude_api")


def test_cascade_no_truncate_skips_tiers_that_would_cut_the_prompt(monkeypatch):
    import runtime.inference_cascade as cascade
    from runtime.token_budget import budget_for

    monkeypatch.delenv("GMAOS_PAID_ADAPTERS_ENABLED", raising=False)
    replies = {t: "ok" for _, t in cascade._TIERS}
    seen = _only_tiers(monkeypatch, cascade, replies)
    prompt = "word " * (budget_for("groq").max_input_chars // 5)  # fits gemini only
    out, tier = cascade.infer("s", prompt, truncate=False)
    assert (out, tier) == ("ok", "gemini") and seen == [("gemini", prompt)]

    seen.clear()
    huge = "word " * budget_for("claude_api").max_input_chars
    out, tier = cascade.infer("s", huge, truncate=False)
    assert tier == "deterministic_fallback" and seen == []
    assert "INPUT_EXCEEDS_TIER_BUDGET" in out

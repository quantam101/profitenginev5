"""
G-MAOS Task Executor
=====================
Executes a single Task through the full pipeline:

  1. Circuit breaker check     — skip if agent is OPEN
  2. Rate limiter check        — back-pressure if over quota
  3. Cache lookup              — return snapshot if fresh enough
  4. Input distillation        — compress prompt before LLM call
  5. Agent invocation          — calls runtime.agent_impls.<agent>.Agent().run()
                                 OR falls back to direct inference_cascade.infer()
  6. Output distillation       — compress snapshot before storing
  7. Snapshot write            — persist success output
  8. Metrics + circuit feedback

The executor is called once per task inside the async worker loop.
It is intentionally stateless (no __init__ state); all state is injected.
"""
from __future__ import annotations

import asyncio
import functools
import logging
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Optional, TYPE_CHECKING

from .schema import Task, MeshResult, TaskStatus
from .distill_engine import distill_task_input, distill_snapshot

if TYPE_CHECKING:
    from .store   import StateStore
    from .limiter import AdaptiveRateLimiter
    from .breaker import BreakerRegistry
    from .metrics import MeshMetrics

log = logging.getLogger("gmaos.executor")

# Thread pool for blocking I/O in agent_impls
_thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="gmaos-io")


async def execute_task(
    task:     Task,
    store:    "StateStore",
    limiter:  "AdaptiveRateLimiter",
    breakers: "BreakerRegistry",
    metrics:  "MeshMetrics",
    loop:     asyncio.AbstractEventLoop,
) -> MeshResult:
    """Full execution pipeline for a single Task."""
    t0 = time.perf_counter()
    agent = task.agent
    tid   = task.id

    # ── 1. stub bypass (test/dev only) ────────────────────────────────────
    if task._stub_response is not None:
        return _ok(task, task._stub_response, "stub", t0, 0, 0)

    # ── 2. circuit breaker ────────────────────────────────────────────────
    if not breakers.allow(agent):
        snap = store.load_snapshot(agent)
        if snap:
            log.debug("[%s] circuit OPEN — serving snapshot", tid)
            metrics.tasks_local.inc()
            return _ok(task, snap, "snapshot_open", t0, 0, 0, cached=True)
        metrics.tasks_failed.inc()
        return _err(task, "CIRCUIT_OPEN_NO_SNAPSHOT", t0)

    # ── 3. rate limiter ───────────────────────────────────────────────────
    wait = limiter.wait_time(agent)
    if wait > 0:
        if wait > task.timeout_sec * 0.5:
            # Would exhaust half the timeout just waiting — serve cache
            snap = store.load_snapshot(agent)
            if snap:
                metrics.rate_limit_hits.inc()
                metrics.tasks_local.inc()
                return _ok(task, snap, "snapshot_ratelimit", t0, 0, 0, cached=True)
        else:
            await asyncio.sleep(min(wait, 5.0))
        metrics.rate_limit_hits.inc()

    limiter.allow(agent)  # consume the token (best-effort)

    # ── 4. distillation ───────────────────────────────────────────────────
    system_raw = task.payload.get("system", "")
    user_raw   = task.payload.get("prompt", str(task.payload))
    objective  = task.payload.get("objective", task.payload.get("title", agent))

    dist_sys, dist_user, stage3, tok_in, tok_out = distill_task_input(
        system    = system_raw,
        user      = user_raw,
        objective = objective,
        agent_id  = agent,
        store     = store,
        task_id   = tid,
    )
    if stage3:
        metrics.distill_stage3.inc()
    metrics.tokens_in_total.inc(tok_in)

    # ── 5. agent invocation ───────────────────────────────────────────────
    output, tier, tokens_out = await _invoke_agent(
        task, dist_sys, dist_user, objective, loop
    )

    # ── 6. circuit feedback ───────────────────────────────────────────────
    if output.startswith("AGENT_ERROR:") or output.startswith("INFERENCE_STUB"):
        breakers.failure(agent)
        snap = store.load_snapshot(agent)
        if snap:
            metrics.tasks_local.inc()
            return _ok(task, snap, "snapshot_err", t0, tok_in, 0, cached=True)
        metrics.tasks_failed.inc()
        store.save_task(tid, agent, TaskStatus.FAILED, task.payload,
                        error=output[:200], retry_count=task.max_retries)
        return _err(task, output[:200], t0)
    else:
        breakers.success(agent)

    # ── 7. output distillation + snapshot ─────────────────────────────────
    snap_output = await loop.run_in_executor(
        _thread_pool,
        functools.partial(distill_snapshot, output, agent),
    )
    store.save_snapshot(agent, snap_output, tier,
                        distilled=bool(stage3),
                        tokens_in=tok_in, tokens_out=tokens_out)

    # ── 8. metrics ────────────────────────────────────────────────────────
    metrics.tasks_completed.inc()
    metrics.tokens_out_total.inc(tokens_out)
    metrics.record_tier(tier)

    dur = int((time.perf_counter() - t0) * 1000)
    metrics.task_duration_ms.observe(dur)

    result = MeshResult(
        task_id     = tid,
        agent       = agent,
        status      = TaskStatus.COMPLETED,
        output      = output,
        tier        = tier,
        duration_ms = dur,
        retry_count = 0,
        cached      = False,
        trace_id    = task.trace_id,
        tokens_in   = tok_in,
        tokens_out  = tokens_out,
        distilled   = stage3,
    )
    store.save_task(tid, agent, TaskStatus.COMPLETED, task.payload,
                    output=output[:4096], tier=tier,
                    tokens_in=tok_in, tokens_out=tokens_out,
                    distilled=stage3)
    return result


async def _invoke_agent(
    task: Task,
    system: str,
    user: str,
    objective: str,
    loop: asyncio.AbstractEventLoop,
) -> tuple[str, str, int]:
    """
    Try agent_impls.<agent>.Agent().run() first.
    Fall back to direct inference_cascade.infer() if not implemented.
    Returns (output, tier, tokens_out).
    """
    agent = task.agent

    # ── Try runtime.agent_impls first ────────────────────────────────────
    try:
        from runtime.agents import load_agent, AgentExecution
        agent_obj = await loop.run_in_executor(
            _thread_pool,
            functools.partial(_run_agent_impl, agent_obj=load_agent(agent),
                              payload=task.payload, system=system, user=user),
        )
        if agent_obj and not str(agent_obj.output).startswith("AGENT_ERROR:"):
            tok = int(agent_obj.metrics.get("tokens_out", 0))
            return agent_obj.output, agent_obj.metrics.get("tier", "agent_impl"), tok
    except (ImportError, ValueError, AttributeError):
        pass  # agent not in registry — fall through to inference cascade
    except Exception as exc:
        log.warning("[%s] agent_impl raised: %s — falling through to cascade", agent, exc)

    # ── Direct inference cascade fallback ────────────────────────────────
    try:
        from runtime.inference_cascade import infer
        prompt = user or objective or str(task.payload)
        sys_p  = system or f"You are the {agent} agent for ProfitEngine."
        output, tier = await loop.run_in_executor(
            _thread_pool,
            functools.partial(infer, sys_p, prompt,
                              max_tokens=task.payload.get("max_tokens", 1024)),
        )
        tok_out = max(1, len(output) // 4)
        return output, tier, tok_out
    except Exception as exc:
        return f"AGENT_ERROR: {exc}", "error", 0


def _run_agent_impl(agent_obj: Any, payload: dict, system: str, user: str) -> Any:
    """Synchronous wrapper for agent.run() — executed in thread pool."""
    try:
        if hasattr(agent_obj, "run"):
            return agent_obj.run(payload)
        if hasattr(agent_obj, "execute"):
            return agent_obj.execute(payload)
    except Exception as exc:
        from runtime.agents import AgentExecution
        return AgentExecution(
            output  = f"AGENT_ERROR: {exc}",
            metrics = {"tier": "error"},
        )
    return None


# ── helpers ───────────────────────────────────────────────────────────────────

def _ok(task: Task, output: str, tier: str, t0: float,
        tok_in: int, tok_out: int, cached: bool = False) -> MeshResult:
    dur = int((time.perf_counter() - t0) * 1000)
    return MeshResult(
        task_id     = task.id,
        agent       = task.agent,
        status      = TaskStatus.COMPLETED_LOCAL if cached else TaskStatus.COMPLETED,
        output      = output,
        tier        = tier,
        duration_ms = dur,
        retry_count = 0,
        cached      = cached,
        trace_id    = task.trace_id,
        tokens_in   = tok_in,
        tokens_out  = tok_out,
    )


def _err(task: Task, error: str, t0: float) -> MeshResult:
    dur = int((time.perf_counter() - t0) * 1000)
    return MeshResult(
        task_id     = task.id,
        agent       = task.agent,
        status      = TaskStatus.FAILED,
        output      = "",
        tier        = "error",
        duration_ms = dur,
        retry_count = 0,
        cached      = False,
        trace_id    = task.trace_id,
        error       = error,
    )

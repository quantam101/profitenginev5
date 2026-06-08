"""
G-MAOS Core — Zero-Origin Global Multi-Agent Operating System
=============================================================
Production-grade async orchestration mesh for ProfitEngine v5.

Architecture:
─────────────
                   ┌─────────────────────────────────────┐
    submit()  ──►  │  Priority Queue (asyncio.PriorityQueue)│
                   └────────────┬────────────────────────┘
                                │ N concurrent workers
                   ┌────────────▼────────────────────────┐
                   │  Rate Limiter  →  Circuit Breaker   │
                   └────────────┬────────────────────────┘
                                │
             ┌──────────────────┼──────────────────────┐
             │                  │                      │
        L1 Cache          Agent Impl            Inference Cascade
     (in-memory)     (runtime.agent_impls)   (8-tier: LMStudio→Ollama
                                              →Groq→HF→Gemini→Claude
                                              →Pollinations→stub)
             │                  │                      │
             └──────────────────┼──────────────────────┘
                                │
                   ┌────────────▼────────────────────────┐
                   │  3-Stage Distillation Engine        │
                   │  (strip→compress→LLM summarise)     │
                   └────────────┬────────────────────────┘
                                │
                   ┌────────────▼────────────────────────┐
                   │  3-Tier StateStore                  │
                   │  L1 Memory → L2 SQLite WAL → L3 Redis│
                   └─────────────────────────────────────┘

Failure hierarchy (most → least preferred):
  1. Agent impl succeeds
  2. Inference cascade succeeds (any tier)
  3. Agent snapshot served (stale but useful)
  4. Dead-letter queue (watchdog retries later)
  5. Hard error returned (never throws)

The mesh NEVER goes down. If every LLM tier fails and there is no snapshot,
it returns a structured error result and queues the task for retry.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional, Sequence

from .schema    import Task, MeshResult, TaskStatus, TaskPriority
from .store     import StateStore
from .limiter   import AdaptiveRateLimiter, LimiterConfig
from .breaker   import BreakerRegistry, BreakerConfig
from .metrics   import MeshMetrics, get_metrics
from .executor  import execute_task
from .watchdog  import Watchdog

log = logging.getLogger("gmaos.core")

_MAX_WORKERS    = int(os.getenv("GMAOS_MAX_WORKERS",   "16"))
_MAX_QUEUE_SIZE = int(os.getenv("GMAOS_QUEUE_SIZE",  "2048"))
_MAX_RETRIES    = int(os.getenv("GMAOS_MAX_RETRIES",     "3"))
_RETRY_DELAY    = float(os.getenv("GMAOS_RETRY_DELAY",  "2.0"))


class _PrioritizedTask:
    """Wrapper so asyncio.PriorityQueue orders by TaskPriority."""
    __slots__ = ("priority", "seq", "task")

    def __init__(self, task: Task, seq: int) -> None:
        self.priority = task.priority.value
        self.seq      = seq
        self.task     = task

    def __lt__(self, other: "_PrioritizedTask") -> bool:
        return (self.priority, self.seq) < (other.priority, other.seq)


class Mesh:
    """
    The G-MAOS mesh. Instantiate once per process.

    Usage:
        mesh = Mesh()
        await mesh.start()
        results = await mesh.run([Task(agent="content_gen", payload={...})])
        await mesh.stop()
    """

    def __init__(
        self,
        max_workers:  int           = _MAX_WORKERS,
        store:        Optional[StateStore]         = None,
        limiter:      Optional[AdaptiveRateLimiter] = None,
        breakers:     Optional[BreakerRegistry]    = None,
        metrics:      Optional[MeshMetrics]        = None,
    ) -> None:
        self._max_workers = max_workers
        self.store    = store    or StateStore()
        self.limiter  = limiter  or AdaptiveRateLimiter(LimiterConfig())
        self.breakers = breakers or BreakerRegistry(BreakerConfig())
        self.metrics  = metrics  or get_metrics()
        self._watchdog = Watchdog(self)

        self._queue: asyncio.PriorityQueue[_PrioritizedTask] = None  # type: ignore[assignment]
        self._workers: list[asyncio.Task] = []
        self._running  = False
        self._seq      = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ── lifecycle ─────────────────────────────────────────────────────────

    async def start(self) -> None:
        if self._running:
            return
        self._loop   = asyncio.get_running_loop()
        self._queue  = asyncio.PriorityQueue(maxsize=_MAX_QUEUE_SIZE)
        self._running = True

        # Spawn worker coroutines
        self._workers = [
            asyncio.create_task(self._worker(i), name=f"gmaos-worker-{i}")
            for i in range(self._max_workers)
        ]
        self.metrics.active_workers.set(self._max_workers)

        # Start background watchdog
        self._watchdog.start()
        log.info("G-MAOS mesh started: %d workers, queue_max=%d",
                 self._max_workers, _MAX_QUEUE_SIZE)

    async def stop(self, timeout: float = 30.0) -> None:
        if not self._running:
            return
        self._running = False
        self._watchdog.stop()

        # Drain queue
        await asyncio.wait_for(self._queue.join(), timeout=timeout)
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self.metrics.active_workers.set(0)
        log.info("G-MAOS mesh stopped cleanly")

    # ── public submission API ─────────────────────────────────────────────

    async def submit(self, task: Task) -> None:
        """Enqueue a task; returns immediately."""
        self.metrics.tasks_submitted.inc()
        self.metrics.queue_depth.inc()
        self._seq += 1
        await self._queue.put(_PrioritizedTask(task, self._seq))
        self.store.save_task(task.id, task.agent, TaskStatus.QUEUED, task.payload)

    async def run(self, tasks: Sequence[Task]) -> list[MeshResult]:
        """
        Submit all tasks, wait for all to complete, return results in order.
        This is the primary synchronous-style entry point.
        """
        if not self._running:
            await self.start()

        futures: dict[str, asyncio.Future[MeshResult]] = {
            t.id: asyncio.get_event_loop().create_future() for t in tasks
        }

        # Override executor to resolve futures on completion
        wrappers = [
            Task(
                id          = t.id,
                agent       = t.agent,
                payload     = {**t.payload, "_future_key": t.id},
                priority    = t.priority,
                max_retries = t.max_retries,
                timeout_sec = t.timeout_sec,
                trace_id    = t.trace_id,
                _stub_response = t._stub_response,
            )
            for t in tasks
        ]

        async def _run_and_resolve(task: Task) -> None:
            result = await self._execute_with_retry(task)
            fid = task.payload.get("_future_key", task.id)
            if fid in futures and not futures[fid].done():
                futures[fid].set_result(result)

        # Run all concurrently
        coros = [_run_and_resolve(t) for t in wrappers]
        await asyncio.gather(*coros)

        return [await futures[t.id] for t in tasks]

    # ── fire-and-forget ───────────────────────────────────────────────────

    async def fire(self, task: Task) -> None:
        """Submit without waiting for completion."""
        await self.submit(task)

    # ── worker loop ───────────────────────────────────────────────────────

    async def _worker(self, worker_id: int) -> None:
        log.debug("Worker %d started", worker_id)
        while self._running:
            try:
                prio_task = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            task = prio_task.task
            self.metrics.queue_depth.dec()
            try:
                await self._execute_with_retry(task)
            finally:
                self._queue.task_done()

        log.debug("Worker %d stopped", worker_id)

    # ── execution with retry + DLQ ────────────────────────────────────────

    async def _execute_with_retry(self, task: Task) -> MeshResult:
        loop   = asyncio.get_running_loop()
        retries = 0
        last_result: Optional[MeshResult] = None

        while retries <= min(task.max_retries, _MAX_RETRIES):
            if retries > 0:
                delay = _RETRY_DELAY * (2 ** (retries - 1))   # exponential
                log.debug("[%s] retry %d/%d in %.1fs",
                          task.id, retries, task.max_retries, delay)
                await asyncio.sleep(delay)
                self.metrics.tasks_retried.inc()
                self.store.save_task(task.id, task.agent, TaskStatus.RETRYING,
                                     task.payload, retry_count=retries)

            try:
                result = await asyncio.wait_for(
                    execute_task(task, self.store, self.limiter,
                                 self.breakers, self.metrics, loop),
                    timeout=task.timeout_sec,
                )
            except asyncio.TimeoutError:
                log.warning("[%s] timed out after %.0fs (retry %d)",
                            task.id, task.timeout_sec, retries)
                self.breakers.failure(task.agent)
                result = MeshResult(
                    task_id=task.id, agent=task.agent,
                    status=TaskStatus.FAILED,
                    output="", tier="timeout", duration_ms=int(task.timeout_sec * 1000),
                    retry_count=retries, cached=False, trace_id=task.trace_id,
                    error="TIMEOUT",
                )

            last_result = result

            if result.status in (TaskStatus.COMPLETED,
                                  TaskStatus.COMPLETED_LOCAL,
                                  TaskStatus.COMPLETED_DISTILL):
                return result

            retries += 1

        # Exhausted retries — move to DLQ
        assert last_result is not None
        log.error("[%s] exhausted retries → DLQ", task.id)
        self.metrics.tasks_dlq.inc()
        self.store.save_task(task.id, task.agent, TaskStatus.DLQ, task.payload,
                             error=last_result.error or "MAX_RETRIES",
                             retry_count=retries - 1)
        return MeshResult(
            task_id=task.id, agent=task.agent,
            status=TaskStatus.DLQ,
            output=last_result.output or "",
            tier="dlq",
            duration_ms=last_result.duration_ms,
            retry_count=retries - 1,
            cached=False, trace_id=task.trace_id,
            error=last_result.error or "MAX_RETRIES",
        )

    # ── observability ─────────────────────────────────────────────────────

    def health(self) -> dict:
        return {
            "running":        self._running,
            "queue_depth":    self._queue.qsize() if self._queue else 0,
            "active_workers": self._max_workers,
            "circuit_health": self.breakers.health_map(),
            "rate_limiter":   self.limiter.stats(),
            "metrics_snapshot": {
                "submitted":  int(self.metrics.tasks_submitted.get()),
                "completed":  int(self.metrics.tasks_completed.get()),
                "local":      int(self.metrics.tasks_local.get()),
                "failed":     int(self.metrics.tasks_failed.get()),
                "dlq":        int(self.metrics.tasks_dlq.get()),
                "tokens_in":  int(self.metrics.tokens_in_total.get()),
                "tokens_out": int(self.metrics.tokens_out_total.get()),
            },
        }


# ── module-level singleton ────────────────────────────────────────────────────

_singleton: Optional[Mesh] = None
_singleton_lock = asyncio.Lock()   # async-safe


async def get_mesh() -> Mesh:
    """Return (or create+start) the process-wide Mesh singleton."""
    global _singleton
    if _singleton is not None and _singleton._running:
        return _singleton
    async with _singleton_lock:
        if _singleton is None or not _singleton._running:
            _singleton = Mesh()
            await _singleton.start()
    return _singleton

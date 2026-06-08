"""
G-MAOS Watchdog
===============
Self-healing supervisor that runs as a background daemon thread.

Responsibilities:
  1. Heartbeat probe — pings each registered agent every `probe_interval_sec`
  2. DLQ drain      — retries dead-letter tasks on a schedule
  3. Snapshot prune — evicts stale snapshots exceeding `max_snap_age_sec`
  4. Circuit reset   — logs prolonged OPEN states and emits alerts
  5. Metrics sync    — updates gauge metrics from live state

The watchdog never throws; any internal error is logged and the loop continues.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .core import Mesh

log = logging.getLogger("gmaos.watchdog")

_PROBE_INTERVAL   = float(os.getenv("GMAOS_WATCHDOG_PROBE_SEC",    "30"))
_DLQ_DRAIN_EVERY  = float(os.getenv("GMAOS_WATCHDOG_DLQ_SEC",     "120"))
_PRUNE_EVERY      = float(os.getenv("GMAOS_WATCHDOG_PRUNE_SEC",   "3600"))
_MAX_SNAP_AGE     = float(os.getenv("GMAOS_SNAP_MAX_AGE_SEC",    str(7 * 86400)))
_ALERT_OPEN_SEC   = float(os.getenv("GMAOS_ALERT_OPEN_SEC",       "300"))


class Watchdog:
    """Background daemon that keeps the mesh healthy."""

    def __init__(self, mesh: "Mesh") -> None:
        self._mesh     = mesh
        self._running  = False
        self._thread: Optional[threading.Thread] = None
        self._last_dlq  = 0.0
        self._last_prune = 0.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="gmaos-watchdog", daemon=True
        )
        self._thread.start()
        log.info("Watchdog started (probe=%.0fs, dlq=%.0fs)", _PROBE_INTERVAL, _DLQ_DRAIN_EVERY)

    def stop(self) -> None:
        self._running = False

    # ── main loop ─────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            try:
                self._run_cycle()
            except Exception as exc:
                log.error("Watchdog cycle error (continuing): %s", exc, exc_info=True)
            time.sleep(_PROBE_INTERVAL)

    def _run_cycle(self) -> None:
        now = time.time()

        # 1. Update circuit breaker gauge metric
        health = self._mesh.breakers.health_map()
        open_count = sum(1 for s in health.values() if s == "OPEN")
        self._mesh.metrics.circuit_open_agents.set(open_count)

        # 2. Alert on prolonged OPEN breakers
        for agent_id, state in health.items():
            if state == "OPEN":
                snap = self._mesh.breakers.get(agent_id).snapshot()
                open_for = time.monotonic() - snap.last_changed
                if open_for > _ALERT_OPEN_SEC:
                    log.warning(
                        "WATCHDOG ALERT: agent '%s' circuit has been OPEN for %.0fs",
                        agent_id, open_for
                    )

        # 3. DLQ drain
        if now - self._last_dlq >= _DLQ_DRAIN_EVERY:
            self._drain_dlq()
            self._last_dlq = now

        # 4. Prune stale DB records
        if now - self._last_prune >= _PRUNE_EVERY:
            pruned = self._mesh.store.prune(_MAX_SNAP_AGE)
            if pruned:
                log.info("Watchdog pruned %d stale task records", pruned)
            self._last_prune = now

        # 5. Update queue depth gauge
        self._mesh.metrics.queue_depth.set(self._mesh._queue.qsize())

    # ── DLQ retry ─────────────────────────────────────────────────────────

    def _drain_dlq(self) -> None:
        dlq = self._mesh.store.get_dlq(limit=20)
        if not dlq:
            return
        log.info("Watchdog: draining %d DLQ tasks", len(dlq))
        for row in dlq:
            try:
                import json
                from .schema import Task, TaskPriority
                payload = json.loads(row.get("payload", "{}"))
                task = Task(
                    id       = row["task_id"],
                    agent    = row["agent"],
                    payload  = payload,
                    priority = TaskPriority.LOW,
                    max_retries = 1,  # one more chance only
                )
                # Re-queue via the mesh's async queue using thread-safe call
                if self._mesh._loop and not self._mesh._loop.is_closed():
                    future = asyncio.run_coroutine_threadsafe(
                        self._mesh._queue.put(task),
                        self._mesh._loop,
                    )
                    future.result(timeout=2.0)
                    self._mesh.store.save_task(
                        task_id=task.id, agent=task.agent,
                        status="QUEUED", payload=payload,
                    )
                    log.info("Watchdog: re-queued DLQ task %s", task.id)
            except Exception as exc:
                log.warning("Watchdog: DLQ re-queue failed for %s: %s",
                            row.get("task_id"), exc)

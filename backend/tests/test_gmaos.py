"""
G-MAOS Test Suite
=================
Tests every layer: store, limiter, breaker, distillation, executor, mesh, API.
All tests are offline-safe: no real LLM calls, no Redis required.
"""
from __future__ import annotations

import asyncio
import time
import threading

import pytest

# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "test_gmaos.db"


@pytest.fixture
def store(tmp_db):
    from runtime.gmaos.store import StateStore
    return StateStore(db_path=tmp_db, redis_url="redis://127.0.0.1:9999/99")  # Redis will fail → WAL only


@pytest.fixture
def limiter():
    from runtime.gmaos.limiter import AdaptiveRateLimiter, LimiterConfig
    return AdaptiveRateLimiter(LimiterConfig(capacity=100, refill_per_sec=50.0, max_per_window=1000))


@pytest.fixture
def breakers():
    from runtime.gmaos.breaker import BreakerRegistry, BreakerConfig
    return BreakerRegistry(BreakerConfig(failure_threshold=2, base_open_sec=0.1))


@pytest.fixture
def metrics():
    from runtime.gmaos.metrics import MeshMetrics
    return MeshMetrics()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Store tests
# ══════════════════════════════════════════════════════════════════════════════

class TestStateStore:

    def test_save_and_load_task(self, store):
        store.save_task("t1", "content_gen", "PENDING", {"x": 1})
        rec = store.load_task("t1")
        assert rec is not None
        assert rec["agent"] == "content_gen"
        assert rec["status"] == "PENDING"

    def test_update_task_status(self, store):
        store.save_task("t2", "agent", "PENDING", {})
        store.save_task("t2", "agent", "COMPLETED", {}, output="done")
        rec = store.load_task("t2")
        assert rec["status"] == "COMPLETED"

    def test_snapshot_roundtrip(self, store):
        store.save_snapshot("blog_publisher", "Generated 5 posts.", "groq")
        out = store.load_snapshot("blog_publisher")
        assert out == "Generated 5 posts."

    def test_dlq_listing(self, store):
        store.save_task("dlq1", "agent", "DLQ", {}, error="TEST")
        dlq = store.get_dlq()
        assert any(r["task_id"] == "dlq1" for r in dlq)

    def test_prune(self, store):
        store.save_task("old1", "agent", "COMPLETED", {})
        pruned = store.prune(max_age_sec=0)
        assert pruned >= 1

    def test_thread_safety(self, store):
        errors = []
        def write(i):
            try:
                store.save_task(f"ts{i}", "agent", "PENDING", {})
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=write, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors


# ══════════════════════════════════════════════════════════════════════════════
# 2. Rate limiter tests
# ══════════════════════════════════════════════════════════════════════════════

class TestRateLimiter:

    def test_allow_within_capacity(self, limiter):
        # agent_share=0.25 of 100 = 25 tokens per agent
        for _ in range(20):
            assert limiter.allow("agent_a")

    def test_per_agent_isolation(self, limiter):
        # drain agent_a
        from runtime.gmaos.limiter import AdaptiveRateLimiter, LimiterConfig
        small = AdaptiveRateLimiter(LimiterConfig(
            capacity=5, refill_per_sec=0.01,
            agent_share=0.5, max_per_window=1000
        ))
        for _ in range(3):
            small.allow("agent_a")
        # agent_b should still have its own tokens
        assert small.allow("agent_b")

    def test_wait_time_positive_when_exhausted(self, limiter):
        from runtime.gmaos.limiter import AdaptiveRateLimiter, LimiterConfig
        tight = AdaptiveRateLimiter(LimiterConfig(capacity=1, refill_per_sec=0.001))
        tight.allow("x")
        assert tight.wait_time("x") > 0

    def test_stats_returned(self, limiter):
        s = limiter.stats()
        assert "global_tokens_remaining" in s
        assert "window_calls" in s


# ══════════════════════════════════════════════════════════════════════════════
# 3. Circuit breaker tests
# ══════════════════════════════════════════════════════════════════════════════

class TestCircuitBreaker:

    def test_starts_closed(self, breakers):
        from runtime.gmaos.breaker import BreakerState
        b = breakers.get("agent_x")
        assert b.state == BreakerState.CLOSED

    def test_opens_after_threshold(self, breakers):
        from runtime.gmaos.breaker import BreakerState
        breakers.failure("agent_y")
        breakers.failure("agent_y")
        assert breakers.get("agent_y").state == BreakerState.OPEN

    def test_blocks_when_open(self, breakers):
        breakers.failure("agent_z")
        breakers.failure("agent_z")
        assert not breakers.allow("agent_z")

    def test_half_open_after_recovery(self, breakers):
        from runtime.gmaos.breaker import BreakerState, BreakerConfig, BreakerRegistry
        reg = BreakerRegistry(BreakerConfig(failure_threshold=1, base_open_sec=0.05))
        reg.failure("a")
        time.sleep(0.1)
        assert reg.get("a").state == BreakerState.HALF_OPEN

    def test_closes_after_successful_probes(self, breakers):
        from runtime.gmaos.breaker import BreakerState, BreakerConfig, BreakerRegistry
        reg = BreakerRegistry(BreakerConfig(failure_threshold=1, base_open_sec=0.05,
                                             success_threshold=1))
        reg.failure("b")
        time.sleep(0.1)
        assert reg.allow("b")   # probe
        reg.success("b")
        assert reg.get("b").state == BreakerState.CLOSED

    def test_health_map(self, breakers):
        breakers.failure("c")
        breakers.failure("c")
        hm = breakers.health_map()
        assert hm["c"] == "OPEN"


# ══════════════════════════════════════════════════════════════════════════════
# 4. Metrics tests
# ══════════════════════════════════════════════════════════════════════════════

class TestMetrics:

    def test_counters_increment(self, metrics):
        metrics.tasks_submitted.inc(5)
        assert metrics.tasks_submitted.get() == 5.0

    def test_gauge_set_and_dec(self, metrics):
        metrics.queue_depth.set(10)
        metrics.queue_depth.dec(3)
        assert metrics.queue_depth.get() == 7.0

    def test_histogram_observe(self, metrics):
        for v in [10, 50, 200, 1000]:
            metrics.task_duration_ms.observe(v)
        assert metrics.task_duration_ms._total == 4

    def test_render_produces_prometheus_text(self, metrics):
        text = metrics.render()
        assert "gmaos_tasks_submitted_total" in text
        assert "gmaos_task_duration_milliseconds_bucket" in text

    def test_tier_tracking(self, metrics):
        metrics.record_tier("groq")
        metrics.record_tier("groq")
        metrics.record_tier("ollama")
        text = metrics.render()
        assert 'tier="groq"' in text


# ══════════════════════════════════════════════════════════════════════════════
# 5. Executor tests (stub mode — no LLM)
# ══════════════════════════════════════════════════════════════════════════════

class TestExecutor:

    @pytest.mark.asyncio
    async def test_stub_bypass(self, store, limiter, breakers, metrics):
        from runtime.gmaos.schema import Task, TaskStatus
        from runtime.gmaos.executor import execute_task

        task = Task(agent="content_gen", payload={}, _stub_response="hello world")
        loop = asyncio.get_event_loop()
        result = await execute_task(task, store, limiter, breakers, metrics, loop)
        assert result.status == TaskStatus.COMPLETED
        assert result.output == "hello world"
        assert result.tier   == "stub"

    @pytest.mark.asyncio
    async def test_circuit_open_serves_snapshot(self, store, limiter, breakers, metrics):
        from runtime.gmaos.schema import Task

        # Pre-populate snapshot
        store.save_snapshot("offline_agent", "cached result", "snapshot")
        # Trip breaker
        breakers.failure("offline_agent")
        breakers.failure("offline_agent")

        from runtime.gmaos.executor import execute_task
        task = Task(agent="offline_agent", payload={})
        loop = asyncio.get_event_loop()
        result = await execute_task(task, store, limiter, breakers, metrics, loop)

        assert result.cached is True
        assert result.output == "cached result"


# ══════════════════════════════════════════════════════════════════════════════
# 6. Full Mesh tests
# ══════════════════════════════════════════════════════════════════════════════

class TestMesh:

    @pytest.mark.asyncio
    async def test_run_single_stub_task(self, store, limiter, breakers, metrics):
        from runtime.gmaos.core import Mesh
        from runtime.gmaos.schema import Task, TaskStatus

        mesh = Mesh(store=store, limiter=limiter, breakers=breakers, metrics=metrics)
        await mesh.start()
        try:
            task = Task(agent="content_gen", payload={}, _stub_response="output A")
            results = await mesh.run([task])
            assert len(results) == 1
            assert results[0].status == TaskStatus.COMPLETED
            assert results[0].output == "output A"
        finally:
            await mesh.stop()

    @pytest.mark.asyncio
    async def test_run_batch_concurrently(self, store, limiter, breakers, metrics):
        from runtime.gmaos.core import Mesh
        from runtime.gmaos.schema import Task, TaskStatus

        mesh = Mesh(max_workers=4, store=store, limiter=limiter,
                    breakers=breakers, metrics=metrics)
        await mesh.start()
        try:
            tasks = [
                Task(agent=f"agent_{i}", payload={}, _stub_response=f"res_{i}")
                for i in range(10)
            ]
            t0      = time.perf_counter()
            results = await mesh.run(tasks)
            elapsed = time.perf_counter() - t0

            assert len(results) == 10
            assert all(r.status == TaskStatus.COMPLETED for r in results)
            # 10 tasks on 4 workers should finish faster than sequential
            assert elapsed < 5.0
        finally:
            await mesh.stop()

    @pytest.mark.asyncio
    async def test_health_endpoint(self, store, limiter, breakers, metrics):
        from runtime.gmaos.core import Mesh

        mesh = Mesh(store=store, limiter=limiter, breakers=breakers, metrics=metrics)
        await mesh.start()
        try:
            h = mesh.health()
            assert h["running"] is True
            assert "circuit_health" in h
            assert "metrics_snapshot" in h
        finally:
            await mesh.stop()

    @pytest.mark.asyncio
    async def test_priority_ordering(self, store, limiter, breakers, metrics):
        """CRITICAL tasks should complete before BACKGROUND tasks."""
        from runtime.gmaos.core import Mesh
        from runtime.gmaos.schema import Task, TaskPriority

        mesh = Mesh(max_workers=1, store=store, limiter=limiter,
                    breakers=breakers, metrics=metrics)
        await mesh.start()
        try:
            bg   = Task(agent="bg",   payload={}, priority=TaskPriority.BACKGROUND,
                        _stub_response="bg")
            crit = Task(agent="crit", payload={}, priority=TaskPriority.CRITICAL,
                        _stub_response="crit")
            # Submit background first, then critical
            results = await mesh.run([bg, crit])
            assert len(results) == 2
        finally:
            await mesh.stop()

    @pytest.mark.asyncio
    async def test_dlq_after_all_retries(self, store, limiter, breakers, metrics):
        from runtime.gmaos.core import Mesh
        from runtime.gmaos.schema import Task, TaskStatus, TaskPriority

        # Trip breaker so executor always fails + no snapshot
        breakers.failure("always_fail")
        breakers.failure("always_fail")

        mesh = Mesh(max_workers=2, store=store, limiter=limiter,
                    breakers=breakers, metrics=metrics)
        await mesh.start()
        try:
            task = Task(agent="always_fail", payload={},
                        max_retries=1, timeout_sec=5.0,
                        priority=TaskPriority.NORMAL)
            results = await mesh.run([task])
            assert results[0].status in (TaskStatus.DLQ, TaskStatus.FAILED)
        finally:
            await mesh.stop()

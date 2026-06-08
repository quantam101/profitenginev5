"""
G-MAOS Metrics
==============
Prometheus-compatible in-process metrics.
No external dependency — exposes /metrics in text format.
Thread-safe; zero I/O on the hot path.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Optional


class _Counter:
    def __init__(self) -> None:
        self._v = 0.0
        self._lock = threading.Lock()

    def inc(self, n: float = 1.0) -> None:
        with self._lock:
            self._v += n

    def get(self) -> float:
        return self._v


class _Gauge:
    def __init__(self) -> None:
        self._v = 0.0
        self._lock = threading.Lock()

    def set(self, v: float) -> None:
        with self._lock:
            self._v = v

    def inc(self, n: float = 1.0) -> None:
        with self._lock:
            self._v += n

    def dec(self, n: float = 1.0) -> None:
        with self._lock:
            self._v -= n

    def get(self) -> float:
        return self._v


class _Histogram:
    """Fixed-bucket histogram (millisecond latency)."""
    BUCKETS = (10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, float("inf"))

    def __init__(self) -> None:
        self._counts: dict[float, int] = {b: 0 for b in self.BUCKETS}
        self._sum    = 0.0
        self._total  = 0
        self._lock   = threading.Lock()

    def observe(self, ms: float) -> None:
        with self._lock:
            self._sum   += ms
            self._total += 1
            for b in self.BUCKETS:
                if ms <= b:
                    self._counts[b] += 1

    def render(self, name: str, labels: str = "") -> str:
        lstr = f"{{{labels}}}" if labels else ""
        lines = []
        with self._lock:
            for b, cnt in self._counts.items():
                le = "+Inf" if b == float("inf") else str(b)
                lines.append(f'{name}_bucket{{{labels + "," if labels else ""}le="{le}"}} {cnt}')
            lines.append(f"{name}_sum{lstr} {self._sum:.3f}")
            lines.append(f"{name}_count{lstr} {self._total}")
        return "\n".join(lines)


class MeshMetrics:
    """Singleton metrics registry."""

    def __init__(self) -> None:
        # Counters
        self.tasks_submitted   = _Counter()
        self.tasks_completed   = _Counter()
        self.tasks_local       = _Counter()   # served from cache/offline
        self.tasks_failed      = _Counter()
        self.tasks_dlq         = _Counter()
        self.tasks_retried     = _Counter()
        self.circuit_opens     = _Counter()
        self.rate_limit_hits   = _Counter()
        self.distill_stage3    = _Counter()
        self.tokens_in_total   = _Counter()
        self.tokens_out_total  = _Counter()

        # Gauges
        self.queue_depth       = _Gauge()
        self.active_workers    = _Gauge()
        self.circuit_open_agents = _Gauge()

        # Histograms
        self.task_duration_ms  = _Histogram()
        self.queue_wait_ms     = _Histogram()

        # Per-tier counters
        self._tier_counts: dict[str, _Counter] = defaultdict(_Counter)
        self._tier_lock = threading.Lock()

        self._start_time = time.time()

    def record_tier(self, tier: str) -> None:
        with self._tier_lock:
            self._tier_counts[tier].inc()

    def render(self) -> str:
        """Return Prometheus text format."""
        lines = [
            "# HELP gmaos_tasks_submitted_total Tasks submitted to the mesh",
            "# TYPE gmaos_tasks_submitted_total counter",
            f"gmaos_tasks_submitted_total {self.tasks_submitted.get():.0f}",

            "# HELP gmaos_tasks_completed_total Tasks completed successfully",
            "# TYPE gmaos_tasks_completed_total counter",
            f"gmaos_tasks_completed_total {self.tasks_completed.get():.0f}",

            "# HELP gmaos_tasks_local_total Tasks served from local cache/snapshot",
            "# TYPE gmaos_tasks_local_total counter",
            f"gmaos_tasks_local_total {self.tasks_local.get():.0f}",

            "# HELP gmaos_tasks_failed_total Tasks that permanently failed",
            "# TYPE gmaos_tasks_failed_total counter",
            f"gmaos_tasks_failed_total {self.tasks_failed.get():.0f}",

            "# HELP gmaos_tasks_dlq_total Tasks moved to dead-letter queue",
            "# TYPE gmaos_tasks_dlq_total counter",
            f"gmaos_tasks_dlq_total {self.tasks_dlq.get():.0f}",

            "# HELP gmaos_circuit_opens_total Total circuit breaker open events",
            "# TYPE gmaos_circuit_opens_total counter",
            f"gmaos_circuit_opens_total {self.circuit_opens.get():.0f}",

            "# HELP gmaos_rate_limit_hits_total Requests rejected by rate limiter",
            "# TYPE gmaos_rate_limit_hits_total counter",
            f"gmaos_rate_limit_hits_total {self.rate_limit_hits.get():.0f}",

            "# HELP gmaos_distill_stage3_total Stage-3 LLM distillation invocations",
            "# TYPE gmaos_distill_stage3_total counter",
            f"gmaos_distill_stage3_total {self.distill_stage3.get():.0f}",

            "# HELP gmaos_tokens_in_total Input tokens estimated",
            "# TYPE gmaos_tokens_in_total counter",
            f"gmaos_tokens_in_total {self.tokens_in_total.get():.0f}",

            "# HELP gmaos_tokens_out_total Output tokens estimated",
            "# TYPE gmaos_tokens_out_total counter",
            f"gmaos_tokens_out_total {self.tokens_out_total.get():.0f}",

            "# HELP gmaos_queue_depth Current tasks waiting in queue",
            "# TYPE gmaos_queue_depth gauge",
            f"gmaos_queue_depth {self.queue_depth.get():.0f}",

            "# HELP gmaos_active_workers Active worker coroutines",
            "# TYPE gmaos_active_workers gauge",
            f"gmaos_active_workers {self.active_workers.get():.0f}",

            "# HELP gmaos_circuit_open_agents Agents with open circuit breakers",
            "# TYPE gmaos_circuit_open_agents gauge",
            f"gmaos_circuit_open_agents {self.circuit_open_agents.get():.0f}",

            "# HELP gmaos_uptime_seconds Mesh uptime",
            "# TYPE gmaos_uptime_seconds gauge",
            f"gmaos_uptime_seconds {time.time() - self._start_time:.1f}",

            "# HELP gmaos_task_duration_milliseconds Task execution latency",
            "# TYPE gmaos_task_duration_milliseconds histogram",
            self.task_duration_ms.render("gmaos_task_duration_milliseconds"),

            "# HELP gmaos_inference_tier_total Calls per inference tier",
            "# TYPE gmaos_inference_tier_total counter",
        ]
        with self._tier_lock:
            for tier, ctr in self._tier_counts.items():
                lines.append(f'gmaos_inference_tier_total{{tier="{tier}"}} {ctr.get():.0f}')

        return "\n".join(lines) + "\n"


# Module-level singleton
_metrics: Optional[MeshMetrics] = None
_metrics_lock = threading.Lock()


def get_metrics() -> MeshMetrics:
    global _metrics
    if _metrics is None:
        with _metrics_lock:
            if _metrics is None:
                _metrics = MeshMetrics()
    return _metrics


def metrics_text() -> str:
    return get_metrics().render()

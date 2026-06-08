"""
G-MAOS Rate Limiter
===================
Adaptive hybrid limiter: token bucket (burst) + sliding window (sustained).

  Token bucket   — absorbs instantaneous bursts up to `capacity`
  Sliding window — enforces sustained per-second / per-minute averages
  Per-agent      — each agent gets its own bucket to prevent monopolisation
  Backpressure   — `wait_time()` returns how many seconds the caller should
                   back off before retrying

All state is in-memory (not Redis) — intentionally so; rate limiting must
never block on I/O.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class LimiterConfig:
    # Token bucket
    capacity:        int   = 120    # max burst tokens
    refill_per_sec:  float = 10.0   # tokens added per second
    # Sliding window
    window_sec:      float = 60.0   # observation window
    max_per_window:  int   = 600    # max calls in that window
    # Per-agent sub-limits (applied multiplicatively)
    agent_share:     float = 0.25   # fraction of global limit per agent


class _AgentBucket:
    """Per-agent token bucket."""

    def __init__(self, capacity: float, refill: float) -> None:
        self._cap    = capacity
        self._refill = refill
        self._tokens = float(capacity)
        self._last   = time.monotonic()
        self._lock   = threading.Lock()

    def consume(self, n: float = 1.0) -> bool:
        with self._lock:
            now     = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self._cap, self._tokens + elapsed * self._refill)
            self._last   = now
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def wait_time(self, n: float = 1.0) -> float:
        with self._lock:
            deficit = n - self._tokens
            return max(0.0, deficit / self._refill)


class AdaptiveRateLimiter:
    """
    Global mesh rate limiter with per-agent sub-limits.
    Thread-safe; zero external dependencies.
    """

    def __init__(self, cfg: LimiterConfig | None = None) -> None:
        self._cfg   = cfg or LimiterConfig()
        self._lock  = threading.Lock()
        # Global token bucket
        self._global_tokens = float(self._cfg.capacity)
        self._last_refill   = time.monotonic()
        # Global sliding window (deque of timestamps)
        self._window: deque[float] = deque()
        # Per-agent buckets
        self._agent_buckets: dict[str, _AgentBucket] = defaultdict(
            lambda: _AgentBucket(
                capacity = self._cfg.capacity * self._cfg.agent_share,
                refill   = self._cfg.refill_per_sec * self._cfg.agent_share,
            )
        )

    # ── public API ────────────────────────────────────────────────────────

    def allow(self, agent: str = "_global_", tokens: float = 1.0) -> bool:
        """Return True if the request may proceed now."""
        return self._check_global(tokens) and self._agent_buckets[agent].consume(tokens)

    def wait_time(self, agent: str = "_global_", tokens: float = 1.0) -> float:
        """Seconds to wait before the next allow() call will likely return True."""
        return max(
            self._global_wait(tokens),
            self._agent_buckets[agent].wait_time(tokens),
        )

    def stats(self) -> dict:
        with self._lock:
            self._refill_global()
            return {
                "global_tokens_remaining": round(self._global_tokens, 1),
                "window_calls":            len(self._window),
                "window_max":              self._cfg.max_per_window,
                "agents_tracked":          len(self._agent_buckets),
            }

    # ── internals ─────────────────────────────────────────────────────────

    def _refill_global(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._global_tokens = min(
            float(self._cfg.capacity),
            self._global_tokens + elapsed * self._cfg.refill_per_sec,
        )
        self._last_refill = now
        # Prune sliding window
        cutoff = now - self._cfg.window_sec
        while self._window and self._window[0] < cutoff:
            self._window.popleft()

    def _check_global(self, tokens: float) -> bool:
        with self._lock:
            self._refill_global()
            if len(self._window) >= self._cfg.max_per_window:
                return False
            if self._global_tokens < tokens:
                return False
            self._global_tokens -= tokens
            self._window.append(time.monotonic())
            return True

    def _global_wait(self, tokens: float) -> float:
        with self._lock:
            self._refill_global()
            deficit = tokens - self._global_tokens
            bucket_wait = max(0.0, deficit / self._cfg.refill_per_sec)
            if len(self._window) >= self._cfg.max_per_window:
                oldest = self._window[0]
                window_wait = max(0.0, oldest + self._cfg.window_sec - time.monotonic())
            else:
                window_wait = 0.0
            return max(bucket_wait, window_wait)

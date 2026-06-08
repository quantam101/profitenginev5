"""
G-MAOS Circuit Breaker
======================
Three-state machine with full exponential back-off and per-agent isolation.

  CLOSED    — normal operation; failures are counted
  OPEN      — requests are rejected instantly; no calls to upstream
  HALF-OPEN — one probe call allowed; success resets, failure re-opens

Back-off schedule:
  open_duration doubles on each consecutive open event, capped at max_open_sec.
  A sustained recovery window resets the back-off to base.

Per-agent breakers:
  Each agent_id gets its own breaker so a single flaky agent cannot cascade
  failures into the rest of the mesh.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

log = logging.getLogger("gmaos.breaker")


class BreakerState(str, Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class BreakerConfig:
    failure_threshold:   int   = 3       # consecutive failures → OPEN
    success_threshold:   int   = 2       # consecutive successes in HALF-OPEN → CLOSED
    base_open_sec:       float = 15.0    # initial OPEN duration
    max_open_sec:        float = 300.0   # max OPEN duration (5 min)
    backoff_multiplier:  float = 2.0     # multiplier per open event
    recovery_window_sec: float = 120.0   # sustained closed time to reset backoff


@dataclass
class BreakerSnapshot:
    state:           BreakerState
    failure_streak:  int
    success_streak:  int
    open_duration:   float
    last_changed:    float
    open_count:      int       # lifetime count of OPEN transitions


class CircuitBreaker:
    """Single-agent circuit breaker."""

    def __init__(self, agent_id: str, cfg: BreakerConfig) -> None:
        self._id   = agent_id
        self._cfg  = cfg
        self._lock = threading.Lock()
        # State
        self._state:         BreakerState = BreakerState.CLOSED
        self._fail_streak:   int   = 0
        self._succ_streak:   int   = 0
        self._open_count:    int   = 0
        self._open_duration: float = cfg.base_open_sec
        self._last_changed:  float = time.monotonic()
        self._last_closed:   float = time.monotonic()
        self._probe_sent:    bool  = False

    # ── public surface ────────────────────────────────────────────────────

    @property
    def state(self) -> BreakerState:
        with self._lock:
            return self._evaluate_state()

    def allow(self) -> bool:
        """Return True if a call may proceed."""
        with self._lock:
            st = self._evaluate_state()
            if st == BreakerState.CLOSED:
                return True
            if st == BreakerState.HALF_OPEN and not self._probe_sent:
                self._probe_sent = True
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._fail_streak = 0
            if self._state == BreakerState.HALF_OPEN:
                self._succ_streak += 1
                if self._succ_streak >= self._cfg.success_threshold:
                    self._transition(BreakerState.CLOSED)
            elif self._state == BreakerState.CLOSED:
                # Check if we can reset back-off
                if time.monotonic() - self._last_closed >= self._cfg.recovery_window_sec:
                    self._open_duration = self._cfg.base_open_sec
                    self._open_count    = 0

    def record_failure(self) -> None:
        with self._lock:
            self._succ_streak = 0
            self._fail_streak += 1
            if self._state == BreakerState.HALF_OPEN:
                # Probe failed → back to OPEN with increased duration
                self._open_duration = min(
                    self._open_duration * self._cfg.backoff_multiplier,
                    self._cfg.max_open_sec,
                )
                self._transition(BreakerState.OPEN)
            elif (self._state == BreakerState.CLOSED
                  and self._fail_streak >= self._cfg.failure_threshold):
                self._transition(BreakerState.OPEN)

    def snapshot(self) -> BreakerSnapshot:
        with self._lock:
            return BreakerSnapshot(
                state          = self._state,
                failure_streak = self._fail_streak,
                success_streak = self._succ_streak,
                open_duration  = self._open_duration,
                last_changed   = self._last_changed,
                open_count     = self._open_count,
            )

    # ── internals ─────────────────────────────────────────────────────────

    def _evaluate_state(self) -> BreakerState:
        if self._state == BreakerState.OPEN:
            elapsed = time.monotonic() - self._last_changed
            if elapsed >= self._open_duration:
                self._transition(BreakerState.HALF_OPEN)
        return self._state

    def _transition(self, new_state: BreakerState) -> None:
        old = self._state
        self._state       = new_state
        self._last_changed = time.monotonic()
        self._probe_sent  = False
        self._succ_streak = 0
        if new_state == BreakerState.OPEN:
            self._open_count += 1
            log.warning("[%s] circuit OPEN (streak=%d, backoff=%.0fs, open#%d)",
                        self._id, self._fail_streak, self._open_duration, self._open_count)
        elif new_state == BreakerState.HALF_OPEN:
            log.info("[%s] circuit HALF-OPEN — probe allowed", self._id)
        elif new_state == BreakerState.CLOSED:
            self._last_closed = time.monotonic()
            log.info("[%s] circuit CLOSED — healthy", self._id)


class BreakerRegistry:
    """Thread-safe registry of per-agent circuit breakers."""

    def __init__(self, default_cfg: Optional[BreakerConfig] = None) -> None:
        self._cfg     = default_cfg or BreakerConfig()
        self._lock    = threading.Lock()
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, agent_id: str) -> CircuitBreaker:
        with self._lock:
            if agent_id not in self._breakers:
                self._breakers[agent_id] = CircuitBreaker(agent_id, self._cfg)
            return self._breakers[agent_id]

    def allow(self, agent_id: str) -> bool:
        return self.get(agent_id).allow()

    def success(self, agent_id: str) -> None:
        self.get(agent_id).record_success()

    def failure(self, agent_id: str) -> None:
        self.get(agent_id).record_failure()

    def health_map(self) -> dict[str, str]:
        with self._lock:
            return {aid: b.state.value for aid, b in self._breakers.items()}

"""
G-MAOS Agent Loss Limit Enforcer
==================================
Dynamic daily loss limit enforcement with volatility-aware scaling.

  Daily Limit = 200 USD * volatility_scalar
  volatility_scalar = (realized_vol_24h / base_vol) capped [0.5, 2.0]

  Track per-agent P&L across a 24-hour rolling window; reset at UTC midnight.
  Check PnL against the dynamic limit before allowing new positions.
  Calculate remaining loss budget with drift-aware precision.

Thread-safe; zero external dependencies; in-memory state (no Redis).
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("gmaos.agent_loss_limit")


@dataclass
class LossLimitConfig:
    """Configuration for dynamic loss limit enforcement."""
    base_daily_loss_usd: float = 200.0      # Base daily loss limit
    base_volatility:     float = 1.0        # Baseline volatility (e.g., 1.0 = 1%)
    vol_min_scalar:      float = 0.5        # Min volatility multiplier
    vol_max_scalar:      float = 2.0        # Max volatility multiplier
    window_sec:          float = 86400.0    # 24-hour rolling window
    cleanup_interval_sec: float = 3600.0    # Prune stale agent data hourly
    reserve_buffer_pct:  float = 0.05       # 5% reserve buffer for safety


@dataclass
class AgentPnLRecord:
    """Point-in-time P&L entry."""
    timestamp: float
    pnl_usd: float
    volatility: float = 1.0


class DynamicLossLimiter:
    """
    Per-agent daily loss limit enforcer with volatility-aware scaling.

    Usage:
        limiter = DynamicLossLimiter(cfg)
        # Before opening position:
        if limiter.check_pnl("agent_1", realized_loss=-50, vol_24h=1.2):
            # Safe to open position
        # Track realized loss:
        limiter.record_pnl("agent_1", pnl_usd=-50.0, volatility=1.2)
        # Check remaining capacity:
        remaining = limiter.calc_remaining("agent_1", vol_24h=1.2)
    """

    def __init__(self, cfg: LossLimitConfig | None = None) -> None:
        self._cfg = cfg or LossLimitConfig()
        self._lock = threading.Lock()
        # Per-agent rolling window of PnL records
        self._agent_pnl: dict[str, list[AgentPnLRecord]] = {}
        # Per-agent cumulative daily loss (cached, updates on record)
        self._agent_daily_loss: dict[str, float] = {}
        # Last cleanup timestamp
        self._last_cleanup = time.time()

    # ── public API ────────────────────────────────────────────────────────

    def check_pnl(
        self,
        agent_id: str,
        realized_loss: float,
        volatility_24h: float = 1.0,
    ) -> bool:
        """
        Check if opening a position with realized_loss would breach the limit.

        Args:
            agent_id: Unique agent identifier
            realized_loss: Loss in USD (negative = actual loss, e.g., -50 means $50 loss)
            volatility_24h: 24h realized volatility as scalar (e.g., 1.2 = 120% of base)

        Returns:
            True if position is allowed; False if it would exceed the loss limit
        """
        with self._lock:
            self._cleanup_stale_agents()
            cumulative = self._calc_cumulative_loss(agent_id)
            limit = self._calc_dynamic_limit(volatility_24h)
            reserve = limit * self._cfg.reserve_buffer_pct

            # Projected loss after opening position
            projected_loss = abs(cumulative + realized_loss)
            allowed_loss = limit - reserve

            is_allowed = projected_loss <= allowed_loss
            log.debug(
                f"check_pnl({agent_id}): cumul={cumulative:.2f} "
                f"new_loss={realized_loss:.2f} projected={projected_loss:.2f} "
                f"limit={limit:.2f} allowed={allowed_loss:.2f} => {is_allowed}"
            )
            return is_allowed

    def calc_remaining(
        self,
        agent_id: str,
        volatility_24h: float = 1.0,
    ) -> float:
        """
        Calculate remaining loss budget for an agent.

        Args:
            agent_id: Unique agent identifier
            volatility_24h: 24h realized volatility as scalar

        Returns:
            Remaining loss budget in USD (positive = available budget)
            Negative = already over limit
        """
        with self._lock:
            self._cleanup_stale_agents()
            cumulative = self._calc_cumulative_loss(agent_id)
            limit = self._calc_dynamic_limit(volatility_24h)
            reserve = limit * self._cfg.reserve_buffer_pct
            allowed_loss = limit - reserve
            remaining = allowed_loss - abs(cumulative)

            log.debug(
                f"calc_remaining({agent_id}): cumul={cumulative:.2f} "
                f"limit={limit:.2f} allowed={allowed_loss:.2f} remaining={remaining:.2f}"
            )
            return remaining

    def record_pnl(
        self,
        agent_id: str,
        pnl_usd: float,
        volatility: float = 1.0,
    ) -> None:
        """
        Record a realized P&L event (profit or loss).

        Args:
            agent_id: Unique agent identifier
            pnl_usd: P&L in USD (negative = loss, positive = profit)
            volatility: Volatility at time of event
        """
        with self._lock:
            if agent_id not in self._agent_pnl:
                self._agent_pnl[agent_id] = []

            record = AgentPnLRecord(
                timestamp=time.time(),
                pnl_usd=pnl_usd,
                volatility=volatility,
            )
            self._agent_pnl[agent_id].append(record)

            # Update cached cumulative
            self._agent_daily_loss[agent_id] = self._calc_cumulative_loss(agent_id)

            log.debug(
                f"record_pnl({agent_id}): pnl={pnl_usd:.2f} "
                f"cumul={self._agent_daily_loss[agent_id]:.2f}"
            )

    def get_agent_stats(self, agent_id: str) -> dict:
        """
        Return snapshot of agent's loss limit state.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Dict with keys:
              - agent_id
              - cumulative_loss_usd
              - num_events_24h
              - avg_volatility
              - dynamic_limit_usd
              - remaining_budget_usd
        """
        with self._lock:
            self._cleanup_stale_agents()
            if agent_id not in self._agent_pnl or not self._agent_pnl[agent_id]:
                avg_vol = self._cfg.base_volatility
            else:
                vols = [r.volatility for r in self._agent_pnl[agent_id]]
                avg_vol = sum(vols) / len(vols) if vols else self._cfg.base_volatility

            cumul = self._calc_cumulative_loss(agent_id)
            limit = self._calc_dynamic_limit(avg_vol)
            remaining = limit * (1 - self._cfg.reserve_buffer_pct) - abs(cumul)

            return {
                "agent_id": agent_id,
                "cumulative_loss_usd": round(cumul, 2),
                "num_events_24h": len(self._agent_pnl.get(agent_id, [])),
                "avg_volatility": round(avg_vol, 3),
                "dynamic_limit_usd": round(limit, 2),
                "remaining_budget_usd": round(remaining, 2),
            }

    def reset_agent(self, agent_id: str) -> None:
        """Reset all P&L history for an agent (e.g., at UTC midnight)."""
        with self._lock:
            self._agent_pnl[agent_id] = []
            self._agent_daily_loss[agent_id] = 0.0
            log.info(f"reset_agent({agent_id}): history cleared")

    def global_stats(self) -> dict:
        """Return snapshot of all tracked agents."""
        with self._lock:
            self._cleanup_stale_agents()
            agents = list(self._agent_pnl.keys())
            total_loss = sum(
                self._calc_cumulative_loss(aid) for aid in agents
            )
            return {
                "agents_tracked": len(agents),
                "total_cumulative_loss_usd": round(total_loss, 2),
                "config": {
                    "base_daily_loss_usd": self._cfg.base_daily_loss_usd,
                    "window_sec": self._cfg.window_sec,
                    "reserve_buffer_pct": self._cfg.reserve_buffer_pct,
                },
            }

    # ── internals ─────────────────────────────────────────────────────────

    def _calc_cumulative_loss(self, agent_id: str) -> float:
        """
        Calculate cumulative loss for an agent in the 24h window.
        Negative = actual loss, positive = profit.
        """
        if agent_id not in self._agent_pnl:
            return 0.0

        now = time.time()
        cutoff = now - self._cfg.window_sec
        records = self._agent_pnl[agent_id]

        # Prune expired records
        self._agent_pnl[agent_id] = [r for r in records if r.timestamp >= cutoff]

        # Sum remaining PnL
        cumul = sum(r.pnl_usd for r in self._agent_pnl[agent_id])
        return cumul

    def _calc_dynamic_limit(self, volatility_scalar: float) -> float:
        """
        Calculate the dynamic loss limit based on volatility.

        Formula: limit = base_daily_loss_usd * clamp(vol_scalar / base_vol, min, max)

        Args:
            volatility_scalar: Current volatility (e.g., 1.2 = 120% of base)

        Returns:
            Dynamic limit in USD
        """
        # Normalize to base volatility
        scaled_vol = volatility_scalar / self._cfg.base_volatility
        # Clamp to [vol_min_scalar, vol_max_scalar]
        clamped = max(self._cfg.vol_min_scalar, min(scaled_vol, self._cfg.vol_max_scalar))
        # Apply to base limit
        limit = self._cfg.base_daily_loss_usd * clamped
        return limit

    def _cleanup_stale_agents(self) -> None:
        """
        Remove agents with no recent activity.
        Called inside lock; interval-controlled by _last_cleanup.
        """
        now = time.time()
        if now - self._last_cleanup < self._cfg.cleanup_interval_sec:
            return

        cutoff = now - self._cfg.window_sec
        stale_agents = []

        for agent_id, records in self._agent_pnl.items():
            # Keep only recent records
            recent = [r for r in records if r.timestamp >= cutoff]
            if not recent:
                stale_agents.append(agent_id)
            else:
                self._agent_pnl[agent_id] = recent

        # Remove fully stale agents
        for agent_id in stale_agents:
            del self._agent_pnl[agent_id]
            if agent_id in self._agent_daily_loss:
                del self._agent_daily_loss[agent_id]

        self._last_cleanup = now
        if stale_agents:
            log.debug(f"cleanup: removed {len(stale_agents)} stale agents")

"""Kelly Criterion Position Sizing Agent

Calculates optimal position sizing using the Kelly criterion formula.
Applies risk management constraints and generates trading signals.

Methods:
- calc_kelly(): Compute Kelly fraction from win rate and odds
- calc_position(): Determine position size given account balance and Kelly fraction
- generate_signal(): Create actionable trading signal with position sizing

Kelly Criterion Formula:
f* = (bp - q) / b
where:
  f* = Kelly fraction (optimal portfolio fraction to bet)
  p = Win probability (historical win rate)
  q = Loss probability (1 - p)
  b = Odds (average win / average loss)

Applications:
- Portfolio sizing for systematic trading strategies
- Risk management via fractional Kelly (f*/2 for conservative approach)
- Position allocation across multiple signal sources
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AgentKellySignal")


class SignalType(Enum):
    """Trading signal direction."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"
    CLOSE = "close"


class SignalStrength(Enum):
    """Signal confidence level."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Historical performance data for Kelly calculation."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_probability: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    odds_ratio: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0

    def calculate_from_results(self, results: List[Dict[str, Any]]) -> None:
        """Calculate metrics from trade results list.

        Args:
            results: List of trade results with 'pnl' and 'direction' keys
        """
        if not results:
            return

        self.total_trades = len(results)
        wins = [r for r in results if r.get("pnl", 0) > 0]
        losses = [r for r in results if r.get("pnl", 0) < 0]

        self.winning_trades = len(wins)
        self.losing_trades = len(losses)

        if self.total_trades > 0:
            self.win_probability = self.winning_trades / self.total_trades

        if wins:
            self.avg_win = sum(r.get("pnl", 0) for r in wins) / len(wins)

        if losses:
            self.avg_loss = abs(sum(r.get("pnl", 0) for r in losses) / len(losses))

        if self.avg_loss > 0:
            self.odds_ratio = self.avg_win / self.avg_loss

        if self.avg_loss > 0:
            total_wins = sum(r.get("pnl", 0) for r in wins)
            total_losses = sum(abs(r.get("pnl", 0)) for r in losses)
            if total_losses > 0:
                self.profit_factor = total_wins / total_losses

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class KellySignal:
    """Trading signal with position sizing."""
    signal_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    direction: SignalType = SignalType.NEUTRAL
    strength: SignalStrength = SignalStrength.MODERATE
    kelly_fraction: float = 0.0
    fractional_kelly: float = 0.0
    recommended_position_size: float = 0.0
    position_units: float = 0.0
    entry_price: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    risk_reward_ratio: float = 0.0
    confidence_score: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["direction"] = self.direction.value
        data["strength"] = self.strength.value
        return data


class AgentKellySignal:
    """Kelly criterion position sizing and signal generation."""

    def __init__(
        self,
        account_balance: float = 10000.0,
        kelly_fraction_multiplier: float = 0.25,
        max_position_size_pct: float = 5.0,
        min_win_probability: float = 0.55,
    ):
        """Initialize Kelly signal agent.

        Args:
            account_balance: Total account balance in USD
            kelly_fraction_multiplier: Multiplier for fractional Kelly (0.25 = 1/4 Kelly)
            max_position_size_pct: Maximum position size as % of account (risk limit)
            min_win_probability: Minimum win probability to generate signal
        """
        self.account_balance = account_balance
        self.kelly_fraction_multiplier = kelly_fraction_multiplier
        self.max_position_size_pct = max_position_size_pct
        self.min_win_probability = min_win_probability
        self.logger = logging.getLogger("AgentKellySignal")

    def calc_kelly(
        self,
        win_probability: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """Calculate Kelly fraction using historical performance.

        Kelly formula: f* = (bp - q) / b
        where:
          b = avg_win / avg_loss (odds ratio)
          p = win_probability
          q = 1 - win_probability

        Args:
            win_probability: Probability of winning trade (0.0 to 1.0)
            avg_win: Average profit per winning trade
            avg_loss: Average loss per losing trade (absolute value)

        Returns:
            Kelly fraction (optimal portfolio fraction to risk)
        """
        if avg_loss == 0 or avg_win == 0:
            self.logger.warning("Invalid win/loss values for Kelly calculation")
            return 0.0

        if win_probability <= 0 or win_probability >= 1:
            self.logger.warning(f"Invalid win probability: {win_probability}")
            return 0.0

        b = avg_win / avg_loss  # Odds ratio
        p = win_probability
        q = 1 - win_probability

        kelly_fraction = (b * p - q) / b

        # Ensure kelly fraction stays within reasonable bounds
        if kelly_fraction < 0:
            return 0.0
        if kelly_fraction > 1.0:
            return 1.0

        return kelly_fraction

    def calc_position(
        self,
        kelly_fraction: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> Dict[str, float]:
        """Calculate position size given Kelly fraction and risk parameters.

        Args:
            kelly_fraction: Kelly fraction from calc_kelly()
            entry_price: Entry price for position
            stop_loss_price: Stop loss price (determines max loss per unit)

        Returns:
            Dictionary with position_size, position_units, and risk_amount
        """
        result = {
            "kelly_fraction": kelly_fraction,
            "fractional_kelly": kelly_fraction * self.kelly_fraction_multiplier,
            "position_size_pct": 0.0,
            "position_size_usd": 0.0,
            "position_units": 0.0,
            "risk_per_unit": 0.0,
            "total_risk": 0.0,
        }

        if entry_price <= 0 or stop_loss_price < 0:
            self.logger.warning("Invalid price inputs for position sizing")
            return result

        # Risk per unit is the difference between entry and stop loss
        risk_per_unit = abs(entry_price - stop_loss_price)
        result["risk_per_unit"] = risk_per_unit

        if risk_per_unit == 0:
            self.logger.warning("Zero risk per unit - position sizing aborted")
            return result

        # Apply fractional Kelly
        fractional_kelly = kelly_fraction * self.kelly_fraction_multiplier

        # Calculate position size as percentage of account
        position_size_pct = fractional_kelly * 100

        # Apply maximum position size constraint
        if position_size_pct > self.max_position_size_pct:
            position_size_pct = self.max_position_size_pct
            self.logger.warning(
                f"Position size capped at {self.max_position_size_pct}% "
                f"(Kelly suggested {fractional_kelly * 100:.2f}%)"
            )

        # Convert percentage to USD
        position_size_usd = (position_size_pct / 100) * self.account_balance

        # Calculate position units
        position_units = position_size_usd / entry_price

        # Total risk is position units * risk per unit
        total_risk = position_units * risk_per_unit

        result.update({
            "position_size_pct": position_size_pct,
            "position_size_usd": position_size_usd,
            "position_units": position_units,
            "total_risk": total_risk,
            "fractional_kelly": fractional_kelly,
        })

        return result

    def generate_signal(
        self,
        signal_id: str,
        metrics: PerformanceMetrics,
        direction: SignalType,
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        confidence_score: float = 0.5,
    ) -> KellySignal:
        """Generate trading signal with Kelly-optimized position sizing.

        Args:
            signal_id: Unique signal identifier
            metrics: PerformanceMetrics from historical analysis
            direction: Trade direction (LONG, SHORT, NEUTRAL)
            entry_price: Proposed entry price
            stop_loss_price: Stop loss price level
            take_profit_price: Take profit price level
            confidence_score: Signal confidence (0.0 to 1.0)

        Returns:
            KellySignal with position sizing and risk parameters
        """
        signal = KellySignal(signal_id=signal_id)
        signal.direction = direction
        signal.confidence_score = confidence_score

        # Validate inputs
        if direction == SignalType.NEUTRAL:
            signal.strength = SignalStrength.WEAK
            signal.message = "Neutral signal: no position recommended"
            return signal

        if metrics.win_probability < self.min_win_probability:
            signal.strength = SignalStrength.WEAK
            signal.message = (
                f"Win probability {metrics.win_probability:.2%} below minimum "
                f"{self.min_win_probability:.2%}"
            )
            return signal

        # Calculate Kelly fraction
        kelly_fraction = self.calc_kelly(
            win_probability=metrics.win_probability,
            avg_win=metrics.avg_win,
            avg_loss=metrics.avg_loss,
        )

        signal.kelly_fraction = kelly_fraction
        signal.fractional_kelly = kelly_fraction * self.kelly_fraction_multiplier

        # Calculate position sizing
        position_data = self.calc_position(
            kelly_fraction=kelly_fraction,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
        )

        signal.recommended_position_size = position_data["position_size_usd"]
        signal.position_units = position_data["position_units"]
        signal.entry_price = entry_price
        signal.stop_loss_price = stop_loss_price
        signal.take_profit_price = take_profit_price

        # Calculate risk/reward ratio
        if stop_loss_price > 0:
            upside = abs(take_profit_price - entry_price)
            downside = abs(entry_price - stop_loss_price)
            if downside > 0:
                signal.risk_reward_ratio = upside / downside

        # Determine signal strength based on metrics and confidence
        if confidence_score >= 0.8 and kelly_fraction >= 0.2:
            signal.strength = SignalStrength.CRITICAL
        elif confidence_score >= 0.7 or kelly_fraction >= 0.15:
            signal.strength = SignalStrength.STRONG
        elif confidence_score >= 0.6 or kelly_fraction >= 0.05:
            signal.strength = SignalStrength.MODERATE
        else:
            signal.strength = SignalStrength.WEAK

        # Build signal message
        signal.message = (
            f"{direction.value.upper()} signal: "
            f"Kelly={kelly_fraction:.2%}, Position={position_data['position_units']:.2f} units, "
            f"Risk/Reward={signal.risk_reward_ratio:.2f}, "
            f"Win Rate={metrics.win_probability:.2%}"
        )

        # Store detailed metrics in signal
        signal.details = {
            "metrics": metrics.to_dict(),
            "position_data": position_data,
            "kelly_multiplier": self.kelly_fraction_multiplier,
        }

        return signal

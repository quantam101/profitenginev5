"""
Dynamic Risk Adjustment Module
Monitors volatility across instruments and adjusts trading parameters in real-time.
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, Optional
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market condition regimes"""
    LOW_VOLATILITY = "low_volatility"
    NORMAL = "normal"
    HIGH_VOLATILITY = "high_volatility"
    CRISIS = "crisis"


@dataclass
class RegimeParameters:
    """Risk parameters for specific market regime"""
    kelly_fraction: float
    loss_limit_scalar: float
    max_position_size: float
    volatility_threshold_low: float
    volatility_threshold_high: float
    volatility_threshold_crisis: float


class DynamicRiskAdjuster:
    """
    Dynamically adjusts trading risk parameters based on real-time market volatility
    and market regime detection.
    """

    def __init__(
        self,
        baseline_daily_loss_limit: float = 200.0,
        kelly_base_fraction: float = 0.05,
        volatility_lookback_periods: int = 20,
        regime_switch_threshold: float = 0.95,
    ):
        """
        Initialize Dynamic Risk Adjuster.

        Args:
            baseline_daily_loss_limit: Base daily loss limit in USD ($200)
            kelly_base_fraction: Base Kelly fraction (5%)
            volatility_lookback_periods: Periods for volatility calculation
            regime_switch_threshold: Confidence threshold for regime change
        """
        self.baseline_daily_loss_limit = baseline_daily_loss_limit
        self.kelly_base_fraction = kelly_base_fraction
        self.volatility_lookback_periods = volatility_lookback_periods
        self.regime_switch_threshold = regime_switch_threshold

        # Rolling volatility storage by instrument
        self.volatility_buffer: Dict[str, deque] = {}

        # Current market regime and parameters
        self.current_regime = MarketRegime.NORMAL
        self.regime_confidence = 1.0
        self.last_regime_change = datetime.now()

        # Regime-specific parameters
        self.regimes = self._initialize_regimes()

        # Performance tracking
        self.daily_realized_loss = 0.0
        self.period_start = datetime.now()

    def _initialize_regimes(self) -> Dict[MarketRegime, RegimeParameters]:
        """Initialize market regime parameters"""
        return {
            MarketRegime.LOW_VOLATILITY: RegimeParameters(
                kelly_fraction=0.08,
                loss_limit_scalar=1.3,
                max_position_size=0.15,
                volatility_threshold_low=0.0,
                volatility_threshold_high=0.015,
                volatility_threshold_crisis=0.04,
            ),
            MarketRegime.NORMAL: RegimeParameters(
                kelly_fraction=0.05,
                loss_limit_scalar=1.0,
                max_position_size=0.10,
                volatility_threshold_low=0.015,
                volatility_threshold_high=0.03,
                volatility_threshold_crisis=0.04,
            ),
            MarketRegime.HIGH_VOLATILITY: RegimeParameters(
                kelly_fraction=0.02,
                loss_limit_scalar=0.7,
                max_position_size=0.05,
                volatility_threshold_low=0.03,
                volatility_threshold_high=0.06,
                volatility_threshold_crisis=0.08,
            ),
            MarketRegime.CRISIS: RegimeParameters(
                kelly_fraction=0.005,
                loss_limit_scalar=0.3,
                max_position_size=0.02,
                volatility_threshold_low=0.06,
                volatility_threshold_high=1.0,
                volatility_threshold_crisis=1.0,
            ),
        }

    def update_price_data(self, instrument: str, returns: list) -> None:
        """
        Update price data for an instrument. Called with latest returns.

        Args:
            instrument: Instrument identifier (e.g., 'BTC/USD')
            returns: List of recent returns (log returns preferred)
        """
        if instrument not in self.volatility_buffer:
            self.volatility_buffer[instrument] = deque(
                maxlen=self.volatility_lookback_periods
            )

        # Add returns to buffer
        for ret in returns:
            self.volatility_buffer[instrument].append(ret)

    def calculate_volatility_scalar(self, instrument: str) -> float:
        """
        Calculate volatility scalar for position sizing.

        The scalar ranges from 0.0 (high volatility, reduce size) to 1.5+ (low volatility, increase size).
        Uses exponential weighted moving average for faster response to volatility changes.

        Args:
            instrument: Instrument identifier

        Returns:
            Volatility scalar (1.0 = baseline Kelly)
        """
        if instrument not in self.volatility_buffer:
            return 1.0

        if len(self.volatility_buffer[instrument]) < 3:
            return 1.0

        returns = np.array(list(self.volatility_buffer[instrument]))

        # Calculate volatility with exponential weighting (recent data more important)
        weights = np.exp(np.linspace(-1, 0, len(returns)))
        weights /= weights.sum()

        # Annualized volatility (assuming 252 trading days)
        volatility = np.sqrt(252) * np.average(
            np.abs(returns), weights=weights
        )

        # Volatility scalar: inverse relationship (high vol = low scalar)
        # Reference volatility: 2% annualized
        reference_vol = 0.02
        scalar = reference_vol / max(volatility, 0.001)

        # Clip to reasonable bounds
        return np.clip(scalar, 0.1, 1.5)

    def adjust_daily_loss_limit(
        self, current_realized_loss: float
    ) -> Tuple[float, float]:
        """
        Adjust daily loss limit based on current volatility regime and realized losses.

        Implements progressive tightening:
        - At 50% of limit: reduce by 10%
        - At 75% of limit: reduce by 25%
        - At 90% of limit: stop new positions

        Args:
            current_realized_loss: Current realized loss for the trading period

        Returns:
            Tuple of (adjusted_limit, utilization_percent)
        """
        # Update realized loss tracking
        self.daily_realized_loss = current_realized_loss

        # Get regime parameters
        regime_params = self.regimes[self.current_regime]

        # Base limit with regime scalar
        regime_adjusted_limit = (
            self.baseline_daily_loss_limit
            * regime_params.loss_limit_scalar
        )

        # Apply progressive tightening
        utilization_ratio = current_realized_loss / regime_adjusted_limit

        if utilization_ratio >= 0.9:
            # Crisis: hard stop on new positions
            adjusted_limit = regime_adjusted_limit * 0.5
        elif utilization_ratio >= 0.75:
            # Reduce further: 25% reduction
            adjusted_limit = regime_adjusted_limit * 0.75
        elif utilization_ratio >= 0.5:
            # Initial reduction: 10% reduction
            adjusted_limit = regime_adjusted_limit * 0.9
        else:
            adjusted_limit = regime_adjusted_limit

        return adjusted_limit, utilization_ratio * 100

    def scale_kelly_fraction(
        self, instrument: str, base_kelly: Optional[float] = None
    ) -> float:
        """
        Scale Kelly fraction based on volatility and regime.

        Implementation: kelly_scaled = base_kelly * volatility_scalar * regime_kelly_adjustment

        Args:
            instrument: Instrument identifier
            base_kelly: Override base Kelly fraction (uses self.kelly_base_fraction if None)

        Returns:
            Scaled Kelly fraction ready for position sizing
        """
        base = base_kelly or self.kelly_base_fraction

        # Get volatility scalar (1.0 = baseline)
        vol_scalar = self.calculate_volatility_scalar(instrument)

        # Get regime parameters
        regime_params = self.regimes[self.current_regime]
        regime_kelly = regime_params.kelly_fraction

        # Combine scalars
        scaled_kelly = base * vol_scalar * (regime_kelly / self.kelly_base_fraction)

        # Final bounds
        return np.clip(scaled_kelly, 0.001, 0.20)

    def get_regime_parameters(self) -> RegimeParameters:
        """
        Get current regime parameters.

        Returns:
            RegimeParameters for the current market regime
        """
        return self.regimes[self.current_regime]

    def update_market_regime(
        self, volatility_metrics: Dict[str, float]
    ) -> Tuple[MarketRegime, float]:
        """
        Update market regime based on volatility metrics.

        Tracks regime confidence to smooth regime transitions.

        Args:
            volatility_metrics: Dict with 'mean_volatility' and 'volatility_spike' keys

        Returns:
            Tuple of (new_regime, confidence_score)
        """
        mean_vol = volatility_metrics.get("mean_volatility", 0.02)
        volatility_spike = volatility_metrics.get("volatility_spike", 1.0)

        # Determine regime based on thresholds
        if mean_vol > 0.06 or volatility_spike > 2.5:
            new_regime = MarketRegime.CRISIS
            confidence = min(1.0, volatility_spike / 2.0)
        elif mean_vol > 0.03 or volatility_spike > 1.5:
            new_regime = MarketRegime.HIGH_VOLATILITY
            confidence = min(1.0, mean_vol / 0.05)
        elif mean_vol < 0.015:
            new_regime = MarketRegime.LOW_VOLATILITY
            confidence = min(1.0, (0.02 - mean_vol) / 0.005)
        else:
            new_regime = MarketRegime.NORMAL
            confidence = 0.85

        # Check if regime change confidence meets threshold
        if new_regime != self.current_regime:
            if confidence >= self.regime_switch_threshold:
                self.current_regime = new_regime
                self.regime_confidence = confidence
                self.last_regime_change = datetime.now()

                logger.info(
                    f"Regime change: {self.current_regime.value} "
                    f"(confidence: {confidence:.2%})"
                )
        else:
            self.regime_confidence = confidence

        return self.current_regime, confidence

    def get_position_sizing_limits(
        self, portfolio_value: float
    ) -> Dict[str, float]:
        """
        Get position sizing limits based on current regime and portfolio value.

        Args:
            portfolio_value: Current total portfolio value

        Returns:
            Dict with max_position_usd, max_single_trade, and stop_loss_pct
        """
        regime_params = self.regimes[self.current_regime]

        max_position_usd = portfolio_value * regime_params.max_position_size
        max_single_trade = max_position_usd * 0.8  # 80% of max per trade
        stop_loss_pct = 0.02 if self.current_regime == MarketRegime.CRISIS else 0.03

        return {
            "max_position_usd": max_position_usd,
            "max_single_trade": max_single_trade,
            "stop_loss_pct": stop_loss_pct,
            "regime": self.current_regime.value,
            "regime_kelly": regime_params.kelly_fraction,
        }

    def reset_daily_limits(self) -> None:
        """Reset daily loss tracking for new trading period"""
        self.daily_realized_loss = 0.0
        self.period_start = datetime.now()

    def get_status(self) -> Dict:
        """
        Get current adjuster status for logging/monitoring.

        Returns:
            Dict with current regime, volatilities, and limits
        """
        return {
            "regime": self.current_regime.value,
            "regime_confidence": f"{self.regime_confidence:.2%}",
            "daily_loss": f"${self.daily_realized_loss:.2f}",
            "baseline_limit": f"${self.baseline_daily_loss_limit:.2f}",
            "regime_loss_limit_scalar": self.regimes[self.current_regime].loss_limit_scalar,
            "regime_kelly_fraction": self.regimes[self.current_regime].kelly_fraction,
        }

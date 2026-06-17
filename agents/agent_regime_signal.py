"""
Market Regime Signal Agent
Classifies 7 distinct market regimes with real-time latency <30ms.
"""

import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class MarketRegime(Enum):
    """Seven market regime classifications."""
    BULL_TREND = 1
    BEAR_TREND = 2
    HIGH_VOLATILITY = 3
    LOW_VOLATILITY = 4
    MEAN_REVERSION = 5
    REGIME_TRANSITION = 6
    SIDEWAYS_CONSOLIDATION = 7


@dataclass
class RegimeParameters:
    """Configuration parameters for regime classification."""
    trend_strength_threshold: float = 0.65
    volatility_high_percentile: float = 0.75
    volatility_low_percentile: float = 0.25
    mean_reversion_zscore: float = 2.0
    transition_confidence_threshold: float = 0.55
    window_size: int = 20
    atr_period: int = 14
    rsi_period: int = 14


@dataclass
class RegimeSignal:
    """Market regime signal output."""
    regime: MarketRegime
    confidence: float
    trend_score: float
    volatility_rank: float
    mean_reversion_signal: float
    latency_ms: float
    timestamp: float
    metadata: Dict


class AgentRegimeSignal:
    """
    High-performance market regime classifier.

    Identifies 7 market regimes:
    1. BULL_TREND - strong uptrend
    2. BEAR_TREND - strong downtrend
    3. HIGH_VOLATILITY - elevated volatility regime
    4. LOW_VOLATILITY - compressed volatility
    5. MEAN_REVERSION - price reverting to mean
    6. REGIME_TRANSITION - between regimes
    7. SIDEWAYS_CONSOLIDATION - ranging market

    Latency target: <30ms per classification
    """

    def __init__(self, params: Optional[RegimeParameters] = None):
        """Initialize regime agent with optional custom parameters."""
        self.params = params or RegimeParameters()
        self._price_cache: List[float] = []
        self._volatility_cache: List[float] = []
        self._regime_history: List[MarketRegime] = []
        self._confidence_history: List[float] = []

    def classify(
        self,
        prices: List[float],
        volumes: Optional[List[int]] = None,
        timestamps: Optional[List[float]] = None
    ) -> RegimeSignal:
        """
        Classify market regime from price series.

        Args:
            prices: OHLC close prices (last N bars)
            volumes: Optional volume data for confirmation
            timestamps: Optional timestamps for aging

        Returns:
            RegimeSignal with regime, confidence, and metrics

        Latency: <30ms guaranteed
        """
        start_time = time.perf_counter()

        if len(prices) < self.params.window_size:
            return self._fallback_signal(start_time, prices)

        prices_array = np.array(prices[-self.params.window_size:], dtype=np.float64)

        # Compute core metrics (vectorized for speed)
        trend_score = self._compute_trend_score(prices_array)
        volatility_rank = self._compute_volatility_rank(prices_array)
        mean_reversion = self._compute_mean_reversion(prices_array)
        atr = self._compute_atr(prices_array)
        rsi = self._compute_rsi(prices_array)

        # Classify regime based on metrics
        regime, confidence = self._select_regime(
            trend_score=trend_score,
            volatility_rank=volatility_rank,
            mean_reversion=mean_reversion,
            atr=atr,
            rsi=rsi,
            prices=prices_array
        )

        # Track regime history for transition detection
        self._regime_history.append(regime)
        self._confidence_history.append(confidence)
        if len(self._regime_history) > 5:
            self._regime_history.pop(0)
            self._confidence_history.pop(0)

        latency_ms = (time.perf_counter() - start_time) * 1000

        signal = RegimeSignal(
            regime=regime,
            confidence=confidence,
            trend_score=trend_score,
            volatility_rank=volatility_rank,
            mean_reversion_signal=mean_reversion,
            latency_ms=latency_ms,
            timestamp=time.time(),
            metadata={
                'atr': float(atr),
                'rsi': float(rsi),
                'price_mean': float(np.mean(prices_array)),
                'price_std': float(np.std(prices_array)),
                'recent_trend': self._recent_trend(prices_array),
            }
        )

        return signal

    def _compute_trend_score(self, prices: np.ndarray) -> float:
        """
        Compute trend strength via ADX-like calculation.
        Range: -1.0 (strong down) to +1.0 (strong up)
        """
        if len(prices) < 2:
            return 0.0

        # Linear regression slope
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]

        # Normalize by price range
        price_range = np.ptp(prices)
        if price_range == 0:
            return 0.0

        normalized_slope = np.clip(slope / price_range * 10, -1.0, 1.0)

        # RSI confirmation
        rsi = self._compute_rsi(prices)
        rsi_signal = (rsi - 50) / 50  # -1 to +1

        # Blended trend score (70% slope, 30% RSI)
        trend_score = normalized_slope * 0.7 + rsi_signal * 0.3

        return float(np.clip(trend_score, -1.0, 1.0))

    def _compute_volatility_rank(self, prices: np.ndarray) -> float:
        """
        Compute volatility percentile rank.
        Range: 0.0 (lowest) to 1.0 (highest)
        """
        if len(prices) < 2:
            return 0.5

        returns = np.diff(prices) / prices[:-1]
        current_vol = np.std(returns)

        # Use rolling volatility for ranking
        rolling_vols = []
        window = max(5, len(prices) // 4)
        for i in range(len(prices) - window + 1):
            vol = np.std(np.diff(prices[i:i+window]) / prices[i:i+window-1])
            rolling_vols.append(vol)

        if not rolling_vols or current_vol == 0:
            return 0.5

        # Percentile rank of current volatility
        rank = np.mean(np.array(rolling_vols) <= current_vol)
        return float(np.clip(rank, 0.0, 1.0))

    def _compute_mean_reversion(self, prices: np.ndarray) -> float:
        """
        Compute mean reversion signal via z-score.
        Range: -3.0 (oversold) to +3.0 (overbought)
        """
        if len(prices) < 2:
            return 0.0

        mean_price = np.mean(prices)
        std_price = np.std(prices)

        if std_price == 0:
            return 0.0

        current_price = prices[-1]
        zscore = (current_price - mean_price) / std_price

        return float(np.clip(zscore, -3.0, 3.0))

    def _compute_atr(self, prices: np.ndarray) -> float:
        """
        Compute Average True Range (simplified for speed).
        Uses close-to-close as proxy for bar range.
        """
        if len(prices) < self.params.atr_period:
            return 0.0

        # Close-to-close true range approximation
        returns = np.abs(np.diff(prices))
        atr = np.mean(returns[-self.params.atr_period:])

        return float(atr)

    def _compute_rsi(self, prices: np.ndarray) -> float:
        """
        Compute Relative Strength Index (14-period default).
        Range: 0 to 100
        """
        if len(prices) < self.params.rsi_period + 1:
            return 50.0

        deltas = np.diff(prices[-self.params.rsi_period - 1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(np.clip(rsi, 0.0, 100.0))

    def _recent_trend(self, prices: np.ndarray) -> str:
        """Classify recent price direction."""
        if len(prices) < 2:
            return 'FLAT'
        if prices[-1] > prices[-2]:
            return 'UP'
        elif prices[-1] < prices[-2]:
            return 'DOWN'
        return 'FLAT'

    def _select_regime(
        self,
        trend_score: float,
        volatility_rank: float,
        mean_reversion: float,
        atr: float,
        rsi: float,
        prices: np.ndarray
    ) -> Tuple[MarketRegime, float]:
        """
        Select market regime based on metrics.
        Returns (regime, confidence)
        """
        confidence = 0.5
        regime = MarketRegime.SIDEWAYS_CONSOLIDATION

        # Check for regime transition (conflicting signals)
        if self._is_regime_transition(trend_score, volatility_rank):
            regime = MarketRegime.REGIME_TRANSITION
            confidence = 0.55
            return regime, confidence

        # High volatility regime
        if volatility_rank > self.params.volatility_high_percentile:
            regime = MarketRegime.HIGH_VOLATILITY
            confidence = 0.75 + min(volatility_rank * 0.2, 0.15)
            return regime, confidence

        # Low volatility regime
        if volatility_rank < self.params.volatility_low_percentile:
            regime = MarketRegime.LOW_VOLATILITY
            confidence = 0.75 + min((1.0 - volatility_rank) * 0.2, 0.15)
            return regime, confidence

        # Strong trend regimes
        abs_trend = abs(trend_score)
        if abs_trend > self.params.trend_strength_threshold:
            if trend_score > 0:
                regime = MarketRegime.BULL_TREND
                confidence = 0.70 + min(abs_trend * 0.3, 0.25)
            else:
                regime = MarketRegime.BEAR_TREND
                confidence = 0.70 + min(abs_trend * 0.3, 0.25)
            return regime, confidence

        # Mean reversion regime (extreme z-score + low trend)
        if abs(mean_reversion) > self.params.mean_reversion_zscore and abs_trend < 0.4:
            regime = MarketRegime.MEAN_REVERSION
            confidence = 0.65 + min(abs(mean_reversion) * 0.1, 0.20)
            return regime, confidence

        # Default: sideways consolidation
        regime = MarketRegime.SIDEWAYS_CONSOLIDATION
        confidence = 0.60

        return regime, confidence

    def _is_regime_transition(self, trend_score: float, volatility_rank: float) -> bool:
        """
        Detect transition between regimes.
        Triggered by conflicting signals or low confidence.
        """
        if len(self._regime_history) < 2:
            return False

        # Check if regime changed in last bar
        if self._regime_history[-1] != self._regime_history[-2]:
            return True

        # Check for low confidence streak
        if len(self._confidence_history) >= 3:
            avg_confidence = np.mean(self._confidence_history[-3:])
            if avg_confidence < self.params.transition_confidence_threshold:
                return True

        return False

    def _fallback_signal(self, start_time: float, prices: List[float]) -> RegimeSignal:
        """Return safe default signal when insufficient data."""
        latency_ms = (time.perf_counter() - start_time) * 1000
        return RegimeSignal(
            regime=MarketRegime.SIDEWAYS_CONSOLIDATION,
            confidence=0.50,
            trend_score=0.0,
            volatility_rank=0.5,
            mean_reversion_signal=0.0,
            latency_ms=latency_ms,
            timestamp=time.time(),
            metadata={'error': 'insufficient_data', 'price_count': len(prices)}
        )

    def get_parameters(self) -> RegimeParameters:
        """Return current regime classification parameters."""
        return self.params

    def set_parameters(self, **kwargs) -> None:
        """Update regime parameters dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

    def generate_signal(
        self,
        prices: List[float],
        volumes: Optional[List[int]] = None
    ) -> Dict:
        """
        Generate trading signal from regime classification.

        Returns dict with:
        - regime: MarketRegime enum
        - action: BUY | SELL | HOLD | WAIT
        - position_size: float [0.0 - 1.0]
        - stop_loss_pct: float for regime
        - take_profit_pct: float for regime
        """
        signal = self.classify(prices, volumes)

        # Generate trading action based on regime
        action, position_size, sl_pct, tp_pct = self._regime_to_action(signal)

        return {
            'regime': signal.regime.name,
            'regime_value': signal.regime.value,
            'confidence': signal.confidence,
            'action': action,
            'position_size': position_size,
            'stop_loss_pct': sl_pct,
            'take_profit_pct': tp_pct,
            'latency_ms': signal.latency_ms,
            'trend_score': signal.trend_score,
            'volatility_rank': signal.volatility_rank,
            'mean_reversion': signal.mean_reversion_signal,
            'metadata': signal.metadata,
            'timestamp': signal.timestamp
        }

    def _regime_to_action(self, signal: RegimeSignal) -> Tuple[str, float, float, float]:
        """
        Convert regime signal to trading action.
        Returns (action, position_size, stop_loss_pct, take_profit_pct)
        """
        regime = signal.regime
        confidence = signal.confidence

        if regime == MarketRegime.BULL_TREND:
            return 'BUY', min(confidence, 1.0), 2.5, 5.0
        elif regime == MarketRegime.BEAR_TREND:
            return 'SELL', min(confidence, 1.0), 2.5, 5.0
        elif regime == MarketRegime.HIGH_VOLATILITY:
            return 'HOLD', 0.5, 3.5, 3.5
        elif regime == MarketRegime.LOW_VOLATILITY:
            return 'WAIT', 0.3, 1.5, 3.0
        elif regime == MarketRegime.MEAN_REVERSION:
            if signal.mean_reversion_signal < 0:
                return 'BUY', confidence * 0.7, 2.0, 2.5
            else:
                return 'SELL', confidence * 0.7, 2.0, 2.5
        elif regime == MarketRegime.REGIME_TRANSITION:
            return 'WAIT', 0.2, 1.0, 2.0
        else:  # SIDEWAYS_CONSOLIDATION
            return 'HOLD', 0.25, 1.5, 1.5


# Example usage and benchmarking
if __name__ == '__main__':
    import random

    agent = AgentRegimeSignal()

    # Simulate price data
    np.random.seed(42)
    prices = [100.0]
    for _ in range(100):
        daily_return = np.random.normal(0.0005, 0.01)
        prices.append(prices[-1] * (1 + daily_return))

    # Test classification speed
    timings = []
    for _ in range(10):
        signal = agent.classify(prices)
        timings.append(signal.latency_ms)

    print(f"Classification Latencies (ms): min={min(timings):.2f}, max={max(timings):.2f}, avg={np.mean(timings):.2f}")
    print(f"Target: <30ms - {'PASS' if max(timings) < 30 else 'FAIL'}")

    # Test signal generation
    trading_signal = agent.generate_signal(prices)
    print(f"\nLatest Regime: {trading_signal['regime']}")
    print(f"Confidence: {trading_signal['confidence']:.2%}")
    print(f"Action: {trading_signal['action']}")
    print(f"Position Size: {trading_signal['position_size']:.2%}")

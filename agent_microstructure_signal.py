import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from collections import deque
import time


@dataclass
class OrderBookSnapshot:
    """Lightweight order book snapshot for microstructure analysis."""
    bids: np.ndarray  # shape: (N, 2) - [price, volume]
    asks: np.ndarray  # shape: (N, 2) - [price, volume]
    timestamp_ns: int


@dataclass
class ImbalanceSignal:
    """Output signal from microstructure analysis."""
    imbalance_ratio: float  # bid_volume / (bid_volume + ask_volume)
    strength: float  # 0-1 normalized strength indicator
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0-1 confidence score
    latency_ns: int  # nanoseconds from snapshot to signal


class AgentMicrostructureSignal:
    """
    High-frequency bid-ask imbalance detector with sub-20ms latency.
    Detects directional pressure from order flow microstructure.
    """

    def __init__(
        self,
        lookback_depth: int = 10,
        imbalance_threshold: float = 0.55,
        strength_window: int = 100,
    ):
        """
        Initialize microstructure signal detector.

        Args:
            lookback_depth: Number of price levels to analyze
            imbalance_threshold: Threshold for bullish/bearish classification
            strength_window: Rolling window for strength calculation
        """
        self.lookback_depth = lookback_depth
        self.imbalance_threshold = imbalance_threshold
        self.strength_window = strength_window

        # Circular buffer for rolling strength calculations
        self.imbalance_history = deque(maxlen=strength_window)
        self.depth_imbalance_history = deque(maxlen=strength_window)

        # Cache for vectorized operations
        self._execution_times_ns = deque(maxlen=1000)

    def calc_imbalance(
        self,
        bids: np.ndarray,
        asks: np.ndarray,
        depth_levels: int = 5,
    ) -> Tuple[float, float, float]:
        """
        Calculate bid-ask imbalance with multi-level depth analysis.

        Args:
            bids: Array of [price, volume] for bid side (descending price order)
            asks: Array of [price, volume] for ask side (ascending price order)
            depth_levels: Number of price levels to use (1-10)

        Returns:
            Tuple of (imbalance_ratio, depth_weighted_imbalance, price_level_ratio)
            - imbalance_ratio: bid_vol / (bid_vol + ask_vol) [0, 1]
            - depth_weighted: weighted by price proximity
            - price_level_ratio: ratio of bid/ask level counts at market price
        """
        depth = min(depth_levels, len(bids), len(asks), self.lookback_depth)

        # Level 1 (market) imbalance
        bid_vol_l1 = float(np.sum(bids[:1, 1])) if len(bids) > 0 else 1e-9
        ask_vol_l1 = float(np.sum(asks[:1, 1])) if len(asks) > 0 else 1e-9

        imbalance_l1 = bid_vol_l1 / (bid_vol_l1 + ask_vol_l1)

        # Multi-level imbalance with exponential decay weighting
        if depth > 1:
            decay_weights = np.exp(-np.arange(depth) * 0.5)
            bid_weighted = np.sum(bids[:depth, 1] * decay_weights)
            ask_weighted = np.sum(asks[:depth, 1] * decay_weights)

            imbalance_weighted = bid_weighted / (bid_weighted + ask_weighted + 1e-10)
        else:
            imbalance_weighted = imbalance_l1

        # Price level distribution ratio
        price_level_ratio = float(len(bids[:depth])) / max(
            float(len(asks[:depth])), 1e-9
        )

        return imbalance_l1, imbalance_weighted, price_level_ratio

    def get_strength(self) -> Tuple[float, float]:
        """
        Calculate normalized strength from rolling imbalance history.

        Returns:
            Tuple of (imbalance_strength, trend_strength)
            - imbalance_strength: Deviation from 0.5 centerline [-1, 1]
            - trend_strength: Consistency of direction [0, 1]
        """
        if not self.imbalance_history:
            return 0.0, 0.0

        imbalances = np.array(list(self.imbalance_history))

        # Strength = how far from neutral (0.5)
        centerline_deviation = np.abs(imbalances - 0.5) * 2  # normalize to [0, 1]
        imbalance_strength = float(np.mean(centerline_deviation))

        # Trend strength = consistency of direction
        if len(imbalances) > 1:
            direction_consistency = np.sum(np.diff(imbalances) > 0) / len(imbalances)
            trend_strength = float(np.abs(2 * direction_consistency - 1))
        else:
            trend_strength = 0.0

        return imbalance_strength, trend_strength

    def generate_signal(
        self,
        order_book: OrderBookSnapshot,
        reference_price: Optional[float] = None,
    ) -> ImbalanceSignal:
        """
        Generate directional signal from microstructure analysis.

        Args:
            order_book: Current order book snapshot with bids/asks
            reference_price: Optional reference price for weighting (default: mid-price)

        Returns:
            ImbalanceSignal with direction, confidence, and latency metrics
        """
        signal_start_ns = time.perf_counter_ns()

        # Extract data
        bids = order_book.bids
        asks = order_book.asks

        if len(bids) == 0 or len(asks) == 0:
            return ImbalanceSignal(
                imbalance_ratio=0.5,
                strength=0.0,
                signal_type="neutral",
                confidence=0.0,
                latency_ns=0,
            )

        # Calculate imbalances at multiple depths
        imb_l1, imb_weighted, price_ratio = self.calc_imbalance(
            bids, asks, depth_levels=5
        )

        # Composite imbalance = weighted average of indicators
        composite_imbalance = (
            0.5 * imb_weighted + 0.3 * imb_l1 + 0.2 * np.clip(price_ratio / 2, 0, 1)
        )

        # Update history for strength calculation
        self.imbalance_history.append(composite_imbalance)
        self.depth_imbalance_history.append(price_ratio)

        # Calculate strength metrics
        imbalance_strength, trend_strength = self.get_strength()

        # Determine signal direction
        if composite_imbalance > self.imbalance_threshold:
            signal_type = "bullish"
            signed_strength = (
                composite_imbalance - self.imbalance_threshold
            ) / (1 - self.imbalance_threshold)
        elif composite_imbalance < (1 - self.imbalance_threshold):
            signal_type = "bearish"
            signed_strength = (
                (1 - self.imbalance_threshold) - composite_imbalance
            ) / (1 - self.imbalance_threshold)
        else:
            signal_type = "neutral"
            signed_strength = 0.0

        # Confidence = combination of imbalance magnitude and trend consistency
        magnitude_confidence = np.abs(composite_imbalance - 0.5) * 2
        confidence = (
            0.6 * magnitude_confidence + 0.4 * trend_strength
        ) * imbalance_strength

        # Calculate latency
        latency_ns = time.perf_counter_ns() - signal_start_ns

        signal = ImbalanceSignal(
            imbalance_ratio=float(composite_imbalance),
            strength=float(np.clip(confidence, 0.0, 1.0)),
            signal_type=signal_type,
            confidence=float(np.clip(confidence, 0.0, 1.0)),
            latency_ns=latency_ns,
        )

        self._execution_times_ns.append(latency_ns)

        return signal

    def get_latency_stats(self) -> Dict[str, float]:
        """
        Get execution latency statistics in milliseconds.

        Returns:
            Dictionary with p50, p95, p99 latency metrics
        """
        if not self._execution_times_ns:
            return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "max_ms": 0.0}

        times_ms = np.array(list(self._execution_times_ns)) / 1e6

        return {
            "p50_ms": float(np.percentile(times_ms, 50)),
            "p95_ms": float(np.percentile(times_ms, 95)),
            "p99_ms": float(np.percentile(times_ms, 99)),
            "max_ms": float(np.max(times_ms)),
        }

    def reset_history(self) -> None:
        """Clear rolling window history for fresh analysis."""
        self.imbalance_history.clear()
        self.depth_imbalance_history.clear()
        self._execution_times_ns.clear()

    def get_state_dict(self) -> Dict[str, Any]:
        """Export detector state for serialization."""
        return {
            "imbalance_history": list(self.imbalance_history),
            "depth_imbalance_history": list(self.depth_imbalance_history),
            "lookback_depth": self.lookback_depth,
            "imbalance_threshold": self.imbalance_threshold,
            "strength_window": self.strength_window,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore detector state from serialization."""
        self.imbalance_history = deque(
            state.get("imbalance_history", []), maxlen=self.strength_window
        )
        self.depth_imbalance_history = deque(
            state.get("depth_imbalance_history", []), maxlen=self.strength_window
        )
        self.lookback_depth = state.get("lookback_depth", self.lookback_depth)
        self.imbalance_threshold = state.get(
            "imbalance_threshold", self.imbalance_threshold
        )

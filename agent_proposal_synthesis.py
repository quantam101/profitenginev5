"""
Agent Proposal Synthesis Module

Fuses multiple trading signals into a single coherent proposal with
sub-5ms latency using weighted signal aggregation and stop-loss logic.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class SignalType(Enum):
    """Enumeration of supported signal types."""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    SENTIMENT = "sentiment"


@dataclass
class TradingSignal:
    """Represents a single trading signal input."""
    signal_type: SignalType
    confidence: float  # [0, 1]
    direction: int  # 1 (long), -1 (short), 0 (neutral)
    strength: float  # [0, 1]
    timestamp: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProposalOutput:
    """Output structure for synthesized proposal."""
    direction: int  # 1 (long), -1 (short), 0 (no trade)
    confidence: float  # [0, 1]
    entry_price: float
    stop_loss: float
    take_profit: Optional[float]
    position_size: float
    weighted_signals: Dict[str, float]
    synthesis_latency_ms: float
    timestamp: float
    rationale: str


class AgentProposalSynthesis:
    """
    Synthesizes multiple trading signals into a single coherent proposal.

    Implements weighted signal aggregation, confidence filtering, stop-loss
    logic, and real-time position sizing with sub-5ms latency.
    """

    def __init__(
        self,
        signal_weights: Optional[Dict[SignalType, float]] = None,
        min_confidence: float = 0.5,
        max_position_size: float = 1.0,
        atr_multiplier: float = 2.0,
        take_profit_multiplier: float = 2.5,
    ):
        """
        Initialize synthesis engine.

        Args:
            signal_weights: Custom weights per signal type. Defaults to equal.
            min_confidence: Minimum aggregated confidence to emit trade.
            max_position_size: Maximum position size [0, 1].
            atr_multiplier: Stop-loss distance in ATR multiples.
            take_profit_multiplier: Take-profit distance in ATR multiples.
        """
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.atr_multiplier = atr_multiplier
        self.take_profit_multiplier = take_profit_multiplier

        # Default equal weights across signal types
        self.signal_weights = signal_weights or {
            SignalType.MOMENTUM: 0.25,
            SignalType.MEAN_REVERSION: 0.25,
            SignalType.VOLATILITY: 0.25,
            SignalType.SENTIMENT: 0.25,
        }

        # Normalize weights to sum to 1
        weight_sum = sum(self.signal_weights.values())
        self.signal_weights = {
            k: v / weight_sum for k, v in self.signal_weights.items()
        }

        # Performance metrics
        self.last_synthesis_time = 0.0
        self.signal_buffer: List[TradingSignal] = []

    def synthesize(
        self,
        signals: List[TradingSignal],
        current_price: float,
        atr: float,
    ) -> ProposalOutput:
        """
        Synthesize multiple signals into a single proposal.

        Args:
            signals: List of TradingSignal inputs.
            current_price: Current market price (for entry/stop placement).
            atr: Average True Range for volatility-based stops.

        Returns:
            ProposalOutput with aggregated recommendation.

        Latency: <5ms for 4-8 signals.
        """
        start_time = time.perf_counter()

        # Input validation
        if not signals or len(signals) == 0:
            return self._create_neutral_proposal(current_price, start_time)

        # Step 1: Weight individual signals
        weighted_signals = self.weight_signals(signals)

        # Step 2: Aggregate direction and confidence
        aggregated_direction, aggregated_confidence = self._aggregate_signals(
            signals, weighted_signals
        )

        # Step 3: Check confidence threshold
        if aggregated_confidence < self.min_confidence:
            return self._create_neutral_proposal(current_price, start_time)

        # Step 4: Apply stop-loss logic
        stop_loss = self.apply_stop_loss(
            current_price, aggregated_direction, atr
        )

        # Step 5: Calculate take-profit
        take_profit = self._calculate_take_profit(
            current_price, aggregated_direction, atr
        )

        # Step 6: Determine position size
        position_size = self._calculate_position_size(aggregated_confidence)

        # Step 7: Build rationale
        signal_types = [s.signal_type.value for s in signals]
        rationale = (
            f"Fused {len(signals)} signals ({', '.join(signal_types)}): "
            f"direction={aggregated_direction:+d}, "
            f"confidence={aggregated_confidence:.2%}"
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.last_synthesis_time = elapsed_ms

        return ProposalOutput(
            direction=aggregated_direction,
            confidence=aggregated_confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            weighted_signals=weighted_signals,
            synthesis_latency_ms=elapsed_ms,
            timestamp=time.time(),
            rationale=rationale,
        )

    def weight_signals(self, signals: List[TradingSignal]) -> Dict[str, float]:
        """
        Assign weights to signals based on type and aggregate scores.

        Weighting strategy:
        - Base weight from signal_weights dict per type
        - Multiply by signal confidence and strength
        - Normalize to [0, 1] sum

        Args:
            signals: List of TradingSignal inputs.

        Returns:
            Dict mapping signal type to final normalized weight [0, 1].
        """
        weighted_map: Dict[str, float] = {}

        for signal in signals:
            signal_key = f"{signal.signal_type.value}_{signals.index(signal)}"
            base_weight = self.signal_weights.get(signal.signal_type, 0.25)
            # Combine base weight, confidence, and strength
            combined_weight = (
                base_weight * signal.confidence * signal.strength
            )
            weighted_map[signal_key] = combined_weight

        # Normalize to [0, 1]
        total_weight = sum(weighted_map.values())
        if total_weight > 0:
            weighted_map = {
                k: v / total_weight for k, v in weighted_map.items()
            }
        else:
            return {f"none_{i}": 0.0 for i in range(len(signals))}

        return weighted_map

    def apply_stop_loss(
        self,
        current_price: float,
        direction: int,
        atr: float,
    ) -> float:
        """
        Calculate stop-loss price using ATR-based logic.

        For long positions: stop = current_price - (atr * multiplier)
        For short positions: stop = current_price + (atr * multiplier)

        Args:
            current_price: Entry price.
            direction: Trade direction (1=long, -1=short).
            atr: Average True Range volatility measure.

        Returns:
            Stop-loss price.
        """
        if direction == 0:
            return current_price

        stop_distance = atr * self.atr_multiplier

        if direction == 1:  # Long
            return current_price - stop_distance
        else:  # Short
            return current_price + stop_distance

    def _create_neutral_proposal(
        self,
        current_price: float,
        start_time: float,
    ) -> ProposalOutput:
        """Create a neutral (no-trade) proposal."""
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return ProposalOutput(
            direction=0,
            confidence=0.0,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit=None,
            position_size=0.0,
            weighted_signals={},
            synthesis_latency_ms=elapsed_ms,
            timestamp=time.time(),
            rationale="No valid trade signal.",
        )

    def _aggregate_signals(
        self,
        signals: List[TradingSignal],
        weighted_signals: Dict[str, float],
    ) -> Tuple[int, float]:
        """
        Aggregate signal directions and confidence scores.

        Uses weighted voting on direction with aggregate confidence
        based on agreement strength.

        Returns:
            Tuple of (aggregated_direction, aggregated_confidence).
        """
        if not signals:
            return 0, 0.0

        # Weighted direction vote
        long_votes = 0.0
        short_votes = 0.0

        for idx, signal in enumerate(signals):
            signal_key = f"{signal.signal_type.value}_{idx}"
            weight = weighted_signals.get(signal_key, 0.0)

            if signal.direction == 1:
                long_votes += weight * signal.confidence
            elif signal.direction == -1:
                short_votes += weight * signal.confidence

        # Determine final direction
        if long_votes > short_votes:
            aggregated_direction = 1
            aggregated_confidence = long_votes
        elif short_votes > long_votes:
            aggregated_direction = -1
            aggregated_confidence = short_votes
        else:
            aggregated_direction = 0
            aggregated_confidence = 0.0

        # Clip confidence to [0, 1]
        aggregated_confidence = min(aggregated_confidence, 1.0)

        return aggregated_direction, aggregated_confidence

    def _calculate_take_profit(
        self,
        current_price: float,
        direction: int,
        atr: float,
    ) -> Optional[float]:
        """
        Calculate take-profit price using ATR-based logic.

        For long positions: tp = current_price + (atr * tp_multiplier)
        For short positions: tp = current_price - (atr * tp_multiplier)

        Args:
            current_price: Entry price.
            direction: Trade direction (1=long, -1=short).
            atr: Average True Range volatility measure.

        Returns:
            Take-profit price or None if direction is neutral.
        """
        if direction == 0:
            return None

        tp_distance = atr * self.take_profit_multiplier

        if direction == 1:  # Long
            return current_price + tp_distance
        else:  # Short
            return current_price - tp_distance

    def _calculate_position_size(self, confidence: float) -> float:
        """
        Calculate position size based on confidence.

        Uses sigmoid-like scaling to convert confidence [0, 1]
        to position size [0, max_position_size].

        Args:
            confidence: Aggregated signal confidence [0, 1].

        Returns:
            Position size [0, max_position_size].
        """
        # Sigmoid scaling for smooth position sizing
        # At confidence=0.5, position_size ~= 50% of max
        if confidence <= 0.0:
            return 0.0
        if confidence >= 1.0:
            return self.max_position_size

        # Scale using sigmoid-like function
        scaled = (2.0 * confidence - 1.0) ** 2
        return self.max_position_size * scaled

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Return recent performance metrics.

        Returns:
            Dict with latency_ms and other operational stats.
        """
        return {
            "last_synthesis_latency_ms": self.last_synthesis_time,
            "signal_buffer_size": len(self.signal_buffer),
            "active_weights_count": len(self.signal_weights),
        }

    def update_signal_weights(
        self,
        new_weights: Dict[SignalType, float],
    ) -> None:
        """
        Dynamically update signal type weights.

        Args:
            new_weights: Dict mapping SignalType to new weight.
        """
        self.signal_weights = new_weights
        # Normalize
        weight_sum = sum(self.signal_weights.values())
        if weight_sum > 0:
            self.signal_weights = {
                k: v / weight_sum for k, v in self.signal_weights.items()
            }

    def backtest_proposal(
        self,
        signals: List[TradingSignal],
        current_price: float,
        atr: float,
        actual_move: float,
    ) -> Dict[str, float]:
        """
        Quick backtest utility for proposal quality.

        Args:
            signals: Input signals.
            current_price: Entry price.
            atr: Volatility measure.
            actual_move: Actual price move (+ or -).

        Returns:
            Dict with pnl, hit_tp, hit_sl, risk_reward.
        """
        proposal = self.synthesize(signals, current_price, atr)

        # Calculate outcome
        final_price = current_price + actual_move
        pnl = (final_price - current_price) * proposal.direction

        hit_tp = False
        hit_sl = False

        if proposal.direction == 1:  # Long
            if final_price >= proposal.take_profit:
                hit_tp = True
            if final_price <= proposal.stop_loss:
                hit_sl = True
        elif proposal.direction == -1:  # Short
            if final_price <= proposal.take_profit:
                hit_tp = True
            if final_price >= proposal.stop_loss:
                hit_sl = True

        risk_distance = abs(proposal.entry_price - proposal.stop_loss)
        reward_distance = (
            abs(proposal.entry_price - proposal.take_profit)
            if proposal.take_profit
            else 0.0
        )
        risk_reward = (
            reward_distance / risk_distance if risk_distance > 0 else 0.0
        )

        return {
            "pnl": pnl,
            "hit_tp": float(hit_tp),
            "hit_sl": float(hit_sl),
            "risk_reward_ratio": risk_reward,
            "synthesis_latency_ms": proposal.synthesis_latency_ms,
        }

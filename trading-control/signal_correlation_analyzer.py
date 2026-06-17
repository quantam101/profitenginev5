import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime
import json

try:
    from .models import (
        TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal
    )
except ImportError:
    from models import (
        TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal
    )


class SignalCorrelationAnalyzer:
    """
    Analyzes correlation between 4 trading agents (Technical, Microstructure,
    Regime, Portfolio) over rolling 20-trade window. Detects correlated failures,
    adjusts agent weights based on diversity, and generates diversity reports.
    """

    def __init__(self, window_size: int = 20):
        """
        Initialize the correlation analyzer.

        Args:
            window_size: Number of trades to maintain in rolling window (default 20)
        """
        self.window_size = window_size
        self.agent_names = ["technical", "microstructure", "regime", "portfolio"]

        # Rolling buffers for agent signals (confidence + key metrics)
        self.signal_history = {
            "technical": deque(maxlen=window_size),
            "microstructure": deque(maxlen=window_size),
            "regime": deque(maxlen=window_size),
            "portfolio": deque(maxlen=window_size)
        }

        # Track trade outcomes (1=win, 0=loss, None=pending)
        self.trade_outcomes = deque(maxlen=window_size)

        # Agent weights (initialized equal)
        self.agent_weights = {name: 0.25 for name in self.agent_names}

        # Correlation matrix cache
        self.correlation_matrix = None
        self.last_update = None

        # Track correlated failures
        self.correlated_failures = []

    def record_trade(self,
                     technical: TechnicalSignal,
                     microstructure: MicrostructureSignal,
                     regime: RegimeSignal,
                     portfolio: PortfolioSignal,
                     outcome: Optional[int] = None) -> None:
        """
        Record a trade with signals from all 4 agents.

        Args:
            technical: Technical analysis signal
            microstructure: Microstructure signal
            regime: Regime signal
            portfolio: Portfolio signal
            outcome: Trade result (1=win, 0=loss, None=pending)
        """
        self.signal_history["technical"].append({
            "confidence": technical.confidence,
            "rsi_score": getattr(technical, 'rsi_oversold_recovery', 0.0),
            "macd_score": getattr(technical, 'macd_bullish_cross', 0.0),
            "trend_alignment": getattr(technical, 'trend_alignment', 0.0)
        })

        self.signal_history["microstructure"].append({
            "confidence": microstructure.confidence,
            "liquidity": getattr(microstructure, 'liquidity_score', 0.0),
            "imbalance": getattr(microstructure, 'bid_ask_imbalance', 0.0),
            "depth": getattr(microstructure, 'order_depth_score', 0.0)
        })

        self.signal_history["regime"].append({
            "confidence": regime.regime_confidence,
            "approved": float(regime.approved_to_trade),
            "volatility_regime": getattr(regime, 'volatility_regime', 0.0),
            "trend_regime": getattr(regime, 'trend_regime', 0.0)
        })

        self.signal_history["portfolio"].append({
            "confidence": 0.75,  # Default from synthesis engine
            "kelly_fraction": getattr(portfolio, 'position_size_kelly', 0.02),
            "max_loss_pct": getattr(portfolio, 'max_loss_pct', 0.01),
            "correlation_risk": getattr(portfolio, 'correlation_risk', 0.0)
        })

        self.trade_outcomes.append(outcome)
        self.last_update = datetime.now()

    def calculate_correlation_matrix(self) -> np.ndarray:
        """
        Calculate rolling 20-trade correlation matrix between 4 agents.
        Extracts primary confidence metric from each agent signal.

        Returns:
            4x4 correlation matrix (np.ndarray)
        """
        if len(self.signal_history["technical"]) < 2:
            # Insufficient data, return identity matrix
            return np.eye(4)

        # Extract confidence scores for each agent
        agent_signals = []
        for agent_name in self.agent_names:
            confidences = [s["confidence"] for s in self.signal_history[agent_name]]
            agent_signals.append(confidences)

        # Convert to numpy array (agents x trades)
        signal_matrix = np.array(agent_signals, dtype=float)

        # Calculate Pearson correlation
        if signal_matrix.shape[1] >= 2:
            self.correlation_matrix = np.corrcoef(signal_matrix)
        else:
            self.correlation_matrix = np.eye(4)

        # Handle NaN values (e.g., constant signal)
        self.correlation_matrix = np.nan_to_num(self.correlation_matrix, nan=0.0)

        return self.correlation_matrix

    def detect_correlated_failures(self,
                                   correlation_threshold: float = 0.75) -> List[Dict]:
        """
        Detect when 2+ agents fail together (high correlation of failures).
        Analyzes historical trades with outcomes to identify failure patterns.

        Args:
            correlation_threshold: Correlation coefficient threshold for flagging (0-1)

        Returns:
            List of detected correlation patterns with failure agents and strength
        """
        if not self.trade_outcomes or len(self.trade_outcomes) < 3:
            return []

        self.correlated_failures = []
        outcomes = np.array(list(self.trade_outcomes), dtype=float)

        # Only analyze trades with outcomes (not pending)
        valid_indices = [i for i, o in enumerate(outcomes) if o is not None]

        if len(valid_indices) < 3:
            return []

        # For each agent, extract signal strengths during losses
        agent_loss_signals = {}
        for agent_idx, agent_name in enumerate(self.agent_names):
            loss_signals = []
            for trade_idx in valid_indices:
                if outcomes[trade_idx] == 0:  # Loss
                    if trade_idx < len(self.signal_history[agent_name]):
                        signal = self.signal_history[agent_name][trade_idx]
                        loss_signals.append(signal["confidence"])
            agent_loss_signals[agent_name] = loss_signals

        # Find agent pairs with correlated failures
        agent_list = self.agent_names
        for i in range(len(agent_list)):
            for j in range(i + 1, len(agent_list)):
                agent_a = agent_list[i]
                agent_b = agent_list[j]

                signals_a = agent_loss_signals.get(agent_a, [])
                signals_b = agent_loss_signals.get(agent_b, [])

                if len(signals_a) >= 3 and len(signals_b) >= 3:
                    # Ensure equal length for correlation
                    min_len = min(len(signals_a), len(signals_b))
                    signals_a = signals_a[:min_len]
                    signals_b = signals_b[:min_len]

                    corr = np.corrcoef(signals_a, signals_b)[0, 1]
                    corr = np.nan_to_num(corr, nan=0.0)

                    if abs(corr) > correlation_threshold:
                        self.correlated_failures.append({
                            "agent_pair": [agent_a, agent_b],
                            "correlation": float(corr),
                            "shared_losses": len(signals_a),
                            "severity": "high" if abs(corr) > 0.85 else "medium",
                            "timestamp": datetime.now().isoformat()
                        })

        return self.correlated_failures

    def adjust_agent_weights(self,
                             diversity_importance: float = 0.6,
                             performance_importance: float = 0.4) -> Dict[str, float]:
        """
        Auto-adjust agent weights based on signal diversity and win rate.
        Penalizes highly correlated agents to enforce diversity.

        Args:
            diversity_importance: Weight for diversity component (0-1)
            performance_importance: Weight for performance component (0-1)

        Returns:
            Updated agent weights dictionary
        """
        if len(self.signal_history["technical"]) < 3:
            return self.agent_weights

        # Calculate correlation-based penalty
        corr_matrix = self.calculate_correlation_matrix()

        # Diversity score: 1 - avg absolute correlation with others
        diversity_scores = {}
        for i, agent_name in enumerate(self.agent_names):
            # Average absolute correlation with other agents
            other_corrs = []
            for j, other_name in enumerate(self.agent_names):
                if i != j:
                    other_corrs.append(abs(corr_matrix[i, j]))

            avg_corr = np.mean(other_corrs) if other_corrs else 0.0
            diversity_scores[agent_name] = 1.0 - min(avg_corr, 1.0)

        # Performance score: win rate from trades with outcomes
        performance_scores = self._calculate_performance_scores()

        # Combine scores
        combined_scores = {}
        for agent_name in self.agent_names:
            diversity_component = diversity_scores[agent_name] * diversity_importance
            performance_component = performance_scores[agent_name] * performance_importance
            combined_scores[agent_name] = diversity_component + performance_component

        # Normalize to sum to 1.0
        total_score = sum(combined_scores.values())
        if total_score > 0:
            for agent_name in self.agent_names:
                self.agent_weights[agent_name] = combined_scores[agent_name] / total_score
        else:
            # Fallback to equal weights
            self.agent_weights = {name: 0.25 for name in self.agent_names}

        return self.agent_weights

    def _calculate_performance_scores(self) -> Dict[str, float]:
        """
        Calculate win rate for each agent's signals (trades where that agent
        was high confidence and the trade won).

        Returns:
            Dictionary of agent performance scores (0-1)
        """
        performance_scores = {name: 0.5 for name in self.agent_names}

        if not self.trade_outcomes or len(self.trade_outcomes) < 2:
            return performance_scores

        outcomes = np.array(list(self.trade_outcomes), dtype=float)
        valid_trades = np.where(outcomes != None)[0]

        if len(valid_trades) < 2:
            return performance_scores

        # For each agent, calculate correlation between high confidence and wins
        for agent_idx, agent_name in enumerate(self.agent_names):
            agent_confidences = []
            agent_outcomes = []

            for trade_idx in valid_trades:
                if trade_idx < len(self.signal_history[agent_name]):
                    signal = self.signal_history[agent_name][trade_idx]
                    agent_confidences.append(signal["confidence"])
                    agent_outcomes.append(outcomes[trade_idx])

            if len(agent_confidences) >= 3:
                # Correlation between agent confidence and outcome
                corr = np.corrcoef(agent_confidences, agent_outcomes)[0, 1]
                corr = np.nan_to_num(corr, nan=0.0)
                # Normalize correlation to 0-1 range
                performance_scores[agent_name] = (corr + 1.0) / 2.0

        return performance_scores

    def generate_diversity_report(self) -> Dict:
        """
        Generate comprehensive diversity report with correlation matrix,
        weighted recommendations, and risk assessment.

        Returns:
            Dictionary containing full analysis report
        """
        corr_matrix = self.calculate_correlation_matrix()
        failures = self.detect_correlated_failures()
        weights = self.adjust_agent_weights()

        # Calculate diversity metrics
        # Overall diversity: how uncorrelated are all agents on average?
        off_diagonal = []
        for i in range(len(self.agent_names)):
            for j in range(i + 1, len(self.agent_names)):
                off_diagonal.append(abs(corr_matrix[i, j]))

        avg_correlation = np.mean(off_diagonal) if off_diagonal else 0.0
        diversity_health = 1.0 - min(avg_correlation, 1.0)

        # Win rate analysis
        outcomes = np.array(list(self.trade_outcomes), dtype=float)
        valid_outcomes = outcomes[outcomes != None]
        win_rate = float(np.mean(valid_outcomes)) if len(valid_outcomes) > 0 else None

        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "window_size": self.window_size,
            "trades_analyzed": len(self.signal_history["technical"]),
            "correlation_matrix": {
                "values": corr_matrix.tolist(),
                "agent_order": self.agent_names,
                "average_correlation": float(avg_correlation)
            },
            "agent_weights": {
                agent: float(weight) for agent, weight in weights.items()
            },
            "diversity_score": float(diversity_health),
            "correlated_failures_detected": len(failures),
            "correlated_failures": failures,
            "performance_metrics": {
                "win_rate": win_rate,
                "total_trades_with_outcomes": int(len(valid_outcomes))
            },
            "recommendations": self._generate_recommendations(
                corr_matrix, failures, weights, diversity_health
            )
        }

        return report

    def _generate_recommendations(self,
                                  corr_matrix: np.ndarray,
                                  failures: List[Dict],
                                  weights: Dict[str, float],
                                  diversity_health: float) -> List[str]:
        """
        Generate actionable recommendations based on analysis.

        Args:
            corr_matrix: Correlation matrix
            failures: List of detected failures
            weights: Agent weights
            diversity_health: Overall diversity score

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if diversity_health < 0.3:
            recommendations.append(
                "ALERT: Very low signal diversity. Agents are highly correlated. "
                "Risk of systematic failures. Consider adding independent signal source."
            )
        elif diversity_health < 0.5:
            recommendations.append(
                "WARNING: Low signal diversity. Correlation between agents is high. "
                "Monitor for correlated drawdowns."
            )
        else:
            recommendations.append(
                "GOOD: Signal diversity is healthy. Agent signals show independence."
            )

        if failures:
            recommendations.append(
                f"CRITICAL: Detected {len(failures)} correlated failure patterns. "
                f"Agents {', '.join(f[0] for f in [f['agent_pair'] for f in failures])} "
                f"tend to fail together. Reduce position size during simultaneous signals."
            )

        # Weight recommendations
        max_weight = max(weights.values())
        min_weight = min(weights.values())
        weight_imbalance = max_weight - min_weight

        if weight_imbalance > 0.15:
            most_trusted = max(weights, key=weights.get)
            least_trusted = min(weights, key=weights.get)
            recommendations.append(
                f"INFO: Agent weighting is imbalanced. {most_trusted} is trusted most "
                f"({weights[most_trusted]:.2%}), {least_trusted} least trusted "
                f"({weights[least_trusted]:.2%}). Consider risk management adjustments."
            )

        return recommendations

    def get_aggregated_signal(self,
                             technical: TechnicalSignal,
                             microstructure: MicrostructureSignal,
                             regime: RegimeSignal,
                             portfolio: PortfolioSignal) -> float:
        """
        Generate weighted aggregated confidence signal using current agent weights.

        Args:
            technical: Technical signal
            microstructure: Microstructure signal
            regime: Regime signal
            portfolio: Portfolio signal

        Returns:
            Weighted confidence score (0-1)
        """
        signals = [
            technical.confidence,
            microstructure.confidence,
            regime.regime_confidence,
            0.75  # Portfolio default confidence
        ]

        weighted_score = sum(
            signals[i] * self.agent_weights[self.agent_names[i]]
            for i in range(len(self.agent_names))
        )

        return float(weighted_score)

    def export_analysis(self, filepath: str) -> None:
        """
        Export full analysis to JSON file for external review.

        Args:
            filepath: Path to save JSON report
        """
        report = self.generate_diversity_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    def reset(self) -> None:
        """Reset analyzer state (clear all buffers and weights)."""
        for agent_name in self.agent_names:
            self.signal_history[agent_name].clear()
        self.trade_outcomes.clear()
        self.agent_weights = {name: 0.25 for name in self.agent_names}
        self.correlation_matrix = None
        self.correlated_failures = []
        self.last_update = None

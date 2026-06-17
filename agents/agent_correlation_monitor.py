"""
Agent Correlation Monitor — Detect and mitigate correlated failures.

Maintains a 4x4 correlation matrix tracking relationships between:
- Technical Signal Agent
- Regime Signal Agent
- Kelly Signal Agent
- Risk Gates Agent

Detects when correlated failures exceed 0.8 threshold and adjusts weights
to prevent cascading failures across the signal mesh.

License: MIT — ProfitEngine v5
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CorrelationMetric:
    """Correlation metric between two agents."""

    agent_a: str
    agent_b: str
    correlation_coefficient: float
    failure_count_a: int
    failure_count_b: int
    shared_failure_count: int
    timestamp: str


@dataclass
class WeightAdjustment:
    """Weight adjustment event for an agent."""

    agent_name: str
    original_weight: float
    adjusted_weight: float
    reason: str
    timestamp: str


class AgentCorrelationMonitor:
    """
    Monitor and manage correlations between agent failures.

    Maintains:
    - 4x4 correlation matrix (Technical, Regime, Kelly, RiskGates)
    - Failure history for each agent
    - Dynamic weight adjustments based on correlation
    - Alerting for high-correlation events

    Methods:
    - calc_correlation(): Compute Pearson correlation coefficient
    - detect_failure(): Track and analyze failure patterns
    - adjust_weights(): Dynamically update agent weights
    - get_correlation_matrix(): Return current 4x4 matrix
    - get_health_score(): Aggregate correlation health metric
    """

    AGENT_NAMES = [
        "technical_signal",
        "regime_signal",
        "kelly_signal",
        "risk_gates",
    ]

    CORRELATION_THRESHOLD = 0.8
    FAILURE_WINDOW_SIZE = 100  # Track last N events
    WEIGHT_ADJUSTMENT_FACTOR = 0.95  # Reduce weight by 5% per event

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize correlation monitor.

        Args:
            cache_dir: Optional path to persist correlation data
        """
        self.cache_dir = cache_dir or Path("./correlation_cache")
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize failure history: agent -> list of pass/fail (1/0)
        self.failure_history: Dict[str, List[int]] = {
            agent: [] for agent in self.AGENT_NAMES
        }

        # Initialize correlation matrix (4x4)
        self.correlation_matrix = self._init_correlation_matrix()

        # Track weight adjustments
        self.weight_history: List[WeightAdjustment] = []

        # Current agent weights (normalized, sum = 1.0)
        self.agent_weights = {agent: 1.0 / len(self.AGENT_NAMES) for agent in self.AGENT_NAMES}

        # Load persisted data if available
        self._load_from_cache()

    def _init_correlation_matrix(self) -> List[List[float]]:
        """Initialize 4x4 correlation matrix with neutral values."""
        size = len(self.AGENT_NAMES)
        matrix = [[0.0 for _ in range(size)] for _ in range(size)]
        # Diagonal = 1.0 (perfect self-correlation)
        for i in range(size):
            matrix[i][i] = 1.0
        return matrix

    def calc_correlation(self, history_a: List[int], history_b: List[int]) -> float:
        """
        Calculate Pearson correlation coefficient between two failure histories.

        Args:
            history_a: Binary list (0=pass, 1=fail) for agent A
            history_b: Binary list (0=pass, 1=fail) for agent B

        Returns:
            Correlation coefficient [-1.0, 1.0]
            Returns 1.0 if both have zero variance and are equal, 0.0 otherwise
        """
        if len(history_a) < 2 or len(history_b) < 2:
            return 0.0

        if len(history_a) != len(history_b):
            # Truncate to common length
            min_len = min(len(history_a), len(history_b))
            history_a = history_a[-min_len:]
            history_b = history_b[-min_len:]

        # Calculate means
        mean_a = sum(history_a) / len(history_a)
        mean_b = sum(history_b) / len(history_b)

        # Calculate standard deviations
        variance_a = sum((x - mean_a) ** 2 for x in history_a) / len(history_a)
        variance_b = sum((x - mean_b) ** 2 for x in history_b) / len(history_b)

        std_a = math.sqrt(variance_a)
        std_b = math.sqrt(variance_b)

        # Handle edge case: zero standard deviation
        # If both have zero variance, they're perfectly aligned if equal, unrelated if different
        if std_a == 0 and std_b == 0:
            return 1.0 if history_a == history_b else 0.0
        if std_a == 0 or std_b == 0:
            return 0.0

        # Calculate covariance
        covariance = sum(
            (history_a[i] - mean_a) * (history_b[i] - mean_b)
            for i in range(len(history_a))
        ) / len(history_a)

        # Correlation = covariance / (std_a * std_b)
        correlation = covariance / (std_a * std_b)

        # Clamp to [-1, 1] to handle floating point errors
        return max(-1.0, min(1.0, correlation))

    def detect_failure(
        self, agent_name: str, is_failure: bool, metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record an agent failure/success event and detect correlations.

        Args:
            agent_name: Name of agent (must be in AGENT_NAMES)
            is_failure: True if failure, False if success
            metadata: Optional context about the event

        Returns:
            Detection result with alerts and recommendations
        """
        if agent_name not in self.AGENT_NAMES:
            return {"error": f"Unknown agent: {agent_name}"}

        # Record event (1 for failure, 0 for success)
        event_value = 1 if is_failure else 0
        self.failure_history[agent_name].append(event_value)

        # Keep history size bounded
        if len(self.failure_history[agent_name]) > self.FAILURE_WINDOW_SIZE:
            self.failure_history[agent_name].pop(0)

        # Recalculate correlation matrix
        self._update_correlation_matrix()

        # Detect high correlations
        high_correlations = self._find_high_correlations()

        result = {
            "agent": agent_name,
            "event": "failure" if is_failure else "success",
            "timestamp": datetime.utcnow().isoformat(),
            "high_correlations": high_correlations,
            "metadata": metadata,
        }

        # If high correlations detected, trigger weight adjustments
        if high_correlations:
            result["weight_adjustments"] = self._execute_weight_adjustments(
                agent_name, high_correlations
            )

        return result

    def _update_correlation_matrix(self) -> None:
        """Recalculate all pairwise correlations in the 4x4 matrix."""
        for i, agent_a in enumerate(self.AGENT_NAMES):
            for j, agent_b in enumerate(self.AGENT_NAMES):
                if i == j:
                    # Diagonal remains 1.0 (perfect self-correlation)
                    self.correlation_matrix[i][j] = 1.0
                else:
                    # Calculate Pearson correlation
                    corr = self.calc_correlation(
                        self.failure_history[agent_a], self.failure_history[agent_b]
                    )
                    self.correlation_matrix[i][j] = corr

    def _find_high_correlations(self) -> List[Tuple[str, str, float]]:
        """
        Find all agent pairs with correlation > CORRELATION_THRESHOLD.

        Returns:
            List of (agent_a, agent_b, correlation) tuples
        """
        high_correlations = []
        for i, agent_a in enumerate(self.AGENT_NAMES):
            for j, agent_b in enumerate(self.AGENT_NAMES):
                if i < j:  # Avoid duplicates
                    corr = self.correlation_matrix[i][j]
                    if corr > self.CORRELATION_THRESHOLD:
                        high_correlations.append((agent_a, agent_b, corr))
        return high_correlations

    def adjust_weights(self, agent_name: str, reduction_factor: Optional[float] = None) -> Dict:
        """
        Dynamically reduce weight of a correlated-failure agent.

        Args:
            agent_name: Agent to adjust
            reduction_factor: Factor to multiply current weight (default: WEIGHT_ADJUSTMENT_FACTOR)

        Returns:
            Adjustment result with new weight and normalization info
        """
        if agent_name not in self.AGENT_NAMES:
            return {"error": f"Unknown agent: {agent_name}"}

        reduction_factor = reduction_factor or self.WEIGHT_ADJUSTMENT_FACTOR
        original_weight = self.agent_weights[agent_name]
        new_weight = original_weight * reduction_factor

        # Update weight
        self.agent_weights[agent_name] = new_weight

        # Re-normalize weights to sum = 1.0
        total = sum(self.agent_weights.values())
        self.agent_weights = {agent: w / total for agent, w in self.agent_weights.items()}

        # Record adjustment
        adjustment = WeightAdjustment(
            agent_name=agent_name,
            original_weight=original_weight,
            adjusted_weight=self.agent_weights[agent_name],
            reason=f"Correlated failure detected (reduction factor: {reduction_factor})",
            timestamp=datetime.utcnow().isoformat(),
        )
        self.weight_history.append(adjustment)

        result = {
            "agent": agent_name,
            "original_weight": original_weight,
            "adjusted_weight": self.agent_weights[agent_name],
            "reduction_factor": reduction_factor,
            "new_weights": self.agent_weights.copy(),
            "timestamp": adjustment.timestamp,
        }

        return result

    def _execute_weight_adjustments(
        self, triggered_agent: str, high_correlations: List[Tuple[str, str, float]]
    ) -> List[Dict]:
        """
        Execute weight adjustments for all highly correlated agents.

        Args:
            triggered_agent: Agent that triggered the detection
            high_correlations: List of high-correlation pairs

        Returns:
            List of adjustment results
        """
        adjustments = []
        affected_agents = set()

        for agent_a, agent_b, _ in high_correlations:
            affected_agents.add(agent_a)
            affected_agents.add(agent_b)

        for agent in affected_agents:
            if agent != triggered_agent:
                adj = self.adjust_weights(agent)
                adjustments.append(adj)

        return adjustments

    def get_correlation_matrix(self) -> Dict:
        """
        Return the 4x4 correlation matrix with agent labels.

        Returns:
            Dictionary with matrix data and metadata
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": self.AGENT_NAMES,
            "matrix": self.correlation_matrix,
            "threshold": self.CORRELATION_THRESHOLD,
            "high_correlations": self._find_high_correlations(),
        }

    def get_health_score(self) -> Dict:
        """
        Calculate overall health score based on correlation metrics.

        Health Score = 1.0 - (sum of correlations above threshold / max possible correlations)

        Returns:
            Health score (0.0-1.0) and breakdown by agent
        """
        high_corrs = self._find_high_correlations()
        max_correlations = (len(self.AGENT_NAMES) * (len(self.AGENT_NAMES) - 1)) // 2

        health_score = 1.0
        if high_corrs:
            excess_correlation = sum(corr - self.CORRELATION_THRESHOLD for _, _, corr in high_corrs)
            health_score = max(0.0, 1.0 - (excess_correlation / max_correlations))

        agent_health = {}
        for agent in self.AGENT_NAMES:
            agent_corrs = [
                corr
                for a, b, corr in high_corrs
                if agent in (a, b)
            ]
            agent_failure_rate = (
                sum(self.failure_history[agent]) / len(self.failure_history[agent])
                if self.failure_history[agent]
                else 0.0
            )
            agent_health[agent] = {
                "weight": self.agent_weights[agent],
                "failure_rate": agent_failure_rate,
                "high_correlations_count": len(agent_corrs),
            }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": health_score,
            "agents": agent_health,
            "high_correlations_count": len(high_corrs),
        }

    def _load_from_cache(self) -> None:
        """Load persisted correlation data from cache directory."""
        matrix_file = self.cache_dir / "correlation_matrix.json"
        weights_file = self.cache_dir / "agent_weights.json"

        if matrix_file.exists():
            try:
                with open(matrix_file, "r") as f:
                    data = json.load(f)
                    self.correlation_matrix = data.get("matrix", self.correlation_matrix)
            except Exception:
                pass  # Use defaults on load error

        if weights_file.exists():
            try:
                with open(weights_file, "r") as f:
                    self.agent_weights = json.load(f)
            except Exception:
                pass  # Use defaults on load error

    def save_to_cache(self) -> None:
        """Persist correlation matrix and weights to cache directory."""
        matrix_file = self.cache_dir / "correlation_matrix.json"
        weights_file = self.cache_dir / "agent_weights.json"
        history_file = self.cache_dir / "weight_history.json"

        try:
            with open(matrix_file, "w") as f:
                json.dump(
                    {
                        "matrix": self.correlation_matrix,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    f,
                    indent=2,
                )

            with open(weights_file, "w") as f:
                json.dump(self.agent_weights, f, indent=2)

            with open(history_file, "w") as f:
                json.dump(
                    [asdict(adj) for adj in self.weight_history[-50:]],  # Keep last 50
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"Warning: Failed to persist correlation data: {e}")

    def reset(self) -> None:
        """Reset monitor to initial state."""
        self.failure_history = {agent: [] for agent in self.AGENT_NAMES}
        self.correlation_matrix = self._init_correlation_matrix()
        self.weight_history = []
        self.agent_weights = {agent: 1.0 / len(self.AGENT_NAMES) for agent in self.AGENT_NAMES}


if __name__ == "__main__":
    # Example usage
    monitor = AgentCorrelationMonitor()

    # Simulate failure events
    print("=== Agent Correlation Monitor Example ===\n")

    # Technical signal and regime signal both fail together (correlated)
    for i in range(25):
        # Technical and Regime are highly correlated
        monitor.detect_failure("technical_signal", True)
        monitor.detect_failure("regime_signal", True)
        # Kelly and RiskGates succeed
        monitor.detect_failure("kelly_signal", False)
        monitor.detect_failure("risk_gates", False)

    # Display correlation matrix
    print(f"Failure histories (length check):")
    for agent in monitor.AGENT_NAMES:
        hist = monitor.failure_history[agent]
        print(f"  {agent}: {len(hist)} events, values={hist[:10]}")

    print("\nCorrelation Matrix:")
    matrix_data = monitor.get_correlation_matrix()
    for i, agent_a in enumerate(matrix_data["agents"]):
        row = [f"{v:0.2f}" for v in matrix_data["matrix"][i]]
        print(f"  {agent_a}: {row}")

    print("\nHigh Correlations:")
    for a, b, corr in matrix_data["high_correlations"]:
        print(f"  {a} <-> {b}: {corr:.2f}")

    print("\nHealth Score:")
    health = monitor.get_health_score()
    print(f"  Overall: {health['overall_health']:.2f}")
    for agent, metrics in health["agents"].items():
        print(f"  {agent}: weight={metrics['weight']:.3f}, failures={metrics['failure_rate']:.2%}")

    # Persist to cache
    monitor.save_to_cache()
    print("\nData persisted to cache directory")

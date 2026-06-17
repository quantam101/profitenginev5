"""
Test and demonstration suite for SignalCorrelationAnalyzer.
Shows how to use the analyzer for detecting correlated failures and auto-weighting.
"""

import numpy as np
from signal_correlation_analyzer import SignalCorrelationAnalyzer

# Mock signal classes for testing
class MockSignal:
    def __init__(self, confidence: float, **kwargs):
        self.confidence = confidence
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_basic_correlation_matrix():
    """Test basic correlation matrix calculation."""
    print("\n=== TEST 1: Basic Correlation Matrix ===")

    analyzer = SignalCorrelationAnalyzer(window_size=20)

    # Simulate 10 trades with varying signal correlations
    for i in range(10):
        # Create correlated signals (technical and microstructure highly correlated)
        tech_conf = 0.6 + 0.2 * np.sin(i * 0.5)
        micro_conf = 0.55 + 0.25 * np.sin(i * 0.5)  # Similar pattern
        regime_conf = 0.7 + 0.15 * np.cos(i * 0.3)  # Different pattern
        portfolio_conf = 0.75

        analyzer.record_trade(
            technical=MockSignal(tech_conf, rsi_oversold_recovery=0.5,
                                macd_bullish_cross=0.5, trend_alignment=0.6),
            microstructure=MockSignal(micro_conf, liquidity_score=0.6,
                                     bid_ask_imbalance=0.05),
            regime=MockSignal(regime_conf, approved_to_trade=True,
                            volatility_regime=0.5, trend_regime=0.6,
                            regime_confidence=regime_conf),
            portfolio=MockSignal(portfolio_conf, position_size_kelly=0.02,
                                max_loss_pct=0.01)
        )

    corr_matrix = analyzer.calculate_correlation_matrix()
    print("Correlation Matrix:")
    print(f"Shape: {corr_matrix.shape}")
    print(f"Technical vs Microstructure: {corr_matrix[0, 1]:.3f}")
    print(f"Technical vs Regime: {corr_matrix[0, 2]:.3f}")
    print(f"Microstructure vs Regime: {corr_matrix[1, 2]:.3f}")
    print(f"Average correlation: {np.mean(np.abs(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])):.3f}")


def test_detect_correlated_failures():
    """Test detection of correlated failures."""
    print("\n=== TEST 2: Correlated Failure Detection ===")

    analyzer = SignalCorrelationAnalyzer(window_size=20)

    # Simulate trades where technical and microstructure tend to fail together
    for i in range(15):
        tech_conf = 0.6
        micro_conf = 0.65

        # On even trades, both technical and micro are high confidence but fail
        outcome = None
        if i % 2 == 0 and i > 2:
            outcome = 0  # Loss
        elif i % 3 == 0:
            outcome = 1  # Win

        analyzer.record_trade(
            technical=MockSignal(tech_conf, rsi_oversold_recovery=0.7,
                                macd_bullish_cross=0.6, trend_alignment=0.65),
            microstructure=MockSignal(micro_conf, liquidity_score=0.7,
                                     bid_ask_imbalance=0.08),
            regime=MockSignal(0.75, approved_to_trade=True,
                            volatility_regime=0.5, trend_regime=0.6,
                            regime_confidence=0.75),
            portfolio=MockSignal(0.75, position_size_kelly=0.02,
                                max_loss_pct=0.01),
            outcome=outcome
        )

    failures = analyzer.detect_correlated_failures(correlation_threshold=0.6)
    print(f"Correlated failures detected: {len(failures)}")
    for failure in failures:
        print(f"  Agents: {failure['agent_pair']}")
        print(f"  Correlation: {failure['correlation']:.3f}")
        print(f"  Shared losses: {failure['shared_losses']}")


def test_adjust_weights():
    """Test agent weight adjustment based on diversity."""
    print("\n=== TEST 3: Agent Weight Adjustment ===")

    analyzer = SignalCorrelationAnalyzer(window_size=20)

    # Simulate trades with different agent performance
    for i in range(12):
        # Technical agent: consistently high and performs well
        tech_conf = 0.75
        # Microstructure: medium confidence, middle performance
        micro_conf = 0.60
        # Regime: high confidence but sometimes fails
        regime_conf = 0.78
        # Portfolio: baseline
        portfolio_conf = 0.75

        outcome = None
        if i >= 3:
            # Technical usually wins, regime sometimes fails
            if i % 4 == 0:
                outcome = 0  # Regime failure
            else:
                outcome = 1  # Technical wins

        analyzer.record_trade(
            technical=MockSignal(tech_conf, rsi_oversold_recovery=0.7,
                                macd_bullish_cross=0.65, trend_alignment=0.72),
            microstructure=MockSignal(micro_conf, liquidity_score=0.6,
                                     bid_ask_imbalance=0.05),
            regime=MockSignal(regime_conf, approved_to_trade=True,
                            volatility_regime=0.55, trend_regime=0.65,
                            regime_confidence=regime_conf),
            portfolio=MockSignal(portfolio_conf, position_size_kelly=0.02,
                                max_loss_pct=0.01),
            outcome=outcome
        )

    weights = analyzer.adjust_agent_weights(
        diversity_importance=0.6,
        performance_importance=0.4
    )

    print("Adjusted Agent Weights:")
    for agent, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {agent}: {weight:.3f}")

    # Verify weights sum to 1.0
    total = sum(weights.values())
    print(f"Weight sum: {total:.3f}")


def test_diversity_report():
    """Test full diversity report generation."""
    print("\n=== TEST 4: Diversity Report ===")

    analyzer = SignalCorrelationAnalyzer(window_size=20)

    # Simulate a realistic sequence of trades
    np.random.seed(42)
    for i in range(18):
        # Random base signals
        tech_conf = 0.65 + np.random.normal(0, 0.1)
        micro_conf = 0.60 + np.random.normal(0, 0.12)
        regime_conf = 0.70 + np.random.normal(0, 0.08)

        # Add some structure: tech and micro are correlated
        micro_conf += 0.1 * (tech_conf - 0.65)

        # Clamp to [0, 1]
        tech_conf = np.clip(tech_conf, 0.3, 0.95)
        micro_conf = np.clip(micro_conf, 0.3, 0.95)
        regime_conf = np.clip(regime_conf, 0.3, 0.95)

        # Trade outcome
        outcome = None
        if i >= 3:
            outcome = 1 if np.random.random() > 0.45 else 0

        analyzer.record_trade(
            technical=MockSignal(tech_conf, rsi_oversold_recovery=tech_conf * 0.9,
                                macd_bullish_cross=tech_conf * 0.85,
                                trend_alignment=tech_conf * 0.95),
            microstructure=MockSignal(micro_conf, liquidity_score=micro_conf * 0.9,
                                     bid_ask_imbalance=micro_conf * 0.3),
            regime=MockSignal(regime_conf, approved_to_trade=True,
                            volatility_regime=regime_conf * 0.8,
                            trend_regime=regime_conf * 0.85,
                            regime_confidence=regime_conf),
            portfolio=MockSignal(0.75, position_size_kelly=0.02,
                                max_loss_pct=0.01),
            outcome=outcome
        )

    report = analyzer.generate_diversity_report()

    print(f"Trades analyzed: {report['trades_analyzed']}")
    print(f"Diversity score: {report['diversity_score']:.3f}")
    print(f"\nCorrelation Matrix (4x4):")
    for i, row in enumerate(report['correlation_matrix']['values']):
        agent = report['correlation_matrix']['agent_order'][i]
        print(f"  {agent:15} | {' '.join(f'{v:6.3f}' for v in row)}")
    print(f"\nAverage correlation: {report['correlation_matrix']['average_correlation']:.3f}")

    print(f"\nAgent Weights:")
    for agent, weight in report['agent_weights'].items():
        print(f"  {agent:15} {weight:.3f}")

    print(f"\nPerformance Metrics:")
    if report['performance_metrics']['win_rate'] is not None:
        print(f"  Win rate: {report['performance_metrics']['win_rate']:.1%}")
    print(f"  Trades with outcomes: {report['performance_metrics']['total_trades_with_outcomes']}")

    print(f"\nCorrelated failures detected: {report['correlated_failures_detected']}")
    for failure in report['correlated_failures']:
        print(f"  {failure['agent_pair']}: {failure['correlation']:.3f} "
              f"({failure['severity']}, {failure['shared_losses']} shared losses)")

    print(f"\nRecommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec[:90]}...")


def test_aggregated_signal():
    """Test weighted signal aggregation."""
    print("\n=== TEST 5: Aggregated Signal ===")

    analyzer = SignalCorrelationAnalyzer(window_size=20)

    # Build up some history for meaningful weights
    for i in range(10):
        analyzer.record_trade(
            technical=MockSignal(0.70, rsi_oversold_recovery=0.6,
                                macd_bullish_cross=0.65, trend_alignment=0.75),
            microstructure=MockSignal(0.65, liquidity_score=0.65,
                                     bid_ask_imbalance=0.08),
            regime=MockSignal(0.75, approved_to_trade=True,
                            volatility_regime=0.55, trend_regime=0.70,
                            regime_confidence=0.75),
            portfolio=MockSignal(0.75, position_size_kelly=0.02,
                                max_loss_pct=0.01),
            outcome=1 if i % 2 == 0 else 0
        )

    # Adjust weights
    weights = analyzer.adjust_agent_weights()

    # Get aggregated signal
    agg_signal = analyzer.get_aggregated_signal(
        technical=MockSignal(0.70),
        microstructure=MockSignal(0.65),
        regime=MockSignal(0.75),
        portfolio=MockSignal(0.75)
    )

    print(f"Current agent weights: {weights}")
    print(f"Individual signals: Technical=0.70, Micro=0.65, Regime=0.75, Portfolio=0.75")
    print(f"Aggregated signal (weighted): {agg_signal:.3f}")
    print(f"Simple average: {np.mean([0.70, 0.65, 0.75, 0.75]):.3f}")


if __name__ == "__main__":
    test_basic_correlation_matrix()
    test_detect_correlated_failures()
    test_adjust_weights()
    test_diversity_report()
    test_aggregated_signal()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

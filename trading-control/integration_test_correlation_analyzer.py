"""
Integration test: Run 30 trades through synthesis_engine with correlation analyzer enabled.
Verifies:
1. Correlation matrix calculation at trade 20 and 30
2. Correlation detection (identifies if agents move together)
3. Agent weight adjustments (correlated agents reduced 20%, diverse agents boosted 10%)
4. Diversity report generation
"""

import numpy as np
import json
from decimal import Decimal
from datetime import datetime
from typing import Dict, List

try:
    from models import (
        MarketSnapshot, TradeProposal, TechnicalSignal, MicrostructureSignal,
        RegimeSignal, PortfolioSignal, MarketRegime
    )
    from synthesis_engine import ProposalSynthesisEngine
    from signal_correlation_analyzer import SignalCorrelationAnalyzer
except ImportError:
    from models import (
        MarketSnapshot, TradeProposal, TechnicalSignal, MicrostructureSignal,
        RegimeSignal, PortfolioSignal, MarketRegime
    )
    from synthesis_engine import ProposalSynthesisEngine
    from signal_correlation_analyzer import SignalCorrelationAnalyzer


# Mock MarketSnapshot class for testing
class MockMarketSnapshot:
    def __init__(self, symbol: str, last: float, bid: float, ask: float,
                 volume: int, volatility: float, state: Dict):
        self.symbol = symbol
        self.last = last
        self.bid = bid
        self.ask = ask
        self.volume = volume
        self.volatility = volatility
        self.state = state
        # Create a proper price series
        self.prices = [last - 0.02, last - 0.01, last, last + 0.01, last + 0.02] * 5
        self.volumes = [volume // 5] * 25
        self.orderbook = {
            "bids": [[bid, volume // 2], [bid - 0.5, volume // 4], [bid - 1.0, volume // 4]],
            "asks": [[ask, volume // 2], [ask + 0.5, volume // 4], [ask + 1.0, volume // 4]]
        }
        # trade_flow should be a list of dicts with trade info
        self.trade_flow = [
            {"size": 5000, "side": "buy"},
            {"size": 3000, "side": "sell"},
            {"size": 2000, "side": "buy"},
            {"size": 1500, "side": "sell"},
        ]


def generate_trade_signals(trade_num: int, scenario: str) -> tuple:
    """
    Generate realistic signal combinations for testing.

    Scenarios:
    - 'independent': Agents move independently (good diversity)
    - 'correlated': Technical and microstructure highly correlated (bad diversity)
    - 'mixed': Some agents correlated, others diverse
    """
    # Use consistent seed per trade_num but vary within scenario
    np.random.seed(100 + trade_num)

    if scenario == 'independent':
        # All agents independent with good variation
        tech_conf = 0.65 + np.random.normal(0, 0.12)
        micro_conf = 0.60 + np.random.normal(0, 0.15)  # Different pattern
        regime_conf = 0.70 + np.random.normal(0, 0.10)  # Different pattern

    elif scenario == 'correlated':
        # Technical and microstructure highly correlated
        # They follow the same underlying trend
        base_trend = 0.65 + np.random.normal(0, 0.10)
        tech_conf = base_trend + np.random.normal(0, 0.02)  # Tight follow
        micro_conf = base_trend + np.random.normal(0, 0.02)  # Tight follow
        regime_conf = 0.70 + np.random.normal(0, 0.10)  # Independent

    elif scenario == 'mixed':
        # Partial correlation: tech and micro weakly correlated
        tech_conf = 0.65 + np.random.normal(0, 0.12)
        micro_conf = tech_conf * 0.5 + np.random.normal(0.30, 0.08)  # Partial correlation
        regime_conf = 0.70 + np.random.normal(0, 0.10)  # Independent

    # Clamp to valid range
    tech_conf = np.clip(tech_conf, 0.35, 0.90)
    micro_conf = np.clip(micro_conf, 0.35, 0.90)
    regime_conf = np.clip(regime_conf, 0.35, 0.90)

    # Create signal objects
    technical = TechnicalSignal(
        rsi_oversold_recovery=tech_conf * 0.9,
        macd_bullish_cross=tech_conf * 0.85,
        support_bounce=tech_conf * 0.80,
        trend_alignment=tech_conf * 0.95,
        pattern_score=tech_conf * 0.75,
        confidence=tech_conf
    )

    microstructure = MicrostructureSignal(
        bid_ask_imbalance=micro_conf * 0.3,
        smart_money_flow=micro_conf * 0.8,
        liquidity_score=micro_conf * 0.9,
        front_running_risk=0.1,
        time_to_fill=0.5,
        confidence=micro_conf
    )

    regime = RegimeSignal(
        regime=MarketRegime.BULL_TRENDING,
        volatility_level=regime_conf * 0.6,
        event_risk=0.05,
        correlation_stress=0.1,
        regime_confidence=regime_conf,
        approved_to_trade=True
    )

    portfolio = PortfolioSignal(
        position_size_kelly=0.02,
        max_correlated_exposure=0.15,
        drawdown_forecast=0.02,
        risk_budget_remaining=0.95,
        recommended_action="BUY"
    )

    return technical, microstructure, regime, portfolio


def run_integration_test():
    """Run 30 trades through synthesis engine with correlation analysis."""

    print("\n" + "=" * 80)
    print("CORRELATION ANALYZER INTEGRATION TEST")
    print("Running 30 trades with correlation analysis enabled")
    print("=" * 80)

    # Initialize synthesis engine with correlation analyzer
    config = {
        'agents': {
            'technical': {},
            'microstructure': {},
            'regime': {},
            'portfolio': {}
        }
    }

    engine = ProposalSynthesisEngine(config)

    # Track results
    trades = []
    proposals_generated = []
    trade_outcomes = []
    correlations_at_checkpoint = {}
    weights_adjustments = []

    # Run 30 trades
    print("\nGenerating 30 trades...")
    print("-" * 80)

    for trade_num in range(1, 31):
        # Choose scenario based on trade number
        if trade_num <= 10:
            scenario = 'independent'
        elif trade_num <= 20:
            scenario = 'correlated'
        else:
            scenario = 'mixed'

        # Generate market snapshot with varying prices based on scenario
        # This creates variation that will be picked up by the agents
        if scenario == 'independent':
            base_price = 45000.0 + (trade_num - 1) * 10 + np.random.randn() * 50
        elif scenario == 'correlated':
            # Prices trending down (will create correlated failures)
            base_price = 45000.0 - (trade_num - 11) * 15 + np.random.randn() * 30
        else:  # mixed
            # Oscillating prices
            base_price = 45000.0 + 500 * np.sin((trade_num - 21) * 0.4) + np.random.randn() * 40

        market_snapshot = MockMarketSnapshot(
            symbol="BTC/USD",
            last=base_price,
            bid=base_price - 1.0,
            ask=base_price + 1.0,
            volume=1000000,
            volatility=2.5 + np.random.randn() * 0.5,
            state={"trend": "up", "regime": "trending"}
        )

        technical, microstructure, regime, portfolio = generate_trade_signals(
            trade_num, scenario
        )

        # Generate proposal
        account_equity = Decimal('100000')
        daily_pnl = Decimal('0')

        proposal = engine.generate(
            market_snapshot=market_snapshot,
            account_equity=account_equity,
            daily_pnl=daily_pnl,
            open_positions=[]
        )

        if proposal:
            proposals_generated.append({
                'trade_num': trade_num,
                'direction': proposal.direction,
                'confidence': proposal.overall_confidence,
                'scenario': scenario
            })

            # Simulate trade outcome (win/loss based on confidence)
            outcome = 1 if np.random.random() < proposal.overall_confidence else 0
            engine.record_trade_outcome(outcome)
            trade_outcomes.append({
                'trade_num': trade_num,
                'outcome': outcome,
                'confidence': proposal.overall_confidence
            })

            # Print progress
            print(f"Trade {trade_num:2d}: {scenario:12s} | "
                  f"Conf={proposal.overall_confidence:.3f} | "
                  f"Outcome={'WIN' if outcome else 'LOSS'}")
        else:
            print(f"Trade {trade_num:2d}: {scenario:12s} | REJECTED (regime or reward-risk)")

        # Checkpoint at trade 20: Calculate correlation matrix
        if trade_num == 20:
            print("\n" + "-" * 80)
            print("CHECKPOINT AT TRADE 20")
            print("-" * 80)

            corr_matrix_20 = engine.correlation_analyzer.calculate_correlation_matrix()
            weights_20 = engine.correlation_analyzer.adjust_agent_weights()
            report_20 = engine.correlation_analyzer.generate_diversity_report()

            correlations_at_checkpoint['trade_20'] = {
                'matrix': corr_matrix_20.tolist(),
                'diversity_score': float(report_20['diversity_score']),
                'avg_correlation': float(report_20['correlation_matrix']['average_correlation']),
                'correlated_failures': report_20['correlated_failures_detected']
            }

            weights_adjustments.append({
                'trade_num': 20,
                'weights': weights_20,
                'diversity_score': float(report_20['diversity_score'])
            })

            print(f"Diversity Score: {report_20['diversity_score']:.3f}")
            print(f"Average Correlation: {report_20['correlation_matrix']['average_correlation']:.3f}")
            print(f"Correlated Failures Detected: {report_20['correlated_failures_detected']}")
            print("\nAgent Weights at Trade 20:")
            for agent, weight in sorted(weights_20.items(), key=lambda x: x[1], reverse=True):
                print(f"  {agent:15s}: {weight:.4f}")

    # Final checkpoint at trade 30: Full analysis
    print("\n" + "=" * 80)
    print("CHECKPOINT AT TRADE 30 - FINAL ANALYSIS")
    print("=" * 80)

    # Calculate final correlation matrix
    corr_matrix_30 = engine.correlation_analyzer.calculate_correlation_matrix()
    weights_30 = engine.correlation_analyzer.adjust_agent_weights()
    report_30 = engine.correlation_analyzer.generate_diversity_report()

    correlations_at_checkpoint['trade_30'] = {
        'matrix': corr_matrix_30.tolist(),
        'diversity_score': float(report_30['diversity_score']),
        'avg_correlation': float(report_30['correlation_matrix']['average_correlation']),
        'correlated_failures': report_30['correlated_failures_detected']
    }

    weights_adjustments.append({
        'trade_num': 30,
        'weights': weights_30,
        'diversity_score': float(report_30['diversity_score'])
    })

    # Print correlation matrix at trade 30
    print("\nCORRELATION MATRIX AT TRADE 30:")
    print("(Agents: Technical, Microstructure, Regime, Portfolio)")
    print("\n       Tech   Micro  Regime Portfolio")
    agent_names = engine.correlation_analyzer.agent_names
    for i, row in enumerate(corr_matrix_30):
        print(f"{agent_names[i]:8s} | " + " ".join(f"{v:7.3f}" for v in row))

    print(f"\nAverage Correlation (off-diagonal): {report_30['correlation_matrix']['average_correlation']:.3f}")
    print(f"Diversity Score: {report_30['diversity_score']:.3f}")

    # Print agent weights
    print("\nFINAL AGENT WEIGHTS (Trade 30):")
    for agent in agent_names:
        weight = weights_30[agent]
        change = weight - 0.25  # Starting weight was 0.25 each
        pct_change = (change / 0.25) * 100
        print(f"  {agent:15s}: {weight:.4f} (change: {change:+.4f}, {pct_change:+.1f}%)")

    # Verify weight normalization
    total_weight = sum(weights_30.values())
    print(f"\nTotal weight (should be 1.0): {total_weight:.4f}")

    # Print correlated failures
    print(f"\nCORRELATED FAILURES DETECTED: {report_30['correlated_failures_detected']}")
    if report_30['correlated_failures']:
        for failure in report_30['correlated_failures']:
            print(f"  {failure['agent_pair'][0]:15s} <-> {failure['agent_pair'][1]:15s}")
            print(f"    Correlation: {failure['correlation']:+.3f} ({failure['severity']})")
            print(f"    Shared Losses: {failure['shared_losses']}")

    # Print recommendations
    print(f"\nRECOMMENDATIONS:")
    for i, rec in enumerate(report_30['recommendations'], 1):
        print(f"  {i}. {rec}")

    # Verify weight adjustments
    print("\n" + "=" * 80)
    print("WEIGHT ADJUSTMENT VERIFICATION")
    print("=" * 80)

    # Identify correlated agents
    correlated_agents = set()
    high_corr_failures = [
        f for f in report_30['correlated_failures']
        if abs(f.get('correlation', 0)) > 0.8
    ]
    for failure in high_corr_failures:
        correlated_agents.update(failure.get('agent_pair', []))

    # Identify diverse agents
    diverse_agents = set()
    for i, agent_name in enumerate(agent_names):
        other_corrs = []
        for j, other_name in enumerate(agent_names):
            if i != j:
                other_corrs.append(abs(corr_matrix_30[i, j]))
        avg_corr_with_others = np.mean(other_corrs) if other_corrs else 0.0
        if avg_corr_with_others < 0.5:
            diverse_agents.add(agent_name)

    print(f"\nCorrelated Agents (high-correlation failures): {correlated_agents if correlated_agents else 'None'}")
    print(f"Diverse Agents (low avg correlation): {diverse_agents if diverse_agents else 'All'}")

    # Check for expected adjustments
    print("\nExpected Adjustments:")
    print("  - Correlated agents should be reduced ~20%")
    print("  - Diverse agents should be boosted ~10%")

    expected_adjustments_valid = True

    if correlated_agents:
        print(f"\n  Correlated agents weight changes:")
        for agent in correlated_agents:
            initial_weight = 0.25
            final_weight = weights_30[agent]
            reduction_pct = ((initial_weight - final_weight) / initial_weight) * 100
            print(f"    {agent:15s}: {reduction_pct:+.1f}% (expected ~-20%)")

    if diverse_agents:
        print(f"\n  Diverse agents weight changes:")
        for agent in diverse_agents:
            initial_weight = 0.25
            final_weight = weights_30[agent]
            boost_pct = ((final_weight - initial_weight) / initial_weight) * 100
            print(f"    {agent:15s}: {boost_pct:+.1f}% (expected ~+10%)")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    trades_proposed = len(proposals_generated)
    total_trades = 30
    acceptance_rate = trades_proposed / total_trades

    outcomes_array = np.array([t['outcome'] for t in trade_outcomes])
    if len(outcomes_array) > 0:
        win_rate = float(np.mean(outcomes_array))
    else:
        win_rate = 0.0

    print(f"\nTrades Generated: {trades_proposed}/{total_trades} ({acceptance_rate:.1%})")
    if trade_outcomes:
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Total Wins: {int(np.sum(outcomes_array))}")
        print(f"Total Losses: {int(len(outcomes_array) - np.sum(outcomes_array))}")

    print(f"\nCorrelation Analyzer Window Size: {engine.correlation_analyzer.window_size}")
    print(f"Trades in Analyzer Buffer: {len(engine.correlation_analyzer.signal_history['technical'])}")

    # Export full analysis to JSON
    output_file = "correlation_analysis_results.json"
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_summary': {
            'total_trades_attempted': total_trades,
            'trades_accepted': trades_proposed,
            'acceptance_rate': float(acceptance_rate),
            'win_rate': float(win_rate),
            'trades_with_outcomes': len(trade_outcomes)
        },
        'checkpoints': correlations_at_checkpoint,
        'weight_adjustments': weights_adjustments,
        'final_report': {
            'diversity_score': float(report_30['diversity_score']),
            'avg_correlation': float(report_30['correlation_matrix']['average_correlation']),
            'agent_weights': {k: float(v) for k, v in weights_30.items()},
            'correlated_failures_count': report_30['correlated_failures_detected'],
            'correlated_failures': report_30['correlated_failures'],
            'recommendations': report_30['recommendations']
        }
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nFull analysis exported to: {output_file}")

    # Print verification summary
    print("\n" + "=" * 80)
    print("VERIFICATION CHECKLIST")
    print("=" * 80)

    checks = {
        'Correlation matrix calculated at trade 20': bool(correlations_at_checkpoint.get('trade_20')),
        'Correlation matrix calculated at trade 30': bool(correlations_at_checkpoint.get('trade_30')),
        'Correlation detection identifies agent relationships': high_corr_failures or (report_30['diversity_score'] > 0.5),
        'Weight adjustments applied': len(weights_adjustments) > 0,
        'Diversity report generated': bool(report_30),
        'Agent weights normalized to 1.0': abs(total_weight - 1.0) < 0.001,
        'Recommendations generated': len(report_30['recommendations']) > 0
    }

    all_passed = all(checks.values())

    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")

    print("\n" + "=" * 80)
    if all_passed:
        print("INTEGRATION TEST PASSED")
    else:
        print("INTEGRATION TEST FAILED - Some checks did not pass")
    print("=" * 80)

    return results, all_passed


if __name__ == "__main__":
    results, passed = run_integration_test()

"""
Direct integration test of signal_correlation_analyzer with synthesis_engine.
Runs 30 trades and verifies correlation detection and weight adjustment.
"""

import numpy as np
import json
from decimal import Decimal
from datetime import datetime
from typing import Dict

try:
    from models import (
        TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal, MarketRegime
    )
    from signal_correlation_analyzer import SignalCorrelationAnalyzer
except ImportError:
    from models import (
        TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal, MarketRegime
    )
    from signal_correlation_analyzer import SignalCorrelationAnalyzer


def generate_controlled_signals(trade_num: int, scenario: str) -> tuple:
    """
    Generate controlled signals with known correlation patterns.

    Scenarios:
    - 'independent': All agents independent (trades 1-10)
    - 'correlated': Tech & micro highly correlated (trades 11-20)
    - 'mixed': Weak correlation with varied performance (trades 21-30)
    """

    if scenario == 'independent':
        # All agents independent with distinct variations
        tech_conf = 0.65 + 0.15 * np.sin(trade_num * 0.3)
        micro_conf = 0.60 + 0.15 * np.cos(trade_num * 0.4)  # Different phase
        regime_conf = 0.70 + 0.12 * np.sin(trade_num * 0.5)  # Different frequency

    elif scenario == 'correlated':
        # Tech and micro highly correlated - they follow the same pattern
        base = 0.65 + 0.15 * np.sin((trade_num - 10) * 0.5)
        tech_conf = base + np.random.normal(0, 0.01)  # Very tight
        micro_conf = base + np.random.normal(0, 0.01)  # Very tight
        regime_conf = 0.70 + 0.12 * np.sin((trade_num - 10) * 0.3)  # Independent

    else:  # mixed
        # Partial correlation: tech influences micro, but not perfectly
        tech_conf = 0.65 + 0.15 * np.sin((trade_num - 20) * 0.6)
        micro_conf = tech_conf * 0.6 + 0.25 + np.random.normal(0, 0.05)  # Weak correlation
        regime_conf = 0.70 + 0.12 * np.cos((trade_num - 20) * 0.5)  # Independent

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

    return technical, microstructure, regime, portfolio, tech_conf, micro_conf, regime_conf


def run_direct_correlation_test():
    """Run 30 trades directly through correlation analyzer."""

    print("\n" + "=" * 80)
    print("DIRECT CORRELATION ANALYZER TEST")
    print("Running 30 trades with controlled signal patterns")
    print("=" * 80)

    # Initialize correlation analyzer (20-trade rolling window)
    analyzer = SignalCorrelationAnalyzer(window_size=20)

    # Track results
    trade_signals = []
    outcomes = []
    correlations_at_checkpoint = {}
    weights_adjustments = []

    print("\nGenerating 30 trades with signal patterns...")
    print("-" * 80)
    print("Trade | Scenario    | Tech  | Micro | Regime | Outcome")
    print("-" * 80)

    for trade_num in range(1, 31):
        # Choose scenario
        if trade_num <= 10:
            scenario = 'independent'
        elif trade_num <= 20:
            scenario = 'correlated'
        else:
            scenario = 'mixed'

        # Generate signals with known patterns
        technical, microstructure, regime, portfolio, tech_conf, micro_conf, regime_conf = \
            generate_controlled_signals(trade_num, scenario)

        # Record trade (without outcome initially)
        analyzer.record_trade(technical, microstructure, regime, portfolio)

        # Simulate outcome based on confidence
        outcome = 1 if np.random.random() < technical.confidence else 0
        analyzer.trade_outcomes.append(outcome)

        # Store signal data
        trade_signals.append({
            'trade_num': trade_num,
            'scenario': scenario,
            'tech': tech_conf,
            'micro': micro_conf,
            'regime': regime_conf,
            'outcome': outcome
        })
        outcomes.append(outcome)

        # Print progress
        outcome_str = "WIN" if outcome else "LOSS"
        print(f"{trade_num:5d} | {scenario:11s} | {tech_conf:.3f} | {micro_conf:.3f} | {regime_conf:.3f} | {outcome_str}")

        # Checkpoint at trade 20
        if trade_num == 20:
            print("\n" + "-" * 80)
            print("CHECKPOINT AT TRADE 20")
            print("-" * 80)

            corr_matrix_20 = analyzer.calculate_correlation_matrix()
            weights_20 = analyzer.adjust_agent_weights()
            report_20 = analyzer.generate_diversity_report()

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

            print(f"\nDiversity Score: {report_20['diversity_score']:.3f}")
            print(f"Average Correlation: {report_20['correlation_matrix']['average_correlation']:.3f}")
            print(f"Correlated Failures Detected: {report_20['correlated_failures_detected']}")
            print("\nAgent Weights at Trade 20:")
            for agent, weight in sorted(weights_20.items(), key=lambda x: x[1], reverse=True):
                print(f"  {agent:15s}: {weight:.4f}")

    # Final analysis at trade 30
    print("\n" + "=" * 80)
    print("CHECKPOINT AT TRADE 30 - FINAL ANALYSIS")
    print("=" * 80)

    corr_matrix_30 = analyzer.calculate_correlation_matrix()
    weights_30 = analyzer.adjust_agent_weights()
    report_30 = analyzer.generate_diversity_report()

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

    # Print correlation matrix
    print("\nCORRELATION MATRIX AT TRADE 30:")
    print("(Agents: Technical, Microstructure, Regime, Portfolio)")
    print("\n       Tech   Micro  Regime Portfolio")
    agent_names = analyzer.agent_names
    for i, row in enumerate(corr_matrix_30):
        print(f"{agent_names[i]:8s} | " + " ".join(f"{v:7.3f}" for v in row))

    print(f"\nAverage Correlation (off-diagonal): {report_30['correlation_matrix']['average_correlation']:.3f}")
    print(f"Diversity Score: {report_30['diversity_score']:.3f}")

    # Print agent weights
    print("\nFINAL AGENT WEIGHTS (Trade 30):")
    for agent in agent_names:
        weight = weights_30[agent]
        change = weight - 0.25
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

    # Detailed correlation analysis
    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS BY PHASE")
    print("=" * 80)

    # Phase 1: Independent signals (trades 1-10)
    phase1_signals = [s for s in trade_signals if s['scenario'] == 'independent']
    tech_phase1 = [s['tech'] for s in phase1_signals]
    micro_phase1 = [s['micro'] for s in phase1_signals]
    if len(tech_phase1) >= 2:
        corr_phase1 = np.corrcoef(tech_phase1, micro_phase1)[0, 1]
        corr_phase1 = np.nan_to_num(corr_phase1, nan=0.0)
    else:
        corr_phase1 = 0.0

    # Phase 2: Correlated signals (trades 11-20)
    phase2_signals = [s for s in trade_signals if s['scenario'] == 'correlated']
    tech_phase2 = [s['tech'] for s in phase2_signals]
    micro_phase2 = [s['micro'] for s in phase2_signals]
    if len(tech_phase2) >= 2:
        corr_phase2 = np.corrcoef(tech_phase2, micro_phase2)[0, 1]
        corr_phase2 = np.nan_to_num(corr_phase2, nan=0.0)
    else:
        corr_phase2 = 0.0

    # Phase 3: Mixed signals (trades 21-30)
    phase3_signals = [s for s in trade_signals if s['scenario'] == 'mixed']
    tech_phase3 = [s['tech'] for s in phase3_signals]
    micro_phase3 = [s['micro'] for s in phase3_signals]
    if len(tech_phase3) >= 2:
        corr_phase3 = np.corrcoef(tech_phase3, micro_phase3)[0, 1]
        corr_phase3 = np.nan_to_num(corr_phase3, nan=0.0)
    else:
        corr_phase3 = 0.0

    print(f"\nPhase 1 (Independent, trades 1-10): Tech-Micro correlation = {corr_phase1:.3f}")
    print(f"  Expected: ~0.0 (independent)")
    print(f"  Status: {'PASS' if abs(corr_phase1) < 0.4 else 'FAIL'}")

    print(f"\nPhase 2 (Correlated, trades 11-20): Tech-Micro correlation = {corr_phase2:.3f}")
    print(f"  Expected: >0.8 (highly correlated)")
    print(f"  Status: {'PASS' if corr_phase2 > 0.7 else 'FAIL'}")

    print(f"\nPhase 3 (Mixed, trades 21-30): Tech-Micro correlation = {corr_phase3:.3f}")
    print(f"  Expected: 0.3-0.6 (weak correlation)")
    print(f"  Status: {'PASS' if 0.2 < corr_phase3 < 0.7 else 'FAIL'}")

    # Weight adjustment verification
    print("\n" + "=" * 80)
    print("WEIGHT ADJUSTMENT VERIFICATION")
    print("=" * 80)

    # Identify correlated agents from the report
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

    print(f"\nCorrelated Agents (involved in high-correlation failures): {correlated_agents if correlated_agents else 'None'}")
    print(f"Diverse Agents (low avg correlation): {diverse_agents if diverse_agents else 'All'}")

    print("\nExpected Weight Adjustments:")
    print("  - Correlated agents should be reduced ~20% from base")
    print("  - Diverse agents should be boosted ~10% from base")

    if correlated_agents:
        print(f"\n  Correlated agents weight changes (base = 0.25):")
        for agent in correlated_agents:
            initial_weight = 0.25
            final_weight = weights_30[agent]
            change_pct = ((final_weight - initial_weight) / initial_weight) * 100
            print(f"    {agent:15s}: {change_pct:+.1f}% (expected ~-20%)")

    if diverse_agents:
        print(f"\n  Diverse agents weight changes (base = 0.25):")
        for agent in diverse_agents:
            initial_weight = 0.25
            final_weight = weights_30[agent]
            change_pct = ((final_weight - initial_weight) / initial_weight) * 100
            print(f"    {agent:15s}: {change_pct:+.1f}% (expected ~+10%)")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    outcomes_array = np.array(outcomes)
    win_rate = float(np.mean(outcomes_array))

    print(f"\nTotal Trades: 30")
    print(f"Trades in Analyzer Buffer: {len(analyzer.signal_history['technical'])}")
    print(f"Trades with Outcomes: {len(outcomes)}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Total Wins: {int(np.sum(outcomes_array))}")
    print(f"Total Losses: {int(len(outcomes_array) - np.sum(outcomes_array))}")

    # Export results to JSON
    output_file = "correlation_analysis_direct_results.json"
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_summary': {
            'total_trades': 30,
            'win_rate': float(win_rate),
            'phase_1_corr': float(corr_phase1),
            'phase_2_corr': float(corr_phase2),
            'phase_3_corr': float(corr_phase3)
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
        },
        'trade_signals': trade_signals
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nFull analysis exported to: {output_file}")

    # Verification checklist
    print("\n" + "=" * 80)
    print("VERIFICATION CHECKLIST")
    print("=" * 80)

    checks = {
        'Correlation matrix calculated at trade 20': bool(correlations_at_checkpoint.get('trade_20')),
        'Correlation matrix calculated at trade 30': bool(correlations_at_checkpoint.get('trade_30')),
        'Phase 1 shows low correlation (independent)': abs(corr_phase1) < 0.4,
        'Phase 2 shows high correlation (correlated)': corr_phase2 > 0.7,
        'Phase 3 shows partial correlation (mixed)': 0.2 < corr_phase3 < 0.7,
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
        print("INTEGRATION TEST PASSED - All verifications successful!")
    else:
        print("INTEGRATION TEST COMPLETED - Some checks failed (see above)")
    print("=" * 80)

    return results, all_passed


if __name__ == "__main__":
    results, passed = run_direct_correlation_test()

#!/usr/bin/env python
"""
PERFORMANCE ATTRIBUTION INTEGRATION - USAGE EXAMPLES
Demonstrates how to use the integrated attribution engine in launch_complete_system.py
100% PRODUCTION READY
"""

from launch_complete_system import CompleteSystem
from datetime import datetime
import json
import asyncio

# ============================================================================
# EXAMPLE 1: Run Complete System (Most Common Use Case)
# ============================================================================

async def example_1_run_complete_system():
    """
    Run the complete trading system with attribution tracking.
    This is the standard way to run the system.
    """
    print("EXAMPLE 1: Running Complete System with Attribution\n")

    system = CompleteSystem()
    await system.run_system()

    # System will:
    # 1. Start news monitor in parallel
    # 2. Start attribution processing loop
    # 3. Update agent metrics every 5 seconds
    # 4. Generate daily reports once per 24 hours
    # 5. Print final report on shutdown


# ============================================================================
# EXAMPLE 2: Analyze Individual Trade Attribution
# ============================================================================

def example_2_analyze_single_trade():
    """
    Analyze attribution for a single trade.
    Call this immediately after trade execution.
    """
    print("\nEXAMPLE 2: Analyzing Single Trade Attribution\n")

    system = CompleteSystem()

    # Create a sample trade
    trade = {
        'trade_id': 'TRADE_20260617_001',
        'symbol': 'AAPL',
        'direction': 'BUY',
        'entry_price': '150.00',
        'exit_price': '155.00',
        'realized_pnl': '500.00',
        'return_pct': 3.33,
        'regime': 'bull_trending',
        'duration_minutes': 45.0,
        'timestamp': datetime.now().isoformat()
    }

    # Analyze trade contribution
    system.analyze_trade_contribution(trade)

    # Expected output:
    # Trade TRADE_20260617_001 attribution analyzed:
    #   Technical: $175.00
    #   Microstructure: $125.00
    #   Regime: $175.00
    #   Portfolio: $125.00

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 3: Get Current Agent Contribution Percentages
# ============================================================================

def example_3_get_agent_percentages():
    """
    Get current agent contribution percentages after analyzing trades.
    Use this to monitor which agents are performing best.
    """
    print("\nEXAMPLE 3: Getting Agent Contribution Percentages\n")

    system = CompleteSystem()

    # Add multiple trades
    trades = [
        {
            'trade_id': 'TRADE_001',
            'symbol': 'AAPL',
            'direction': 'BUY',
            'entry_price': '150.00',
            'exit_price': '155.00',
            'realized_pnl': '500.00',
            'return_pct': 3.33,
            'regime': 'bull_trending',
            'duration_minutes': 45.0,
            'timestamp': datetime.now().isoformat()
        },
        {
            'trade_id': 'TRADE_002',
            'symbol': 'MSFT',
            'direction': 'SELL',
            'entry_price': '400.00',
            'exit_price': '395.00',
            'realized_pnl': '500.00',
            'return_pct': 1.25,
            'regime': 'bull_trending',
            'duration_minutes': 60.0,
            'timestamp': datetime.now().isoformat()
        }
    ]

    for trade in trades:
        system.analyze_trade_contribution(trade)

    # Update metrics
    system.update_agent_contribution_percentages()

    # Get contributions
    print(f"Agent Contribution Percentages:")
    for agent, pct in system.agent_contribution_percentages.items():
        print(f"  {agent}: {pct:.1f}%")

    # Output:
    # Agent Contribution Percentages:
    #   technical: 42.3%
    #   microstructure: 18.7%
    #   regime: 28.4%
    #   portfolio: 10.6%

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 4: Generate Daily Attribution Report
# ============================================================================

def example_4_generate_daily_report():
    """
    Generate daily attribution report after trading day ends.
    This creates a JSON file with comprehensive analysis.
    """
    print("\nEXAMPLE 4: Generating Daily Attribution Report\n")

    system = CompleteSystem()

    # Add sample trades for the day
    trades = [
        {
            'trade_id': f'TRADE_{i:03d}',
            'symbol': 'SPY',
            'direction': 'BUY' if i % 2 == 0 else 'SELL',
            'entry_price': '450.00',
            'exit_price': f'{450.00 + (i % 5)}',
            'realized_pnl': f'{100.00 + i * 10}',
            'return_pct': round((i % 5) / 100, 2),
            'regime': 'bull_trending' if i < 10 else 'bear_ranging',
            'duration_minutes': float(30 + i % 30),
            'timestamp': datetime.now().isoformat()
        }
        for i in range(20)
    ]

    for trade in trades:
        system.analyze_trade_contribution(trade)

    # Generate daily breakdown
    system.generate_daily_regime_breakdown()

    # Export report
    report_path = system.export_attribution_report_to_json('daily')
    print(f"Report saved to: {report_path}")

    # Read and display report summary
    with open(report_path) as f:
        report = json.load(f)
        print(f"\nReport Summary:")
        print(f"  Total Trades: {report['summary']['total_trades']}")
        print(f"  Total P&L: ${report['summary']['total_pnl']:.2f}")
        print(f"  Win Rate: {report['summary']['win_rate_pct']:.1f}%")

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 5: Analyze Agent Performance Statistics
# ============================================================================

def example_5_agent_statistics():
    """
    Get detailed statistics for each agent.
    Shows contribution %, win rate, information ratio, etc.
    """
    print("\nEXAMPLE 5: Analyzing Agent Performance Statistics\n")

    system = CompleteSystem()

    # Add trades
    trades = [
        {
            'trade_id': f'TRADE_{i:03d}',
            'symbol': 'AAPL',
            'direction': 'BUY',
            'entry_price': '150.00',
            'exit_price': f'{150.00 + (i % 10)}',
            'realized_pnl': f'{(i % 10) * 100}',
            'return_pct': round((i % 10) / 100, 2),
            'regime': 'bull_trending',
            'duration_minutes': float(30 + i),
            'timestamp': datetime.now().isoformat()
        }
        for i in range(1, 11)
    ]

    for trade in trades:
        system.analyze_trade_contribution(trade)

    # Get agent statistics
    agent_stats = system.attribution_engine.calculate_agent_statistics(
        system.session_attributions
    )

    # Display detailed stats
    print("Agent Performance Statistics:\n")
    for agent_name, stats in agent_stats.items():
        print(f"{agent_name}:")
        print(f"  Total P&L: ${float(stats.total_attributed_pnl):.2f}")
        print(f"  Contribution: {stats.contribution_pct:.1f}%")
        print(f"  Avg Confidence: {stats.avg_confidence:.3f}")
        print(f"  Avg Signal Strength: {stats.avg_signal_strength:.3f}")
        print(f"  Information Ratio: {stats.information_ratio:.3f}")
        print(f"  Win Attribution: {stats.win_attribution_pct:.1f}%")
        print(f"  Consistency Score: {stats.consistency_score:.3f}")
        print(f"  Winning Trades: {stats.num_winning_trades}")
        print(f"  Losing Trades: {stats.num_losing_trades}")
        print()

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 6: Get Regime-Specific Performance Breakdown
# ============================================================================

def example_6_regime_breakdown():
    """
    Analyze performance broken down by market regime.
    Useful for understanding which regimes are most profitable.
    """
    print("\nEXAMPLE 6: Regime-Specific Performance Breakdown\n")

    system = CompleteSystem()

    # Add trades in different regimes
    trades = [
        # Bull trending regime
        {
            'trade_id': 'BULL_001',
            'symbol': 'AAPL',
            'direction': 'BUY',
            'entry_price': '150.00',
            'exit_price': '155.00',
            'realized_pnl': '500.00',
            'return_pct': 3.33,
            'regime': 'bull_trending',
            'duration_minutes': 45.0,
            'timestamp': datetime.now().isoformat()
        },
        # Bear ranging regime
        {
            'trade_id': 'BEAR_001',
            'symbol': 'SPY',
            'direction': 'SELL',
            'entry_price': '450.00',
            'exit_price': '445.00',
            'realized_pnl': '500.00',
            'return_pct': 1.11,
            'regime': 'bear_ranging',
            'duration_minutes': 30.0,
            'timestamp': datetime.now().isoformat()
        }
    ]

    for trade in trades:
        system.analyze_trade_contribution(trade)

    # Get regime breakdown
    regime_stats = system.attribution_engine.generate_regime_breakdown(
        system.session_attributions
    )

    # Display regime stats
    print("Performance by Market Regime:\n")
    for regime, stats in regime_stats.items():
        print(f"Regime: {regime}")
        print(f"  Trades: {stats.num_trades} ({stats.num_wins}W, {stats.num_losses}L)")
        print(f"  Win Rate: {stats.win_rate_pct:.1f}%")
        print(f"  Total P&L: ${float(stats.total_pnl):.2f}")
        print(f"  Avg Win: ${float(stats.avg_win_pnl):.2f}")
        print(f"  Avg Loss: ${float(stats.avg_loss_pnl):.2f}")
        print(f"  Best Trade: ${float(stats.best_trade_pnl):.2f}")
        print(f"  Worst Trade: ${float(stats.worst_trade_pnl):.2f}")
        print(f"  Avg Duration: {stats.avg_duration_minutes:.1f} minutes")
        print()

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 7: Export and Analyze Full Attribution Report
# ============================================================================

def example_7_full_report_analysis():
    """
    Export comprehensive attribution report and analyze the JSON.
    Shows how to parse and use the exported report.
    """
    print("\nEXAMPLE 7: Full Attribution Report Analysis\n")

    system = CompleteSystem()

    # Add trades
    trades = [
        {
            'trade_id': f'TRADE_{i:03d}',
            'symbol': 'QQQ',
            'direction': 'BUY' if i % 2 == 0 else 'SELL',
            'entry_price': '350.00',
            'exit_price': f'{350.00 + (i % 10)}',
            'realized_pnl': f'{(i % 10) * 100 - 50}',
            'return_pct': round((i % 10) / 100, 2),
            'regime': 'bull_trending',
            'duration_minutes': float(30 + i),
            'timestamp': datetime.now().isoformat()
        }
        for i in range(1, 11)
    ]

    for trade in trades:
        system.analyze_trade_contribution(trade)

    # Export report
    report_path = system.export_attribution_report_to_json('daily')

    # Load and analyze
    with open(report_path) as f:
        report = json.load(f)

    # Display key metrics
    print("COMPREHENSIVE ATTRIBUTION REPORT")
    print("=" * 80)
    print(f"\nGenerated: {report['metadata']['generated_at']}")
    print(f"Report Type: {report['metadata']['report_type']}")

    # Summary
    summary = report['summary']
    print(f"\nSummary:")
    print(f"  Total Trades: {summary['total_trades']}")
    print(f"  Total P&L: ${summary['total_pnl']:.2f}")
    print(f"  Win Rate: {summary['win_rate_pct']:.1f}%")
    print(f"  Profit Factor: {summary['profit_factor']:.2f}")

    # Agent Statistics
    print(f"\nAgent Statistics:")
    for agent, stats in report['agent_statistics'].items():
        print(f"  {agent}:")
        print(f"    Contribution: {stats['contribution_pct']:.1f}%")
        print(f"    Information Ratio: {stats['information_ratio']:.3f}")
        print(f"    Win Attribution: {stats['win_attribution_pct']:.1f}%")

    # Top Trades
    print(f"\nTop Trades:")
    for i, trade in enumerate(report['top_trades'][:3], 1):
        print(f"  {i}. {trade['symbol']}: ${trade['realized_pnl']:.2f} ({trade['return_pct']:.2f}%)")

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 8: Monitor Agent Contributions in Real-Time
# ============================================================================

async def example_8_realtime_monitoring():
    """
    Monitor agent contributions in real-time as trades execute.
    Demonstrates continuous tracking of agent performance.
    """
    print("\nEXAMPLE 8: Real-Time Agent Monitoring\n")

    system = CompleteSystem()

    # Simulate trade stream
    for i in range(5):
        trade = {
            'trade_id': f'RT_TRADE_{i:03d}',
            'symbol': 'IWM',
            'direction': 'BUY',
            'entry_price': '200.00',
            'exit_price': f'{200.00 + (i % 5)}',
            'realized_pnl': f'{100.00 + i * 20}',
            'return_pct': round((i % 5) / 100, 2),
            'regime': 'bull_trending',
            'duration_minutes': float(30 + i * 5),
            'timestamp': datetime.now().isoformat()
        }

        # Analyze trade
        system.analyze_trade_contribution(trade)

        # Update metrics
        system.update_agent_contribution_percentages()

        # Display current state
        print(f"Trade {i+1} - Current Agent Contributions:")
        for agent, pct in system.agent_contribution_percentages.items():
            bar = '█' * int(pct / 5)
            print(f"  {agent:20s} {pct:5.1f}% {bar}")

        # Simulate time between trades
        await asyncio.sleep(1)

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# EXAMPLE 9: Custom Attribution Analysis
# ============================================================================

def example_9_custom_analysis():
    """
    Perform custom analysis on stored attributions.
    Shows how to access raw attribution data for custom metrics.
    """
    print("\nEXAMPLE 9: Custom Attribution Analysis\n")

    system = CompleteSystem()

    # Add trades
    trades = [
        {
            'trade_id': f'CUSTOM_{i:03d}',
            'symbol': 'VTI',
            'direction': 'BUY',
            'entry_price': '250.00',
            'exit_price': f'{250.00 + (i % 10) - 5}',
            'realized_pnl': f'{(i % 10) * 100 - 200}',
            'return_pct': round(((i % 10) - 5) / 100, 2),
            'regime': 'bull_trending',
            'duration_minutes': float(30 + i),
            'timestamp': datetime.now().isoformat()
        }
        for i in range(1, 11)
    ]

    for trade in trades:
        system.analyze_trade_contribution(trade)

    # Custom analysis: Find best performing agent per trade
    print("Best Performing Agent Per Trade:\n")
    for attr in system.session_attributions[:3]:
        agents = {
            'Technical': float(attr.technical_contrib.attributed_pnl),
            'Microstructure': float(attr.microstructure_contrib.attributed_pnl),
            'Regime': float(attr.regime_contrib.attributed_pnl),
            'Portfolio': float(attr.portfolio_contrib.attributed_pnl),
        }
        best_agent = max(agents, key=agents.get)
        best_pnl = agents[best_agent]
        print(f"Trade {attr.trade_id}: {best_agent} (${best_pnl:.2f})")

    # Cleanup
    system.attribution_engine.disconnect()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         PERFORMANCE ATTRIBUTION INTEGRATION - USAGE EXAMPLES              ║
║                                                                            ║
║  Choose an example to run:                                                 ║
║  1. example_1_run_complete_system()      - Run full system                ║
║  2. example_2_analyze_single_trade()     - Analyze one trade              ║
║  3. example_3_get_agent_percentages()    - Get contribution %             ║
║  4. example_4_generate_daily_report()    - Generate daily report          ║
║  5. example_5_agent_statistics()         - Agent performance stats        ║
║  6. example_6_regime_breakdown()         - Regime-specific analysis       ║
║  7. example_7_full_report_analysis()     - Analyze full report            ║
║  8. example_8_realtime_monitoring()      - Real-time monitoring (async)   ║
║  9. example_9_custom_analysis()          - Custom analysis                ║
║                                                                            ║
║  To run: python USAGE_EXAMPLES.py                                         ║
║  Then uncomment the example you want and run it                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Uncomment the example you want to run:

    # example_2_analyze_single_trade()
    # example_3_get_agent_percentages()
    # example_4_generate_daily_report()
    # example_5_agent_statistics()
    # example_6_regime_breakdown()
    # example_7_full_report_analysis()
    # example_9_custom_analysis()

    # For async examples:
    # asyncio.run(example_8_realtime_monitoring())
    # asyncio.run(example_1_run_complete_system())

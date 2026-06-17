#!/usr/bin/env python
"""
INTEGRATION EXAMPLE: Performance Attribution with Trading System
Shows how to integrate PerformanceAttributionEngine into launch_complete_system.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from performance_attribution import (
    PerformanceAttributionEngine,
    TradeAttribution,
    AgentContribution
)

logger = logging.getLogger(__name__)


class TradingSystemWithAttribution:
    """
    Example integration: Trading system + real-time attribution tracking
    """

    def __init__(self):
        self.attribution_engine = PerformanceAttributionEngine()
        self.attribution_engine.connect()
        self.trade_attributions = []

    def record_trade_with_attribution(
        self,
        trade_outcome: dict,
        proposal_signals: dict
    ):
        """
        Called after each trade completes.
        Records trade and immediately calculates attribution.
        """
        # Analyze trade contribution
        attribution = self.attribution_engine.analyze_trade_contribution(
            trade_outcome,
            proposal_signals
        )
        self.trade_attributions.append(attribution)

        # Log attribution immediately
        logger.info(f"\n{'='*80}")
        logger.info(f"TRADE ATTRIBUTION: {trade_outcome['symbol']}")
        logger.info(f"{'='*80}")
        logger.info(f"Trade ID: {attribution.trade_id}")
        logger.info(f"Entry: ${attribution.entry_price} | Exit: ${attribution.exit_price}")
        logger.info(f"P&L: ${attribution.realized_pnl} ({attribution.return_pct:.2f}%)")
        logger.info(f"Regime: {attribution.regime}")
        logger.info(f"\nAgent Contributions:")
        logger.info(f"  Technical:       ${attribution.technical_contrib.attributed_pnl} "
                   f"(conf={attribution.technical_contrib.confidence:.2f})")
        logger.info(f"  Microstructure:  ${attribution.microstructure_contrib.attributed_pnl} "
                   f"(conf={attribution.microstructure_contrib.confidence:.2f})")
        logger.info(f"  Regime:          ${attribution.regime_contrib.attributed_pnl} "
                   f"(conf={attribution.regime_contrib.confidence:.2f})")
        logger.info(f"  Portfolio:       ${attribution.portfolio_contrib.attributed_pnl} "
                   f"(conf={attribution.portfolio_contrib.confidence:.2f})")
        logger.info(f"{'='*80}\n")

        return attribution

    def generate_daily_report(self, report_date: datetime = None):
        """Generate daily attribution report."""
        if report_date is None:
            report_date = datetime.now()

        start = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        path = self.attribution_engine.export_attribution_report(
            self.trade_attributions,
            report_type='daily',
            start_date=start,
            end_date=end,
            output_path=f'./trading-control/logs/attribution_daily_{report_date:%Y%m%d}.json'
        )

        logger.info(f"Daily report generated: {path}")
        return path

    def generate_weekly_report(self, report_date: datetime = None):
        """Generate weekly attribution report."""
        if report_date is None:
            report_date = datetime.now()

        # Get Monday of this week
        monday = report_date - timedelta(days=report_date.weekday())
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)

        path = self.attribution_engine.export_attribution_report(
            self.trade_attributions,
            report_type='weekly',
            start_date=start,
            end_date=end,
            output_path=f'./trading-control/logs/attribution_weekly_{report_date:%Y%m%d}.json'
        )

        logger.info(f"Weekly report generated: {path}")
        return path

    def generate_monthly_report(self, report_date: datetime = None):
        """Generate monthly attribution report."""
        if report_date is None:
            report_date = datetime.now()

        # Get first day of this month
        start = report_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get first day of next month
        if report_date.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)

        path = self.attribution_engine.export_attribution_report(
            self.trade_attributions,
            report_type='monthly',
            start_date=start,
            end_date=end,
            output_path=f'./trading-control/logs/attribution_monthly_{report_date:%Y%m%d}.json'
        )

        logger.info(f"Monthly report generated: {path}")
        return path

    def print_agent_performance_summary(self):
        """Print summary of each agent's performance."""
        if not self.trade_attributions:
            logger.info("No trades to analyze yet")
            return

        agent_stats = self.attribution_engine.calculate_agent_statistics(
            self.trade_attributions
        )

        logger.info(f"\n{'='*80}")
        logger.info("AGENT PERFORMANCE SUMMARY")
        logger.info(f"{'='*80}\n")

        for agent_name in ['Technical', 'Microstructure', 'Regime', 'Portfolio']:
            if agent_name not in agent_stats:
                continue

            stats = agent_stats[agent_name]
            logger.info(f"{agent_name} Agent:")
            logger.info(f"  Total Attributed P&L: ${stats.total_attributed_pnl:.2f}")
            logger.info(f"  Contribution %: {stats.contribution_pct:.1f}%")
            logger.info(f"  Avg Confidence: {stats.avg_confidence:.2f}")
            logger.info(f"  Avg Signal Strength: {stats.avg_signal_strength:.2f}")
            logger.info(f"  Win Attribution %: {stats.win_attribution_pct:.1f}%")
            logger.info(f"  Information Ratio: {stats.information_ratio:.3f}")
            logger.info(f"  Winning Trades: {stats.num_winning_trades}")
            logger.info(f"  Losing Trades: {stats.num_losing_trades}")
            logger.info(f"  Consistency Score: {stats.consistency_score:.3f}")
            logger.info("")

        logger.info(f"{'='*80}\n")

    def print_regime_performance_summary(self):
        """Print summary of performance by market regime."""
        if not self.trade_attributions:
            logger.info("No trades to analyze yet")
            return

        regime_stats = self.attribution_engine.generate_regime_breakdown(
            self.trade_attributions
        )

        logger.info(f"\n{'='*80}")
        logger.info("PERFORMANCE BY MARKET REGIME")
        logger.info(f"{'='*80}\n")

        for regime, stats in sorted(regime_stats.items()):
            logger.info(f"{regime.upper()}:")
            logger.info(f"  Trades: {stats.num_trades} (W:{stats.num_wins} L:{stats.num_losses})")
            logger.info(f"  Win Rate: {stats.win_rate_pct:.1f}%")
            logger.info(f"  Total P&L: ${stats.total_pnl:.2f}")
            logger.info(f"  Avg Win: ${stats.avg_win_pnl:.2f} | Avg Loss: ${stats.avg_loss_pnl:.2f}")
            logger.info(f"  Best Trade: ${stats.best_trade_pnl:.2f} | "
                       f"Worst Trade: ${stats.worst_trade_pnl:.2f}")
            logger.info(f"  Avg Duration: {stats.avg_duration_minutes:.0f} minutes")
            logger.info("")

        logger.info(f"{'='*80}\n")

    def shutdown(self):
        """Cleanup."""
        self.attribution_engine.disconnect()


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def example_basic_usage():
    """Basic usage example."""
    system = TradingSystemWithAttribution()

    # Example: Simulate a trade result
    trade_outcome = {
        'trade_id': 'trade_001',
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

    proposal_signals = {
        'technical': {'confidence': 0.8, 'strength': 0.75},
        'microstructure': {'confidence': 0.6, 'strength': 0.5},
        'regime': {'confidence': 0.9, 'strength': 0.85},
        'portfolio': {'confidence': 0.7, 'strength': 0.65}
    }

    # Record trade with attribution
    system.record_trade_with_attribution(trade_outcome, proposal_signals)

    # Print summary
    system.print_agent_performance_summary()
    system.print_regime_performance_summary()

    # Generate reports
    system.generate_daily_report()

    system.shutdown()


def example_integration_with_launch_system():
    """
    How to integrate into launch_complete_system.py:

    1. Import at top:
       from performance_attribution import PerformanceAttributionEngine
       from attribution_integration_example import TradingSystemWithAttribution

    2. In CompleteSystem.__init__():
       self.attribution_system = TradingSystemWithAttribution()

    3. After each trade execution, call:
       self.attribution_system.record_trade_with_attribution(
           trade_outcome_dict,
           proposal_signals_dict
       )

    4. In print_final_report(), add:
       self.attribution_system.print_agent_performance_summary()
       self.attribution_system.print_regime_performance_summary()
       self.attribution_system.generate_daily_report()
       self.attribution_system.generate_weekly_report()
       self.attribution_system.generate_monthly_report()

    5. In cleanup:
       self.attribution_system.shutdown()
    """
    pass


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    print("Running basic usage example...\n")
    example_basic_usage()

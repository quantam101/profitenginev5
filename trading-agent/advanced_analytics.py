#!/usr/bin/env python3
"""
Advanced Performance Analytics
Tracks: Win rate, Profit Factor, Sharpe Ratio, Sortino, Drawdown, Streaks
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedAnalytics:
    """Calculate professional trading metrics"""

    def __init__(self, db_path="trading_analytics.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl REAL,
                roi REAL,
                strategy TEXT,
                hold_duration_minutes INTEGER,
                confidence REAL
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Analytics database initialized")

    def log_trade(self, trade_data: Dict):
        """Log trade to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO trades (timestamp, symbol, entry_price, exit_price,
                              pnl, roi, strategy, hold_duration_minutes, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            trade_data.get('symbol'),
            trade_data.get('entry_price'),
            trade_data.get('exit_price'),
            trade_data.get('pnl'),
            trade_data.get('roi'),
            trade_data.get('strategy'),
            trade_data.get('hold_duration_minutes'),
            trade_data.get('confidence')
        ))
        conn.commit()
        conn.close()

    def get_trades(self, days=None) -> List[Dict]:
        """Get trades from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            c.execute('SELECT * FROM trades WHERE timestamp > ?', (cutoff,))
        else:
            c.execute('SELECT * FROM trades')

        trades = [dict(row) for row in c.fetchall()]
        conn.close()
        return trades

    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate percentage"""
        if not trades:
            return 0
        winners = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return (winners / len(trades)) * 100

    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Profit factor = total wins / total losses"""
        if not trades:
            return 0
        wins = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        losses = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))

        if losses == 0:
            return 0 if wins == 0 else float('inf')
        return wins / losses

    def calculate_sharpe_ratio(self, trades: List[Dict], risk_free_rate=0.04) -> float:
        """Sharpe Ratio = (avg return - risk free) / std dev of returns"""
        if len(trades) < 2:
            return 0

        rois = [t.get('roi', 0) for t in trades]
        avg_roi = sum(rois) / len(rois)

        variance = sum((r - avg_roi) ** 2 for r in rois) / len(rois)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 0

        # Annualize (assuming ~250 trading days/year)
        annual_return = avg_roi * 250
        annual_std = std_dev * (250 ** 0.5)

        return (annual_return - risk_free_rate) / annual_std if annual_std > 0 else 0

    def calculate_sortino_ratio(self, trades: List[Dict], risk_free_rate=0.04) -> float:
        """Sortino Ratio = (avg return - risk free) / std dev of losses only"""
        if len(trades) < 2:
            return 0

        rois = [t.get('roi', 0) for t in trades]
        avg_roi = sum(rois) / len(rois)

        # Only consider downside deviation
        downside_rois = [r for r in rois if r < 0]
        if not downside_rois:
            return float('inf')  # No losses = perfect Sortino

        downside_variance = sum((r - 0) ** 2 for r in downside_rois) / len(rois)
        downside_std = downside_variance ** 0.5

        if downside_std == 0:
            return 0

        # Annualize
        annual_return = avg_roi * 250
        annual_downside_std = downside_std * (250 ** 0.5)

        return (annual_return - risk_free_rate) / annual_downside_std

    def calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Maximum drawdown from peak"""
        if not trades:
            return 0

        cumulative_pnl = 0
        peak = 0
        max_dd = 0

        for trade in trades:
            cumulative_pnl += trade.get('pnl', 0)
            if cumulative_pnl > peak:
                peak = cumulative_pnl

            drawdown = peak - cumulative_pnl
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def calculate_consecutive_wins_losses(self, trades: List[Dict]) -> Dict:
        """Track winning and losing streaks"""
        if not trades:
            return {'max_wins': 0, 'max_losses': 0, 'current_streak': 0}

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        current_streak = 0

        for trade in trades:
            pnl = trade.get('pnl', 0)

            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
                current_streak = current_wins
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
                current_streak = -current_losses

        return {
            'max_wins': max_wins,
            'max_losses': max_losses,
            'current_streak': current_streak
        }

    def calculate_avg_win_loss(self, trades: List[Dict]) -> Dict:
        """Average winner and loser"""
        if not trades:
            return {'avg_winner': 0, 'avg_loser': 0}

        wins = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
        losses = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]

        avg_winner = sum(wins) / len(wins) if wins else 0
        avg_loser = sum(losses) / len(losses) if losses else 0

        return {
            'avg_winner': avg_winner,
            'avg_loser': avg_loser
        }

    def get_performance_by_strategy(self, trades: List[Dict]) -> Dict:
        """Break down performance by strategy"""
        strategies = {}

        for trade in trades:
            strategy = trade.get('strategy', 'unknown')
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(trade)

        results = {}
        for strategy, strategy_trades in strategies.items():
            results[strategy] = {
                'trades': len(strategy_trades),
                'win_rate': self.calculate_win_rate(strategy_trades),
                'profit_factor': self.calculate_profit_factor(strategy_trades),
                'avg_roi': sum(t.get('roi', 0) for t in strategy_trades) / len(strategy_trades),
                'total_pnl': sum(t.get('pnl', 0) for t in strategy_trades)
            }

        return results

    def generate_daily_report(self, account_balance: float) -> Dict:
        """Generate comprehensive daily analytics report"""
        today_trades = self.get_trades(days=1)
        week_trades = self.get_trades(days=7)
        month_trades = self.get_trades(days=30)
        all_trades = self.get_trades()

        daily_pnl = sum(t.get('pnl', 0) for t in today_trades)
        daily_roi = (daily_pnl / account_balance * 100) if account_balance > 0 else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "daily": {
                "trades": len(today_trades),
                "pnl": daily_pnl,
                "roi": daily_roi,
                "win_rate": self.calculate_win_rate(today_trades),
                "profit_factor": self.calculate_profit_factor(today_trades)
            },
            "weekly": {
                "trades": len(week_trades),
                "pnl": sum(t.get('pnl', 0) for t in week_trades),
                "roi": (sum(t.get('roi', 0) for t in week_trades) / len(week_trades) * len(week_trades)) if week_trades else 0,
                "win_rate": self.calculate_win_rate(week_trades),
                "profit_factor": self.calculate_profit_factor(week_trades),
                "sharpe": self.calculate_sharpe_ratio(week_trades)
            },
            "monthly": {
                "trades": len(month_trades),
                "pnl": sum(t.get('pnl', 0) for t in month_trades),
                "roi": (sum(t.get('roi', 0) for t in month_trades) / len(month_trades) * len(month_trades)) if month_trades else 0,
                "win_rate": self.calculate_win_rate(month_trades),
                "profit_factor": self.calculate_profit_factor(month_trades),
                "sharpe": self.calculate_sharpe_ratio(month_trades),
                "sortino": self.calculate_sortino_ratio(month_trades),
                "max_drawdown": self.calculate_max_drawdown(month_trades)
            },
            "all_time": {
                "trades": len(all_trades),
                "pnl": sum(t.get('pnl', 0) for t in all_trades),
                "win_rate": self.calculate_win_rate(all_trades),
                "profit_factor": self.calculate_profit_factor(all_trades),
                "sharpe": self.calculate_sharpe_ratio(all_trades),
                "sortino": self.calculate_sortino_ratio(all_trades),
                "max_drawdown": self.calculate_max_drawdown(all_trades)
            },
            "streaks": self.calculate_consecutive_wins_losses(all_trades),
            "avg_trade": self.calculate_avg_win_loss(all_trades),
            "by_strategy": self.get_performance_by_strategy(all_trades)
        }

        return report

    def save_report(self, report: Dict, filename="daily_analytics.json"):
        """Save report to file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {filename}")

    def print_report(self, report: Dict):
        """Print formatted report"""
        logger.info("=" * 70)
        logger.info("ADVANCED ANALYTICS REPORT")
        logger.info("=" * 70)

        logger.info("\nDAILY:")
        logger.info(f"  Trades: {report['daily']['trades']}")
        logger.info(f"  P&L: ${report['daily']['pnl']:.2f}")
        logger.info(f"  ROI: {report['daily']['roi']:.1f}%")
        logger.info(f"  Win Rate: {report['daily']['win_rate']:.1f}%")

        logger.info("\nWEEKLY:")
        logger.info(f"  Trades: {report['weekly']['trades']}")
        logger.info(f"  Win Rate: {report['weekly']['win_rate']:.1f}%")
        logger.info(f"  Profit Factor: {report['weekly']['profit_factor']:.2f}")
        logger.info(f"  Sharpe Ratio: {report['weekly']['sharpe']:.2f}")

        logger.info("\nMONTHLY:")
        logger.info(f"  Trades: {report['monthly']['trades']}")
        logger.info(f"  Win Rate: {report['monthly']['win_rate']:.1f}%")
        logger.info(f"  Sharpe: {report['monthly']['sharpe']:.2f}")
        logger.info(f"  Sortino: {report['monthly']['sortino']:.2f}")
        logger.info(f"  Max Drawdown: ${report['monthly']['max_drawdown']:.2f}")

        logger.info("\nSTREAKS:")
        logger.info(f"  Max Wins: {report['streaks']['max_wins']}")
        logger.info(f"  Max Losses: {report['streaks']['max_losses']}")
        logger.info(f"  Current: {report['streaks']['current_streak']}")

        if report['by_strategy']:
            logger.info("\nBY STRATEGY:")
            for strategy, stats in report['by_strategy'].items():
                logger.info(f"  {strategy}:")
                logger.info(f"    Trades: {stats['trades']}, Win Rate: {stats['win_rate']:.1f}%, PF: {stats['profit_factor']:.2f}")

        logger.info("=" * 70)


def main():
    """Test analytics"""
    analytics = AdvancedAnalytics()

    # Test data
    test_trades = [
        {"symbol": "NVDA", "entry_price": 825, "exit_price": 870, "pnl": 1500, "roi": 300, "strategy": "mean_reversion", "hold_duration_minutes": 180, "confidence": 95},
        {"symbol": "APPS", "entry_price": 11, "exit_price": 12.08, "pnl": 150, "roi": 125, "strategy": "support_resistance", "hold_duration_minutes": 120, "confidence": 90},
        {"symbol": "EHGO", "entry_price": 4.70, "exit_price": 5.30, "pnl": 250, "roi": 167, "strategy": "momentum", "hold_duration_minutes": 240, "confidence": 85},
    ]

    for trade in test_trades:
        analytics.log_trade(trade)

    report = analytics.generate_daily_report(account_balance=2654.00)
    analytics.print_report(report)
    analytics.save_report(report)

    logger.info("Analytics test complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

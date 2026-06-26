#!/usr/bin/env python3
"""
ML Signal Optimization
Auto-improves ensemble weights based on daily performance
"""

import json
import logging
import os
from datetime import datetime
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLSignalOptimization:
    """Machine learning based strategy weight optimization"""

    def __init__(self, db_path="ml_optimization.db"):
        self.db_path = db_path
        self.init_database()

        # Strategy weights (updated daily)
        self.strategy_weights = {
            "mean_reversion": 1.0,
            "momentum_continuation": 1.0,
            "support_resistance": 1.0,
            "volatility_breakout": 1.0,
            "institutional_patterns": 1.0,
            "order_flow": 1.0,
            "price_action": 1.0,
            "ml_ensemble": 1.0,
            "causal_inference": 1.0
        }

        self.min_weight = 0.5
        self.max_weight = 1.5
        self.learning_rate = 0.05

    def init_database(self):
        """Initialize optimization database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY,
                date TEXT,
                strategy TEXT,
                trades INTEGER,
                wins INTEGER,
                losses INTEGER,
                win_rate REAL,
                avg_profit REAL,
                total_profit REAL,
                weight REAL
            )
        ''')
        conn.commit()
        conn.close()

    def log_strategy_performance(self, date: str, strategy: str, performance: dict):
        """Log daily strategy performance"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO strategy_performance
            (date, strategy, trades, wins, losses, win_rate, avg_profit, total_profit, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date,
            strategy,
            performance.get('trades', 0),
            performance.get('wins', 0),
            performance.get('losses', 0),
            performance.get('win_rate', 0),
            performance.get('avg_profit', 0),
            performance.get('total_profit', 0),
            self.strategy_weights.get(strategy, 1.0)
        ))
        conn.commit()
        conn.close()

    def calculate_strategy_win_rate(self, trades: list, strategy: str) -> float:
        """Calculate win rate for specific strategy"""
        strategy_trades = [t for t in trades if t.get('strategy') == strategy]
        if not strategy_trades:
            return 50  # Default to 50% if no trades

        wins = sum(1 for t in strategy_trades if t.get('pnl', 0) > 0)
        return (wins / len(strategy_trades)) * 100

    def calculate_strategy_profit(self, trades: list, strategy: str) -> dict:
        """Calculate profit metrics for strategy"""
        strategy_trades = [t for t in trades if t.get('strategy') == strategy]

        if not strategy_trades:
            return {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 50, 'avg_profit': 0, 'total_profit': 0}

        wins = sum(1 for t in strategy_trades if t.get('pnl', 0) > 0)
        losses = len(strategy_trades) - wins
        total_profit = sum(t.get('pnl', 0) for t in strategy_trades)
        avg_profit = total_profit / len(strategy_trades)

        return {
            'trades': len(strategy_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(strategy_trades)) * 100,
            'avg_profit': avg_profit,
            'total_profit': total_profit
        }

    def optimize_weights(self, trades: list) -> dict:
        """Update weights based on today's performance"""
        logger.info("=" * 70)
        logger.info("ML SIGNAL OPTIMIZATION - UPDATING WEIGHTS")
        logger.info("=" * 70)

        old_weights = self.strategy_weights.copy()
        performance_map = {}

        for strategy in self.strategy_weights.keys():
            performance = self.calculate_strategy_profit(trades, strategy)
            performance_map[strategy] = performance

            win_rate = performance['win_rate']
            total_profit = performance['total_profit']

            # Calculate new weight based on performance
            if performance['trades'] > 0:
                # Win rate is primary factor
                win_rate_factor = win_rate / 50  # 50% = 1.0x, 80% = 1.6x, 40% = 0.8x

                # Profit is secondary factor
                profit_factor = 1.0 if total_profit >= 0 else (1.0 - abs(total_profit / 100))

                # Combine factors
                performance_score = (win_rate_factor * 0.7 + profit_factor * 0.3)

                # Adjust weight
                new_weight = self.strategy_weights[strategy] * (1 + self.learning_rate * (performance_score - 1))

                # Clamp between min and max
                new_weight = max(self.min_weight, min(self.max_weight, new_weight))

                self.strategy_weights[strategy] = new_weight

                change = ((new_weight - old_weights[strategy]) / old_weights[strategy]) * 100

                logger.info(f"\n{strategy.upper()}:")
                logger.info(f"  Trades: {performance['trades']}")
                logger.info(f"  Win Rate: {win_rate:.1f}%")
                logger.info(f"  Total Profit: ${total_profit:.2f}")
                logger.info(f"  Weight: {old_weights[strategy]:.2f} → {new_weight:.2f} ({change:+.1f}%)")

                # Log to database
                self.log_strategy_performance(
                    datetime.now().strftime('%Y-%m-%d'),
                    strategy,
                    performance
                )

        logger.info("\n" + "=" * 70)
        logger.info("WEIGHT UPDATE COMPLETE")
        logger.info("=" * 70 + "\n")

        return self.strategy_weights

    def get_current_weights(self) -> dict:
        """Get current strategy weights"""
        return self.strategy_weights

    def save_weights(self, filename="strategy_weights.json"):
        """Save weights to file"""
        with open(filename, 'w') as f:
            json.dump(self.strategy_weights, f, indent=2)
        logger.info(f"Weights saved to {filename}")

    def load_weights(self, filename="strategy_weights.json"):
        """Load weights from file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.strategy_weights = json.load(f)
            logger.info(f"Weights loaded from {filename}")

    def get_performance_report(self) -> dict:
        """Generate performance report by strategy"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM strategy_performance ORDER BY date DESC LIMIT 30')
        rows = c.fetchall()
        conn.close()

        report = {}
        for row in rows:
            strategy = row[2]
            if strategy not in report:
                report[strategy] = []
            report[strategy].append({
                'date': row[1],
                'trades': row[3],
                'win_rate': row[6],
                'total_profit': row[8],
                'weight': row[9]
            })

        return report


def main():
    """Test ML optimization"""
    optimizer = MLSignalOptimization()

    logger.info("Testing ML Signal Optimization...\n")

    # Simulate today's trades
    test_trades = [
        {"symbol": "NVDA", "strategy": "mean_reversion", "pnl": 1500, "confidence": 95},
        {"symbol": "APPS", "strategy": "support_resistance", "pnl": 150, "confidence": 90},
        {"symbol": "EHGO", "strategy": "momentum_continuation", "pnl": 250, "confidence": 85},
        {"symbol": "TEST1", "strategy": "mean_reversion", "pnl": 200, "confidence": 88},
        {"symbol": "TEST2", "strategy": "volatility_breakout", "pnl": -100, "confidence": 75},
        {"symbol": "TEST3", "strategy": "support_resistance", "pnl": 100, "confidence": 82},
    ]

    logger.info("Original weights:")
    for strategy, weight in optimizer.strategy_weights.items():
        logger.info(f"  {strategy}: {weight:.2f}")

    # Optimize based on today's trades
    new_weights = optimizer.optimize_weights(test_trades)

    logger.info("\nOptimized weights:")
    for strategy, weight in new_weights.items():
        logger.info(f"  {strategy}: {weight:.2f}")

    optimizer.save_weights()
    logger.info("\nOptimization test complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

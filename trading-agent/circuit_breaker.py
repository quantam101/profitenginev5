#!/usr/bin/env python3
"""
Automated Circuit Breaker System
Protects capital by pausing trading on bad days
"""

import json
import logging
import os
from datetime import datetime, timedelta
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Automatic trading pause on risk thresholds"""

    def __init__(self, db_path="circuit_breaker.db"):
        self.db_path = db_path
        self.init_database()

        # Risk thresholds
        self.daily_loss_limit = 200  # Pause if -$200 in one day
        self.weekly_loss_limit = 500  # Pause if -$500 in one week
        self.max_drawdown_limit = 30  # Pause if 30% drawdown
        self.min_win_rate_threshold = 50  # If <50% after 10 trades, require 95% confidence only
        self.consecutive_loss_limit = 5  # Pause if 5+ losses in a row

    def init_database(self):
        """Initialize circuit breaker database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS circuit_breaker_state (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                is_paused BOOLEAN,
                pause_reason TEXT,
                pause_until TEXT,
                daily_loss REAL,
                weekly_loss REAL,
                win_rate REAL,
                consecutive_losses INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def log_state(self, is_paused: bool, reason: str = "", daily_loss: float = 0,
                  weekly_loss: float = 0, win_rate: float = 0, consecutive_losses: int = 0):
        """Log circuit breaker state"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO circuit_breaker_state
            (timestamp, is_paused, pause_reason, daily_loss, weekly_loss, win_rate, consecutive_losses)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            is_paused,
            reason,
            daily_loss,
            weekly_loss,
            win_rate,
            consecutive_losses
        ))
        conn.commit()
        conn.close()

    def get_latest_state(self):
        """Get most recent state"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM circuit_breaker_state ORDER BY timestamp DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        return row

    def check_daily_loss(self, daily_pnl: float) -> bool:
        """Check daily loss threshold"""
        if daily_pnl <= -self.daily_loss_limit:
            logger.critical(f"CIRCUIT BREAKER: Daily loss limit hit (${daily_pnl:.2f})")
            return False  # PAUSE
        return True  # CONTINUE

    def check_weekly_loss(self, weekly_pnl: float) -> bool:
        """Check weekly loss threshold"""
        if weekly_pnl <= -self.weekly_loss_limit:
            logger.critical(f"CIRCUIT BREAKER: Weekly loss limit hit (${weekly_pnl:.2f})")
            return False  # PAUSE
        return True  # CONTINUE

    def check_win_rate(self, trades_count: int, win_rate: float) -> tuple:
        """Check win rate and recommend confidence adjustment"""
        if trades_count >= 10 and win_rate < self.min_win_rate_threshold:
            logger.warning(f"CIRCUIT BREAKER: Win rate below 50% ({win_rate:.1f}%)")
            logger.warning("ACTION: Raising confidence threshold to 95% only")
            return False, 95  # Require 95% confidence minimum

        return True, None  # Continue with normal thresholds

    def check_consecutive_losses(self, consecutive_losses: int) -> bool:
        """Check consecutive loss streak"""
        if consecutive_losses >= self.consecutive_loss_limit:
            logger.warning(f"CIRCUIT BREAKER: {consecutive_losses} consecutive losses")
            logger.warning("ACTION: Pause trading for review")
            return False  # PAUSE

        if consecutive_losses >= 3:
            logger.warning(f"WARNING: {consecutive_losses} consecutive losses")
            logger.warning("Consider tightening stops if this continues")

        return True  # CONTINUE

    def check_max_drawdown(self, current_drawdown: float, max_drawdown_pct: float) -> tuple:
        """Check drawdown and recommend scaling"""
        drawdown_pct = abs(max_drawdown_pct)

        if drawdown_pct > self.max_drawdown_limit:
            logger.critical(f"CIRCUIT BREAKER: Max drawdown {drawdown_pct:.1f}%")
            return False, 0.5  # Scale to 50% of normal positions

        if drawdown_pct > 20:
            logger.warning(f"WARNING: Drawdown at {drawdown_pct:.1f}%")
            return True, 0.75  # Scale to 75% of normal positions

        return True, 1.0  # Normal position sizing

    def evaluate_trading_day(self, metrics: dict) -> dict:
        """Full evaluation before trading day"""
        decision = {
            "should_trade": True,
            "reasons": [],
            "recommended_confidence": None,
            "position_scale": 1.0,
            "alerts": []
        }

        # Check daily loss
        daily_pnl = metrics.get('daily_pnl', 0)
        if not self.check_daily_loss(daily_pnl):
            decision["should_trade"] = False
            decision["reasons"].append(f"Daily loss limit hit: ${daily_pnl:.2f}")
            self.log_state(True, "daily_loss", daily_pnl)

        # Check weekly loss
        weekly_pnl = metrics.get('weekly_pnl', 0)
        if not self.check_weekly_loss(weekly_pnl):
            decision["should_trade"] = False
            decision["reasons"].append(f"Weekly loss limit hit: ${weekly_pnl:.2f}")
            self.log_state(True, "weekly_loss", weekly_loss=weekly_pnl)

        # Check win rate
        trades_count = metrics.get('trades_count', 0)
        win_rate = metrics.get('win_rate', 100)
        can_trade, min_confidence = self.check_win_rate(trades_count, win_rate)
        if not can_trade:
            decision["recommended_confidence"] = min_confidence
            decision["alerts"].append(f"Win rate low ({win_rate:.1f}%). Confidence raised to 95%")
            self.log_state(True, "low_win_rate", win_rate=win_rate)

        # Check consecutive losses
        consecutive_losses = metrics.get('consecutive_losses', 0)
        if not self.check_consecutive_losses(consecutive_losses):
            decision["should_trade"] = False
            decision["reasons"].append(f"{consecutive_losses} consecutive losses")
            self.log_state(True, "consecutive_losses", consecutive_losses=consecutive_losses)

        # Check drawdown
        max_drawdown = metrics.get('max_drawdown', 0)
        max_drawdown_pct = metrics.get('max_drawdown_pct', 0)
        can_scale, scale_factor = self.check_max_drawdown(max_drawdown, max_drawdown_pct)
        if scale_factor and scale_factor < 1.0:
            decision["position_scale"] = scale_factor
            decision["alerts"].append(f"Drawdown {abs(max_drawdown_pct):.1f}%. Scaling positions to {scale_factor*100:.0f}%")

        # Final decision log
        self.log_state(
            not decision["should_trade"],
            ", ".join(decision["reasons"]) if decision["reasons"] else "normal",
            daily_pnl,
            weekly_pnl,
            win_rate,
            consecutive_losses
        )

        return decision

    def generate_report(self) -> dict:
        """Generate circuit breaker activity report"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM circuit_breaker_state ORDER BY timestamp DESC LIMIT 30')
        rows = c.fetchall()
        conn.close()

        pauses = sum(1 for row in rows if row[2])  # is_paused column
        total_checks = len(rows)

        report = {
            "total_checks": total_checks,
            "circuit_breaks": pauses,
            "break_rate": (pauses / total_checks * 100) if total_checks > 0 else 0,
            "recent_activity": []
        }

        for row in rows[:10]:
            report["recent_activity"].append({
                "timestamp": row[1],
                "paused": row[2],
                "reason": row[3],
                "daily_loss": row[5],
                "weekly_loss": row[6],
                "win_rate": row[7]
            })

        return report


def main():
    """Test circuit breaker"""
    cb = CircuitBreaker()

    logger.info("=" * 70)
    logger.info("CIRCUIT BREAKER SYSTEM TEST")
    logger.info("=" * 70)

    # Test 1: Normal day
    logger.info("\nTest 1: Normal trading day")
    metrics = {
        'daily_pnl': 500,
        'weekly_pnl': 2000,
        'trades_count': 5,
        'win_rate': 80,
        'consecutive_losses': 0,
        'max_drawdown': 50,
        'max_drawdown_pct': 5
    }
    decision = cb.evaluate_trading_day(metrics)
    logger.info(f"Decision: {decision}")

    # Test 2: Bad win rate
    logger.info("\nTest 2: Low win rate (after 15 trades)")
    metrics = {
        'daily_pnl': 100,
        'weekly_pnl': 500,
        'trades_count': 15,
        'win_rate': 45,
        'consecutive_losses': 2,
        'max_drawdown': 100,
        'max_drawdown_pct': 8
    }
    decision = cb.evaluate_trading_day(metrics)
    logger.info(f"Decision: {decision}")

    # Test 3: Daily loss limit
    logger.info("\nTest 3: Daily loss limit hit")
    metrics = {
        'daily_pnl': -250,
        'weekly_pnl': -100,
        'trades_count': 8,
        'win_rate': 50,
        'consecutive_losses': 4,
        'max_drawdown': 250,
        'max_drawdown_pct': 15
    }
    decision = cb.evaluate_trading_day(metrics)
    logger.info(f"Decision: {decision}")

    # Test 4: High drawdown
    logger.info("\nTest 4: High drawdown (25%)")
    metrics = {
        'daily_pnl': -50,
        'weekly_pnl': 200,
        'trades_count': 12,
        'win_rate': 75,
        'consecutive_losses': 1,
        'max_drawdown': 500,
        'max_drawdown_pct': 25
    }
    decision = cb.evaluate_trading_day(metrics)
    logger.info(f"Decision: {decision}")

    logger.info("=" * 70)
    logger.info("Circuit breaker test complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

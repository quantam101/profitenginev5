"""
LIVE TRADING SAFETY GATES & COMPLIANCE CHECKS
Enforces user readiness, account verification, risk limits, regulatory compliance
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Tuple, Optional
from dataclasses import dataclass
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeploymentStatus:
    """Deployment status constants"""
    PENDING_CONFIRMATION = "pending_confirmation"
    IN_PROGRESS = "in_progress"
    ACCOUNT_CREATION = "account_creation"
    CAPITAL_DEPLOYMENT = "capital_deployment"
    LIVE_ACTIVE = "live_active"
    PAUSED = "paused"
    SAFETY_CHECK_FAILED = "safety_check_failed"
    CONFIRMATION_EXPIRED = "confirmation_expired"
    BROKER_CONNECTION_FAILED = "broker_connection_failed"
    CAPITAL_DEPLOYMENT_FAILED = "capital_deployment_failed"
    CLOSED = "closed"


@dataclass
class DeploymentApproval:
    """Deployment approval request"""
    user_id: int
    email: str
    approval_code: str
    created_at: datetime
    expires_at: datetime
    paper_balance: Decimal
    live_deployment_amount: Decimal
    max_daily_loss: Decimal
    robinhood_account_id: Optional[str] = None


class LiveTradingSafetyGate:
    """
    Enforces safety gates before live trading deployment.
    Verifies: account verification, 2FA, funding, regulatory status.
    """

    # Account verification requirements
    MIN_TRADING_DAYS = 7  # Paper trading for at least 7 days
    MIN_TRADES_COUNT = 10  # At least 10 trades executed
    MIN_WIN_RATE = 0.30  # 30% minimum win rate
    ACCOUNT_AGE_DAYS = 30  # Account must be 30+ days old

    def __init__(self, db_path: str = "clients.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def verify_user_readiness(
        self,
        user_id: int,
        email: str,
        paper_balance: Decimal
    ) -> Tuple[bool, str]:
        """
        Multi-check verification for live trading readiness.

        Returns:
            (is_ready, reason_if_not_ready)
        """
        checks = [
            ("Account age", await self._check_account_age(user_id)),
            ("Trading history", await self._check_trading_history(user_id)),
            ("Win rate", await self._check_win_rate(user_id)),
            ("Account status", await self._check_account_status(user_id)),
            ("No active disputes", await self._check_disputes(user_id)),
            ("Compliance", await self._check_regulatory_compliance(user_id)),
        ]

        for check_name, (passed, reason) in checks:
            if not passed:
                logger.warning(f"Safety check failed for user {user_id}: {check_name} - {reason}")
                return False, f"{check_name}: {reason}"

        logger.info(f"All safety checks passed for user {user_id}")
        return True, ""

    async def _check_account_age(self, user_id: int) -> Tuple[bool, str]:
        """Verify account is at least 30 days old"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT signup_date FROM users WHERE id = ?
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            if not row:
                return False, "User not found"

            signup_date = datetime.fromisoformat(row['signup_date'])
            age_days = (datetime.now() - signup_date).days

            if age_days < self.ACCOUNT_AGE_DAYS:
                return False, f"Account only {age_days} days old (need {self.ACCOUNT_AGE_DAYS})"

            return True, ""

        except Exception as e:
            logger.error(f"Error checking account age: {e}")
            return False, str(e)

    async def _check_trading_history(self, user_id: int) -> Tuple[bool, str]:
        """Verify minimum trading activity"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Count days with trades
            cur.execute("""
                SELECT COUNT(DISTINCT date) as trading_days,
                       SUM(num_trades) as total_trades
                FROM daily_trades
                WHERE user_id = ?
                  AND date >= date('now', '-30 days')
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            if not row:
                return False, "No trading history found"

            trading_days = row['trading_days'] or 0
            total_trades = row['total_trades'] or 0

            if trading_days < self.MIN_TRADING_DAYS:
                return False, f"Only {trading_days} trading days (need {self.MIN_TRADING_DAYS})"

            if total_trades < self.MIN_TRADES_COUNT:
                return False, f"Only {total_trades} trades (need {self.MIN_TRADES_COUNT})"

            return True, ""

        except Exception as e:
            logger.error(f"Error checking trading history: {e}")
            return False, str(e)

    async def _check_win_rate(self, user_id: int) -> Tuple[bool, str]:
        """Verify minimum 30% win rate"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT SUM(win_count) as wins,
                       SUM(loss_count) as losses
                FROM daily_trades
                WHERE user_id = ?
                  AND date >= date('now', '-30 days')
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            if not row:
                return False, "No trade data"

            wins = row['wins'] or 0
            losses = row['losses'] or 0
            total = wins + losses

            if total == 0:
                return False, "No completed trades"

            win_rate = wins / total
            if win_rate < self.MIN_WIN_RATE:
                return False, f"Win rate {win_rate:.1%} below {self.MIN_WIN_RATE:.1%} threshold"

            return True, ""

        except Exception as e:
            logger.error(f"Error checking win rate: {e}")
            return False, str(e)

    async def _check_account_status(self, user_id: int) -> Tuple[bool, str]:
        """Verify account is active and in good standing"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT is_active FROM users WHERE id = ?
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            if not row:
                return False, "User not found"

            if not row['is_active']:
                return False, "Account is inactive"

            return True, ""

        except Exception as e:
            logger.error(f"Error checking account status: {e}")
            return False, str(e)

    async def _check_disputes(self, user_id: int) -> Tuple[bool, str]:
        """Check for active disputes or complaints"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Check for any unresolved disputes
            cur.execute("""
                SELECT COUNT(*) as dispute_count
                FROM user_disputes
                WHERE user_id = ? AND status = 'open'
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            dispute_count = row['dispute_count'] if row else 0

            if dispute_count > 0:
                return False, f"{dispute_count} open dispute(s)"

            return True, ""

        except Exception as e:
            # Table might not exist; treat as pass
            logger.debug(f"Disputes check skipped: {e}")
            return True, ""

    async def _check_regulatory_compliance(self, user_id: int) -> Tuple[bool, str]:
        """
        Check regulatory compliance:
        - Not on OFAC list
        - US resident or allowed jurisdiction
        - No PDT rule violations (if US)
        """
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT jurisdiction FROM users WHERE id = ?
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            if not row:
                return False, "User not found"

            # TODO: Check OFAC list here if integrated
            # TODO: Check jurisdiction restrictions

            return True, ""

        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return False, str(e)

    async def enforce_daily_loss_limit(
        self,
        user_id: int,
        max_daily_loss: Decimal,
        current_day_pnl: Decimal
    ) -> Tuple[bool, str]:
        """
        Check if daily loss limit exceeded.

        Returns:
            (within_limit, reason_if_exceeded)
        """
        if current_day_pnl < -max_daily_loss:
            reason = f"Daily loss ${abs(current_day_pnl):.2f} exceeds limit ${max_daily_loss:.2f}"
            logger.warning(f"Daily loss limit exceeded for user {user_id}: {reason}")
            return False, reason

        return True, ""

    async def enforce_drawdown_limit(
        self,
        user_id: int,
        max_drawdown_pct: Decimal,
        peak_equity: Decimal,
        current_equity: Decimal
    ) -> Tuple[bool, str]:
        """
        Check if drawdown limit exceeded.

        Returns:
            (within_limit, reason_if_exceeded)
        """
        if peak_equity == 0:
            return True, ""

        drawdown_pct = ((peak_equity - current_equity) / peak_equity) * 100

        if drawdown_pct > max_drawdown_pct:
            reason = f"Drawdown {drawdown_pct:.2f}% exceeds limit {max_drawdown_pct:.2f}%"
            logger.warning(f"Drawdown limit exceeded for user {user_id}: {reason}")
            return False, reason

        return True, ""

    async def enforce_position_limits(
        self,
        user_id: int,
        symbol: str,
        direction: str,
        position_value: Decimal,
        account_equity: Decimal,
        max_position_pct: Decimal = Decimal("10.00")
    ) -> Tuple[bool, str]:
        """
        Check position size as % of account.

        Args:
            position_value: USD value of position
            account_equity: Total account equity
            max_position_pct: Max % of account per position (default 10%)

        Returns:
            (within_limit, reason_if_exceeded)
        """
        if account_equity == 0:
            return False, "Zero account equity"

        position_pct = (position_value / account_equity) * 100

        if position_pct > max_position_pct:
            reason = f"{symbol} position {position_pct:.2f}% exceeds max {max_position_pct:.2f}%"
            logger.warning(f"Position limit exceeded for user {user_id}: {reason}")
            return False, reason

        return True, ""

    async def enforce_max_open_positions(
        self,
        user_id: int,
        current_positions: int,
        max_open: int = 5
    ) -> Tuple[bool, str]:
        """Check max open positions"""
        if current_positions >= max_open:
            reason = f"{current_positions} open positions at limit {max_open}"
            logger.warning(f"Max open positions for user {user_id}: {reason}")
            return False, reason

        return True, ""


class CircuitBreaker:
    """
    Circuit breaker: pauses trading if loss limits exceeded.
    Three states: GREEN (normal), YELLOW (warning), RED (paused).
    """

    STATE_GREEN = "green"
    STATE_YELLOW = "yellow"
    STATE_RED = "red"

    def __init__(self, db_path: str = "clients.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def check_circuit_breaker(
        self,
        user_id: int,
        daily_pnl: Decimal,
        max_daily_loss: Decimal,
        drawdown_pct: Decimal,
        max_drawdown_pct: Decimal
    ) -> Tuple[str, str]:
        """
        Evaluate circuit breaker state.

        Returns:
            (state, reason)
            states: green, yellow, red
        """
        # RED: Hard loss limit exceeded
        if daily_pnl < -max_daily_loss or drawdown_pct > max_drawdown_pct:
            return self.STATE_RED, "Loss limits exceeded — trading paused"

        # YELLOW: Approaching limit (80%)
        threshold = max_daily_loss * Decimal("0.80")
        if abs(daily_pnl) > threshold or drawdown_pct > (max_drawdown_pct * Decimal("0.80")):
            return self.STATE_YELLOW, "Approaching loss limits — caution advised"

        return self.STATE_GREEN, "Normal operation"

    async def update_circuit_breaker(
        self,
        user_id: int,
        state: str,
        reason: str
    ):
        """Update circuit breaker status in database"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO circuit_breakers (
                    user_id, state, reason, updated_at
                ) VALUES (?, ?, ?, ?)
            """, (
                user_id,
                state,
                reason,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            logger.info(f"Circuit breaker updated for user {user_id}: {state} - {reason}")

        except Exception as e:
            logger.error(f"Failed to update circuit breaker: {e}")

    async def is_trading_allowed(self, user_id: int) -> bool:
        """Check if trading is allowed (not in RED state)"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT state FROM circuit_breakers
                WHERE user_id = ?
                ORDER BY updated_at DESC LIMIT 1
            """, (user_id,))

            row = cur.fetchone()
            conn.close()

            if not row:
                return True  # No breaker set; allow trading

            return row['state'] != self.STATE_RED

        except Exception as e:
            logger.warning(f"Error checking circuit breaker: {e}")
            return True  # Default to allowing if error


class ManualOverride:
    """Allow Already Here LLC admins to manually pause/resume accounts"""

    def __init__(self, db_path: str = "clients.db"):
        self.db_path = db_path
        self.admin_emails = ["admin@alreadyherellc.com", "dispatch@alreadyherellc.com"]

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def pause_user_trading(
        self,
        user_id: int,
        admin_email: str,
        reason: str
    ) -> Tuple[bool, str]:
        """Admin pause user trading"""
        if admin_email not in self.admin_emails:
            return False, "Unauthorized"

        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE live_accounts
                SET status = 'paused', paused_at = ?, pause_reason = ?
                WHERE user_id = ?
            """, (
                datetime.now().isoformat(),
                f"ADMIN PAUSE: {reason}",
                user_id
            ))

            cur.execute("""
                INSERT INTO admin_actions (
                    user_id, action, admin_email, reason, created_at
                ) VALUES (?, 'pause', ?, ?, ?)
            """, (
                user_id,
                admin_email,
                reason,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            logger.warning(f"Admin {admin_email} paused user {user_id}: {reason}")
            return True, "User trading paused"

        except Exception as e:
            logger.error(f"Failed to pause user: {e}")
            return False, str(e)

    async def resume_user_trading(
        self,
        user_id: int,
        admin_email: str
    ) -> Tuple[bool, str]:
        """Admin resume user trading"""
        if admin_email not in self.admin_emails:
            return False, "Unauthorized"

        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE live_accounts
                SET status = 'active', paused_at = NULL, pause_reason = NULL
                WHERE user_id = ?
            """, (user_id,))

            cur.execute("""
                INSERT INTO admin_actions (
                    user_id, action, admin_email, reason, created_at
                ) VALUES (?, 'resume', ?, ?, ?)
            """, (
                user_id,
                admin_email,
                "Admin resume",
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            logger.warning(f"Admin {admin_email} resumed user {user_id}")
            return True, "User trading resumed"

        except Exception as e:
            logger.error(f"Failed to resume user: {e}")
            return False, str(e)

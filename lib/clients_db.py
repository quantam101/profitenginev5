"""
Client tracking database helper module for ProfitEngine v5

Provides high-level functions for:
- Managing user accounts and trading tiers
- Recording and querying daily trading metrics
- Tracking upsell opportunities and revenue progression

Usage:
    from lib.clients_db import ClientsDB

    db = ClientsDB()

    # Create user
    user = db.create_user("alice@example.com", "pro")

    # Record daily trades
    db.record_daily_trades(user_id=1, date="2026-06-18", num_trades=10, ...)

    # Query analytics
    stats = db.get_user_stats(user_id=1, days=30)
    tier_breakdown = db.get_tier_breakdown()
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class User:
    """Represents a user record."""
    id: int
    email: str
    signup_date: str
    first_trade_date: Optional[str]
    trading_tier: str
    created_at: str
    updated_at: str
    last_active_at: Optional[str]
    is_active: bool


@dataclass
class DailyTrade:
    """Represents a daily trading record."""
    id: int
    user_id: int
    date: str
    num_trades: int
    win_count: int
    loss_count: int
    pnl_dollars: float
    pnl_percent: float
    balance: float
    win_rate: float
    created_at: str
    updated_at: str


@dataclass
class UpsellTracking:
    """Represents upsell tracking data."""
    id: int
    user_id: int
    tier_history: List[Dict[str, str]]
    current_tier: str
    revenue_tier: str
    last_upsell_offered: Optional[str]
    upsell_count: int
    conversion_count: int
    lifetime_revenue: float
    created_at: str
    updated_at: str


class ClientsDB:
    """Main database interface for client tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        if db_path is None:
            # Default to project root/clients.db
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            db_path = project_root / "clients.db"

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                "Run: python scripts/init-clients-db.py"
            )

    @contextmanager
    def _get_conn(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ===== USER OPERATIONS =====

    def create_user(
        self,
        email: str,
        trading_tier: str = "free",
        signup_date: Optional[str] = None
    ) -> User:
        """
        Create a new user account.

        Args:
            email: User email address
            trading_tier: Initial tier ('free', 'basic', 'pro', 'elite')
            signup_date: ISO 8601 date string (defaults to today)

        Returns:
            User object with assigned ID
        """
        if signup_date is None:
            signup_date = datetime.now().strftime("%Y-%m-%d")

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, signup_date, trading_tier)
                VALUES (?, ?, ?)
                """,
                (email, signup_date, trading_tier)
            )
            conn.commit()
            user_id = cursor.lastrowid

        return self.get_user(user_id)

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return User(**dict(row))
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return User(**dict(row))
            return None

    def update_user_tier(self, user_id: int, new_tier: str) -> User:
        """Update user's trading tier."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET trading_tier = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_tier, user_id)
            )
            conn.commit()

        return self.get_user(user_id)

    def update_user_activity(self, user_id: int) -> User:
        """Update last_active_at timestamp."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET last_active_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id,)
            )
            conn.commit()

        return self.get_user(user_id)

    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id,)
            )
            conn.commit()

        return self.get_user(user_id)

    def list_users(
        self,
        tier: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100
    ) -> List[User]:
        """
        List users with optional filtering.

        Args:
            tier: Filter by trading tier ('free', 'basic', 'pro', 'elite')
            active_only: Only return active users
            limit: Maximum number of results

        Returns:
            List of User objects
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM users WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = 1"

            if tier:
                query += " AND trading_tier = ?"
                params.append(tier)

            query += " ORDER BY signup_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [User(**dict(row)) for row in cursor.fetchall()]

    # ===== DAILY TRADES OPERATIONS =====

    def record_daily_trades(
        self,
        user_id: int,
        date: str,
        num_trades: int,
        win_count: int,
        loss_count: int,
        pnl_dollars: float,
        pnl_percent: float,
        balance: float
    ) -> DailyTrade:
        """
        Record daily trading metrics for a user.

        Args:
            user_id: User ID
            date: Trade date in ISO 8601 format (YYYY-MM-DD)
            num_trades: Total number of trades
            win_count: Number of winning trades
            loss_count: Number of losing trades
            pnl_dollars: Profit/loss in dollars
            pnl_percent: Profit/loss percentage
            balance: Account balance after trading

        Returns:
            DailyTrade object
        """
        # Calculate win_rate
        win_rate = (win_count / (win_count + loss_count) * 100) \
            if (win_count + loss_count) > 0 else 0.0

        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Use INSERT OR REPLACE to handle updates
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_trades
                (user_id, date, num_trades, win_count, loss_count, pnl_dollars, pnl_percent, balance, win_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, date, num_trades, win_count, loss_count, pnl_dollars, pnl_percent, balance, win_rate)
            )
            conn.commit()

        # Update user's first_trade_date if not set
        user = self.get_user(user_id)
        if user and user.first_trade_date is None:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET first_trade_date = ? WHERE id = ?",
                    (date, user_id)
                )
                conn.commit()

        return self.get_daily_trades(user_id, date)

    def get_daily_trades(self, user_id: int, date: str) -> Optional[DailyTrade]:
        """Get daily trades for a specific date."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM daily_trades WHERE user_id = ? AND date = ?",
                (user_id, date)
            )
            row = cursor.fetchone()
            if row:
                return DailyTrade(**dict(row))
            return None

    def get_user_trading_history(
        self,
        user_id: int,
        days: int = 30,
        start_date: Optional[str] = None
    ) -> List[DailyTrade]:
        """
        Get user's trading history for past N days.

        Args:
            user_id: User ID
            days: Number of days to look back
            start_date: Optional specific start date (ISO 8601)

        Returns:
            List of DailyTrade objects
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM daily_trades
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
                """,
                (user_id, start_date)
            )
            return [DailyTrade(**dict(row)) for row in cursor.fetchall()]

    # ===== ANALYTICS OPERATIONS =====

    def get_user_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated trading statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to aggregate over

        Returns:
            Dictionary with stats (total_trades, avg_win_rate, total_pnl, etc.)
        """
        history = self.get_user_trading_history(user_id, days)

        if not history:
            return {
                "user_id": user_id,
                "days_analyzed": days,
                "has_trades": False,
                "total_trades": 0,
                "total_wins": 0,
                "total_losses": 0,
                "avg_win_rate": 0.0,
                "total_pnl_dollars": 0.0,
                "total_pnl_percent": 0.0,
                "avg_daily_pnl": 0.0,
                "best_day": None,
                "worst_day": None,
                "current_balance": 0.0,
            }

        total_trades = sum(t.num_trades for t in history)
        total_wins = sum(t.win_count for t in history)
        total_losses = sum(t.loss_count for t in history)
        total_pnl = sum(t.pnl_dollars for t in history)
        avg_pnl_percent = sum(t.pnl_percent for t in history) / len(history) if history else 0.0

        avg_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0
        avg_daily_pnl = total_pnl / len(history) if history else 0.0

        best_day = max(history, key=lambda x: x.pnl_dollars) if history else None
        worst_day = min(history, key=lambda x: x.pnl_dollars) if history else None

        return {
            "user_id": user_id,
            "days_analyzed": days,
            "has_trades": len(history) > 0,
            "total_trades": total_trades,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "avg_win_rate": round(avg_win_rate, 2),
            "total_pnl_dollars": round(total_pnl, 2),
            "total_pnl_percent": round(avg_pnl_percent, 2),
            "avg_daily_pnl": round(avg_daily_pnl, 2),
            "best_day": {
                "date": best_day.date,
                "pnl": best_day.pnl_dollars
            } if best_day else None,
            "worst_day": {
                "date": worst_day.date,
                "pnl": worst_day.pnl_dollars
            } if worst_day else None,
            "current_balance": history[0].balance if history else 0.0,
        }

    def get_tier_breakdown(self) -> Dict[str, int]:
        """Get count of users by trading tier."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT trading_tier, COUNT(*) as count
                FROM users
                WHERE is_active = 1
                GROUP BY trading_tier
                ORDER BY count DESC
                """
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_top_performers(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing users by PnL percentage."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.email, u.trading_tier,
                       SUM(d.pnl_dollars) as total_pnl,
                       AVG(d.win_rate) as avg_win_rate,
                       COUNT(d.id) as trade_days
                FROM users u
                LEFT JOIN daily_trades d ON u.id = d.user_id
                WHERE u.is_active = 1 AND d.date >= date('now', '-' || ? || ' days')
                GROUP BY u.id
                ORDER BY total_pnl DESC
                LIMIT ?
                """,
                (days, limit)
            )
            results = []
            for row in cursor.fetchall():
                results.append({
                    "user_id": row[0],
                    "email": row[1],
                    "tier": row[2],
                    "total_pnl": row[3] or 0.0,
                    "avg_win_rate": row[4] or 0.0,
                    "trade_days": row[5] or 0,
                })
            return results

    # ===== UPSELL OPERATIONS =====

    def create_upsell_tracking(self, user_id: int) -> UpsellTracking:
        """Create upsell tracking record for a user."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO upsell_tracking (user_id, tier_history)
                VALUES (?, ?)
                """,
                (user_id, json.dumps([]))
            )
            conn.commit()

        return self.get_upsell_tracking(user_id)

    def get_upsell_tracking(self, user_id: int) -> Optional[UpsellTracking]:
        """Get upsell tracking for a user."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM upsell_tracking WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data["tier_history"] = json.loads(data["tier_history"])
                return UpsellTracking(**data)
            return None

    def record_upsell_offer(
        self,
        user_id: int,
        tier: str,
        conversion: bool = False
    ) -> UpsellTracking:
        """
        Record an upsell offer to a user.

        Args:
            user_id: User ID
            tier: Tier being offered ('basic', 'pro', 'elite')
            conversion: Whether user converted to this tier
        """
        tracking = self.get_upsell_tracking(user_id)
        if not tracking:
            tracking = self.create_upsell_tracking(user_id)

        # Update tier_history
        tier_history = tracking.tier_history or []
        tier_history.append({
            "tier": tier,
            "date": datetime.now().isoformat(),
            "source": "upsell_offer"
        })

        # Update conversion count if applicable
        conversion_count = tracking.conversion_count
        if conversion:
            conversion_count += 1

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE upsell_tracking
                SET tier_history = ?,
                    last_upsell_offered = CURRENT_TIMESTAMP,
                    upsell_count = upsell_count + 1,
                    conversion_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (json.dumps(tier_history), conversion_count, user_id)
            )
            conn.commit()

        return self.get_upsell_tracking(user_id)

    def update_revenue_tier(self, user_id: int, revenue_tier: str, amount: float) -> UpsellTracking:
        """
        Update user's revenue tier and lifetime revenue.

        Args:
            user_id: User ID
            revenue_tier: Revenue tier ('none', 'trial', 'paid-basic', 'paid-pro', 'paid-elite')
            amount: Revenue amount to add
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE upsell_tracking
                SET revenue_tier = ?,
                    lifetime_revenue = lifetime_revenue + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (revenue_tier, amount, user_id)
            )
            conn.commit()

        return self.get_upsell_tracking(user_id)

    def get_revenue_summary(self) -> Dict[str, Any]:
        """Get summary of revenue by tier."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT revenue_tier, COUNT(*) as user_count, SUM(lifetime_revenue) as total_revenue
                FROM upsell_tracking
                GROUP BY revenue_tier
                ORDER BY total_revenue DESC
                """
            )
            results = {}
            for row in cursor.fetchall():
                results[row[0]] = {
                    "user_count": row[1],
                    "total_revenue": row[2] or 0.0,
                }
            return results

    def get_upsell_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get users who are candidates for upselling (not yet premium)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.email, u.trading_tier,
                       AVG(d.win_rate) as avg_win_rate,
                       SUM(d.pnl_dollars) as total_pnl,
                       COUNT(DISTINCT d.date) as trade_days
                FROM users u
                LEFT JOIN upsell_tracking ut ON u.id = ut.user_id
                LEFT JOIN daily_trades d ON u.id = d.user_id AND d.date >= date('now', '-30 days')
                WHERE u.is_active = 1 AND (ut.revenue_tier = 'none' OR ut.revenue_tier = 'trial')
                GROUP BY u.id
                ORDER BY total_pnl DESC
                LIMIT ?
                """,
                (limit,)
            )
            results = []
            for row in cursor.fetchall():
                results.append({
                    "user_id": row[0],
                    "email": row[1],
                    "tier": row[2],
                    "avg_win_rate": row[3] or 0.0,
                    "total_pnl_30d": row[4] or 0.0,
                    "trade_days_30d": row[5] or 0,
                })
            return results

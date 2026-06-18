"""
Unit tests for client tracking database (clients_db.py)

Run with: python -m pytest tests/test_clients_db.py -v
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from lib.clients_db import ClientsDB, User, DailyTrade, UpsellTracking


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create database with schema
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Create tables (inline to avoid import issues)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                signup_date TEXT NOT NULL,
                first_trade_date TEXT,
                trading_tier TEXT NOT NULL DEFAULT 'free',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_active_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Daily trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                num_trades INTEGER NOT NULL DEFAULT 0,
                win_count INTEGER NOT NULL DEFAULT 0,
                loss_count INTEGER NOT NULL DEFAULT 0,
                pnl_dollars REAL NOT NULL DEFAULT 0.0,
                pnl_percent REAL NOT NULL DEFAULT 0.0,
                balance REAL NOT NULL DEFAULT 0.0,
                win_rate REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, date)
            )
        """)

        # Upsell tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upsell_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                tier_history TEXT NOT NULL DEFAULT '[]',
                current_tier TEXT NOT NULL DEFAULT 'free',
                revenue_tier TEXT NOT NULL DEFAULT 'none',
                last_upsell_offered TEXT,
                upsell_count INTEGER NOT NULL DEFAULT 0,
                conversion_count INTEGER NOT NULL DEFAULT 0,
                lifetime_revenue REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

        db = ClientsDB(str(db_path))
        yield db


class TestUserOperations:
    """Test user management functions."""

    def test_create_user(self, temp_db):
        """Test creating a new user."""
        user = temp_db.create_user("test@example.com", "pro")

        assert user.email == "test@example.com"
        assert user.trading_tier == "pro"
        assert user.is_active == 1
        assert user.first_trade_date is None

    def test_get_user_by_id(self, temp_db):
        """Test retrieving user by ID."""
        created = temp_db.create_user("test@example.com", "basic")
        retrieved = temp_db.get_user(created.id)

        assert retrieved is not None
        assert retrieved.email == "test@example.com"
        assert retrieved.id == created.id

    def test_get_user_by_email(self, temp_db):
        """Test retrieving user by email."""
        created = temp_db.create_user("alice@example.com", "pro")
        retrieved = temp_db.get_user_by_email("alice@example.com")

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_update_user_tier(self, temp_db):
        """Test updating user tier."""
        user = temp_db.create_user("test@example.com")
        assert user.trading_tier == "free"

        updated = temp_db.update_user_tier(user.id, "elite")
        assert updated.trading_tier == "elite"

    def test_duplicate_user_email(self, temp_db):
        """Test that duplicate emails are rejected."""
        temp_db.create_user("test@example.com")

        # Attempting to create duplicate should raise IntegrityError
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.create_user("test@example.com")

    def test_list_users(self, temp_db):
        """Test listing users with filtering."""
        temp_db.create_user("user1@example.com", "free")
        temp_db.create_user("user2@example.com", "pro")
        temp_db.create_user("user3@example.com", "free")

        all_users = temp_db.list_users()
        assert len(all_users) == 3

        free_users = temp_db.list_users(tier="free")
        assert len(free_users) == 2
        assert all(u.trading_tier == "free" for u in free_users)

    def test_deactivate_user(self, temp_db):
        """Test deactivating a user."""
        user = temp_db.create_user("test@example.com")
        assert user.is_active == 1

        deactivated = temp_db.deactivate_user(user.id)
        assert deactivated.is_active == 0


class TestDailyTradesOperations:
    """Test daily trading metrics functions."""

    def test_record_daily_trades(self, temp_db):
        """Test recording daily trades."""
        user = temp_db.create_user("test@example.com")

        trade = temp_db.record_daily_trades(
            user_id=user.id,
            date="2026-06-18",
            num_trades=10,
            win_count=7,
            loss_count=3,
            pnl_dollars=500.00,
            pnl_percent=5.0,
            balance=10500.00
        )

        assert trade.user_id == user.id
        assert trade.num_trades == 10
        assert trade.win_rate == 70.0
        assert trade.pnl_dollars == 500.00

    def test_get_daily_trades(self, temp_db):
        """Test retrieving daily trades."""
        user = temp_db.create_user("test@example.com")

        temp_db.record_daily_trades(
            user_id=user.id,
            date="2026-06-18",
            num_trades=5,
            win_count=4,
            loss_count=1,
            pnl_dollars=200.00,
            pnl_percent=2.0,
            balance=10200.00
        )

        trade = temp_db.get_daily_trades(user.id, "2026-06-18")
        assert trade is not None
        assert trade.num_trades == 5

    def test_update_daily_trades(self, temp_db):
        """Test updating daily trades (INSERT OR REPLACE)."""
        user = temp_db.create_user("test@example.com")

        # Record first time
        temp_db.record_daily_trades(
            user_id=user.id,
            date="2026-06-18",
            num_trades=5,
            win_count=3,
            loss_count=2,
            pnl_dollars=150.00,
            pnl_percent=1.5,
            balance=10150.00
        )

        # Update same date
        updated = temp_db.record_daily_trades(
            user_id=user.id,
            date="2026-06-18",
            num_trades=8,
            win_count=6,
            loss_count=2,
            pnl_dollars=300.00,
            pnl_percent=3.0,
            balance=10300.00
        )

        assert updated.num_trades == 8
        assert updated.pnl_dollars == 300.00

    def test_get_user_trading_history(self, temp_db):
        """Test retrieving user trading history."""
        user = temp_db.create_user("test@example.com")

        # Record trades for 5 days
        for i in range(5):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            temp_db.record_daily_trades(
                user_id=user.id,
                date=date,
                num_trades=10,
                win_count=7,
                loss_count=3,
                pnl_dollars=100.00 * (i + 1),
                pnl_percent=1.0 * (i + 1),
                balance=10000.00 + (100.00 * (i + 1))
            )

        history = temp_db.get_user_trading_history(user.id, days=30)
        assert len(history) == 5

    def test_first_trade_date_auto_update(self, temp_db):
        """Test that first_trade_date is set on first trade."""
        user = temp_db.create_user("test@example.com")
        assert user.first_trade_date is None

        temp_db.record_daily_trades(
            user_id=user.id,
            date="2026-06-18",
            num_trades=1,
            win_count=1,
            loss_count=0,
            pnl_dollars=50.00,
            pnl_percent=0.5,
            balance=10050.00
        )

        updated = temp_db.get_user(user.id)
        assert updated.first_trade_date == "2026-06-18"


class TestAnalyticsOperations:
    """Test analytics and reporting functions."""

    def test_get_user_stats(self, temp_db):
        """Test getting user statistics."""
        user = temp_db.create_user("test@example.com")

        # Record 10 days of trades
        for i in range(10):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            temp_db.record_daily_trades(
                user_id=user.id,
                date=date,
                num_trades=10,
                win_count=7,
                loss_count=3,
                pnl_dollars=100.00,
                pnl_percent=1.0,
                balance=10000.00 + (100.00 * i)
            )

        stats = temp_db.get_user_stats(user.id, days=30)

        assert stats['has_trades'] is True
        assert stats['total_trades'] == 100
        assert stats['total_wins'] == 70
        assert stats['total_losses'] == 30
        assert stats['avg_win_rate'] == 70.0
        assert stats['total_pnl_dollars'] == 1000.0
        assert stats['current_balance'] == 10900.0

    def test_get_tier_breakdown(self, temp_db):
        """Test getting tier breakdown."""
        temp_db.create_user("user1@example.com", "free")
        temp_db.create_user("user2@example.com", "free")
        temp_db.create_user("user3@example.com", "pro")
        temp_db.create_user("user4@example.com", "elite")

        breakdown = temp_db.get_tier_breakdown()

        assert breakdown['free'] == 2
        assert breakdown['pro'] == 1
        assert breakdown['elite'] == 1

    def test_get_top_performers(self, temp_db):
        """Test getting top performers."""
        # Create users with different performance levels
        for tier_idx in range(3):
            user = temp_db.create_user(f"user{tier_idx}@example.com", "pro")

            # Record trades (vary the P&L)
            for i in range(5):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                temp_db.record_daily_trades(
                    user_id=user.id,
                    date=date,
                    num_trades=10,
                    win_count=7,
                    loss_count=3,
                    pnl_dollars=100.00 * (tier_idx + 1),  # Vary by user
                    pnl_percent=1.0,
                    balance=10000.00
                )

        top = temp_db.get_top_performers(days=30, limit=10)

        # Should return 3 users sorted by total P&L
        assert len(top) == 3
        assert top[0]['total_pnl'] >= top[1]['total_pnl']


class TestUpsellOperations:
    """Test upsell tracking functions."""

    def test_record_upsell_offer(self, temp_db):
        """Test recording upsell offer."""
        user = temp_db.create_user("test@example.com", "free")

        tracking = temp_db.record_upsell_offer(user.id, "pro", conversion=False)

        assert tracking.user_id == user.id
        assert tracking.upsell_count == 1
        assert tracking.conversion_count == 0
        assert len(tracking.tier_history) == 1

    def test_record_upsell_with_conversion(self, temp_db):
        """Test recording successful upsell conversion."""
        user = temp_db.create_user("test@example.com", "free")

        tracking = temp_db.record_upsell_offer(user.id, "pro", conversion=True)

        assert tracking.upsell_count == 1
        assert tracking.conversion_count == 1

    def test_update_revenue_tier(self, temp_db):
        """Test updating revenue tier and tracking."""
        user = temp_db.create_user("test@example.com", "free")

        tracking = temp_db.update_revenue_tier(user.id, "paid-pro", 49.99)

        assert tracking.revenue_tier == "paid-pro"
        assert tracking.lifetime_revenue == 49.99

    def test_get_revenue_summary(self, temp_db):
        """Test getting revenue summary."""
        user1 = temp_db.create_user("user1@example.com")
        user2 = temp_db.create_user("user2@example.com")
        user3 = temp_db.create_user("user3@example.com")

        temp_db.update_revenue_tier(user1.id, "paid-basic", 19.99)
        temp_db.update_revenue_tier(user2.id, "paid-pro", 49.99)
        temp_db.update_revenue_tier(user2.id, "paid-pro", 49.99)  # Add again

        summary = temp_db.get_revenue_summary()

        assert summary['none']['user_count'] == 1
        assert summary['paid-basic']['user_count'] == 1
        assert summary['paid-basic']['total_revenue'] == 19.99
        assert summary['paid-pro']['total_revenue'] == 99.98

    def test_get_upsell_candidates(self, temp_db):
        """Test getting upsell candidates."""
        # Create free user with high P&L
        user1 = temp_db.create_user("high_performer@example.com", "free")
        for i in range(5):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            temp_db.record_daily_trades(
                user_id=user1.id,
                date=date,
                num_trades=10,
                win_count=8,
                loss_count=2,
                pnl_dollars=500.00,
                pnl_percent=5.0,
                balance=10000.00
            )

        # Create paid user (not a candidate)
        user2 = temp_db.create_user("paid_user@example.com", "pro")
        temp_db.update_revenue_tier(user2.id, "paid-pro", 49.99)

        candidates = temp_db.get_upsell_candidates(limit=10)

        # Should only return the free user (not the paid one)
        assert len(candidates) >= 1
        assert any(c['user_id'] == user1.id for c in candidates)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

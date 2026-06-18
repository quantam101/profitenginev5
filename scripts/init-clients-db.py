#!/usr/bin/env python3
"""
Client tracking database initialization script for ProfitEngine v5

Creates a lightweight SQLite database for tracking:
- User accounts and trading tiers
- Daily trading activity and performance metrics
- Upsell opportunities and revenue tier progression

Usage:
  python scripts/init-clients-db.py [--seed] [--reset]
  python scripts/init-clients-db.py --seed  # Initialize with sample data
  python scripts/init-clients-db.py --reset  # Drop existing db and recreate

Output:
  clients.db (SQLite database at project root)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json


def get_db_path():
    """Get the path to clients.db at project root."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root / "clients.db"


def init_schema(conn: sqlite3.Connection):
    """Initialize the database schema with all tables and indexes."""
    cursor = conn.cursor()

    # ===== USERS TABLE =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            signup_date TEXT NOT NULL,  -- ISO 8601 format
            first_trade_date TEXT,       -- ISO 8601 format (NULL if not traded yet)
            trading_tier TEXT NOT NULL DEFAULT 'free',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_active_at TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Index for email lookups (most common query)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    """)

    # Index for tier and active status (for segmentation)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_tier_active
        ON users(trading_tier, is_active)
    """)

    # Index for recent signups (for cohort analysis)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_signup_date
        ON users(signup_date DESC)
    """)

    # ===== DAILY_TRADES TABLE =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,  -- ISO 8601 format (YYYY-MM-DD)
            num_trades INTEGER NOT NULL DEFAULT 0,
            win_count INTEGER NOT NULL DEFAULT 0,
            loss_count INTEGER NOT NULL DEFAULT 0,
            pnl_dollars REAL NOT NULL DEFAULT 0.0,
            pnl_percent REAL NOT NULL DEFAULT 0.0,
            balance REAL NOT NULL DEFAULT 0.0,
            win_rate REAL NOT NULL DEFAULT 0.0,  -- Cached for quick access: win_count / (win_count + loss_count)
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, date)
        )
    """)

    # Index for user's daily history (fastest common query)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_trades_user_date
        ON daily_trades(user_id, date DESC)
    """)

    # Index for date-based aggregations (portfolio-wide queries)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_trades_date
        ON daily_trades(date DESC)
    """)

    # Index for high performers (leaderboard queries)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_trades_performance
        ON daily_trades(pnl_percent DESC, pnl_dollars DESC)
    """)

    # ===== UPSELL_TRACKING TABLE =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upsell_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            tier_history TEXT NOT NULL DEFAULT '[]',  -- JSON array of {tier, date, source}
            current_tier TEXT NOT NULL DEFAULT 'free',
            revenue_tier TEXT NOT NULL DEFAULT 'none',  -- 'none', 'trial', 'paid-basic', 'paid-pro', 'paid-elite'
            last_upsell_offered TEXT,  -- ISO 8601 timestamp
            upsell_count INTEGER NOT NULL DEFAULT 0,
            conversion_count INTEGER NOT NULL DEFAULT 0,
            lifetime_revenue REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Index for revenue tracking
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_upsell_revenue_tier
        ON upsell_tracking(revenue_tier, lifetime_revenue DESC)
    """)

    # Index for upsell candidates (users not yet in premium tiers)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_upsell_candidates
        ON upsell_tracking(user_id)
        WHERE revenue_tier = 'none' OR revenue_tier = 'trial'
    """)

    conn.commit()
    return True


def verify_schema(conn: sqlite3.Connection):
    """Verify that all tables exist."""
    cursor = conn.cursor()

    # Check tables
    tables = ['users', 'daily_trades', 'upsell_tracking']
    for table in tables:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            return False, f"Table '{table}' not found"

    # Check indexes
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
    count = cursor.fetchone()[0]
    if count < 5:  # At least 5 indexes should be created
        return False, f"Expected at least 5 indexes, found {count}"

    return True, "All tables and indexes created successfully"


def seed_sample_data(conn: sqlite3.Connection):
    """Populate database with sample data for testing."""
    cursor = conn.cursor()

    # Sample users
    users = [
        ("alice@trading.com", "2026-01-15", "2026-01-20", "pro"),
        ("bob@trading.com", "2026-02-10", "2026-02-15", "free"),
        ("charlie@trading.com", "2026-03-01", None, "free"),
        ("diana@trading.com", "2026-03-15", "2026-03-18", "elite"),
        ("eve@trading.com", "2026-04-01", "2026-04-05", "basic"),
    ]

    for email, signup_date, first_trade_date, tier in users:
        try:
            cursor.execute(
                """
                INSERT INTO users (email, signup_date, first_trade_date, trading_tier)
                VALUES (?, ?, ?, ?)
                """,
                (email, signup_date, first_trade_date, tier)
            )
        except sqlite3.IntegrityError:
            pass  # User already exists

    conn.commit()

    # Get the user IDs we just created
    cursor.execute("SELECT id, email FROM users WHERE email LIKE '%@trading.com'")
    user_map = {email: uid for uid, email in cursor.fetchall()}

    # Sample daily trades (last 30 days)
    base_date = datetime.now()
    for user_id in user_map.values():
        for i in range(30):
            trade_date = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
            win_count = 3 + (user_id * i) % 7
            loss_count = 2 + ((user_id + i) % 5)
            num_trades = win_count + loss_count
            pnl_dollars = (win_count * 150) - (loss_count * 75)
            pnl_percent = (pnl_dollars / 10000) * 100
            win_rate = (win_count / num_trades) * 100 if num_trades > 0 else 0.0
            balance = 10000 + (pnl_dollars * (i + 1))

            try:
                cursor.execute(
                    """
                    INSERT INTO daily_trades
                    (user_id, date, num_trades, win_count, loss_count, pnl_dollars, pnl_percent, balance, win_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, trade_date, num_trades, win_count, loss_count,
                     pnl_dollars, pnl_percent, balance, win_rate)
                )
            except sqlite3.IntegrityError:
                pass  # Record already exists

    conn.commit()

    # Sample upsell tracking
    revenue_tiers = ["none", "trial", "paid-basic", "paid-pro", "paid-elite"]
    for idx, user_id in enumerate(user_map.values()):
        tier_history = [
            {
                "tier": "free",
                "date": "2026-01-15",
                "source": "signup"
            }
        ]
        revenue_tier = revenue_tiers[idx % len(revenue_tiers)]

        try:
            cursor.execute(
                """
                INSERT INTO upsell_tracking
                (user_id, tier_history, current_tier, revenue_tier, lifetime_revenue)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, json.dumps(tier_history), "free", revenue_tier,
                 [0, 9.99, 19.99, 49.99, 99.99][idx % len(revenue_tiers)])
            )
        except sqlite3.IntegrityError:
            pass  # Record already exists

    conn.commit()
    print(f"[+] Seeded {len(user_map)} users with sample data")


def reset_database(db_path: Path):
    """Drop and recreate the database."""
    if db_path.exists():
        db_path.unlink()
        print(f"[*] Removed existing database: {db_path}")
    return True


def main():
    """Main initialization flow."""
    db_path = get_db_path()
    should_seed = "--seed" in sys.argv
    should_reset = "--reset" in sys.argv

    try:
        # Reset if requested
        if should_reset:
            reset_database(db_path)

        # Create/connect to database
        print(f"[*] Initializing SQLite database: {db_path}")
        conn = sqlite3.Connection(str(db_path))
        conn.row_factory = sqlite3.Row

        # Initialize schema
        print("[*] Creating schema...")
        init_schema(conn)

        # Verify schema
        success, message = verify_schema(conn)
        if not success:
            print(f"[!] Schema verification failed: {message}")
            return 1
        print(f"[+] {message}")

        # Seed sample data if requested
        if should_seed:
            print("[*] Seeding sample data...")
            seed_sample_data(conn)

        conn.close()
        print(f"\n[+] Database initialization complete!")
        print(f"    Location: {db_path}")
        print(f"    Tables: users, daily_trades, upsell_tracking")
        if should_seed:
            print(f"    Sample data: 5 users with 30-day trading history")
        return 0

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

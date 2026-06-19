"""
LIVE TRADING STATE & DATABASE SCHEMA
Manages all persistence for live trading system, deployments, accounts, and audit trails
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_live_trading_schema(db_path: str = "clients.db"):
    """
    Create all required tables for live trading system.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ========================================================================
    # DEPLOYMENTS TABLE
    # Track paper -> live transition requests and progress
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_confirmation',
            paper_balance DECIMAL(10, 2) NOT NULL,
            deployment_amount DECIMAL(10, 2) NOT NULL,
            max_daily_loss DECIMAL(10, 2) NOT NULL,
            status_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id),
            CHECK(deployment_amount > 0)
        )
    """)

    # ========================================================================
    # DEPLOYMENT APPROVALS TABLE
    # Stores confirmation codes and approval status
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deployment_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deployment_id INTEGER NOT NULL UNIQUE,
            approval_code TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            confirmed_at TEXT,
            confirmed_via TEXT,
            robinhood_account_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(deployment_id) REFERENCES deployments(id)
        )
    """)

    # ========================================================================
    # LIVE ACCOUNTS TABLE
    # Tracks active live trading accounts and performance
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            robinhood_account_id TEXT NOT NULL UNIQUE,
            deployment_amount DECIMAL(10, 2) NOT NULL,
            current_balance DECIMAL(10, 2) NOT NULL,
            peak_balance DECIMAL(10, 2) NOT NULL,
            daily_loss_limit DECIMAL(10, 2) NOT NULL,
            max_drawdown_pct DECIMAL(5, 2) NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            paused_at TEXT,
            pause_reason TEXT,
            closed_at TEXT,
            closure_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id),
            CHECK(current_balance >= 0),
            CHECK(peak_balance >= current_balance)
        )
    """)

    # ========================================================================
    # LIVE TRADES TABLE
    # All trades executed on live account
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            robinhood_order_id TEXT NOT NULL UNIQUE,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity DECIMAL(10, 4) NOT NULL,
            entry_price DECIMAL(10, 4) NOT NULL,
            exit_price DECIMAL(10, 4),
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            position_value DECIMAL(12, 2) NOT NULL,
            realized_pnl DECIMAL(12, 2),
            unrealized_pnl DECIMAL(12, 2),
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id),
            CHECK(side IN ('buy', 'sell')),
            CHECK(quantity > 0),
            CHECK(entry_price > 0)
        )
    """)

    # ========================================================================
    # DAILY P&L TABLE
    # Daily performance tracking for live accounts
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_daily_pnl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            opening_balance DECIMAL(10, 2) NOT NULL,
            closing_balance DECIMAL(10, 2) NOT NULL,
            daily_pnl DECIMAL(10, 2) NOT NULL,
            daily_pnl_pct DECIMAL(5, 4) NOT NULL,
            trades_count INTEGER DEFAULT 0,
            wins_count INTEGER DEFAULT 0,
            losses_count INTEGER DEFAULT 0,
            win_rate DECIMAL(5, 4),
            max_intraday_loss DECIMAL(10, 2),
            max_intraday_gain DECIMAL(10, 2),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, date),
            CHECK(trades_count >= 0)
        )
    """)

    # ========================================================================
    # CIRCUIT BREAKER STATE TABLE
    # Current circuit breaker state for each user
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS circuit_breakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            state TEXT NOT NULL DEFAULT 'green',
            reason TEXT,
            triggered_at TEXT,
            updated_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id),
            CHECK(state IN ('green', 'yellow', 'red'))
        )
    """)

    # ========================================================================
    # DEPLOYMENT EVENTS TABLE
    # Audit trail of all deployment events
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deployment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ========================================================================
    # ADMIN ACTIONS TABLE
    # Track all manual admin overrides
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            admin_email TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ========================================================================
    # ROBINHOOD WEBHOOKS TABLE
    # Track webhook events from Robinhood for trade execution
    # ========================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS robinhood_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            webhook_id TEXT UNIQUE,
            event_type TEXT NOT NULL,
            event_data TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            processed_at TEXT,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ========================================================================
    # INDICES FOR PERFORMANCE
    # ========================================================================
    indices = [
        ("idx_deployments_user_id_status", "deployments", "user_id, status"),
        ("idx_live_accounts_user_id", "live_accounts", "user_id"),
        ("idx_live_accounts_status", "live_accounts", "status"),
        ("idx_live_trades_user_id_status", "live_trades", "user_id, status"),
        ("idx_live_trades_symbol_date", "live_trades", "symbol, entry_time"),
        ("idx_live_daily_pnl_user_date", "live_daily_pnl", "user_id, date"),
        ("idx_circuit_breakers_user_state", "circuit_breakers", "user_id, state"),
        ("idx_deployment_events_user_date", "deployment_events", "user_id, created_at"),
        ("idx_admin_actions_user_date", "admin_actions", "user_id, created_at"),
    ]

    for idx_name, table, columns in indices:
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({columns})")
        except sqlite3.Error as e:
            logger.warning(f"Could not create index {idx_name}: {e}")

    conn.commit()
    logger.info("Live trading schema initialized successfully")
    conn.close()


def verify_live_trading_schema(db_path: str = "clients.db") -> bool:
    """
    Verify all required tables exist.
    Returns True if all tables present, False otherwise.
    """
    required_tables = [
        "deployments",
        "deployment_approvals",
        "live_accounts",
        "live_trades",
        "live_daily_pnl",
        "circuit_breakers",
        "deployment_events",
        "admin_actions",
        "robinhood_webhooks"
    ]

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cur.fetchall()}
        conn.close()

        missing = set(required_tables) - existing_tables

        if missing:
            logger.error(f"Missing tables: {missing}")
            return False

        logger.info(f"All {len(required_tables)} tables verified")
        return True

    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def clear_live_trading_data(db_path: str = "clients.db", confirm: bool = False):
    """
    Clear all live trading data (for reset/testing).
    Requires confirm=True to prevent accidental deletion.
    """
    if not confirm:
        logger.error("Refusing to clear data without explicit confirmation")
        return False

    tables_to_clear = [
        "robinhood_webhooks",
        "admin_actions",
        "deployment_events",
        "circuit_breakers",
        "live_daily_pnl",
        "live_trades",
        "live_accounts",
        "deployment_approvals",
        "deployments"
    ]

    # Allowed table names - prevents SQL injection
    allowed_tables = set(tables_to_clear)

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        for table in tables_to_clear:
            if table not in allowed_tables:
                logger.error(f"Invalid table name: {table}")
                continue
            cur.execute(f"DELETE FROM {table}")  # noqa: S608 - validated against hardcoded list above
            logger.info(f"Cleared {table}")

        conn.commit()
        conn.close()
        logger.warning("All live trading data cleared")
        return True

    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        return False


def get_live_trading_stats(db_path: str = "clients.db") -> dict:
    """Get summary statistics about live trading system"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        stats = {}

        # Count deployments by status
        cur.execute("SELECT status, COUNT(*) as count FROM deployments GROUP BY status")
        stats["deployments_by_status"] = dict(cur.fetchall())

        # Count live accounts
        cur.execute("SELECT status, COUNT(*) as count FROM live_accounts GROUP BY status")
        stats["live_accounts_by_status"] = dict(cur.fetchall())

        # Total live capital deployed
        cur.execute("SELECT SUM(deployment_amount) as total FROM live_accounts WHERE status IN ('active', 'paused')")
        row = cur.fetchone()
        stats["total_live_capital"] = row[0] if row and row[0] else 0.0

        # Total trades executed
        cur.execute("SELECT COUNT(*) as total FROM live_trades")
        stats["total_live_trades"] = cur.fetchone()[0]

        # Average account balance
        cur.execute("SELECT AVG(current_balance) as avg FROM live_accounts WHERE status IN ('active', 'paused')")
        row = cur.fetchone()
        stats["avg_account_balance"] = row[0] if row and row[0] else 0.0

        conn.close()
        return stats

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        initialize_live_trading_schema()
        print("Schema initialized")
    elif len(sys.argv) > 1 and sys.argv[1] == "--verify":
        if verify_live_trading_schema():
            print("Schema verification passed")
        else:
            print("Schema verification failed")
    elif len(sys.argv) > 1 and sys.argv[1] == "--stats":
        stats = get_live_trading_stats()
        import json
        print(json.dumps(stats, indent=2))
    else:
        print("Usage:")
        print("  python live_trading_state.py --init      # Initialize schema")
        print("  python live_trading_state.py --verify    # Verify schema")
        print("  python live_trading_state.py --stats     # Show stats")

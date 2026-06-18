#!/usr/bin/env python3
"""
Daily Results Reporter (5 PM MST)
Updates daily-command with end-of-day metrics and declares daily winner
Stores daily trading results in clients.db database
"""

import os
import json
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

def get_mst_time():
    """Get current time in MST"""
    utc_now = datetime.now(timezone.utc)
    mst = utc_now.astimezone(timezone(timedelta(hours=-7)))
    return mst

def init_clients_database(db_path="clients.db"):
    """Initialize clients database with required tables if they don't exist"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create users table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                system_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create daily_trades table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                system TEXT,
                num_trades INTEGER,
                win_rate REAL,
                balance REAL,
                pnl_dollars REAL,
                pnl_percent REAL,
                wins INTEGER,
                losses INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date, system)
            )
        """)

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        return False

def get_or_create_user(email=None, system_id=None, db_path="clients.db"):
    """Get existing user or create new one with email and system_id"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Try to get existing user by system_id first (preferred)
        if system_id:
            cursor.execute("SELECT id FROM users WHERE system_id = ?", (system_id,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return result[0]

        # Try to get existing user by email
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return result[0]

        # Create new user with system_id, using unique email based on system_id
        unique_email = email or f"{system_id or 'default'}@profitengine.local"
        cursor.execute(
            "INSERT INTO users (email, system_id) VALUES (?, ?)",
            (unique_email, system_id or "system-default")
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.Error as e:
        print(f"Error managing user: {e}")
        return None

def store_daily_results(report, db_path="clients.db"):
    """Store daily trading results in clients database"""
    try:
        # Initialize database if needed
        init_clients_database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        date_str = report.get("date")
        stored_records = []

        # Store System A results
        system_a = report.get("system_a", {})
        if system_a and system_a.get("trades_today") is not None:
            user_id = get_or_create_user(
                system_id="system-a",
                db_path=db_path
            )

            cursor.execute("""
                INSERT OR REPLACE INTO daily_trades
                (user_id, date, system, num_trades, win_rate, balance, pnl_dollars, pnl_percent, wins, losses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                date_str,
                "System A (Local/Aggressive)",
                system_a.get("trades_today", 0),
                (system_a.get("wins", 0) / max(system_a.get("trades_today", 1), 1) * 100) if system_a.get("trades_today") else 0,
                system_a.get("current_balance", 100.0),
                system_a.get("pnl_dollars", 0.0),
                system_a.get("pnl_percent", 0.0),
                system_a.get("wins", 0),
                system_a.get("losses", 0)
            ))
            stored_records.append({
                "system": "System A",
                "user_id": user_id,
                "date": date_str,
                "trades": system_a.get("trades_today", 0),
                "pnl_percent": system_a.get("pnl_percent", 0.0)
            })

        # Store System B results
        system_b = report.get("system_b", {})
        if system_b and system_b.get("trades_today") not in ("TBD", None):
            user_id = get_or_create_user(
                system_id="system-b",
                db_path=db_path
            )

            cursor.execute("""
                INSERT OR REPLACE INTO daily_trades
                (user_id, date, system, num_trades, win_rate, balance, pnl_dollars, pnl_percent, wins, losses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                date_str,
                "System B (Vercel/Conservative)",
                system_b.get("trades_today", 0),
                (system_b.get("wins", 0) / max(system_b.get("trades_today", 1), 1) * 100) if system_b.get("trades_today") else 0,
                system_b.get("current_balance", 100.0),
                system_b.get("pnl_dollars", 0.0),
                system_b.get("pnl_percent", 0.0),
                system_b.get("wins", 0),
                system_b.get("losses", 0)
            ))
            stored_records.append({
                "system": "System B",
                "user_id": user_id,
                "date": date_str,
                "trades": system_b.get("trades_today", 0),
                "pnl_percent": system_b.get("pnl_percent", 0.0)
            })

        conn.commit()
        conn.close()

        return stored_records
    except sqlite3.Error as e:
        print(f"Database error storing results: {e}")
        return []

def parse_system_a_metrics():
    """Extract System A metrics from autonomous_trading.log"""
    log_path = "autonomous_trading.log"

    if not os.path.exists(log_path):
        return None

    with open(log_path, "r") as f:
        lines = f.readlines()

    # Find latest balance and trade count
    trades = len([l for l in lines if "Trade:" in l])

    # Extract all Trade lines to calculate P&L
    trade_lines = [l for l in lines if "Trade:" in l]

    # Simple P&L calculation (would need actual position tracking)
    starting_balance = 100.0
    pnl = 0.0

    # Count winning vs losing trades (rough estimate)
    wins = len([l for l in lines if "take_profit" in l.lower()])
    losses = len([l for l in lines if "stop_loss" in l.lower()])

    return {
        "system": "System A (Local/Aggressive)",
        "trades_today": trades,
        "starting_balance": starting_balance,
        "current_balance": starting_balance + pnl,
        "pnl_dollars": pnl,
        "pnl_percent": (pnl / starting_balance * 100) if starting_balance else 0,
        "wins": wins,
        "losses": losses,
        "cycle_time_seconds": 30
    }

def parse_system_b_metrics():
    """System B metrics (would fetch from Vercel API)"""
    return {
        "system": "System B (Vercel/Conservative)",
        "trades_today": "TBD",
        "starting_balance": 100.0,
        "current_balance": 100.0,
        "pnl_dollars": 0.0,
        "pnl_percent": 0.0,
        "wins": "TBD",
        "losses": "TBD",
        "cycle_time_seconds": 60,
        "note": "Check Vercel dashboard for real-time metrics"
    }

def generate_daily_report(system_a, system_b):
    """Generate end-of-day report"""
    mst = get_mst_time()
    date_str = mst.strftime("%Y-%m-%d")

    # Determine winner
    a_balance = system_a.get("current_balance", 100)
    b_balance = system_b.get("current_balance", 100)

    winner = "System A" if a_balance >= b_balance else "System B"

    report = {
        "date": date_str,
        "market_close_time_mst": mst.strftime("%H:%M:%S"),
        "daily_winner": winner,
        "system_a": system_a,
        "system_b": system_b,
        "competition_status": "ACTIVE - Racing to $1,000",
        "next_market_open_mst": "04:30 (next trading day)"
    }

    return report, winner

def update_daily_command(report, winner):
    """Update daily-command file with results"""

    # Read existing daily-command if it exists
    daily_command_path = "daily-command"
    existing = []

    if os.path.exists(daily_command_path):
        with open(daily_command_path, "r") as f:
            existing = json.load(f) if f.read().strip() else []

    # Append today's results
    daily_entry = {
        "date": report["date"],
        "daily_winner": winner,
        "system_a_balance": report["system_a"].get("current_balance", 100),
        "system_b_balance": report["system_b"].get("current_balance", 100),
        "system_a_pnl_percent": report["system_a"].get("pnl_percent", 0),
        "system_b_pnl_percent": report["system_b"].get("pnl_percent", 0),
        "system_a_trades": report["system_a"].get("trades_today", 0),
        "system_b_trades": report["system_b"].get("trades_today", "TBD"),
        "timestamp": report["market_close_time_mst"]
    }

    if isinstance(existing, list):
        existing.append(daily_entry)
    else:
        existing = [daily_entry]

    # Write updated daily-command
    with open(daily_command_path, "w") as f:
        json.dump(existing, f, indent=2)

    return daily_entry

def print_daily_summary(report, winner):
    """Print formatted daily summary"""
    print("\n" + "="*80)
    print("DAILY RESULTS - 5 PM MST MARKET CLOSE")
    print("="*80)
    print(f"\nDate: {report['date']}")
    print(f"Time: {report['market_close_time_mst']} MST")
    print(f"\nDaily Winner: {winner}")
    print(f"Competition Status: {report['competition_status']}")

    print(f"\n--- System A (Local/Aggressive) ---")
    a = report['system_a']
    print(f"  Balance: ${a.get('current_balance', 100):.2f}")
    print(f"  P&L: ${a.get('pnl_dollars', 0):.2f} ({a.get('pnl_percent', 0):.2f}%)")
    print(f"  Trades: {a.get('trades_today', 0)}")
    print(f"  Wins/Losses: {a.get('wins', '?')}/{a.get('losses', '?')}")

    print(f"\n--- System B (Vercel/Conservative) ---")
    b = report['system_b']
    print(f"  Balance: ${b.get('current_balance', 100):.2f}")
    print(f"  P&L: ${b.get('pnl_dollars', 0):.2f} ({b.get('pnl_percent', 0):.2f}%)")
    print(f"  Trades: {b.get('trades_today', 'TBD')}")
    print(f"  Wins/Losses: {b.get('wins', 'TBD')}/{b.get('losses', 'TBD')}")

    print(f"\nNext Market Open: {report['next_market_open_mst']} MST")
    print("="*80 + "\n")

def main():
    """Run daily report at 5 PM MST"""
    mst = get_mst_time()
    hour = mst.hour + mst.minute / 60.0

    # Check if it's close to 5 PM (17:00) MST
    if 16.9 <= hour <= 17.1:  # Within 6 minutes of 5 PM
        print(f"[{mst.isoformat()}] Running daily report...")

        # Parse metrics from both systems
        system_a = parse_system_a_metrics() or {}
        system_b = parse_system_b_metrics()

        # Generate report
        report, winner = generate_daily_report(system_a, system_b)

        # Update daily-command
        daily_entry = update_daily_command(report, winner)

        # Print summary
        print_daily_summary(report, winner)

        # Log to daily_results.jsonl
        with open("daily_results.jsonl", "a") as f:
            f.write(json.dumps(report) + "\n")

        print("Daily results saved to daily_results.jsonl")
        print("Daily command updated")

        # Store in clients.db database
        print("\n[Database] Storing trading results in clients.db...")
        stored_records = store_daily_results(report)

        if stored_records:
            print(f"[Database] Successfully stored {len(stored_records)} record(s):")
            for record in stored_records:
                print(f"  - {record['system']}: {record['trades']} trades, {record['pnl_percent']:.2f}% P&L")
            print("[Database] Daily trading results persisted")
        else:
            print("[Database] WARNING: No trading results were stored")

        return report, winner
    else:
        print(f"Not market close yet. Current MST time: {hour:.2f} (need 17:00)")
        return None, None

if __name__ == "__main__":
    main()

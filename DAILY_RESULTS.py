#!/usr/bin/env python3
"""
Daily Results Reporter (5 PM MST)
Updates daily-command with end-of-day metrics and declares daily winner
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta

def get_mst_time():
    """Get current time in MST"""
    utc_now = datetime.now(timezone.utc)
    mst = utc_now.astimezone(timezone(timedelta(hours=-7)))
    return mst

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

        return report, winner
    else:
        print(f"Not market close yet. Current MST time: {hour:.2f} (need 17:00)")
        return None, None

if __name__ == "__main__":
    main()

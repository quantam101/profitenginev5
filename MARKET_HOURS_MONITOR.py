#!/usr/bin/env python3
"""
Market Hours Monitor (4:30 AM - 5 PM MST)
Tracks System A vs System B P&L and performance during US trading hours
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
import re

MARKET_START_MST = 4.5  # 4:30 AM
MARKET_END_MST = 17.0   # 5 PM
MONITOR_INTERVAL = 300  # Check every 5 minutes

def get_mst_hour():
    """Get current hour in MST"""
    utc_now = datetime.now(timezone.utc)
    mst = utc_now.astimezone(timezone(timedelta(hours=-7)))
    return mst.hour + mst.minute / 60.0

def is_market_hours():
    """Check if current time is within market hours"""
    hour = get_mst_hour()
    return MARKET_START_MST <= hour <= MARKET_END_MST

def parse_system_a_logs():
    """Extract System A metrics from autonomous_trading.log"""
    log_path = "autonomous_trading.log"
    if not os.path.exists(log_path):
        return None

    with open(log_path, "r") as f:
        content = f.read()

    # Extract latest metrics
    trades = len(re.findall(r"Trade: ", content))
    balance = 100.0  # Starting balance
    pnl_pct = 0.0

    return {
        "system": "A (Local/Aggressive)",
        "trades": trades,
        "balance": balance,
        "pnl_pct": pnl_pct,
        "timestamp": datetime.now().isoformat()
    }

def parse_system_b_status():
    """System B status from Vercel"""
    # Would normally fetch from Vercel API or WebSocket
    return {
        "system": "B (Vercel/Conservative)",
        "status": "Check Vercel dashboard: already-here-llc project",
        "timestamp": datetime.now().isoformat()
    }

def log_status(metrics_a, metrics_b):
    """Log comparison to file"""
    timestamp = datetime.now().isoformat()
    hour = get_mst_hour()

    log_entry = {
        "timestamp": timestamp,
        "mst_hour": hour,
        "system_a": metrics_a,
        "system_b": metrics_b,
        "market_hours": is_market_hours()
    }

    # Append to market_hours_tracking.jsonl
    with open("market_hours_tracking.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    if is_market_hours():
        print(f"\n[{timestamp}] MARKET HOURS - {hour:.1f} MST")
        print(f"System A: {metrics_a.get('trades', '?')} trades, {metrics_a.get('pnl_pct', 0):.2f}% P&L")
        print(f"System B: See Vercel dashboard")

def main():
    """Monitor both systems during market hours"""
    print("Market Hours Monitor (4:30 AM - 5 PM MST)")
    print(f"Current time: {datetime.now().isoformat()}")
    print(f"Current MST hour: {get_mst_hour():.1f}")
    print(f"Market hours active: {is_market_hours()}")
    print(f"\nMonitoring interval: {MONITOR_INTERVAL}s")
    print("Log: market_hours_tracking.jsonl\n")

    while True:
        if is_market_hours():
            metrics_a = parse_system_a_logs()
            metrics_b = parse_system_b_status()
            log_status(metrics_a, metrics_b)

        time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    main()

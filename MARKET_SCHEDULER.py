#!/usr/bin/env python3
"""
Market Hours Scheduler
- Monitors trading 4:30 AM - 5 PM MST
- Generates daily report at 5 PM MST
- Updates daily-command with winner
"""

import os
import json
import time
import subprocess
from datetime import datetime, timezone, timedelta

MARKET_START_MST = 4.5   # 4:30 AM
MARKET_END_MST = 17.0    # 5 PM
CHECK_INTERVAL = 60      # Check every minute

def get_mst_hour():
    """Get current hour in MST"""
    utc_now = datetime.now(timezone.utc)
    mst = utc_now.astimezone(timezone(timedelta(hours=-7)))
    return mst.hour + mst.minute / 60.0, mst

def is_market_hours():
    """Check if trading hours"""
    hour, _ = get_mst_hour()
    return MARKET_START_MST <= hour <= MARKET_END_MST

def is_market_close():
    """Check if at market close (5 PM MST ± 5 min)"""
    hour, _ = get_mst_hour()
    return 16.92 <= hour <= 17.08  # Within 5 minutes of 5 PM

def run_daily_report():
    """Execute daily report at market close"""
    try:
        result = subprocess.run(
            ["python", "DAILY_RESULTS.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.stderr:
            print(f"[ERROR] {result.stderr}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to run daily report: {e}")
        return False

def check_system_status():
    """Check if systems are running"""
    status = {}

    # Check System A
    if os.path.exists("autonomous_trading.log"):
        size = os.path.getsize("autonomous_trading.log")
        status["system_a"] = f"ACTIVE ({size} bytes)"
    else:
        status["system_a"] = "NOT FOUND"

    # Check System B (would check Vercel API)
    status["system_b"] = "CHECK Vercel dashboard"

    return status

def main():
    """Main scheduler loop"""
    print("Market Hours Scheduler Started")
    print(f"Market hours: 4:30 AM - 5 PM MST")
    print(f"Daily close: 5 PM MST")
    print(f"Check interval: {CHECK_INTERVAL}s\n")

    last_report_run = None

    while True:
        hour, mst = get_mst_hour()
        trading = is_market_hours()
        at_close = is_market_close()

        status = check_system_status()

        if trading:
            print(f"\n[{mst.strftime('%H:%M:%S')} MST] Market OPEN - {status}")
        else:
            print(f"\n[{mst.strftime('%H:%M:%S')} MST] Market CLOSED - {status}")

        # Run daily report at market close
        if at_close:
            today = mst.strftime("%Y-%m-%d")
            if last_report_run != today:
                print(f"\n[{mst.strftime('%H:%M:%S')}] MARKET CLOSE - Running daily report...")
                run_daily_report()
                last_report_run = today

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

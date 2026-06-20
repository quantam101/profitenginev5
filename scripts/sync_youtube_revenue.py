#!/usr/bin/env python3
"""YouTube AdSense revenue sync script.

Fetches AdSense earnings from YouTube Analytics API and logs to ledger.

Usage:
    python scripts/sync_youtube_revenue.py                    # Sync current month
    python scripts/sync_youtube_revenue.py 2026 6             # Sync June 2026
    python scripts/sync_youtube_revenue.py --last-3-months    # Sync last 3 months
    python scripts/sync_youtube_revenue.py --scheduler        # Start scheduler (daily sync)
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.youtube_analytics import YouTubeRevenueAnalytics


def setup_logging():
    """Configure logging with timestamps and colors."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )


def sync_current_month():
    """Sync AdSense revenue for current month."""
    analytics = YouTubeRevenueAnalytics()
    now = datetime.utcnow()
    amount = analytics.sync_revenue(now.year, now.month)
    return amount


def sync_specific_month(year: int, month: int):
    """Sync AdSense revenue for a specific month."""
    analytics = YouTubeRevenueAnalytics()
    amount = analytics.sync_revenue(year, month)
    return amount


def sync_last_n_months(n: int):
    """Sync AdSense revenue for last N months."""
    analytics = YouTubeRevenueAnalytics()
    now = datetime.utcnow()
    total = 0.0

    logging.info(f"Syncing revenue for last {n} months...")

    for i in range(n):
        # Go back i months
        date = now - timedelta(days=30 * i)
        year = date.year
        month = date.month

        logging.info(f"Syncing {year}-{month:02d}...")
        amount = analytics.sync_revenue(year, month)

        if amount:
            total += amount

    logging.info(f"Total synced: ${total:.2f}")
    return total


def start_scheduler():
    """Start the revenue scheduler for daily syncs."""
    from backend.services.revenue_scheduler import init_revenue_scheduler
    import time

    logging.info("Starting revenue scheduler...")
    scheduler = init_revenue_scheduler()

    try:
        logging.info("Scheduler running. Press Ctrl+C to stop.")
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down scheduler...")
        scheduler.stop()
        logging.info("Scheduler stopped.")
        return 0

    return 1


def main():
    """Parse arguments and execute sync."""
    parser = argparse.ArgumentParser(
        description="YouTube AdSense revenue sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/sync_youtube_revenue.py
    Sync revenue for current month

  python scripts/sync_youtube_revenue.py 2026 6
    Sync revenue for June 2026

  python scripts/sync_youtube_revenue.py --last-3-months
    Sync last 3 months of revenue

  python scripts/sync_youtube_revenue.py --scheduler
    Start scheduler for automatic daily syncs
        """
    )

    parser.add_argument(
        "year",
        nargs="?",
        type=int,
        help="Year (YYYY) for manual sync"
    )
    parser.add_argument(
        "month",
        nargs="?",
        type=int,
        help="Month (1-12) for manual sync"
    )
    parser.add_argument(
        "--last-n-months",
        type=int,
        metavar="N",
        help="Sync last N months"
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start background scheduler for daily syncs"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Execute based on arguments
    if args.scheduler:
        return start_scheduler()

    if args.last_n_months:
        return 0 if sync_last_n_months(args.last_n_months) > 0 else 1

    if args.year and args.month:
        if not (1 <= args.month <= 12):
            logging.error("Month must be 1-12")
            return 1
        return 0 if sync_specific_month(args.year, args.month) else 1

    # Default: sync current month
    return 0 if sync_current_month() else 1


if __name__ == "__main__":
    sys.exit(main())

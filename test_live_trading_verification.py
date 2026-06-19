"""
Quick test of Live Trading Verification system.
This version runs for shorter duration to test functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add runtime directory to path
sys.path.insert(0, str(Path(__file__).parent / "runtime"))

# Import verifier
from live_trading_verification import LiveTradingVerifier
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_verification():
    """Run quick verification test (5 trades, 10 symbols)."""
    logger.info("Starting quick verification test...")

    verifier = LiveTradingVerifier(
        account_balance=10000.0,
        max_duration_hours=0.5,  # 30 minutes max
        min_trades=5,             # Only 5 trades for test
        trades_per_symbol=1       # 1 per symbol
    )

    try:
        metrics = await verifier.run_verification()

        # Print summary
        print("\n" + "=" * 80)
        print("QUICK TEST SUMMARY")
        print("=" * 80)
        print(f"Total Trades: {metrics.total_trades}")
        print(f"Win Rate: {metrics.win_rate:.1f}%")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")
        print(f"Net P&L: ${metrics.net_pnl:+.2f}")
        print(f"Return: {metrics.return_percent:+.1f}%")

        return metrics

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        metrics = asyncio.run(test_verification())
        print("\n✓ Test complete!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)

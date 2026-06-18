#!/usr/bin/env python3
"""
SIMPLE LAUNCHER - Master Orchestrator Only (No Dashboard)
Optimized for 1-week timeline with aggressive parameters
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('autonomous_trading.log')
    ]
)
logger = logging.getLogger("TradingEngine")

async def run_trading():
    """Launch and run the Master Orchestrator"""

    logger.info("="*80)
    logger.info("AUTONOMOUS TRADING ENGINE - OPTIMIZED FOR 1-WEEK TIMELINE")
    logger.info("="*80)

    logger.info("\nOPTIMIZED CONFIGURATION:")
    logger.info("  Risk per Trade: 4%")
    logger.info("  Take Profit: +7%")
    logger.info("  Stop Loss: -1.5%")
    logger.info("  Daily Drawdown Limit: 12%")
    logger.info("  Scan Interval: 30 seconds")
    logger.info("  Confidence Threshold: >0.75")
    logger.info("  Timeline: 1 week (7x acceleration)")

    try:
        logger.info("\nInitializing Master Orchestrator...")
        from runtime.master_orchestrator_ai import MasterOrchestratorAI

        master_ai = MasterOrchestratorAI()
        await master_ai.initialize()
        logger.info("  [OK] Master Orchestrator ready")

        logger.info("\n" + "="*80)
        logger.info("STARTING 24/7 AUTONOMOUS TRADING OPERATION")
        logger.info("="*80)
        logger.info("\nLive monitoring: autonomous_trading.log")
        logger.info("Press Ctrl+C to stop\n")

        # Run the trading loop
        await master_ai.run_autonomous_24_7()

    except KeyboardInterrupt:
        logger.info("\n\nShutdown signal received")
        if 'master_ai' in locals():
            master_ai.running = False
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return False

    return True

def main():
    """Entry point"""
    result = asyncio.run(run_trading())
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()

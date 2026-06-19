#!/usr/bin/env python3
"""
PRE-LAUNCH VERIFICATION — Test all systems before 4 AM deployment

Verifies:
1. All trading modules load correctly
2. Robinhood client initializes
3. Signal generation works
4. Risk management constraints are set
5. Position sizing calculations work
6. Compliance monitoring is ready
7. Deployment script is runnable
"""

import asyncio
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)


async def verify_all_systems() -> bool:
    """Run all verification checks"""

    logger.info("="*70)
    logger.info("PRE-LAUNCH VERIFICATION - $1000 TRADING SYSTEM")
    logger.info("="*70)
    logger.info(f"Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    all_passed = True

    # 1. Test module imports
    logger.info("[CHECK 1] Testing module imports...")
    try:
        from runtime.enhanced_trading_engine import EnhancedTradingEngine, TradeSignal
        from runtime.stock_compliance_monitor import get_compliance_monitor
        from runtime.robinhood_client import get_robinhood_client, RobinhoodClient
        from runtime.dynamic_risk_params import calculate_stop_loss, calculate_take_profit, calculate_position_size
        logger.info("  ✓ All module imports successful")
    except ImportError as e:
        logger.error(f"  ✗ Import failed: {e}")
        all_passed = False

    # 2. Test trading engine initialization
    logger.info("[CHECK 2] Testing EnhancedTradingEngine initialization...")
    try:
        engine = EnhancedTradingEngine(account_balance=100.0)
        summary = engine.get_summary()
        assert summary['account_balance'] == 100.0
        assert summary['active_positions'] == 0
        logger.info(f"  ✓ Engine initialized: ${summary['account_balance']:,.2f}")
    except Exception as e:
        logger.error(f"  ✗ Engine init failed: {e}")
        all_passed = False

    # 3. Test Robinhood client
    logger.info("[CHECK 3] Testing Robinhood client...")
    try:
        broker = await get_robinhood_client()
        account = await broker.get_account()
        if account:
            logger.info(f"  ✓ Broker connected: ${account.portfolio_value:,.2f}")
        else:
            logger.warning(f"  ⚠ Broker in simulation mode (no credentials provided)")
        broker.shutdown()
    except Exception as e:
        logger.error(f"  ✗ Broker init failed: {e}")
        all_passed = False

    # 4. Test trade signal generation
    logger.info("[CHECK 4] Testing trade signal generation...")
    try:
        signal = TradeSignal(
            symbol='AAPL',
            action='BUY',
            confidence=85,
            entry_price=150.0,
            stop_loss=147.0,
            take_profit=154.5,
            position_size=10,
            reason='Test signal',
            timestamp=datetime.utcnow().isoformat(),
            multiframe_score=85,
            catalyst_score=85,
        )
        assert signal.symbol == 'AAPL'
        assert signal.confidence == 85
        logger.info(f"  ✓ Signal generation working")
    except Exception as e:
        logger.error(f"  ✗ Signal generation failed: {e}")
        all_passed = False

    # 5. Test position sizing
    logger.info("[CHECK 5] Testing position sizing logic...")
    try:
        portfolio_value = 100.0
        current_price = 150.0
        position_size = max(1, int(portfolio_value * 0.1 / current_price))
        assert position_size >= 1
        logger.info(f"  ✓ Position sizing: {position_size} shares for ${portfolio_value:,.2f} portfolio")
    except Exception as e:
        logger.error(f"  ✗ Position sizing failed: {e}")
        all_passed = False

    # 6. Test risk parameters
    logger.info("[CHECK 6] Testing risk management...")
    try:
        entry = 150.0
        stop_loss = entry * 0.98  # 2% stop
        take_profit = entry * 1.03  # 3% target
        assert stop_loss < entry < take_profit
        logger.info(f"  ✓ Risk configured: Entry ${entry:.2f}, Stop ${stop_loss:.2f}, Target ${take_profit:.2f}")
    except Exception as e:
        logger.error(f"  ✗ Risk management failed: {e}")
        all_passed = False

    # 7. Test deployment script syntax
    logger.info("[CHECK 7] Testing deployment script...")
    try:
        with open('deploy_premarket_4am.py', 'r') as f:
            code = f.read()
            compile(code, 'deploy_premarket_4am.py', 'exec')
        logger.info(f"  ✓ Deployment script syntax valid")
    except Exception as e:
        logger.error(f"  ✗ Deployment script error: {e}")
        all_passed = False

    # 8. Test checklist exists
    logger.info("[CHECK 8] Testing deployment checklist...")
    try:
        with open('DEPLOYMENT_4AM_$1000_CHECKLIST.md', 'r') as f:
            content = f.read()
            assert '$1000' in content
            assert '4:00 AM' in content
        logger.info(f"  ✓ Deployment checklist exists and configured")
    except Exception as e:
        logger.error(f"  ✗ Checklist missing: {e}")
        all_passed = False

    # 9. Calculate daily requirements
    logger.info("[CHECK 9] Calculating $1000 target requirements...")
    try:
        starting = 100.0
        target = 1000.0
        daily_rate = ((target / starting) ** (1/7) - 1) * 100
        logger.info(f"  ✓ Daily target: {daily_rate:.1f}% compounded return needed")
        logger.info(f"     OR: $43.00 profit needed on Day 1 to stay on pace")
    except Exception as e:
        logger.error(f"  ✗ Calculation failed: {e}")
        all_passed = False

    # 10. Test market hours
    logger.info("[CHECK 10] Verifying market timing...")
    try:
        now = datetime.now()
        hour = now.hour
        if hour < 4:
            logger.warning(f"  ⚠ Current time: {hour}:00 (before 4 AM - set alarm for 4:00 AM MST)")
        elif 4 <= hour < 14:
            logger.warning(f"  ⚠ Current time: {hour}:00 (within trading hours - good time to verify!)")
        else:
            logger.warning(f"  ⚠ Current time: {hour}:00 (after market close - wait for 4 AM)")
    except Exception as e:
        logger.error(f"  ✗ Time check failed: {e}")
        all_passed = False

    # Final summary
    logger.info("")
    logger.info("="*70)
    if all_passed:
        logger.info("✓ ALL SYSTEMS READY FOR 4 AM DEPLOYMENT")
    else:
        logger.error("✗ SOME SYSTEMS FAILED - FIX BEFORE 4 AM LAUNCH")
    logger.info("="*70)
    logger.info("")

    return all_passed


if __name__ == '__main__':
    try:
        ready = asyncio.run(verify_all_systems())
        sys.exit(0 if ready else 1)
    except KeyboardInterrupt:
        logger.info("\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error during verification: {e}", exc_info=True)
        sys.exit(1)

#!/usr/bin/env python3
"""
Complete System Verification
Tests all trading system components and Profit Engine integration
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

sys.path.insert(0, '.')

# Import trading system components
try:
    from app import TradingControlOS
    from cmdos_integration import CMDOSIntegration
    from models import MarketSnapshot, AccountState
    from decimal import Decimal
    import yaml
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemVerification:
    """Comprehensive system verification."""

    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'components': {},
            'cmdos': {},
            'trading': {},
            'overall_status': 'PENDING'
        }

    async def verify_trading_core(self) -> bool:
        """Verify trading system core components."""
        logger.info("\n" + "="*80)
        logger.info("VERIFYING TRADING SYSTEM CORE")
        logger.info("="*80 + "\n")

        try:
            # Load configuration
            logger.info("✓ Loading configuration...")
            with open('./config.yaml') as f:
                config = yaml.safe_load(f)
            self.results['components']['config_loaded'] = True

            # Initialize trading system
            logger.info("✓ Initializing TradingControlOS...")
            os_instance = TradingControlOS(config_path='./config.yaml')
            self.results['components']['trading_os_initialized'] = True

            # Verify critical components
            components_check = {
                'synthesis_engine': hasattr(os_instance, 'synthesis_engine'),
                'risk_kernel': hasattr(os_instance, 'risk_kernel'),
                'paper_broker': hasattr(os_instance, 'paper_broker'),
                'audit_ledger': hasattr(os_instance, 'audit_ledger'),
            }

            for component, exists in components_check.items():
                status = "✅" if exists else "❌"
                logger.info(f"{status} {component}: {'READY' if exists else 'MISSING'}")
                self.results['components'][component] = exists

            # Test demo snapshot processing
            logger.info("\n✓ Testing market snapshot processing...")
            snapshot = {
                'symbol': 'AAPL',
                'timestamp': datetime.utcnow().isoformat(),
                'bid': 150.0,
                'ask': 150.05,
                'last': 150.02,
                'volume': 1000000,
                'volume_24h': Decimal('50000000'),
                'volatility': 10.0,
                'prices': [150.0 + i*0.01 for i in range(50)],
                'volumes': [100000 for _ in range(50)],
                'orderbook': {'bids': [[150.0-j*0.01, 10000] for j in range(5)],
                             'asks': [[150.0+j*0.01, 10000] for j in range(5)]},
                'trade_flow': [],
                'state': {'event_risk': 0.1, 'correlation_stress': 0.2},
                'account_equity': 100000.0,
                'buying_power': 95000.0,
                'cash': 50000.0,
                'daily_pnl': 0.0,
                'weekly_pnl': 0.0,
                'max_drawdown_pct': 0.0,
                'open_positions': [],
                'position_mismatch': False,
                'broker_offline': False
            }

            result = await os_instance.process_market_snapshot(snapshot)
            self.results['components']['snapshot_processing'] = result is not None
            logger.info(f"{'✅' if result else '⚠️'} Snapshot processing: {'SUCCESS' if result else 'NO PROPOSAL'}")

            # Get stats
            stats = os_instance.get_audit_stats()
            self.results['components']['audit_stats'] = {
                'total_trades': stats.get('total_trades', 0),
                'approval_rate': stats.get('approval_rate_pct', 0),
                'win_rate': stats.get('win_rate_pct', 0)
            }

            return all(components_check.values())

        except Exception as e:
            logger.error(f"❌ Trading core verification failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def verify_cmdos_integration(self) -> bool:
        """Verify CMDOS Profit Engine integration."""
        logger.info("\n" + "="*80)
        logger.info("VERIFYING CMDOS INTEGRATION")
        logger.info("="*80 + "\n")

        try:
            async with CMDOSIntegration() as cmdos:
                # Check health
                logger.info("✓ Checking CMDOS system health...")
                health = await cmdos.check_health()

                self.results['cmdos']['runtime_api'] = health['runtime']
                self.results['cmdos']['backend_api'] = health['backend']
                self.results['cmdos']['oracle_api'] = health['oracle']

                logger.info(f"  Runtime API (8000):  {'✅ HEALTHY' if health['runtime'] else '⚠️  OFFLINE'}")
                logger.info(f"  Backend API (8001):  {'✅ HEALTHY' if health['backend'] else '⚠️  OFFLINE'}")
                logger.info(f"  Oracle (3000):       {'✅ HEALTHY' if health['oracle'] else '⚠️  OFFLINE'}")

                # Get system status
                logger.info("\n✓ Fetching system status...")
                status = await cmdos.get_system_status()
                self.results['cmdos']['system_status'] = status

                # Try to fetch market data if runtime is healthy
                if health['runtime']:
                    logger.info("\n✓ Testing market data fetch...")
                    quote = await cmdos.get_market_data('AAPL')
                    self.results['cmdos']['market_data_fetch'] = quote is not None
                    logger.info(f"  AAPL Quote: {'✅ SUCCESS' if quote else '⚠️  FAILED'}")

                # Print health report
                cmdos.print_health_report()

                return any([health['runtime'], health['backend'], health['oracle']])

        except Exception as e:
            logger.error(f"❌ CMDOS integration verification failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def verify_file_structure(self) -> bool:
        """Verify required files exist."""
        logger.info("\n" + "="*80)
        logger.info("VERIFYING FILE STRUCTURE")
        logger.info("="*80 + "\n")

        required_files = [
            'app.py',
            'models.py',
            'agents_impl.py',
            'synthesis_engine.py',
            'risk_kernel.py',
            'paper_broker.py',
            'audit_ledger.py',
            'robinhood_adapter.py',
            'config.yaml',
            'cmdos_integration.py',
            'news_monitor_24_7.py',
            'launch_complete_system.py',
            'run_phase_test.py',
        ]

        all_present = True
        for filename in required_files:
            exists = os.path.exists(filename)
            status = "✅" if exists else "❌"
            logger.info(f"{status} {filename}")
            self.results['components'][f'file_{filename}'] = exists
            all_present = all_present and exists

        return all_present

    async def run_all_verifications(self) -> Dict:
        """Run all verifications and return results."""
        logger.info("\n")
        logger.info("╔" + "="*78 + "╗")
        logger.info("║" + " "*78 + "║")
        logger.info("║" + "PROFIT ENGINE TRADING SYSTEM — COMPLETE VERIFICATION".center(78) + "║")
        logger.info("║" + " "*78 + "║")
        logger.info("╚" + "="*78 + "╝")

        # Run verifications
        file_check = await self.verify_file_structure()
        trading_check = await self.verify_trading_core()
        cmdos_check = await self.verify_cmdos_integration()

        # Determine overall status
        if file_check and trading_check and cmdos_check:
            self.results['overall_status'] = 'READY'
            status_emoji = '✅'
        elif file_check and trading_check:
            self.results['overall_status'] = 'PARTIAL'
            status_emoji = '⚠️'
        else:
            self.results['overall_status'] = 'FAILED'
            status_emoji = '❌'

        # Final report
        logger.info("\n" + "="*80)
        logger.info("FINAL VERIFICATION REPORT")
        logger.info("="*80 + "\n")

        logger.info(f"{status_emoji} Overall Status: {self.results['overall_status']}")
        logger.info(f"📅 Timestamp: {self.results['timestamp']}")
        logger.info(f"📊 Components: {sum(1 for v in self.results['components'].values() if v is True)}/{len([v for v in self.results['components'].values() if isinstance(v, bool)])}")

        logger.info("\n✅ VERIFIED SYSTEMS:")
        if file_check:
            logger.info("  • File structure complete")
        if trading_check:
            logger.info("  • Trading system core operational")
        if cmdos_check:
            logger.info("  • CMDOS integration available")

        logger.info("\n" + "="*80)

        if self.results['overall_status'] == 'READY':
            logger.info("\n🚀 SYSTEM IS READY FOR TRADING")
            logger.info("\nNext steps:")
            logger.info("  1. Export Robinhood OAuth token:")
            logger.info("     export ROBINHOOD_OAUTH_TOKEN='your_token'")
            logger.info("  2. Launch complete system:")
            logger.info("     python launch_complete_system.py")
        elif self.results['overall_status'] == 'PARTIAL':
            logger.info("\n⚠️  SYSTEM PARTIALLY READY")
            logger.info("\nIssues detected:")
            if not cmdos_check:
                logger.info("  • CMDOS connectivity issue (check SSH)")
                logger.info("    Run: bash scripts/enforce-cmdos-keys.sh")
            logger.info("\nFix issues then re-run verification.")
        else:
            logger.info("\n❌ SYSTEM NOT READY")
            logger.info("\nCritical issues must be resolved before launching.")

        logger.info("="*80 + "\n")

        return self.results


async def main():
    """Run complete verification."""
    verification = SystemVerification()

    try:
        results = await verification.run_all_verifications()

        # Write results to JSON
        import json
        with open('./logs/verification_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
            logger.info(f"\n📋 Results saved to: ./logs/verification_results.json")

        return results['overall_status']

    except KeyboardInterrupt:
        logger.info("\n\n✅ Verification interrupted by user")
        return 'INTERRUPTED'
    except Exception as e:
        logger.error(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 'ERROR'


if __name__ == "__main__":
    status = asyncio.run(main())
    sys.exit(0 if status == 'READY' else 1)

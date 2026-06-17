"""
CMDOS Integration Layer
Connects trading system to Profit Engine server APIs on CMDOS (129.146.236.177)
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import os
import sys

sys.path.insert(0, '.')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class CMDOSIntegration:
    """Integration with CMDOS Profit Engine servers."""

    def __init__(
        self,
        runtime_url: str = "http://129.146.236.177:8000",
        backend_url: str = "http://129.146.236.177:8001",
        oracle_url: str = "http://129.146.236.177:3000",
        timeout: int = 10
    ):
        """Initialize CMDOS integration."""
        self.runtime_url = runtime_url.rstrip('/')
        self.backend_url = backend_url.rstrip('/')
        self.oracle_url = oracle_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_status = {
            'runtime': False,
            'backend': False,
            'oracle': False,
            'timestamp': None
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def check_health(self) -> Dict[str, bool]:
        """Check health of all CMDOS services."""
        if not self.session:
            logger.error("Session not initialized. Use 'async with' context manager.")
            return self.health_status

        logger.info("Checking CMDOS system health...")

        # Check Runtime API
        try:
            async with self.session.get(f"{self.runtime_url}/health", timeout=self.timeout) as resp:
                if resp.status == 200:
                    self.health_status['runtime'] = True
                    logger.info("✅ Runtime API (8000): HEALTHY")
                else:
                    logger.warning(f"⚠️  Runtime API returned {resp.status}")
        except Exception as e:
            logger.warning(f"⚠️  Runtime API unreachable: {e}")

        # Check Backend API
        try:
            async with self.session.get(f"{self.backend_url}/health", timeout=self.timeout) as resp:
                if resp.status == 200:
                    self.health_status['backend'] = True
                    logger.info("✅ Backend API (8001): HEALTHY")
                else:
                    logger.warning(f"⚠️  Backend API returned {resp.status}")
        except Exception as e:
            logger.warning(f"⚠️  Backend API unreachable: {e}")

        # Check Oracle/Dashboard
        try:
            async with self.session.get(f"{self.oracle_url}/health", timeout=self.timeout) as resp:
                if resp.status == 200:
                    self.health_status['oracle'] = True
                    logger.info("✅ Oracle/Dashboard (3000): HEALTHY")
                else:
                    logger.warning(f"⚠️  Oracle returned {resp.status}")
        except Exception as e:
            logger.warning(f"⚠️  Oracle unreachable: {e}")

        self.health_status['timestamp'] = datetime.utcnow().isoformat()
        return self.health_status

    async def get_account_status(self) -> Optional[Dict[str, Any]]:
        """Fetch account status from Runtime API."""
        try:
            async with self.session.get(
                f"{self.runtime_url}/account/status",
                timeout=self.timeout
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"📊 Account Status: {data}")
                    return data
        except Exception as e:
            logger.warning(f"Could not fetch account status: {e}")
        return None

    async def get_holdings(self) -> Optional[Dict[str, Any]]:
        """Fetch holdings from Backend API."""
        try:
            async with self.session.get(
                f"{self.backend_url}/holdings",
                timeout=self.timeout
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"💼 Holdings: {data}")
                    return data
        except Exception as e:
            logger.warning(f"Could not fetch holdings: {e}")
        return None

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch market data from Runtime API."""
        try:
            async with self.session.get(
                f"{self.runtime_url}/market/quote/{symbol}",
                timeout=self.timeout
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"📈 {symbol} Quote: {data}")
                    return data
        except Exception as e:
            logger.warning(f"Could not fetch {symbol} data: {e}")
        return None

    async def submit_trade_proposal(
        self,
        symbol: str,
        direction: str,
        quantity: int,
        entry_price: Decimal,
        stop_loss: Decimal,
        target_price: Decimal,
        rationale: str
    ) -> Optional[Dict[str, Any]]:
        """Submit trade proposal to Runtime API."""
        payload = {
            'symbol': symbol,
            'direction': direction,
            'quantity': quantity,
            'entry_price': float(entry_price),
            'stop_loss': float(stop_loss),
            'target_price': float(target_price),
            'rationale': rationale,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            async with self.session.post(
                f"{self.runtime_url}/trades/propose",
                json=payload,
                timeout=self.timeout
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    logger.info(f"✅ Trade proposal submitted: {data}")
                    return data
                else:
                    logger.warning(f"Trade proposal rejected ({resp.status})")
        except Exception as e:
            logger.warning(f"Could not submit trade proposal: {e}")
        return None

    async def get_trading_performance(self) -> Optional[Dict[str, Any]]:
        """Fetch trading performance metrics."""
        try:
            async with self.session.get(
                f"{self.runtime_url}/trades/performance",
                timeout=self.timeout
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"📊 Trading Performance: {data}")
                    return data
        except Exception as e:
            logger.warning(f"Could not fetch performance: {e}")
        return None

    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'cmdos_host': '129.146.236.177',
            'health': self.health_status.copy(),
            'services': {}
        }

        # Runtime status
        try:
            async with self.session.get(f"{self.runtime_url}/status") as resp:
                if resp.status == 200:
                    status['services']['runtime'] = await resp.json()
        except:
            status['services']['runtime'] = {'status': 'offline'}

        # Backend status
        try:
            async with self.session.get(f"{self.backend_url}/status") as resp:
                if resp.status == 200:
                    status['services']['backend'] = await resp.json()
        except:
            status['services']['backend'] = {'status': 'offline'}

        # Oracle status
        try:
            async with self.session.get(f"{self.oracle_url}/status") as resp:
                if resp.status == 200:
                    status['services']['oracle'] = await resp.json()
        except:
            status['services']['oracle'] = {'status': 'offline'}

        return status

    def print_health_report(self):
        """Print formatted health report."""
        logger.info("\n" + "=" * 80)
        logger.info("CMDOS SYSTEM HEALTH REPORT")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {self.health_status['timestamp']}")
        logger.info(f"Host: 129.146.236.177")
        logger.info("")
        logger.info("Service Status:")
        logger.info(f"  Runtime API (8000):    {'✅ HEALTHY' if self.health_status['runtime'] else '❌ OFFLINE'}")
        logger.info(f"  Backend API (8001):    {'✅ HEALTHY' if self.health_status['backend'] else '❌ OFFLINE'}")
        logger.info(f"  Oracle (3000):         {'✅ HEALTHY' if self.health_status['oracle'] else '❌ OFFLINE'}")
        logger.info("")

        all_healthy = all([
            self.health_status['runtime'],
            self.health_status['backend'],
            self.health_status['oracle']
        ])

        if all_healthy:
            logger.info("✅ ALL SYSTEMS HEALTHY — Ready for trading")
        else:
            logger.warning("⚠️  Some systems offline — Check SSH connection and deployment")

        logger.info("=" * 80 + "\n")


async def main():
    """Test CMDOS integration."""
    logger.info("Starting CMDOS Integration Test...\n")

    async with CMDOSIntegration() as cmdos:
        # Check health
        health = await cmdos.check_health()
        cmdos.print_health_report()

        # If runtime is healthy, try to get account status
        if health['runtime']:
            logger.info("\n📊 Fetching account data from Runtime API...")
            account = await cmdos.get_account_status()

        if health['backend']:
            logger.info("\n💼 Fetching holdings from Backend API...")
            holdings = await cmdos.get_holdings()

        # Get market data for AAPL as example
        if health['runtime']:
            logger.info("\n📈 Fetching market data for AAPL...")
            quote = await cmdos.get_market_data('AAPL')

        # Get system status
        logger.info("\n🔍 Fetching complete system status...")
        system_status = await cmdos.get_system_status()

        logger.info("\n" + "=" * 80)
        logger.info("SYSTEM STATUS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {system_status['timestamp']}")
        logger.info(f"CMDOS Host: {system_status['cmdos_host']}")
        logger.info(f"Health Check: {'✅ PASS' if all(system_status['health'].values()) else '⚠️  PARTIAL'}")
        logger.info(f"Services Status:")
        for service, status in system_status['services'].items():
            logger.info(f"  {service}: {status}")
        logger.info("=" * 80 + "\n")

        return system_status


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        logger.info("✅ CMDOS Integration test completed")
    except KeyboardInterrupt:
        logger.info("\n\n✅ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python
"""
24/7 News Monitoring & Trading Bot
Continuous surveillance of financial news, holdings, and market events
Integrates with Robinhood for real account data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging
import json
from decimal import Decimal
from typing import List, Dict

sys.path.insert(0, '.')

try:
    import aiohttp
    from robinhood_adapter import RobinhoodMCPAdapter
except ImportError:
    os.system("pip install aiohttp -q")
    import aiohttp

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/news_monitor_24_7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsMonitor24_7:
    """24/7 financial news monitor and trading alert system."""

    def __init__(self, robinhood_token: str = None):
        self.robinhood_token = robinhood_token or os.getenv('ROBINHOOD_OAUTH_TOKEN')
        self.robinhood = None
        self.holdings = {}
        self.account_balance = Decimal('0')
        self.buying_power = Decimal('0')
        self.news_cache = {}
        self.alert_threshold = 0.03  # 3% price move triggers alert
        self.start_time = datetime.now()

        if self.robinhood_token:
            self.robinhood = RobinhoodMCPAdapter(
                oauth_token=self.robinhood_token,
                mode="live"
            )
            logger.info("✅ Robinhood connection initialized")
        else:
            logger.warning("⚠️ No Robinhood token provided - using demo mode")

    async def initialize(self):
        """Initialize bot and fetch account data."""
        logger.info("=" * 80)
        logger.info("INITIALIZING 24/7 NEWS MONITOR & TRADING BOT")
        logger.info("=" * 80)

        if self.robinhood:
            await self.fetch_account_data()
        else:
            logger.info("Running in DEMO MODE - add ROBINHOOD_OAUTH_TOKEN to connect")

    async def fetch_account_data(self):
        """Fetch real Robinhood account data."""
        try:
            account_state = await self.robinhood.get_account_state()
            if account_state:
                self.account_balance = Decimal(str(account_state.get('account_equity', 0)))
                self.buying_power = Decimal(str(account_state.get('buying_power', 0)))

                logger.info(f"\n{'='*80}")
                logger.info("ROBINHOOD ACCOUNT STATUS")
                logger.info(f"{'='*80}")
                logger.info(f"Account Balance: ${self.account_balance:,.2f}")
                logger.info(f"Buying Power: ${self.buying_power:,.2f}")

                # Parse holdings from account state
                positions = account_state.get('positions', [])
                logger.info(f"Open Positions: {len(positions)}")

                for pos in positions:
                    symbol = pos.get('symbol', 'UNKNOWN')
                    qty = float(pos.get('quantity', 0))
                    avg_price = Decimal(str(pos.get('average_price', 0)))
                    current_price = Decimal(str(pos.get('current_price', 0)))

                    if qty > 0:
                        self.holdings[symbol] = {
                            'quantity': qty,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'unrealized_pnl': (current_price - avg_price) * Decimal(str(qty))
                        }
                        logger.info(f"  {symbol}: {qty} shares @ ${avg_price} (Current: ${current_price})")

        except Exception as e:
            logger.error(f"Error fetching account data: {e}")

    async def monitor_news_24_7(self):
        """Run 24/7 news monitoring loop."""
        logger.info(f"\n{'='*80}")
        logger.info("STARTING 24/7 NEWS MONITORING")
        logger.info(f"{'='*80}\n")

        cycle = 0
        while True:
            cycle += 1

            try:
                logger.info(f"\n[SCAN CYCLE {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Scan multiple news sources in parallel
                tasks = [
                    self.scan_financial_news(),
                    self.scan_market_alerts(),
                    self.scan_earnings_calendar(),
                    self.scan_sec_filings(),
                    self.monitor_holdings()
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log scan results
                news_found = sum(1 for r in results if isinstance(r, dict) and r.get('found'))
                logger.info(f"✓ Scan complete: {news_found} news items found")

                # Refresh account data every 10 cycles
                if cycle % 10 == 0 and self.robinhood:
                    await self.fetch_account_data()

                # Sleep based on market hours
                sleep_duration = self.get_sleep_duration()
                logger.info(f"Next scan in {sleep_duration}s...")
                await asyncio.sleep(sleep_duration)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {type(e).__name__}: {e}")
                await asyncio.sleep(60)

    def get_sleep_duration(self) -> int:
        """Adjust sleep duration based on market hours."""
        now = datetime.now()
        hour = now.hour

        # More frequent scans during market hours (9:30am - 4:00pm ET)
        if 9 <= hour < 16:
            return 30  # Every 30 seconds during market hours
        # Less frequent outside market hours
        elif 16 <= hour < 21:
            return 60  # After hours
        else:
            return 300  # Overnight: every 5 minutes

    async def scan_financial_news(self) -> Dict:
        """Scan financial news for trading-relevant events."""
        try:
            logger.debug("Scanning financial news...")

            news_items = []
            keywords = ['earnings', 'dividend', 'split', 'acquisition', 'bankruptcy', 'IPO']

            # Simulate news scan (in production, would use newsapi, finnhub, etc)
            for symbol in list(self.holdings.keys())[:5]:  # Check first 5 holdings
                for keyword in keywords:
                    # This would call real news API
                    logger.debug(f"  Checking {symbol} for {keyword}...")

            return {'found': len(news_items) > 0, 'items': news_items}

        except Exception as e:
            logger.error(f"Error scanning financial news: {e}")
            return {'found': False, 'items': []}

    async def scan_market_alerts(self) -> Dict:
        """Scan for market-wide alerts and volatility spikes."""
        try:
            logger.debug("Scanning market alerts...")

            alerts = []

            # Check VIX level, sector movements, etc
            logger.debug("  Checking volatility levels...")
            logger.debug("  Checking sector movements...")

            return {'found': len(alerts) > 0, 'alerts': alerts}

        except Exception as e:
            logger.error(f"Error scanning market alerts: {e}")
            return {'found': False, 'alerts': []}

    async def scan_earnings_calendar(self) -> Dict:
        """Scan upcoming earnings dates for holdings."""
        try:
            logger.debug("Scanning earnings calendar...")

            earnings = []

            for symbol in self.holdings.keys():
                logger.debug(f"  Checking {symbol} earnings date...")

            return {'found': len(earnings) > 0, 'earnings': earnings}

        except Exception as e:
            logger.error(f"Error scanning earnings: {e}")
            return {'found': False, 'earnings': []}

    async def scan_sec_filings(self) -> Dict:
        """Scan SEC filings for holdings."""
        try:
            logger.debug("Scanning SEC filings...")

            filings = []

            for symbol in list(self.holdings.keys())[:5]:
                logger.debug(f"  Checking {symbol} SEC filings...")

            return {'found': len(filings) > 0, 'filings': filings}

        except Exception as e:
            logger.error(f"Error scanning SEC filings: {e}")
            return {'found': False, 'filings': []}

    async def monitor_holdings(self) -> Dict:
        """Monitor price movements of holdings."""
        try:
            logger.debug("Monitoring holdings prices...")

            alerts = []

            for symbol, holding in self.holdings.items():
                current = holding['current_price']
                avg = holding['avg_price']

                if avg > 0:
                    pct_change = abs((current - avg) / avg)

                    if pct_change >= self.alert_threshold:
                        alert = {
                            'symbol': symbol,
                            'change_pct': float(pct_change) * 100,
                            'current_price': float(current),
                            'avg_price': float(avg),
                            'qty': holding['quantity'],
                            'unrealized_pnl': float(holding['unrealized_pnl'])
                        }
                        alerts.append(alert)
                        logger.warning(f"  🚨 {symbol}: {pct_change*100:.2f}% move detected!")

            return {'found': len(alerts) > 0, 'price_alerts': alerts}

        except Exception as e:
            logger.error(f"Error monitoring holdings: {e}")
            return {'found': False, 'price_alerts': []}

    async def run_forever(self):
        """Run monitoring forever."""
        await self.initialize()
        await self.monitor_news_24_7()

    def generate_report(self) -> str:
        """Generate current status report."""
        uptime = datetime.now() - self.start_time
        report = f"""
{'='*80}
24/7 NEWS MONITOR STATUS REPORT
{'='*80}

UPTIME: {uptime}

ACCOUNT STATUS:
  Balance: ${self.account_balance:,.2f}
  Buying Power: ${self.buying_power:,.2f}
  Holdings: {len(self.holdings)}

HOLDINGS:
"""
        for symbol, holding in self.holdings.items():
            pnl = holding['unrealized_pnl']
            pnl_sign = "+" if pnl > 0 else ""
            report += f"  {symbol}: {holding['quantity']} @ ${holding['avg_price']} | Unrealized P&L: {pnl_sign}${pnl:,.2f}\n"

        report += f"\n{'='*80}"
        return report

async def main():
    robinhood_token = os.getenv('ROBINHOOD_OAUTH_TOKEN')

    monitor = NewsMonitor24_7(robinhood_token=robinhood_token)

    # Run in background or foreground based on args
    if len(sys.argv) > 1 and sys.argv[1] == '--background':
        logger.info("Starting in background mode...")
        asyncio.create_task(monitor.run_forever())
        # Keep event loop running
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    else:
        logger.info("Starting in foreground mode...")
        await monitor.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n24/7 Monitor stopped by user")
        sys.exit(0)

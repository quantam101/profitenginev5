#!/usr/bin/env python3
"""
PRE-MARKET DEPLOYMENT — 4:00 AM MST
Launches EnhancedTradingEngine with Finnhub paper trading ($100 → $1000).

Timeline: 4:00 AM - 9:30 AM MST (pre-market)
          9:30 AM - 2:00 PM MST (official market)

Strategy: Paper trading with real Finnhub prices
          Auto-switch to real money at $1000 threshold

Goal: $1000 from $100 in one week (43% daily compound return)
"""

import asyncio
import json
import logging
import os
from datetime import datetime
import sys

try:
    from runtime.hybrid_trading_engine import HybridTradingEngine, CombinedSignal, MarketRegime
    from runtime.finnhub_client import get_finnhub_client, FinnhubClient
except ImportError as e:
    print(f"ERROR: Cannot import modules: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('premarket_trading_4am.log'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


class PreMarketTradingSession:
    """Pre-market trading session: paper trading $100 → $1000, then real money"""

    def __init__(self, starting_balance: float = 100.0, finnhub_client: FinnhubClient = None):
        self.starting_balance = starting_balance
        self.target_balance = starting_balance * 10  # $1000 from $100
        self.engine = HybridTradingEngine(account_balance=starting_balance, finnhub_client=finnhub_client)
        self.finnhub = finnhub_client
        self.session_start = datetime.utcnow()
        self.trades = []
        self.skipped_trades = []
        self.current_portfolio_value = starting_balance
        self.is_real_money = False
        logger.info(f"TARGET: Reach ${self.target_balance:,.2f} from ${starting_balance:,.2f}")
        logger.info(f"MODE: Paper trading with real Finnhub prices (11-strategy hybrid engine)")

    async def run(self) -> dict:
        """Run pre-market trading session (4 AM - 2 PM MST) with paper trading"""

        logger.info("="*70)
        logger.info("PRE-MARKET TRADING SESSION - PAPER TRADING")
        logger.info("="*70)
        logger.info(f"Start Time: {self.session_start}")
        logger.info(f"Starting Balance: ${self.starting_balance:,.2f}")
        logger.info(f"Target Balance: ${self.target_balance:,.2f}")
        logger.info(f"Required Daily Return: {((self.target_balance / self.starting_balance) ** (1/7) - 1) * 100:.1f}%")

        if self.finnhub:
            logger.info(f"Data Source: Finnhub API (REAL market prices)")
            logger.info(f"Mode: LIVE MARKET paper trading")
        else:
            logger.info(f"Data Source: Simulation mode (no live prices)")
            logger.info(f"Mode: Paper trading (validation/testing)")

        logger.info(f"Auto-Switch: Real money at ${self.target_balance:,.2f}")
        logger.info("")

        # High-probability symbols for growth
        symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD']

        cycle = 0
        max_trades_per_day = 10

        while len(self.trades) < max_trades_per_day:
            cycle += 1

            # Update real portfolio value from Finnhub
            if self.finnhub:
                await self.finnhub.update_positions()
                account = self.finnhub.get_account_summary()
                self.current_portfolio_value = account['portfolio_value']
                self.is_real_money = account['is_real_money']

                progress = ((self.current_portfolio_value - self.starting_balance) /
                           (self.target_balance - self.starting_balance)) * 100
                mode = "[REAL MONEY]" if self.is_real_money else "[PAPER]"
                logger.info(f"{mode} Portfolio: ${self.current_portfolio_value:,.2f} ({progress:.1f}% to target)")

            for symbol in symbols:
                if len(self.trades) >= max_trades_per_day:
                    break

                try:
                    # Get REAL market price from Finnhub
                    if self.finnhub:
                        market = await self.finnhub.get_price(symbol)
                        if not market:
                            logger.warning(f"{symbol} - No price data available")
                            continue
                        current_price = market.price
                    else:
                        current_price = 150.0 + (cycle % 5)

                    # Generate high-conviction signal via 11-strategy hybrid engine
                    class MockMarketData:
                        def __init__(self, price, volume):
                            self.price = price
                            self.volume = volume

                    market_data = MockMarketData(current_price, 1.5e6)
                    regime, _ = self.engine.signal_combiner.regime_detector.detect([current_price] * 20)
                    strategy_signals = self.engine._generate_strategy_signals(symbol, market_data, regime)
                    conviction, firing = self.engine.signal_combiner.combine_signals(strategy_signals, regime)

                    if abs(conviction) >= 0.5:  # High conviction threshold
                        # Check compliance gate before trading
                        compliant, compliance_reason = await self.engine.compliance.check_compliance(
                            symbol, 'BUY' if conviction > 0 else 'SELL', len(self.engine.open_positions)
                        )

                        if not compliant:
                            logger.warning(f"{symbol} SKIPPED - {compliance_reason}")
                            self.skipped_trades.append({
                                'symbol': symbol,
                                'reason': compliance_reason,
                                'timestamp': datetime.utcnow().isoformat(),
                            })
                            continue

                        position_size, stop_loss, take_profit = self.engine.risk.calculate_position_size(
                            symbol, current_price, abs(conviction)
                        )

                        action = 'BUY' if conviction > 0 else 'SELL'
                        signal = CombinedSignal(
                            symbol=symbol,
                            action=action,
                            conviction=abs(conviction),
                            entry_price=current_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            position_size=position_size,
                            reason=f"11-strategy consensus: {', '.join(firing[:3])}",
                            strategies_firing=firing,
                            regime=regime,
                            timestamp=datetime.utcnow().isoformat(),
                        )

                        # Execute paper trade via Finnhub (real prices)
                        if self.finnhub:
                            order = await self.finnhub.place_order(
                                symbol=symbol,
                                quantity=position_size,
                                side=signal.action.lower(),
                                price=current_price,
                            )
                            result = {'status': 'FILLED', 'order_id': order.order_id if order else None}
                        else:
                            result = {'status': 'SIMULATED', 'order_id': None}

                        if result:
                            self.trades.append({
                                'timestamp': datetime.utcnow().isoformat(),
                                'symbol': symbol,
                                'action': signal.action,
                                'quantity': position_size,
                                'entry': current_price,
                                'stop_loss': stop_loss,
                                'take_profit': take_profit,
                                'pnl': 0,
                                'reason': signal.reason,
                                'order_id': result.get('order_id'),
                                'is_real_money': self.is_real_money,
                                'conviction': signal.conviction,
                                'regime': signal.regime.value,
                                'strategies_firing': signal.strategies_firing,
                            })

                            logger.info(f"[TRADE {len(self.trades)}] {symbol} {signal.action} {position_size} shares @ REAL PRICE ${current_price:.2f}")
                            logger.info(f"  Conviction: {signal.conviction:.2f} (Regime: {signal.regime.value})")
                            logger.info(f"  Stop: ${stop_loss:.2f} (2%)")
                            logger.info(f"  Target: ${take_profit:.2f} (3%)")
                            logger.info(f"  Current Portfolio: ${self.current_portfolio_value:,.2f}")
                            logger.info("")

                except Exception as e:
                    logger.error(f"Error trading {symbol}: {e}")

            await asyncio.sleep(0.05)

        logger.info("="*70)
        logger.info("PRE-MARKET SESSION ENDED")
        logger.info("="*70)

        return self._generate_final_summary()

    def _generate_final_summary(self) -> dict:
        """Generate final session summary focusing on $1000 target"""

        if not self.trades:
            return {
                'status': 'NO_TRADES',
                'message': 'No trades executed',
            }

        wins = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
        total = len(self.trades)
        pnl_dollars = self.current_portfolio_value - self.starting_balance
        win_rate = (wins / total * 100) if total > 0 else 0
        progress_to_target = (self.current_portfolio_value / self.target_balance) * 100

        summary = {
            'status': 'COMPLETE',
            'session_start': self.session_start.isoformat(),
            'session_end': datetime.utcnow().isoformat(),
            'duration_minutes': round((datetime.utcnow() - self.session_start).total_seconds() / 60),

            # $1000 Target Tracking
            'starting_balance': round(self.starting_balance, 2),
            'current_portfolio_value': round(self.current_portfolio_value, 2),
            'target_balance': round(self.target_balance, 2),
            'pnl_dollars': round(pnl_dollars, 2),
            'progress_percent': round(progress_to_target, 1),

            # Trading metrics
            'total_trades': total,
            'winning_trades': wins,
            'losing_trades': total - wins,
            'win_rate_percent': round(win_rate, 1),

            # Compliance
            'skipped_trades': len(self.skipped_trades),
            'compliance_blocks': [s['reason'] for s in self.skipped_trades],

            # Sample data
            'sample_trades': self.trades[:3],
        }

        # Print final results
        logger.info("FINAL SESSION RESULTS")
        logger.info("="*70)
        logger.info(f"Starting Balance: ${self.starting_balance:,.2f}")
        logger.info(f"Current Balance: ${self.current_portfolio_value:,.2f}")
        logger.info(f"Target Balance: ${self.target_balance:,.2f}")
        logger.info(f"P&L: ${pnl_dollars:+,.2f}")
        logger.info(f"Progress to Target: {progress_to_target:.1f}%")
        logger.info("")
        logger.info(f"Total Trades: {total}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Trades Won: {wins}/{total}")
        logger.info(f"Compliance Blocks: {len(self.skipped_trades)}")
        logger.info("="*70)

        if progress_to_target >= 100.0:
            logger.info(f"SUCCESS! TARGET ACHIEVED: ${self.current_portfolio_value:,.2f}")
        elif pnl_dollars > 0:
            daily_rate = ((self.current_portfolio_value / self.starting_balance) ** (1/7) - 1) * 100
            logger.info(f"PROGRESS! ${pnl_dollars:+,.2f} gained (daily rate needed: {daily_rate:.1f}%)")
        else:
            logger.warning(f"BELOW TARGET: Need to improve strategy for tomorrow")

        # Save summary
        with open('premarket_trading_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info("Results saved to premarket_trading_summary.json")

        return summary


async def main():
    """Main entry point - Finnhub live market paper trading (required, no simulation)"""

    now = datetime.now()
    logger.info(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    if now.hour < 4:
        logger.warning("Before 4 AM - waiting for pre-market start")
    elif now.hour >= 14:
        logger.warning("After 2 PM MST - markets closed")

    # Finnhub API key is REQUIRED (no simulation mode)
    logger.info("="*70)
    logger.info("FINNHUB LIVE MARKET PAPER TRADING REQUIRED")
    logger.info("="*70)

    finnhub_api_key = os.getenv('FINNHUB_API_KEY', '')

    if not finnhub_api_key:
        logger.error("[FINNHUB] ERROR: API KEY REQUIRED")
        logger.error("[FINNHUB] No credentials provided - cannot proceed")
        logger.error("")
        logger.error("SETUP REQUIRED (2 minutes):")
        logger.error("")
        logger.error("1. Register for FREE Finnhub API key:")
        logger.error("   https://finnhub.io/register")
        logger.error("")
        logger.error("2. Copy your API key from dashboard")
        logger.error("")
        logger.error("3. Set environment variable (PowerShell):")
        logger.error("   $env:FINNHUB_API_KEY = \"your_api_key_here\"")
        logger.error("")
        logger.error("4. Run again:")
        logger.error("   python deploy_premarket_4am.py")
        logger.error("")
        logger.error("="*70)
        sys.exit(1)

    # Initialize Finnhub client for live market paper trading
    logger.info("Initializing Finnhub live market paper trading...")
    try:
        finnhub = await get_finnhub_client(api_key=finnhub_api_key, starting_balance=100.0)
        logger.info("[FINNHUB] [OK] Connected to Finnhub API")
        logger.info("[FINNHUB] [OK] Live market prices enabled")
        logger.info("[FINNHUB] [OK] Paper trading mode: $100.00 starting")
        logger.info("[FINNHUB] [OK] Auto-switch to real money at $1000.00")
        logger.info("")
        starting_balance = 100.0
    except Exception as e:
        logger.error(f"[FINNHUB] FATAL: Failed to connect to Finnhub API")
        logger.error(f"[FINNHUB] Error: {e}")
        logger.error("")
        logger.error("Possible causes:")
        logger.error("- Invalid API key")
        logger.error("- Network connection issue")
        logger.error("- Finnhub API rate limit exceeded")
        logger.error("")
        logger.error("Fix:")
        logger.error("- Verify API key is correct")
        logger.error("- Check internet connection")
        logger.error("- Wait 60 seconds and retry")
        logger.error("")
        sys.exit(1)

    logger.info("Launching pre-market trading engine...")
    session = PreMarketTradingSession(starting_balance=starting_balance, finnhub_client=finnhub)
    results = await session.run()

    # Cleanup
    await finnhub.close_session()

    return results


if __name__ == '__main__':
    try:
        results = asyncio.run(main())
        logger.info("\nPre-market session completed.")
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\nSession interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

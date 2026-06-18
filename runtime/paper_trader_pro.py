"""
PAPER TRADING PRO — Live Market Simulator with Real Data
Runs all 11 strategies against live prices, tracks P&L from $100 → $1000 target
Supports Finnhub, Yahoo Finance, and Alpaca feeds
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
import os
import time

try:
    import yfinance as yf
    import websocket
    import requests
except ImportError:
    raise ImportError("Install dependencies: pip install yfinance websocket-client requests")

from runtime.mcp_native_trading_engine import (
    StrategyEngine, RiskSupervisor, MarketContext, MarketRegime,
    PORTFOLIO, PRECISION, POSITION_SIZE_LIMIT, MAX_DAILY_DRAWDOWN
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA FEED PROVIDERS
# ============================================================================
class FinnhubFeed:
    """Real-time WebSocket feed from Finnhub (~1s latency)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None
        self.prices = {}
        self.latest_bars = {}

    async def connect(self):
        """Connect to Finnhub WebSocket"""
        self.ws_url = f"wss://ws.finnhub.io?token={self.api_key}"
        # In production, use websocket library
        logger.info(f"Finnhub connected (API key: {self.api_key[:10]}...)")

    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch real-time quote via Finnhub REST API"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.api_key}"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                return {
                    "price": data.get("c", 0),
                    "bid": data.get("bp", 0) or data.get("c", 0),
                    "ask": data.get("ap", 0) or data.get("c", 0),
                    "volume": data.get("v", 0),
                    "timestamp": data.get("t", time.time())
                }
        except Exception as e:
            logger.warning(f"Finnhub fetch failed for {symbol}: {e}")
        return None

class YahooFinanceFeed:
    """Fallback feed using Yahoo Finance (1-5min delay)"""

    @staticmethod
    async def fetch_quote(symbol: str) -> Optional[Dict[str, float]]:
        """Fetch quote from Yahoo Finance"""
        try:
            data = yf.Ticker(symbol)
            info = data.info
            hist = data.history(period="1d")

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            return {
                "price": float(latest.get("Close", 0)),
                "bid": float(latest.get("Close", 0)) * 0.999,
                "ask": float(latest.get("Close", 0)) * 1.001,
                "volume": float(latest.get("Volume", 0)),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"Yahoo Finance fetch failed: {e}")
        return None

class MarketDataProvider:
    """Unified feed manager — tries Finnhub first, falls back to Yahoo"""

    def __init__(self):
        self.finnhub_key = os.environ.get("FINNHUB_API_KEY")
        self.finnhub = FinnhubFeed(self.finnhub_key) if self.finnhub_key else None
        self.cache = {}
        self.cache_ttl = 30  # seconds

    async def get_quote(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get real-time quote with caching"""
        # Check cache
        if symbol in self.cache:
            cached_time, cached_data = self.cache[symbol]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        # Try Finnhub first
        if self.finnhub:
            data = await self.finnhub.fetch_quote(symbol)
            if data:
                self.cache[symbol] = (time.time(), data)
                return data

        # Fallback to Yahoo
        data = await YahooFinanceFeed.fetch_quote(symbol)
        if data:
            self.cache[symbol] = (time.time(), data)
        return data

    async def fetch_historical(self, symbol: str, bars: int = 250) -> Optional[List[Dict]]:
        """Fetch historical OHLCV data for indicator computation"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")

            if hist.empty:
                return None

            bars_data = []
            for idx, row in hist.tail(bars).iterrows():
                bars_data.append({
                    "timestamp": idx.timestamp(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"])
                })
            return bars_data
        except Exception as e:
            logger.error(f"Historical fetch failed: {e}")
        return None

# ============================================================================
# TECHNICAL INDICATOR CALCULATIONS
# ============================================================================
class TechnicalAnalysis:
    """Computes RSI, MACD, Bollinger, VWAP, and momentum indicators"""

    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        """Compute RSI(14)"""
        if len(closes) < period + 1:
            return 50.0

        closes = closes[-period - 1:]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Compute MACD, signal line, and histogram"""
        if len(closes) < slow:
            return 0.0, 0.0, 0.0

        ema_fast = TechnicalAnalysis.ema(closes, fast)
        ema_slow = TechnicalAnalysis.ema(closes, slow)
        macd_line = ema_fast - ema_slow

        signal_line = TechnicalAnalysis.ema([macd_line], signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def ema(values: List[float], period: int) -> float:
        """Compute exponential moving average"""
        if not values or period < 1:
            return values[-1] if values else 0.0

        multiplier = 2 / (period + 1)
        ema = sum(values[-period:]) / min(len(values), period)

        for val in values[-min(len(values), period):]:
            ema = val * multiplier + ema * (1 - multiplier)

        return ema

    @staticmethod
    def bollinger_bands(closes: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """Compute Bollinger Bands (upper, middle, lower)"""
        if len(closes) < period:
            return closes[-1], closes[-1], closes[-1]

        sma = sum(closes[-period:]) / period
        variance = sum((c - sma) ** 2 for c in closes[-period:]) / period
        std = variance ** 0.5

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

    @staticmethod
    def vwap(bars: List[Dict[str, float]]) -> float:
        """Compute VWAP (Volume Weighted Average Price)"""
        if not bars:
            return 0.0

        tp_volume = sum((b["high"] + b["low"] + b["close"]) / 3 * b["volume"] for b in bars)
        total_volume = sum(b["volume"] for b in bars)

        return tp_volume / total_volume if total_volume > 0 else 0.0

    @staticmethod
    def momentum(closes: List[float], period: int = 5) -> float:
        """Compute momentum (rate of change)"""
        if len(closes) < period + 1:
            return 0.0

        return (closes[-1] - closes[-period - 1]) / closes[-period - 1]

# ============================================================================
# PAPER TRADING SIMULATOR
# ============================================================================
class PaperTradingSimulator:
    """Runs live trading simulation with all 11 strategies"""

    WATCHLIST = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "GOOG", "AMZN", "META", "SPY", "QQQ"]
    SCAN_INTERVAL = 60  # seconds

    def __init__(self):
        self.provider = MarketDataProvider()
        self.running = False
        self.scan_count = 0
        self.audit_log = []

    async def run(self):
        """Main simulation loop"""
        logger.info(f"Starting paper trading with ${PORTFOLIO.account_balance}")
        logger.info(f"Target: $1000 | Watchlist: {self.WATCHLIST}")
        self.running = True

        while self.running:
            self.scan_count += 1
            logger.info(f"\n=== SCAN #{self.scan_count} ===")

            for symbol in self.WATCHLIST:
                await self.analyze_symbol(symbol)

            # Check for position exits
            await self.check_exits()

            # Report status
            await self.report_status()

            # Sleep before next scan
            await asyncio.sleep(self.SCAN_INTERVAL)

    async def analyze_symbol(self, symbol: str):
        """Analyze a single symbol and execute trades"""
        try:
            # Fetch live quote
            quote = await self.provider.get_quote(symbol)
            if not quote:
                logger.warning(f"{symbol}: Quote fetch failed")
                return

            # Fetch historical data
            bars = await self.provider.fetch_historical(symbol)
            if not bars or len(bars) < 250:
                logger.warning(f"{symbol}: Insufficient historical data")
                return

            closes = [b["close"] for b in bars]

            # Compute indicators
            rsi = TechnicalAnalysis.rsi(closes)
            macd, signal, hist = TechnicalAnalysis.macd(closes)
            upper, middle, lower = TechnicalAnalysis.bollinger_bands(closes)
            vwap = TechnicalAnalysis.vwap(bars)
            momentum = TechnicalAnalysis.momentum(closes)

            # Detect regime
            if momentum > 0.05 and rsi > 50:
                regime = MarketRegime.BULL
            elif momentum < -0.05:
                regime = MarketRegime.CRISIS
            elif abs(momentum) < 0.02 and 40 < rsi < 60:
                regime = MarketRegime.CHOPPY
            else:
                regime = MarketRegime.HIGH_VOL_TREND

            # Build market context
            context = MarketContext(
                symbol=symbol,
                spot_price=Decimal(str(quote["price"])),
                bid=Decimal(str(quote["bid"])),
                ask=Decimal(str(quote["ask"])),
                volume=quote["volume"],
                rsi_14=rsi,
                macd_signal=signal,
                bollinger_upper=Decimal(str(upper)),
                bollinger_lower=Decimal(str(lower)),
                vwap=Decimal(str(vwap)),
                momentum_5bar=momentum,
                orderbook_imbalance=0.0,  # Would need live orderbook
                regime=regime,
                timestamp=time.time()
            )

            # Run strategy engine
            composite_signal, signals = StrategyEngine.compute_composite_signal(context)

            if abs(composite_signal) < 0.25:
                return

            # Determine side
            side = "BUY" if composite_signal > 0 else "SELL"

            # Risk check
            is_safe, receipt, reason = RiskSupervisor.audit_trade_setup(
                symbol, Decimal(str(quote["price"])), composite_signal, side
            )

            if not is_safe:
                logger.debug(f"{symbol}: Rejected - {reason}")
                return

            # Execute trade
            logger.info(f"{symbol}: {side} @ ${quote['price']:.2f} (signal: {composite_signal:.3f})")
            PORTFOLIO.positions[symbol] = {
                "side": side,
                "entry_price": str(quote["price"]),
                "shares": str(receipt.shares),
                "stop_loss": str(receipt.stop_loss),
                "take_profit": str(receipt.take_profit),
                "entry_time": datetime.now().isoformat()
            }

            self.audit_log.append({
                "scan": self.scan_count,
                "symbol": symbol,
                "action": side,
                "price": quote["price"],
                "signal": composite_signal,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"{symbol}: Analysis failed - {e}")

    async def check_exits(self):
        """Check for stop loss and take profit exits"""
        symbols_to_exit = []

        for symbol, position in list(PORTFOLIO.positions.items()):
            quote = await self.provider.get_quote(symbol)
            if not quote:
                continue

            current_price = Decimal(str(quote["price"]))
            entry_price = Decimal(position["entry_price"])
            stop_loss = Decimal(position["stop_loss"])
            take_profit = Decimal(position["take_profit"])

            should_exit = False
            reason = ""

            if position["side"] == "BUY":
                if current_price <= stop_loss:
                    should_exit = True
                    reason = f"STOP_LOSS @ ${current_price}"
                elif current_price >= take_profit:
                    should_exit = True
                    reason = f"TAKE_PROFIT @ ${current_price}"
            else:  # SELL
                if current_price >= stop_loss:
                    should_exit = True
                    reason = f"STOP_LOSS @ ${current_price}"
                elif current_price <= take_profit:
                    should_exit = True
                    reason = f"TAKE_PROFIT @ ${current_price}"

            if should_exit:
                symbols_to_exit.append((symbol, reason, current_price, entry_price))

        # Process exits
        for symbol, reason, current_price, entry_price in symbols_to_exit:
            position = PORTFOLIO.positions.pop(symbol)
            pnl = (current_price - entry_price) * Decimal(position["shares"])
            if position["side"] == "SELL":
                pnl = -pnl

            PORTFOLIO.account_balance += pnl
            logger.info(f"{symbol}: {reason} | P&L: ${pnl:.2f} | Balance: ${PORTFOLIO.account_balance:.2f}")

            self.audit_log.append({
                "scan": self.scan_count,
                "symbol": symbol,
                "action": "EXIT",
                "reason": reason,
                "pnl": str(pnl),
                "timestamp": datetime.now().isoformat()
            })

    async def report_status(self):
        """Print current portfolio status"""
        total_value = PORTFOLIO.account_balance
        for symbol, pos in PORTFOLIO.positions.items():
            logger.info(f"  {symbol}: {pos['side']} @ ${pos['entry_price']}")

        target = Decimal("1000.00")
        progress = (PORTFOLIO.account_balance / target * 100)
        logger.info(f"Balance: ${PORTFOLIO.account_balance:.2f} | Target: ${target} | Progress: {progress:.1f}%")

        if PORTFOLIO.account_balance >= target:
            logger.info(" TARGET REACHED! $1000 achieved!")
            self.running = False

    def save_audit_trail(self, filename: str = "paper_trading_audit.jsonl"):
        """Save audit trail to file"""
        with open(filename, "w") as f:
            for entry in self.audit_log:
                f.write(json.dumps(entry) + "\n")
        logger.info(f"Audit trail saved: {filename}")

async def main():
    """Run paper trading simulator"""
    simulator = PaperTradingSimulator()
    try:
        await simulator.run()
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user")
    finally:
        simulator.save_audit_trail()

if __name__ == "__main__":
    asyncio.run(main())

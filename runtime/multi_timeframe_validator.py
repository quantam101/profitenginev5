"""
MULTI-TIMEFRAME SIGNAL VALIDATOR — Confirm trades across 5min, 30min, and daily timeframes
Reduces false signals by requiring alignment across multiple timeframes.

Features:
- get_timeframe_signals(): Fetch RSI, SMA200/SMA50, and trend data for all timeframes
- validate_signal(): Confirm signal with 2+ timeframe confirmations
- confidence_score(): Rate signal strength 0-100 based on alignment

Usage:
    validator = MultiTimeframeValidator()
    signals = await validator.get_timeframe_signals('AAPL', timeframes=['5min','30min','day'])
    is_valid = await validator.validate_signal('AAPL', 'BUY', min_confirmations=2)
    confidence = await validator.confidence_score('AAPL', 'BUY')
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import os

try:
    import yfinance as yf
    import requests
except ImportError:
    raise ImportError("Install dependencies: pip install yfinance requests")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# TIMEFRAME DATA STRUCTURES
# ============================================================================

class TimeframeSignal:
    """Represents technical signals for a single timeframe"""

    def __init__(
        self,
        timeframe: str,
        symbol: str,
        rsi: float,
        sma50: float,
        sma200: float,
        price: float,
        timestamp: float
    ):
        """
        Initialize timeframe signal.

        Args:
            timeframe: '5min', '30min', or 'day'
            symbol: Stock ticker symbol
            rsi: RSI(14) value 0-100
            sma50: 50-period simple moving average
            sma200: 200-period simple moving average
            price: Current price
            timestamp: Unix timestamp of data point
        """
        self.timeframe = timeframe
        self.symbol = symbol
        self.rsi = rsi
        self.sma50 = sma50
        self.sma200 = sma200
        self.price = price
        self.timestamp = timestamp
        self.is_uptrend = sma50 > sma200
        self.rsi_signal = self._interpret_rsi()

    def _interpret_rsi(self) -> str:
        """Interpret RSI: 'OVERSOLD', 'OVERBOUGHT', or 'NEUTRAL'"""
        if self.rsi < 30:
            return "OVERSOLD"
        elif self.rsi > 70:
            return "OVERBOUGHT"
        else:
            return "NEUTRAL"

    def get_signal(self) -> Optional[str]:
        """
        Generate signal for this timeframe.

        Returns:
            'BUY', 'SELL', or None
        """
        # BUY: Oversold (RSI < 30) + Uptrend (SMA50 > SMA200)
        if self.rsi < 30 and self.is_uptrend:
            return "BUY"
        # SELL: Overbought (RSI > 70) + Downtrend (SMA50 < SMA200)
        elif self.rsi > 70 and not self.is_uptrend:
            return "SELL"
        else:
            return None

    def __repr__(self) -> str:
        return (
            f"TimeframeSignal({self.timeframe}): "
            f"Price={self.price:.2f}, RSI={self.rsi:.1f}, "
            f"SMA50={self.sma50:.2f}, SMA200={self.sma200:.2f}, "
            f"Trend={'UP' if self.is_uptrend else 'DOWN'}"
        )


class MultiTimeframeAnalysis:
    """Container for signals across all timeframes"""

    def __init__(self, symbol: str, signals: Dict[str, TimeframeSignal]):
        """
        Initialize multi-timeframe analysis.

        Args:
            symbol: Stock ticker
            signals: Dict mapping timeframe -> TimeframeSignal
        """
        self.symbol = symbol
        self.signals = signals
        self.timestamp = time.time()

    def get_confirmation_count(self, signal_type: str) -> int:
        """
        Count how many timeframes confirm the signal.

        Args:
            signal_type: 'BUY' or 'SELL'

        Returns:
            Number of timeframes with matching signal (0-3)
        """
        count = 0
        for ts in self.signals.values():
            if ts.get_signal() == signal_type:
                count += 1
        return count

    def is_aligned(self, signal_type: str) -> bool:
        """
        Check if all timeframes are aligned on the signal.

        Args:
            signal_type: 'BUY' or 'SELL'

        Returns:
            True if all timeframes show same signal
        """
        return self.get_confirmation_count(signal_type) == len(self.signals)

    def get_strongest_signal(self) -> Optional[Tuple[str, int]]:
        """
        Find the strongest signal across timeframes.

        Returns:
            Tuple of (signal_type, confirmation_count) or None
        """
        buy_count = self.get_confirmation_count("BUY")
        sell_count = self.get_confirmation_count("SELL")

        if buy_count > 0:
            return ("BUY", buy_count)
        elif sell_count > 0:
            return ("SELL", sell_count)
        else:
            return None

    def __repr__(self) -> str:
        signals_str = "\n  ".join(str(s) for s in self.signals.values())
        buy_count = self.get_confirmation_count("BUY")
        sell_count = self.get_confirmation_count("SELL")
        return (
            f"MultiTimeframeAnalysis({self.symbol}):\n  {signals_str}\n"
            f"  BUY confirmations: {buy_count}, SELL confirmations: {sell_count}"
        )


# ============================================================================
# DATA FETCHING
# ============================================================================

class TimeframeDataFetcher:
    """Fetches OHLCV data for different timeframes"""

    def __init__(self):
        """Initialize data fetcher with cache"""
        self.cache = {}
        self.cache_ttl = {
            "5min": 60,      # 1 minute
            "30min": 300,    # 5 minutes
            "day": 3600      # 1 hour
        }

    async def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        bars: int = 200
    ) -> Optional[List[Dict[str, float]]]:
        """
        Fetch historical OHLCV data for a timeframe.

        Args:
            symbol: Stock ticker
            timeframe: '5min', '30min', or 'day'
            bars: Number of bars to fetch (default 200 for SMA200)

        Returns:
            List of OHLCV dicts or None if fetch fails
        """
        cache_key = f"{symbol}_{timeframe}"

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl.get(timeframe, 300):
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data

        # Fetch based on timeframe
        try:
            if timeframe == "5min":
                data = await self._fetch_intraday(symbol, interval="5m", bars=bars)
            elif timeframe == "30min":
                data = await self._fetch_intraday(symbol, interval="30m", bars=bars)
            elif timeframe == "day":
                data = await self._fetch_daily(symbol, bars=bars)
            else:
                logger.error(f"Unknown timeframe: {timeframe}")
                return None

            if data:
                self.cache[cache_key] = (time.time(), data)
            return data

        except Exception as e:
            logger.error(f"Failed to fetch {timeframe} data for {symbol}: {e}")
            return None

    async def _fetch_intraday(
        self,
        symbol: str,
        interval: str,
        bars: int
    ) -> Optional[List[Dict[str, float]]]:
        """
        Fetch intraday data via yfinance.

        Args:
            symbol: Stock ticker
            interval: '5m' or '30m'
            bars: Number of bars

        Returns:
            List of OHLCV dicts or None
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="60d", interval=interval)

            if hist.empty:
                logger.warning(f"No data returned for {symbol} {interval}")
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

            logger.info(f"Fetched {len(bars_data)} {interval} bars for {symbol}")
            return bars_data

        except Exception as e:
            logger.error(f"Intraday fetch failed for {symbol}: {e}")
            return None

    async def _fetch_daily(
        self,
        symbol: str,
        bars: int
    ) -> Optional[List[Dict[str, float]]]:
        """
        Fetch daily data via yfinance.

        Args:
            symbol: Stock ticker
            bars: Number of bars (days)

        Returns:
            List of OHLCV dicts or None
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")

            if hist.empty:
                logger.warning(f"No daily data returned for {symbol}")
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

            logger.info(f"Fetched {len(bars_data)} daily bars for {symbol}")
            return bars_data

        except Exception as e:
            logger.error(f"Daily fetch failed for {symbol}: {e}")
            return None


# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

class TechnicalIndicators:
    """Compute RSI, SMA, and related indicators"""

    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        """
        Compute RSI(14).

        Args:
            closes: List of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value 0-100
        """
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
    def sma(closes: List[float], period: int) -> float:
        """
        Compute simple moving average.

        Args:
            closes: List of closing prices
            period: SMA period (e.g., 50, 200)

        Returns:
            SMA value
        """
        if len(closes) < period:
            return sum(closes) / len(closes) if closes else 0.0

        return sum(closes[-period:]) / period

    @staticmethod
    def extract_closes(bars: List[Dict[str, float]]) -> List[float]:
        """
        Extract closing prices from OHLCV bars.

        Args:
            bars: List of OHLCV dicts

        Returns:
            List of closing prices
        """
        return [bar["close"] for bar in bars]


# ============================================================================
# MULTI-TIMEFRAME VALIDATOR
# ============================================================================

class MultiTimeframeValidator:
    """Main validator for multi-timeframe signal confirmation"""

    def __init__(self):
        """Initialize validator with data fetcher and indicator computer"""
        self.fetcher = TimeframeDataFetcher()
        self.indicators = TechnicalIndicators()
        self.last_analysis = {}  # Cache last analysis per symbol

    async def get_timeframe_signals(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None
    ) -> MultiTimeframeAnalysis:
        """
        Fetch signals for a symbol across multiple timeframes.

        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            timeframes: List of timeframes to analyze (default ['5min','30min','day'])

        Returns:
            MultiTimeframeAnalysis with signals for all timeframes

        Example:
            analysis = await validator.get_timeframe_signals('AAPL')
            print(analysis)  # Shows RSI, SMA, and signals for each timeframe
        """
        if timeframes is None:
            timeframes = ["5min", "30min", "day"]

        logger.info(f"Fetching signals for {symbol} across {timeframes}")
        signals = {}

        # Fetch data and compute signals for each timeframe
        for tf in timeframes:
            try:
                bars = await self.fetcher.fetch_historical_data(symbol, tf, bars=200)
                if not bars:
                    logger.warning(f"No data for {symbol} {tf}")
                    continue

                closes = self.indicators.extract_closes(bars)
                current_price = closes[-1]
                current_time = bars[-1]["timestamp"]

                # Compute indicators
                rsi = self.indicators.rsi(closes, period=14)
                sma50 = self.indicators.sma(closes, period=50)
                sma200 = self.indicators.sma(closes, period=200)

                # Create signal object
                signal = TimeframeSignal(
                    timeframe=tf,
                    symbol=symbol,
                    rsi=rsi,
                    sma50=sma50,
                    sma200=sma200,
                    price=current_price,
                    timestamp=current_time
                )
                signals[tf] = signal
                logger.info(f"  {signal}")

            except Exception as e:
                logger.error(f"Error processing {symbol} {tf}: {e}")
                continue

        # Create and cache analysis
        analysis = MultiTimeframeAnalysis(symbol, signals)
        self.last_analysis[symbol] = analysis
        return analysis

    async def validate_signal(
        self,
        symbol: str,
        base_signal: str,
        min_confirmations: int = 2,
        timeframes: Optional[List[str]] = None
    ) -> bool:
        """
        Validate a trading signal across multiple timeframes.

        Args:
            symbol: Stock ticker
            base_signal: 'BUY' or 'SELL'
            min_confirmations: Minimum timeframes confirming signal (default 2)
            timeframes: Timeframes to check (default ['5min','30min','day'])

        Returns:
            True if signal is valid (min_confirmations met), False otherwise

        Example:
            is_valid = await validator.validate_signal('AAPL', 'BUY', min_confirmations=2)
            if is_valid:
                print("Signal confirmed across 2+ timeframes")
        """
        if base_signal not in ["BUY", "SELL"]:
            logger.error(f"Invalid signal type: {base_signal}")
            return False

        # Get signals across timeframes
        analysis = await self.get_timeframe_signals(symbol, timeframes)

        # Count confirmations
        confirmation_count = analysis.get_confirmation_count(base_signal)
        is_valid = confirmation_count >= min_confirmations

        logger.info(
            f"Signal validation for {symbol} {base_signal}: "
            f"{confirmation_count}/{len(analysis.signals)} timeframes "
            f"confirm (need {min_confirmations}): {'VALID' if is_valid else 'INVALID'}"
        )

        return is_valid

    async def confidence_score(
        self,
        symbol: str,
        base_signal: str,
        timeframes: Optional[List[str]] = None
    ) -> int:
        """
        Calculate confidence score for a signal (0-100).

        Scoring:
            - Base: 0 (no confirmations)
            - +30 per confirmation (1 TF = 30, 2 TF = 60, 3 TF = 100)
            - Bonus: +10 if all timeframes aligned
            - Bonus: +10 if RSI is extreme (< 20 or > 80)
            - Cap: 100 maximum

        Args:
            symbol: Stock ticker
            base_signal: 'BUY' or 'SELL'
            timeframes: Timeframes to analyze (default ['5min','30min','day'])

        Returns:
            Confidence score 0-100

        Example:
            conf = await validator.confidence_score('AAPL', 'BUY')
            print(f"Trade with {conf}% confidence")  # e.g., 85%
        """
        if base_signal not in ["BUY", "SELL"]:
            return 0

        # Get signals across timeframes
        analysis = await self.get_timeframe_signals(symbol, timeframes)

        # Base score: 30 points per confirming timeframe
        confirmation_count = analysis.get_confirmation_count(base_signal)
        score = confirmation_count * 30

        # Alignment bonus: all timeframes agree
        if analysis.is_aligned(base_signal):
            score += 10

        # RSI extreme bonus: RSI < 20 or > 80 = more extreme
        for signal in analysis.signals.values():
            if (base_signal == "BUY" and signal.rsi < 20) or \
               (base_signal == "SELL" and signal.rsi > 80):
                score += 10
                break

        # Cap at 100
        score = min(score, 100)

        logger.info(
            f"Confidence score for {symbol} {base_signal}: {score}/100 "
            f"({confirmation_count} confirmations)"
        )

        return score

    def get_last_analysis(self, symbol: str) -> Optional[MultiTimeframeAnalysis]:
        """
        Get cached analysis for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Last MultiTimeframeAnalysis or None
        """
        return self.last_analysis.get(symbol)

    async def get_all_signals(
        self,
        symbols: List[str]
    ) -> Dict[str, Optional[MultiTimeframeAnalysis]]:
        """
        Get signals for multiple symbols in parallel.

        Args:
            symbols: List of tickers to analyze

        Returns:
            Dict mapping symbol -> MultiTimeframeAnalysis

        Example:
            results = await validator.get_all_signals(['AAPL', 'MSFT', 'NVDA'])
            for symbol, analysis in results.items():
                print(f"{symbol}: {analysis.get_strongest_signal()}")
        """
        tasks = [self.get_timeframe_signals(sym) for sym in symbols]
        analyses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for symbol, analysis in zip(symbols, analyses):
            if isinstance(analysis, Exception):
                logger.error(f"Error analyzing {symbol}: {analysis}")
                results[symbol] = None
            else:
                results[symbol] = analysis

        return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    """
    Demonstrates multi-timeframe signal validation.

    This example:
    1. Validates BUY signal across timeframes
    2. Calculates confidence score
    3. Analyzes multiple symbols
    """
    validator = MultiTimeframeValidator()

    # Example 1: Get signals for a single symbol
    print("\n" + "="*80)
    print("EXAMPLE 1: Get Timeframe Signals")
    print("="*80)
    analysis = await validator.get_timeframe_signals("AAPL")
    print(analysis)

    # Example 2: Validate a BUY signal
    print("\n" + "="*80)
    print("EXAMPLE 2: Validate BUY Signal (2+ confirmations required)")
    print("="*80)
    is_valid = await validator.validate_signal("AAPL", "BUY", min_confirmations=2)
    print(f"BUY signal valid: {is_valid}")

    # Example 3: Get confidence score
    print("\n" + "="*80)
    print("EXAMPLE 3: Confidence Score (0-100)")
    print("="*80)
    confidence = await validator.confidence_score("AAPL", "BUY")
    print(f"BUY confidence: {confidence}%")

    # Example 4: Analyze multiple symbols
    print("\n" + "="*80)
    print("EXAMPLE 4: Analyze Multiple Symbols")
    print("="*80)
    symbols = ["AAPL", "MSFT", "NVDA"]
    all_analyses = await validator.get_all_signals(symbols)
    for symbol, analysis in all_analyses.items():
        if analysis:
            strongest = analysis.get_strongest_signal()
            print(f"{symbol}: {strongest}")

    # Example 5: Use cached analysis
    print("\n" + "="*80)
    print("EXAMPLE 5: Use Cached Analysis")
    print("="*80)
    cached = validator.get_last_analysis("AAPL")
    if cached:
        print(f"Cached analysis for AAPL (age: {time.time() - cached.timestamp:.0f}s)")
        print(f"  Strongest signal: {cached.get_strongest_signal()}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_usage())

#!/usr/bin/env python
"""Agent Market Data: Real-time quotes with freshness validation and local SQLite caching."""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import threading
from dataclasses import dataclass, asdict

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger(__name__)


@dataclass
class MarketQuote:
    """Market quote data structure."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: str
    volatility: float
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return asdict(self)

    def age_seconds(self) -> float:
        quote_time = datetime.fromisoformat(self.timestamp)
        return (datetime.now() - quote_time).total_seconds()


class AgentMarketData:
    """Market data manager: fetch real-time quotes, validate freshness, local SQLite cache."""

    DEFAULT_CACHE_TTL_SECONDS = 60  # 1 minute cache
    DEFAULT_STALE_THRESHOLD_SECONDS = 300  # 5 minutes = stale
    MAX_CACHE_SIZE_MB = 500

    def __init__(self, cache_db_path: str = "./market_data_cache.db",
                 cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
                 stale_threshold_seconds: int = DEFAULT_STALE_THRESHOLD_SECONDS,
                 enable_persistence: bool = True):
        self.cache_db_path = cache_db_path
        self.cache_ttl_seconds = cache_ttl_seconds
        self.stale_threshold_seconds = stale_threshold_seconds
        self.enable_persistence = enable_persistence
        self._lock = threading.RLock()
        self._memory_cache: Dict[str, MarketQuote] = {}
        self._last_fetch_time: Dict[str, float] = {}
        if self.enable_persistence:
            self._init_cache_db()

    def _init_cache_db(self) -> None:
        """Initialize SQLite cache database."""
        try:
            Path(self.cache_db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.cache_db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS market_quotes (
                symbol TEXT PRIMARY KEY, bid REAL, ask REAL, last REAL,
                volume INTEGER, timestamp TEXT, volatility REAL, confidence REAL)""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cache DB init failed: {e}")
            self.enable_persistence = False

    def fetch_quote(self, symbol: str, force_refresh: bool = False) -> Optional[MarketQuote]:
        """Fetch real-time market quote with caching."""
        with self._lock:
            if not force_refresh and symbol in self._memory_cache:
                if not self._is_cache_expired(symbol):
                    return self._memory_cache[symbol]
            quote = self._fetch_live_quote(symbol)
            if quote:
                self._memory_cache[symbol] = quote
                self._last_fetch_time[symbol] = datetime.now().timestamp()
                if self.enable_persistence:
                    self._persist_quote(quote)
                return quote
            if self.enable_persistence:
                cached = self._load_quote_from_db(symbol)
                if cached:
                    return cached
            return None

    def _fetch_live_quote(self, symbol: str) -> Optional[MarketQuote]:
        """Fetch live quote from yfinance."""
        try:
            if yf is None:
                return None
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = float(info.get('currentPrice') or info.get('regularMarketPrice', 0.0))
            if price <= 0:
                return None
            bid = float(info.get('bid', price * 0.999))
            ask = float(info.get('ask', price * 1.001))
            vol = min(100.0, float(info.get('impliedVolatility', 0.15)) * 100)
            return MarketQuote(symbol, bid, ask, price, int(info.get('volume', 0)),
                             datetime.now().isoformat(), vol, 0.95)
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            return None

    def validate_fresh(self, symbol: str, max_age_seconds: Optional[int] = None) -> Tuple[bool, float]:
        """Validate if cached quote is fresh. Returns (is_fresh, age_seconds)."""
        max_age = max_age_seconds or self.cache_ttl_seconds
        with self._lock:
            if symbol not in self._memory_cache:
                return False, float(self.stale_threshold_seconds)
            quote = self._memory_cache[symbol]
            age = quote.age_seconds()
            return age <= max_age, age

    def get_cached(self, symbol: str, include_stale: bool = False) -> Optional[MarketQuote]:
        """Get cached quote without network access."""
        with self._lock:
            if symbol in self._memory_cache:
                quote = self._memory_cache[symbol]
                if quote.age_seconds() <= self.stale_threshold_seconds or include_stale:
                    return quote
            if self.enable_persistence:
                quote = self._load_quote_from_db(symbol)
                if quote and (quote.age_seconds() <= self.stale_threshold_seconds or include_stale):
                    return quote
            return None

    def get_multi(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, MarketQuote]:
        """Fetch multiple quotes efficiently."""
        results = {}
        for symbol in symbols:
            quote = self.fetch_quote(symbol, force_refresh=force_refresh)
            if quote:
                results[symbol] = quote
        return results

    def validate_quote_integrity(self, quote: MarketQuote) -> bool:
        """Validate quote data integrity."""
        if quote.bid <= 0 or quote.ask <= 0 or quote.last <= 0:
            return False
        if quote.bid > quote.ask:
            return False
        spread_pct = (quote.ask - quote.bid) / quote.bid * 100
        if spread_pct > 2.0:
            return False
        return quote.bid <= quote.last <= quote.ask

    def _persist_quote(self, quote: MarketQuote) -> None:
        """Persist quote to SQLite database."""
        if not self.enable_persistence:
            return
        try:
            conn = sqlite3.connect(self.cache_db_path, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO market_quotes VALUES (?,?,?,?,?,?,?,?)",
                         (quote.symbol, quote.bid, quote.ask, quote.last, quote.volume,
                          quote.timestamp, quote.volatility, quote.confidence))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Persist failed: {e}")

    def _load_quote_from_db(self, symbol: str) -> Optional[MarketQuote]:
        """Load quote from SQLite database."""
        if not self.enable_persistence:
            return None
        try:
            conn = sqlite3.connect(self.cache_db_path, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM market_quotes WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            conn.close()
            return MarketQuote(*row) if row else None
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return None

    def _is_cache_expired(self, symbol: str) -> bool:
        """Check if cache entry is expired."""
        if symbol not in self._last_fetch_time:
            return True

        age = datetime.now().timestamp() - self._last_fetch_time[symbol]
        return age > self.cache_ttl_seconds

    def clear_cache(self, symbol: Optional[str] = None) -> int:
        """Clear cache entries. Returns count cleared."""
        cleared = 0
        with self._lock:
            if symbol:
                if symbol in self._memory_cache:
                    del self._memory_cache[symbol]
                    cleared += 1
                if self.enable_persistence:
                    try:
                        conn = sqlite3.connect(self.cache_db_path)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM market_quotes WHERE symbol = ?", (symbol,))
                        cleared += cursor.rowcount
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"Clear cache failed: {e}")
            else:
                cleared = len(self._memory_cache)
                self._memory_cache.clear()
                self._last_fetch_time.clear()
                if self.enable_persistence:
                    try:
                        conn = sqlite3.connect(self.cache_db_path)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM market_quotes")
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"Clear cache failed: {e}")
        return cleared

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            return {'memory_entries': len(self._memory_cache),
                    'cache_ttl_seconds': self.cache_ttl_seconds,
                    'stale_threshold_seconds': self.stale_threshold_seconds,
                    'persistence_enabled': self.enable_persistence}



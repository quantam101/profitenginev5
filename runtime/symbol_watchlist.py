"""
Symbol Watchlist Manager for ProfitEngine v5

Manages trading watchlists across multiple market categories with intelligent
scoring, volume filtering, and market hours awareness.

Features:
- Multi-category watchlist organization
- Symbol scoring based on catalyst strength and tradability
- Market hours filtering (9:30 AM - 4 PM ET)
- Bid/ask spread validation
- Daily volume filtering
- Real-time symbol prioritization
"""

import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketCategory(Enum):
    """Trading categories for symbol organization."""
    BIOTECH = "BIOTECH"
    GROWTH_TECH = "GROWTH_TECH"
    FINANCE = "FINANCE"
    HEALTHCARE = "HEALTHCARE"
    ENERGY = "ENERGY"


@dataclass
class SymbolMetrics:
    """Trading metrics for a symbol."""
    symbol: str
    category: str
    daily_volume: int
    bid_ask_spread: float
    catalyst_strength: float  # 0-1 score
    volatility: float  # annualized %
    tradability_score: float  # 0-1 score

    def is_valid(self) -> bool:
        """Check if symbol meets minimum trading criteria."""
        if self.daily_volume < 1_000_000:
            return False

        # Bid/ask spread validation by price (approximated)
        if self.bid_ask_spread > 0.05:  # 5 cents max spread
            return False

        return True


class SymbolWatchlist:
    """
    Intelligent symbol watchlist manager with multi-category support,
    scoring, and market hours awareness.
    """

    # Watchlist database organized by category
    WATCHLIST_DB = {
        MarketCategory.BIOTECH.value: [
            "CRSP", "EDIT", "BEAM", "FATE", "ARQT", "VERV", "PACB", "RXDX"
        ],
        MarketCategory.GROWTH_TECH.value: [
            "NVDA", "TSLA", "COIN", "UPST", "DDOG", "NFLX", "ROKU", "MSTR"
        ],
        MarketCategory.FINANCE.value: [
            "JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW"
        ],
        MarketCategory.HEALTHCARE.value: [
            "UNH", "JNJ", "PFE", "ABBV", "MRK", "ELV", "CNC", "HCA"
        ],
        MarketCategory.ENERGY.value: [
            "XOM", "CVX", "COP", "MPC", "SLB", "EOG", "PXD", "OKE"
        ],
    }

    # Catalyst strength scores by category (baseline)
    CATALYST_BASELINE = {
        MarketCategory.BIOTECH.value: 0.85,  # High catalyst activity
        MarketCategory.GROWTH_TECH.value: 0.75,  # Earnings/product driven
        MarketCategory.FINANCE.value: 0.70,  # Macro events
        MarketCategory.HEALTHCARE.value: 0.78,  # Earnings/M&A driven
        MarketCategory.ENERGY.value: 0.72,  # Geopolitical events
    }

    # Expected volatility by category (annualized %)
    VOLATILITY_BASELINE = {
        MarketCategory.BIOTECH.value: 0.65,  # 65% annualized
        MarketCategory.GROWTH_TECH.value: 0.55,  # 55% annualized
        MarketCategory.FINANCE.value: 0.35,  # 35% annualized
        MarketCategory.HEALTHCARE.value: 0.38,  # 38% annualized
        MarketCategory.ENERGY.value: 0.42,  # 42% annualized
    }

    # Market hours (ET): 9:30 AM - 4:00 PM
    MARKET_OPEN = time(9, 30)
    MARKET_CLOSE = time(16, 0)

    def __init__(self):
        """Initialize symbol watchlist manager."""
        self._symbol_cache: Dict[str, SymbolMetrics] = {}
        self._volume_cache: Dict[str, int] = {}
        self._spread_cache: Dict[str, float] = {}
        logger.info("SymbolWatchlist initialized with %d categories",
                   len(self.WATCHLIST_DB))

    def get_watchlist(self, category: Optional[str] = None) -> List[str]:
        """
        Retrieve watchlist for specified category or all symbols.

        Args:
            category: Optional category name (e.g., 'BIOTECH'). If None, returns all symbols.

        Returns:
            List of symbol tickers.

        Example:
            >>> wl = SymbolWatchlist()
            >>> biotech_symbols = wl.get_watchlist('BIOTECH')
            >>> all_symbols = wl.get_watchlist()
        """
        if category is None:
            # Return all symbols across all categories
            all_symbols = []
            for symbols in self.WATCHLIST_DB.values():
                all_symbols.extend(symbols)
            logger.debug("Retrieved all %d symbols", len(all_symbols))
            return all_symbols

        # Validate category
        category_upper = category.upper()
        if category_upper not in self.WATCHLIST_DB:
            logger.warning("Invalid category: %s", category)
            return []

        symbols = self.WATCHLIST_DB[category_upper]
        logger.debug("Retrieved %d symbols for category: %s", len(symbols), category_upper)
        return symbols

    def score_symbol(self, symbol: str) -> Dict[str, float]:
        """
        Calculate trading scores for a symbol based on category metrics.

        Args:
            symbol: Ticker symbol (e.g., 'NVDA')

        Returns:
            Dictionary with scoring metrics:
            - catalyst_strength: 0-1 strength of catalysts (FDA approvals, earnings, etc.)
            - tradability: 0-1 score (volume, spread, liquidity)
            - expected_volatility: Annualized volatility percentage
            - overall_score: Composite score for priority ranking

        Example:
            >>> wl = SymbolWatchlist()
            >>> score = wl.score_symbol('CRSP')
            >>> print(f"Catalyst strength: {score['catalyst_strength']}")
        """
        symbol = symbol.upper()

        # Find symbol's category
        category = self._find_symbol_category(symbol)
        if category is None:
            logger.warning("Symbol not in watchlist: %s", symbol)
            return {
                "catalyst_strength": 0.0,
                "tradability": 0.0,
                "expected_volatility": 0.0,
                "overall_score": 0.0,
            }

        # Base catalyst strength from category
        catalyst_strength = self.CATALYST_BASELINE.get(category, 0.7)

        # Expected volatility from category
        expected_volatility = self.VOLATILITY_BASELINE.get(category, 0.5)

        # Tradability score (simulated - would use real market data in production)
        # This would be enhanced with real bid/ask and volume data
        tradability = self._calculate_tradability(symbol, category)

        # Composite overall score (weighted)
        overall_score = (catalyst_strength * 0.4 +
                        tradability * 0.4 +
                        (1.0 - min(expected_volatility / 2.0, 1.0)) * 0.2)

        score_dict = {
            "catalyst_strength": round(catalyst_strength, 3),
            "tradability": round(tradability, 3),
            "expected_volatility": round(expected_volatility, 3),
            "overall_score": round(overall_score, 3),
            "category": category,
        }

        logger.debug("Scored %s: catalyst=%.2f, tradability=%.2f, volatility=%.2f%%",
                    symbol, catalyst_strength, tradability, expected_volatility * 100)

        return score_dict

    def get_market_hours_symbols(self) -> List[str]:
        """
        Retrieve all symbols that are trading during current market hours (9:30 AM - 4 PM ET).

        Returns:
            List of symbols currently in market hours. Empty list if outside market hours.

        Note:
            Returns all watchlist symbols if currently in market hours, empty list otherwise.
            In production, would check actual trading halts and extended hours.

        Example:
            >>> wl = SymbolWatchlist()
            >>> trading_now = wl.get_market_hours_symbols()
            >>> print(f"Symbols trading now: {len(trading_now)}")
        """
        now = datetime.now().time()

        # Check if current time is within market hours
        if now >= self.MARKET_OPEN and now < self.MARKET_CLOSE:
            symbols = self.get_watchlist()
            logger.info("Market hours active. %d symbols available", len(symbols))
            return symbols

        logger.debug("Outside market hours (current: %s)", now.strftime("%H:%M"))
        return []

    def prioritize_symbols(self, max_symbols: int = 5,
                          category: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Get top priority symbols ranked by composite trading score.

        Args:
            max_symbols: Maximum symbols to return (default 5)
            category: Optional category filter (e.g., 'BIOTECH')

        Returns:
            List of (symbol, score) tuples sorted by score descending.

        Example:
            >>> wl = SymbolWatchlist()
            >>> top_5 = wl.prioritize_symbols(max=5)
            >>> for symbol, score in top_5:
            ...     print(f"{symbol}: {score:.3f}")
        """
        # Get symbols for this category or all
        if category:
            symbols = self.get_watchlist(category)
        else:
            symbols = self.get_watchlist()

        # Score all symbols
        scored = []
        for symbol in symbols:
            score_data = self.score_symbol(symbol)
            overall_score = score_data.get("overall_score", 0.0)
            scored.append((symbol, overall_score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Limit to max_symbols
        top_symbols = scored[:max_symbols]

        logger.info("Top %d priority symbols: %s",
                   len(top_symbols),
                   [s[0] for s in top_symbols])

        return top_symbols

    def validate_symbol_tradability(self, symbol: str,
                                   daily_volume: int,
                                   bid_ask_spread: float) -> bool:
        """
        Validate if a symbol meets minimum tradability criteria.

        Args:
            symbol: Ticker symbol
            daily_volume: Average daily volume in shares
            bid_ask_spread: Bid/ask spread in dollars

        Returns:
            True if symbol meets criteria, False otherwise

        Criteria:
            - Daily volume > 1,000,000 shares
            - Bid/ask spread < $0.05 (5 cents)

        Example:
            >>> wl = SymbolWatchlist()
            >>> is_tradable = wl.validate_symbol_tradability('NVDA', 45000000, 0.01)
        """
        if daily_volume < 1_000_000:
            logger.warning("%s: volume %d below 1M threshold", symbol, daily_volume)
            return False

        if bid_ask_spread > 0.05:
            logger.warning("%s: spread %.4f exceeds 5 cent threshold",
                         symbol, bid_ask_spread)
            return False

        logger.debug("%s: tradability validation passed", symbol)
        return True

    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each watchlist category.

        Returns:
            Dictionary with category statistics including symbol count and baseline metrics.

        Example:
            >>> wl = SymbolWatchlist()
            >>> stats = wl.get_category_stats()
            >>> for cat, data in stats.items():
            ...     print(f"{cat}: {data['count']} symbols")
        """
        stats = {}
        for category, symbols in self.WATCHLIST_DB.items():
            stats[category] = {
                "count": len(symbols),
                "symbols": symbols,
                "catalyst_baseline": self.CATALYST_BASELINE.get(category, 0.7),
                "volatility_baseline": self.VOLATILITY_BASELINE.get(category, 0.5),
            }

        total_symbols = sum(s["count"] for s in stats.values())
        logger.info("Category stats: %d total symbols across %d categories",
                   total_symbols, len(stats))

        return stats

    def search_symbols(self, query: str) -> List[str]:
        """
        Search for symbols matching a query string.

        Args:
            query: Search query (symbol or partial match)

        Returns:
            List of matching symbols

        Example:
            >>> wl = SymbolWatchlist()
            >>> matches = wl.search_symbols('CRSP')
        """
        query = query.upper()
        matches = []

        for symbols in self.WATCHLIST_DB.values():
            for symbol in symbols:
                if query in symbol:
                    matches.append(symbol)

        logger.debug("Search for '%s' returned %d matches", query, len(matches))
        return sorted(matches)

    # ========== Private Methods ==========

    def _find_symbol_category(self, symbol: str) -> Optional[str]:
        """Find which category contains a symbol."""
        symbol = symbol.upper()
        for category, symbols in self.WATCHLIST_DB.items():
            if symbol in symbols:
                return category
        return None

    def _calculate_tradability(self, symbol: str, category: str) -> float:
        """
        Calculate tradability score based on category and symbol characteristics.

        In production, this would use real market data:
        - Actual bid/ask spread
        - Real-time volume
        - Order book depth
        - Historical volume patterns
        """
        # Base tradability from category
        base_score = {
            MarketCategory.GROWTH_TECH.value: 0.92,  # Very liquid mega caps
            MarketCategory.FINANCE.value: 0.88,       # Highly liquid
            MarketCategory.HEALTHCARE.value: 0.85,    # Good liquidity
            MarketCategory.ENERGY.value: 0.83,        # Good liquidity
            MarketCategory.BIOTECH.value: 0.78,       # More variable
        }

        score = base_score.get(category, 0.80)

        # Small adjustments based on symbol position in category
        # (mega-caps like NVDA, TSLA get slight boost)
        mega_caps = ["NVDA", "TSLA", "NFLX", "JPM", "JNJ", "XOM"]
        if symbol in mega_caps:
            score = min(score + 0.05, 1.0)

        return round(score, 3)

    def is_market_hours(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if given datetime (or current time) is within market hours.

        Args:
            dt: Datetime to check. If None, uses current time.

        Returns:
            True if within market hours (9:30 AM - 4 PM ET), False otherwise.
        """
        if dt is None:
            dt = datetime.now()

        current_time = dt.time()
        return self.MARKET_OPEN <= current_time < self.MARKET_CLOSE


# ========== Convenience Functions ==========

def get_watchlist(category: Optional[str] = None) -> List[str]:
    """Get watchlist symbols (default or by category)."""
    wl = SymbolWatchlist()
    return wl.get_watchlist(category)


def score_symbol(symbol: str) -> Dict[str, float]:
    """Score a single symbol."""
    wl = SymbolWatchlist()
    return wl.score_symbol(symbol)


def get_market_hours_symbols() -> List[str]:
    """Get symbols currently trading in market hours."""
    wl = SymbolWatchlist()
    return wl.get_market_hours_symbols()


def prioritize_symbols(max_symbols: int = 5,
                      category: Optional[str] = None) -> List[Tuple[str, float]]:
    """Get top priority symbols ranked by score."""
    wl = SymbolWatchlist()
    return wl.prioritize_symbols(max_symbols, category)


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example usage
    wl = SymbolWatchlist()

    print("\n=== ProfitEngine Symbol Watchlist Manager ===\n")

    # Example 1: Get all symbols
    print("1. All Watchlist Symbols:")
    all_symbols = wl.get_watchlist()
    print(f"   Total symbols: {len(all_symbols)}\n")

    # Example 2: Get category-specific symbols
    print("2. BIOTECH Category:")
    biotech = wl.get_watchlist('BIOTECH')
    print(f"   Symbols: {', '.join(biotech)}\n")

    # Example 3: Score a symbol
    print("3. Symbol Scoring (CRSP):")
    crsp_score = wl.score_symbol('CRSP')
    for key, value in crsp_score.items():
        print(f"   {key}: {value}")
    print()

    # Example 4: Get market hours symbols
    print("4. Symbols Trading Now:")
    trading = wl.get_market_hours_symbols()
    print(f"   Market hours active: {len(trading) > 0}")
    print(f"   Symbols available: {len(trading)}\n")

    # Example 5: Prioritize symbols
    print("5. Top 5 Priority Symbols (all categories):")
    top_all = wl.prioritize_symbols(max_symbols=5)
    for i, (symbol, score) in enumerate(top_all, 1):
        print(f"   {i}. {symbol}: {score:.3f}")
    print()

    # Example 6: Prioritize by category
    print("6. Top 5 Priority Symbols (GROWTH_TECH):")
    top_tech = wl.prioritize_symbols(max_symbols=5, category='GROWTH_TECH')
    for i, (symbol, score) in enumerate(top_tech, 1):
        print(f"   {i}. {symbol}: {score:.3f}")
    print()

    # Example 7: Category statistics
    print("7. Category Statistics:")
    stats = wl.get_category_stats()
    for category, data in stats.items():
        print(f"   {category}: {data['count']} symbols (volatility: {data['volatility_baseline']:.1%})")
    print()

    # Example 8: Search symbols
    print("8. Search Results (query: 'TECH'):")
    matches = wl.search_symbols('TECH')
    print(f"   Found: {', '.join(matches) if matches else 'None'}\n")

    # Example 9: Validate tradability
    print("9. Tradability Validation:")
    is_valid = wl.validate_symbol_tradability('NVDA', 45_000_000, 0.01)
    print(f"   NVDA (vol: 45M, spread: $0.01): {is_valid}\n")

    print("=== End of Examples ===\n")

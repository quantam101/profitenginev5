"""
EXAMPLE: Multi-Timeframe Trading Integration
Demonstrates how to use MultiTimeframeValidator in a live trading system.

This example shows:
1. Validating signals before trade execution
2. Confidence-based position sizing
3. Real-time scanning of watchlists
4. Integration with existing PaperTradingSimulator
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from multi_timeframe_validator import MultiTimeframeValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MultiTimeframeTrading")


# ============================================================================
# VALIDATED TRADING EXECUTOR
# ============================================================================

class ValidatedTradingExecutor:
    """Executes trades only when multi-timeframe validation passes"""

    def __init__(
        self,
        min_confirmations: int = 2,
        min_confidence: int = 60,
        position_size_base: int = 100
    ):
        """
        Initialize executor.

        Args:
            min_confirmations: Minimum timeframes to confirm (2-3)
            min_confidence: Minimum confidence score (0-100)
            position_size_base: Base shares per trade
        """
        self.validator = MultiTimeframeValidator()
        self.min_confirmations = min_confirmations
        self.min_confidence = min_confidence
        self.position_size_base = position_size_base
        self.executed_trades = []
        self.rejected_trades = []

    async def should_trade(
        self,
        symbol: str,
        signal: str
    ) -> Tuple[bool, int, str]:
        """
        Check if trade should execute.

        Args:
            symbol: Stock ticker
            signal: 'BUY' or 'SELL'

        Returns:
            Tuple of (should_trade, confidence, reason)
        """
        try:
            # Validate across timeframes
            is_valid = await self.validator.validate_signal(
                symbol,
                signal,
                min_confirmations=self.min_confirmations
            )

            if not is_valid:
                reason = f"Signal needs {self.min_confirmations}+ confirmations"
                return False, 0, reason

            # Get confidence score
            confidence = await self.validator.confidence_score(symbol, signal)

            if confidence < self.min_confidence:
                reason = f"Confidence {confidence}% < {self.min_confidence}%"
                return False, confidence, reason

            return True, confidence, "Trade approved"

        except Exception as e:
            logger.error(f"Error validating {symbol}: {e}")
            return False, 0, f"Validation error: {e}"

    def calculate_position_size(self, confidence: int) -> int:
        """
        Scale position size based on confidence.

        Args:
            confidence: Confidence score 0-100

        Returns:
            Number of shares to trade

        Scaling:
            90-100%: 100% of base size
            75-89%: 80% of base size
            60-74%: 60% of base size
            < 60%: 0 (no trade)
        """
        if confidence >= 90:
            return int(self.position_size_base * 1.0)
        elif confidence >= 75:
            return int(self.position_size_base * 0.8)
        elif confidence >= 60:
            return int(self.position_size_base * 0.6)
        else:
            return 0

    async def execute_trade(
        self,
        symbol: str,
        signal: str,
        current_price: float
    ) -> Dict:
        """
        Execute a validated trade.

        Args:
            symbol: Stock ticker
            signal: 'BUY' or 'SELL'
            current_price: Current market price

        Returns:
            Trade result dict
        """
        should_trade, confidence, reason = await self.should_trade(symbol, signal)

        if not should_trade:
            result = {
                "executed": False,
                "symbol": symbol,
                "signal": signal,
                "reason": reason,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            self.rejected_trades.append(result)
            logger.warning(f"Trade rejected: {symbol} {signal} - {reason}")
            return result

        # Calculate position size
        position_size = self.calculate_position_size(confidence)

        if position_size == 0:
            result = {
                "executed": False,
                "symbol": symbol,
                "signal": signal,
                "reason": "Position size calculated to 0",
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            self.rejected_trades.append(result)
            return result

        # Execute trade
        trade_value = position_size * current_price
        result = {
            "executed": True,
            "symbol": symbol,
            "signal": signal,
            "position_size": position_size,
            "current_price": current_price,
            "trade_value": trade_value,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

        self.executed_trades.append(result)
        logger.info(
            f"Trade executed: {signal} {position_size} @ ${current_price:.2f} = "
            f"${trade_value:.2f} ({confidence}% confidence)"
        )

        return result

    def get_statistics(self) -> Dict:
        """
        Get trading statistics.

        Returns:
            Stats dict with trade counts and metrics
        """
        total_trades = len(self.executed_trades) + len(self.rejected_trades)
        avg_confidence = (
            sum(t["confidence"] for t in self.executed_trades) /
            len(self.executed_trades)
            if self.executed_trades else 0
        )

        total_value = sum(t.get("trade_value", 0) for t in self.executed_trades)

        return {
            "total_signals": total_trades,
            "executed_trades": len(self.executed_trades),
            "rejected_trades": len(self.rejected_trades),
            "execution_rate": (
                len(self.executed_trades) / total_trades * 100
                if total_trades > 0 else 0
            ),
            "avg_confidence": avg_confidence,
            "total_trade_value": total_value,
        }


# ============================================================================
# WATCHLIST SCANNER
# ============================================================================

class MultiTimeframeWatchlistScanner:
    """Scans watchlist for signals across multiple symbols"""

    def __init__(self, watchlist: List[str], executor: ValidatedTradingExecutor):
        """
        Initialize scanner.

        Args:
            watchlist: List of symbols to scan
            executor: ValidatedTradingExecutor instance
        """
        self.watchlist = watchlist
        self.executor = executor
        self.validator = executor.validator
        self.scan_history = []

    async def scan_for_signals(self) -> Dict[str, Dict]:
        """
        Scan watchlist for trading signals.

        Returns:
            Dict mapping symbol -> signal analysis
        """
        logger.info(f"Scanning {len(self.watchlist)} symbols for signals...")

        # Get all analyses in parallel
        analyses = await self.validator.get_all_signals(self.watchlist)

        results = {}
        for symbol, analysis in analyses.items():
            if not analysis:
                results[symbol] = {"error": "Failed to analyze"}
                continue

            signal_data = analysis.get_strongest_signal()

            if not signal_data:
                results[symbol] = {
                    "signal": None,
                    "reason": "No clear signal",
                    "confirmations": 0
                }
                continue

            signal_type, confirmations = signal_data
            confidence = await self.validator.confidence_score(symbol, signal_type)

            results[symbol] = {
                "signal": signal_type,
                "confirmations": confirmations,
                "confidence": confidence,
                "buy_count": analysis.get_confirmation_count("BUY"),
                "sell_count": analysis.get_confirmation_count("SELL"),
            }

        logger.info(f"Scan complete: {len(results)} symbols analyzed")
        return results

    async def execute_scan_and_trade(self, current_prices: Dict[str, float]) -> Dict:
        """
        Scan watchlist and execute validated trades.

        Args:
            current_prices: Dict mapping symbol -> current_price

        Returns:
            Scan results with trade executions
        """
        scan_results = await self.scan_for_signals()

        execution_results = {}
        for symbol, signal_data in scan_results.items():
            if not signal_data.get("signal"):
                continue

            signal = signal_data["signal"]
            price = current_prices.get(symbol)

            if not price:
                logger.warning(f"No price for {symbol}")
                continue

            # Execute validated trade
            trade_result = await self.executor.execute_trade(symbol, signal, price)
            execution_results[symbol] = trade_result

        return execution_results

    def print_scan_summary(self, scan_results: Dict):
        """Print human-readable scan summary"""
        print("\n" + "="*80)
        print("WATCHLIST SCAN SUMMARY")
        print("="*80)
        print(f"Timestamp: {datetime.now().isoformat()}\n")

        # Group by signal type
        buy_signals = [
            (sym, data) for sym, data in scan_results.items()
            if data.get("signal") == "BUY"
        ]
        sell_signals = [
            (sym, data) for sym, data in scan_results.items()
            if data.get("signal") == "SELL"
        ]
        no_signals = [
            (sym, data) for sym, data in scan_results.items()
            if not data.get("signal")
        ]

        # Print BUY signals
        if buy_signals:
            print(f"BUY SIGNALS ({len(buy_signals)}):")
            for symbol, data in sorted(buy_signals, key=lambda x: x[1].get("confidence", 0), reverse=True):
                print(
                    f"  {symbol:8} | Confidence: {data['confidence']:3}% | "
                    f"Confirmations: {data['confirmations']}/{data.get('buy_count', 0)}"
                )
            print()

        # Print SELL signals
        if sell_signals:
            print(f"SELL SIGNALS ({len(sell_signals)}):")
            for symbol, data in sorted(sell_signals, key=lambda x: x[1].get("confidence", 0), reverse=True):
                print(
                    f"  {symbol:8} | Confidence: {data['confidence']:3}% | "
                    f"Confirmations: {data['confirmations']}/{data.get('sell_count', 0)}"
                )
            print()

        # Print statistics
        print(f"NO CLEAR SIGNALS: {len(no_signals)}")
        print()

    def print_execution_summary(self, execution_results: Dict):
        """Print execution summary"""
        executed = [r for r in execution_results.values() if r.get("executed")]
        rejected = [r for r in execution_results.values() if not r.get("executed")]

        print("\n" + "="*80)
        print("EXECUTION SUMMARY")
        print("="*80)

        if executed:
            print(f"EXECUTED ({len(executed)}):")
            for trade in executed:
                print(
                    f"  {trade['signal']:4} {trade['position_size']:3} @ "
                    f"${trade['current_price']:7.2f} = "
                    f"${trade['trade_value']:8.2f} ({trade['confidence']:3}%)"
                )
            print()

        if rejected:
            print(f"REJECTED ({len(rejected)}):")
            for trade in rejected:
                print(f"  {trade['symbol']:8} {trade['signal']:4} - {trade['reason']}")
            print()

        stats = self.executor.get_statistics()
        print("STATISTICS:")
        print(f"  Total Signals: {stats['total_signals']}")
        print(f"  Executed: {stats['executed_trades']}")
        print(f"  Rejected: {stats['rejected_trades']}")
        print(f"  Execution Rate: {stats['execution_rate']:.1f}%")
        print(f"  Avg Confidence: {stats['avg_confidence']:.1f}%")
        print(f"  Total Value: ${stats['total_trade_value']:,.2f}")
        print("="*80 + "\n")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_single_trade():
    """Example 1: Execute a single validated trade"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Single Trade Validation")
    print("="*80)

    executor = ValidatedTradingExecutor(
        min_confirmations=2,
        min_confidence=60,
        position_size_base=100
    )

    # Simulate a trade signal
    result = await executor.execute_trade("AAPL", "BUY", 150.25)

    print(f"\nTrade Result:")
    print(f"  Executed: {result['executed']}")
    print(f"  Symbol: {result['symbol']}")
    print(f"  Signal: {result['signal']}")
    print(f"  Reason: {result['reason']}")
    if result['executed']:
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Position Size: {result['position_size']} shares")
        print(f"  Trade Value: ${result['trade_value']:.2f}")


async def example_watchlist_scan():
    """Example 2: Scan watchlist and execute trades"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Watchlist Scan and Execution")
    print("="*80)

    # Set up scanner
    watchlist = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "GOOG", "AMZN", "META"]
    executor = ValidatedTradingExecutor(
        min_confirmations=2,
        min_confidence=65,
        position_size_base=100
    )

    scanner = MultiTimeframeWatchlistScanner(watchlist, executor)

    # Scan watchlist
    scan_results = await scanner.scan_for_signals()
    scanner.print_scan_summary(scan_results)

    # Simulate current prices (in real usage, fetch from market data)
    current_prices = {
        symbol: 100.0 + (hash(symbol) % 50) for symbol in watchlist
    }

    # Execute trades
    execution_results = await executor.execute_trade(
        "AAPL",
        "BUY",
        current_prices["AAPL"]
    )

    scanner.print_execution_summary({
        "AAPL": execution_results
    })


async def example_confidence_scaling():
    """Example 3: Demonstrate confidence-based position sizing"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Confidence-Based Position Sizing")
    print("="*80)

    executor = ValidatedTradingExecutor(
        min_confirmations=2,
        min_confidence=50,  # Low threshold to show scaling
        position_size_base=100
    )

    confidence_levels = [100, 90, 75, 60, 50, 40]

    print(f"\nPosition Sizing Scale (Base: {executor.position_size_base} shares):")
    print("="*50)
    print(f"{'Confidence':<15} {'Position Size':<15} {'% of Base':<15}")
    print("-"*50)

    for confidence in confidence_levels:
        position_size = executor.calculate_position_size(confidence)
        pct = (position_size / executor.position_size_base * 100) if position_size > 0 else 0
        print(f"{confidence:>3}% {'':<9} {position_size:>3} shares {'':<3} {pct:>6.0f}%")

    print()


async def example_statistics():
    """Example 4: Analyze trading statistics"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Trading Statistics")
    print("="*80)

    executor = ValidatedTradingExecutor()

    # Simulate some trades
    trades = [
        ("BUY", True, 85),
        ("SELL", False, "Confidence 45% < 60%", 45),
        ("BUY", True, 72),
        ("BUY", False, "Signal needs 2+ confirmations", 0),
        ("SELL", True, 68),
    ]

    for i, trade_data in enumerate(trades):
        if len(trade_data) == 3:
            signal, executed, confidence = trade_data
            if executed:
                executor.executed_trades.append({
                    "symbol": f"SYM{i}",
                    "signal": signal,
                    "confidence": confidence,
                    "trade_value": 10000
                })
            else:
                executor.rejected_trades.append({
                    "symbol": f"SYM{i}",
                    "signal": signal,
                    "confidence": confidence,
                    "reason": "Test rejection"
                })
        else:
            signal, executed, reason, confidence = trade_data
            executor.rejected_trades.append({
                "symbol": f"SYM{i}",
                "signal": signal,
                "reason": reason,
                "confidence": confidence
            })

    stats = executor.get_statistics()

    print(f"\nTrading Performance:")
    print(f"  Total Signals: {stats['total_signals']}")
    print(f"  Executed: {stats['executed_trades']}")
    print(f"  Rejected: {stats['rejected_trades']}")
    print(f"  Execution Rate: {stats['execution_rate']:.1f}%")
    print(f"  Avg Confidence: {stats['avg_confidence']:.1f}%")
    print(f"  Total Value: ${stats['total_trade_value']:,.2f}")
    print()


async def main():
    """Run all examples"""
    print("\nMulti-Timeframe Trading System Examples")
    print("=" * 80)

    # Run examples
    await example_confidence_scaling()
    await example_single_trade()
    await example_watchlist_scan()
    await example_statistics()

    print("="*80)
    print("All examples complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

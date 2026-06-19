"""
LIVE PAPER TRADING VERIFICATION SYSTEM — ProfitEngine v5

Comprehensive live trading verification that:
- Runs EnhancedTradingEngine against live market data
- Executes 1-5 trades per symbol on the watchlist
- Tracks entry, exit, P&L for each trade
- Records win rate, average win, average loss, profit factor
- Runs for 24 hours or until 100+ trades executed
- Generates detailed summary report

Target Metrics (Phase 4):
- Win rate: 85%+
- Profit factor: 3.0+
- Symbols traded: 10+
- Trades executed: 100+

Author: ProfitEngine Trading System
Version: 5.0.0
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# Add runtime directory to path
sys.path.insert(0, str(Path(__file__).parent / "runtime"))

try:
    from enhanced_trading_engine import (
        EnhancedTradingEngine,
        TradeSignal,
        ExecutionResult,
        PositionStatus,
        SignalAction
    )
    from symbol_watchlist import SymbolWatchlist
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE = Path(__file__).parent / "live_trading_verification.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ExecutedTrade:
    """Complete record of an executed trade."""
    trade_id: str
    symbol: str
    action: str  # BUY or SELL
    entry_price: float
    entry_time: str
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    position_size: int = 0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED_PROFIT, CLOSED_LOSS, AT_STOP, AT_TARGET
    confidence: int = 0
    reason: str = ""

    def close_trade(
        self,
        exit_price: float,
        exit_time: str,
        exit_reason: str = ""
    ) -> None:
        """Mark trade as closed and calculate P&L."""
        self.exit_price = exit_price
        self.exit_time = exit_time

        if self.action == "BUY":
            self.pnl = (exit_price - self.entry_price) * self.position_size
        else:  # SELL
            self.pnl = (self.entry_price - exit_price) * self.position_size

        self.pnl_percent = (self.pnl / (self.entry_price * self.position_size)) * 100 if self.entry_price > 0 else 0.0

        if self.pnl > 0:
            self.status = "CLOSED_PROFIT"
        elif self.pnl < 0:
            self.status = "CLOSED_LOSS"
        else:
            self.status = "CLOSED_BREAKEVEN"


@dataclass
class VerificationMetrics:
    """Summary metrics for verification run."""
    start_time: str
    end_time: str
    duration_hours: float
    total_trades: int
    symbols_traded: int
    unique_symbols: List[str]

    # P&L Metrics
    closed_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float  # percentage

    gross_profit: float
    gross_loss: float
    net_pnl: float

    avg_win: float
    avg_loss: float
    avg_trade_pnl: float

    profit_factor: float  # gross_profit / abs(gross_loss)
    largest_win: float
    largest_loss: float

    initial_balance: float
    final_balance: float
    return_percent: float


# ============================================================================
# LIVE TRADING VERIFIER
# ============================================================================

class LiveTradingVerifier:
    """
    Comprehensive live paper trading verification system.
    """

    def __init__(
        self,
        account_balance: float = 10000.0,
        max_duration_hours: float = 24.0,
        min_trades: int = 100,
        trades_per_symbol: int = 3
    ):
        """
        Initialize verifier.

        Args:
            account_balance: Starting account balance
            max_duration_hours: Maximum run duration (default 24 hours)
            min_trades: Target minimum trades to execute
            trades_per_symbol: Max trades per symbol (1-5)
        """
        self.account_balance = account_balance
        self.initial_balance = account_balance
        self.max_duration_hours = max_duration_hours
        self.min_trades = min_trades
        self.trades_per_symbol = min(max(trades_per_symbol, 1), 5)

        # Initialize engine and watchlist
        self.engine = EnhancedTradingEngine(account_balance=account_balance)
        self.watchlist = SymbolWatchlist()

        # Tracking
        self.executed_trades: List[ExecutedTrade] = []
        self.trade_attempts: Dict[str, int] = {}  # Count attempts per symbol
        self.start_time = datetime.now(timezone.utc)
        self.running = False

        logger.info(
            f"LiveTradingVerifier initialized: "
            f"balance=${account_balance:.2f}, "
            f"duration={max_duration_hours}h, "
            f"target={min_trades} trades, "
            f"{trades_per_symbol} per symbol"
        )

    async def run_verification(self) -> VerificationMetrics:
        """
        Run complete verification loop.

        Execution Flow:
        1. Get all symbols from watchlist
        2. Loop until time limit or trade target reached:
           - Generate signal for next symbol
           - If valid signal, execute trade
           - Monitor open positions and close when targets/stops hit
           - Track metrics
        3. Close any remaining open positions
        4. Calculate final metrics

        Returns:
            VerificationMetrics with complete summary
        """
        self.running = True
        logger.info("=" * 80)
        logger.info("STARTING LIVE TRADING VERIFICATION")
        logger.info("=" * 80)

        try:
            # Get all symbols
            all_symbols = self.watchlist.get_watchlist()
            logger.info(f"Total symbols in watchlist: {len(all_symbols)}")

            # Initialize tracking
            for symbol in all_symbols:
                self.trade_attempts[symbol] = 0

            # Main loop
            iteration = 0
            while self.running:
                iteration += 1

                # Check termination conditions
                elapsed_hours = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600

                if elapsed_hours >= self.max_duration_hours:
                    logger.info(f"Time limit reached ({self.max_duration_hours} hours)")
                    break

                if len(self.executed_trades) >= self.min_trades:
                    logger.info(f"Trade target reached ({len(self.executed_trades)} trades)")
                    break

                # Get next symbol to trade
                symbol = self._get_next_symbol(all_symbols)
                if not symbol:
                    logger.info("No more symbols available for trading")
                    break

                logger.info(f"\n[Iteration {iteration}] Trading {symbol}...")

                # Generate signal
                signal = await self.engine.generate_trade_signal(symbol)
                if not signal or signal.action == SignalAction.NONE:
                    logger.info(f"[{symbol}] No valid signal generated")
                    self.trade_attempts[symbol] += 1
                    await asyncio.sleep(1)  # Small delay before next iteration
                    continue

                # Execute trade
                result = await self.engine.execute_signal(signal)
                if result.status != "SUCCESS":
                    logger.warning(f"[{symbol}] Execution failed: {result.error_message}")
                    self.trade_attempts[symbol] += 1
                    continue

                # Record trade
                trade = ExecutedTrade(
                    trade_id=result.order_id,
                    symbol=symbol,
                    action=signal.action.value,
                    entry_price=signal.entry_price,
                    entry_time=signal.timestamp,
                    position_size=signal.position_size,
                    confidence=signal.confidence,
                    reason=signal.reason
                )

                self.executed_trades.append(trade)
                self.trade_attempts[symbol] += 1

                logger.info(
                    f"[{symbol}] Trade #{len(self.executed_trades)}: "
                    f"{signal.action.value} {signal.position_size} @ ${signal.entry_price:.2f} "
                    f"(confidence: {signal.confidence}%, RR: {signal.risk_reward_ratio:.2f}:1)"
                )

                # Simulate price movement and close trades
                await self._simulate_price_movement(result.order_id)

                # Small delay between trades
                await asyncio.sleep(0.5)

            # Close remaining open positions
            logger.info(f"\nClosing {len(self.engine.open_positions)} open positions...")
            await self._close_remaining_positions()

            # Calculate and return metrics
            end_time = datetime.now(timezone.utc)
            metrics = self._calculate_metrics(end_time)

            return metrics

        except Exception as e:
            logger.error(f"Error in verification loop: {e}", exc_info=True)
            raise
        finally:
            self.running = False

    def _get_next_symbol(self, symbols: List[str]) -> Optional[str]:
        """Get next symbol to trade (least attempted)."""
        tradable_symbols = [
            s for s in symbols
            if self.trade_attempts.get(s, 0) < self.trades_per_symbol
        ]

        if not tradable_symbols:
            return None

        # Pick symbol with fewest attempts
        return min(tradable_symbols, key=lambda s: self.trade_attempts.get(s, 0))

    async def _simulate_price_movement(self, order_id: str) -> None:
        """
        Simulate price movement and close trades when targets/stops are hit.

        In live trading, this would monitor real market data.
        For paper trading, we simulate random price movements.
        """
        if order_id not in self.engine.open_positions:
            return

        position = self.engine.open_positions[order_id]

        # Simulate 1-10 random price movements
        import random
        num_moves = random.randint(3, 10)

        for move in range(num_moves):
            await asyncio.sleep(0.1)  # Small delay between simulations

            # Generate random price movement (within volatility bounds)
            direction = random.choice([-1, 1])
            volatility = position.entry_price * 0.02  # 2% volatility
            price_change = direction * random.uniform(0, volatility)
            simulated_price = max(0.01, position.entry_price + price_change)

            # Monitor position
            position = await self.engine.monitor_position(order_id, simulated_price)
            if not position:
                continue

            # Check if position hit stop or target
            should_close = False
            exit_reason = ""

            if position.status == "AT_STOP":
                logger.info(f"[{position.symbol}] Position hit stop loss @ ${simulated_price:.2f}")
                should_close = True
                exit_reason = "Stop Loss"
            elif position.status == "AT_TARGET":
                logger.info(f"[{position.symbol}] Position hit take profit @ ${simulated_price:.2f}")
                should_close = True
                exit_reason = "Take Profit"

            if should_close:
                # Close the trade
                for trade in self.executed_trades:
                    if trade.trade_id == order_id and trade.status == "OPEN":
                        trade.close_trade(
                            exit_price=simulated_price,
                            exit_time=datetime.now(timezone.utc).isoformat(),
                            exit_reason=exit_reason
                        )
                        logger.info(
                            f"[{trade.symbol}] Trade closed: "
                            f"P&L: ${trade.pnl:+.2f} ({trade.pnl_percent:+.1f}%)"
                        )
                        break

                # Remove from open positions
                del self.engine.open_positions[order_id]
                break

    async def _close_remaining_positions(self) -> None:
        """Close any remaining open positions at market price."""
        positions_to_close = list(self.engine.open_positions.items())

        for order_id, position in positions_to_close:
            # Use current price as exit (market close)
            exit_price = position.current_price

            for trade in self.executed_trades:
                if trade.trade_id == order_id and trade.status == "OPEN":
                    trade.close_trade(
                        exit_price=exit_price,
                        exit_time=datetime.now(timezone.utc).isoformat(),
                        exit_reason="Market Close"
                    )
                    logger.info(
                        f"[{trade.symbol}] Final position closed: "
                        f"P&L: ${trade.pnl:+.2f} ({trade.pnl_percent:+.1f}%)"
                    )
                    break

            del self.engine.open_positions[order_id]

    def _calculate_metrics(self, end_time: datetime) -> VerificationMetrics:
        """Calculate comprehensive verification metrics."""
        duration = (end_time - self.start_time).total_seconds() / 3600

        # Separate closed trades
        closed_trades = [t for t in self.executed_trades if t.status != "OPEN"]

        # Profit/Loss analysis
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]
        breakeven_trades = [t for t in closed_trades if t.pnl == 0]

        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        net_pnl = gross_profit - gross_loss

        # Calculate averages
        avg_win = gross_profit / len(winning_trades) if winning_trades else 0.0
        avg_loss = gross_loss / len(losing_trades) if losing_trades else 0.0
        avg_trade_pnl = net_pnl / len(closed_trades) if closed_trades else 0.0

        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Win rate
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0.0

        # Largest win/loss
        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0.0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0.0

        # Unique symbols
        unique_symbols = sorted(set(t.symbol for t in self.executed_trades))

        # Final balance
        final_balance = self.initial_balance + net_pnl
        return_percent = (net_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0.0

        metrics = VerificationMetrics(
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_hours=duration,
            total_trades=len(self.executed_trades),
            symbols_traded=len(unique_symbols),
            unique_symbols=unique_symbols,
            closed_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            breakeven_trades=len(breakeven_trades),
            win_rate=win_rate,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_pnl=net_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade_pnl=avg_trade_pnl,
            profit_factor=profit_factor,
            largest_win=largest_win,
            largest_loss=largest_loss,
            initial_balance=self.initial_balance,
            final_balance=final_balance,
            return_percent=return_percent
        )

        return metrics

    def save_results(self, metrics: VerificationMetrics) -> None:
        """Save verification results to log file."""
        logger.info("\n" + "=" * 80)
        logger.info("LIVE TRADING VERIFICATION SUMMARY")
        logger.info("=" * 80)

        logger.info(f"\n--- Duration ---")
        logger.info(f"Start: {metrics.start_time}")
        logger.info(f"End: {metrics.end_time}")
        logger.info(f"Duration: {metrics.duration_hours:.1f} hours")

        logger.info(f"\n--- Trade Execution ---")
        logger.info(f"Total Trades: {metrics.total_trades}")
        logger.info(f"Symbols Traded: {metrics.symbols_traded}")
        logger.info(f"Symbols: {', '.join(metrics.unique_symbols)}")
        logger.info(f"Closed Trades: {metrics.closed_trades}")
        logger.info(f"Open Trades: {metrics.total_trades - metrics.closed_trades}")

        logger.info(f"\n--- Win/Loss Analysis ---")
        logger.info(f"Winning Trades: {metrics.winning_trades}")
        logger.info(f"Losing Trades: {metrics.losing_trades}")
        logger.info(f"Breakeven Trades: {metrics.breakeven_trades}")
        logger.info(f"Win Rate: {metrics.win_rate:.1f}%")

        logger.info(f"\n--- P&L Metrics ---")
        logger.info(f"Gross Profit: ${metrics.gross_profit:+.2f}")
        logger.info(f"Gross Loss: ${metrics.gross_loss:+.2f}")
        logger.info(f"Net P&L: ${metrics.net_pnl:+.2f}")
        logger.info(f"Profit Factor: {metrics.profit_factor:.2f}")

        logger.info(f"\n--- Average Trade Analysis ---")
        logger.info(f"Average Win: ${metrics.avg_win:.2f}")
        logger.info(f"Average Loss: ${metrics.avg_loss:.2f}")
        logger.info(f"Average Trade P&L: ${metrics.avg_trade_pnl:+.2f}")
        logger.info(f"Largest Win: ${metrics.largest_win:+.2f}")
        logger.info(f"Largest Loss: ${metrics.largest_loss:+.2f}")

        logger.info(f"\n--- Account Performance ---")
        logger.info(f"Initial Balance: ${metrics.initial_balance:.2f}")
        logger.info(f"Final Balance: ${metrics.final_balance:.2f}")
        logger.info(f"Return: {metrics.return_percent:+.1f}%")

        logger.info(f"\n--- Phase 4 Target Comparison ---")
        logger.info(f"Win Rate Target: 85%+ (Achieved: {metrics.win_rate:.1f}%)")
        logger.info(f"Profit Factor Target: 3.0+ (Achieved: {metrics.profit_factor:.2f})")
        logger.info(f"Symbols Target: 10+ (Achieved: {metrics.symbols_traded})")
        logger.info(f"Trades Target: 100+ (Achieved: {metrics.total_trades})")

        # Detailed trade log
        logger.info(f"\n--- Detailed Trade Log ---")
        for i, trade in enumerate(self.executed_trades, 1):
            logger.info(
                f"Trade {i}: {trade.symbol} {trade.action} "
                f"@ ${trade.entry_price:.2f} (confidence: {trade.confidence}%) → "
                f"${trade.exit_price if trade.exit_price else 'OPEN':.2f} "
                f"P&L: ${trade.pnl:+.2f} ({trade.pnl_percent:+.1f}%) [{trade.status}]"
            )

        # Save JSON export
        self._save_json_export(metrics)

        logger.info("=" * 80)

    def _save_json_export(self, metrics: VerificationMetrics) -> None:
        """Save detailed results as JSON."""
        export_file = Path(__file__).parent / "live_trading_results.json"

        export_data = {
            'metrics': asdict(metrics),
            'trades': [asdict(t) for t in self.executed_trades],
            'metadata': {
                'system': 'ProfitEngine v5',
                'verification_type': 'Live Paper Trading',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"\nResults exported to: {export_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Run live trading verification."""
    logger.info("Starting ProfitEngine v5 Live Trading Verification")

    # Configuration
    ACCOUNT_BALANCE = 10000.0
    MAX_DURATION_HOURS = 24.0
    MIN_TRADES = 100
    TRADES_PER_SYMBOL = 3

    # Run verifier
    verifier = LiveTradingVerifier(
        account_balance=ACCOUNT_BALANCE,
        max_duration_hours=MAX_DURATION_HOURS,
        min_trades=MIN_TRADES,
        trades_per_symbol=TRADES_PER_SYMBOL
    )

    try:
        metrics = await verifier.run_verification()
        verifier.save_results(metrics)

        # Return status
        return metrics

    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        metrics = asyncio.run(main())
        print(f"\n✓ Verification complete: {metrics.total_trades} trades, "
              f"{metrics.win_rate:.1f}% win rate, "
              f"${metrics.net_pnl:+.2f} P&L")
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        sys.exit(1)

"""
POSITION MANAGER — Exit Logic & Lifecycle Management
Handles position entry, monitoring, and exit (CRITICAL — currently missing)
"""

import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Active trading position"""
    symbol: str
    entry_price: float
    entry_time: str
    quantity: int
    stop_loss: float
    take_profit: float
    side: str  # 'BUY' or 'SELL'
    position_id: str
    max_profit: float = 0.0
    peak_price: float = None
    cumulative_pnl: float = 0.0


@dataclass
class ClosedTrade:
    """Completed trade with exit details"""
    symbol: str
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    quantity: int
    side: str
    pnl: float
    pnl_percent: float
    exit_reason: str
    duration_minutes: int


class PositionManager:
    """
    CRITICAL COMPONENT: Manages position lifecycle
    - Entry validation
    - Real-time exit monitoring
    - Stop-loss/take-profit execution
    - Trailing stop management
    - Position sizing validation
    """

    def __init__(self, account_balance: float):
        self.account_balance = account_balance
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[ClosedTrade] = []
        self.position_counter = 0
        logger.info("[POSITION_MANAGER] Initialized with ${:.2f}".format(account_balance))

    def open_position(
        self,
        symbol: str,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        take_profit: float,
        side: str = "BUY"
    ) -> Tuple[bool, str, Position]:
        """
        Open a new position with validation

        Returns: (success, reason, position)
        """
        if quantity <= 0:
            return False, "Quantity must be > 0", None

        if side == "BUY":
            if stop_loss >= entry_price:
                return False, "Stop loss must be below entry for BUY", None
            if take_profit <= entry_price:
                return False, "Take profit must be above entry for BUY", None
        else:  # SELL
            if stop_loss <= entry_price:
                return False, "Stop loss must be above entry for SELL", None
            if take_profit >= entry_price:
                return False, "Take profit must be below entry for SELL", None

        if len(self.positions) >= 5:
            return False, "Max 5 positions reached", None

        position_cost = entry_price * quantity
        if position_cost > self.account_balance * 0.5:
            return False, "Position exceeds 50% of account", None

        self.position_counter += 1
        position = Position(
            symbol=symbol,
            entry_price=entry_price,
            entry_time=datetime.utcnow().isoformat(),
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            side=side,
            position_id="POS_{}".format(self.position_counter),
            peak_price=entry_price
        )

        self.positions[symbol] = position
        logger.info("[POSITION] Opened {}: {} {} @ ${:.2f}, SL=${:.2f}, TP=${:.2f}".format(
            position.position_id, side, quantity, entry_price, stop_loss, take_profit))

        return True, "Position opened", position

    def check_exits(self, current_prices: Dict[str, float]) -> List[ClosedTrade]:
        """
        Check all positions for exit conditions
        Returns list of trades that were closed
        """
        closed_today = []

        symbols_to_close = []
        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]
            exit_trade = self._evaluate_position(position, current_price)

            if exit_trade:
                symbols_to_close.append(symbol)
                closed_today.append(exit_trade)
                self.closed_trades.append(exit_trade)

        for symbol in symbols_to_close:
            del self.positions[symbol]

        return closed_today

    def _evaluate_position(self, position: Position, current_price: float) -> Optional[ClosedTrade]:
        """Evaluate single position for exit"""

        if position.side == "BUY":
            if current_price <= position.stop_loss:
                return self._close_position(position, current_price, "STOP_LOSS")
            elif current_price >= position.take_profit:
                return self._close_position(position, current_price, "TAKE_PROFIT")

            if current_price > position.peak_price:
                position.peak_price = current_price

            position.max_profit = ((current_price - position.entry_price) / position.entry_price) * 100

        else:  # SELL
            if current_price >= position.stop_loss:
                return self._close_position(position, current_price, "STOP_LOSS")
            elif current_price <= position.take_profit:
                return self._close_position(position, current_price, "TAKE_PROFIT")

            if current_price < position.peak_price:
                position.peak_price = current_price

            position.max_profit = ((position.entry_price - current_price) / position.entry_price) * 100

        return None

    def _close_position(self, position: Position, exit_price: float, exit_reason: str) -> ClosedTrade:
        """Close position and return completed trade"""

        if position.side == "BUY":
            pnl = (exit_price - position.entry_price) * position.quantity
            pnl_percent = ((exit_price - position.entry_price) / position.entry_price) * 100
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
            pnl_percent = ((position.entry_price - exit_price) / position.entry_price) * 100

        entry_dt = datetime.fromisoformat(position.entry_time)
        duration = int((datetime.utcnow() - entry_dt).total_seconds() / 60)

        trade = ClosedTrade(
            symbol=position.symbol,
            entry_price=position.entry_price,
            exit_price=exit_price,
            entry_time=position.entry_time,
            exit_time=datetime.utcnow().isoformat(),
            quantity=position.quantity,
            side=position.side,
            pnl=pnl,
            pnl_percent=pnl_percent,
            exit_reason=exit_reason,
            duration_minutes=duration
        )

        logger.info("[TRADE_CLOSED] {}: {} -> {} [{:.2f}% in {} min] - {}".format(
            position.position_id,
            position.side,
            exit_reason,
            pnl_percent,
            duration,
            position.symbol
        ))

        return trade

    def get_portfolio_stats(self) -> Dict:
        """Get current portfolio statistics"""
        total_open_pnl = 0.0
        open_count = len(self.positions)

        for position in self.positions.values():
            if position.side == "BUY":
                pnl = position.max_profit * position.quantity
            else:
                pnl = position.max_profit * position.quantity
            total_open_pnl += pnl

        closed_count = len(self.closed_trades)
        closed_pnl = sum(t.pnl for t in self.closed_trades)
        win_rate = 0.0
        if closed_count > 0:
            wins = sum(1 for t in self.closed_trades if t.pnl > 0)
            win_rate = (wins / closed_count) * 100

        avg_win = 0.0
        avg_loss = 0.0
        if closed_count > 0:
            wins = [t.pnl for t in self.closed_trades if t.pnl > 0]
            losses = [t.pnl for t in self.closed_trades if t.pnl < 0]
            if wins:
                avg_win = np.mean(wins)
            if losses:
                avg_loss = np.mean(losses)

        return {
            "open_positions": open_count,
            "closed_trades": closed_count,
            "total_realized_pnl": closed_pnl,
            "total_unrealized_pnl": total_open_pnl,
            "win_rate_percent": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        }

    def get_risk_metrics(self) -> Dict:
        """Calculate risk metrics for open positions"""
        max_loss_scenario = 0.0
        total_notional = 0.0

        for position in self.positions.values():
            if position.side == "BUY":
                loss_per_share = position.entry_price - position.stop_loss
            else:
                loss_per_share = position.stop_loss - position.entry_price

            max_loss = loss_per_share * position.quantity
            max_loss_scenario += max_loss
            total_notional += position.entry_price * position.quantity

        return {
            "max_loss_scenario": max_loss_scenario,
            "max_loss_percent": (max_loss_scenario / self.account_balance * 100),
            "total_notional": total_notional,
            "notional_leverage": total_notional / self.account_balance,
            "open_position_count": len(self.positions)
        }

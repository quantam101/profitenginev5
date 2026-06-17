"""
Agent Account State Manager - Maintains cash, positions, NAV, buying power.

Provides unified interface for account tracking across all trading agents.
Handles position reconciliation, NAV calculation, and buying power constraints.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Single position in account."""
    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Decimal = Decimal('0')
    market_value: Decimal = Decimal('0')
    unrealized_pnl: Decimal = Decimal('0')
    unrealized_pnl_pct: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def update_market_value(self, current_price: Decimal):
        """Update position market value and unrealized P&L."""
        self.current_price = current_price
        self.market_value = (self.quantity * current_price).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        entry_value = (self.quantity * self.avg_entry_price).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        self.unrealized_pnl = self.market_value - entry_value
        if entry_value > 0:
            self.unrealized_pnl_pct = float(self.unrealized_pnl / entry_value)
        self.timestamp = datetime.utcnow()


@dataclass
class AccountMetrics:
    """Account performance and constraint metrics."""
    nav: Decimal
    cash: Decimal
    positions_value: Decimal
    buying_power: Decimal
    margin_used: Decimal
    margin_available: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_pct: float
    leverage: float
    daily_pnl: Decimal
    daily_pnl_pct: float
    weekly_pnl: Decimal
    max_drawdown_pct: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AgentAccountState:
    """
    Maintains account state: cash, positions, NAV, buying power.

    Tracks:
    - Cash balance
    - Open positions (symbol -> qty, avg_price, current_price, P&L)
    - Account NAV (cash + positions value)
    - Buying power (available capital for trading)
    - Realized/unrealized P&L
    - Daily/weekly P&L windows
    - Max drawdown from peak
    """

    def __init__(self, config: Dict):
        """Initialize account state."""
        self.config = config
        self.initial_capital = Decimal(str(config.get('initial_capital', 100000)))
        self.cash = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.peak_nav = self.initial_capital
        self.realized_pnl = Decimal('0')
        self.daily_pnl = Decimal('0')
        self.weekly_pnl = Decimal('0')
        self.daily_pnl_window = []  # (timestamp, pnl_change)
        self.weekly_pnl_window = []  # (timestamp, pnl_change)
        self.trades_history = []  # (timestamp, symbol, direction, qty, price, fee, pnl)
        self.margin_requirement = Decimal(str(config.get('margin_requirement_pct', 25))) / 100
        self.leverage_limit = config.get('leverage_limit', 4.0)
        self.max_position_size_pct = config.get('max_position_size_pct', 10.0) / 100

    def get_state(self) -> AccountMetrics:
        """Get complete account state snapshot."""
        positions_value = sum(p.market_value for p in self.positions.values())
        nav = self.cash + positions_value
        buying_power = self._calculate_buying_power(positions_value)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())

        nav_pct = float((nav - self.initial_capital) / self.initial_capital) if self.initial_capital > 0 else 0.0
        drawdown = float((nav - self.peak_nav) / self.peak_nav) if self.peak_nav > 0 else 0.0

        margin_used = (positions_value * self.margin_requirement).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        margin_available = (positions_value * (Decimal('1') - self.margin_requirement)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        leverage = float(positions_value / nav) if nav > 0 else 0.0

        self.peak_nav = max(self.peak_nav, nav)

        return AccountMetrics(
            nav=nav,
            cash=self.cash,
            positions_value=positions_value,
            buying_power=buying_power,
            margin_used=margin_used,
            margin_available=margin_available,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_pct=nav_pct,
            leverage=leverage,
            daily_pnl=self.daily_pnl,
            daily_pnl_pct=float(self.daily_pnl / self.initial_capital) if self.initial_capital > 0 else 0.0,
            weekly_pnl=self.weekly_pnl,
            max_drawdown_pct=drawdown
        )

    def update_position(self, symbol: str, quantity: Decimal, avg_price: Decimal, current_price: Decimal):
        """Add or update position with market price."""
        if quantity == 0:
            self.positions.pop(symbol, None)
            return

        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, quantity, avg_price, current_price)
        else:
            pos = self.positions[symbol]
            # Average price calculation for additions/reductions
            if (pos.quantity > 0 and quantity > 0) or (pos.quantity < 0 and quantity < 0):
                total_value = (pos.quantity * pos.avg_entry_price + quantity * avg_price)
                pos.quantity += quantity
                pos.avg_entry_price = (total_value / pos.quantity).quantize(Decimal('0.0001'))
            else:
                pos.quantity = quantity
                pos.avg_entry_price = avg_price

        self.positions[symbol].update_market_value(current_price)
        logger.info(f"Position updated: {symbol} qty={quantity} price={avg_price}")

    def update_cash(self, delta: Decimal, reason: str = "trade"):
        """Update cash balance after transaction."""
        old_cash = self.cash
        self.cash = (self.cash + delta).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        logger.info(f"Cash update: {old_cash} -> {self.cash} ({reason})")

    def execute_trade(self, symbol: str, direction: str, quantity: Decimal,
                     entry_price: Decimal, fill_price: Decimal, fee: Decimal) -> bool:
        """Record executed trade and update account."""
        if fill_price <= 0:
            logger.error(f"Invalid fill price: {fill_price}")
            return False

        trade_value = (quantity * fill_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_cost = (trade_value + fee).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if direction.upper() == "LONG":
            if self.cash < total_cost:
                logger.error(f"Insufficient cash: {self.cash} < {total_cost}")
                return False
            self.cash -= total_cost
            self.update_position(symbol, quantity, fill_price, fill_price)
        elif direction.upper() == "SHORT":
            # Short sales reduce cash directly
            self.cash += trade_value - fee
            self.update_position(symbol, -quantity, fill_price, fill_price)

        self.trades_history.append({
            'timestamp': datetime.utcnow(),
            'symbol': symbol,
            'direction': direction,
            'quantity': quantity,
            'price': fill_price,
            'fee': fee,
            'pnl': Decimal('0')
        })
        return True

    def close_position(self, symbol: str, exit_price: Decimal, fee: Decimal = Decimal('0')) -> Decimal:
        """Close position and realize P&L."""
        if symbol not in self.positions:
            logger.warning(f"Position not found: {symbol}")
            return Decimal('0')

        pos = self.positions[symbol]
        exit_value = (pos.quantity * exit_price - fee).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        entry_value = (pos.quantity * pos.avg_entry_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        realized_pnl = exit_value - entry_value

        self.cash = (self.cash + exit_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.realized_pnl = (self.realized_pnl + realized_pnl).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Track daily/weekly P&L
        self.daily_pnl = (self.daily_pnl + realized_pnl).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.weekly_pnl = (self.weekly_pnl + realized_pnl).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        del self.positions[symbol]
        logger.info(f"Position closed: {symbol} realized_pnl={realized_pnl}")
        return realized_pnl

    def calc_nav(self) -> Decimal:
        """Calculate Net Asset Value: cash + positions market value."""
        positions_value = sum(p.market_value for p in self.positions.values())
        nav = self.cash + positions_value
        return nav.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position details for symbol."""
        return self.positions.get(symbol)

    def get_open_positions(self) -> List[Position]:
        """Get all open positions."""
        return list(self.positions.values())

    def can_trade(self, symbol: str, direction: str, notional: Decimal) -> Tuple[bool, str]:
        """Check if trade is allowed within buying power constraints."""
        state = self.get_state()

        if notional > state.buying_power:
            return False, f"Insufficient buying power: {notional} > {state.buying_power}"

        if state.leverage >= self.leverage_limit:
            return False, f"Leverage limit reached: {state.leverage:.2f}x >= {self.leverage_limit}x"

        position_pct = float(notional / state.nav) if state.nav > 0 else 0.0
        if position_pct > self.max_position_size_pct:
            return False, f"Position size exceeds limit: {position_pct:.1%} > {self.max_position_size_pct:.1%}"

        return True, "OK"

    def _calculate_buying_power(self, positions_value: Decimal) -> Decimal:
        """Calculate available buying power under margin constraints."""
        if positions_value == 0:
            return self.cash

        # Buying power = cash + (margin available from positions)
        margin_available = positions_value * (Decimal('1') - self.margin_requirement)
        buying_power = self.cash + margin_available
        return buying_power.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def reset_daily_metrics(self):
        """Reset daily P&L window (typically called at market open)."""
        self.daily_pnl = Decimal('0')
        self.daily_pnl_window = []

    def reset_weekly_metrics(self):
        """Reset weekly P&L window (typically called at start of week)."""
        self.weekly_pnl = Decimal('0')
        self.weekly_pnl_window = []

    def to_dict(self) -> Dict:
        """Serialize account state to dict."""
        state = self.get_state()
        return {
            'timestamp': state.timestamp.isoformat(),
            'nav': float(state.nav),
            'cash': float(state.cash),
            'positions_value': float(state.positions_value),
            'buying_power': float(state.buying_power),
            'leverage': state.leverage,
            'total_unrealized_pnl': float(state.total_unrealized_pnl),
            'total_unrealized_pnl_pct': state.total_unrealized_pnl_pct,
            'realized_pnl': float(self.realized_pnl),
            'daily_pnl': float(state.daily_pnl),
            'weekly_pnl': float(state.weekly_pnl),
            'max_drawdown_pct': state.max_drawdown_pct,
            'positions': {
                s: {
                    'quantity': float(p.quantity),
                    'avg_price': float(p.avg_entry_price),
                    'current_price': float(p.current_price),
                    'market_value': float(p.market_value),
                    'unrealized_pnl': float(p.unrealized_pnl),
                    'unrealized_pnl_pct': p.unrealized_pnl_pct
                }
                for s, p in self.positions.items()
            }
        }

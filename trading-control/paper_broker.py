from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
import numpy as np

try:
    from .models import (
        TradeProposal, ExecutionResult, OrderState
    )
except ImportError:
    from models import (
        TradeProposal, ExecutionResult, OrderState
    )

class PaperBroker:
    """Simulates order execution with realistic fills and slippage."""

    def __init__(self, config: Dict):
        self.config = config
        self.orders = {}  # order_id -> execution state
        self.positions = {}  # symbol -> {qty, avg_price, pnl}
        self.cash = Decimal(str(config.get('initial_capital', 100000)))
        self.account_equity = self.cash
        self.slippage_bps_min = config.get('execution', {}).get('slippage_model_buffer_pct', 1.0) / 100
        self.slippage_bps_max = config.get('execution', {}).get('slippage_model_buffer_pct', 1.5) / 100

    async def submit_proposal(self, proposal: TradeProposal) -> ExecutionResult:
        """Execute proposal as paper trade."""

        order_id = str(uuid.uuid4())
        self.orders[order_id] = {
            'state': OrderState.SUBMITTED,
            'proposal': proposal,
            'submit_time': datetime.utcnow()
        }

        # Simulate fill with slippage
        slippage_pct = Decimal(str(np.random.uniform(
            self.slippage_bps_min, self.slippage_bps_max
        )))

        if proposal.direction == "LONG":
            # Buy: slippage is negative (worse price)
            fill_price = proposal.entry_price * (Decimal('1') + slippage_pct)
        else:
            # Sell: slippage is negative (worse price)
            fill_price = proposal.entry_price * (Decimal('1') - slippage_pct)

        fill_price = fill_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        slippage = abs(fill_price - proposal.entry_price)

        # Calculate position size in shares
        quantity = (proposal.position_size_usd / fill_price).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        )

        # Commission (simplified: 0.1% of trade value)
        fee = (quantity * fill_price * Decimal('0.001')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Update cash and positions
        if proposal.direction == "LONG":
            self.cash -= (quantity * fill_price + fee)
            if proposal.symbol not in self.positions:
                self.positions[proposal.symbol] = {
                    'quantity': Decimal('0'),
                    'avg_price': Decimal('0')
                }
            pos = self.positions[proposal.symbol]
            pos['quantity'] += quantity
            pos['avg_price'] = fill_price
        else:
            self.cash += (quantity * fill_price - fee)
            if proposal.symbol in self.positions:
                self.positions[proposal.symbol]['quantity'] -= quantity

        self.orders[order_id]['state'] = OrderState.FILLED
        self.orders[order_id]['fill_price'] = fill_price
        self.orders[order_id]['quantity'] = quantity

        # No realized P&L yet (pending exit)
        result = ExecutionResult(
            order_id=order_id,
            state=OrderState.FILLED,
            timestamp=datetime.utcnow(),
            entry_price=proposal.entry_price,
            quantity=quantity,
            fill_price=fill_price,
            slippage=slippage,
            fee=fee,
            realized_pnl=Decimal('0'),
            is_complete=False
        )

        return result

    async def close_position(self, symbol: str, exit_price: Decimal) -> Decimal:
        """Close position and calculate realized P&L."""

        if symbol not in self.positions:
            return Decimal('0')

        pos = self.positions[symbol]
        if pos['quantity'] == 0:
            return Decimal('0')

        # Realized P&L
        pnl = (exit_price - pos['avg_price']) * pos['quantity']
        fee = (pos['quantity'] * exit_price * Decimal('0.001')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        self.cash += (pos['quantity'] * exit_price - fee)
        del self.positions[symbol]

        return pnl - fee

    def get_account_equity(self) -> Decimal:
        """Current account equity (cash + position values)."""
        equity = self.cash
        for symbol, pos in self.positions.items():
            # Simplified: assume last price = entry price
            equity += pos['quantity'] * pos['avg_price']
        self.account_equity = equity
        return equity

    def get_stats(self) -> Dict:
        """Return paper trading stats."""
        completed_trades = len([
            o for o in self.orders.values()
            if o['state'] == OrderState.FILLED
        ])

        profits = sum(
            1 for o in self.orders.values()
            if o['state'] == OrderState.FILLED and o.get('realized_pnl', 0) > 0
        )

        win_rate = profits / completed_trades if completed_trades > 0 else 0.0

        return {
            'total_trades': completed_trades,
            'win_rate': win_rate,
            'cash': float(self.cash),
            'equity': float(self.get_account_equity()),
            'positions': {
                sym: {
                    'qty': float(pos['quantity']),
                    'avg_price': float(pos['avg_price'])
                }
                for sym, pos in self.positions.items()
            }
        }

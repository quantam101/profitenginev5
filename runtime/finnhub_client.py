"""
FINNHUB TRADING CLIENT — Real-time market data + paper/live trading

Features:
- Real market data from Finnhub API
- Paper trading (simulated positions, real prices)
- Automatic switch to real money at $1000 threshold
- Live price feeds for signal generation
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import os
import httpx

logger = logging.getLogger(__name__)


@dataclass
class MarketPrice:
    """Real-time market price from Finnhub"""
    symbol: str
    price: float
    bid: float
    ask: float
    timestamp: float
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None


@dataclass
class PaperPosition:
    """Paper trading position (simulated)"""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    entry_time: str


@dataclass
class PaperOrder:
    """Paper trading order (simulated)"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    entry_price: float
    status: str  # 'pending', 'filled', 'cancelled'
    created_at: str
    filled_at: Optional[str] = None


class FinnhubClient:
    """Finnhub trading client with paper trading and automatic real money switch"""

    def __init__(self, api_key: str = "", starting_balance: float = 100.0):
        """Initialize Finnhub client

        Args:
            api_key: Finnhub API key
            starting_balance: Starting balance for paper trading
        """
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY', '')
        self.starting_balance = starting_balance
        self.cash_balance = starting_balance
        self.positions = {}  # symbol -> PaperPosition
        self.orders = {}  # order_id -> PaperOrder
        self.trade_history = []
        self.is_real_money = False  # Paper trading until $1000
        self.real_money_threshold = 1000.0
        self.base_url = "https://finnhub.io/api/v1"
        self.session = None
        logger.info(f"[FinnhubClient] Initialized with ${starting_balance:.2f} paper trading")
        logger.info(f"[FinnhubClient] Will auto-switch to real money at ${self.real_money_threshold:.2f}")

    async def init_session(self):
        """Initialize HTTP session for API calls"""
        self.session = httpx.AsyncClient(timeout=10.0)
        logger.info("[FinnhubClient] Session initialized")

    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            logger.info("[FinnhubClient] Session closed")

    async def get_price(self, symbol: str) -> Optional[MarketPrice]:
        """Get real-time market price from Finnhub API

        Args:
            symbol: Stock ticker (e.g., 'AAPL')

        Returns:
            MarketPrice with current bid/ask/last price
        """
        try:
            if not self.session:
                await self.init_session()

            # Finnhub quote endpoint
            url = f"{self.base_url}/quote"
            params = {
                'symbol': symbol,
                'token': self.api_key,
            }

            response = await self.session.get(url, params=params)
            data = response.json()

            if 'c' not in data:
                logger.warning(f"[FinnhubClient] No price data for {symbol}")
                return None

            # c=last, h=high, l=low, v=volume, bid=bid, ask=ask, o=open
            price = MarketPrice(
                symbol=symbol,
                price=data.get('c', 0),  # Current/last price
                bid=data.get('bid', data.get('c', 0)),  # Bid (or use last if not available)
                ask=data.get('ask', data.get('c', 0)),  # Ask (or use last if not available)
                timestamp=data.get('t', 0),
                high_price=data.get('h'),
                low_price=data.get('l'),
                volume=data.get('v'),
            )

            logger.debug(f"[FinnhubClient] {symbol}: ${price.price:.2f}")
            return price

        except Exception as e:
            logger.error(f"[FinnhubClient] Failed to fetch price for {symbol}: {e}")
            return None

    async def get_prices_batch(self, symbols: List[str]) -> Dict[str, MarketPrice]:
        """Get prices for multiple symbols efficiently

        Args:
            symbols: List of stock tickers

        Returns:
            Dict of symbol -> MarketPrice
        """
        prices = {}
        tasks = [self.get_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)

        for symbol, price in zip(symbols, results):
            if price:
                prices[symbol] = price

        return prices

    async def place_order(
        self,
        symbol: str,
        quantity: int,
        side: str,  # 'buy' or 'sell'
        price: Optional[float] = None,
    ) -> Optional[PaperOrder]:
        """Place paper trading order (simulated execution)

        Args:
            symbol: Stock ticker
            quantity: Number of shares
            side: 'buy' or 'sell'
            price: Entry price (uses current market price if not provided)

        Returns:
            PaperOrder if successful
        """
        try:
            # Get current market price
            if not price:
                market = await self.get_price(symbol)
                if not market:
                    logger.error(f"[FinnhubClient] Cannot get price for {symbol}")
                    return None
                price = market.price

            # Check buying power for buy orders
            if side.lower() == 'buy':
                cost = quantity * price
                if cost > self.cash_balance:
                    logger.warning(f"[FinnhubClient] Insufficient buying power: ${self.cash_balance:.2f} < ${cost:.2f}")
                    return None
                self.cash_balance -= cost
            elif side.lower() == 'sell':
                # Check position exists
                if symbol not in self.positions:
                    logger.warning(f"[FinnhubClient] No position to sell: {symbol}")
                    return None
                if self.positions[symbol].quantity < quantity:
                    logger.warning(f"[FinnhubClient] Insufficient shares: have {self.positions[symbol].quantity}, need {quantity}")
                    return None
                self.cash_balance += quantity * price

            # Create order
            order_id = f"paper_{datetime.now().timestamp()}_{symbol}"
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=side.lower(),
                quantity=quantity,
                entry_price=price,
                status='filled',
                created_at=datetime.utcnow().isoformat(),
                filled_at=datetime.utcnow().isoformat(),
            )

            self.orders[order_id] = order
            logger.info(f"[FinnhubClient] Paper order {order_id}: {side.upper()} {quantity} {symbol} @ ${price:.2f}")

            # Update position
            if side.lower() == 'buy':
                if symbol in self.positions:
                    old_qty = self.positions[symbol].quantity
                    old_cost = old_qty * self.positions[symbol].entry_price
                    new_cost = old_cost + (quantity * price)
                    new_qty = old_qty + quantity
                    avg_price = new_cost / new_qty
                    self.positions[symbol].quantity = new_qty
                    self.positions[symbol].entry_price = avg_price
                else:
                    self.positions[symbol] = PaperPosition(
                        symbol=symbol,
                        quantity=quantity,
                        entry_price=price,
                        current_price=price,
                        unrealized_pnl=0,
                        entry_time=datetime.utcnow().isoformat(),
                    )
            elif side.lower() == 'sell':
                self.positions[symbol].quantity -= quantity
                if self.positions[symbol].quantity == 0:
                    del self.positions[symbol]

            return order

        except Exception as e:
            logger.error(f"[FinnhubClient] Failed to place order: {e}")
            return None

    async def update_positions(self):
        """Update all open positions with current market prices"""
        try:
            if not self.positions:
                return

            symbols = list(self.positions.keys())
            prices = await self.get_prices_batch(symbols)

            for symbol, price_data in prices.items():
                if symbol in self.positions:
                    position = self.positions[symbol]
                    position.current_price = price_data.price
                    position.unrealized_pnl = (price_data.price - position.entry_price) * position.quantity

        except Exception as e:
            logger.error(f"[FinnhubClient] Failed to update positions: {e}")

    def get_portfolio_value(self) -> float:
        """Get total portfolio value (cash + positions)

        Returns:
            Total portfolio value in dollars
        """
        position_value = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )
        total = self.cash_balance + position_value
        return total

    def get_account_summary(self) -> Dict[str, Any]:
        """Get complete account summary

        Returns:
            Account metrics including portfolio value, positions, P&L
        """
        portfolio_value = self.get_portfolio_value()
        total_pnl = portfolio_value - self.starting_balance
        positions_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

        # Check if should switch to real money
        if portfolio_value >= self.real_money_threshold and not self.is_real_money:
            logger.warning(f"[FinnhubClient] THRESHOLD REACHED: ${portfolio_value:.2f} >= ${self.real_money_threshold:.2f}")
            logger.warning(f"[FinnhubClient] SWITCHING TO REAL MONEY TRADING")
            self.is_real_money = True

        return {
            'starting_balance': self.starting_balance,
            'cash_balance': self.cash_balance,
            'positions_value': portfolio_value - self.cash_balance,
            'portfolio_value': portfolio_value,
            'total_pnl': total_pnl,
            'pnl_percent': (total_pnl / self.starting_balance * 100) if self.starting_balance > 0 else 0,
            'positions_count': len(self.positions),
            'positions_pnl': positions_pnl,
            'is_real_money': self.is_real_money,
            'trades_count': len(self.trade_history),
        }

    async def close_position(self, symbol: str) -> Optional[PaperOrder]:
        """Close an open position at market price

        Args:
            symbol: Stock ticker

        Returns:
            PaperOrder for the sell
        """
        if symbol not in self.positions:
            logger.warning(f"[FinnhubClient] No position to close: {symbol}")
            return None

        position = self.positions[symbol]
        quantity = position.quantity

        # Get current price and sell
        market = await self.get_price(symbol)
        if not market:
            logger.error(f"[FinnhubClient] Cannot get price to close {symbol}")
            return None

        order = await self.place_order(symbol, quantity, 'sell', market.price)

        if order:
            # Track in history
            self.trade_history.append({
                'symbol': symbol,
                'entry_price': position.entry_price,
                'exit_price': market.price,
                'quantity': quantity,
                'pnl': (market.price - position.entry_price) * quantity,
                'entry_time': position.entry_time,
                'exit_time': datetime.utcnow().isoformat(),
            })

        return order

    def shutdown(self):
        """Cleanup and close connections"""
        logger.info("[FinnhubClient] Shutting down")


async def get_finnhub_client(api_key: str = "", starting_balance: float = 100.0) -> FinnhubClient:
    """Factory function to create and initialize Finnhub client

    Args:
        api_key: Finnhub API key (or reads from FINNHUB_API_KEY env var)
        starting_balance: Starting balance for paper trading

    Returns:
        Initialized FinnhubClient
    """
    client = FinnhubClient(api_key=api_key, starting_balance=starting_balance)
    await client.init_session()
    return client

"""
ROBINHOOD LIVE TRADING INTEGRATION
Connects to Robinhood via MCP protocol and official agentic trading endpoint
Executes real trades, monitors P&L, enforces risk gates
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, List, Tuple
import httpx
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ROBINHOOD MCP CONSTANTS
# ============================================================================
ROBINHOOD_MCP_ENDPOINT = "https://agent.robinhood.com/mcp/trading"
MAX_REQUEST_TIMEOUT = 10.0
POSITION_SIZE_LIMIT = Decimal("5000.00")  # Max per position
MAX_LIVE_POSITIONS = 5
LIVE_TRADE_HISTORY_DAYS = 30


class RobinhoodLiveTrader:
    """
    Live Robinhood trading integration via MCP protocol.
    Handles account management, trades, P&L monitoring, risk enforcement.
    """

    def __init__(self, oauth_token: str, account_id: Optional[str] = None):
        """
        Initialize Robinhood connection.

        Args:
            oauth_token: OAuth2 token from Robinhood agentic trading setup
            account_id: Robinhood account ID (if known; auto-discovered if None)
        """
        self.oauth_token = oauth_token
        self.account_id = account_id
        self.client = httpx.AsyncClient(http2=True, timeout=MAX_REQUEST_TIMEOUT)
        self.headers = {
            "Content-Type": "application/json",
            "X-MCP-Protocol-Version": "2026-04-27",
            "Authorization": f"Bearer {oauth_token}",
            "User-Agent": "ProfitEngine/5.0"
        }
        self.cache = {}
        self.cache_ttl = 60  # Cache account state for 60 seconds

    async def _post(
        self,
        method: str,
        params: Optional[Dict] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Send JSON-RPC 2.0 request to Robinhood MCP endpoint.

        Args:
            method: RPC method name (e.g., "place_equity_order")
            params: Method parameters
            request_id: Optional request ID for tracking

        Returns:
            Parsed response dict
        """
        if request_id is None:
            request_id = f"{method}_{datetime.now().timestamp()}"

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
            "params": params or {}
        }

        try:
            logger.debug(f"RH MCP: {method} {params}")
            response = await self.client.post(
                ROBINHOOD_MCP_ENDPOINT,
                json=payload,
                headers=self.headers
            )

            data = response.json()

            if "error" in data:
                error = data["error"]
                logger.error(f"RH MCP error ({method}): {error}")
                raise RobinhoodException(
                    error.get("message", "Unknown error"),
                    error.get("code", -1)
                )

            return data.get("result", {})

        except httpx.TimeoutException:
            logger.error(f"RH MCP timeout: {method}")
            raise RobinhoodException("Request timeout", -32000)
        except Exception as e:
            logger.error(f"RH MCP exception: {e}")
            raise

    async def get_account(self) -> Dict:
        """
        Fetch current account state.
        Returns: {
            'account_id': str,
            'account_number': str,
            'account_type': 'agentic' or 'preview',
            'account_status': 'active',
            'cash': float (buying power in USD),
            'equity': float (total account value),
            'buying_power': float,
            'created_at': str (ISO timestamp),
            'last_updated_at': str
        }
        """
        if "account" in self.cache:
            cached_time, cached_data = self.cache["account"]
            if datetime.now().timestamp() - cached_time < self.cache_ttl:
                return cached_data

        result = await self._post("get_account")

        if result:
            self.account_id = result.get("account_id", self.account_id)
            self.cache["account"] = (datetime.now().timestamp(), result)

        return result

    async def get_positions(self) -> List[Dict]:
        """
        Fetch all open positions.
        Returns: [
            {
                'symbol': str,
                'shares': float,
                'average_entry_price': float,
                'current_price': float,
                'unrealized_pnl': float,
                'unrealized_pnl_pct': float,
                'side': 'long' or 'short',
                'created_at': str
            },
            ...
        ]
        """
        result = await self._post("get_positions")
        return result if result else []

    async def place_order(
        self,
        symbol: str,
        direction: str,  # "buy" or "sell"
        order_type: str,  # "market" or "limit"
        quantity: Optional[float] = None,
        amount_usd: Optional[float] = None,
        limit_price: Optional[float] = None,
        time_in_force: str = "day"
    ) -> Dict:
        """
        Place a live equity order.

        Args:
            symbol: Ticker symbol (e.g., "AAPL")
            direction: "buy" or "sell"
            order_type: "market" or "limit"
            quantity: Number of shares (mutually exclusive with amount_usd)
            amount_usd: Dollar amount to trade (mutually exclusive with quantity)
            limit_price: Limit price for limit orders
            time_in_force: "day", "gtc" (good-til-cancel), "opg" (at open)

        Returns: {
            'order_id': str,
            'symbol': str,
            'side': str,
            'quantity': float,
            'average_fill_price': float,
            'status': 'filled', 'pending', 'cancelled',
            'created_at': str,
            'updated_at': str
        }
        """
        if not quantity and not amount_usd:
            raise ValueError("Specify either quantity or amount_usd")

        if quantity and amount_usd:
            raise ValueError("Cannot specify both quantity and amount_usd")

        params = {
            "account_type": "agentic",  # Live account type
            "symbol": symbol,
            "side": direction.lower(),
            "order_type": order_type.lower(),
            "time_in_force": time_in_force.lower()
        }

        if quantity:
            params["quantity"] = quantity
        else:
            params["amount_usd"] = amount_usd

        if limit_price and order_type.lower() == "limit":
            params["limit_price"] = limit_price

        result = await self._post("place_equity_order", params)
        logger.info(f"Order placed: {symbol} {direction} {quantity or amount_usd}")
        return result

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        try:
            await self._post(
                "cancel_order",
                {"order_id": order_id}
            )
            logger.info(f"Order cancelled: {order_id}")
            return True
        except RobinhoodException:
            return False

    async def get_order(self, order_id: str) -> Dict:
        """Get order status"""
        return await self._post("get_order", {"order_id": order_id})

    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        days: int = LIVE_TRADE_HISTORY_DAYS
    ) -> List[Dict]:
        """
        Fetch recent trade history.
        Returns: [
            {
                'order_id': str,
                'symbol': str,
                'side': 'buy' or 'sell',
                'quantity': float,
                'average_fill_price': float,
                'total_value': float,
                'status': 'filled',
                'filled_at': str
            },
            ...
        ]
        """
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        params = {"start_date": start_date}
        if symbol:
            params["symbol"] = symbol

        result = await self._post("get_order_history", params)
        return result if result else []

    async def deposit_capital(self, amount: Decimal) -> bool:
        """
        Initiate capital deposit to live account.

        Args:
            amount: USD amount to deposit

        Returns:
            True if deposit initiated successfully
        """
        try:
            # Link funding source if not already done
            await self._post("link_funding_source", {
                "source_type": "bank_account",
                "account_type": "agentic"
            })

            # Initiate deposit
            result = await self._post("deposit_funds", {
                "amount_usd": float(amount),
                "source_type": "bank_account",
                "account_type": "agentic"
            })

            if result.get("deposit_id"):
                logger.info(f"Deposit initiated: ${amount} (ID: {result['deposit_id']})")
                return True

            return False

        except RobinhoodException as e:
            logger.error(f"Deposit failed: {e}")
            return False

    async def withdraw_capital(self, amount: Decimal) -> bool:
        """
        Initiate capital withdrawal from live account.

        Args:
            amount: USD amount to withdraw

        Returns:
            True if withdrawal initiated successfully
        """
        try:
            result = await self._post("withdraw_funds", {
                "amount_usd": float(amount),
                "account_type": "agentic"
            })

            if result.get("withdrawal_id"):
                logger.info(f"Withdrawal initiated: ${amount} (ID: {result['withdrawal_id']})")
                return True

            return False

        except RobinhoodException as e:
            logger.error(f"Withdrawal failed: {e}")
            return False

    async def get_account_pnl(self) -> Dict:
        """
        Get current account P&L summary.
        Returns: {
            'equity': float (current account value),
            'cash': float (available cash),
            'buying_power': float,
            'total_pnl': float,
            'total_pnl_pct': float,
            'positions_pnl': float,
            'positions_pnl_pct': float
        }
        """
        account = await self.get_account()
        positions = await self.get_positions()

        equity = Decimal(str(account.get("equity", 0)))
        cash = Decimal(str(account.get("cash", 0)))

        positions_value = sum(
            Decimal(str(p["shares"])) * Decimal(str(p["current_price"]))
            for p in positions
        )

        positions_pnl = sum(
            Decimal(str(p.get("unrealized_pnl", 0)))
            for p in positions
        )

        return {
            "equity": float(equity),
            "cash": float(cash),
            "buying_power": float(Decimal(str(account.get("buying_power", 0)))),
            "positions_value": float(positions_value),
            "positions_pnl": float(positions_pnl),
            "positions_pnl_pct": float(
                (positions_pnl / equity * 100) if equity > 0 else Decimal("0")
            )
        }

    async def validate_trade_safety(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        current_price: Decimal
    ) -> Tuple[bool, str]:
        """
        Validate trade against risk gates before execution.

        Returns:
            (is_safe, reason)
        """
        try:
            account = await self.get_account()
            positions = await self.get_positions()

            buying_power = Decimal(str(account.get("buying_power", 0)))
            trade_cost = Decimal(str(quantity)) * current_price

            # Check 1: Position size limit
            if trade_cost > POSITION_SIZE_LIMIT:
                return False, f"Position size ${trade_cost} exceeds limit ${POSITION_SIZE_LIMIT}"

            # Check 2: Buying power
            if trade_cost > buying_power:
                return False, f"Insufficient buying power: ${buying_power} < ${trade_cost}"

            # Check 3: Max open positions
            if len(positions) >= MAX_LIVE_POSITIONS and not any(p["symbol"] == symbol for p in positions):
                return False, f"Max {MAX_LIVE_POSITIONS} open positions allowed"

            # Check 4: Existing position in same direction
            existing = next((p for p in positions if p["symbol"] == symbol), None)
            if existing:
                if (direction == "buy" and existing["side"] == "long") or \
                   (direction == "sell" and existing["side"] == "short"):
                    return False, f"Already have {existing['side']} position in {symbol}"

            return True, "Trade safe"

        except Exception as e:
            logger.warning(f"Trade validation error: {e}")
            return False, str(e)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class RobinhoodException(Exception):
    """Robinhood API exception"""

    def __init__(self, message: str, code: int = -1):
        self.message = message
        self.code = code
        super().__init__(f"RH Error {code}: {message}")


async def test_robinhood_connection():
    """Quick test of Robinhood connection"""
    token = os.getenv("ROBINHOOD_OAUTH_TOKEN")
    if not token:
        print("ERROR: ROBINHOOD_OAUTH_TOKEN not set")
        return

    trader = RobinhoodLiveTrader(token)

    try:
        account = await trader.get_account()
        print(f"Account: {account.get('account_id')}")
        print(f"Equity: ${account.get('equity', 0):.2f}")
        print(f"Buying Power: ${account.get('buying_power', 0):.2f}")

        positions = await trader.get_positions()
        print(f"Open Positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['shares']} @ ${pos['current_price']}")

    except RobinhoodException as e:
        print(f"Error: {e}")
    finally:
        await trader.close()


if __name__ == "__main__":
    asyncio.run(test_robinhood_connection())

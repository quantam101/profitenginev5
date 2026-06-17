"""
Robinhood Trading MCP Adapter
Connects to Robinhood's official agentic trading endpoint via MCP protocol
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import httpx
import json

try:
    from .models import TradeProposal, ExecutionResult, OrderState
except ImportError:
    from models import TradeProposal, ExecutionResult, OrderState

class RobinhoodMCPAdapter:
    """Adapter for Robinhood Trading MCP endpoint."""

    def __init__(self, oauth_token: str, mode: str = "preview"):
        """
        Initialize Robinhood MCP connection.

        Args:
            oauth_token: Robinhood OAuth2 token (from agentic trading account setup)
            mode: "preview" (paper) or "live" (real capital)
        """
        self.oauth_token = oauth_token
        self.mode = mode
        self.base_url = "https://agent.robinhood.com/mcp/trading"
        self.headers = {
            "Content-Type": "application/json",
            "X-MCP-Protocol-Version": "2026-04-27",
            "Authorization": f"Bearer {oauth_token}"
        }
        self.client = httpx.AsyncClient(http2=True, timeout=5.0)
        self.orders = {}

    async def submit_proposal(self, proposal: TradeProposal) -> ExecutionResult:
        """Submit approved proposal to Robinhood."""

        order_payload = {
            "jsonrpc": "2.0",
            "method": "place_equity_order",
            "id": proposal.proposal_id,
            "params": {
                "account_type": "preview" if self.mode == "preview" else "agentic",
                "symbol": proposal.symbol,
                "side": proposal.direction.lower(),
                "order_type": proposal.order_type.lower(),
                "limit_price": float(proposal.entry_price) if proposal.order_type == "LIMIT" else None,
                "time_in_force": proposal.time_in_force.lower(),
                "amount_usd": float(proposal.position_size_usd)
            }
        }

        try:
            response = await self.client.post(
                self.base_url,
                json=order_payload,
                headers=self.headers
            )

            result_data = response.json()

            if "error" in result_data:
                return ExecutionResult(
                    order_id=proposal.proposal_id,
                    state=OrderState.SUBMIT_FAILED,
                    timestamp=datetime.now(),
                    entry_price=proposal.entry_price,
                    quantity=Decimal('0'),
                    fill_price=Decimal('0'),
                    slippage=Decimal('0'),
                    fee=Decimal('0'),
                    realized_pnl=Decimal('0'),
                    is_complete=False
                )

            # Parse successful response
            order_id = result_data.get('result', {}).get('order_id', proposal.proposal_id)
            fill_price = Decimal(str(result_data.get('result', {}).get('fill_price', proposal.entry_price)))
            quantity = Decimal(str(result_data.get('result', {}).get('quantity', proposal.position_size_usd / fill_price)))

            self.orders[order_id] = {
                'proposal_id': proposal.proposal_id,
                'state': OrderState.FILLED,
                'fill_price': fill_price,
                'timestamp': datetime.now()
            }

            return ExecutionResult(
                order_id=order_id,
                state=OrderState.FILLED,
                timestamp=datetime.now(),
                entry_price=proposal.entry_price,
                quantity=quantity,
                fill_price=fill_price,
                slippage=abs(fill_price - proposal.entry_price),
                fee=Decimal(str(quantity * fill_price * Decimal('0.001'))),
                realized_pnl=Decimal('0'),
                is_complete=False
            )

        except Exception as e:
            return ExecutionResult(
                order_id=proposal.proposal_id,
                state=OrderState.BROKER_TIMEOUT,
                timestamp=datetime.now(),
                entry_price=proposal.entry_price,
                quantity=Decimal('0'),
                fill_price=Decimal('0'),
                slippage=Decimal('0'),
                fee=Decimal('0'),
                realized_pnl=Decimal('0'),
                is_complete=False
            )

    async def get_account_state(self) -> Dict:
        """Get current account state from Robinhood."""

        payload = {
            "jsonrpc": "2.0",
            "method": "get_account",
            "id": "account_state_query"
        }

        try:
            response = await self.client.post(self.base_url, json=payload, headers=self.headers)
            return response.json().get('result', {})
        except:
            return {}

    async def get_order_status(self, order_id: str) -> Dict:
        """Get status of submitted order."""

        payload = {
            "jsonrpc": "2.0",
            "method": "get_order",
            "id": order_id,
            "params": {"order_id": order_id}
        }

        try:
            response = await self.client.post(self.base_url, json=payload, headers=self.headers)
            return response.json().get('result', {})
        except:
            return {}

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order."""

        payload = {
            "jsonrpc": "2.0",
            "method": "cancel_order",
            "id": order_id,
            "params": {"order_id": order_id}
        }

        try:
            response = await self.client.post(self.base_url, json=payload, headers=self.headers)
            return "error" not in response.json()
        except:
            return False

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

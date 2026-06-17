"""
Trade Execution Agent — OrderProposal Executor via Robinhood MCP
==================================================================

Executes OrderProposals with sub-10ms latency target. Tracks order fills,
handles partial fills, and provides real-time order status monitoring.

Required env vars:
  ROBINHOOD_OAUTH_TOKEN   — Robinhood API OAuth token
  ROBINHOOD_API_URL       — Robinhood MCP endpoint (default: https://agent.robinhood.com/mcp/trading)

Usage:
  agent = TradeExecutionAgent()
  result = agent.execute_proposal(proposal)  # OrderProposal object
  status = agent.get_status(order_id)
  agent.cancel_order(order_id)
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from runtime.agents import AgentExecution


# ── Data Models ───────────────────────────────────────────────────────────

class OrderStatus(Enum):
    """Order execution state."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Buy or Sell."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Market, Limit, Stop, Stop-Limit."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class OrderProposal:
    """Order proposal for execution."""
    symbol: str
    quantity: float
    side: OrderSide
    order_type: OrderType
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    time_in_force: str = "day"  # GTC, IOC, FOK, day
    account_id: Optional[str] = None
    ref_id: Optional[str] = None  # Client reference ID


@dataclass
class OrderFill:
    """Represents a partial or full fill."""
    fill_id: str
    timestamp: datetime
    quantity: float
    price: float
    commission: float = 0.0


@dataclass
class OrderExecutionStatus:
    """Real-time order status snapshot."""
    order_id: str
    status: OrderStatus
    proposal: OrderProposal
    submitted_at: Optional[datetime] = None
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    avg_fill_price: float = 0.0
    total_commission: float = 0.0
    fills: List[OrderFill] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    last_status_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_terminal(self) -> bool:
        """Check if order is in terminal state."""
        return self.status in (OrderStatus.FILLED, OrderStatus.CANCELLED,
                               OrderStatus.REJECTED, OrderStatus.EXPIRED)

    def fill_percentage(self) -> float:
        """Return fill % (0.0 to 1.0)."""
        if self.proposal.quantity == 0:
            return 0.0
        return self.filled_quantity / self.proposal.quantity


# ── Robinhood MCP Client ──────────────────────────────────────────────────

class RobinhoodMCPClient:
    """Minimal Robinhood MCP HTTP client for order execution."""

    def __init__(self, token: str, base_url: str = "https://agent.robinhood.com/mcp/trading"):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._session_cache: Optional[Any] = None

    def _get_session(self) -> Any:
        """Lazy-load requests session (zero import overhead on module load)."""
        if self._session_cache is None:
            try:
                import requests
                self._session_cache = requests.Session()
                self._session_cache.headers.update({"Authorization": f"Bearer {self.token}"})
            except ImportError:
                raise ImportError("requests library required for Robinhood MCP client")
        return self._session_cache

    def submit_order(self, proposal: OrderProposal, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Submit order to Robinhood MCP.
        Returns: {"order_id": "...", "status": "submitted", ...}
        """
        session = self._get_session()
        payload = {
            "action": "submit_order",
            "symbol": proposal.symbol,
            "quantity": proposal.quantity,
            "side": proposal.side.value,
            "type": proposal.order_type.value,
            "time_in_force": proposal.time_in_force,
        }
        if proposal.price:
            payload["price"] = proposal.price
        if proposal.stop_price:
            payload["stop_price"] = proposal.stop_price
        if proposal.ref_id:
            payload["ref_id"] = proposal.ref_id

        try:
            resp = session.post(
                f"{self.base_url}/orders",
                json=payload,
                timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "order_id": None}

    def get_order_status(self, order_id: str, timeout: float = 3.0) -> Dict[str, Any]:
        """
        Poll order status from Robinhood MCP.
        Returns: {"order_id": "...", "status": "filled", "fills": [...], ...}
        """
        session = self._get_session()
        try:
            resp = session.get(
                f"{self.base_url}/orders/{order_id}",
                timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "order_id": order_id}

    def cancel_order(self, order_id: str, timeout: float = 3.0) -> Dict[str, Any]:
        """Cancel an open order."""
        session = self._get_session()
        try:
            resp = session.post(
                f"{self.base_url}/orders/{order_id}/cancel",
                timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "order_id": order_id}


# ── Trade Execution Agent ─────────────────────────────────────────────────

class TradeExecutionAgent:
    """
    High-performance order executor with <10ms target latency.
    Tracks fills and partial-fill scenarios.
    """

    def __init__(self):
        self.id = "agent-trade-execution"
        self.token = os.getenv("ROBINHOOD_OAUTH_TOKEN", "")
        self.api_url = os.getenv("ROBINHOOD_API_URL", "https://agent.robinhood.com/mcp/trading")

        self.client = RobinhoodMCPClient(self.token, self.api_url)
        self._orders: Dict[str, OrderExecutionStatus] = {}
        self._order_id_counter = 0
        self._start_time = time.perf_counter()

    def execute_proposal(self, proposal: OrderProposal) -> OrderExecutionStatus:
        """
        Execute an OrderProposal with sub-10ms latency.
        Returns OrderExecutionStatus with order_id and status.
        """
        start = time.perf_counter()

        # Validate proposal
        if not proposal.symbol or proposal.quantity <= 0:
            return OrderExecutionStatus(
                order_id="INVALID",
                status=OrderStatus.REJECTED,
                proposal=proposal,
                rejection_reason="Invalid symbol or quantity"
            )

        # Generate order ID (deterministic for reproducibility)
        self._order_id_counter += 1
        order_id = f"ORD-{int(self._start_time)}-{self._order_id_counter:06d}"

        # Submit to Robinhood MCP
        response = self.client.submit_order(proposal, timeout=0.008)  # 8ms SLA

        if response.get("error"):
            status = OrderExecutionStatus(
                order_id=order_id,
                status=OrderStatus.REJECTED,
                proposal=proposal,
                submitted_at=datetime.now(timezone.utc),
                rejection_reason=response["error"]
            )
        else:
            # MCP returned successfully
            status = OrderExecutionStatus(
                order_id=response.get("order_id", order_id),
                status=OrderStatus(response.get("status", "submitted")),
                proposal=proposal,
                submitted_at=datetime.now(timezone.utc),
                filled_quantity=response.get("filled_quantity", 0.0),
                remaining_quantity=proposal.quantity - response.get("filled_quantity", 0.0),
                avg_fill_price=response.get("avg_fill_price", 0.0),
            )

        # Cache order for tracking
        self._orders[status.order_id] = status

        latency_ms = (time.perf_counter() - start) * 1000
        print(f"[TradeExecution] Order {status.order_id} submitted in {latency_ms:.2f}ms")

        return status

    def get_status(self, order_id: str) -> OrderExecutionStatus:
        """
        Get real-time order status. Polls Robinhood MCP if not cached as terminal.
        """
        # Return cached if terminal
        if order_id in self._orders:
            cached = self._orders[order_id]
            if cached.is_terminal():
                return cached

        # Poll Robinhood MCP
        start = time.perf_counter()
        response = self.client.get_order_status(order_id, timeout=0.003)  # 3ms SLA
        latency_ms = (time.perf_counter() - start) * 1000

        if response.get("error"):
            return OrderExecutionStatus(
                order_id=order_id,
                status=OrderStatus.REJECTED,
                proposal=OrderProposal(symbol="", quantity=0, side=OrderSide.BUY,
                                       order_type=OrderType.MARKET),
                rejection_reason=response["error"]
            )

        # Parse fills
        fills = []
        for fill_data in response.get("fills", []):
            fills.append(OrderFill(
                fill_id=fill_data.get("fill_id", ""),
                timestamp=datetime.fromisoformat(fill_data.get("timestamp", "")),
                quantity=fill_data.get("quantity", 0.0),
                price=fill_data.get("price", 0.0),
                commission=fill_data.get("commission", 0.0)
            ))

        # Calculate aggregate metrics
        filled_qty = sum(f.quantity for f in fills)
        total_commission = sum(f.commission for f in fills)
        avg_price = sum(f.quantity * f.price for f in fills) / filled_qty if filled_qty > 0 else 0.0

        # Create cached status object (from order proposal stored)
        proposal = self._orders.get(order_id, OrderExecutionStatus(
            order_id=order_id,
            status=OrderStatus.PENDING,
            proposal=OrderProposal(symbol="", quantity=0, side=OrderSide.BUY,
                                   order_type=OrderType.MARKET)
        )).proposal

        status = OrderExecutionStatus(
            order_id=order_id,
            status=OrderStatus(response.get("status", "pending")),
            proposal=proposal,
            submitted_at=datetime.fromisoformat(response.get("submitted_at", "")),
            filled_quantity=filled_qty,
            remaining_quantity=proposal.quantity - filled_qty,
            avg_fill_price=avg_price,
            total_commission=total_commission,
            fills=fills,
            last_status_check=datetime.now(timezone.utc)
        )

        # Cache if terminal
        if status.is_terminal():
            self._orders[order_id] = status

        print(f"[TradeExecution] Order {order_id} status checked in {latency_ms:.2f}ms: "
              f"{status.filled_quantity}/{proposal.quantity} filled @ {status.avg_fill_price:.2f}")

        return status

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order. Returns True if successful."""
        response = self.client.cancel_order(order_id, timeout=0.003)

        if response.get("error"):
            print(f"[TradeExecution] Cancel failed for {order_id}: {response['error']}")
            return False

        # Update cache
        if order_id in self._orders:
            self._orders[order_id].status = OrderStatus.CANCELLED
            self._orders[order_id].last_status_check = datetime.now(timezone.utc)

        print(f"[TradeExecution] Order {order_id} cancelled successfully")
        return True

    def get_all_orders(self) -> List[OrderExecutionStatus]:
        """Return all tracked orders."""
        return list(self._orders.values())

    def clear_filled_orders(self) -> int:
        """Clear terminal orders from cache. Returns count cleared."""
        before = len(self._orders)
        self._orders = {
            k: v for k, v in self._orders.items()
            if not v.is_terminal()
        }
        return before - len(self._orders)


# ── Agent Interface (for ProfitEngine runtime) ────────────────────────────

class Agent:
    """ProfitEngine Agent interface for trade execution."""

    def __init__(self):
        self.id = "agent-trade-execution"
        self.executor = TradeExecutionAgent()

    def __call__(self, context: str) -> AgentExecution:
        """
        Parse order proposals from context and execute.
        Context JSON format:
            {
              "orders": [
                {
                  "symbol": "AAPL",
                  "quantity": 10,
                  "side": "buy",
                  "type": "market",
                  "price": null,
                  "stop_price": null
                }
              ]
            }
        """
        try:
            data = json.loads(context)
            orders = data.get("orders", [])
            results = []

            for order_data in orders:
                proposal = OrderProposal(
                    symbol=order_data["symbol"],
                    quantity=order_data["quantity"],
                    side=OrderSide(order_data.get("side", "buy")),
                    order_type=OrderType(order_data.get("type", "market")),
                    price=order_data.get("price"),
                    stop_price=order_data.get("stop_price"),
                    time_in_force=order_data.get("time_in_force", "day"),
                )

                status = self.executor.execute_proposal(proposal)
                results.append({
                    "order_id": status.order_id,
                    "status": status.status.value,
                    "symbol": status.proposal.symbol,
                    "quantity": status.proposal.quantity,
                })

            return AgentExecution(
                output=json.dumps(results, indent=2),
                metrics={
                    "orders_executed": len(results),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        except Exception as e:
            return AgentExecution(
                output=json.dumps({"error": str(e)}),
                metrics={"error": "execution_failed"}
            )


# ── CLI for local testing ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Local test (no real Robinhood connection needed)
        agent = Agent()

        test_order = json.dumps({
            "orders": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "side": "buy",
                    "type": "market"
                }
            ]
        })

        result = agent(test_order)
        print("Output:")
        print(result.output)
        print("\nMetrics:")
        print(result.metrics)
    else:
        print("Trade Execution Agent — ready for execution")
        print("Usage: python -m runtime.agent_impls.agent_trade_execution test")

"""
Agent Position Manager - Manages open trading positions with P&L tracking.

Maintains open positions, tracks unrealized P&L, enforces 3-position maximum,
and provides position lifecycle management (open, close, list, analyze).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import uuid


class PositionStatus(Enum):
    """Position lifecycle states."""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"
    SUSPENDED = "suspended"


class PositionSide(Enum):
    """Position direction (long or short)."""
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """Represents a single trading position."""

    position_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    side: PositionSide = PositionSide.LONG
    entry_price: float = 0.0
    quantity: float = 0.0
    current_price: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    commission: float = 0.0
    notes: str = ""

    def get_entry_value(self) -> float:
        """Calculate total value at entry (excluding commission)."""
        return self.entry_price * self.quantity

    def get_current_value(self) -> float:
        """Calculate current position value at market price."""
        return self.current_price * self.quantity

    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L for long positions (opposite for short)."""
        if self.side == PositionSide.LONG:
            return (self.current_price - self.entry_price) * self.quantity - self.commission
        else:  # SHORT
            return (self.entry_price - self.current_price) * self.quantity - self.commission

    def get_unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L as percentage."""
        entry_value = self.get_entry_value()
        if entry_value == 0:
            return 0.0
        return (self.get_unrealized_pnl() / entry_value) * 100

    def get_exposure(self) -> float:
        """Get notional exposure (for margin/risk calculations)."""
        return abs(self.get_current_value())

    def update_price(self, new_price: float) -> None:
        """Update current market price."""
        if new_price < 0:
            raise ValueError("Price cannot be negative")
        self.current_price = new_price

    def __repr__(self) -> str:
        return (
            f"Position({self.position_id}: {self.symbol} {self.side.value} "
            f"qty={self.quantity} entry={self.entry_price} "
            f"current={self.current_price} pnl={self.get_unrealized_pnl():.2f})"
        )


class AgentPositionManager:
    """
    Manages trading positions for automated trading agents.

    Features:
    - Open/close positions with full audit trail
    - Real-time P&L tracking (realized and unrealized)
    - 3-position maximum enforcement
    - Position status lifecycle management
    - Risk metrics (exposure, concentration)
    """

    MAX_OPEN_POSITIONS = 3

    def __init__(self, agent_id: str = "default"):
        """Initialize position manager for an agent."""
        self.agent_id = agent_id
        self.positions: Dict[str, Position] = {}  # position_id -> Position
        self.closed_positions: List[Position] = []
        self.position_history: List[Dict] = []
        self.realized_pnl: float = 0.0

    def add_position(
        self,
        symbol: str,
        side: PositionSide,
        entry_price: float,
        quantity: float,
        current_price: float,
        commission: float = 0.0,
        notes: str = ""
    ) -> Position:
        """
        Open a new trading position.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTC/USD')
            side: PositionSide.LONG or PositionSide.SHORT
            entry_price: Price at which position was entered
            quantity: Number of units/shares in position
            current_price: Current market price
            commission: Trading commission/fees
            notes: Optional notes about position

        Returns:
            Position: The newly created position object

        Raises:
            ValueError: If position exceeds MAX_OPEN_POSITIONS or invalid parameters
        """
        # Validate inputs
        if quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {quantity}")
        if entry_price < 0 or current_price < 0:
            raise ValueError("Prices cannot be negative")
        if commission < 0:
            raise ValueError("Commission cannot be negative")

        # Check position limit
        open_count = len([p for p in self.positions.values()
                         if p.status == PositionStatus.OPEN])
        if open_count >= self.MAX_OPEN_POSITIONS:
            raise ValueError(
                f"Cannot open position: already at maximum "
                f"({open_count}/{self.MAX_OPEN_POSITIONS} open positions)"
            )

        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            current_price=current_price,
            status=PositionStatus.OPEN,
            commission=commission,
            notes=notes
        )

        # Store position
        self.positions[position.position_id] = position

        # Log to history
        self._log_event("POSITION_OPENED", position)

        return position

    def close_position(
        self,
        position_id: str,
        exit_price: Optional[float] = None,
        partial_quantity: Optional[float] = None,
        close_notes: str = ""
    ) -> Tuple[Position, float]:
        """
        Close an open position (fully or partially).

        Args:
            position_id: ID of position to close
            exit_price: Price at which position is closed (uses current if None)
            partial_quantity: Close only this amount (partial close). None = full close
            close_notes: Notes about closure reason

        Returns:
            Tuple of (Position, realized_pnl) for the closed portion

        Raises:
            ValueError: If position not found or invalid parameters
        """
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")

        position = self.positions[position_id]
        if position.status == PositionStatus.CLOSED:
            raise ValueError(f"Position {position_id} is already closed")

        # Use current price if exit price not provided
        if exit_price is None:
            exit_price = position.current_price

        # Validate exit price
        if exit_price < 0:
            raise ValueError("Exit price cannot be negative")

        # Determine quantity to close
        qty_to_close = partial_quantity or position.quantity
        if qty_to_close <= 0 or qty_to_close > position.quantity:
            raise ValueError(
                f"Invalid close quantity {qty_to_close}, "
                f"position has {position.quantity}"
            )

        # Calculate realized P&L for closed portion
        if position.side == PositionSide.LONG:
            realized = (exit_price - position.entry_price) * qty_to_close
        else:  # SHORT
            realized = (position.entry_price - exit_price) * qty_to_close

        # Apply commission proportionally
        commission_portion = position.commission * (qty_to_close / position.quantity)
        realized -= commission_portion

        # Update position or close it
        if partial_quantity and partial_quantity < position.quantity:
            # Partial close - reduce quantity
            position.quantity -= qty_to_close
            position.status = PositionStatus.PARTIALLY_CLOSED
            closed_position = Position(
                symbol=position.symbol,
                side=position.side,
                entry_price=position.entry_price,
                quantity=qty_to_close,
                current_price=exit_price,
                status=PositionStatus.CLOSED,
                commission=commission_portion,
                notes=f"Partial close: {close_notes}"
            )
        else:
            # Full close
            position.current_price = exit_price
            position.quantity = qty_to_close  # Ensure exact quantity
            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.utcnow()
            closed_position = position

        # Update realized P&L
        self.realized_pnl += realized

        # Move to closed positions
        if position.status == PositionStatus.CLOSED:
            del self.positions[position_id]

        self.closed_positions.append(closed_position)

        # Log to history
        self._log_event("POSITION_CLOSED", closed_position, {"realized_pnl": realized})

        return closed_position, realized

    def get_pnl(self, position_id: Optional[str] = None) -> Dict:
        """
        Get P&L information for a position or all positions.

        Args:
            position_id: Specific position ID, or None for portfolio totals

        Returns:
            Dict with realized_pnl, unrealized_pnl, total_pnl, and per-position breakdown

        Raises:
            ValueError: If position_id provided but not found
        """
        if position_id:
            if position_id not in self.positions:
                raise ValueError(f"Position {position_id} not found")

            position = self.positions[position_id]
            return {
                "position_id": position_id,
                "symbol": position.symbol,
                "unrealized_pnl": position.get_unrealized_pnl(),
                "unrealized_pnl_pct": position.get_unrealized_pnl_pct(),
                "exposure": position.get_exposure(),
                "status": position.status.value
            }

        # Portfolio-wide P&L
        total_unrealized = sum(
            p.get_unrealized_pnl() for p in self.positions.values()
            if p.status == PositionStatus.OPEN
        )

        total_pnl = self.realized_pnl + total_unrealized

        positions_breakdown = [
            {
                "position_id": p.position_id,
                "symbol": p.symbol,
                "side": p.side.value,
                "quantity": p.quantity,
                "unrealized_pnl": p.get_unrealized_pnl(),
                "unrealized_pnl_pct": p.get_unrealized_pnl_pct()
            }
            for p in self.positions.values()
        ]

        return {
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": total_unrealized,
            "total_pnl": total_pnl,
            "open_positions": len(self.positions),
            "closed_positions": len(self.closed_positions),
            "positions": positions_breakdown
        }

    def list_positions(self, status: Optional[PositionStatus] = None) -> List[Position]:
        """
        List all positions, optionally filtered by status.

        Args:
            status: Filter by PositionStatus (OPEN, CLOSED, etc.), or None for all

        Returns:
            List of Position objects matching filter
        """
        positions = list(self.positions.values()) + self.closed_positions

        if status:
            return [p for p in positions if p.status == status]

        return positions

    def get_position(self, position_id: str) -> Optional[Position]:
        """Retrieve a specific position by ID."""
        return self.positions.get(position_id)

    def update_market_prices(self, price_map: Dict[str, float]) -> None:
        """
        Update current market prices for positions.

        Args:
            price_map: Dict mapping symbol -> current_price
        """
        for position in self.positions.values():
            if position.symbol in price_map:
                position.update_price(price_map[position.symbol])

    def get_total_exposure(self) -> float:
        """Get total notional exposure across all open positions."""
        return sum(p.get_exposure() for p in self.positions.values())

    def get_position_count(self) -> int:
        """Get count of currently open positions."""
        return len([p for p in self.positions.values()
                   if p.status == PositionStatus.OPEN])

    def can_open_position(self) -> bool:
        """Check if another position can be opened without exceeding limit."""
        return self.get_position_count() < self.MAX_OPEN_POSITIONS

    def suspend_position(self, position_id: str, reason: str = "") -> Position:
        """
        Temporarily suspend a position (prevent closing/trading).

        Args:
            position_id: Position to suspend
            reason: Reason for suspension

        Returns:
            The suspended Position
        """
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")

        position = self.positions[position_id]
        position.status = PositionStatus.SUSPENDED
        self._log_event("POSITION_SUSPENDED", position, {"reason": reason})

        return position

    def resume_position(self, position_id: str) -> Position:
        """Resume a suspended position."""
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")

        position = self.positions[position_id]
        position.status = PositionStatus.OPEN
        self._log_event("POSITION_RESUMED", position)

        return position

    def get_concentration(self, symbol: str) -> float:
        """
        Get total exposure concentration for a symbol (sum of all positions).

        Args:
            symbol: Symbol to analyze

        Returns:
            Total notional exposure for symbol
        """
        return sum(
            p.get_exposure() for p in self.positions.values()
            if p.symbol == symbol and p.status == PositionStatus.OPEN
        )

    def clear_history(self) -> None:
        """Clear position history log."""
        self.position_history.clear()

    def _log_event(self, event_type: str, position: Position,
                   extra_data: Optional[Dict] = None) -> None:
        """Internal method to log position events."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "position_id": position.position_id,
            "symbol": position.symbol,
            "side": position.side.value,
            "quantity": position.quantity,
            "price": position.current_price,
            **(extra_data or {})
        }
        self.position_history.append(log_entry)

    def __repr__(self) -> str:
        pnl_data = self.get_pnl()
        return (
            f"AgentPositionManager(agent={self.agent_id}, "
            f"open={self.get_position_count()}/{self.MAX_OPEN_POSITIONS}, "
            f"total_pnl={pnl_data['total_pnl']:.2f})"
        )

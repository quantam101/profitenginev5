"""
Agent Spread Validator — Ensures bid-ask spread <= 25 basis points (0.25%).

Validates market data spreads for agent trading operations with configurable
thresholds and comprehensive error handling.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpreadMetrics:
    """Container for spread calculation results."""
    bid: Decimal
    ask: Decimal
    spread_bps: Decimal
    spread_pct: Decimal
    is_valid: bool
    margin_to_limit: Decimal
    confidence: float = 1.0


class AgentSpreadValidator:
    """
    Validates bid-ask spreads for agent trading operations.

    Enforces maximum spread of 25 basis points (0.25%) to ensure
    trading quality and prevent slippage during automated execution.
    """

    MAX_SPREAD_BPS = Decimal("25")  # 25 basis points = 0.25%
    MIN_PRICE = Decimal("0.01")
    DECIMAL_PLACES = 8

    def __init__(self, max_spread_bps: Optional[Decimal] = None, strict_mode: bool = True):
        """
        Initialize the validator.

        Args:
            max_spread_bps: Custom maximum spread in basis points (default: 25)
            strict_mode: If True, reject spreads exactly at limit (default: True)
        """
        self.max_spread_bps = max_spread_bps or self.MAX_SPREAD_BPS
        self.strict_mode = strict_mode
        self.validation_history: List[SpreadMetrics] = []

    def calc_spread(self, bid: float, ask: float) -> SpreadMetrics:
        """
        Calculate the bid-ask spread in basis points.

        Formula:
            spread_bps = ((ask - bid) / midpoint) * 10000
            where midpoint = (bid + ask) / 2

        Args:
            bid: Bid price (lower price buyers offer)
            ask: Ask price (lower price sellers accept)

        Returns:
            SpreadMetrics containing spread in bps and percentage

        Raises:
            ValueError: If prices are invalid or bid >= ask
        """
        bid_dec = Decimal(str(bid))
        ask_dec = Decimal(str(ask))

        # Validate price ranges
        if bid_dec <= 0 or ask_dec <= 0:
            raise ValueError(
                f"Prices must be positive. Got bid={bid_dec}, ask={ask_dec}"
            )

        if bid_dec >= ask_dec:
            raise ValueError(
                f"Bid ({bid_dec}) must be less than ask ({ask_dec})"
            )

        if ask_dec < self.MIN_PRICE or bid_dec < self.MIN_PRICE:
            raise ValueError(
                f"Prices below minimum ({self.MIN_PRICE}). "
                f"Got bid={bid_dec}, ask={ask_dec}"
            )

        # Calculate midpoint and spread
        midpoint = (bid_dec + ask_dec) / Decimal(2)
        spread_raw = ask_dec - bid_dec

        # Convert to basis points (1 bp = 0.01%)
        spread_bps = (spread_raw / midpoint) * Decimal(10000)
        spread_bps = spread_bps.quantize(
            Decimal(10) ** -self.DECIMAL_PLACES,
            rounding=ROUND_HALF_UP
        )

        # Convert to percentage
        spread_pct = spread_bps / Decimal(100)

        # Determine validity
        if self.strict_mode:
            is_valid = spread_bps < self.max_spread_bps
        else:
            is_valid = spread_bps <= self.max_spread_bps

        # Calculate margin to limit
        margin_to_limit = self.max_spread_bps - spread_bps

        metrics = SpreadMetrics(
            bid=bid_dec,
            ask=ask_dec,
            spread_bps=spread_bps,
            spread_pct=spread_pct,
            is_valid=is_valid,
            margin_to_limit=margin_to_limit
        )

        return metrics

    def validate(
        self,
        bid: float,
        ask: float,
        symbol: Optional[str] = None,
        confidence: float = 1.0
    ) -> Tuple[bool, SpreadMetrics, str]:
        """
        Validate a bid-ask spread against the maximum limit.

        Args:
            bid: Bid price
            ask: Ask price
            symbol: Optional trading symbol for logging (e.g., 'BTC/USD')
            confidence: Data confidence score 0-1 (default: 1.0)

        Returns:
            Tuple of (is_valid, metrics, message)
            - is_valid: True if spread <= max_spread_bps
            - metrics: SpreadMetrics with detailed calculations
            - message: Human-readable validation result

        Example:
            >>> validator = AgentSpreadValidator()
            >>> is_valid, metrics, msg = validator.validate(100.00, 100.05, "BTC/USD")
            >>> print(msg)
            'PASS: BTC/USD spread 50.00 bps (0.05%) within limit (25.00 bps)'
        """
        try:
            metrics = self.calc_spread(bid, ask)
            metrics.confidence = confidence

            # Add to history
            self.validation_history.append(metrics)

            # Generate message
            symbol_label = f"{symbol} " if symbol else ""
            status = "PASS" if metrics.is_valid else "FAIL"

            message = (
                f"{status}: {symbol_label}spread {metrics.spread_bps} bps "
                f"({metrics.spread_pct}%) "
                f"{'within' if metrics.is_valid else 'exceeds'} "
                f"limit ({self.max_spread_bps} bps)"
            )

            if metrics.is_valid and metrics.margin_to_limit < Decimal(5):
                message += f" (WARNING: only {metrics.margin_to_limit} bps margin)"

            if confidence < 1.0:
                message += f" [confidence: {confidence:.1%}]"

            log_level = logging.INFO if metrics.is_valid else logging.WARNING
            logger.log(log_level, message)

            return metrics.is_valid, metrics, message

        except ValueError as e:
            message = f"INVALID: {str(e)}"
            logger.error(message)
            # Return dummy metrics for error case
            dummy_metrics = SpreadMetrics(
                bid=Decimal(str(bid)) if bid else Decimal(0),
                ask=Decimal(str(ask)) if ask else Decimal(0),
                spread_bps=Decimal(-1),
                spread_pct=Decimal(-1),
                is_valid=False,
                margin_to_limit=Decimal(0),
                confidence=confidence
            )
            return False, dummy_metrics, message

    def batch_validate(
        self,
        prices: List[Tuple[float, float, Optional[str]]]
    ) -> Dict[str, List[Tuple[bool, SpreadMetrics, str]]]:
        """
        Validate multiple bid-ask pairs in one call.

        Args:
            prices: List of (bid, ask, symbol) tuples

        Returns:
            Dictionary mapping symbols to validation results
        """
        results = {}
        for bid, ask, symbol in prices:
            symbol_key = symbol or f"pair_{len(results)}"
            is_valid, metrics, msg = self.validate(bid, ask, symbol)
            results[symbol_key] = (is_valid, metrics, msg)

        return results

    def get_summary(self) -> Dict:
        """
        Get summary statistics from validation history.

        Returns:
            Dictionary with pass rate, average spread, and extremes
        """
        if not self.validation_history:
            return {
                "total_validations": 0,
                "pass_count": 0,
                "fail_count": 0,
                "pass_rate": 0.0,
                "avg_spread_bps": 0,
                "min_spread_bps": 0,
                "max_spread_bps": 0
            }

        valid_metrics = [m for m in self.validation_history if m.is_valid]
        all_spreads = [m.spread_bps for m in self.validation_history]

        return {
            "total_validations": len(self.validation_history),
            "pass_count": len(valid_metrics),
            "fail_count": len(self.validation_history) - len(valid_metrics),
            "pass_rate": len(valid_metrics) / len(self.validation_history),
            "avg_spread_bps": float(sum(all_spreads) / len(all_spreads)),
            "min_spread_bps": float(min(all_spreads)),
            "max_spread_bps": float(max(all_spreads))
        }

    def clear_history(self) -> None:
        """Clear validation history."""
        self.validation_history = []


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    validator = AgentSpreadValidator()

    # Test case 1: Valid spread (5 bps)
    is_valid, metrics, msg = validator.validate(100.00, 100.005, "BTC/USD")
    print(msg)

    # Test case 2: Invalid spread (50 bps)
    is_valid, metrics, msg = validator.validate(100.00, 100.05, "ETH/USD")
    print(msg)

    # Test case 3: At limit in strict mode
    is_valid, metrics, msg = validator.validate(1000.00, 1002.5, "SPY")
    print(msg)

    # Test case 4: Batch validation
    batch_results = validator.batch_validate([
        (100.00, 100.005, "BTC/USD"),
        (50.00, 50.10, "ETH/USD"),
        (1000.00, 1000.50, "SPY")
    ])

    print("\nBatch Results:")
    for symbol, (is_valid, metrics, msg) in batch_results.items():
        print(f"  {symbol}: {msg}")

    # Summary statistics
    print("\nValidation Summary:")
    summary = validator.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

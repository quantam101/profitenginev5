"""
STOCK COMPLIANCE MONITOR — Real-time regulatory & broker restrictions
Ensures trades comply with SEC rules, short-sale restrictions, and broker limits.

Checks:
- FINRA SHO list (short-sale circuit breaker)
- Trading halts
- Margin requirements
- Borrow availability
- Uptick rule status
- Fail-to-deliver tracking
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplianceStatus:
    """Stock compliance check result"""
    symbol: str
    tradable: bool
    short_available: bool
    uptick_rule_active: bool
    trading_halt: bool
    margin_ok: bool
    borrow_available: bool
    on_sho_list: bool
    fail_to_deliver_risk: bool
    reason: Optional[str] = None
    
    def is_compliant(self) -> bool:
        """Check if stock passes all compliance checks"""
        return (
            self.tradable and 
            self.margin_ok and 
            not self.trading_halt and
            not self.on_sho_list
        )


class StockComplianceMonitor:
    """Monitor stock compliance in real-time"""

    def __init__(self):
        """Initialize compliance monitor"""
        self.sho_list = set()  # FINRA short-sale halt list
        self.trading_halts = set()  # Stocks with trading halts
        self.fail_to_deliver = set()  # High fail-to-deliver risk
        self.borrow_restricted = set()  # No short borrow available
        self.update_lists()

    def update_lists(self):
        """Update regulatory lists (in production: real API calls)"""
        # In real system: fetch from FINRA, SEC, broker APIs
        # For now, mock data
        self.sho_list = {
            # Example: stocks on SHO list
        }
        self.trading_halts = {
            # Example: stocks with halts
        }
        self.fail_to_deliver = {
            # Example: high FTD risk stocks
        }
        self.borrow_restricted = {
            # Example: no borrow available
        }
        logger.info("Compliance lists updated")

    async def check_compliance(self, symbol: str, action: str = 'BUY') -> ComplianceStatus:
        """
        Check if stock is compliant for trading
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
        
        Returns:
            ComplianceStatus with all checks
        """
        try:
            # Check each compliance rule
            on_sho = symbol in self.sho_list
            has_halt = symbol in self.trading_halts
            has_ftd = symbol in self.fail_to_deliver
            no_borrow = symbol in self.borrow_restricted
            
            # Determine short availability
            short_ok = not (on_sho or no_borrow)
            
            # Uptick rule (simplified)
            uptick_active = on_sho
            
            # Margin check (simplified)
            margin_ok = not has_halt
            
            # Overall tradability
            tradable = not (has_halt or has_ftd)
            
            # Determine reason if non-compliant
            reason = None
            if on_sho:
                reason = "Stock on FINRA SHO list"
            elif has_halt:
                reason = "Trading halt in effect"
            elif has_ftd:
                reason = "High fail-to-deliver risk"
            elif no_borrow and action == 'SELL':
                reason = "No borrow availability for short"
            
            status = ComplianceStatus(
                symbol=symbol,
                tradable=tradable,
                short_available=short_ok,
                uptick_rule_active=uptick_active,
                trading_halt=has_halt,
                margin_ok=margin_ok,
                borrow_available=not no_borrow,
                on_sho_list=on_sho,
                fail_to_deliver_risk=has_ftd,
                reason=reason,
            )
            
            if not status.is_compliant():
                logger.warning(f"{symbol} compliance FAILED: {reason}")
            else:
                logger.debug(f"{symbol} compliance OK")
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking compliance for {symbol}: {e}")
            return ComplianceStatus(
                symbol=symbol,
                tradable=False,
                short_available=False,
                uptick_rule_active=True,
                trading_halt=True,
                margin_ok=False,
                borrow_available=False,
                on_sho_list=True,
                fail_to_deliver_risk=True,
                reason=f"Compliance check error: {e}",
            )

    def get_tradable_symbols(self, symbol_list: List[str]) -> List[str]:
        """Filter symbol list to only compliant stocks"""
        import asyncio
        tradable = []
        for symbol in symbol_list:
            status = asyncio.run(self.check_compliance(symbol))
            if status.is_compliant():
                tradable.append(symbol)
        return tradable

    def add_to_sho_list(self, symbol: str):
        """Add symbol to SHO list (regulatory)"""
        self.sho_list.add(symbol)
        logger.warning(f"{symbol} added to SHO list")

    def remove_from_sho_list(self, symbol: str):
        """Remove symbol from SHO list"""
        self.sho_list.discard(symbol)
        logger.info(f"{symbol} removed from SHO list")

    def add_trading_halt(self, symbol: str, reason: str = ""):
        """Add symbol to trading halts"""
        self.trading_halts.add(symbol)
        logger.warning(f"{symbol} trading halted: {reason}")

    def clear_trading_halt(self, symbol: str):
        """Clear trading halt"""
        self.trading_halts.discard(symbol)
        logger.info(f"{symbol} trading halt cleared")

    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance monitoring report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'sho_list_count': len(self.sho_list),
            'trading_halts_count': len(self.trading_halts),
            'fail_to_deliver_count': len(self.fail_to_deliver),
            'borrow_restricted_count': len(self.borrow_restricted),
            'sho_symbols': list(self.sho_list),
            'halted_symbols': list(self.trading_halts),
        }


# Global compliance monitor instance
_compliance_monitor = None


def get_compliance_monitor() -> StockComplianceMonitor:
    """Get or create global compliance monitor"""
    global _compliance_monitor
    if _compliance_monitor is None:
        _compliance_monitor = StockComplianceMonitor()
    return _compliance_monitor

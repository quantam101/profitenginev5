"""
Data Freshness Validation Module

Validates all market quotes and data within a 15-second threshold to ensure
data integrity and timeliness across the agent ecosystem. Provides comprehensive
validation metrics and summary reporting.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class FreshnessStatus(Enum):
    """Enum for data freshness status levels."""
    FRESH = "fresh"
    STALE = "stale"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class QuoteData:
    """Container for quote metadata and timestamp information."""
    symbol: str
    price: float
    timestamp: datetime
    source: str
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FreshnessMetric:
    """Container for individual freshness validation result."""
    symbol: str
    age_seconds: float
    status: FreshnessStatus
    is_valid: bool
    threshold_seconds: int
    source: str
    timestamp: datetime
    warning_message: Optional[str] = None


@dataclass
class FreshnessSummary:
    """Container for aggregate freshness validation report."""
    total_quotes: int
    fresh_count: int
    stale_count: int
    critical_count: int
    validation_timestamp: datetime
    overall_status: FreshnessStatus
    freshness_percentage: float
    oldest_quote_age: float
    newest_quote_age: float
    failed_symbols: List[str] = field(default_factory=list)
    average_age: float = 0.0
    metrics_by_symbol: Dict[str, FreshnessMetric] = field(default_factory=dict)


class AgentDataFreshness:
    """
    Validates all market quotes and data within a 15-second threshold.

    Provides methods to check individual quote age, validate all quotes,
    and generate comprehensive freshness reports for the agent ecosystem.
    """

    DEFAULT_THRESHOLD_SECONDS = 15
    CRITICAL_THRESHOLD_SECONDS = 30
    STALE_THRESHOLD_SECONDS = 15

    def __init__(self, threshold_seconds: int = DEFAULT_THRESHOLD_SECONDS):
        """
        Initialize the data freshness validator.

        Args:
            threshold_seconds: Maximum acceptable age in seconds (default: 15)
        """
        self.threshold_seconds = threshold_seconds
        self.quotes: Dict[str, QuoteData] = {}
        self.validation_history: List[FreshnessSummary] = []
        self.last_validation_time: Optional[datetime] = None

    def add_quote(
        self,
        symbol: str,
        price: float,
        timestamp: datetime,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a quote to the validation pool.

        Args:
            symbol: Market symbol identifier
            price: Quote price value
            timestamp: Quote generation timestamp
            source: Data source identifier
            metadata: Optional additional metadata
        """
        quote = QuoteData(
            symbol=symbol,
            price=price,
            timestamp=timestamp,
            source=source,
            last_updated=datetime.now(),
            metadata=metadata or {},
        )
        self.quotes[symbol] = quote

    def remove_quote(self, symbol: str) -> bool:
        """
        Remove a quote from the validation pool.

        Args:
            symbol: Market symbol to remove

        Returns:
            True if quote was removed, False if not found
        """
        if symbol in self.quotes:
            del self.quotes[symbol]
            return True
        return False

    def check_age(
        self, symbol: str, reference_time: Optional[datetime] = None
    ) -> Tuple[float, FreshnessStatus]:
        """
        Check the age of a specific quote.

        Calculates elapsed time since quote generation and determines
        freshness status based on configured thresholds.

        Args:
            symbol: Market symbol to check
            reference_time: Optional reference time (default: now)

        Returns:
            Tuple of (age_seconds, freshness_status)

        Raises:
            KeyError: If symbol not found in quotes pool
        """
        if symbol not in self.quotes:
            raise KeyError(f"Quote not found for symbol: {symbol}")

        quote = self.quotes[symbol]
        reference = reference_time or datetime.now()
        age = (reference - quote.timestamp).total_seconds()

        if age > self.CRITICAL_THRESHOLD_SECONDS:
            status = FreshnessStatus.CRITICAL
        elif age > self.STALE_THRESHOLD_SECONDS:
            status = FreshnessStatus.STALE
        else:
            status = FreshnessStatus.FRESH

        return age, status

    def validate_all(
        self, reference_time: Optional[datetime] = None
    ) -> FreshnessSummary:
        """
        Validate all quotes in the pool against the freshness threshold.

        Performs comprehensive validation of all tracked quotes and generates
        detailed metrics including failure counts, age statistics, and overall
        system health status.

        Args:
            reference_time: Optional reference time for validation (default: now)

        Returns:
            FreshnessSummary object containing validation results and metrics
        """
        reference = reference_time or datetime.now()
        metrics_by_symbol: Dict[str, FreshnessMetric] = {}
        fresh_count = 0
        stale_count = 0
        critical_count = 0
        failed_symbols: List[str] = []
        ages: List[float] = []

        for symbol, quote in self.quotes.items():
            age = (reference - quote.timestamp).total_seconds()
            ages.append(age)

            # Determine freshness status
            if age > self.CRITICAL_THRESHOLD_SECONDS:
                status = FreshnessStatus.CRITICAL
                critical_count += 1
                failed_symbols.append(symbol)
                warning = f"Critical: {age:.2f}s old (threshold: {self.threshold_seconds}s)"
            elif age > self.STALE_THRESHOLD_SECONDS:
                status = FreshnessStatus.STALE
                stale_count += 1
                failed_symbols.append(symbol)
                warning = f"Stale: {age:.2f}s old (threshold: {self.threshold_seconds}s)"
            else:
                status = FreshnessStatus.FRESH
                fresh_count += 1
                warning = None

            is_valid = age <= self.threshold_seconds

            metric = FreshnessMetric(
                symbol=symbol,
                age_seconds=age,
                status=status,
                is_valid=is_valid,
                threshold_seconds=self.threshold_seconds,
                source=quote.source,
                timestamp=quote.timestamp,
                warning_message=warning,
            )
            metrics_by_symbol[symbol] = metric

        # Calculate aggregate metrics
        total_quotes = len(self.quotes)
        oldest_age = max(ages) if ages else 0.0
        newest_age = min(ages) if ages else 0.0
        average_age = sum(ages) / len(ages) if ages else 0.0

        # Determine overall status
        if critical_count > 0:
            overall_status = FreshnessStatus.CRITICAL
        elif stale_count > 0:
            overall_status = FreshnessStatus.STALE
        else:
            overall_status = FreshnessStatus.FRESH

        freshness_pct = (fresh_count / total_quotes * 100) if total_quotes > 0 else 0.0

        summary = FreshnessSummary(
            total_quotes=total_quotes,
            fresh_count=fresh_count,
            stale_count=stale_count,
            critical_count=critical_count,
            validation_timestamp=reference,
            overall_status=overall_status,
            freshness_percentage=freshness_pct,
            oldest_quote_age=oldest_age,
            newest_quote_age=newest_age,
            failed_symbols=failed_symbols,
            average_age=average_age,
            metrics_by_symbol=metrics_by_symbol,
        )

        self.validation_history.append(summary)
        self.last_validation_time = reference

        return summary

    def get_summary(self) -> Optional[FreshnessSummary]:
        """
        Get the most recent validation summary.

        Returns the last generated FreshnessSummary from validate_all(),
        or None if no validation has been performed yet.

        Returns:
            FreshnessSummary object or None if no validation yet
        """
        return self.validation_history[-1] if self.validation_history else None

    def get_detailed_report(self, summary: Optional[FreshnessSummary] = None) -> str:
        """
        Generate a detailed text report of validation results.

        Args:
            summary: FreshnessSummary to report (default: most recent)

        Returns:
            Formatted string report of validation results
        """
        if summary is None:
            summary = self.get_summary()
            if summary is None:
                return "No validation data available. Run validate_all() first."

        report_lines = [
            "=" * 70,
            "DATA FRESHNESS VALIDATION REPORT",
            "=" * 70,
            f"Validation Time: {summary.validation_timestamp.isoformat()}",
            f"Overall Status:  {summary.overall_status.value.upper()}",
            "",
            "SUMMARY STATISTICS",
            "-" * 70,
            f"Total Quotes:    {summary.total_quotes}",
            f"Fresh:           {summary.fresh_count} ({summary.freshness_percentage:.1f}%)",
            f"Stale:           {summary.stale_count}",
            f"Critical:        {summary.critical_count}",
            f"Average Age:     {summary.average_age:.2f}s",
            f"Oldest Quote:    {summary.oldest_quote_age:.2f}s",
            f"Newest Quote:    {summary.newest_quote_age:.2f}s",
            "",
        ]

        if summary.failed_symbols:
            report_lines.extend([
                "FAILED SYMBOLS",
                "-" * 70,
            ])
            for symbol in summary.failed_symbols:
                metric = summary.metrics_by_symbol.get(symbol)
                if metric:
                    report_lines.append(
                        f"  {symbol}: {metric.age_seconds:.2f}s "
                        f"({metric.status.value}) - {metric.source}"
                    )
            report_lines.append("")

        report_lines.extend([
            "=" * 70,
        ])

        return "\n".join(report_lines)

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a system health check based on data freshness.

        Returns:
            Dictionary containing health status and key metrics
        """
        summary = self.get_summary()
        if summary is None:
            return {
                "healthy": False,
                "reason": "No validation performed",
                "quote_count": 0,
            }

        is_healthy = (
            summary.overall_status == FreshnessStatus.FRESH
            and summary.freshness_percentage >= 95.0
        )

        return {
            "healthy": is_healthy,
            "status": summary.overall_status.value,
            "freshness_percentage": summary.freshness_percentage,
            "quote_count": summary.total_quotes,
            "failed_count": len(summary.failed_symbols),
            "average_age_seconds": summary.average_age,
            "last_validation": summary.validation_timestamp.isoformat(),
        }

    def clear_history(self) -> None:
        """Clear all quotes and validation history."""
        self.quotes.clear()
        self.validation_history.clear()
        self.last_validation_time = None

    def get_stale_symbols(self) -> List[str]:
        """
        Get list of symbols that are stale or critical.

        Returns:
            List of symbol identifiers exceeding freshness threshold
        """
        summary = self.get_summary()
        if summary is None:
            return []
        return summary.failed_symbols

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all validation metrics in JSON-serializable format.

        Returns:
            Dictionary containing complete validation state
        """
        summary = self.get_summary()
        if summary is None:
            return {"status": "no_validation_performed"}

        return {
            "timestamp": summary.validation_timestamp.isoformat(),
            "overall_status": summary.overall_status.value,
            "total_quotes": summary.total_quotes,
            "fresh_count": summary.fresh_count,
            "stale_count": summary.stale_count,
            "critical_count": summary.critical_count,
            "freshness_percentage": summary.freshness_percentage,
            "average_age_seconds": summary.average_age,
            "oldest_quote_seconds": summary.oldest_quote_age,
            "newest_quote_seconds": summary.newest_quote_age,
            "failed_symbols": summary.failed_symbols,
            "threshold_seconds": self.threshold_seconds,
        }

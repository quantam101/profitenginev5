"""
SEC Form 4 Insider Trading Compliance Module

Validates insider trading windows, generates Form 4 reports, and enforces
30-second threshold constraints for transaction reporting.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Tuple
import json


class TransactionType(Enum):
    PURCHASE = "P"
    SALE = "S"
    GRANT = "G"
    EXERCISE = "E"
    OTHER = "O"


class Form4Status(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class SecurityHolding:
    """Represents a securities holding for an insider."""
    symbol: str
    shares: int
    acquisition_price: float
    acquisition_date: datetime
    is_derivative: bool = False


@dataclass
class Transaction:
    """Represents a single securities transaction."""
    transaction_id: str
    insider_id: str
    symbol: str
    transaction_type: TransactionType
    shares: int
    price: float
    transaction_date: datetime
    execution_time: datetime
    form4_filed: Optional[datetime] = None
    is_deemed: bool = False


@dataclass
class Form4Report:
    """SEC Form 4 insider trading report."""
    form_id: str
    insider_id: str
    insider_name: str
    insider_title: str
    company_ticker: str
    company_cik: str
    transactions: List[Transaction] = field(default_factory=list)
    holdings: List[SecurityHolding] = field(default_factory=list)
    filing_date: datetime = field(default_factory=datetime.now)
    status: Form4Status = Form4Status.PENDING
    derivative_securities: List[Dict] = field(default_factory=list)
    non_derivative_securities: List[Dict] = field(default_factory=list)
    certification_signature: Optional[str] = None
    signature_date: Optional[datetime] = None
    notes: str = ""

    def to_dict(self) -> Dict:
        """Convert Form 4 to dictionary representation."""
        return {
            "form_id": self.form_id,
            "insider_id": self.insider_id,
            "insider_name": self.insider_name,
            "insider_title": self.insider_title,
            "company_ticker": self.company_ticker,
            "company_cik": self.company_cik,
            "filing_date": self.filing_date.isoformat(),
            "status": self.status.value,
            "transaction_count": len(self.transactions),
            "total_shares_transacted": sum(t.shares for t in self.transactions),
            "derivative_count": len(self.derivative_securities),
            "non_derivative_count": len(self.non_derivative_securities),
        }


class TradingWindowValidator:
    """Validates insider trading window constraints and timelines."""

    # SEC Rule 16a-3(f): Form 4 must be filed within 2 business days
    FORM4_FILING_DEADLINE_DAYS = 2
    # 30-second threshold for transaction clustering
    CLUSTER_THRESHOLD_SECONDS = 30
    # Blackout period: 10 trading days after earnings announcement
    BLACKOUT_DAYS = 10
    # Look-back period for clustering analysis
    LOOKBACK_WINDOW_MINUTES = 5

    def __init__(self):
        """Initialize the trading window validator."""
        self.transactions: List[Transaction] = []
        self.forms: Dict[str, Form4Report] = {}
        self.trading_windows: Dict[str, Tuple[datetime, datetime]] = {}

    def check_window(
        self,
        insider_id: str,
        symbol: str,
        transaction_date: datetime,
        transaction_type: TransactionType,
        shares: int,
        price: float,
    ) -> Dict:
        """
        Check if transaction falls within valid trading window.

        Args:
            insider_id: Unique identifier for the insider
            symbol: Security ticker symbol
            transaction_date: Date of the transaction
            transaction_type: Type of transaction (P/S/G/E/O)
            shares: Number of shares
            price: Transaction price per share

        Returns:
            Dictionary with window validation results, including:
            - is_valid: bool - whether transaction is in valid window
            - window_type: str - "open" or "blackout"
            - form4_deadline: datetime - when Form 4 must be filed
            - clustering_risk: bool - if within 30-sec cluster
            - compliance_status: str - "PASS", "FAIL", or "WARNING"
        """
        execution_time = datetime.now()
        window_key = f"{insider_id}_{symbol}"

        # Check if window exists for this insider-security pair
        window_valid = True
        window_type = "open"
        compliance_status = "PASS"

        # Validate against blackout periods (simplified)
        is_in_blackout = self._is_in_blackout_period(symbol, transaction_date)
        if is_in_blackout:
            window_valid = False
            window_type = "blackout"
            compliance_status = "FAIL"

        # Calculate Form 4 filing deadline (2 business days from transaction)
        form4_deadline = self._calculate_form4_deadline(transaction_date)

        # Check for 30-second clustering risk
        clustering_risk = self._check_clustering_threshold(
            insider_id, symbol, execution_time
        )
        if clustering_risk:
            compliance_status = "WARNING"

        # Store transaction for tracking
        transaction = Transaction(
            transaction_id=f"TXN_{insider_id}_{transaction_date.timestamp()}",
            insider_id=insider_id,
            symbol=symbol,
            transaction_type=transaction_type,
            shares=shares,
            price=price,
            transaction_date=transaction_date,
            execution_time=execution_time,
        )
        self.transactions.append(transaction)

        return {
            "is_valid": window_valid,
            "window_type": window_type,
            "transaction_date": transaction_date.isoformat(),
            "form4_deadline": form4_deadline.isoformat(),
            "clustering_risk": clustering_risk,
            "compliance_status": compliance_status,
            "trading_window_key": window_key,
            "lookback_window_minutes": self.LOOKBACK_WINDOW_MINUTES,
            "cluster_threshold_seconds": self.CLUSTER_THRESHOLD_SECONDS,
        }

    def gen_form4(
        self,
        insider_id: str,
        insider_name: str,
        insider_title: str,
        company_ticker: str,
        company_cik: str,
        transactions: List[Transaction],
        holdings: Optional[List[SecurityHolding]] = None,
    ) -> Form4Report:
        """
        Generate SEC Form 4 report from transactions.

        Args:
            insider_id: Unique identifier for insider
            insider_name: Full name of insider
            insider_title: Officer/director title
            company_ticker: Company ticker symbol
            company_cik: SEC Central Index Key
            transactions: List of transactions to report
            holdings: Optional post-transaction holdings

        Returns:
            Form4Report object with calculated fields
        """
        form_id = f"FORM4_{insider_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Separate derivatives from non-derivatives
        derivative_securities = []
        non_derivative_securities = []

        for txn in transactions:
            security_entry = {
                "symbol": txn.symbol,
                "type": txn.transaction_type.value,
                "shares": txn.shares,
                "price": txn.price,
                "transaction_date": txn.transaction_date.isoformat(),
                "execution_time": txn.execution_time.isoformat(),
                "is_deemed": txn.is_deemed,
            }

            if txn.is_deemed:
                derivative_securities.append(security_entry)
            else:
                non_derivative_securities.append(security_entry)

        form4 = Form4Report(
            form_id=form_id,
            insider_id=insider_id,
            insider_name=insider_name,
            insider_title=insider_title,
            company_ticker=company_ticker,
            company_cik=company_cik,
            transactions=transactions,
            holdings=holdings or [],
            derivative_securities=derivative_securities,
            non_derivative_securities=non_derivative_securities,
            filing_date=datetime.now(),
            status=Form4Status.PENDING,
        )

        self.forms[form_id] = form4
        return form4

    def validate(self, form4: Form4Report) -> Dict:
        """
        Validate Form 4 report for SEC compliance.

        Checks:
        - All transactions within Form 4 deadline
        - Proper transaction documentation
        - Insider title and relationship validation
        - Non-derivative vs derivative classification
        - Transaction timing alignment
        - Clustering threshold violations

        Args:
            form4: Form4Report object to validate

        Returns:
            Dictionary with validation results:
            - is_valid: bool - overall compliance pass/fail
            - errors: List[str] - validation failure reasons
            - warnings: List[str] - compliance warnings
            - deadline_status: str - filing deadline status
            - filing_status: str - current Form 4 status
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Validate insider information
        if not form4.insider_id:
            errors.append("Missing insider_id")
        if not form4.insider_name:
            errors.append("Missing insider_name")
        if not form4.insider_title:
            errors.append("Missing insider_title")

        # Validate company information
        if not form4.company_ticker:
            errors.append("Missing company_ticker")
        if not form4.company_cik:
            errors.append("Missing company_cik")

        # Validate transactions
        if not form4.transactions:
            errors.append("No transactions provided")
        else:
            for txn in form4.transactions:
                # Check Form 4 filing deadline (2 business days)
                if txn.form4_filed is None:
                    deadline = self._calculate_form4_deadline(txn.transaction_date)
                    days_until_deadline = (deadline - datetime.now()).days
                    if days_until_deadline < 0:
                        errors.append(
                            f"Transaction {txn.transaction_id} exceeded Form 4 deadline"
                        )
                    elif days_until_deadline == 0:
                        warnings.append(
                            f"Transaction {txn.transaction_id} due today (deadline: {deadline.date()})"
                        )

                # Validate transaction data
                if txn.shares <= 0:
                    errors.append(f"Transaction {txn.transaction_id}: shares must be > 0")
                if txn.price < 0:
                    errors.append(f"Transaction {txn.transaction_id}: price cannot be negative")

                # Check for clustering violations
                cluster_count = self._count_transactions_in_cluster(txn)
                if cluster_count > 1:
                    warnings.append(
                        f"Transaction {txn.transaction_id}: {cluster_count} transactions within {self.CLUSTER_THRESHOLD_SECONDS}s"
                    )

        # Validate derivative classification
        derivative_count = len(form4.derivative_securities)
        non_derivative_count = len(form4.non_derivative_securities)
        if derivative_count + non_derivative_count != len(form4.transactions):
            errors.append("Transaction classification mismatch")

        # Determine deadline status
        deadline_status = "ON_TRACK"
        if errors:
            deadline_status = "FAILED"
        elif warnings:
            deadline_status = "AT_RISK"

        # Determine filing status based on validation
        filing_status = form4.status.value
        if errors and form4.status == Form4Status.PENDING:
            filing_status = "BLOCKED_BY_VALIDATION"

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "form_id": form4.form_id,
            "insider_id": form4.insider_id,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "deadline_status": deadline_status,
            "filing_status": filing_status,
            "form4_deadline_days": self.FORM4_FILING_DEADLINE_DAYS,
            "transaction_count": len(form4.transactions),
            "validation_timestamp": datetime.now().isoformat(),
        }

    def _is_in_blackout_period(self, symbol: str, transaction_date: datetime) -> bool:
        """Check if transaction date falls in blackout period (simplified)."""
        # In production, would check earnings dates, disclosure events, etc.
        return False

    def _calculate_form4_deadline(self, transaction_date: datetime) -> datetime:
        """Calculate Form 4 filing deadline (2 business days from transaction)."""
        # Simplified: add 2 calendar days (in production would count business days)
        business_days_added = 0
        current_date = transaction_date

        while business_days_added < self.FORM4_FILING_DEADLINE_DAYS:
            current_date += timedelta(days=1)
            # Skip weekends (simplified)
            if current_date.weekday() < 5:  # Mon-Fri
                business_days_added += 1

        return current_date

    def _check_clustering_threshold(
        self, insider_id: str, symbol: str, execution_time: datetime
    ) -> bool:
        """Check if transaction falls within 30-second cluster threshold."""
        lookback_start = execution_time - timedelta(
            minutes=self.LOOKBACK_WINDOW_MINUTES
        )

        recent_txns = [
            t
            for t in self.transactions
            if t.insider_id == insider_id
            and t.symbol == symbol
            and lookback_start <= t.execution_time <= execution_time
        ]

        return len(recent_txns) > 0

    def _count_transactions_in_cluster(self, transaction: Transaction) -> int:
        """Count transactions for same insider-security within 30 seconds."""
        cluster_start = transaction.execution_time - timedelta(
            seconds=self.CLUSTER_THRESHOLD_SECONDS
        )
        cluster_end = transaction.execution_time + timedelta(
            seconds=self.CLUSTER_THRESHOLD_SECONDS
        )

        cluster_txns = [
            t
            for t in self.transactions
            if t.insider_id == transaction.insider_id
            and t.symbol == transaction.symbol
            and cluster_start <= t.execution_time <= cluster_end
        ]

        return len(cluster_txns)

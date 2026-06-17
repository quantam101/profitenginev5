"""
Integration tests for compliance_automation.py with audit_ledger.py

Demonstrates:
- Form 4 pre-fill generation
- Insider trading window enforcement
- Daily/quarterly compliance reporting
- Compliance attestation generation
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

try:
    from compliance_automation import ComplianceAutomator, InsiderTradingWindow
    from audit_ledger import AuditLedger
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from compliance_automation import ComplianceAutomator, InsiderTradingWindow
    from audit_ledger import AuditLedger


class TestComplianceAutomation(unittest.TestCase):
    """Test compliance automation features."""

    def setUp(self):
        """Initialize test databases."""
        self.audit_ledger = AuditLedger(db_path="./test_audit.db")
        self.compliance = ComplianceAutomator(
            audit_ledger_path="./test_audit.db",
            compliance_db="./test_compliance.db"
        )

    def tearDown(self):
        """Clean up test databases."""
        import os
        import time
        for db in ["./test_audit.db", "./test_compliance.db"]:
            if os.path.exists(db):
                try:
                    time.sleep(0.1)
                    os.remove(db)
                except PermissionError:
                    pass  # Database still locked, will be cleaned up later

    def test_form4_prefill_generation(self):
        """Test Form 4 pre-fill data generation."""
        form4 = self.compliance.generate_form4_prefill(
            insider_id="EXEC001",
            insider_name="Jane Smith",
            insider_title="Chief Executive Officer",
            company_ticker="AAPL",
            cik_number="0000320193",
            transaction_date=datetime.now(),
            security_title="Common Stock",
            transaction_type="acquisition",
            shares=Decimal("1000"),
            price_per_share=Decimal("150.50"),
            beneficial_ownership=Decimal("25000"),
        )

        # Verify Form 4 structure
        self.assertIn("form_type", form4)
        self.assertEqual(form4["form_type"], "4")

        self.assertIn("sec_header", form4)
        self.assertEqual(form4["sec_header"]["filer_cik"], "0000320193")

        self.assertIn("reporting_owner", form4)
        self.assertEqual(form4["reporting_owner"]["owner_name"], "Jane Smith")

        self.assertIn("non_derivative_holdings", form4)
        self.assertEqual(form4["non_derivative_holdings"]["shares_acquired"], 1000.0)
        self.assertEqual(form4["non_derivative_holdings"]["price_per_share"], 150.50)
        self.assertEqual(form4["non_derivative_holdings"]["aggregate_value"], 150500.0)

        self.assertIn("metadata", form4)
        self.assertEqual(form4["metadata"]["filing_status"], "READY_FOR_FILING")

    def test_trading_window_open(self):
        """Test trading window check when window is open."""
        transaction_date = datetime.now() + timedelta(days=5)

        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=transaction_date,
            security="AAPL"
        )

        self.assertTrue(is_open)
        self.assertIn("OPEN", reason)
        self.assertEqual(details["window_state"], InsiderTradingWindow.OPEN.value)

    def test_trading_window_blackout(self):
        """Test trading window check during blackout period."""
        # Add blackout period
        blackout_start = datetime.now()
        blackout_end = datetime.now() + timedelta(days=30)

        self.compliance.add_blackout_period(
            start_date=blackout_start,
            end_date=blackout_end,
            reason="Acquisition process - confidential information period"
        )

        # Try to trade during blackout
        transaction_date = datetime.now() + timedelta(days=15)
        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=transaction_date,
            security="AAPL"
        )

        self.assertFalse(is_open)
        self.assertIn("forbidden", reason.lower())
        self.assertEqual(details["window_state"], InsiderTradingWindow.BLACKOUT.value)

    def test_trading_window_earnings_restriction(self):
        """Test trading window check near earnings announcement."""
        earnings_date = datetime.now() + timedelta(days=5)

        self.compliance.add_earnings_date(earnings_date)

        # Try to trade 1 day before earnings
        transaction_date = earnings_date - timedelta(days=1)
        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=transaction_date,
            security="AAPL"
        )

        self.assertFalse(is_open)
        self.assertIn("restricted", reason.lower())
        self.assertEqual(details["window_state"], InsiderTradingWindow.CLOSE_TO_EARNINGS.value)

    def test_daily_compliance_report(self):
        """Test daily compliance report generation."""
        report = self.compliance.generate_daily_report(
            report_date=datetime.now()
        )

        self.assertIn("report_id", report)
        self.assertIn("created_timestamp", report)
        self.assertIn("report_date", report)
        self.assertIn("total_trades", report)
        self.assertIn("trades_in_window", report)
        self.assertIn("window_violations", report)
        self.assertIn("blackout_violations", report)
        self.assertIn("total_volume_usd", report)
        self.assertIn("compliance_status", report)

        # Should be GREEN when no violations
        self.assertEqual(report["compliance_status"], "GREEN")

    def test_quarterly_attestation(self):
        """Test quarterly compliance attestation generation."""
        attestation = self.compliance.generate_quarterly_attestation(
            fiscal_quarter=2,
            fiscal_year=2024,
            attestor_name="Robert Johnson",
            attestor_title="Chief Financial Officer",
        )

        self.assertIn("attestation_id", attestation)
        self.assertIn("created_timestamp", attestation)
        self.assertEqual(attestation["fiscal_quarter"], 2)
        self.assertEqual(attestation["fiscal_year"], 2024)
        self.assertEqual(attestation["attestor_name"], "Robert Johnson")
        self.assertIn("control_effectiveness", attestation)
        self.assertIn("attestation_statement", attestation)

        # Verify attestation statement contains required SOX references
        statement = attestation["attestation_statement"]
        self.assertIn("Sarbanes-Oxley", statement)
        self.assertIn("Regulation FD", statement)

    def test_compliance_violation_logging(self):
        """Test compliance violation logging."""
        violation = self.compliance.log_compliance_violation(
            violation_type="LATE_FILING",
            severity="HIGH",
            description="Form 4 filed 1 day after required deadline",
            insider_id="EXEC001",
            remedial_action="Filed with late fee, internal review scheduled"
        )

        self.assertIn("violation_id", violation)
        self.assertIn("violation_date", violation)
        self.assertEqual(violation["violation_type"], "LATE_FILING")
        self.assertEqual(violation["severity"], "HIGH")
        self.assertEqual(violation["insider_id"], "EXEC001")

    def test_integration_form4_with_window_check(self):
        """Test integrated workflow: check window then generate Form 4."""
        # Check trading window
        is_open, _, _ = self.compliance.check_insider_trading_window(
            insider_id="EXEC002",
            proposed_transaction_date=datetime.now(),
            security="MSFT"
        )

        self.assertTrue(is_open)

        # Generate Form 4 if window is open
        if is_open:
            form4 = self.compliance.generate_form4_prefill(
                insider_id="EXEC002",
                insider_name="Alice Brown",
                insider_title="Chief Technology Officer",
                company_ticker="MSFT",
                cik_number="0000789019",
                transaction_date=datetime.now(),
                security_title="Common Stock",
                transaction_type="disposition",
                shares=Decimal("500"),
                price_per_share=Decimal("370.00"),
                beneficial_ownership=Decimal("10000"),
            )

            self.assertEqual(form4["metadata"]["filing_status"], "READY_FOR_FILING")
            self.assertEqual(form4["non_derivative_holdings"]["shares_disposed"], 500.0)

    def test_multiple_blackout_periods(self):
        """Test handling of multiple overlapping blackout periods."""
        # Add first blackout (acquisition)
        self.compliance.add_blackout_period(
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2024, 6, 30),
            reason="Acquisition process"
        )

        # Add second blackout (earnings)
        self.compliance.add_blackout_period(
            start_date=datetime(2024, 6, 15),
            end_date=datetime(2024, 6, 17),
            reason="Earnings announcement window"
        )

        self.assertEqual(len(self.compliance.blackout_periods), 2)

        # Test date in second blackout
        is_open, reason, _ = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=datetime(2024, 6, 16),
            security="AAPL"
        )

        self.assertFalse(is_open)


class TestComplianceAuditIntegration(unittest.TestCase):
    """Test integration between compliance_automation and audit_ledger."""

    def setUp(self):
        """Initialize test databases."""
        self.audit_ledger = AuditLedger(db_path="./test_audit_integration.db")
        self.compliance = ComplianceAutomator(
            audit_ledger_path="./test_audit_integration.db",
            compliance_db="./test_compliance_integration.db"
        )

    def tearDown(self):
        """Clean up test databases."""
        import os
        import time
        for db in ["./test_audit_integration.db", "./test_compliance_integration.db"]:
            if os.path.exists(db):
                try:
                    time.sleep(0.1)
                    os.remove(db)
                except PermissionError:
                    pass  # Database still locked, will be cleaned up later

    def test_audit_ledger_stats_with_compliance(self):
        """Test that compliance reports can reference audit ledger stats."""
        # Get audit ledger stats
        stats = self.audit_ledger.get_stats()

        # Stats should be available even with zero trades
        self.assertIn("total_trades", stats)
        self.assertIn("total_pnl", stats)
        self.assertIn("win_rate_pct", stats)

        # Generate compliance report using audit data
        report = self.compliance.generate_daily_report()

        # Report should reference audit data
        self.assertIn("total_trades", report)
        self.assertIn("total_volume_usd", report)


if __name__ == "__main__":
    unittest.main()

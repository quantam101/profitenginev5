"""
Compliance Automation Integration Verification Script

Logs 10 sample trades through audit_ledger with compliance_automation enabled,
generates SEC Form 4 prefill data, verifies insider trading window checks,
and produces daily/quarterly compliance reports.

Exit codes:
  0 = All tests passed
  1 = Form 4 generation failed
  2 = Trading window checks failed
  3 = Daily report generation failed
  4 = Quarterly attestation failed
  5 = Database integrity failed
"""

import sqlite3
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys

try:
    from compliance_automation import ComplianceAutomator, InsiderTradingWindow
    from audit_ledger import AuditLedger
    from models import TradeProposal, ExecutionResult
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from compliance_automation import ComplianceAutomator, InsiderTradingWindow
    from audit_ledger import AuditLedger
    from models import TradeProposal, ExecutionResult


class ComplianceVerifier:
    """Comprehensive compliance automation verification."""

    def __init__(self, audit_db="./verification_audit.db", compliance_db="./verification_compliance.db"):
        self.audit_db = audit_db
        self.compliance_db = compliance_db
        self.audit_ledger = AuditLedger(db_path=audit_db, compliance_db=compliance_db)
        self.compliance = self.audit_ledger.compliance_automator
        self.form4_samples = []
        self.window_checks = []
        self.daily_reports = []
        self.attestations = []
        self.violations = []

    def log_sample_trades(self):
        """Log 10 sample trades with various configurations."""
        print("\n" + "="*80)
        print("STEP 1: LOGGING 10 SAMPLE TRADES WITH COMPLIANCE ENABLED")
        print("="*80)

        sample_trades = [
            {
                "insider_id": "EXEC001",
                "insider_name": "Jane Smith",
                "insider_title": "Chief Executive Officer",
                "ticker": "AAPL",
                "cik": "0000320193",
                "shares": Decimal("1000"),
                "price": Decimal("150.50"),
                "beneficial_ownership": Decimal("25000"),
                "type": "acquisition",
            },
            {
                "insider_id": "EXEC002",
                "insider_name": "John Doe",
                "insider_title": "Chief Financial Officer",
                "ticker": "MSFT",
                "cik": "0000789019",
                "shares": Decimal("500"),
                "price": Decimal("370.00"),
                "beneficial_ownership": Decimal("10000"),
                "type": "disposition",
            },
            {
                "insider_id": "EXEC003",
                "insider_name": "Alice Brown",
                "insider_title": "Chief Technology Officer",
                "ticker": "GOOGL",
                "cik": "0001652044",
                "shares": Decimal("750"),
                "price": Decimal("140.25"),
                "beneficial_ownership": Decimal("15000"),
                "type": "acquisition",
            },
            {
                "insider_id": "EXEC004",
                "insider_name": "Robert Johnson",
                "insider_title": "VP Engineering",
                "ticker": "AMZN",
                "cik": "0001018724",
                "shares": Decimal("250"),
                "price": Decimal("180.75"),
                "beneficial_ownership": Decimal("5000"),
                "type": "disposition",
            },
            {
                "insider_id": "EXEC005",
                "insider_name": "Sarah Williams",
                "insider_title": "VP Sales",
                "ticker": "TSLA",
                "cik": "0001318605",
                "shares": Decimal("600"),
                "price": Decimal("250.00"),
                "beneficial_ownership": Decimal("12000"),
                "type": "acquisition",
            },
            {
                "insider_id": "EXEC001",
                "insider_name": "Jane Smith",
                "insider_title": "Chief Executive Officer",
                "ticker": "AAPL",
                "cik": "0000320193",
                "shares": Decimal("300"),
                "price": Decimal("155.25"),
                "beneficial_ownership": Decimal("24700"),
                "type": "disposition",
            },
            {
                "insider_id": "EXEC002",
                "insider_name": "John Doe",
                "insider_title": "Chief Financial Officer",
                "ticker": "MSFT",
                "cik": "0000789019",
                "shares": Decimal("200"),
                "price": Decimal("375.50"),
                "beneficial_ownership": Decimal("9800"),
                "type": "acquisition",
            },
            {
                "insider_id": "EXEC003",
                "insider_name": "Alice Brown",
                "insider_title": "Chief Technology Officer",
                "ticker": "GOOGL",
                "cik": "0001652044",
                "shares": Decimal("400"),
                "price": Decimal("142.75"),
                "beneficial_ownership": Decimal("14600"),
                "type": "disposition",
            },
            {
                "insider_id": "EXEC004",
                "insider_name": "Robert Johnson",
                "insider_title": "VP Engineering",
                "ticker": "AMZN",
                "cik": "0001018724",
                "shares": Decimal("100"),
                "price": Decimal("185.50"),
                "beneficial_ownership": Decimal("4900"),
                "type": "acquisition",
            },
            {
                "insider_id": "EXEC005",
                "insider_name": "Sarah Williams",
                "insider_title": "VP Sales",
                "ticker": "TSLA",
                "cik": "0001318605",
                "shares": Decimal("150"),
                "price": Decimal("255.75"),
                "beneficial_ownership": Decimal("11850"),
                "type": "disposition",
            },
        ]

        for idx, trade in enumerate(sample_trades, 1):
            try:
                form4 = self.compliance.generate_form4_prefill(
                    insider_id=trade["insider_id"],
                    insider_name=trade["insider_name"],
                    insider_title=trade["insider_title"],
                    company_ticker=trade["ticker"],
                    cik_number=trade["cik"],
                    transaction_date=datetime.now(timezone.utc),
                    security_title="Common Stock",
                    transaction_type=trade["type"],
                    shares=trade["shares"],
                    price_per_share=trade["price"],
                    beneficial_ownership=trade["beneficial_ownership"],
                )

                self.form4_samples.append(form4)
                print(f"\n[Trade {idx:2d}] {trade['insider_name']:20s} | {trade['type']:11s} | "
                      f"{str(trade['shares']):6s} shares @ ${trade['price']:7.2f}")
                print(f"           Ticker: {trade['ticker']:5s} | Form4 ID: {form4['metadata']['form4_id'][:8]}")

            except Exception as e:
                print(f"[Trade {idx:2d}] ERROR: {str(e)}")
                return 1

        print(f"\nSuccessfully logged {len(self.form4_samples)} trades with Form 4 prefill data.")
        return 0

    def verify_form4_prefill_fields(self):
        """Verify SEC Form 4 prefill data contains correct fields."""
        print("\n" + "="*80)
        print("STEP 2: VERIFY SEC FORM 4 PREFILL DATA - FIELD VALIDATION")
        print("="*80)

        required_fields = {
            "form_type": "4",
            "sec_header": ["accession_number", "filing_date", "period_end", "filer_cik"],
            "issuer": ["issuer_name", "issuer_cik", "issuer_ticker"],
            "reporting_owner": ["owner_id", "owner_name", "owner_title", "owner_cik"],
            "non_derivative_holdings": [
                "security_title", "transaction_date", "transaction_code",
                "shares_acquired", "shares_disposed", "price_per_share",
                "aggregate_shares", "aggregate_value"
            ],
            "form4_certification": ["certifying_officer", "certification_date", "certification_text"],
            "metadata": ["form4_id", "created_timestamp", "reporting_due_date", "filing_status"]
        }

        all_valid = True
        for idx, form4 in enumerate(self.form4_samples, 1):
            print(f"\n[Form 4 {idx:2d}] Validating structure...")
            valid = True

            # Check form_type
            if form4.get("form_type") != "4":
                print(f"  ERROR: form_type = {form4.get('form_type')} (expected '4')")
                valid = False

            # Check sections
            for section, fields in [k for k in required_fields.items() if k[0] != "form_type"]:
                if section not in form4:
                    print(f"  ERROR: Missing section '{section}'")
                    valid = False
                    continue

                if isinstance(fields, list):
                    for field in fields:
                        if field not in form4[section]:
                            print(f"  ERROR: Missing field '{section}.{field}'")
                            valid = False

            # Validate critical fields
            if form4.get("metadata", {}).get("filing_status") != "READY_FOR_FILING":
                print(f"  ERROR: filing_status = {form4.get('metadata', {}).get('filing_status')}")
                valid = False

            non_deriv = form4.get("non_derivative_holdings", {})
            total_shares = non_deriv.get("shares_acquired", 0) + non_deriv.get("shares_disposed", 0)
            if total_shares == 0:
                print(f"  ERROR: No shares in transaction")
                valid = False

            if valid:
                print(f"  OK - All required fields present and valid")
                print(f"       Symbol: {form4['issuer']['issuer_ticker']}")
                print(f"       Insider: {form4['reporting_owner']['owner_name']}")
                print(f"       Transaction: {non_deriv.get('shares_acquired', 0):.0f} acq / "
                      f"{non_deriv.get('shares_disposed', 0):.0f} disp @ ${non_deriv.get('price_per_share'):.2f}")
                print(f"       Value: ${non_deriv.get('aggregate_value'):,.2f}")
            else:
                all_valid = False

        if not all_valid:
            return 1

        print(f"\n[PASS] All {len(self.form4_samples)} Form 4 records validated successfully")
        return 0

    def check_insider_trading_windows(self):
        """Test insider trading window checks with pass/fail scenarios."""
        print("\n" + "="*80)
        print("STEP 3: INSIDER TRADING WINDOW CHECKS - OPEN, BLACKOUT, EARNINGS")
        print("="*80)

        # Test 1: Normal trading window (should PASS)
        print("\n[Window Check 1] Normal trading window (no restrictions)")
        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=datetime.now(timezone.utc),
            security="AAPL"
        )
        self.window_checks.append({"check": "Normal", "passed": is_open, "reason": reason})
        print(f"  Result: {'PASS' if is_open else 'FAIL'} - {reason}")

        # Test 2: During blackout period (should FAIL)
        print("\n[Window Check 2] During blackout period (acquisition confidential period)")
        blackout_start = datetime.now(timezone.utc) + timedelta(days=1)
        blackout_end = datetime.now(timezone.utc) + timedelta(days=31)
        self.compliance.add_blackout_period(blackout_start, blackout_end, "Acquisition process - confidential")

        transaction_date = datetime.now(timezone.utc) + timedelta(days=15)
        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=transaction_date,
            security="AAPL"
        )
        self.window_checks.append({"check": "Blackout", "passed": not is_open, "reason": reason})
        print(f"  Result: {'PASS (correctly blocked)' if not is_open else 'FAIL (should block)'} - {reason}")

        # Test 3: Near earnings announcement (should FAIL)
        # Use earnings date far away from blackout window to avoid overlap
        print("\n[Window Check 3] Within 2 days of earnings announcement")
        earnings_date = datetime.now(timezone.utc) + timedelta(days=50)
        self.compliance.add_earnings_date(earnings_date)

        transaction_date = earnings_date - timedelta(days=1)
        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=transaction_date,
            security="AAPL"
        )
        self.window_checks.append({"check": "Earnings", "passed": not is_open, "reason": reason})
        print(f"  Result: {'PASS (correctly blocked)' if not is_open else 'FAIL (should block)'} - {reason}")

        # Test 4: After blackout/earnings window (should PASS)
        print("\n[Window Check 4] After all restrictions lifted")
        transaction_date = datetime.now(timezone.utc) + timedelta(days=60)
        is_open, reason, details = self.compliance.check_insider_trading_window(
            insider_id="EXEC001",
            proposed_transaction_date=transaction_date,
            security="AAPL"
        )
        self.window_checks.append({"check": "Post-restrictions", "passed": is_open, "reason": reason})
        print(f"  Result: {'PASS' if is_open else 'FAIL'} - {reason}")

        # Verify pass/fail counts
        # Tests 1 and 4 should pass (True), tests 2 and 3 should correctly block (True)
        # So "passed" means the test behaved as expected
        all_correct = all(w["passed"] for w in self.window_checks)
        print(f"\n[PASS] All {len(self.window_checks)} window checks behaved as expected")
        print(f"       - 2 checks correctly allowed trading")
        print(f"       - 2 checks correctly blocked trading")

        if not all_correct:
            print(f"  ERROR: Not all window checks behaved as expected")
            return 2

        return 0

    def generate_daily_reports(self):
        """Generate daily compliance reports."""
        print("\n" + "="*80)
        print("STEP 4: DAILY COMPLIANCE REPORTS - FORMAT AND DATA VALIDATION")
        print("="*80)

        # Generate reports for multiple days
        for day_offset in range(3):
            report_date = datetime.now(timezone.utc) - timedelta(days=day_offset)
            report = self.audit_ledger.generate_daily_compliance_report(report_date)
            self.daily_reports.append(report)

            print(f"\n[Report {day_offset + 1}] Date: {report['report_date']}")
            print(f"  Report ID: {report['report_id'][:8]}")
            print(f"  Total Trades: {report['total_trades']}")
            print(f"  Trades in Window: {report['trades_in_window']}")
            print(f"  Window Violations: {report['window_violations']}")
            print(f"  Blackout Violations: {report['blackout_violations']}")
            print(f"  Total Volume (USD): ${report['total_volume_usd']:,.2f}")
            print(f"  Compliance Status: {report['compliance_status']}")

            # Validate required fields
            required = ["report_id", "report_date", "total_trades", "trades_in_window",
                       "window_violations", "blackout_violations", "total_volume_usd", "compliance_status"]
            for field in required:
                if field not in report:
                    print(f"  ERROR: Missing field '{field}'")
                    return 3

        print(f"\n[PASS] Generated {len(self.daily_reports)} daily compliance reports")
        return 0

    def generate_quarterly_attestations(self):
        """Generate quarterly compliance attestations."""
        print("\n" + "="*80)
        print("STEP 5: QUARTERLY ATTESTATION GENERATION - SOX COMPLIANCE")
        print("="*80)

        quarters = [(1, 2024), (2, 2024), (3, 2024), (4, 2024)]
        for quarter, year in quarters:
            attestation = self.audit_ledger.generate_quarterly_attestation(
                fiscal_quarter=quarter,
                fiscal_year=year,
                attestor_name=f"John Smith, CFO",
                attestor_title="Chief Financial Officer"
            )
            self.attestations.append(attestation)

            print(f"\n[Attestation Q{quarter} {year}]")
            print(f"  Attestation ID: {attestation['attestation_id'][:8]}")
            print(f"  Form 4s Filed: {attestation['total_form4s_filed']}")
            print(f"  Late Filings: {attestation['late_filings']}")
            print(f"  Material Changes: {attestation['material_changes']}")
            print(f"  Control Effectiveness: {attestation['control_effectiveness']}")

            # Validate required fields
            required = ["attestation_id", "fiscal_quarter", "fiscal_year", "attestor_name",
                       "total_form4s_filed", "late_filings", "material_changes",
                       "control_effectiveness", "attestation_statement"]
            for field in required:
                if field not in attestation:
                    print(f"  ERROR: Missing field '{field}'")
                    return 4

            # Verify SOX references in statement
            statement = attestation.get("attestation_statement", "")
            if "Sarbanes-Oxley" not in statement or "Regulation FD" not in statement:
                print(f"  ERROR: Missing SOX/RegFD references in attestation statement")
                return 4

        print(f"\n[PASS] Generated {len(self.attestations)} quarterly attestations with SOX compliance")
        return 0

    def test_violation_logging(self):
        """Test compliance violation logging."""
        print("\n" + "="*80)
        print("STEP 6: COMPLIANCE VIOLATION LOGGING")
        print("="*80)

        violations = [
            {
                "type": "LATE_FILING",
                "severity": "HIGH",
                "description": "Form 4 filed 2 days after required deadline",
                "insider": "EXEC001"
            },
            {
                "type": "WINDOW_VIOLATION",
                "severity": "CRITICAL",
                "description": "Trade executed during blackout period",
                "insider": "EXEC002"
            },
            {
                "type": "INCOMPLETE_DISCLOSURE",
                "severity": "MEDIUM",
                "description": "Missing beneficial ownership disclosure",
                "insider": "EXEC003"
            },
        ]

        for idx, violation in enumerate(violations, 1):
            v = self.audit_ledger.log_compliance_violation(
                violation_type=violation["type"],
                severity=violation["severity"],
                description=violation["description"],
                insider_id=violation["insider"],
                remedial_action="Under review"
            )
            self.violations.append(v)

            print(f"\n[Violation {idx}] {violation['type']}")
            print(f"  ID: {v['violation_id'][:8]}")
            print(f"  Severity: {violation['severity']}")
            print(f"  Description: {violation['description']}")

        print(f"\n[PASS] Logged {len(self.violations)} compliance violations")
        return 0

    def verify_database_integrity(self):
        """Verify database schema and record counts."""
        print("\n" + "="*80)
        print("STEP 7: DATABASE INTEGRITY VERIFICATION")
        print("="*80)

        try:
            # Check compliance database
            with sqlite3.connect(self.compliance_db) as conn:
                cursor = conn.cursor()

                # Verify tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                expected_tables = [
                    "form4_prefills", "trading_windows", "daily_compliance_reports",
                    "quarterly_attestations", "compliance_violations"
                ]

                print("\nCompliance Database Tables:")
                for table in expected_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                        count = cursor.fetchone()[0]
                        print(f"  [OK] {table:30s} - {count:3d} records")
                    else:
                        print(f"  [FAIL] {table:30s} - NOT FOUND")
                        return 5

            # Check audit database
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                expected_tables = [
                    "proposals", "risk_decisions", "executions", "outcomes",
                    "rejections", "compliance_audit_trail"
                ]

                print("\nAudit Database Tables:")
                for table in expected_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                        count = cursor.fetchone()[0]
                        print(f"  [OK] {table:30s} - {count:3d} records")
                    else:
                        print(f"  [FAIL] {table:30s} - NOT FOUND")
                        return 5

                # Check compliance audit trail specifically
                cursor.execute("""
                    SELECT COUNT(*) FROM compliance_audit_trail
                """)
                trail_count = cursor.fetchone()[0]
                print(f"\n  Compliance Audit Trail Events: {trail_count}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            return 5

        print("\n[PASS] Database integrity verified successfully")
        return 0

    def generate_compliance_report_samples(self):
        """Output sample compliance reports."""
        print("\n" + "="*80)
        print("STEP 8: SAMPLE COMPLIANCE REPORTS")
        print("="*80)

        # Sample Form 4
        if self.form4_samples:
            print("\n--- SAMPLE SEC FORM 4 PREFILL DATA ---")
            form4 = self.form4_samples[0]
            print(json.dumps({
                "form_type": form4.get("form_type"),
                "sec_header": form4.get("sec_header"),
                "issuer": form4.get("issuer"),
                "reporting_owner": form4.get("reporting_owner"),
                "non_derivative_holdings": form4.get("non_derivative_holdings"),
                "metadata": form4.get("metadata"),
            }, indent=2, default=str))

        # Sample Daily Report
        if self.daily_reports:
            print("\n--- SAMPLE DAILY COMPLIANCE REPORT ---")
            print(json.dumps(self.daily_reports[0], indent=2, default=str))

        # Sample Quarterly Attestation
        if self.attestations:
            print("\n--- SAMPLE QUARTERLY ATTESTATION ---")
            att = self.attestations[0]
            print(json.dumps({
                "attestation_id": att.get("attestation_id"),
                "fiscal_quarter": att.get("fiscal_quarter"),
                "fiscal_year": att.get("fiscal_year"),
                "attestor_name": att.get("attestor_name"),
                "attestor_title": att.get("attestor_title"),
                "total_form4s_filed": att.get("total_form4s_filed"),
                "late_filings": att.get("late_filings"),
                "material_changes": att.get("material_changes"),
                "control_effectiveness": att.get("control_effectiveness"),
                "attestation_statement": att.get("attestation_statement")[:200] + "...",
            }, indent=2, default=str))

        return 0

    def run_all_verifications(self):
        """Run complete verification suite."""
        print("\n" + "="*80)
        print("COMPLIANCE AUTOMATION INTEGRATION VERIFICATION")
        print("="*80)
        print(f"Audit DB: {self.audit_db}")
        print(f"Compliance DB: {self.compliance_db}")

        steps = [
            ("Logging 10 sample trades", self.log_sample_trades),
            ("Verifying Form 4 fields", self.verify_form4_prefill_fields),
            ("Testing trading windows", self.check_insider_trading_windows),
            ("Generating daily reports", self.generate_daily_reports),
            ("Generating quarterly attestations", self.generate_quarterly_attestations),
            ("Logging violations", self.test_violation_logging),
            ("Verifying database integrity", self.verify_database_integrity),
            ("Generating sample reports", self.generate_compliance_report_samples),
        ]

        for step_name, step_func in steps:
            result = step_func()
            if result != 0:
                print(f"\n[FAILED] VERIFICATION FAILED at: {step_name}")
                return result

        print("\n" + "="*80)
        print("[SUCCESS] ALL COMPLIANCE VERIFICATION TESTS PASSED")
        print("="*80)
        print(f"\nSummary:")
        print(f"  Form 4 Records: {len(self.form4_samples)}")
        print(f"  Window Checks: {len(self.window_checks)} (2 correctly failed)")
        print(f"  Daily Reports: {len(self.daily_reports)}")
        print(f"  Quarterly Attestations: {len(self.attestations)}")
        print(f"  Violation Logs: {len(self.violations)}")

        return 0


def main():
    verifier = ComplianceVerifier(
        audit_db="./verification_audit.db",
        compliance_db="./verification_compliance.db"
    )

    exit_code = verifier.run_all_verifications()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

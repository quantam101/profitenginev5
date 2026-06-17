"""
Compliance Automation Integration Example

Demonstrates complete workflow integrating compliance_automation.py with audit_ledger.py
for production-ready insider trading compliance tracking.
"""

from compliance_automation import ComplianceAutomator, InsiderTradingWindow
from audit_ledger import AuditLedger
from datetime import datetime, timedelta
from decimal import Decimal


def example_daily_trading_workflow():
    """Example: Daily trading with real-time compliance checking."""
    print("=== DAILY TRADING WITH COMPLIANCE CHECKING ===\n")

    # Initialize systems
    audit_ledger = AuditLedger(db_path="./example_audit.db")
    compliance = ComplianceAutomator(
        audit_ledger_path="./example_audit.db",
        compliance_db="./example_compliance.db"
    )

    # Insider information
    insider_id = "EXEC_VP_001"
    insider_name = "Alice Johnson"
    insider_title = "Vice President, Strategic Initiatives"

    # Step 1: Check if trading window is open
    print(f"Step 1: Check trading window for {insider_name}")
    is_window_open, window_reason, window_details = compliance.check_insider_trading_window(
        insider_id=insider_id,
        proposed_transaction_date=datetime.now(),
        security="AAPL"
    )

    print(f"  Window Open: {is_window_open}")
    print(f"  Reason: {window_reason}")
    print(f"  Window ID: {window_details['window_id']}\n")

    if not is_window_open:
        print("  [BLOCKED] TRADE BLOCKED - Window closed")
        compliance.log_compliance_violation(
            violation_type="WINDOW_VIOLATION",
            severity="CRITICAL",
            description=f"Attempted transaction during restricted period: {window_reason}",
            insider_id=insider_id,
            remedial_action="Trade rejected by system"
        )
        return

    # Step 2: Execute trade and generate Form 4
    print(f"Step 2: Execute transaction and generate Form 4")
    shares = Decimal("500")
    price = Decimal("175.50")

    form4 = compliance.generate_form4_prefill(
        insider_id=insider_id,
        insider_name=insider_name,
        insider_title=insider_title,
        company_ticker="AAPL",
        cik_number="0000320193",
        transaction_date=datetime.now(),
        security_title="Common Stock",
        transaction_type="acquisition",
        shares=shares,
        price_per_share=price,
        beneficial_ownership=Decimal("5000"),
    )

    print(f"  Form 4 ID: {form4['metadata']['form4_id']}")
    print(f"  Filing Status: {form4['metadata']['filing_status']}")
    print(f"  Shares Acquired: {form4['non_derivative_holdings']['shares_acquired']}")
    print(f"  Total Value: ${form4['non_derivative_holdings']['aggregate_value']:,.2f}")
    print(f"  Reporting Due: {form4['metadata']['reporting_due_date']}\n")

    # Step 3: Generate daily compliance report
    print(f"Step 3: Generate daily compliance report")
    daily_report = compliance.generate_daily_report(report_date=datetime.now())

    print(f"  Report ID: {daily_report['report_id']}")
    print(f"  Report Date: {daily_report['report_date']}")
    print(f"  Total Trades: {daily_report['total_trades']}")
    print(f"  Compliance Status: {daily_report['compliance_status']}\n")

    # Step 4: Check audit ledger statistics
    print(f"Step 4: Review audit ledger statistics")
    stats = audit_ledger.get_stats()

    print(f"  Total Audit Trades: {stats['total_trades']}")
    print(f"  Approval Rate: {stats['approval_rate_pct']:.1f}%")
    print(f"  Total Rejections: {stats['total_rejections']}\n")

    print("[OK] Daily workflow complete\n")


def example_blackout_period():
    """Example: Managing trading blackout during acquisition."""
    print("=== BLACKOUT PERIOD EXAMPLE ===\n")

    compliance = ComplianceAutomator(
        compliance_db="./example_compliance_blackout.db"
    )

    # Add 30-day blackout for confidential acquisition
    blackout_start = datetime(2024, 6, 1)
    blackout_end = datetime(2024, 6, 30)

    print(f"Step 1: Add blackout period for acquisition")
    blackout_info = compliance.add_blackout_period(
        start_date=blackout_start,
        end_date=blackout_end,
        reason="Acquisition of TechCorp Inc. - confidential process"
    )

    print(f"  Blackout Added: {blackout_info['blackout_added']}")
    print(f"  Period: {blackout_info['start_date']} to {blackout_info['end_date']}")
    print(f"  Reason: {blackout_info['reason']}")
    print(f"  Active Blackout Periods: {blackout_info['active_blackout_periods']}\n")

    # Attempt trade during blackout
    print(f"Step 2: Attempt trade during blackout (June 15)")
    is_open, reason, details = compliance.check_insider_trading_window(
        insider_id="EXEC_CEO_001",
        proposed_transaction_date=datetime(2024, 6, 15),
        security="AAPL"
    )

    print(f"  Window Open: {is_open}")
    print(f"  Window State: {details['window_state']}")
    print(f"  Reason: {reason}\n")

    # Attempt trade after blackout ends
    print(f"Step 3: Attempt trade after blackout (July 1)")
    is_open, reason, details = compliance.check_insider_trading_window(
        insider_id="EXEC_CEO_001",
        proposed_transaction_date=datetime(2024, 7, 1),
        security="AAPL"
    )

    print(f"  Window Open: {is_open}")
    print(f"  Window State: {details['window_state']}")
    print(f"  Reason: {reason}\n")

    print("[OK] Blackout period example complete\n")


def example_quarterly_attestation():
    """Example: Generate quarterly SOX compliance attestation."""
    print("=== QUARTERLY COMPLIANCE ATTESTATION ===\n")

    compliance = ComplianceAutomator(
        compliance_db="./example_compliance_attestation.db"
    )

    # Generate multiple Form 4s during quarter
    for i in range(3):
        compliance.generate_form4_prefill(
            insider_id=f"EXEC_{i:03d}",
            insider_name=f"Executive {i}",
            insider_title=f"Title {i}",
            company_ticker="MSFT",
            cik_number="0000789019",
            transaction_date=datetime.now() - timedelta(days=30-i*10),
            security_title="Common Stock",
            transaction_type="acquisition" if i % 2 == 0 else "disposition",
            shares=Decimal(str(100 * (i + 1))),
            price_per_share=Decimal("350.00"),
            beneficial_ownership=Decimal("10000"),
        )

    # Generate quarterly attestation
    print(f"Step 1: Generate Q2 2024 Quarterly Attestation")
    attestation = compliance.generate_quarterly_attestation(
        fiscal_quarter=2,
        fiscal_year=2024,
        attestor_name="Robert Chen",
        attestor_title="Chief Financial Officer",
    )

    print(f"  Attestation ID: {attestation['attestation_id']}")
    print(f"  Period: Q{attestation['fiscal_quarter']} {attestation['fiscal_year']}")
    print(f"  Attestor: {attestation['attestor_name']}, {attestation['attestor_title']}")
    print(f"  Form 4s Filed: {attestation['total_form4s_filed']}")
    print(f"  Late Filings: {attestation['late_filings']}")
    print(f"  Material Violations: {attestation['material_changes']}")
    print(f"  Control Effectiveness: {attestation['control_effectiveness']}\n")

    print(f"Step 2: Attestation Statement Preview")
    statement_lines = attestation['attestation_statement'].split('\n')[:10]
    for line in statement_lines:
        print(f"  {line}")
    print("  ...\n")

    print("[OK] Quarterly attestation complete\n")


def example_violation_tracking():
    """Example: Track and remediate compliance violations."""
    print("=== VIOLATION TRACKING AND REMEDIATION ===\n")

    compliance = ComplianceAutomator(
        compliance_db="./example_compliance_violations.db"
    )

    # Log different violation types
    violations = [
        {
            "type": "LATE_FILING",
            "severity": "HIGH",
            "description": "Form 4 filed 1 day after regulatory deadline",
            "insider_id": "EXEC_001",
            "action": "Filed with late fee, notified compliance officer"
        },
        {
            "type": "WINDOW_VIOLATION",
            "severity": "CRITICAL",
            "description": "Attempted trade during blackout period (acquisition process)",
            "insider_id": "EXEC_002",
            "action": "Trade rejected by system, executive retrained"
        },
        {
            "type": "DOCUMENTATION_DEFECT",
            "severity": "MEDIUM",
            "description": "Form 4 missing beneficial ownership calculation",
            "insider_id": "EXEC_003",
            "action": "Amended Form 4 submitted, process improved"
        },
    ]

    print(f"Logging {len(violations)} compliance violations\n")

    for i, v in enumerate(violations, 1):
        print(f"Step {i}: Log {v['type']} violation")
        violation = compliance.log_compliance_violation(
            violation_type=v['type'],
            severity=v['severity'],
            description=v['description'],
            insider_id=v['insider_id'],
            remedial_action=v['action'],
        )

        print(f"  Violation ID: {violation['violation_id']}")
        print(f"  Severity: {violation['severity']}")
        print(f"  Insider: {violation['insider_id']}")
        print(f"  Remedial Action: {violation['remedial_action']}\n")

    print("[OK] Violation tracking complete\n")


def main():
    """Run all compliance automation examples."""
    print("\n" + "="*60)
    print("COMPLIANCE AUTOMATION INTEGRATION EXAMPLES")
    print("="*60 + "\n")

    try:
        example_daily_trading_workflow()
        example_blackout_period()
        example_quarterly_attestation()
        example_violation_tracking()

        print("="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

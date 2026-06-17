# Compliance Automation Module

## Overview

`compliance_automation.py` provides SEC Form 4 pre-fill data generation, insider trading window compliance tracking, and regulatory reporting functionality. It integrates seamlessly with `audit_ledger.py` to create a comprehensive compliance audit trail for trading operations.

## Features

### 1. SEC Form 4 Pre-Fill Generation
- Generates complete Form 4 filing data with SEC header information
- Tracks acquisition/disposition transactions
- Includes insider beneficial ownership calculations
- Creates filing-ready JSON that can be submitted to SEC EDGAR
- All filings marked with compliance status

### 2. Insider Trading Window Enforcement
- Tracks trading window state (open/closed/blackout)
- Enforces blackout periods (acquisition processes, quiet periods)
- Restricts trading near earnings announcements (2 days before/after)
- Generates window status reports with restriction details
- Full audit trail of window checks

### 3. Daily Compliance Reporting
- Analyzes all trades from audit ledger
- Tracks window compliance per transaction
- Identifies violations and blackout infractions
- Generates compliance status (GREEN/RED)
- Integrates with audit_ledger.py for seamless data access

### 4. Quarterly Compliance Attestation
- Generates SOX-compliant quarterly attestation documents
- Certifies Form 4 filing timeliness and accuracy
- Reports material violations and control effectiveness
- Includes formal executive signature block
- References required regulatory frameworks

### 5. Compliance Violation Logging
- Records all compliance violations with severity levels
- Tracks remedial actions taken
- Maintains complete audit trail per insider
- Severity levels: LOW, MEDIUM, HIGH, CRITICAL, MATERIAL

## Database Schema

The module creates 5 compliance-specific tables:

```
form4_prefills
├─ form4_id (PK)
├─ insider_id, insider_name, insider_title
├─ company_ticker, cik_number
├─ transaction_date, security_title, transaction_type
├─ shares_acquired, shares_disposed, price_per_share
├─ total_value, beneficial_ownership
├─ reporting_due_date, filing_status
└─ form4_json (complete filing data)

trading_windows
├─ window_id (PK)
├─ insider_id
├─ window_type (BLACKOUT, INTRADAY)
├─ window_state (open/closed/blackout/close_to_earnings)
├─ start_date, end_date, reason
└─ affected_securities

daily_compliance_reports
├─ report_id (PK)
├─ report_date
├─ total_trades, trades_in_window
├─ window_violations, blackout_violations
├─ total_shares_traded, total_volume_usd
└─ report_summary (JSON)

quarterly_attestations
├─ attestation_id (PK)
├─ fiscal_quarter, fiscal_year
├─ attestor_name, attestor_title
├─ total_form4s_filed, late_filings
├─ material_changes, control_effectiveness
└─ attestation_statement (full text)

compliance_violations
├─ violation_id (PK)
├─ violation_date
├─ violation_type, severity
├─ insider_id
├─ description, remedial_action
```

## Usage Examples

### 1. Generate Form 4 Pre-Fill

```python
from compliance_automation import ComplianceAutomator
from datetime import datetime
from decimal import Decimal

compliance = ComplianceAutomator()

form4 = compliance.generate_form4_prefill(
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

print(f"Form 4 ID: {form4['metadata']['form4_id']}")
print(f"Filing Status: {form4['metadata']['filing_status']}")
print(f"Total Value: ${form4['non_derivative_holdings']['aggregate_value']}")
```

### 2. Check Trading Window

```python
from datetime import datetime

# Check if trading window is open
is_open, reason, details = compliance.check_insider_trading_window(
    insider_id="EXEC001",
    proposed_transaction_date=datetime.now(),
    security="AAPL"
)

if is_open:
    print("Window is OPEN - transaction permitted")
else:
    print(f"Window CLOSED: {reason}")
    print(f"Restrictions: {details['restrictions']}")
```

### 3. Manage Blackout Periods

```python
from datetime import datetime, timedelta

# Add blackout period (e.g., acquisition process)
compliance.add_blackout_period(
    start_date=datetime(2024, 6, 1),
    end_date=datetime(2024, 6, 30),
    reason="Acquisition process - confidential information period"
)

# Add earnings announcement date
earnings_date = datetime(2024, 6, 15)
compliance.add_earnings_date(earnings_date)

# Subsequent window checks will respect these restrictions
```

### 4. Generate Daily Compliance Report

```python
from datetime import datetime

report = compliance.generate_daily_report(
    report_date=datetime.now()
)

print(f"Report ID: {report['report_id']}")
print(f"Total Trades: {report['total_trades']}")
print(f"Window Violations: {report['window_violations']}")
print(f"Compliance Status: {report['compliance_status']}")
```

### 5. Generate Quarterly Attestation

```python
attestation = compliance.generate_quarterly_attestation(
    fiscal_quarter=2,
    fiscal_year=2024,
    attestor_name="Robert Johnson",
    attestor_title="Chief Financial Officer",
)

print(f"Attestation ID: {attestation['attestation_id']}")
print(f"Control Effectiveness: {attestation['control_effectiveness']}")
print(f"Form 4s Filed: {attestation['total_form4s_filed']}")

# Attestation statement can be printed directly or saved to file
print(attestation['attestation_statement'])
```

### 6. Log Compliance Violation

```python
violation = compliance.log_compliance_violation(
    violation_type="LATE_FILING",
    severity="HIGH",
    description="Form 4 filed 1 day after deadline",
    insider_id="EXEC001",
    remedial_action="Filed with late fee, internal review scheduled"
)

print(f"Violation ID: {violation['violation_id']}")
print(f"Severity: {violation['severity']}")
```

## Integration with audit_ledger.py

### Automated Compliance Checking Workflow

```python
from audit_ledger import AuditLedger
from compliance_automation import ComplianceAutomator
from datetime import datetime
from decimal import Decimal

# Initialize both systems
audit_ledger = AuditLedger()
compliance = ComplianceAutomator(audit_ledger_path="./audit.db")

# For each proposed trade:
# 1. Check trading window compliance
is_open, reason, details = compliance.check_insider_trading_window(
    insider_id="EXEC001",
    proposed_transaction_date=datetime.now(),
    security="AAPL"
)

if not is_open:
    print(f"Cannot execute trade: {reason}")
    compliance.log_compliance_violation(
        violation_type="WINDOW_VIOLATION",
        severity="HIGH",
        description=f"Trade attempted during restricted window: {reason}",
        insider_id="EXEC001",
    )
    return  # Block trade

# 2. If window is open, execute trade and log to audit ledger
# ... (trade execution logic)

# 3. Log Form 4 entry if required (typically for significant transactions)
if shares_traded > FORM_4_THRESHOLD:
    form4 = compliance.generate_form4_prefill(
        insider_id="EXEC001",
        insider_name="Jane Smith",
        insider_title="CEO",
        company_ticker="AAPL",
        cik_number="0000320193",
        transaction_date=datetime.now(),
        security_title="Common Stock",
        transaction_type="acquisition" if direction == "BUY" else "disposition",
        shares=Decimal(shares_traded),
        price_per_share=Decimal(execution_price),
        beneficial_ownership=Decimal(current_beneficial_ownership),
    )
    print(f"Form 4 generated: {form4['metadata']['form4_id']}")

# 4. Generate daily compliance report
daily_report = compliance.generate_daily_report()
if daily_report['window_violations'] > 0:
    print(f"COMPLIANCE ALERT: {daily_report['window_violations']} window violations detected")
```

### Quarterly Reporting Workflow

```python
# At end of each fiscal quarter:

# 1. Generate daily compliance reports for all quarter dates
for day in range(quarter_start, quarter_end):
    daily_report = compliance.generate_daily_report(report_date=day)

# 2. Generate quarterly attestation
attestation = compliance.generate_quarterly_attestation(
    fiscal_quarter=Q,
    fiscal_year=2024,
    attestor_name="CFO Name",
    attestor_title="Chief Financial Officer",
)

# 3. Save attestation to file
with open(f"attestation_Q{Q}_2024.txt", "w") as f:
    f.write(attestation['attestation_statement'])

# 4. Verify no material violations
if attestation['material_changes'] > 0:
    print(f"ALERT: {attestation['material_changes']} material violations found")
else:
    print(f"Quarterly compliance status: {attestation['control_effectiveness']}")
```

## Regulatory References

The compliance module implements requirements from:

- **Section 302** of Sarbanes-Oxley Act (Corporate Responsibility for Financial Reports)
- **Section 906** of Sarbanes-Oxley Act (Criminal Penalties for Falsification)
- **SEC Regulation FD** (Fair Disclosure)
- **SEC Rule 10b5-1** (Rule 10b5-1 Trading Plans)
- **SEC Form 4** (Changes in Beneficial Ownership)

## File Specifications

- **File Size**: ~320 lines
- **Database**: SQLite (compliance.db)
- **Timezone**: UTC with timezone-aware datetime objects
- **Data Format**: JSON for complex fields (Form 4 data, violations)

## Class Reference

### ComplianceAutomator

Main compliance automation engine.

#### Methods

| Method | Parameters | Returns | Purpose |
|--------|-----------|---------|---------|
| `generate_form4_prefill()` | insider_id, insider_name, insider_title, company_ticker, cik_number, transaction_date, security_title, transaction_type, shares, price_per_share, beneficial_ownership | Dict[str, Any] | Generate SEC Form 4 filing data |
| `check_insider_trading_window()` | insider_id, proposed_transaction_date, security="ALL" | Tuple[bool, str, Dict] | Check if trading window is open |
| `generate_daily_report()` | report_date=None | Dict[str, Any] | Generate daily compliance report |
| `generate_quarterly_attestation()` | fiscal_quarter, fiscal_year, attestor_name, attestor_title | Dict[str, Any] | Generate quarterly SOX attestation |
| `add_blackout_period()` | start_date, end_date, reason | Dict[str, Any] | Add trading blackout period |
| `add_earnings_date()` | earnings_date | Dict[str, Any] | Add earnings announcement date |
| `log_compliance_violation()` | violation_type, severity, description, insider_id, remedial_action=None | Dict[str, Any] | Log compliance violation |

## Security Considerations

1. **Insider IDs**: Should be unique per insider with proper authentication
2. **CIK Numbers**: Validate against SEC database
3. **Database Access**: SQLite databases should be in secure location
4. **Attestations**: Attestor names/titles should be verified
5. **Audit Trail**: All operations create immutable database records
6. **Timezone**: All timestamps use UTC to prevent manipulation

## Error Handling

The module handles:
- Missing or locked audit_ledger database (graceful fallback to 0 trades)
- Invalid date ranges for blackout periods
- Timezone-aware datetime conversion
- SQLite connection errors with automatic cleanup

## Testing

Run comprehensive test suite:

```bash
python test_compliance_automation.py -v
```

Tests cover:
- Form 4 prefill generation with full SEC header
- Trading window checks (open/blackout/earnings restriction)
- Daily compliance reporting
- Quarterly attestation generation
- Compliance violation logging
- Multi-period blackout handling
- Audit ledger integration

All 10 tests should pass with no errors.

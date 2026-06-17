import sqlite3
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Any
from pathlib import Path
import uuid

try:
    from .models import TradeProposal, RiskApprovalDecision, ExecutionResult, TradeOutcome
except ImportError:
    from models import TradeProposal, RiskApprovalDecision, ExecutionResult, TradeOutcome

try:
    from .compliance_automation import ComplianceAutomator
except ImportError:
    from compliance_automation import ComplianceAutomator

class AuditLedger:
    """SQLite-backed immutable audit trail."""

    def __init__(self, db_path: str = "./audit.db", compliance_db: str = "./compliance.db"):
        self.db_path = db_path
        self.compliance_db = compliance_db
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.compliance_db).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        # Initialize compliance automation
        self.compliance_automator = ComplianceAutomator(
            audit_ledger_path=self.db_path,
            compliance_db=self.compliance_db
        )

    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    symbol TEXT,
                    direction TEXT,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    position_size_usd REAL,
                    overall_confidence REAL,
                    expected_reward_risk REAL,
                    rationale TEXT,
                    data JSON
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_decisions (
                    decision_id TEXT PRIMARY KEY,
                    proposal_id TEXT,
                    timestamp TEXT,
                    approved BOOLEAN,
                    rejection_reasons TEXT,
                    risk_score REAL,
                    final_decision TEXT,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    order_id TEXT PRIMARY KEY,
                    proposal_id TEXT,
                    timestamp TEXT,
                    state TEXT,
                    entry_price REAL,
                    fill_price REAL,
                    quantity REAL,
                    slippage REAL,
                    fee REAL,
                    realized_pnl REAL,
                    is_complete BOOLEAN,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    trade_id TEXT PRIMARY KEY,
                    proposal_id TEXT,
                    timestamp TEXT,
                    realized_pnl REAL,
                    return_pct REAL,
                    duration_minutes REAL,
                    max_favorable_excursion REAL,
                    max_adverse_excursion REAL,
                    outcome_json TEXT,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rejections (
                    rejection_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    symbol TEXT,
                    rejection_reasons TEXT,
                    proposal_data JSON
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audit_trail (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    event_type TEXT,
                    proposal_id TEXT,
                    order_id TEXT,
                    insider_id TEXT,
                    compliance_check TEXT,
                    compliance_status TEXT,
                    details JSON,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
                    FOREIGN KEY (order_id) REFERENCES executions(order_id)
                )
            """)

            conn.commit()

    def _log_compliance_status(
        self,
        event_type: str,
        compliance_check: str,
        compliance_status: str,
        proposal_id: str = None,
        order_id: str = None,
        insider_id: str = None,
        details: Dict = None
    ):
        """Log compliance status to audit trail."""
        log_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_audit_trail
                (log_id, timestamp, event_type, proposal_id, order_id, insider_id,
                 compliance_check, compliance_status, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                datetime.utcnow().isoformat(),
                event_type,
                proposal_id,
                order_id,
                insider_id,
                compliance_check,
                compliance_status,
                json.dumps(details) if details else None
            ))
            conn.commit()

    def log_proposal(self, proposal: TradeProposal):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO proposals
                (proposal_id, timestamp, symbol, direction, entry_price, stop_loss,
                 take_profit, position_size_usd, overall_confidence, expected_reward_risk, rationale, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.proposal_id,
                proposal.timestamp.isoformat(),
                proposal.symbol,
                proposal.direction,
                float(proposal.entry_price),
                float(proposal.stop_loss),
                float(proposal.take_profit),
                float(proposal.position_size_usd),
                proposal.overall_confidence,
                proposal.expected_reward_risk,
                proposal.rationale,
                json.dumps({
                    'technical': {
                        'rsi': proposal.technical_signal.rsi_oversold_recovery,
                        'macd': proposal.technical_signal.macd_bullish_cross,
                        'trend': proposal.technical_signal.trend_alignment
                    },
                    'microstructure': {
                        'imbalance': proposal.microstructure_signal.bid_ask_imbalance,
                        'liquidity': proposal.microstructure_signal.liquidity_score
                    },
                    'regime': proposal.regime_signal.regime.value,
                    'portfolio': proposal.portfolio_signal.recommended_action
                })
            ))
            conn.commit()

    def log_risk_decision(self, proposal_id: str, decision: RiskApprovalDecision):
        decision_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO risk_decisions
                (decision_id, proposal_id, timestamp, approved, rejection_reasons, risk_score, final_decision)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                proposal_id,
                datetime.utcnow().isoformat(),
                decision.approved,
                json.dumps([r.value for r in decision.rejection_reasons]),
                decision.risk_score,
                decision.final_decision
            ))
            conn.commit()

        # Check insider trading window for the proposal
        try:
            window_is_open, window_reason, window_details = self.compliance_automator.check_insider_trading_window(
                insider_id="SYSTEM",
                proposed_transaction_date=datetime.utcnow(),
                security="ALL"
            )
            window_status = "OPEN" if window_is_open else "RESTRICTED"
            self._log_compliance_status(
                event_type="RISK_DECISION",
                compliance_check="INSIDER_TRADING_WINDOW",
                compliance_status=window_status,
                proposal_id=proposal_id,
                details={
                    "decision_id": decision_id,
                    "window_open": window_is_open,
                    "window_reason": window_reason,
                    "window_details": window_details
                }
            )
        except Exception as e:
            self._log_compliance_status(
                event_type="RISK_DECISION",
                compliance_check="INSIDER_TRADING_WINDOW",
                compliance_status="ERROR",
                proposal_id=proposal_id,
                details={"error": str(e)}
            )

    def log_execution(self, result: ExecutionResult, proposal_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO executions
                (order_id, proposal_id, timestamp, state, entry_price, fill_price,
                 quantity, slippage, fee, realized_pnl, is_complete)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.order_id,
                proposal_id,
                result.timestamp.isoformat(),
                result.state.value,
                float(result.entry_price),
                float(result.fill_price),
                float(result.quantity),
                float(result.slippage),
                float(result.fee),
                float(result.realized_pnl),
                result.is_complete
            ))
            conn.commit()

        # Generate SEC Form 4 prefill data for the executed trade
        try:
            form4_data = self.compliance_automator.generate_form4_prefill(
                insider_id="SYSTEM",
                insider_name="Automated Trading System",
                insider_title="Trading Algorithm",
                company_ticker="UNKNOWN",
                cik_number="0000000000",
                transaction_date=result.timestamp,
                security_title="Equity Security",
                transaction_type="acquisition" if result.quantity > 0 else "disposition",
                shares=Decimal(str(result.quantity)),
                price_per_share=Decimal(str(result.fill_price)),
                beneficial_ownership=Decimal(str(result.quantity))
            )
            self._log_compliance_status(
                event_type="EXECUTION",
                compliance_check="FORM4_PREFILL_GENERATION",
                compliance_status="GENERATED",
                proposal_id=proposal_id,
                order_id=result.order_id,
                details={
                    "form4_id": form4_data.get("metadata", {}).get("form4_id"),
                    "filing_status": form4_data.get("metadata", {}).get("filing_status"),
                    "window_status": form4_data.get("metadata", {}).get("window_status")
                }
            )
        except Exception as e:
            self._log_compliance_status(
                event_type="EXECUTION",
                compliance_check="FORM4_PREFILL_GENERATION",
                compliance_status="ERROR",
                proposal_id=proposal_id,
                order_id=result.order_id,
                details={"error": str(e)}
            )

    def log_outcome(self, outcome: TradeOutcome):
        import uuid
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO outcomes
                (trade_id, proposal_id, timestamp, realized_pnl, return_pct,
                 duration_minutes, max_favorable_excursion, max_adverse_excursion, outcome_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome.trade_id,
                outcome.proposal.proposal_id,
                outcome.exit_time.isoformat(),
                float(outcome.realized_pnl),
                outcome.return_pct,
                outcome.duration_minutes,
                float(outcome.max_favorable_excursion),
                float(outcome.max_adverse_excursion),
                json.dumps({
                    'symbol': outcome.proposal.symbol,
                    'direction': outcome.proposal.direction,
                    'entry_price': float(outcome.proposal.entry_price),
                    'exit_price': float(outcome.exit_price),
                    'pnl': float(outcome.realized_pnl)
                })
            ))
            conn.commit()

    def get_trades(self, limit: int = 100) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM executions ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        self._init_schema()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total trades
                try:
                    cursor.execute("SELECT COUNT(*) FROM executions")
                    total_trades = cursor.fetchone()[0] or 0
                except:
                    total_trades = 0

                # Profitable trades
                try:
                    cursor.execute("SELECT COUNT(*) FROM outcomes WHERE realized_pnl > 0")
                    profitable_trades = cursor.fetchone()[0] or 0
                except:
                    profitable_trades = 0

                # Total P&L
                try:
                    cursor.execute("SELECT SUM(realized_pnl) FROM outcomes")
                    total_pnl_row = cursor.fetchone()
                    total_pnl = total_pnl_row[0] if total_pnl_row and total_pnl_row[0] else 0
                except:
                    total_pnl = 0

                # Average return
                try:
                    cursor.execute("SELECT AVG(return_pct) FROM outcomes")
                    avg_return_row = cursor.fetchone()
                    avg_return = avg_return_row[0] if avg_return_row and avg_return_row[0] else 0
                except:
                    avg_return = 0

                # Win rate
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

                # Rejections
                try:
                    cursor.execute("SELECT COUNT(*) FROM rejections")
                    total_rejections = cursor.fetchone()[0] or 0
                except:
                    total_rejections = 0

                return {
                    'total_trades': total_trades,
                    'profitable_trades': profitable_trades,
                    'win_rate_pct': win_rate,
                    'total_pnl': total_pnl,
                    'avg_return_pct': avg_return,
                    'total_rejections': total_rejections,
                    'approval_rate_pct': (total_trades / (total_trades + total_rejections) * 100) if (total_trades + total_rejections) > 0 else 0
                }
        except Exception as e:
            # Return default stats if database is unavailable
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'win_rate_pct': 0.0,
                'total_pnl': 0,
                'avg_return_pct': 0.0,
                'total_rejections': 0,
                'approval_rate_pct': 0.0
            }

    def generate_daily_compliance_report(self, report_date: datetime = None) -> Dict[str, Any]:
        """
        Generate daily compliance report. Call this daily at 8pm UTC.

        Args:
            report_date: Date for which to generate report (default: today UTC)

        Returns:
            Daily compliance report with trade counts, violations, and status
        """
        if report_date is None:
            report_date = datetime.utcnow()

        report = self.compliance_automator.generate_daily_report(report_date)

        # Log the report generation to audit trail
        self._log_compliance_status(
            event_type="DAILY_REPORT",
            compliance_check="DAILY_COMPLIANCE_REPORT",
            compliance_status="GENERATED",
            details={
                "report_id": report.get("report_id"),
                "report_date": report.get("report_date"),
                "total_trades": report.get("total_trades"),
                "window_violations": report.get("window_violations"),
                "blackout_violations": report.get("blackout_violations"),
                "compliance_status": report.get("compliance_status")
            }
        )

        return report

    def generate_quarterly_attestation(
        self,
        fiscal_quarter: int,
        fiscal_year: int,
        attestor_name: str,
        attestor_title: str
    ) -> Dict[str, Any]:
        """
        Generate quarterly compliance attestation. Call on 1st of each quarter.

        Args:
            fiscal_quarter: Quarter number (1-4)
            fiscal_year: Fiscal year
            attestor_name: Name of person attesting
            attestor_title: Title of person attesting

        Returns:
            Quarterly attestation document with Form 4 filing stats and violations summary
        """
        attestation = self.compliance_automator.generate_quarterly_attestation(
            fiscal_quarter=fiscal_quarter,
            fiscal_year=fiscal_year,
            attestor_name=attestor_name,
            attestor_title=attestor_title
        )

        # Log the attestation generation to audit trail
        self._log_compliance_status(
            event_type="QUARTERLY_ATTESTATION",
            compliance_check="QUARTERLY_COMPLIANCE_ATTESTATION",
            compliance_status="GENERATED",
            details={
                "attestation_id": attestation.get("attestation_id"),
                "fiscal_quarter": attestation.get("fiscal_quarter"),
                "fiscal_year": attestation.get("fiscal_year"),
                "total_form4s_filed": attestation.get("total_form4s_filed"),
                "late_filings": attestation.get("late_filings"),
                "material_changes": attestation.get("material_changes"),
                "control_effectiveness": attestation.get("control_effectiveness")
            }
        )

        return attestation

    def add_blackout_period(self, start_date: datetime, end_date: datetime, reason: str) -> Dict[str, Any]:
        """Add a trading blackout period (e.g., quiet period, acquisition process)."""
        return self.compliance_automator.add_blackout_period(start_date, end_date, reason)

    def add_earnings_date(self, earnings_date: datetime) -> Dict[str, Any]:
        """Add an earnings announcement date for insider trading window enforcement."""
        return self.compliance_automator.add_earnings_date(earnings_date)

    def log_compliance_violation(
        self,
        violation_type: str,
        severity: str,
        description: str,
        insider_id: str = None,
        remedial_action: str = None
    ) -> Dict[str, Any]:
        """Log compliance violation to audit trail."""
        violation = self.compliance_automator.log_compliance_violation(
            violation_type=violation_type,
            severity=severity,
            description=description,
            insider_id=insider_id or "SYSTEM",
            remedial_action=remedial_action
        )

        # Also log to compliance audit trail
        self._log_compliance_status(
            event_type="COMPLIANCE_VIOLATION",
            compliance_check=violation_type,
            compliance_status=f"VIOLATION_{severity}",
            insider_id=insider_id,
            details={
                "violation_id": violation.get("violation_id"),
                "violation_type": violation_type,
                "severity": severity,
                "description": description,
                "remedial_action": remedial_action
            }
        )

        return violation

    def get_compliance_audit_trail(self, limit: int = 100) -> List[Dict]:
        """Retrieve compliance audit trail logs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM compliance_audit_trail ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

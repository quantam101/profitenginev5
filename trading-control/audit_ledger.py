import sqlite3
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
from pathlib import Path

try:
    from .models import TradeProposal, RiskApprovalDecision, ExecutionResult, TradeOutcome
except ImportError:
    from models import TradeProposal, RiskApprovalDecision, ExecutionResult, TradeOutcome

class AuditLedger:
    """SQLite-backed immutable audit trail."""

    def __init__(self, db_path: str = "./audit.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

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
        import uuid
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO risk_decisions
                (decision_id, proposal_id, timestamp, approved, rejection_reasons, risk_score, final_decision)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                proposal_id,
                datetime.utcnow().isoformat(),
                decision.approved,
                json.dumps([r.value for r in decision.rejection_reasons]),
                decision.risk_score,
                decision.final_decision
            ))
            conn.commit()

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

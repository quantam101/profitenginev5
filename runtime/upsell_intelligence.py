"""
UPSELL INTELLIGENCE SYSTEM — Premium Tier Scoring & Monetization Candidate Detection
Identifies high-value trading clients ready for Hybrid, White-Label, or Enterprise upgrades.

Scoring Logic:
  - Win Rate >= 70%       → Hybrid Tier Candidate (good reliability)
  - Win Rate >= 85%       → White-Label / Enterprise Candidate (proven performer)
  - 5+ Consecutive Winning Days → Premium Candidate (consistency signal)
  - Balance Growth > 50% in 7 days → High-Value Customer (strong growth trajectory)
  - Daily Trades >= 10    → Active User (engagement signal / volume buyer)

Output: Ranked list of clients with monetization readiness, tier recommendations, and sales messaging.
"""

from __future__ import annotations

import sqlite3
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from decimal import Decimal
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# UPSELL TIER DEFINITIONS
# ============================================================================
class UpsellTier(Enum):
    """Premium monetization tiers"""
    FREE = "free"
    HYBRID = "hybrid"  # Win rate >= 70%, light support
    WHITE_LABEL = "white_label"  # Win rate >= 85%, premium support
    ENTERPRISE = "enterprise"  # All metrics top-tier, custom features


class UpsellSignal(Enum):
    """Scoring signal types for client readiness"""
    HIGH_WIN_RATE = "high_win_rate"
    BALANCE_GROWTH = "balance_growth"
    CONSISTENCY = "consistency"
    ENGAGEMENT = "engagement"
    VOLATILITY_CONTROL = "volatility_control"


@dataclass(frozen=True)
class ClientMetrics:
    """Read-only snapshot of client trading performance"""
    client_id: str
    username: str
    account_balance: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # 0.0-1.0
    avg_win_usd: Decimal
    avg_loss_usd: Decimal
    daily_trades_list: List[int]  # trades per day for last 7 days
    balance_history: List[Decimal]  # balance snapshots for last 7 days
    pnl_daily: List[Decimal]  # daily P&L for last 7 days
    max_drawdown_daily: Decimal
    risk_score: float  # 0.0 (safe) to 1.0 (reckless)
    last_trade_timestamp: datetime
    account_created: datetime


@dataclass
class UpsellScoreBreakdown:
    """Detailed scoring breakdown for transparency"""
    client_id: str
    username: str
    base_score: float  # 0-100
    win_rate_score: float  # 0-25
    growth_score: float  # 0-25
    consistency_score: float  # 0-25
    engagement_score: float  # 0-25
    tier_recommendation: UpsellTier
    signals: List[Tuple[UpsellSignal, str]] = field(default_factory=list)
    sales_message: str = ""
    estimated_upsell_value_usd: float = 0.0
    priority_rank: int = 0


@dataclass
class UpsellCampaign:
    """Campaign targeting results"""
    date_generated: datetime
    total_clients_scored: int
    enterprise_candidates: List[UpsellScoreBreakdown]
    white_label_candidates: List[UpsellScoreBreakdown]
    hybrid_candidates: List[UpsellScoreBreakdown]
    total_pipeline_value_usd: float


# ============================================================================
# UPSELL SCORER
# ============================================================================
class UpsellScorer:
    """
    Analyzes client trading metrics and recommends monetization tiers.
    Designed to be called daily by sales outreach automation.
    """

    # Tier Thresholds
    MIN_WIN_RATE_HYBRID = 0.70
    MIN_WIN_RATE_ENTERPRISE = 0.85
    MIN_BALANCE_GROWTH_7D = 0.50  # 50% growth
    MIN_CONSECUTIVE_WINS = 5  # days
    MIN_DAILY_TRADES = 10  # for "active user" signal
    MIN_ACCOUNT_AGE_DAYS = 7  # must be active for at least 1 week

    # Monetization Tier Pricing (annual)
    HYBRID_AUM_FEE_BPS = 50  # 0.50% annually
    WHITE_LABEL_AUM_FEE_BPS = 100  # 1.0% annually
    ENTERPRISE_AUM_FEE_BPS = 150  # 1.5% annually

    def __init__(self, db_path: str = "clients.db"):
        """Initialize scorer with database path"""
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize or verify database exists"""
        # If DB doesn't exist, create demo data structure
        if not self.db_path.exists():
            logger.warning(f"Database {self.db_path} not found. Creating demo structure.")
            self._create_demo_db()

    def _create_demo_db(self):
        """Create demo database with sample trading clients"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                account_balance REAL NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_trade_at TIMESTAMP,
                subscription_tier TEXT DEFAULT 'free'
            )
        """)

        # Create trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                entry_price REAL,
                exit_price REAL,
                shares INTEGER,
                pnl_usd REAL,
                win BOOLEAN,
                executed_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        """)

        # Create daily_snapshots table (for balance history tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                balance REAL,
                trade_count INTEGER,
                daily_pnl REAL,
                captured_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Created demo database at {self.db_path}")

    def score_all_clients(self) -> UpsellCampaign:
        """
        Score all clients in database and generate upsell campaign targeting list.
        Returns sorted candidates by tier and priority.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Fetch all active clients
        cursor.execute("""
            SELECT client_id, username FROM clients WHERE created_at IS NOT NULL
        """)
        client_rows = cursor.fetchall()
        conn.close()

        scores: List[UpsellScoreBreakdown] = []

        for client_id, username in client_rows:
            try:
                metrics = self._fetch_client_metrics(client_id, username)
                if metrics:
                    score = self._score_client(metrics)
                    scores.append(score)
            except Exception as e:
                logger.error(f"Error scoring client {client_id}: {e}")
                continue

        # Sort by base score descending
        scores.sort(key=lambda x: x.base_score, reverse=True)

        # Assign priority ranks
        for rank, score in enumerate(scores, 1):
            score.priority_rank = rank

        # Separate by tier
        enterprise = [s for s in scores if s.tier_recommendation == UpsellTier.ENTERPRISE]
        white_label = [s for s in scores if s.tier_recommendation == UpsellTier.WHITE_LABEL]
        hybrid = [s for s in scores if s.tier_recommendation == UpsellTier.HYBRID]

        # Calculate total pipeline value
        pipeline_value = sum(s.estimated_upsell_value_usd for s in scores)

        campaign = UpsellCampaign(
            date_generated=datetime.now(),
            total_clients_scored=len(scores),
            enterprise_candidates=enterprise,
            white_label_candidates=white_label,
            hybrid_candidates=hybrid,
            total_pipeline_value_usd=pipeline_value,
        )

        logger.info(
            f"Campaign generated: {len(enterprise)} Enterprise, "
            f"{len(white_label)} White-Label, {len(hybrid)} Hybrid candidates"
        )

        return campaign

    def _fetch_client_metrics(self, client_id: str, username: str) -> Optional[ClientMetrics]:
        """Fetch all metrics for a single client"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            # Fetch basic client info
            cursor.execute(
                "SELECT account_balance, created_at FROM clients WHERE client_id = ?",
                (client_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            balance, created_at_str = row
            created_at = (
                datetime.fromisoformat(created_at_str)
                if created_at_str
                else datetime.now()
            )

            # Fetch all trades for the client
            cursor.execute(
                """
                SELECT pnl_usd, win, executed_at FROM trades
                WHERE client_id = ? ORDER BY executed_at ASC
                """,
                (client_id,),
            )
            trades = cursor.fetchall()

            if not trades:
                logger.warning(f"Client {client_id} has no trades")
                return None

            # Calculate trade statistics
            winning_trades = sum(1 for _, win, _ in trades if win)
            losing_trades = len(trades) - winning_trades
            win_rate = winning_trades / len(trades) if trades else 0.0

            winning_pnls = [Decimal(str(pnl)) for pnl, win, _ in trades if win and pnl > 0]
            losing_pnls = [Decimal(str(pnl)) for pnl, win, _ in trades if not win and pnl < 0]

            avg_win = (
                sum(winning_pnls) / len(winning_pnls)
                if winning_pnls
                else Decimal("0.00")
            )
            avg_loss = (
                sum(losing_pnls) / len(losing_pnls)
                if losing_pnls
                else Decimal("0.00")
            )

            # Calculate daily aggregates for last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            daily_trades_list = self._calculate_daily_trades(
                client_id, trades, seven_days_ago
            )
            balance_history = self._fetch_balance_history(client_id, seven_days_ago)
            pnl_daily = self._calculate_daily_pnl(client_id, trades, seven_days_ago)

            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown(pnl_daily)

            # Calculate risk score (volatility + drawdown)
            risk_score = self._calculate_risk_score(pnl_daily, max_drawdown)

            # Last trade timestamp
            last_trade_dt = (
                datetime.fromisoformat(trades[-1][2]) if trades[-1][2] else datetime.now()
            )

            metrics = ClientMetrics(
                client_id=client_id,
                username=username,
                account_balance=Decimal(str(balance)),
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                avg_win_usd=avg_win,
                avg_loss_usd=avg_loss,
                daily_trades_list=daily_trades_list,
                balance_history=balance_history,
                pnl_daily=pnl_daily,
                max_drawdown_daily=max_drawdown,
                risk_score=risk_score,
                last_trade_timestamp=last_trade_dt,
                account_created=created_at,
            )

            return metrics

        finally:
            conn.close()

    def _calculate_daily_trades(
        self,
        client_id: str,
        trades: List[Tuple],
        since: datetime,
    ) -> List[int]:
        """Count trades per day for last 7 days"""
        daily_counts = {}
        for _, _, executed_at_str in trades:
            if not executed_at_str:
                continue
            executed_at = datetime.fromisoformat(executed_at_str)
            if executed_at < since:
                continue
            day_key = executed_at.date()
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

        # Return as ordered list for last 7 days
        result = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).date()
            result.append(daily_counts.get(day, 0))

        return result

    def _fetch_balance_history(
        self, client_id: str, since: datetime
    ) -> List[Decimal]:
        """Fetch balance snapshots from daily_snapshots table"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT balance FROM daily_snapshots
                WHERE client_id = ? AND captured_at > ?
                ORDER BY captured_at ASC
                """,
                (client_id, since.isoformat()),
            )
            snapshots = cursor.fetchall()
            return [Decimal(str(balance)) for balance, in snapshots]

        finally:
            conn.close()

    def _calculate_daily_pnl(
        self, client_id: str, trades: List[Tuple], since: datetime
    ) -> List[Decimal]:
        """Calculate P&L per day for last 7 days"""
        daily_pnl = {}
        for pnl, _, executed_at_str in trades:
            if not executed_at_str:
                continue
            executed_at = datetime.fromisoformat(executed_at_str)
            if executed_at < since:
                continue
            day_key = executed_at.date()
            daily_pnl[day_key] = daily_pnl.get(day_key, Decimal("0")) + Decimal(
                str(pnl)
            )

        # Return as ordered list
        result = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).date()
            result.append(daily_pnl.get(day, Decimal("0")))

        return result

    def _calculate_max_drawdown(self, pnl_daily: List[Decimal]) -> Decimal:
        """Calculate maximum drawdown from daily P&L"""
        if not pnl_daily:
            return Decimal("0")

        cumulative = Decimal("0")
        peak = Decimal("0")
        max_dd = Decimal("0")

        for pnl in pnl_daily:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def _calculate_risk_score(
        self, pnl_daily: List[Decimal], max_drawdown: Decimal
    ) -> float:
        """
        Calculate risk score (0.0 = safe, 1.0 = reckless).
        Based on volatility and drawdown.
        """
        if not pnl_daily or len(pnl_daily) < 2:
            return 0.5

        # Calculate volatility (standard deviation proxy)
        avg = sum(pnl_daily) / len(pnl_daily)
        variance = sum((x - avg) ** 2 for x in pnl_daily) / len(pnl_daily)
        volatility = float(variance.sqrt())

        # Normalize to 0-1 range (assuming volatility > $100 = high risk)
        vol_score = min(1.0, float(volatility) / 100.0)

        # Normalize max drawdown (assuming > $500 = high risk)
        dd_score = min(1.0, float(max_drawdown) / 500.0)

        # Combined risk score
        risk = (vol_score * 0.6) + (dd_score * 0.4)
        return min(1.0, risk)

    def _score_client(self, metrics: ClientMetrics) -> UpsellScoreBreakdown:
        """Generate detailed score for a client"""
        score = UpsellScoreBreakdown(
            client_id=metrics.client_id,
            username=metrics.username,
            base_score=0.0,
            win_rate_score=0.0,
            growth_score=0.0,
            consistency_score=0.0,
            engagement_score=0.0,
            tier_recommendation=UpsellTier.FREE,
            signals=[],
        )

        # Check account age
        account_age = (datetime.now() - metrics.account_created).days
        if account_age < self.MIN_ACCOUNT_AGE_DAYS:
            logger.debug(
                f"Client {metrics.username} too new ({account_age} days)"
            )
            return score

        # ===== WIN RATE SCORING (0-25 pts) =====
        if metrics.win_rate >= self.MIN_WIN_RATE_ENTERPRISE:
            score.win_rate_score = 25.0
            score.signals.append(
                (
                    UpsellSignal.HIGH_WIN_RATE,
                    f"Enterprise-tier win rate: {metrics.win_rate*100:.1f}%",
                )
            )
        elif metrics.win_rate >= self.MIN_WIN_RATE_HYBRID:
            score.win_rate_score = 20.0
            score.signals.append(
                (
                    UpsellSignal.HIGH_WIN_RATE,
                    f"Hybrid-tier win rate: {metrics.win_rate*100:.1f}%",
                )
            )
        else:
            score.win_rate_score = max(0.0, (metrics.win_rate - 0.5) * 50.0)

        # ===== BALANCE GROWTH SCORING (0-25 pts) =====
        if metrics.balance_history:
            earliest_balance = metrics.balance_history[0]
            current_balance = metrics.account_balance
            if earliest_balance > 0:
                growth = float((current_balance - earliest_balance) / earliest_balance)
                if growth >= self.MIN_BALANCE_GROWTH_7D:
                    score.growth_score = 25.0
                    score.signals.append(
                        (
                            UpsellSignal.BALANCE_GROWTH,
                            f"50%+ growth in 7 days: {growth*100:.1f}%",
                        )
                    )
                else:
                    score.growth_score = max(0.0, min(25.0, growth * 50.0))

        # ===== CONSISTENCY SCORING (0-25 pts) =====
        consecutive_wins = self._count_consecutive_wins(metrics.pnl_daily)
        if consecutive_wins >= self.MIN_CONSECUTIVE_WINS:
            score.consistency_score = 25.0
            score.signals.append(
                (
                    UpsellSignal.CONSISTENCY,
                    f"{consecutive_wins} consecutive winning days",
                )
            )
        else:
            score.consistency_score = (consecutive_wins / self.MIN_CONSECUTIVE_WINS) * 25.0

        # ===== ENGAGEMENT SCORING (0-25 pts) =====
        avg_daily_trades = (
            sum(metrics.daily_trades_list) / len(metrics.daily_trades_list)
            if metrics.daily_trades_list
            else 0.0
        )
        if avg_daily_trades >= self.MIN_DAILY_TRADES:
            score.engagement_score = 25.0
            score.signals.append(
                (
                    UpsellSignal.ENGAGEMENT,
                    f"High-volume trader: {avg_daily_trades:.1f} trades/day",
                )
            )
        else:
            score.engagement_score = max(0.0, (avg_daily_trades / self.MIN_DAILY_TRADES) * 25.0)

        # ===== TOTAL SCORE =====
        score.base_score = (
            score.win_rate_score
            + score.growth_score
            + score.consistency_score
            + score.engagement_score
        )

        # ===== TIER ASSIGNMENT =====
        if (
            metrics.win_rate >= self.MIN_WIN_RATE_ENTERPRISE
            and score.consistency_score >= 15.0
            and score.engagement_score >= 15.0
        ):
            score.tier_recommendation = UpsellTier.ENTERPRISE
            aum_fee_pct = self.ENTERPRISE_AUM_FEE_BPS / 10000.0
            score.estimated_upsell_value_usd = (
                float(metrics.account_balance) * aum_fee_pct
            )
        elif metrics.win_rate >= self.MIN_WIN_RATE_HYBRID and score.base_score >= 50.0:
            score.tier_recommendation = UpsellTier.WHITE_LABEL
            aum_fee_pct = self.WHITE_LABEL_AUM_FEE_BPS / 10000.0
            score.estimated_upsell_value_usd = (
                float(metrics.account_balance) * aum_fee_pct
            )
        elif metrics.win_rate >= self.MIN_WIN_RATE_HYBRID:
            score.tier_recommendation = UpsellTier.HYBRID
            aum_fee_pct = self.HYBRID_AUM_FEE_BPS / 10000.0
            score.estimated_upsell_value_usd = (
                float(metrics.account_balance) * aum_fee_pct
            )

        # ===== SALES MESSAGE =====
        score.sales_message = self._generate_sales_message(metrics, score)

        return score

    def _count_consecutive_wins(self, pnl_daily: List[Decimal]) -> int:
        """Count consecutive winning days (positive daily P&L)"""
        if not pnl_daily:
            return 0

        consecutive = 0
        for pnl in reversed(pnl_daily):
            if pnl > 0:
                consecutive += 1
            else:
                break

        return consecutive

    def _generate_sales_message(
        self, metrics: ClientMetrics, score: UpsellScoreBreakdown
    ) -> str:
        """Generate personalized sales outreach message"""
        messages = {
            UpsellTier.ENTERPRISE: (
                f"Hi {metrics.username},\n\n"
                f"Your trading performance is exceptional: {metrics.win_rate*100:.1f}% win rate with "
                f"${float(metrics.account_balance):,.2f} in managed capital. We'd like to discuss our "
                f"Enterprise tier, which includes white-label platform access, 24/7 support, and "
                f"custom strategy integration. Are you available for a brief call this week?"
            ),
            UpsellTier.WHITE_LABEL: (
                f"Hi {metrics.username},\n\n"
                f"You've achieved {metrics.win_rate*100:.1f}% win rate with consistent profitability. "
                f"Our White-Label tier offers dedicated support, advanced analytics, and risk management tools. "
                f"Let's see if this is a good fit for your trading goals."
            ),
            UpsellTier.HYBRID: (
                f"Hi {metrics.username},\n\n"
                f"Your {metrics.win_rate*100:.1f}% win rate shows strong trading discipline. "
                f"Our Hybrid tier adds premium features and support—interested in learning more?"
            ),
            UpsellTier.FREE: (
                f"Hi {metrics.username},\n\n"
                f"Thanks for using ProfitEngine. Keep refining your strategy, and we'll check back as you grow!"
            ),
        }

        return messages.get(score.tier_recommendation, "")


# ============================================================================
# CONVENIENCE FUNCTIONS FOR DAILY SALES AUTOMATION
# ============================================================================


def generate_daily_upsell_report(db_path: str = "clients.db") -> Dict[str, Any]:
    """
    Main entry point: Generate complete upsell report for the day.
    Call this daily via cron for sales team automation.

    Returns:
        Dict with campaign data suitable for email/dashboard export
    """
    scorer = UpsellScorer(db_path)
    campaign = scorer.score_all_clients()

    return {
        "generated_at": campaign.date_generated.isoformat(),
        "total_clients": campaign.total_clients_scored,
        "pipeline_value_usd": campaign.total_pipeline_value_usd,
        "enterprise_count": len(campaign.enterprise_candidates),
        "white_label_count": len(campaign.white_label_candidates),
        "hybrid_count": len(campaign.hybrid_candidates),
        "enterprise_candidates": [
            _score_to_dict(s) for s in campaign.enterprise_candidates
        ],
        "white_label_candidates": [
            _score_to_dict(s) for s in campaign.white_label_candidates
        ],
        "hybrid_candidates": [_score_to_dict(s) for s in campaign.hybrid_candidates],
    }


def _score_to_dict(score: UpsellScoreBreakdown) -> Dict[str, Any]:
    """Convert score to JSON-serializable dict"""
    return {
        "client_id": score.client_id,
        "username": score.username,
        "base_score": score.base_score,
        "win_rate_score": score.win_rate_score,
        "growth_score": score.growth_score,
        "consistency_score": score.consistency_score,
        "engagement_score": score.engagement_score,
        "tier_recommendation": score.tier_recommendation.value,
        "estimated_upsell_value_usd": score.estimated_upsell_value_usd,
        "priority_rank": score.priority_rank,
        "signals": [(s.value, msg) for s, msg in score.signals],
        "sales_message": score.sales_message,
    }


def export_campaign_csv(
    campaign: UpsellCampaign, output_path: str = "upsell_campaign.csv"
):
    """Export campaign candidates to CSV for sales team import"""
    import csv

    all_candidates = (
        campaign.enterprise_candidates
        + campaign.white_label_candidates
        + campaign.hybrid_candidates
    )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "priority_rank",
                "username",
                "client_id",
                "tier_recommendation",
                "base_score",
                "estimated_upsell_value_usd",
                "sales_message",
            ],
        )
        writer.writeheader()
        for cand in all_candidates:
            writer.writerow(
                {
                    "priority_rank": cand.priority_rank,
                    "username": cand.username,
                    "client_id": cand.client_id,
                    "tier_recommendation": cand.tier_recommendation.value,
                    "base_score": f"{cand.base_score:.1f}",
                    "estimated_upsell_value_usd": f"${cand.estimated_upsell_value_usd:.2f}",
                    "sales_message": cand.sales_message.replace("\n", " "),
                }
            )

    logger.info(f"Campaign exported to {output_path}")


# ============================================================================
# EXAMPLE USAGE & INTEGRATION
# ============================================================================
if __name__ == "__main__":
    """
    Example: Run daily upsell scoring and generate report.
    """

    # Example 1: Score all clients and get JSON report
    print("=" * 80)
    print("UPSELL INTELLIGENCE — Daily Scoring Run")
    print("=" * 80)

    report = generate_daily_upsell_report()

    print(f"\nCampaign Generated: {report['generated_at']}")
    print(f"Total Clients Scored: {report['total_clients']}")
    print(f"Pipeline Value: ${report['pipeline_value_usd']:,.2f}")
    print()

    print(f"Enterprise Candidates: {report['enterprise_count']}")
    for cand in report["enterprise_candidates"]:
        print(f"  • {cand['username']} (Score: {cand['base_score']:.1f}/100)")
        print(f"    Est. Annual Value: ${cand['estimated_upsell_value_usd']:.2f}")
    print()

    print(f"White-Label Candidates: {report['white_label_count']}")
    for cand in report["white_label_candidates"]:
        print(f"  • {cand['username']} (Score: {cand['base_score']:.1f}/100)")
        print(f"    Est. Annual Value: ${cand['estimated_upsell_value_usd']:.2f}")
    print()

    print(f"Hybrid Candidates: {report['hybrid_count']}")
    for cand in report["hybrid_candidates"][:5]:  # Show top 5
        print(f"  • {cand['username']} (Score: {cand['base_score']:.1f}/100)")
        print(f"    Est. Annual Value: ${cand['estimated_upsell_value_usd']:.2f}")
    if report["hybrid_count"] > 5:
        print(f"  ... and {report['hybrid_count'] - 5} more")
    print()

    # Example 2: Get detailed breakdown for a specific tier
    if report["enterprise_candidates"]:
        top_enterprise = report["enterprise_candidates"][0]
        print(f"\nDETAILED BREAKDOWN — {top_enterprise['username']} (Enterprise)")
        print(f"  Win Rate Score:      {top_enterprise['win_rate_score']:.1f}/25")
        print(f"  Growth Score:        {top_enterprise['growth_score']:.1f}/25")
        print(f"  Consistency Score:   {top_enterprise['consistency_score']:.1f}/25")
        print(f"  Engagement Score:    {top_enterprise['engagement_score']:.1f}/25")
        print(f"  Total Score:         {top_enterprise['base_score']:.1f}/100")
        print(f"\n  Signals:")
        for signal, message in top_enterprise["signals"]:
            print(f"    - {signal}: {message}")
        print(f"\n  Sales Message:")
        for line in top_enterprise["sales_message"].split("\n"):
            print(f"    {line}")

    # Example 3: Export CSV for sales team
    print("\n" + "=" * 80)
    scorer = UpsellScorer()
    campaign = scorer.score_all_clients()
    export_campaign_csv(campaign, "upsell_campaign_sample.csv")
    print(f"Campaign CSV exported to upsell_campaign_sample.csv")
    print("=" * 80)

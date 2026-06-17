from decimal import Decimal
from typing import List, Dict
from datetime import datetime
import numpy as np

try:
    from .models import (
        TradeProposal, RiskApprovalDecision, RejectionReason, AccountState
    )
except ImportError:
    from models import (
        TradeProposal, RiskApprovalDecision, RejectionReason, AccountState
    )

class DeterministicRiskKernel:
    def __init__(self, hard_limits: Dict):
        self.max_daily_loss = Decimal(str(hard_limits.get('max_daily_loss_usd', 200)))
        self.max_weekly_loss = Decimal(str(hard_limits.get('max_weekly_loss_usd', 1000)))
        self.max_spread_bps = hard_limits.get('max_spread_bps', 5)
        self.min_volume_usd = Decimal(str(hard_limits.get('min_volume_usd', 100000)))
        self.min_reward_risk = hard_limits.get('min_reward_risk_ratio', 2.0)
        self.max_correlation = hard_limits.get('max_correlation', 0.7)
        self.quote_stale_threshold_sec = hard_limits.get('quote_stale_threshold_sec', 5)
        self.max_open_positions = hard_limits.get('max_open_positions', 3)
        self.max_trades_per_day = hard_limits.get('max_trades_per_day', 10)

    def evaluate(self, proposal: TradeProposal, market_snapshot: Dict,
                 account_state: AccountState, open_orders: List = None) -> RiskApprovalDecision:
        """
        Apply ALL hard gates. ANY gate failure → rejection.
        No override possible; no human negotiation on hard limits.
        """
        rejections = []
        open_orders = open_orders or []

        # GATE 1: Regime approval
        if not proposal.regime_signal.approved_to_trade:
            rejections.append(RejectionReason.REGIME_FORBIDS)

        # GATE 2: Account reconciliation
        if account_state.position_mismatch:
            rejections.append(RejectionReason.ACCOUNT_UNRECONCILED)

        if account_state.broker_offline:
            rejections.append(RejectionReason.BROKER_OFFLINE)

        # GATE 3: Daily loss limit
        if account_state.daily_pnl <= -self.max_daily_loss:
            rejections.append(RejectionReason.DAILY_LOSS_HIT)

        # GATE 4: Weekly loss limit
        if account_state.weekly_pnl <= -self.max_weekly_loss:
            rejections.append(RejectionReason.WEEKLY_LOSS_HIT)

        # GATE 5: Capital available
        if proposal.position_size_usd > account_state.buying_power:
            rejections.append(RejectionReason.CAPITAL_INSUFFICIENT)

        # GATE 6: Duplicate order check
        duplicate_exists = False
        for order in open_orders:
            order_symbol = order.get('symbol') if isinstance(order, dict) else getattr(order, 'symbol', None)
            order_direction = order.get('direction') if isinstance(order, dict) else getattr(order, 'direction', None)
            if order_symbol == proposal.symbol and order_direction == proposal.direction:
                duplicate_exists = True
                break
        if duplicate_exists:
            rejections.append(RejectionReason.DUPLICATE_ORDER)

        # GATE 7: Spread check
        bid = Decimal(str(market_snapshot['bid']))
        ask = Decimal(str(market_snapshot['ask']))
        if bid > 0:
            spread_bps = ((ask - bid) / bid) * 10000
            if spread_bps > self.max_spread_bps:
                rejections.append(RejectionReason.SPREAD_TOO_WIDE)

        # GATE 8: Liquidity check (simplified)
        orderbook = market_snapshot.get('orderbook', {})
        if not orderbook:
            rejections.append(RejectionReason.LIQUIDITY_INSUFFICIENT)
        else:
            bids = np.array(orderbook.get('bids', []), dtype=float)
            if len(bids) > 0:
                bid_volume = Decimal(str(np.sum(bids[:5, 1]) * float(bids[0, 0])))
                if bid_volume < self.min_volume_usd:
                    rejections.append(RejectionReason.LIQUIDITY_INSUFFICIENT)

        # GATE 9: Data freshness
        ts = market_snapshot['timestamp']
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        age_sec = (datetime.utcnow() - ts).total_seconds()
        if age_sec > self.quote_stale_threshold_sec:
            rejections.append(RejectionReason.DATA_STALE)

        # GATE 10: Reward-to-risk ratio
        if proposal.expected_reward_risk < self.min_reward_risk:
            rejections.append(RejectionReason.REWARD_RISK_LOW)

        # GATE 11: Correlation check
        if proposal.portfolio_signal.max_correlated_exposure > self.max_correlation:
            rejections.append(RejectionReason.CORRELATION_HIGH)

        # GATE 12: Event risk
        if proposal.regime_signal.event_risk > 0.5:
            rejections.append(RejectionReason.EVENT_RISK_HIGH)

        # GATE 13: Open position count
        if len(account_state.open_positions) >= self.max_open_positions:
            rejections.append(RejectionReason.CAPITAL_INSUFFICIENT)

        # Decision
        if rejections:
            return RiskApprovalDecision(
                approved=False,
                rejection_reasons=rejections,
                risk_score=1.0,
                final_decision="REJECTED"
            )

        # Calculate risk score
        risk_score = self._calculate_risk_score(proposal, account_state, market_snapshot)

        # If risk_score > 0.7, flag for human review
        decision_level = "APPROVED" if risk_score < 0.7 else "HUMAN_REVIEW"

        return RiskApprovalDecision(
            approved=(decision_level == "APPROVED"),
            rejection_reasons=[],
            risk_score=risk_score,
            final_decision=decision_level
        )

    def _calculate_risk_score(self, proposal: TradeProposal,
                             account_state: AccountState,
                             market_snapshot: Dict) -> float:
        components = {
            'position_size': min(1.0, proposal.position_size_pct / 0.05) * 0.3,
            'daily_loss_proximity': min(1.0, float(abs(account_state.daily_pnl / self.max_daily_loss))) * 0.2,
            'correlation': proposal.portfolio_signal.max_correlated_exposure * 0.2,
            'confidence_inverse': (1.0 - proposal.overall_confidence) * 0.15,
            'volatility': min(1.0, proposal.regime_signal.volatility_level / 100) * 0.15,
        }
        return float(np.mean(list(components.values())))

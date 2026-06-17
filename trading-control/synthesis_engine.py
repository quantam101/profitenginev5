from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional
from datetime import datetime
import numpy as np

try:
    from .models import (
        TradeProposal, MarketSnapshot, TechnicalSignal, MicrostructureSignal,
        RegimeSignal, PortfolioSignal
    )
    from .agents_impl import (
        TechnicalAgent, MicrostructureAgent, RegimeAgent, PortfolioAgent
    )
    from .signal_correlation_analyzer import SignalCorrelationAnalyzer
except ImportError:
    from models import (
        TradeProposal, MarketSnapshot, TechnicalSignal, MicrostructureSignal,
        RegimeSignal, PortfolioSignal
    )
    from agents_impl import (
        TechnicalAgent, MicrostructureAgent, RegimeAgent, PortfolioAgent
    )
    from signal_correlation_analyzer import SignalCorrelationAnalyzer

class ProposalSynthesisEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.technical_agent = TechnicalAgent(config.get('agents', {}).get('technical', {}))
        self.microstructure_agent = MicrostructureAgent(config.get('agents', {}).get('microstructure', {}))
        self.regime_agent = RegimeAgent(config.get('agents', {}).get('regime', {}))
        self.portfolio_agent = PortfolioAgent(config.get('agents', {}).get('portfolio', {}))

        # Initialize signal correlation analyzer (rolling 20-trade window)
        self.correlation_analyzer = SignalCorrelationAnalyzer(window_size=20)

        # Track trade count for periodic correlation recalculation
        self.trade_count = 0
        self.correlation_update_interval = 20  # Recalculate every 20 trades
        self.correlation_threshold = 0.8  # Flag correlated failures above this threshold
        self.correlated_agent_penalty = 0.20  # Reduce correlated agents by 20%
        self.diverse_agent_boost = 0.10  # Boost diverse agents by 10%

        # Store dynamic weight adjustments
        self.dynamic_weights = None
        self.last_correlation_report = None

    def generate(self, market_snapshot: MarketSnapshot, account_equity: Decimal,
                 daily_pnl: Decimal, open_positions: list = None) -> Optional[TradeProposal]:
        """Merge all signals → single proposal."""

        open_positions = open_positions or []

        # STEP 1: Get all agent signals
        prices = np.array(market_snapshot.prices, dtype=float) if market_snapshot.prices else np.array([float(market_snapshot.last)])
        volumes = np.array(market_snapshot.volumes, dtype=float) if market_snapshot.volumes else np.array([market_snapshot.volume])

        technical = self.technical_agent.analyze(prices, volumes)
        microstructure = self.microstructure_agent.analyze(
            market_snapshot.orderbook,
            market_snapshot.trade_flow
        )
        regime = self.regime_agent.analyze(
            prices,
            market_snapshot.volatility,
            market_snapshot.state
        )

        proposed_trade = {
            'symbol': market_snapshot.symbol,
            'win_rate': technical.confidence,
            'avg_win_pct': 0.04,
            'avg_loss_pct': 0.02
        }

        portfolio = self.portfolio_agent.analyze(
            open_positions,
            proposed_trade,
            account_equity,
            daily_pnl
        )

        # STEP 2: Regime gate (short-circuit if regime forbids)
        if not regime.approved_to_trade:
            return None

        # STEP 3: Determine direction
        direction = "LONG" if technical.trend_alignment > 0.5 else "SHORT"

        # STEP 4: Smart entry limit price
        bid = Decimal(str(market_snapshot.bid))
        ask = Decimal(str(market_snapshot.ask))
        mid = (bid + ask) / 2

        if direction == "LONG":
            # Buy: set limit below ask
            entry_price = ask - (ask - bid) * Decimal('0.5')
        else:
            # Sell: set limit above bid
            entry_price = bid + (ask - bid) * Decimal('0.5')

        entry_price = entry_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # STEP 5: Risk placement
        volatility_factor = Decimal(str(1.0 + market_snapshot.volatility / 100))

        if direction == "LONG":
            stop_loss = entry_price * (Decimal('1.0') - Decimal('0.015') * volatility_factor)
            take_profit = entry_price * (Decimal('1.0') + Decimal('0.045') * volatility_factor)
        else:
            stop_loss = entry_price * (Decimal('1.0') + Decimal('0.015') * volatility_factor)
            take_profit = entry_price * (Decimal('1.0') - Decimal('0.045') * volatility_factor)

        stop_loss = stop_loss.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        take_profit = take_profit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # STEP 6: Position sizing
        position_size_pct = portfolio.position_size_kelly
        position_size_usd = account_equity * Decimal(str(position_size_pct))
        position_size_usd = position_size_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # STEP 7: Reward-to-risk
        if direction == "LONG":
            reward = take_profit - entry_price
            risk = entry_price - stop_loss
        else:
            reward = entry_price - take_profit
            risk = stop_loss - entry_price

        reward_risk = float(reward / risk) if risk > 0 else 0.0

        if reward_risk < 2.0:
            return None

        # STEP 8: Record signals in correlation analyzer
        self.trade_count += 1
        self.correlation_analyzer.record_trade(
            technical, microstructure, regime, portfolio
        )

        # STEP 8a: Periodic correlation recalculation every 20 trades
        if self.trade_count % self.correlation_update_interval == 0:
            self._update_dynamic_weights_from_correlation()

        # STEP 8b: Get diversity-adjusted confidence using dynamic weights
        diversity_confidence = self._get_weighted_confidence(
            technical, microstructure, regime, portfolio
        )

        # STEP 8c: Aggregate confidence with diversity adjustment
        base_confidence = np.mean([
            technical.confidence,
            microstructure.confidence,
            regime.regime_confidence,
            0.75  # Default portfolio confidence
        ])

        # Blend base confidence with diversity-adjusted signal
        confidence = 0.7 * base_confidence + 0.3 * diversity_confidence

        # STEP 9: Generate rationale with correlation insights
        rationale = self._generate_rationale(
            technical, microstructure, regime, portfolio, direction
        )

        # Add diversity warnings and correlated failure alerts if applicable
        corr_report = self.correlation_analyzer.generate_diversity_report()
        self.last_correlation_report = corr_report

        if corr_report['diversity_score'] < 0.4:
            rationale += " [DIVERSITY ALERT: Signal correlation is high]"

        # Alert if correlated failures detected at high threshold
        if corr_report['correlated_failures_detected'] > 0:
            high_correlation_failures = [
                f for f in corr_report['correlated_failures']
                if f['correlation'] > self.correlation_threshold
            ]
            if high_correlation_failures:
                failure_pairs = ', '.join(
                    f"{'-'.join(f['agent_pair'])}" for f in high_correlation_failures
                )
                rationale += f" [CORRELATED FAILURE ALERT: {failure_pairs} correlation > {self.correlation_threshold}]"

        # STEP 10: Build proposal
        proposal = TradeProposal(
            symbol=market_snapshot.symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size_usd=position_size_usd,
            position_size_pct=position_size_pct,
            time_in_force="DAY",
            order_type="LIMIT",
            technical_signal=technical,
            microstructure_signal=microstructure,
            regime_signal=regime,
            portfolio_signal=portfolio,
            overall_confidence=float(confidence),
            expected_reward_risk=reward_risk,
            rationale=rationale
        )

        return proposal

    def record_trade_outcome(self, outcome: int) -> None:
        """
        Record the outcome of the last proposed trade (1=win, 0=loss).
        Used by correlation analyzer to track performance.

        Args:
            outcome: 1 for winning trade, 0 for losing trade
        """
        if len(self.correlation_analyzer.signal_history["technical"]) > 0:
            # Update the last recorded trade with outcome
            self.correlation_analyzer.trade_outcomes.append(outcome)

    def get_correlation_analysis(self) -> Dict:
        """
        Get the full correlation analysis report for the current state.

        Returns:
            Dictionary containing correlation matrix, weights, and recommendations
        """
        return self.correlation_analyzer.generate_diversity_report()

    def _update_dynamic_weights_from_correlation(self) -> Dict[str, float]:
        """
        Recalculate correlation matrix every 20 trades and dynamically adjust agent weights.
        Penalizes correlated agents by 20% and boosts diverse agents by 10%.

        Returns:
            Updated dynamic weights dictionary
        """
        # Generate correlation report
        corr_report = self.correlation_analyzer.generate_diversity_report()

        # Get base correlation-adjusted weights from analyzer
        base_weights = self.correlation_analyzer.adjust_agent_weights(
            diversity_importance=0.6,
            performance_importance=0.4
        )

        # Detect agents involved in high-correlation failures (>0.8)
        correlated_agents = set()
        high_corr_failures = [
            f for f in corr_report.get('correlated_failures', [])
            if abs(f.get('correlation', 0)) > self.correlation_threshold
        ]

        for failure in high_corr_failures:
            agent_pair = failure.get('agent_pair', [])
            correlated_agents.update(agent_pair)

        # Identify diverse agents (low correlation with others)
        diverse_agents = set()
        corr_matrix = self.correlation_analyzer.correlation_matrix if self.correlation_analyzer.correlation_matrix is not None else np.eye(4)
        agent_names = self.correlation_analyzer.agent_names

        for i, agent_name in enumerate(agent_names):
            # Average absolute correlation with other agents
            other_corrs = []
            for j, other_name in enumerate(agent_names):
                if i != j:
                    other_corrs.append(abs(corr_matrix[i, j]))

            avg_corr_with_others = np.mean(other_corrs) if other_corrs else 0.0
            # Diverse if low avg correlation with others
            if avg_corr_with_others < 0.5:
                diverse_agents.add(agent_name)

        # Apply dynamic adjustments to base weights
        adjusted_weights = {}
        for agent_name, base_weight in base_weights.items():
            adjusted_weight = base_weight

            # Penalize correlated agents (reduce by 20%)
            if agent_name in correlated_agents:
                adjusted_weight *= (1.0 - self.correlated_agent_penalty)

            # Boost diverse agents (increase by 10%)
            if agent_name in diverse_agents:
                adjusted_weight *= (1.0 + self.diverse_agent_boost)

            adjusted_weights[agent_name] = adjusted_weight

        # Renormalize weights to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            for agent_name in adjusted_weights:
                adjusted_weights[agent_name] /= total_weight

        # Store dynamic weights for use in proposal synthesis
        self.dynamic_weights = adjusted_weights
        self.correlation_analyzer.agent_weights = adjusted_weights

        return adjusted_weights

    def _get_weighted_confidence(self,
                                technical: TechnicalSignal,
                                microstructure: MicrostructureSignal,
                                regime: RegimeSignal,
                                portfolio: PortfolioSignal) -> float:
        """
        Calculate weighted confidence using dynamic weights (or base weights if not yet computed).
        Incorporates correlation analysis and agent-specific confidence adjustments.

        Args:
            technical: Technical signal
            microstructure: Microstructure signal
            regime: Regime signal
            portfolio: Portfolio signal

        Returns:
            Weighted confidence score (0-1)
        """
        # Use dynamic weights if available, otherwise use base weights
        weights = self.dynamic_weights or self.correlation_analyzer.agent_weights

        signals = [
            technical.confidence,
            microstructure.confidence,
            regime.regime_confidence,
            0.75  # Portfolio default confidence
        ]

        agent_names = self.correlation_analyzer.agent_names

        # Calculate weighted confidence
        weighted_score = sum(
            signals[i] * weights[agent_names[i]]
            for i in range(len(agent_names))
        )

        return float(weighted_score)

    def _generate_rationale(self, technical: TechnicalSignal,
                           microstructure: MicrostructureSignal,
                           regime: RegimeSignal, portfolio: PortfolioSignal,
                           direction: str) -> str:
        reasons = []

        if technical.rsi_oversold_recovery > 0.7:
            reasons.append("RSI recovery from oversold")

        if technical.macd_bullish_cross > 0.7:
            reasons.append("MACD bullish crossover")

        if technical.trend_alignment > 0.7:
            reasons.append("Price above moving averages")

        if microstructure.liquidity_score > 0.7:
            reasons.append("Strong liquidity")

        if microstructure.bid_ask_imbalance > 0.1:
            reasons.append("Favorable order flow")

        rationale = f"{direction} setup: {', '.join(reasons)}"
        return rationale

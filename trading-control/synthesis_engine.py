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
except ImportError:
    from models import (
        TradeProposal, MarketSnapshot, TechnicalSignal, MicrostructureSignal,
        RegimeSignal, PortfolioSignal
    )
    from agents_impl import (
        TechnicalAgent, MicrostructureAgent, RegimeAgent, PortfolioAgent
    )

class ProposalSynthesisEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.technical_agent = TechnicalAgent(config.get('agents', {}).get('technical', {}))
        self.microstructure_agent = MicrostructureAgent(config.get('agents', {}).get('microstructure', {}))
        self.regime_agent = RegimeAgent(config.get('agents', {}).get('regime', {}))
        self.portfolio_agent = PortfolioAgent(config.get('agents', {}).get('portfolio', {}))

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

        # STEP 8: Aggregate confidence
        confidence = np.mean([
            technical.confidence,
            microstructure.confidence,
            regime.regime_confidence,
            0.75  # Default portfolio confidence
        ])

        # STEP 9: Generate rationale
        rationale = self._generate_rationale(
            technical, microstructure, regime, portfolio, direction
        )

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

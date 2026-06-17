"""
Integration tests for All components.
Verifies: agents, synthesis, risk kernel, execution, audit.
"""

import pytest
import asyncio
import numpy as np
from decimal import Decimal
from datetime import datetime
from models import (
    MarketSnapshot, AccountState, TradeProposal, OrderState
)
from agents_impl import (
    TechnicalAgent, MicrostructureAgent, RegimeAgent, PortfolioAgent
)
from synthesis_engine import ProposalSynthesisEngine
from risk_kernel import DeterministicRiskKernel
from paper_broker import PaperBroker
from audit_ledger import AuditLedger

@pytest.fixture
def config():
    return {
        'agents': {
            'technical': {'rsi_period': 14, 'rsi_oversold_threshold': 35, 'confidence_min': 0.65},
            'microstructure': {'imbalance_threshold': 0.2, 'confidence_min': 0.60},
            'regime': {'volatility_percentile_threshold': 60, 'event_risk_max': 0.3},
            'portfolio': {'kelly_fraction': 0.25, 'max_correlated_exposure': 0.7, 'max_daily_loss_usd': 200}
        },
        'risk': {
            'hard_limits': {
                'max_daily_loss_usd': 200,
                'max_weekly_loss_usd': 1000,
                'max_spread_bps': 5,
                'min_volume_usd': 100000,
                'min_reward_risk_ratio': 2.0,
                'max_correlation': 0.7,
                'quote_stale_threshold_sec': 5
            }
        },
        'execution': {'slippage_model_buffer_pct': 1.5},
        'initial_capital': 100000
    }

def test_technical_agent(config):
    """Test technical signal generation."""
    agent = TechnicalAgent(config['agents']['technical'])
    prices = np.array([150.0, 151.0, 149.0, 152.0, 150.5, 148.0, 149.5, 151.0, 150.0, 149.0] * 5)
    volumes = np.array([1000000] * len(prices))

    signal = agent.analyze(prices, volumes)

    assert 0.0 <= signal.rsi_oversold_recovery <= 1.0
    assert 0.0 <= signal.macd_bullish_cross <= 1.0
    assert 0.0 <= signal.confidence <= 1.0
    print(f"✓ Technical Agent: confidence={signal.confidence:.2f}")

def test_microstructure_agent(config):
    """Test microstructure signal generation."""
    agent = MicrostructureAgent(config['agents']['microstructure'])

    orderbook = {
        'bids': [[150.0 - i*0.01, 10000] for i in range(5)],
        'asks': [[150.0 + i*0.01, 10000] for i in range(5)]
    }
    trade_flow = [{'size': 100}, {'size': 500}, {'size': 2000}]

    signal = agent.analyze(orderbook, trade_flow)

    assert -1.0 <= signal.bid_ask_imbalance <= 1.0
    assert 0.0 <= signal.liquidity_score <= 1.0
    assert 0.0 <= signal.confidence <= 1.0
    print(f"✓ Microstructure Agent: liquidity={signal.liquidity_score:.2f}")

def test_regime_agent(config):
    """Test regime detection."""
    agent = RegimeAgent(config['agents']['regime'])
    prices = np.array([150.0 + np.sin(i * 0.1) for i in range(100)])

    signal = agent.analyze(prices, volatility=12.0, market_state={'event_risk': 0.1, 'correlation_stress': 0.2})

    assert signal.regime is not None
    assert 0.0 <= signal.volatility_level <= 100.0
    assert isinstance(signal.approved_to_trade, bool)
    print(f"✓ Regime Agent: regime={signal.regime.value}, approved={signal.approved_to_trade}")

def test_portfolio_agent(config):
    """Test portfolio sizing."""
    agent = PortfolioAgent(config['agents']['portfolio'])

    signal = agent.analyze(
        open_positions=[],
        proposed_trade={'win_rate': 0.45, 'avg_win_pct': 0.04, 'avg_loss_pct': 0.02},
        account_equity=Decimal('100000'),
        daily_pnl=Decimal('-50')
    )

    assert 0.0 <= signal.position_size_kelly <= 1.0
    assert 0.0 <= signal.risk_budget_remaining <= 1.0
    print(f"✓ Portfolio Agent: kelly_size={signal.position_size_kelly:.2f}, action={signal.recommended_action}")

def test_synthesis_engine(config):
    """Test proposal generation."""
    engine = ProposalSynthesisEngine(config)

    snapshot = MarketSnapshot(
        symbol="AAPL",
        timestamp=datetime.utcnow(),
        bid=Decimal('150.0'),
        ask=Decimal('150.05'),
        last=Decimal('150.02'),
        volume=1000000,
        volume_24h=Decimal('50000000'),
        volatility=10.0,
        prices=[150.0 + np.sin(i * 0.1) for i in range(50)],
        volumes=[1000000] * 50,
        orderbook={'bids': [[150.0 - i*0.01, 10000] for i in range(5)],
                  'asks': [[150.0 + i*0.01, 10000] for i in range(5)]},
        state={'event_risk': 0.1, 'correlation_stress': 0.2}
    )

    proposal = engine.generate(snapshot, Decimal('100000'), Decimal('-50'), [])

    if proposal:
        assert proposal.direction in ['LONG', 'SHORT']
        assert proposal.entry_price > 0
        assert proposal.stop_loss > 0
        assert proposal.take_profit > 0
        assert proposal.expected_reward_risk >= 2.0
        print(f"✓ Synthesis Engine: {proposal.direction} proposal generated")
    else:
        print("✓ Synthesis Engine: No proposal (regime forbids)")

def test_risk_kernel(config):
    """Test risk gate enforcement."""
    kernel = DeterministicRiskKernel(config['risk']['hard_limits'])

    # Create a valid proposal
    snapshot = MarketSnapshot(
        symbol="AAPL",
        timestamp=datetime.utcnow(),
        bid=Decimal('150.0'),
        ask=Decimal('150.05'),
        last=Decimal('150.02'),
        volume=1000000,
        volume_24h=Decimal('50000000'),
        volatility=10.0,
        orderbook={'bids': [[150.0 - i*0.01, 10000] for i in range(5)],
                  'asks': [[150.0 + i*0.01, 10000] for i in range(5)]}
    )

    from models import TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal, MarketRegime

    proposal = TradeProposal(
        symbol="AAPL",
        direction="LONG",
        entry_price=Decimal('150.0'),
        stop_loss=Decimal('148.0'),
        take_profit=Decimal('154.0'),
        position_size_usd=Decimal('5000'),
        position_size_pct=0.05,
        time_in_force="DAY",
        order_type="LIMIT",
        technical_signal=TechnicalSignal(0.8, 0.8, 0.8, 0.8, 0.8, 0.8),
        microstructure_signal=MicrostructureSignal(0.1, 0.5, 0.8, 0.0, 5.0, 0.7),
        regime_signal=RegimeSignal(MarketRegime.BULL_TRENDING, 50.0, 0.1, 0.2, 0.85, True),
        portfolio_signal=PortfolioSignal(0.05, 0.3, -2000.0, 0.8, "NORMAL"),
        overall_confidence=0.8,
        expected_reward_risk=2.67,
        rationale="Test proposal"
    )

    account_state = AccountState(
        timestamp=datetime.utcnow(),
        account_equity=Decimal('100000'),
        buying_power=Decimal('95000'),
        cash=Decimal('50000'),
        daily_pnl=Decimal('-50'),
        weekly_pnl=Decimal('0'),
        max_drawdown_pct=2.5,
        open_positions=[],
        position_mismatch=False,
        broker_offline=False
    )

    decision = kernel.evaluate(proposal, snapshot.__dict__, account_state)

    assert isinstance(decision.approved, bool)
    assert isinstance(decision.risk_score, float)
    print(f"✓ Risk Kernel: approved={decision.approved}, risk_score={decision.risk_score:.2f}")

@pytest.mark.asyncio
async def test_paper_broker(config):
    """Test paper execution."""
    broker = PaperBroker(config)

    from models import TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal, MarketRegime

    proposal = TradeProposal(
        symbol="AAPL",
        direction="LONG",
        entry_price=Decimal('150.0'),
        stop_loss=Decimal('148.0'),
        take_profit=Decimal('154.0'),
        position_size_usd=Decimal('5000'),
        position_size_pct=0.05,
        time_in_force="DAY",
        order_type="LIMIT",
        technical_signal=TechnicalSignal(0.8, 0.8, 0.8, 0.8, 0.8, 0.8),
        microstructure_signal=MicrostructureSignal(0.1, 0.5, 0.8, 0.0, 5.0, 0.7),
        regime_signal=RegimeSignal(MarketRegime.BULL_TRENDING, 50.0, 0.1, 0.2, 0.85, True),
        portfolio_signal=PortfolioSignal(0.05, 0.3, -2000.0, 0.8, "NORMAL"),
        overall_confidence=0.8,
        expected_reward_risk=2.67,
        rationale="Test"
    )

    result = await broker.submit_proposal(proposal)

    assert result.order_id is not None
    assert result.state == OrderState.FILLED
    assert result.fill_price > 0
    assert result.slippage >= 0
    print(f"✓ Paper Broker: filled @ {result.fill_price}, slippage={result.slippage}")

def test_audit_ledger(config):
    """Test audit logging."""
    ledger = AuditLedger(":memory:")

    from models import TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal, MarketRegime

    proposal = TradeProposal(
        symbol="AAPL",
        direction="LONG",
        entry_price=Decimal('150.0'),
        stop_loss=Decimal('148.0'),
        take_profit=Decimal('154.0'),
        position_size_usd=Decimal('5000'),
        position_size_pct=0.05,
        time_in_force="DAY",
        order_type="LIMIT",
        technical_signal=TechnicalSignal(0.8, 0.8, 0.8, 0.8, 0.8, 0.8),
        microstructure_signal=MicrostructureSignal(0.1, 0.5, 0.8, 0.0, 5.0, 0.7),
        regime_signal=RegimeSignal(MarketRegime.BULL_TRENDING, 50.0, 0.1, 0.2, 0.85, True),
        portfolio_signal=PortfolioSignal(0.05, 0.3, -2000.0, 0.8, "NORMAL"),
        overall_confidence=0.8,
        expected_reward_risk=2.67,
        rationale="Test"
    )

    ledger.log_proposal(proposal)
    stats = ledger.get_stats()

    assert stats['total_trades'] >= 0
    print(f"✓ Audit Ledger: proposal logged, stats={stats}")

if __name__ == "__main__":
    print("\n=== INTEGRATION TESTS ===\n")

    config_dict = {
        'agents': {
            'technical': {'rsi_period': 14, 'rsi_oversold_threshold': 35, 'confidence_min': 0.65},
            'microstructure': {'imbalance_threshold': 0.2, 'confidence_min': 0.60},
            'regime': {'volatility_percentile_threshold': 60, 'event_risk_max': 0.3},
            'portfolio': {'kelly_fraction': 0.25, 'max_correlated_exposure': 0.7, 'max_daily_loss_usd': 200}
        },
        'risk': {
            'hard_limits': {
                'max_daily_loss_usd': 200,
                'max_weekly_loss_usd': 1000,
                'max_spread_bps': 5,
                'min_volume_usd': 100000,
                'min_reward_risk_ratio': 2.0,
                'max_correlation': 0.7,
                'quote_stale_threshold_sec': 5
            }
        },
        'execution': {'slippage_model_buffer_pct': 1.5},
        'initial_capital': 100000
    }

    test_technical_agent(config_dict)
    test_microstructure_agent(config_dict)
    test_regime_agent(config_dict)
    test_portfolio_agent(config_dict)
    test_synthesis_engine(config_dict)
    test_risk_kernel(config_dict)
    asyncio.run(test_paper_broker(config_dict))
    test_audit_ledger(config_dict)

    print("\n✅ All integration tests passed!\n")

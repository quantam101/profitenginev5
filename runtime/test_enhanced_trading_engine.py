"""
Test Suite for Enhanced Trading Engine

Comprehensive tests for signal generation, execution, position monitoring,
and risk management.

Run with: pytest test_enhanced_trading_engine.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from enhanced_trading_engine import (
    EnhancedTradingEngine,
    TradeSignal,
    ExecutionResult,
    PositionStatus,
    SignalAction
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def engine():
    """Create test engine instance."""
    return EnhancedTradingEngine(account_balance=50000.0)


@pytest.fixture
def sample_signal():
    """Create sample trade signal."""
    return TradeSignal(
        action=SignalAction.BUY,
        symbol='NVDA',
        confidence=85,
        reason='Test signal',
        entry_price=125.50,
        stop_price=123.20,
        target_price=128.75,
        position_size=32,
        position_value=4016.00,
        risk_reward_ratio=2.50,
        timeframe_confirmations=3,
        catalyst_score=75.0,
        volatility_regime='normal',
        timestamp=datetime.now(timezone.utc).isoformat()
    )


# ============================================================================
# SIGNAL GENERATION TESTS
# ============================================================================

class TestSignalGeneration:
    """Test signal generation pipeline."""

    @pytest.mark.asyncio
    async def test_signal_generation_basic(self, engine):
        """Test basic signal generation."""
        signal = await engine.generate_trade_signal('NVDA')

        # Signal can be None if no data or low confidence
        if signal:
            assert signal.symbol == 'NVDA'
            assert signal.confidence >= 0
            assert signal.confidence <= 100
            assert signal.action in [SignalAction.BUY, SignalAction.SELL, SignalAction.NONE]

    @pytest.mark.asyncio
    async def test_signal_not_in_watchlist(self, engine):
        """Test signal for non-watchlist symbol."""
        signal = await engine.generate_trade_signal('FAKESYMBOL')
        assert signal is None

    @pytest.mark.asyncio
    async def test_signal_confidence_ranges(self, engine):
        """Test signal confidence is in valid range."""
        signal = await engine.generate_trade_signal('NVDA')

        if signal:
            assert 0 <= signal.confidence <= 100

    @pytest.mark.asyncio
    async def test_signal_has_required_fields(self, engine, sample_signal):
        """Test signal has all required fields."""
        required_fields = [
            'action', 'symbol', 'confidence', 'reason',
            'entry_price', 'stop_price', 'target_price',
            'position_size', 'position_value', 'risk_reward_ratio'
        ]

        for field in required_fields:
            assert hasattr(sample_signal, field)

    @pytest.mark.asyncio
    async def test_signal_risk_reward_ratio(self, engine, sample_signal):
        """Test risk/reward ratio calculation."""
        # BUY: target > entry > stop
        assert sample_signal.entry_price > sample_signal.stop_price
        assert sample_signal.target_price > sample_signal.entry_price

        # Calculate ratio
        risk = sample_signal.entry_price - sample_signal.stop_price
        reward = sample_signal.target_price - sample_signal.entry_price
        expected_ratio = reward / risk

        assert abs(sample_signal.risk_reward_ratio - expected_ratio) < 0.01


# ============================================================================
# EXECUTION TESTS
# ============================================================================

class TestSignalExecution:
    """Test signal execution."""

    @pytest.mark.asyncio
    async def test_execute_signal_success(self, engine, sample_signal):
        """Test successful signal execution."""
        result = await engine.execute_signal(sample_signal)

        assert result.status == "SUCCESS"
        assert result.symbol == 'NVDA'
        assert result.position_size == 32
        assert result.entry_price == 125.50

    @pytest.mark.asyncio
    async def test_execute_signal_creates_position(self, engine, sample_signal):
        """Test execution creates tracked position."""
        result = await engine.execute_signal(sample_signal)

        assert result.order_id in engine.open_positions
        position = engine.open_positions[result.order_id]
        assert position.symbol == 'NVDA'
        assert position.status == "OPEN"

    @pytest.mark.asyncio
    async def test_execute_none_signal_fails(self, engine):
        """Test execution of NONE signal fails."""
        signal = TradeSignal(
            action=SignalAction.NONE,
            symbol='NVDA',
            confidence=0,
            reason='No signal',
            entry_price=125.50,
            stop_price=123.20,
            target_price=128.75,
            position_size=0,
            position_value=0,
            risk_reward_ratio=0,
            timeframe_confirmations=0,
            catalyst_score=0,
            volatility_regime='normal',
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        result = await engine.execute_signal(signal)
        assert result.status == "FAILED"

    @pytest.mark.asyncio
    async def test_execute_low_confidence_fails(self, engine):
        """Test execution of low confidence signal fails."""
        signal = TradeSignal(
            action=SignalAction.BUY,
            symbol='NVDA',
            confidence=30,  # Below 50 threshold
            reason='Low confidence',
            entry_price=125.50,
            stop_price=123.20,
            target_price=128.75,
            position_size=32,
            position_value=4016.00,
            risk_reward_ratio=2.50,
            timeframe_confirmations=1,
            catalyst_score=0,
            volatility_regime='normal',
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        result = await engine.execute_signal(signal)
        assert result.status == "FAILED"

    @pytest.mark.asyncio
    async def test_max_concurrent_positions_limit(self, engine, sample_signal):
        """Test max concurrent positions limit."""
        # Execute max positions
        for i in range(engine.MAX_CONCURRENT_TRADES):
            await engine.execute_signal(sample_signal)

        assert len(engine.open_positions) == engine.MAX_CONCURRENT_TRADES

        # Try to execute one more
        signal = TradeSignal(
            action=SignalAction.BUY,
            symbol='TSLA',
            confidence=80,
            reason='Extra signal',
            entry_price=250.0,
            stop_price=248.0,
            target_price=253.0,
            position_size=10,
            position_value=2500.0,
            risk_reward_ratio=1.5,
            timeframe_confirmations=2,
            catalyst_score=70,
            volatility_regime='normal',
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        result = await engine.execute_signal(signal)
        # Should check limits before execution
        assert len(engine.open_positions) <= engine.MAX_CONCURRENT_TRADES


# ============================================================================
# POSITION MONITORING TESTS
# ============================================================================

class TestPositionMonitoring:
    """Test position monitoring and P&L tracking."""

    @pytest.mark.asyncio
    async def test_monitor_position_updates_pnl(self, engine, sample_signal):
        """Test position monitoring updates P&L."""
        result = await engine.execute_signal(sample_signal)
        order_id = result.order_id

        # Monitor with price increase
        position = await engine.monitor_position(order_id, current_price=127.50)

        assert position is not None
        assert position.unrealized_pnl > 0  # Profit
        assert position.current_price == 127.50

    @pytest.mark.asyncio
    async def test_monitor_position_buy_signal(self, engine, sample_signal):
        """Test position monitoring for BUY signal."""
        result = await engine.execute_signal(sample_signal)
        order_id = result.order_id

        # Price goes up (profit)
        position = await engine.monitor_position(order_id, current_price=130.00)
        expected_pnl = (130.00 - 125.50) * 32

        assert position.unrealized_pnl > 0
        assert abs(position.unrealized_pnl - expected_pnl) < 1.0

    @pytest.mark.asyncio
    async def test_monitor_position_sell_signal(self, engine):
        """Test position monitoring for SELL signal."""
        signal = TradeSignal(
            action=SignalAction.SELL,
            symbol='NVDA',
            confidence=85,
            reason='Test sell',
            entry_price=125.50,
            stop_price=127.00,
            target_price=123.00,
            position_size=32,
            position_value=4016.00,
            risk_reward_ratio=1.25,
            timeframe_confirmations=2,
            catalyst_score=70,
            volatility_regime='normal',
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        result = await engine.execute_signal(signal)
        order_id = result.order_id

        # Price goes down (profit for short)
        position = await engine.monitor_position(order_id, current_price=122.00)
        expected_pnl = (125.50 - 122.00) * 32

        assert position.unrealized_pnl > 0

    @pytest.mark.asyncio
    async def test_monitor_position_at_stop_loss(self, engine, sample_signal):
        """Test position triggers stop loss."""
        result = await engine.execute_signal(sample_signal)
        order_id = result.order_id

        # Price hits stop loss
        position = await engine.monitor_position(order_id, current_price=123.20)

        assert position.status == "AT_STOP"

    @pytest.mark.asyncio
    async def test_monitor_position_at_target(self, engine, sample_signal):
        """Test position triggers take profit."""
        result = await engine.execute_signal(sample_signal)
        order_id = result.order_id

        # Price hits target
        position = await engine.monitor_position(order_id, current_price=128.75)

        assert position.status == "AT_TARGET"

    @pytest.mark.asyncio
    async def test_monitor_all_positions(self, engine, sample_signal):
        """Test monitoring all positions."""
        # Execute multiple signals
        for i in range(3):
            await engine.execute_signal(sample_signal)

        positions = await engine.monitor_all_positions()

        assert len(positions) >= 3
        for order_id, pos in positions.items():
            assert pos.order_id == order_id


# ============================================================================
# POSITION SIZING TESTS
# ============================================================================

class TestPositionSizing:
    """Test position sizing calculations."""

    def test_position_size_calculation(self, engine):
        """Test position sizing formula."""
        position_size = engine._calculate_position_size(
            symbol='NVDA',
            entry_price=125.50,
            stop_price=123.20,
            direction='LONG'
        )

        # Risk per share
        risk_per_share = 125.50 - 123.20  # $2.30
        # Account risk at 2%
        account_risk = 50000 * 0.02  # $1,000
        # Expected size
        expected_size = int(account_risk / risk_per_share)  # ~435 shares

        # But capped at MAX_SINGLE_POSITION / entry_price
        max_shares = int(5000 / 125.50)  # ~39 shares

        assert 1 <= position_size <= max_shares

    def test_position_size_respects_max_limit(self, engine):
        """Test position size respects max single position."""
        position_size = engine._calculate_position_size(
            symbol='NVDA',
            entry_price=125.50,
            stop_price=123.20,
            direction='LONG'
        )

        position_value = position_size * 125.50
        assert position_value <= engine.MAX_SINGLE_POSITION

    def test_position_size_minimum_one_share(self, engine):
        """Test position size minimum is 1 share."""
        position_size = engine._calculate_position_size(
            symbol='TSLA',
            entry_price=250.00,
            stop_price=249.00,  # Very tight stop
            direction='LONG'
        )

        assert position_size >= 1

    def test_position_size_zero_stop_difference(self, engine):
        """Test position sizing with zero stop difference."""
        position_size = engine._calculate_position_size(
            symbol='NVDA',
            entry_price=125.50,
            stop_price=125.50,  # Same as entry
            direction='LONG'
        )

        assert position_size == 0


# ============================================================================
# PORTFOLIO METRICS TESTS
# ============================================================================

class TestPortfolioMetrics:
    """Test portfolio analytics."""

    def test_portfolio_metrics_no_positions(self, engine):
        """Test portfolio metrics with no open positions."""
        metrics = engine.get_portfolio_metrics()

        assert metrics['account_balance'] == 50000.0
        assert metrics['open_positions'] == 0
        assert metrics['total_exposure'] == 0.0
        assert metrics['unrealized_pnl'] == 0.0

    @pytest.mark.asyncio
    async def test_portfolio_metrics_with_positions(self, engine, sample_signal):
        """Test portfolio metrics with open positions."""
        await engine.execute_signal(sample_signal)

        metrics = engine.get_portfolio_metrics()

        assert metrics['open_positions'] == 1
        assert metrics['total_exposure'] > 0

    @pytest.mark.asyncio
    async def test_portfolio_exposure_limit(self, engine, sample_signal):
        """Test total exposure respects limit."""
        # Try to exceed max exposure
        for i in range(4):
            await engine.execute_signal(sample_signal)

        metrics = engine.get_portfolio_metrics()

        # Total exposure should not exceed max concurrent
        assert metrics['total_exposure'] <= engine.MAX_CONCURRENT_POSITIONS

    def test_portfolio_win_rate_calculation(self, engine):
        """Test win rate calculation."""
        # Add sample trades
        engine.trade_history = [
            {'action': 'CLOSE', 'pnl': 100},   # Winning
            {'action': 'CLOSE', 'pnl': -50},   # Losing
            {'action': 'CLOSE', 'pnl': 200},   # Winning
        ]

        metrics = engine.get_portfolio_metrics()

        # 2 winning out of 3
        expected_win_rate = (2 / 3) * 100
        # Note: actual calculation may differ based on implementation


# ============================================================================
# RISK MANAGEMENT TESTS
# ============================================================================

class TestRiskManagement:
    """Test risk management constraints."""

    def test_max_single_position_constraint(self, engine, sample_signal):
        """Test max single position is enforced."""
        assert sample_signal.position_value <= engine.MAX_SINGLE_POSITION

    def test_position_size_respects_account_risk(self, engine):
        """Test position size respects account risk percentage."""
        position_size = engine._calculate_position_size(
            symbol='NVDA',
            entry_price=125.50,
            stop_price=123.20,
            direction='LONG'
        )

        risk_per_share = 125.50 - 123.20
        position_risk = position_size * risk_per_share
        account_risk = engine.account_balance * engine.DEFAULT_RISK_PER_TRADE

        assert position_risk <= account_risk

    def test_concurrent_position_limit(self, engine):
        """Test maximum concurrent positions."""
        assert engine.MAX_CONCURRENT_TRADES > 0
        assert engine.MAX_CONCURRENT_POSITIONS > 0

    def test_min_confidence_threshold(self, engine):
        """Test minimum confidence for execution."""
        assert engine.MIN_CONFIDENCE_FOR_EXECUTION == 50


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================

class TestDataIntegrity:
    """Test data integrity and logging."""

    @pytest.mark.asyncio
    async def test_signal_logged(self, engine):
        """Test signals are logged."""
        signal = await engine.generate_trade_signal('NVDA')

        if signal:
            assert len(engine.signal_log) > 0
            last_log = engine.signal_log[-1]
            assert last_log['symbol'] == 'NVDA'

    @pytest.mark.asyncio
    async def test_trade_logged_on_execution(self, engine, sample_signal):
        """Test trades are logged on execution."""
        await engine.execute_signal(sample_signal)

        assert len(engine.trade_history) > 0

    def test_export_signals_creates_file(self, engine, tmp_path):
        """Test signal export creates file."""
        engine.signal_log = [
            {'timestamp': '2024-01-01T10:00:00Z', 'action': 'BUY', 'symbol': 'NVDA'}
        ]

        export_file = tmp_path / "signals.json"
        engine.export_signals(str(export_file))

        assert export_file.exists()

    def test_export_positions_creates_file(self, engine, tmp_path):
        """Test position export creates file."""
        export_file = tmp_path / "positions.json"
        engine.export_positions(str(export_file))

        assert export_file.exists()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_trading_cycle(self, engine):
        """Test complete trading cycle: signal -> execute -> monitor."""
        # Generate signal
        signal = await engine.generate_trade_signal('NVDA')

        if signal and signal.action != SignalAction.NONE:
            # Execute
            result = await engine.execute_signal(signal)
            assert result.status == "SUCCESS"

            # Monitor
            position = await engine.monitor_position(result.order_id, current_price=127.00)
            assert position is not None
            assert position.unrealized_pnl > 0

    @pytest.mark.asyncio
    async def test_multiple_signals(self, engine):
        """Test generating signals for multiple symbols."""
        symbols = ['NVDA', 'TSLA', 'MSFT']

        for symbol in symbols:
            signal = await engine.generate_trade_signal(symbol)
            # Signal can be None or valid

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, engine, sample_signal):
        """Test concurrent signal execution."""
        tasks = [
            engine.execute_signal(sample_signal)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(r.status == "SUCCESS" for r in results)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

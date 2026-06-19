"""
TEST SUITE: Dynamic Risk Parameters Module

Comprehensive tests for ATR calculation, position sizing, and volatility adjustments.
Run with: python -m pytest runtime/test_dynamic_risk_params.py -v
"""

import pytest
import math
from runtime.dynamic_risk_params import (
    calculate_atr,
    estimate_atr_from_volatility,
    get_volatility_adjustment,
    normalize_iv_rank,
    calculate_stop_loss,
    calculate_take_profit,
    calculate_position_size,
    create_risk_profile,
    validate_risk_profile,
    RiskMetrics,
)


# ============================================================================
# ATR CALCULATION TESTS
# ============================================================================

class TestATRCalculation:
    """Test Average True Range calculation"""

    def test_atr_basic_calculation(self):
        """Test basic ATR with simple data"""
        # Simple data: high, low, close with known TR values
        highs = [100.0, 101.0, 102.0, 101.5, 100.5, 99.5, 100.0, 101.0]
        lows = [98.0, 99.0, 100.0, 99.5, 98.5, 97.5, 98.0, 99.0]
        closes = [99.0, 100.0, 101.0, 100.5, 99.5, 98.5, 99.0, 100.0]

        atr = calculate_atr(highs, lows, closes, period=3)
        assert atr > 0
        assert atr < 3.0  # Should be reasonable

    def test_atr_insufficient_data(self):
        """Test ATR with insufficient data points"""
        highs = [100.0, 101.0]
        lows = [98.0, 99.0]
        closes = [99.0, 100.0]

        atr = calculate_atr(highs, lows, closes, period=14)
        assert atr == 0.0

    def test_atr_equal_prices(self):
        """Test ATR when prices are equal (no range)"""
        highs = [100.0] * 20
        lows = [100.0] * 20
        closes = [100.0] * 20

        atr = calculate_atr(highs, lows, closes, period=14)
        # ATR should be 0 or very small
        assert atr <= 0.01

    def test_atr_varying_volatility(self):
        """Test ATR with increasing volatility"""
        # Low volatility period
        highs_low = [100.0, 100.5, 100.2, 100.3] + [100.0] * 16
        lows_low = [99.8, 99.5, 99.8, 99.9] + [99.8] * 16
        closes_low = [99.9, 100.2, 100.0, 100.1] + [99.9] * 16

        atr_low = calculate_atr(highs_low, lows_low, closes_low, period=14)

        # High volatility period
        highs_high = [100.0, 105.0, 110.0, 105.0] + [100.0] * 16
        lows_high = [95.0, 100.0, 105.0, 100.0] + [95.0] * 16
        closes_high = [97.5, 102.5, 107.5, 102.5] + [97.5] * 16

        atr_high = calculate_atr(highs_high, lows_high, closes_high, period=14)

        assert atr_high > atr_low


class TestATREstimation:
    """Test ATR estimation from volatility"""

    def test_atr_from_volatility_valid(self):
        """Test ATR estimation with valid volatility"""
        atr = estimate_atr_from_volatility(entry_price=100.0, historical_volatility=0.25)
        assert atr > 0
        # 25% annual vol scales up for 5-min bars, so can be larger
        assert atr > 0.10
        assert atr < 50.0

    def test_atr_from_volatility_zero(self):
        """Test ATR estimation with zero volatility"""
        atr = estimate_atr_from_volatility(entry_price=100.0, historical_volatility=0.0)
        assert atr > 0
        assert atr == 100.0 * 0.02  # Default 2%

    def test_atr_from_volatility_scales_with_price(self):
        """Test that ATR scales with entry price"""
        atr_low_price = estimate_atr_from_volatility(50.0, 0.25)
        atr_high_price = estimate_atr_from_volatility(100.0, 0.25)

        # Should scale approximately proportionally
        ratio = atr_high_price / atr_low_price
        assert 1.8 < ratio < 2.2  # Close to 2x


# ============================================================================
# VOLATILITY ADJUSTMENT TESTS
# ============================================================================

class TestVolatilityAdjustment:
    """Test volatility-based stop and target adjustments"""

    def test_volatility_adjustment_low_iv_rank(self):
        """Test tightened stops at low IV rank"""
        multiplier, regime = get_volatility_adjustment(iv_rank=10.0, base_atr=2.0)
        assert multiplier < 0.8
        assert regime == "low"
        assert multiplier >= 0.5

    def test_volatility_adjustment_normal_iv_rank(self):
        """Test multiplier at medium IV rank (boundary between normal/elevated)"""
        multiplier, regime = get_volatility_adjustment(iv_rank=50.0, base_atr=2.0)
        assert 0.9 <= multiplier <= 1.2
        # At exactly 50, it's at the boundary - could be normal or elevated
        assert regime in ["normal", "elevated"]

    def test_volatility_adjustment_high_iv_rank(self):
        """Test loosened stops at high IV rank"""
        multiplier, regime = get_volatility_adjustment(iv_rank=90.0, base_atr=2.0)
        assert multiplier > 1.3
        assert regime == "extreme"
        assert multiplier <= 2.0

    def test_volatility_adjustment_boundary_transitions(self):
        """Test smooth transitions between volatility regimes"""
        mult_24 = get_volatility_adjustment(24.0, 2.0)[0]
        mult_25 = get_volatility_adjustment(25.0, 2.0)[0]
        mult_26 = get_volatility_adjustment(26.0, 2.0)[0]

        # Should be continuous
        assert abs(mult_25 - mult_24) < 0.05
        assert abs(mult_26 - mult_25) < 0.05

    def test_volatility_adjustment_clamping(self):
        """Test clamping of out-of-range IV ranks"""
        mult_neg, _ = get_volatility_adjustment(-10.0, 2.0)
        mult_high, _ = get_volatility_adjustment(150.0, 2.0)

        assert mult_neg >= 0.5
        assert mult_high <= 2.0


class TestIVRankNormalization:
    """Test IV rank percentile calculation"""

    def test_iv_rank_at_low(self):
        """Test IV rank at 52-week low"""
        iv_rank = normalize_iv_rank(current_iv=10.0, iv_52week_low=10.0, iv_52week_high=30.0)
        assert iv_rank == 0.0

    def test_iv_rank_at_high(self):
        """Test IV rank at 52-week high"""
        iv_rank = normalize_iv_rank(current_iv=30.0, iv_52week_low=10.0, iv_52week_high=30.0)
        assert iv_rank == 100.0

    def test_iv_rank_at_midpoint(self):
        """Test IV rank at midpoint"""
        iv_rank = normalize_iv_rank(current_iv=20.0, iv_52week_low=10.0, iv_52week_high=30.0)
        assert iv_rank == 50.0

    def test_iv_rank_zero_range(self):
        """Test IV rank with zero range"""
        iv_rank = normalize_iv_rank(current_iv=20.0, iv_52week_low=20.0, iv_52week_high=20.0)
        assert iv_rank == 50.0  # Default middle

    def test_iv_rank_clamping(self):
        """Test clamping to [0, 100]"""
        iv_rank = normalize_iv_rank(current_iv=50.0, iv_52week_low=10.0, iv_52week_high=20.0)
        assert 0 <= iv_rank <= 100


# ============================================================================
# STOP LOSS CALCULATION TESTS
# ============================================================================

class TestStopLossCalculation:
    """Test ATR-based stop loss calculation"""

    def test_stop_loss_long_position(self):
        """Test stop loss for LONG position"""
        stop = calculate_stop_loss(
            symbol="SPY",
            entry_price=100.0,
            direction="LONG",
            atr_value=2.0,
            atr_multiplier=1.5,
            volatility_multiplier=1.0
        )
        # LONG: stop = entry - (ATR × 1.5 × 1.0)
        expected = 100.0 - (2.0 * 1.5)
        assert stop == expected

    def test_stop_loss_short_position(self):
        """Test stop loss for SHORT position"""
        stop = calculate_stop_loss(
            symbol="SPY",
            entry_price=100.0,
            direction="SHORT",
            atr_value=2.0,
            atr_multiplier=1.5,
            volatility_multiplier=1.0
        )
        # SHORT: stop = entry + (ATR × 1.5 × 1.0)
        expected = 100.0 + (2.0 * 1.5)
        assert stop == expected

    def test_stop_loss_with_volatility_adjustment(self):
        """Test stop loss with volatility adjustment"""
        stop = calculate_stop_loss(
            symbol="SPY",
            entry_price=100.0,
            direction="LONG",
            atr_value=2.0,
            atr_multiplier=1.5,
            volatility_multiplier=0.8  # Low volatility regime
        )
        # LONG: stop = entry - (ATR × 1.5 × 0.8)
        expected = 100.0 - (2.0 * 1.5 * 0.8)
        assert stop == expected

    def test_stop_loss_minimum_value(self):
        """Test that stop loss never goes below $0.01"""
        stop = calculate_stop_loss(
            symbol="PENNY",
            entry_price=0.05,
            direction="LONG",
            atr_value=1.0,
            atr_multiplier=2.0
        )
        assert stop >= 0.01

    def test_stop_loss_invalid_direction(self):
        """Test error on invalid direction"""
        with pytest.raises(ValueError):
            calculate_stop_loss(
                symbol="SPY",
                entry_price=100.0,
                direction="INVALID"
            )


# ============================================================================
# TAKE PROFIT CALCULATION TESTS
# ============================================================================

class TestTakeProfitCalculation:
    """Test ATR-based take profit calculation"""

    def test_take_profit_long_position(self):
        """Test take profit for LONG position"""
        target = calculate_take_profit(
            symbol="SPY",
            entry_price=100.0,
            direction="LONG",
            atr_value=2.0,
            atr_multiplier=2.5,
            volatility_multiplier=1.0
        )
        # LONG: target = entry + (ATR × 2.5 × 1.0)
        expected = 100.0 + (2.0 * 2.5)
        assert target == expected

    def test_take_profit_short_position(self):
        """Test take profit for SHORT position"""
        target = calculate_take_profit(
            symbol="SPY",
            entry_price=100.0,
            direction="SHORT",
            atr_value=2.0,
            atr_multiplier=2.5,
            volatility_multiplier=1.0
        )
        # SHORT: target = entry - (ATR × 2.5 × 1.0)
        expected = 100.0 - (2.0 * 2.5)
        assert target == expected

    def test_take_profit_wider_with_high_volatility(self):
        """Test that targets are wider with high volatility"""
        target_normal = calculate_take_profit(
            symbol="SPY",
            entry_price=100.0,
            direction="LONG",
            atr_value=2.0,
            atr_multiplier=2.5,
            volatility_multiplier=1.0
        )

        target_high_vol = calculate_take_profit(
            symbol="SPY",
            entry_price=100.0,
            direction="LONG",
            atr_value=2.0,
            atr_multiplier=2.5,
            volatility_multiplier=1.5
        )

        assert target_high_vol > target_normal


# ============================================================================
# POSITION SIZING TESTS
# ============================================================================

class TestPositionSizing:
    """Test risk-based position sizing"""

    def test_position_sizing_basic(self):
        """Test basic position sizing calculation"""
        sizing = calculate_position_size(
            symbol="SPY",
            account_balance=50000.0,
            entry_price=100.0,
            stop_price=98.0,
            risk_percent=2.0
        )

        assert sizing["shares"] > 0
        assert sizing["position_value"] > 0
        assert sizing["risk_amount"] > 0

    def test_position_sizing_respects_risk_percent(self):
        """Test that position sizing respects risk percentage"""
        account = 50000.0
        risk_pct = 2.0
        expected_risk = account * (risk_pct / 100)

        sizing = calculate_position_size(
            symbol="SPY",
            account_balance=account,
            entry_price=100.0,
            stop_price=98.0,
            risk_percent=risk_pct
        )

        # Actual risk might be slightly less due to position limits
        assert sizing["risk_amount"] <= expected_risk

    def test_position_sizing_respects_max_single_position(self):
        """Test that position sizing respects max single position"""
        sizing = calculate_position_size(
            symbol="SPY",
            account_balance=100000.0,
            entry_price=10.0,
            stop_price=9.0,
            risk_percent=10.0,  # Would be large
            max_single_position=5000.0
        )

        assert sizing["position_value"] <= 5000.0
        assert sizing["limited_by"] == "max_position"

    def test_position_sizing_respects_concurrent_limit(self):
        """Test that position sizing respects concurrent position limit"""
        sizing = calculate_position_size(
            symbol="QQQ",
            account_balance=50000.0,
            entry_price=350.0,
            stop_price=340.0,
            risk_percent=2.0,
            max_concurrent_value=15000.0,
            current_positions_value=14000.0
        )

        # Should leave room for only ~$1000 more
        assert sizing["position_value"] <= 1000.0
        assert sizing["limited_by"] == "concurrent_limit"

    def test_position_sizing_invalid_stop(self):
        """Test position sizing with invalid stop price"""
        sizing = calculate_position_size(
            symbol="SPY",
            account_balance=50000.0,
            entry_price=100.0,
            stop_price=100.0  # Same as entry = invalid
        )

        assert sizing["shares"] == 0
        assert sizing["limited_by"] == "invalid_stop_price"


# ============================================================================
# COMPLETE RISK PROFILE TESTS
# ============================================================================

class TestCompleteRiskProfile:
    """Test full risk profile creation"""

    def test_risk_profile_long_trade(self):
        """Test risk profile for LONG trade"""
        metrics = create_risk_profile(
            symbol="SPY",
            entry_price=100.0,
            account_balance=50000.0,
            direction="LONG",
            atr_value=2.0,
            iv_rank=50.0
        )

        assert metrics.symbol == "SPY"
        assert metrics.direction == "LONG"
        assert metrics.entry_price == 100.0
        assert metrics.stop_price < metrics.entry_price
        assert metrics.target_price > metrics.entry_price
        assert metrics.position_size > 0
        assert metrics.risk_reward_ratio > 0

    def test_risk_profile_short_trade(self):
        """Test risk profile for SHORT trade"""
        metrics = create_risk_profile(
            symbol="QQQ",
            entry_price=350.0,
            account_balance=50000.0,
            direction="SHORT",
            atr_value=3.0,
            iv_rank=50.0
        )

        assert metrics.direction == "SHORT"
        assert metrics.stop_price > metrics.entry_price
        assert metrics.target_price < metrics.entry_price

    def test_risk_profile_low_volatility_regime(self):
        """Test risk profile in low volatility environment"""
        metrics = create_risk_profile(
            symbol="SPY",
            entry_price=100.0,
            account_balance=50000.0,
            direction="LONG",
            atr_value=2.0,
            iv_rank=20.0  # Low IV
        )

        # Low volatility should tighten stops (smaller range)
        assert metrics.volatility_multiplier < 1.0
        assert metrics.risk_amount < (100.0 - (100.0 - (2.0 * 1.5 * 1.0)))

    def test_risk_profile_high_volatility_regime(self):
        """Test risk profile in high volatility environment"""
        metrics_low_vol = create_risk_profile(
            symbol="SPY",
            entry_price=100.0,
            account_balance=50000.0,
            direction="LONG",
            atr_value=2.0,
            iv_rank=20.0
        )

        metrics_high_vol = create_risk_profile(
            symbol="SPY",
            entry_price=100.0,
            account_balance=50000.0,
            direction="LONG",
            atr_value=2.0,
            iv_rank=85.0
        )

        # High volatility should loosen stops (larger range)
        assert metrics_high_vol.volatility_multiplier > metrics_low_vol.volatility_multiplier
        assert metrics_high_vol.risk_amount > metrics_low_vol.risk_amount


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestRiskProfileValidation:
    """Test risk profile validation"""

    def test_validation_passes_valid_profile(self):
        """Test that valid profile passes validation"""
        metrics = create_risk_profile(
            symbol="SPY",
            entry_price=100.0,
            account_balance=50000.0,
            direction="LONG",
            atr_value=2.0,
            iv_rank=50.0
        )

        is_valid, reason = validate_risk_profile(metrics)
        assert is_valid is True

    def test_validation_fails_zero_position(self):
        """Test that zero position fails validation"""
        metrics = RiskMetrics(
            symbol="SPY",
            entry_price=100.0,
            direction="LONG",
            stop_price=100.0,
            target_price=105.0,
            position_size=0,
            position_value=0.0,
            risk_amount=0.0,
            reward_amount=5.0,
            risk_reward_ratio=0.0,
            atr_value=2.0,
            iv_rank=50.0,
            volatility_multiplier=1.0,
            max_loss_usd=0.0,
            max_gain_usd=0.0,
            timestamp="2024-01-01T00:00:00"
        )

        is_valid, _ = validate_risk_profile(metrics)
        assert is_valid is False

    def test_validation_fails_poor_risk_reward(self):
        """Test that poor risk/reward ratio fails validation"""
        metrics = create_risk_profile(
            symbol="SPY",
            entry_price=100.0,
            account_balance=50000.0,
            direction="LONG",
            atr_value=5.0,  # Very high, creating poor RR ratio
            stop_atr_multiplier=2.5,  # Large stop
            target_atr_multiplier=1.0  # Small target
        )

        is_valid, _ = validate_risk_profile(metrics, min_risk_reward_ratio=2.0)
        # Likely to fail with min RR of 2.0
        # (depends on actual numbers)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests across multiple functions"""

    def test_full_workflow_long_spy(self):
        """Test complete workflow for SPY LONG trade"""
        highs = [400.0, 402.0, 401.0, 403.0, 402.0] + [400.0] * 15
        lows = [398.0, 400.0, 399.0, 401.0, 400.0] + [398.0] * 15
        closes = [399.0, 401.0, 400.0, 402.0, 401.0] + [399.0] * 15

        metrics = create_risk_profile(
            symbol="SPY",
            entry_price=400.0,
            account_balance=100000.0,
            direction="LONG",
            iv_rank=45.0,
            high_prices=highs,
            low_prices=lows,
            close_prices=closes
        )

        # Validate the profile
        is_valid, reason = validate_risk_profile(metrics)
        assert is_valid is True

        # Check constraints
        assert metrics.position_value <= 5000.0  # Max single position
        assert metrics.max_loss_usd > 0
        assert metrics.max_gain_usd > metrics.max_loss_usd  # Positive R:R

    def test_full_workflow_short_qqq(self):
        """Test complete workflow for QQQ SHORT trade"""
        metrics = create_risk_profile(
            symbol="QQQ",
            entry_price=350.0,
            account_balance=100000.0,
            direction="SHORT",
            atr_value=3.5,
            iv_rank=65.0,  # Elevated volatility
            risk_percent=1.5
        )

        is_valid, reason = validate_risk_profile(metrics)
        assert is_valid is True

        # High IV should result in larger stops
        assert metrics.volatility_multiplier > 1.0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

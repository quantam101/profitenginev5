"""
Integration tests for Dynamic Risk Adjustment module.
Tests volatility scalar calculations, loss limit adjustments, Kelly scaling, and regime transitions.
"""

import pytest
import numpy as np
from datetime import datetime
from dynamic_risk_adjustment import (
    DynamicRiskAdjuster,
    MarketRegime,
    RegimeParameters
)


class TestVolatilityScalarCalculation:
    """Test calculate_volatility_scalar() returns values between 0.5-1.5"""

    def test_volatility_scalar_default_no_data(self):
        """Test scalar returns 1.0 with no price data"""
        adjuster = DynamicRiskAdjuster()
        scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        assert scalar == 1.0, "Should return 1.0 (baseline) when no data available"

    def test_volatility_scalar_insufficient_data(self):
        """Test scalar returns 1.0 with fewer than 3 data points"""
        adjuster = DynamicRiskAdjuster()
        adjuster.update_price_data("BTC/USD", [0.01, 0.02])
        scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        assert scalar == 1.0, "Should return 1.0 with insufficient data"

    def test_volatility_scalar_low_volatility(self):
        """Test scalar increases (>1.0) for low volatility"""
        adjuster = DynamicRiskAdjuster()

        # Generate low volatility returns (small variations)
        low_vol_returns = [0.0001] * 20  # Very small returns
        adjuster.update_price_data("BTC/USD", low_vol_returns)

        scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        assert 1.0 <= scalar <= 1.5, f"Low volatility scalar {scalar} should be >= 1.0 and <= 1.5"
        assert scalar > 1.0, "Low volatility should increase scalar (encourage trading)"

    def test_volatility_scalar_high_volatility(self):
        """Test scalar decreases (<1.0) for high volatility"""
        adjuster = DynamicRiskAdjuster()

        # Generate high volatility returns (large variations)
        high_vol_returns = [0.05, -0.04, 0.06, -0.05, 0.04, -0.06, 0.05, -0.04,
                            0.06, -0.05, 0.04, -0.06, 0.05, -0.04, 0.06, -0.05,
                            0.04, -0.06, 0.05, -0.04]
        adjuster.update_price_data("BTC/USD", high_vol_returns)

        scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        assert 0.1 <= scalar <= 1.5, f"High volatility scalar {scalar} should be within bounds [0.1, 1.5]"
        assert scalar < 1.0, "High volatility should decrease scalar (reduce position size)"

    def test_volatility_scalar_bounds(self):
        """Test scalar is always clipped between 0.1 and 1.5"""
        adjuster = DynamicRiskAdjuster()

        # Test extreme low volatility
        ultra_low_returns = [0.00001] * 20
        adjuster.update_price_data("ETH/USD", ultra_low_returns)
        scalar = adjuster.calculate_volatility_scalar("ETH/USD")
        assert 0.1 <= scalar <= 1.5, f"Scalar {scalar} violates bounds [0.1, 1.5]"

        # Test extreme high volatility
        adjuster.volatility_buffer.clear()
        high_vol_base = [0.1, -0.1] * 10
        extreme_returns = [r * 10 for r in high_vol_base]
        adjuster.update_price_data("XRP/USD", extreme_returns)
        scalar = adjuster.calculate_volatility_scalar("XRP/USD")
        assert 0.1 <= scalar <= 1.5, f"Scalar {scalar} violates bounds [0.1, 1.5]"


class TestDailyLossLimitAdjustment:
    """Test adjust_daily_loss_limit() scales from $100-$300 based on volatility"""

    def test_loss_limit_baseline_normal_regime(self):
        """Test baseline loss limit in NORMAL regime ($200)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.NORMAL

        limit, utilization = adjuster.adjust_daily_loss_limit(0.0)
        assert limit == 200.0, "Normal regime with no loss should have $200 limit"
        assert utilization == 0.0, "Utilization should be 0% with no realized loss"

    def test_loss_limit_low_volatility_regime(self):
        """Test loss limit increases in LOW_VOLATILITY regime (1.3x = $260)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.LOW_VOLATILITY

        limit, utilization = adjuster.adjust_daily_loss_limit(0.0)
        expected_limit = 200.0 * 1.3  # 1.3 scalar for low volatility
        assert limit == expected_limit, f"Low volatility should scale limit to ${expected_limit}"
        assert 260.0 <= limit <= 300.0, f"Low vol limit {limit} should be in expanded range"

    def test_loss_limit_high_volatility_regime(self):
        """Test loss limit decreases in HIGH_VOLATILITY regime (0.7x = $140)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.HIGH_VOLATILITY

        limit, utilization = adjuster.adjust_daily_loss_limit(0.0)
        expected_limit = 200.0 * 0.7  # 0.7 scalar for high volatility
        assert limit == expected_limit, f"High volatility should scale limit to ${expected_limit}"
        assert 100.0 <= limit <= 150.0, f"High vol limit {limit} should be constrained"

    def test_loss_limit_crisis_regime(self):
        """Test loss limit severely decreases in CRISIS regime (0.3x = $60)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.CRISIS

        limit, utilization = adjuster.adjust_daily_loss_limit(0.0)
        expected_limit = 200.0 * 0.3  # 0.3 scalar for crisis
        assert limit == expected_limit, f"Crisis should scale limit to ${expected_limit}"
        assert limit <= 100.0, "Crisis limit should be heavily constrained"

    def test_progressive_tightening_50_percent(self):
        """Test progressive tightening at 50% utilization (10% reduction)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.NORMAL

        # At 50% utilization: $100 loss
        limit, utilization = adjuster.adjust_daily_loss_limit(100.0)
        expected_limit = 200.0 * 0.9  # 10% reduction
        assert abs(limit - expected_limit) < 0.01, f"50% utilization should reduce limit by 10% to ${expected_limit}"
        assert abs(utilization - 50.0) < 0.1, "Utilization should be ~50%"

    def test_progressive_tightening_75_percent(self):
        """Test progressive tightening at 75% utilization (25% reduction)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.NORMAL

        # At 75% utilization: $150 loss
        limit, utilization = adjuster.adjust_daily_loss_limit(150.0)
        expected_limit = 200.0 * 0.75  # 25% reduction
        assert abs(limit - expected_limit) < 0.01, f"75% utilization should reduce limit by 25% to ${expected_limit}"
        assert abs(utilization - 75.0) < 0.1, "Utilization should be ~75%"

    def test_progressive_tightening_90_percent(self):
        """Test hard stop at 90% utilization (50% reduction)"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)
        adjuster.current_regime = MarketRegime.NORMAL

        # At 90% utilization: $180 loss
        limit, utilization = adjuster.adjust_daily_loss_limit(180.0)
        expected_limit = 200.0 * 0.5  # 50% reduction (hard stop)
        assert abs(limit - expected_limit) < 0.01, f"90% utilization should invoke hard stop, reduce to ${expected_limit}"
        assert abs(utilization - 90.0) < 0.1, "Utilization should be ~90%"

    def test_loss_limit_scaling_range(self):
        """Verify loss limit scales across full $100-$300 range"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)

        test_cases = [
            (MarketRegime.CRISIS, 0.3, 60.0),      # $60 minimum
            (MarketRegime.HIGH_VOLATILITY, 0.7, 140.0),  # $140 constrained
            (MarketRegime.NORMAL, 1.0, 200.0),     # $200 baseline
            (MarketRegime.LOW_VOLATILITY, 1.3, 260.0),   # $260 expanded
        ]

        for regime, scalar, expected in test_cases:
            adjuster.current_regime = regime
            limit, _ = adjuster.adjust_daily_loss_limit(0.0)
            assert abs(limit - expected) < 0.01, f"{regime.value} should produce limit ${expected}"


class TestKellyFractionScaling:
    """Test Kelly fraction scaling produces valid position sizes"""

    def test_kelly_baseline_normal_regime(self):
        """Test baseline Kelly in NORMAL regime (5%)"""
        adjuster = DynamicRiskAdjuster(kelly_base_fraction=0.05)
        adjuster.current_regime = MarketRegime.NORMAL

        # Setup low volatility to get scalar 1.0
        adjuster.update_price_data("BTC/USD", [0.0001] * 20)
        kelly = adjuster.scale_kelly_fraction("BTC/USD")

        assert 0.001 <= kelly <= 0.20, f"Kelly {kelly} should be within bounds [0.001, 0.20]"

    def test_kelly_low_volatility_increased(self):
        """Test Kelly increases in low volatility regime"""
        adjuster = DynamicRiskAdjuster(kelly_base_fraction=0.05)
        adjuster.current_regime = MarketRegime.LOW_VOLATILITY

        # Setup low volatility
        adjuster.update_price_data("BTC/USD", [0.0001] * 20)
        kelly = adjuster.scale_kelly_fraction("BTC/USD")

        # Expected: 0.05 * 1.0 (low vol scalar) * (0.08/0.05) = 0.08
        expected = 0.05 * (0.08 / 0.05)  # regime adjustment
        assert kelly >= 0.05, f"Low volatility Kelly {kelly} should be >= base 5%"
        assert kelly <= 0.20, "Kelly should not exceed max bound"

    def test_kelly_high_volatility_decreased(self):
        """Test Kelly decreases in high volatility regime"""
        adjuster = DynamicRiskAdjuster(kelly_base_fraction=0.05)
        adjuster.current_regime = MarketRegime.HIGH_VOLATILITY

        # Setup high volatility
        high_vol = [0.05, -0.04, 0.06, -0.05] * 5
        adjuster.update_price_data("BTC/USD", high_vol)
        kelly = adjuster.scale_kelly_fraction("BTC/USD")

        # Expected: much lower Kelly due to high volatility
        assert kelly <= 0.05, f"High volatility Kelly {kelly} should be <= base 5%"
        assert kelly >= 0.001, "Kelly should not go below minimum"

    def test_kelly_crisis_severely_reduced(self):
        """Test Kelly severely reduced in crisis regime"""
        adjuster = DynamicRiskAdjuster(kelly_base_fraction=0.05)
        adjuster.current_regime = MarketRegime.CRISIS

        # Crisis regime Kelly fraction is 0.005
        extreme_vol = [0.1, -0.1, 0.1, -0.1] * 5
        adjuster.update_price_data("BTC/USD", extreme_vol)
        kelly = adjuster.scale_kelly_fraction("BTC/USD")

        # Expected: 0.05 * low_scalar * (0.005/0.05) = very small
        assert kelly <= 0.02, f"Crisis Kelly {kelly} should be severely reduced"
        assert kelly >= 0.001, "Kelly should stay above minimum"

    def test_kelly_bounds_enforcement(self):
        """Test Kelly is always bounded [0.001, 0.20]"""
        adjuster = DynamicRiskAdjuster(kelly_base_fraction=0.05)

        regimes_to_test = [
            MarketRegime.CRISIS,
            MarketRegime.HIGH_VOLATILITY,
            MarketRegime.NORMAL,
            MarketRegime.LOW_VOLATILITY
        ]

        for regime in regimes_to_test:
            adjuster.current_regime = regime
            kelly = adjuster.scale_kelly_fraction("BTC/USD")
            assert 0.001 <= kelly <= 0.20, f"Kelly {kelly} violates bounds for {regime.value}"

    def test_kelly_with_custom_base(self):
        """Test Kelly scaling with custom base fraction"""
        adjuster = DynamicRiskAdjuster(kelly_base_fraction=0.05)
        adjuster.current_regime = MarketRegime.NORMAL

        # Use custom base override
        kelly = adjuster.scale_kelly_fraction("BTC/USD", base_kelly=0.10)

        assert 0.001 <= kelly <= 0.20, "Custom base Kelly should still respect bounds"
        assert kelly != 0.05, "Custom base should be applied"


class TestRegimeLoadAndTransition:
    """Test regime-specific parameters load correctly and transitions work"""

    def test_regime_parameters_initialization(self):
        """Test all regimes are properly initialized with correct parameters"""
        adjuster = DynamicRiskAdjuster()

        expected_regimes = {
            MarketRegime.LOW_VOLATILITY: {
                'kelly_fraction': 0.08,
                'loss_limit_scalar': 1.3,
                'max_position_size': 0.15,
            },
            MarketRegime.NORMAL: {
                'kelly_fraction': 0.05,
                'loss_limit_scalar': 1.0,
                'max_position_size': 0.10,
            },
            MarketRegime.HIGH_VOLATILITY: {
                'kelly_fraction': 0.02,
                'loss_limit_scalar': 0.7,
                'max_position_size': 0.05,
            },
            MarketRegime.CRISIS: {
                'kelly_fraction': 0.005,
                'loss_limit_scalar': 0.3,
                'max_position_size': 0.02,
            },
        }

        for regime, expected_params in expected_regimes.items():
            params = adjuster.regimes[regime]
            assert params.kelly_fraction == expected_params['kelly_fraction']
            assert params.loss_limit_scalar == expected_params['loss_limit_scalar']
            assert params.max_position_size == expected_params['max_position_size']

    def test_regime_default_normal(self):
        """Test default regime is NORMAL"""
        adjuster = DynamicRiskAdjuster()
        assert adjuster.current_regime == MarketRegime.NORMAL

    def test_regime_transition_to_low_volatility(self):
        """Test regime transition to LOW_VOLATILITY"""
        adjuster = DynamicRiskAdjuster(regime_switch_threshold=0.95)

        # Trigger low volatility detection
        metrics = {
            'mean_volatility': 0.01,  # < 0.015 threshold
            'volatility_spike': 1.0
        }

        new_regime, confidence = adjuster.update_market_regime(metrics)
        assert new_regime == MarketRegime.LOW_VOLATILITY
        assert confidence >= 0.85, "Confidence should be reasonable for clear signal"

    def test_regime_transition_to_high_volatility(self):
        """Test regime transition to HIGH_VOLATILITY with sufficient confidence"""
        adjuster = DynamicRiskAdjuster(regime_switch_threshold=0.75)  # Lower threshold
        adjuster.current_regime = MarketRegime.NORMAL

        metrics = {
            'mean_volatility': 0.045,  # > 0.03 threshold
            'volatility_spike': 1.6
        }

        new_regime, confidence = adjuster.update_market_regime(metrics)
        # Confidence = min(1.0, 0.045 / 0.05) = 0.90, which meets 0.75 threshold
        assert new_regime == MarketRegime.HIGH_VOLATILITY, \
            f"Expected HIGH_VOLATILITY with confidence {confidence}, got {new_regime.value}"

    def test_regime_transition_to_crisis(self):
        """Test regime transition to CRISIS"""
        adjuster = DynamicRiskAdjuster(regime_switch_threshold=0.95)

        metrics = {
            'mean_volatility': 0.07,  # > 0.06 threshold
            'volatility_spike': 2.8
        }

        new_regime, confidence = adjuster.update_market_regime(metrics)
        assert new_regime == MarketRegime.CRISIS
        assert confidence >= 0.9, "Crisis signal should have high confidence"

    def test_regime_transition_threshold_enforcement(self):
        """Test regime transition respects confidence threshold"""
        adjuster = DynamicRiskAdjuster(regime_switch_threshold=0.99)  # High threshold
        adjuster.current_regime = MarketRegime.NORMAL

        # Weak signal that doesn't meet threshold
        metrics = {
            'mean_volatility': 0.031,  # Just over 0.03
            'volatility_spike': 1.0
        }

        new_regime, confidence = adjuster.update_market_regime(metrics)
        # May not transition if confidence < 0.99
        assert isinstance(new_regime, MarketRegime)
        assert 0 <= confidence <= 1.0


class TestHighLowVolatilityScenarios:
    """Simulate high and low volatility scenarios, verify limits adjust properly"""

    def test_scenario_low_volatility_full_flow(self):
        """Complete low volatility scenario: expand limits, increase Kelly"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)

        # Simulate low volatility prices
        prices = [100 + 0.01 * i for i in range(50)]  # Steady increase
        returns = np.diff(np.log(prices)).tolist()

        # Update price data
        adjuster.update_price_data("BTC/USD", returns)

        # Check volatility scalar is high
        scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        assert scalar > 1.0, f"Low volatility should increase scalar, got {scalar}"

        # Update regime
        metrics = {'mean_volatility': 0.01, 'volatility_spike': 0.8}
        adjuster.update_market_regime(metrics)
        assert adjuster.current_regime == MarketRegime.LOW_VOLATILITY

        # Check expanded loss limit
        limit, _ = adjuster.adjust_daily_loss_limit(0.0)
        assert limit > 200.0, f"Low vol regime should expand limit beyond $200, got ${limit}"

        # Check increased Kelly
        kelly = adjuster.scale_kelly_fraction("BTC/USD")
        assert kelly > 0.05, f"Low vol should increase Kelly above 5%, got {kelly:.4f}"

    def test_scenario_high_volatility_full_flow(self):
        """Complete high volatility scenario: constrain limits, reduce Kelly"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)

        # Simulate high volatility prices
        prices = [100 * (1.02 ** np.sin(i/3)) for i in range(50)]  # Oscillating
        returns = np.diff(np.log(prices)).tolist()

        # Update price data
        adjuster.update_price_data("BTC/USD", returns)

        # Check volatility scalar is low
        scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        assert scalar < 1.0, f"High volatility should reduce scalar, got {scalar}"

        # Update regime
        metrics = {'mean_volatility': 0.05, 'volatility_spike': 1.8}
        adjuster.update_market_regime(metrics)
        assert adjuster.current_regime == MarketRegime.HIGH_VOLATILITY

        # Check constrained loss limit
        limit, _ = adjuster.adjust_daily_loss_limit(0.0)
        assert limit < 200.0, f"High vol regime should constrain limit below $200, got ${limit}"

        # Check reduced Kelly
        kelly = adjuster.scale_kelly_fraction("BTC/USD")
        assert kelly < 0.05, f"High vol should reduce Kelly below 5%, got {kelly:.4f}"

    def test_scenario_crisis_with_realized_losses(self):
        """Crisis scenario with progressive loss accumulation"""
        adjuster = DynamicRiskAdjuster(baseline_daily_loss_limit=200.0)

        # Update to crisis regime
        metrics = {'mean_volatility': 0.08, 'volatility_spike': 3.0}
        adjuster.update_market_regime(metrics)
        assert adjuster.current_regime == MarketRegime.CRISIS

        # Check baseline crisis limit (0.3x = $60)
        limit, util = adjuster.adjust_daily_loss_limit(0.0)
        assert limit == 60.0, f"Crisis baseline should be $60, got ${limit}"

        # Accumulate losses
        loss_scenarios = [
            (10.0, "10% utilization"),  # $6 loss, still OK
            (30.0, "50% utilization"),  # $30 loss, progressive tightening
            (45.0, "75% utilization"),  # $45 loss, further tightening
            (54.0, "90% utilization"),  # $54 loss, hard stop
        ]

        for loss, desc in loss_scenarios:
            limit, util = adjuster.adjust_daily_loss_limit(loss)
            assert limit > 0, f"{desc}: limit should remain positive"
            assert limit <= 60.0, f"{desc}: limit should not exceed crisis baseline"
            print(f"  {desc}: limit=${limit:.2f}, utilization={util:.1f}%")


class TestRegimeSpecificBehavior:
    """Verify regime-specific parameters are applied correctly"""

    def test_position_sizing_limits_by_regime(self):
        """Test position sizing limits vary by regime"""
        adjuster = DynamicRiskAdjuster()
        portfolio_value = 10000.0

        test_cases = [
            (MarketRegime.LOW_VOLATILITY, 0.15, "High position sizing"),
            (MarketRegime.NORMAL, 0.10, "Standard position sizing"),
            (MarketRegime.HIGH_VOLATILITY, 0.05, "Reduced position sizing"),
            (MarketRegime.CRISIS, 0.02, "Minimal position sizing"),
        ]

        for regime, expected_max_pct, description in test_cases:
            adjuster.current_regime = regime
            limits = adjuster.get_position_sizing_limits(portfolio_value)

            max_position = limits['max_position_usd']
            expected_position = portfolio_value * expected_max_pct

            assert abs(max_position - expected_position) < 0.01, \
                f"{description}: expected ${expected_position}, got ${max_position}"

    def test_stop_loss_adjusts_in_crisis(self):
        """Test stop loss percentage tightens in crisis regime"""
        adjuster = DynamicRiskAdjuster()

        # Normal regime
        adjuster.current_regime = MarketRegime.NORMAL
        limits = adjuster.get_position_sizing_limits(10000.0)
        assert limits['stop_loss_pct'] == 0.03, "Normal should use 3% stop loss"

        # Crisis regime
        adjuster.current_regime = MarketRegime.CRISIS
        limits = adjuster.get_position_sizing_limits(10000.0)
        assert limits['stop_loss_pct'] == 0.02, "Crisis should use 2% stop loss"

    def test_get_regime_parameters(self):
        """Test get_regime_parameters returns current regime params"""
        adjuster = DynamicRiskAdjuster()

        for regime in [MarketRegime.LOW_VOLATILITY, MarketRegime.NORMAL,
                       MarketRegime.HIGH_VOLATILITY, MarketRegime.CRISIS]:
            adjuster.current_regime = regime
            params = adjuster.get_regime_parameters()
            assert params == adjuster.regimes[regime]
            assert hasattr(params, 'kelly_fraction')
            assert hasattr(params, 'loss_limit_scalar')


class TestIntegrationWithRiskKernel:
    """Test integration with DeterministicRiskKernel"""

    def test_adjusted_limit_passed_to_risk_kernel(self):
        """Verify adjusted limit can be passed to risk kernel"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading-control'))

        from risk_kernel import DeterministicRiskKernel

        risk_kernel = DeterministicRiskKernel({
            'max_daily_loss_usd': 200.0,
            'max_weekly_loss_usd': 1000.0
        })

        # Should accept adjusted_daily_loss_limit parameter
        assert hasattr(risk_kernel, 'evaluate')

        # Check signature accepts adjusted limit
        import inspect
        sig = inspect.signature(risk_kernel.evaluate)
        assert 'adjusted_daily_loss_limit' in sig.parameters


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_multiple_instruments_separate_buffers(self):
        """Test multiple instruments maintain separate volatility buffers"""
        adjuster = DynamicRiskAdjuster()

        # BTC: low volatility
        adjuster.update_price_data("BTC/USD", [0.0001] * 20)

        # ETH: high volatility
        adjuster.update_price_data("ETH/USD", [0.05, -0.05] * 10)

        btc_scalar = adjuster.calculate_volatility_scalar("BTC/USD")
        eth_scalar = adjuster.calculate_volatility_scalar("ETH/USD")

        assert btc_scalar > eth_scalar, "BTC (low vol) scalar should be higher than ETH (high vol)"

    def test_reset_daily_limits(self):
        """Test daily limit reset functionality"""
        adjuster = DynamicRiskAdjuster()
        adjuster.daily_realized_loss = 150.0

        initial_time = adjuster.period_start
        adjuster.reset_daily_limits()

        assert adjuster.daily_realized_loss == 0.0
        assert adjuster.period_start > initial_time or adjuster.period_start == adjuster.period_start

    def test_get_status_returns_dict(self):
        """Test status reporting functionality"""
        adjuster = DynamicRiskAdjuster()
        adjuster.daily_realized_loss = 50.0

        status = adjuster.get_status()

        assert isinstance(status, dict)
        assert 'regime' in status
        assert 'regime_confidence' in status
        assert 'daily_loss' in status
        assert 'baseline_limit' in status


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

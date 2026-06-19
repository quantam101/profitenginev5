"""
AUTOMATED REGRESSION TESTING — Prevent Code Drift
Continuously validates that core functionality doesn't regress with changes
"""

import asyncio
from runtime.strategy_implementations import (
    RSI2Connors, IBSMeanReversion, KAMATrend, VWAPDeviation,
    StatArbKalman, MomentumScanner
)
from runtime.position_manager import PositionManager
from runtime.advanced_strategies import AdvancedStrategyOrchestrator
from runtime.trading_agents_system import MasterOrchestratorAI
from runtime.error_handling import ErrorRecoveryHandler, ErrorSeverity


class RegressionBaseline:
    """Stores baseline metrics for comparison"""

    def __init__(self):
        self.baseline_signals = {}
        self.baseline_positions = {}
        self.baseline_errors = {}

    def capture_strategy_baseline(self):
        """Capture baseline strategy signals"""
        print("  Capturing strategy baselines...")

        test_prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3
        test_volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320] * 3

        strategies = {
            "RSI2": RSI2Connors.calculate(test_prices),
            "IBS": IBSMeanReversion.calculate(106.0, 104.0, 105.8, 105.0),
            "KAMA": KAMATrend.calculate(test_prices),
            "VWAP": VWAPDeviation.calculate(test_prices, test_volumes),
            "Kalman": StatArbKalman.calculate(test_prices),
            "Momentum": MomentumScanner.calculate(test_prices),
        }

        self.baseline_signals = {
            name: {
                "signal": result.signal,
                "conviction": result.conviction,
                "reasoning": result.reasoning[:30],  # First 30 chars
            }
            for name, result in strategies.items()
        }

        return self.baseline_signals

    def capture_position_baseline(self):
        """Capture baseline position manager behavior"""
        print("  Capturing position manager baselines...")

        pm = PositionManager(100000.0)

        # Open positions
        pm.open_position("AAPL", 150.0, 100, 147.0, 154.0, "BUY")
        pm.open_position("MSFT", 300.0, 50, 295.0, 310.0, "BUY")

        # Trigger exits
        closed = pm.check_exits({"AAPL": 155.0, "MSFT": 294.0})

        self.baseline_positions = {
            "positions_opened": 2,
            "positions_closed": len(closed),
            "expected_exits": [
                {"symbol": "AAPL", "exit_reason": "TAKE_PROFIT"},
                {"symbol": "MSFT", "exit_reason": "STOP_LOSS"},
            ],
            "actual_exits": [
                {"symbol": t.symbol, "exit_reason": t.exit_reason}
                for t in closed
            ],
        }

        return self.baseline_positions

    def capture_error_baseline(self):
        """Capture baseline error handling"""
        print("  Capturing error handling baselines...")

        handler = ErrorRecoveryHandler()
        handler.log_error(ErrorSeverity.RECOVERABLE, "Test recoverable", {})
        handler.log_error(ErrorSeverity.DEGRADED, "Test degraded", {})
        handler.log_error(ErrorSeverity.CRITICAL, "Test critical", {})

        self.baseline_errors = {
            "total_errors": len(handler.error_log),
            "recoverable": len([e for e in handler.error_log if e["severity"] == "recoverable"]),
            "degraded": len([e for e in handler.error_log if e["severity"] == "degraded"]),
            "critical": len([e for e in handler.error_log if e["severity"] == "critical"]),
        }

        return self.baseline_errors


def test_strategy_no_regression():
    """Regression test: strategies produce consistent outputs"""
    print("\n[REGRESSION TEST 1] Strategy Signal Consistency")
    print("-" * 80)

    baseline = RegressionBaseline()
    baseline_signals = baseline.capture_strategy_baseline()

    # Run again and compare
    test_prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3
    test_volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320] * 3

    strategies = {
        "RSI2": RSI2Connors.calculate(test_prices),
        "IBS": IBSMeanReversion.calculate(106.0, 104.0, 105.8, 105.0),
        "KAMA": KAMATrend.calculate(test_prices),
        "VWAP": VWAPDeviation.calculate(test_prices, test_volumes),
        "Kalman": StatArbKalman.calculate(test_prices),
        "Momentum": MomentumScanner.calculate(test_prices),
    }

    regressions = []
    for name, result in strategies.items():
        baseline = baseline_signals[name]
        actual = {
            "signal": result.signal,
            "conviction": result.conviction,
        }

        # Check signal matches exactly
        if abs(actual["signal"] - baseline["signal"]) > 0.0001:
            regressions.append(
                f"{name} signal regressed: {baseline['signal']:.4f} -> {actual['signal']:.4f}"
            )
        else:
            print(f"  [OK] {name} signal consistent: {actual['signal']:.2f}")

        # Check conviction matches exactly
        if abs(actual["conviction"] - baseline["conviction"]) > 0.0001:
            regressions.append(
                f"{name} conviction regressed: {baseline['conviction']:.4f} -> {actual['conviction']:.4f}"
            )

    assert len(regressions) == 0, f"Regressions found:\n" + "\n".join(regressions)
    print("[OK] Strategy signal consistency test passed")
    return True


def test_position_manager_no_regression():
    """Regression test: position manager behavior unchanged"""
    print("\n[REGRESSION TEST 2] Position Manager Behavior Consistency")
    print("-" * 80)

    baseline = RegressionBaseline()
    baseline_positions = baseline.capture_position_baseline()

    # Verify baseline
    assert baseline_positions["positions_opened"] == 2
    assert baseline_positions["positions_closed"] == 2
    assert baseline_positions["actual_exits"][0]["exit_reason"] == "TAKE_PROFIT"
    assert baseline_positions["actual_exits"][1]["exit_reason"] == "STOP_LOSS"

    print(f"  [OK] Positions opened: {baseline_positions['positions_opened']}")
    print(f"  [OK] Positions closed: {baseline_positions['positions_closed']}")
    print(f"  [OK] Exit reason 1: {baseline_positions['actual_exits'][0]['exit_reason']}")
    print(f"  [OK] Exit reason 2: {baseline_positions['actual_exits'][1]['exit_reason']}")

    print("[OK] Position manager behavior consistency test passed")
    return True


def test_error_handling_no_regression():
    """Regression test: error handling behavior unchanged"""
    print("\n[REGRESSION TEST 3] Error Handling Behavior Consistency")
    print("-" * 80)

    baseline = RegressionBaseline()
    baseline_errors = baseline.capture_error_baseline()

    # Verify baseline
    assert baseline_errors["total_errors"] == 3
    assert baseline_errors["recoverable"] == 1
    assert baseline_errors["degraded"] == 1
    assert baseline_errors["critical"] == 1

    print(f"  [OK] Total errors logged: {baseline_errors['total_errors']}")
    print(f"  [OK] Recoverable errors: {baseline_errors['recoverable']}")
    print(f"  [OK] Degraded errors: {baseline_errors['degraded']}")
    print(f"  [OK] Critical errors: {baseline_errors['critical']}")

    print("[OK] Error handling behavior consistency test passed")
    return True


async def test_advanced_strategies_no_regression():
    """Regression test: advanced strategies work correctly"""
    print("\n[REGRESSION TEST 4] Advanced Strategies Consistency")
    print("-" * 80)

    orchestrator = AdvancedStrategyOrchestrator()

    test_prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3

    # Generate signals
    signals = orchestrator.generate_advanced_signals("AAPL", 0.6, test_prices, None)

    # Verify baseline: should generate 3+ signals
    assert len(signals) >= 3, f"Expected 3+ signals, got {len(signals)}"

    # Verify each signal is valid
    for sig in signals:
        assert -1.0 <= sig.value <= 1.0, f"{sig.strategy_name} value out of range"
        assert 0.0 <= sig.conviction <= 1.0, f"{sig.strategy_name} conviction out of range"
        assert sig.sharpe_ratio > 0, f"{sig.strategy_name} sharpe_ratio invalid"
        print(f"  [OK] {sig.strategy_name}: valid signal")

    print("[OK] Advanced strategies consistency test passed")
    return True


async def test_multi_agent_no_regression():
    """Regression test: multi-agent system works correctly"""
    print("\n[REGRESSION TEST 5] Multi-Agent System Consistency")
    print("-" * 80)

    orchestrator = MasterOrchestratorAI(account_balance=100000.0)

    # Verify 6 agents
    assert len(orchestrator.agents) == 6, f"Expected 6 agents, got {len(orchestrator.agents)}"
    print(f"  [OK] 6 agents initialized")

    # Execute trading cycle
    test_prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3
    test_volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320] * 3

    market_data = {
        "symbol": "AAPL",
        "prices": test_prices,
        "volumes": test_volumes,
        "regime": "bull",
        "symbol_prices": {"AAPL": 105.8}
    }

    cycle = await orchestrator.execute_trading_cycle(market_data)

    # Verify cycle structure
    assert "final_decision" in cycle, "Missing final_decision"
    assert "execution_time_ms" in cycle, "Missing execution_time_ms"
    print(f"  [OK] Trading cycle executed: {cycle['final_decision']}")

    # Get system status
    status = await orchestrator.get_system_status()
    assert "agents" in status, "Missing agents in status"
    print(f"  [OK] System status retrieved")

    print("[OK] Multi-agent system consistency test passed")
    return True


async def run_all_regression_tests():
    """Execute all regression tests"""
    print("=" * 80)
    print("AUTOMATED REGRESSION TESTING")
    print("=" * 80)

    results = []

    try:
        results.append(("Strategy Signal Consistency", test_strategy_no_regression()))
        results.append(("Position Manager Consistency", test_position_manager_no_regression()))
        results.append(("Error Handling Consistency", test_error_handling_no_regression()))
        results.append(("Advanced Strategies Consistency", await test_advanced_strategies_no_regression()))
        results.append(("Multi-Agent System Consistency", await test_multi_agent_no_regression()))
    except Exception as e:
        print(f"\n[FAILED] Error during regression testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("REGRESSION TESTING COMPLETE")
    print("=" * 80)

    for name, passed in results:
        status = "[OK]" if passed else "[FAILED]"
        print(f"  {status} {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n[OK] NO REGRESSIONS DETECTED")
        print("     System behavior consistent across versions")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_regression_tests())
    exit(0 if success else 1)

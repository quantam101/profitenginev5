"""
SMOKE TESTING — Pre-Deployment Quick Health Checks
Fast, lightweight tests that verify system is ready for deployment
Runs in < 5 seconds, catches obvious errors before live trading
"""

import asyncio
import sys
from datetime import datetime
from runtime.strategy_implementations import (
    RSI2Connors, IBSMeanReversion, KAMATrend, VWAPDeviation,
    StatArbKalman, MomentumScanner
)
from runtime.position_manager import PositionManager
from runtime.advanced_strategies import AdvancedStrategyOrchestrator
from runtime.trading_agents_system import MasterOrchestratorAI
from runtime.error_handling import ErrorRecoveryHandler


class DeploymentSmokeTest:
    """Quick pre-deployment health checks"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.start_time = datetime.now()

    def check(self, condition: bool, message: str) -> bool:
        """Register a check result"""
        if condition:
            self.checks_passed += 1
            print(f"  [OK] {message}")
            return True
        else:
            self.checks_failed += 1
            print(f"  [FAIL] {message}")
            return False

    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()


def test_imports():
    """Smoke test 1: All imports work"""
    print("\n[SMOKE 1] Imports & Module Loading")
    print("-" * 80)

    test = DeploymentSmokeTest()

    try:
        test.check(RSI2Connors is not None, "RSI2Connors imports")
        test.check(IBSMeanReversion is not None, "IBSMeanReversion imports")
        test.check(KAMATrend is not None, "KAMATrend imports")
        test.check(VWAPDeviation is not None, "VWAPDeviation imports")
        test.check(StatArbKalman is not None, "StatArbKalman imports")
        test.check(MomentumScanner is not None, "MomentumScanner imports")
        test.check(PositionManager is not None, "PositionManager imports")
        test.check(AdvancedStrategyOrchestrator is not None, "AdvancedStrategyOrchestrator imports")
        test.check(MasterOrchestratorAI is not None, "MasterOrchestratorAI imports")
        test.check(ErrorRecoveryHandler is not None, "ErrorRecoveryHandler imports")
    except Exception as e:
        test.check(False, f"Import error: {e}")
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


def test_strategy_instantiation():
    """Smoke test 2: All strategies instantiate"""
    print("\n[SMOKE 2] Strategy Instantiation")
    print("-" * 80)

    test = DeploymentSmokeTest()
    prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3
    volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320] * 3

    try:
        rsi = RSI2Connors.calculate(prices)
        test.check(rsi is not None and rsi.signal is not None, "RSI-2 instantiates")

        ibs = IBSMeanReversion.calculate(106.0, 104.0, 105.8, 105.0)
        test.check(ibs is not None and ibs.signal is not None, "IBS instantiates")

        kama = KAMATrend.calculate(prices)
        test.check(kama is not None and kama.signal is not None, "KAMA instantiates")

        vwap = VWAPDeviation.calculate(prices, volumes)
        test.check(vwap is not None and vwap.signal is not None, "VWAP instantiates")

        kalman = StatArbKalman.calculate(prices)
        test.check(kalman is not None and kalman.signal is not None, "Kalman instantiates")

        momentum = MomentumScanner.calculate(prices)
        test.check(momentum is not None and momentum.signal is not None, "Momentum instantiates")
    except Exception as e:
        test.check(False, f"Strategy instantiation error: {e}")
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


def test_position_manager_basic():
    """Smoke test 3: Position manager basic operations"""
    print("\n[SMOKE 3] Position Manager Basic Operations")
    print("-" * 80)

    test = DeploymentSmokeTest()

    try:
        pm = PositionManager(100000.0)
        test.check(pm is not None, "PositionManager instantiates")
        test.check(pm.account_balance == 100000.0, "Account balance set correctly")

        success, reason, pos = pm.open_position("AAPL", 150.0, 100, 147.0, 154.0, "BUY")
        test.check(success, f"Position opens (reason: {reason if not success else 'ok'})")
        test.check(pos is not None and pos.position_id.startswith("POS_"), "Position ID generated")

        closed = pm.check_exits({"AAPL": 155.0})
        test.check(len(closed) == 1, "Position exits on take-profit")

        stats = pm.get_portfolio_stats()
        test.check(stats["closed_trades"] == 1, "Trade counted in stats")
        test.check(stats["win_rate_percent"] == 100.0, "Win rate calculated")
    except Exception as e:
        test.check(False, f"Position manager error: {e}")
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


def test_advanced_strategies():
    """Smoke test 4: Advanced strategies instantiate"""
    print("\n[SMOKE 4] Advanced Strategies")
    print("-" * 80)

    test = DeploymentSmokeTest()

    try:
        orch = AdvancedStrategyOrchestrator()
        test.check(orch is not None, "AdvancedStrategyOrchestrator instantiates")

        prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3
        signals = orch.generate_advanced_signals("AAPL", 0.6, prices, None)

        test.check(len(signals) > 0, f"Advanced signals generated ({len(signals)})")
        test.check(all(-1.0 <= s.value <= 1.0 for s in signals), "All signals in [-1, 1] range")
        test.check(all(0.0 <= s.conviction <= 1.0 for s in signals), "All conviction in [0, 1] range")
    except Exception as e:
        test.check(False, f"Advanced strategies error: {e}")
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


async def test_orchestrator():
    """Smoke test 5: Master orchestrator instantiates and runs"""
    print("\n[SMOKE 5] Master Orchestrator")
    print("-" * 80)

    test = DeploymentSmokeTest()

    try:
        orchestrator = MasterOrchestratorAI(account_balance=100000.0)
        test.check(orchestrator is not None, "MasterOrchestratorAI instantiates")
        test.check(len(orchestrator.agents) == 6, f"6 agents initialized ({len(orchestrator.agents)})")

        market_data = {
            "symbol": "AAPL",
            "prices": [100.0, 101.5, 102.3] * 10,
            "volumes": [1000, 1100, 1050] * 10,
            "regime": "bull",
            "symbol_prices": {"AAPL": 102.3}
        }

        cycle = await orchestrator.execute_trading_cycle(market_data)
        test.check("final_decision" in cycle, "Trading cycle completes")
        test.check("execution_time_ms" in cycle, "Execution time recorded")

        status = await orchestrator.get_system_status()
        test.check("agents" in status, "System status available")
        test.check(len(status.get("agents", {})) == 6, "All agents report status")
    except Exception as e:
        test.check(False, f"Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


def test_error_handling():
    """Smoke test 6: Error handling works"""
    print("\n[SMOKE 6] Error Handling")
    print("-" * 80)

    test = DeploymentSmokeTest()

    try:
        handler = ErrorRecoveryHandler()
        test.check(handler is not None, "ErrorRecoveryHandler instantiates")

        from runtime.error_handling import ErrorSeverity
        handler.log_error(ErrorSeverity.RECOVERABLE, "Test", {})
        test.check(len(handler.error_log) == 1, "Error logging works")
        test.check(handler.error_log[0]["severity"] == "recoverable", "Error severity tracked")
    except Exception as e:
        test.check(False, f"Error handling error: {e}")
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


def test_critical_values():
    """Smoke test 7: Signal values in expected ranges"""
    print("\n[SMOKE 7] Signal Value Ranges")
    print("-" * 80)

    test = DeploymentSmokeTest()

    prices = [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8] * 3
    volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320] * 3

    try:
        results = {
            "RSI-2": RSI2Connors.calculate(prices),
            "IBS": IBSMeanReversion.calculate(106.0, 104.0, 105.8, 105.0),
            "KAMA": KAMATrend.calculate(prices),
            "VWAP": VWAPDeviation.calculate(prices, volumes),
            "Kalman": StatArbKalman.calculate(prices),
            "Momentum": MomentumScanner.calculate(prices),
        }

        all_valid = True
        for name, result in results.items():
            valid_signal = -1.0 <= result.signal <= 1.0
            valid_conviction = 0.0 <= result.conviction <= 1.0
            test.check(valid_signal and valid_conviction, f"{name} values in range")
            all_valid = all_valid and valid_signal and valid_conviction

    except Exception as e:
        test.check(False, f"Signal range error: {e}")
        return False

    passed = test.checks_failed == 0
    print(f"\n  Result: {test.checks_passed}/{test.checks_passed + test.checks_failed} passed")
    return passed


async def run_all_smoke_tests():
    """Execute all smoke tests"""
    print("=" * 80)
    print("SMOKE TESTING — PRE-DEPLOYMENT HEALTH CHECKS")
    print("=" * 80)

    results = []
    start = datetime.now()

    try:
        results.append(("Imports", test_imports()))
        results.append(("Strategy Instantiation", test_strategy_instantiation()))
        results.append(("Position Manager", test_position_manager_basic()))
        results.append(("Advanced Strategies", test_advanced_strategies()))
        results.append(("Master Orchestrator", await test_orchestrator()))
        results.append(("Error Handling", test_error_handling()))
        results.append(("Signal Ranges", test_critical_values()))
    except Exception as e:
        print(f"\n[FAILED] Smoke test error: {e}")
        return False

    elapsed = (datetime.now() - start).total_seconds()

    print("\n" + "=" * 80)
    print("SMOKE TESTING COMPLETE")
    print("=" * 80)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    all_passed = all(r[1] for r in results)

    print(f"\n  Execution time: {elapsed:.2f} seconds")
    print(f"  Speed: < 5 seconds [PASS]" if elapsed < 5 else f"  Speed: {elapsed:.2f}s (expected < 5s)")

    if all_passed:
        print("\n[READY FOR DEPLOYMENT]")
        print("  [OK] All system components operational")
        print("  [OK] All signals in valid ranges")
        print("  [OK] Position manager functional")
        print("  [OK] Multi-agent system running")
        print("  [OK] Error handling active")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_smoke_tests())
    sys.exit(0 if success else 1)

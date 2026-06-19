"""
FUZZ TESTING — Random Input Generation & Edge Case Discovery
Tests system resilience to unexpected/malformed market data
"""

import random
import numpy as np
from typing import List, Dict
from runtime.strategy_implementations import (
    RSI2Connors, IBSMeanReversion, KAMATrend, VWAPDeviation,
    StatArbKalman, MomentumScanner
)
from runtime.position_manager import PositionManager
from runtime.advanced_strategies import AdvancedStrategyOrchestrator


def test_fuzz_price_data():
    """Test strategies with random/extreme price data"""
    print("\n[FUZZ TEST 1] Random Price Data Generation")
    print("-" * 80)

    test_cases = [
        ("Normal", [100.0 + random.gauss(0, 2) for _ in range(20)]),
        ("Extreme up", [100.0 * (1.1 ** i) for i in range(20)]),  # 10% daily moves
        ("Extreme down", [100.0 * (0.9 ** i) for i in range(20)]),  # -10% daily moves
        ("Volatile gaps", [100.0 + random.choice([-5, -3, 0, 3, 5]) for _ in range(20)]),
        ("All same", [100.0] * 20),
        ("Tiny differences", [100.0 + random.uniform(-0.01, 0.01) for _ in range(20)]),
        ("NaN/Inf handling", [100.0] * 19 + [float('inf')]),
    ]

    for name, prices in test_cases:
        try:
            result = RSI2Connors.calculate(prices)
            assert -1.0 <= result.signal <= 1.0, f"Signal out of range: {result.signal}"
            assert 0.0 <= result.conviction <= 1.0, f"Conviction out of range: {result.conviction}"
            print(f"  [OK] {name}: signal={result.signal:.2f}, conviction={result.conviction:.2f}")
        except Exception as e:
            print(f"  [FAIL] {name}: {type(e).__name__}: {str(e)[:50]}")
            raise

    print("[OK] Fuzz testing on price data passed")
    return True


def test_fuzz_volume_data():
    """Test VWAP with random/extreme volume data"""
    print("\n[FUZZ TEST 2] Random Volume Data Generation")
    print("-" * 80)

    prices = [100.0, 101.5, 102.3, 101.8, 103.2] * 4  # 20 prices

    test_cases = [
        ("Normal volumes", [1000 + random.randint(-100, 100) for _ in range(20)]),
        ("Spike volumes", [1000] * 19 + [1000000]),  # Flash crash
        ("Zero volumes", [0] * 20),
        ("Tiny volumes", [0.01] * 20),
        ("Huge volumes", [1e10] * 20),
        ("Mixed zero/huge", [random.choice([0, 1e10]) for _ in range(20)]),
    ]

    for name, volumes in test_cases:
        try:
            result = VWAPDeviation.calculate(prices, volumes)
            assert -1.0 <= result.signal <= 1.0, f"Signal out of range: {result.signal}"
            assert 0.0 <= result.conviction <= 1.0, f"Conviction out of range: {result.conviction}"
            print(f"  [OK] {name}: signal={result.signal:.2f}, conviction={result.conviction:.2f}")
        except Exception as e:
            print(f"  [FAIL] {name}: {type(e).__name__}: {str(e)[:50]}")
            raise

    print("[OK] Fuzz testing on volume data passed")
    return True


def test_fuzz_position_entries():
    """Test position manager with random entry parameters"""
    print("\n[FUZZ TEST 3] Random Position Entry Parameters")
    print("-" * 80)

    pm = PositionManager(100000.0)

    # Fuzz: random entry prices, quantities, stop-losses, take-profits
    symbols = ["AAPL", "MSFT", "NVDA", "GOOG", "AMZN"]
    success_count = 0
    rejection_count = 0

    for i in range(20):
        symbol = random.choice(symbols)
        entry_price = random.uniform(50, 500)
        quantity = random.randint(1, 100)
        sl_offset = random.uniform(0.01, 0.1)  # 1-10% below entry
        tp_offset = random.uniform(0.01, 0.1)  # 1-10% above entry

        success, reason, pos = pm.open_position(
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=entry_price * (1 - sl_offset),
            take_profit=entry_price * (1 + tp_offset),
            side="BUY"
        )

        if success:
            success_count += 1
            assert pos.position_id.startswith("POS_")
            assert pos.entry_price == entry_price
            assert pos.quantity == quantity
        else:
            rejection_count += 1
            # Rejections OK — limits enforced

    print(f"  [OK] Random entries: {success_count} accepted, {rejection_count} rejected")
    print(f"       - Open positions: {len(pm.positions)}")
    print(f"       - Max 5 position limit enforced: {len(pm.positions) <= 5}")

    print("[OK] Fuzz testing on position entries passed")
    return True


def test_fuzz_exit_prices():
    """Test position exits with random price movements"""
    print("\n[FUZZ TEST 4] Random Price Movements (Exit Testing)")
    print("-" * 80)

    pm = PositionManager(100000.0)

    # Open 3 positions
    positions_data = [
        ("AAPL", 150.0, 10),
        ("MSFT", 300.0, 5),
        ("NVDA", 500.0, 2),
    ]

    for symbol, entry_price, qty in positions_data:
        pm.open_position(
            symbol=symbol,
            entry_price=entry_price,
            quantity=qty,
            stop_loss=entry_price * 0.95,
            take_profit=entry_price * 1.05,
            side="BUY"
        )

    # Fuzz: random price movements
    closed_count = 0
    for iteration in range(50):
        # Random prices that might trigger exits
        prices = {
            "AAPL": 150.0 * (0.9 + random.random() * 0.2),  # 90-110% of entry
            "MSFT": 300.0 * (0.9 + random.random() * 0.2),
            "NVDA": 500.0 * (0.9 + random.random() * 0.2),
        }

        closed = pm.check_exits(prices)
        closed_count += len(closed)

        if len(closed) > 0:
            print(f"  Iteration {iteration}: {len(closed)} positions closed")

    print(f"  [OK] Total positions closed across 50 iterations: {closed_count}")
    print(f"       - Win rate: {sum(1 for t in pm.closed_trades if t.pnl > 0) / max(1, len(pm.closed_trades)) * 100:.0f}%")

    print("[OK] Fuzz testing on exit prices passed")
    return True


def test_boundary_values():
    """Boundary value analysis — test at system limits"""
    print("\n[BOUNDARY TEST] System Limits & Edge Cases")
    print("-" * 80)

    pm = PositionManager(100000.0)

    # Test 1: Maximum positions (limit is 5)
    print("  Testing max positions (5)...")
    for i in range(6):
        success, reason, pos = pm.open_position(
            symbol=f"SYM{i}",
            entry_price=100.0 + i,
            quantity=10,
            stop_loss=100.0 + i - 1,
            take_profit=100.0 + i + 1,
            side="BUY"
        )
        if i < 5:
            assert success, f"Should accept position {i+1}/5"
        else:
            assert not success, f"Should reject position 6 (exceeded limit)"

    print(f"  [OK] Max position limit: {len(pm.positions)}/5 enforced")

    # Test 2: Zero/negative quantities
    print("  Testing invalid quantities...")
    success, reason, pos = pm.open_position(
        symbol="TEST",
        entry_price=100.0,
        quantity=0,
        stop_loss=99.0,
        take_profit=101.0,
        side="BUY"
    )
    assert not success, "Should reject zero quantity"
    print(f"  [OK] Zero quantity rejected: {reason}")

    # Test 3: Invalid stop-loss/take-profit
    print("  Testing invalid stops...")
    success, reason, pos = pm.open_position(
        symbol="TEST",
        entry_price=100.0,
        quantity=10,
        stop_loss=101.0,  # ABOVE entry (wrong for BUY)
        take_profit=99.0,  # BELOW entry (wrong for BUY)
        side="BUY"
    )
    assert not success, "Should reject invalid stop/target"
    print(f"  [OK] Invalid stops rejected: {reason}")

    # Test 4: Extreme prices
    print("  Testing extreme prices...")
    extreme_cases = [
        (0.01, 100),  # Penny stock
        (10000, 1),   # Expensive stock
        (0.001, 100),  # Extreme penny
        (1000000, 1),  # Extreme expensive
    ]

    for price, qty in extreme_cases:
        success, reason, pos = pm.open_position(
            symbol="EXTREME",
            entry_price=price,
            quantity=qty,
            stop_loss=price * 0.95,
            take_profit=price * 1.05,
            side="BUY"
        )
        if pos:
            print(f"  [OK] Extreme price ${price}: position opened")

    print("[OK] Boundary value testing passed")
    return True


async def run_all_fuzz_tests():
    """Execute all fuzz testing suites"""
    print("=" * 80)
    print("FUZZ TESTING & BOUNDARY VALUE ANALYSIS")
    print("=" * 80)

    results = []

    try:
        results.append(("Random Price Data", test_fuzz_price_data()))
        results.append(("Random Volume Data", test_fuzz_volume_data()))
        results.append(("Random Position Entries", test_fuzz_position_entries()))
        results.append(("Random Exit Prices", test_fuzz_exit_prices()))
        results.append(("Boundary Value Analysis", test_boundary_values()))
    except Exception as e:
        print(f"\n[FAILED] Error during fuzz testing: {e}")
        return False

    print("\n" + "=" * 80)
    print("FUZZ TESTING COMPLETE")
    print("=" * 80)

    for name, passed in results:
        status = "[OK]" if passed else "[FAILED]"
        print(f"  {status} {name}")

    all_passed = all(r[1] for r in results)
    return all_passed


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_fuzz_tests())
    exit(0 if success else 1)

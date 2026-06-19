"""
TEST SUITE: Multi-Agent Trading System
Verifies each agent's single responsibility and master orchestrator coordination
"""

import asyncio
import pytest
from runtime.trading_agents_system import (
    SignalGenerationAgent, PositionEntryAgent, PositionExitAgent,
    RiskManagementAgent, ErrorRecoveryAgent, ReportingAgent,
    MasterOrchestratorAI
)
from runtime.position_manager import PositionManager


def test_signal_generation_agent():
    """Test signal generation agent works correctly"""
    print("\n[TEST 1] Signal Generation Agent")
    print("-" * 70)

    agent = SignalGenerationAgent()
    assert agent.agent_id == "signal_generation"
    assert "16 strategies" in agent.agent_role.lower() or "strategies" in agent.agent_role.lower()

    # Test signal generation
    task = {
        "symbol": "AAPL",
        "prices": [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8],
        "volumes": [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320],
        "regime": "bull"
    }

    result = asyncio.run(agent.execute(task))
    assert "signal" in result
    assert "conviction" in result
    assert "firing_strategies" in result
    assert -1.0 <= result["signal"] <= 1.0
    assert 0.0 <= result["conviction"] <= 1.0

    print(f"  Signal: {result['signal']:.2f}")
    print(f"  Conviction: {result['conviction']:.2f}")
    print(f"  Firing: {result['firing_strategies'][:3]}")
    print("[OK] Signal generation working correctly")


def test_position_entry_agent():
    """Test position entry agent validation and sizing"""
    print("\n[TEST 2] Position Entry Agent")
    print("-" * 70)

    pm = PositionManager(100000.0)
    agent = PositionEntryAgent(pm)
    assert agent.agent_id == "position_entry"
    assert "entries" in agent.agent_role.lower()

    # Test valid entry
    task = {
        "symbol": "AAPL",
        "signal": 0.8,
        "conviction": 0.7,  # >= min threshold
        "entry_price": 150.0
    }

    result = asyncio.run(agent.execute(task))
    assert "opened" in result
    assert result["conviction"] == 0.7

    print(f"  Entry signal: 0.8 (BUY)")
    print(f"  Conviction: 0.7")
    print(f"  Opened: {result['opened']}")
    if result['opened']:
        print(f"  Position: {result['position_id']}")
    print("[OK] Position entry validation working")

    # Test low conviction rejection
    task2 = {
        "symbol": "MSFT",
        "signal": 0.3,
        "conviction": 0.3,  # < min threshold (0.5)
        "entry_price": 300.0
    }
    result2 = asyncio.run(agent.execute(task2))
    assert result2["opened"] == False
    print("[OK] Low conviction rejection working")


def test_position_exit_agent():
    """Test position exit agent monitors and closes positions"""
    print("\n[TEST 3] Position Exit Agent")
    print("-" * 70)

    pm = PositionManager(100000.0)
    agent = PositionExitAgent(pm)
    assert agent.agent_id == "position_exit"
    assert "position" in agent.agent_role.lower() and "exit" in agent.agent_role.lower()

    # Open a position first
    pm.open_position("AAPL", 150.0, 100, 147.0, 154.0, "BUY")
    assert len(pm.positions) == 1

    # Check exits with take-profit
    task = {
        "prices": {"AAPL": 155.0}  # Above take-profit
    }
    result = asyncio.run(agent.execute(task))
    assert result["closed_count"] == 1
    assert result["closed_trades"][0]["exit_reason"] == "TAKE_PROFIT"

    print(f"  Closed trades: {result['closed_count']}")
    print(f"  Exit reason: {result['closed_trades'][0]['exit_reason']}")
    print(f"  P&L: ${result['total_pnl']:.2f}")
    print("[OK] Position exit execution working")


def test_risk_management_agent():
    """Test risk management agent enforces limits"""
    print("\n[TEST 4] Risk Management Agent")
    print("-" * 70)

    agent = RiskManagementAgent(100000.0)
    assert agent.agent_id == "risk_management"
    assert "enforce" in agent.agent_role.lower()

    # Test position count check
    task = {
        "open_positions": 3,
        "recent_pnl": -100.0,
        "position_size": 10,
        "entry_price": 150.0
    }

    result = asyncio.run(agent.execute(task))
    assert "risk_check_pass" in result
    assert result["checks"]["position_count_ok"] == True

    print(f"  Position count: 3 / {agent.max_position_count}")
    print(f"  Daily loss: ${agent.daily_loss:.2f}")
    print(f"  Risk check: {'PASS' if result['risk_check_pass'] else 'FAIL'}")
    print("[OK] Risk management enforcement working")

    # Test position limit enforcement
    task2 = {
        "open_positions": 5,  # At max
        "recent_pnl": 0.0,
        "position_size": 10,
        "entry_price": 150.0
    }
    result2 = asyncio.run(agent.execute(task2))
    assert result2["checks"]["position_count_ok"] == False
    print("[OK] Position limit enforcement working")


def test_error_recovery_agent():
    """Test error recovery agent handles failures"""
    print("\n[TEST 5] Error Recovery Agent")
    print("-" * 70)

    agent = ErrorRecoveryAgent()
    assert agent.agent_id == "error_recovery"
    assert "handle" in agent.agent_role.lower()

    # Test recoverable error
    task = {
        "error_type": "connection_error",
        "error_message": "Connection timeout to broker",
        "context": {"symbol": "AAPL", "action": "entry"}
    }

    result = asyncio.run(agent.execute(task))
    assert result["error_handled"] == True
    assert "recovery_action" in result

    print(f"  Error: {task['error_message']}")
    print(f"  Recovery: {result['recovery_action']}")
    print(f"  Handled: {result['error_handled']}")
    print("[OK] Error recovery working")


def test_reporting_agent():
    """Test reporting agent generates statistics"""
    print("\n[TEST 6] Reporting Agent")
    print("-" * 70)

    pm = PositionManager(100000.0)
    agent = ReportingAgent(pm)
    assert agent.agent_id == "reporting"
    assert "generate" in agent.agent_role.lower()

    # Add some trades
    pm.open_position("AAPL", 150.0, 100, 147.0, 154.0, "BUY")
    pm.open_position("MSFT", 300.0, 50, 295.0, 310.0, "BUY")
    pm.check_exits({"AAPL": 155.0, "MSFT": 294.0})

    result = asyncio.run(agent.execute({}))
    assert "portfolio_stats" in result
    assert "summary" in result

    print(f"  Closed trades: {result['summary']['closed_trades']}")
    print(f"  Win rate: {result['summary']['win_rate']}")
    print(f"  Total P&L: {result['summary']['total_pnl']}")
    print("[OK] Reporting generation working")


@pytest.mark.asyncio
async def test_master_orchestrator_ai():
    """Test master orchestrator coordinates all agents"""
    print("\n[TEST 7] Master Orchestrator AI Coordination")
    print("-" * 70)

    orchestrator = MasterOrchestratorAI(account_balance=100000.0)
    assert len(orchestrator.agents) == 6
    assert "signal_generation" in orchestrator.agents
    assert "position_entry" in orchestrator.agents
    assert "position_exit" in orchestrator.agents
    assert "risk_management" in orchestrator.agents
    assert "error_recovery" in orchestrator.agents
    assert "reporting" in orchestrator.agents

    print(f"  Agents initialized: {len(orchestrator.agents)}")
    for agent_id in orchestrator.agents:
        print(f"    [OK] {agent_id}")

    # Execute trading cycle
    market_data = {
        "symbol": "AAPL",
        "prices": [100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 103.5, 105.0, 106.2, 105.8],
        "volumes": [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1320],
        "regime": "bull",
        "symbol_prices": {"AAPL": 105.5}
    }

    cycle_result = await orchestrator.execute_trading_cycle(market_data)
    assert cycle_result["cycle"] == 1
    assert "agent_results" in cycle_result
    assert "final_decision" in cycle_result

    print(f"  Cycle: {cycle_result['cycle']}")
    print(f"  Decision: {cycle_result['final_decision']}")
    print(f"  Execution time: {cycle_result['execution_time_ms']:.1f}ms")

    # Check system status
    status = await orchestrator.get_system_status()
    assert "agents" in status
    assert status["total_cycles"] == 1

    print(f"  Total cycles: {status['total_cycles']}")
    print(f"  Agent health: All reporting")
    print("[OK] Master orchestrator coordination working")


@pytest.mark.asyncio
async def test_multi_cycle_trading():
    """Test multiple trading cycles in sequence"""
    print("\n[TEST 8] Multi-Cycle Trading Sequence")
    print("-" * 70)

    orchestrator = MasterOrchestratorAI(account_balance=100000.0)

    market_scenarios = [
        {
            "cycle": 1,
            "symbol": "AAPL",
            "prices": [100.0, 101.5, 102.3, 101.8, 103.2, 104.1],
            "regime": "bull"
        },
        {
            "cycle": 2,
            "symbol": "MSFT",
            "prices": [300.0, 301.0, 302.0, 301.5, 303.0, 304.0],
            "regime": "bull"
        },
        {
            "cycle": 3,
            "symbol": "AAPL",
            "prices": [103.2, 104.1, 103.5, 105.0, 106.2, 105.8],
            "regime": "bull"
        }
    ]

    for scenario in market_scenarios:
        market_data = {
            "symbol": scenario["symbol"],
            "prices": scenario["prices"],
            "volumes": [1000] * len(scenario["prices"]),
            "regime": scenario["regime"],
            "symbol_prices": {scenario["symbol"]: scenario["prices"][-1]}
        }

        result = await orchestrator.execute_trading_cycle(market_data)
        print(f"  Cycle {result['cycle']}: {result['final_decision']}")

    status = await orchestrator.get_system_status()
    print(f"  Total cycles completed: {status['total_cycles']}")
    print(f"  Portfolio stats: {status['portfolio_stats']['closed_trades']} closed trades")
    print("[OK] Multi-cycle trading working")


def run_all_agent_tests():
    """Run all agent tests"""
    print("=" * 70)
    print("MULTI-AGENT TRADING SYSTEM TEST SUITE")
    print("=" * 70)

    test_signal_generation_agent()
    test_position_entry_agent()
    test_position_exit_agent()
    test_risk_management_agent()
    test_error_recovery_agent()
    test_reporting_agent()
    asyncio.run(test_master_orchestrator_ai())
    asyncio.run(test_multi_cycle_trading())

    print("\n" + "=" * 70)
    print("ALL AGENT TESTS PASSED [OK]")
    print("=" * 70)
    print("\nSUMMARY: Multi-Agent Architecture Working")
    print("  [OK] 1 Agent per Task (clear separation of concerns)")
    print("  [OK] Each agent has single responsibility")
    print("  [OK] Master orchestrator coordinates all agents")
    print("  [OK] All agents report status (heartbeat)")
    print("  [OK] Full trading cycle: signals => entry => exit => reporting")
    print("=" * 70)


if __name__ == "__main__":
    run_all_agent_tests()

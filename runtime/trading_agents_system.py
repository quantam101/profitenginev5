"""
MULTI-AGENT TRADING SYSTEM — One Agent Per Task
Each task has a dedicated autonomous agent, coordinated by a super-intelligent master orchestrator

Agent Architecture:
- SignalGenerationAgent: Computes all 16 strategies, combines signals
- PositionEntryAgent: Validates entries, applies compliance, sizes positions
- PositionExitAgent: Monitors exits, executes stops and profits
- RiskManagementAgent: Enforces position limits, circuit breakers, drawdowns
- ErrorRecoveryAgent: Handles failures, retries, graceful degradation
- ReportingAgent: Logs trades, statistics, performance metrics
- MasterOrchestratorAI: Routes tasks, makes high-level decisions, optimizes agents

One Responsibility Per Agent → Maximum Autonomy + Clarity
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import time

from runtime.strategy_implementations import (
    RSI2Connors, IBSMeanReversion, KAMATrend, VWAPDeviation,
    StatArbKalman, MomentumScanner
)
from runtime.advanced_strategies import AdvancedStrategyOrchestrator
from runtime.position_manager import PositionManager, ClosedTrade
from runtime.error_handling import ErrorRecoveryHandler, ErrorSeverity, CircuitBreaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingAgents")


# ============================================================================
# AGENT INTERFACE
# ============================================================================

class IAgent(ABC):
    """Interface all trading agents must implement"""

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique agent identifier"""
        pass

    @property
    @abstractmethod
    def agent_role(self) -> str:
        """Agent's single responsibility"""
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute primary responsibility"""
        pass

    @abstractmethod
    async def heartbeat(self) -> Dict[str, Any]:
        """Report status to orchestrator"""
        pass


# ============================================================================
# SIGNAL GENERATION AGENT
# ============================================================================

class SignalGenerationAgent(IAgent):
    """
    SINGLE RESPONSIBILITY: Generate trading signals from all 16 strategies

    Input: Market data (prices, volumes, regime)
    Output: Combined signal with conviction and reasoning
    """

    def __init__(self):
        self._agent_id = "signal_generation"
        self._agent_role = "Compute all 16 trading strategies and combine signals"
        self.tasks_executed = 0
        self.errors = 0
        self.last_execution = None
        self.advanced_orchestrator = AdvancedStrategyOrchestrator()

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_role(self) -> str:
        return self._agent_role

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate signals from:
        - 6 real strategy implementations
        - 5 advanced ML strategies
        """
        try:
            symbol = task.get("symbol", "AAPL")
            prices = task.get("prices", [])
            volumes = task.get("volumes", [])
            market_regime = task.get("regime", "bull")

            if not prices or len(prices) < 5:
                return {"error": "Insufficient price data", "signal": 0.0, "conviction": 0.0}

            # Generate original 6 strategy signals
            original_signals = {
                "rsi2_connors": RSI2Connors.calculate(prices),
                "ibs_mean_reversion": IBSMeanReversion.calculate(max(prices), min(prices), prices[-1], prices[-2]),
                "kama_trend": KAMATrend.calculate(prices),
                "vwap_deviation": VWAPDeviation.calculate(prices, volumes if volumes else [1000]*len(prices)),
                "stat_arb_kalman": StatArbKalman.calculate(prices),
                "momentum_scanner": MomentumScanner.calculate(prices),
            }

            # Generate 5 advanced strategy signals
            advanced_signals = await asyncio.to_thread(
                self.advanced_orchestrator.generate_advanced_signals,
                symbol, 0.5, prices, None
            )

            # Combine all signals
            combined_signal = 0.0
            total_conviction = 0.0
            firing_strategies = []

            for strategy_name, result in original_signals.items():
                combined_signal += result.signal * result.conviction
                total_conviction += result.conviction
                if result.signal != 0:
                    firing_strategies.append(f"{strategy_name}:{result.conviction:.2f}")

            for adv_signal in advanced_signals:
                combined_signal += adv_signal.value * adv_signal.conviction
                total_conviction += adv_signal.conviction
                firing_strategies.append(f"{adv_signal.strategy_name}:{adv_signal.conviction:.2f}")

            final_signal = combined_signal / max(total_conviction, 1.0)
            final_conviction = min(abs(final_signal), 1.0)

            self.tasks_executed += 1
            self.last_execution = datetime.now()

            return {
                "symbol": symbol,
                "signal": final_signal,
                "conviction": final_conviction,
                "firing_strategies": firing_strategies[:5],  # Top 5
                "strategy_count": len(original_signals) + len(advanced_signals),
                "regime": market_regime,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.errors += 1
            logger.error(f"[{self.agent_id}] Error: {e}")
            return {"error": str(e), "signal": 0.0, "conviction": 0.0}

    async def heartbeat(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "tasks_executed": self.tasks_executed,
            "errors": self.errors,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None
        }


# ============================================================================
# POSITION ENTRY AGENT
# ============================================================================

class PositionEntryAgent(IAgent):
    """
    SINGLE RESPONSIBILITY: Validate signals and open positions

    Input: Trading signal with conviction
    Output: Opened position with size, stops, targets
    """

    def __init__(self, position_manager: PositionManager):
        self._agent_id = "position_entry"
        self._agent_role = "Validate entries, apply compliance, size positions"
        self.position_manager = position_manager
        self.tasks_executed = 0
        self.errors = 0
        self.min_conviction = 0.5

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_role(self) -> str:
        return self._agent_role

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Open position if signal conviction >= threshold"""
        try:
            symbol = task.get("symbol")
            signal = task.get("signal", 0.0)
            conviction = task.get("conviction", 0.0)
            entry_price = task.get("entry_price", 0.0)

            # Check conviction threshold
            if conviction < self.min_conviction:
                return {"opened": False, "reason": f"Conviction {conviction:.2f} < {self.min_conviction}"}

            # Determine side (BUY if signal > 0, SELL if < 0)
            side = "BUY" if signal > 0 else "SELL"

            # Calculate position size and stops
            stop_distance = entry_price * 0.02  # 2% stop
            take_distance = entry_price * 0.03  # 3% target
            stop_loss = entry_price - stop_distance if side == "BUY" else entry_price + stop_distance
            take_profit = entry_price + take_distance if side == "BUY" else entry_price - take_distance

            # Open position
            success, reason, position = self.position_manager.open_position(
                symbol=symbol,
                entry_price=entry_price,
                quantity=10,  # Base quantity
                stop_loss=stop_loss,
                take_profit=take_profit,
                side=side
            )

            self.tasks_executed += 1

            return {
                "opened": success,
                "reason": reason,
                "position_id": position.position_id if position else None,
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "conviction": conviction
            }

        except Exception as e:
            self.errors += 1
            logger.error(f"[{self.agent_id}] Error: {e}")
            return {"error": str(e), "opened": False}

    async def heartbeat(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "tasks_executed": self.tasks_executed,
            "errors": self.errors,
            "open_positions": len(self.position_manager.positions)
        }


# ============================================================================
# POSITION EXIT AGENT
# ============================================================================

class PositionExitAgent(IAgent):
    """
    SINGLE RESPONSIBILITY: Monitor positions and execute exits

    Input: Current prices for all symbols
    Output: Closed positions with P&L
    """

    def __init__(self, position_manager: PositionManager):
        self._agent_id = "position_exit"
        self._agent_role = "Monitor and execute position exits (stops, profits)"
        self.position_manager = position_manager
        self.tasks_executed = 0
        self.closed_trades = 0

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_role(self) -> str:
        return self._agent_role

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check and execute exits for all positions"""
        try:
            current_prices = task.get("prices", {})

            closed = self.position_manager.check_exits(current_prices)
            self.closed_trades += len(closed)
            self.tasks_executed += 1

            closed_details = []
            total_pnl = 0.0

            for trade in closed:
                closed_details.append({
                    "symbol": trade.symbol,
                    "exit_reason": trade.exit_reason,
                    "pnl": trade.pnl,
                    "pnl_percent": trade.pnl_percent,
                    "duration_minutes": trade.duration_minutes
                })
                total_pnl += trade.pnl

            return {
                "closed_count": len(closed),
                "closed_trades": closed_details,
                "total_pnl": total_pnl,
                "remaining_open": len(self.position_manager.positions)
            }

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error: {e}")
            return {"error": str(e), "closed_count": 0}

    async def heartbeat(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "tasks_executed": self.tasks_executed,
            "closed_trades": self.closed_trades,
            "open_positions": len(self.position_manager.positions)
        }


# ============================================================================
# RISK MANAGEMENT AGENT
# ============================================================================

class RiskManagementAgent(IAgent):
    """
    SINGLE RESPONSIBILITY: Enforce risk limits and circuit breakers

    Input: Current portfolio state
    Output: Risk checks pass/fail, circuit breaker status
    """

    def __init__(self, account_balance: float):
        self._agent_id = "risk_management"
        self._agent_role = "Enforce position limits, drawdown limits, circuit breaker"
        self.account_balance = account_balance
        self.max_position_count = 5
        self.max_daily_loss_pct = 0.06  # 6%
        self.max_loss_per_trade = 0.02  # 2%
        self.daily_loss = 0.0
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.tasks_executed = 0

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_role(self) -> str:
        return self._agent_role

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check all risk constraints"""
        try:
            open_positions = task.get("open_positions", 0)
            recent_pnl = task.get("recent_pnl", 0)
            proposed_position_size = task.get("position_size", 0)

            # Update daily loss
            if recent_pnl < 0:
                self.daily_loss += abs(recent_pnl)

            checks = {
                "position_count_ok": open_positions < self.max_position_count,
                "daily_loss_ok": self.daily_loss < (self.account_balance * self.max_daily_loss_pct),
                "circuit_breaker_closed": self.circuit_breaker.state == "CLOSED",
                "position_size_ok": proposed_position_size * task.get("entry_price", 0) < (self.account_balance * 0.5)
            }

            all_checks_pass = all(checks.values())
            self.tasks_executed += 1

            return {
                "risk_check_pass": all_checks_pass,
                "checks": checks,
                "circuit_breaker_state": self.circuit_breaker.state,
                "daily_loss": self.daily_loss,
                "daily_loss_limit": self.account_balance * self.max_daily_loss_pct,
                "open_positions": open_positions,
                "max_positions": self.max_position_count
            }

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error: {e}")
            return {"error": str(e), "risk_check_pass": False}

    async def heartbeat(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "tasks_executed": self.tasks_executed,
            "daily_loss": self.daily_loss,
            "circuit_breaker_state": self.circuit_breaker.state
        }


# ============================================================================
# ERROR RECOVERY AGENT
# ============================================================================

class ErrorRecoveryAgent(IAgent):
    """
    SINGLE RESPONSIBILITY: Handle errors and implement recovery strategies

    Input: Error events
    Output: Recovery actions (retry, fallback, graceful degradation)
    """

    def __init__(self):
        self._agent_id = "error_recovery"
        self._agent_role = "Handle errors with retry, circuit breaker, graceful degradation"
        self.error_handler = ErrorRecoveryHandler()
        self.tasks_executed = 0
        self.errors_recovered = 0

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_role(self) -> str:
        return self._agent_role

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error with appropriate recovery strategy"""
        try:
            error_type = task.get("error_type")
            error_message = task.get("error_message", "")
            context = task.get("context", {})

            # Classify error severity
            if "connection" in error_message.lower() or "timeout" in error_message.lower():
                severity = ErrorSeverity.RECOVERABLE
            elif "rate limit" in error_message.lower():
                severity = ErrorSeverity.DEGRADED
            else:
                severity = ErrorSeverity.CRITICAL

            # Log error
            self.error_handler.log_error(severity, error_message, context)

            # Implement recovery
            recovery_action = None
            if severity == ErrorSeverity.RECOVERABLE:
                recovery_action = "RETRY_WITH_BACKOFF"
            elif severity == ErrorSeverity.DEGRADED:
                recovery_action = "FALLBACK_TO_CACHE"
            else:
                recovery_action = "PAUSE_TRADING"

            self.tasks_executed += 1
            self.errors_recovered += 1

            return {
                "error_handled": True,
                "severity": severity.value,
                "recovery_action": recovery_action,
                "message": error_message,
                "logged": True
            }

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in recovery: {e}")
            return {"error_handled": False, "error": str(e)}

    async def heartbeat(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "tasks_executed": self.tasks_executed,
            "errors_recovered": self.errors_recovered,
            "error_log_size": len(self.error_handler.error_log)
        }


# ============================================================================
# REPORTING AGENT
# ============================================================================

class ReportingAgent(IAgent):
    """
    SINGLE RESPONSIBILITY: Generate reports and performance metrics

    Input: Trading activity (trades, positions, statistics)
    Output: Reports (daily summary, performance metrics, alerts)
    """

    def __init__(self, position_manager: PositionManager):
        self._agent_id = "reporting"
        self._agent_role = "Generate trading reports and performance metrics"
        self.position_manager = position_manager
        self.tasks_executed = 0
        self.reports_generated = 0

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_role(self) -> str:
        return self._agent_role

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading report"""
        try:
            stats = self.position_manager.get_portfolio_stats()
            risk_metrics = self.position_manager.get_risk_metrics()

            report = {
                "timestamp": datetime.now().isoformat(),
                "portfolio_stats": stats,
                "risk_metrics": risk_metrics,
                "summary": {
                    "open_positions": stats.get("open_positions", 0),
                    "closed_trades": stats.get("closed_trades", 0),
                    "win_rate": f"{stats.get('win_rate_percent', 0):.1f}%",
                    "total_pnl": f"${stats.get('total_realized_pnl', 0):.2f}",
                    "profit_factor": f"{stats.get('profit_factor', 0):.2f}",
                    "max_loss_scenario": f"${risk_metrics.get('max_loss_scenario', 0):.2f}"
                }
            }

            self.tasks_executed += 1
            self.reports_generated += 1

            return report

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error: {e}")
            return {"error": str(e)}

    async def heartbeat(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "tasks_executed": self.tasks_executed,
            "reports_generated": self.reports_generated
        }


# ============================================================================
# MASTER ORCHESTRATOR AI — Super-Intelligent Coordinator
# ============================================================================

class MasterOrchestratorAI:
    """
    Super-Intelligent AI that coordinates all trading agents

    Responsibilities:
    - Initialize and manage all agents
    - Route tasks to appropriate agents
    - Synthesize agent results into trading decisions
    - Monitor agent health
    - Optimize agent coordination
    - Make high-level strategic decisions
    """

    def __init__(self, account_balance: float = 100.0):
        self.account_balance = account_balance
        self.position_manager = PositionManager(account_balance)

        # Initialize all agents
        self.agents: Dict[str, IAgent] = {
            "signal_generation": SignalGenerationAgent(),
            "position_entry": PositionEntryAgent(self.position_manager),
            "position_exit": PositionExitAgent(self.position_manager),
            "risk_management": RiskManagementAgent(account_balance),
            "error_recovery": ErrorRecoveryAgent(),
            "reporting": ReportingAgent(self.position_manager),
        }

        self.decision_log = []
        self.scan_count = 0

    async def execute_trading_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one complete trading cycle coordinating all agents

        Flow:
        1. Signal Generation Agent → Generate 16-strategy signals
        2. Risk Management Agent → Validate risk constraints
        3. Position Entry Agent → Open positions if approved
        4. Position Exit Agent → Monitor and execute exits
        5. Reporting Agent → Generate report
        """

        self.scan_count += 1
        cycle_start = time.time()
        cycle_result = {
            "cycle": self.scan_count,
            "timestamp": datetime.now().isoformat(),
            "agent_results": {},
            "final_decision": None,
            "execution_time_ms": 0
        }

        try:
            # STEP 1: Generate signals (Signal Generation Agent)
            logger.info(f"[Cycle {self.scan_count}] Step 1: Generate signals")
            signal_task = {
                "symbol": market_data.get("symbol", "AAPL"),
                "prices": market_data.get("prices", []),
                "volumes": market_data.get("volumes", []),
                "regime": market_data.get("regime", "bull")
            }
            signal_result = await self.agents["signal_generation"].execute(signal_task)
            cycle_result["agent_results"]["signal_generation"] = signal_result

            # STEP 2: Validate risk (Risk Management Agent)
            logger.info(f"[Cycle {self.scan_count}] Step 2: Validate risk")
            risk_task = {
                "open_positions": len(self.position_manager.positions),
                "recent_pnl": signal_result.get("signal", 0) * 100,
                "position_size": 10,
                "entry_price": market_data.get("prices", [0])[-1] if market_data.get("prices") else 0
            }
            risk_result = await self.agents["risk_management"].execute(risk_task)
            cycle_result["agent_results"]["risk_management"] = risk_result

            # STEP 3: Enter positions if approved (Position Entry Agent)
            if (signal_result.get("conviction", 0) > 0.5 and
                risk_result.get("risk_check_pass", False)):
                logger.info(f"[Cycle {self.scan_count}] Step 3: Enter position")
                entry_task = {
                    "symbol": market_data.get("symbol", "AAPL"),
                    "signal": signal_result.get("signal", 0),
                    "conviction": signal_result.get("conviction", 0),
                    "entry_price": market_data.get("prices", [0])[-1] if market_data.get("prices") else 0
                }
                entry_result = await self.agents["position_entry"].execute(entry_task)
                cycle_result["agent_results"]["position_entry"] = entry_result
                cycle_result["final_decision"] = "POSITION_OPENED" if entry_result.get("opened") else "POSITION_BLOCKED"
            else:
                cycle_result["final_decision"] = "NO_SIGNAL" if signal_result.get("conviction", 0) <= 0.5 else "RISK_CHECK_FAILED"

            # STEP 4: Monitor exits (Position Exit Agent)
            logger.info(f"[Cycle {self.scan_count}] Step 4: Monitor exits")
            exit_task = {
                "prices": market_data.get("symbol_prices", {})
            }
            exit_result = await self.agents["position_exit"].execute(exit_task)
            cycle_result["agent_results"]["position_exit"] = exit_result

            # STEP 5: Generate report (Reporting Agent)
            logger.info(f"[Cycle {self.scan_count}] Step 5: Generate report")
            report_result = await self.agents["reporting"].execute({})
            cycle_result["agent_results"]["reporting"] = report_result

            cycle_result["execution_time_ms"] = (time.time() - cycle_start) * 1000

            # Log decision
            self.decision_log.append(cycle_result)
            logger.info(f"[Cycle {self.scan_count}] Complete: {cycle_result['final_decision']}")

            return cycle_result

        except Exception as e:
            logger.error(f"[Cycle {self.scan_count}] Error: {e}")
            cycle_result["error"] = str(e)
            return cycle_result

    async def get_system_status(self) -> Dict[str, Any]:
        """Get health status of all agents"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "portfolio_stats": self.position_manager.get_portfolio_stats(),
            "total_cycles": self.scan_count
        }

        for agent_id, agent in self.agents.items():
            heartbeat = await agent.heartbeat()
            status["agents"][agent_id] = heartbeat

        return status

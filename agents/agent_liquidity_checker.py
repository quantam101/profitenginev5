"""Agent Liquidity Checker — Minimum Liquidity Validation System

Validates portfolio and position liquidity constraints to ensure sufficient
capital availability for trading operations and risk management execution.

Liquidity Validation Gates:
1. Portfolio Liquidity Floor - Enforces minimum portfolio liquidity
2. Position Size Limits - Validates position sizing vs liquidity pool
3. Emergency Exit Capacity - Confirms ability to exit positions under stress
4. Cash Reserve Requirements - Enforces minimum cash allocation
5. Drawdown Protection - Validates reserves for adverse price movements
6. Spread Tolerance Limits - Ensures adequate spread capacity for orders
7. Concentration Risk Limits - Prevents excessive single-position allocation
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AgentLiquidityChecker")


class LiquidityStatus(Enum):
	"""Liquidity validation result status."""
	PASS = "pass"
	FAIL = "fail"
	WARN = "warn"
	SKIP = "skip"


class LiquiditySeverity(Enum):
	"""Liquidity check failure severity level."""
	CRITICAL = "critical"
	HIGH = "high"
	MEDIUM = "medium"
	LOW = "low"


@dataclass
class LiquidityResult:
	"""Individual liquidity validation result."""
	check_id: str
	check_name: str
	status: LiquidityStatus
	severity: LiquiditySeverity
	message: str
	details: Dict[str, Any] = field(default_factory=dict)
	timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
	execution_time_ms: float = 0.0

	def to_dict(self) -> Dict[str, Any]:
		"""Convert result to dictionary."""
		return {
			"check_id": self.check_id,
			"check_name": self.check_name,
			"status": self.status.value,
			"severity": self.severity.value,
			"message": self.message,
			"details": self.details,
			"timestamp": self.timestamp,
			"execution_time_ms": self.execution_time_ms,
		}


@dataclass
class LiquidityReport:
	"""Complete liquidity validation report."""
	timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
	total_checks: int = 0
	passed: int = 0
	failed: int = 0
	warned: int = 0
	skipped: int = 0
	critical_failures: int = 0
	results: List[LiquidityResult] = field(default_factory=list)
	total_execution_time_ms: float = 0.0
	validation_pass: bool = False
	portfolio_liquidity_pct: float = 0.0
	available_capital: float = 0.0
	minimum_reserve_usd: float = 0.0

	def to_dict(self) -> Dict[str, Any]:
		"""Convert report to dictionary."""
		return {
			"timestamp": self.timestamp,
			"total_checks": self.total_checks,
			"passed": self.passed,
			"failed": self.failed,
			"warned": self.warned,
			"skipped": self.skipped,
			"critical_failures": self.critical_failures,
			"validation_pass": self.validation_pass,
			"portfolio_liquidity_pct": self.portfolio_liquidity_pct,
			"available_capital": self.available_capital,
			"minimum_reserve_usd": self.minimum_reserve_usd,
			"total_execution_time_ms": self.total_execution_time_ms,
			"results": [r.to_dict() for r in self.results],
		}


class AgentLiquidityChecker:
	"""Validates portfolio and position liquidity constraints."""

	def __init__(
		self,
		portfolio_value_usd: float = 100000.0,
		min_liquidity_pct: float = 0.15,
		min_cash_reserve_usd: float = 5000.0,
		env: Optional[Dict[str, str]] = None,
		timeout_sec: int = 30,
	):
		"""Initialize liquidity checker.

		Args:
			portfolio_value_usd: Total portfolio value in USD
			min_liquidity_pct: Minimum liquidity requirement (0.0-1.0)
			min_cash_reserve_usd: Minimum cash reserve required
			env: Environment variables dict (defaults to os.environ)
			timeout_sec: Overall validation timeout in seconds
		"""
		self.portfolio_value_usd = portfolio_value_usd
		self.min_liquidity_pct = min_liquidity_pct
		self.min_cash_reserve_usd = min_cash_reserve_usd
		self.env = env or os.environ
		self.timeout_sec = timeout_sec
		self.logger = logging.getLogger("AgentLiquidityChecker")

	async def check_liquidity(self) -> Dict[str, Any]:
		"""Perform comprehensive liquidity check.

		Returns:
			Dictionary with liquidity metrics and status
		"""
		report = await self.validate()
		return report.to_dict()

	async def validate(self) -> LiquidityReport:
		"""Validate all liquidity constraints in parallel.

		Returns:
			LiquidityReport with complete liquidity validation results
		"""
		start_time = asyncio.get_event_loop().time()

		# Create all liquidity validation tasks
		tasks = [
			self._validate_portfolio_floor(),
			self._validate_position_limits(),
			self._validate_emergency_exit(),
			self._validate_cash_reserve(),
			self._validate_drawdown_protection(),
			self._validate_spread_tolerance(),
			self._validate_concentration_risk(),
		]

		# Execute all checks in parallel with timeout
		try:
			results = await asyncio.wait_for(
				asyncio.gather(*tasks, return_exceptions=True),
				timeout=self.timeout_sec
			)
		except asyncio.TimeoutError:
			self.logger.error(f"Liquidity validation timeout after {self.timeout_sec}s")
			results = [
				LiquidityResult(
					check_id="timeout",
					check_name="Validation Timeout",
					status=LiquidityStatus.FAIL,
					severity=LiquiditySeverity.CRITICAL,
					message=f"Validation exceeded {self.timeout_sec}s timeout"
				)
			]

		# Build report from results
		report = LiquidityReport()
		report.total_checks = len([r for r in results if isinstance(r, LiquidityResult)])
		report.available_capital = self.portfolio_value_usd * (1 - self.min_liquidity_pct)
		report.minimum_reserve_usd = self.min_cash_reserve_usd
		report.portfolio_liquidity_pct = self.min_liquidity_pct * 100

		for result in results:
			if not isinstance(result, LiquidityResult):
				result = LiquidityResult(
					check_id="exception",
					check_name="Exception Handler",
					status=LiquidityStatus.FAIL,
					severity=LiquiditySeverity.CRITICAL,
					message=f"Liquidity check exception: {str(result)}"
				)

			report.results.append(result)

			# Update counts
			if result.status == LiquidityStatus.PASS:
				report.passed += 1
			elif result.status == LiquidityStatus.FAIL:
				report.failed += 1
				if result.severity == LiquiditySeverity.CRITICAL:
					report.critical_failures += 1
			elif result.status == LiquidityStatus.WARN:
				report.warned += 1
			elif result.status == LiquidityStatus.SKIP:
				report.skipped += 1

		# Determine overall validation result
		report.validation_pass = (
			report.critical_failures == 0 and
			report.failed == 0
		)

		report.total_execution_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
		return report

	async def _validate_portfolio_floor(self) -> LiquidityResult:
		"""Check minimum portfolio liquidity requirement."""
		start = asyncio.get_event_loop().time()
		try:
			current_liquidity_pct = float(
				self.env.get("CURRENT_LIQUIDITY_PCT", str(self.min_liquidity_pct))
			)

			if current_liquidity_pct >= self.min_liquidity_pct:
				status = LiquidityStatus.PASS
				message = f"Portfolio liquidity floor met: {current_liquidity_pct:.1%}"
			else:
				status = LiquidityStatus.FAIL
				message = f"Portfolio liquidity BELOW minimum: {current_liquidity_pct:.1%} < {self.min_liquidity_pct:.1%}"

			return LiquidityResult(
				check_id="portfolio_floor",
				check_name="Portfolio Liquidity Floor",
				status=status,
				severity=LiquiditySeverity.CRITICAL,
				message=message,
				details={
					"current_liquidity_pct": current_liquidity_pct,
					"required_liquidity_pct": self.min_liquidity_pct,
					"portfolio_value_usd": self.portfolio_value_usd,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="portfolio_floor",
				check_name="Portfolio Liquidity Floor",
				status=LiquidityStatus.FAIL,
				severity=LiquiditySeverity.CRITICAL,
				message=f"Portfolio floor validation failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

	async def _validate_position_limits(self) -> LiquidityResult:
		"""Check position size limits vs liquidity pool."""
		start = asyncio.get_event_loop().time()
		try:
			max_position_pct = float(self.env.get("MAX_POSITION_PCT", "0.10"))
			largest_position_pct = float(self.env.get("LARGEST_POSITION_PCT", "0.05"))

			if largest_position_pct <= max_position_pct:
				status = LiquidityStatus.PASS
				message = f"Position size within limits: {largest_position_pct:.1%} <= {max_position_pct:.1%}"
			else:
				status = LiquidityStatus.FAIL
				message = f"Position EXCEEDS limit: {largest_position_pct:.1%} > {max_position_pct:.1%}"

			return LiquidityResult(
				check_id="position_limits",
				check_name="Position Size Limits",
				status=status,
				severity=LiquiditySeverity.HIGH,
				message=message,
				details={
					"max_position_pct": max_position_pct,
					"largest_position_pct": largest_position_pct,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="position_limits",
				check_name="Position Size Limits",
				status=LiquidityStatus.WARN,
				severity=LiquiditySeverity.HIGH,
				message=f"Position limit check failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

	async def _validate_emergency_exit(self) -> LiquidityResult:
		"""Validate emergency exit capacity."""
		start = asyncio.get_event_loop().time()
		try:
			can_exit_all_positions = self.env.get("CAN_EXIT_ALL_POSITIONS", "true").lower() == "true"
			exit_time_minutes = int(self.env.get("EMERGENCY_EXIT_TIME_MIN", "5"))

			if can_exit_all_positions:
				status = LiquidityStatus.PASS
				message = f"Emergency exit capable within {exit_time_minutes} minutes"
			else:
				status = LiquidityStatus.FAIL
				message = "Emergency exit NOT possible - positions potentially illiquid"

			return LiquidityResult(
				check_id="emergency_exit",
				check_name="Emergency Exit Capacity",
				status=status,
				severity=LiquiditySeverity.CRITICAL,
				message=message,
				details={
					"can_exit_all_positions": can_exit_all_positions,
					"exit_time_minutes": exit_time_minutes,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="emergency_exit",
				check_name="Emergency Exit Capacity",
				status=LiquidityStatus.WARN,
				severity=LiquiditySeverity.CRITICAL,
				message=f"Emergency exit check failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

	async def _validate_cash_reserve(self) -> LiquidityResult:
		"""Validate minimum cash reserve requirements."""
		start = asyncio.get_event_loop().time()
		try:
			current_cash_usd = float(self.env.get("CURRENT_CASH_USD", "0"))

			if current_cash_usd >= self.min_cash_reserve_usd:
				status = LiquidityStatus.PASS
				message = f"Cash reserve adequate: ${current_cash_usd:,.2f}"
			else:
				status = LiquidityStatus.FAIL
				message = f"Cash reserve INSUFFICIENT: ${current_cash_usd:,.2f} < ${self.min_cash_reserve_usd:,.2f}"

			return LiquidityResult(
				check_id="cash_reserve",
				check_name="Cash Reserve Requirements",
				status=status,
				severity=LiquiditySeverity.CRITICAL,
				message=message,
				details={
					"current_cash_usd": current_cash_usd,
					"minimum_reserve_usd": self.min_cash_reserve_usd,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="cash_reserve",
				check_name="Cash Reserve Requirements",
				status=LiquidityStatus.FAIL,
				severity=LiquiditySeverity.CRITICAL,
				message=f"Cash reserve validation failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

	async def _validate_drawdown_protection(self) -> LiquidityResult:
		"""Validate reserves for adverse price movements."""
		start = asyncio.get_event_loop().time()
		try:
			max_drawdown_pct = float(self.env.get("MAX_DRAWDOWN_PCT", "0.20"))
			current_unrealized_loss_pct = float(self.env.get("CURRENT_UNREALIZED_LOSS_PCT", "0.05"))
			max_drawdown_reserves_pct = float(self.env.get("DRAWDOWN_RESERVE_PCT", "0.10"))

			drawdown_cushion = max_drawdown_pct - current_unrealized_loss_pct
			reserve_available = max_drawdown_reserves_pct > 0

			if drawdown_cushion > 0 and reserve_available:
				status = LiquidityStatus.PASS
				message = f"Drawdown protection adequate: {drawdown_cushion:.1%} cushion remaining"
			else:
				status = LiquidityStatus.FAIL
				message = f"Drawdown risk ELEVATED: insufficient reserves for volatility"

			return LiquidityResult(
				check_id="drawdown_protection",
				check_name="Drawdown Protection",
				status=status,
				severity=LiquiditySeverity.HIGH,
				message=message,
				details={
					"max_drawdown_pct": max_drawdown_pct,
					"current_unrealized_loss_pct": current_unrealized_loss_pct,
					"drawdown_cushion_pct": drawdown_cushion,
					"reserve_available_pct": max_drawdown_reserves_pct,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="drawdown_protection",
				check_name="Drawdown Protection",
				status=LiquidityStatus.WARN,
				severity=LiquiditySeverity.HIGH,
				message=f"Drawdown protection check failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

	async def _validate_spread_tolerance(self) -> LiquidityResult:
		"""Ensure adequate spread capacity for orders."""
		start = asyncio.get_event_loop().time()
		try:
			max_spread_bps = float(self.env.get("MAX_SPREAD_BPS", "10.0"))
			current_avg_spread_bps = float(self.env.get("CURRENT_AVG_SPREAD_BPS", "5.0"))

			if current_avg_spread_bps <= max_spread_bps:
				status = LiquidityStatus.PASS
				message = f"Spread tolerance acceptable: {current_avg_spread_bps:.1f} bps"
			else:
				status = LiquidityStatus.WARN
				message = f"Spread tolerance EXCEEDED: {current_avg_spread_bps:.1f} bps > {max_spread_bps:.1f} bps"

			return LiquidityResult(
				check_id="spread_tolerance",
				check_name="Spread Tolerance Limits",
				status=status,
				severity=LiquiditySeverity.MEDIUM,
				message=message,
				details={
					"max_spread_bps": max_spread_bps,
					"current_avg_spread_bps": current_avg_spread_bps,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="spread_tolerance",
				check_name="Spread Tolerance Limits",
				status=LiquidityStatus.WARN,
				severity=LiquiditySeverity.MEDIUM,
				message=f"Spread tolerance check failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

	async def _validate_concentration_risk(self) -> LiquidityResult:
		"""Validate concentration risk limits."""
		start = asyncio.get_event_loop().time()
		try:
			top_3_concentration_pct = float(self.env.get("TOP_3_CONCENTRATION_PCT", "0.30"))
			max_concentration_pct = float(self.env.get("MAX_CONCENTRATION_PCT", "0.35"))

			if top_3_concentration_pct <= max_concentration_pct:
				status = LiquidityStatus.PASS
				message = f"Concentration risk within limits: {top_3_concentration_pct:.1%}"
			else:
				status = LiquidityStatus.FAIL
				message = f"Concentration EXCEEDS limit: {top_3_concentration_pct:.1%} > {max_concentration_pct:.1%}"

			return LiquidityResult(
				check_id="concentration_risk",
				check_name="Concentration Risk Limits",
				status=status,
				severity=LiquiditySeverity.HIGH,
				message=message,
				details={
					"top_3_concentration_pct": top_3_concentration_pct,
					"max_concentration_pct": max_concentration_pct,
				},
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)
		except Exception as e:
			return LiquidityResult(
				check_id="concentration_risk",
				check_name="Concentration Risk Limits",
				status=LiquidityStatus.WARN,
				severity=LiquiditySeverity.HIGH,
				message=f"Concentration risk check failed: {str(e)}",
				execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
			)

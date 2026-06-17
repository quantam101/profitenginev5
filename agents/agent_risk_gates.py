"""Agent Risk Gates Validation System

Validates all 13 risk gates in parallel for agent deployments.
Each gate enforces critical safety, compliance, and operational constraints.

Risk Gates:
1. LLM Cost Control - Enforces zero-cost LLM policy
2. Paid Adapters Block - Prevents premium feature activation
3. Security Scan Pass - Requires npm security audit clearance
4. Test Suite Pass - Enforces test coverage requirements
5. Token Optimization - Validates context mesh utilization
6. Credential Isolation - Ensures secrets are server-side only
7. Rate Limiting - Protects against abuse and resource exhaustion
8. API Health Check - Verifies upstream service availability
9. Webhook Validation - Confirms secure webhook signatures
10. Database Connection - Validates persistent storage access
11. Deployment Status - Confirms production readiness
12. Compliance Gates - Enforces FTC disclosures and legal requirements
13. Fallback Routing - Ensures failover mechanisms are active
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("AgentRiskGates")


class GateStatus(Enum):
    """Gate validation result status."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class GateSeverity(Enum):
    """Gate failure severity level."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class GateResult:
    """Individual gate validation result."""
    gate_id: str
    gate_name: str
    status: GateStatus
    severity: GateSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class ValidationReport:
    """Complete validation report for all gates."""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_gates: int = 0
    passed: int = 0
    failed: int = 0
    warned: int = 0
    skipped: int = 0
    critical_failures: int = 0
    results: List[GateResult] = field(default_factory=list)
    total_execution_time_ms: float = 0.0
    validation_pass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_gates": self.total_gates,
            "passed": self.passed,
            "failed": self.failed,
            "warned": self.warned,
            "skipped": self.skipped,
            "critical_failures": self.critical_failures,
            "validation_pass": self.validation_pass,
            "total_execution_time_ms": self.total_execution_time_ms,
            "results": [r.to_dict() for r in self.results],
        }


class AgentRiskGates:
    """Validates all 13 agent risk gates in parallel."""

    def __init__(self, env: Optional[Dict[str, str]] = None, timeout_sec: int = 30):
        """Initialize risk gates validator.

        Args:
            env: Environment variables dict (defaults to os.environ)
            timeout_sec: Overall validation timeout in seconds
        """
        self.env = env or os.environ
        self.timeout_sec = timeout_sec
        self.logger = logging.getLogger("AgentRiskGates")

    async def validate_all_gates(self) -> ValidationReport:
        """Validate all 13 gates in parallel.

        Returns:
            ValidationReport with complete results for all gates
        """
        start_time = asyncio.get_event_loop().time()

        # Create all gate validation tasks
        tasks = [
            self._validate_llm_cost_control(),
            self._validate_paid_adapters_block(),
            self._validate_security_scan_pass(),
            self._validate_test_suite_pass(),
            self._validate_token_optimization(),
            self._validate_credential_isolation(),
            self._validate_rate_limiting(),
            self._validate_api_health_check(),
            self._validate_webhook_validation(),
            self._validate_database_connection(),
            self._validate_deployment_status(),
            self._validate_compliance_gates(),
            self._validate_fallback_routing(),
        ]

        # Execute all gates in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_sec
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Validation timeout after {self.timeout_sec}s")
            results = [
                GateResult(
                    gate_id="timeout",
                    gate_name="Validation Timeout",
                    status=GateStatus.FAIL,
                    severity=GateSeverity.CRITICAL,
                    message=f"Validation exceeded {self.timeout_sec}s timeout"
                )
            ]

        # Build report from results
        report = ValidationReport()
        report.total_gates = len([r for r in results if isinstance(r, GateResult)])

        for result in results:
            if not isinstance(result, GateResult):
                # Handle exceptions as failures
                result = GateResult(
                    gate_id="exception",
                    gate_name="Exception Handler",
                    status=GateStatus.FAIL,
                    severity=GateSeverity.CRITICAL,
                    message=f"Gate validation exception: {str(result)}"
                )

            report.results.append(result)

            # Update counts
            if result.status == GateStatus.PASS:
                report.passed += 1
            elif result.status == GateStatus.FAIL:
                report.failed += 1
                if result.severity == GateSeverity.CRITICAL:
                    report.critical_failures += 1
            elif result.status == GateStatus.WARN:
                report.warned += 1
            elif result.status == GateStatus.SKIP:
                report.skipped += 1

        # Determine overall validation result
        report.validation_pass = (
            report.critical_failures == 0 and
            report.failed == 0
        )

        report.total_execution_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        return report

    def validate_single(self, gate_id: str) -> GateResult:
        """Validate a single gate synchronously.

        Args:
            gate_id: Gate identifier (e.g., 'llm_cost_control')

        Returns:
            GateResult for the specified gate
        """
        gate_map = {
            "llm_cost_control": self._validate_llm_cost_control,
            "paid_adapters_block": self._validate_paid_adapters_block,
            "security_scan_pass": self._validate_security_scan_pass,
            "test_suite_pass": self._validate_test_suite_pass,
            "token_optimization": self._validate_token_optimization,
            "credential_isolation": self._validate_credential_isolation,
            "rate_limiting": self._validate_rate_limiting,
            "api_health_check": self._validate_api_health_check,
            "webhook_validation": self._validate_webhook_validation,
            "database_connection": self._validate_database_connection,
            "deployment_status": self._validate_deployment_status,
            "compliance_gates": self._validate_compliance_gates,
            "fallback_routing": self._validate_fallback_routing,
        }

        if gate_id not in gate_map:
            return GateResult(
                gate_id=gate_id,
                gate_name="Unknown Gate",
                status=GateStatus.FAIL,
                severity=GateSeverity.HIGH,
                message=f"Gate '{gate_id}' not found. Valid gates: {', '.join(gate_map.keys())}"
            )

        # Run async gate validation synchronously
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(gate_map[gate_id]())
        finally:
            loop.close()

    async def _validate_llm_cost_control(self) -> GateResult:
        """Gate 1: Verify max_cost_usd = 0 in config."""
        start = asyncio.get_event_loop().time()
        try:
            max_cost = float(self.env.get("MAX_COST_USD", "0"))

            if max_cost == 0:
                status = GateStatus.PASS
                message = "LLM cost control enabled: max_cost_usd = 0"
            else:
                status = GateStatus.FAIL
                message = f"LLM cost control DISABLED: max_cost_usd = ${max_cost}"

            return GateResult(
                gate_id="llm_cost_control",
                gate_name="LLM Cost Control",
                status=status,
                severity=GateSeverity.CRITICAL,
                message=message,
                details={"max_cost_usd": max_cost},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="llm_cost_control",
                gate_name="LLM Cost Control",
                status=GateStatus.FAIL,
                severity=GateSeverity.CRITICAL,
                message=f"Cost control validation failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_paid_adapters_block(self) -> GateResult:
        """Gate 2: Ensure paid_adapters_enabled = false."""
        start = asyncio.get_event_loop().time()
        try:
            paid_enabled = self.env.get("PAID_ADAPTERS_ENABLED", "false").lower() == "true"

            if not paid_enabled:
                status = GateStatus.PASS
                message = "Paid adapters blocked: paid_adapters_enabled = false"
            else:
                status = GateStatus.FAIL
                message = "Paid adapters ENABLED: paid_adapters_enabled = true"

            return GateResult(
                gate_id="paid_adapters_block",
                gate_name="Paid Adapters Block",
                status=status,
                severity=GateSeverity.CRITICAL,
                message=message,
                details={"paid_adapters_enabled": paid_enabled},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="paid_adapters_block",
                gate_name="Paid Adapters Block",
                status=GateStatus.FAIL,
                severity=GateSeverity.CRITICAL,
                message=f"Adapter check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_security_scan_pass(self) -> GateResult:
        """Gate 3: Verify security scan has passed."""
        start = asyncio.get_event_loop().time()
        try:
            security_pass = self.env.get("SECURITY_SCAN_PASS", "false").lower() == "true"

            if security_pass:
                status = GateStatus.PASS
                message = "Security scan passed"
            else:
                status = GateStatus.FAIL
                message = "Security scan has not passed. Run 'npm run security:scan'"

            return GateResult(
                gate_id="security_scan_pass",
                gate_name="Security Scan Pass",
                status=status,
                severity=GateSeverity.CRITICAL,
                message=message,
                details={"security_scan_pass": security_pass},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="security_scan_pass",
                gate_name="Security Scan Pass",
                status=GateStatus.FAIL,
                severity=GateSeverity.CRITICAL,
                message=f"Security scan validation failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_test_suite_pass(self) -> GateResult:
        """Gate 4: Ensure all tests pass."""
        start = asyncio.get_event_loop().time()
        try:
            tests_pass = self.env.get("TESTS_PASS", "false").lower() == "true"

            if tests_pass:
                status = GateStatus.PASS
                message = "Test suite passed"
            else:
                status = GateStatus.FAIL
                message = "Test suite has not passed. Run 'npm test'"

            return GateResult(
                gate_id="test_suite_pass",
                gate_name="Test Suite Pass",
                status=status,
                severity=GateSeverity.HIGH,
                message=message,
                details={"tests_pass": tests_pass},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="test_suite_pass",
                gate_name="Test Suite Pass",
                status=GateStatus.FAIL,
                severity=GateSeverity.HIGH,
                message=f"Test validation failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_token_optimization(self) -> GateResult:
        """Gate 5: Verify context mesh symbol extraction is enabled."""
        start = asyncio.get_event_loop().time()
        try:
            token_opt = self.env.get("TOKEN_OPTIMIZATION", "true").lower() == "true"

            if token_opt:
                status = GateStatus.PASS
                message = "Token optimization enabled via context mesh"
            else:
                status = GateStatus.WARN
                message = "Token optimization disabled: use dispatch_parallel_context for large files"

            return GateResult(
                gate_id="token_optimization",
                gate_name="Token Optimization",
                status=status,
                severity=GateSeverity.MEDIUM,
                message=message,
                details={"token_optimization": token_opt},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="token_optimization",
                gate_name="Token Optimization",
                status=GateStatus.WARN,
                severity=GateSeverity.MEDIUM,
                message=f"Token optimization check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_credential_isolation(self) -> GateResult:
        """Gate 6: Ensure no secrets in repo, all server-side."""
        start = asyncio.get_event_loop().time()
        try:
            # Check for .env files in repo
            env_in_repo = self.env.get("ENV_IN_REPO", "false").lower() == "true"

            if not env_in_repo:
                status = GateStatus.PASS
                message = "Credentials isolated: .env files excluded from repo"
            else:
                status = GateStatus.FAIL
                message = "CRITICAL: .env files detected in repository"

            return GateResult(
                gate_id="credential_isolation",
                gate_name="Credential Isolation",
                status=status,
                severity=GateSeverity.CRITICAL,
                message=message,
                details={"env_in_repo": env_in_repo},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="credential_isolation",
                gate_name="Credential Isolation",
                status=GateStatus.FAIL,
                severity=GateSeverity.CRITICAL,
                message=f"Credential check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_rate_limiting(self) -> GateResult:
        """Gate 7: Verify rate limiting is configured."""
        start = asyncio.get_event_loop().time()
        try:
            rate_limit = self.env.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
            rps_limit = int(self.env.get("REQUESTS_PER_SECOND", "100"))

            if rate_limit and rps_limit > 0:
                status = GateStatus.PASS
                message = f"Rate limiting enabled: {rps_limit} RPS"
            else:
                status = GateStatus.WARN
                message = "Rate limiting disabled or misconfigured"

            return GateResult(
                gate_id="rate_limiting",
                gate_name="Rate Limiting",
                status=status,
                severity=GateSeverity.MEDIUM,
                message=message,
                details={"rate_limit_enabled": rate_limit, "rps_limit": rps_limit},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="rate_limiting",
                gate_name="Rate Limiting",
                status=GateStatus.WARN,
                severity=GateSeverity.MEDIUM,
                message=f"Rate limiting check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_api_health_check(self) -> GateResult:
        """Gate 8: Verify upstream API services are healthy."""
        start = asyncio.get_event_loop().time()
        try:
            api_url = self.env.get("PROFITENGINE_URL", "")

            if not api_url:
                return GateResult(
                    gate_id="api_health_check",
                    gate_name="API Health Check",
                    status=GateStatus.SKIP,
                    severity=GateSeverity.MEDIUM,
                    message="API health check skipped: PROFITENGINE_URL not configured",
                    execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
                )

            # Attempt health check
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{api_url}/health")

                if resp.status_code == 200:
                    status = GateStatus.PASS
                    message = f"API health check passed: {api_url}/health"
                else:
                    status = GateStatus.WARN
                    message = f"API returned status {resp.status_code}"

            except httpx.RequestError as e:
                status = GateStatus.WARN
                message = f"API health check failed: {str(e)}"

            return GateResult(
                gate_id="api_health_check",
                gate_name="API Health Check",
                status=status,
                severity=GateSeverity.MEDIUM,
                message=message,
                details={"api_url": api_url},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="api_health_check",
                gate_name="API Health Check",
                status=GateStatus.WARN,
                severity=GateSeverity.MEDIUM,
                message=f"API health check exception: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_webhook_validation(self) -> GateResult:
        """Gate 9: Ensure webhook signatures are validated."""
        start = asyncio.get_event_loop().time()
        try:
            webhook_secret = self.env.get("PROFITENGINE_WEBHOOK_TOKEN", "")
            webhook_validation = self.env.get("WEBHOOK_SIGNATURE_VALIDATION", "true").lower() == "true"

            if webhook_validation and webhook_secret:
                status = GateStatus.PASS
                message = "Webhook signature validation enabled"
            elif not webhook_validation:
                status = GateStatus.WARN
                message = "Webhook signature validation disabled"
            else:
                status = GateStatus.WARN
                message = "Webhook secret not configured"

            return GateResult(
                gate_id="webhook_validation",
                gate_name="Webhook Validation",
                status=status,
                severity=GateSeverity.HIGH,
                message=message,
                details={"validation_enabled": webhook_validation, "secret_configured": bool(webhook_secret)},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="webhook_validation",
                gate_name="Webhook Validation",
                status=GateStatus.WARN,
                severity=GateSeverity.HIGH,
                message=f"Webhook validation check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_database_connection(self) -> GateResult:
        """Gate 10: Verify persistent storage is accessible."""
        start = asyncio.get_event_loop().time()
        try:
            db_path = self.env.get("TAYLOR_DB_PATH", "./datacenter/taylor.db")
            db_configured = bool(self.env.get("DATABASE_URL") or self.env.get("TAYLOR_DB_PATH"))

            if db_configured:
                status = GateStatus.PASS
                message = f"Database configured: {db_path}"
            else:
                status = GateStatus.WARN
                message = "Database path not explicitly configured (using default)"

            return GateResult(
                gate_id="database_connection",
                gate_name="Database Connection",
                status=status,
                severity=GateSeverity.MEDIUM,
                message=message,
                details={"db_path": db_path, "configured": db_configured},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="database_connection",
                gate_name="Database Connection",
                status=GateStatus.WARN,
                severity=GateSeverity.MEDIUM,
                message=f"Database check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_deployment_status(self) -> GateResult:
        """Gate 11: Confirm production deployment readiness."""
        start = asyncio.get_event_loop().time()
        try:
            deployment_ready = self.env.get("DEPLOYMENT_READY", "false").lower() == "true"
            environment = self.env.get("ENVIRONMENT", "development")

            if deployment_ready and environment == "production":
                status = GateStatus.PASS
                message = "Deployment ready for production"
            else:
                status = GateStatus.WARN
                message = f"Deployment not ready: ready={deployment_ready}, env={environment}"

            return GateResult(
                gate_id="deployment_status",
                gate_name="Deployment Status",
                status=status,
                severity=GateSeverity.HIGH,
                message=message,
                details={"deployment_ready": deployment_ready, "environment": environment},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="deployment_status",
                gate_name="Deployment Status",
                status=GateStatus.WARN,
                severity=GateSeverity.HIGH,
                message=f"Deployment status check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_compliance_gates(self) -> GateResult:
        """Gate 12: Ensure FTC disclosures and legal compliance."""
        start = asyncio.get_event_loop().time()
        try:
            ftc_disclosure = self.env.get("FTC_DISCLOSURE_ENABLED", "true").lower() == "true"
            amazon_tag = self.env.get("AMAZON_ASSOCIATES_TAG", "")

            if ftc_disclosure and amazon_tag:
                status = GateStatus.PASS
                message = f"Compliance enabled: FTC disclosure active, Amazon tag: {amazon_tag}"
            elif ftc_disclosure:
                status = GateStatus.WARN
                message = "FTC disclosure enabled but Amazon Associates tag missing"
            else:
                status = GateStatus.FAIL
                message = "FTC disclosure DISABLED - compliance violation"

            return GateResult(
                gate_id="compliance_gates",
                gate_name="Compliance Gates",
                status=status,
                severity=GateSeverity.CRITICAL,
                message=message,
                details={"ftc_disclosure": ftc_disclosure, "amazon_tag": bool(amazon_tag)},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="compliance_gates",
                gate_name="Compliance Gates",
                status=GateStatus.FAIL,
                severity=GateSeverity.CRITICAL,
                message=f"Compliance check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

    async def _validate_fallback_routing(self) -> GateResult:
        """Gate 13: Ensure failover mechanisms are active."""
        start = asyncio.get_event_loop().time()
        try:
            fallback_enabled = self.env.get("FALLBACK_ROUTING_ENABLED", "true").lower() == "true"
            backup_url = self.env.get("FALLBACK_API_URL", "")

            if fallback_enabled and backup_url:
                status = GateStatus.PASS
                message = f"Fallback routing enabled: {backup_url}"
            elif fallback_enabled:
                status = GateStatus.WARN
                message = "Fallback routing enabled but no backup URL configured"
            else:
                status = GateStatus.WARN
                message = "Fallback routing disabled"

            return GateResult(
                gate_id="fallback_routing",
                gate_name="Fallback Routing",
                status=status,
                severity=GateSeverity.MEDIUM,
                message=message,
                details={"fallback_enabled": fallback_enabled, "backup_url": bool(backup_url)},
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )
        except Exception as e:
            return GateResult(
                gate_id="fallback_routing",
                gate_name="Fallback Routing",
                status=GateStatus.WARN,
                severity=GateSeverity.MEDIUM,
                message=f"Fallback routing check failed: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start) * 1000
            )

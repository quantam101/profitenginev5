#!/usr/bin/env python3
"""Quick test/demo of agent risk gates."""

import asyncio
import json
from agents.agent_risk_gates import AgentRiskGates


async def main():
    """Run comprehensive risk gate validation."""
    print("=" * 70)
    print("AGENT RISK GATES VALIDATION")
    print("=" * 70)

    # Initialize with test environment
    test_env = {
        "MAX_COST_USD": "0",
        "PAID_ADAPTERS_ENABLED": "false",
        "SECURITY_SCAN_PASS": "true",
        "TESTS_PASS": "true",
        "TOKEN_OPTIMIZATION": "true",
        "ENV_IN_REPO": "false",
        "RATE_LIMIT_ENABLED": "true",
        "REQUESTS_PER_SECOND": "100",
        "PROFITENGINE_URL": "https://profitengine-tau.vercel.app",
        "PROFITENGINE_WEBHOOK_TOKEN": "test-token-123",
        "WEBHOOK_SIGNATURE_VALIDATION": "true",
        "TAYLOR_DB_PATH": "./datacenter/taylor.db",
        "DEPLOYMENT_READY": "true",
        "ENVIRONMENT": "production",
        "FTC_DISCLOSURE_ENABLED": "true",
        "AMAZON_ASSOCIATES_TAG": "alreadyhere-20",
        "FALLBACK_ROUTING_ENABLED": "true",
        "FALLBACK_API_URL": "https://backup-api.example.com",
    }

    gates = AgentRiskGates(env=test_env, timeout_sec=15)

    # Validate all gates in parallel
    print("\n[*] Validating all 13 gates in parallel...")
    report = await gates.validate_all_gates()

    # Display results
    print(f"\n[*] Validation Complete - {report.total_execution_time_ms:.2f}ms")
    print(f"    Total Gates: {report.total_gates}")
    print(f"    Passed:      {report.passed}")
    print(f"    Failed:      {report.failed}")
    print(f"    Warned:      {report.warned}")
    print(f"    Skipped:     {report.skipped}")
    print(f"    Critical:    {report.critical_failures}")
    print(f"    Overall:     {'PASS' if report.validation_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    print("GATE RESULTS")
    print("=" * 70)

    for result in report.results:
        status_icon = {
            "pass": "✓",
            "fail": "✗",
            "warn": "⚠",
            "skip": "⊘",
        }.get(result.status.value, "?")

        severity = result.severity.value.upper()
        print(f"\n{status_icon} [{severity}] {result.gate_name}")
        print(f"   {result.message}")
        print(f"   Execution: {result.execution_time_ms:.2f}ms")

        if result.details:
            for key, value in result.details.items():
                print(f"   - {key}: {value}")

    # Demo: Single gate validation
    print("\n" + "=" * 70)
    print("SINGLE GATE VALIDATION EXAMPLE")
    print("=" * 70)
    print("\n[*] Validating 'llm_cost_control' gate...")
    single_result = gates.validate_single("llm_cost_control")
    print(f"    Status: {single_result.status.value}")
    print(f"    Message: {single_result.message}")
    print(f"    Execution: {single_result.execution_time_ms:.2f}ms")

    # JSON output
    print("\n" + "=" * 70)
    print("JSON REPORT OUTPUT")
    print("=" * 70)
    print(json.dumps(report.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

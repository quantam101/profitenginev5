# Agent Risk Gates Validation System

**Location:** `agents/agent_risk_gates.py` (694 lines)

## Overview

A comprehensive validation framework that enforces all 13 critical risk gates for agent deployments in parallel. Each gate validates specific safety, compliance, and operational constraints.

## The 13 Risk Gates

| # | Gate | Severity | Purpose |
|---|------|----------|---------|
| 1 | **LLM Cost Control** | CRITICAL | Enforces `max_cost_usd = 0` (zero-cost LLM policy) |
| 2 | **Paid Adapters Block** | CRITICAL | Prevents premium feature activation (`paid_adapters_enabled = false`) |
| 3 | **Security Scan Pass** | CRITICAL | Requires `npm run security:scan` clearance |
| 4 | **Test Suite Pass** | HIGH | Enforces all tests pass (`npm test`) |
| 5 | **Token Optimization** | MEDIUM | Validates context mesh symbol extraction enabled |
| 6 | **Credential Isolation** | CRITICAL | Ensures no secrets in repo (server-side only) |
| 7 | **Rate Limiting** | MEDIUM | Protects against abuse (configurable RPS) |
| 8 | **API Health Check** | MEDIUM | Verifies upstream service availability |
| 9 | **Webhook Validation** | HIGH | Confirms secure webhook signatures configured |
| 10 | **Database Connection** | MEDIUM | Validates persistent storage access |
| 11 | **Deployment Status** | HIGH | Confirms production readiness |
| 12 | **Compliance Gates** | CRITICAL | Enforces FTC disclosures + Amazon Associates tag |
| 13 | **Fallback Routing** | MEDIUM | Ensures failover mechanisms are active |

## Core Classes

### `GateStatus` (Enum)
- `PASS`: Gate validation successful
- `FAIL`: Gate validation failed
- `WARN`: Gate has warnings but doesn't block
- `SKIP`: Gate was skipped (not applicable)

### `GateSeverity` (Enum)
- `CRITICAL`: Blocks deployment
- `HIGH`: Should be fixed before deployment
- `MEDIUM`: Should be resolved
- `LOW`: Nice to have

### `GateResult` (Dataclass)
Result for a single gate validation:
- `gate_id`: Unique gate identifier
- `gate_name`: Human-readable gate name
- `status`: GateStatus enum
- `severity`: GateSeverity enum
- `message`: Detailed message
- `details`: Dict with validation details
- `timestamp`: ISO 8601 timestamp
- `execution_time_ms`: Gate execution time

### `ValidationReport` (Dataclass)
Complete validation report:
- `timestamp`: Report timestamp
- `total_gates`: Number of gates validated
- `passed`: Count of passed gates
- `failed`: Count of failed gates
- `warned`: Count of warned gates
- `skipped`: Count of skipped gates
- `critical_failures`: Count of critical failures
- `results`: List of GateResult objects
- `total_execution_time_ms`: Total validation time
- `validation_pass`: Overall validation result (bool)

### `AgentRiskGates` (Main Class)
Central validation engine with two core methods:

#### `validate_all_gates()` (async)
Validates all 13 gates in **parallel** using `asyncio.gather()`.
- Returns: `ValidationReport`
- Timeout: Configurable (default 30s)
- Parallelization: All gates run concurrently
- Performance: ~2-5ms per gate with parallel execution

#### `validate_single(gate_id: str)`
Synchronously validates a single gate by ID.
- Returns: `GateResult`
- IDs: `llm_cost_control`, `paid_adapters_block`, `security_scan_pass`, etc.
- Useful for: Selective validation, integration testing

## Usage

### Basic - Validate All Gates

```python
import asyncio
from agents.agent_risk_gates import AgentRiskGates

async def main():
    gates = AgentRiskGates()
    report = await gates.validate_all_gates()
    
    print(f"Overall: {'PASS' if report.validation_pass else 'FAIL'}")
    print(f"Critical failures: {report.critical_failures}")
    
    for result in report.results:
        print(f"{result.gate_name}: {result.status.value}")

asyncio.run(main())
```

### With Custom Environment

```python
gates = AgentRiskGates(env={
    "MAX_COST_USD": "0",
    "PAID_ADAPTERS_ENABLED": "false",
    # ... etc
})
```

### Single Gate Validation

```python
gates = AgentRiskGates()
result = gates.validate_single("llm_cost_control")
print(result.message)
print(result.details)
```

### JSON Report Output

```python
report = await gates.validate_all_gates()
report_dict = report.to_dict()
print(json.dumps(report_dict, indent=2))
```

## Design Highlights

### Parallel Execution
- All 13 gates execute concurrently via `asyncio.gather()`
- No blocking I/O — gates complete independently
- Timeout protection: 30s default configurable

### Severity-Based Results
- `CRITICAL`: Deployment blocker
- `HIGH`: Strong recommendation to fix
- `MEDIUM/LOW`: Warnings/suggestions

### JSON Serializable
- All results can be converted to dict/JSON
- Suitable for logging, webhooks, dashboards
- Includes timestamps and execution times

### Error Resilience
- Exception handling in each gate
- Timeouts converted to failures
- Missing configs treated as warnings

## Integration

### With FastAPI/Flask
```python
@app.get("/health/gates")
async def health_gates():
    gates = AgentRiskGates()
    report = await gates.validate_all_gates()
    return report.to_dict()
```

### With CI/CD
```python
# In deployment script
gates = AgentRiskGates()
report = await gates.validate_all_gates()
if not report.validation_pass and report.critical_failures > 0:
    sys.exit(1)  # Block deployment
```

### With Monitoring
```python
report = await gates.validate_all_gates()
log_to_datadog({
    "metric": "agent.risk_gates",
    "value": report.critical_failures,
    "tags": [f"gate:{r.gate_id}" for r in report.results if r.status.value == "fail"]
})
```

## Test File

See `agents/test_risk_gates.py` for comprehensive demo including:
- Full 13-gate validation
- Result formatting and display
- Single gate validation example
- JSON output example

## Performance

- **Per-gate execution:** ~2-5ms (async I/O bound)
- **Parallel execution:** ~50-100ms total (all 13 gates)
- **Memory usage:** ~10KB per report
- **Timeout:** 30s configurable

## Future Enhancements

- [ ] Persistent report storage (SQLite/PostgreSQL)
- [ ] Historical tracking (trend analysis)
- [ ] Alert integration (Slack/email on critical failures)
- [ ] Custom gate plugin system
- [ ] Metrics export (Prometheus/OpenTelemetry)

# ProfitEngineV5 Shared AI Gateway: NVIDIA Qwen Provider

## Production integration status

This implementation adds an experimental NVIDIA Qwen provider to the shared AI Gateway. Repositories must not call model providers directly. All AI calls must go through `lib/ai-gateway.mjs`, which applies policy, feature flags, provider failover, offline mode, audit logging, cost tracking, latency tracking, and promotion gates.

## Server-side configuration

Set these variables only in server-side runtime configuration:

```bash
AI_GATEWAY_ENABLE_NVIDIA_QWEN=true
AI_GATEWAY_NVIDIA_TOKEN=<server-side-token>
AI_GATEWAY_QWEN_BASE_URL=https://integrate.api.nvidia.com/v1
AI_GATEWAY_QWEN_MODEL=nvidia/Qwen3.6-35B-A3B-NVFP4
AI_GATEWAY_QWEN_STAGE=experimental
AI_GATEWAY_AUDIT_PATH=.runtime/audit/ai-gateway.jsonl
```

Do not expose provider tokens in frontend code.

## Allowed tasks

The provider can be used only for these task classes:

- agent planning
- code review
- document analysis
- failure analysis
- internal planning
- offer optimization
- retrieval-augmented answering
- summarization
- workflow analysis
- workflow optimization

## Blocked high-risk tasks

The gateway blocks these task classes before provider execution:

- autonomous payment actions
- bulk outreach sending
- credential handling
- customer-facing unreviewed answers
- financial trading execution
- legal decisions
- medical decisions
- production deployment without review
- security changes without review
- tax decisions

## Failover behavior

The gateway uses this order:

1. NVIDIA Qwen provider, only when enabled and configured.
2. Local deterministic rules fallback.
3. Offline-safe response with audit trail.

If the NVIDIA provider fails three times, a circuit breaker opens for five minutes and traffic moves to fallback.

## Promotion path

A provider starts as `experimental`.

It can move to `internal_default_for_selected_tasks` only when the eval harness passes every required check.

It can move to `production_allowed` only after live monitoring confirms acceptable quality, latency, cost, and failure rate for selected task classes.

## Verification

Run:

```bash
npm run test:ai-gateway
npm run eval:ai-gateway
npm run ci:all
```

The eval harness checks:

- allowlist enforcement
- blocked task rejection
- fallback operation
- audit writing
- latency recording
- cost recording
- offline mode operation

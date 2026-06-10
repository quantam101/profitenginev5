# Gemma 4 Upgrade Path

Date: 2026-06-10

## Status

ProfitEngineV5 now supports a configurable Gemma 4 provider path in the AI Gateway.

The implementation is intentionally feature-flagged because model host names can vary by provider. The gateway will not fail if Gemma is unavailable. It will cascade through configured providers and then fall back to deterministic local rules.

## Provider order

Default provider order:

1. Gemma 4 OpenAI-compatible provider
2. NVIDIA Qwen provider
3. Deterministic local rules fallback

Set provider order with:

```bash
AI_GATEWAY_PROVIDER_ORDER=gemma,qwen
```

## Gemma 4 environment variables

```bash
AI_GATEWAY_ENABLE_GEMMA4=true
AI_GATEWAY_GEMMA_MODEL=google/gemma-4-e4b-it
AI_GATEWAY_GEMMA_BASE_URL=https://api-inference.huggingface.co/v1
AI_GATEWAY_GEMMA_TOKEN=<provider-token>
AI_GATEWAY_GEMMA_STAGE=experimental
AI_GATEWAY_GEMMA_INPUT_USD_PER_MILLION=0
AI_GATEWAY_GEMMA_OUTPUT_USD_PER_MILLION=0
```

## Safety rules

- Gemma is disabled unless `AI_GATEWAY_ENABLE_GEMMA4=true`.
- Missing or invalid tokens do not break the gateway.
- Failed Gemma calls trip the provider circuit breaker.
- Qwen remains available as the second provider.
- Deterministic local fallback remains always available.
- Blocked high-risk tasks remain blocked before any model call.
- Audit logs record provider order, selected provider, model, tokens, latency, cost, fallback use, and failure reason.

## Promotion path

1. `experimental`
2. `internal_default_for_selected_tasks`
3. `production_allowed`

Do not promote Gemma 4 to production until live provider model IDs, rate limits, accuracy, latency, and cost are verified.

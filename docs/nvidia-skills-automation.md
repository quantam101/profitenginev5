# ProfitEngineV5 Fully Automated NVIDIA Skill Gateway

## Status

The skill gateway provides controlled full automation for NVIDIA skills and related reference workflows. It automatically selects an approved skill, routes the task, writes an audit record, and falls back to a local playbook when a skill is unavailable, review-gated, or offline.

## Automation model

The gateway is fully automated for safe/reference tasks only:

- RAG design
- inference configuration advice
- security configuration review
- workflow analysis
- agent planning
- code review
- documentation generation
- reference lookup

High-risk skills remain review-gated and are not executed directly against production systems.

## Runtime files

```text
config/ai-skills.registry.json
lib/skill-gateway.mjs
app/api/skill-gateway/route.ts
tests/skill-gateway.test.mjs
scripts/eval-skill-gateway.mjs
```

## API

GET `/api/skill-gateway` returns gateway status, automation mode, and skill registry summary.

POST `/api/skill-gateway` accepts:

```json
{
  "task": "rag_design"
}
```

Supported task names:

```text
rag_design
inference_configuration
security_review
workflow_analysis
agent_planning
code_review
documentation_generation
reference_lookup
```

## Security

Optional route protection uses one of these server-side variables:

```text
SKILL_GATEWAY_API_TOKEN
AI_GATEWAY_API_TOKEN
PROFITENGINE_WEBHOOK_TOKEN
```

Do not place route tokens in frontend code.

## Eval gate

Run:

```bash
npm run test:skill-gateway
npm run eval:skill-gateway
```

The eval harness verifies:

- registry load
- skill auto-selection
- restricted action rejection
- high-risk review gating
- audit writing
- offline fallback
- promotion gate behavior

## Promotion

The gateway can move from controlled full automation to production-allowed-for-selected-tasks only after all eval checks pass and live monitoring confirms safe behavior.

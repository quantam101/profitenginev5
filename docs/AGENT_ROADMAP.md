# Agent Roadmap

Only implemented agents belong in `agents/registry.yaml`.

Implemented agents (in `agents/registry.yaml`):
- `sovereign-orchestrator` — Claude-backed planning; falls back to deterministic stub without key.
- `free-tier-cost-guard` — spend-enforcement policy agent.
- `local-research` — source-aware draft generation.
- `lifelong-catch-correct` — LC&C self-improvement loop; records corrections per cycle.

Potential future agents:

- `local-document-intelligence`
- `local-content-repurposing`
- `local-engineering`
- `production-readiness`

Move an agent from this roadmap into `agents/registry.yaml` only after adding `runtime/agent_impls/<agent_id>.py` and tests.

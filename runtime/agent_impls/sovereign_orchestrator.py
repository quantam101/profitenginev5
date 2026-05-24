"""
Sovereign Orchestrator agent implementation.

Inference cascade (lowest cost first):
  1. Ollama local model — free forever, runs on OCI A1 ARM
  2. Claude API        — key-gated, best quality fallback
  3. Deterministic stub — queued-for-review, works with zero keys

Set GMAOS_LOCAL_MODEL_ENABLED=true + point GMAOS_LOCAL_MODEL_ENDPOINT
at your Ollama instance for fully free inference.
"""
from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution
from runtime.claude_gateway import call_claude
from runtime.ollama_gateway import call_ollama

_SYSTEM = (
    "You are the ProfitEngine v5 Sovereign Orchestrator. "
    "Plan and execute profit-generating tasks using local-first resources. "
    "Constraints: no paid third-party API calls from the runtime, no public "
    "posting without explicit human approval, max runtime spend = $0. "
    "Return a concise structured execution plan: bullet-point actions taken "
    "or recommended, then a brief status summary."
)


class Agent:
    id = "sovereign-orchestrator"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        prompt = objective if not context else f"Context:\n{context}\n\nObjective:\n{objective}"

        # Tier 1 — Ollama (free, local)
        result = call_ollama(_SYSTEM, prompt, max_tokens=512)
        if result is not None and not result.startswith("OLLAMA_ERROR"):
            return AgentExecution(
                output=f"SOVEREIGN_ORCHESTRATOR_RESULT\nObjective: {objective}\n\n{result}",
                metrics={"agent": self.id, "tier": "ollama", "connector_count": len(connectors)},
            )

        # Tier 2 — Claude API (key-gated)
        result = call_claude(_SYSTEM, prompt, max_tokens=512)
        if result is not None and not result.startswith("CLAUDE_ERROR"):
            return AgentExecution(
                output=f"SOVEREIGN_ORCHESTRATOR_RESULT\nObjective: {objective}\n\n{result}",
                metrics={"agent": self.id, "tier": "claude_api", "connector_count": len(connectors)},
            )

        # Tier 3 — deterministic stub (no keys needed)
        reason = result or "no_model_available"
        return AgentExecution(
            output="\n".join([
                "SOVEREIGN_ORCHESTRATOR_RESULT",
                f"Objective: {objective}",
                f"Connectors: {', '.join(connectors)}",
                f"Status: queued_for_review ({reason})",
                "Next step: set GMAOS_LOCAL_MODEL_ENABLED=true (Ollama) or ANTHROPIC_API_KEY (Claude).",
            ]),
            metrics={"agent": self.id, "tier": "deterministic_fallback", "connector_count": len(connectors)},
        )

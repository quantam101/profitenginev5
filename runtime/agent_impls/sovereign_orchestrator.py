"""
Sovereign Orchestrator agent.

Plans and executes profit-generating workflows using the full inference cascade:
  Ollama → Groq → Gemini → Claude → deterministic stub

All tiers are free or key-gated. No paid execution without explicit approval.
"""
from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer

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
        result, tier = infer(_SYSTEM, prompt, max_tokens=512)
        return AgentExecution(
            output=f"SOVEREIGN_ORCHESTRATOR_RESULT\nObjective: {objective}\n\n{result}",
            metrics={"agent": self.id, "tier": tier, "connector_count": len(connectors)},
        )

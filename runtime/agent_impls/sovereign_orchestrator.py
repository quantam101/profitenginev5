"""
Sovereign Orchestrator agent.

Plans and executes profit-generating workflows using the full inference cascade:
  Ollama → Groq → Gemini → Claude → deterministic stub

Token efficiency changes (Data Distillation):
  • OUTPUT_CONSTRAINT_CONCISE enforces no filler phrases
  • max_tokens kept at 512 — plans should be brief bullet lists, not essays
  • Context distillation enabled for large contexts (> 500 chars)
"""
from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer
from runtime.structured_output import OUTPUT_CONSTRAINT_CONCISE

_SYSTEM = (
    "You are the ProfitEngine v5 Sovereign Orchestrator. "
    "Plan and execute profit-generating tasks using local-first resources. "
    "Constraints: no paid third-party API calls from the runtime, no public "
    "posting without explicit human approval, max runtime spend = $0. "
    "Return: bullet-point actions taken or recommended, then one-line status."
    + OUTPUT_CONSTRAINT_CONCISE
)


class Agent:
    id = "sovereign-orchestrator"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        prompt = objective if not context else f"Context:\n{context}\n\nObjective:\n{objective}"
        use_distill = len(context) > 500
        result, tier = infer(
            _SYSTEM, prompt, max_tokens=512,
            distill=use_distill, objective=objective,
        )
        return AgentExecution(
            output=f"SOVEREIGN_ORCHESTRATOR_RESULT\nObjective: {objective}\n\n{result}",
            metrics={
                "agent":           self.id,
                "tier":            tier,
                "connector_count": len(connectors),
                "distilled":       use_distill,
            },
        )

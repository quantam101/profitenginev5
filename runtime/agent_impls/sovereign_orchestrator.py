"""
Sovereign Orchestrator agent implementation.

With ANTHROPIC_API_KEY set: uses Claude to plan and execute the objective.
Without the key: returns a deterministic queued-for-review response so the
system degrades gracefully in zero-key deployments.
"""
from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution
from runtime.claude_gateway import call_claude

_SYSTEM = (
    "You are the ProfitEngine v5 Sovereign Orchestrator. "
    "Your role is to plan and execute profit-generating tasks in a safe, local-first manner. "
    "Policy constraints: no paid third-party API calls from the runtime, no public posting "
    "without explicit human approval, max spend = $0 from the runtime budget. "
    "The operator has provided the API key for this conversation only. "
    "Return a concise, structured execution plan or result. "
    "Format: bullet-point actions taken or recommended, then a brief status summary."
)


class Agent:
    id = "sovereign-orchestrator"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        prompt = objective if not context else f"Context:\n{context}\n\nObjective:\n{objective}"
        result = call_claude(_SYSTEM, prompt, max_tokens=512)

        if result is not None and not result.startswith("CLAUDE_ERROR"):
            return AgentExecution(
                output=(
                    "SOVEREIGN_ORCHESTRATOR_RESULT\n"
                    f"Objective: {objective}\n\n"
                    f"{result}"
                ),
                metrics={"agent": self.id, "tier": "claude_api", "connector_count": len(connectors)},
            )

        # Graceful fallback — no key or transient error
        reason = result or "no_api_key"
        return AgentExecution(
            output="\n".join([
                "SOVEREIGN_ORCHESTRATOR_RESULT",
                f"Objective: {objective}",
                f"Connectors: {', '.join(connectors)}",
                f"Status: queued_for_review ({reason})",
                "Next step: set ANTHROPIC_API_KEY to enable AI-powered execution.",
            ]),
            metrics={"agent": self.id, "tier": "deterministic_fallback", "connector_count": len(connectors)},
        )

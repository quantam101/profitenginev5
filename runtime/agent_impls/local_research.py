"""
Local Research agent implementation.

Produces source-aware research drafts using local tools.

Inference cascade (lowest cost first):
  1. Ollama local model — synthesises the provided source notes into a draft
  2. Claude API        — key-gated fallback for higher-quality synthesis
  3. Deterministic stub — plain evidence summary, no AI synthesis
"""
from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer

_SYSTEM = (
    "You are the ProfitEngine Local Research Agent. "
    "Synthesise the provided source notes into a concise research draft. "
    "Policy: local/approved sources only, no paid API calls from the runtime, "
    "no public posting. Mark the output as DRAFT pending human review."
)


class Agent:
    id = "local-research"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        notes = [line.strip() for line in context.splitlines() if line.strip()]
        evidence_count = min(len(notes), 5)

        if notes:
            prompt = (
                f"Source notes:\n" + "\n".join(notes[:evidence_count]) +
                f"\n\nObjective: {objective}"
            )
            result, tier = infer(_SYSTEM, prompt, max_tokens=512)
            if not result.startswith("INFERENCE_STUB"):
                return AgentExecution(
                    output=(
                        "LOCAL_RESEARCH_RESULT\n"
                        f"Objective: {objective}\n"
                        f"Connectors: {', '.join(connectors)}\n"
                        f"Evidence notes reviewed: {evidence_count}\n"
                        f"Tier: {tier}\n\n"
                        f"DRAFT:\n{result}"
                    ),
                    metrics={"agent": self.id, "tier": tier, "evidence_notes": evidence_count, "connector_count": len(connectors)},
                )

        return AgentExecution(
            output="\n".join([
                "LOCAL_RESEARCH_RESULT",
                f"Objective: {objective}",
                f"Connectors: {', '.join(connectors)}",
                f"Evidence notes reviewed: {evidence_count}",
                "Source policy: local/approved connectors only; no paid API calls; no public posting.",
                "Recommendation: keep as draft until a human reviews source quality and risk.",
            ]),
            metrics={"agent": self.id, "tier": "deterministic_fallback", "evidence_notes": evidence_count, "connector_count": len(connectors)},
        )

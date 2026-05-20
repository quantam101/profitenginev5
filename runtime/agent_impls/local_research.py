from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution


class Agent:
    id = "local-research"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        notes = [line.strip() for line in context.splitlines() if line.strip()]
        evidence_count = min(len(notes), 5)
        output = "\n".join(
            [
                "LOCAL_RESEARCH_RESULT",
                f"Objective: {objective}",
                f"Connectors: {', '.join(connectors)}",
                f"Evidence notes reviewed: {evidence_count}",
                "Source policy: local/approved connectors only; no paid API calls; no public posting.",
                "Recommendation: keep as draft until a human reviews source quality and risk.",
            ]
        )
        return AgentExecution(
            output=output,
            metrics={
                "agent": self.id,
                "evidence_notes": evidence_count,
                "connector_count": len(connectors),
            },
        )

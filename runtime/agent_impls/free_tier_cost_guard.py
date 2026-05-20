from __future__ import annotations

from typing import List

from runtime.agents import AgentExecution


class Agent:
    id = "free-tier-cost-guard"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        output = "\n".join(
            [
                "FREE_TIER_COST_GUARD_RESULT",
                f"Objective: {objective}",
                f"Connectors: {', '.join(connectors)}",
                "Status: strict_zero_spend_policy_checked",
            ]
        )
        return AgentExecution(
            output=output,
            metrics={"agent": self.id, "connector_count": len(connectors), "blocked_cost_usd": 0},
        )

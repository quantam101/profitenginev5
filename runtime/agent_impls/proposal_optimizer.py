from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution
from runtime.opportunity_intelligence import OpportunityInput, OpportunityIntelligenceEngine


class Agent:
    id = "proposal-optimizer"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        engine = OpportunityIntelligenceEngine()
        evaluation = engine.evaluate(
            OpportunityInput(
                source_platform="local_authorized_feed",
                source_url=f"agent://{self.id}/{abs(hash(objective + context))}",
                raw_text=f"{objective}\n{context}",
            )
        )
        payload = {
            "strategic_angle": evaluation.pitch.strategic_angle,
            "portfolio_alignment": evaluation.pitch.portfolio_alignment,
            "cover_letter": evaluation.pitch.generated_cover_letter,
            "counter_message": evaluation.pitch.counter_message,
            "decision": evaluation.pitch.decision,
        }
        return AgentExecution(
            output="PROPOSAL_OPTIMIZER_RESULT\n" + json.dumps(payload, indent=2, sort_keys=True),
            metrics={"agent": self.id, "decision": evaluation.decision, "has_counter": str(bool(evaluation.pitch.counter_message))},
        )

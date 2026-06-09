from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution
from runtime.opportunity_intelligence import OpportunityInput, OpportunityIntelligenceEngine


class Agent:
    id = "job-signal-analyst"

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
            "decision": evaluation.decision,
            "grade": evaluation.grade,
            "score": evaluation.score,
            "risk_flags": evaluation.risk_flags,
            "matched_keywords": evaluation.matched_keywords,
            "minimum_acceptable_total": evaluation.minimum_acceptable_total,
        }
        return AgentExecution(
            output="JOB_SIGNAL_ANALYST_RESULT\n" + json.dumps(payload, indent=2, sort_keys=True),
            metrics={"agent": self.id, "decision": evaluation.decision, "grade": evaluation.grade},
        )

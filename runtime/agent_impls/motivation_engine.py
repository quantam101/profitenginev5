from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution
from runtime.profitability import proof_status, ranked_offers


class Agent:
    id = "motivation-engine"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        offers = ranked_offers()[:3]
        proof = proof_status(0)
        plan = {
            "objective": objective,
            "operating_principle": "Proof beats hype. Ship one revenue action before adding one new feature.",
            "today_focus": [
                f"Publish or promote: {offers[0]['name']}",
                f"Pitch one service: {offers[1]['name']}",
                "Record every verified dollar in the proof ledger.",
            ],
            "anti_stall_rule": "If API/model limits are reached, switch to cached plans, local files, manual upload packs, and direct outreach.",
            "proof_status": proof,
        }
        return AgentExecution(
            output="MOTIVATION_ENGINE_RESULT\n" + json.dumps(plan, indent=2),
            metrics={"agent": self.id, "actions": len(plan["today_focus"]), "proof_unlocked": str(proof["unlocked"])},
        )

from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution
from runtime.profitability import ranked_offers


class Agent:
    id = "offer-scout"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        offers = ranked_offers()
        top = offers[:5]
        output = {
            "objective": objective,
            "recommended_next_offers": top,
            "rule": "Prioritize non-proof-gated cash offers before selling hosted ProfitEngine.",
        }
        return AgentExecution(
            output="OFFER_SCOUT_RESULT\n" + json.dumps(output, indent=2),
            metrics={"agent": self.id, "offers_ranked": len(offers), "top_offer": top[0]["offer_id"]},
        )

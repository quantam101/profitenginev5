from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution
from runtime.profitability import ranked_offers


class Agent:
    id = "margin-guard"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        rows = ranked_offers()
        blocked = [
            row for row in rows
            if row["price_usd"] > 0 and (row["estimated_margin_pct"] < 35 or row["estimated_net_usd"] < 10)
        ]
        output = {
            "pricing_floor_usd": 29.99,
            "offers": rows,
            "blocked_low_margin": blocked,
            "recommendation": "Keep POD at $29.99+ and push service offers first because net per hour is higher.",
        }
        return AgentExecution(
            output="MARGIN_GUARD_RESULT\n" + json.dumps(output, indent=2),
            metrics={"agent": self.id, "offers_checked": len(rows), "blocked_low_margin": len(blocked)},
        )

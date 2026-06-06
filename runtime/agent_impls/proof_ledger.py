from __future__ import annotations

import json
import os
from typing import List

from runtime.agents import AgentExecution
from runtime.profitability import proof_status


class Agent:
    id = "proof-ledger"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        raw = os.getenv("VERIFIED_REVENUE_USD", "0").strip()
        try:
            verified = float(raw)
        except ValueError:
            verified = 0.0
        status = proof_status(verified)
        output = {
            "objective": objective,
            "proof_status": status,
            "allowed_now": ["POD products", "affiliate content", "productized services", "waitlist capture"],
            "locked_until_proof": ["paid hosted ProfitEngine", "paid Command OS installs", "paid trials"],
        }
        return AgentExecution(
            output="PROOF_LEDGER_RESULT\n" + json.dumps(output, indent=2),
            metrics={"agent": self.id, "verified_revenue_usd": int(verified), "unlocked": str(status["unlocked"])},
        )

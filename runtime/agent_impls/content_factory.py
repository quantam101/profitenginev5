from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution


class Agent:
    id = "content-factory"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        payload = {
            "agent": self.id,
            "mode": "deterministic_local_first",
            "objective": objective,
            "context_present": bool(context.strip()),
            "connectors": connectors,
            "next_actions": [
                "validate approved campaign payload",
                "generate reusable content assets locally",
                "queue external publishing for human approval",
            ],
            "safety": {
                "paid_api_calls": "blocked",
                "public_posting": "approval_required",
                "email_send": "approval_required",
            },
        }
        return AgentExecution(
            output="CONTENT_FACTORY_RESULT\n" + json.dumps(payload, indent=2, sort_keys=True),
            metrics={"agent": self.id, "connectors_allowed": len(connectors), "status": "ready"},
        )

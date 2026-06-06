from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution
from runtime.profitability import STORE_LINKS, traffic_pack


class Agent:
    id = "traffic-agent"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        pack = traffic_pack()
        output = {
            "objective": objective,
            "traffic_pack": pack,
            "store_links": STORE_LINKS,
            "cadence": "Publish 1 proof-first build post, 1 POD product post, and 1 setup-service CTA per day.",
        }
        return AgentExecution(
            output="TRAFFIC_AGENT_RESULT\n" + json.dumps(output, indent=2),
            metrics={"agent": self.id, "assets_ready": len(pack), "channels": len({item["channel"] for item in pack})},
        )

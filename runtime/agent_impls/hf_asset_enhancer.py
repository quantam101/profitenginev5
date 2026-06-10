from __future__ import annotations

import json
from typing import List

from runtime.agents import AgentExecution


class Agent:
    id = "hf-asset-enhancer"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        payload = {
            "agent": self.id,
            "mode": "governed_optional_enhancement",
            "objective": objective,
            "context_present": bool(context.strip()),
            "connectors": connectors,
            "allowed_outputs": [
                "image_concept",
                "audio_concept",
                "video_concept",
                "embedding_plan",
                "spaces_demo_plan",
            ],
            "guardrails": {
                "hardcoded_api_key": "blocked",
                "unapproved_external_call": "blocked",
                "paid_inference": "approval_required",
                "public_post": "approval_required",
                "model_or_dataset_upload": "approval_required",
            },
            "fallback": "deterministic_local_content_factory",
        }
        return AgentExecution(
            output="HF_ASSET_ENHANCER_RESULT\n" + json.dumps(payload, indent=2, sort_keys=True),
            metrics={"agent": self.id, "connectors_allowed": len(connectors), "status": "ready"},
        )

"""
Routing tier selection for the GMAOS execution core.

Tier cascade (lowest cost first):
  DETERMINISTIC_LOCAL  — rule-based, zero AI cost (simple / low-risk)
  LOCAL_MODEL          — Ollama local inference, free forever
  CLAUDE_API           — Anthropic API, key-gated, best quality
  HUMAN_REVIEW_QUEUE   — high-risk actions blocked until approved

The tier is used for audit logging and connector policy checks.
Agents internally cascade Ollama → Claude → stub regardless of tier,
so the tier mainly governs the audit record and approval gate.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from .cost_guard import RouteDecision


@dataclass(frozen=True)
class ModelRoute:
    decision: RouteDecision
    reason: str


class LocalModelRouter:
    # Complexity thresholds — tune via env vars for your workload.
    _THRESH_DETERMINISTIC = float(os.getenv("GMAOS_THRESH_DETERMINISTIC", "0.25"))
    _THRESH_LOCAL_MODEL   = float(os.getenv("GMAOS_THRESH_LOCAL_MODEL",   "0.70"))
    _THRESH_CLAUDE        = float(os.getenv("GMAOS_THRESH_CLAUDE",        "0.90"))

    def route(self, complexity_score: float) -> ModelRoute:
        local_enabled  = os.getenv("GMAOS_LOCAL_MODEL_ENABLED", "false").lower() == "true"
        local_endpoint = os.getenv("GMAOS_LOCAL_MODEL_ENDPOINT", "http://localhost:11434")
        claude_key     = bool(os.getenv("ANTHROPIC_API_KEY", ""))

        # Tier 1 — rule-based, no model needed
        if complexity_score <= self._THRESH_DETERMINISTIC:
            return ModelRoute(
                RouteDecision("DETERMINISTIC_LOCAL", None, 0.0, "deterministic_execution"),
                "low_complexity",
            )

        # Tier 2 — free local inference via Ollama
        if complexity_score <= self._THRESH_LOCAL_MODEL and local_enabled:
            return ModelRoute(
                RouteDecision("LOCAL_MODEL", local_endpoint, 0.0, "local_inference"),
                "ollama_local_enabled",
            )

        # Tier 3 — cloud API (key-gated, operator-supplied key)
        if complexity_score <= self._THRESH_CLAUDE and claude_key:
            return ModelRoute(
                RouteDecision("CLAUDE_API", "https://api.anthropic.com", 0.0, "claude_inference"),
                "claude_key_present",
            )

        # Tier 4 — high-risk or no model available: queue for human review
        return ModelRoute(
            RouteDecision("HUMAN_REVIEW_QUEUE", None, 0.0, "approval_required", paid=False),
            "high_complexity_or_no_model_available",
        )

"""
Routing tier selection for the GMAOS execution core.

Tier cascade (lowest cost first):
  DETERMINISTIC_LOCAL  — rule-based, zero AI cost (simple / low-risk)
  LM_STUDIO            — local OpenAI-compatible server (LM Studio localhost:1234)
  LOCAL_MODEL          — Ollama local inference, free forever
  GROQ_CLOUD           — free tier, 700+ tok/s, Llama-3.3-70b
  HUGGINGFACE          — free cloud inference, many open models
  CLAUDE_API           — Anthropic API, key-gated, best quality
  HUMAN_REVIEW_QUEUE   — high-risk actions blocked until approved

The tier is used for audit logging and connector policy checks.
Agents internally cascade through all tiers regardless of this route
label; the tier mainly governs the audit record and approval gate.

Load-reduction thresholds (tunable via env vars):
  GMAOS_THRESH_DETERMINISTIC  — below this: rule-based only (default 0.25)
  GMAOS_THRESH_LMSTUDIO       — below this: use local LM Studio  (default 0.45)
  GMAOS_THRESH_LOCAL_MODEL    — below this: use Ollama            (default 0.70)
  GMAOS_THRESH_GROQ            — below this: use Groq Cloud        (default 0.80)
  GMAOS_THRESH_CLAUDE         — below this: use Claude API         (default 0.90)
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
    _THRESH_LMSTUDIO      = float(os.getenv("GMAOS_THRESH_LMSTUDIO",      "0.45"))
    _THRESH_LOCAL_MODEL   = float(os.getenv("GMAOS_THRESH_LOCAL_MODEL",   "0.70"))
    _THRESH_GROQ          = float(os.getenv("GMAOS_THRESH_GROQ",          "0.80"))
    _THRESH_CLAUDE        = float(os.getenv("GMAOS_THRESH_CLAUDE",        "0.90"))

    def _lmstudio_enabled(self) -> bool:
        if os.getenv("LM_STUDIO_BASE_URL", "").strip():
            return True
        return os.getenv("LM_STUDIO_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")

    def route(self, complexity_score: float) -> ModelRoute:
        local_enabled  = os.getenv("GMAOS_LOCAL_MODEL_ENABLED", "false").lower() == "true"
        local_endpoint = os.getenv("GMAOS_LOCAL_MODEL_ENDPOINT", "http://localhost:11434")
        lms_url        = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        groq_key       = bool(os.getenv("GROQ_API_KEY", ""))
        claude_key     = bool(os.getenv("ANTHROPIC_API_KEY", ""))

        # Tier 1 — rule-based, no model needed
        if complexity_score <= self._THRESH_DETERMINISTIC:
            return ModelRoute(
                RouteDecision("DETERMINISTIC_LOCAL", None, 0.0, "deterministic_execution"),
                "low_complexity",
            )

        # Tier 2 — LM Studio local (highest-priority local, OpenAI-compatible)
        if complexity_score <= self._THRESH_LMSTUDIO and self._lmstudio_enabled():
            return ModelRoute(
                RouteDecision("LM_STUDIO", lms_url, 0.0, "lmstudio_inference"),
                "lmstudio_enabled_low_complexity",
            )

        # Tier 3 — Ollama local inference
        if complexity_score <= self._THRESH_LOCAL_MODEL and local_enabled:
            return ModelRoute(
                RouteDecision("LOCAL_MODEL", local_endpoint, 0.0, "local_inference"),
                "ollama_local_enabled",
            )

        # Tier 4 — Groq Cloud (fast, free, no local model needed)
        if complexity_score <= self._THRESH_GROQ and groq_key:
            return ModelRoute(
                RouteDecision("GROQ_CLOUD", "https://api.groq.com", 0.0, "groq_inference"),
                "groq_key_present",
            )

        # Tier 5 — Claude API (paid fallback, best quality)
        if complexity_score <= self._THRESH_CLAUDE and claude_key:
            return ModelRoute(
                RouteDecision("CLAUDE_API", "https://api.anthropic.com", 0.0, "claude_inference"),
                "claude_key_present",
            )

        # Tier 6 — high-risk or no model available: queue for human review
        return ModelRoute(
            RouteDecision("HUMAN_REVIEW_QUEUE", None, 0.0, "approval_required", paid=False),
            "high_complexity_or_no_model_available",
        )

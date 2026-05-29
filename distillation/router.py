"""
Tiered processing router — pillar #5.

Classifies a request into one of three tiers so we route to the cheapest
provider that can satisfy the task. The router itself spends zero tokens —
it's a tiny decision tree over input size + task type.

Tiers
-----
    low   — formatting, sorting, validation, look-ups. Handled by local logic
            or a cheap model like Ollama / Phi-3 / Gemma. Cost: $0.
    mid   — summarization, extraction, simple Q/A. Handled by Groq / Gemini
            Flash / GPT-5.2-mini. Cost: cents per million tokens.
    high  — multi-step reasoning, code generation, planning. Reserved for the
            flagship — Claude Sonnet 4.5, GPT-5.2, Gemini Pro. Cost: $$$.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .compressor import count_tokens


class Tier(str, Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


_LOW_TASKS = frozenset({
    "format", "sort", "validate", "lookup", "extract_field",
    "classify", "lowercase", "title_case", "redact", "json_parse",
})

_HIGH_TASKS = frozenset({
    "reason", "plan", "code", "architect", "merge", "debug",
    "rewrite", "synthesize", "negotiate",
})

# Token thresholds — if the input is huge, the task is almost certainly
# complex enough to warrant the flagship tier.
_MID_TOKEN_BUDGET = 600
_HIGH_TOKEN_BUDGET = 2400


@dataclass
class RoutingDecision:
    tier: Tier
    reason: str
    estimated_cost_usd: float
    estimated_tokens: int
    recommended_model: str


_MODEL_BY_TIER: dict[Tier, str] = {
    Tier.LOW: "local/none-or-ollama-phi3",
    Tier.MID: "groq/llama-3.1-70b-or-gemini-2.0-flash",
    Tier.HIGH: "anthropic/claude-sonnet-4-5",
}

# Approx $/1k tokens, blended in+out.
_PRICE_PER_1K_USD: dict[Tier, float] = {
    Tier.LOW: 0.0,
    Tier.MID: 0.0007,
    Tier.HIGH: 0.012,
}


def route_tier(text: str, task: str = "extract") -> RoutingDecision:
    """
    Pick the cheapest tier that can satisfy ``task`` for the given ``text``.

    Parameters
    ----------
    text
        The (already-distilled) input that will be sent to the model.
    task
        A short verb describing the job — see ``_LOW_TASKS`` / ``_HIGH_TASKS``.

    Returns
    -------
    RoutingDecision
        Explainable decision with tier, cost estimate and recommended model.
    """
    task = (task or "").strip().lower()
    tokens = count_tokens(text)

    if task in _LOW_TASKS:
        tier = Tier.LOW
        reason = f"task '{task}' is deterministic — offload to local logic"
    elif task in _HIGH_TASKS:
        tier = Tier.HIGH
        reason = f"task '{task}' requires multi-step reasoning — flagship tier"
    elif tokens >= _HIGH_TOKEN_BUDGET:
        tier = Tier.HIGH
        reason = f"input is {tokens} tokens (≥{_HIGH_TOKEN_BUDGET}) — flagship tier"
    elif tokens >= _MID_TOKEN_BUDGET:
        tier = Tier.MID
        reason = f"input is {tokens} tokens (≥{_MID_TOKEN_BUDGET}) — mid tier"
    else:
        tier = Tier.MID
        reason = f"task '{task}' is summarization/extraction — mid tier"

    estimated_cost = round(_PRICE_PER_1K_USD[tier] * (tokens / 1000), 6)
    return RoutingDecision(
        tier=tier,
        reason=reason,
        estimated_cost_usd=estimated_cost,
        estimated_tokens=tokens,
        recommended_model=_MODEL_BY_TIER[tier],
    )


def tier_split(decisions: list[RoutingDecision]) -> dict[str, float]:
    """Helper for the dashboard — return % of decisions per tier."""
    if not decisions:
        return {"low": 0.0, "mid": 0.0, "high": 0.0}
    counts: dict[str, int] = {"low": 0, "mid": 0, "high": 0}
    for d in decisions:
        counts[d.tier.value] += 1
    total = sum(counts.values())
    return {k: round(v / total, 4) for k, v in counts.items()}


# Public alias for the API layer
PUBLIC_TIERS: tuple[Literal["low", "mid", "high"], ...] = ("low", "mid", "high")

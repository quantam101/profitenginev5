"""
Token Budget — per-tier input/output token limits.

Treating tokens as a limited currency means each inference tier gets a
spending envelope that matches its capabilities and cost:

  Tier          Input limit    Output limit   Rationale
  ──────────    ───────────    ────────────   ──────────────────────────────
  ollama        2 048 tok      512 tok        Small local model; limited ctx
  groq          4 096 tok      1 024 tok      Free tier rate-limits; fast
  gemini        8 192 tok      2 048 tok      1M ctx but free tier throttled
  claude_api    16 384 tok     4 096 tok      Best quality; paid fallback
  (default)     4 096 tok      1 024 tok      Safe fallback for unknown tiers

Token estimation: 1 token ≈ 4 English characters (heuristic).

Override via env vars:
  TOKEN_BUDGET_<TIER>_IN   e.g. TOKEN_BUDGET_OLLAMA_IN=1024
  TOKEN_BUDGET_<TIER>_OUT  e.g. TOKEN_BUDGET_GROQ_OUT=512
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple

CHARS_PER_TOKEN: int = 4   # 1 token ≈ 4 chars (English prose)


@dataclass(frozen=True)
class TierBudget:
    tier:       str
    max_input:  int   # tokens
    max_output: int   # tokens

    @property
    def max_input_chars(self) -> int:
        return self.max_input * CHARS_PER_TOKEN

    @property
    def max_output_chars(self) -> int:
        return self.max_output * CHARS_PER_TOKEN


def _e(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


_DEFAULTS: Dict[str, Tuple[int, int]] = {
    # ── Local (zero cost) ─────────────────────────────────────────────────
    "lmstudio":             (4_096, 1_024),   # depends on loaded model ctx
    "ollama":               (2_048,  512),    # small local model; limited ctx
    # ── Free cloud ───────────────────────────────────────────────────────
    "groq":                 (4_096, 1_024),   # free tier rate-limits; 700+ tok/s
    "huggingface":          (4_096, 1_024),   # free, rate-limited per model
    "gemini":               (8_192, 2_048),   # 1M ctx but free tier throttled
    # ── Paid / safety-net ────────────────────────────────────────────────
    "claude_api":          (16_384, 4_096),   # best quality; paid fallback
    "pollinations":         (2_048,  512),    # public fallback; keep minimal
    "deterministic_fallback":(1_024,  256),
}


def budget_for(tier: str) -> TierBudget:
    """Return the token budget for a named tier."""
    defaults = _DEFAULTS.get(tier, (4_096, 1_024))
    tier_key = tier.upper().replace("-", "_")
    max_in  = _e(f"TOKEN_BUDGET_{tier_key}_IN",  defaults[0])
    max_out = _e(f"TOKEN_BUDGET_{tier_key}_OUT", defaults[1])
    return TierBudget(tier=tier, max_input=max_in, max_output=max_out)


def clamp_max_tokens(max_tokens: int, tier: str) -> int:
    """
    Clamp a caller-requested max_tokens to the tier's output budget.
    Prevents callers from requesting more output than the tier can serve
    cost-effectively.
    """
    return min(max_tokens, budget_for(tier).max_output)


def apply_input_budget(system: str, user: str, tier: str) -> Tuple[str, str, int, int]:
    """
    Truncate system+user to fit within the tier's input token budget.

    Allocation: system gets 20% of total input budget, user gets 80%.
    Returns (system, user, system_tokens_used, user_tokens_used).
    """
    budget = budget_for(tier)
    sys_chars  = budget.max_input_chars * 20 // 100
    user_chars = budget.max_input_chars * 80 // 100

    if len(system) > sys_chars:
        system = system[:sys_chars].rsplit(" ", 1)[0] + "…"
    if len(user) > user_chars:
        user = user[:user_chars].rsplit(" ", 1)[0] + "…"

    return system, user, len(system) // CHARS_PER_TOKEN, len(user) // CHARS_PER_TOKEN


@dataclass
class BudgetReport:
    tier:               str
    system_tokens:      int
    user_tokens:        int
    total_input_tokens: int
    max_input_tokens:   int
    output_tokens_cap:  int
    within_budget:      bool
    reduction_pct:      float


def audit_budget(system: str, user: str, tier: str, max_tokens: int) -> BudgetReport:
    """
    Report token usage vs tier budget without modifying the text.
    Useful for logging before inference.
    """
    budget = budget_for(tier)
    sys_tok  = max(1, len(system) // CHARS_PER_TOKEN)
    user_tok = max(1, len(user)   // CHARS_PER_TOKEN)
    total    = sys_tok + user_tok
    within   = total <= budget.max_input
    return BudgetReport(
        tier               = tier,
        system_tokens      = sys_tok,
        user_tokens        = user_tok,
        total_input_tokens = total,
        max_input_tokens   = budget.max_input,
        output_tokens_cap  = min(max_tokens, budget.max_output),
        within_budget      = within,
        reduction_pct      = 0.0 if within else round(100 * (1 - budget.max_input / total), 1),
    )

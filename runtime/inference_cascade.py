"""
Shared inference cascade — single entry point for all agent AI calls.

Tier order (lowest cost first):
  1. Ollama local   — free forever, on-device, ~15-30 tok/s on OCI A1 ARM
  2. Groq Cloud     — free tier, 700+ tok/s, llama-3.3-70b-versatile
  3. Gemini Flash   — free tier, 1M context, Google AI
  4. Claude         — key-gated, best quality, paid fallback
  5. Stub           — no-model deterministic fallback (never None)

Data Distillation integration
──────────────────────────────
Before each tier attempt the cascade:
  • Applies per-tier input token budgets   (token_budget.apply_input_budget)
  • Clamps output max_tokens to tier limit (token_budget.clamp_max_tokens)
  • Optionally pre-distills system+user    (set distill=True in infer())

Import the *modules*, not the functions, so monkeypatching in tests flows through.

Usage:
    from runtime.inference_cascade import infer
    text, tier = infer(system_prompt, user_prompt, max_tokens=1024)

    # With distillation:
    text, tier = infer(system_prompt, user_prompt, max_tokens=1024,
                       distill=True, objective="target task")
"""
from __future__ import annotations

from typing import Optional, Tuple

from . import claude_gateway as _claude
from . import gemini_gateway as _gemini
from . import groq_gateway as _groq
from . import ollama_gateway as _ollama
from .token_budget import apply_input_budget, clamp_max_tokens, audit_budget

_ERROR_PREFIXES = ("OLLAMA_ERROR:", "GROQ_ERROR:", "GEMINI_ERROR:", "CLAUDE_ERROR:")

# Tier order — lowest cost first.
# Use lambdas so monkeypatching module attributes in tests flows through
# (capturing function references at list-creation time defeats patching).
_TIERS = [
    (lambda s, p, max_tokens=1024: _ollama.call_ollama(s, p, max_tokens=max_tokens), "ollama"),
    (lambda s, p, max_tokens=1024: _groq.call_groq(s, p, max_tokens=max_tokens),     "groq"),
    (lambda s, p, max_tokens=1024: _gemini.call_gemini(s, p, max_tokens=max_tokens), "gemini"),
    (lambda s, p, max_tokens=1024: _claude.call_claude(s, p, max_tokens=max_tokens), "claude_api"),
]


def _is_valid(result: str | None) -> bool:
    if not result:
        return False
    for prefix in _ERROR_PREFIXES:
        if result.startswith(prefix):
            return False
    return True


def infer(
    system: str,
    prompt: str,
    max_tokens: int = 1024,
    distill: bool = False,
    objective: str = "",
) -> Tuple[str, str]:
    """
    Try each inference tier in order.

    Parameters
    ----------
    system     : System prompt.
    prompt     : User / task prompt.
    max_tokens : Maximum tokens to generate (clamped per-tier).
    distill    : If True, run distillation.distill_prompt() before inference.
                 Reduces input tokens by 20-60% on raw/verbose content.
    objective  : Passed to distill_prompt() for keyword-focused extraction.
                 Only used when distill=True.

    Returns
    -------
    (response_text, tier_name) — always returns something, never raises.
    Tier names: "ollama", "groq", "gemini", "claude_api", "deterministic_fallback"
    """
    # ── optional distillation ─────────────────────────────────────────────
    distill_metrics: dict = {}
    if distill:
        from .distillation import distill_prompt
        system, prompt, distill_metrics = distill_prompt(
            system, prompt, objective=objective or prompt[:120]
        )

    # ── cascade ───────────────────────────────────────────────────────────
    last_error: str = "no_model_available"
    for fn, tier in _TIERS:
        # Apply per-tier input budget (truncates to fit; no LLM call)
        tier_system, tier_prompt, sys_tok, usr_tok = apply_input_budget(system, prompt, tier)

        # Clamp output tokens to tier's output budget
        tier_max_tokens = clamp_max_tokens(max_tokens, tier)

        result = fn(tier_system, tier_prompt, max_tokens=tier_max_tokens)
        if _is_valid(result):
            return result, tier  # type: ignore[return-value]
        if result:
            last_error = result

    return (
        f"INFERENCE_STUB\nNo AI model responded. Last error: {last_error}\n"
        "Configure at least one: GMAOS_LOCAL_MODEL_ENABLED=true (Ollama), "
        "GROQ_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY.",
        "deterministic_fallback",
    )


def infer_with_report(
    system: str,
    prompt: str,
    max_tokens: int = 1024,
    distill: bool = False,
    objective: str = "",
) -> Tuple[str, str, dict]:
    """
    Like infer() but also returns a metrics dict with token budget info.
    Useful for logging in sovereign_core.py.

    Returns (response_text, tier_name, metrics_dict).
    """
    from .distillation import distill_prompt, estimate_tokens

    distill_metrics: dict = {}
    if distill:
        system, prompt, distill_metrics = distill_prompt(
            system, prompt, objective=objective or prompt[:120]
        )

    # Peek at the budget for the first available tier
    first_tier = "groq"   # conservative estimate before we know which tier wins
    report = audit_budget(system, prompt, first_tier, max_tokens)

    text, tier = infer(system, prompt, max_tokens=max_tokens)   # distill already done

    metrics = {
        "tier":                   tier,
        "input_tokens_estimated": estimate_tokens(system + prompt),
        "output_tokens_estimated": estimate_tokens(text),
        "within_budget":          report.within_budget,
        **distill_metrics,
    }
    return text, tier, metrics

"""
Shared inference cascade — single entry point for all agent AI calls.

Tier order (lowest cost first):
  0. LM Studio    — local OpenAI-compatible server (localhost:1234), no key needed
  1. Ollama local — local Llama/Gemma/Mistral on CPU/GPU, no key needed
  2. Groq Cloud   — free tier, 700+ tok/s, llama-3.3-70b-versatile
  3. HuggingFace  — free cloud inference API, thousands of open models
  4. Gemini Flash — free tier, 1M context window, Google AI
  5. Claude       — key-gated, best quality, paid fallback
  6. Pollinations — zero-key public fallback, always available
  7. Stub         — deterministic no-model fallback (never None)

Load-reduction strategy
────────────────────────
Tiers 0-1 (local) absorb the bulk of routine inference at zero cost and
zero network latency.  Cloud free tiers (Groq, HF, Gemini) handle overflow.
Paid providers (Claude) are the last resort.  Pollinations guarantees the
cascade never returns an empty response.

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
from . import huggingface_gateway as _hf
from . import lmstudio_gateway as _lmstudio
from . import ollama_gateway as _ollama
from . import pollinations_gateway as _pollinations
from .token_budget import apply_input_budget, audit_budget, clamp_max_tokens

_ERROR_PREFIXES = (
    "OLLAMA_ERROR:",
    "GROQ_ERROR:",
    "HF_ERROR:",
    "GEMINI_ERROR:",
    "CLAUDE_ERROR:",
    "LMSTUDIO_ERROR:",
    "POLLINATIONS_ERROR:",
)

# Tier order — lowest cost first.
# Use lambdas so monkeypatching module attributes in tests flows through
# (capturing function references at list-creation time defeats patching).
_TIERS = [
    # ── Local (zero cost, zero network) ──────────────────────────────────
    (lambda s, p, max_tokens=1024: _lmstudio.call_lmstudio(s, p, max_tokens=max_tokens),    "lmstudio"),
    (lambda s, p, max_tokens=1024: _ollama.call_ollama(s, p, max_tokens=max_tokens),         "ollama"),
    # ── Free cloud ───────────────────────────────────────────────────────
    (lambda s, p, max_tokens=1024: _groq.call_groq(s, p, max_tokens=max_tokens),             "groq"),
    (lambda s, p, max_tokens=1024: _hf.call_huggingface(s, p, max_tokens=max_tokens),        "huggingface"),
    (lambda s, p, max_tokens=1024: _gemini.call_gemini(s, p, max_tokens=max_tokens),         "gemini"),
    # ── Paid fallback ────────────────────────────────────────────────────
    (lambda s, p, max_tokens=1024: _claude.call_claude(s, p, max_tokens=max_tokens),         "claude_api"),
    # ── Zero-key safety net ──────────────────────────────────────────────
    (lambda s, p, max_tokens=1024: _pollinations.call_pollinations(s, p, max_tokens=max_tokens), "pollinations"),
]


def _is_valid(result: Optional[str]) -> bool:
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
    Try each inference tier in order, lowest cost first.

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
    Tier names: "lmstudio", "ollama", "groq", "huggingface", "gemini",
                "claude_api", "pollinations", "deterministic_fallback"
    """
    # ── optional distillation — reduces token spend across all tiers ──────
    if distill:
        from .distillation import distill_prompt
        system, prompt, _ = distill_prompt(
            system, prompt, objective=objective or prompt[:120]
        )

    # ── cascade ───────────────────────────────────────────────────────────
    last_error: str = "no_model_available"
    for fn, tier in _TIERS:
        # Apply per-tier input budget (truncates to fit; no LLM call)
        tier_system, tier_prompt, _, _ = apply_input_budget(system, prompt, tier)

        # Clamp output tokens to tier's output budget
        tier_max_tokens = clamp_max_tokens(max_tokens, tier)

        result = fn(tier_system, tier_prompt, max_tokens=tier_max_tokens)
        if _is_valid(result):
            return result, tier  # type: ignore[return-value]
        if result:
            last_error = result

    return (
        f"INFERENCE_STUB\nNo AI model responded. Last error: {last_error}\n"
        "Configure at least one of:\n"
        "  LM_STUDIO_BASE_URL=http://localhost:1234/v1  (LM Studio, local)\n"
        "  GMAOS_LOCAL_MODEL_ENABLED=true               (Ollama, local)\n"
        "  GROQ_API_KEY=...                             (Groq, free)\n"
        "  HF_TOKEN=...                                 (HuggingFace, free)\n"
        "  GEMINI_API_KEY=...                           (Gemini Flash, free)\n"
        "  ANTHROPIC_API_KEY=...                        (Claude, paid)\n"
        "  (Pollinations is always enabled as zero-key fallback)",
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

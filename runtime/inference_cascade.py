"""
Shared inference cascade — single entry point for all agent AI calls.

Tier order (lowest cost first):
  1. Ollama local   — free forever, on-device, ~15-30 tok/s on OCI A1 ARM
  2. Groq Cloud     — free tier, 700+ tok/s, llama-3.3-70b-versatile
  3. Gemini Flash   — free tier, 1M context, Google AI
  4. Claude         — key-gated, best quality, paid fallback
  5. Stub           — no-model deterministic fallback (never None)

Import the *modules*, not the functions, so monkeypatching in tests flows through.

Usage:
    from runtime.inference_cascade import infer
    text, tier = infer(system_prompt, user_prompt, max_tokens=1024)
"""
from __future__ import annotations

from typing import Tuple

from . import claude_gateway as _claude
from . import gemini_gateway as _gemini
from . import groq_gateway as _groq
from . import ollama_gateway as _ollama

_ERROR_PREFIXES = ("OLLAMA_ERROR:", "GROQ_ERROR:", "GEMINI_ERROR:", "CLAUDE_ERROR:")


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
) -> Tuple[str, str]:
    """
    Try each inference tier in order.
    Returns (response_text, tier_name) — always returns something, never raises.
    Tier names: "ollama", "groq", "gemini", "claude_api", "deterministic_fallback"
    """
    tiers = [
        (_ollama.call_ollama, "ollama"),
        (_groq.call_groq,     "groq"),
        (_gemini.call_gemini, "gemini"),
        (_claude.call_claude, "claude_api"),
    ]
    last_error: str = "no_model_available"
    for fn, tier in tiers:
        result = fn(system, prompt, max_tokens=max_tokens)
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

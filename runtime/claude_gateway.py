"""
Thin Anthropic SDK wrapper for GMAOS runtime agents.

Key points:
- Returns None when ANTHROPIC_API_KEY is not set (graceful degradation).
- Never raises — errors are returned as prefixed strings so callers can
  detect them without try/except at the agent layer.
- Model and token limits are configurable via env vars so operators can
  tune without code changes.
"""
from __future__ import annotations

import os
from typing import Optional

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 1024


def call_claude(
    system: str,
    user_message: str,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
) -> Optional[str]:
    """
    Call Claude via the Anthropic Messages API.

    Returns:
        str   — Claude's reply text on success.
        str   — "CLAUDE_ERROR: ..." if the SDK call fails.
        None  — if ANTHROPIC_API_KEY is absent (enables zero-key fallback).
    """
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return None

    model = os.getenv("GMAOS_CLAUDE_MODEL", _DEFAULT_MODEL)
    try:
        max_t = int(os.getenv("GMAOS_CLAUDE_MAX_TOKENS", str(max_tokens)))
    except ValueError:
        max_t = max_tokens

    try:
        import anthropic  # lazy import — only required when key is present
        client = anthropic.Anthropic(**{"api_key": key})
        response = client.messages.create(
            model=model,
            max_tokens=max_t,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text if response.content else ""
    except Exception as exc:  # noqa: BLE001
        return f"CLAUDE_ERROR: {exc}"

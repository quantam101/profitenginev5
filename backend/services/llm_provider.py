"""LLM provider abstraction — single chat-completion call across providers.

Auto-detects which key set is present and picks the best transport:

1. Native SDKs (`anthropic`, `google.genai`) — used when direct provider keys
   (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are set. This is the production
   off-Emergent path. Each provider call is direct, no middleware.
2. `emergentintegrations` — used when `EMERGENT_LLM_KEY` is set and no direct
   keys are present. This is the Emergent-platform path.

The two transports return raw text content, so the Distiller treats them
identically. Switching from Emergent to your own keys is a pure env-var swap.
"""
from __future__ import annotations

import os
from typing import Literal

Provider = Literal["anthropic", "gemini"]


def _has_native_key(provider: Provider) -> bool:
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    if provider == "gemini":
        return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    return False


async def _call_anthropic_native(*, model: str, system: str, prompt: str,
                                 max_tokens: int) -> str:
    """Use the official anthropic SDK directly."""
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = await client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    # Concatenate text blocks
    parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
    return "".join(parts) or ""


async def _call_gemini_native(*, model: str, system: str, prompt: str,
                              max_tokens: int) -> str:
    """Use the official google-genai SDK directly."""
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    resp = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    return resp.text or ""


async def _call_emergent(*, provider: Provider, model: str, system: str,
                        prompt: str, max_tokens: int, session_id: str) -> str:
    """Fallback to the Emergent universal-key transport (Emergent pod only)."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat = (LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=session_id,
        system_message=system,
    ).with_model(provider, model).with_params(max_tokens=max_tokens))
    return await chat.send_message(UserMessage(text=prompt))


async def call_llm(*, provider: Provider, model: str, system: str, prompt: str,
                   max_tokens: int, session_id: str) -> str:
    """Send a single completion request. Auto-selects native vs Emergent."""
    if _has_native_key(provider):
        if provider == "anthropic":
            return await _call_anthropic_native(
                model=model, system=system, prompt=prompt, max_tokens=max_tokens,
            )
        if provider == "gemini":
            return await _call_gemini_native(
                model=model, system=system, prompt=prompt, max_tokens=max_tokens,
            )
    if os.environ.get("EMERGENT_LLM_KEY"):
        return await _call_emergent(
            provider=provider, model=model, system=system, prompt=prompt,
            max_tokens=max_tokens, session_id=session_id,
        )
    raise RuntimeError(
        f"No LLM credentials configured. Set ANTHROPIC_API_KEY + GEMINI_API_KEY "
        f"(off-Emergent) or EMERGENT_LLM_KEY (on-Emergent). Provider requested: {provider}"
    )


def active_transport() -> str:
    """Diagnostic: 'native' if any direct key is set, else 'emergent' / 'none'."""
    if _has_native_key("anthropic") or _has_native_key("gemini"):
        return "native"
    if os.environ.get("EMERGENT_LLM_KEY"):
        return "emergent"
    return "none"

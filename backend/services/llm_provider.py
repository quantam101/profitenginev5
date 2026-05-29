"""LLM provider abstraction — single chat-completion call across providers.

Free-tier and low-cost provider strategy:

1. **Gemini Flash** — Google AI Studio (free tier: 15 RPM, 1M tok/day forever).
   Used for the cheap distillation tier. Key: GEMINI_API_KEY.
2. **DeepSeek Chat** — OpenAI-compatible API, very cheap.
   Used for the expensive distillation tier. Key: DEEPSEEK_API_KEY.
3. **OpenRouter** — aggregator with many free models. Used as a generic
   fallback for either tier. Key: OPENROUTER_API_KEY.
4. **Anthropic** — official anthropic SDK. Optional. Key: ANTHROPIC_API_KEY.

The `provider` arg accepted by `call_llm` maps to one of these transports.
"""
from __future__ import annotations

import os
from typing import Literal

Provider = Literal["gemini", "deepseek", "openrouter", "anthropic", "openai", "groq"]


def _has_key(provider: Provider) -> bool:
    return bool({
        "gemini": os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"),
        "deepseek": os.environ.get("DEEPSEEK_API_KEY"),
        "openrouter": os.environ.get("OPENROUTER_API_KEY"),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
        "openai": os.environ.get("OPENAI_API_KEY"),
        "groq": os.environ.get("GROQ_API_KEY"),
    }.get(provider))


async def _call_gemini(*, model: str, system: str, prompt: str, max_tokens: int) -> str:
    """Official google-genai SDK — free tier."""
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


async def _call_openai_compatible(
    *, base_url: str, api_key: str, model: str, system: str,
    prompt: str, max_tokens: int, extra_headers: dict | None = None,
) -> str:
    """Shared helper for OpenAI-protocol endpoints (DeepSeek, OpenRouter)."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url=base_url,
                         default_headers=extra_headers or {})
    msg = await client.chat.completions.create(
        model=model, max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return msg.choices[0].message.content or ""


async def _call_deepseek(*, model: str, system: str, prompt: str, max_tokens: int) -> str:
    return await _call_openai_compatible(
        base_url="https://api.deepseek.com",
        api_key=os.environ["DEEPSEEK_API_KEY"],
        model=model, system=system, prompt=prompt, max_tokens=max_tokens,
    )


async def _call_openrouter(*, model: str, system: str, prompt: str, max_tokens: int) -> str:
    return await _call_openai_compatible(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=model, system=system, prompt=prompt, max_tokens=max_tokens,
        extra_headers={
            "HTTP-Referer": os.environ.get("APP_PUBLIC_URL", "https://profitengine.app"),
            "X-Title": "ProfitEngine",
        },
    )


async def _call_openai(*, model: str, system: str, prompt: str, max_tokens: int) -> str:
    """OpenAI official endpoint via the openai SDK."""
    return await _call_openai_compatible(
        base_url="https://api.openai.com/v1",
        api_key=os.environ["OPENAI_API_KEY"],
        model=model, system=system, prompt=prompt, max_tokens=max_tokens,
    )


async def _call_groq(*, model: str, system: str, prompt: str, max_tokens: int) -> str:
    """Groq Cloud — free tier, OpenAI-compatible, very fast inference."""
    return await _call_openai_compatible(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
        model=model, system=system, prompt=prompt, max_tokens=max_tokens,
    )


async def _call_anthropic(*, model: str, system: str, prompt: str, max_tokens: int) -> str:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = await client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
    return "".join(parts) or ""


# Map provider name → (callable, default-model-env-var, hardcoded-default)
_DISPATCH = {
    "gemini": _call_gemini,
    "deepseek": _call_deepseek,
    "openrouter": _call_openrouter,
    "openai": _call_openai,
    "anthropic": _call_anthropic,
    "groq": _call_groq,
}


async def call_llm(
    *, provider: Provider, model: str, system: str, prompt: str,
    max_tokens: int, session_id: str = "",  # session_id kept for API compat; unused
) -> str:
    """Send a single completion. Raises if the requested provider has no key."""
    del session_id  # unused — kept in signature for backward compat
    if provider not in _DISPATCH:
        raise RuntimeError(f"Unknown LLM provider: {provider}")
    if not _has_key(provider):
        raise RuntimeError(
            f"No credentials for provider '{provider}'. "
            f"Set the matching API key env var "
            f"(GEMINI_API_KEY / DEEPSEEK_API_KEY / OPENROUTER_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY / GROQ_API_KEY)."
        )
    fn = _DISPATCH[provider]
    return await fn(model=model, system=system, prompt=prompt, max_tokens=max_tokens)


def active_transport() -> str:
    """Diagnostic: comma-separated list of providers with keys configured."""
    have = [p for p in _DISPATCH if _has_key(p)]
    return ",".join(have) if have else "none"

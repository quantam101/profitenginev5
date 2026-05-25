"""
Groq gateway — fast free inference via Groq Cloud API.

Groq processes 700+ tokens/second on llama-3.3-70b-versatile (free tier).
This is ~30-50x faster than Ollama on OCI A1 ARM CPU.

Set GROQ_API_KEY in your server .env to activate this tier.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import httpx

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_groq(system: str, user_message: str, max_tokens: int = 1024) -> Optional[str]:
    """
    Call Groq API. Returns the text response or None if key is not set.
    Returns "GROQ_ERROR: ..." string on API failure (never raises).
    """
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return None

    model = os.getenv("GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile")
    timeout = float(os.getenv("GMAOS_GROQ_TIMEOUT", "60"))

    try:
        response = httpx.post(
            _GROQ_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        return f"GROQ_ERROR: HTTP {exc.response.status_code}"
    except Exception as exc:
        return f"GROQ_ERROR: {exc}"

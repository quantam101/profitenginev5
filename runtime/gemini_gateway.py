"""
Gemini gateway — free Google AI inference.

Gemini 1.5 Flash: free tier, 1M token context, fast and high quality.
Great for content generation, summarization, SEO optimization.

Set GEMINI_API_KEY in your server .env to activate this tier.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini(system: str, user_message: str, max_tokens: int = 1024) -> Optional[str]:
    """
    Call Gemini API. Returns text response or None if key is not set.
    Returns "GEMINI_ERROR: ..." on failure (never raises).
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None

    model = os.getenv("GMAOS_GEMINI_MODEL", "gemini-1.5-flash")
    timeout = float(os.getenv("GMAOS_GEMINI_TIMEOUT", "60"))
    url = f"{_GEMINI_BASE}/{model}:generateContent"

    try:
        response = httpx.post(
            url,
            params={"key": key},
            json={
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7,
                },
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except httpx.HTTPStatusError as exc:
        return f"GEMINI_ERROR: HTTP {exc.response.status_code}"
    except (KeyError, IndexError) as exc:
        return f"GEMINI_ERROR: unexpected response shape: {exc}"
    except Exception as exc:
        return f"GEMINI_ERROR: {exc}"

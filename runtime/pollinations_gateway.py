"""
Pollinations AI gateway — zero-key free fallback.

Pollinations provides truly free AI text generation with no API key or
account required.  OpenAI-compatible endpoint at:
  https://text.pollinations.ai/openai

This is the final cloud fallback before the deterministic stub — it is
always available and costs nothing, making it the ultimate safety net.

Available models (as of 2026):
  openai          — GPT-4o-mini proxy (default)
  mistral         — Mistral 7B
  llama            — Llama 3 proxy
  claude-hybridspace — limited Claude access

Environment variables:
  GMAOS_POLLINATIONS_MODEL   — model to use (default: openai)
  GMAOS_POLLINATIONS_TIMEOUT — request timeout seconds (default: 45)
  POLLINATIONS_DISABLED      — "true" to disable (useful in strict mode)

No API key required.  Set POLLINATIONS_DISABLED=true to skip this tier.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

_POLLINATIONS_URL = "https://text.pollinations.ai/openai"
_DEFAULT_MODEL = "openai"
_DEFAULT_TIMEOUT = 45


def call_pollinations(
    system: str,
    user_message: str,
    max_tokens: int = 1024,
) -> Optional[str]:
    """
    Call Pollinations AI — no key needed, always available.

    Returns:
        str   — model reply text on success.
        str   — "POLLINATIONS_ERROR: ..." on failure.
        None  — if explicitly disabled via POLLINATIONS_DISABLED=true.
    """
    if os.getenv("POLLINATIONS_DISABLED", "").lower() in ("1", "true", "yes"):
        return None

    model = os.getenv("GMAOS_POLLINATIONS_MODEL", _DEFAULT_MODEL)
    try:
        timeout = int(os.getenv("GMAOS_POLLINATIONS_TIMEOUT", str(_DEFAULT_TIMEOUT)))
    except ValueError:
        timeout = _DEFAULT_TIMEOUT

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False,
        "private": True,   # don't log on Pollinations public feed
        "seed": -1,        # random seed
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            _POLLINATIONS_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
            # Pollinations returns OpenAI-compatible response
            content = body["choices"][0]["message"]["content"]
            return content if content else None
    except urllib.error.URLError as exc:
        return f"POLLINATIONS_ERROR: network — {exc.reason}"
    except (KeyError, json.JSONDecodeError) as exc:
        return f"POLLINATIONS_ERROR: bad response — {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"POLLINATIONS_ERROR: {exc}"

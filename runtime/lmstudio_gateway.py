"""
LM Studio gateway — local OpenAI-compatible inference server.

LM Studio runs at localhost:1234 (default) and serves any GGUF model
via the OpenAI Chat Completions API.  No API key required.

Priority: highest — free, private, zero latency overhead.

Environment variables:
  LM_STUDIO_BASE_URL   — base URL  (default: http://localhost:1234/v1)
  LM_STUDIO_MODEL      — model name to request (default: local-model)
  LM_STUDIO_ENABLED    — "true"/"1"/"yes" to force-enable without BASE_URL
  GMAOS_LMS_TIMEOUT    — request timeout in seconds (default: 120)

Returns None  — if not configured / server unreachable (graceful degrade).
Returns str   — reply text on success.
Returns str   — "LMSTUDIO_ERROR: ..." on unexpected error.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

_DEFAULT_BASE_URL = "http://localhost:1234/v1"
_DEFAULT_MODEL = "local-model"
_DEFAULT_TIMEOUT = 120


def _enabled() -> bool:
    if os.getenv("LM_STUDIO_BASE_URL", "").strip():
        return True
    return os.getenv("LM_STUDIO_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def _base_url() -> str:
    return os.getenv("LM_STUDIO_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _model() -> str:
    raw = os.getenv("LM_STUDIO_MODELS", "").strip()
    first = raw.split(",")[0].strip() if raw else ""
    return (
        os.getenv("LM_STUDIO_MODEL", "").strip()
        or first
        or _DEFAULT_MODEL
    )


def call_lmstudio(
    system: str,
    user_message: str,
    max_tokens: int = 1024,
) -> Optional[str]:
    """
    Call LM Studio's OpenAI-compatible /chat/completions endpoint.

    Returns:
        str   — model reply text on success.
        str   — "LMSTUDIO_ERROR: ..." on unexpected error.
        None  — if not configured or server is unreachable.
    """
    if not _enabled():
        return None

    base = _base_url()
    model = _model()
    try:
        timeout = int(os.getenv("GMAOS_LMS_TIMEOUT", str(_DEFAULT_TIMEOUT)))
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
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", "Authorization": "Bearer lm-studio"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
            return body["choices"][0]["message"]["content"]
    except urllib.error.URLError:
        # LM Studio not running — degrade gracefully to next tier
        return None
    except (KeyError, json.JSONDecodeError) as exc:
        return f"LMSTUDIO_ERROR: malformed response — {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"LMSTUDIO_ERROR: {exc}"

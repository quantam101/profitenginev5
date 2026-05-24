"""
Ollama local inference gateway for GMAOS runtime agents.

Calls the Ollama native chat API at:
  http://<GMAOS_LOCAL_MODEL_ENDPOINT>/api/chat

Environment variables:
  GMAOS_LOCAL_MODEL_ENABLED   — "true" to activate (default: false)
  GMAOS_LOCAL_MODEL_ENDPOINT  — Ollama base URL (default: http://localhost:11434)
                                 Docker: set to http://ollama:11434
  GMAOS_LOCAL_MODEL_NAME      — model tag (default: llama3.1:8b)
  GMAOS_LOCAL_MODEL_TIMEOUT   — per-request timeout seconds (default: 120)

Returns None  — if disabled or Ollama is unreachable (degrade to next tier).
Returns str   — reply text on success.
Returns str   — "OLLAMA_ERROR: ..." on unexpected non-network error.

OCI A1 ARM guidance:
  4 OCPUs / 24 GB RAM — runs 7-8B 4-bit models (~15-30 tok/s CPU-only).
  Recommended models (in order of quality/speed trade-off):
    llama3.1:8b   — best all-round general intelligence  (default)
    qwen2.5:7b    — strong for SEO/multilingual content
    phi3.5:3.8b   — fastest, good for short structured tasks
    mistral:7b    — good for coding / reasoning tasks
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.1:8b"
_DEFAULT_TIMEOUT = 120


def call_ollama(
    system: str,
    user_message: str,
    max_tokens: int = 512,
) -> Optional[str]:
    """
    Call Ollama's /api/chat endpoint.

    Returns:
        str   — model reply text on success.
        str   — "OLLAMA_ERROR: ..." on unexpected error.
        None  — if disabled or Ollama is unreachable (enables tier fallback).
    """
    enabled = os.getenv("GMAOS_LOCAL_MODEL_ENABLED", "false").lower() == "true"
    if not enabled:
        return None

    base_url = os.getenv("GMAOS_LOCAL_MODEL_ENDPOINT", _DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("GMAOS_LOCAL_MODEL_NAME", _DEFAULT_MODEL)
    try:
        timeout = int(os.getenv("GMAOS_LOCAL_MODEL_TIMEOUT", str(_DEFAULT_TIMEOUT)))
    except ValueError:
        timeout = _DEFAULT_TIMEOUT

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"num_predict": max_tokens},
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
            return body["message"]["content"]
    except urllib.error.URLError:
        # Ollama not running — degrade gracefully to next tier
        return None
    except (KeyError, json.JSONDecodeError) as exc:
        return f"OLLAMA_ERROR: malformed response — {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"OLLAMA_ERROR: {exc}"

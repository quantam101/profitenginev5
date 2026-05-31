"""
HuggingFace Inference API gateway — free cloud inference.

Uses HuggingFace's OpenAI-compatible /v1/chat/completions endpoint.
Free tier: rate-limited, no credit card required.  Thousands of open
models (Llama, Phi, Mistral, Qwen, DeepSeek, Gemma, Zephyr...).

Priority: after local providers (LM Studio / Ollama), before paid cloud.

Environment variables:
  HF_TOKEN or HUGGINGFACE_API_KEY — HuggingFace read token (required)
  GMAOS_HF_MODEL                  — model repo-id  (default below)
  GMAOS_HF_FALLBACK_MODELS        — comma-sep list tried in order
  GMAOS_HF_TIMEOUT                — request timeout seconds (default: 60)

Default model cascade (tried in order if primary fails):
  meta-llama/Llama-3.2-3B-Instruct   — fast, small, good general quality
  microsoft/Phi-3.5-mini-instruct     — very efficient 3.8B
  mistralai/Mistral-7B-Instruct-v0.3 — reliable 7B
  HuggingFaceH4/zephyr-7b-beta        — chat-tuned, consistent
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

_HF_API_BASE = "https://api-inference.huggingface.co/models"

_DEFAULT_MODELS = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "microsoft/Phi-3.5-mini-instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
]


def _api_key() -> str:
    return (
        os.getenv("HF_TOKEN", "").strip()
        or os.getenv("HUGGINGFACE_API_KEY", "").strip()
    )


def _models_to_try() -> list[str]:
    primary = os.getenv("GMAOS_HF_MODEL", "").strip()
    fallbacks_raw = os.getenv("GMAOS_HF_FALLBACK_MODELS", "").strip()
    fallbacks = [m.strip() for m in fallbacks_raw.split(",") if m.strip()]
    if primary:
        return [primary] + (fallbacks or _DEFAULT_MODELS)
    return fallbacks or _DEFAULT_MODELS


def call_huggingface(
    system: str,
    user_message: str,
    max_tokens: int = 1024,
) -> Optional[str]:
    """
    Call HuggingFace Inference API (OpenAI-compatible).

    Tries each model in sequence until one succeeds.

    Returns:
        str   — model reply text on success.
        str   — "HF_ERROR: ..." if all models fail.
        None  — if HF_TOKEN / HUGGINGFACE_API_KEY not set.
    """
    key = _api_key()
    if not key:
        return None

    try:
        timeout = int(os.getenv("GMAOS_HF_TIMEOUT", "60"))
    except ValueError:
        timeout = 60

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    last_error = "no_models_tried"
    for model in _models_to_try():
        url = f"{_HF_API_BASE}/{model}/v1/chat/completions"
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
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            # 503 = model loading, 429 = rate-limited → try next model
            last_error = f"HTTP {exc.code} on {model}"
            continue
        except urllib.error.URLError as exc:
            last_error = f"URLError on {model}: {exc.reason}"
            continue
        except (KeyError, json.JSONDecodeError) as exc:
            last_error = f"bad response from {model}: {exc}"
            continue
        except Exception as exc:  # noqa: BLE001
            last_error = f"{model}: {exc}"
            continue

    return f"HF_ERROR: all models failed — last: {last_error}"

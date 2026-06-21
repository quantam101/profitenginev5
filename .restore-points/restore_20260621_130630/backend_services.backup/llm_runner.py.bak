'use strict' if False else None  # noqa — Python file

"""
backend/services/llm_runner.py — ProfitEngine v5.0
Python LLM orchestrator mirroring core/llm/index.js.
Groq → OpenRouter → Gemini failover chain.
Circuit breaker per provider, daily token budget, request dedup.
"""

import hashlib
import os
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import requests

# ── Circuit Breaker ───────────────────────────────────────────────────────────

@dataclass
class _Breaker:
    failures: int = 0
    open_until: float = 0.0

_breakers: dict[str, _Breaker] = {}
_cb_lock = Lock()

def _cb(name: str) -> _Breaker:
    if name not in _breakers:
        _breakers[name] = _Breaker()
    return _breakers[name]

def _trip(name: str) -> None:
    with _cb_lock:
        b = _cb(name)
        b.failures += 1
        if b.failures >= 3:
            b.open_until = time.time() + min(300, 30 * b.failures)

def _close(name: str) -> None:
    with _cb_lock:
        _breakers[name] = _Breaker()

def _is_open(name: str) -> bool:
    return _cb(name).open_until > time.time()

# ── Token Budget ──────────────────────────────────────────────────────────────

_tokens_used: int = 0
_token_day: Optional[str] = None

def _check_budget(needed: int = 500) -> None:
    global _tokens_used, _token_day
    today = time.strftime("%Y-%m-%d")
    if _token_day != today:
        _tokens_used = 0
        _token_day = today
    limit = int(os.environ.get("DAILY_TOKEN_LIMIT", "500000"))
    if _tokens_used + needed > limit:
        raise RuntimeError(f"[LLM] Daily token budget exceeded ({_tokens_used}/{limit})")

def _track_tokens(provider: str, prompt_t: int, completion_t: int) -> None:
    global _tokens_used
    _tokens_used += prompt_t + completion_t

# ── Request Dedup ─────────────────────────────────────────────────────────────

_DEDUP: dict[str, dict] = {}
_DEDUP_TTL = 60  # seconds

def _dedup_key(prompt: str, system: Optional[str]) -> str:
    return hashlib.md5(((system or "") + prompt).encode()).hexdigest()

def _dedup_get(key: str) -> Optional[str]:
    entry = _DEDUP.get(key)
    if entry and time.time() - entry["ts"] < _DEDUP_TTL:
        return entry["value"]
    _DEDUP.pop(key, None)
    return None

def _dedup_set(key: str, value: str) -> None:
    _DEDUP[key] = {"value": value, "ts": time.time()}
    if len(_DEDUP) > 500:
        oldest = min(_DEDUP.items(), key=lambda x: x[1]["ts"])
        _DEDUP.pop(oldest[0], None)

# ── Provider Calls ────────────────────────────────────────────────────────────

def _groq(prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key or _is_open("groq"):
        raise RuntimeError("groq:unavailable")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": 0.7},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        _track_tokens("groq", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        _close("groq")
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        _trip("groq")
        raise e

def _openrouter(prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key or _is_open("openrouter"):
        raise RuntimeError("openrouter:unavailable")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={"model": model, "messages": msgs, "max_tokens": max_tokens},
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://alreadyherellc.com",
                "X-Title": "ProfitEngine",
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        _track_tokens("openrouter", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        _close("openrouter")
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        _trip("openrouter")
        raise e

def _gemini(prompt: str, system: Optional[str], max_tokens: int) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key or _is_open("gemini"):
        raise RuntimeError("gemini:unavailable")
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": f"[System]: {system}"}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            json={
                "contents": contents,
                "generationConfig": {
                    # gemini-2.5-flash is a thinking model: thinking tokens count against maxOutputTokens.
                    # Add a 3072-token thinking buffer so actual output always has full room.
                    "maxOutputTokens": max_tokens + 3072,
                    "temperature": 0.7,
                },
            },
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usageMetadata", {})
        _track_tokens("gemini", usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0))
        _close("gemini")
        parts = (data.get("candidates", [{}])[0]
                     .get("content", {})
                     .get("parts", []))
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise RuntimeError("gemini:empty_response")
        return text
    except Exception as e:
        _trip("gemini")
        raise e

# ── Tier Routing ──────────────────────────────────────────────────────────────

def _call_fast(prompt: str, system: Optional[str], max_tokens: int) -> str:
    errs = []
    for fn in [
        lambda: _groq(prompt, system, "gemma2-9b-it", max_tokens),
        lambda: _openrouter(prompt, system, "google/gemma-2-9b-it", max_tokens),
        lambda: _gemini(prompt, system, max_tokens),
    ]:
        try:
            return fn()
        except Exception as e:
            errs.append(str(e))
    raise RuntimeError(f"[LLM] All fast providers failed: {' | '.join(errs)}")

def _call_full(prompt: str, system: Optional[str], max_tokens: int) -> str:
    errs = []
    for fn in [
        lambda: _groq(prompt, system, "llama-3.3-70b-versatile", max_tokens),
        lambda: _openrouter(prompt, system, "meta-llama/llama-3.3-70b-instruct", max_tokens),
        lambda: _gemini(prompt, system, max_tokens),
    ]:
        try:
            return fn()
        except Exception as e:
            errs.append(str(e))
    raise RuntimeError(f"[LLM] All full providers failed: {' | '.join(errs)}")

# ── Public API ────────────────────────────────────────────────────────────────

def llm_complete(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 1500,
    fast: bool = False,
) -> str:
    """Run prompt through the failover chain (Groq → OpenRouter → Gemini). Returns text."""
    _check_budget(max_tokens)
    dk = _dedup_key(prompt, system)
    hit = _dedup_get(dk)
    if hit:
        return hit
    result = _call_fast(prompt, system, max_tokens) if fast else _call_full(prompt, system, max_tokens)
    _dedup_set(dk, result)
    return result

def tokens_used_today() -> int:
    return _tokens_used

def token_budget_remaining() -> int:
    limit = int(os.environ.get("DAILY_TOKEN_LIMIT", "500000"))
    return max(0, limit - _tokens_used)

def circuit_status() -> list[dict]:
    return [
        {"provider": name, "open": b.open_until > time.time(), "failures": b.failures}
        for name, b in _breakers.items()
    ]

def reset_breakers() -> None:
    global _tokens_used
    _breakers.clear()
    _tokens_used = 0

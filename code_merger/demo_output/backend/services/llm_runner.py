from __future__ import annotations
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from emergentintegrations.llm.chat import LlmChat, UserMessage
from services.distillation_service import cache_lookup, cache_store, distill_text, estimate_tokens
'use strict' if False else None
'\nbackend/services/llm_runner.py — ProfitEngine v5.0\nPython LLM orchestrator mirroring core/llm/index.js.\nGroq → OpenRouter → Gemini failover chain.\nCircuit breaker per provider, daily token budget, request dedup.\n'
import hashlib
import os
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional
import requests

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
_tokens_used: int = 0
_token_day: Optional[str] = None

def _check_budget(needed: int=500) -> None:
    global _tokens_used, _token_day
    today = time.strftime('%Y-%m-%d')
    if _token_day != today:
        _tokens_used = 0
        _token_day = today
    limit = int(os.environ.get('DAILY_TOKEN_LIMIT', '500000'))
    if _tokens_used + needed > limit:
        raise RuntimeError(f'[LLM] Daily token budget exceeded ({_tokens_used}/{limit})')

def _track_tokens(provider: str, prompt_t: int, completion_t: int) -> None:
    global _tokens_used
    _tokens_used += prompt_t + completion_t
_DEDUP: dict[str, dict] = {}
_DEDUP_TTL = 60

def _dedup_key(prompt: str, system: Optional[str]) -> str:
    return hashlib.md5(((system or '') + prompt).encode()).hexdigest()

def _dedup_get(key: str) -> Optional[str]:
    entry = _DEDUP.get(key)
    if entry and time.time() - entry['ts'] < _DEDUP_TTL:
        return entry['value']
    _DEDUP.pop(key, None)
    return None

def _dedup_set(key: str, value: str) -> None:
    _DEDUP[key] = {'value': value, 'ts': time.time()}
    if len(_DEDUP) > 500:
        oldest = min(_DEDUP.items(), key=lambda x: x[1]['ts'])
        _DEDUP.pop(oldest[0], None)

def _groq(prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
    key = os.environ.get('GROQ_API_KEY')
    if not key or _is_open('groq'):
        raise RuntimeError('groq:unavailable')
    msgs = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    msgs.append({'role': 'user', 'content': prompt})
    try:
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions', json={'model': model, 'messages': msgs, 'max_tokens': max_tokens, 'temperature': 0.7}, headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get('usage', {})
        _track_tokens('groq', usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0))
        _close('groq')
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        _trip('groq')
        raise e

def _openrouter(prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key or _is_open('openrouter'):
        raise RuntimeError('openrouter:unavailable')
    msgs = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    msgs.append({'role': 'user', 'content': prompt})
    try:
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions', json={'model': model, 'messages': msgs, 'max_tokens': max_tokens}, headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'HTTP-Referer': 'https://alreadyherellc.com', 'X-Title': 'ProfitEngine'}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get('usage', {})
        _track_tokens('openrouter', usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0))
        _close('openrouter')
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        _trip('openrouter')
        raise e

def _gemini(prompt: str, system: Optional[str], max_tokens: int) -> str:
    key = os.environ.get('GEMINI_API_KEY')
    if not key or _is_open('gemini'):
        raise RuntimeError('gemini:unavailable')
    contents = []
    if system:
        contents.append({'role': 'user', 'parts': [{'text': f'[System]: {system}'}]})
    contents.append({'role': 'user', 'parts': [{'text': prompt}]})
    try:
        resp = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}', json={'contents': contents, 'generationConfig': {'maxOutputTokens': max_tokens + 3072, 'temperature': 0.7}}, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get('usageMetadata', {})
        _track_tokens('gemini', usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0))
        _close('gemini')
        parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        text = ''.join((p.get('text', '') for p in parts)).strip()
        if not text:
            raise RuntimeError('gemini:empty_response')
        return text
    except Exception as e:
        _trip('gemini')
        raise e

def _call_fast(prompt: str, system: Optional[str], max_tokens: int) -> str:
    errs = []
    for fn in [lambda: _groq(prompt, system, 'gemma2-9b-it', max_tokens), lambda: _openrouter(prompt, system, 'google/gemma-2-9b-it', max_tokens), lambda: _gemini(prompt, system, max_tokens)]:
        try:
            return fn()
        except Exception as e:
            errs.append(str(e))
    raise RuntimeError(f"[LLM] All fast providers failed: {' | '.join(errs)}")

def _call_full(prompt: str, system: Optional[str], max_tokens: int) -> str:
    errs = []
    for fn in [lambda: _groq(prompt, system, 'llama-3.3-70b-versatile', max_tokens), lambda: _openrouter(prompt, system, 'meta-llama/llama-3.3-70b-instruct', max_tokens), lambda: _gemini(prompt, system, max_tokens)]:
        try:
            return fn()
        except Exception as e:
            errs.append(str(e))
    raise RuntimeError(f"[LLM] All full providers failed: {' | '.join(errs)}")

async def llm_complete(system: str, user: str, *, max_tokens: int=1500, temperature: float=0.7, session_id: str='llm-complete') -> str:
    """
    Smart multi-provider LLM call with automatic failover.

    Tries providers in priority order (Groq first — fastest & free).
    Falls through to the next provider on any error (expired key, rate limit, 4xx/5xx).

    Use this in routes / agents instead of hardcoding run_cached(provider="gemini", …).
    Does NOT use the distillation cache or budget tracker — it is stateless.
    If you need caching, call run_cached() directly after this.

    Raises HTTPException(502) only when ALL configured providers fail.
    Raises HTTPException(503) when no providers are configured.
    """
    providers = _failover_providers()
    if not providers:
        raise HTTPException(status_code=503, detail='No LLM keys configured. Set GROQ_API_KEY or EMERGENT_LLM_KEY in .env.')
    last_error: Exception | None = None
    for provider, model, api_key in providers:
        try:
            logger.debug('llm_complete: trying provider=%s model=%s', provider, model)
            import uuid as _uuid
            sid = f'{session_id}-{_uuid.uuid4().hex[:8]}'
            chat = LlmChat(api_key=api_key, session_id=sid, system_message=system)
            chat.with_model(provider, model)
            response = await chat.send_message(UserMessage(text=user))
            if response:
                logger.info('llm_complete: success provider=%s model=%s', provider, model)
                return response
        except Exception as exc:
            last_error = exc
            logger.warning('llm_complete: provider=%s model=%s failed: %s — trying next', provider, model, str(exc)[:120])
            continue
    raise HTTPException(status_code=502, detail=f'All LLM providers failed. Last error: {last_error}')

def tokens_used_today() -> int:
    return _tokens_used

def token_budget_remaining() -> int:
    limit = int(os.environ.get('DAILY_TOKEN_LIMIT', '500000'))
    return max(0, limit - _tokens_used)

def circuit_status() -> list[dict]:
    return [{'provider': name, 'open': b.open_until > time.time(), 'failures': b.failures} for name, b in _breakers.items()]

def reset_breakers() -> None:
    global _tokens_used
    _breakers.clear()
    _tokens_used = 0

def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()

def _daily_cap() -> int:
    """Daily token cap (in + out combined). 0 = unlimited."""
    try:
        return int(os.environ.get('LLM_DAILY_TOKEN_CAP', '0'))
    except ValueError:
        return 0

async def _get_today_row(db) -> dict:
    today = _today_iso()
    row = await db[BUDGET_COLLECTION].find_one({'date': today}, {'_id': 0})
    if not row:
        row = {'id': f'budget-{today}', 'date': today, 'tokens_in': 0, 'tokens_out': 0, 'calls': 0, 'blocked': 0, 'cache_hits': 0}
        try:
            await db[BUDGET_COLLECTION].insert_one(row)
        except Exception:
            row = await db[BUDGET_COLLECTION].find_one({'date': today}, {'_id': 0}) or row
    return row

async def get_today_usage(db) -> dict:
    """Operator-facing daily summary."""
    row = await _get_today_row(db)
    cap = _daily_cap()
    used = int(row.get('tokens_in', 0)) + int(row.get('tokens_out', 0))
    return {'date': row['date'], 'tokens_in': int(row.get('tokens_in', 0)), 'tokens_out': int(row.get('tokens_out', 0)), 'tokens_total': used, 'calls': int(row.get('calls', 0)), 'cache_hits': int(row.get('cache_hits', 0)), 'blocked': int(row.get('blocked', 0)), 'daily_cap': cap, 'remaining': cap - used if cap else None, 'over_cap': bool(cap and used >= cap)}

async def _record_call(db, *, tokens_in: int, tokens_out: int, cache_hit: bool=False):
    """Best-effort: bump the daily counters. Never fail the calling request."""
    today = _today_iso()
    try:
        await _get_today_row(db)
        inc = {'calls': 1}
        if cache_hit:
            inc['cache_hits'] = 1
            inc['tokens_in'] = 0
            inc['tokens_out'] = 0
        else:
            inc['tokens_in'] = int(tokens_in)
            inc['tokens_out'] = int(tokens_out)
        await db[BUDGET_COLLECTION].update_one({'date': today}, {'$inc': inc})
    except Exception as e:
        logger.warning('llm budget bump failed: %s', e)

async def _record_blocked(db) -> None:
    today = _today_iso()
    try:
        await _get_today_row(db)
        await db[BUDGET_COLLECTION].update_one({'date': today}, {'$inc': {'blocked': 1}})
    except Exception:
        pass

async def check_daily_budget(db, *, expected_tokens: int=0) -> None:
    """Raise HTTP 429 if today's usage + expected next call would exceed cap.

    Pass `expected_tokens` if you know the rough size of the prompt — this
    short-circuits BEFORE the LLM call, so you don't burn the call to discover
    the budget is gone.
    """
    cap = _daily_cap()
    if cap <= 0:
        return
    row = await _get_today_row(db)
    used = int(row.get('tokens_in', 0)) + int(row.get('tokens_out', 0))
    if used + expected_tokens >= cap:
        await _record_blocked(db)
        raise HTTPException(status_code=429, detail=f'Daily LLM token cap reached ({used}/{cap}). Bump LLM_DAILY_TOKEN_CAP env or wait for UTC midnight.')

async def run_cached(db, provider: str, model: str, system_msg: str, prompt: str, *, session_id: str, tier: int=3, parse_json: bool=False) -> str:
    """One-stop LLM call: distill → cache-lookup → budget-check → LLM → cache-store.

    Returns the raw LLM response string. Caller is responsible for parsing it.
    On cache hit, no LLM call is made and the budget is not charged.
    """
    api_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('GROQ_API_KEY') or ''
    if not api_key:
        raise HTTPException(status_code=503, detail='No LLM key configured (set EMERGENT_LLM_KEY or GROQ_API_KEY)')
    model_id = f'{provider}/{model}'
    distilled_prompt = distill_text(prompt)
    try:
        hit = await cache_lookup(db, model_id, system_msg, distilled_prompt)
    except Exception:
        hit = None
    if hit and hit.get('response'):
        await _record_call(db, tokens_in=0, tokens_out=0, cache_hit=True)
        logger.info('llm_runner: cache HIT session=%s', session_id)
        return hit['response']
    estimated = estimate_tokens(distilled_prompt) + estimate_tokens(system_msg)
    await check_daily_budget(db, expected_tokens=estimated)
    chat = LlmChat(api_key=api_key, session_id=session_id, system_message=system_msg)
    chat.with_model(provider, model)
    try:
        response = await chat.send_message(UserMessage(text=distilled_prompt))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'LLM call failed: {e}') from e
    await _record_call(db, tokens_in=estimated, tokens_out=estimate_tokens(response), cache_hit=False)
    try:
        await cache_store(db, model_id, system_msg, distilled_prompt, response, tier=tier)
    except Exception:
        pass
    return response

async def daily_usage_history(db, days: int=14) -> list[dict]:
    """Last N days of LLM budget rows, newest first."""
    rows = await db[BUDGET_COLLECTION].find({}, {'_id': 0}).sort('date', -1).to_list(days)
    return rows

def _failover_providers() -> list[tuple[str, str, str]]:
    """
    Build the ordered provider list from available env vars.
    Returns list of (provider_name, model_id, api_key).
    Priority: Groq (fastest, free) → Gemini Flash → Mistral → DeepSeek → OpenRouter
    """
    providers: list[tuple[str, str, str]] = []
    gr = os.environ.get('GROQ_API_KEY', '').strip()
    lm = os.environ.get('EMERGENT_LLM_KEY', '').strip()
    ms = os.environ.get('MISTRAL_API_KEY', '').strip()
    ds = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    qw = os.environ.get('QWEN_API_KEY', '').strip()
    or_ = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if gr:
        providers.append(('groq', 'llama-3.3-70b-versatile', gr))
        providers.append(('groq', 'llama-3.1-8b-instant', gr))
    if lm:
        providers.append(('gemini', 'gemini-2.5-flash', lm))
    if ms:
        providers.append(('mistral', 'mistral-small-latest', ms))
        providers.append(('codestral', 'codestral-latest', ms))
    if ds:
        providers.append(('deepseek', 'deepseek-chat', ds))
    if qw:
        providers.append(('qwen', 'qwen-plus', qw))
    if or_:
        providers.append(('openrouter', 'openai/gpt-4o-mini', or_))
    if lm:
        providers.append(('gemini', 'gemini-1.5-flash', lm))
    return providers

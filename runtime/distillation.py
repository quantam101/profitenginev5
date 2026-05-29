"""
Data Distillation Pipeline — maximise information density before LLM calls.

Every token sent to a model costs money (or rate-limit quota). This module
compresses raw text through four deterministic stages before any LLM sees it:

  Stage 1  noise_strip       — strip HTML, markdown fences, boilerplate
  Stage 2  dedup_sentences   — remove repeated / near-identical sentences
  Stage 3  keyword_focus     — surface sentences most relevant to objective
  Stage 4  budget_truncate   — hard-cap to char budget (tokens approx chars / 4)

None of these stages call an LLM. Zero cost. Fast (< 5 ms on typical inputs).

Usage
-----
    from runtime.distillation import distill, estimate_tokens

    compressed = distill(raw_text, objective="your task here", char_budget=8192)
    tok = estimate_tokens(compressed)   # rough token count

Tuning
------
Set env vars to override defaults:
  DISTILL_DEDUP_THRESHOLD   float 0-1  word-overlap threshold for dedup (default 0.72)
  DISTILL_FOCUS_TOP_N       int        sentences kept after keyword focus  (default 40)
  DISTILL_BUDGET_DEFAULT    int        default char budget                 (default 8192)
"""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import Any, List, Optional

_DEDUP_THRESHOLD: float = float(os.getenv('DISTILL_DEDUP_THRESHOLD', '0.72'))
_FOCUS_TOP_N: int = int(os.getenv('DISTILL_FOCUS_TOP_N', '40'))
_BUDGET_DEFAULT: int = int(os.getenv('DISTILL_BUDGET_DEFAULT', '8192'))
_HTML_TAG = re.compile('<[^>]{1,200}>')
_HTML_ENTITY = re.compile('&(?:[a-z]{2,8}|#\\d{1,5});', re.I)
_MARKDOWN_FENCE = re.compile('```[a-zA-Z0-9_-]*\\n?|```')
_MARKDOWN_HEADING = re.compile('^#{1,6}\\s+', re.MULTILINE)
_MARKDOWN_RULE = re.compile('^[=\\-\\*]{3,}\\s*$', re.MULTILINE)
_MARKDOWN_LINK = re.compile('!?\\[([^\\]]*)\\]\\([^)]*\\)')
_URL_BARE = re.compile('https?://\\S+')
_MULTISPACE = re.compile('[ \\t]{2,}')
_MULTIBLANK = re.compile('\\n{3,}')
_BOILERPLATE_RE = re.compile(
    '(cookie\\s+policy|privacy\\s+policy|terms\\s+of\\s+(use|service)|'
    'all\\s+rights\\s+reserved|copyright\\s+\\d{4}|subscribe\\s+to\\s+our\\s+newsletter|'
    'sign\\s+up|log\\s+in|advertisement|share\\s+this\\s+article)',
    re.I,
)
_STOP_WORDS = frozenset(
    'a an the is are was were be been being have has had do does did will would '
    'could should may might shall can i you he she it we they what which who '
    'this that these those of in on at by for with from to as or and but if so '
    'not no nor yet both either neither than then such than because since while '
    'though although when where how'.split()
)

# ── Backend imports (FastAPI router, pydantic, services) ─────────────────────
_BACKEND_AVAILABLE = False
try:
    from fastapi import APIRouter, Depends
    from pydantic import BaseModel
    from services.distillation_service import (  # type: ignore[import]
        CACHE_TTL_SECONDS, cache_clear, cache_stats, distill_text,
        to_yaml_payload,
    )
    from services.llm_runner import daily_usage_history, get_today_usage  # type: ignore[import]
    router = APIRouter()
    _BACKEND_AVAILABLE = True
except ImportError:
    router = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment,misc]


# ── Core pure-Python distillation functions ───────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ~ 4 chars for English prose."""
    return max(1, len(text) // 4)


def distill(
    text: str,
    objective: str = '',
    char_budget: int = _BUDGET_DEFAULT,
    run_dedup: bool = True,
    run_focus: bool = True,
) -> str:
    """
    Run all four distillation stages in sequence.
    Returns a string <= char_budget characters that preserves the highest-value
    information relative to *objective*.
    """
    text = noise_strip(text)
    if run_dedup:
        text = dedup_sentences(text)
    if run_focus and objective:
        text = keyword_focus(text, objective)
    text = budget_truncate(text, char_budget)
    return text


def noise_strip(text: str) -> str:
    """Remove HTML, markdown syntax, bare URLs, and boilerplate."""
    text = _HTML_TAG.sub(' ', text)
    text = _HTML_ENTITY.sub(' ', text)
    text = _MARKDOWN_FENCE.sub('', text)
    text = _MARKDOWN_HEADING.sub('', text)
    text = _MARKDOWN_RULE.sub('', text)
    text = _MARKDOWN_LINK.sub('\\1', text)
    text = _URL_BARE.sub('', text)
    lines = [ln for ln in text.splitlines() if not _BOILERPLATE_RE.search(ln)]
    text = '\n'.join(lines)
    text = _MULTISPACE.sub(' ', text)
    text = _MULTIBLANK.sub('\n\n', text)
    return text.strip()


def _tokenise(sentence: str) -> frozenset:
    words = re.findall('[a-z0-9]+', sentence.lower())
    return frozenset(w for w in words if w not in _STOP_WORDS)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedup_sentences(text: str, threshold: float = _DEDUP_THRESHOLD) -> str:
    """
    Remove sentences whose content is >= threshold Jaccard-similar to a
    previously seen sentence. Preserves order and keeps the first occurrence.
    """
    sentences = _split_sentences(text)
    seen_tokens: List[frozenset] = []
    kept: List[str] = []
    for sent in sentences:
        tok = _tokenise(sent)
        if len(tok) < 4:
            kept.append(sent)
            continue
        duplicate = any(_jaccard(tok, s) >= threshold for s in seen_tokens)
        if not duplicate:
            kept.append(sent)
            seen_tokens.append(tok)
    return ' '.join(kept)


def keyword_focus(text: str, objective: str, top_n: int = _FOCUS_TOP_N) -> str:
    """
    Score each sentence by word overlap with *objective* (TF-weighted).
    Keep the top_n highest-scoring sentences in their original order.
    """
    obj_words = Counter(
        w for w in re.findall('[a-z0-9]+', objective.lower())
        if w not in _STOP_WORDS and len(w) > 2
    )
    if not obj_words:
        return text
    sentences = _split_sentences(text)
    if len(sentences) <= top_n:
        return text
    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall('[a-z0-9]+', sent.lower())
        score = sum(obj_words.get(w, 0) for w in sent_words if w not in _STOP_WORDS)
        pos_bonus = max(0.0, 1.0 - i / len(sentences)) * 0.2
        scored.append((score + pos_bonus, i, sent))
    top = sorted(scored, key=lambda x: -x[0])[:top_n]
    top.sort(key=lambda x: x[1])
    return ' '.join(s for _, _, s in top)


def budget_truncate(text: str, char_budget: int) -> str:
    """
    Truncate to *char_budget* characters, breaking on a sentence boundary
    where possible to avoid cutting mid-thought.
    """
    if len(text) <= char_budget:
        return text
    truncated = text[:char_budget]
    for delim in ('.', '!', '?', '\n'):
        pos = truncated.rfind(delim)
        if pos > char_budget * 0.8:
            return truncated[:pos + 1].strip()
    return truncated.rstrip() + '...'


def _split_sentences(text: str) -> List[str]:
    """
    Split text into sentences. Handles common abbreviations to avoid false
    splits (e.g. "Dr. Smith", "e.g.", "2.5 GB").
    """
    text = re.sub(
        '(\\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\\.g|i\\.e|al))\\.',
        '\\1<DOT>',
        text,
    )
    text = re.sub('(\\d+)\\.(\\d+)', '\\1<DOT>\\2', text)
    parts = re.split('(?<=[.!?])\\s+(?=[A-Z\\"])|(?<=[.!?])\\n', text)
    result = []
    for part in parts:
        part = part.replace('<DOT>', '.').strip()
        if len(part) > 10:
            result.append(part)
    return result or [text.strip()]


def distill_prompt(
    system: str,
    user: str,
    objective: str,
    system_budget: Optional[int] = None,
    user_budget: Optional[int] = None,
) -> tuple[str, str, dict]:
    """
    Distill both halves of a chat prompt.

    Returns (compressed_system, compressed_user, metrics_dict).
    system_budget defaults to 25% of total, user_budget to 75%.
    """
    total_budget = _BUDGET_DEFAULT
    sys_bud = system_budget or int(total_budget * 0.25)
    user_bud = user_budget or int(total_budget * 0.75)
    sys_before = len(system)
    user_before = len(user)
    comp_system = budget_truncate(noise_strip(system), sys_bud)
    comp_user = distill(user, objective=objective, char_budget=user_bud)
    metrics = {
        'system_before': sys_before,
        'system_after': len(comp_system),
        'user_before': user_before,
        'user_after': len(comp_user),
        'total_before_tokens': estimate_tokens(system + user),
        'total_after_tokens': estimate_tokens(comp_system + comp_user),
        'reduction_pct': round(
            100 * (1 - (len(comp_system) + len(comp_user)) / max(1, sys_before + user_before)),
            1,
        ),
    }
    return (comp_system, comp_user, metrics)


# ── FastAPI routes (only registered when backend deps are available) ───────────

if _BACKEND_AVAILABLE:
    async def _get_db():
        from server import db  # type: ignore[import]
        return db

    class PreviewRequest(BaseModel):  # type: ignore[misc]
        text: str = ''
        payload: Optional[Any] = None
        max_chars: Optional[int] = None

    @router.get('/stats')  # type: ignore[union-attr]
    async def stats(db=Depends(_get_db)):
        return await cache_stats(db)

    @router.get('/config')  # type: ignore[union-attr]
    async def config():
        return {
            'ttl_seconds': CACHE_TTL_SECONDS,
            'token_cost_per_1k_usd': float(os.environ.get('TOKEN_COST_PER_1K', '0.0001')),
            'compression_enabled': True,
            'yaml_payloads_enabled': True,
            'tiers': {
                'tier_1': 'Local rule-based -- no LLM (hashtags, formatting, slugs)',
                'tier_2': 'Distill + cache lookup -- LLM only on miss',
                'tier_3': 'LLM call with compressed input + YAML payloads',
            },
        }

    @router.post('/preview')  # type: ignore[union-attr]
    async def preview(body: PreviewRequest):
        """Show the operator exactly what distillation does to their text."""
        distilled = distill_text(body.text, max_chars=body.max_chars)
        yaml_str = to_yaml_payload(body.payload) if body.payload is not None else ''
        json_alt = ''
        if body.payload is not None:
            import json
            json_alt = json.dumps(body.payload, separators=(',', ':'), default=str)
        return {
            'original': {
                'chars': len(body.text or ''),
                'tokens_est': estimate_tokens(body.text or ''),
            },
            'distilled': {
                'text': distilled,
                'chars': len(distilled),
                'tokens_est': estimate_tokens(distilled),
            },
            'savings': {
                'chars': max(0, len(body.text or '') - len(distilled)),
                'tokens_est': max(0, estimate_tokens(body.text or '') - estimate_tokens(distilled)),
                'percent': (
                    round(100 * (1 - len(distilled) / max(1, len(body.text or ''))), 1)
                    if body.text else 0.0
                ),
            },
            'yaml_payload': yaml_str,
            'json_payload': json_alt,
            'payload_savings_tokens_est': max(0, estimate_tokens(json_alt) - estimate_tokens(yaml_str)),
        }

    @router.post('/clear')  # type: ignore[union-attr]
    async def clear(db=Depends(_get_db)):
        n = await cache_clear(db)
        return {'deleted': n}

    @router.get('/budget')  # type: ignore[union-attr]
    async def budget(db=Depends(_get_db)):
        """Today's LLM token usage and daily cap status (Cost Guard hard floor)."""
        return await get_today_usage(db)

    @router.get('/budget/history')  # type: ignore[union-attr]
    async def budget_history(days: int = 14, db=Depends(_get_db)):
        """Last N days of LLM token usage rows (newest first)."""
        days = max(1, min(int(days), 90))
        return await daily_usage_history(db, days=days)

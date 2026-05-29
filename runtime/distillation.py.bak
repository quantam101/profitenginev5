"""
Data Distillation Pipeline — maximise information density before LLM calls.

Every token sent to a model costs money (or rate-limit quota). This module
compresses raw text through four deterministic stages before any LLM sees it:

  Stage 1  noise_strip       — strip HTML, markdown fences, boilerplate
  Stage 2  dedup_sentences   — remove repeated / near-identical sentences
  Stage 3  keyword_focus     — surface sentences most relevant to objective
  Stage 4  budget_truncate   — hard-cap to char budget (tokens ≈ chars / 4)

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
from typing import List, Optional

# ── tunables ────────────────────────────────────────────────────────────────
_DEDUP_THRESHOLD: float = float(os.getenv("DISTILL_DEDUP_THRESHOLD", "0.72"))
_FOCUS_TOP_N:     int   = int(os.getenv("DISTILL_FOCUS_TOP_N", "40"))
_BUDGET_DEFAULT:  int   = int(os.getenv("DISTILL_BUDGET_DEFAULT", "8192"))

# ── noise patterns ───────────────────────────────────────────────────────────
_HTML_TAG         = re.compile(r"<[^>]{1,200}>")
_HTML_ENTITY      = re.compile(r"&(?:[a-z]{2,8}|#\d{1,5});", re.I)
_MARKDOWN_FENCE   = re.compile(r"```[a-zA-Z0-9_-]*\n?|```")
_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_MARKDOWN_RULE    = re.compile(r"^[=\-\*]{3,}\s*$", re.MULTILINE)
_MARKDOWN_LINK    = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")  # keep label, drop URL
_URL_BARE         = re.compile(r"https?://\S+")
_MULTISPACE       = re.compile(r"[ \t]{2,}")
_MULTIBLANK       = re.compile(r"\n{3,}")

# boilerplate lines that add no information
_BOILERPLATE_RE = re.compile(
    r"(cookie\s+policy|privacy\s+policy|terms\s+of\s+(use|service)|"
    r"all\s+rights\s+reserved|copyright\s+\d{4}|subscribe\s+to\s+our\s+newsletter|"
    r"sign\s+up|log\s+in|advertisement|share\s+this\s+article)",
    re.I,
)

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "could should may might shall can i you he she it we they what which who "
    "this that these those of in on at by for with from to as or and but if so "
    "not no nor yet both either neither than then such than because since while "
    "though although when where how".split()
)


# ── public API ───────────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 chars for English prose."""
    return max(1, len(text) // 4)


def distill(
    text: str,
    objective: str = "",
    char_budget: int = _BUDGET_DEFAULT,
    run_dedup: bool = True,
    run_focus: bool = True,
) -> str:
    """
    Run all four distillation stages in sequence.
    Returns a string ≤ char_budget characters that preserves the highest-value
    information relative to *objective*.
    """
    text = noise_strip(text)
    if run_dedup:
        text = dedup_sentences(text)
    if run_focus and objective:
        text = keyword_focus(text, objective)
    text = budget_truncate(text, char_budget)
    return text


# ── stage 1: noise strip ─────────────────────────────────────────────────────

def noise_strip(text: str) -> str:
    """Remove HTML, markdown syntax, bare URLs, and boilerplate."""
    text = _HTML_TAG.sub(" ", text)
    text = _HTML_ENTITY.sub(" ", text)
    text = _MARKDOWN_FENCE.sub("", text)
    text = _MARKDOWN_HEADING.sub("", text)
    text = _MARKDOWN_RULE.sub("", text)
    text = _MARKDOWN_LINK.sub(r"\1", text)   # keep link label text
    text = _URL_BARE.sub("", text)

    # Strip boilerplate lines
    lines = [ln for ln in text.splitlines() if not _BOILERPLATE_RE.search(ln)]
    text = "\n".join(lines)

    text = _MULTISPACE.sub(" ", text)
    text = _MULTIBLANK.sub("\n\n", text)
    return text.strip()


# ── stage 2: sentence-level deduplication ────────────────────────────────────

def _tokenise(sentence: str) -> frozenset:
    words = re.findall(r"[a-z0-9]+", sentence.lower())
    return frozenset(w for w in words if w not in _STOP_WORDS)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedup_sentences(text: str, threshold: float = _DEDUP_THRESHOLD) -> str:
    """
    Remove sentences whose content is ≥ threshold Jaccard-similar to a
    previously seen sentence. Preserves order and keeps the first occurrence.
    """
    sentences = _split_sentences(text)
    seen_tokens: List[frozenset] = []
    kept: List[str] = []

    for sent in sentences:
        tok = _tokenise(sent)
        if len(tok) < 4:          # very short sentences: always keep
            kept.append(sent)
            continue
        duplicate = any(_jaccard(tok, s) >= threshold for s in seen_tokens)
        if not duplicate:
            kept.append(sent)
            seen_tokens.append(tok)

    return " ".join(kept)


# ── stage 3: keyword-focused extraction ──────────────────────────────────────

def keyword_focus(text: str, objective: str, top_n: int = _FOCUS_TOP_N) -> str:
    """
    Score each sentence by word overlap with *objective* (TF-weighted).
    Keep the top_n highest-scoring sentences in their original order.

    This is a deterministic, zero-cost approximation of RAG paragraph
    extraction — no embeddings, no model calls.
    """
    obj_words = Counter(
        w for w in re.findall(r"[a-z0-9]+", objective.lower())
        if w not in _STOP_WORDS and len(w) > 2
    )
    if not obj_words:
        return text

    sentences = _split_sentences(text)
    if len(sentences) <= top_n:
        return text

    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r"[a-z0-9]+", sent.lower())
        score = sum(obj_words.get(w, 0) for w in sent_words if w not in _STOP_WORDS)
        # small positional bonus to prefer sentences near start (context-setting)
        pos_bonus = max(0.0, 1.0 - i / len(sentences)) * 0.2
        scored.append((score + pos_bonus, i, sent))

    # Keep top_n by score, then re-sort by original position
    top = sorted(scored, key=lambda x: -x[0])[:top_n]
    top.sort(key=lambda x: x[1])
    return " ".join(s for _, _, s in top)


# ── stage 4: hard budget truncation ──────────────────────────────────────────

def budget_truncate(text: str, char_budget: int) -> str:
    """
    Truncate to *char_budget* characters, breaking on a sentence boundary
    where possible to avoid cutting mid-thought.
    """
    if len(text) <= char_budget:
        return text

    truncated = text[:char_budget]
    # Try to end on a sentence boundary
    for delim in (".", "!", "?", "\n"):
        pos = truncated.rfind(delim)
        if pos > char_budget * 0.80:      # don't cut more than 20% off
            return truncated[: pos + 1].strip()
    return truncated.rstrip() + "…"


# ── helpers ───────────────────────────────────────────────────────────────────

def _split_sentences(text: str) -> List[str]:
    """
    Split text into sentences. Handles common abbreviations to avoid false
    splits (e.g. "Dr. Smith", "e.g.", "2.5 GB").
    """
    # Protect common abbreviations
    text = re.sub(r"(\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e|al))\.", r"\1<DOT>", text)
    text = re.sub(r"(\d+)\.(\d+)", r"\1<DOT>\2", text)  # decimal numbers

    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"])|(?<=[.!?])\n", text)

    result = []
    for part in parts:
        part = part.replace("<DOT>", ".").strip()
        if len(part) > 10:
            result.append(part)
    return result or [text.strip()]


# ── convenience: compress a system+user prompt pair ──────────────────────────

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

    Metrics keys: system_before, system_after, user_before, user_after,
                  total_before_tokens, total_after_tokens, reduction_pct
    """
    total_budget = _BUDGET_DEFAULT
    sys_bud  = system_budget or int(total_budget * 0.25)
    user_bud = user_budget   or int(total_budget * 0.75)

    sys_before  = len(system)
    user_before = len(user)

    # System prompts: strip noise + truncate (don't focus — they're already concise)
    comp_system = budget_truncate(noise_strip(system), sys_bud)

    # User prompts: full pipeline
    comp_user = distill(user, objective=objective, char_budget=user_bud)

    metrics = {
        "system_before":       sys_before,
        "system_after":        len(comp_system),
        "user_before":         user_before,
        "user_after":          len(comp_user),
        "total_before_tokens": estimate_tokens(system + user),
        "total_after_tokens":  estimate_tokens(comp_system + comp_user),
        "reduction_pct":       round(
            100 * (1 - (len(comp_system) + len(comp_user)) / max(1, sys_before + user_before)), 1
        ),
    }
    return comp_system, comp_user, metrics

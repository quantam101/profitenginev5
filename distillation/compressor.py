"""
Semantic compression — pillar #1 + #3 of the distillation strategy.

We treat tokens as a limited currency. Every helper here removes "filler" from
text before it's handed to an LLM — without changing the meaning.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

try:
    import yaml  # PyYAML ships with the backend
except ImportError:  # pragma: no cover - graceful fallback
    yaml = None  # type: ignore


# A compact English stopword list. We avoid full NLTK to keep distillation
# dependency-free (logic offloading principle).
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "then", "so", "for", "to", "of", "in", "on",
    "at", "by", "with", "from", "as", "that", "this", "these", "those",
    "it", "its", "i", "you", "he", "she", "we", "they", "them", "his",
    "her", "their", "our", "your", "my", "me", "us", "him",
    "do", "does", "did", "have", "has", "had", "will", "would", "could",
    "should", "may", "might", "shall", "can", "must", "ought", "not",
    "no", "yes", "very", "just", "really", "actually", "quite", "rather",
})


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_MULTI_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^\w\s.,;:!?\-/]")


def strip_html(text: str) -> str:
    """Remove HTML tags and comments. Preserves visible text only."""
    text = _HTML_COMMENT_RE.sub(" ", text)
    text = _HTML_TAG_RE.sub(" ", text)
    return _MULTI_WS_RE.sub(" ", text).strip()


def _drop_stopwords(text: str) -> str:
    """Drop common stopwords. Case-insensitive, preserves punctuation chars."""
    out: list[str] = []
    for tok in text.split():
        bare = tok.strip(".,;:!?\"'()[]").lower()
        if bare and bare not in _STOPWORDS:
            out.append(tok)
    return " ".join(out)


@dataclass
class CompressionStats:
    original_chars: int
    compressed_chars: int
    original_tokens: int
    compressed_tokens: int
    savings_pct: float


def count_tokens(text: str) -> int:
    """Cheap token estimator — 1 token ≈ 4 chars (matches OpenAI's heuristic)."""
    return max(0, (len(text) + 3) // 4)


def compress(
    text: str,
    *,
    strip_html_tags: bool = True,
    drop_stopwords: bool = True,
    collapse_whitespace: bool = True,
    drop_non_word_chars: bool = False,
) -> tuple[str, CompressionStats]:
    """
    Compress ``text`` losslessly-ish for LLM consumption.

    Returns the compressed string and a :class:`CompressionStats` payload so the
    caller can prove the savings.
    """
    original = text
    if strip_html_tags:
        text = strip_html(text)
    if drop_non_word_chars:
        text = _NON_WORD_RE.sub("", text)
    if collapse_whitespace:
        text = _MULTI_WS_RE.sub(" ", text).strip()
    if drop_stopwords:
        text = _drop_stopwords(text)

    stats = CompressionStats(
        original_chars=len(original),
        compressed_chars=len(text),
        original_tokens=count_tokens(original),
        compressed_tokens=count_tokens(text),
        savings_pct=round(
            1 - (count_tokens(text) / count_tokens(original)) if count_tokens(original) else 0,
            4,
        ),
    )
    return text, stats


def yaml_vs_json(payload: dict[str, Any]) -> dict[str, int]:
    """
    Pillar #3 — show YAML vs JSON token cost for the same payload.

    Useful when emitting configuration: many models tokenize YAML cheaper than
    JSON because of the absence of braces and quotes.
    """
    json_str = json.dumps(payload, indent=2, ensure_ascii=False)
    if yaml is None:
        yaml_str = json_str  # graceful fallback
    else:
        yaml_str = yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
    return {
        "json_tokens": count_tokens(json_str),
        "yaml_tokens": count_tokens(yaml_str),
        "yaml_savings_pct": round(
            1 - (count_tokens(yaml_str) / count_tokens(json_str)) if count_tokens(json_str) else 0,
            4,
        ),
    }

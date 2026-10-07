"""SEO content quality and freshness gates for ProfitEngine.

The gate is intentionally deterministic and zero-cost. It catches structural defects,
known stale SEO claims, placeholders, and weak source hygiene before publication.
It does not attempt to replace editorial judgment or live web research.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityResult:
    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    word_count: int
    h2_count: int
    external_link_count: int


_PLACEHOLDER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\[(?:insert|placeholder|todo|tbd|edit)[^\]]*\]", re.I),
    re.compile(r"\b(?:lorem ipsum|coming soon|example\.com)\b", re.I),
    re.compile(r"\[(?:AFFILIATE|AMAZON_LINK)(?::[^\]]+)?\]", re.I),
)

# Claims we know are stale or materially misleading as of 2026-09-20.
_STALE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"tinypng.{0,80}\b500\b.{0,40}(?:compress|image).{0,30}(?:month|monthly)",
            re.I | re.S,
        ),
        "TinyPNG web usage is not a 500-compressions-per-month limit; distinguish the web optimizer from API quotas.",
    ),
    (
        re.compile(
            r"yoast.{0,120}(?:free|free version).{0,160}internal[- ]link(?:ing)? suggestion",
            re.I | re.S,
        ),
        "Yoast internal-linking suggestions are not a core free feature; do not attribute them to Yoast Free.",
    ),
    (
        re.compile(
            r"faq schema.{0,160}(?:people also ask|rich result|rich snippet|surface|boost)",
            re.I | re.S,
        ),
        "Do not recommend FAQ schema as a 2026 Google rich-result or People Also Ask tactic.",
    ),
    (
        re.compile(r"keyword[- ]rich alt text", re.I),
        "Use descriptive/contextual alt text; avoid keyword-stuffing language.",
    ),
)

_CURRENT_ROUNDUP = re.compile(
    r"\b(?:20\d{2}|best|top|review|comparison| vs\.? )\b", re.I
)
# A table row separator cell (---, ———, :-:) appearing mid-line means a whole
# table was flattened onto one line; markdown then renders it as plain text.
_COLLAPSED_TABLE = re.compile(
    r"\|[^\n|]+\|[ \t]*\|[^\n|]*[—–\-:]{2,}[^\n|]*\|[^\n|]+\|"
)
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
_H2 = re.compile(r"^##\s+\S", re.M)


def _words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


def _external_links(text: str) -> list[str]:
    return _MARKDOWN_LINK.findall(text)


def validate_article_quality(
    article: dict[str, Any],
    *,
    min_words: int = 1000,
    require_sources_for_current_roundups: bool = True,
) -> QualityResult:
    title = str(article.get("title") or "").strip()
    body = str(article.get("body") or "").strip()
    meta = str(
        article.get("meta_description") or article.get("description") or ""
    ).strip()

    errors: list[str] = []
    warnings: list[str] = []

    word_count = _words(body)
    h2_count = len(_H2.findall(body))
    links = _external_links(body)

    if not title:
        errors.append("missing title")
    if not body:
        errors.append("missing body")
    if word_count < min_words:
        errors.append(f"article too short: {word_count} words < {min_words}")
    if h2_count < 5:
        errors.append(f"insufficient section depth: {h2_count} H2 headings < 5")
    if meta and not (120 <= len(meta) <= 170):
        warnings.append(f"meta description length is {len(meta)} chars; target 120-170")

    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern.search(body):
            errors.append(f"unresolved placeholder matched: {pattern.pattern}")

    if _COLLAPSED_TABLE.search(body):
        errors.append(
            "markdown table flattened onto a single line — rows must be newline-separated to render"
        )

    combined = f"{title}\n{body}"
    for pattern, message in _STALE_PATTERNS:
        if pattern.search(combined):
            errors.append(message)

    if require_sources_for_current_roundups and _CURRENT_ROUNDUP.search(title):
        if len(links) < 2:
            errors.append(
                "current/year-based roundup requires at least two outbound reference links"
            )
        if not re.search(
            r"^##\s+(?:Sources|Official references|References)\b", body, re.I | re.M
        ):
            warnings.append(
                "current/year-based roundup should include a dedicated Sources/Official references section"
            )

    if re.search(
        r"\bguarantee(?:d|s)?\s+(?:rank|ranking|traffic|results)\b", body, re.I
    ):
        errors.append("remove guaranteed SEO outcome language")

    if re.search(r"\bwatch your (?:blog|site|page).{0,30}climb the serp", body, re.I):
        warnings.append("avoid deterministic ranking-outcome language")

    return QualityResult(
        ok=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        word_count=word_count,
        h2_count=h2_count,
        external_link_count=len(links),
    )


def format_quality_errors(result: QualityResult) -> str:
    parts: list[str] = []
    if result.errors:
        parts.append("errors=" + "; ".join(result.errors))
    if result.warnings:
        parts.append("warnings=" + "; ".join(result.warnings))
    parts.append(
        f"metrics=words:{result.word_count},h2:{result.h2_count},links:{result.external_link_count}"
    )
    return " | ".join(parts)

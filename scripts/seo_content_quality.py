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

# Technical claims verified wrong against vendor docs on 2026-10-19
# (developers.cloudflare.com/workers/platform/limits, /pricing; Durable Objects
# release notes; Vercel storage docs). Each entry exists because a published
# ProfitEngine article shipped the error. Update the date and the entry when a
# vendor changes the underlying fact.
_STALE_TECH_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"npm\s+(?:install|i)\s+(?:-g\s+)?@cloudflare/wrangler\b", re.I),
        "`@cloudflare/wrangler` is the retired Wrangler v1 package; use `npm create cloudflare@latest` or `npx wrangler`.",
    ),
    (
        re.compile(r"\bwrangler\s+(?:publish|generate)\b", re.I),
        "`wrangler publish` / `wrangler generate` are retired; use `wrangler deploy` and `npm create cloudflare@latest`.",
    ),
    (
        re.compile(
            r"(?:cloudflare|workers?).{0,200}free.{0,80}\b(?:50|100)\s?ms\b.{0,40}cpu",
            re.I | re.S,
        ),
        "Workers Free CPU limit is 10 ms per request (Paid: 30 s default, up to 5 min).",
    ),
    (
        re.compile(
            r"(?:workers?|cloudflare).{0,200}paid.{0,80}\b(?:30|50)\s?ms\b",
            re.I | re.S,
        ),
        "Workers Paid CPU limit is 30 seconds by default (up to 5 minutes), not milliseconds.",
    ),
    (
        re.compile(
            r"(?:workers?|cloudflare).{0,200}(?:keep(?:ing)?\s+(?:instances?\s+)?warm|paid plans?.{0,60}cold[- ]start)",
            re.I | re.S,
        ),
        "Workers run on V8 isolates; there is no paid keep-warm tier for cold starts.",
    ),
    (
        re.compile(r"\bVercel\s+KV\b", re.I),
        "Vercel KV is discontinued; Redis on Vercel is provisioned through Marketplace integrations (e.g. Upstash).",
    ),
    (
        re.compile(r"403\s+Forbidden.{0,60}(?:reading|read|access).{0,20}secret", re.I | re.S),
        "A missing Workers secret is `undefined` at runtime; it does not return 403.",
    ),
)

_CODE_FENCE = re.compile(r"^```", re.M)
_SOURCES_SECTION = re.compile(
    r"^##\s+(?:Sources|Official references|References)\b(?P<section>.*?)(?=^##\s|\Z)",
    re.I | re.M | re.S,
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

    for pattern, message in _STALE_TECH_PATTERNS:
        if pattern.search(combined):
            errors.append(message)

    # Tutorials that ship code teach readers to run it, so the claims behind the
    # commands and limits must be traceable to linked documentation.
    if len(_CODE_FENCE.findall(body)) >= 2:
        match = _SOURCES_SECTION.search(body)
        section_links = _external_links(match.group("section")) if match else []
        if len(section_links) < 2:
            errors.append(
                "technical tutorial with code requires a Sources section with at least two linked references"
            )

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


_SLUG_STOPWORDS = frozenset(
    "a an and at for from how in of on the to with your you guide 2025 2026 2027 free best".split()
)


def _slug_tokens(name: str) -> frozenset[str]:
    stem = re.sub(r"\.md$", "", name.lower())
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    stem = re.sub(r"\bset[- ]up\b", "setup", stem)
    return frozenset(t for t in re.split(r"[^a-z0-9]+", stem) if t and t not in _SLUG_STOPWORDS)


def find_duplicate_post(slug: str, existing_names: list[str], threshold: float = 0.6) -> str | None:
    """Return the existing post filename that covers the same topic, if any.

    Compares slug token sets (stopwords and years removed) by Jaccard
    similarity. The content repo held three near-identical Cloudflare Workers
    posts before this guard existed.
    """
    wanted = _slug_tokens(slug)
    if not wanted:
        return None
    best_name, best_score = None, 0.0
    for name in existing_names:
        tokens = _slug_tokens(name)
        if not tokens:
            continue
        score = len(wanted & tokens) / len(wanted | tokens)
        if score > best_score:
            best_name, best_score = name, score
    return best_name if best_score >= threshold else None

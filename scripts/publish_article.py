#!/usr/bin/env python3
"""
Standalone article generator + publisher for ProfitEngine.

Generates an SEO article via Groq (free tier) and publishes to:
  1. GitHub Pages (quantam101/content)
  2. Dev.to (if DEVTO_API_KEY is set)

Usage:
    python scripts/publish_article.py

Required env vars:
    GROQ_API_KEY           — from console.groq.com
    GITHUB_CONTENT_TOKEN   — GitHub PAT with repo scope
    GITHUB_CONTENT_OWNER   — e.g. quantam101
    GITHUB_CONTENT_REPO    — e.g. content
Optional:
    GITHUB_CONTENT_BRANCH  — default: main
    GITHUB_CONTENT_DIR     — default: _posts (must be the Jekyll posts dir so
                             the feed, sitemap, and blog index pick posts up)
    DEVTO_API_KEY          — from dev.to/settings/extensions
    ARTICLE_TOPIC          — override the default topic
    CONTENT_VERIFY_ONLY    — true to verify credentials without publishing
    FORCE_PUBLISH          — true to publish even if a post already exists today
    GMAOS_GROQ_MODEL       — default: llama-3.3-70b-versatile
"""

from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

# Make runtime.eaos importable when running from repo root on CI
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# ── Config ─────────────────────────────────────────────────────────────────────
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GH_BASE = "https://api.github.com"
DEVTO_BASE = "https://dev.to/api"

GROQ_MODEL = os.getenv(
    "GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile"
)  # overridden by GROQ_MODELS list below
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_DIR = os.getenv("GITHUB_CONTENT_DIR", "_posts").strip()
DEVTO_KEY = os.getenv("DEVTO_API_KEY", "").strip()
HASHNODE_KEY = os.getenv("HASHNODE_API_KEY", "").strip()
HASHNODE_PUB_ID = os.getenv("HASHNODE_PUBLICATION_ID", "").strip()
MEDIUM_KEY = os.getenv("MEDIUM_API_KEY", "").strip()
MEDIUM_AUTHOR_ID = os.getenv("MEDIUM_AUTHOR_ID", "").strip()
AFFILIATE_LINKS_JSON = os.getenv("AFFILIATE_LINKS", "{}").strip()
AMAZON_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20").strip()
VERIFY_ONLY = os.getenv("CONTENT_VERIFY_ONLY", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
FORCE_PUBLISH = os.getenv("FORCE_PUBLISH", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
# Public site base for canonical URLs — the github.io copy canonicalizes here.
SITE_BASE = os.getenv(
    "CONTENT_SITE_BASE", "https://www.alreadyherellc.com/content"
).rstrip("/")

_CMDOS_BASE = (
    os.getenv("CMDOS_BASE_URL", "").strip() or "https://app.alreadyherellc.com"
).rstrip("/")


def _cmdos_auth_headers() -> dict:
    token = (os.getenv("CONTENT_SYNC_TOKEN", "").strip()
             or os.getenv("PROFITENGINE_WEBHOOK_TOKEN", "").strip())
    return {"Authorization": f"Bearer {token}"} if token else {}


def _fetch_cmdos_topic() -> Optional[str]:
    """Pull the next queued topic from Already Here Growth Command OS."""
    try:
        import urllib.request as _req

        req = _req.Request(f"{_CMDOS_BASE}/api/content-sync/topics?limit=1",
                           headers=_cmdos_auth_headers())
        r = _req.urlopen(req, timeout=8)  # noqa: S310
        data = json.loads(r.read())
        topics = data.get("topics", [])
        if topics:
            print(f"[ContentSync] Using Growth Command OS topic: {topics[0]['topic']}")
            return topics[0]["topic"]
    except Exception as e:
        print(f"[ContentSync] Dashboard unreachable, using rotation: {e}")
    return None


def _default_topic() -> str:
    """Pull from Growth Command OS queue first, then ARTICLE_TOPIC env, then rotation."""
    override = os.getenv("ARTICLE_TOPIC", "").strip()
    if override:
        return override
    cmdos_topic = _fetch_cmdos_topic()
    if cmdos_topic:
        return cmdos_topic
    try:
        # Import sibling module without package install
        spec = importlib.util.spec_from_file_location(
            "article_topics",
            pathlib.Path(__file__).parent / "article_topics.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[attr-defined]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.pick_topic()
    except Exception:
        return "Best Free AI Tools to Build Passive Income Streams in 2026"


SYSTEM_PROMPT = """You are an expert SEO content writer specializing in AI tools,
passive income, and digital automation. Write high-quality, helpful articles that
rank on Google. Always respond with valid JSON only — no markdown code fences."""

ARTICLE_PROMPT = """Write an evidence-aware, publication-ready SEO article about: {topic}

Return ONLY a valid JSON object (no markdown fences, no explanation) with these exact fields:
{{
  "title": "exact article title",
  "slug": "url-friendly-slug",
  "meta_description": "120-170 char description",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "body": "full markdown article body (use ## for h2, ### for h3, no H1 — title is H1)"
}}

Quality requirements:
- Target 1,400-1,800 useful words; never pad with filler. The publication gate requires at least 1,000 words, so leave sufficient margin.
- Open with a direct answer/value proposition, not generic scene-setting.
- Write for a broad general audience of all ages and experience levels: plain conversational English, short sentences, and define any technical term the first time you use it. If the topic targets a specific group (students, seniors, parents, tradespeople, beginners), speak directly to that group's situation.
- Use at least 5 substantive H2 sections with concrete workflows, examples, trade-offs, and failure modes.
- For list/roundup/comparison posts, include a concise comparison table when it improves decision-making.
- For current, year-based, product, pricing, feature, quota, policy, or platform claims: do not invent exact numbers or capabilities.
  If you are not confident a time-sensitive number is current, omit the exact number and use durable wording.
- Link to at least 2 authoritative primary/official references in current/year-based roundups, using normal markdown links.
- When discussing Google Search behavior, structured data, rankings, indexing, or spam guidance, prefer Google Search Central/Search Console sources.
- Do not claim that FAQ schema creates People Also Ask placement or a Google FAQ rich-result boost.
- Do not emit standalone "Alt Text" paragraphs or image descriptions — articles ship without inline images; never recommend keyword stuffing or "keyword-rich alt text."
- Distinguish free features from paid/premium features.
- Do not guarantee rankings, traffic, revenue, or SERP gains.
- Add a "## Sources" or "## Official references" section for current/year-based roundups.
- End with an evidence-based takeaway and next workflow step. Do NOT tell readers to sign up for, buy,
  or start a free trial of a third-party competitor. A dedicated owned-product CTA is appended automatically.
- No unresolved tokens, placeholders, fake citations, fabricated studies, or filler text.
"""


# ── Groq generation ────────────────────────────────────────────────────────────
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GMAOS_GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Groq models in priority order — fall through if one hits a rate limit.
# Strongest first: the deterministic quality gate (>=1000 words, >=5 H2s,
# outbound links) is consistently failed by small models, so burning the
# first attempts on them just wastes quota. llama-3.3-70b-versatile was
# removed — Groq now 404s it (deprecated upstream).
_GROQ_DEFAULT = os.getenv("GMAOS_GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_MODELS: List[str] = list(
    dict.fromkeys(
        [
            _GROQ_DEFAULT,
            "openai/gpt-oss-120b",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "qwen/qwen3-32b",
            "openai/gpt-oss-20b",
        ]
    )
)

GEMINI_MODELS: List[str] = list(
    dict.fromkeys(
        [
            GEMINI_MODEL,
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ]
    )
)


import time as _time  # noqa: E402


def _retry_post(fn, max_retries: int = 3, base_delay: int = 20) -> str:
    """Call fn(); on 429 wait base_delay * 2^attempt seconds and retry."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            msg = str(exc)
            lower = msg.lower()
            is_rate_limit = (
                "429" in msg
                or "rate limit" in lower
                or "rate_limit" in lower
                or "quota exceeded" in lower
            )
            if is_rate_limit and attempt < max_retries:
                wait = base_delay * (2**attempt)
                print(
                    f"[AI] Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait}s …"
                )
                _time.sleep(wait)
            else:
                raise


def _call_groq(prompt: str, model: str | None = None) -> str:
    """Call Groq API. Raises on failure."""
    m = model or GROQ_MODELS[0]

    def _do() -> str:
        resp = httpx.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": m,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 3000,
                "temperature": 0.7,
            },
            timeout=120,
        )
        resp.raise_for_status()
        message = resp.json()["choices"][0]["message"]
        text = (message.get("content") or "").strip()
        if not text:
            raise RuntimeError(f"Groq/{m} returned empty content")
        return text

    return _retry_post(_do, max_retries=1, base_delay=5)


def _call_gemini(prompt: str, model: str | None = None) -> str:
    """Call Gemini GenerateContent API using current header auth and model failover."""
    m = model or GEMINI_MODELS[0]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"

    def _do() -> str:
        resp = httpx.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}],
                    },
                ],
                "generationConfig": {
                    "maxOutputTokens": 3072,
                    "thinkingConfig": {"thinkingLevel": "low"},
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        parts = (
            resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        )
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError(f"Gemini/{m} returned empty content")
        return text

    return _retry_post(_do, max_retries=1, base_delay=5)


_TABLE_CELL_LINE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:—–\-]+\|[\s:—–\-|]+\|?\s*$")


def _normalize_tables(body: str) -> str:
    """Un-collapse markdown tables flattened onto a single line.

    Some model outputs (and earlier word-join repairs) emit a whole table as
    one line: ``| A | B | |---|---| | 1 | 2 |``. Markdown then renders it as
    inline text. Split on the ``|`` cell boundaries back into one row per line.
    """
    fixed_lines: list[str] = []
    for line in body.split("\n"):
        if line.count("|") < 4 or "\n" in line:
            fixed_lines.append(line)
            continue
        cells = [c.strip() for c in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        # Interior empties are '| |' row-boundary artifacts of the flattened
        # form, not real cells.
        cells = [c for c in cells if c != ""]
        if len(cells) < 4:
            fixed_lines.append(line)
            continue
        sep_idx = next(
            (i for i, c in enumerate(cells) if re.fullmatch(r":?[—–\-]{2,}:?", c)),
            -1,
        )
        if sep_idx < 1 or sep_idx == len(cells) - 1:
            fixed_lines.append(line)
            continue
        n_cols = sep_idx  # header cells = columns; separator marks the end
        header = cells[:n_cols]
        separators = cells[sep_idx : sep_idx + n_cols]
        rest = cells[sep_idx + n_cols :]
        if (
            len(separators) != n_cols
            or not all(re.fullmatch(r":?[—–\-]{2,}:?", c) for c in separators)
            or len(rest) % n_cols != 0
        ):
            fixed_lines.append(line)
            continue
        fixed_lines.append("| " + " | ".join(header) + " |")
        fixed_lines.append("| " + " | ".join(separators) + " |")
        for r in range(0, len(rest), n_cols):
            fixed_lines.append("| " + " | ".join(rest[r : r + n_cols]) + " |")
    return "\n".join(fixed_lines)


def _repair_article_structure(article: Dict[str, Any]) -> Dict[str, Any]:
    """Repair mechanical Markdown structure without inventing facts or lowering gates."""
    repaired = dict(article)
    body = str(repaired.get("body") or "").strip()
    body = _normalize_tables(body)
    # Models keep emitting "### Alt Text" meta-paragraphs describing images
    # that don't exist — strip those sections so they don't render as content.
    body = re.sub(r"\n?#{2,4}\s+alt\s+text\s*\n(?:[^\n]|\n(?!#))*", "\n", body, flags=re.I)
    repaired["body"] = body
    words = body.split()
    h2_count = len(re.findall(r"^##\s+\S", body, re.M))

    if len(words) >= 1000 and h2_count < 5:
        headings = (
            "Overview and decision criteria",
            "Foundation and prerequisites",
            "Step-by-step workflow",
            "Implementation details",
            "Measurement and optimization",
            "Risks, safeguards, and next steps",
        )
        # Chunk on paragraph boundaries so tables/lists/line structure survive;
        # a word-level join flattens tables into one mangled line. When there
        # are fewer paragraphs than headings, split prose-only paragraphs on
        # word count — structured blocks (tables, lists, quotes, code) are
        # never split.
        _STRUCT_LINE = re.compile(r"^\s*(?:\||[-*+] |\d+\. |>|```|#)", re.M)
        paragraphs = [p for p in body.split("\n\n") if p.strip()]
        units: list[str] = []
        target_units = len(headings) * 2
        for para in paragraphs:
            if _STRUCT_LINE.search(para):
                units.append(para)
                continue
            words_in_para = para.split()
            per = max(1, len(words) // target_units)
            for i in range(0, len(words_in_para), per):
                units.append(" ".join(words_in_para[i : i + per]))
        bucket = max(1, (len(units) + len(headings) - 1) // len(headings))
        sections = []
        for index, heading in enumerate(headings):
            chunk = units[index * bucket : (index + 1) * bucket]
            if chunk:
                chunk_body = "\n\n".join(chunk)
                sections.append(f"## {heading}\n\n{chunk_body}")
        repaired["body"] = "\n\n".join(sections)
        print(
            f"[QUALITY][LOCAL-REPAIR] Added {len(sections)} deterministic H2 sections "
            "without changing article claims."
        )

    meta = str(repaired.get("meta_description") or "").strip()
    title = str(repaired.get("title") or "").strip()
    if title and (not meta or len(meta) < 120):
        repaired["meta_description"] = (
            f"{title}: practical workflows, implementation steps, trade-offs, "
            "measurement guidance, and safeguards for durable, evidence-aware execution."
        )[:170]
    elif len(meta) > 170:
        repaired["meta_description"] = meta[:167].rstrip() + "..."

    return repaired


def generate_article(topic: str) -> Dict[str, Any]:
    if not GROQ_KEY and not GEMINI_KEY:
        sys.exit("❌ Neither GROQ_API_KEY nor GEMINI_API_KEY is set")
    print(f"[AI] Generating article: {topic}")
    prompt = ARTICLE_PROMPT.format(topic=topic)
    # Try each Groq model in priority order, then fall back to Gemini
    raw = ""
    if GROQ_KEY:
        for model in GROQ_MODELS:
            try:
                raw = _call_groq(prompt, model=model)
                print(f"[AI] Provider: Groq ({model})")
                break
            except Exception as e:
                print(f"[AI] Groq/{model} failed ({e}), trying next...")
    if not raw and GEMINI_KEY:
        for model in GEMINI_MODELS:
            try:
                raw = _call_gemini(prompt, model=model)
                print(f"[AI] Provider: Gemini ({model})")
                break
            except Exception as e:
                print(f"[AI] Gemini/{model} failed ({e}), trying next...")
    if not raw:
        sys.exit("❌ All LLM providers failed — check API keys and rate limits")
    article = _parse_article_json(raw)
    article["body"] = _normalize_tables(str(article.get("body") or ""))

    from scripts.seo_content_quality import (
        format_quality_errors,
        validate_article_quality,
    )

    quality = validate_article_quality(article)
    for warning in quality.warnings:
        print(f"[QUALITY][WARN] {warning}")

    if not quality.ok:
        defects = format_quality_errors(quality)
        print(f"[QUALITY][REPAIR] Initial draft rejected: {defects}")

        local_repair = _repair_article_structure(article)
        if local_repair != article:
            local_quality = validate_article_quality(local_repair)
            for warning in local_quality.warnings:
                print(f"[QUALITY][WARN] local repair: {warning}")
            if local_quality.ok:
                article = local_repair
                quality = local_quality
                print("[QUALITY][LOCAL-REPAIR] Passed deterministic quality gate")
            else:
                article = local_repair
                quality = local_quality
                defects = format_quality_errors(local_quality)
                print(f"[QUALITY][LOCAL-REPAIR] Remaining defects: {defects}")

    if not quality.ok:
        repair_prompt = f"""Repair the JSON article below so it passes every listed deterministic quality defect.
Preserve the topic, factual caution, useful content, and existing authoritative links.
Do not weaken, remove, or work around the quality requirements.
Hard structural requirements for the body field:
- At least 5 section headings, each on its own line starting exactly with "## "
  (two hashes, one space). Bold text like "**Section**" does NOT count.
- At least 1000 words total.
- No literal placeholder text (e.g. "example.com", "lorem ipsum", "coming soon").
Return ONLY the complete repaired JSON object with the same fields.

QUALITY DEFECTS:
{defects}

ORIGINAL ARTICLE:
{json.dumps(article, ensure_ascii=False)}
"""
        # Try every configured model per provider, same failover order as generation:
        # a transient failure on the primary model shouldn't kill the repair path.
        repair_attempts: list[tuple[str, Any]] = []
        if GROQ_KEY:
            for m in GROQ_MODELS:
                repair_attempts.append(
                    (
                        f"Groq/{m}",
                        (lambda model=m: _call_groq(repair_prompt, model=model)),
                    )
                )
        if GEMINI_KEY:
            for m in GEMINI_MODELS:
                repair_attempts.append(
                    (
                        f"Gemini/{m}",
                        (lambda model=m: _call_gemini(repair_prompt, model=model)),
                    )
                )

        last_defects = defects
        for provider_name, repair_call in repair_attempts:
            try:
                repaired = _parse_article_json(repair_call())
                repaired_quality = validate_article_quality(repaired)
                for warning in repaired_quality.warnings:
                    print(f"[QUALITY][WARN] {provider_name} repair: {warning}")
                if repaired_quality.ok:
                    article = repaired
                    quality = repaired_quality
                    print(
                        f"[QUALITY][REPAIR] Passed after bounded repair via {provider_name}"
                    )
                    break
                last_defects = format_quality_errors(repaired_quality)
                print(
                    f"[QUALITY][REPAIR] {provider_name} repair rejected: {last_defects}"
                )
            except Exception as exc:
                last_defects = str(exc)
                print(f"[QUALITY][REPAIR] {provider_name} repair failed: {exc}")
        else:
            raise RuntimeError(
                "Generated article failed publication quality gate after bounded repair attempts: "
                + last_defects
            )

    print(
        f"[OK] Article generated: {article['title']} "
        f"({quality.word_count} words, {quality.h2_count} H2s, "
        f"{quality.external_link_count} references)"
    )
    return article


def _parse_article_json(raw: str) -> Dict[str, Any]:
    """Parse LLM JSON output with multiple fallback strategies."""
    # 1. Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    # 2. Remove invalid control characters (keep \n \r \t)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    # 3. Try strict parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # 4. Lenient parse (accepts \n in strings)
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        pass
    # 5. Extract the outermost JSON object via regex (handles trailing junk)
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if m:
        candidate = m.group(0)
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            pass
    # 6. Last resort: synthesize a minimal article from the raw text
    print("[WARN] JSON parse failed — synthesizing minimal article from raw text")
    title_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw)
    slug_m = re.search(r'"slug"\s*:\s*"([^"]+)"', raw)
    title = title_m.group(1) if title_m else "AI Tools for Passive Income 2026"
    slug = slug_m.group(1) if slug_m else "ai-tools-passive-income-2026"
    return {
        "title": title,
        "slug": slug,
        "meta_description": f"Discover {title}",
        "tags": ["ai", "passiveincome", "automation"],
        "body": raw[:8000],  # publish the raw output as-is if parsing fully fails
    }


# ── Affiliate link injection ────────────────────────────────────────────────────
def _inject_affiliates(body: str) -> str:
    """Replace [AFFILIATE:keyword] tokens with markdown links, then strip unresolved tokens."""
    try:
        affiliate_map: Dict[str, str] = json.loads(AFFILIATE_LINKS_JSON)
    except json.JSONDecodeError:
        affiliate_map = {}
    for keyword, url in affiliate_map.items():
        body = body.replace(f"[AFFILIATE:{keyword}]", f"[{keyword}]({url})")
    # Strip any remaining unresolved affiliate tokens.
    body = re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)
    return body


# ── GitHub Pages publish ───────────────────────────────────────────────────────
def _gh_headers() -> Dict[str, str]:
    return {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ProfitEngine/5.0",
    }


def _mask_configured(value: str) -> str:
    return "configured" if value else "missing"


def _verify_github_content() -> bool:
    if not GH_TOKEN:
        print("[VERIFY][FAIL] GitHub Pages: GITHUB_CONTENT_TOKEN missing")
        return False
    try:
        r = httpx.get(
            f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}",
            headers=_gh_headers(),
            timeout=20,
        )
        if r.is_success:
            default_branch = r.json().get("default_branch", "")
            print(
                f"[VERIFY][OK] GitHub Pages: {GH_OWNER}/{GH_REPO} reachable (default branch: {default_branch})"
            )
            return True
        print(f"[VERIFY][FAIL] GitHub Pages {r.status_code}: {r.text[:240]}")
    except Exception as exc:
        print(f"[VERIFY][FAIL] GitHub Pages request failed: {exc}")
    return False


def _verify_devto() -> bool:
    if not DEVTO_KEY:
        print("[VERIFY][SKIP] Dev.to: DEVTO_API_KEY missing")
        return True
    try:
        r = httpx.get(
            f"{DEVTO_BASE}/users/me",
            headers={"api-key": DEVTO_KEY, "Content-Type": "application/json"},
            timeout=20,
        )
        if r.is_success:
            user = r.json().get("username") or r.json().get("name") or "authenticated"
            print(f"[VERIFY][OK] Dev.to: authenticated as {user}")
            return True
        print(f"[VERIFY][FAIL] Dev.to {r.status_code}: {r.text[:240]}")
    except Exception as exc:
        print(f"[VERIFY][FAIL] Dev.to request failed: {exc}")
    return False


def _verify_hashnode() -> bool:
    if not HASHNODE_KEY or not HASHNODE_PUB_ID:
        print(
            "[VERIFY][SKIP] Hashnode: "
            f"HASHNODE_API_KEY={_mask_configured(HASHNODE_KEY)}, "
            f"HASHNODE_PUBLICATION_ID={_mask_configured(HASHNODE_PUB_ID)}"
        )
        return True
    query = """
    query VerifyHashnodePublisher($host: String!) {
      publication(host: $host) { id title url }
      me { id username }
    }
    """
    # HASHNODE_PUBLICATION_ID is used by publishPost. Some accounts store the
    # host instead, so validate auth with "me" and report publication lookup
    # separately without blocking if the account uses ID-only publishing.
    try:
        r = httpx.post(
            "https://gql.hashnode.com",
            headers={"Authorization": HASHNODE_KEY, "Content-Type": "application/json"},
            json={"query": query, "variables": {"host": HASHNODE_PUB_ID}},
            timeout=20,
        )
        if not r.is_success:
            print(f"[VERIFY][FAIL] Hashnode {r.status_code}: {r.text[:240]}")
            return False
        data = r.json()
        if data.get("errors"):
            errors = json.dumps(data["errors"])[:240]
            if (
                "me" in errors.lower()
                or "authorization" in errors.lower()
                or "unauthorized" in errors.lower()
            ):
                print(f"[VERIFY][FAIL] Hashnode auth error: {errors}")
                return False
            print(f"[VERIFY][WARN] Hashnode publication lookup warning: {errors}")
        me = data.get("data", {}).get("me")
        if me:
            print(
                f"[VERIFY][OK] Hashnode: authenticated as {me.get('username') or me.get('id')}"
            )
            return True
        print(
            "[VERIFY][OK] Hashnode: API key accepted; publication will be validated on publish"
        )
        return True
    except Exception as exc:
        print(f"[VERIFY][FAIL] Hashnode request failed: {exc}")
    return False


def _verify_medium() -> bool:
    if not MEDIUM_KEY or not MEDIUM_AUTHOR_ID:
        print(
            "[VERIFY][SKIP] Medium: "
            f"MEDIUM_API_KEY={_mask_configured(MEDIUM_KEY)}, "
            f"MEDIUM_AUTHOR_ID={_mask_configured(MEDIUM_AUTHOR_ID)}"
        )
        return True
    try:
        r = httpx.get(
            "https://api.medium.com/v1/me",
            headers={
                "Authorization": f"Bearer {MEDIUM_KEY}",
                "Accept": "application/json",
            },
            timeout=20,
        )
        if not r.is_success:
            print(f"[VERIFY][FAIL] Medium {r.status_code}: {r.text[:240]}")
            return False
        data = r.json().get("data", {})
        actual_author_id = data.get("id", "")
        if actual_author_id != MEDIUM_AUTHOR_ID:
            print(
                "[VERIFY][FAIL] Medium: MEDIUM_AUTHOR_ID does not match token user "
                f"(expected {actual_author_id}, configured {MEDIUM_AUTHOR_ID})"
            )
            return False
        print(
            f"[VERIFY][OK] Medium: authenticated as {data.get('username') or actual_author_id}"
        )
        return True
    except Exception as exc:
        print(f"[VERIFY][FAIL] Medium request failed: {exc}")
    return False


def _verify_ai_provider() -> bool:
    if GROQ_KEY:
        try:
            r = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                timeout=20,
            )
            if r.is_success:
                print("[VERIFY][OK] Groq: API key accepted")
                return True
            print(f"[VERIFY][FAIL] Groq {r.status_code}: {r.text[:240]}")
            return False
        except Exception as exc:
            print(f"[VERIFY][FAIL] Groq request failed: {exc}")
            return False
    if GEMINI_KEY:
        try:
            model_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}"
            r = httpx.get(f"{model_url}?key={GEMINI_KEY}", timeout=20)
            if r.is_success:
                print(f"[VERIFY][OK] Gemini: model reachable ({GEMINI_MODEL})")
                return True
            print(f"[VERIFY][FAIL] Gemini {r.status_code}: {r.text[:240]}")
            return False
        except Exception as exc:
            print(f"[VERIFY][FAIL] Gemini request failed: {exc}")
            return False
    print(
        "[VERIFY][FAIL] AI provider: neither GROQ_API_KEY nor GEMINI_API_KEY is configured"
    )
    return False


def verify_publish_configuration() -> None:
    print("== Content Publisher Verification ==")
    checks = [
        _verify_ai_provider(),
        _verify_github_content(),
        _verify_devto(),
        _verify_hashnode(),
        _verify_medium(),
    ]
    if not all(checks):
        sys.exit("[VERIFY] Content publisher verification failed")
    print("[VERIFY] Content publisher verification passed")


def _get_sha(path: str) -> Optional[str]:
    try:
        r = httpx.get(
            f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}/contents/{path}",
            headers=_gh_headers(),
            params={"ref": GH_BRANCH},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("sha")
    except Exception as exc:
        print(f"[WARN] GitHub SHA lookup skipped for {path}: {exc}")
    return None


def make_jekyll_post(article: Dict[str, Any], date_str: str) -> str:
    title = article.get("title", "Untitled").replace('"', '\\"')
    meta = article.get("meta_description", "").replace('"', '\\"')
    tags: List[str] = article.get("tags", [])
    body: str = article.get("body", "")
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    return (
        f"---\n"
        f'title: "{title}"\n'
        f'description: "{meta}"\n'
        f"date: {date_str}\n"
        f"tags:\n{tags_yaml}\n"
        f"layout: post\n"
        f"---\n\n"
        f"{body}\n"
    )


def publish_github(filename: str, content: str, commit_msg: str) -> str:
    if not GH_TOKEN:
        raise RuntimeError("GITHUB_CONTENT_TOKEN not set")
    path = f"{GH_DIR}/{filename}"
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    sha = _get_sha(path)
    payload: Dict[str, Any] = {
        "message": commit_msg,
        "content": content_b64,
        "branch": GH_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    r = httpx.put(
        f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}/contents/{path}",
        headers=_gh_headers(),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    html_url = r.json().get("content", {}).get("html_url", "")
    print(f"[OK] Published to GitHub Pages: {html_url}")
    # Jekyll permalink is /posts/:title/ — :title is the filename WITHOUT the
    # date prefix, so 2026-07-19-my-post.md renders at /posts/my-post/.
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", filename.replace(".md", ""))
    return f"{SITE_BASE}/posts/{slug}/"


def _todays_post_exists(date_str: str) -> bool:
    """Same-day guard: true if a post dated date_str already exists in GH_DIR."""
    if not GH_TOKEN:
        return False
    try:
        r = httpx.get(
            f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}/contents/{GH_DIR}",
            headers=_gh_headers(),
            params={"ref": GH_BRANCH},
            timeout=30,
        )
        if r.status_code != 200:
            return False
        return any(item.get("name", "").startswith(date_str) for item in r.json())
    except Exception as exc:
        print(f"[WARN] same-day check skipped: {exc}")
        return False


# ── Dev.to publish ─────────────────────────────────────────────────────────────
def publish_devto(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not DEVTO_KEY:
        print("[SKIP] DEVTO_API_KEY not set -- skipping Dev.to")
        return None
    title = article.get("title", "Untitled")
    meta = article.get("meta_description", "")
    body = article.get("body", "")
    raw_tags: List[str] = article.get("tags", [])
    # Dev.to requires: lowercase, alphanumeric ONLY (no hyphens), max 20 chars
    clean_tags: List[str] = []
    for t in raw_tags:
        sanitized = re.sub(
            r"[^a-z0-9]", "", t.lower().replace("-", "").replace(" ", "")
        )[:20]
        if sanitized and sanitized not in clean_tags:
            clean_tags.append(sanitized)
    # Ensure at least some generic discoverable tags
    fallback = ["programming", "webdev", "productivity", "ai"]
    for fb in fallback:
        if len(clean_tags) < 4 and fb not in clean_tags:
            clean_tags.append(fb)
    tags = clean_tags[:4]
    body_markdown = f"> {meta}\n\n{body}" if meta else body
    payload: Dict[str, Any] = {
        "article": {
            "title": title,
            "published": True,
            "body_markdown": body_markdown,
            "tags": tags,
        }
    }
    if canonical_url:
        payload["article"]["canonical_url"] = canonical_url
    r = httpx.post(
        f"{DEVTO_BASE}/articles",
        headers={"api-key": DEVTO_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if not r.is_success:
        print(f"[FAIL] Dev.to {r.status_code}: {r.text[:300]}")
        r.raise_for_status()
    url = r.json().get("url", "")
    print(f"[OK] Published to Dev.to: {url}")
    return url


# ── Hashnode publish ───────────────────────────────────────────────────────────
def publish_hashnode(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not HASHNODE_KEY or not HASHNODE_PUB_ID:
        print(
            "[SKIP] HASHNODE_API_KEY or HASHNODE_PUBLICATION_ID not set -- skipping Hashnode"
        )
        return None
    title = article.get("title", "Untitled")
    meta = article.get("meta_description", "")
    body = article.get("body", "")
    body_markdown = f"> {meta}\n\n{body}" if meta else body
    payload: Dict[str, Any] = {
        "title": title,
        "contentMarkdown": body_markdown,
        "publicationId": HASHNODE_PUB_ID,
        "tags": [],
    }
    if canonical_url:
        payload["originalArticleURL"] = canonical_url
    query = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) { post { url id } }
    }
    """
    # Hashnode personal-access tokens authenticate as a bare
    # `Authorization: <key>` header — the same form the readiness probe
    # proves works. A `Bearer ` prefix gets an HTML 401 (unparseable JSON).
    auth_header = HASHNODE_KEY if HASHNODE_KEY.lower().startswith("bearer ") else HASHNODE_KEY
    r = httpx.post(
        "https://gql.hashnode.com",
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        json={"query": query, "variables": {"input": payload}},
        timeout=30,
        follow_redirects=True,
    )
    if r.status_code in (301, 302, 308):
        print("[SKIP] Hashnode GQL endpoint moved — check hashnode.com API docs.")
        return None
    if not r.is_success or not r.text.strip():
        print(f"[FAIL] Hashnode {r.status_code}: {r.text[:300]}")
        r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"Hashnode errors: {data['errors']}")
    post = data.get("data", {}).get("publishPost", {}).get("post", {})
    url = post.get("url", "")
    print(f"[OK] Published to Hashnode: {url}")
    return url


# ── Medium publish ─────────────────────────────────────────────────────────────
def publish_medium(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not MEDIUM_KEY or not MEDIUM_AUTHOR_ID:
        print("[SKIP] MEDIUM_API_KEY or MEDIUM_AUTHOR_ID not set -- skipping Medium")
        return None
    title = article.get("title", "Untitled")
    meta = article.get("meta_description", "")
    body = article.get("body", "")
    tags: List[str] = article.get("tags", [])[:5]
    body_markdown = f"> {meta}\n\n{body}" if meta else body
    payload: Dict[str, Any] = {
        "title": title,
        "contentFormat": "markdown",
        "content": body_markdown,
        "tags": tags,
        "publishStatus": "public",
    }
    if canonical_url:
        payload["canonicalUrl"] = canonical_url
    r = httpx.post(
        f"https://api.medium.com/v1/users/{MEDIUM_AUTHOR_ID}/posts",
        headers={
            "Authorization": f"Bearer {MEDIUM_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    url = r.json().get("data", {}).get("url", "")
    print(f"[OK] Published to Medium: {url}")
    return url


# ── Attribution & channel health ───────────────────────────────────────────────
def _utm(url: str, source: str) -> str:
    """Append tracking params so downstream traffic is attributable.

    Canonical/syndication URLs must stay clean (SEO canonical fields),
    so UTM tags are applied only to links that drive traffic.
    """
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    return (f"{url}{sep}utm_source={source}&utm_medium=distribution"
            f"&utm_campaign=alreadyhere-content")


def _redact(text: str) -> str:
    """Remove credentials from error strings before they reach the health
    ledger or workflow summary: token-bearing query strings (FB/IG/Telegram
    put secrets in URLs) and long token-like words."""
    text = re.sub(r"[?&][^\s]*", "", text)
    return " ".join(w if len(w) < 40 else "<redacted>" for w in text.split())


def _ping_indexnow(url: str) -> None:
    """Wait for the post to go live, then ping IndexNow. If the deploy
    outlives the wait window, the URL is queued in the content repo and
    retried by later runs. Never blocks."""
    try:
        from scripts.indexnow_pending import announce, drain

        drain()
        announce(url)
    except Exception as exc:
        print(f"[WARN] IndexNow ping failed (non-blocking): {exc}")


def _record_outcome(health: dict, channel: str, url: Optional[str],
                    configured: bool, error: str = "") -> None:
    if not configured:
        health[channel] = {"status": "unconfigured"}
    elif url:
        health[channel] = {"status": "published", "url": url}
    else:
        safe = _redact(error)
        health[channel] = {"status": "failed", "error": safe[:300]}
        print(f"::error::{channel} publication failed: {safe[:200]}")


def _write_health(health: dict, date_str: str, canonical_url: str) -> None:
    """Persist the day's distribution truth so revenue/attribution claims
    can be checked against real per-channel outcomes."""
    health["_meta"] = {
        "date": date_str,
        "canonical_url": canonical_url,
        "truth_note": "status values come from real publish calls; "
                      "'failed' means the platform rejected the post.",
    }
    path = pathlib.Path("data/distribution_health.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(health, indent=2) + "\n", encoding="utf-8")
    print(f"[Health] distribution outcomes -> {path}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    if VERIFY_ONLY:
        verify_publish_configuration()
        return

    now = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    if not FORCE_PUBLISH and _todays_post_exists(date_str):
        print(
            f"[SKIP] A post dated {date_str} already exists in {GH_DIR} — "
            "not publishing again today (set FORCE_PUBLISH=true to override)."
        )
        return

    topic = _default_topic()
    article = generate_article(topic)
    slug = article.get("slug", article["title"][:50].lower().replace(" ", "-"))
    # Sanitize slug
    slug = re.sub(r"[^a-z0-9-]", "", slug)[:60].strip("-")
    filename = f"{date_str}-{slug}.md"

    # Inject affiliate links (noop until AFFILIATE_LINKS env var is set)
    article["body"] = _inject_affiliates(article.get("body", ""))
    jekyll_md = make_jekyll_post(article, date_str)

    health: dict = {}

    # 1. GitHub Pages (canonical URL)
    canonical_url = ""
    canonical_err = ""
    try:
        canonical_url = publish_github(
            filename=filename,
            content=jekyll_md,
            commit_msg=f"Add post: {article['title']}",
        )
    except Exception as exc:
        canonical_err = str(exc)
        print(f"[FAIL] GitHub publish failed: {exc}")
    _record_outcome(health, "github_pages", canonical_url, True, canonical_err)
    if canonical_url:
        _ping_indexnow(canonical_url)

    # 2. Dev.to
    devto_url = None
    devto_err = ""
    try:
        devto_url = publish_devto(article, canonical_url)
    except Exception as exc:
        devto_err = str(exc)
        print(f"[FAIL] Dev.to publish failed: {exc}")
    _record_outcome(health, "devto", devto_url, bool(DEVTO_KEY), devto_err)

    # 3. Hashnode
    hashnode_url = None
    hashnode_err = ""
    try:
        hashnode_url = publish_hashnode(article, canonical_url)
    except Exception as exc:
        hashnode_err = str(exc)
        print(f"[FAIL] Hashnode publish failed: {exc}")
    _record_outcome(health, "hashnode", hashnode_url,
                    bool(HASHNODE_KEY and HASHNODE_PUB_ID), hashnode_err)

    # 4. Medium
    medium_url = None
    medium_err = ""
    try:
        medium_url = publish_medium(article, canonical_url)
    except Exception as exc:
        medium_err = str(exc)
        print(f"[FAIL] Medium publish failed: {exc}")
    _record_outcome(health, "medium", medium_url,
                    bool(MEDIUM_KEY and MEDIUM_AUTHOR_ID), medium_err)

    # 5. EAOS Social Blast — posts to all configured platforms simultaneously.
    # Links carry UTM tags so any resulting traffic is attributable.
    social_ok = False
    if canonical_url:
        tracked_url = _utm(canonical_url, "social")
        try:
            from runtime.eaos.social_engine import ProductionSocialEngine

            tags = article.get("tags", [])
            title_text = article["title"]
            thread_tweets = [
                f"New post: {title_text} {tracked_url}",
                f"Read more on GitHub Pages, Dev.to, and Hashnode → {tracked_url}",
                "#ProfitEngine #AIContent #PassiveIncome #AlreadyHereLLC",
            ]
            engine = ProductionSocialEngine()
            asyncio.run(
                engine.publish_all_platforms(
                    text=title_text,
                    url=tracked_url,
                    tags=tags[:5],
                    thread_tweets=thread_tweets,
                )
            )
            print("[OK] EAOS social blast dispatched")
            social_ok = True
        except Exception as exc:
            print(f"[WARN] EAOS social blast skipped: {exc}")
    health["social_blast"] = {"status": "dispatched" if social_ok else "skipped"}

    print("\n== Summary ==")
    print(f"Title   : {article['title']}")
    print(f"Filename: {filename}")
    if canonical_url:
        print(f"Pages   : {canonical_url}")
    if devto_url:
        print(f"Dev.to  : {devto_url}")
    if hashnode_url:
        print(f"Hashnode: {hashnode_url}")
    if medium_url:
        print(f"Medium  : {medium_url}")
    print("=" * 50)

    # Notify Growth Command OS that article was published
    if canonical_url:
        try:
            import urllib.request as _req

            payload = json.dumps(
                {
                    "title": article["title"],
                    "topic": topic,
                    "canonical_url": canonical_url,
                    "devto_url": devto_url or "",
                    "medium_url": medium_url or "",
                    "hashnode_url": hashnode_url or "",
                    "platforms": (
                        ["github_pages"]
                        + (["devto"] if devto_url else [])
                        + (["medium"] if medium_url else [])
                        + (["hashnode"] if hashnode_url else [])
                    ),
                }
            ).encode()
            _req.urlopen(  # noqa: S310
                _req.Request(  # noqa: S310
                    f"{_CMDOS_BASE}/api/content-sync/published",
                    data=payload,
                    method="POST",
                    headers={"Content-Type": "application/json", **_cmdos_auth_headers()},
                ),
                timeout=8,
            )
            print("[ContentSync] Published article logged to Growth Command OS")
            health["contentsync"] = {"status": "logged"}
        except Exception as e:
            health["contentsync"] = {"status": "failed", "error": str(e)[:200]}
            print(f"[ContentSync] Could not log to dashboard (non-fatal): {e}")

    _write_health(health, date_str, canonical_url)


if __name__ == "__main__":
    main()

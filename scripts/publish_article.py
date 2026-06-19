#!/usr/bin/env python3
"""
Standalone article generator + publisher for ProfitEngine.

Generates an SEO article via Groq (primary, free credits), then HuggingFace, then Gemini and publishes to:
  1. GitHub Pages (quantam101/content) — always published
  2. Dev.to (if DEVTO_API_KEY is set)
  3. Hashnode (if HASHNODE_API_KEY and HASHNODE_PUBLICATION_ID set; paid-only since 2026-05-13)
  4. Medium (if MEDIUM_API_KEY and MEDIUM_AUTHOR_ID set)
  5. Social platforms via EAOS engine (if canonical_url exists)

Usage:
    python scripts/publish_article.py
    CONTENT_VERIFY_ONLY=true python scripts/publish_article.py  # verify credentials only

Required env vars:
    GROQ_API_KEY           — from console.groq.com
    GITHUB_CONTENT_TOKEN   — GitHub PAT with repo scope
    GITHUB_CONTENT_OWNER   — e.g. quantam101
    GITHUB_CONTENT_REPO    — e.g. content
Optional:
    GITHUB_CONTENT_BRANCH  — default: main
    GITHUB_CONTENT_DIR     — default: posts
    DEVTO_API_KEY          — from dev.to/settings/extensions
    HASHNODE_API_KEY       — from hashnode.com/settings/developer (paid-only)
    HASHNODE_PUBLICATION_ID — publication ID or host slug
    MEDIUM_API_KEY         — from medium.com/@{username}/settings
    MEDIUM_AUTHOR_ID       — from Medium API /me endpoint
    ARTICLE_TOPIC          — override the default topic
    CONTENT_VERIFY_ONLY    — true to verify credentials without publishing
    GMAOS_GROQ_MODEL       — default: llama-3.3-70b-versatile
    PAID_ADAPTERS_ENABLED  — set to true to enable Hashnode (requires paid Pro plan)
    OPENAI_API_KEY         — from platform.openai.com/api-keys
    OPENROUTER_API_KEY     — from openrouter.ai/keys
    DEEPSEEK_API_KEY       — from platform.deepseek.com/api/keys
    ANTHROPIC_API_KEY      — from console.anthropic.com/api/keys
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
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

# Make runtime.eaos importable when running from repo root on CI
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# ── Config ─────────────────────────────────────────────────────────────────────
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GH_BASE = "https://api.github.com"
DEVTO_BASE = "https://dev.to/api"
HF_INFERENCE_BASE = "https://api-inference.huggingface.co/models"

GROQ_MODEL = os.getenv("GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile")  # overridden by GROQ_MODELS list below
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# HuggingFace models with OpenAI-compatible chat endpoint (free serverless)
HF_MODELS: List[str] = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3-mini-4k-instruct",
]
GH_TOKEN = os.getenv("CONTENT_REPO_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_DIR = os.getenv("GITHUB_CONTENT_DIR", "posts").strip()
DEVTO_KEY = os.getenv("DEVTO_API_KEY", "").strip()
HASHNODE_KEY = os.getenv("HASHNODE_API_KEY", "").strip()
HASHNODE_PUB_ID = os.getenv("HASHNODE_PUBLICATION_ID", "").strip()
MEDIUM_KEY = os.getenv("MEDIUM_API_KEY", "").strip()
MEDIUM_AUTHOR_ID = os.getenv("MEDIUM_AUTHOR_ID", "").strip()
AFFILIATE_LINKS_JSON = os.getenv("AFFILIATE_LINKS", "{}").strip()
AMAZON_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20").strip()
VERIFY_ONLY = os.getenv("CONTENT_VERIFY_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}

_CMDOS_BASE = os.getenv("CMDOS_BASE_URL", "https://app.alreadyherellc.com").rstrip("/")


def _fetch_cmdos_topic() -> Optional[str]:
    """Pull the next queued topic from Already Here Growth Command OS."""
    try:
        import urllib.request as _req
        r = _req.urlopen(f"{_CMDOS_BASE}/api/content-sync/topics?limit=1", timeout=8)  # noqa: S310
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

ARTICLE_PROMPT = """Write a comprehensive SEO article about: {topic}

Return ONLY a valid JSON object (no markdown, no explanation) with these exact fields:
{{
  "title": "exact article title",
  "slug": "url-friendly-slug",
  "meta_description": "150-160 char description",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "body": "full markdown article body (use ## for h2, ### for h3, no H1 — title is H1)"
}}

The article should be 800-1200 words, include:
- A brief intro explaining the value
- 5-7 sections with practical examples
- A conclusion with a clear CTA
- Natural keyword placement for SEO
- No unresolved tokens or filler text; publish real, useful content"""


# ── LLM Providers (cascading fallback: Groq → HF → Gemini → OpenAI → OpenRouter → DeepSeek → Anthropic)
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GMAOS_GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# Groq models in priority order — fall through if one hits a rate limit.
# llama-3.1-8b-instant is tried first: higher daily token allowance on free tier.
# llama-3.3-70b is second: better quality but tighter daily token quota.
_GROQ_DEFAULT = os.getenv("GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MODELS: List[str] = list(dict.fromkeys([
    _GROQ_DEFAULT,                    # env-configured (default: 70b) — best quality for long articles
    "qwen-qwq-32b",                   # reasoning model — excellent structured JSON, strong SEO content
    "llama-3.1-8b-instant",          # high quota, fast, good JSON fidelity
    "gemma2-9b-it",                   # alternative free model
]))


import time as _time  # noqa: E402

def _retry_post(fn, max_retries: int = 3, base_delay: int = 20) -> str:
    """Call fn(); on 429 wait base_delay * 2^attempt seconds and retry."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            msg = str(exc)
            is_rate_limit = "429" in msg or "rate" in msg.lower() or "quota" in msg.lower()
            if is_rate_limit and attempt < max_retries:
                wait = base_delay * (2 ** attempt)
                print(f"[AI] Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s …")
                _time.sleep(wait)
            else:
                raise


def _call_groq(prompt: str, model: str | None = None) -> str:
    """Call Groq API. Raises on failure."""
    m = model or GROQ_MODELS[0]
    def _do() -> str:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
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
        return resp.json()["choices"][0]["message"]["content"].strip()
    return _retry_post(_do, max_retries=2, base_delay=30)


def _call_gemini(prompt: str) -> str:
    """Call Gemini Flash API. Raises on failure."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    def _do() -> str:
        resp = httpx.post(
            f"{url}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]},
                ],
                "generationConfig": {"maxOutputTokens": 3072, "temperature": 0.7},
            },
            timeout=120,
        )
        resp.raise_for_status()
        parts = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()
    return _retry_post(_do, max_retries=2, base_delay=30)


def _call_hf_inference(prompt: str, model: str | None = None) -> str:
    """Call HuggingFace Serverless Inference API (free tier). Raises on failure."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not set")
    m = model or HF_MODELS[0]
    url = f"{HF_INFERENCE_BASE}/{m}/v1/chat/completions"

    def _do() -> str:
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
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
        return resp.json()["choices"][0]["message"]["content"].strip()
    return _retry_post(_do, max_retries=2, base_delay=20)


def _call_openai(prompt: str) -> str:
    """Call OpenAI API. Raises on failure."""
    if not OPENAI_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    def _do() -> str:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
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
        return resp.json()["choices"][0]["message"]["content"].strip()
    return _retry_post(_do, max_retries=2, base_delay=30)


def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter API. Raises on failure."""
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")
    def _do() -> str:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENROUTER_MODEL,
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
        return resp.json()["choices"][0]["message"]["content"].strip()
    return _retry_post(_do, max_retries=2, base_delay=30)


def _call_deepseek(prompt: str) -> str:
    """Call DeepSeek API. Raises on failure."""
    if not DEEPSEEK_KEY:
        raise ValueError("DEEPSEEK_API_KEY not set")
    def _do() -> str:
        resp = httpx.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
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
        return resp.json()["choices"][0]["message"]["content"].strip()
    return _retry_post(_do, max_retries=2, base_delay=30)


def _call_anthropic(prompt: str) -> str:
    """Call Anthropic (Claude) API. Raises on failure."""
    if not ANTHROPIC_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")
    def _do() -> str:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Authorization": f"Bearer {ANTHROPIC_KEY}", "x-api-key": ANTHROPIC_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 3000,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    return _retry_post(_do, max_retries=2, base_delay=30)


def generate_article(topic: str) -> Dict[str, Any]:
    if not any([GROQ_KEY, HF_TOKEN, GEMINI_KEY, OPENAI_KEY, OPENROUTER_KEY, DEEPSEEK_KEY, ANTHROPIC_KEY]):
        sys.exit("[ERROR] No LLM provider configured - set at least one of: GROQ_API_KEY, HF_TOKEN, GEMINI_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY")
    print(f"[AI] Generating article: {topic}")
    prompt = ARTICLE_PROMPT.format(topic=topic)
    affiliate_keywords = list(_affiliate_map().keys())
    if affiliate_keywords:
        prompt += (
            "\n\nWhere genuinely helpful to the reader, naturally mention these "
            "products/services using these exact phrases (do not force them in, "
            "and do not turn the article into an advertisement): "
            + ", ".join(affiliate_keywords)
        )
    # Cascading fallback: Groq → HF → Gemini → OpenAI → OpenRouter → DeepSeek → Anthropic
    raw = ""

    # 1. Try Groq first (free credits), then HuggingFace, then Gemini
    if GROQ_KEY:
        for model in GROQ_MODELS:
            try:
                raw = _call_groq(prompt, model=model)
                print(f"[AI] Provider: Groq ({model})")
                break
            except Exception as e:
                print(f"[AI] Groq/{model} failed ({e}), trying next...")

    if not raw and HF_TOKEN:
        for hf_model in HF_MODELS:
            try:
                raw = _call_hf_inference(prompt, model=hf_model)
                print(f"[AI] Provider: HuggingFace ({hf_model})")
                break
            except Exception as e:
                print(f"[AI] HF/{hf_model} failed ({e}), trying next...")

    if not raw and GEMINI_KEY:
        try:
            raw = _call_gemini(prompt)
            print(f"[AI] Provider: Gemini ({GEMINI_MODEL})")
        except Exception as e:
            print(f"[AI] Gemini failed ({e}), trying next...")

    # 2. Try OpenAI
    if not raw and OPENAI_KEY:
        try:
            raw = _call_openai(prompt)
            print(f"[AI] Provider: OpenAI ({OPENAI_MODEL})")
        except Exception as e:
            print(f"[AI] OpenAI failed ({e}), trying next...")

    # 3. Try OpenRouter
    if not raw and OPENROUTER_KEY:
        try:
            raw = _call_openrouter(prompt)
            print(f"[AI] Provider: OpenRouter ({OPENROUTER_MODEL})")
        except Exception as e:
            print(f"[AI] OpenRouter failed ({e}), trying next...")

    # 4. Try DeepSeek
    if not raw and DEEPSEEK_KEY:
        try:
            raw = _call_deepseek(prompt)
            print(f"[AI] Provider: DeepSeek ({DEEPSEEK_MODEL})")
        except Exception as e:
            print(f"[AI] DeepSeek failed ({e}), trying next...")

    # 5. Try Anthropic (Claude) — last fallback
    if not raw and ANTHROPIC_KEY:
        try:
            raw = _call_anthropic(prompt)
            print(f"[AI] Provider: Anthropic ({ANTHROPIC_MODEL})")
        except Exception as e:
            print(f"[AI] Anthropic failed ({e})")

    if not raw:
        sys.exit("❌ All LLM providers failed — check API keys and rate limits")
    article = _parse_article_json(raw)
    print(f"[OK] Article generated: {article['title']}")
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
    slug_m  = re.search(r'"slug"\s*:\s*"([^"]+)"', raw)
    title   = title_m.group(1) if title_m else "AI Tools for Passive Income 2026"
    slug    = slug_m.group(1) if slug_m else "ai-tools-passive-income-2026"
    return {
        "title": title,
        "slug": slug,
        "meta_description": f"Discover {title}",
        "tags": ["ai", "passiveincome", "automation"],
        "body": raw[:8000],  # publish the raw output as-is if parsing fully fails
    }


# ── Affiliate link injection ────────────────────────────────────────────────────
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20")


def _affiliate_map() -> Dict[str, str]:
    try:
        parsed = json.loads(AFFILIATE_LINKS_JSON)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _auto_link_keywords(body: str, affiliate_map: Dict[str, str]) -> str:
    """Link the first plain-text occurrence of each affiliate keyword.

    Token replacement alone never fired in production: generated bodies do
    not contain [AFFILIATE:...] tokens, so configured links never reached
    readers. Skips headings, code fences, and text already inside links.
    """
    lines = body.split("\n")
    in_code = False
    linked: set = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or stripped.startswith("#"):
            continue
        for keyword, url in affiliate_map.items():
            if keyword in linked:
                continue
            if url in line:
                linked.add(keyword)
                continue
            m = re.search(re.escape(keyword), line, re.IGNORECASE)
            if not m:
                continue
            prefix = line[: m.start()]
            if prefix.count("[") > prefix.count("]"):
                continue  # already inside a markdown link
            line = f"{prefix}[{m.group(0)}]({url}){line[m.end():]}"
            lines[i] = line
            linked.add(keyword)
    return "\n".join(lines)


def _recommended_tools_section(body: str, affiliate_map: Dict[str, str]) -> str:
    """A short link box for keywords the article actually mentions — never
    a dump of every configured link."""
    matched = [
        (kw, url) for kw, url in affiliate_map.items()
        if re.search(re.escape(kw), body, re.IGNORECASE)
    ]
    if not matched:
        return ""
    items = "\n".join(f"- [{kw}]({url})" for kw, url in matched)
    return f"\n\n## Recommended Tools\n\n{items}\n"


def _tag_amazon_links(body: str) -> str:
    """Append the partner tag to untagged amazon.com links."""
    if not AMAZON_PARTNER_TAG:
        return body

    def _add_tag(m: "re.Match[str]") -> str:
        url = m.group(0)
        if "tag=" in url:
            return url
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}tag={AMAZON_PARTNER_TAG}"

    return re.sub(r"https?://(?:www\.)?amazon\.com/[^\s\)\]\"'<>]+", _add_tag, body)


def _inject_affiliates(body: str) -> str:
    """Full monetization pass: tokens → keyword auto-links → recommended
    section → Amazon partner tag. No-op while AFFILIATE_LINKS is empty."""
    affiliate_map = _affiliate_map()
    for keyword, url in affiliate_map.items():
        body = body.replace(f"[AFFILIATE:{keyword}]", f"[{keyword}]({url})")
    # Strip any remaining unresolved affiliate tokens.
    body = re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)
    if affiliate_map:
        body = _auto_link_keywords(body, affiliate_map)
        body += _recommended_tools_section(body, affiliate_map)
    return _tag_amazon_links(body)


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
        print("[VERIFY][FAIL] GitHub Pages: CONTENT_REPO_TOKEN missing")
        return False
    try:
        r = httpx.get(
            f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}",
            headers=_gh_headers(),
            timeout=20,
        )
        if r.is_success:
            default_branch = r.json().get("default_branch", "")
            print(f"[VERIFY][OK] GitHub Pages: {GH_OWNER}/{GH_REPO} reachable (default branch: {default_branch})")
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
    if not _hashnode_allowed():
        print(
            "[VERIFY][SKIP] Hashnode: API requires a paid Pro plan since 2026-05-13 "
            "(gql.hashnode.com 301s to the announcement); disabled under max_cost_usd:0. "
            "Set PAID_ADAPTERS_ENABLED=true to re-enable after upgrading."
        )
        return True
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
            if "me" in errors.lower() or "authorization" in errors.lower() or "unauthorized" in errors.lower():
                print(f"[VERIFY][FAIL] Hashnode auth error: {errors}")
                return False
            print(f"[VERIFY][WARN] Hashnode publication lookup warning: {errors}")
        me = data.get("data", {}).get("me")
        if me:
            print(f"[VERIFY][OK] Hashnode: authenticated as {me.get('username') or me.get('id')}")
            return True
        print("[VERIFY][OK] Hashnode: API key accepted; publication will be validated on publish")
        return True
    except Exception as exc:
        print(f"[VERIFY][FAIL] Hashnode request failed: {exc}")
    return False


def _verify_medium() -> bool:
    if not MEDIUM_KEY or not MEDIUM_AUTHOR_ID:
        print(
            "[VERIFY][SKIP] Medium: API key or author ID not configured"
        )
        return True
    try:
        r = httpx.get(
            "https://api.medium.com/v1/me",
            headers={"Authorization": f"Bearer {MEDIUM_KEY}", "Accept": "application/json"},
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
        print(f"[VERIFY][OK] Medium: authenticated as {data.get('username') or actual_author_id}")
        return True
    except Exception as exc:
        print(f"[VERIFY][FAIL] Medium request failed: {exc}")
    return False


def _verify_ai_provider() -> bool:
    """Verify at least one LLM provider is configured and reachable."""
    providers_checked = 0
    providers_ok = 0

    if GROQ_KEY:
        providers_checked += 1
        try:
            r = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                timeout=20,
            )
            if r.is_success:
                print("[VERIFY][OK] Groq: API key accepted")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] Groq {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] Groq request failed: {exc}")

    if HF_TOKEN:
        providers_checked += 1
        try:
            r = httpx.get(
                f"{HF_INFERENCE_BASE}/meta-llama/Llama-3.1-8B-Instruct/v1/chat/completions",
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                timeout=20,
            )
            if r.status_code in (200, 400):  # 400 = missing input (expected for HEAD check), 200 = OK
                print("[VERIFY][OK] HuggingFace: API key accepted")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] HuggingFace {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] HuggingFace request failed: {exc}")

    if GEMINI_KEY:
        providers_checked += 1
        try:
            model_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}"
            r = httpx.get(f"{model_url}?key={GEMINI_KEY}", timeout=20)
            if r.is_success:
                print(f"[VERIFY][OK] Gemini: model reachable ({GEMINI_MODEL})")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] Gemini {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] Gemini request failed: {exc}")

    if OPENAI_KEY:
        providers_checked += 1
        try:
            r = httpx.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                timeout=20,
            )
            if r.is_success:
                print(f"[VERIFY][OK] OpenAI: API key accepted ({OPENAI_MODEL})")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] OpenAI {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] OpenAI request failed: {exc}")

    if OPENROUTER_KEY:
        providers_checked += 1
        try:
            r = httpx.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
                timeout=20,
            )
            if r.is_success:
                print(f"[VERIFY][OK] OpenRouter: API key accepted ({OPENROUTER_MODEL})")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] OpenRouter {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] OpenRouter request failed: {exc}")

    if DEEPSEEK_KEY:
        providers_checked += 1
        try:
            r = httpx.get(
                "https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
                timeout=20,
            )
            if r.is_success:
                print(f"[VERIFY][OK] DeepSeek: API key accepted ({DEEPSEEK_MODEL})")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] DeepSeek {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] DeepSeek request failed: {exc}")

    if ANTHROPIC_KEY:
        providers_checked += 1
        try:
            r = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": ANTHROPIC_KEY},
                timeout=20,
            )
            if r.is_success:
                print(f"[VERIFY][OK] Anthropic: API key accepted ({ANTHROPIC_MODEL})")
                providers_ok += 1
            else:
                print(f"[VERIFY][WARN] Anthropic {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][WARN] Anthropic request failed: {exc}")

    if providers_ok == 0:
        print("[VERIFY][FAIL] AI providers: no LLM provider is configured or reachable")
        return False
    print(f"[VERIFY][OK] AI providers: {providers_ok}/{providers_checked} providers reachable")
    return True


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
        raise RuntimeError("CONTENT_REPO_TOKEN not set")
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
    pages_url = f"https://{GH_OWNER}.github.io/{GH_REPO}"
    # Jekyll permalink: pretty — posts render as /posts/slug/
    return f"{pages_url}/posts/{filename.replace('.md', '')}/"


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
        sanitized = re.sub(r'[^a-z0-9]', '', t.lower().replace('-', '').replace(' ', ''))[:20]
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
    if r.status_code == 422 and "canonical" in r.text.lower():
        # Article with this canonical URL was already published in a previous run.
        existing = _find_devto_by_canonical(canonical_url)
        if existing:
            print(f"[OK] Dev.to: already published (canonical match): {existing}")
            return existing
        print("[SKIP] Dev.to: canonical URL already taken; existing article not found via API")
        return None
    if not r.is_success:
        print(f"[FAIL] Dev.to {r.status_code}: {r.text[:300]}")
        r.raise_for_status()
    url = r.json().get("url", "")
    print(f"[OK] Published to Dev.to: {url}")
    return url


def _find_devto_by_canonical(canonical_url: str) -> Optional[str]:
    """Find the authenticated user's existing Dev.to article matching a canonical URL."""
    if not canonical_url:
        return None
    try:
        r = httpx.get(
            f"{DEVTO_BASE}/articles/me/all",
            headers={"api-key": DEVTO_KEY},
            params={"per_page": 100},
            timeout=30,
        )
        r.raise_for_status()
        for a in r.json():
            if (a.get("canonical_url") or "").rstrip("/") == canonical_url.rstrip("/"):
                return a.get("url", "")
    except Exception as exc:
        print(f"[WARN] Dev.to canonical lookup failed: {exc}")
    return None


# ── Hashnode publish ───────────────────────────────────────────────────────────
def _hashnode_allowed() -> bool:
    # Hashnode retired free GraphQL API access on 2026-05-13; all requests now
    # require a paid Pro plan, which violates the max_cost_usd:0 constraint.
    return os.getenv("PAID_ADAPTERS_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def publish_hashnode(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not _hashnode_allowed():
        print(
            "[SKIP] Hashnode: API is paid-only since 2026-05-13 — disabled under "
            "max_cost_usd:0 (set PAID_ADAPTERS_ENABLED=true after upgrading to Pro)"
        )
        return None
    if not HASHNODE_KEY or not HASHNODE_PUB_ID:
        print("[SKIP] HASHNODE_API_KEY or HASHNODE_PUBLICATION_ID not set -- skipping Hashnode")
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
    # Hashnode v2 GQL expects the raw token in Authorization (no Bearer prefix);
    # a Bearer-prefixed token is rejected and can return a non-JSON error page.
    auth_header = HASHNODE_KEY[7:].strip() if HASHNODE_KEY.lower().startswith("bearer ") else HASHNODE_KEY
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
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(
            f"Hashnode returned non-JSON (HTTP {r.status_code}, "
            f"content-type {r.headers.get('content-type', '?')}): {r.text[:300]}"
        )
    if data.get("errors"):
        raise RuntimeError(f"Hashnode errors: {data['errors']}")
    post = data.get("data", {}).get("publishPost", {}).get("post", {})
    url = post.get("url", "")
    print(f"[OK] Published to Hashnode: {url}")
    return url


# ── Medium publish ─────────────────────────────────────────────────────────────
def publish_medium(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not MEDIUM_KEY or not MEDIUM_AUTHOR_ID:
        print("[SKIP] Medium: API key or author ID not configured")
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
        headers={"Authorization": f"Bearer {MEDIUM_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    url = r.json().get("data", {}).get("url", "")
    print(f"[OK] Published to Medium: {url}")
    return url


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    if VERIFY_ONLY:
        verify_publish_configuration()
        return

    topic = _default_topic()
    article = generate_article(topic)

    now = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    slug = article.get("slug", article["title"][:50].lower().replace(" ", "-"))
    # Sanitize slug
    slug = re.sub(r"[^a-z0-9-]", "", slug)[:60].strip("-")
    filename = f"{date_str}-{slug}.md"

    # Inject affiliate links (noop until AFFILIATE_LINKS env var is set)
    article["body"] = _inject_affiliates(article.get("body", ""))
    jekyll_md = make_jekyll_post(article, date_str)

    # 1. GitHub Pages (canonical URL)
    canonical_url = ""
    try:
        canonical_url = publish_github(
            filename=filename,
            content=jekyll_md,
            commit_msg=f"Add post: {article['title']}",
        )
    except Exception as exc:
        print(f"[FAIL] GitHub publish failed: {exc}")

    # 2. Dev.to
    devto_url = None
    try:
        devto_url = publish_devto(article, canonical_url)
    except Exception as exc:
        print(f"[FAIL] Dev.to publish failed: {exc}")

    # 3. Hashnode
    hashnode_url = None
    try:
        hashnode_url = publish_hashnode(article, canonical_url)
    except Exception as exc:
        print(f"[FAIL] Hashnode publish failed: {exc}")

    # 4. Medium
    medium_url = None
    try:
        medium_url = publish_medium(article, canonical_url)
    except Exception as exc:
        print(f"[FAIL] Medium publish failed: {exc}")

    # 5. EAOS Social Blast — posts to all configured platforms simultaneously
    if canonical_url:
        try:
            from runtime.eaos.social_engine import ProductionSocialEngine
            tags = article.get("tags", [])
            title_text = article["title"]
            thread_tweets = [
                f"New post: {title_text} {canonical_url}",
                f"Read more on GitHub Pages, Dev.to, and Hashnode → {canonical_url}",
                "#ProfitEngine #AIContent #PassiveIncome #AlreadyHereLLC",
            ]
            engine = ProductionSocialEngine()
            asyncio.run(engine.publish_all_platforms(
                text=title_text,
                url=canonical_url,
                tags=tags[:5],
                thread_tweets=thread_tweets,
            ))
            print("[OK] EAOS social blast dispatched")
        except Exception as exc:
            print(f"[WARN] EAOS social blast skipped: {exc}")

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
            payload = json.dumps({
                "title": article["title"],
                "topic": topic,
                "canonical_url": canonical_url,
                "devto_url": devto_url or "",
                "medium_url": medium_url or "",
                "hashnode_url": hashnode_url or "",
                "platforms": (["github_pages"]
                              + (["devto"] if devto_url else [])
                              + (["medium"] if medium_url else [])
                              + (["hashnode"] if hashnode_url else [])),
            }).encode()
            _req.urlopen(  # noqa: S310
                _req.Request(  # noqa: S310
                    f"{_CMDOS_BASE}/api/content-sync/published",
                    data=payload,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                ),
                timeout=8,
            )
            print("[ContentSync] Published article logged to Growth Command OS")
        except Exception as e:
            print(f"[ContentSync] Could not log to dashboard (non-fatal): {e}")


if __name__ == "__main__":
    main()

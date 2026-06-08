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
    GITHUB_CONTENT_DIR     — default: posts
    DEVTO_API_KEY          — from dev.to/settings/extensions
    ARTICLE_TOPIC          — override the default topic
    CONTENT_VERIFY_ONLY    — true to verify credentials without publishing
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

GROQ_MODEL = os.getenv("GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile")  # overridden by GROQ_MODELS list below
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
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


# ── Groq generation ────────────────────────────────────────────────────────────
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GMAOS_GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

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
        try:
            raw = _call_gemini(prompt)
            print(f"[AI] Provider: Gemini ({GEMINI_MODEL})")
        except Exception as e:
            print(f"[AI] Gemini failed ({e})")
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
            "[VERIFY][SKIP] Medium: "
            f"MEDIUM_API_KEY={_mask_configured(MEDIUM_KEY)}, "
            f"MEDIUM_AUTHOR_ID={_mask_configured(MEDIUM_AUTHOR_ID)}"
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
    print("[VERIFY][FAIL] AI provider: neither GROQ_API_KEY nor GEMINI_API_KEY is configured")
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
    if not r.is_success:
        print(f"[FAIL] Dev.to {r.status_code}: {r.text[:300]}")
        r.raise_for_status()
    url = r.json().get("url", "")
    print(f"[OK] Published to Dev.to: {url}")
    return url


# ── Hashnode publish ───────────────────────────────────────────────────────────
def publish_hashnode(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
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
    # Hashnode uses Authorization: Bearer <token> as of their v2 API migration
    # follow_redirects=True so 301 redirects are followed automatically
    auth_header = HASHNODE_KEY if HASHNODE_KEY.lower().startswith("bearer ") else f"Bearer {HASHNODE_KEY}"
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

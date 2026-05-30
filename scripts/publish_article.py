#!/usr/bin/env python3
"""
Standalone article generator + publisher for ProfitEngine.

Generates an SEO article via free-tier AI providers and publishes to:
  1. GitHub Pages (quantam101/content)
  2. Dev.to (if DEVTO_API_KEY is set)
  3. Hashnode (if HASHNODE_API_KEY and HASHNODE_PUBLICATION_ID are set)
  4. Medium (if MEDIUM_API_KEY and MEDIUM_AUTHOR_ID are set)

Usage:
    python scripts/publish_article.py

Required env vars:
    GITHUB_CONTENT_TOKEN   — GitHub PAT with repo scope
    GITHUB_CONTENT_OWNER   — e.g. quantam101
    GITHUB_CONTENT_REPO    — e.g. content

AI provider env vars:
    GROQ_API_KEY           — primary provider from console.groq.com
    GEMINI_API_KEY         — fallback provider from Google AI Studio

Optional:
    GITHUB_CONTENT_BRANCH  — default: main
    GITHUB_CONTENT_DIR     — default: posts
    DEVTO_API_KEY          — from dev.to/settings/extensions
    HASHNODE_API_KEY       — Hashnode Personal Access Token
    HASHNODE_PUBLICATION_ID — Hashnode publication ID
    MEDIUM_API_KEY         — Medium integration token
    MEDIUM_AUTHOR_ID       — Medium user/author ID
    ARTICLE_TOPIC          — override the default topic
    GMAOS_GROQ_MODEL       — default: llama-3.3-70b-versatile
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

# ── Config ─────────────────────────────────────────────────────────────────────
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GH_BASE = "https://api.github.com"
DEVTO_BASE = "https://dev.to/api"

GROQ_MODEL = os.getenv("GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
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


def _default_topic() -> str:
    """Pick today's topic from the rotation list, or use ARTICLE_TOPIC env override."""
    override = os.getenv("ARTICLE_TOPIC", "").strip()
    if override:
        return override
    try:
        # Import sibling module without package install.
        import importlib.util
        import pathlib

        spec = importlib.util.spec_from_file_location(
            "article_topics",
            pathlib.Path(__file__).parent / "article_topics.py",
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("article_topics module spec unavailable")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return str(mod.pick_topic())
    except Exception:
        return "Best Free AI Tools to Build Passive Income Streams in 2026"


DEFAULT_TOPIC = _default_topic()

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
- No placeholder text — real, useful content"""


# ── AI generation ──────────────────────────────────────────────────────────────
def _call_groq(prompt: str) -> str:
    """Call Groq API. Raises on failure."""
    resp = httpx.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={
            "model": GROQ_MODEL,
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


def _call_gemini(prompt: str) -> str:
    """Call Gemini Flash API. Raises on failure."""
    resp = httpx.post(
        f"{GEMINI_URL}?key={GEMINI_KEY}",
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


def _parse_article_json(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        article = json.loads(cleaned)
    except json.JSONDecodeError:
        article = json.loads(cleaned, strict=False)
    if not isinstance(article, dict):
        raise ValueError("AI response was not a JSON object")
    required = ["title", "slug", "meta_description", "tags", "body"]
    missing = [field for field in required if not article.get(field)]
    if missing:
        raise ValueError(f"AI response missing required fields: {', '.join(missing)}")
    return article


def generate_article(topic: str) -> Dict[str, Any]:
    if not GROQ_KEY and not GEMINI_KEY:
        sys.exit("Neither GROQ_API_KEY nor GEMINI_API_KEY is set")
    print(f"[AI] Generating article: {topic}")
    prompt = ARTICLE_PROMPT.format(topic=topic)

    raw = ""
    if GROQ_KEY:
        try:
            raw = _call_groq(prompt)
            print("[AI] Provider: Groq")
        except Exception as exc:
            print(f"[AI] Groq failed ({exc}), trying Gemini...")
    if not raw and GEMINI_KEY:
        raw = _call_gemini(prompt)
        print("[AI] Provider: Gemini")
    if not raw:
        raise RuntimeError("No AI provider returned content")

    article = _parse_article_json(raw)
    print(f"[OK] Article generated: {article['title']}")
    return article


# ── Affiliate link injection ───────────────────────────────────────────────────
def _inject_affiliates(body: str) -> str:
    """Replace [AFFILIATE:keyword] placeholders with markdown links, or strip them."""
    try:
        affiliate_map: Dict[str, str] = json.loads(AFFILIATE_LINKS_JSON)
    except json.JSONDecodeError:
        affiliate_map = {}
    for keyword, url in affiliate_map.items():
        body = body.replace(f"[AFFILIATE:{keyword}]", f"[{keyword}]({url})")
    return re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)


# ── GitHub Pages publish ───────────────────────────────────────────────────────
def _gh_headers() -> Dict[str, str]:
    return {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ProfitEngine/5.0",
    }


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
    except Exception:
        pass
    return None


def make_jekyll_post(article: Dict[str, Any], date_str: str) -> str:
    title = str(article.get("title", "Untitled")).replace('"', '\\"')
    meta = str(article.get("meta_description", "")).replace('"', '\\"')
    tags: List[str] = [str(tag) for tag in article.get("tags", [])]
    body: str = str(article.get("body", ""))
    tags_yaml = "\n".join(f"  - {tag}" for tag in tags)
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
    return f"{pages_url}/posts/{filename.replace('.md', '.html')}"


# ── Dev.to publish ─────────────────────────────────────────────────────────────
def publish_devto(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not DEVTO_KEY:
        print("[SKIP] DEVTO_API_KEY not set -- skipping Dev.to")
        return None
    title = article.get("title", "Untitled")
    meta = article.get("meta_description", "")
    body = article.get("body", "")
    raw_tags: List[str] = article.get("tags", [])
    clean_tags: List[str] = []
    for tag in raw_tags:
        sanitized = re.sub(r"[^a-z0-9]", "", str(tag).lower().replace(" ", "").replace("-", ""))[:20]
        if sanitized and sanitized not in clean_tags:
            clean_tags.append(sanitized)
    payload: Dict[str, Any] = {
        "article": {
            "title": title,
            "published": True,
            "body_markdown": f"> {meta}\n\n{body}" if meta else body,
            "tags": clean_tags[:4],
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
    payload: Dict[str, Any] = {
        "title": title,
        "contentMarkdown": f"> {meta}\n\n{body}" if meta else body,
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
    r = httpx.post(
        "https://gql.hashnode.com/",
        headers={"Authorization": HASHNODE_KEY, "Content-Type": "application/json"},
        json={"query": query, "variables": {"input": payload}},
        timeout=30,
    )
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
    payload: Dict[str, Any] = {
        "title": title,
        "contentFormat": "markdown",
        "content": f"> {meta}\n\n{body}" if meta else body,
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
    article = generate_article(DEFAULT_TOPIC)
    now = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    slug = str(article.get("slug", article["title"][:50].lower().replace(" ", "-")))
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower())[:60].strip("-") or "profitengine-article"
    filename = f"{date_str}-{slug}.md"

    article["body"] = _inject_affiliates(str(article.get("body", "")))
    jekyll_md = make_jekyll_post(article, date_str)

    canonical_url = ""
    try:
        canonical_url = publish_github(
            filename=filename,
            content=jekyll_md,
            commit_msg=f"Add post: {article['title']}",
        )
    except Exception as exc:
        print(f"[FAIL] GitHub publish failed: {exc}")

    devto_url = None
    try:
        devto_url = publish_devto(article, canonical_url)
    except Exception as exc:
        print(f"[FAIL] Dev.to publish failed: {exc}")

    hashnode_url = None
    try:
        hashnode_url = publish_hashnode(article, canonical_url)
    except Exception as exc:
        print(f"[FAIL] Hashnode publish failed: {exc}")

    medium_url = None
    try:
        medium_url = publish_medium(article, canonical_url)
    except Exception as exc:
        print(f"[FAIL] Medium publish failed: {exc}")

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


if __name__ == "__main__":
    main()

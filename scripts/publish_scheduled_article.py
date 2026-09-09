#!/usr/bin/env python3
"""Publish a pre-produced daily article and fan it out to configured channels.

The article is loaded from data/scheduled_articles/YYYY-MM-DD.json. This lets
ProfitEngine produce tomorrow's article ahead of time while preserving the same
canonical publish, syndication, social blast, and daily verification path.

Idempotency: if the dated canonical post already exists in quantam101/content,
this script exits successfully without re-syndicating it.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

GH_BASE = "https://api.github.com"
DEVTO_BASE = "https://dev.to/api"
GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_DIR = os.getenv("GITHUB_CONTENT_DIR", "_posts").strip()
SITE_BASE = os.getenv("CONTENT_SITE_BASE", "https://www.alreadyherellc.com/content").rstrip("/")
DEVTO_KEY = os.getenv("DEVTO_API_KEY", "").strip()
HASHNODE_KEY = os.getenv("HASHNODE_API_KEY", "").strip()
HASHNODE_PUB_ID = os.getenv("HASHNODE_PUBLICATION_ID", "").strip()
MEDIUM_KEY = os.getenv("MEDIUM_API_KEY", "").strip()
MEDIUM_AUTHOR_ID = os.getenv("MEDIUM_AUTHOR_ID", "").strip()
CMDOS_BASE = (os.getenv("CMDOS_BASE_URL", "").strip() or "https://app.alreadyherellc.com").rstrip("/")


def headers() -> Dict[str, str]:
    return {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ProfitEngine-Scheduled-Content/1.0",
    }


def load_article(date_str: str) -> Dict[str, Any]:
    path = pathlib.Path("data/scheduled_articles") / f"{date_str}.json"
    if not path.exists():
        raise SystemExit(f"No scheduled article found for {date_str}: {path}")
    article = json.loads(path.read_text(encoding="utf-8"))
    for key in ("title", "slug", "meta_description", "tags", "body"):
        if not article.get(key):
            raise SystemExit(f"Scheduled article missing required field: {key}")
    if not isinstance(article["tags"], list):
        raise SystemExit("Scheduled article tags must be a list")
    return article


def canonical_path(date_str: str, slug: str) -> str:
    clean = re.sub(r"[^a-z0-9-]", "", slug.lower())[:80].strip("-")
    return f"{GH_DIR}/{date_str}-{clean}.md"


def canonical_exists(path: str) -> bool:
    r = httpx.get(
        f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}/contents/{path}",
        headers=headers(),
        params={"ref": GH_BRANCH},
        timeout=20,
    )
    return r.status_code == 200


def jekyll_post(article: Dict[str, Any], date_str: str) -> str:
    title = str(article["title"]).replace('"', '\\"')
    meta = str(article["meta_description"]).replace('"', '\\"')
    tags = "\n".join(f"  - {str(t)}" for t in article["tags"])
    return (
        "---\n"
        f'title: "{title}"\n'
        f'description: "{meta}"\n'
        f"date: {date_str}\n"
        f"tags:\n{tags}\n"
        "layout: post\n"
        "---\n\n"
        f"{article['body'].rstrip()}\n"
    )


def publish_canonical(path: str, content: str, title: str) -> str:
    if not GH_TOKEN:
        raise RuntimeError("GITHUB_CONTENT_TOKEN not set")
    payload = {
        "message": f"Add scheduled post: {title}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": GH_BRANCH,
    }
    r = httpx.put(
        f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}/contents/{path}",
        headers=headers(),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", pathlib.Path(path).stem)
    url = f"{SITE_BASE}/posts/{slug}/"
    print(f"[OK] Canonical scheduled article published: {url}")
    return url


def publish_devto(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not DEVTO_KEY:
        print("[SKIP] Dev.to credentials missing")
        return None
    clean_tags: List[str] = []
    for tag in article["tags"]:
        t = re.sub(r"[^a-z0-9]", "", str(tag).lower())[:20]
        if t and t not in clean_tags:
            clean_tags.append(t)
    for fallback in ("ai", "saas", "automation", "productivity"):
        if len(clean_tags) < 4 and fallback not in clean_tags:
            clean_tags.append(fallback)
    payload = {
        "article": {
            "title": article["title"],
            "published": True,
            "body_markdown": article["body"],
            "tags": clean_tags[:4],
            "canonical_url": canonical_url,
        }
    }
    r = httpx.post(
        f"{DEVTO_BASE}/articles",
        headers={"api-key": DEVTO_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    url = r.json().get("url", "")
    print(f"[OK] Dev.to: {url}")
    return url or None


def publish_hashnode(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not HASHNODE_KEY or not HASHNODE_PUB_ID:
        print("[SKIP] Hashnode credentials missing")
        return None
    auth = HASHNODE_KEY if HASHNODE_KEY.lower().startswith("bearer ") else f"Bearer {HASHNODE_KEY}"
    query = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) { post { url id } }
    }
    """
    inp = {
        "title": article["title"],
        "contentMarkdown": article["body"],
        "publicationId": HASHNODE_PUB_ID,
        "tags": [],
        "originalArticleURL": canonical_url,
    }
    r = httpx.post(
        "https://gql.hashnode.com",
        headers={"Authorization": auth, "Content-Type": "application/json"},
        json={"query": query, "variables": {"input": inp}},
        timeout=30,
        follow_redirects=True,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"Hashnode errors: {data['errors']}")
    url = data.get("data", {}).get("publishPost", {}).get("post", {}).get("url", "")
    print(f"[OK] Hashnode: {url}")
    return url or None


def publish_medium(article: Dict[str, Any], canonical_url: str) -> Optional[str]:
    if not MEDIUM_KEY or not MEDIUM_AUTHOR_ID:
        print("[SKIP] Medium credentials missing")
        return None
    payload = {
        "title": article["title"],
        "contentFormat": "markdown",
        "content": article["body"],
        "tags": article["tags"][:5],
        "publishStatus": "public",
        "canonicalUrl": canonical_url,
    }
    r = httpx.post(
        f"https://api.medium.com/v1/users/{MEDIUM_AUTHOR_ID}/posts",
        headers={"Authorization": f"Bearer {MEDIUM_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    url = r.json().get("data", {}).get("url", "")
    print(f"[OK] Medium: {url}")
    return url or None


async def social_blast(article: Dict[str, Any], canonical_url: str) -> None:
    try:
        from runtime.eaos.social_engine import ProductionSocialEngine

        title = article["title"]
        engine = ProductionSocialEngine()
        await engine.publish_all_platforms(
            text=f"{title} — {canonical_url}",
            url=canonical_url,
            tags=article["tags"][:5],
            thread_tweets=[
                f"New from ProfitEngine AI: {title} {canonical_url}",
                f"Practical implementation guide: {canonical_url}",
                "#ProfitEngine #AI #Automation #AlreadyHereLLC",
            ],
        )
        print("[OK] Social blast dispatched to every configured EAOS platform")
    except Exception as exc:
        print(f"[WARN] Social blast non-fatal failure: {exc}")


def notify_cmdos(article: Dict[str, Any], canonical_url: str, urls: Dict[str, Optional[str]]) -> None:
    try:
        payload = json.dumps({
            "title": article["title"],
            "topic": article["title"],
            "canonical_url": canonical_url,
            "devto_url": urls.get("devto") or "",
            "medium_url": urls.get("medium") or "",
            "hashnode_url": urls.get("hashnode") or "",
            "platforms": ["github_pages"] + [k for k, v in urls.items() if v],
        }).encode()
        req = urllib.request.Request(
            f"{CMDOS_BASE}/api/content-sync/published",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=8)
        print("[OK] Growth Command OS publication callback recorded")
    except Exception as exc:
        print(f"[WARN] Growth Command OS callback non-fatal failure: {exc}")


def main() -> None:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    article = load_article(date_str)
    path = canonical_path(date_str, article["slug"])
    if canonical_exists(path):
        print(f"[SKIP] Scheduled canonical already exists: {path}")
        return

    canonical_url = publish_canonical(path, jekyll_post(article, date_str), article["title"])

    urls: Dict[str, Optional[str]] = {"devto": None, "hashnode": None, "medium": None}
    for name, fn in (("devto", publish_devto), ("hashnode", publish_hashnode), ("medium", publish_medium)):
        try:
            urls[name] = fn(article, canonical_url)
        except Exception as exc:
            print(f"[WARN] {name} syndication failed: {exc}")

    asyncio.run(social_blast(article, canonical_url))
    notify_cmdos(article, canonical_url, urls)

    print("\n== Scheduled Content Summary ==")
    print(f"Date: {date_str}")
    print(f"Title: {article['title']}")
    print(f"Canonical: {canonical_url}")
    for name, url in urls.items():
        if url:
            print(f"{name}: {url}")


if __name__ == "__main__":
    main()

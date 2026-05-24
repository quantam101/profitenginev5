"""
Dev.to API client.

Publishes markdown articles to dev.to.
Free to use — create an API key at https://dev.to/settings/extensions
Set DEVTO_API_KEY in your server .env.

Dev.to is a developer community with high organic traffic.
Articles published here get indexed by Google within 24-48 hours.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

_DEVTO_BASE = "https://dev.to/api"


def _key() -> str:
    return os.getenv("DEVTO_API_KEY", "").strip()


def publish_article(
    title: str,
    body_markdown: str,
    tags: Optional[List[str]] = None,
    canonical_url: Optional[str] = None,
    published: bool = True,
) -> Dict[str, Any]:
    """
    Publish an article to Dev.to.
    Returns the API response dict (includes 'url', 'id', 'slug').
    Raises RuntimeError if key is missing or request fails.
    """
    api_key = _key()
    if not api_key:
        raise RuntimeError("DEVTO_API_KEY not set — add it to your server .env")

    article_payload: Dict[str, Any] = {
        "title": title,
        "published": published,
        "body_markdown": body_markdown,
        "tags": (tags or [])[:4],  # dev.to max 4 tags
    }
    if canonical_url:
        article_payload["canonical_url"] = canonical_url

    try:
        resp = httpx.post(
            f"{_DEVTO_BASE}/articles",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json={"article": article_payload},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Dev.to API error {exc.response.status_code}: {exc.response.text}") from exc


def list_articles(page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
    """List articles published by the authenticated user."""
    api_key = _key()
    if not api_key:
        return []
    try:
        resp = httpx.get(
            f"{_DEVTO_BASE}/articles/me",
            headers={"api-key": api_key},
            params={"page": page, "per_page": per_page},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

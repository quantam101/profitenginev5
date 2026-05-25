"""
Medium API client.

Publishes articles to Medium.
Free — get an integration token at https://medium.com/me/settings → Integration tokens
Set MEDIUM_API_KEY and MEDIUM_AUTHOR_ID in your server .env.

To find your author ID:
  curl -H 'Authorization: Bearer YOUR_KEY' https://api.medium.com/v1/me | python3 -m json.tool
  Look for the "id" field.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

_MEDIUM_BASE = "https://api.medium.com/v1"


def _key() -> str:
    return os.getenv("MEDIUM_API_KEY", "").strip()


def _author_id() -> str:
    return os.getenv("MEDIUM_AUTHOR_ID", "").strip()


def publish_article(
    title: str,
    body_markdown: str,
    tags: Optional[List[str]] = None,
    canonical_url: Optional[str] = None,
    published: bool = True,
) -> Dict[str, Any]:
    """
    Publish an article to Medium.
    Returns dict with 'url' and 'id'.
    Raises RuntimeError if key or author ID is missing or request fails.
    """
    api_key = _key()
    author_id = _author_id()
    if not api_key:
        raise RuntimeError("MEDIUM_API_KEY not set — get it at medium.com/me/settings → Integration tokens")
    if not author_id:
        raise RuntimeError(
            "MEDIUM_AUTHOR_ID not set — run: "
            "curl -H 'Authorization: Bearer KEY' https://api.medium.com/v1/me"
        )

    payload: Dict[str, Any] = {
        "title": title,
        "contentFormat": "markdown",
        "content": body_markdown,
        "publishStatus": "public" if published else "draft",
        "tags": (tags or [])[:5],
    }
    if canonical_url:
        payload["canonicalUrl"] = canonical_url

    try:
        resp = httpx.post(
            f"{_MEDIUM_BASE}/users/{author_id}/posts",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {"url": data.get("url", ""), "id": data.get("id", "")}
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Medium HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Medium request failed: {exc}") from exc

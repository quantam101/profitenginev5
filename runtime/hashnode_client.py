"""
Hashnode API client.

Publishes articles to your Hashnode blog.
Free — get an API key at https://hashnode.com/settings/developer
Set HASHNODE_API_KEY and HASHNODE_PUBLICATION_ID in your server .env.

Hashnode provides high-authority SEO backlinks and a developer audience.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

_HASHNODE_GQL = "https://gql.hashnode.com/"


def _key() -> str:
    return os.getenv("HASHNODE_API_KEY", "").strip()


def _pub_id() -> str:
    return os.getenv("HASHNODE_PUBLICATION_ID", "").strip()


def publish_article(
    title: str,
    body_markdown: str,
    tags: Optional[List[str]] = None,
    canonical_url: Optional[str] = None,
    published: bool = True,
) -> Dict[str, Any]:
    """
    Publish an article to Hashnode via GraphQL.
    Returns dict with 'url' and 'id'.
    Raises RuntimeError if key or publication ID is missing or request fails.
    """
    api_key = _key()
    pub_id = _pub_id()
    if not api_key:
        raise RuntimeError("HASHNODE_API_KEY not set — add it to your server .env")
    if not pub_id:
        raise RuntimeError("HASHNODE_PUBLICATION_ID not set — find it in your Hashnode dashboard")

    payload: Dict[str, Any] = {
        "title": title,
        "contentMarkdown": body_markdown,
        "publicationId": pub_id,
        "tags": [],
    }
    if canonical_url:
        payload["originalArticleURL"] = canonical_url

    query = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post { url id }
      }
    }
    """

    try:
        resp = httpx.post(
            _HASHNODE_GQL,
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json",
            },
            json={"query": query, "variables": {"input": payload}},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        errors = data.get("errors")
        if errors:
            raise RuntimeError(f"Hashnode API error: {errors}")
        post = data.get("data", {}).get("publishPost", {}).get("post", {})
        if not post:
            raise RuntimeError("Hashnode: no post returned in response")
        return {"url": post.get("url", ""), "id": post.get("id", "")}
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Hashnode HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Hashnode request failed: {exc}") from exc

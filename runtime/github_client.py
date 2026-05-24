"""
GitHub API client for publishing content to a GitHub Pages repository.

Commits markdown files to a repo so they can be served as a static content site.
Free forever — uses GitHub's public CDN + Pages.

Set these in your server .env:
  GITHUB_CONTENT_TOKEN  — personal access token (repo scope)
  GITHUB_CONTENT_OWNER  — GitHub username or org (e.g. quantam101)
  GITHUB_CONTENT_REPO   — repository name (e.g. content)
  GITHUB_CONTENT_BRANCH — branch to commit to (default: main)
  GITHUB_CONTENT_DIR    — directory prefix inside the repo (default: posts)
"""
from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional

import httpx

_GH_BASE = "https://api.github.com"


def _cfg() -> Dict[str, str]:
    return {
        "token": os.getenv("GITHUB_CONTENT_TOKEN", "").strip(),
        "owner": os.getenv("GITHUB_CONTENT_OWNER", "").strip(),
        "repo": os.getenv("GITHUB_CONTENT_REPO", "").strip(),
        "branch": os.getenv("GITHUB_CONTENT_BRANCH", "main").strip(),
        "dir": os.getenv("GITHUB_CONTENT_DIR", "posts").strip(),
    }


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ProfitEngine/5.0",
    }


def _get_file_sha(token: str, owner: str, repo: str, path: str, branch: str) -> Optional[str]:
    """Get current SHA of a file (needed for updates)."""
    try:
        resp = httpx.get(
            f"{_GH_BASE}/repos/{owner}/{repo}/contents/{path}",
            headers=_headers(token),
            params={"ref": branch},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("sha")
    except Exception:
        pass
    return None


def publish_file(
    filename: str,
    content: str,
    commit_message: str = "Add content via ProfitEngine",
) -> Dict[str, Any]:
    """
    Create or update a file in the configured GitHub content repo.
    filename: just the filename, e.g. '2026-05-24-ai-tools.md'
    Returns the GitHub API response with 'content.html_url'.
    Raises RuntimeError if config is missing or request fails.
    """
    cfg = _cfg()
    if not cfg["token"] or not cfg["owner"] or not cfg["repo"]:
        raise RuntimeError(
            "GitHub publishing requires GITHUB_CONTENT_TOKEN, GITHUB_CONTENT_OWNER, "
            "and GITHUB_CONTENT_REPO in your server .env"
        )

    path = f"{cfg['dir']}/{filename}"
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    sha = _get_file_sha(cfg["token"], cfg["owner"], cfg["repo"], path, cfg["branch"])

    payload: Dict[str, Any] = {
        "message": commit_message,
        "content": content_b64,
        "branch": cfg["branch"],
    }
    if sha:
        payload["sha"] = sha  # required for updates

    try:
        resp = httpx.put(
            f"{_GH_BASE}/repos/{cfg['owner']}/{cfg['repo']}/contents/{path}",
            headers=_headers(cfg["token"]),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "html_url": data.get("content", {}).get("html_url", ""),
            "path": path,
            "sha": data.get("content", {}).get("sha", ""),
        }
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"GitHub API error {exc.response.status_code}: {exc.response.text}"
        ) from exc


def pages_url() -> str:
    """Return the GitHub Pages URL for the content repo."""
    cfg = _cfg()
    if cfg["owner"] and cfg["repo"]:
        return f"https://{cfg['owner']}.github.io/{cfg['repo']}"
    return ""

"""IndexNow submission queue persisted in the content repo.

A ping is only sent once the post is publicly live. If GitHub Pages has not
deployed by the time the wait window ends, the URL is appended to
`_data/indexnow_pending.json` in the content repo and retried by later runs —
so a slow deploy can never lose the notification.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from typing import List

import httpx

GH_BASE = "https://api.github.com"
PENDING_PATH = "_data/indexnow_pending.json"


def _repo_config():
    return (
        os.getenv("GITHUB_CONTENT_TOKEN", "").strip(),
        os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip(),
        os.getenv("GITHUB_CONTENT_REPO", "content").strip(),
        os.getenv("GITHUB_CONTENT_BRANCH", "main").strip(),
    )


def _headers(token: str):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ProfitEngine-IndexNow/1.0",
    }


def _pending_get():
    token, owner, repo, branch = _repo_config()
    if not token:
        return None
    r = httpx.get(
        f"{GH_BASE}/repos/{owner}/{repo}/contents/{PENDING_PATH}",
        headers=_headers(token),
        params={"ref": branch},
        timeout=20,
    )
    if r.status_code != 200:
        return None
    return r.json()


def load_pending() -> List[str]:
    doc = _pending_get()
    if not doc:
        return []
    try:
        data = json.loads(base64.b64decode(doc["content"]).decode("utf-8"))
        return [u for u in data.get("urls", []) if isinstance(u, str) and u]
    except Exception:
        return []


def save_pending(urls: List[str]) -> None:
    token, owner, repo, branch = _repo_config()
    if not token:
        return
    doc = _pending_get()
    payload = {
        "message": "chore: update IndexNow pending queue",
        "content": base64.b64encode(
            json.dumps({"urls": urls}, indent=2).encode("utf-8")
        ).decode("ascii"),
        "branch": branch,
    }
    if doc and doc.get("sha"):
        payload["sha"] = doc["sha"]
    r = httpx.put(
        f"{GH_BASE}/repos/{owner}/{repo}/contents/{PENDING_PATH}",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()


def enqueue(url: str) -> None:
    try:
        urls = load_pending()
        if url not in urls:
            urls.append(url)
            save_pending(urls)
            print(f"[OK] IndexNow: queued {url} for a later run")
    except Exception as exc:
        print(f"[WARN] IndexNow: failed to persist pending URL ({exc}); pinging anyway")
        ping(url)


def wait_for_live(url: str, attempts: int = 8, delay: int = 20) -> bool:
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        if attempt < attempts - 1:
            time.sleep(delay)
    return False


def ping(url: str) -> bool:
    """Submit the URL to IndexNow. Returns True when the API accepts it.
    The key file must be served at the same host as the URL."""
    key = os.getenv("INDEXNOW_KEY", "").strip()
    if not key:
        return False
    host = urllib.parse.urlparse(url).netloc
    params = urllib.parse.urlencode({
        "url": url,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
    })
    try:
        with urllib.request.urlopen(
            f"https://api.indexnow.org/indexnow?{params}", timeout=15
        ) as resp:
            print(f"[OK] IndexNow ping accepted: {resp.status}")
            return True
    except Exception as exc:
        print(f"[WARN] IndexNow ping failed (non-blocking): {exc}")
        return False


def announce(url: str, attempts: int = 8, delay: int = 20) -> None:
    """Wait for the post to go live, then ping IndexNow. If it never comes
    up inside the wait window, queue the URL so a later run retries it."""
    if wait_for_live(url, attempts=attempts, delay=delay):
        ping(url)
    else:
        print("[WARN] post not live yet; queueing IndexNow submission")
        enqueue(url)


def drain(attempts: int = 3, delay: int = 15) -> None:
    """Retry every queued URL: ping the ones that are live now, keep the
    rest queued for the next run."""
    urls = load_pending()
    if not urls:
        return
    remaining = []
    for url in urls:
        if wait_for_live(url, attempts=attempts, delay=delay) and ping(url):
            continue
        remaining.append(url)
    if remaining != urls:
        try:
            save_pending(remaining)
        except Exception as exc:
            print(f"[WARN] IndexNow: could not update pending queue: {exc}")

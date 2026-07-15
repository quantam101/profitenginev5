#!/usr/bin/env python3
"""Repost OUR OWN top-performing Instagram Reel with a fresh caption.

Safe by construction: only touches media owned by our account (IG_USER_ID) —
never third-party content. Reposts carry an "· encore" marker so they are
never re-reposted, and originals younger than MIN_AGE_DAYS are left alone.

Env:    IG_USER_ID, IG_ACCESS_TOKEN  (same as post_social.py)
Usage:  python scripts/repost_top.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
GRAPH_IG = "https://graph.instagram.com/v21.0"
MARKER = "· encore"
MIN_AGE_DAYS = 14
PREFIXES = ["ICYMI:", "Still true:", "One of our most-loved posts:", "Worth a rewatch:"]


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "already-here-poster/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _post(url: str, data: dict) -> dict:
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(data).encode(), method="POST",
        headers={"User-Agent": "already-here-poster/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def pick_top(base: str, ig: str, tok: str) -> dict | None:
    fields = "id,caption,media_type,media_url,permalink,like_count,comments_count,timestamp"
    d = _get(f"{base}/{ig}/media?fields={fields}&limit=50&access_token={urllib.parse.quote(tok)}")
    now = time.time()
    best, best_score = None, -1
    for m in d.get("data", []):
        if m.get("media_type") != "VIDEO" or not m.get("media_url"):
            continue
        if MARKER in (m.get("caption") or ""):
            continue  # never repost a repost
        ts = time.mktime(time.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
        if (now - ts) < MIN_AGE_DAYS * 86400:
            continue
        score = (m.get("like_count") or 0) + 2 * (m.get("comments_count") or 0)
        if score > best_score:
            best, best_score = m, score
    return best


def main() -> None:
    dry = "--dry-run" in sys.argv
    ig = os.getenv("IG_USER_ID", "").strip()
    tok = os.getenv("IG_ACCESS_TOKEN", "").strip()
    if not (ig and tok):
        print("IG_USER_ID / IG_ACCESS_TOKEN not set — nothing to do")
        return
    base = GRAPH_IG if tok.startswith("IG") else GRAPH
    top = pick_top(base, ig, tok)
    if not top:
        print(f"no repost candidate (needs an owned VIDEO older than {MIN_AGE_DAYS}d without '{MARKER}')")
        return
    first_line = (top.get("caption") or "").split("\n")[0][:120].strip() \
        or "This one deserved a second run."
    prefix = PREFIXES[int(time.time() // 86400) % len(PREFIXES)]  # rotates daily, deterministic
    caption = f"{prefix} {first_line}\n\n{MARKER}"
    print(f"top candidate: {top['permalink']}  (likes={top.get('like_count')}, comments={top.get('comments_count')})")
    if dry:
        print(f"[dry-run] would repost with caption: {caption!r}")
        return
    c = _post(f"{base}/{ig}/media",
              {"media_type": "REELS", "video_url": top["media_url"],
               "caption": caption, "access_token": tok})
    cid = c.get("id")
    if not cid:
        print(f"container failed: {c.get('error', {}).get('message', c)}")
        sys.exit(1)
    for _ in range(30):
        time.sleep(6)
        s = _get(f"{base}/{cid}?fields=status_code&access_token={urllib.parse.quote(tok)}")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            print("container processing ERROR")
            sys.exit(1)
    p = _post(f"{base}/{ig}/media_publish", {"creation_id": cid, "access_token": tok})
    if p.get("id"):
        perma = _get(f"{base}/{p['id']}?fields=permalink&access_token={urllib.parse.quote(tok)}")
        print(f"reposted: {perma.get('permalink', p['id'])}")
    else:
        print(f"publish failed: {p.get('error', {}).get('message', p)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

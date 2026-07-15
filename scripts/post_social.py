#!/usr/bin/env python3
"""Multi-platform auto-poster. Reads videos_manifest.json (with an added public
`url` per video) and posts to every platform whose credentials are present and
valid. Each platform is independent and fails soft — a missing/expired token for
one never blocks the others.

Env (all optional):
  FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN     → Facebook Page video/reel
  IG_USER_ID, IG_ACCESS_TOKEN          → Instagram Reels (falls back to FB token)
  # Twitter/X handled separately (needs OAuth1 lib); wired later.

The rendered MP4s are published as GitHub Release assets by the workflow, giving
each a public https URL that IG/FB fetch by `video_url`.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v21.0"
GRAPH_IG = "https://graph.instagram.com/v21.0"  # Instagram-Login tokens (IGAA…) only work here


def _post(url: str, data: dict) -> dict:
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(data).encode(), method="POST",
        headers={"User-Agent": "already-here-poster/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "already-here-poster/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def post_facebook(video: dict) -> str | None:
    page = os.getenv("FB_PAGE_ID", "").strip()
    tok = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    if not (page and tok and video.get("url")):
        return None
    try:
        caption = f"{video['title']}\n\n{video.get('description', '')[:400]}"
        d = _post(f"{GRAPH}/{page}/videos",
                  {"file_url": video["url"], "description": caption, "access_token": tok})
        if d.get("id"):
            print(f"   ✅ Facebook: posted (id={d['id']})")
            return d["id"]
        print(f"   ❌ Facebook: {d.get('error', {}).get('message', d)}")
    except Exception as e:
        print(f"   ❌ Facebook: {str(e)[:120]}")
    return None


def post_instagram(video: dict) -> str | None:
    ig = os.getenv("IG_USER_ID", "").strip()
    tok = (os.getenv("IG_ACCESS_TOKEN") or os.getenv("FB_PAGE_ACCESS_TOKEN") or "").strip()
    if not (ig and tok and video.get("url")):
        return None
    base = GRAPH_IG if tok.startswith("IG") else GRAPH
    try:
        caption = f"{video['title']}\n\n{video.get('description', '')[:1800]}"
        # 1) create the Reels container
        c = _post(f"{base}/{ig}/media",
                  {"media_type": "REELS", "video_url": video["url"],
                   "caption": caption, "access_token": tok})
        cid = c.get("id")
        if not cid:
            print(f"   ❌ Instagram: {c.get('error', {}).get('message', c)}")
            return None
        # 2) poll until the async upload is FINISHED (IG processes the video)
        for _ in range(30):
            time.sleep(6)
            s = _get(f"{base}/{cid}?fields=status_code&access_token={urllib.parse.quote(tok)}")
            if s.get("status_code") == "FINISHED":
                break
            if s.get("status_code") == "ERROR":
                print("   ❌ Instagram: container processing ERROR")
                return None
        # 3) publish
        p = _post(f"{base}/{ig}/media_publish", {"creation_id": cid, "access_token": tok})
        if p.get("id"):
            print(f"   ✅ Instagram: posted (id={p['id']})")
            return p["id"]
        print(f"   ❌ Instagram: {p.get('error', {}).get('message', p)}")
    except Exception as e:
        print(f"   ❌ Instagram: {str(e)[:120]}")
    return None


GRAPH_THREADS = "https://graph.threads.net/v1.0"


def _yt_link(program: str) -> str | None:
    up = Path("youtube_uploads.json")
    if not up.exists():
        return None
    for u in json.loads(up.read_text()):
        if u.get("program") == program and u.get("video_id"):
            return f"https://www.youtube.com/shorts/{u['video_id']}"
    return None


def post_threads(video: dict) -> str | None:
    """Text post with a clickable link — Threads is the only Meta surface
    where post links are clickable. Activates when THREADS_ACCESS_TOKEN set."""
    tok = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
    if not tok:
        return None
    try:
        link = _yt_link(video["program"]) or video.get("url") or ""
        text = f"{video['title']}\n\n{link}".strip()
        c = _post(f"{GRAPH_THREADS}/me/threads",
                  {"media_type": "TEXT", "text": text[:495], "access_token": tok})
        cid = c.get("id")
        if not cid:
            print(f"   ❌ Threads: {c.get('error', {}).get('message', c)}")
            return None
        time.sleep(3)
        p = _post(f"{GRAPH_THREADS}/me/threads_publish",
                  {"creation_id": cid, "access_token": tok})
        if p.get("id"):
            print(f"   ✅ Threads: posted (id={p['id']})")
            return p["id"]
        print(f"   ❌ Threads: {p.get('error', {}).get('message', p)}")
    except Exception as e:
        print(f"   ❌ Threads: {str(e)[:120]}")
    return None


def main() -> None:
    mf = Path("videos_manifest.json")
    if not mf.exists():
        print("no videos_manifest.json — nothing to post")
        return
    videos = json.loads(mf.read_text())
    results = []
    for v in videos:
        print(f"▶ posting {v['program']}  (url={'yes' if v.get('url') else 'MISSING'})")
        results.append({"program": v["program"],
                        "facebook": post_facebook(v),
                        "instagram": post_instagram(v),
                        "threads": post_threads(v)})
    Path("social_posts.json").write_text(json.dumps(results, indent=2))
    fb = sum(1 for r in results if r["facebook"])
    ig = sum(1 for r in results if r["instagram"])
    th = sum(1 for r in results if r["threads"])
    print(f"\n✅ Social: Facebook {fb}/{len(videos)}, Instagram {ig}/{len(videos)}, "
          f"Threads {th}/{len(videos)}")


if __name__ == "__main__":
    main()

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
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v21.0"
GRAPH_IG = "https://graph.instagram.com/v21.0"  # Instagram-Login tokens (IGAA…) only work here


def _extract_error(e: Exception) -> dict:
    """Turn an HTTPError into the platform's own error dict so logs and the
    health ledger show the real rejection reason, not 'HTTP 400'."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            body = json.loads(e.read())
            if isinstance(body, dict) and body.get("error"):
                err = body["error"]
                return {"message": err.get("message", ""),
                        "code": err.get("code", e.code),
                        "type": err.get("type", "")}
        except Exception:
            pass
        return {"message": f"HTTP {e.code}", "code": e.code}
    return {"message": str(e)[:200]}


def _post(url: str, data: dict) -> dict:
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(data).encode(), method="POST",
        headers={"User-Agent": "already-here-poster/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": _extract_error(e)}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "already-here-poster/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": _extract_error(e)}


def _utm(url: str, source: str) -> str:
    """Tag links that drive traffic so downstream conversions are attributable."""
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    return (f"{url}{sep}utm_source={source}&utm_medium=social"
            f"&utm_campaign=alreadyhere-video")


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
    # Pre-probe: distinguishes "token can't see this IG account" (auth/scope
    # problem) from "account visible but media rejected" (media/URL problem).
    probe = _get(f"{base}/{ig}?fields=id,username,account_type&access_token={urllib.parse.quote(tok)}")
    if probe.get("error"):
        print(f"   ❌ Instagram: auth probe failed — "
              f"{probe['error'].get('message')[:160]} "
              f"(token likely lacks instagram_content_publish or IG_USER_ID is wrong)")
        return {"error": probe["error"], "stage": "auth_probe"}
    if probe.get("account_type") not in ("BUSINESS", "CREATOR"):
        msg = f"account_type={probe.get('account_type') or 'UNKNOWN'} — Reels require a Business/Creator account"
        print(f"   ❌ Instagram: {msg}")
        return {"error": {"message": msg}, "stage": "account_type"}
    print(f"   ℹ️  Instagram: @{probe.get('username','?')} ({probe.get('account_type')})")
    try:
        caption = f"{video['title']}\n\n{video.get('description', '')[:1800]}"
        # 1) create the Reels container
        c = _post(f"{base}/{ig}/media",
                  {"media_type": "REELS", "video_url": video["url"],
                   "caption": caption, "access_token": tok})
        cid = c.get("id")
        if not cid:
            print(f"   ❌ Instagram: {c.get('error', {}).get('message', c)}")
            return {"error": c.get("error", {}), "stage": "container"}
        # 2) poll until the async upload is FINISHED (IG processes the video)
        for _ in range(30):
            time.sleep(6)
            s = _get(f"{base}/{cid}?fields=status_code&access_token={urllib.parse.quote(tok)}")
            if s.get("status_code") == "FINISHED":
                break
            if s.get("status_code") == "ERROR":
                print("   ❌ Instagram: container processing ERROR")
                return {"error": {"message": "container processing error"}, "stage": "processing"}
        # 3) publish
        p = _post(f"{base}/{ig}/media_publish", {"creation_id": cid, "access_token": tok})
        if p.get("id"):
            print(f"   ✅ Instagram: posted (id={p['id']})")
            return p["id"]
        print(f"   ❌ Instagram: {p.get('error', {}).get('message', p)}")
        return {"error": p.get("error", {}), "stage": "publish"}
    except Exception as e:
        print(f"   ❌ Instagram: {str(e)[:120]}")
        return {"error": {"message": str(e)[:200]}, "stage": "exception"}


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
        link = _utm(_yt_link(video["program"]) or video.get("url") or "", "threads")
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
    # Honest health: count a channel as OK only when it returned a real id.
    def _ok(v):
        return isinstance(v, str) and bool(v)
    failures = {r["program"]: {c: r[c] for c in ("facebook", "instagram", "threads")
                               if r.get(c) and not _ok(r[c])}
                for r in results}
    failures = {k: v for k, v in failures.items() if v}
    Path("social_posts.json").write_text(json.dumps(results, indent=2))
    fb = sum(1 for r in results if _ok(r["facebook"]))
    ig = sum(1 for r in results if _ok(r["instagram"]))
    th = sum(1 for r in results if _ok(r["threads"]))
    print(f"\n✅ Social: Facebook {fb}/{len(videos)}, Instagram {ig}/{len(videos)}, "
          f"Threads {th}/{len(videos)}")
    for prog, chans in failures.items():
        for ch, err in chans.items():
            print(f"::error::{ch} post failed for {prog}: "
                  f"{err.get('error', {}).get('message', err)[:160]}")


if __name__ == "__main__":
    main()

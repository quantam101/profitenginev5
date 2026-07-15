#!/usr/bin/env python3
"""Retro-fix: append the funnel link block to existing YouTube video
descriptions that don't have one yet. Videos are read from
youtube_uploads.json (or pass IDs: --ids id1,id2). Idempotent — skips any
description already containing the '→' marker.

Env: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
     AFFILIATE_LINKS (optional JSON map program->url)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

EBOOK = "https://quantam101.github.io/content/ebooks/zero-dollar-content-engine/"
STORE = "https://alreadyhere.gumroad.com"


def link_block(program: str) -> str:
    try:
        links = json.loads(os.getenv("AFFILIATE_LINKS", "") or "{}")
    except Exception:
        links = {}
    lines = []
    if links.get(program):
        lines.append(f"→ Try it: {links[program]}")
    lines.append(f"→ Free playbook — The $0 Content Engine: {EBOOK}")
    lines.append(f"→ Our tools & kits: {STORE}")
    return "\n".join(lines)


def main() -> None:
    if "--ids" in sys.argv:
        ids = sys.argv[sys.argv.index("--ids") + 1].split(",")
        videos = [{"video_id": i, "program": ""} for i in ids]
    else:
        up = Path("youtube_uploads.json")
        if not up.exists():
            print("no youtube_uploads.json and no --ids — nothing to do")
            return
        videos = [u for u in json.loads(up.read_text()) if u.get("video_id")]

    creds = Credentials.from_authorized_user_info({
        "type": "authorized_user",
        "client_id": (os.getenv("YOUTUBE_CLIENT_ID") or "").strip(),
        "client_secret": (os.getenv("YOUTUBE_CLIENT_SECRET") or "").strip(),
        "refresh_token": (os.getenv("YOUTUBE_REFRESH_TOKEN") or "").strip(),
    })
    creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)

    fixed = 0
    for v in videos:
        vid = v["video_id"]
        try:
            r = yt.videos().list(part="snippet", id=vid).execute()
            if not r.get("items"):
                print(f"  ? {vid}: not found")
                continue
            sn = r["items"][0]["snippet"]
            if "→" in (sn.get("description") or ""):
                print(f"  = {vid}: already has links")
                continue
            sn["description"] = (sn.get("description") or "").rstrip() + \
                "\n\n" + link_block(v.get("program", ""))
            yt.videos().update(part="snippet",
                               body={"id": vid, "snippet": sn}).execute()
            print(f"  ✓ {vid}: links added")
            fixed += 1
        except Exception as e:
            print(f"  ! {vid}: {str(e)[:120]}")
    print(f"done — {fixed}/{len(videos)} updated")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Trend miner — metadata-only YouTube search via yt-dlp (no API key, nothing
downloaded). Finds the highest-view Shorts per niche query, scores by views/day,
and writes trending_topics.json: fuel for the video engine to RECREATE topics
with our own scripts + licensed B-roll. We never re-upload third-party video.

Usage:  python scripts/find_trending.py            # all queries, top 3 each
        python scripts/find_trending.py --fast     # skip per-video date fetch

Output: trending_topics.json (sorted by views_per_day desc)
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp

# niche queries: affiliate verticals + requested content formats
QUERIES = [
    # existing affiliate programs
    "seo tools tutorial shorts",
    "web hosting explained shorts",
    "cloud hosting developers shorts",
    # requested formats
    "seo secrets shorts",
    "make money online story shorts",
    "diy marketing automation shorts",
    "ai side hustle shorts",
    "passive income update shorts",
    "newsletter growth shorts",
    "free ebook lead magnet shorts",
    # tech / AI / tips verticals
    "tech explained shorts",
    "new tech gadgets shorts",
    "ai tools you need shorts",
    "ai news update shorts",
    "chatgpt tips shorts",
    "productivity tips shorts",
    "tech tips tricks shorts",
    "coding tips shorts",
]
PER_QUERY = 3          # detail-fetch this many top hits per query
SEARCH_DEPTH = 25      # flat-search this many results per query
MIN_S, MAX_S = 12, 150  # plausible Shorts duration window


def flat_search(query: str) -> list[dict]:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
            "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{SEARCH_DEPTH}:{query}", download=False)
    out = []
    for e in (info or {}).get("entries") or []:
        views, dur = e.get("view_count"), e.get("duration")
        if not views or not dur or not (MIN_S <= dur <= MAX_S):
            continue
        out.append({"id": e.get("id"), "title": e.get("title") or "",
                    "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                    "channel": e.get("channel") or e.get("uploader") or "",
                    "views": views, "duration": dur})
    return sorted(out, key=lambda x: x["views"], reverse=True)


def add_age(video: dict) -> dict:
    """Fetch upload_date for one video → views/day score. Fails soft."""
    try:
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video["url"], download=False)
        up = info.get("upload_date")  # YYYYMMDD
        if up:
            age = max((datetime.now(timezone.utc)
                       - datetime.strptime(up, "%Y%m%d").replace(tzinfo=timezone.utc)).days, 1)
            video["age_days"] = age
            video["views_per_day"] = round(video["views"] / age)
    except Exception as e:
        print(f"   ! detail fetch failed ({str(e)[:60]})")
    video.setdefault("age_days", None)
    video.setdefault("views_per_day", video["views"] // 365)  # conservative fallback
    return video


def main() -> None:
    fast = "--fast" in sys.argv
    results = []
    for q in QUERIES:
        print(f"* {q}")
        try:
            top = flat_search(q)[:PER_QUERY]
        except Exception as e:
            print(f"   ! search failed: {str(e)[:80]}")
            continue
        for v in top:
            v["query"] = q
            if not fast:
                v = add_age(v)
                time.sleep(1)  # be polite
            else:
                v["age_days"] = None
                v["views_per_day"] = v["views"] // 365
            print(f"   {v['views']:>10,} views  {v['title'][:55]}")
            results.append(v)
    results.sort(key=lambda x: x["views_per_day"], reverse=True)
    Path("trending_topics.json").write_text(json.dumps(results, indent=2))
    print(f"\nok {len(results)} trending topics -> trending_topics.json")
    if not results:
        sys.exit(1)


if __name__ == "__main__":
    main()

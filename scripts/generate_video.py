#!/usr/bin/env python3
"""
EAOS video generation script — runs in GitHub Actions after daily-content publish.
Generates a faceless vertical video from the latest article topic and posts to
configured video/social platforms. Falls back gracefully if ffmpeg or platform
credentials are unavailable.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from runtime.eaos.video_engine import UltimateVideoEngine
from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost

TOPIC = os.getenv("ARTICLE_TOPIC", "Best AI Tools for Passive Income in 2026")
CANONICAL_URL = os.getenv("CANONICAL_URL", "https://www.alreadyherellc.com/content")
PUBLIC_CONTENT_BASE = os.getenv("PUBLIC_CONTENT_BASE", "https://www.alreadyherellc.com/content").rstrip("/")
GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_VIDEO_DIR = os.getenv("GITHUB_VIDEO_DIR", "assets/videos").strip().strip("/")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", value.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:70] or "profitengine-video"


def _upload_video_to_content_repo(video_path: str) -> Optional[str]:
    """Publish the generated MP4 to the content repo so Instagram can ingest it."""
    if not GH_TOKEN:
        print("[Video] GITHUB_CONTENT_TOKEN missing — Instagram public video URL unavailable")
        return None
    if not os.path.exists(video_path) or os.path.getsize(video_path) < 100:
        print("[Video] Video file missing/empty — upload skipped")
        return None

    filename = f"{int(time.time())}-{_slugify(TOPIC)}.mp4"
    repo_path = f"{GH_VIDEO_DIR}/{filename}"
    api_url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/contents/{repo_path}"

    with open(video_path, "rb") as vf:
        encoded = base64.b64encode(vf.read()).decode("ascii")

    payload = json.dumps({
        "message": f"Add generated video: {TOPIC[:80]}",
        "content": encoded,
        "branch": GH_BRANCH,
    }).encode()

    req = urllib.request.Request(
        api_url,
        data=payload,
        method="PUT",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "ProfitEngineV5-VideoPublisher",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status not in {200, 201}:
                print(f"[Video] Unexpected GitHub upload status: {resp.status}")
                return None
    except urllib.error.HTTPError as exc:
        print(f"[Video] GitHub video upload failed: HTTP {exc.code} {exc.read()[:240]!r}")
        return None
    except Exception as exc:
        print(f"[Video] GitHub video upload failed: {exc}")
        return None

    public_url = f"{PUBLIC_CONTENT_BASE}/{repo_path}"
    print(f"[Video] Public video URL ready: {public_url}")
    return public_url


async def main() -> None:
    engine = UltimateVideoEngine()
    print(f"[Video] Generating video for: {TOPIC}")

    body = (
        f"{TOPIC}. "
        "Artificial intelligence is transforming how small businesses create leverage. "
        "One article can become a video, a product idea, an affiliate campaign, and a sales asset. "
        "Faceless video systems can promote useful tools around the clock. "
        "Digital products, affiliate offers, Etsy listings, and automation services can all work together. "
        "The future of passive income is already here. "
        "Already Here LLC builds and ships these systems so you don't have to. "
        "Visit alreadyherellc.com to learn more."
    )

    video_path = await engine.produce_article_video(
        title=TOPIC,
        body=body,
        canonical_url=CANONICAL_URL,
    )

    if not video_path or not os.path.exists(video_path):
        print("[Video] No video produced — ffmpeg may not be available")
        return

    print(f"[Video] Master ready: {video_path}")
    public_video_url = _upload_video_to_content_repo(video_path)

    tiktok_token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    instagram_ready = bool(os.getenv("IG_USER_ID", "") and os.getenv("FB_PAGE_ACCESS_TOKEN", "") and public_video_url)
    youtube_ready = all([
        os.getenv("YOUTUBE_CLIENT_ID", ""),
        os.getenv("YOUTUBE_CLIENT_SECRET", ""),
        os.getenv("YOUTUBE_REFRESH_TOKEN", ""),
    ])

    if not any([tiktok_token, telegram_token, youtube_ready, instagram_ready]):
        print("[Video] No video/social credentials — video saved as artifact only")
        return

    social = ProductionSocialEngine()
    caption = f"{TOPIC}\n\n{CANONICAL_URL}\n\n#ProfitEngine #PassiveIncome #AITools #AlreadyHereLLC"

    if tiktok_token:
        await social.publish(SocialPost(None, "TIKTOK", caption, media_path=video_path))
    else:
        print("[Video] TikTok credentials missing — skip")

    if youtube_ready:
        await social.publish(SocialPost(
            None,
            "YOUTUBE",
            TOPIC[:100],
            media_path=video_path,
            extra={
                "description": f"{TOPIC}\n\n{CANONICAL_URL}\n\n{caption}",
                "tags": ["ProfitEngine", "PassiveIncome", "AITools", "AlreadyHereLLC"],
            },
        ))
    else:
        print("[Video] YouTube credentials missing — skip")

    if instagram_ready:
        await social.publish(SocialPost(
            None,
            "INSTAGRAM",
            caption,
            media_path=video_path,
            extra={"video_url": public_video_url},
        ))
    else:
        print("[Video] Instagram credentials or public video URL missing — skip")

    if telegram_token:
        await social.publish(SocialPost(None, "TELEGRAM", f"New video: {caption}\n\nVideo: {public_video_url or video_path}"))


if __name__ == "__main__":
    asyncio.run(main())

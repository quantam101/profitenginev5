#!/usr/bin/env python3
"""
ProfitEngine video publisher — deterministic end-to-end faceless video pipeline.

Pipeline:
1. Build branded 9:16 slide images from the article topic.
2. Render one guaranteed MP4 with FFmpeg.
3. Validate real video output by file size.
4. Upload MP4 to the public content repo for browser/Instagram access.
5. Post to configured social platforms: TikTok, YouTube, Instagram, Telegram,
   Facebook, LinkedIn, Reddit, and X/Twitter where credentials exist.
6. Write a machine-readable run report for verification.

The article/content publisher is intentionally separate. Video errors are explicit,
logged, and fail the video job when VIDEO_STRICT=true.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from typing import Iterable, Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageFont

from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost

TOPIC = os.getenv("ARTICLE_TOPIC", "Best AI Tools for Passive Income in 2026").strip() or "Best AI Tools for Passive Income in 2026"
CANONICAL_URL = os.getenv("CANONICAL_URL", "https://www.alreadyherellc.com/content").strip()
PUBLIC_CONTENT_BASE = os.getenv("PUBLIC_CONTENT_BASE", "https://www.alreadyherellc.com/content").rstrip("/")
VIDEO_ROOT = pathlib.Path(os.getenv("EAOS_VIDEO_ROOT", "./datacenter/video_pipeline"))
VIDEO_STRICT = os.getenv("VIDEO_STRICT", "true").lower() == "true"
MIN_VIDEO_BYTES = int(os.getenv("MIN_VIDEO_BYTES", "250000"))
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
SECONDS_PER_SLIDE = int(os.getenv("SECONDS_PER_SLIDE", "5"))

GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_VIDEO_DIR = os.getenv("GITHUB_VIDEO_DIR", "assets/videos").strip().strip("/")

SLIDES_DIR = VIDEO_ROOT / "slides"
OUTPUT_DIR = VIDEO_ROOT / "distribution_masters"
LOG_DIR = VIDEO_ROOT / "logs"
REPORT_PATH = LOG_DIR / "video_publish_report.json"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", value.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:70] or "profitengine-video"


def _ensure_dirs() -> None:
    for path in (SLIDES_DIR, OUTPUT_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def _ffmpeg_path() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _verify_ffmpeg() -> None:
    ffmpeg = _ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=True,
        )
        first = (result.stdout or result.stderr).splitlines()[0]
        print(f"[Video] FFmpeg available: {first}")
    except Exception as exc:
        raise RuntimeError(f"ffmpeg is not available or not executable: {exc}") from exc


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _wrapped_lines(text: str, width: int) -> list[str]:
    return textwrap.wrap(re.sub(r"\s+", " ", text).strip(), width=width) or [text[:width]]


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    font: ImageFont.ImageFont,
    y: int,
    fill: tuple[int, int, int],
) -> int:
    y_cursor = y
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        line_w = box[2] - box[0]
        line_h = box[3] - box[1]
        draw.text(((VIDEO_WIDTH - line_w) // 2, y_cursor), line, font=font, fill=fill)
        y_cursor += line_h + 18
    return y_cursor


def _make_slide(path: pathlib.Path, headline: str, body: str, footer: str, index: int, total: int) -> None:
    # Deterministic dark vertical background. No external assets required.
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 14, 24))
    pixels = img.load()
    for y in range(VIDEO_HEIGHT):
        r = int(10 + (y / VIDEO_HEIGHT) * 24)
        g = int(14 + (y / VIDEO_HEIGHT) * 34)
        b = int(24 + (y / VIDEO_HEIGHT) * 52)
        for x in range(VIDEO_WIDTH):
            accent = 6 if (x + y) % 53 == 0 else 0
            pixels[x, y] = (min(r + accent, 255), min(g + accent, 255), min(b + accent, 255))

    draw = ImageDraw.Draw(img)
    title_font = _load_font(68)
    body_font = _load_font(44)
    small_font = _load_font(31)
    label_font = _load_font(36)

    draw.rounded_rectangle((70, 80, 1010, 160), radius=18, fill=(20, 31, 48), outline=(74, 144, 226), width=2)
    brand = "ALREADY HERE LLC  •  PROFITENGINE V5"
    brand_box = draw.textbbox((0, 0), brand, font=label_font)
    draw.text(((VIDEO_WIDTH - (brand_box[2] - brand_box[0])) // 2, 101), brand, font=label_font, fill=(220, 235, 255))

    y = 350
    y = _draw_centered_lines(draw, _wrapped_lines(headline, 18), title_font, y, (255, 255, 255))
    y += 70
    _draw_centered_lines(draw, _wrapped_lines(body, 30), body_font, y, (220, 231, 242))

    cta = "Read the full article → alreadyherellc.com/content"
    cta_box = draw.textbbox((0, 0), cta, font=small_font)
    draw.rounded_rectangle((90, 1545, 990, 1635), radius=18, fill=(16, 124, 184), outline=(120, 210, 255), width=2)
    draw.text(((VIDEO_WIDTH - (cta_box[2] - cta_box[0])) // 2, 1572), cta, font=small_font, fill=(255, 255, 255))

    progress = f"{index}/{total}"
    draw.text((80, 1745), footer[:70], font=small_font, fill=(185, 205, 225))
    draw.text((915, 1745), progress, font=small_font, fill=(185, 205, 225))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=95)


def _video_script() -> list[tuple[str, str]]:
    clean_topic = re.sub(r"\s+", " ", TOPIC).strip()
    return [
        (clean_topic, "Turn one article into a video, offer, affiliate campaign, and reusable sales asset."),
        ("Faceless video automation", "Create short vertical videos without a camera crew, studio, or manual edit session."),
        ("Affiliate-ready content", "Every video can drive traffic back to monetized articles, tools, and digital products."),
        ("Small business leverage", "Already Here LLC turns repeatable workflows into automated marketing infrastructure."),
        ("24/7 distribution", "Publish to YouTube, TikTok, Instagram, Telegram, and public content hosting when credentials are active."),
        ("Next action", "Use the article, video, product idea, and social post together instead of leaving content unused."),
    ]


def _build_slides() -> list[pathlib.Path]:
    slides: list[pathlib.Path] = []
    items = _video_script()
    total = len(items)
    for idx, (headline, body) in enumerate(items, start=1):
        slide_path = SLIDES_DIR / f"slide_{idx:03d}.png"
        _make_slide(slide_path, headline, body, "AI automation • affiliate marketing • digital products", idx, total)
        slides.append(slide_path)
    print(f"[Video] Slides ready: {len(slides)}")
    return slides


def _concat_file(slides: list[pathlib.Path]) -> pathlib.Path:
    concat = VIDEO_ROOT / "slides_concat.txt"
    with open(concat, "w", encoding="utf-8") as f:
        for slide in slides:
            f.write(f"file '{slide.resolve().as_posix()}'\n")
            f.write(f"duration {SECONDS_PER_SLIDE}\n")
        # FFmpeg concat duration behavior requires the final frame repeated.
        f.write(f"file '{slides[-1].resolve().as_posix()}'\n")
    return concat


def _run_ffmpeg(args: list[str], timeout: int = 300) -> tuple[bool, str]:
    cmd = [_ffmpeg_path(), "-y", *args]
    print("[Video] FFmpeg command:", " ".join(cmd[:16]), "...")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    stderr = proc.stderr or ""
    if proc.returncode != 0:
        print(f"[Video][FFmpeg] Non-zero exit {proc.returncode}: {stderr[-1600:]}")
        return False, stderr
    return True, stderr


def _render_direct_mp4() -> pathlib.Path:
    _ensure_dirs()
    _verify_ffmpeg()
    slides = _build_slides()
    concat = _concat_file(slides)
    output = OUTPUT_DIR / f"{_slugify(TOPIC)}.mp4"
    total_duration = max(SECONDS_PER_SLIDE * len(slides), 15)

    args = [
        "-f", "concat", "-safe", "0", "-i", str(concat.resolve()),
        "-f", "lavfi", "-t", str(total_duration), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-map", "0:v:0", "-map", "1:a:0",
        "-r", "30",
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output.resolve()),
    ]
    ok, _ = _run_ffmpeg(args, timeout=420)
    if not ok:
        raise RuntimeError("direct slide-to-MP4 render failed")

    if not output.exists():
        raise RuntimeError(f"video output not found: {output}")
    size = output.stat().st_size
    print(f"[Video] Master ready: {output.resolve()} ({size} bytes)")
    if size < MIN_VIDEO_BYTES:
        raise RuntimeError(f"video output too small for production: {size} bytes < {MIN_VIDEO_BYTES}")
    return output


def _upload_video_to_content_repo(video_path: pathlib.Path) -> Optional[str]:
    """Publish the generated MP4 to the content repo so Instagram can ingest it."""
    if not GH_TOKEN:
        print("[Video] GITHUB_CONTENT_TOKEN missing — public video URL unavailable")
        return None
    if not video_path.exists() or video_path.stat().st_size < MIN_VIDEO_BYTES:
        print("[Video] Video file missing/too small — upload skipped")
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            if resp.status not in {200, 201}:
                print(f"[Video] Unexpected GitHub upload status: {resp.status}")
                return None
    except urllib.error.HTTPError as exc:
        print(f"[Video] GitHub video upload failed: HTTP {exc.code} {exc.read()[:300]!r}")
        return None
    except Exception as exc:
        print(f"[Video] GitHub video upload failed: {exc}")
        return None

    public_url = f"{PUBLIC_CONTENT_BASE}/{repo_path}"
    print(f"[Video] Public video URL ready: {public_url}")
    return public_url


def _credential_status(public_video_url: Optional[str]) -> dict[str, bool]:
    return {
        "tiktok": bool(os.getenv("TIKTOK_ACCESS_TOKEN", "")),
        "youtube": all([
            os.getenv("YOUTUBE_CLIENT_ID", ""),
            os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            os.getenv("YOUTUBE_REFRESH_TOKEN", ""),
        ]),
        "instagram": bool(os.getenv("IG_USER_ID", "") and os.getenv("FB_PAGE_ACCESS_TOKEN", "") and public_video_url),
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN", "") and os.getenv("TELEGRAM_CHAT_ID", "")),
        "facebook": bool(os.getenv("FB_PAGE_ID", "") and os.getenv("FB_PAGE_ACCESS_TOKEN", "")),
        "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN", "") and os.getenv("LINKEDIN_PERSON_URN", "")),
        "reddit": bool(os.getenv("REDDIT_CLIENT_ID", "") and os.getenv("REDDIT_CLIENT_SECRET", "") and os.getenv("REDDIT_USERNAME", "") and os.getenv("REDDIT_PASSWORD", "")),
        "x": bool(os.getenv("TWITTER_API_KEY", "") and os.getenv("TWITTER_API_SECRET", "") and os.getenv("TWITTER_ACCESS_TOKEN", "") and os.getenv("TWITTER_ACCESS_SECRET", "")),
    }


async def _publish_socials(video_path: pathlib.Path, public_video_url: Optional[str]) -> dict[str, str]:
    social = ProductionSocialEngine()
    caption = f"{TOPIC}\n\n{CANONICAL_URL}\n\n#ProfitEngine #PassiveIncome #AITools #AlreadyHereLLC"
    link_caption = f"New ProfitEngine video: {TOPIC}\n\nWatch: {public_video_url or video_path}\nRead: {CANONICAL_URL}\n\n#ProfitEngine #AlreadyHereLLC"
    creds = _credential_status(public_video_url)
    results: dict[str, str] = {}

    async def attempt(platform: str, post: SocialPost, ready: bool) -> None:
        if not ready:
            print(f"[Video][{platform}] credentials missing — skip")
            results[platform] = "skipped_missing_credentials"
            return
        print(f"[Video][{platform}] posting started")
        try:
            await social.publish(post)
            print(f"[Video][{platform}] post attempt complete — inspect platform-specific log lines for posted/cached/failed status")
            results[platform] = "attempted"
        except Exception as exc:
            print(f"[Video][{platform}] post raised exception: {exc}")
            results[platform] = f"exception:{exc}"

    await attempt("TikTok", SocialPost(None, "TIKTOK", caption, media_path=str(video_path)), creds["tiktok"])
    await attempt(
        "YouTube",
        SocialPost(
            None,
            "YOUTUBE",
            TOPIC[:100],
            media_path=str(video_path),
            extra={
                "description": f"{TOPIC}\n\n{CANONICAL_URL}\n\n{caption}",
                "tags": ["ProfitEngine", "PassiveIncome", "AITools", "AlreadyHereLLC"],
            },
        ),
        creds["youtube"],
    )
    await attempt(
        "Instagram",
        SocialPost(None, "INSTAGRAM", caption, media_path=str(video_path), extra={"video_url": public_video_url or ""}),
        creds["instagram"],
    )
    await attempt("Telegram", SocialPost(None, "TELEGRAM", link_caption), creds["telegram"])
    await attempt("Facebook", SocialPost(None, "FACEBOOK", link_caption, extra={"url": public_video_url or CANONICAL_URL}), creds["facebook"])
    await attempt("LinkedIn", SocialPost(None, "LINKEDIN", link_caption), creds["linkedin"])
    await attempt("Reddit", SocialPost(None, "REDDIT", TOPIC[:300], extra={"url": public_video_url or CANONICAL_URL, "subreddit": "passive_income"}), creds["reddit"])
    await attempt("X", SocialPost(None, "X", link_caption[:280]), creds["x"])

    return results


def _write_report(report: dict) -> None:
    _ensure_dirs()
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[Video] Report written: {REPORT_PATH}")


async def main() -> None:
    report: dict = {
        "topic": TOPIC,
        "canonical_url": CANONICAL_URL,
        "video_path": None,
        "video_size_bytes": 0,
        "public_video_url": None,
        "social_results": {},
        "status": "started",
    }
    print(f"[Video] Generating deterministic faceless video for: {TOPIC}")

    try:
        video_path = _render_direct_mp4()
        report["video_path"] = str(video_path)
        report["video_size_bytes"] = video_path.stat().st_size
        public_video_url = _upload_video_to_content_repo(video_path)
        report["public_video_url"] = public_video_url
        social_results = await _publish_socials(video_path, public_video_url)
        report["social_results"] = social_results
        report["status"] = "complete"
        print("[Video] Pipeline complete")
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        print(f"[Video] Pipeline failed: {exc}")
        _write_report(report)
        if VIDEO_STRICT:
            raise
        return

    _write_report(report)


if __name__ == "__main__":
    asyncio.run(main())

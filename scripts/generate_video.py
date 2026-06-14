#!/usr/bin/env python3
"""
ProfitEngine video publisher.

This is a production path, not a fake artifact:
- builds a real vertical MP4 with FFmpeg
- writes reusable written assets from the same topic
- writes SRT/VTT subtitles and a capability manifest
- optionally attempts Hugging Face image scenes, then falls back locally
- uploads the MP4 to the public content repo
- posts only to platforms with configured credentials
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
import time
import urllib.error
import urllib.request
from typing import Iterable, Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageFont

from runtime.eaos.content_asset_factory import ContentAssetPack
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

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
ENABLE_HF_IMAGE_SCENES = os.getenv("ENABLE_HF_IMAGE_SCENES", "true").lower() in {"1", "true", "yes", "on"}
MAX_HF_IMAGE_SCENES = int(os.getenv("MAX_HF_IMAGE_SCENES", "2"))
HF_IMAGE_API = os.getenv(
    "HF_IMAGE_API",
    "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
).strip()

GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_VIDEO_DIR = os.getenv("GITHUB_VIDEO_DIR", "assets/videos").strip().strip("/")

SLIDES_DIR = VIDEO_ROOT / "slides"
IMAGE_SCENES_DIR = VIDEO_ROOT / "ai_scenes"
OUTPUT_DIR = VIDEO_ROOT / "distribution_masters"
LOG_DIR = VIDEO_ROOT / "logs"
ASSET_DIR = VIDEO_ROOT / "asset_pack"
REPORT_PATH = LOG_DIR / "video_publish_report.json"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", value.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:70] or "profitengine-video"


def _ensure_dirs() -> None:
    for path in (SLIDES_DIR, IMAGE_SCENES_DIR, OUTPUT_DIR, LOG_DIR, ASSET_DIR):
        path.mkdir(parents=True, exist_ok=True)


def _asset_pack() -> ContentAssetPack:
    return ContentAssetPack(topic=TOPIC, canonical_url=CANONICAL_URL, output_dir=ASSET_DIR)


def _ffmpeg_path() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _has_ffmpeg() -> bool:
    return bool(shutil.which("ffmpeg"))


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
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return [""]
    words = cleaned.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        next_line = " ".join([*current, word])
        if len(next_line) <= width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    font: ImageFont.ImageFont,
    y: int,
    fill: tuple[int, int, int],
    gap: int = 18,
) -> int:
    y_cursor = y
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        line_w = box[2] - box[0]
        line_h = box[3] - box[1]
        draw.text(((VIDEO_WIDTH - line_w) // 2, y_cursor), line, font=font, fill=fill)
        y_cursor += line_h + gap
    return y_cursor


def _gradient_background(index: int) -> Image.Image:
    palette = [
        ((7, 18, 29), (22, 92, 125)),
        ((20, 16, 34), (84, 55, 126)),
        ((8, 28, 22), (52, 118, 86)),
        ((30, 22, 12), (120, 84, 38)),
        ((18, 20, 33), (50, 92, 160)),
        ((10, 29, 36), (48, 138, 148)),
    ]
    top, bottom = palette[(index - 1) % len(palette)]
    strip = Image.new("RGB", (1, VIDEO_HEIGHT), top)
    pixels = strip.load()
    for y in range(VIDEO_HEIGHT):
        mix = y / max(VIDEO_HEIGHT - 1, 1)
        pixels[0, y] = tuple(int(top[c] * (1 - mix) + bottom[c] * mix) for c in range(3))
    img = strip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")
    for offset in range(-VIDEO_HEIGHT, VIDEO_WIDTH, 220):
        draw.line((offset, VIDEO_HEIGHT, offset + VIDEO_HEIGHT, 0), fill=(255, 255, 255, 20), width=3)
    return img


def _fit_cover(image: Image.Image) -> Image.Image:
    source = image.convert("RGB")
    scale = max(VIDEO_WIDTH / source.width, VIDEO_HEIGHT / source.height)
    resized = source.resize((int(source.width * scale), int(source.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - VIDEO_WIDTH) // 2
    top = (resized.height - VIDEO_HEIGHT) // 2
    return resized.crop((left, top, left + VIDEO_WIDTH, top + VIDEO_HEIGHT))


def _try_hf_image_scene(prompt: str, index: int) -> Optional[pathlib.Path]:
    if not HF_TOKEN or not ENABLE_HF_IMAGE_SCENES or index > MAX_HF_IMAGE_SCENES:
        return None
    output = IMAGE_SCENES_DIR / f"scene_{index:03d}.png"
    payload = json.dumps({
        "inputs": (
            "vertical 9:16 editorial marketing image, no text, no logo, no watermark, "
            f"professional lighting, useful business automation visual, {prompt}"
        ),
        "parameters": {"width": 1024, "height": 1792},
    }).encode("utf-8")
    req = urllib.request.Request(
        HF_IMAGE_API,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "image/png",
            "User-Agent": "ProfitEngineV5-VideoPublisher",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()
        if "image" not in content_type.lower() or len(data) < 10_000:
            print(f"[Video][HFImage] scene {index} skipped: non-image response")
            return None
        output.write_bytes(data)
        with Image.open(output) as img:
            _fit_cover(img).save(output, quality=92)
        print(f"[Video][HFImage] scene {index} generated: {output}")
        return output
    except urllib.error.HTTPError as exc:
        print(f"[Video][HFImage] scene {index} HTTP {exc.code}; deterministic fallback")
    except Exception as exc:
        print(f"[Video][HFImage] scene {index} unavailable: {exc}; deterministic fallback")
    return None


def _make_slide(path: pathlib.Path, scene: dict[str, str], index: int, total: int) -> None:
    scene_image = _try_hf_image_scene(scene["visual_prompt"], index)
    if scene_image:
        with Image.open(scene_image) as source:
            img = _fit_cover(source)
        overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rectangle((0, 0, VIDEO_WIDTH, VIDEO_HEIGHT), fill=(4, 8, 15, 125))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    else:
        img = _gradient_background(index)

    draw = ImageDraw.Draw(img)
    title_font = _load_font(68)
    body_font = _load_font(44)
    small_font = _load_font(31)
    label_font = _load_font(36)
    chip_font = _load_font(28)

    draw.rounded_rectangle((70, 80, 1010, 160), radius=18, fill=(20, 31, 48), outline=(74, 144, 226), width=2)
    brand = "ALREADY HERE LLC  |  PROFITENGINE V5"
    brand_box = draw.textbbox((0, 0), brand, font=label_font)
    draw.text(((VIDEO_WIDTH - (brand_box[2] - brand_box[0])) // 2, 101), brand, font=label_font, fill=(220, 235, 255))

    draw.rounded_rectangle((78, 230, 1002, 275), radius=22, fill=(255, 255, 255), outline=(255, 255, 255), width=1)
    chip = "FACELESS AI VIDEO | BLOG TO ASSET SYSTEM"
    chip_box = draw.textbbox((0, 0), chip, font=chip_font)
    draw.text(((VIDEO_WIDTH - (chip_box[2] - chip_box[0])) // 2, 237), chip, font=chip_font, fill=(10, 24, 36))

    y = 365
    y = _draw_centered_lines(draw, _wrapped_lines(scene["headline"], 18), title_font, y, (255, 255, 255))
    y += 70
    _draw_centered_lines(draw, _wrapped_lines(scene["body"], 30), body_font, y, (220, 231, 242))

    cta = "Read the full article -> alreadyherellc.com/content"
    cta_box = draw.textbbox((0, 0), cta, font=small_font)
    draw.rounded_rectangle((90, 1545, 990, 1635), radius=18, fill=(16, 124, 184), outline=(120, 210, 255), width=2)
    draw.text(((VIDEO_WIDTH - (cta_box[2] - cta_box[0])) // 2, 1572), cta, font=small_font, fill=(255, 255, 255))

    progress = f"{index}/{total}"
    footer = "AI automation | affiliate marketing | digital products"
    draw.text((80, 1745), footer[:70], font=small_font, fill=(185, 205, 225))
    draw.text((915, 1745), progress, font=small_font, fill=(185, 205, 225))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=95)


def _video_script() -> list[dict[str, str]]:
    return _asset_pack().scene_plan()


def _build_slides() -> list[pathlib.Path]:
    slides: list[pathlib.Path] = []
    scenes = _video_script()
    total = len(scenes)
    for idx, scene in enumerate(scenes, start=1):
        slide_path = SLIDES_DIR / f"slide_{idx:03d}.png"
        _make_slide(slide_path, scene, idx, total)
        slides.append(slide_path)
    print(f"[Video] Slides ready: {len(slides)}")
    return slides


def _timestamp(seconds: int, *, webvtt: bool = False) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    sep = "." if webvtt else ","
    return f"{hours:02d}:{minutes:02d}:{sec:02d}{sep}000"


def _write_subtitles() -> dict[str, str]:
    scenes = _video_script()
    srt_lines: list[str] = []
    vtt_lines: list[str] = ["WEBVTT", ""]
    for idx, scene in enumerate(scenes, start=1):
        start = (idx - 1) * SECONDS_PER_SLIDE
        end = idx * SECONDS_PER_SLIDE
        srt_lines.extend([str(idx), f"{_timestamp(start)} --> {_timestamp(end)}", scene["body"], ""])
        vtt_lines.extend([f"{_timestamp(start, webvtt=True)} --> {_timestamp(end, webvtt=True)}", scene["body"], ""])
    srt_path = LOG_DIR / f"{_slugify(TOPIC)}.srt"
    vtt_path = LOG_DIR / f"{_slugify(TOPIC)}.vtt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")
    print(f"[Video] Subtitle sidecars ready: {srt_path}, {vtt_path}")
    return {"srt": str(srt_path), "vtt": str(vtt_path)}


def _concat_file(slides: list[pathlib.Path]) -> pathlib.Path:
    concat = VIDEO_ROOT / "slides_concat.txt"
    with open(concat, "w", encoding="utf-8") as f:
        for slide in slides:
            f.write(f"file '{slide.resolve().as_posix()}'\n")
            f.write(f"duration {SECONDS_PER_SLIDE}\n")
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
    if not GH_TOKEN:
        print("[Video] GITHUB_CONTENT_TOKEN missing - public video URL unavailable")
        return None
    if not video_path.exists() or video_path.stat().st_size < MIN_VIDEO_BYTES:
        print("[Video] Video file missing/too small - upload skipped")
        return None

    filename = f"{int(time.time())}-{_slugify(TOPIC)}.mp4"
    repo_path = f"{GH_VIDEO_DIR}/{filename}"
    api_url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/contents/{repo_path}"

    encoded = base64.b64encode(video_path.read_bytes()).decode("ascii")
    payload = json.dumps({
        "message": f"Add generated video: {TOPIC[:80]}",
        "content": encoded,
        "branch": GH_BRANCH,
    }).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=payload,
        method="PUT",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json; charset=UTF-8",
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
            print(f"[Video][{platform}] credentials missing - skip")
            results[platform] = "skipped_missing_credentials"
            return
        print(f"[Video][{platform}] posting started")
        try:
            await social.publish(post)
            print(f"[Video][{platform}] post attempt complete - inspect platform-specific log lines for posted/cached/failed status")
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
    await attempt("Instagram", SocialPost(None, "INSTAGRAM", caption, media_path=str(video_path), extra={"video_url": public_video_url or ""}), creds["instagram"])
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
        "asset_files": {},
        "subtitle_files": {},
        "capability_manifest": {},
        "video_path": None,
        "video_size_bytes": 0,
        "public_video_url": None,
        "social_results": {},
        "status": "started",
    }
    print(f"[Video] Generating optimized faceless video and asset pack for: {TOPIC}")

    try:
        _ensure_dirs()
        pack = _asset_pack()
        report["asset_files"] = pack.write_all()
        report["subtitle_files"] = _write_subtitles()
        report["capability_manifest"] = pack.capability_manifest(
            hf_token_present=bool(HF_TOKEN),
            hf_image_enabled=ENABLE_HF_IMAGE_SCENES,
            ffmpeg_present=_has_ffmpeg(),
        )
        (LOG_DIR / "capability_manifest.json").write_text(
            json.dumps(report["capability_manifest"], indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print("[Video] Asset pack ready")

        video_path = _render_direct_mp4()
        report["video_path"] = str(video_path)
        report["video_size_bytes"] = video_path.stat().st_size
        public_video_url = _upload_video_to_content_repo(video_path)
        report["public_video_url"] = public_video_url
        report["social_results"] = await _publish_socials(video_path, public_video_url)
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

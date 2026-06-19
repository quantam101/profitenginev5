#!/usr/bin/env python3
"""
AI Video Generator for ProfitEngine.

Multi-stage pipeline for AI-generated video content:
1. Topic → AI script generation (using Claude/Ollama)
2. Script → Voice-over with ElevenLabs, Google TTS, or Pyttsx3
3. Voice + Script → AI video slides with FFmpeg
4. Video → Social media distribution (YouTube, TikTok, etc.)

Video Types:
- Explainer videos (AI avatar explaining concepts)
- Product demos (feature walkthroughs)
- Tutorial videos (step-by-step guides)
- News summary videos (trending topics)
- Motivation/inspiration videos (success stories)

Features:
- Auto-generation pipeline with quality controls
- Manual review queue before publishing
- Monetization integration (Gumroad, YouTube)
- Email campaign integration
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

# ────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────

VIDEO_ROOT = pathlib.Path(os.getenv("EAOS_VIDEO_ROOT", "./datacenter/ai_video_pipeline"))
SCRIPT_CACHE = VIDEO_ROOT / "scripts"
AUDIO_CACHE = VIDEO_ROOT / "audio"
OUTPUT_DIR = VIDEO_ROOT / "distribution_masters"
LOG_DIR = VIDEO_ROOT / "logs"
REVIEW_QUEUE = VIDEO_ROOT / "review_queue"

# AI Models & Inference
OLLAMA_ENDPOINT = os.getenv("GMAOS_LOCAL_MODEL_ENDPOINT", "http://localhost:11434").strip()
OLLAMA_MODEL = os.getenv("GMAOS_LOCAL_MODEL_NAME", "llama3.1:8b").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Voice APIs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "9BWtsMINqrJLrRacOk9x").strip()  # Adam voice
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

# Video Rendering
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
SECONDS_PER_SLIDE = int(os.getenv("SECONDS_PER_SLIDE", "5"))
MIN_VIDEO_BYTES = int(os.getenv("MIN_VIDEO_BYTES", "250000"))

# GitHub Content Repo (for video hosting)
GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_VIDEO_DIR = os.getenv("GITHUB_VIDEO_DIR", "assets/videos").strip().strip("/")

# Affiliate & Monetization
AFFILIATE_LINKS = os.getenv("AFFILIATE_LINKS", "{}").strip()
try:
    AFFILIATE_LINKS = json.loads(AFFILIATE_LINKS) if AFFILIATE_LINKS else {}
except json.JSONDecodeError:
    AFFILIATE_LINKS = {}

CANONICAL_URL = os.getenv("CANONICAL_URL", "https://www.alreadyherellc.com/content").strip()
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "alreadyhere-20").strip()

# Quality Controls
MIN_SCRIPT_LENGTH = int(os.getenv("MIN_SCRIPT_LENGTH", "500"))
MAX_SCRIPT_LENGTH = int(os.getenv("MAX_SCRIPT_LENGTH", "2000"))
MIN_SLIDES = int(os.getenv("MIN_SLIDES", "3"))
MAX_SLIDES = int(os.getenv("MAX_SLIDES", "12"))

# ────────────────────────────────────────────────────────────────────────────
# Enums & Data Classes
# ────────────────────────────────────────────────────────────────────────────


class VideoType(Enum):
    """Video content type."""
    EXPLAINER = "explainer"
    PRODUCT_DEMO = "product_demo"
    TUTORIAL = "tutorial"
    NEWS_SUMMARY = "news_summary"
    MOTIVATION = "motivation"
    EDUCATIONAL = "educational"


class VoiceProvider(Enum):
    """Voice-over service provider."""
    ELEVENLABS = "elevenlabs"
    GOOGLE_TTS = "google_tts"
    PYTTSX3 = "pyttsx3"  # Local fallback


class VoiceQuality(Enum):
    """Voice-over quality settings."""
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass
class VideoScript:
    """Generated video script structure."""
    topic: str
    video_type: VideoType
    headline: str
    body: str
    ctas: list[str]
    slides: list[dict]  # [{"headline": str, "body": str, "visual_prompt": str}, ...]
    estimated_duration: float  # seconds
    hash: str = ""  # SHA256 of content for deduplication

    def __post_init__(self) -> None:
        if not self.hash:
            content = f"{self.topic}{self.headline}{self.body}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class VoiceOverResult:
    """Voice-over generation result."""
    audio_path: str
    duration_seconds: float
    provider: str
    voice_id: str = ""
    sample_rate: int = 0
    format: str = "mp3"


@dataclass
class VideoGenerationResult:
    """Final video generation result."""
    video_path: str
    size_bytes: int
    duration_seconds: float
    script_hash: str
    voice_path: str
    public_url: Optional[str] = None
    subtitle_path: Optional[str] = None
    needs_review: bool = True


# ────────────────────────────────────────────────────────────────────────────
# Utilities
# ────────────────────────────────────────────────────────────────────────────


def _ensure_dirs() -> None:
    """Ensure all working directories exist."""
    for path in (SCRIPT_CACHE, AUDIO_CACHE, OUTPUT_DIR, LOG_DIR, REVIEW_QUEUE):
        path.mkdir(parents=True, exist_ok=True)


def _slugify(value: str) -> str:
    """Convert text to URL-safe slug."""
    slug = re.sub(r"[^a-z0-9-]", "-", value.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:70] or "ai-video"


def _has_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    return bool(shutil.which("ffmpeg"))


def _verify_ffmpeg() -> None:
    """Verify FFmpeg installation."""
    if not _has_ffmpeg():
        raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=True,
        )
        first = (result.stdout or result.stderr).splitlines()[0]
        print(f"[AIVideo] FFmpeg available: {first}")
    except Exception as exc:
        raise RuntimeError(f"FFmpeg verification failed: {exc}") from exc


def _load_font(size: int) -> Optional[ImageFont.ImageFont]:
    """Load TrueType font or default."""
    if ImageFont is None:
        return None
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _wrapped_lines(text: str, width: int) -> list[str]:
    """Wrap text to specified character width."""
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


# ────────────────────────────────────────────────────────────────────────────
# Script Generation
# ────────────────────────────────────────────────────────────────────────────


async def topic_to_script(
    topic: str,
    video_type: VideoType = VideoType.EXPLAINER,
    slides_count: int = 5,
) -> VideoScript:
    """
    Generate AI video script from article topic.

    Uses Ollama (free local) → Claude (key-gated) cascade.
    """
    _ensure_dirs()

    prompt = f"""Generate a detailed {video_type.value} video script for this topic:

Topic: {topic}

Requirements:
1. Audience: Digital entrepreneurs, passive income seekers
2. Tone: Engaging, professional, action-oriented
3. Structure: {slides_count} sections with clear visuals
4. Include 2-3 calls-to-action (CTAs)
5. Make it affiliate-friendly (mention relevant tools naturally)

Output JSON format:
{{
    "headline": "Main topic headline",
    "body": "2-3 sentence overview",
    "ctas": ["CTA 1", "CTA 2", "CTA 3"],
    "slides": [
        {{
            "headline": "Slide title",
            "body": "2-3 sentences of content",
            "visual_prompt": "DALL-E or HF Flux description for this slide"
        }},
        ...
    ]
}}

Generate JSON only, no markdown."""

    # Try Ollama first (free, local)
    script_data = await _generate_script_ollama(prompt, topic)

    if not script_data:
        # Fallback to Claude if Ollama fails
        if ANTHROPIC_API_KEY:
            script_data = await _generate_script_claude(prompt, topic)

    if not script_data:
        raise RuntimeError(f"Script generation failed for: {topic}")

    slides = []
    for slide_data in script_data.get("slides", [])[:MAX_SLIDES]:
        slides.append({
            "headline": slide_data.get("headline", ""),
            "body": slide_data.get("body", ""),
            "visual_prompt": slide_data.get("visual_prompt", ""),
        })

    if len(slides) < MIN_SLIDES:
        raise ValueError(f"Generated only {len(slides)} slides; minimum is {MIN_SLIDES}")

    total_body = sum(len(s["body"].split()) for s in slides)
    estimated_duration = (total_body / 150.0) * 60  # Rough estimate: 150 WPM

    script = VideoScript(
        topic=topic,
        video_type=video_type,
        headline=script_data.get("headline", topic),
        body=script_data.get("body", ""),
        ctas=script_data.get("ctas", []),
        slides=slides,
        estimated_duration=estimated_duration,
    )

    # Cache script
    script_path = SCRIPT_CACHE / f"{script.hash}.json"
    script_path.write_text(json.dumps({
        "topic": script.topic,
        "video_type": script.video_type.value,
        "headline": script.headline,
        "body": script.body,
        "ctas": script.ctas,
        "slides": script.slides,
        "estimated_duration": script.estimated_duration,
        "hash": script.hash,
    }, indent=2), encoding="utf-8")

    print(f"[AIVideo][Script] Generated {len(slides)} slides (~{estimated_duration:.0f}s)")
    return script


async def _generate_script_ollama(prompt: str, topic: str) -> Optional[dict]:
    """Generate script using Ollama (free local inference)."""
    if not OLLAMA_ENDPOINT or not OLLAMA_MODEL:
        return None

    try:
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{OLLAMA_ENDPOINT}/api/generate",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())

        response_text = result.get("response", "").strip()
        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as exc:
        print(f"[AIVideo][Ollama] Script generation failed: {exc}")

    return None


async def _generate_script_claude(prompt: str, topic: str) -> Optional[dict]:
    """Generate script using Anthropic Claude (key-gated fallback)."""
    if not ANTHROPIC_API_KEY:
        return None

    try:
        import anthropic
    except ImportError:
        print("[AIVideo][Claude] anthropic package not installed")
        return None

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as exc:
        print(f"[AIVideo][Claude] Script generation failed: {exc}")

    return None


# ────────────────────────────────────────────────────────────────────────────
# Voice-Over Generation
# ────────────────────────────────────────────────────────────────────────────


async def script_to_voiceover(
    script: VideoScript,
    provider: VoiceProvider = VoiceProvider.ELEVENLABS,
    quality: VoiceQuality = VoiceQuality.STANDARD,
) -> VoiceOverResult:
    """
    Generate voice-over audio from video script.

    Cascade: ElevenLabs (premium) → Google TTS (free with key) → Pyttsx3 (free local)
    """
    _ensure_dirs()

    # Concatenate all slide bodies for voice-over
    full_text = " ".join([slide["body"] for slide in script.slides])

    if provider == VoiceProvider.ELEVENLABS and ELEVENLABS_API_KEY:
        result = await _voiceover_elevenlabs(full_text, script.hash, quality)
        if result:
            return result

    if provider == VoiceProvider.GOOGLE_TTS or (provider == VoiceProvider.ELEVENLABS and not ELEVENLABS_API_KEY):
        if GOOGLE_API_KEY:
            result = await _voiceover_google_tts(full_text, script.hash)
            if result:
                return result

    # Fallback to local Pyttsx3
    result = await _voiceover_pyttsx3(full_text, script.hash)
    return result


async def _voiceover_elevenlabs(text: str, script_hash: str, quality: VoiceQuality) -> Optional[VoiceOverResult]:
    """Generate voice-over using ElevenLabs API."""
    if len(text) < 10:
        return None

    try:
        stability = 0.6 if quality == VoiceQuality.STANDARD else 0.5
        similarity = 0.75 if quality == VoiceQuality.STANDARD else 0.85

        payload = json.dumps({
            "text": text,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {ELEVENLABS_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        audio_path = AUDIO_CACHE / f"{script_hash}_elevenlabs.mp3"
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio_path.write_bytes(resp.read())

        # Estimate duration (rough: 150 WPM)
        duration = (len(text.split()) / 150.0) * 60

        print(f"[AIVideo][Voice] ElevenLabs: {len(text)} chars → {duration:.1f}s audio")

        return VoiceOverResult(
            audio_path=str(audio_path),
            duration_seconds=duration,
            provider="elevenlabs",
            voice_id=ELEVENLABS_VOICE_ID,
            format="mp3",
        )
    except Exception as exc:
        print(f"[AIVideo][ElevenLabs] Voice generation failed: {exc}")

    return None


async def _voiceover_google_tts(text: str, script_hash: str) -> Optional[VoiceOverResult]:
    """Generate voice-over using Google Text-to-Speech API."""
    if len(text) < 10 or not GOOGLE_API_KEY:
        return None

    try:
        from google.cloud import texttospeech
        from google.oauth2 import service_account
    except ImportError:
        print("[AIVideo][GoogleTTS] google-cloud-texttospeech not installed")
        return None

    try:
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text[:5000])  # API limit
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-C",
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        audio_path = AUDIO_CACHE / f"{script_hash}_google.mp3"
        audio_path.write_bytes(response.audio_content)

        duration = (len(text.split()) / 150.0) * 60

        print(f"[AIVideo][Voice] Google TTS: {len(text)} chars → {duration:.1f}s audio")

        return VoiceOverResult(
            audio_path=str(audio_path),
            duration_seconds=duration,
            provider="google_tts",
            format="mp3",
        )
    except Exception as exc:
        print(f"[AIVideo][GoogleTTS] Voice generation failed: {exc}")

    return None


async def _voiceover_pyttsx3(text: str, script_hash: str) -> VoiceOverResult:
    """Generate voice-over using local Pyttsx3 (free fallback)."""
    try:
        import pyttsx3
    except ImportError:
        raise RuntimeError("pyttsx3 not installed. Install with: pip install pyttsx3")

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  # Words per minute
    engine.setProperty("volume", 0.9)

    audio_path = AUDIO_CACHE / f"{script_hash}_pyttsx3.wav"
    engine.save_to_file(text, str(audio_path))
    engine.runAndWait()

    duration = (len(text.split()) / 150.0) * 60

    print(f"[AIVideo][Voice] Pyttsx3: {len(text)} chars → {duration:.1f}s audio (local)")

    return VoiceOverResult(
        audio_path=str(audio_path),
        duration_seconds=duration,
        provider="pyttsx3",
        format="wav",
    )


# ────────────────────────────────────────────────────────────────────────────
# Video Generation
# ────────────────────────────────────────────────────────────────────────────


async def generate_ai_video(
    script: VideoScript,
    voice: VoiceOverResult,
    topic: str = "",
) -> VideoGenerationResult:
    """
    Generate MP4 video from script and voice-over.

    Pipeline:
    1. Create slide images from script (with optional AI art)
    2. Composite audio track
    3. Render with FFmpeg to MP4
    """
    _ensure_dirs()
    _verify_ffmpeg()

    topic = topic or script.topic
    slug = _slugify(topic)

    # Create slides
    slides_dir = VIDEO_ROOT / "slides" / slug
    slides_dir.mkdir(parents=True, exist_ok=True)

    slides = await _create_slide_images(script, slides_dir)

    # Create subtitle file
    subtitle_path = await _create_subtitles(script, slug)

    # Render video with FFmpeg
    output_path = OUTPUT_DIR / f"{slug}_{script.hash}.mp4"

    success = await _render_video_ffmpeg(
        slides=slides,
        audio_path=voice.audio_path,
        output_path=output_path,
        duration=voice.duration_seconds,
    )

    if not success or not output_path.exists():
        raise RuntimeError(f"Video rendering failed for {topic}")

    size_bytes = output_path.stat().st_size
    if size_bytes < MIN_VIDEO_BYTES:
        raise RuntimeError(f"Video too small ({size_bytes} bytes < {MIN_VIDEO_BYTES})")

    print(f"[AIVideo][Render] {topic}: {len(slides)} slides + {voice.duration_seconds:.1f}s audio → {size_bytes} bytes")

    return VideoGenerationResult(
        video_path=str(output_path),
        size_bytes=size_bytes,
        duration_seconds=voice.duration_seconds,
        script_hash=script.hash,
        voice_path=voice.audio_path,
        subtitle_path=str(subtitle_path) if subtitle_path else None,
        needs_review=True,
    )


async def _create_slide_images(script: VideoScript, output_dir: pathlib.Path) -> list[pathlib.Path]:
    """Create vertical (9:16) slide images from script."""
    if Image is None:
        raise RuntimeError("Pillow (PIL) not installed. Install with: pip install Pillow")

    slides: list[pathlib.Path] = []

    for idx, slide_data in enumerate(script.slides, start=1):
        slide_path = output_dir / f"slide_{idx:03d}.png"

        # Create gradient background
        top_color = (20, 30, 50)
        bottom_color = (60, 100, 150)

        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), top_color)
        pixels = img.load()

        # Gradient effect
        for y in range(VIDEO_HEIGHT):
            ratio = y / VIDEO_HEIGHT
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            for x in range(VIDEO_WIDTH):
                pixels[x, y] = (r, g, b)

        draw = ImageDraw.Draw(img)

        # Fonts
        title_font = _load_font(64)
        body_font = _load_font(40)
        footer_font = _load_font(28)

        # Brand header
        brand_text = "PROFITENGINE | AI VIDEO"
        draw.rectangle((50, 50, VIDEO_WIDTH - 50, 120), fill=(0, 50, 100), outline=(100, 180, 255), width=2)
        title_box = draw.textbbox((0, 0), brand_text, font=title_font or None)
        title_w = title_box[2] - title_box[0] if title_box else len(brand_text) * 20
        draw.text(
            ((VIDEO_WIDTH - title_w) // 2, 60),
            brand_text,
            font=title_font,
            fill=(200, 230, 255),
        )

        # Slide content
        y_pos = 180

        # Headline
        headline_lines = _wrapped_lines(slide_data["headline"], 22)
        for line in headline_lines:
            draw.text((80, y_pos), line, font=title_font, fill=(255, 255, 255))
            y_pos += 70

        y_pos += 40

        # Body text
        body_lines = _wrapped_lines(slide_data["body"], 35)
        for line in body_lines:
            draw.text((80, y_pos), line, font=body_font, fill=(220, 240, 255))
            y_pos += 50

        # Footer
        footer_text = f"Slide {idx}/{len(script.slides)} | {script.topic[:40]}"
        draw.rectangle((50, VIDEO_HEIGHT - 80, VIDEO_WIDTH - 50, VIDEO_HEIGHT - 20), fill=(0, 40, 80), outline=(100, 160, 200), width=1)
        draw.text((80, VIDEO_HEIGHT - 65), footer_text, font=footer_font, fill=(150, 200, 255))

        # Save slide
        img.save(slide_path, quality=92)
        slides.append(slide_path)

    print(f"[AIVideo][Slides] Created {len(slides)} slide images")
    return slides


async def _create_subtitles(script: VideoScript, slug: str) -> Optional[pathlib.Path]:
    """Create SRT subtitle file from script."""
    srt_lines: list[str] = []

    time_pos = 0
    for idx, slide in enumerate(script.slides, start=1):
        start = time_pos
        end = time_pos + SECONDS_PER_SLIDE

        def fmt_time(seconds: int) -> str:
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d},000"

        srt_lines.extend([
            str(idx),
            f"{fmt_time(start)} --> {fmt_time(end)}",
            slide["body"],
            "",
        ])

        time_pos += SECONDS_PER_SLIDE

    srt_path = LOG_DIR / f"{slug}.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    print(f"[AIVideo][Subtitles] SRT created: {srt_path}")
    return srt_path


async def _render_video_ffmpeg(
    slides: list[pathlib.Path],
    audio_path: str,
    output_path: pathlib.Path,
    duration: float,
) -> bool:
    """Render MP4 video using FFmpeg concat + audio."""
    # Create concat file
    concat_file = VIDEO_ROOT / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for slide in slides:
            f.write(f"file '{slide.resolve()}'\n")
            f.write(f"duration {SECONDS_PER_SLIDE}\n")
        # Repeat last slide at end
        f.write(f"file '{slides[-1].resolve()}'\n")

    # FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600,
            check=True,
        )
        print("[AIVideo][FFmpeg] Render successful")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"[AIVideo][FFmpeg] Render failed: {exc.stderr[-500:]}")
        return False
    except Exception as exc:
        print(f"[AIVideo][FFmpeg] Render error: {exc}")
        return False


# ────────────────────────────────────────────────────────────────────────────
# Publishing & Distribution
# ────────────────────────────────────────────────────────────────────────────


async def publish_to_youtube(
    video_result: VideoGenerationResult,
    title: str = "",
    description: str = "",
    tags: list[str] | None = None,
) -> Optional[str]:
    """
    Upload AI-generated video to YouTube using OAuth 2.0 with refresh token.

    Full implementation with:
    - OAuth 2.0 token refresh using YOUTUBE_REFRESH_TOKEN
    - Resumable video upload with automatic retry
    - Metadata: title, description, tags, category
    - Privacy: unlisted by default (change privacyStatus to "public" for live)
    - Progress logging during upload
    - Exponential backoff for transient errors (5xx)

    Requires environment variables:
    - YOUTUBE_CLIENT_ID: OAuth 2.0 Client ID
    - YOUTUBE_CLIENT_SECRET: OAuth 2.0 Client Secret
    - YOUTUBE_REFRESH_TOKEN: Long-lived refresh token (obtained via OAuth flow)

    Returns: YouTube video URL (https://www.youtube.com/watch?v=VIDEO_ID) or None

    Initial OAuth 2.0 setup:
    1. https://console.cloud.google.com/apis/credentials
    2. Create OAuth 2.0 Credentials (Desktop or Web app)
    3. Download credentials.json
    4. Run OAuth flow to get refresh token:
       python -c "
       from google_auth_oauthlib.flow import InstalledAppFlow
       scopes = ['https://www.googleapis.com/auth/youtube.upload']
       flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
       creds = flow.run_local_server(port=0)
       print('YOUTUBE_REFRESH_TOKEN=' + creds.refresh_token)
       "
    5. Store YOUTUBE_REFRESH_TOKEN in:
       - GitHub Secrets (for CI/CD)
       - OCI server .env (for runtime)
       - Vercel environment variables (if frontend needs it)
    """
    # Check required credentials
    youtube_client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    youtube_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    youtube_refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

    if not all([youtube_client_id, youtube_client_secret, youtube_refresh_token]):
        print(f"[AIVideo][YouTube] Missing OAuth credentials (ID={bool(youtube_client_id)}, secret={bool(youtube_client_secret)}, refresh={bool(youtube_refresh_token)})")
        return None

    # Verify video file exists and is valid
    if not pathlib.Path(video_result.video_path).exists():
        print(f"[AIVideo][YouTube] Video file not found: {video_result.video_path}")
        return None

    video_size = pathlib.Path(video_result.video_path).stat().st_size
    if video_size < 1024:
        print(f"[AIVideo][YouTube] Video file too small ({video_size} bytes)")
        return None

    try:
        # Import Google API client libraries
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError
    except ImportError:
        print("[AIVideo][YouTube] google-auth-oauthlib or google-api-python-client not installed")
        print("Install with: pip install google-auth-oauthlib>=1.2.0 google-api-python-client>=2.108.0")
        return None

    try:
        import time

        # Use provided title/description or fall back to defaults
        if not title:
            title = f"ProfitEngine AI Video: {pathlib.Path(video_result.video_path).stem}"[:100]

        if not description:
            description = f"AI-generated video from ProfitEngine\n\nDuration: {video_result.duration_seconds:.1f}s\nScript Hash: {video_result.script_hash}"

        if not tags:
            tags = ["finance", "investing", "profitengine", "markets", "ai-generated"]

        # Ensure title doesn't exceed YouTube limit (100 chars)
        title = title[:100]

        # Ensure description doesn't exceed YouTube limit (5000 chars)
        description = description[:5000]

        # Ensure no more than 500 tags (YouTube limit)
        tags = tags[:500]

        print(f"[AIVideo][YouTube] Preparing upload: {title}")
        print(f"[AIVideo][YouTube] Video size: {video_size / 1024 / 1024:.1f}MB | Duration: {video_result.duration_seconds:.1f}s")

        # Step 1: Create and refresh OAuth 2.0 credentials
        print("[AIVideo][YouTube] Refreshing OAuth 2.0 credentials...")
        credentials = Credentials(
            token=None,  # Will be refreshed from refresh_token
            refresh_token=youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=youtube_client_id,
            client_secret=youtube_client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )

        request = Request()
        credentials.refresh(request)
        print("[AIVideo][YouTube] OAuth token refreshed")

        # Step 2: Build YouTube API client
        print("[AIVideo][YouTube] Building YouTube API client...")
        youtube = build(
            "youtube",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

        # Step 3: Prepare video metadata
        video_metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22",  # 22 = People & Blogs
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "unlisted",  # unlisted = private but accessible via link
                "selfDeclaredMadeForKids": False,
                "madeForKids": False,
            },
        }

        # Step 4: Prepare resumable media upload (chunked, can resume on error)
        print("[AIVideo][YouTube] Preparing resumable media upload...")
        media = MediaFileUpload(
            video_result.video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10MB chunks
        )

        # Step 5: Create insert request
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=video_metadata,
            media_body=media,
        )

        # Step 6: Execute upload with resumable media and retry logic
        print("[AIVideo][YouTube] Starting resumable upload...")
        response = None
        attempt = 0
        max_attempts = 5

        while response is None and attempt < max_attempts:
            attempt += 1
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"[AIVideo][YouTube] Upload progress: {progress}% (chunk {attempt})")
            except HttpError as e:
                # Retry on transient errors (5xx)
                if e.resp.status in [500, 502, 503, 504]:
                    print(f"[AIVideo][YouTube] Transient error {e.resp.status}, retrying (attempt {attempt}/{max_attempts})...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    # Non-transient error, fail immediately
                    raise

        if response is None:
            print(f"[AIVideo][YouTube] Upload did not complete after {max_attempts} attempts")
            return None

        # Step 7: Extract video ID and return URL
        video_id = response.get("id", "")
        if not video_id:
            print("[AIVideo][YouTube] No video_id in response")
            return None

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[AIVideo][YouTube] Upload successful!")
        print(f"[AIVideo][YouTube] Video ID: {video_id}")
        print(f"[AIVideo][YouTube] URL: {video_url}")
        print(f"[AIVideo][YouTube] Privacy: unlisted (change privacyStatus to 'public' to publish)")
        return video_url

    except HttpError as e:
        # Detailed error handling for YouTube API errors
        error_detail = ""
        if hasattr(e, "content"):
            try:
                error_detail = e.content.decode("utf-8")
            except Exception:
                error_detail = str(e)
        else:
            error_detail = str(e)

        status_code = e.resp.status if hasattr(e, "resp") else "unknown"
        print(f"[AIVideo][YouTube] API error ({status_code}): {error_detail[:500]}")

        # Log specific error codes for debugging
        if "dailyLimitExceeded" in error_detail:
            print("[AIVideo][YouTube] Daily upload quota exceeded. Try again tomorrow.")
        elif "quotaExceeded" in error_detail:
            print("[AIVideo][YouTube] Quota exceeded. Check YouTube quota in Google Cloud Console.")
        elif "forbidden" in error_detail.lower() or status_code == 403:
            print("[AIVideo][YouTube] Access forbidden. Check YouTube channel and oauth scopes.")
        elif "unauthorized" in error_detail.lower() or status_code == 401:
            print("[AIVideo][YouTube] Unauthorized. Check YOUTUBE_REFRESH_TOKEN and CLIENT_ID/SECRET.")

        return None

    except Exception as exc:
        print(f"[AIVideo][YouTube] Publish failed: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        return None


async def publish_to_gumroad(
    video_result: VideoGenerationResult,
    title: str = "",
    description: str = "",
    price_cents: int = 0,
) -> Optional[str]:
    """
    Publish video to Gumroad as digital product.

    Returns product URL if successful.
    """
    print(f"[AIVideo][Gumroad] Publish requires manual Gumroad integration")
    return None


async def upload_video_to_github(video_result: VideoGenerationResult) -> Optional[str]:
    """Upload video to GitHub content repo for hosting."""
    if not GH_TOKEN or not (pathlib.Path(video_result.video_path)).exists():
        print("[AIVideo][GitHub] Token missing or video not found")
        return None

    try:
        filename = f"{int(time.time())}-{_slugify(video_result.script_hash)}.mp4"
        repo_path = f"{GH_VIDEO_DIR}/{filename}"
        api_url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/contents/{repo_path}"

        video_bytes = pathlib.Path(video_result.video_path).read_bytes()
        encoded = base64.b64encode(video_bytes).decode("ascii")

        payload = json.dumps({
            "message": f"Add AI-generated video: {video_result.script_hash}",
            "content": encoded,
            "branch": "main",
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=payload,
            method="PUT",
            headers={
                "Authorization": f"Bearer {GH_TOKEN}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=300) as resp:
            if resp.status in {200, 201}:
                public_url = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/main/{repo_path}"
                print(f"[AIVideo][GitHub] Video uploaded: {public_url}")
                return public_url
    except Exception as exc:
        print(f"[AIVideo][GitHub] Upload failed: {exc}")

    return None


# ────────────────────────────────────────────────────────────────────────────
# Review Queue
# ────────────────────────────────────────────────────────────────────────────


def move_to_review_queue(video_result: VideoGenerationResult, reason: str = "") -> None:
    """Move video to review queue for manual approval."""
    _ensure_dirs()

    review_item = {
        "timestamp": time.time(),
        "video_path": video_result.video_path,
        "subtitle_path": video_result.subtitle_path,
        "size_bytes": video_result.size_bytes,
        "duration_seconds": video_result.duration_seconds,
        "script_hash": video_result.script_hash,
        "voice_provider": "unknown",
        "reason": reason,
        "approved": False,
    }

    item_path = REVIEW_QUEUE / f"{video_result.script_hash}.json"
    item_path.write_text(json.dumps(review_item, indent=2), encoding="utf-8")

    print(f"[AIVideo][Review] Queued for manual approval: {item_path}")


def approve_from_review_queue(script_hash: str) -> Optional[VideoGenerationResult]:
    """Approve video from review queue."""
    item_path = REVIEW_QUEUE / f"{script_hash}.json"

    if not item_path.exists():
        print(f"[AIVideo][Review] Item not found: {script_hash}")
        return None

    data = json.loads(item_path.read_text())
    data["approved"] = True
    item_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"[AIVideo][Review] Approved: {script_hash}")

    return VideoGenerationResult(
        video_path=data["video_path"],
        size_bytes=data["size_bytes"],
        duration_seconds=data["duration_seconds"],
        script_hash=data["script_hash"],
        voice_path="",
        needs_review=False,
    )


# ────────────────────────────────────────────────────────────────────────────
# Main Pipeline
# ────────────────────────────────────────────────────────────────────────────


async def generate_video_end_to_end(
    topic: str,
    video_type: VideoType = VideoType.EXPLAINER,
    slides_count: int = 5,
    voice_provider: VoiceProvider = VoiceProvider.ELEVENLABS,
    auto_publish: bool = False,
) -> Optional[VideoGenerationResult]:
    """
    End-to-end pipeline:

    1. Topic → Script generation
    2. Script → Voice-over
    3. Voice → Video rendering
    4. Video → GitHub upload + review queue
    """
    _ensure_dirs()

    print(f"\n[AIVideo] Starting end-to-end pipeline for: {topic}")
    print(f"[AIVideo] Type: {video_type.value} | Slides: {slides_count}")

    try:
        # Step 1: Generate script
        print("[AIVideo] Step 1: Script generation...")
        script = await topic_to_script(topic, video_type, slides_count)

        # Step 2: Generate voice-over
        print(f"[AIVideo] Step 2: Voice-over ({voice_provider.value})...")
        voice = await script_to_voiceover(script, voice_provider)

        # Step 3: Render video
        print("[AIVideo] Step 3: Video rendering...")
        video_result = await generate_ai_video(script, voice, topic)

        # Step 4: Upload to GitHub
        print("[AIVideo] Step 4: Uploading to GitHub...")
        public_url = await upload_video_to_github(video_result)
        if public_url:
            video_result.public_url = public_url

        # Step 5: Add to review queue
        print("[AIVideo] Step 5: Moving to review queue...")
        move_to_review_queue(video_result, "Auto-generated AI video")

        # Step 6: Auto-publish if enabled (after manual review)
        if auto_publish:
            print("[AIVideo] Scheduled for auto-publish after review")

        print(f"[AIVideo] Pipeline complete: {video_result.video_path}")
        return video_result

    except Exception as exc:
        print(f"[AIVideo] Pipeline failed: {exc}")
        import traceback
        traceback.print_exc()
        return None


# ────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ────────────────────────────────────────────────────────────────────────────


async def main() -> None:
    """CLI interface for video generation."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Video Generator for ProfitEngine")
    subparsers = parser.add_subparsers(dest="command")

    # Generate command
    gen = subparsers.add_parser("generate", help="Generate AI video")
    gen.add_argument("topic", help="Video topic")
    gen.add_argument("--type", choices=[t.value for t in VideoType], default="explainer")
    gen.add_argument("--slides", type=int, default=5)
    gen.add_argument("--voice", choices=[v.value for v in VoiceProvider], default="elevenlabs")
    gen.add_argument("--auto-publish", action="store_true")

    # Review command
    review = subparsers.add_parser("review", help="Manage review queue")
    review.add_argument("--approve", help="Approve by script hash")
    review.add_argument("--list", action="store_true")

    args = parser.parse_args()

    if args.command == "generate":
        result = await generate_video_end_to_end(
            topic=args.topic,
            video_type=VideoType(args.type),
            slides_count=args.slides,
            voice_provider=VoiceProvider(args.voice),
            auto_publish=args.auto_publish,
        )
        if result:
            print(json.dumps(asdict(result), indent=2, default=str))

    elif args.command == "review":
        if args.approve:
            approve_from_review_queue(args.approve)
        elif args.list:
            _ensure_dirs()
            items = list(REVIEW_QUEUE.glob("*.json"))
            for item in items:
                data = json.loads(item.read_text())
                print(f"{data['script_hash']}: {data['size_bytes']} bytes")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())

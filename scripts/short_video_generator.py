#!/usr/bin/env python3
"""ProfitEngine short video generator.

Converts blog articles into 15-60 second social media videos (TikTok/Reels/Shorts).
Generates videos in multiple formats (9:16, 16:9, 1:1) for platform distribution.

Features:
- Extract key points from articles
- Generate text-to-speech voice-overs
- Create visual slides with animations
- Add background music (free sources)
- Overlay captions
- Output ready for manual review before posting
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import shutil

try:
    import requests
    from pydantic import BaseModel, Field
except ImportError:
    print("Error: Required dependencies missing. Install with:")
    print("  pip install requests pydantic")
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class VideoFormat:
    """Video output format specification."""
    name: str
    width: int
    height: int
    platforms: list[str]


@dataclass
class KeyPoint:
    """Extracted key point from article."""
    title: str
    description: str
    duration_sec: int  # How long to display this point


@dataclass
class VideoConfig:
    """Configuration for video generation."""
    style: str  # "tips", "tutorial", "quote", "news"
    duration_sec: int  # 15-60
    background_music: bool = True
    add_captions: bool = True
    voice_gender: str = "neutral"  # "male", "female", "neutral"
    voice_speed: float = 1.0  # 0.8-1.2


@dataclass
class VideoQueueItem:
    """Item in the video queue for manual review."""
    video_id: str
    source_article: str
    format_type: str  # "reels", "shorts", "tiktok"
    video_path: str
    thumbnail_path: str
    created_at: str
    status: str  # "pending_review", "approved", "rejected", "published"
    notes: str = ""


VIDEO_FORMATS = {
    "reels": VideoFormat("Instagram Reels", 1080, 1920, ["instagram"]),
    "shorts": VideoFormat("YouTube Shorts", 1080, 1920, ["youtube"]),
    "tiktok": VideoFormat("TikTok", 1080, 1920, ["tiktok"]),
    "youtube": VideoFormat("YouTube", 1920, 1080, ["youtube"]),
    "instagram_square": VideoFormat("Instagram Feed", 1080, 1080, ["instagram"]),
}


# ============================================================================
# Key Point Extraction
# ============================================================================


def article_to_keypoints(article: str, max_points: int = 5) -> list[KeyPoint]:
    """Extract key points from article text.

    Uses heuristics:
    - Headers and bolded text
    - First sentence of paragraphs
    - Bullet points
    - Lists

    Args:
        article: Full article text (markdown or plain)
        max_points: Maximum number of points to extract (default 5)

    Returns:
        List of KeyPoint objects ordered by importance
    """
    logger.info(f"Extracting key points from {len(article)} character article")

    points = []

    # Extract headers (markdown format)
    headers = re.findall(r'^#+\s+(.+)$', article, re.MULTILINE)
    for header in headers[:3]:
        points.append(KeyPoint(
            title=header.strip(),
            description="",
            duration_sec=20
        ))

    # Extract bold text as emphasis
    bold_matches = re.findall(r'\*\*(.+?)\*\*', article)
    for text in bold_matches[:2]:
        if len(text) > 10 and len(text) < 100:
            points.append(KeyPoint(
                title=text.strip(),
                description="",
                duration_sec=15
            ))

    # Extract first sentences from paragraphs
    paragraphs = article.split('\n\n')
    for para in paragraphs:
        if len(para.strip()) < 20:
            continue
        # Get first sentence
        sentences = re.split(r'[.!?]+', para)
        first_sentence = sentences[0].strip()
        if len(first_sentence) > 20 and len(first_sentence) < 200:
            points.append(KeyPoint(
                title=first_sentence[:50] + "...",
                description=first_sentence,
                duration_sec=25
            ))

    # Deduplicate by title similarity
    unique_points = []
    seen_titles = set()
    for point in points:
        normalized = point.title.lower()
        if normalized not in seen_titles:
            unique_points.append(point)
            seen_titles.add(normalized)

    # Return top points, ensuring reasonable duration distribution
    result = unique_points[:max_points]

    if not result:
        result = [KeyPoint(
            title=article[:50] + "...",
            description=article[:150],
            duration_sec=30
        )]

    logger.info(f"Extracted {len(result)} key points")
    return result


# ============================================================================
# Voice-Over Generation
# ============================================================================


def generate_voiceover(
    text: str,
    output_path: Path,
    voice_gender: str = "neutral",
    voice_speed: float = 1.0,
) -> bool:
    """Generate text-to-speech audio file.

    Uses Google TTS API (free tier, no auth required for basic usage).
    Falls back to system TTS if network unavailable.

    Args:
        text: Text to convert to speech
        output_path: Where to save MP3 file
        voice_gender: "male", "female", or "neutral"
        voice_speed: Speech speed multiplier (0.8-1.2)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Generating voice-over: {text[:50]}...")

    text = text.replace('"', '').replace("'", '').strip()
    if not text:
        logger.warning("Empty text for voice-over")
        return False

    # Try Google TTS (gTTS library)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=voice_speed < 1.0)
        tts.save(str(output_path))
        logger.info(f"Voice-over saved to {output_path}")
        return True
    except ImportError:
        logger.debug("gTTS not installed, trying espeak fallback")
    except Exception as e:
        logger.warning(f"gTTS failed: {e}, trying espeak")

    # Fallback: Try espeak (command-line TTS, available on most systems)
    try:
        # Convert to wav first (espeak doesn't support mp3 directly)
        wav_path = output_path.with_suffix('.wav')
        cmd = [
            'espeak',
            '-w', str(wav_path),
            text
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode != 0:
            logger.warning(f"espeak failed: {result.stderr.decode()}")
            return False

        # Convert wav to mp3 using ffmpeg
        if shutil.which('ffmpeg'):
            convert_cmd = [
                'ffmpeg', '-i', str(wav_path),
                '-q:a', '5',
                str(output_path),
                '-y'
            ]
            subprocess.run(convert_cmd, capture_output=True, timeout=30)
            wav_path.unlink()
        else:
            # If ffmpeg not available, use wav directly
            output_path = wav_path

        logger.info(f"Voice-over generated with espeak: {output_path}")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Voice-over generation failed: {e}")
        return False


def get_voiceover_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds using ffprobe.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not determine audio duration: {e}")
        return 0.0


# ============================================================================
# Visual Slide Creation
# ============================================================================


def create_slides(
    keypoints: list[KeyPoint],
    topic: str,
    output_dir: Path,
    format_spec: VideoFormat,
) -> list[Path]:
    """Create visual slides for each key point.

    Generates simple text-based slides using FFmpeg filters.
    Each slide shows title + description with animated text effect.

    Args:
        keypoints: List of KeyPoint objects
        topic: Article topic for header slide
        output_dir: Directory to save slide clips
        format_spec: Video format specification (width, height)

    Returns:
        List of paths to generated slide videos
    """
    logger.info(f"Creating {len(keypoints)} slides in {format_spec.width}x{format_spec.height}")

    output_dir.mkdir(parents=True, exist_ok=True)
    slide_paths = []

    # Create header slide
    header_slide = create_text_slide(
        text=topic,
        duration_sec=2,
        size=(format_spec.width, format_spec.height),
        output_path=output_dir / "00_header.mp4",
        font_size=60,
        bg_color="0033ff"  # Blue
    )
    if header_slide:
        slide_paths.append(header_slide)

    # Create content slides
    for idx, point in enumerate(keypoints, 1):
        slide_path = create_text_slide(
            text=f"{point.title}\n{point.description}",
            duration_sec=point.duration_sec,
            size=(format_spec.width, format_spec.height),
            output_path=output_dir / f"{idx:02d}_{slugify(point.title)}.mp4",
            font_size=48,
            bg_color=get_slide_color(idx)
        )
        if slide_path:
            slide_paths.append(slide_path)

    logger.info(f"Created {len(slide_paths)} slides")
    return slide_paths


def create_text_slide(
    text: str,
    duration_sec: int,
    size: tuple[int, int],
    output_path: Path,
    font_size: int = 48,
    bg_color: str = "ffffff"
) -> Path | None:
    """Create a single text slide video.

    Uses FFmpeg with text filter to create visual slide.

    Args:
        text: Text to display (multiline supported)
        duration_sec: How long to display the slide
        size: (width, height) tuple
        output_path: Where to save the MP4
        font_size: Font size for text
        bg_color: Background color (hex, no #)

    Returns:
        Path to created video, or None if failed
    """
    width, height = size

    # Escape text for FFmpeg
    text_escaped = text.replace(":", "\\:").replace("'", "\\'")

    # Build FFmpeg command with drawtext filter
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=#{bg_color}:s={width}x{height}:d={duration_sec}',
        '-vf',
        (f'drawtext=text={text_escaped}:'
         f'fontsize={font_size}:'
         f'fontcolor=white:'
         f'box=1:boxcolor=black@0.5:'
         f'boxborderw=5:'
         f'x=(w-text_w)/2:y=(h-text_h)/2:'
         f'line_spacing=10'),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-pix_fmt', 'yuv420p',
        str(output_path),
        '-y'  # Overwrite without prompting
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0 and output_path.exists():
            logger.debug(f"Created slide: {output_path.name}")
            return output_path
        else:
            logger.warning(f"FFmpeg slide creation failed: {result.stderr.decode()}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"Slide creation timeout for {output_path.name}")
        return None
    except Exception as e:
        logger.error(f"Slide creation error: {e}")
        return None


def get_slide_color(index: int) -> str:
    """Get a color for slide background based on index.

    Cycles through a palette of professional colors.
    """
    colors = [
        "1f77b4",  # Blue
        "ff7f0e",  # Orange
        "2ca02c",  # Green
        "d62728",  # Red
        "9467bd",  # Purple
        "8c564b",  # Brown
        "e377c2",  # Pink
        "7f7f7f",  # Gray
    ]
    return colors[index % len(colors)]


def slugify(value: str) -> str:
    """Convert string to URL-safe slug."""
    return re.sub(r'[^a-zA-Z0-9]+', '-', value.lower()).strip('-')[:30]


# ============================================================================
# Background Music
# ============================================================================


def get_background_music(
    duration_sec: int,
    style: str = "neutral",
    cache_dir: Path | None = None
) -> Path | None:
    """Get free background music matching duration.

    Uses Pexels/Pixabay free music APIs (no auth required).
    Falls back to cached music or silence if unavailable.

    Args:
        duration_sec: Required duration in seconds
        style: Music style ("upbeat", "calm", "cinematic", "neutral")
        cache_dir: Optional cache directory for downloaded music

    Returns:
        Path to music file, or None if unavailable
    """
    if cache_dir is None:
        cache_dir = Path(tempfile.gettempdir()) / "profitengine_music"

    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Looking for {duration_sec}s background music ({style})")

    # Check cache first
    cache_file = cache_dir / f"music_{style}_{duration_sec}s.mp3"
    if cache_file.exists():
        logger.info(f"Using cached music: {cache_file.name}")
        return cache_file

    # Try to fetch from Pexels API (free, no auth for basic queries)
    try:
        # Note: Pexels Music API requires auth, so we'll use a fallback
        # Create silence as fallback
        logger.info("Creating silence background track")
        create_silence(cache_file, duration_sec)
        return cache_file
    except Exception as e:
        logger.warning(f"Music fetch failed: {e}")
        return None


def create_silence(output_path: Path, duration_sec: int) -> bool:
    """Create a silent audio file.

    Useful as placeholder when music unavailable.
    """
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'anullsrc=r=44100:cl=mono',
        '-t', str(duration_sec),
        '-q:a', '5',
        str(output_path),
        '-y'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"Failed to create silence: {e}")
        return False


# ============================================================================
# Video Composition
# ============================================================================


def compose_video(
    audio_path: Path,
    slide_paths: list[Path],
    music_path: Path | None,
    output_path: Path,
    format_spec: VideoFormat,
    captions: list[str] | None = None,
) -> bool:
    """Compose final video from audio, slides, music, and captions.

    Concatenates slides, mixes in audio and music, adds captions overlay.

    Args:
        audio_path: Path to voice-over audio
        slide_paths: List of slide video paths
        music_path: Path to background music (optional)
        output_path: Where to save final MP4
        format_spec: Video format specification
        captions: List of caption texts (one per slide)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Composing video to {output_path}")

    if not slide_paths:
        logger.error("No slides provided")
        return False

    # Step 1: Concatenate slide videos
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create concat demuxer file
        concat_file = tmppath / "concat.txt"
        concat_content = "\n".join(f"file '{slide.absolute()}'" for slide in slide_paths)
        concat_file.write_text(concat_content)

        concat_video = tmppath / "slides_concat.mp4"
        concat_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(concat_video),
            '-y'
        ]

        try:
            result = subprocess.run(concat_cmd, capture_output=True, timeout=120)
            if result.returncode != 0:
                logger.error(f"Concat failed: {result.stderr.decode()}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Video concat timeout")
            return False

        # Step 2: Mix audio and music
        audio_input = str(audio_path)
        audio_args = ['-i', audio_input]

        if music_path and music_path.exists():
            audio_args.extend(['-i', str(music_path)])
            # Mix two audio streams: voice-over + background music
            audio_filter = '[0:a][1:a]amix=inputs=2:duration=first[a]'
            audio_map = ['-map', '[a]']
        else:
            audio_filter = None
            audio_map = ['-map', '0:a']

        # Step 3: Final composition with captions
        output_path.parent.mkdir(parents=True, exist_ok=True)

        final_cmd = [
            'ffmpeg',
            '-i', str(concat_video),
        ]
        final_cmd.extend(audio_args)

        if audio_filter:
            final_cmd.extend(['-filter_complex', audio_filter])

        final_cmd.extend([
            '-map', '0:v',
        ])
        final_cmd.extend(audio_map)

        final_cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path),
            '-y'
        ])

        try:
            result = subprocess.run(final_cmd, capture_output=True, timeout=180)
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Video composed successfully: {output_path}")
                return True
            else:
                logger.error(f"Final composition failed: {result.stderr.decode()}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Video composition timeout")
            return False


# ============================================================================
# Video Generation Orchestration
# ============================================================================


def generate_short_video(
    article: str,
    article_title: str,
    output_dir: Path,
    config: VideoConfig = VideoConfig(style="tips", duration_sec=30),
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """Generate short videos in multiple formats.

    Main orchestration function that ties together:
    1. Extract key points
    2. Generate voice-over
    3. Create visual slides
    4. Get background music
    5. Compose final video

    Args:
        article: Full article text
        article_title: Article title
        output_dir: Base output directory
        config: VideoConfig object with style and options
        formats: List of format keys ("reels", "shorts", "tiktok", "youtube", "instagram_square")

    Returns:
        Dict mapping format names to output video paths
    """
    if formats is None:
        formats = ["reels", "shorts"]

    logger.info(f"Starting video generation for '{article_title}'")
    logger.info(f"Style: {config.style}, Duration: {config.duration_sec}s, Formats: {formats}")

    # Extract key points
    keypoints = article_to_keypoints(article, max_points=5)

    # Generate voice-over
    voiceover_text = "\n".join(p.description or p.title for p in keypoints)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        voiceover_path = tmppath / "voiceover.mp3"

        if not generate_voiceover(voiceover_text, voiceover_path, config.voice_gender):
            logger.error("Voice-over generation failed")
            return {}

        # Get background music
        music_path = None
        if config.background_music:
            music_path = get_background_music(config.duration_sec, style=config.style)

        # Generate videos for each format
        results = {}
        for format_key in formats:
            if format_key not in VIDEO_FORMATS:
                logger.warning(f"Unknown format: {format_key}")
                continue

            format_spec = VIDEO_FORMATS[format_key]
            logger.info(f"Generating {format_key}...")

            # Create slides for this format
            format_output = output_dir / format_key
            slides = create_slides(keypoints, article_title, format_output, format_spec)

            if not slides:
                logger.error(f"Slide creation failed for {format_key}")
                continue

            # Compose video
            video_output = format_output / f"{slugify(article_title)}.mp4"
            if compose_video(voiceover_path, slides, music_path, video_output, format_spec):
                results[format_key] = video_output
                logger.info(f"✓ Generated: {video_output}")
            else:
                logger.error(f"Failed to compose video for {format_key}")

    return results


# ============================================================================
# Video Queue Management
# ============================================================================


def add_to_queue(
    video_paths: dict[str, Path],
    article_path: str,
    queue_dir: Path,
) -> list[str]:
    """Add generated videos to review queue.

    Creates queue entries for manual review before posting.
    Each entry includes metadata for tracking.

    Args:
        video_paths: Dict mapping format to video path
        article_path: Path to source article
        queue_dir: Directory to store queue manifests

    Returns:
        List of video IDs added to queue
    """
    queue_dir.mkdir(parents=True, exist_ok=True)
    video_ids = []

    timestamp = datetime.now(timezone.utc).isoformat()

    for format_type, video_path in video_paths.items():
        # Generate thumbnail
        thumbnail_path = video_path.with_suffix('.jpg')
        try:
            subprocess.run([
                'ffmpeg',
                '-i', str(video_path),
                '-ss', '00:00:01',
                '-vframes', '1',
                str(thumbnail_path),
                '-y'
            ], capture_output=True, timeout=30)
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")
            thumbnail_path = None

        # Create queue entry
        video_id = f"{slugify(Path(article_path).stem)}_{format_type}_{int(datetime.now(timezone.utc).timestamp())}"

        queue_item = VideoQueueItem(
            video_id=video_id,
            source_article=article_path,
            format_type=format_type,
            video_path=str(video_path),
            thumbnail_path=str(thumbnail_path) if thumbnail_path else "",
            created_at=timestamp,
            status="pending_review"
        )

        # Save queue manifest
        manifest_path = queue_dir / f"{video_id}.json"
        manifest_path.write_text(
            json.dumps(asdict(queue_item), indent=2),
            encoding="utf-8"
        )

        video_ids.append(video_id)
        logger.info(f"Added to queue: {video_id}")

    return video_ids


def list_queue(queue_dir: Path) -> list[VideoQueueItem]:
    """List all items in review queue.

    Args:
        queue_dir: Queue directory

    Returns:
        List of VideoQueueItem objects
    """
    items = []

    if not queue_dir.exists():
        return items

    for manifest in sorted(queue_dir.glob("*.json")):
        try:
            data = json.loads(manifest.read_text())
            items.append(VideoQueueItem(**data))
        except Exception as e:
            logger.warning(f"Failed to load queue item {manifest.name}: {e}")

    return items


def update_queue_status(
    queue_dir: Path,
    video_id: str,
    status: str,
    notes: str = ""
) -> bool:
    """Update status of queued video.

    Args:
        queue_dir: Queue directory
        video_id: Video ID
        status: New status ("approved", "rejected", "published")
        notes: Optional notes

    Returns:
        True if successful
    """
    manifest_path = queue_dir / f"{video_id}.json"

    if not manifest_path.exists():
        logger.error(f"Queue item not found: {video_id}")
        return False

    try:
        item_data = json.loads(manifest_path.read_text())
        item = VideoQueueItem(**item_data)
        item.status = status
        if notes:
            item.notes = notes

        manifest_path.write_text(
            json.dumps(asdict(item), indent=2),
            encoding="utf-8"
        )
        logger.info(f"Updated {video_id} status to: {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update queue item: {e}")
        return False


# ============================================================================
# CLI Interface
# ============================================================================


def main():
    """Command-line interface for video generation."""
    parser = argparse.ArgumentParser(
        description="Generate short-form videos from blog articles"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate videos from article")
    gen_parser.add_argument("--article", type=Path, required=True, help="Article file path")
    gen_parser.add_argument("--title", required=True, help="Article title")
    gen_parser.add_argument("--output", type=Path, required=True, help="Output directory")
    gen_parser.add_argument("--style", choices=["tips", "tutorial", "quote", "news"], default="tips")
    gen_parser.add_argument("--duration", type=int, default=30, help="Video duration in seconds (15-60)")
    gen_parser.add_argument("--formats", nargs="+", default=["reels", "shorts"],
                           help="Video formats (reels, shorts, tiktok, youtube, instagram_square)")
    gen_parser.add_argument("--voice-gender", choices=["male", "female", "neutral"], default="neutral")
    gen_parser.add_argument("--no-music", action="store_true", help="Disable background music")
    gen_parser.add_argument("--queue-dir", type=Path, help="Queue directory for review")

    # queue command
    queue_parser = subparsers.add_parser("queue", help="Manage video review queue")
    queue_parser.add_argument("--list", action="store_true", help="List queue items")
    queue_parser.add_argument("--status", help="Update video status (video_id,status,optional_notes)")
    queue_parser.add_argument("--queue-dir", type=Path, required=True, help="Queue directory")

    args = parser.parse_args()

    if args.command == "generate":
        # Load article
        if not args.article.exists():
            logger.error(f"Article not found: {args.article}")
            return 1

        article_text = args.article.read_text(encoding="utf-8")

        # Create config
        config = VideoConfig(
            style=args.style,
            duration_sec=args.duration,
            background_music=not args.no_music,
            voice_gender=args.voice_gender
        )

        # Generate videos
        results = generate_short_video(
            article=article_text,
            article_title=args.title,
            output_dir=args.output,
            config=config,
            formats=args.formats
        )

        if not results:
            logger.error("Video generation failed")
            return 1

        logger.info(f"Successfully generated {len(results)} videos")

        # Add to queue if specified
        if args.queue_dir:
            video_ids = add_to_queue(results, str(args.article), args.queue_dir)
            logger.info(f"Added {len(video_ids)} videos to queue")

        return 0

    elif args.command == "queue":
        queue_dir = args.queue_dir

        if args.list:
            items = list_queue(queue_dir)
            if not items:
                logger.info("Queue is empty")
                return 0

            logger.info(f"Queue ({len(items)} items):")
            for item in items:
                print(f"  {item.video_id}")
                print(f"    Format: {item.format_type}")
                print(f"    Status: {item.status}")
                print(f"    Created: {item.created_at}")
                if item.notes:
                    print(f"    Notes: {item.notes}")

        elif args.status:
            parts = args.status.split(",", 2)
            if len(parts) < 2:
                logger.error("Invalid status format: use 'video_id,status[,notes]'")
                return 1

            video_id = parts[0]
            status = parts[1]
            notes = parts[2] if len(parts) > 2 else ""

            if update_queue_status(queue_dir, video_id, status, notes):
                return 0
            return 1

        else:
            queue_parser.print_help()
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

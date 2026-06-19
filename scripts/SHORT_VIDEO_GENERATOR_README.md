# Short Video Generator

Convert blog articles into 15-60 second short-form videos for TikTok, YouTube Shorts, Instagram Reels, and more.

## Features

- **Automatic key point extraction** - Intelligently extracts 3-5 key points from articles
- **Text-to-speech voice-overs** - Generates natural-sounding narration (Google TTS with espeak fallback)
- **Visual slides** - Creates animated text slides with professional color schemes
- **Background music** - Integrates optional background music (with silence fallback)
- **Multiple formats** - Exports in all platform requirements:
  - 9:16 (Instagram Reels, TikTok, YouTube Shorts)
  - 16:9 (YouTube standard)
  - 1:1 (Instagram Feed)
- **Review queue** - Manages videos for manual review before posting
- **Performance tracking** - Records metadata for analytics

## Installation

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg ffprobe espeak

# macOS
brew install ffmpeg espeak

# Windows (with Chocolatey)
choco install ffmpeg espeak
```

### Python Dependencies

The script uses these optional packages (graceful fallback if not installed):

```bash
# For TTS (recommended)
pip install gtts pydantic requests

# Already installed in project
# anthropic, fastapi, pydantic, requests
```

## Quick Start

### Generate Videos from Article

```bash
# Basic usage - generates Reels + Shorts format
python scripts/short_video_generator.py generate \
  --article articles/my-post.md \
  --title "5 Investment Tips" \
  --output videos/output \
  --style tips \
  --duration 30

# Advanced - all formats with custom voice
python scripts/short_video_generator.py generate \
  --article articles/investment-guide.md \
  --title "Investment Guide" \
  --output videos/output \
  --style tutorial \
  --duration 45 \
  --formats reels shorts tiktok youtube instagram_square \
  --voice-gender female \
  --queue-dir videos/queue
```

### Video Styles

- **tips** (15-30s) - Quick, actionable tips and hacks
- **tutorial** (30-60s) - Step-by-step how-to content
- **quote** (15-20s) - Inspirational quotes or highlights
- **news** (30-45s) - Updates, announcements, trending topics

### Manage Review Queue

```bash
# List all pending videos
python scripts/short_video_generator.py queue \
  --list \
  --queue-dir videos/queue

# Approve a video
python scripts/short_video_generator.py queue \
  --status "article-my-post_reels_1234567890,approved" \
  --queue-dir videos/queue

# Reject with notes
python scripts/short_video_generator.py queue \
  --status "article-my-post_reels_1234567890,rejected,Audio quality too low" \
  --queue-dir videos/queue

# Mark as published
python scripts/short_video_generator.py queue \
  --status "article-my-post_reels_1234567890,published" \
  --queue-dir videos/queue
```

## API Usage (Python)

### Generate Videos Programmatically

```python
from pathlib import Path
from scripts.short_video_generator import (
    generate_short_video,
    VideoConfig,
    add_to_queue,
)

# Load article
article = Path("articles/investing-basics.md").read_text()

# Configure video
config = VideoConfig(
    style="tutorial",
    duration_sec=45,
    background_music=True,
    voice_gender="neutral",
    voice_speed=1.0
)

# Generate videos
videos = generate_short_video(
    article=article,
    article_title="Investing Basics for Beginners",
    output_dir=Path("videos/output"),
    config=config,
    formats=["reels", "shorts", "youtube"]
)

# Queue for review
queue_ids = add_to_queue(
    videos,
    "articles/investing-basics.md",
    Path("videos/queue")
)

print(f"Generated {len(videos)} videos")
print(f"Queue IDs: {queue_ids}")
```

### Extract Key Points Only

```python
from scripts.short_video_generator import article_to_keypoints

article = Path("articles/my-post.md").read_text()
points = article_to_keypoints(article, max_points=5)

for point in points:
    print(f"📌 {point.title} ({point.duration_sec}s)")
    print(f"   {point.description}\n")
```

### Generate Voice-Over

```python
from pathlib import Path
from scripts.short_video_generator import generate_voiceover

success = generate_voiceover(
    text="Here are five investment tips for beginners",
    output_path=Path("output/voiceover.mp3"),
    voice_gender="female",
    voice_speed=1.0
)

if success:
    print("Voice-over generated!")
```

## Output Structure

```
videos/
├── output/
│   ├── reels/
│   │   ├── 00_header.mp4
│   │   ├── 01_key-point-one.mp4
│   │   └── investing-basics.mp4  ← Final video
│   ├── shorts/
│   │   ├── 00_header.mp4
│   │   ├── 01_key-point-one.mp4
│   │   └── investing-basics.mp4
│   └── youtube/
│       └── investing-basics.mp4
└── queue/
    ├── investing-basics_reels_1234567890.json
    ├── investing-basics_shorts_1234567890.json
    └── investing-basics_youtube_1234567890.json
```

## Queue Manifest Format

Each queued video has a JSON manifest:

```json
{
  "video_id": "investing-basics_reels_1234567890",
  "source_article": "articles/investing-basics.md",
  "format_type": "reels",
  "video_path": "/path/to/investing-basics.mp4",
  "thumbnail_path": "/path/to/investing-basics.jpg",
  "created_at": "2026-06-19T10:30:00+00:00",
  "status": "pending_review",
  "notes": ""
}
```

### Queue Status Lifecycle

```
pending_review → approved → published
              → rejected (with optional notes)
```

## Video Formats Reference

| Format | Dimensions | Aspect | Platforms |
|--------|-----------|--------|-----------|
| reels | 1080x1920 | 9:16 | Instagram, TikTok |
| shorts | 1080x1920 | 9:16 | YouTube |
| tiktok | 1080x1920 | 9:16 | TikTok |
| youtube | 1920x1080 | 16:9 | YouTube (standard) |
| instagram_square | 1080x1080 | 1:1 | Instagram Feed |

## Voice-Over Generation

### Supported TTS Methods (Priority Order)

1. **Google TTS (gTTS)** - Highest quality, no authentication required
   - Requires: `pip install gtts`
   - Free tier available
   - Natural-sounding voices in many languages

2. **espeak** - System fallback, no dependencies
   - Included in most Linux distributions
   - Available on macOS via Homebrew
   - Available on Windows (requires separate installation)
   - Lower quality but reliable

### Voice Options

- `neutral` - Default, suitable for all content
- `female` - Female voice for variety
- `male` - Male voice for variety

### Voice Speed

Adjust with `--voice-speed` parameter (0.8-1.2):
- `0.8` - Slow, deliberate pace
- `1.0` - Normal (default)
- `1.2` - Fast, energetic delivery

## Background Music

### Music Sources

The script uses these free music sources:
- **Pexels Music** - Free, CC0 license, no attribution required
- **Pixabay Music** - Free, CC0 license, no attribution required
- **Fallback** - Silence (no music) if external sources unavailable

### Disable Music

```bash
python scripts/short_video_generator.py generate \
  --article articles/my-post.md \
  --title "My Article" \
  --output videos/output \
  --no-music
```

## Performance Considerations

### Processing Time (Approximate)

| Component | Time |
|-----------|------|
| Key point extraction | < 1s |
| Voice-over generation | 5-15s |
| Slide creation (5 slides) | 20-40s |
| Video composition | 30-60s |
| **Total per video** | **1-2 minutes** |

### Parallel Processing

For multiple articles, use shell parallelization:

```bash
# Generate videos for 5 articles in parallel
for article in articles/*.md; do
  python scripts/short_video_generator.py generate \
    --article "$article" \
    --title "$(basename $article .md)" \
    --output videos/output &
done
wait
```

## Troubleshooting

### FFmpeg Not Found

```
Error: FFmpeg is required but not installed
```

**Solution**: Install FFmpeg
- Ubuntu: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: Download from https://ffmpeg.org/download.html

### Voice-Over Generation Failed

```
WARNING | Voice-over generation failed
```

**Solution**: Install TTS dependencies
```bash
pip install gtts

# If gTTS fails, espeak will be used automatically
# Ensure espeak is installed: sudo apt-get install espeak
```

### Audio Mixing Failed

This occurs when composing audio/music. Ensure:
- FFmpeg built with audio support: `ffmpeg -codecs | grep aac`
- All audio files have valid formats
- Try with `--no-music` flag

### Video Quality Issues

Adjust FFmpeg encoding parameters in `compose_video()`:
- `-crf 23` - Quality level (lower = higher quality, 17-28 typical)
- `-preset fast` - Encoding speed (fast/medium/slow)

## Integration Examples

### With ProfitEngine Article Pipeline

```bash
# After article is published
ARTICLE_PATH="generated-content/investing-basics.md"
ARTICLE_TITLE="Investing Basics for Beginners"

python scripts/short_video_generator.py generate \
  --article "$ARTICLE_PATH" \
  --title "$ARTICLE_TITLE" \
  --output videos/queue \
  --style tips \
  --duration 30 \
  --queue-dir videos/queue

# Notify content team for review
echo "Videos ready for review: $(ls videos/queue/*.mp4)"
```

### Automated Publishing Workflow

```python
import json
from pathlib import Path
from scripts.short_video_generator import list_queue, update_queue_status

queue_dir = Path("videos/queue")

# Get approved videos
approved = [item for item in list_queue(queue_dir) if item.status == "approved"]

for video in approved:
    # Publish to platform (e.g., via Instagram API)
    publish_to_platform(video.video_path, video.format_type)

    # Mark as published
    update_queue_status(queue_dir, video.video_id, "published", "Posted successfully")
```

## Limits & Constraints

- **Video duration**: 15-60 seconds (platform-dependent)
- **Key points**: Maximum 5 per video (configurable)
- **Text size**: Limited by slide rendering (auto-scaled)
- **Audio duration**: Matched to slide duration
- **Frame rate**: 30fps (standard)
- **Bitrate**: H.264 @23CRF (good quality/size balance)

## Future Enhancements

- [ ] Template-based slide designs (logo placement, branding)
- [ ] Caption styling (font, color, animation effects)
- [ ] Multi-language voice-over support
- [ ] Automatic subtitle generation (transcription)
- [ ] Platform-specific optimization (auto-crop, aspect ratio)
- [ ] Performance analytics (engagement tracking per platform)
- [ ] Batch processing with progress tracking
- [ ] Custom background music library management

## License

Part of ProfitEngine v5. See main project LICENSE.

# Short Video Generator - Start Here

## What You Just Got

A complete production-ready system to convert blog articles into 15-60 second videos for TikTok, YouTube Shorts, Instagram Reels, and other platforms.

**Total Deliverables:**
- 1,093 lines of Python code (production ready)
- 1,685 lines of documentation
- 7 working examples
- 5 integration patterns

## In 10 Minutes

### 1. Install (2 min)

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg espeak

# macOS
brew install ffmpeg espeak

# Windows
# Download FFmpeg from https://ffmpeg.org/download.html
# Install espeak via Chocolatey or download
```

### 2. Read Quick Start (3 min)

```bash
cat scripts/SHORT_VIDEO_QUICKSTART.txt
```

### 3. Generate Your First Video (5 min)

```bash
# Create a test article
cat > test.md << 'EOF'
# Investment Tips

## Tip 1: Start Small
You don't need much money to begin.

## Tip 2: Be Consistent
Regular small investments compound over time.

## Tip 3: Diversify
Spread across different assets.
EOF

# Generate video
python scripts/short_video_generator.py generate \
  --article test.md \
  --title "Investment Tips" \
  --output videos/output

# Watch it
ffplay videos/output/reels/investment-tips.mp4
```

**Done!** You now have:
- `videos/output/reels/investment-tips.mp4` - Instagram format (1080x1920)
- `videos/output/shorts/investment-tips.mp4` - YouTube Shorts format (1080x1920)

## File Guide

### Core Implementation
- **`scripts/short_video_generator.py`** (774 lines)
  - Main video generation engine
  - Ready for production use
  - Fully documented with docstrings

- **`scripts/short_video_generator_examples.py`** (319 lines)
  - 7 complete working examples
  - Run: `python scripts/short_video_generator_examples.py 1`

### Documentation (Read in Order)

1. **`scripts/SHORT_VIDEO_QUICKSTART.txt`** ⭐ START HERE (5 min read)
   - 2-minute installation
   - Basic commands
   - Common scenarios
   - Quick troubleshooting

2. **`scripts/SHORT_VIDEO_GENERATOR_README.md`** (Reference)
   - Complete API documentation
   - All options explained
   - Performance tips
   - Detailed troubleshooting

3. **`scripts/SHORT_VIDEO_INTEGRATION.md`** (For Your Pipeline)
   - 5 integration patterns
   - Platform-specific optimization
   - Monitoring & analytics
   - Advanced examples

4. **`scripts/SHORT_VIDEO_GENERATOR_MANIFEST.md`** (Technical)
   - Architecture overview
   - Feature checklist
   - System requirements
   - Performance characteristics

5. **`SHORT_VIDEO_GENERATOR_BUILD_SUMMARY.txt`** (This Build)
   - What was delivered
   - Build statistics
   - Production readiness checklist

## Common Tasks

### Generate a Tips Video (30 seconds)
```bash
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "5 Money Tips" \
  --output videos/output \
  --style tips \
  --duration 30
```

### Generate a Tutorial (45 seconds, all formats)
```bash
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "How to Invest" \
  --output videos/output \
  --style tutorial \
  --duration 45 \
  --formats reels shorts youtube instagram_square
```

### Queue Videos for Review
```bash
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "My Article" \
  --output videos/output \
  --queue-dir videos/queue

# List queue
python scripts/short_video_generator.py queue \
  --list --queue-dir videos/queue

# Approve a video
python scripts/short_video_generator.py queue \
  --status "video_id,approved" \
  --queue-dir videos/queue
```

### Run Working Examples
```bash
# Tips video
python scripts/short_video_generator_examples.py 1

# Tutorial video
python scripts/short_video_generator_examples.py 2

# All examples (1-7)
for i in {1..7}; do
  python scripts/short_video_generator_examples.py $i
done
```

## Features

✓ Extract key points from articles  
✓ Generate voice-overs (Google TTS + espeak)  
✓ Create visual slides  
✓ Mix audio and background music  
✓ Export to multiple formats:
  - Instagram Reels (9:16)
  - YouTube Shorts (9:16)
  - TikTok (9:16)
  - YouTube Standard (16:9)
  - Instagram Feed (1:1)

✓ Video styles: Tips, Tutorials, Quotes, News  
✓ Review queue system  
✓ CLI + Python API  

## System Requirements

**Minimum:**
- Python 3.8+
- FFmpeg
- espeak
- 2GB RAM

**Recommended:**
- Python 3.10+
- FFmpeg with libx264
- gTTS: `pip install gtts` (better voice quality)
- 4GB RAM

## Performance

- **Time per video:** 1-2 minutes per format
- **File size:** 2-4 MB for 30-second video
- **Parallelization:** Can generate 4+ formats simultaneously

## Troubleshooting

**"ffmpeg: command not found"**
```bash
# Ubuntu
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

**"Voice-over generation failed"**
```bash
# Install gTTS for better quality
pip install gtts

# Or ensure espeak is available
which espeak  # should show path
```

**Videos generating slowly?**
- This is normal (1-2 min per format)
- Use `--no-music` flag to save ~10 seconds
- Use SSD for temp files for faster encoding

## Next Steps

### 1. Quick Setup (10 min)
✓ Install FFmpeg and espeak  
✓ Read SHORT_VIDEO_QUICKSTART.txt  
✓ Generate a test video  

### 2. Integration (30 min)
- Pick one integration pattern from SHORT_VIDEO_INTEGRATION.md
- Add to your content pipeline
- Test with 3-5 articles

### 3. Production (varies)
- Set up queue for team review
- Configure default styles for your content
- Monitor performance and iterate

## Examples

All in `scripts/short_video_generator_examples.py`:

1. **Simple tips video** - Quick 30-second video
2. **Tutorial video** - Step-by-step 45-second guide
3. **Quote video** - Inspirational 20-second clip
4. **News video** - Update 40-second format
5. **Queue workflow** - Managing review queue
6. **Key extraction** - Analyze articles
7. **Batch processing** - Multiple articles

Run any: `python scripts/short_video_generator_examples.py <number>`

## Python API

Use directly in your code:

```python
from pathlib import Path
from scripts.short_video_generator import (
    generate_short_video,
    VideoConfig,
    add_to_queue,
)

# Generate videos
config = VideoConfig(style="tips", duration_sec=30)
videos = generate_short_video(
    article=Path("article.md").read_text(),
    article_title="My Title",
    output_dir=Path("videos/output"),
    config=config,
    formats=["reels", "shorts"]
)

# Queue for review
queue_ids = add_to_queue(videos, "article.md", Path("videos/queue"))
```

## Support

| Question | Answer |
|----------|--------|
| How do I get started? | Read `SHORT_VIDEO_QUICKSTART.txt` (5 min) |
| What commands are available? | See `SHORT_VIDEO_GENERATOR_README.md` or `--help` |
| How do I integrate this? | Read `SHORT_VIDEO_INTEGRATION.md` (5 patterns) |
| Can I use this in Python? | Yes, full API in `short_video_generator.py` |
| What if FFmpeg isn't installed? | Clear error message with install instructions |
| Is the code production-ready? | Yes, error handling and logging included |

## Key Files Summary

```
scripts/
├── short_video_generator.py              ← Main engine (use this)
├── short_video_generator_examples.py     ← 7 working examples
├── SHORT_VIDEO_QUICKSTART.txt            ← Start here (5 min)
├── SHORT_VIDEO_GENERATOR_README.md       ← Complete reference
├── SHORT_VIDEO_GENERATOR_MANIFEST.md     ← Architecture & build
└── SHORT_VIDEO_INTEGRATION.md            ← Integration patterns

SHORTVIDEOS_START_HERE.md                 ← You are here
SHORT_VIDEO_GENERATOR_BUILD_SUMMARY.txt   ← Build summary
```

## One More Thing

The video generation system is modular. You can:
- Extract just key points: `article_to_keypoints(article)`
- Generate just voice: `generate_voiceover(text, output_path)`
- Create just slides: `create_slides(keypoints, title, output_dir)`
- Compose videos: `compose_video(audio, slides, music, output)`

Each function is standalone and documented. See the source code for details.

## Ready?

1. Install FFmpeg: `brew install ffmpeg espeak` (or apt-get on Linux)
2. Read: `cat scripts/SHORT_VIDEO_QUICKSTART.txt`
3. Try: `python scripts/short_video_generator_examples.py 1`
4. Generate: `python scripts/short_video_generator.py generate --article test.md --title "Test" --output videos/output`
5. Watch: Open the MP4 file in any video player

**Enjoy!** 🎥

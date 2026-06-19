# Short Video Generator - Integration Guide

This document explains how to integrate the Short Video Generator into your existing ProfitEngine content pipeline.

## Quick Integration (5 minutes)

### Step 1: Verify Dependencies

```bash
# Check FFmpeg installed
ffmpeg -version

# Check espeak installed (fallback TTS)
espeak --version

# (Optional) Install gTTS for better voice quality
pip install gtts
```

### Step 2: Generate Your First Video

```bash
# Create a test article
cat > test_article.md << 'EOF'
# Test Article: Investment Tips

## Tip 1: Start Small
You don't need much money to begin investing.

## Tip 2: Be Consistent
Small regular investments compound over time.

## Tip 3: Diversify
Spread investments across different assets.
EOF

# Generate video
python scripts/short_video_generator.py generate \
  --article test_article.md \
  --title "Investment Tips" \
  --output videos/test_output

# Check result
ls -la videos/test_output/reels/
ffplay videos/test_output/reels/investment-tips.mp4  # or open in any video player
```

### Step 3: Add to Content Pipeline

Add to your article publishing workflow:

```python
# In your publish function, after article is saved:
from pathlib import Path
from scripts.short_video_generator import generate_short_video, VideoConfig, add_to_queue

article_path = Path("articles/my-article.md")
article_title = "My Article Title"

# Generate videos
config = VideoConfig(style="tips", duration_sec=30)
videos = generate_short_video(
    article=article_path.read_text(),
    article_title=article_title,
    output_dir=Path("videos/output"),
    config=config,
    formats=["reels", "shorts"]
)

# Queue for review
queue_ids = add_to_queue(videos, str(article_path), Path("videos/queue"))
print(f"Videos queued: {queue_ids}")
```

## Integration Patterns

### Pattern 1: Content Factory Integration

After your content factory generates articles, also generate videos:

```bash
#!/bin/bash
# scripts/autopublish_with_videos.sh

CAMPAIGN_JSON="$1"
OUTPUT_DIR="$2"

# Run existing content factory
python scripts/content_factory_run.py \
  --campaign "$CAMPAIGN_JSON" \
  --output "$OUTPUT_DIR"

# Generate videos for each article
for article in "$OUTPUT_DIR"/*.md; do
  title=$(basename "$article" .md)
  
  python scripts/short_video_generator.py generate \
    --article "$article" \
    --title "$title" \
    --output "videos/$(basename $OUTPUT_DIR)" \
    --style tips \
    --queue-dir videos/queue &
done

wait
echo "✓ Content and videos generated"
```

### Pattern 2: Post-Publish Video Generation

Generate videos after article is live:

```python
# In your article publishing module
import subprocess
from pathlib import Path

def publish_article(article_path, article_title, publish_date):
    # ... existing publish logic ...
    
    # Generate videos asynchronously
    subprocess.Popen([
        "python", "scripts/short_video_generator.py", "generate",
        "--article", str(article_path),
        "--title", article_title,
        "--output", "videos/output",
        "--queue-dir", "videos/queue",
        "--style", "tips"
    ])
    
    return article_url
```

### Pattern 3: Batch Processing with Progress

Generate videos for multiple articles with tracking:

```python
from pathlib import Path
from scripts.short_video_generator import generate_short_video, VideoConfig, add_to_queue
import json

articles = list(Path("articles").glob("*.md"))
queue_dir = Path("videos/queue")

for i, article_path in enumerate(articles, 1):
    print(f"Processing {i}/{len(articles)}: {article_path.name}")
    
    config = VideoConfig(
        style="tips",
        duration_sec=30,
        background_music=True
    )
    
    videos = generate_short_video(
        article=article_path.read_text(),
        article_title=article_path.stem.replace("-", " ").title(),
        output_dir=Path("videos/output"),
        config=config,
        formats=["reels", "shorts"]
    )
    
    if videos:
        add_to_queue(videos, str(article_path), queue_dir)
        print(f"  ✓ Generated {len(videos)} formats")
    else:
        print(f"  ✗ Generation failed")

print("\nAll done! Review queue:")
print(f"  Queue dir: {queue_dir}")
```

### Pattern 4: Manual Review Workflow

Integrate with team review process:

```bash
#!/bin/bash
# scripts/video_review_workflow.sh

QUEUE_DIR="videos/queue"

echo "📹 PENDING VIDEOS FOR REVIEW"
echo "================================"

python scripts/short_video_generator.py queue --list --queue-dir "$QUEUE_DIR"

echo ""
echo "NEXT STEPS:"
echo "  ✓ Download videos and review thumbnails"
echo "  ✓ Test on your phone in landscape/portrait"
echo "  ✓ Check audio levels and pacing"
echo "  ✓ Approve with: python ... queue --status 'VIDEO_ID,approved'"
echo "  ✓ Reject with: python ... queue --status 'VIDEO_ID,rejected,Notes here'"
```

### Pattern 5: Scheduled Batch Generation

Run video generation on a schedule:

```bash
#!/bin/bash
# scripts/scheduled_video_gen.sh
# Add to crontab: 0 6 * * * /path/to/scripts/scheduled_video_gen.sh

# Find articles from yesterday
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
ARTICLE_DIR="generated-content"

# Generate videos for yesterday's articles
for article in "$ARTICLE_DIR"/*"$YESTERDAY"*.md; do
  [ -e "$article" ] || continue
  
  title=$(basename "$article" .md)
  
  python scripts/short_video_generator.py generate \
    --article "$article" \
    --title "$title" \
    --output "videos/$(date +%Y-%m-%d)" \
    --queue-dir "videos/queue"
done
```

## Platform-Specific Optimization

### For Instagram Reels

```bash
# Instagram loves vertical video with text overlays
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "Article Title" \
  --output videos/output \
  --formats reels \
  --style tips \  # Fast cuts work well
  --duration 30
```

Video tips:
- Add captions (auto-generated in final version)
- Use bright, contrasting colors
- Keep text readable on mobile
- Fast pacing keeps attention

### For YouTube Shorts

```bash
# YouTube Shorts allow up to 60 seconds
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "Article Title" \
  --output videos/output \
  --formats shorts \
  --style tutorial \  # Room for more content
  --duration 60
```

Video tips:
- Use intro/outro slides
- Include text hints for algo engagement
- High-quality audio important
- Vertical orientation critical

### For YouTube Standard

```bash
# YouTube standard format for upload
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "Article Title" \
  --output videos/output \
  --formats youtube \
  --style tutorial \  # More time for detailed explanation
  --duration 45
```

Video tips:
- 16:9 aspect ratio
- Can include intro cards
- Thumbnail quality matters more
- Title card helps

### For TikTok

```bash
# TikTok vertical format with aggressive cuts
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "Article Title" \
  --output videos/output \
  --formats tiktok \
  --style tips \  # Ultra-fast pacing
  --duration 20 \
  --voice-gender female  # Variety helps
```

Video tips:
- Shorter is better (15-20s)
- Fast cuts every 2-3 seconds
- Trending sounds matter more than script
- Hook in first 1 second

## Monitoring & Analytics

### Track Generated Videos

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

queue_dir = Path("videos/queue")

# Count videos by status
stats = {
    "pending": 0,
    "approved": 0,
    "rejected": 0,
    "published": 0
}

for manifest in queue_dir.glob("*.json"):
    data = json.loads(manifest.read_text())
    stats[data["status"]] += 1

print("Video Queue Statistics:")
print(f"  Pending:   {stats['pending']}")
print(f"  Approved:  {stats['approved']}")
print(f"  Rejected:  {stats['rejected']}")
print(f"  Published: {stats['published']}")

# Find videos from last 7 days
week_ago = datetime.now() - timedelta(days=7)
recent = []

for manifest in queue_dir.glob("*.json"):
    data = json.loads(manifest.read_text())
    created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    if created > week_ago:
        recent.append(data)

print(f"\nVideos from last 7 days: {len(recent)}")
for video in recent:
    print(f"  {video['video_id']}: {video['status']}")
```

### Performance Metrics

Track video generation performance:

```python
import time
import json
from pathlib import Path

def generate_with_metrics(article, title, output_dir):
    metrics = {"steps": {}}
    
    # Key points
    start = time.time()
    keypoints = article_to_keypoints(article)
    metrics["steps"]["extract_keypoints"] = time.time() - start
    
    # Voice-over
    start = time.time()
    generate_voiceover(...)
    metrics["steps"]["voice_over"] = time.time() - start
    
    # Slides
    start = time.time()
    create_slides(...)
    metrics["steps"]["slides"] = time.time() - start
    
    # Composition
    start = time.time()
    compose_video(...)
    metrics["steps"]["composition"] = time.time() - start
    
    # Save metrics
    metrics_file = output_dir / "metrics.json"
    metrics_file.write_text(json.dumps(metrics, indent=2))
    
    return metrics
```

## Troubleshooting Integration Issues

### Issue: Videos not generating

Check logs:
```bash
python scripts/short_video_generator.py generate \
  --article article.md \
  --title "Test" \
  --output videos/test 2>&1 | tee generation.log
```

Common causes:
- FFmpeg not installed
- Article file path incorrect
- Output directory not writable
- Insufficient disk space

### Issue: Slow generation

Expected timing:
- Keys extraction: <1s
- Voice-over: 5-15s
- Slides: 20-40s
- Composition: 30-60s
- **Total: 1-2 min per format**

To optimize:
- Use `--no-music` flag (saves ~10s)
- Reduce `--duration` parameter
- Generate one format at a time
- Use SSD for temporary files

### Issue: Poor audio quality

Solutions in order:
1. Install gTTS: `pip install gtts`
2. Reduce voice speed: `--voice-speed 0.9`
3. Simplify text (shorter sentences)
4. Test espeak quality on target system

## Advanced Integration

### Custom Slide Themes

Modify slide colors in source:
```python
# In short_video_generator.py, modify get_slide_color():
def get_slide_color(index: int) -> str:
    """Get brand colors instead of default palette."""
    brand_colors = [
        "003366",  # Your brand blue
        "FF6600",  # Your brand orange
        "CCCCCC",  # Light gray
        # ... add more
    ]
    return brand_colors[index % len(brand_colors)]
```

### Custom Voice Profiles

Create voice presets:
```python
VOICE_PROFILES = {
    "upbeat": {"gender": "female", "speed": 1.1, "style": "tips"},
    "authoritative": {"gender": "male", "speed": 0.9, "style": "news"},
    "storyteller": {"gender": "neutral", "speed": 1.0, "style": "tutorial"},
}

# Use in generation:
profile = VOICE_PROFILES["upbeat"]
videos = generate_short_video(..., voice_gender=profile["gender"])
```

### Platform-Specific Publishing

Auto-detect and optimize for platform:
```python
PLATFORM_CONFIGS = {
    "instagram": {"format": "reels", "duration": 30, "style": "tips"},
    "youtube": {"format": "shorts", "duration": 60, "style": "tutorial"},
    "tiktok": {"format": "tiktok", "duration": 20, "style": "tips"},
}

def generate_for_platform(article, title, platform):
    config = PLATFORM_CONFIGS[platform]
    return generate_short_video(
        article=article,
        article_title=title,
        config=VideoConfig(**config),
        formats=[config["format"]]
    )
```

## Next Steps After Integration

1. **Test with real content**
   - Generate videos from 3-5 existing articles
   - Test on mobile devices
   - Gather team feedback

2. **Optimize for your brand**
   - Adjust colors to match brand
   - Choose preferred voice profiles
   - Set default durations per style

3. **Set up review workflow**
   - Decide on approval process
   - Set team member responsibilities
   - Create publishing schedule

4. **Monitor performance**
   - Track which video styles perform best
   - Collect engagement metrics
   - Iterate on templates

5. **Scale to production**
   - Run daily/weekly batch generation
   - Automate queue management
   - Set up scheduled publishing

## Support & Questions

- See SHORT_VIDEO_QUICKSTART.txt for common commands
- See SHORT_VIDEO_GENERATOR_README.md for full API docs
- See short_video_generator_examples.py for working code
- Review inline comments in short_video_generator.py for implementation details

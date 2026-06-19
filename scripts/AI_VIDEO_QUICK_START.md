# AI Video Generator — Quick Start Guide

Get started generating AI videos in 5 minutes.

## Step 1: Install Dependencies

```bash
cd scripts

# Required
pip install Pillow anthropic pyttsx3

# Optional (recommended)
pip install google-cloud-texttospeech  # For Google TTS voice-over
```

## Step 2: Verify FFmpeg

```bash
ffmpeg -version

# If not found:
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html
```

## Step 3: Check Environment

```bash
# Ensure .env has at least one voice provider configured:
grep -E "ELEVEN|GOOGLE|OLLAMA" .env

# Example .env entries (copy if missing):
ELEVENLABS_API_KEY=sk_...                        # Optional but recommended
GMAOS_LOCAL_MODEL_ENDPOINT=http://localhost:11434
GMAOS_LOCAL_MODEL_NAME=llama3.1:8b
```

## Step 4: Generate Your First Video

```bash
# Simplest option (uses local Pyttsx3 - completely free)
python ai_video_generator.py generate "How to Make Money with AI"

# With ElevenLabs (best quality, if you have API key)
python ai_video_generator.py generate "How to Make Money with AI" --voice elevenlabs

# With Google TTS (good quality, if you have API key)
python ai_video_generator.py generate "How to Make Money with AI" --voice google_tts

# Longer tutorial (8 slides instead of default 5)
python ai_video_generator.py generate "My Complete AI Business Guide" --slides 8

# Specific video type
python ai_video_generator.py generate "Latest AI Trends" --type news_summary

# With auto-publish flag (reviews later)
python ai_video_generator.py generate "Topic" --auto-publish
```

## Step 5: Check Results

```bash
# Video output
ls -lh datacenter/ai_video_pipeline/distribution_masters/

# Example output:
# how-to-make-money-with-ai_a1b2c3d4e5f6.mp4  (15-30 MB)

# Review queue
ls -lh datacenter/ai_video_pipeline/review_queue/

# Audio files
ls -lh datacenter/ai_video_pipeline/audio/

# Scripts (cached)
ls -lh datacenter/ai_video_pipeline/scripts/
```

## Step 6: Review & Approve

```bash
# List pending reviews
python ai_video_generator.py review --list

# Approve video by script hash
python ai_video_generator.py review --approve abc123def456

# Video is now ready for publishing!
```

## Common Quick Recipes

### Free Offline (No API Keys)
```bash
python ai_video_generator.py generate "Topic"
```
Uses: Ollama (local) + Pyttsx3 (local)
Speed: 2-3 min per video
Quality: Good for 80% of use cases

### Premium Quality (Requires API Keys)
```bash
python ai_video_generator.py generate "Topic" --voice elevenlabs
```
Uses: Ollama (local) + ElevenLabs (API)
Speed: 2-4 min per video
Quality: Broadcast-ready voice
Cost: ~$0.03 per video

### Balanced (Recommended)
```bash
python ai_video_generator.py generate "Topic" --voice google_tts --slides 6
```
Uses: Ollama (local) + Google TTS (API)
Speed: 2-3 min per video
Quality: Professional voice
Cost: ~$0.001 per video (cheapest paid option)

### Batch Generation
```bash
# One-liner to generate 3 videos
for topic in "AI Tools" "Passive Income" "ChatGPT Tips"; do
  python ai_video_generator.py generate "$topic"
done
```

## Output Files

After running `generate`, you'll find:

```
datacenter/ai_video_pipeline/
├── distribution_masters/
│   └── {slug}_{hash}.mp4          ← Final video (ready to publish)
├── audio/
│   └── {hash}_{provider}.mp3      ← Voice-over audio
├── slides/
│   └── {slug}/
│       ├── slide_001.png
│       ├── slide_002.png
│       └── ...
├── logs/
│   └── {slug}.srt                 ← Subtitles (SRT format)
├── scripts/
│   └── {hash}.json                ← Generated script (cached)
└── review_queue/
    └── {hash}.json                ← Pending approval
```

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `ffmpeg not found` | Install FFmpeg (see Step 2) |
| `ModuleNotFoundError: Pillow` | `pip install Pillow` |
| `Connection refused (Ollama)` | Run `ollama serve` in another terminal |
| `Video too small error` | Use `--slides 8` for longer videos |
| `API rate limit` | Wait 60s or switch to pyttsx3 |
| `Script generation failed` | Ensure Ollama running OR set ANTHROPIC_API_KEY |

## Next Steps

1. **Try the examples:**
   ```bash
   python ai_video_examples.py all
   ```

2. **Read full documentation:**
   ```bash
   cat AI_VIDEO_GENERATOR_README.md
   ```

3. **Integrate with workflow:**
   - Add to `publish_article.py` for auto-video on article publish
   - Add to `social_media_publishers.py` for multi-platform posting
   - Add to `newsletter_publisher.py` for email promotion

4. **Monitor quality:**
   ```bash
   # Review generated videos
   python ai_video_generator.py review --list
   python ai_video_generator.py review --approve {hash}
   ```

5. **Set up GitHub hosting:**
   ```bash
   # Ensure GitHub token configured
   grep GITHUB_CONTENT_TOKEN .env
   # Videos auto-upload to GitHub content repo
   ```

## Performance Tips

- **Use pyttsx3 for speed** (instant generation, no API calls)
- **Batch videos at off-peak hours** (faster Ollama inference)
- **Reuse scripts** (hashed cache prevents duplication)
- **Use shorter slides** (SECONDS_PER_SLIDE=4 for snappier videos)
- **Disable HF images** if not needed (faster slide rendering)

## Cost Breakdown (Monthly)

| Scenario | Cost | Videos/Month |
|----------|------|--------------|
| Free (Ollama + Pyttsx3) | $0 | Unlimited |
| Balanced (Google TTS) | <$1 | 1000+ |
| Premium (ElevenLabs) | $10 | 30-50 |
| All services enabled | $15 | 100+ |

## Next: Production Setup

For production deployment:

1. Set up Ollama on OCI server (for model inference)
2. Configure all API keys in Vercel env vars
3. Create GitHub Actions workflow for auto-generation
4. Set up email notification on review queue
5. Create Slack bot for approval workflow

See: `AI_VIDEO_GENERATOR_README.md` → Integration with ProfitEngine Ecosystem

---

**Questions?** Check the full README or examples:
- `AI_VIDEO_GENERATOR_README.md` — Complete documentation
- `ai_video_examples.py` — 10 example scenarios
- `ai_video_generator.py` — Source code (well-commented)

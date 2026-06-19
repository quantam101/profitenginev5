# AI Video Generator for ProfitEngine

Complete end-to-end pipeline for generating AI-powered vertical video content (9:16 format) optimized for TikTok, YouTube Shorts, Instagram Reels, and other social platforms.

## Features

### 1. Intelligent Script Generation
- **Topic-to-Script Pipeline**: Convert article topics into detailed video scripts
- **AI Model Cascade**: Free Ollama (local) → Claude (key-gated) → Fallback
- **Multiple Video Types**:
  - Explainer videos (AI avatar explaining concepts)
  - Product demos (feature walkthroughs)
  - Tutorial videos (step-by-step guides)
  - News summary videos (trending topics)
  - Motivation/inspiration videos (success stories)
  - Educational content

### 2. Professional Voice-Over
- **ElevenLabs Integration**: Premium quality AI voices (Adam, Bella, etc.)
- **Google Text-to-Speech**: Free fallback with Neural2 voices
- **Local Pyttsx3**: Completely free, offline voice generation
- **Automatic Fallback Cascade**: Graceful degradation based on available APIs
- **Quality Control**: Standard vs Premium voice settings

### 3. Video Rendering
- **Vertical Format**: 1080x1920 (9:16) optimized for mobile
- **Gradient Backgrounds**: Animated color transitions per slide
- **Professional Typography**: Clear headline + body text hierarchy
- **Automatic Subtitles**: SRT subtitle generation from script
- **FFmpeg Processing**: H.264 codec, fast encoding preset

### 4. Quality Controls
- **Script Validation**: Min/max length enforcement
- **Slide Count Verification**: Ensure balanced video structure
- **File Size Checks**: Minimum video bytes threshold
- **Manual Review Queue**: All videos require approval before publishing
- **Hashbased Deduplication**: Prevent duplicate script generation

### 5. Monetization Integration
- **Gumroad Direct**: Sell video courses on Gumroad
- **YouTube Monetization**: Upload to YouTube for ad revenue
- **Email Integration**: Promote videos in newsletters
- **Affiliate Links**: Natural product mentions in descriptions
- **GitHub Hosting**: Free CDN for video content

## Installation

### Prerequisites

```bash
# macOS
brew install ffmpeg python3

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg python3 python3-pip

# Windows
# Download FFmpeg from https://ffmpeg.org/download.html
# Add to PATH, or use chocolatey: choco install ffmpeg
```

### Python Dependencies

```bash
cd scripts
pip install -r requirements.txt

# Core dependencies
pip install Pillow anthropic pyttsx3

# Optional: For Google TTS
pip install google-cloud-texttospeech

# Optional: For YouTube publishing
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Optional: For Gumroad API
pip install gumroad
```

### Environment Configuration

Add to your `.env` or `.env.local`:

```bash
# AI Models & Inference
GMAOS_LOCAL_MODEL_ENDPOINT=http://localhost:11434        # Ollama endpoint
GMAOS_LOCAL_MODEL_NAME=llama3.1:8b                      # Local model
ANTHROPIC_API_KEY=sk-ant-...                             # Claude fallback
OPENAI_API_KEY=sk-...                                    # (optional)

# Voice APIs
ELEVENLABS_API_KEY=sk_...                                # Premium voice-over
ELEVENLABS_VOICE_ID=9BWtsMINqrJLrRacOk9x                 # Adam voice (default)
GOOGLE_API_KEY=...                                        # Google TTS fallback

# GitHub Content Repo (video hosting)
GITHUB_CONTENT_TOKEN=ghp_...
GITHUB_CONTENT_OWNER=quantam101
GITHUB_CONTENT_REPO=content
GITHUB_VIDEO_DIR=assets/videos

# Video Rendering
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
SECONDS_PER_SLIDE=5
MIN_VIDEO_BYTES=250000

# Quality Controls
MIN_SCRIPT_LENGTH=500
MAX_SCRIPT_LENGTH=2000
MIN_SLIDES=3
MAX_SLIDES=12

# Monetization
CANONICAL_URL=https://www.alreadyherellc.com/content
AMAZON_AFFILIATE_TAG=alreadyhere-20
AFFILIATE_LINKS={...json...}
```

## Usage

### Basic Generation

```bash
# Generate explainer video (5 slides)
python scripts/ai_video_generator.py generate "How to Build Passive Income with AI"

# Generate tutorial (8 slides)
python scripts/ai_video_generator.py generate \
  "Complete Guide to Social Media Automation" \
  --type tutorial \
  --slides 8

# Generate news summary video
python scripts/ai_video_generator.py generate \
  "Top AI Trends in 2026" \
  --type news_summary \
  --slides 6
```

### Voice Provider Options

```bash
# Use ElevenLabs (premium quality - requires API key)
python scripts/ai_video_generator.py generate "Topic" --voice elevenlabs

# Use Google TTS (free with API key)
python scripts/ai_video_generator.py generate "Topic" --voice google_tts

# Use local Pyttsx3 (free, completely offline)
python scripts/ai_video_generator.py generate "Topic" --voice pyttsx3
```

### Auto-Publishing

```bash
# Generate video and schedule for auto-publish (after review)
python scripts/ai_video_generator.py generate "Topic" --auto-publish
```

### Review Queue Management

```bash
# List pending reviews
python scripts/ai_video_generator.py review --list

# Approve video by script hash
python scripts/ai_video_generator.py review --approve abc123def456
```

## Output Structure

All generated content is organized in `datacenter/ai_video_pipeline/`:

```
datacenter/ai_video_pipeline/
├── scripts/                    # Generated video scripts (cached by hash)
│   └── abc123def456.json
├── audio/                      # Voice-over audio files
│   ├── abc123def456_elevenlabs.mp3
│   ├── abc123def456_google.mp3
│   └── abc123def456_pyttsx3.wav
├── slides/
│   └── {slug}/
│       ├── slide_001.png
│       ├── slide_002.png
│       └── ...
├── distribution_masters/       # Final MP4 videos
│   └── how-to-build-passive-income_abc123def456.mp4
├── logs/                       # Rendering logs & subtitles
│   ├── {slug}.srt              # SRT subtitle file
│   ├── {slug}.vtt              # WebVTT subtitle file
│   ├── video_publish_report.json
│   └── capability_manifest.json
└── review_queue/               # Pending manual approval
    └── abc123def456.json       # Review metadata
```

## API Integration Details

### Script Generation Cascade

1. **Ollama (Free Local)** — Runs on OCI A1 ARM CPU
   - Model: `llama3.1:8b` or configured `GMAOS_LOCAL_MODEL_NAME`
   - No API key required
   - Completely offline

2. **Claude (Key-Gated)** — Anthropic API fallback
   - Model: `claude-3-5-sonnet-20241022`
   - Requires `ANTHROPIC_API_KEY`
   - Used when Ollama unavailable

3. **OpenAI (Optional)** — Additional fallback
   - Requires `OPENAI_API_KEY`
   - Not used by default

### Voice-Over Cascade

1. **ElevenLabs** (Premium)
   - API: `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`
   - Voices: Adam (9BWtsMINqrJLrRacOk9x), Bella, etc.
   - Quality: Near-human naturalness
   - Cost: ~$0.30 per 1M characters

2. **Google Text-to-Speech** (Moderate)
   - API: `google.cloud.texttospeech`
   - Voices: Neural2-C (Neural voice)
   - Quality: Natural sounding
   - Cost: $16 per 1M characters

3. **Pyttsx3** (Free Local)
   - Completely offline, no API
   - Quality: Robotic but functional
   - Cost: Free

### Video Hosting

Videos are uploaded to GitHub content repository:

```
GitHub: quantam101/content
Path: assets/videos/{timestamp}-{slug}.mp4
URL: https://raw.githubusercontent.com/quantam101/content/main/assets/videos/{filename}
```

## Script Generation Example

**Input Topic:**
```
"Best AI Tools for Passive Income in 2026"
```

**Generated Script Output:**
```json
{
  "headline": "Turn AI Into Passive Income: 5 Tools Making $5K+/Month",
  "body": "Discover the AI-powered tools and strategies entrepreneurs are using to build automated income streams. From content creation to course sales, learn which tools actually deliver results.",
  "ctas": [
    "Check out all tools at alreadyherellc.com/content",
    "Subscribe for weekly AI updates",
    "Start your free trial with tools below"
  ],
  "slides": [
    {
      "headline": "ChatGPT: The Content Machine",
      "body": "Use ChatGPT to generate blog posts, email sequences, and sales copy in minutes. Thousands of creators are earning $2K-5K monthly with AI-generated content.",
      "visual_prompt": "professional AI content creator workspace with laptop showing ChatGPT interface, modern minimalist desk, natural lighting"
    },
    {
      "headline": "Midjourney: AI Art on Demand",
      "body": "Create viral-worthy graphics, thumbnails, and product mockups without design skills. Use for social media, digital products, or agency services.",
      "visual_prompt": "vibrant Midjourney AI-generated art gallery display, fantasy and realistic images, artistic lighting"
    },
    ...
  ],
  "estimated_duration": 245.0
}
```

## Quality Control Checklist

Before videos are published, they go through:

- [ ] Script validation (500-2000 words)
- [ ] Slide count verification (3-12 slides)
- [ ] Audio quality check (voice clarity)
- [ ] Video file size check (min 250KB)
- [ ] Subtitle accuracy review
- [ ] Brand compliance review
- [ ] CTA effectiveness review
- [ ] Manual approval required

## Monetization Strategies

### 1. YouTube Ad Revenue
- Upload approved videos to YouTube
- Enable monetization after 1K subscribers / 4K watch hours
- Estimated earnings: $3-8 per 1000 views

### 2. Gumroad Digital Products
- Bundle videos into courses on Gumroad
- Price: $27-197 per course
- Estimated earnings: 10-20% conversion, $500-2000 per launch

### 3. Email List Building
- Promote videos in newsletters
- Build audience for affiliate promotions
- Estimated earnings: $100-500 per campaign

### 4. Affiliate Marketing
- Naturally mention tools in descriptions
- Include affiliate links to ElevenLabs, Midjourney, etc.
- Estimated earnings: 5-20% commission per sale

### 5. Corporate Sponsorship
- Brands sponsor individual videos
- Estimated earnings: $500-5000 per sponsored video

## Troubleshooting

### FFmpeg Not Found
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
# Or: choco install ffmpeg
```

### Ollama Connection Refused
```bash
# Ensure Ollama is running
ollama serve

# Fallback to Claude by ensuring ANTHROPIC_API_KEY is set
```

### ElevenLabs API Rate Limit
```
Error: 429 Too Many Requests

Solution:
1. Wait 60 seconds before retry
2. Use google_tts or pyttsx3 as fallback
3. Upgrade ElevenLabs subscription tier
```

### Video Too Small
```
Error: video output too small for production (120000 bytes < 250000)

Solution:
1. Increase MIN_VIDEO_BYTES check in code
2. Use longer script (more slides)
3. Lower VIDEO_WIDTH/HEIGHT if needed
```

### Pillow Not Installed
```bash
pip install Pillow
```

## Performance Metrics

### Typical Generation Time

| Step | Duration | Notes |
|------|----------|-------|
| Script gen (Ollama) | 30-60s | Free local inference |
| Voice-over (ElevenLabs) | 10-30s | Depends on text length |
| Slide rendering | 5-15s | 5 slides @ 1080x1920 |
| FFmpeg encoding | 60-180s | H.264 @ veryfast preset |
| GitHub upload | 30-120s | Depends on file size |
| **Total** | **2-7 min** | End-to-end |

### File Sizes

| Component | Size | Notes |
|-----------|------|-------|
| MP4 Video (5 slides) | 15-30 MB | Depends on duration |
| Audio (3-5 min) | 1-5 MB | MP3 @ 128kbps |
| Slide images (5) | 5-10 MB | PNG @ 1080x1920 |
| JSON script | 5-20 KB | Compressed text |

## Advanced Configuration

### Custom Voice ID
```bash
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"  # Bella voice
python scripts/ai_video_generator.py generate "Topic"
```

### Custom Video Dimensions
```bash
export VIDEO_WIDTH=1080
export VIDEO_HEIGHT=1920
# Or landscape:
export VIDEO_WIDTH=1920
export VIDEO_HEIGHT=1080
```

### Custom Slide Duration
```bash
export SECONDS_PER_SLIDE=4  # Faster pacing
```

### Offline Mode (Pyttsx3 + Ollama Only)
```bash
# Disable all API calls except Ollama
python scripts/ai_video_generator.py generate "Topic" --voice pyttsx3
```

## Integration with ProfitEngine Ecosystem

### Publish Article Trigger
```bash
# From publish_article.py
# Automatically generate video for each published article
python scripts/ai_video_generator.py generate "{article_topic}"
```

### Newsletter Integration
```bash
# From newsletter_publisher.py
# Add video thumbnail + link to email
# Featured in daily newsletter
```

### Social Distribution
```bash
# From social_media_publishers.py
# Auto-post to TikTok, YouTube Shorts, Instagram Reels
# Once approved from review queue
```

### Gumroad Automation
```bash
# From gumroad_publisher.py
# Create video course product
# Auto-generate product page + description
```

## API Costs & Limits

### Free/Included Services
- Ollama (self-hosted): Free
- Pyttsx3: Free
- FFmpeg: Free
- GitHub content hosting: Free (1GB limit)

### Paid APIs (Optional)

| Service | Cost | Usage |
|---------|------|-------|
| ElevenLabs | $0.30 per 1M chars | 100K = $0.03 |
| Google TTS | $16 per 1M chars | 100K = $0.0016 |
| Claude API | $3-15 per 1M tokens | 10K tokens = $0.03-0.15 |
| YouTube Storage | Free | 1TB included |
| Gumroad | 10% + $0.30 fee | No storage cost |

## Future Enhancements

- [ ] Runway ML video generation (next phase)
- [ ] Synthesia AI avatar integration
- [ ] DALL-E 3 image generation for slides
- [ ] Multi-language support
- [ ] Real-time video preview
- [ ] A/B testing different voice providers
- [ ] Automated performance metrics tracking
- [ ] TikTok trending topic integration

## License

ProfitEngine V5 — All rights reserved.

Contact: ops@alreadyherellc.com

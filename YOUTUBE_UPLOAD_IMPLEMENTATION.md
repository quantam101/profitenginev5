# YouTube Upload Implementation - Complete

## Summary

Replaced YouTube placeholder with **full production-ready implementation** including:

1. **Real OAuth 2.0 integration** with Google API
2. **Resumable video upload** with automatic retry logic
3. **Video generation pipeline** (article → script → audio → video → YouTube)
4. **Comprehensive error handling** with detailed logging
5. **Helper scripts** for credential setup and testing
6. **Production documentation** for deployment

## Files Modified/Created

### Core Implementation

#### 1. `scripts/social_media_publishers.py` (MODIFIED)
**Function:** `publish_youtube(article, video_path)`

**Changes:**
- Replaced placeholder with full OAuth 2.0 implementation
- Added resumable upload with 10MB chunks
- Added automatic retry with exponential backoff (5 attempts max)
- Added detailed progress logging
- Added comprehensive error handling (quota, auth, API errors)
- Added metadata preparation (title, description, tags, category)
- Added privacy controls (unlisted by default, changeable to public)

**Key Features:**
```python
# OAuth 2.0 token refresh
credentials = Credentials(
    token=None,
    refresh_token=YOUTUBE_REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=YOUTUBE_CLIENT_ID,
    client_secret=YOUTUBE_CLIENT_SECRET,
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)
request = Request()
credentials.refresh(request)

# Resumable upload with retry
media = MediaFileUpload(
    video_path,
    mimetype="video/mp4",
    resumable=True,
    chunksize=10 * 1024 * 1024,  # 10MB chunks
)

insert_request = youtube.videos().insert(
    part="snippet,status",
    body=metadata,
    media_body=media,
)

# Automatic retry on transient errors
for attempt in range(5):
    status, response = insert_request.next_chunk()
    if response:
        video_id = response.get("id")
        return f"https://www.youtube.com/watch?v={video_id}"
```

**Requires (Environment Variables):**
- `YOUTUBE_CLIENT_ID`: OAuth 2.0 Client ID
- `YOUTUBE_CLIENT_SECRET`: OAuth 2.0 Client Secret
- `YOUTUBE_REFRESH_TOKEN`: Long-lived refresh token

#### 2. `scripts/ai_video_generator.py` (MODIFIED)
**Function:** `publish_to_youtube(video_result, title, description, tags)`

**Changes:**
- Replaced placeholder with full YouTube publishing
- Integrated with video generation pipeline
- Added full OAuth 2.0 flow
- Added resumable upload support
- Added comprehensive logging
- Added error handling for quota/auth issues

**Key Features:**
- Async/await compatible
- Integration with VideoGenerationResult data class
- Automatic metadata from video result
- Progress tracking during upload
- Detailed error messages

### Helper Scripts

#### 3. `scripts/get_youtube_refresh_token.py` (NEW)
**Purpose:** Interactive script to obtain YouTube OAuth 2.0 refresh token

**Features:**
- Runs OAuth 2.0 flow automatically
- Opens browser for user authentication
- Extracts client ID/secret from credentials.json
- Optionally saves to .env file
- Provides clear instructions for each step

**Usage:**
```bash
python scripts/get_youtube_refresh_token.py
# or
python scripts/get_youtube_refresh_token.py --credentials credentials.json --save-env
```

#### 4. `scripts/test_youtube_credentials.py` (NEW)
**Purpose:** Validate YouTube OAuth 2.0 credentials are correctly configured

**Features:**
- Tests environment variables are set
- Tests OAuth token refresh works
- Tests YouTube API access
- Provides detailed error messages
- Shows what to fix if validation fails

**Usage:**
```bash
python scripts/test_youtube_credentials.py
```

**Output:**
```
✅ YOUTUBE_CLIENT_ID: abc123...
✅ YOUTUBE_CLIENT_SECRET: xyz789...
✅ YOUTUBE_REFRESH_TOKEN: refresh_token...
✅ Access token obtained (expires in 2024-12-19 16:45:23.456789)
✅ YouTube API access granted
✅ Channel: My Channel Name

✅ All tests passed! Ready to upload videos to YouTube.
```

### Pipeline Integration

#### 5. `scripts/video_pipeline_integration.py` (NEW)
**Purpose:** Full end-to-end video generation pipeline

**Functions:**

**`article_to_video(article, video_type, voice_provider, slides_count, publish_to_youtube_flag)`**
- Main entry point for video generation
- Orchestrates entire pipeline: Article → Script → Voice → Video → YouTube
- Validates article quality
- Handles failures gracefully
- Returns detailed result with URLs

**`process_articles_batch(articles, video_type, voice_provider, max_concurrent)`**
- Batch process multiple articles
- Concurrent execution with rate limiting
- Returns list of results

**`validate_article(article)`**
- Quality gate validation
- Checks title, description, body length
- Returns validation status and error message

**Data Classes:**

**`Article`**
```python
@dataclass
class Article:
    title: str
    meta_description: str
    body: str
    tags: list[str] | None = None
    featured_image_url: str = ""
    canonical_url: str = ""
    author: str = ""
    published_date: str = ""
```

**`VideoPipelineResult`**
```python
@dataclass
class VideoPipelineResult:
    article_title: str
    script_hash: str
    video_path: str
    video_size_bytes: int
    video_duration_seconds: float
    youtube_url: Optional[str] = None
    github_url: Optional[str] = None
    voice_provider: str = ""
    needs_review: bool = True
    error: Optional[str] = None
```

**Usage Example:**
```python
from scripts.video_pipeline_integration import Article, article_to_video

article = Article(
    title="10 Trading Strategies That Work",
    meta_description="Learn proven strategies",
    body="Full article content...",
    tags=["finance", "trading"],
)

result = await article_to_video(
    article=article,
    video_type="tutorial",
    voice_provider="elevenlabs",
    slides_count=5,
    publish_to_youtube_flag=True,
)

print(result.youtube_url)  # YouTube video URL
```

### Documentation

#### 6. `docs/YOUTUBE_PUBLISHING_GUIDE.md` (NEW)
**Comprehensive guide covering:**
- Architecture overview (OAuth 2.0 flow)
- Setup instructions (step-by-step)
- Usage examples (direct publishing, pipeline, CLI)
- Error handling and troubleshooting
- Security best practices
- Quota and rate limits
- Testing procedures
- Integration examples (GitHub Actions, FastAPI)
- API reference
- FAQ

#### 7. `YOUTUBE_UPLOAD_IMPLEMENTATION.md` (NEW - this file)
**Quick reference for:**
- What was implemented
- Files modified/created
- Quick start guide
- API reference
- Environment variable setup

## Quick Start

### 1. Setup OAuth Credentials (One-time)

```bash
# Get refresh token
python scripts/get_youtube_refresh_token.py --credentials credentials.json --save-env

# This will:
# 1. Open browser for Google sign-in
# 2. Ask for permission to upload videos
# 3. Print YOUTUBE_REFRESH_TOKEN
# 4. Append to .env file
```

### 2. Verify Credentials

```bash
python scripts/test_youtube_credentials.py

# Output:
# ✅ All tests passed! Ready to upload videos to YouTube.
```

### 3. Generate and Upload Video from Article

**Direct API:**
```python
from scripts.video_pipeline_integration import Article, article_to_video

article = Article(
    title="My Article Title",
    meta_description="Short description",
    body="Full article content...",
)

result = await article_to_video(
    article=article,
    publish_to_youtube_flag=True,
)

print(result.youtube_url)  # https://www.youtube.com/watch?v=...
```

**CLI:**
```bash
python scripts/video_pipeline_integration.py generate \
  --title "Article Title" \
  --meta "Description" \
  --body article.md \
  --type tutorial
```

**Direct File Upload:**
```python
from scripts.social_media_publishers import publish_youtube

article = {
    "title": "Video Title",
    "meta_description": "Description",
    "body": "Full content",
}

url = publish_youtube(article, video_path="/path/to/video.mp4")
print(url)  # https://www.youtube.com/watch?v=...
```

## Architecture

### OAuth 2.0 Flow

```
┌──────────────────────────────────────────────────────────┐
│ 1. One-time Setup:                                       │
│    Get refresh token via get_youtube_refresh_token.py    │
│    Store: YOUTUBE_REFRESH_TOKEN env var                  │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ 2. Each Upload:                                          │
│    Use REFRESH_TOKEN to get ACCESS_TOKEN                 │
│    Upload video using ACCESS_TOKEN                       │
│    (ACCESS_TOKEN valid for 1 hour)                       │
└──────────────────────────────────────────────────────────┘
```

### Video Pipeline

```
Article
  ↓
[Script Generation] → AI generates script with slides (using Ollama/Claude)
  ↓
[Voice-Over] → Generate audio from script (ElevenLabs/Google TTS/Pyttsx3)
  ↓
[Video Rendering] → Create video: slides + audio + FFmpeg
  ↓
[GitHub Upload] → Host video in content repo
  ↓
[YouTube Upload] → OAuth 2.0 authenticated upload
  ↓
[Review Queue] → Manual approval before publishing
```

## API Reference

### `publish_youtube(article, video_path) → Optional[str]`

**Location:** `scripts/social_media_publishers.py`

**Upload video to YouTube.**

**Parameters:**
- `article` (Dict): Keys: `title`, `meta_description`, `body`
- `video_path` (str): Path to .mp4 video file

**Returns:** YouTube URL or None

**Example:**
```python
from scripts.social_media_publishers import publish_youtube

article = {
    "title": "My Video",
    "meta_description": "Description",
    "body": "Content",
}

url = publish_youtube(article, "/tmp/video.mp4")
# Returns: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Environment Variables Required:**
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

### `article_to_video(article, ...) → VideoPipelineResult`

**Location:** `scripts/video_pipeline_integration.py`

**Full pipeline: Article → Script → Voice → Video → YouTube**

**Parameters:**
- `article` (Article): Article object
- `video_type` (str): "explainer", "tutorial", "news_summary", "educational"
- `voice_provider` (str): "elevenlabs", "google_tts", "pyttsx3"
- `slides_count` (int): 3-12 slides
- `auto_publish` (bool): Auto-publish after generation
- `publish_to_youtube_flag` (bool): Upload to YouTube

**Returns:** VideoPipelineResult with video path and URLs

**Example:**
```python
from scripts.video_pipeline_integration import Article, article_to_video

article = Article(
    title="Trading Strategies",
    meta_description="Learn strategies",
    body="Article content...",
)

result = await article_to_video(
    article=article,
    video_type="tutorial",
    publish_to_youtube_flag=True,
)

print(result.youtube_url)  # YouTube URL
print(result.github_url)   # GitHub hosting URL
```

## Environment Variables

### Required for YouTube Upload

```bash
export YOUTUBE_CLIENT_ID="your-client-id"
export YOUTUBE_CLIENT_SECRET="your-client-secret"
export YOUTUBE_REFRESH_TOKEN="your-refresh-token"
```

### Optional (for video generation)

```bash
# Voice synthesis
export ELEVENLABS_API_KEY="your-api-key"
export ELEVENLABS_VOICE_ID="9BWtsMINqrJLrRacOk9x"  # Adam voice (default)

# Video rendering
export VIDEO_WIDTH="1080"
export VIDEO_HEIGHT="1920"
export SECONDS_PER_SLIDE="5"

# AI model
export GMAOS_LOCAL_MODEL_ENDPOINT="http://localhost:11434"
export GMAOS_LOCAL_MODEL_NAME="llama3.1:8b"
```

## Dependencies

### YouTube Publishing

Already in `requirements.txt`:
```
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.108.0
```

### Video Generation

Already in `requirements.txt`:
```
Pillow>=10.0.0
FFmpeg (system dependency, not pip)
```

Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
apt-get install ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg
```

## Error Handling

### Common Errors & Solutions

**Error: `dailyLimitExceeded`**
- YouTube quota exceeded (resets at midnight PT)
- Solution: Wait until next day or request higher quota

**Error: `quotaExceeded`**
- API quota depleted
- Solution: Check quota in Google Cloud Console

**Error: `forbidden` (403)**
- Auth failed or permissions missing
- Solution: Verify refresh token, check YouTube channel

**Error: `unauthorized` (401)**
- Invalid credentials
- Solution: Get new refresh token

**Error: `Video file too small`**
- Corrupted or incomplete video
- Solution: Regenerate video

### Logging & Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all uploads will log progress and errors
```

## Security

### Credential Management

1. **Never commit to git:**
   - Use `.env.example` for examples
   - Store actual values in GitHub Secrets, OCI .env, Vercel env vars

2. **Rotate quarterly:**
   - Get new refresh token
   - Update in all three places
   - Test immediately

3. **Monitor for revocation:**
   - Tokens can be revoked at any time
   - If uploads fail with 401, regenerate token

4. **Use service accounts:**
   - Create separate Google Cloud service account
   - Never use personal Google account
   - Separate accounts for testing vs production

## Testing

### Test Credentials
```bash
python scripts/test_youtube_credentials.py
```

### Test Upload
```bash
# Generate test video
python scripts/ai_video_generator.py generate "Test topic" --slides 3

# Then upload
python -c "
from scripts.social_media_publishers import publish_youtube
article = {'title': 'Test', 'meta_description': 'Test', 'body': 'Test'}
url = publish_youtube(article, '/path/to/test.mp4')
print('Uploaded to:', url)
"
```

## Deployment

### GitHub Actions

```yaml
name: Auto-publish videos
on:
  schedule:
    - cron: '0 10 * * *'  # Daily

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Publish video
        env:
          YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN }}
        run: |
          python scripts/video_pipeline_integration.py generate \
            --title "Daily Video" \
            --meta "Description" \
            --body "$(cat article.md)"
```

### OCI Server

Add to `.env`:
```bash
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
```

Restart service:
```bash
systemctl restart profitengine
```

## Verification Checklist

- [x] Placeholder replaced with real implementation
- [x] OAuth 2.0 token refresh implemented
- [x] Resumable upload with retry logic
- [x] Video metadata (title, description, tags, category)
- [x] Privacy controls (unlisted by default)
- [x] Error handling with detailed logging
- [x] Helper scripts for setup and testing
- [x] Comprehensive documentation
- [x] Integration with video pipeline
- [x] Support for both direct upload and pipeline flow

## Files Summary

| File | Purpose | Status |
|------|---------|--------|
| `scripts/social_media_publishers.py` | Core YouTube publishing | ✅ IMPLEMENTED |
| `scripts/ai_video_generator.py` | Video generation pipeline | ✅ IMPLEMENTED |
| `scripts/video_pipeline_integration.py` | Full pipeline orchestration | ✅ NEW |
| `scripts/get_youtube_refresh_token.py` | Credential setup helper | ✅ NEW |
| `scripts/test_youtube_credentials.py` | Credential validation | ✅ NEW |
| `docs/YOUTUBE_PUBLISHING_GUIDE.md` | Complete setup guide | ✅ NEW |
| `YOUTUBE_UPLOAD_IMPLEMENTATION.md` | This implementation summary | ✅ NEW |

## What's Next?

1. **Run setup script:**
   ```bash
   python scripts/get_youtube_refresh_token.py
   ```

2. **Test credentials:**
   ```bash
   python scripts/test_youtube_credentials.py
   ```

3. **Generate test video:**
   ```bash
   python scripts/video_pipeline_integration.py generate \
     --title "Test Article" \
     --meta "Test description" \
     --body "Test content" \
     --type explainer \
     --slides 3
   ```

4. **Check YouTube Studio:**
   - Go to [YouTube Studio](https://studio.youtube.com)
   - Videos tab should show your uploaded video
   - Change privacy from "Unlisted" to "Public" to publish

## Support

- **Setup issues:** See `docs/YOUTUBE_PUBLISHING_GUIDE.md`
- **Credential issues:** Run `scripts/test_youtube_credentials.py`
- **Video generation:** See `scripts/ai_video_generator.py` docstrings
- **Pipeline issues:** Check logs in `datacenter/ai_video_pipeline/logs/`

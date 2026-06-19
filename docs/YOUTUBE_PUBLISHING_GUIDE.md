# YouTube Publishing Integration Guide

## Overview

ProfitEngine can now automatically generate videos from articles and publish them to YouTube using OAuth 2.0 authentication.

**Full video pipeline:**
1. **Article** → AI-generated script (using Claude/Ollama)
2. **Script** → Voice-over audio (ElevenLabs, Google TTS, or Pyttsx3)
3. **Voice** → Video rendering (slideshow with images + audio via FFmpeg)
4. **Video** → YouTube upload (OAuth 2.0 with refresh token)

## Architecture

### OAuth 2.0 Flow

ProfitEngine uses **OAuth 2.0 with Refresh Token** for YouTube authentication:

```
┌─────────────────────────────────────────────────────────┐
│ Initial Setup (one-time, manual):                       │
│ 1. Create OAuth 2.0 credentials in Google Cloud Console │
│ 2. Run OAuth flow to get REFRESH_TOKEN                  │
│ 3. Store REFRESH_TOKEN in environment                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Runtime (automatic):                                    │
│ 1. Use REFRESH_TOKEN to get ACCESS_TOKEN                │
│ 2. Upload video using ACCESS_TOKEN                      │
│ 3. ACCESS_TOKEN expires after 1 hour                    │
│ 4. Next upload automatically gets new ACCESS_TOKEN      │
└─────────────────────────────────────────────────────────┘
```

### Credentials

Three credentials required:
- `YOUTUBE_CLIENT_ID`: OAuth 2.0 Client ID
- `YOUTUBE_CLIENT_SECRET`: OAuth 2.0 Client Secret  
- `YOUTUBE_REFRESH_TOKEN`: Long-lived refresh token (valid indefinitely until revoked)

## Setup Instructions

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the **YouTube Data API v3**:
   - Search for "YouTube Data API v3"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. Go to [Credentials page](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose **"Desktop application"** as the application type
4. Click "Create"
5. Click the created credential to open it
6. Click "Download JSON" and save as `credentials.json`

### Step 3: Get Refresh Token

Run the OAuth flow to get the refresh token:

```bash
# Option A: Using google-auth-oauthlib directly
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
scopes = ['https://www.googleapis.com/auth/youtube.upload']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
creds = flow.run_local_server(port=0)
print('Refresh token:', creds.refresh_token)
"

# Option B: Using our helper script
python scripts/get_youtube_refresh_token.py --credentials credentials.json
```

This will:
1. Open a browser for you to sign in with your Google account
2. Ask you to grant permission to upload videos
3. Print your `YOUTUBE_REFRESH_TOKEN`

**Important:** Save this token securely. It never expires unless you revoke it.

### Step 4: Store Credentials

#### GitHub Secrets (for CI/CD)

1. Go to repository Settings → Secrets and variables → Actions
2. Create three new secrets:
   - `YOUTUBE_CLIENT_ID`: paste from credentials.json
   - `YOUTUBE_CLIENT_SECRET`: paste from credentials.json
   - `YOUTUBE_REFRESH_TOKEN`: paste from step 3

#### OCI Server (for runtime)

SSH into the OCI server and add to `.env`:

```bash
export YOUTUBE_CLIENT_ID="your-client-id"
export YOUTUBE_CLIENT_SECRET="your-client-secret"
export YOUTUBE_REFRESH_TOKEN="your-refresh-token"
```

Restart the server:
```bash
systemctl restart profitengine
```

#### Vercel (if using frontend)

1. Go to Vercel project settings → Environment Variables
2. Add the same three variables
3. Redeploy

## Usage

### Direct Publishing from Articles

Using the video pipeline integration:

```python
from scripts.video_pipeline_integration import Article, article_to_video

article = Article(
    title="10 Trading Strategies That Work",
    meta_description="Learn proven strategies to increase profits",
    body="Full article content here...",
    tags=["finance", "investing", "trading"],
)

result = await article_to_video(
    article=article,
    video_type="explainer",  # or: tutorial, news_summary, educational
    voice_provider="elevenlabs",  # or: google_tts, pyttsx3
    slides_count=5,
    publish_to_youtube_flag=True,  # Automatically upload to YouTube
)

print(result.youtube_url)  # https://www.youtube.com/watch?v=...
```

### Direct Publishing from Video File

Using the social media publisher:

```python
from scripts.social_media_publishers import publish_youtube

article = {
    "title": "My Video Title",
    "meta_description": "Video description",
    "body": "Full article text...",
}

url = publish_youtube(article, video_path="/path/to/video.mp4")
print(url)  # https://www.youtube.com/watch?v=...
```

### CLI Usage

```bash
# Generate video from article file
python scripts/video_pipeline_integration.py generate \
  --title "Article Title" \
  --meta "Meta description" \
  --body article.md \
  --type explainer \
  --voice elevenlabs \
  --slides 5

# Skip YouTube upload (just generate video)
python scripts/video_pipeline_integration.py generate \
  --title "Article Title" \
  --meta "Meta description" \
  --body article.md \
  --no-youtube
```

## Video Metadata

Videos are published with:

- **Title**: Article title (max 100 chars)
- **Description**: Meta + article body + link (max 5000 chars)
- **Tags**: finance, investing, profitengine, markets, trading
- **Category**: 22 (People & Blogs)
- **Privacy**: **Unlisted** (not searchable, but accessible via direct link)
  - Change in code to "public" to make searchable

## Resumable Uploads

Videos are uploaded using **resumable uploads**, which means:

- Uploads can be **paused and resumed** if interrupted
- Automatic **retry with exponential backoff** on transient errors (5xx)
- Maximum **5 retry attempts** before failing
- **10MB chunks** for faster resumable upload
- Progress logged during upload

## Error Handling

### Common Errors

**Error: `dailyLimitExceeded`**
- YouTube API quota exceeded
- Solution: Try again tomorrow (quota resets at midnight Pacific Time)
- Check quota: [Google Cloud Console → Quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

**Error: `quotaExceeded`**
- API quota exceeded
- Solution: Increase quota in Google Cloud Console or wait for reset
- Request higher quota: [Google Cloud Console → Quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

**Error: `forbidden` (403)**
- YouTube channel issue or missing permissions
- Solutions:
  - Verify YouTube channel exists and is in good standing
  - Check `youtube.upload` scope in OAuth consent
  - Verify refresh token not revoked (check [Google Account Security](https://myaccount.google.com/device-activity))

**Error: `unauthorized` (401)**
- OAuth credentials invalid
- Solutions:
  - Verify `YOUTUBE_CLIENT_ID` and `YOUTUBE_CLIENT_SECRET` are correct
  - Get new refresh token (old one may be revoked)
  - Check environment variables are set

**Error: `Video file too small`**
- Video file corrupted or incomplete
- Solution: Regenerate video using video pipeline

### Logging

Enable debug logging to troubleshoot:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Monitoring

### Track Upload Progress

```python
import logging

# Set up logging to see progress
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s: %(message)s"
)

# Now uploads will log:
# [16:45:23] scripts.social_media_publishers: [YouTube] Upload progress: 25%
# [16:45:34] scripts.social_media_publishers: [YouTube] Upload progress: 50%
# [16:45:45] scripts.social_media_publishers: [YouTube] Upload progress: 75%
# [16:45:56] scripts.social_media_publishers: [OK] Published to YouTube: https://www.youtube.com/watch?v=...
```

### YouTube Studio

Monitor all uploads at [YouTube Studio](https://studio.youtube.com/channel/):

1. Go to YouTube Studio
2. Click "Videos" in left sidebar
3. See all uploaded videos (sorted by most recent)
4. Click on a video to edit metadata
5. Change privacy setting from "Unlisted" to "Public" to publish

## Security Best Practices

1. **Never commit credentials to git**
   - Use `.env.example` for examples only
   - Store actual values in GitHub Secrets, OCI .env, Vercel env vars

2. **Rotate refresh token quarterly**
   - Get a new token following Step 3 above
   - Update in all three places: GitHub Secrets, OCI .env, Vercel env vars
   - Test upload immediately after rotation

3. **Monitor for revoked tokens**
   - Tokens can be revoked at any time by user actions
   - If uploads suddenly fail with 401, refresh token may be revoked
   - Solution: Generate new refresh token and update everywhere

4. **Use service accounts for production**
   - Create a separate Google Cloud service account for uploads
   - Never use personal Google account credentials
   - Separate service account for testing vs. production

5. **Limit API quotas**
   - YouTube Data API has default quotas (10,000 units/day)
   - Each video upload uses ~1500 quota units
   - Monitor usage at [Google Cloud Console → Quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
   - Request higher quota if needed

## Testing

### Test Credentials

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def test_youtube_credentials():
    """Test if YouTube credentials are valid."""
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ Missing credentials")
        return False

    try:
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
        
        request = Request()
        credentials.refresh(request)
        print("✅ Credentials valid")
        return True
    except Exception as e:
        print(f"❌ Credentials invalid: {e}")
        return False

# Run test
if test_youtube_credentials():
    print("Ready to upload videos!")
```

### Test Upload

```bash
# Generate a small test video
python scripts/ai_video_generator.py generate \
  "Test video topic" \
  --type explainer \
  --slides 3 \
  --voice pyttsx3

# Then upload to YouTube
python -c "
from scripts.social_media_publishers import publish_youtube
article = {
    'title': 'Test Upload',
    'meta_description': 'Testing YouTube upload',
    'body': 'This is a test video',
}
url = publish_youtube(article, '/path/to/test_video.mp4')
print('Uploaded to:', url)
"
```

## Quotas & Rate Limits

**YouTube Data API v3 Quotas:**
- Default: 10,000 quota units per day
- Each video upload: ~1,500 units
- Each video metadata update: ~50 units
- Max uploads/day: ~6 with default quota

**Upload Size Limits:**
- Max file size: 256 GB (practically unlimited for our use case)
- Recommended: < 2 GB for reliable uploads
- Our videos: typically 50-200 MB

**Upload Rate Limits:**
- No per-second rate limit (resumable uploads)
- Daily quota reset: midnight Pacific Time
- Monitor at: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas

## Troubleshooting

### Uploads Failing with 503 (Service Unavailable)

YouTube services occasionally experience issues. The code handles this with:
- Automatic retry up to 5 times
- Exponential backoff (2^attempt seconds between retries)
- Resumable uploads that can pick up where they left off

If retries exhaust, wait 5-10 minutes and try again.

### Refresh Token Revoked

Refresh tokens are revoked when:
- User manually revokes in Google Account Settings
- Password changed
- App permissions revoked
- Token not used for extended period

Solution:
1. Generate new refresh token (follow Step 3)
2. Update in GitHub Secrets, OCI .env, Vercel env vars
3. Redeploy

### Video Privacy Settings

Videos are published as **"Unlisted"** by default:
- ✅ Accessible via direct link (YouTube, social media)
- ✅ Not discoverable in search
- ✅ Not on your channel's public videos tab
- ✅ Good for testing and limited distribution

To change to "Public":
1. Edit `publish_youtube()` in `scripts/social_media_publishers.py`
2. Change `"privacyStatus": "unlisted"` to `"privacyStatus": "public"`
3. Redeploy

Or change manually in YouTube Studio:
1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click on video
3. Click "Details"
4. Change "Visibility" from "Unlisted" to "Public"
5. Click "Save"

## API Reference

### `publish_youtube(article, video_path)`

Upload video to YouTube.

**Parameters:**
- `article` (Dict): Keys: `title`, `meta_description`, `body`
- `video_path` (str): Path to .mp4 video file

**Returns:** YouTube URL (str) or None if failed

**Example:**
```python
from scripts.social_media_publishers import publish_youtube

article = {
    "title": "My Video",
    "meta_description": "Description",
    "body": "Full content",
}

url = publish_youtube(article, "/path/to/video.mp4")
# Returns: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### `article_to_video(article, ...)`

Full end-to-end: Article → Script → Voice → Video → YouTube

**Parameters:**
- `article` (Article): Article object with title, description, body
- `video_type` (str): "explainer", "tutorial", "news_summary", "educational"
- `voice_provider` (str): "elevenlabs", "google_tts", "pyttsx3"
- `slides_count` (int): 3-12 slides
- `publish_to_youtube_flag` (bool): Upload to YouTube

**Returns:** VideoPipelineResult with URLs and metadata

**Example:**
```python
from scripts.video_pipeline_integration import Article, article_to_video

article = Article(
    title="10 Trading Strategies",
    meta_description="Learn strategies",
    body="Article content...",
)

result = await article_to_video(
    article=article,
    video_type="tutorial",
    voice_provider="elevenlabs",
    publish_to_youtube_flag=True,
)

print(result.youtube_url)  # YouTube video URL
```

## Integration Examples

### GitHub Actions Workflow

```yaml
name: Auto-publish videos

on:
  schedule:
    - cron: '0 10 * * *'  # Daily at 10 AM UTC

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate and publish video
        env:
          YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN }}
        run: |
          python scripts/video_pipeline_integration.py generate \
            --title "Daily Market Update" \
            --meta "Today's market analysis" \
            --body "$(cat articles/daily_update.md)" \
            --type news_summary
```

### Backend API Endpoint

```python
from fastapi import FastAPI, HTTPException
from scripts.video_pipeline_integration import Article, article_to_video

@app.post("/api/videos/generate")
async def generate_video(
    title: str,
    description: str,
    body: str,
):
    """Generate video from article."""
    article = Article(
        title=title,
        meta_description=description,
        body=body,
    )
    
    result = await article_to_video(
        article=article,
        publish_to_youtube_flag=True,
    )
    
    if result.error:
        raise HTTPException(status_code=500, detail=result.error)
    
    return {
        "video_url": result.video_path,
        "youtube_url": result.youtube_url,
        "duration": result.video_duration_seconds,
    }
```

## Support & Resources

- [Google Cloud Console](https://console.cloud.google.com)
- [YouTube Data API Docs](https://developers.google.com/youtube/v3)
- [Google Auth Documentation](https://github.com/googleapis/google-auth-library-python)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [YouTube API Quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

## FAQ

**Q: Can I upload to multiple YouTube channels?**
A: Yes, create separate OAuth credentials for each channel and set different environment variables.

**Q: How long does a video upload take?**
A: Depends on file size and internet speed. Typically 2-10 minutes for 100-500 MB videos.

**Q: Can I edit videos after uploading?**
A: Yes, videos are uploaded as "Unlisted" so you can edit metadata and privacy settings in YouTube Studio.

**Q: What happens if the server crashes during upload?**
A: Resumable upload will resume from the last chunk on the next attempt (within 24 hours).

**Q: Can I schedule videos for future publishing?**
A: Not via API. Upload as unlisted, then schedule publishing manually in YouTube Studio.

**Q: How do I monitor uploads?**
A: Check logs in `datacenter/ai_video_pipeline/logs/` or YouTube Studio dashboard.

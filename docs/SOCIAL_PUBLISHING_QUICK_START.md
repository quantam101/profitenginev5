# Social Media Publishing Quick Start

Fast reference for publishing articles to 6 social media platforms.

## 1-Minute Setup

### Install Dependencies
```bash
pip install tweepy>=4.14.0 praw>=7.7.0 google-auth-oauthlib>=1.2.0 google-api-python-client>=2.108.0
# httpx, already installed
```

### Set Environment Variables (OCI `.env`)

Copy-paste template from `docs/SOCIAL_MEDIA_CREDENTIALS_SETUP.md` and fill in real values.

```bash
# Minimum required for testing
TWITTER_BEARER_TOKEN=your_token_here
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USERNAME=bot_username
REDDIT_PASSWORD=bot_password
REDDIT_SUBREDDIT=investing
```

### Test Connection

```bash
python3 -c "
from scripts.social_media_publishers import *
import json

# Verify all env vars loaded
creds = {
    'twitter': bool(TWITTER_BEARER_TOKEN or TWITTER_API_KEY),
    'reddit': all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET]),
    'linkedin': bool(LINKEDIN_ACCESS_TOKEN),
    'facebook': all([FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN]),
    'instagram': bool(IG_USER_ID),
    'tiktok': bool(TIKTOK_ACCESS_TOKEN),
    'youtube': all([YOUTUBE_CLIENT_ID, YOUTUBE_REFRESH_TOKEN])
}
print(json.dumps(creds, indent=2))
"
```

Expected output (only platforms with credentials show `true`):
```json
{
  "twitter": true,
  "reddit": true,
  "linkedin": false,
  "facebook": false,
  "instagram": false,
  "tiktok": false,
  "youtube": false
}
```

---

## 2-Minute Usage

### Publish Single Article

```python
from scripts.social_media_publishers import publish_to_all_platforms

article = {
    "title": "10 Trading Strategies That Work in 2024",
    "meta_description": "Proven strategies used by professional traders",
    "body": "Full article content here..."
}

results = publish_to_all_platforms(
    article=article,
    canonical_url="https://profitengine.alreadyherellc.com/article",
    image_url="https://cdn.profitengine.com/image.jpg",  # For Instagram
    video_url="https://cdn.profitengine.com/video.mp4",  # For TikTok
    video_path="/tmp/article.mp4",  # For YouTube upload
)

for platform, url in results.items():
    if url:
        print(f"{platform}: {url}")
    else:
        print(f"{platform}: SKIPPED (credentials missing or error)")
```

### Publish to Specific Platform

```python
from scripts.social_media_publishers import (
    publish_twitter,
    publish_reddit,
    publish_linkedin,
    publish_facebook,
    publish_instagram,
    publish_tiktok,
    publish_youtube,
)

# Twitter only
twitter_url = publish_twitter(article, canonical_url)
print(twitter_url)

# Reddit only
reddit_url = publish_reddit(article, canonical_url)
print(reddit_url)

# LinkedIn only
linkedin_url = publish_linkedin(article, canonical_url)
print(linkedin_url)

# Facebook only
facebook_url = publish_facebook(article, canonical_url)
print(facebook_url)

# Instagram (requires image_url)
instagram_url = publish_instagram(article, image_url="https://...")
print(instagram_url)

# TikTok (requires video_url)
tiktok_url = publish_tiktok(article, video_url="https://...")
print(tiktok_url)

# YouTube (requires local video file)
youtube_url = publish_youtube(article, video_path="/tmp/video.mp4")
print(youtube_url)
```

---

## Platform-Specific Requirements

| Platform | Required Env Vars | Required Article Fields | Media | Notes |
|----------|-------------------|-------------------------|-------|-------|
| **Twitter** | `TWITTER_BEARER_TOKEN` | title, meta_description | — | 280 char limit, v2 API |
| **Reddit** | `REDDIT_*`, `REDDIT_SUBREDDIT` | title, meta_description | — | Link post format |
| **LinkedIn** | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN` | title, meta_description | — | Personal profile posts |
| **Facebook** | `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN` | title, meta_description | — | Page feed posts |
| **Instagram** | `IG_USER_ID`, `FB_PAGE_ACCESS_TOKEN` | title | image_url (required) | Public HTTPS .jpg/.png |
| **TikTok** | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_OPEN_ID` | title | video_url (required) | Business account only |
| **YouTube** | `YOUTUBE_CLIENT_ID`, `YOUTUBE_REFRESH_TOKEN` | title, meta_description | video_path (required) | OAuth 2.0 refresh flow |

---

## Common Patterns

### Publish to Multiple Platforms (Skip Invalid)

```python
from scripts.social_media_publishers import publish_to_all_platforms

results = publish_to_all_platforms(
    article=article,
    canonical_url=canonical_url,
    image_url=image_url,
    video_url=None,  # Skip TikTok, YouTube
)

# Results: {platform: url_or_None}
posted = {k: v for k, v in results.items() if v is not None}
skipped = {k: v for k, v in results.items() if v is None}

print(f"Posted to: {', '.join(posted.keys())}")
print(f"Skipped: {', '.join(skipped.keys())}")
```

### Batch Publish Multiple Articles

```python
from scripts.social_media_publishers import publish_to_all_platforms

articles = [
    {
        "title": "Article 1",
        "meta_description": "...",
        "body": "...",
    },
    {
        "title": "Article 2",
        "meta_description": "...",
        "body": "...",
    },
]

for article in articles:
    canonical_url = f"https://profitengine.alreadyherellc.com/{article['slug']}"
    results = publish_to_all_platforms(article, canonical_url)
    print(f"Article: {article['title']}")
    print(f"Results: {results}")
    print()
```

### Publish Only to Text Platforms (No Media)

```python
from scripts.social_media_publishers import (
    publish_twitter,
    publish_reddit,
    publish_linkedin,
    publish_facebook,
)

article = {"title": "...", "meta_description": "...", "body": "..."}
canonical_url = "https://..."

results = {
    "twitter": publish_twitter(article, canonical_url),
    "reddit": publish_reddit(article, canonical_url),
    "linkedin": publish_linkedin(article, canonical_url),
    "facebook": publish_facebook(article, canonical_url),
}
```

### Retry Failed Posts

```python
from scripts.social_media_publishers import publish_to_all_platforms
import time

article = {"title": "...", "meta_description": "...", "body": "..."}
canonical_url = "https://..."

max_retries = 3
for attempt in range(max_retries):
    results = publish_to_all_platforms(article, canonical_url)
    failed = {k: v for k, v in results.items() if v is None}
    
    if not failed:
        print("All platforms posted successfully!")
        break
    
    print(f"Attempt {attempt + 1}/{max_retries}: {len(failed)} platform(s) failed")
    if attempt < max_retries - 1:
        time.sleep(5)  # Wait before retry
```

---

## Logging & Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from scripts.social_media_publishers import publish_to_all_platforms

results = publish_to_all_platforms(article, canonical_url)
# Now see [DEBUG], [INFO], [WARNING], [ERROR] messages
```

### Check Specific Errors

```python
from scripts.social_media_publishers import publish_linkedin

# Add try/except for more details
try:
    url = publish_linkedin(article, canonical_url)
except Exception as e:
    print(f"LinkedIn error: {type(e).__name__}: {e}")
```

---

## API Rate Limits

| Platform | Limit | Window | Recommendation |
|----------|-------|--------|-----------------|
| **Twitter** | 300 posts/mo (free tier) | Monthly | 1 post/day max |
| **Reddit** | ~10 posts/day per sub | Daily | 1-2 posts/day |
| **LinkedIn** | Unlimited (but monitored) | — | 1-3 posts/week |
| **Facebook** | Unlimited | — | 1-3 posts/day |
| **Instagram** | Unlimited | — | 1 post/day recommended |
| **TikTok** | Varies by account tier | Variable | Check dashboard |
| **YouTube** | 10,000 uploads/day | Daily | 1-2 videos/day |

**Best practice**: Schedule posts at intervals (1 per day, 3x per week) to avoid rate limiting.

---

## Troubleshooting

### Platform Not Publishing?

1. **Check credentials**
   ```bash
   echo $TWITTER_BEARER_TOKEN  # Should print non-empty string
   ```

2. **Check permissions**
   - Twitter: `read:write` or `write` scope
   - Reddit: Can post to target subreddit?
   - LinkedIn: Access token not expired?
   - Facebook: Page access token with `pages_manage_posts`?

3. **Check media URLs**
   - Image for Instagram? Must be HTTPS, not localhost
   - Video for TikTok? Must be publicly accessible
   - YouTube file exists?

4. **Check logs**
   ```bash
   # Enable DEBUG logging
   DEBUG=1 python3 your_script.py
   ```

### 401/403 Errors?

These mean authentication failed. Check:
1. Token format (should not have quotes or extra spaces)
2. Token not expired (some platforms require regeneration)
3. Token has correct scopes/permissions
4. Token for correct account (personal vs business)

### Rate Limited?

Slow down posting frequency:
```python
import time
from scripts.social_media_publishers import publish_twitter

for article in articles:
    publish_twitter(article, canonical_url)
    time.sleep(60)  # Wait 1 minute between posts
```

---

## Integration Examples

### Webhook from Blog Publishing System

```python
# Triggered when blog posts via webhook
from fastapi import FastAPI, Request
from scripts.social_media_publishers import publish_to_all_platforms

app = FastAPI()

@app.post("/api/webhooks/blog")
async def blog_published(request: Request):
    data = await request.json()
    
    article = {
        "title": data.get("title"),
        "meta_description": data.get("description"),
        "body": data.get("body"),
    }
    
    canonical_url = data.get("url")
    image_url = data.get("featured_image")
    
    results = publish_to_all_platforms(article, canonical_url, image_url)
    
    return {
        "posted": {k: v for k, v in results.items() if v},
        "skipped": {k: v for k, v in results.items() if not v},
    }
```

### Scheduled Daily Publishing (APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.social_media_publishers import publish_to_all_platforms

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=0)
def publish_daily():
    # Get latest article from database
    article = db.get_latest_article()
    canonical_url = f"https://profitengine.alreadyherellc.com/{article.slug}"
    
    results = publish_to_all_platforms(article, canonical_url)
    print(f"Daily publish: {results}")

scheduler.start()
```

---

## Next Steps

1. **Set up credentials**: `docs/SOCIAL_MEDIA_CREDENTIALS_SETUP.md`
2. **Review tests**: `tests/test_social_media_publishers.py`
3. **Check full implementation**: `scripts/social_media_publishers.py`
4. **Monitor publishing**: Use logging to track posts
5. **Rotate credentials quarterly**: See setup guide

---

## Support

- **API Documentation**: See `docs/SOCIAL_MEDIA_CREDENTIALS_SETUP.md` for platform links
- **Test Suite**: `pytest tests/test_social_media_publishers.py -v`
- **Implementation**: `scripts/social_media_publishers.py` (fully documented)

Last updated: 2026-06-19

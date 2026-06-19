# Social Distributor — Quick Reference

## Installation

```bash
pip install apscheduler requests
```

## Environment Variables (server .env only)

```env
# Twitter
TWITTER_API_KEY=xxx
TWITTER_API_SECRET=xxx
TWITTER_ACCESS_TOKEN=xxx
TWITTER_ACCESS_SECRET=xxx

# LinkedIn
LINKEDIN_ACCESS_TOKEN=xxx
LINKEDIN_PERSON_URN=urn:li:person:12345678

# Reddit
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USERNAME=xxx
REDDIT_PASSWORD=xxx

# TikTok
TIKTOK_ACCESS_TOKEN=xxx

# YouTube
YOUTUBE_CLIENT_ID=xxx
YOUTUBE_CLIENT_SECRET=xxx
YOUTUBE_REFRESH_TOKEN=xxx

# Email
GMAIL_USER=alreadyherellc@gmail.com
GMAIL_APP_PASSWORD=xxx
ALERT_EMAIL=dispatch@alreadyherellc.com

# Optional
PROFITENGINE_URL=https://profitengine.alreadyherellc.com
AFFILIATE_TAG=alreadyhere-20
```

## Quick Start

### 1. Initialize Scheduler (Automatic Posting)

```python
from runtime.social_distributor import SocialDistributor

distributor = SocialDistributor()
distributor.schedule_daily_posts()  # Runs in background
```

### 2. Create & Distribute Posts

```python
import asyncio

async def distribute():
    distributor = SocialDistributor()
    
    results = await distributor.post_all_platforms(
        content_id="my_post_001",
        title="90% Win Rate Trading Bot",
        body="Learn how we built it...",
        link="https://profitengine.alreadyherellc.com/blog/post",
        platforms=["twitter", "linkedin", "reddit"],
        hashtags=["trading", "ai", "alreadyhere", "autonomous"],
    )
    
    print(results)  # {platform: success}

asyncio.run(distribute())
```

### 3. Send Email Digest (Manual)

```python
distributor = SocialDistributor()
distributor.send_email_digest()
```

## API Endpoints

### Distribute to platforms

```bash
curl -X POST http://localhost:8000/api/social/distribute \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "post_001",
    "title": "Title",
    "body": "Body...",
    "link": "https://...",
    "platforms": ["twitter", "linkedin", "reddit"],
    "hashtags": ["trading", "ai"]
  }'
```

### List posts

```bash
curl http://localhost:8000/api/social/posts?platform=twitter&status=posted
```

### Get engagement metrics

```bash
curl http://localhost:8000/api/social/engagement?days=7&limit=5
```

### Send digest

```bash
curl -X POST http://localhost:8000/api/social/digest
```

## Posting Schedule (Automatic)

| Platform | Time (MST) | Frequency |
|----------|-----------|-----------|
| Twitter | 9:00 AM | Daily |
| Twitter | 5:00 PM | Daily |
| LinkedIn | 9:00 AM | Daily |
| TikTok | 5:00 PM | Daily |
| YouTube | 5:00 PM | Daily |
| Email | Friday 10 AM | Weekly |
| Reddit | On-demand | Whenever |

## Database

```bash
sqlite3 datacenter/social_distributor.db

# List all posts
SELECT id, platform, title, status, created_at FROM social_posts;

# Count by platform
SELECT platform, COUNT(*) FROM social_posts GROUP BY platform;

# Get failed posts
SELECT id, platform, error_message FROM social_posts WHERE status='failed';
```

## Class Methods

### SocialDistributor

```python
# Create posts in draft status
post_ids = distributor.create_post(
    content_id="unique_id",
    title="Post title",
    body="Body text",
    link="https://...",
    platforms=["twitter", "linkedin"],
    hashtags=["tag1", "tag2"],
    image_url="https://...",
    video_path="/path/to/video.mp4",
)

# Post individual platforms
await distributor.post_twitter(post)
await distributor.post_linkedin(post)
await distributor.post_tiktok(post)
await distributor.post_youtube(post)
await distributor.post_reddit(post, ["subreddit1", "subreddit2"])

# Post to all platforms simultaneously
results = await distributor.post_all_platforms(...)

# Send email
distributor.send_email_digest(recipient="email@example.com")

# Schedule automatic posting
distributor.schedule_daily_posts()
```

### SocialDistributorDB

```python
# Query
post = distributor.db.get_post(post_id)
posts = distributor.db.list_posts_by_platform("twitter", status="posted")
top_posts = distributor.db.get_top_posts_by_engagement(days=7, limit=5)

# Check duplicate
is_dup = distributor.db.check_duplicate("twitter", "content_id")

# Update
distributor.db.update_post_status(post_id, "posted")
distributor.db.update_engagement(post_id, likes=42, retweets=15, comments=3, views=500)
```

## Platform Formatting

```python
from runtime.social_distributor import PlatformFormatter, SocialPost

post = SocialPost(
    platform="twitter",
    title="Title",
    body="Body",
    link="https://...",
    hashtags=["tag1", "tag2"],
)

# Format for each platform
twitter_text = PlatformFormatter.format_twitter(post)        # 280 chars
linkedin_text = PlatformFormatter.format_linkedin(post)      # 3000 chars
tiktok_text = PlatformFormatter.format_tiktok(post)          # 150 chars
yt_title, yt_desc = PlatformFormatter.format_youtube(post)   # (100, 5000) chars
sub, title, body = PlatformFormatter.format_reddit(post)     # (subreddit, 300, 40000)
html = PlatformFormatter.format_email_digest([post1, post2]) # HTML email
```

## Duplicate Prevention

```python
# First post
post_ids = distributor.create_post(
    content_id="trading_101",
    title="5 Trading Signals",
    body="...",
    link="...",
    platforms=["twitter", "linkedin"],
)

# Try again — will be skipped
post_ids = distributor.create_post(
    content_id="trading_101",  # Same ID
    title="5 Trading Signals",
    body="...",
    link="...",
    platforms=["twitter", "linkedin"],
)
# Result: post_ids = [] (nothing created)
```

## Engagement Tracking

```python
# Get top posts
top_posts = distributor.db.get_top_posts_by_engagement(days=7, limit=5)

for post in top_posts:
    print(f"{post.title}")
    print(f"  Likes: {post.engagement_likes}")
    print(f"  Retweets: {post.engagement_retweets}")
    print(f"  Comments: {post.engagement_comments}")
    print(f"  Views: {post.engagement_views}")
    print(f"  Total: {sum([post.engagement_likes, post.engagement_retweets, post.engagement_comments, post.engagement_views])}")
```

## Common Errors

### "No credentials — skip"
- Missing environment variable
- Check: `echo $TWITTER_API_KEY`
- Verify in server `.env` (never repo)

### "Post cached in local journal"
- Network connection lost
- Posts auto-sync when connectivity returns
- Check: `sqlite3 datacenter/social_cache.db`

### "Content hash unique constraint"
- Duplicate post detection triggered
- Use different `content_id` for new posts

### "No video file"
- `video_path` file doesn't exist
- Check file permissions: `ls -la /path/to/video.mp4`

## Logging

```bash
# Watch logs live
tail -f social_distributor.log

# Count posts by platform
grep "\[Twitter\]" social_distributor.log | wc -l
grep "\[LinkedIn\]" social_distributor.log | wc -l

# Check for errors
grep "ERROR" social_distributor.log
```

## Integration with Content Generator

```python
import asyncio
import json
from runtime.agent_impls.content_gen import Agent as ContentGen
from runtime.social_distributor import SocialDistributor

async def full_pipeline():
    # Generate content
    gen = ContentGen()
    result = gen.run(
        objective="AI Trading Strategies",
        context="90% win rate achieved",
        connectors=[],
    )
    
    # Parse article
    article = json.loads(result.output.split("ARTICLE_JSON:")[1])
    
    # Distribute
    distributor = SocialDistributor()
    results = await distributor.post_all_platforms(
        content_id=article["slug"],
        title=article["title"],
        body=article["body"],
        link=f"https://profitengine.alreadyherellc.com/blog/{article['slug']}",
        platforms=["twitter", "linkedin", "reddit"],
        hashtags=article.get("tags", ["trading", "ai", "alreadyhere"]),
    )
    
    return results

asyncio.run(full_pipeline())
```

## Performance

- Post creation: <10ms per platform
- Single post: <500ms (1.5s with latency)
- 6-platform distribution: <3s
- Email digest: <2s
- DB query: <50ms

## Testing

```bash
# Test environment
python -c "
from runtime.social_distributor import SocialDistributor
d = SocialDistributor()
print('DB path:', d.db.db_path)
print('DB accessible:', d.db.db_path exists)
"

# Run examples
python runtime/social_distributor_examples.py
```

## Checklist Before Production

- [ ] All 6 platform credentials configured
- [ ] Gmail app password set
- [ ] Database directory exists: `mkdir -p datacenter`
- [ ] Tested at least one post to each platform
- [ ] Scheduler configured and tested
- [ ] Email digest template reviewed
- [ ] Hashtags match brand voice
- [ ] FTC disclosure included in all posts
- [ ] Logs configured and rotating
- [ ] Database backups scheduled
- [ ] Engagement tracking working
- [ ] Team trained on API endpoints

---

**Quick Links:**
- Full Setup: [SOCIAL_DISTRIBUTOR_SETUP.md](SOCIAL_DISTRIBUTOR_SETUP.md)
- Examples: [social_distributor_examples.py](social_distributor_examples.py)
- Source: [social_distributor.py](social_distributor.py)
- Social Engine: [runtime/eaos/social_engine.py](eaos/social_engine.py)

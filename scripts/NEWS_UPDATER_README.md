# Daily News Updater for ProfitEngine v5

## Overview

The **News Updater** automatically curates and publishes daily business, AI, and passive income news across all ProfitEngine channels:

- **Newsletter** — Curated daily email digest
- **Blog** — SEO-optimized daily news article
- **Social Media** — Twitter/X threads with top stories
- **API** — Programmatic article creation

## Features

### News Aggregation
- **NewsAPI.org** — Real-time news from 10,000+ sources
- **RSS Feeds** — TechCrunch, HackerNews, ProductHunt, Indie Hackers, Medium
- **Trending Topics** — Market analysis and synthetic trending items
- **Smart Scoring** — Relevance, recency, and engagement-based ranking

### Content Generation
- **"5 Things to Know Today"** — Top news with commentary
- **"Industry Updates"** — News organized by category with analysis
- **"Trending Opportunities"** — Passive income & business opportunities
- **Affiliate Integration** — Links to relevant tools and services
- **SEO Optimization** — Keywords, meta descriptions, structured data

### Multi-Channel Publishing
- **Newsletter** — Full digest with affiliate links
- **Blog** — Standalone article with tags and metadata
- **Social Media** — Tweet threads with engagement hooks
- **Backend API** — Programmatic article creation

### Categories
- AI & Tools
- Business
- Passive Income
- Technology
- Trending
- Opportunities

## Installation

### 1. Install Dependencies

```bash
pip install requests feedparser
```

### 2. Configure API Keys

Add to your `.env` or GitHub Secrets:

```env
# NewsAPI.org (sign up free at https://newsapi.org)
NEWSAPI_KEY=your_newsapi_key_here

# Newsletter service (if using external service)
NEWSLETTER_API_KEY=your_newsletter_key

# Backend URL
PROFITENGINE_URL=https://profitengine-tau.vercel.app
```

### 3. Verify Dependencies

The script gracefully degrades if modules are missing:

```bash
python scripts/news_updater.py --action preview
```

## Usage

### Quick Preview (No Publishing)

```bash
python scripts/news_updater.py --action preview
```

Output shows:
- 5 Things to Know Today
- Industry Updates by category
- Trending Opportunities
- Top 5 stories

### Run Daily Update (Publish)

```bash
python scripts/news_updater.py --action daily
```

Publishes to:
- ✅ Newsletter service
- ✅ Blog (as new article)
- ✅ Twitter/Social media
- ✅ Backend API

### Save Output to File

```bash
python scripts/news_updater.py --action daily --output
```

Saves JSON to `scripts/output/daily_news_YYYYMMDD_HHMMSS.json`

### Schedule Daily Execution

#### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/daily-news.yml`:

```yaml
name: Daily News Update

on:
  schedule:
    # Run at 9 AM UTC daily
    - cron: '0 9 * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  update-news:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install requests feedparser
      
      - name: Run daily news update
        env:
          NEWSAPI_KEY: ${{ secrets.NEWSAPI_KEY }}
          NEWSLETTER_API_KEY: ${{ secrets.NEWSLETTER_API_KEY }}
          PROFITENGINE_URL: https://profitengine-tau.vercel.app
        run: python scripts/news_updater.py --action daily
      
      - name: Commit and push (optional)
        if: success()
        run: |
          git config user.name "News Bot"
          git config user.email "bot@profitengine.ai"
          git add -A
          git commit -m "chore: daily news digest update" || true
          git push
```

#### Option 2: System Cron

Add to crontab:

```bash
# Run at 9 AM daily
0 9 * * * cd /path/to/profitengine && python scripts/news_updater.py --action daily
```

#### Option 3: OCI Always Free VM

SSH to `opc@129.146.236.177` and add to crontab:

```bash
0 9 * * * python /home/opc/profitengine/scripts/news_updater.py --action daily
```

## Output Format

### Newsletter Format

Subject: `Daily Digest: December 19, 2024 — Business & AI News`

```
**5 Things to Know Today — December 19, 2024**

1. AI Startups Raise $15B in Q4
Source: TechCrunch

   Description of the news...

   Our take: Market momentum continues despite economic headwinds

   💡 Opportunity: Consider starting your own AI-powered SaaS

   [Read full article →](https://example.com/article)

... (items 2-5) ...

## Industry Updates

### AI & Tools
- **Item 1** — Source
- **Item 2** — Source

📊 3 AI developments today. The pace of innovation continues...

... (other categories) ...

## Trending Opportunities for You

### Passive Income Automation Tools See Record Growth

Market analysis shows growing interest in automation for content creators...

**Recommended Tools:** ChatGPT Plus for creators
[Learn more →](https://chat.openai.com)

**Getting started:** Start with one revenue stream, optimize it, then add...
```

### Blog Article Format

```markdown
# Daily Digest: December 19, 2024 — Business & AI News

Your daily update on the most important news for entrepreneurs, creators, and passive income builders...

## 5 Things to Know Today

1. [Story details] ...

## Industry Updates

### AI & Tools
...

### Business
...

## Trending Opportunities for You

...

---

## Stay Updated Daily

[Subscribe to our newsletter →](https://profitengine-tau.vercel.app/subscribe)

Tags: daily news, AI news, business updates, passive income news, entrepreneur news, trend alerts
```

## API Integration

### How to Integrate with Existing Services

#### Newsletter Publisher
The script uses `newsletter_publisher.py` if available:

```python
from newsletter_publisher import NewsletterPublisher

publisher = NewsletterPublisher()
success, msg = publisher.publish(
    subject="Daily Digest: Today's News",
    body=article['content'],
    tags=['daily-news', 'digest']
)
```

#### Article Publisher
Integrates with `publish_article.py`:

```python
from publish_article import ArticlePublisher

publisher = ArticlePublisher()
success, url = publisher.publish_article(
    title="Daily Digest: December 19",
    content=article['content'],
    tags=article['seo_keywords'],
    category='News'
)
```

#### Social Media Publisher
Uses `social_media_publishers.py`:

```python
from social_media_publishers import SocialMediaPublisher

publisher = SocialMediaPublisher()
success = publisher.publish_to_twitter(snippet)
```

### Programmatic Usage

```python
from scripts.news_updater import NewsUpdater

updater = NewsUpdater()

# Get preview (no publishing)
result = updater.preview_update()
print(result['digest'])
print(result['industry'])
print(result['opportunities'])

# Full update with publishing
result = updater.run_daily_update()
print(f"Published to {len(result['publish_results'])} channels")

# Save to file
filepath = updater.save_to_file(result)
```

## Configuration

### Customizing News Sources

Edit `news_updater.py` to modify RSS feeds:

```python
feeds = {
    'TechCrunch': 'https://feeds.techcrunch.com/techcrunch/startups',
    'HackerNews': 'https://news.ycombinator.com/rss',
    'Your-Custom-Feed': 'https://example.com/feed.rss',
}
```

### Customizing Categories

Add new categories in `NewsCategory` enum:

```python
class NewsCategory(Enum):
    YOUR_CATEGORY = "Your Category Name"
```

Then update categorization logic in `_categorize_article()`.

### Customizing Affiliate Links

Update the affiliate links dictionary:

```python
def _load_affiliate_links(self) -> Dict[str, Dict]:
    return {
        'Your Product': {
            'description': 'Product description',
            'url': 'https://affiliate-link.com',
            'commission': '10%'
        },
    }
```

## Keyword & SEO Optimization

The script automatically includes:

- **Primary keywords** — "daily news", "AI news", "business updates"
- **Long-tail keywords** — "passive income news", "entrepreneur news"
- **Category tags** — Each article tagged by content category
- **Meta descriptions** — Auto-generated summaries
- **Internal linking** — Links to relevant articles

### SEO Features

- ✅ Structured headline (`h1`, `h2`, `h3` hierarchy)
- ✅ Meta description (under 160 chars)
- ✅ Focus keywords in title and first paragraph
- ✅ Internal links to related articles
- ✅ Image alt text support
- ✅ Recency signals (publication date)
- ✅ Categories and tags

## Troubleshooting

### "No news items found"

**Cause:** NewsAPI key missing or API rate limit exceeded

**Solution:**
1. Verify `NEWSAPI_KEY` is set: `echo $NEWSAPI_KEY`
2. Check NewsAPI account at https://newsapi.org
3. Free tier has 100 requests/day limit
4. Wait 24 hours or upgrade to paid plan

### "RSS feed timeout"

**Cause:** Feed service unreachable

**Solution:**
1. The script has 10-second timeout per feed
2. It gracefully continues to next feed
3. Verify internet connection
4. Check feed URLs are accessible

### "Newsletter/Blog publish failed"

**Cause:** Related modules not installed or configured

**Solution:**
1. Script gracefully skips unavailable services
2. Check that `email_list_manager.py` exists
3. Verify API keys are configured
4. Check backend service is running

## Performance

- **Aggregation:** ~5-10 seconds (NewsAPI + 6 RSS feeds)
- **Formatting:** <1 second (text processing)
- **Publishing:** 10-30 seconds (depends on services)
- **Total time:** ~20-40 seconds

## Monitoring & Logging

### Verbose Logging

```bash
python scripts/news_updater.py --action daily --verbose
```

### Log Example

```
2024-12-19 09:00:15 - news_updater - INFO - Starting daily news update
2024-12-19 09:00:22 - news_updater - INFO - Fetched 15 articles from NewsAPI
2024-12-19 09:00:23 - news_updater - INFO - Fetched 5 items from TechCrunch
2024-12-19 09:00:24 - news_updater - INFO - Generated 5 trending topic items
2024-12-19 09:00:25 - news_updater - INFO - Aggregated 25 unique news items
2024-12-19 09:00:26 - news_updater - INFO - Published to API: https://...
2024-12-19 09:00:35 - news_updater - INFO - Daily update complete
```

### GitHub Actions Status

View workflow runs at:
```
https://github.com/quantam101/profitenginev5/actions/workflows/daily-news.yml
```

## Advanced Features

### Engagement Scoring

Items are scored based on:
- **Keyword relevance** (AI, passive income, affiliate, etc.)
- **Category importance** (AI & Tools > generic tech news)
- **Recency** (published < 12 hours = +1.0 point)
- **Deduplication** (same URL counted once)

### Smart Categorization

Articles are auto-categorized using keyword matching:
- "ChatGPT" + "automation" → AI & Tools
- "passive income" + "freelance" → Passive Income
- "startup" + "funding" → Business

### Affiliate Opportunity Matching

The formatter automatically matches article titles to affiliate products:
- ChatGPT article → Link to ChatGPT Plus
- Vercel article → Link to Vercel deployment
- Print-on-demand article → Link to Printful

## Future Enhancements

- [ ] Twitter Trends API integration
- [ ] Sentiment analysis for news tone
- [ ] Custom keyword alerts
- [ ] Subscriber preference filtering
- [ ] A/B testing different headlines
- [ ] Clickthrough rate tracking
- [ ] Subscriber segmentation by interest
- [ ] AI-generated commentary per article
- [ ] Video news summaries
- [ ] Podcast episode generation

## Support

For issues or feature requests:
1. Check logs: `python scripts/news_updater.py --action preview --verbose`
2. Verify API keys: `echo $NEWSAPI_KEY`
3. Test preview: `python scripts/news_updater.py --action preview --output`
4. File GitHub issue with output logs

## License

Part of ProfitEngine v5 — All Rights Reserved to Already Here LLC

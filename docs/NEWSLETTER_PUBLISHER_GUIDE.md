# Newsletter Publisher Guide

**Email distribution platform for ProfitEngine v5** — Automated newsletters across Beehiiv, Resend, and Substack with monetization, personalization, and full metrics tracking.

---

## Quick Start

### 1. Setup Environment Variables

Add to `.env` or `.profitengine-secrets`:

```bash
# Beehiiv (primary provider)
BEEHIIV_API_KEY=your-beehiiv-api-key
NEWSLETTER_PUBLICATION_ID=your-publication-id

# Resend (fallback)
RESEND_API_KEY=your-resend-api-key

# Substack (optional)
SUBSTACK_ACCESS_TOKEN=your-substack-token

# Newsletter sender
NEWSLETTER_SENDER_EMAIL=dispatch@alreadyherellc.com
NEWSLETTER_SENDER_NAME=ProfitEngine Newsletter
PROFITENGINE_DOMAIN=profitengine.alreadyherellc.com

# Monetization & tracking
AFFILIATE_LINKS={"VPS hosting":"https://ref.url","AI tools":"https://ai-ref.url"}
AMAZON_PARTNER_TAG=alreadyhere-20
```

### 2. Send Your First Newsletter

```python
from scripts.newsletter_publisher import Article, send_newsletter
from datetime import datetime, timezone

# Create articles
articles = [
    Article(
        id="art-001",
        title="How to Build AI Apps for Free",
        summary="Use Groq and Google's free tiers...",
        body="Full article content...",
        canonical_url="https://profitengine.alreadyherellc.com/ai-free",
        published_at=datetime.now(timezone.utc).isoformat(),
        author="Stephen Franklin",
        read_time_minutes=8,
    )
]

# Send weekly digest
result = send_newsletter(
    template_type="weekly_digest",
    articles=articles,
    recipient_segment="all",
    sponsor_html="<h3>Sponsor: FastAPI Pro</h3>",
    track_opens=True,
    track_clicks=True,
)

print(f"Campaign ID: {result['campaign_id']}")
print(f"Success: {result['success']}")
```

### 3. Check Metrics

```python
from scripts.newsletter_publisher import get_newsletter_metrics

metrics = get_newsletter_metrics(campaign_id="...")
print(f"Opens: {metrics.open_rate:.1%}")
print(f"Clicks: {metrics.click_rate:.1%}")
print(f"Conversions: {metrics.conversion_rate:.1%}")
```

---

## Features

### Newsletter Templates

#### Weekly Digest
- **Best for**: General audience, broad content mix
- **Content**: Top 5 most recent articles
- **Frequency**: Once per week
- **Engagement**: Moderate-to-high (readers can digest multiple topics)

```python
from scripts.newsletter_publisher import create_weekly_digest

newsletter = create_weekly_digest(
    articles=articles[:5],  # Automatically takes top 5
    sponsor_html="<h3>Sponsor Message</h3>",
    campaign_id="camp-123"
)
```

#### Daily Briefing
- **Best for**: Power users, premium subscribers
- **Content**: 1-2 best articles + AI-generated summary
- **Frequency**: Daily (or 3-4x per week)
- **Engagement**: High (curated, personalized, exclusive)

```python
newsletter = create_daily_briefing(
    articles=articles[:2],
    ai_summary="Today's AI breakthrough: Models are getting cheaper.",
    sponsor_html="...",
    campaign_id="camp-123"
)
```

#### Things to Know
- **Best for**: Busy professionals, tip seekers
- **Content**: Extracted lessons/tips from multiple articles
- **Frequency**: 2x per week
- **Engagement**: Very high (scannable, actionable)

```python
newsletter = create_things_to_know(
    articles=articles,
    tips_per_article=2,  # Extract 2 tips per article
    sponsor_html="..."
)
```

### Email Providers

#### Beehiiv (Recommended)
- Built-in subscriber management
- Advanced segmentation
- Monetization features (paid subscriptions)
- Free tier includes up to 10,000 subscribers

**Setup**:
1. Go to https://beehiiv.com
2. Create publication
3. API Console → Create API key
4. Copy `Publication ID` and `API Key` to `.env`

#### Resend (Fallback)
- Transactional email service
- Pay-per-send ($0.10 per 1000 emails)
- Great for triggered/transactional emails
- Ideal fallback if Beehiiv is down

**Setup**:
1. https://resend.com → Sign up
2. API Tokens → Create new token
3. Copy to `RESEND_API_KEY`

#### Substack (Optional)
- Free platform with built-in monetization
- No subscriber management (handled by Substack)
- Pay-per-read model
- Good for readers who prefer Substack format

**Setup**:
1. https://substack.com → Create publication
2. Settings → Integrations → Generate API token
3. Copy to `SUBSTACK_ACCESS_TOKEN`

### Subscriber Segmentation

Send different content to different segments:

```python
# Free subscribers get weekly digest with sponsors
send_newsletter(
    template_type="weekly_digest",
    articles=articles,
    recipient_segment="free",  # Beehiiv segment
    sponsor_html="..."
)

# Premium subscribers get daily briefing
send_newsletter(
    template_type="daily_briefing",
    articles=articles[:2],
    recipient_segment="premium",
    ai_summary="..."
)
```

**Segments in Beehiiv**:
- `all` — All subscribers
- `free` — Free tier only
- `premium` — Paid subscribers
- Custom segments based on tags, behavior, etc.

### Personalization

#### Read Time Estimates
Automatically calculated at 170 words-per-minute:

```python
from scripts.newsletter_publisher import _calculate_read_time

read_time = _calculate_read_time(article_text)  # Returns: 5, 8, 12, etc.
```

#### Affiliate Link Injection
Automatically inject affiliate links based on keywords:

```python
AFFILIATE_LINKS={
    "VPS hosting": "https://linode.com/ref",
    "AI tools": "https://groq.com/ref",
    "Database": "https://supabase.io/ref"
}
```

If article mentions "VPS hosting", link automatically becomes affiliate link.

#### UTM Tracking
All links automatically include UTM parameters:

```
Original: https://profitengine.alreadyherellc.com/article
Tracked:  https://profitengine.alreadyherellc.com/article?utm_source=profitengine&utm_medium=newsletter&utm_campaign=camp-123
```

Track in Google Analytics:
- Source: `profitengine`
- Medium: `newsletter`
- Campaign: Auto-generated UUID

---

## Monetization

### Pricing Tiers

| Tier | Price | Billing | Features |
|------|-------|---------|----------|
| **Free** | $0 | — | Weekly digest, Sponsor content, Archive |
| **Premium** | $7.99 | /month | Daily briefing, Early access (24h), Ad-free, Exclusive interviews |
| **Sponsor** | $300 | /week | Top banner, Click tracking, Metrics, Newsletter mentions |

### Revenue Projections

```python
from scripts.newsletter_publisher import calculate_newsletter_revenue

revenue = calculate_newsletter_revenue(
    free_subscribers=500,
    premium_subscribers=50,
    sponsor_slots=2,
    sponsor_rate=300.0
)

# Output:
# Premium Revenue: $399.50/mo
# Sponsor Revenue: $2,598.00/mo
# Total: $2,997.50/mo
```

### Implementation Checklist

- [ ] **Beehiiv Setup**
  - [ ] Create publication at https://beehiiv.com
  - [ ] Enable paid subscriptions (Settings → Monetization)
  - [ ] Set up pricing ($7.99/mo default)
  - [ ] Create subscriber groups (free, premium)

- [ ] **Sponsor Management**
  - [ ] Create sponsor booking form (Typeform/Airtable)
  - [ ] Set rate ($300-500/week)
  - [ ] Add sponsor HTML template
  - [ ] Setup sponsor tracking (UTM params)

- [ ] **Affiliate Links**
  - [ ] Register affiliate programs (AWS, Stripe, Vercel, etc.)
  - [ ] Get referral URLs
  - [ ] Add to `AFFILIATE_LINKS` env var

---

## Metrics & Analytics

### Key Metrics

| Metric | Target | Action if Low |
|--------|--------|---------------|
| **Open Rate** | 25-35% | Improve subject lines, send time |
| **Click Rate** | 3-5% | Improve call-to-action, add more links |
| **Conversion Rate** | 0.5-1.5% | A/B test sponsorships, optimize landing page |
| **Bounce Rate** | <2% | Clean subscriber list, check email validity |
| **Unsubscribe Rate** | <0.5% | Reduce send frequency, improve content |

### Fetch Metrics

```python
from scripts.newsletter_publisher import get_newsletter_metrics

metrics = get_newsletter_metrics(campaign_id="camp-123")

print(f"Delivered: {metrics.delivered_count}")
print(f"Opens: {metrics.open_count} ({metrics.open_rate:.1%})")
print(f"Clicks: {metrics.click_count} ({metrics.click_rate:.1%})")
print(f"Conversions: {metrics.conversion_count} ({metrics.conversion_rate:.1%})")
print(f"Bounces: {metrics.bounce_rate:.2%}")
print(f"Unsubscribes: {metrics.unsubscribe_rate:.2%}")
```

### Tracking Setup

Email client support for tracking:
- ✅ **Open tracking** — Pixel-based (works in 95%+ of clients)
- ✅ **Click tracking** — Link rewriting (100% compatible)
- ✅ **UTM tracking** — Google Analytics integration

---

## Scheduling & Automation

### Schedule Newsletter for Later

```python
from datetime import datetime, timezone, timedelta
from scripts.newsletter_publisher import schedule_newsletter

# Schedule for 2 hours from now
schedule_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

result = schedule_newsletter(
    template_type="weekly_digest",
    articles=articles,
    schedule_time=schedule_time,
    recipient_segment="all"
)

print(f"Scheduled: {result['campaign_id']} for {result['scheduled_for']}")
```

### Cron Job Example

Send weekly digest every Monday at 9 AM:

```bash
# .github/workflows/weekly-newsletter.yml
name: Weekly Newsletter

on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM UTC

jobs:
  send:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - env:
          BEEHIIV_API_KEY: ${{ secrets.BEEHIIV_API_KEY }}
          NEWSLETTER_PUBLICATION_ID: ${{ secrets.NEWSLETTER_PUBLICATION_ID }}
        run: python scripts/newsletter_publisher.py
```

---

## API Reference

### Core Functions

#### `send_newsletter()`

Send newsletter across configured providers.

```python
result = send_newsletter(
    template_type="weekly_digest",        # "weekly_digest" | "daily_briefing" | "things_to_know"
    articles=[Article(...), ...],         # List of Article objects
    recipient_segment="all",              # "all" | "free" | "premium" | custom
    sponsor_html="<h3>Sponsor</h3>",      # Optional sponsor message
    ai_summary="...",                     # Optional AI summary (for daily briefing)
    track_opens=True,                     # Enable open tracking
    track_clicks=True,                    # Enable click tracking
    providers=["beehiiv"]                 # List of providers to use
)

# Returns:
# {
#     "campaign_id": "uuid",
#     "template_type": "weekly_digest",
#     "subject": "Subject line",
#     "article_count": 5,
#     "recipient_segment": "all",
#     "timestamp": "2026-06-19T...",
#     "provider_results": {
#         "beehiiv": {"campaign_id": "...", "status": "sent"}
#     },
#     "success": True
# }
```

#### `schedule_newsletter()`

Schedule newsletter for future delivery.

```python
result = schedule_newsletter(
    template_type="weekly_digest",
    articles=[Article(...), ...],
    schedule_time="2026-06-20T09:00:00Z",  # ISO 8601 format
    recipient_segment="all",
    sponsor_html="...",
    provider="beehiiv"
)
```

#### `get_newsletter_metrics()`

Fetch campaign performance metrics.

```python
metrics = get_newsletter_metrics(
    campaign_id="camp-123",
    provider="beehiiv"
)

# Returns NewsletterMetrics object with:
# - sent_count, delivered_count
# - open_count, open_rate
# - click_count, click_rate
# - conversion_count, conversion_rate
# - bounce_rate, unsubscribe_rate
```

#### `create_weekly_digest()`, `create_daily_briefing()`, `create_things_to_know()`

Create newsletter HTML without sending.

```python
newsletter = create_weekly_digest(
    articles=[Article(...), ...],
    sponsor_html="...",
    campaign_id="..."
)

# Returns:
# {
#     "template_type": "weekly_digest",
#     "subject": "...",
#     "preview_text": "...",
#     "html": "<html>...",
#     "article_count": 5
# }
```

### Data Models

#### `Article`

Represents a single article.

```python
Article(
    id="art-001",                    # Unique ID
    title="Article Title",           # Required
    summary="Brief summary...",       # Required
    body="Full content...",           # Required
    canonical_url="https://...",      # Required, for tracking
    published_at="2026-06-19T...",    # ISO 8601, required
    author="Author Name",             # Required
    read_time_minutes=8,              # Required, integer
    image_url="https://...",          # Optional
    tags=["tag1", "tag2"]             # Optional
)
```

#### `NewsletterCampaign`

Metadata about a newsletter campaign.

```python
NewsletterCampaign(
    id="camp-123",
    template_type="weekly_digest",
    subject="Subject line",
    preview_text="Preview...",
    sender_email="dispatch@alreadyherellc.com",
    sender_name="Newsletter",
    recipient_segment="all",
    scheduled_for=None,               # For scheduled sends
    sent_at=None,                     # Populated after send
    open_rate=0.25,
    click_rate=0.04,
    status="sent"                     # "draft" | "scheduled" | "sent" | "failed"
)
```

#### `NewsletterMetrics`

Campaign performance data.

```python
NewsletterMetrics(
    campaign_id="camp-123",
    sent_count=1000,
    delivered_count=950,
    open_count=250,
    click_count=40,
    conversion_count=15,
    open_rate=0.263,
    click_rate=0.042,
    conversion_rate=0.016,
    bounce_rate=0.05,
    unsubscribe_rate=0.002,
    avg_read_time=3.2
)
```

---

## Testing

Run the test suite:

```bash
python scripts/test_newsletter_publisher.py
```

This will:
- Test all helper functions
- Create sample newsletters
- Validate HTML output
- Test segmentation
- Calculate monetization metrics
- (Won't actually send without API keys)

---

## Troubleshooting

### Newsletter Not Sending

**Problem**: `[SKIP] Beehiiv credentials not configured`

**Solution**:
1. Check `.env` has `BEEHIIV_API_KEY`
2. Check `.env` has `NEWSLETTER_PUBLICATION_ID`
3. Run: `echo $BEEHIIV_API_KEY` to verify it's set

### Invalid API Key

**Problem**: `[FAIL] Beehiiv API error 401`

**Solution**:
1. Go to https://beehiiv.com/dashboard
2. Settings → API → Check API token is correct
3. Ensure no leading/trailing spaces in `.env`

### Campaign Not Found

**Problem**: `[FAIL] Metrics API error 404`

**Solution**:
1. Verify `campaign_id` is correct
2. Wait 5-10 minutes after send (Beehiiv needs time to index)
3. Check campaign actually sent successfully

### Affiliate Links Not Injecting

**Problem**: Article links aren't being replaced with affiliate URLs

**Solution**:
1. Check `AFFILIATE_LINKS` is valid JSON
2. Verify keyword in `AFFILIATE_LINKS` matches article content
3. Check URL parsing logic (some URLs may have special characters)

---

## Best Practices

### Content

- ✅ Keep articles to 5-10 min read time
- ✅ Use clear, action-oriented headlines
- ✅ Include 1-2 calls-to-action per email
- ✅ Link to full articles (drive traffic to main site)
- ✅ Vary content topics to maintain engagement

### Sending

- ✅ Test on multiple clients (Gmail, Outlook, Apple Mail)
- ✅ Use A/B testing for subject lines
- ✅ Send at consistent times (9 AM local time)
- ✅ Warm up sender domain (avoid spam folder)
- ✅ Monitor bounce rate (>5% is concerning)

### Monetization

- ✅ Start with free tier to build audience
- ✅ Offer premium after 500+ subscribers
- ✅ Price premium at $5-10/month
- ✅ Limit sponsors to 1-2 per email
- ✅ Disclose affiliate links (FTC compliance)

### Metrics

- ✅ Track opens and clicks for all campaigns
- ✅ Review metrics after 24 hours
- ✅ A/B test templates and content
- ✅ Build historical comparison
- ✅ Set goals: "30% open rate", "5% click rate"

---

## Examples

### Daily Email Workflow

```python
# 1. Fetch today's published articles
articles = fetch_articles_from_database(days=1)

# 2. Generate AI summary
summary = generate_ai_summary(articles)

# 3. Create newsletter
newsletter = create_daily_briefing(
    articles=articles[:2],
    ai_summary=summary
)

# 4. Schedule for 9 AM tomorrow
schedule_time = get_tomorrow_9am_utc()
schedule_newsletter(
    template_type="daily_briefing",
    articles=articles,
    schedule_time=schedule_time
)

# 5. Check metrics from yesterday's send
yesterday_campaign = get_last_sent_campaign()
metrics = get_newsletter_metrics(yesterday_campaign.id)
if metrics.open_rate < 0.20:
    print(f"⚠ Low open rate: {metrics.open_rate:.1%}")
```

### Monthly Sponsor Onboarding

```python
# 1. Get sponsor details from booking form
sponsor = {
    "name": "FastAPI Pro",
    "html": "<h3>Sponsor: FastAPI Pro</h3>...",
    "url": "https://fastapi.pro/ref",
    "start_date": "2026-07-01",
    "end_date": "2026-07-31",
}

# 2. Schedule weekly sends with sponsor banner
for week in range(4):
    send_date = parse_date(sponsor["start_date"]) + timedelta(weeks=week)
    schedule_newsletter(
        template_type="weekly_digest",
        articles=articles,
        schedule_time=send_date.isoformat(),
        sponsor_html=sponsor["html"]
    )

# 3. Generate sponsor report at month end
metrics = get_month_campaign_metrics(sponsor["start_date"], sponsor["end_date"])
report = {
    "sponsor": sponsor["name"],
    "emails_sent": metrics.sent_count,
    "clicks": metrics.click_count,
    "click_rate": metrics.click_rate,
    "conversions": metrics.conversion_count
}
print_sponsor_report(report)
```

---

## Support

For issues:
1. Check API key configuration
2. Run test suite: `python scripts/test_newsletter_publisher.py`
3. Enable debug logging (set `DEBUG=true`)
4. Check Beehiiv/Resend dashboard for error details

Contact: dispatch@alreadyherellc.com

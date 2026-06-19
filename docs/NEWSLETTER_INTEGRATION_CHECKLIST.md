# Newsletter Publisher Integration Checklist

**Setup and deployment guide for the newsletter_publisher.py module**

---

## Pre-Flight Checklist

### Files Created
- [ ] `scripts/newsletter_publisher.py` — Main module (35.8 KB)
- [ ] `scripts/test_newsletter_publisher.py` — Test suite (13 KB)
- [ ] `docs/NEWSLETTER_PUBLISHER_GUIDE.md` — User documentation
- [ ] `docs/NEWSLETTER_INTEGRATION_CHECKLIST.md` — This file

### Dependencies
Check `requirements.txt` includes:
```
httpx>=0.24.0
python-dotenv>=1.0.0
```

Run:
```bash
pip install -r requirements.txt
```

---

## 1. Beehiiv Setup (Primary Provider)

### 1.1 Create Beehiiv Publication

- [ ] Go to https://beehiiv.com/dashboard
- [ ] Click "New Publication"
- [ ] Enter publication name: **"ProfitEngine Newsletter"**
- [ ] Configure publication settings:
  - [ ] Set description: "AI-powered content distribution, monetized"
  - [ ] Set default sender: "dispatch@alreadyherellc.com"
  - [ ] Set sender name: "ProfitEngine Newsletter"

### 1.2 Enable Monetization (Optional)

- [ ] Settings → Monetization → Enable Paid Subscriptions
- [ ] Set subscription tier:
  - [ ] Price: $7.99/month
  - [ ] Name: "Premium"
  - [ ] Description: "Daily briefings + exclusive interviews"
- [ ] Create subscriber segments in Beehiiv:
  - [ ] **free** — Free tier subscribers
  - [ ] **premium** — Paid subscribers
  - [ ] **sponsor** — Sponsor contacts

### 1.3 Generate API Key

- [ ] Settings → API & Integrations
- [ ] Click "Create API Key"
- [ ] Copy **API Key** (starts with `api_...`)
- [ ] Copy **Publication ID** (UUID format)

### 1.4 Add to Environment

Add to `.env`:
```bash
BEEHIIV_API_KEY=api_xxxxxxxxxxxxxxxx
NEWSLETTER_PUBLICATION_ID=00000000-0000-0000-0000-000000000000
```

Or GitHub Secrets:
```
Repository Settings → Secrets and variables → Actions
- BEEHIIV_API_KEY
- NEWSLETTER_PUBLICATION_ID
```

---

## 2. Resend Setup (Fallback Provider)

### 2.1 Create Resend Account

- [ ] Go to https://resend.com
- [ ] Sign up with dispatch@alreadyherellc.com
- [ ] Verify email

### 2.2 Add Domain

- [ ] Dashboard → Domains
- [ ] Add Domain: `profitengine.alreadyherellc.com`
- [ ] Add DNS records (follow Resend instructions)
- [ ] Wait for domain verification (5-15 minutes)

### 2.3 Generate API Key

- [ ] Settings → API Tokens
- [ ] Create API Token
- [ ] Copy token (starts with `re_...`)

### 2.4 Add to Environment

```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
```

---

## 3. Substack Setup (Optional)

### 3.1 Create Substack Publication

- [ ] Go to https://substack.com
- [ ] Sign up with dispatch@alreadyherellc.com
- [ ] Create publication: "ProfitEngine"

### 3.2 Generate API Token

- [ ] Settings → Integrations
- [ ] API Tokens → Generate Token
- [ ] Copy token

### 3.3 Add to Environment

```bash
SUBSTACK_ACCESS_TOKEN=st_xxxxxxxxxxxxxxxx
```

---

## 4. Configuration

### 4.1 Newsletter Metadata

Add to `.env`:
```bash
NEWSLETTER_SENDER_EMAIL=dispatch@alreadyherellc.com
NEWSLETTER_SENDER_NAME=ProfitEngine Newsletter
PROFITENGINE_DOMAIN=profitengine.alreadyherellc.com
```

### 4.2 Monetization

Add to `.env`:
```bash
AFFILIATE_LINKS={"VPS hosting":"https://linode.com/ref","AI tools":"https://groq.com/ref"}
AMAZON_PARTNER_TAG=alreadyhere-20
```

### 4.3 Verify Configuration

Run:
```bash
python scripts/test_newsletter_publisher.py
```

Expected output:
```
[PASS] All tests passed!
```

---

## 5. Initial Data Import

### 5.1 Seed Subscriber List (Beehiiv)

```python
# scripts/import_subscribers.py (example)
import httpx

subscribers = [
    {"email": "user1@example.com", "name": "User 1", "tier": "free"},
    {"email": "user2@example.com", "name": "User 2", "tier": "premium"},
]

with httpx.Client() as client:
    for sub in subscribers:
        response = client.post(
            f"https://api.beehiiv.com/v1/subscriptions",
            json={
                "email": sub["email"],
                "name": sub["name"],
                "doubleOptin": False,
            },
            headers={"Authorization": f"Bearer {BEEHIIV_API_KEY}"}
        )
```

### 5.2 Create Test Segment

- [ ] Beehiiv Dashboard → Audiences → Create Segment
- [ ] Name: "test"
- [ ] Add 5 test emails (including yours)

### 5.3 Send Test Newsletter

```python
from scripts.newsletter_publisher import Article, send_newsletter

articles = [
    Article(
        id="test-1",
        title="Test Article",
        summary="Testing the newsletter system",
        body="Full content...",
        canonical_url="https://profitengine.alreadyherellc.com/test",
        published_at="2026-06-19T00:00:00Z",
        author="Stephen",
        read_time_minutes=3,
    )
]

result = send_newsletter(
    template_type="weekly_digest",
    articles=articles,
    recipient_segment="test",
    providers=["beehiiv"]
)

print(f"Campaign ID: {result['campaign_id']}")
```

Check emails in test inbox.

---

## 6. Integration with Content Pipeline

### 6.1 Trigger on Article Publish

Add to publish workflow (e.g., `publish_article.py`):

```python
from scripts.newsletter_publisher import send_newsletter, Article

# After publishing article...
article = Article(
    id=article_id,
    title=published_title,
    summary=meta_description,
    body=content_body,
    canonical_url=published_url,
    published_at=datetime.now(timezone.utc).isoformat(),
    author="ProfitEngine AI",
    read_time_minutes=calculate_read_time(content_body),
)

# Send immediately to premium subscribers
send_newsletter(
    template_type="daily_briefing",
    articles=[article],
    recipient_segment="premium",
    providers=["beehiiv"]
)
```

### 6.2 Daily Digest Cron Job

Create `.github/workflows/daily-newsletter.yml`:

```yaml
name: Daily Newsletter

on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:

jobs:
  send-daily:
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
        run: python scripts/send_daily_newsletter.py
```

Create `scripts/send_daily_newsletter.py`:

```python
#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from scripts.newsletter_publisher import send_newsletter, Article
from scripts.publish_article import fetch_articles  # Your article fetch function

# Get articles published in last 24 hours
articles = fetch_articles(
    published_after=datetime.now(timezone.utc) - timedelta(hours=24)
)

if articles:
    result = send_newsletter(
        template_type="daily_briefing",
        articles=articles[:2],
        recipient_segment="premium",
        providers=["beehiiv"]
    )
    print(f"Daily newsletter sent: {result['campaign_id']}")
else:
    print("No articles to send")
```

### 6.3 Weekly Digest Cron Job

Create `.github/workflows/weekly-newsletter.yml`:

```yaml
name: Weekly Newsletter

on:
  schedule:
    - cron: '0 9 * * 1'  # 9 AM UTC every Monday
  workflow_dispatch:

jobs:
  send-weekly:
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
        run: python scripts/send_weekly_newsletter.py
```

---

## 7. Sponsor Management

### 7.1 Sponsor Booking Form

Create form in Airtable/Typeform:
- Sponsor name
- Banner HTML
- URL (for click tracking)
- Start date
- End date
- Price ($300-500/week)

### 7.2 Sponsor Email Template

```python
sponsor_html = """
<table style="width: 100%; background: #f5f5f5; border-radius: 8px; padding: 20px;">
  <tr>
    <td>
      <h3 style="color: #667eea; margin-top: 0;">This Week's Sponsor</h3>
      <p><strong>FastAPI Pro</strong> — Build production APIs in minutes.</p>
      <p>Special discount for ProfitEngine readers: <strong>50% off annual plan</strong></p>
      <a href="https://fastapi.pro/ref" style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Get Started →</a>
    </td>
  </tr>
</table>
"""

send_newsletter(
    template_type="weekly_digest",
    articles=articles,
    recipient_segment="all",
    sponsor_html=sponsor_html,
    providers=["beehiiv"]
)
```

### 7.3 Sponsor Metrics Report

```python
from scripts.newsletter_publisher import get_newsletter_metrics

# Get all campaigns in date range
campaigns = beehiiv_client.get_campaigns(
    start_date="2026-07-01",
    end_date="2026-07-31"
)

for campaign in campaigns:
    if "FastAPI Pro" in campaign.subject:
        metrics = get_newsletter_metrics(campaign.id)
        print(f"Sponsor: FastAPI Pro")
        print(f"Emails: {metrics.delivered_count}")
        print(f"Clicks: {metrics.click_count} ({metrics.click_rate:.1%})")
        print(f"Conversions: {metrics.conversion_count}")
```

---

## 8. Metrics & Reporting

### 8.1 Weekly Metrics Report

Create `scripts/generate_newsletter_report.py`:

```python
from datetime import datetime, timedelta, timezone
from scripts.newsletter_publisher import get_newsletter_metrics

# Get campaigns from last 7 days
start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
end_date = datetime.now(timezone.utc).isoformat()

campaigns = beehiiv_client.get_campaigns(start_date, end_date)

print("Newsletter Metrics Report")
print("=" * 60)

total_sent = 0
total_opens = 0
total_clicks = 0

for campaign in campaigns:
    metrics = get_newsletter_metrics(campaign.id)
    total_sent += metrics.sent_count
    total_opens += metrics.open_count
    total_clicks += metrics.click_count
    
    print(f"\n{campaign.subject}")
    print(f"  Sent: {metrics.sent_count}")
    print(f"  Opens: {metrics.open_count} ({metrics.open_rate:.1%})")
    print(f"  Clicks: {metrics.click_count} ({metrics.click_rate:.1%})")

print(f"\nTotal")
print(f"  Sent: {total_sent}")
print(f"  Opens: {total_opens} ({total_opens/total_sent:.1%})")
print(f"  Clicks: {total_clicks} ({total_clicks/total_sent:.1%})")
```

### 8.2 Send Report to Email

```python
import smtplib
from email.mime.text import MIMEText

report = generate_newsletter_report()

msg = MIMEText(report, "plain")
msg["Subject"] = "Weekly Newsletter Report"
msg["From"] = "stephen47@gmail.com"
msg["To"] = "dispatch@alreadyherellc.com"

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_USER, "dispatch@alreadyherellc.com", msg.as_string())

print("Report sent!")
```

---

## 9. Monetization Launch

### 9.1 Premium Tier Launch

- [ ] Create premium tier in Beehiiv ($7.99/month)
- [ ] Add premium content (daily briefing for premium only)
- [ ] Announce in weekly newsletter
- [ ] Set initial target: 25 premium subscribers

### 9.2 Sponsor Tier Launch

- [ ] Create sponsor inquiry form
- [ ] Set sponsor rate: $300-500/week
- [ ] Create sponsor media kit
- [ ] Reach out to 10-15 companies in target space

### 9.3 Revenue Projection

```python
from scripts.newsletter_publisher import calculate_newsletter_revenue

# 500 free, 25 premium, 2 sponsors
revenue = calculate_newsletter_revenue(
    free_subscribers=500,
    premium_subscribers=25,
    sponsor_slots=2,
    sponsor_rate=350.0
)

print(f"Monthly Premium: ${revenue['premium_revenue_monthly_usd']:.2f}")
print(f"Monthly Sponsors: ${revenue['sponsor_revenue_monthly_usd']:.2f}")
print(f"Total Monthly: ${revenue['total_monthly_usd']:.2f}")
```

---

## 10. Production Verification

### 10.1 Pre-Launch Checklist

- [ ] All environment variables set in GitHub Secrets
- [ ] Test send to segment "test" successful
- [ ] Metrics fetching working
- [ ] Sponsor template renders correctly
- [ ] Affiliate links injecting correctly
- [ ] UTM tracking working in Google Analytics
- [ ] Unsubscribe link present in emails
- [ ] FTC disclosure in email footer
- [ ] SPF/DKIM configured for sender domain

### 10.2 Launch Day Verification

- [ ] Send first production newsletter
- [ ] Verify delivery to test segment
- [ ] Check open rate after 1 hour
- [ ] Click links, verify UTM parameters
- [ ] Check Google Analytics for utm_medium=newsletter traffic
- [ ] Monitor bounce rate (should be <2%)

### 10.3 First Week Monitoring

- [ ] Daily check of open rates
- [ ] Monitor unsubscribe rate (should stay <0.5%)
- [ ] Review click-through destinations
- [ ] Check conversion tracking
- [ ] Get feedback from initial subscribers

---

## 11. Troubleshooting

### Issue: "Beehiiv credentials not configured"

**Solution**:
1. Verify `BEEHIIV_API_KEY` set: `echo $BEEHIIV_API_KEY`
2. Verify `NEWSLETTER_PUBLICATION_ID` set
3. Check no extra spaces in `.env`
4. Restart shell/GitHub Actions runner

### Issue: API returns 401 Unauthorized

**Solution**:
1. Go to Beehiiv dashboard
2. Settings → API & Integrations
3. Regenerate API key if needed
4. Update `.env` / GitHub Secrets

### Issue: Emails going to spam

**Solution**:
1. Configure SPF: `v=spf1 include:sendmail.beehiiv.com ~all`
2. Configure DKIM: Follow Beehiiv instructions
3. Warm up sender IP (send to own email first)
4. Avoid spam trigger words

### Issue: Click tracking not working

**Solution**:
1. Verify UTM parameters in HTML: `utm_source=profitengine&utm_medium=newsletter`
2. Check Google Analytics property created
3. Wait 24 hours for data to populate
4. Check that Beehiiv's `track_clicks=True`

---

## 12. Success Metrics

### Month 1 Goals
- [ ] 100+ free subscribers
- [ ] Send 4 weekly newsletters
- [ ] 25%+ open rate
- [ ] 3-5% click rate
- [ ] 0 major delivery issues

### Month 2-3 Goals
- [ ] 250+ free subscribers
- [ ] 5+ premium subscribers
- [ ] 1 sponsor locked in ($300/week)
- [ ] 28%+ average open rate
- [ ] Revenue: $1,000+

### Month 4+ Goals
- [ ] 500+ subscribers
- [ ] 25+ premium subscribers
- [ ] 2-3 sponsors ($600-900/week)
- [ ] 30%+ open rate, 5%+ click rate
- [ ] Revenue: $2,500+/month

---

## Support

For issues: dispatch@alreadyherellc.com
For API docs: https://docs.beehiiv.com/api
For testing: Run `python scripts/test_newsletter_publisher.py`

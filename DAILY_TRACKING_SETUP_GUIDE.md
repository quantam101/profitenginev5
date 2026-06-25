# Daily Revenue Tracking Setup Guide

## Overview
This guide walks through setting up automated daily revenue tracking across all 8 revenue streams:
1. Gumroad (hourly checks)
2. Email metrics
3. Social media (YouTube, TikTok, Instagram, X, LinkedIn)
4. Affiliate programs
5. Sponsorships
6. Consulting bookings
7. Trading P&L
8. Health checks & alerts

---

## Quick Start (5 minutes)

### Step 1: Copy the Template
```bash
cp DAILY_REVENUE_TRACKING_TEMPLATE.md ./tracking/daily_tracking_$(date +%Y-%m-%d).md
```

### Step 2: Fill In Your Baseline Data
1. Open the copied template
2. Fill in your current:
   - Product names (Gumroad)
   - Email list size
   - Social media follower counts
   - Affiliate program names
   - YouTube channel stats
   - Trading account details

### Step 3: Set Up GitHub Secrets
Configure these in GitHub Actions → Settings → Secrets and variables → Actions:

```
GUMROAD_API_KEY              [Your Gumroad API token]
STRIPE_SECRET_KEY            [Your Stripe secret key]
YOUTUBE_API_KEY              [Your YouTube Data API key]
EMAIL_PLATFORM_API_KEY       [Mailchimp/ConvertKit/etc token]
AFFILIATE_API_KEY            [Your affiliate network API key]
TRADING_API_KEY              [Robinhood/Tradier/etc token]
SENDGRID_API_KEY             [For email summaries]
SLACK_WEBHOOK_REVENUE_ALERTS [Your Slack webhook]
DAILY_TRACKING_EMAIL         [Your email for summaries]
```

### Step 4: Enable Automation
The workflow `.github/workflows/daily_revenue_tracking.yml` automatically:
- ✅ Runs hourly Gumroad checks
- ✅ Generates daily consolidated report at 9 AM UTC
- ✅ Emails summary to you
- ✅ Posts to Slack
- ✅ Commits reports to git

---

## Platform-by-Platform Setup

### 1. GUMROAD SETUP

#### Get API Key
1. Go to gumroad.com → Settings → Developer
2. Generate API token
3. Add to GitHub Secrets as `GUMROAD_API_KEY`

#### Metrics Captured
- Products: name, sales (24h), revenue (24h)
- Customer data: new customers, refunds, cancellations
- Page views, conversion rate, AVG order value

#### Automation
- Hourly check via GitHub Actions (top of every hour)
- Logs to: `daily_revenue_YYYY-MM-DD.json`
- Dashboard check script: `scripts/daily_revenue_tracker.py`

#### Manual Check
```bash
curl -H "Authorization: Bearer $GUMROAD_API_KEY" \
  https://api.gumroad.com/v2/products | jq
```

---

### 2. EMAIL METRICS (Mailchimp, ConvertKit, etc.)

#### Mailchimp Setup
1. Go to Mailchimp → Account → Extras → API Keys
2. Create new API key
3. Note your Mailchimp Server (e.g., `us1`, `us2`, etc.)
4. Add to GitHub Secrets

#### Metrics Captured
- List size, growth rate (24h)
- Campaign opens, clicks, conversions
- Unsubscribe rate, bounce rate
- Revenue attributed to email

#### Sample API Call
```bash
curl -s -X GET "https://us1.api.mailchimp.com/3.0/lists" \
  -u "user:$MAILCHIMP_API_KEY"
```

#### Email Revenue Tracking
- Create UTM parameters for email links:
  - `utm_source=email`
  - `utm_medium=newsletter`
  - `utm_campaign=[campaign-name]`
- Track conversions through Google Analytics
- Link to Gumroad/Stripe for revenue attribution

---

### 3. SOCIAL MEDIA METRICS

#### YouTube Setup
1. Enable YouTube Data API v3 in Google Cloud Console
2. Create OAuth 2.0 credentials
3. Generate API key
4. Add to GitHub Secrets as `YOUTUBE_API_KEY`

#### YouTube Metrics
- Views (24h, 7d, 30d)
- Watch time (hours)
- Subscribers gained
- Revenue (if monetized)
  - AdSense revenue
  - Channel memberships
  - Super Chat/Thanks
  - Shorts Bonus Fund
- Click-through rate (CTR)

#### YouTube Analytics Query
```bash
curl -s "https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true" \
  -H "Authorization: Bearer $YOUTUBE_API_KEY"
```

#### TikTok Setup
1. Apply for TikTok Creator Analytics API access
2. Get API credentials
3. Use to track:
   - Video views
   - Engagement (likes, comments, shares)
   - Follower growth
   - Link clicks

#### Instagram Setup
1. Use Meta Business Platform
2. Get Graph API access
3. Track:
   - Post impressions
   - Engagement rate
   - Story views
   - Link clicks (in bio)

#### X/Twitter Setup
1. Apply for API access at developer.twitter.com
2. Get v2 API credentials
3. Track:
   - Post impressions
   - Engagement rate
   - Mention volume

---

### 4. AFFILIATE TRACKING

#### Tracking Setup
Affiliate networks often provide:
- Real-time dashboard (check hourly)
- API access (optional)
- Click tracking links (must use consistently)

#### Popular Affiliate Networks
| Network | Setup Difficulty | Real-time API | Revenue Share |
|---------|------------------|---------------|--------------|
| Amazon Associates | Easy | Limited | 3-10% |
| ShareASale | Medium | Yes | 5-25% |
| CJ Affiliate | Medium | Yes | 5-20% |
| Impact | Hard | Yes | Custom |
| Refersion | Easy | Yes | 10-30% |
| Kenshoo | Hard | Yes | Custom |

#### Setup Each Program
1. **Get Unique Affiliate ID/Link**
   - Amazon: `alreadyhere-20`
   - Others: link to affiliate dashboard

2. **Place Links**
   - Email newsletters
   - Blog posts / content
   - YouTube description
   - Social media bios
   - Product recommendations

3. **Track Clicks & Conversions**
   - Use UTM params: `utm_source=affiliate&utm_medium=[program]`
   - Monitor dashboard daily
   - Record clicks/conversions/revenue in template

#### Revenue Attribution
Track per-program:
- Clicks (24h)
- Conversion rate
- Average order value
- Commission per sale
- Total revenue (24h, weekly, monthly)

#### Sample API (ShareASale)
```bash
curl -X GET "https://api.shareasale.com/x/api/stats" \
  -H "Authorization: Bearer $SHAREASALE_API_KEY" \
  -d "token=$SHAREASALE_TOKEN&action=lastMonth"
```

---

### 5. SPONSORSHIP TRACKING

#### Setup Spreadsheet
Create a tracking sheet with:
- Sponsor name
- Deal type (flat fee, performance-based, hybrid)
- Expected value ($)
- Duration
- Deliverables
- Status (pipeline, negotiating, active, expired)
- Performance metrics (impressions, clicks, conversions)

#### Metrics to Track
1. **Deliverables**
   - Mention in email newsletter
   - Social media posts
   - YouTube video integration
   - Blog article placement
   - Ad slots

2. **Performance**
   - Impressions on each channel
   - Clicks to sponsor site
   - Conversions attributed
   - ROI for sponsor

3. **Revenue**
   - Direct sponsorship fee
   - Performance bonuses
   - Affiliate revenue from sponsor products

#### Follow-up Automation
- Prospect list: track outreach stage
- Deal status: weekly updates
- Performance: measure post-launch

---

### 6. CONSULTING BOOKINGS

#### Setup Calendar Integration
1. Use Google Calendar for bookings
2. Create event categories:
   - Consulting (billable)
   - Sales calls (pipeline)
   - Delivery (project fulfillment)

3. Add metadata to events:
   - Client name
   - Service type
   - Duration
   - Rate
   - Status

#### Metrics to Track
- Billable hours (24h, weekly, monthly)
- Monthly Recurring Revenue (MRR)
- Pipeline value (active proposals)
- Sales cycle length
- Win rate (proposals → deals)
- Average project value

#### Revenue Calculation
```
Consulting Revenue = (Billable Hours × Hourly Rate) + Project Fees
Monthly Target = (Billable Hours Target × Rate) + (Project Fee Targets)
```

#### Booking Tracking
- Create leads from email/social inbound
- Track proposal sent date
- Monitor close date
- Calculate time-to-close

#### Sample Metrics
| Service | Rate | Sessions (24h) | Revenue (24h) | Weekly Avg |
|---------|------|----------------|---------------|-----------|
| 1-on-1 Coaching | $200/h | 0 | $0 | $0 |
| Strategy Session | $500 | 0 | $0 | $0 |
| Full Consulting | $2000 | 0 | $0 | $0 |

---

### 7. TRADING P&L

#### Account Setup
Connect your trading account:
- Robinhood
- Tradier
- Interactive Brokers
- ThinkorSwim

#### API Integration
Get API credentials and track:
- Daily portfolio value
- P&L (closed trades)
- Open positions
- Win rate (wins/total trades)
- Risk metrics

#### Daily Metrics
| Metric | Formula | 24h Value |
|--------|---------|-----------|
| Daily P&L | (Closed wins - Closed losses) | $0 |
| Win Rate | (Winning trades / Total trades) × 100 | 0% |
| Profit Factor | (Gross profit / Gross loss) | 0x |
| Avg Win | (Total wins / # wins) | $0 |
| Avg Loss | (Total losses / # losses) | -$0 |

#### Trading Log
Record each trade:
- Entry time/price
- Exit time/price
- Quantity
- P&L
- Reason for trade

---

### 8. HEALTH CHECKS & ALERTS

#### Connection Verification
Daily check that all integrations are:
- ✅ APIs responding
- ✅ Authentication valid
- ✅ No recent errors
- ✅ Data freshness (< 24h old)

#### Alerts to Monitor
| Alert | Severity | Action |
|-------|----------|--------|
| Payment processor down | Critical | Manual check & retry |
| API rate limit hit | High | Reduce frequency or upgrade |
| Missing API key | High | Add key to GitHub Secrets |
| Data sync delay | Medium | Check platform status |
| Negative P&L (trading) | Low | Monitor position |

#### Status Dashboard
Create a simple status page showing:
- Last check time
- Integration health (✓/✗)
- Days since update
- Error count

---

## Complete Automation Setup

### GitHub Actions Workflow
File: `.github/workflows/daily_revenue_tracking.yml`

**Triggers:**
- `0 * * * *` — Hourly Gumroad check
- `0 9 * * *` — Daily 9 AM UTC aggregation
- Manual trigger available

**Jobs:**
1. **hourly-check** — Fetch Gumroad metrics
2. **daily-aggregation** — Consolidate all sources
3. **email-summary** — Send email report
4. **slack-notification** — Slack alert

**Outputs:**
- JSON report: `daily_revenue_YYYY-MM-DD.json`
- Markdown summary: `DAILY_REVENUE_REPORT.md`
- Email notification
- Slack notification

### Manual Daily Update Workflow

1. **Morning (9 AM UTC)**
   - GitHub Actions runs automated pull
   - Check email for summary
   - Review Slack notification

2. **Throughout Day**
   - Check Gumroad dashboard (automated hourly)
   - Monitor affiliate networks
   - Track consulting activity

3. **Evening (6 PM UTC)**
   - Manual update: add any missing metrics
   - Edit: `daily_tracking_YYYY-MM-DD.md`
   - Commit changes to git

---

## Monthly Review Process

### First of Month
1. **Archive previous month**
   ```bash
   mkdir -p archives/2026-06
   mv DAILY_REVENUE_TRACKING_*.md archives/2026-06/
   mv daily_revenue_*.json archives/2026-06/
   ```

2. **Calculate monthly totals**
   - Sum daily revenue by stream
   - Calculate month-over-month growth
   - Identify top performers

3. **Review and optimize**
   - Which streams underperformed?
   - Which need investment?
   - New opportunities?

### Quarterly Review
1. **Analyze trends**
   - Revenue growth rate
   - Stream stability
   - Seasonality patterns

2. **Set targets for next quarter**
   - Revenue goals per stream
   - New stream launches
   - Optimization priorities

---

## Troubleshooting

### Gumroad API Not Connecting
- Verify token is current (regenerate if needed)
- Check GitHub Secret is set correctly
- Test manually: `curl -H "Authorization: Bearer TOKEN" https://api.gumroad.com/v2/products`

### Missing Email Metrics
- Verify API key for email platform
- Confirm you have API access enabled
- Check API documentation for v3 vs legacy endpoints

### YouTube Data Not Showing
- YouTube Analytics requires OAuth (more complex than API key)
- Alternative: use YouTube Studio API directly
- Or manually record metrics in template

### Affiliate Numbers Don't Match
- Check date ranges (24h vs calendar day)
- Verify using correct timezone
- Some networks have reporting delays

### Trading Account Not Connected
- Verify API credentials
- Check that paper trading vs live account selected
- Confirm account has trading activity enabled

---

## File Structure

```
profitengine-v5/
├── DAILY_REVENUE_TRACKING_TEMPLATE.md    # Main template
├── DAILY_TRACKING_SETUP_GUIDE.md          # This guide
├── .github/workflows/
│   └── daily_revenue_tracking.yml         # Automation
├── scripts/
│   └── daily_revenue_tracker.py           # Python aggregator
├── tracking/                              # Daily tracking files
│   └── daily_tracking_2026-06-25.md       # Daily updates
└── archives/                              # Monthly archives
    └── 2026-06/
        └── DAILY_REVENUE_TRACKING_*.md    # Monthly files
```

---

## Next Steps

1. **Today**
   - [ ] Copy template: `DAILY_REVENUE_TRACKING_TEMPLATE.md`
   - [ ] Fill in baseline data
   - [ ] Add GitHub Secrets

2. **This Week**
   - [ ] Set up API access for each platform
   - [ ] Test connections manually
   - [ ] Enable GitHub Actions workflow

3. **This Month**
   - [ ] Run first automated daily report
   - [ ] Create first monthly summary
   - [ ] Optimize tracking based on real data

---

## Support & References

### API Documentation
- **Gumroad:** https://gumroad.com/api
- **Stripe:** https://stripe.com/docs/api
- **YouTube:** https://developers.google.com/youtube
- **Mailchimp:** https://mailchimp.com/developer/marketing/
- **ShareASale:** https://shareasale.com/help
- **Robinhood:** API not officially supported (use unofficial)
- **Tradier:** https://tradier.com/documentation

### Tools & Services
- **Google Analytics** — UTM tracking & revenue attribution
- **SendGrid** — Email delivery
- **Slack API** — Real-time alerts
- **GitHub Actions** — Free automation

---

**Last Updated:** 2026-06-25  
**Next Review:** 2026-07-25  
**Version:** 1.0

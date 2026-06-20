# ProfitEngine v5 — Automation Triggers & Schedules

## Overview

Complete documentation of all automation triggers that run ProfitEngine's product launches, social media posting, and email marketing.

---

## Daily Triggers

### 📱 Instagram Stories (3x Daily)

**Times**: 07:00 UTC, 14:00 UTC, 20:00 UTC
**What happens**:
- Generates 3 unique story images (via DALL-E or Replicate)
- Cycles through all active products (Trading Course → Alert System → Profit Blueprint)
- Includes current engagement metrics, sales count, or customer testimonial
- Auto-posts to Instagram via Graph API
- Logs post metrics to `automation-status.json`

**Schedule**:
```
Morning:   07:00 UTC
Midday:    14:00 UTC
Evening:   20:00 UTC
```

**Example Story Flow**:
- 07:00: "Good morning traders! 📈 97 followers, 14 sales this week, +2 overnight"
- 14:00: "Lunch break tip: Set trailing stops on your alert system 🎯"
- 20:00: "Market closed. Here's your daily digest 📊"

**Failure Handling**:
- If image generation fails: fallback to pre-designed story template
- If Instagram API fails: queue story for next attempt (max 3 retries)
- If all retries fail: send Slack alert to `#automation-alerts`

---

## Weekly Triggers

### 📸 Instagram Carousels (3x Weekly)

**Days**: Tuesday, Thursday, Saturday
**Time**: 09:00 UTC
**Duration**: ~1 minute per product

**What happens**:
1. Generates 5-slide carousel for each active product
2. Slide 1: Product hero image + title
3. Slide 2: Key benefit #1 + screenshot
4. Slide 3: Key benefit #2 + testimonial
5. Slide 4: Pricing & CTA
6. Slide 5: Affiliate link / email signup CTA
7. Posts to Instagram with hashtags: `#profittrading #financialfreedom #daytrading`

**Product Rotation**:
- Tuesday: Trading Course
- Thursday: Alert System
- Saturday: Profit Blueprint

**Caption Template**:
```
[PRODUCT NAME] 🚀

Get started with [FEATURE]: [BENEFIT]

Link in bio → [GUMROAD_URL]
Mention a trader who needs this 👇

#profittrading #daytrading #financialfreedom
```

**Failure Handling**:
- Fallback: Post pre-generated carousel images if API fails
- Retry: 3 attempts at 5-min intervals
- Alert: Slack notification if carousel fails after 3 retries

---

### 🎬 Instagram Reels (3x Weekly)

**Days**: Monday, Wednesday, Friday
**Time**: 10:00 UTC
**Duration**: ~2 minutes per product (includes video generation)

**What happens**:
1. Generates 15-30 second reel using Synthesia API
2. Script: Product demo narrated by AI avatar (Eleven Labs voiceover)
3. Background: Relevant B-roll / screen recording
4. Graphics: Price, CTA, product name overlay
5. Posts to Instagram as Reel
6. Pins comment with affiliate link

**Reel Topics** (rotating):
- Monday: "5-minute setup tutorial"
- Wednesday: "Before/after profit comparison"
- Friday: "Week review + top trade"

**Failure Handling**:
- If video generation fails: post static image carousel instead
- If Synthesia API unavailable: use Replicate for fallback video
- If audio fails: post silent reel with captions
- Alert: Slack if reel generation takes >5 mins

---

### 📧 Email Campaign (Weekly)

**Day**: Monday
**Time**: 08:00 UTC
**Target**: All email subscribers

**What happens**:
1. Pulls fresh content from blog/news API
2. Generates email copy highlighting new products/updates
3. Sends via selected platform (Klaviyo, Substack, or ConvertKit)
4. Includes affiliate links in footer
5. Tracks open rate, click rate, conversions
6. Updates `automation-status.json` with metrics

**Email Sequence**:
```
Subject: [PRODUCT] — New trading strategy inside 📈

Hi [FIRST_NAME],

This week, we're sharing [PRODUCT_FEATURE]...

[PRODUCT_DESCRIPTION]

GET ACCESS → [GUMROAD_LINK]

---

Not interested? [MANAGE_PREFERENCES]
```

**Failure Handling**:
- If email platform API fails: queue email for next attempt
- If list is empty: skip campaign (don't send to nobody)
- If rate limit hit: wait 60 seconds and retry
- Alert: Slack if campaign fails to send

---

## On-Demand Triggers

### 🚀 Manual Full Launch

**Trigger**: GitHub Actions UI or API → "Run workflow"

**What happens** (sequential):
1. ✅ Publish all products to Gumroad
2. ✅ Generate and post Instagram carousel (immediately)
3. ✅ Generate and post Instagram reel (after carousel)
4. ✅ Send launch email to all subscribers
5. ✅ Pin Slack message with launch summary
6. ✅ Update dashboard with live metrics

**Expected Duration**: 5-10 minutes

**Status Updates**:
- Slack: "Starting full launch..." → "Publishing to Gumroad..." → "Posting to IG..." → "Launch complete ✅"
- Dashboard: Animated spinner → Progress bar → Success badge

**Failure Recovery**:
- If Gumroad fails: don't proceed to Instagram/email
- If Instagram fails: still send email (don't block launch)
- If email fails: mark as failed, retry in 30 mins
- If any step fails: send alert with manual recovery steps

---

### 📸 Manual Instagram Post

**Trigger**: GitHub Actions UI → "Run workflow" → "Instagram Only"

**What happens**:
1. Takes latest 3 products
2. Generates carousel + reel for each
3. Posts all to Instagram (3 carousels + 3 reels = 6 total posts)
4. Updates status to `automation-status.json`

**Expected Duration**: 3-5 minutes

---

### 📧 Manual Email Campaign

**Trigger**: GitHub Actions UI → "Run workflow" → "Email Only"

**What happens**:
1. Sends email to all active subscribers (not unsubscribed)
2. Includes latest product, news, and affiliate links
3. Tracks opens, clicks, unsubscribes
4. Updates `automation-status.json` with performance metrics

**Expected Duration**: 30-60 seconds

---

## Event-Driven Triggers

### 🎉 On New Email Signup

**Event**: New subscriber added to email list (Klaviyo webhook / Substack API)

**What happens**:
1. Triggers `email-automation` job immediately
2. Sends welcome email sequence (sequence set in email platform)
3. Logs signup to `automation-status.json`
4. Increments `email.new_signups_today` counter
5. If signup count > 100 in 24h: trigger alert to notify

**Welcome Email Flow** (auto-sequence in Klaviyo/Substack):
```
Day 0 (immediate):  Welcome email + free guide
Day 1:              First product overview
Day 3:              Case study / testimonial
Day 7:              Limited-time offer
```

**Failure Handling**:
- If email platform webhook fails: manually add to list (fallback)
- If welcome sequence doesn't send: retry at next sync (hourly)

---

### 💰 On Gumroad Sale

**Event**: Webhook from Gumroad (new sale detected)

**What happens**:
1. Triggers `gumroad-sale` job immediately
2. Updates `automation-status.json`:
   - Increments product sales count
   - Updates revenue total
   - Records timestamp of last sale
3. If sale is 5th this hour: trigger promotional post to Instagram
4. Logs transaction to `.runtime/revenue/transactions.jsonl`

**Failure Handling**:
- If webhook delivery fails: health check syncs sales data every hour
- If duplicate detected: deduplicate by Gumroad order ID

---

### 📈 On Instagram Engagement Spike

**Event**: Hourly metrics check detects >500 new engagements

**What happens**:
1. Triggers `engagement-alert` job
2. Sends Slack notification with breakdown (likes, comments, saves)
3. Reposts top comment as story (via screenshot + quote)
4. Updates `automation-status.json` with spike details

---

## Scheduled Metrics Sync

### ⏰ Hourly

**Trigger**: Cron job at top of every hour (00:00, 01:00, 02:00, etc.)

**What happens**:
1. Fetches latest metrics from all APIs:
   - Gumroad: sales, revenue, product list
   - Instagram: followers, engagement, story views
   - Email platform: subscribers, open rates, conversions
2. Calculates deltas (new followers, new sales, etc.)
3. Updates `automation-status.json` with fresh data
4. Checks API health (all services responding)
5. If any API health check fails: add warning to alerts array

**Expected Duration**: 30-45 seconds

---

### Daily

**Trigger**: Cron job at 23:59 UTC (end of day)

**What happens**:
1. Runs all hourly metrics sync
2. Calculates daily summaries:
   - Total sales today
   - Email signups today
   - IG engagement today
   - Revenue today
3. Generates daily report email
4. Sends to `ALERT_EMAIL` (stephen47@gmail.com)
5. Archives previous day's metrics

**Expected Duration**: 1 minute

---

### Weekly

**Trigger**: Cron job at Monday 00:00 UTC

**What happens**:
1. Runs all daily metrics syncs
2. Calculates weekly summary:
   - Sales per product
   - Revenue breakdown (Gumroad vs affiliate vs email)
   - IG growth (followers gained, posts, engagement)
   - Email performance (signups, conversions, open rates)
3. Generates weekly report PDF
4. Sends to `ALERT_EMAIL`
5. Posts weekly recap to Instagram story

**Expected Duration**: 2 minutes

---

## Workflow Dependencies & Concurrency

### Concurrency Rules

**No concurrent runs**:
- Only 1 full launch can run at a time
- If manual launch triggered while daily story running: cancel story, run launch
- If launch in progress: queue new triggers for after completion

**Parallel runs allowed**:
- Daily stories (3x daily) can run in parallel
- Carousels and reels (different days) never overlap
- Metrics sync never blocks other jobs

---

## Error Handling & Retries

### Retry Policy (Global)

| Trigger | Max Retries | Delay | Action on Final Failure |
|---------|------------|-------|------------------------|
| Instagram Post | 3 | 5 min | Slack alert |
| Gumroad Upload | 5 | 10 min | Slack alert + manual email |
| Email Send | 3 | 30 min | Slack alert + manual send |
| Image Generation | 2 | 5 min | Use fallback template |
| Metrics Sync | 1 | 1 hour | Skip metrics, keep running |

### Alert Channels

1. **Slack** (`#automation-alerts`): Immediate alerts for all failures
2. **Email** (stephen47@gmail.com): Daily digest of warnings/errors
3. **GitHub Issues**: Create issue if >3 consecutive failures on same trigger

---

## Disabling / Pausing Automation

### Temporary Pause (24 hours)

```bash
# Pause all scheduled jobs
AUTOMATION_ENABLED=false npm run sync:automation-config

# Resume after 24h or manually:
AUTOMATION_ENABLED=true npm run sync:automation-config
```

### Disable Specific Trigger

Edit GitHub Actions workflow file:
```yaml
jobs:
  daily-stories:
    if: false  # Disables this job
```

### Full Disable (Emergency)

Delete all scheduled workflows in GitHub Actions:
```bash
gh workflow disable daily-stories.yml
gh workflow disable weekly-carousels.yml
gh workflow disable email-automation.yml
```

Re-enable:
```bash
gh workflow enable daily-stories.yml
```

---

## Testing Automation (Dry-Run Mode)

### Local Testing (No Real Posts)

```bash
# Enable dry-run (simulates automation without posting)
AUTOMATION_DRY_RUN=true npm run verify:automation

# This will:
# - Generate images but not upload to IG
# - Generate emails but not send
# - Upload products to Gumroad TEST mode (not live)
# - Log all actions to console
```

### GitHub Actions Testing

1. Go to **Actions** → Workflow name
2. Click **Run workflow** → expand options
3. Check **DRY_RUN** checkbox
4. Click **Run workflow**

---

## Monitoring & Observability

### Real-Time Monitoring

```bash
# Watch workflow in real-time:
gh workflow run daily-stories.yml --ref main --watch

# View logs after completion:
gh workflow view daily-stories.yml --log
```

### Dashboard Auto-Refresh

Open `automation-dashboard.html` in browser → auto-refreshes every 30 seconds with live metrics

### Logs Location

```
.runtime/automation/
├── daily-stories.log
├── weekly-carousels.log
├── email-automation.log
├── gumroad-sync.log
└── metrics-sync.log
```

---

## Summary Table

| Trigger | Frequency | Time | Duration | Status Sink |
|---------|-----------|------|----------|-----------|
| Stories | Daily | 3x (07/14/20 UTC) | 30 sec | automation-status.json |
| Carousels | Weekly | Tue/Thu/Sat 09 UTC | 1 min | automation-status.json |
| Reels | Weekly | Mon/Wed/Fri 10 UTC | 2 min | automation-status.json |
| Email | Weekly | Mon 08 UTC | 1 min | automation-status.json |
| Metrics Sync | Hourly | Every hour | 45 sec | automation-status.json |
| Full Launch | On-demand | Manual trigger | 5-10 min | Slack + dashboard |


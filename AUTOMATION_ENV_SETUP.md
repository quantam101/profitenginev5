# Complete Automation Environment Setup

**Step-by-step guide to configure all services for end-to-end automation**

---

## Quick Start (5 minutes)

```bash
# 1. Set up GitHub Secrets
gh secret set GUMROAD_API_TOKEN --body "your-token"
gh secret set OPENAI_API_KEY --body "your-key"
gh secret set IG_USER_ID --body "your-id"
gh secret set FB_PAGE_ACCESS_TOKEN --body "your-token"
gh secret set REPLICATE_API_TOKEN --body "your-token"
gh secret set BEEHIIV_API_KEY --body "your-key"

# 2. Create content files
touch GUMROAD_PRODUCT_EBOOK.md
touch INSTAGRAM_CAROUSEL_DESIGNS.md
touch PREMIUM_ONBOARDING_SEQUENCE.md

# 3. Trigger automation
gh workflow run automation.yml

# 4. Monitor
gh run list --workflow=automation.yml --limit=1
```

---

## Detailed Setup by Service

### 1. Gumroad Setup

#### Get API Token
1. Go to https://gumroad.com/settings/api
2. Under "API Keys," click "Create API Key"
3. Name it "ProfitEngine Automation"
4. Copy the token

#### Add to GitHub
```bash
gh secret set GUMROAD_API_TOKEN --body "gumroad_api_xxx"
gh secret set GUMROAD_CREATOR_ID --body "alreadyhere"
```

#### Create Product Files
Create `GUMROAD_PRODUCT_MASTER_BLUEPRINT.md`:
```yaml
---
title: "Master Blueprint: Trading System Design"
description: "Complete guide to building profitable trading systems"
price: 47.00
category: "book"
product_type: "ebook"
tags: [trading, systemdesign, automation, python]
image_prompt: "Professional eBook cover: Trading System Blueprint, modern design, technical aesthetic"
---

# Master Blueprint: Complete Trading System

## Part 1: Foundation
- Market mechanics
- Data sources
- Backtesting principles

## Part 2: Strategy Development
- Signal generation
- Risk management
- Portfolio construction

[Full content here...]
```

---

### 2. Image Generation (for Gumroad & Carousels)

#### Option A: OpenAI DALL-E (Recommended)

1. **Create OpenAI Account**
   - Visit https://platform.openai.com/
   - Sign up or log in

2. **Get API Key**
   - Go to https://platform.openai.com/api/keys
   - Click "Create new secret key"
   - Copy key (save securely)

3. **Add Billing**
   - Go to Settings → Billing
   - Add payment method
   - Set usage limit (~$1-5/month for testing)

4. **Add to GitHub**
   ```bash
   gh secret set OPENAI_API_KEY --body "sk-proj-xxx"
   gh secret set IMAGE_GENERATION_API --body "dalle"
   ```

5. **Test**
   ```bash
   curl https://api.openai.com/v1/images/generations \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"test","n":1,"size":"1024x1024"}'
   ```

#### Option B: Unsplash (Free)

1. Go to https://unsplash.com/oauth/applications
2. Create application
3. Copy Access Key
4. Add to GitHub:
   ```bash
   gh secret set UNSPLASH_API_KEY --body "xxx"
   gh secret set IMAGE_GENERATION_API --body "unsplash"
   ```

#### Option C: Pexels (Free)

1. Go to https://www.pexels.com/api/
2. Create account
3. Copy API Key
4. Add to GitHub:
   ```bash
   gh secret set PEXELS_API_KEY --body "xxx"
   gh secret set IMAGE_GENERATION_API --body "pexels"
   ```

#### Option D: Replicate (Stable Diffusion)

1. Go to https://replicate.com/
2. Sign in or create account
3. Go to Account → API tokens
4. Create token
5. Add to GitHub:
   ```bash
   gh secret set REPLICATE_API_TOKEN --body "xxx"
   gh secret set IMAGE_GENERATION_API --body "replicate"
   ```

---

### 3. Instagram / Meta Setup

#### Step 1: Create Meta Business Account

1. Go to https://business.facebook.com/
2. Click "Create Account"
3. Follow setup wizard
4. Add business name: "Already Here LLC"

#### Step 2: Connect Instagram Account

1. In Meta Business Suite, go to Accounts → Instagram accounts
2. Click "Add account"
3. Connect your Instagram business account
4. Verify account ownership

#### Step 3: Get Access Token

```bash
# Via Facebook Graph API

# 1. Get your Page ID (Instagram connected to Page)
curl https://graph.facebook.com/me/accounts \
  -H "Authorization: Bearer TEMP_TOKEN"

# 2. Generate long-lived access token
curl -X POST https://graph.api.com/v18.0/oauth/access_token \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "grant_type=client_credentials"

# 3. Get Instagram User ID
curl https://graph.instagram.com/ig_hashtag_search \
  -d "user_id=YOUR_IG_USER_ID" \
  -d "fields=id,name" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

#### Step 4: Add to GitHub

```bash
# Find your values at https://developers.facebook.com/apps/YOUR_APP_ID/

gh secret set IG_USER_ID --body "your-ig-business-user-id"
gh secret set FB_PAGE_ACCESS_TOKEN --body "long-lived-access-token"
```

#### Step 5: Test Connection

```bash
curl https://graph.instagram.com/me \
  -H "Authorization: Bearer $FB_PAGE_ACCESS_TOKEN"

# Should return:
# {"id":"your-ig-user-id","username":"your-username"}
```

---

### 4. Video Generation (for Reels & Stories)

#### Option A: Replicate (Recommended for flexibility)

Already set up above for image generation. Same token works for video.

Add to GitHub:
```bash
gh secret set VIDEO_GENERATION_API --body "replicate"
```

#### Option B: Synthesia.io (Avatar Videos)

1. Go to https://www.synthesia.io/
2. Sign up for account
3. Go to Settings → API Access
4. Create API token
5. Add to GitHub:
   ```bash
   gh secret set SYNTHESIA_API_KEY --body "xxx"
   gh secret set VIDEO_GENERATION_API --body "synthesia"
   ```

#### Option C: D-ID (Talking Avatar)

1. Go to https://www.d-id.com/
2. Create account
3. Go to Dashboard → API Key
4. Copy key
5. Add to GitHub:
   ```bash
   gh secret set DID_API_KEY --body "xxx"
   gh secret set VIDEO_GENERATION_API --body "d-id"
   ```

#### Voice Generation: ElevenLabs (Required)

1. Go to https://elevenlabs.io/
2. Sign up for account
3. Go to API Key (bottom left)
4. Copy API key
5. Add to GitHub:
   ```bash
   gh secret set ELEVENLABS_API_KEY --body "sk_xxx"
   ```

Test:
```bash
curl https://api.elevenlabs.io/v1/text-to-speech/preset \
  -X POST \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -d '{"text":"Hello world"}'
```

---

### 5. Email Automation

#### Option A: Beehiiv (Recommended)

1. Go to https://www.beehiiv.com/
2. Create account or log in
3. Create publication
4. Go to Settings → API & Integrations
5. Under API Keys, click "Create API key"
6. Copy key
7. Find your Publication ID in Publication Settings
8. Add to GitHub:
   ```bash
   gh secret set BEEHIIV_API_KEY --body "xxx"
   gh secret set BEEHIIV_PUBLICATION_ID --body "your-pub-id"
   gh secret set EMAIL_SERVICE --body "beehiiv"
   ```

Test:
```bash
curl https://api.beehiiv.com/v1/publications/subscriptions \
  -X POST \
  -H "Authorization: Bearer $BEEHIIV_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","reactivate_existing":true}'
```

#### Option B: Klaviyo

1. Go to https://www.klaviyo.com/
2. Create account or log in
3. Go to Account → Settings → API Keys
4. Create new Private API Key
5. Add to GitHub:
   ```bash
   gh secret set KLAVIYO_API_KEY --body "pk_xxx"
   gh secret set EMAIL_SERVICE --body "klaviyo"
   ```

#### Option C: ConvertKit

1. Go to https://convertkit.com/
2. Create account or log in
3. Go to Account → Integrations → API
4. Copy API Secret
5. Add to GitHub:
   ```bash
   gh secret set CONVERTKIT_API_KEY --body "xxx"
   gh secret set EMAIL_SERVICE --body "convertkit"
   ```

#### Option D: Substack

1. Go to https://substack.com/
2. Create publication or log in
3. Go to Settings → Import & Export → API
4. Create API token
5. Add to GitHub:
   ```bash
   gh secret set SUBSTACK_API_TOKEN --body "xxx"
   gh secret set EMAIL_SERVICE --body "substack"
   ```

---

## Create Content Files

### 1. Gumroad Products

Create `GUMROAD_PRODUCT_EBOOK.md`:

```yaml
---
title: "Profitable Trading Systems: The Complete Blueprint"
description: "Step-by-step guide to building and testing trading strategies that actually work"
price: 49.99
category: "book"
product_type: "ebook"
tags: [trading, systems, backtesting, python, risk-management]
image_prompt: "Professional eBook cover for trading systems guide, modern tech aesthetic, gold and dark blue colors"
---

## Introduction

Trading systems are the bridge between market opportunity and consistent profits...

[Full eBook content]
```

### 2. Instagram Carousel

Create `INSTAGRAM_CAROUSEL_DESIGNS.md`:

```markdown
# Why Retail Traders Fail (And How to Fix It)

## Description
7-slide carousel breaking down the mistakes retail traders make and ProfitEngine's solutions

## Hashtags
#trading #forextrading #cryptotrading #stocktrading #algorithmitrading #profitengine

## CTA
Learn how to build profitable trading systems

### Slide 1
Title: The Problem
Description: 90% of retail traders lose money. Here's why.
Image Prompt: Modern graphic showing down arrow, frustrated trader, market chaos
CTA: Keep Reading →

### Slide 2
Title: Mistake #1: Wrong Entry Signals
Description: Most traders use signals that don't work in live markets
Image Prompt: Chart with multiple failed entry signals highlighted in red

### Slide 3
Title: Mistake #2: No Risk Management
Description: Trading size is everything. Most traders don't know this.
Image Prompt: Money management chart showing position sizing formula

### Slide 4
Title: Mistake #3: Backtesting Lies
Description: Your backtest isn't real. Here's what's missing.
Image Prompt: Computer screen showing backtest vs actual trading results comparison

### Slide 5
Title: Mistake #4: Emotion Trading
Description: When markets move, emotions take over. Systems don't have emotions.
Image Prompt: Brain activity visualization, trading dashboard with stable lines

### Slide 6
Title: Mistake #5: No Diversification
Description: All-in on one trade = all-in on one mistake
Image Prompt: Portfolio diversification pie chart, multiple asset classes

### Slide 7
Title: The Solution
Description: ProfitEngine eliminates all 5 mistakes automatically
Image Prompt: Green uptrend arrow, professional trading dashboard, success theme
CTA: Build Your System →
```

### 3. Email Sequences

Create `PREMIUM_ONBOARDING_SEQUENCE.md`:

```markdown
## Sequence: Premium Welcome

**Description**: Welcome new premium members and guide them through first strategy setup

**Trigger**: signup

### Email 1: Welcome to Premium
**Subject**: Welcome to ProfitEngine Premium
**Send After**: 0 hours
**CTA**: Start Your First Strategy
**CTA Link**: https://profitengine.alreadyherellc.com/get-started

Dear [Name],

Welcome to ProfitEngine Premium!

You now have access to everything you need to build profitable trading systems...

[Full email content]

---

### Email 2: Your First Strategy (Guided)
**Subject**: Let's Build Your First Trading System
**Send After**: 24 hours
**CTA**: Open Strategy Builder
**CTA Link**: https://profitengine.alreadyherellc.com/strategy-builder

We're going to walk you through building your first profitable strategy...

[Full email content]

---

### Email 3: Backtesting Like a Pro
**Subject**: The Backtesting Framework That Works
**Send After**: 72 hours
**CTA**: Access Full Framework
**CTA Link**: https://profitengine.alreadyherellc.com/backtesting

Most traders backtest wrong. Here's the right way...

[Full email content]

---

### Email 4: Your Results Week 1
**Subject**: [Name], Here's What's Possible
**Send After**: 168 hours
**CTA**: View Your Dashboard
**CTA Link**: https://profitengine.alreadyherellc.com/dashboard

Looking at your first week of trading...

[Full email content]

---

### Email 5: Premium Exclusive: Correlation Systems
**Subject**: Exclusive: The Correlation Strategy That Works
**Send After**: 336 hours
**CTA**: Build Correlation System
**CTA Link**: https://profitengine.alreadyherellc.com/correlation

This strategy is exclusive to premium members...

[Full email content]
```

---

## Test All Integrations

### Test Gumroad
```bash
# Verify API works
curl -X GET https://api.gumroad.com/v2/products \
  -d "access_token=$GUMROAD_API_TOKEN"

# Should list your products
```

### Test Instagram
```bash
# Verify Graph API access
curl https://graph.instagram.com/me/media \
  -H "Authorization: Bearer $FB_PAGE_ACCESS_TOKEN"

# Should return your recent posts
```

### Test Email Service
```bash
# For Beehiiv
curl https://api.beehiiv.com/v1/publications \
  -H "Authorization: Bearer $BEEHIIV_API_KEY"

# For Klaviyo
curl https://a.klaviyo.com/api/v1/flows \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_API_KEY"
```

---

## Verify GitHub Actions Setup

```bash
# List secrets (won't show values)
gh secret list

# Expected output:
# GUMROAD_API_TOKEN
# OPENAI_API_KEY
# IG_USER_ID
# FB_PAGE_ACCESS_TOKEN
# REPLICATE_API_TOKEN
# ELEVENLABS_API_KEY
# BEEHIIV_API_KEY
# BEEHIIV_PUBLICATION_ID
# EMAIL_SERVICE
# IMAGE_GENERATION_API
# VIDEO_GENERATION_API

# Check workflow file exists
ls -la .github/workflows/automation.yml

# Validate YAML
npm run validate:yaml
```

---

## Run First Automation

```bash
# Manual trigger via CLI
gh workflow run automation.yml --ref main

# Or via GitHub UI
# 1. Go to Actions → Full Automation Launch
# 2. Click "Run workflow"
# 3. Choose parallel=true
# 4. Submit

# Monitor in real-time
gh run list --workflow=automation.yml --limit=5

# View detailed output
gh run view <RUN_ID> --log
```

---

## Budget Estimate (Monthly)

| Service | Cost | Notes |
|---------|------|-------|
| DALL-E Image Gen | $0-5 | ~$0.016/image, 300 images/month |
| Replicate | $0-10 | ~$0.01-0.05/video, 50 videos/month |
| ElevenLabs | $0-5 | ~$1/1M chars, 2M chars/month |
| Beehiiv | $0-99 | Free tier up to 10k subscribers |
| Instagram Meta | $0 | Free Business Suite |
| GitHub Actions | $0 | Free tier includes automations |
| **TOTAL** | **$0-30** | Well within budget |

---

## Maintenance Checklist

**Weekly:**
- [ ] Check automation logs: `.runtime/automation/launch-status.jsonl`
- [ ] Verify no failed tasks
- [ ] Monitor API usage (stay within free tier)

**Monthly:**
- [ ] Review GitHub Actions costs
- [ ] Test manual trigger
- [ ] Validate all API keys still work

**Quarterly:**
- [ ] Rotate API tokens for security
- [ ] Archive old automation logs
- [ ] Update content files for new products

---

## Troubleshooting

### "API key not configured"
```bash
# Check secret is set
gh secret list | grep YOUR_KEY

# If not found, add it
gh secret set YOUR_KEY --body "value"
```

### "File not found"
```bash
# Create missing content files
touch GUMROAD_PRODUCT_*.md
touch INSTAGRAM_CAROUSEL_DESIGNS.md
touch PREMIUM_ONBOARDING_SEQUENCE.md

# Verify they exist
ls -la GUMROAD_PRODUCT_*.md
```

### "Rate limit exceeded"
```bash
# Switch to serial execution
# Edit .github/workflows/automation.yml
# Change: AUTOMATION_PARALLEL: false

# Or use fewer tasks
# Add to workflow_dispatch: skipTasks: ["carousel", "reel"]
```

### "Invalid token"
```bash
# Regenerate the token from source service
# Update GitHub secret
gh secret set EXPIRED_TOKEN --body "new-token"

# Verify update
gh secret list
```

---

**Setup Time:** 30-45 minutes  
**Difficulty:** Intermediate  
**Support:** See AUTOMATION_SETUP.md for full documentation

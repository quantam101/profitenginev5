# ProfitEngine v5 — Complete Automation Setup Guide

## Table of Contents
1. [Overview](#overview)
2. [API Key Setup (Step-by-Step)](#api-key-setup)
3. [GitHub Secrets Configuration](#github-secrets-configuration)
4. [Triggering Automation](#triggering-automation)
5. [Monitoring Status](#monitoring-status)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks through setting up fully automated product launches across:
- **Gumroad**: Product publishing & sales tracking
- **Instagram**: Daily stories, weekly carousels/reels
- **Email**: Automated welcome sequences
- **GitHub Actions**: Scheduled & on-demand automation

**Expected timeline**: 30 minutes to set all keys + 5 minutes to verify

---

## API Key Setup

### 1. GUMROAD API KEY

**What it does**: Automates product uploads, tracks sales in real-time

**Steps**:
1. Log in to https://app.gumroad.com
2. Click your profile icon → **Settings** → **Advanced**
3. Scroll to **API** section → copy your **API Token** (starts with `gumroad_pat_`)
4. Paste into `.env.automation`:
   ```
   GUMROAD_API_KEY=gumroad_pat_xxxxx
   ```

**Verify connection**:
```bash
curl -H "Authorization: Bearer YOUR_KEY" \
  https://api.gumroad.com/v2/user/products
```
Should return a JSON list of your products (not a 403/401 error).

---

### 2. INSTAGRAM ACCESS TOKEN & BUSINESS ACCOUNT ID

**What it does**: Posts stories, carousels, reels; tracks engagement metrics

**Setup (Instagram Graph API)**:

1. **Create a Meta App**:
   - Go to https://developers.facebook.com/apps
   - Click **Create App** → Select **Business** type
   - Fill in app name (e.g., "ProfitEngine Automation")

2. **Add Instagram Graph API**:
   - In your app → **Products** → Click **+** → Add **Instagram Graph API**

3. **Set up OAuth Redirect**:
   - Settings → Basic → Copy your **App ID** and **App Secret**
   - Settings → Basic → Add OAuth Redirect URI:
     ```
     https://profitengine-tau.vercel.app/api/instagram/callback
     ```

4. **Get Instagram Business Account ID**:
   - Log in to https://business.facebook.com
   - Click **Settings** → **Accounts** → **Instagram Accounts**
   - Copy the **Account ID** (e.g., `17841400963180`)

5. **Generate Access Token**:
   - Go to https://developers.facebook.com/tools/explorer
   - Select your app → select **Instagram Graph API**
   - Request permissions: `instagram_basic`, `instagram_content_publish`
   - Copy the **User Access Token** (starts with `IGSHO...` or `IGALAAx...`)

6. **Store in `.env.automation`**:
   ```
   INSTAGRAM_ACCESS_TOKEN=IGALAAx...
   INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400963180
   ```

**Verify connection**:
```bash
curl "https://graph.instagram.com/me?fields=id,username,account_type&access_token=YOUR_TOKEN"
```
Should return your account info (not an error).

---

### 3. IMAGE GENERATION: DALL-E or Replicate

**Option A: OpenAI DALL-E 3** (paid, $0.04–0.20 per image)

1. Go to https://platform.openai.com/account/billing/overview
2. **Set billing method** and add a valid credit card
3. **API keys** → Create new secret key
4. Store in `.env.automation`:
   ```
   DALLE_API_KEY=sk-...
   IMAGE_GENERATION_PROVIDER=dalle
   ```

**Option B: Replicate** (free tier + pay-as-you-go, ~$0.01 per image)

1. Sign up at https://replicate.com
2. Go to **Account** → **API tokens**
3. Copy your token
4. Store in `.env.automation`:
   ```
   REPLICATE_API_TOKEN=r8_...
   IMAGE_GENERATION_PROVIDER=replicate
   ```

**Recommendation**: Start with Replicate (free, fast). Switch to DALL-E if you need higher quality.

**Verify connection**:
```bash
# For Replicate:
curl https://api.replicate.com/v1/models \
  -H "Authorization: Token YOUR_TOKEN"

# For DALL-E:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

---

### 4. VIDEO GENERATION: Synthesia API

**What it does**: Auto-generates talking-head product demo videos

1. Sign up at https://synthesia.io (free trial available)
2. Dashboard → **Integrations** → **API**
3. Generate API key and copy
4. Choose an avatar from the dashboard
5. Store in `.env.automation`:
   ```
   SYNTHESIA_API_KEY=your-key-here
   SYNTHESIA_AVATAR_ID=avatar_id_from_dashboard
   ```

**Verify connection**:
```bash
curl https://api.synthesia.io/v1/videos \
  -H "Authorization: Bearer YOUR_KEY"
```

---

### 5. VOICEOVER: Eleven Labs API

**What it does**: Generates professional voice narration for product demos

1. Sign up at https://elevenlabs.io (free 10k characters/month)
2. Account → **API Key** → Copy your key
3. Explore different voice IDs (Dashboard → **Voices**)
4. Store in `.env.automation`:
   ```
   ELEVEN_LABS_API_KEY=sk_...
   ELEVEN_LABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
   ```

**Available voice IDs** (female):
- `21m00Tcm4TlvDq8ikWAM` — Rachel (warm, professional)
- `EXAVITQu4vr4xnSDxMaL` — Bella (energetic)
- `nPczCjzI2devNricPZAf` — Lily (clear, confident)

---

### 6. EMAIL PLATFORM: Choose One

#### Option A: **Klaviyo** (recommended: best for conversions + SMS)

1. Log in to https://www.klaviyo.com
2. **Account** → **Account settings** → **Integrations** → **API Keys**
3. Generate a new **Private API Key**
4. Create a **List** (or use default):
   - Marketing → **Lists** → Create new list
   - Copy the **List ID**
5. Store in `.env.automation`:
   ```
   EMAIL_PLATFORM=klaviyo
   KLAVIYO_API_KEY=pk_...
   KLAVIYO_LIST_ID=list_...
   ```

#### Option B: **Substack** (simple email newsletter)

1. Log in to https://substack.com/dashboard
2. **Settings** → **Account** → **Integrations** → **APIs**
3. Generate API key
4. Store in `.env.automation`:
   ```
   EMAIL_PLATFORM=substack
   SUBSTACK_API_KEY=key_...
   SUBSTACK_PUBLICATION_ID=pub_...
   ```

#### Option C: **ConvertKit** (email + memberships)

1. Log in to https://convertkit.com/account
2. **Integrations** → **API** → Generate token
3. Find your **Form ID**:
   - Dashboard → Forms → Find form → Copy the ID from URL
4. Store in `.env.automation`:
   ```
   EMAIL_PLATFORM=convertkit
   CONVERTKIT_API_KEY=key_...
   CONVERTKIT_FORM_ID=1234567
   ```

---

### 7. GITHUB ACTIONS TOKEN

**What it does**: Allows automation to trigger other workflows (e.g., sync metrics)

1. Log in to https://github.com/settings/tokens
2. Click **Generate new token** → **Tokens (classic)**
3. Set **Name**: `ProfitEngine Automation`
4. Select scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (actions)
   - ✅ `read:user` (read account info)
5. Copy the token
6. Store in `.env.automation`:
   ```
   GITHUB_ACTIONS_TOKEN=ghp_...
   ```

**Verify**:
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user
```
Should return your GitHub profile (not a 401 error).

---

### 8. SLACK WEBHOOK

**What it does**: Sends automation status updates to Slack (success/failure alerts)

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. Name: `ProfitEngine Automation`, Workspace: select yours
4. Left sidebar → **Incoming Webhooks** → toggle **On**
5. Click **Add New Webhook to Workspace**
6. Select channel (e.g., `#automation-alerts`)
7. Copy the **Webhook URL**
8. Store in `.env.automation`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   SLACK_NOTIFICATION_CHANNEL=#automation-alerts
   ```

**Verify**:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL
```
Should appear in your Slack channel.

---

## GitHub Secrets Configuration

Once you have all API keys, add them to GitHub Secrets (used by CI/CD workflows).

**Steps**:
1. Go to https://github.com/quantam101/profitenginev5/settings/secrets/actions
2. Click **New repository secret**
3. Add each key:

| Secret Name | Value |
|---|---|
| `GUMROAD_API_KEY` | Your Gumroad API token |
| `INSTAGRAM_ACCESS_TOKEN` | Your Instagram token |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Your IG account ID |
| `DALLE_API_KEY` | OpenAI key (if using DALL-E) |
| `REPLICATE_API_TOKEN` | Replicate key (if using Replicate) |
| `SYNTHESIA_API_KEY` | Synthesia API key |
| `ELEVEN_LABS_API_KEY` | Eleven Labs API key |
| `KLAVIYO_API_KEY` | Klaviyo key (if using Klaviyo) |
| `SUBSTACK_API_KEY` | Substack key (if using Substack) |
| `CONVERTKIT_API_KEY` | ConvertKit key (if using ConvertKit) |
| `GITHUB_ACTIONS_TOKEN` | Your GitHub PAT |
| `SLACK_WEBHOOK_URL` | Your Slack webhook |

---

## Triggering Automation

### Method 1: Manual Trigger via GitHub UI

1. Go to **Actions** → **Automation Launch**
2. Click **Run workflow**
3. Select options:
   - **Publish to Gumroad**: ✅ (publish products)
   - **Post to Instagram**: ✅ (stories + carousels)
   - **Send Email**: ✅ (email sequences)
4. Click **Run workflow**

**Status**: Watch the workflow run in real-time. Check Slack for notifications.

### Method 2: Scheduled Automation (Already Configured)

The system automatically:
- **Daily** (3 times): Posts Instagram stories at 07:00, 14:00, 20:00 UTC
- **Weekly** (Tue/Thu/Sat): Posts carousels at 09:00 UTC
- **Weekly** (Mon/Wed/Fri): Posts reels at 10:00 UTC
- **Weekly** (Monday 08:00 UTC): Full product launch (Gumroad + email)

### Method 3: CLI Trigger (Local)

```bash
# Verify all API keys are valid
npm run verify:automation

# Run full launch (local testing)
AUTOMATION_DRY_RUN=true npm run launch:automation

# Monitor automation status
npm run automation:status

# View dashboard
open http://localhost:8765
```

---

## Monitoring Status

### Real-Time Dashboard

Open the automation dashboard (updates every 30 seconds):

```bash
npm run automation:dashboard
# or open: http://localhost:8765
```

**Shows**:
- ✅ Last successful product upload (Gumroad)
- ✅ Instagram posts scheduled/published
- ✅ Email signups (last 24h)
- ✅ Revenue metrics (total sales, conversions)
- ✅ Engagement (followers, likes, comments)

### Slack Notifications

Automation sends status to Slack:
- ✅ `[SUCCESS]` — Product uploaded, post scheduled
- ❌ `[FAILED]` — API error, retry in 5 mins
- ⚠️ `[PENDING]` — Awaiting API response

### JSON Status File

Auto-generated status log:
```bash
cat automation-status.json
```

**Output**:
```json
{
  "last_run": "2026-06-20T15:30:00Z",
  "products": {
    "trading-course": {
      "gumroad_id": "abc123",
      "published": true,
      "sales": 12,
      "revenue_usd": 299.88,
      "last_update": "2026-06-20T15:30:00Z"
    }
  },
  "instagram": {
    "followers": 1234,
    "posts_this_week": 7,
    "total_engagement": 456,
    "last_story": "2026-06-20T14:00:00Z"
  },
  "email": {
    "signups_today": 34,
    "open_rate": "28%",
    "click_rate": "4.2%"
  },
  "status": "healthy"
}
```

---

## Troubleshooting

### Problem: "Invalid API Key" Error

**Solution**: Verify the key is correct:
```bash
# For Gumroad:
curl -H "Authorization: Bearer $GUMROAD_API_KEY" \
  https://api.gumroad.com/v2/user/products

# For Instagram:
curl "https://graph.instagram.com/me?access_token=$INSTAGRAM_ACCESS_TOKEN"
```

If the request fails, regenerate the key in the service dashboard.

### Problem: Instagram Token Expires

Instagram tokens are short-lived (1 hour). The automation refreshes them automatically.

If you see `401 Unauthorized` errors:
1. Go to Meta Business Manager
2. Regenerate a new **Long-Lived Token** (valid 60 days)
3. Update GitHub Secrets with the new token
4. Re-run the workflow

### Problem: Gumroad Product Not Found

**Solution**: Verify the product ID:
```bash
# List all products:
curl -H "Authorization: Bearer $GUMROAD_API_KEY" \
  https://api.gumroad.com/v2/user/products

# Find the product ID from the response
```

Update `PRODUCTS_TO_AUTOMATE` in `.env.automation` with the correct ID.

### Problem: Email Not Sending

**Solution**: Check list/form configuration:
- **Klaviyo**: Verify the list exists and is active
- **Substack**: Verify the publication ID is correct
- **ConvertKit**: Verify the form exists and allows API signups

### Problem: Workflow Hangs or Times Out

**Solution**:
1. Check if external APIs are down:
   - Gumroad status: https://status.gumroad.com
   - Instagram: https://status.fb.com
   - Stripe: https://status.stripe.com

2. Increase timeout in GitHub Actions workflow:
   ```yaml
   timeout-minutes: 10
   ```

3. Check API rate limits:
   - Gumroad: 60 requests/minute
   - Instagram: 200 requests/min per token
   - Stripe: 100 requests/sec

### Problem: Slack Notifications Not Appearing

**Solution**:
1. Verify webhook URL is correct
2. Check Slack app permissions:
   - Go to https://api.slack.com/apps → Your App → Permissions
   - Ensure `chat:write` is enabled
3. Test webhook manually:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test"}' \
     $SLACK_WEBHOOK_URL
   ```

---

## Next Steps

1. ✅ Set up all API keys (8 total)
2. ✅ Add secrets to GitHub
3. ✅ Run verification: `npm run verify:automation`
4. ✅ Test manual trigger (one workflow run)
5. ✅ Monitor dashboard and Slack for 24 hours
6. ✅ Adjust schedules as needed
7. ✅ Set up backup email notifications (optional)

**Questions?** Check `automation-status.json` or recent workflow runs in GitHub Actions.

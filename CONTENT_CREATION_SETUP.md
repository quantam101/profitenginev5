# Content Creation & Publishing Setup

**Status**: REQUIRES GITHUB SECRETS CONFIGURATION  
**Priority**: CRITICAL — Content pipeline must be operational

---

## Current State

✅ **Scripts Exist**:
- `scripts/publish_article_resilient.py` — Main publisher (22 KB, working)
- `scripts/publish_article.py` — Fallback publisher (38 KB, working)
- `scripts/content_factory_run.py` — Content generation
- `.github/workflows/daily-content.yml` — Scheduled publishing workflow

✅ **Deterministic Fallback**:
- If all LLM providers fail, generates operational articles without API keys
- Ensures content is always published, even on provider outages

❌ **BLOCKING ISSUE**:
- Daily-content workflow requires GitHub Secrets to be configured
- Secrets exist in local `.env` but NOT in GitHub Actions repository secrets
- Without these secrets, the workflow validation fails and publishing doesn't happen

---

## Required GitHub Secrets (CRITICAL)

These MUST be configured in GitHub to enable daily content publishing:

### Core Content Generation (Required)
- `GROQ_API_KEY` — For content generation
- `GEMINI_API_KEY` — Fallback content generation
- `HF_TOKEN` — HuggingFace fallback
- `CONTENT_REPO_TOKEN` — Personal access token for pushing to `quantam101/content` repo

### Content Metadata
- `AMAZON_PARTNER_TAG` — Amazon Associates tag for affiliate links
- `AFFILIATE_LINKS` — JSON map of 50+ affiliate networks

### Social Publishing (Optional — content still publishes without these)
- `DEVTO_API_KEY` — Dev.to publishing
- `HASHNODE_API_KEY` — Hashnode publishing
- `HASHNODE_PUB_ID` — Hashnode publication ID
- `MEDIUM_API_KEY` — Medium publishing
- `MEDIUM_AUTHOR_ID` — Medium author ID
- `TELEGRAM_BOT_TOKEN` — Telegram alerts
- `TELEGRAM_CHAT_ID` — Telegram recipient
- Twitter, LinkedIn, Reddit, TikTok, Facebook, Instagram secrets (optional)

---

## How Content Publishing Works

### 1. Workflow Trigger
**File**: `.github/workflows/daily-content.yml`

**Scheduled Execution**:
- 07:05 UTC daily (morning publish)
- 15:05 UTC daily (afternoon publish)
- Manual trigger available via workflow_dispatch

**Process**:
1. Validate job checks if required secrets are present
2. If validation passes, publish job runs
3. Publisher generates article via Groq → Gemini → HuggingFace → Deterministic fallback
4. Publishes to `quantam101/content` GitHub Pages
5. Publishes to optional social platforms
6. Verifies publication succeeded

### 2. Publisher Chain
**Provider Order** (tries each until success):
1. **Groq** (fastest, free tier) ← Primary
2. **Google Gemini** ← Fallback
3. **HuggingFace** ← Fallback
4. **Deterministic Generator** ← Always works (operational how-to articles)

**Affiliate Injection**:
- Automatically inserts 50+ affiliate links
- Amazon Associates tag auto-injected
- FTC disclosure auto-included

### 3. GitHub Pages Publication
**Target**: `https://quantam101.github.io/content/`

**Files Created**:
- `posts/YYYY-MM-DD-slug-title.md` — Published article
- Auto-indexed on GitHub Pages

**Current Status**:
- 58 posts live
- Latest: 2026-06-09
- ⚠️ No posts since June 9 (secrets not configured in GitHub)

---

## Setup Instructions

### Step 1: Gather Secrets from Local `.env`

The values are already in your `.env` file:

```bash
# From your .env file:
GROQ_API_KEY=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
GEMINI_API_KEY=AIzaSyCVAAmQUhhxCqtIm88w6U6u2cbzzZYn8oc
HF_TOKEN=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
CONTENT_REPO_TOKEN=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
AMAZON_PARTNER_TAG=alreadyhere-20
```

### Step 2: Add Secrets to GitHub

Go to: **github.com → quantam101/profitenginev5 → Settings → Secrets and variables → Actions**

Create NEW repository secrets (these are REQUIRED):

1. **Name**: `GROQ_API_KEY`
   - **Value**: (from .env above)

2. **Name**: `GEMINI_API_KEY`
   - **Value**: (from .env above)

3. **Name**: `HF_TOKEN`
   - **Value**: (from .env above)

4. **Name**: `CONTENT_REPO_TOKEN`
   - **Value**: (from .env above)
   - This allows publishing to `quantam101/content` repo

5. **Name**: `AMAZON_PARTNER_TAG`
   - **Value**: `alreadyhere-20`

6. **Name**: `AFFILIATE_LINKS`
   - **Value**: Full JSON from your .env (the 50+ partner links)

### Step 3: Optional — Add Social Platform Secrets

Add these if you want content distributed to social platforms:

- `DEVTO_API_KEY` (Dev.to)
- `HASHNODE_API_KEY` (Hashnode)
- `HASHNODE_PUB_ID` (Hashnode)
- `MEDIUM_API_KEY` (Medium)
- `MEDIUM_AUTHOR_ID` (Medium)

### Step 4: Verify Secrets Are Configured

Go to **Settings → Secrets and variables → Actions** and verify:
- ✅ GROQ_API_KEY appears (masked value shown)
- ✅ GEMINI_API_KEY appears (masked value shown)
- ✅ HF_TOKEN appears (masked value shown)
- ✅ CONTENT_REPO_TOKEN appears (masked value shown)

### Step 5: Trigger Workflow Manually

Go to: **Actions → Daily Content Publisher → Run workflow**

- Topic: (leave blank for auto-generated)
- Verify only: false
- Click "Run workflow"

**Wait 2-5 minutes** for the workflow to execute.

### Step 6: Check Results

**Workflow Logs**:
- Go to **Actions → Daily Content Publisher → Latest run**
- Check logs for success message

**Published Content**:
- Go to `https://quantam101.github.io/content/`
- New post should appear
- Latest post should have today's date

**GitHub Pages Deployment**:
- Go to **quantam101/content** repo
- Check recent commits in `posts/` directory
- New markdown file should be present

---

## Troubleshooting

### Workflow fails on "Validate secrets"
**Problem**: GitHub Secrets not configured  
**Solution**: Follow Step 2 above to add all 4 required secrets

### "Secrets-valid: false" error
**Problem**: One or more required secrets missing  
**Solution**: 
1. Go to Settings → Secrets
2. Verify all 4 secrets are present (GROQ, GEMINI, HF_TOKEN, CONTENT_REPO_TOKEN)
3. Check secret names are EXACTLY correct (case-sensitive)

### Workflow runs but "Publish fails"
**Problem**: LLM provider failure without fallback  
**Solution**: This should not happen — deterministic fallback generates content even without APIs
- Check workflow logs for error message
- Verify API keys are valid in GitHub Secrets

### Article published but to wrong repository
**Problem**: Publishing to profitenginev5 instead of quantam101/content  
**Cause**: CONTENT_REPO_TOKEN not set or invalid  
**Solution**: Verify CONTENT_REPO_TOKEN is correct GitHub token with write access to `quantam101/content`

### GitHub Pages not updating
**Problem**: Article commits to repo but GitHub Pages not showing new post  
**Solution**:
1. Go to **quantam101/content** repo → Settings → Pages
2. Verify Source is set to "Deploy from a branch"
3. Check branch is `main` and directory is `/posts` or root
4. Wait 2-5 minutes for GitHub Pages rebuild

---

## Expected Behavior After Setup

### Daily Publishing
- 07:05 UTC: Morning article publishes automatically
- 15:05 UTC: Afternoon article publishes automatically
- Each article:
  - Generated via Groq/Gemini/HuggingFace
  - Includes 50+ affiliate links (Amazon, Zapier, Hosting, Tools, etc.)
  - FTC disclosure auto-included
  - Published to GitHub Pages
  - Published to optional social platforms (Dev.to, Hashnode, Medium, etc.)

### Content Metrics
- Currently: 58 posts live (as of 2026-06-19)
- After setup: 2 new posts daily (07:05 UTC + 15:05 UTC)
- All monetized with affiliate links
- All compliant with FTC disclosure

### Revenue from Content
- Amazon Associates clicks tracked
- Affiliate link conversions tracked
- Revenue feeds into `/api/profitability` ranking
- Proves monetization before ProfitEngine $149/mo unlocks

---

## Verify End-to-End

After completing setup:

```bash
# 1. Check workflow status (GitHub UI)
# Actions → Daily Content Publisher → Latest run should show ✅ PASS

# 2. Verify article published (GitHub Pages)
curl https://quantam101.github.io/content/
# Should list latest article

# 3. Verify GitHub commit (GitHub repo)
# quantam101/content → Recent commits should include new post

# 4. Check content is live
# Visit https://quantam101.github.io/content/YYYY-MM-DD-article-name.md
# Article should load with affiliate links visible
```

---

## Timeline

**Now**: You have all the infrastructure and secrets locally
**After setup (5 minutes)**: GitHub Secrets configured
**Within 5 minutes of next scheduled time**: Workflow runs and publishes
**Within 1-5 minutes**: Content appears on GitHub Pages

---

## Critical Path to Working System

```
CURRENT STATE (Not working):
├── ✅ Scripts exist
├── ✅ Workflow defined
├── ✅ 58 posts published (historically)
├── ❌ GitHub Secrets NOT configured ← BLOCKER
└── ❌ Daily publishing NOT running ← RESULT OF BLOCKER

AFTER SETUP (Working):
├── ✅ Scripts ready
├── ✅ Workflow defined
├── ✅ GitHub Secrets configured ← UNBLOCKS EVERYTHING
├── ✅ Workflow runs on schedule (07:05, 15:05 UTC)
├── ✅ Content auto-generates
├── ✅ Content auto-publishes to GitHub Pages
├── ✅ Content auto-distributes to social (optional)
└── ✅ Revenue tracked via affiliate links
```

---

## Verify It's Actually Working

After 1-2 scheduled runs (allow 1-5 min after 07:05 or 15:05 UTC):

1. **Check GitHub Pages**:
   - `https://quantam101.github.io/content/`
   - Should show new post with today's date

2. **Check profitability API**:
   - `https://profitengine-tau.vercel.app/api/data`
   - Should show latest post: today's date

3. **Check GitHub repo**:
   - `quantam101/content` repo
   - Recent commits should include new posts

4. **Check workflow history**:
   - GitHub Actions → Daily Content Publisher
   - Recent runs should show ✅ PASSED

---

**NEXT ACTION**: Add the 4 required secrets to GitHub Secrets, then the system will automatically publish content on schedule. Without this, content creation is blocked.

# Automation Quick Start Guide

**Get your complete automated launch system running in 5 minutes**

---

## TL;DR

```bash
# 1. Add secrets to GitHub
gh secret set GUMROAD_API_TOKEN --body "gumroad_api_xxx"
gh secret set OPENAI_API_KEY --body "sk-proj-xxx"
gh secret set IG_USER_ID --body "xxx"
gh secret set FB_PAGE_ACCESS_TOKEN --body "xxx"
gh secret set REPLICATE_API_TOKEN --body "xxx"
gh secret set ELEVENLABS_API_KEY --body "xxx"
gh secret set BEEHIIV_API_KEY --body "xxx"

# 2. Create content files
cat > GUMROAD_PRODUCT_EBOOK.md << 'EOF'
---
title: "Your eBook Title"
description: "Description"
price: 29.99
product_type: "ebook"
---
Content here...
EOF

# 3. Trigger automation
gh workflow run automation.yml

# Done! Workflow runs daily at 9 AM UTC
```

---

## What Gets Automated

| Task | Frequency | Output |
|------|-----------|--------|
| Gumroad eBooks | On demand | Product page + sales page |
| Instagram Carousels | Daily | 7-slide posts (Tue 9 AM, Thu 2 PM, Sat 9 AM ET) |
| Instagram Reels | Daily | 60-second video with voiceover |
| Instagram Stories | Daily | 3 stories (9 AM, 12 PM, 7 PM ET) |
| Email Sequences | On demand | Automated onboarding in email service |

---

## Minimum Setup (5 services required)

1. **Gumroad** — Sell eBooks/products
   - Token from: gumroad.com/settings/api

2. **OpenAI** — Generate cover images
   - Key from: platform.openai.com/api/keys
   - Cost: ~$5/month

3. **Meta/Instagram** — Post to Instagram
   - Token from: business.facebook.com
   - Cost: Free

4. **Replicate** — Generate videos
   - Token from: replicate.com
   - Cost: ~$10/month

5. **ElevenLabs** — Generate voiceovers
   - Key from: elevenlabs.io
   - Cost: ~$5/month

---

## Files to Create

### 1. GUMROAD_PRODUCT_EBOOK.md
```yaml
---
title: "Your Product Title"
description: "One-line description"
price: 29.99
category: "book"
product_type: "ebook"
tags: [tag1, tag2]
image_prompt: "Description of cover image"
---

# Your eBook Content

## Chapter 1
Content...
```

### 2. INSTAGRAM_CAROUSEL_DESIGNS.md
```markdown
# Carousel Title

## Description
Overview

## Hashtags
#tag1 #tag2

### Slide 1
Title: Slide title
Description: What this slide says
Image Prompt: Visual description
```
(Create 7 slides total)

### 3. PREMIUM_ONBOARDING_SEQUENCE.md
```markdown
## Sequence: Welcome Email

**Trigger**: signup

### Email 1: Welcome
**Subject**: Welcome!
**Send After**: 0 hours
**CTA**: Click Here
**CTA Link**: https://...

Content...
```

---

## Run Automation

### Option 1: Automatic Daily (Default)
Runs automatically at 9 AM UTC (4 AM ET)

### Option 2: Manual Trigger
```bash
# Via CLI
gh workflow run automation.yml --ref main

# Via GitHub UI
# Actions → Full Automation Launch → Run workflow
```

### Option 3: API Trigger
```bash
curl -X POST https://your-app.vercel.app/api/automation/launch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"parallel": true}'
```

---

## Monitor Results

```bash
# Check latest run
gh run list --workflow=automation.yml --limit=1

# View detailed logs
gh run view <RUN_ID> --log

# Check automation status
curl https://your-app.vercel.app/api/automation/launch \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Environment Variables

Set in GitHub Settings → Secrets and variables → Actions:

**Required:**
```
GUMROAD_API_TOKEN = gumroad_api_xxx
OPENAI_API_KEY = sk-proj-xxx
IG_USER_ID = instagram-id
FB_PAGE_ACCESS_TOKEN = access-token
REPLICATE_API_TOKEN = replica-token
ELEVENLABS_API_KEY = xi-xxx
BEEHIIV_API_KEY = xxx
```

**Configuration:**
```
AUTOMATION_PARALLEL = true
EMAIL_SERVICE = beehiiv
IMAGE_GENERATION_API = dalle
VIDEO_GENERATION_API = replicate
```

---

## Status & Logs

**GitHub Actions:**
- Go to Actions tab → Full Automation Launch
- View latest run results

**Local Logs:**
```bash
# View all runs
cat .runtime/automation/launch-status.jsonl | jq .

# View specific run
cat .runtime/automation/automation-<runId>.json
```

---

## Success Criteria

✓ All secrets configured  
✓ Content files created and formatted  
✓ Workflow runs without errors  
✓ Products posted to Gumroad  
✓ Instagram posts published  
✓ Email sequences created  

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "API key not configured" | Add to GitHub Secrets |
| "File not found" | Create GUMROAD_PRODUCT_*.md, etc. |
| "No tasks enabled" | Ensure API keys are set in secrets |
| "Rate limit exceeded" | Set AUTOMATION_PARALLEL=false |

---

## Support Files

- **Setup Details:** AUTOMATION_ENV_SETUP.md
- **Full Documentation:** AUTOMATION_SETUP.md
- **API Reference:** POST /api/automation/launch

---

## Cost Estimate

| Service | Est. Monthly |
|---------|--------------|
| OpenAI (images) | $5 |
| Replicate (videos) | $10 |
| ElevenLabs (voice) | $5 |
| Other services | Free |
| **Total** | **~$20** |

All within free tier or minimal cost!

---

## Next Steps

1. Add secrets to GitHub (5 min)
2. Create content files (10 min)
3. Test workflow manually (5 min)
4. Enable daily schedule (1 min)
5. Monitor first run (3 min)

**Total time: ~25 minutes**

---

For detailed setup instructions, see: **AUTOMATION_ENV_SETUP.md**

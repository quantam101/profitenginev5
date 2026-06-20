# ProfitEngine v5 — Complete Automation System

A fully automated product launch infrastructure that handles everything from Gumroad product publishing to Instagram content generation to email marketing campaigns.

**Status**: Production-ready (v5.1.0)  
**Last Updated**: 2026-06-20

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Configuration](#configuration)
4. [Running Automation](#running-automation)
5. [Monitoring & Dashboards](#monitoring--dashboards)
6. [API Integrations](#api-integrations)
7. [Troubleshooting](#troubleshooting)
8. [File Reference](#file-reference)

---

## Quick Start

### 1. Set Up Environment (5 minutes)

```bash
# Copy automation config template
cp .env.automation .env.automation.local

# Edit with your API keys
nano .env.automation.local

# Verify all keys are valid
npx ts-node scripts/automation/verify-automation.ts
```

### 2. Add Secrets to GitHub (5 minutes)

Go to **Settings** → **Secrets and variables** → **Actions**

Add these secrets from `.env.automation.local`:

```
GUMROAD_API_KEY
INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ACCOUNT_ID
DALLE_API_KEY or REPLICATE_API_TOKEN
SYNTHESIA_API_KEY
ELEVEN_LABS_API_KEY
KLAVIYO_API_KEY (or SUBSTACK_API_KEY)
GITHUB_ACTIONS_TOKEN
SLACK_WEBHOOK_URL
```

### 3. Trigger Your First Automation (1 minute)

**Option A: Manual (Recommended for testing)**

1. Go to **Actions** → **Automation Launch System**
2. Click **Run workflow**
3. Select:
   - **trigger_type**: `full-launch`
   - **dry_run**: `true` (first time only)
   - **notify_slack**: `true`
4. Click **Run workflow**

**Option B: CLI**

```bash
# Test without publishing (dry-run)
AUTOMATION_DRY_RUN=true npm run launch:automation

# Or via GitHub CLI
gh workflow run automation-launch.yml \
  -f trigger_type=full-launch \
  -f dry_run=true
```

### 4. Monitor Results (Ongoing)

```bash
# Watch real-time dashboard
open automation-dashboard.html

# Or check status file
cat automation-status.json | jq .

# Or monitor Slack #automation-alerts channel
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ProfitEngine v5 Automation              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Trigger Layer                          │   │
│  │  • Manual (GitHub UI)                              │   │
│  │  • Scheduled (Cron)                                │   │
│  │  • Event-driven (webhooks)                         │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │     Automation Pipeline (.github/workflows/         │   │
│  │     automation-launch.yml)                          │   │
│  │                                                     │   │
│  │  1. Validate secrets                               │   │
│  │  2. Publish to Gumroad                             │   │
│  │  3. Generate & post to Instagram                   │   │
│  │  4. Send email campaigns                           │   │
│  │  5. Sync metrics                                   │   │
│  │  6. Notify Slack                                   │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │         External APIs                              │   │
│  │  • Gumroad (product sales)                         │   │
│  │  • Instagram Graph API (social media)              │   │
│  │  • Replicate / DALL-E (image generation)           │   │
│  │  • Synthesia (video generation)                    │   │
│  │  • Eleven Labs (voiceover)                         │   │
│  │  • Klaviyo / Substack (email)                      │   │
│  │  • Slack (notifications)                           │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │         Status & Monitoring                        │   │
│  │  • automation-status.json (live metrics)           │   │
│  │  • automation-dashboard.html (web UI)              │   │
│  │  • Slack notifications                             │   │
│  │  • .runtime/automation/ (logs & artifacts)         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

Store in `.env.automation.local` (never commit):

```bash
# Gumroad
GUMROAD_API_KEY=gumroad_pat_...
GUMROAD_CREATOR_ID=alreadyhere

# Instagram
INSTAGRAM_ACCESS_TOKEN=IGSHO...
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400963180
INSTAGRAM_HASHTAGS=profittrading,financialfreedom

# Image Generation (choose one)
REPLICATE_API_TOKEN=r8_...
DALLE_API_KEY=sk-...
IMAGE_GENERATION_PROVIDER=replicate

# Video & Voiceover
SYNTHESIA_API_KEY=...
ELEVEN_LABS_API_KEY=sk_...
ELEVEN_LABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Email (choose one platform)
EMAIL_PLATFORM=klaviyo
KLAVIYO_API_KEY=pk_...
KLAVIYO_LIST_ID=list_...

# Automation Control
GITHUB_ACTIONS_TOKEN=ghp_...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
AUTOMATION_DRY_RUN=false
AUTOMATION_TIMEOUT_MS=30000
```

### GitHub Secrets

Required for CI/CD workflows. Add all secrets from `.env.automation.local` to:  
`Settings` → `Secrets and variables` → `Actions`

**Naming convention**: Use `UPPERCASE_SNAKE_CASE` (e.g., `GUMROAD_API_KEY`)

---

## Running Automation

### Manual Trigger (Recommended for Testing)

```bash
# Full product launch (Gumroad + Instagram + Email)
gh workflow run automation-launch.yml \
  -f trigger_type=full-launch \
  -f dry_run=false

# Instagram posts only
gh workflow run automation-launch.yml \
  -f trigger_type=instagram-posts

# Email campaign only
gh workflow run automation-launch.yml \
  -f trigger_type=email-campaign

# Verify APIs without publishing
gh workflow run automation-launch.yml \
  -f trigger_type=verify-only
```

### Scheduled Automation (Already Configured)

These run automatically on schedule:

| What | Schedule | Config |
|------|----------|--------|
| **Instagram Stories** | 07:00, 14:00, 20:00 UTC daily | `.github/workflows/automation-launch.yml` |
| **Carousels** | Tue/Thu/Sat 09:00 UTC | `.github/workflows/automation-launch.yml` |
| **Reels** | Mon/Wed/Fri 10:00 UTC | `.github/workflows/automation-launch.yml` |
| **Email** | Monday 08:00 UTC | `.github/workflows/automation-launch.yml` |
| **Metrics Sync** | Every hour | `.github/workflows/automation-launch.yml` |

### Local Testing (Dry-Run)

```bash
# Verify all APIs without making changes
npx ts-node scripts/automation/verify-automation.ts

# Simulate automation (generate images but don't post)
AUTOMATION_DRY_RUN=true npm run launch:automation

# Generate test report
npm run automation:report
```

---

## Monitoring & Dashboards

### Web Dashboard

Open in browser (auto-updates every 30 seconds):

```bash
# Start dashboard server
npm run automation:dashboard

# Or open directly
open automation-dashboard.html
```

**Shows**:
- ✅ Real-time revenue & sales
- ✅ Instagram metrics (followers, engagement, scheduled posts)
- ✅ Email performance (open rates, conversions)
- ✅ Product status (published, active, sales)
- ✅ API health (response times, errors)
- ✅ Job status (last run, next run)

### Status JSON

Real-time metrics file (auto-updated):

```bash
cat automation-status.json | jq '.revenue, .instagram, .email'
```

Contains:
- Product sales & revenue
- Instagram followers & engagement
- Email subscribers & conversion rates
- Automation job history
- API health status

### Slack Notifications

Receives automatic updates in `#automation-alerts`:

```
✅ [Automation Launch] Full launch successful
   • Gumroad: 3 products published
   • Instagram: 6 posts scheduled
   • Email: 234 sent (28.5% open rate)
   • Metrics synced at 2026-06-20T15:30:00Z
```

### GitHub Actions Logs

Monitor workflow runs in real-time:

```bash
# Watch specific workflow
gh workflow run automation-launch.yml --watch

# View recent runs
gh run list --workflow=automation-launch.yml --limit=10

# View logs
gh run view <run-id> --log
```

---

## API Integrations

### Gumroad

**What**: Product publishing & sales tracking  
**Setup**: https://app.gumroad.com → Settings → Advanced → API  
**Rate limit**: 60 req/min  
**Timeout**: 10 seconds

```bash
# Test connection
curl -H "Authorization: Bearer $GUMROAD_API_KEY" \
  https://api.gumroad.com/v2/user/products
```

### Instagram (Meta Graph API)

**What**: Post stories, carousels, reels + engagement tracking  
**Setup**: https://developers.facebook.com → Instagram Graph API  
**Rate limit**: 200 req/min per token  
**Timeout**: 15 seconds

```bash
# Test connection
curl "https://graph.instagram.com/me?access_token=$INSTAGRAM_ACCESS_TOKEN"
```

**Token refresh**: Instagram tokens expire after 1 hour. Use long-lived tokens (60 day validity):
1. Go to Meta Business Manager
2. Settings → Accounts → Instagram
3. Generate long-lived token

### Image Generation

**Replicate** (recommended for cost):
- Cost: ~$0.01/image
- Speed: 20-30 seconds
- Quality: Good

**DALL-E** (premium quality):
- Cost: $0.04-0.20/image
- Speed: 10-30 seconds
- Quality: Excellent

### Email Platforms

**Klaviyo** (recommended):
- Cost: Free up to 500 subscribers
- Features: Email + SMS
- Automation: Excellent

**Substack**:
- Cost: Free
- Features: Email only
- Automation: Limited

**ConvertKit**:
- Cost: Free up to 1,000 subscribers
- Features: Email + memberships
- Automation: Good

---

## Troubleshooting

### Issue: Workflow stuck/hanging

**Solution**:
1. Check GitHub Actions status: https://www.githubstatus.com
2. Increase timeout in workflow:
   ```yaml
   timeout-minutes: 10  # Increase from default
   ```
3. Kill hung workflow: `gh run cancel <run-id>`

### Issue: Instagram posts not appearing

**Solution**:
1. Verify token is still valid (they expire after 1 hour)
2. Check Instagram Graph API quota: https://developers.facebook.com/docs/instagram-api/overview
3. Ensure business account has proper permissions
4. Check Slack for detailed error messages

### Issue: Email not sending

**Solution**:
1. Verify email platform is configured in `EMAIL_PLATFORM` variable
2. Check API key is correct in GitHub Secrets
3. Verify recipient list exists and is active
4. Check email platform rate limits

### Issue: Metrics not updating

**Solution**:
1. Run manual metrics sync:
   ```bash
   gh workflow run automation-launch.yml \
     -f trigger_type=metrics-sync
   ```
2. Check API health in dashboard
3. Verify all API tokens haven't expired

### Issue: "Missing required secrets" error

**Solution**:
1. List required secrets for your trigger:
   ```bash
   gh secret list
   ```
2. Add missing secrets from GitHub UI:
   https://github.com/quantam101/profitenginev5/settings/secrets/actions

### Issue: API rate limits hit

**Solution**:

| API | Limit | Fix |
|-----|-------|-----|
| Gumroad | 60/min | Wait 60 seconds |
| Instagram | 200/min | Reduce frequency |
| Stripe | 100/sec | Space out requests |
| Slack | Unlimited | - |

---

## File Reference

### Configuration Files

| File | Purpose |
|------|---------|
| `.env.automation` | Template with all required keys |
| `.env.automation.local` | Your local secrets (never commit) |
| `automation-status.json` | Live metrics & status |
| `AUTOMATION_SETUP.md` | Step-by-step setup guide |
| `AUTOMATION_TRIGGERS.md` | All automation triggers documented |

### Workflow Files

| File | Purpose |
|------|---------|
| `.github/workflows/automation-launch.yml` | Main automation workflow |

### Scripts

| File | Purpose |
|------|---------|
| `scripts/automation/verify-automation.ts` | Verify all APIs |
| `scripts/automation/gumroad-publish.mjs` | Publish to Gumroad |
| `scripts/automation/instagram-post.mjs` | Post to Instagram |
| `scripts/automation/email-campaign.mjs` | Send emails |
| `scripts/automation/generate-images.py` | Generate product images |
| `scripts/automation/sync-*-metrics.mjs` | Sync metrics from each platform |
| `scripts/automation/update-status.mjs` | Update automation-status.json |
| `scripts/automation/merge-status.mjs` | Merge all metrics |
| `scripts/automation/generate-report.mjs` | Generate final report |

### Dashboard

| File | Purpose |
|------|---------|
| `automation-dashboard.html` | Web dashboard (open in browser) |

### Documentation

| File | Purpose |
|------|---------|
| `AUTOMATION_README.md` | This file (system overview) |
| `AUTOMATION_SETUP.md` | API setup guide |
| `AUTOMATION_TRIGGERS.md` | Complete trigger documentation |

---

## NPM Scripts

Add these to `package.json` for convenience:

```json
{
  "scripts": {
    "verify:automation": "npx ts-node scripts/automation/verify-automation.ts",
    "launch:automation": "gh workflow run automation-launch.yml -f trigger_type=full-launch",
    "launch:automation:test": "gh workflow run automation-launch.yml -f trigger_type=full-launch -f dry_run=true",
    "automation:dashboard": "python -m http.server 8765 --directory .",
    "automation:status": "cat automation-status.json | jq .",
    "automation:report": "gh workflow run automation-launch.yml -f trigger_type=verify-only"
  }
}
```

Then run:
```bash
npm run verify:automation
npm run launch:automation:test
npm run automation:dashboard
```

---

## Advanced: Customizing Schedules

Edit `.github/workflows/automation-launch.yml` to change when automation runs:

```yaml
schedule:
  # Stories at custom times
  - cron: '0 8 * * *'     # 08:00 UTC
  - cron: '0 16 * * *'    # 16:00 UTC
  
  # Carousels on different days
  - cron: '0 9 * * 1,4'   # Mon + Thu (1=Mon, 4=Thu)
```

[Cron syntax reference](https://crontab.guru/)

---

## Security Best Practices

### ✅ DO

- Store all API keys in GitHub Secrets only
- Use long-lived tokens for Instagram (60 days)
- Rotate API keys every 90 days
- Use dry-run mode (`AUTOMATION_DRY_RUN=true`) for testing
- Monitor Slack for failed automation alerts
- Keep `.env.automation.local` in `.gitignore`

### ❌ DON'T

- Commit API keys to repository
- Use short-lived Instagram tokens in production
- Run full automation without dry-run first
- Disable security checks in workflows
- Share API keys via email or chat
- Run manual overrides during scheduled jobs

---

## Support & Documentation

- **Setup help**: See `AUTOMATION_SETUP.md`
- **Trigger docs**: See `AUTOMATION_TRIGGERS.md`
- **API errors**: Check Slack `#automation-alerts`
- **Workflow logs**: GitHub Actions tab
- **Dashboard status**: Open `automation-dashboard.html`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v5.1.0 | 2026-06-20 | Complete automation system |
| v5.0.0 | 2026-06-15 | Initial release |

---

**Ready to automate?** Start with [AUTOMATION_SETUP.md](./AUTOMATION_SETUP.md)

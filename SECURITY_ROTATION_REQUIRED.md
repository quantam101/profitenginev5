# SECURITY: Secrets Rotation Required ⚠️

**Status**: BLOCKING PRODUCTION DEPLOYMENT  
**Severity**: CRITICAL  
**Date**: 2026-06-19

## Overview

The `.env` file in the working directory contains 20+ live production API keys and database credentials. These secrets must be rotated before production deployment.

**Why This Matters**:
- Secrets in `.env` could be exposed via: git backups, IDE caching, USB drives, logs, accidental commits
- Compromised Stripe keys allow attackers to charge customers
- Compromised database credentials enable data theft
- Compromised GitHub tokens allow repository takeover

## Current State

✅ **Good**: `.env` is in `.gitignore` and NOT in git history  
⚠️ **Problem**: `.env` exists locally with live production secrets  
⚠️ **Problem**: Need to verify all secrets are in Vercel + GitHub Secrets  

## Secrets That Need Rotation

### Tier 1: IMMEDIATE (Payment Systems)
- `STRIPE_API_KEY` (sk_live_...)
- `STRIPE_SECRET_KEY` (sk_live_...)  
- `STRIPE_WEBHOOK_SECRET`
- `GUMROAD_ACCESS_TOKEN`
- `GUMROAD_SELLER_ID`

**Action**: 
1. Go to Stripe dashboard → API Keys
2. Rotate all API keys
3. Update in Vercel (Production env vars)
4. Update in GitHub Secrets

### Tier 2: IMMEDIATE (Database Access)
- `MONGODB_URL` (with credentials)
- `DATABASE_URL` (Neon PostgreSQL with credentials)

**Action**:
1. Regenerate MongoDB connection string (change password in MongoDB Atlas)
2. Regenerate Neon connection string (rotate password in Neon console)
3. Update in Vercel (Production env vars)
4. Update in GitHub Secrets
5. Restart all services that use these

### Tier 3: URGENT (LLM API Access)
- `OPENAI_API_KEY` (sk-proj-...)
- `OPENROUTER_API_KEY` (sk-or-v1-...)
- `GEMINI_API_KEY` (AIzaSy...)
- `GROQ_API_KEY` (gsk_...)
- `DEEPSEEK_API_KEY`

**Action**:
1. Go to each provider's dashboard
2. Revoke old API keys
3. Generate new keys
4. Update in Vercel (Production env vars)
5. Update in GitHub Secrets

### Tier 4: HIGH (OAuth & Platform Access)
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `GITHUB_TOKEN` (JWT-based)
- `CONTENT_REPO_TOKEN` (gho_...)
- `HF_TOKEN` (HuggingFace)

**Action**:
1. Regenerate each OAuth token in respective platform
2. Update in Vercel (Production env vars)
3. Update in GitHub Secrets

### Tier 5: MEDIUM (Communication Services)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_WEBHOOK_SECRET`
- `GMAIL_APP_PASSWORD`
- `BOTPRESS_TOKEN`
- `RESEND_API_KEY`

**Action**:
1. For Telegram: Create new bot via @BotFather
2. For Gmail: Generate new app password
3. For Botpress & Resend: Regenerate tokens
4. Update in Vercel (Production env vars)
5. Update in GitHub Secrets

### Tier 6: MEDIUM (Content Platforms)
- `HASHNODE_API_KEY`
- `HASHNODE_PUB_ID`
- `DEVTO_API_KEY`
- `BEEHIIV_API_KEY`
- `BEEHIIV_PUBLICATION_ID`
- `MEDIUM_API_KEY`

**Action**:
1. Regenerate each API key in respective platform
2. Update in Vercel (Production env vars)
3. Update in GitHub Secrets

### Other Secrets
- `PROFITENGINE_WEBHOOK_TOKEN` — rotate to new random value
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — currently empty (skip)
- `AFFILIATE_LINKS` — public JSON, no rotation needed

## Rotation Process

### Step 1: Verify Current Configuration

```bash
# Check if .env is gitignored
grep ".env" .gitignore

# Check .env is NOT in git history
git log --all -- .env

# Check Vercel has Production env vars set (cannot check directly from CLI)
# Manually verify: vercel.com → profitengine-tau → Settings → Environment Variables

# Check GitHub Secrets (cannot check values from CLI)
# Manually verify: github.com → quantam101/profitenginev5 → Settings → Secrets
```

### Step 2: Rotate Secrets (In Priority Order)

For each secret in the priority list above:

1. **Access the platform** (Stripe, MongoDB, OpenAI, etc.)
2. **Revoke old credential** (delete, disable, or rotate)
3. **Generate new credential**
4. **Update Vercel Production env** (must set as Production, not Preview)
5. **Update GitHub Secrets** (required for CI/CD workflows)
6. **Update local .env** (for continued development, but will be deleted after verification)
7. **Test in CI/CD** (run workflows to verify new secrets work)

### Step 3: Verify Secrets are Working

After rotating all critical secrets:

```bash
# Run CI pipeline to verify secrets in GitHub Actions
git push origin main

# Watch GitHub Actions → CI workflow
# All stages should pass with new secrets:
#   - Stage 1: pre_merge (lint, unit, types)
#   - Stage 2: integration (API + Mongo)
#   - Stage 3: e2e (backend health)

# Verify Vercel deployment uses new Vercel secrets
# Go to: vercel.com → profitengine-tau → Deployments → Latest
# Check that build succeeded with new env vars
```

### Step 4: Cleanup

After verifying all new secrets work:

```bash
# Back up the old .env (optional, for reference only)
cp .env .env.backup-2026-06-19

# Remove local .env
rm .env

# Verify git is clean
git status
# Should show: "working tree clean"

# Optional: Remove backup after confirming no issues for 1 week
rm .env.backup-2026-06-19
```

## Where Secrets Go

| Secret | Development | Staging | Production |
|--------|-------------|---------|------------|
| API Keys (OpenAI, Groq, etc) | `.env` local | GitHub Secrets | Vercel (Production) |
| Database URLs (MongoDB, Neon) | `.env` local | GitHub Secrets | Vercel (Production) |
| Payment Keys (Stripe) | `.env` local | GitHub Secrets | Vercel (Production) + PCI monitoring |
| GitHub Tokens | GitHub Secrets | GitHub Secrets | GitHub Secrets (rotate 90 days) |
| OAuth Credentials | `.env` local + GitHub Secrets | GitHub Secrets | Vercel (Production) + platform dashboard |

## Secret Names Mapping

The following table maps the secrets in `.env` to where they should be configured:

### Vercel Production Environment Variables

```
RUNTIME_API_URL=https://api.profitengine.alreadyherellc.com
BACKEND_API_URL=https://api.profitengine.alreadyherellc.com
ORACLE_API_URL=https://api.profitengine.alreadyherellc.com
STRIPE_API_KEY=sk_live_... (from Stripe)
STRIPE_SECRET_KEY=sk_live_... (from Stripe)
STRIPE_WEBHOOK_SECRET=whsec_... (from Stripe)
GUMROAD_ACCESS_TOKEN=... (from Gumroad)
GUMROAD_SELLER_ID=... (from Gumroad)
GROQ_API_KEY=gsk_... (from Groq)
OPENROUTER_API_KEY=sk-or-v1-... (from OpenRouter)
GEMINI_API_KEY=AIzaSy... (from Google)
OPENAI_API_KEY=sk-proj-... (from OpenAI)
DEEPSEEK_API_KEY=... (from DeepSeek)
MONGODB_URL=mongodb+srv://... (from MongoDB Atlas)
DATABASE_URL=postgresql://... (from Neon)
BEEHIIV_API_KEY=... (from Beehiiv)
BEEHIIV_PUBLICATION_ID=... (from Beehiiv)
DEVTO_API_KEY=... (from DevTo)
HASHNODE_API_KEY=... (from Hashnode)
HASHNODE_PUB_ID=... (from Hashnode)
YOUTUBE_CLIENT_ID=... (from Google Cloud)
YOUTUBE_CLIENT_SECRET=... (from Google Cloud)
YOUTUBE_REFRESH_TOKEN=... (from YouTube OAuth)
TELEGRAM_BOT_TOKEN=... (from BotFather)
TELEGRAM_CHAT_ID=... (from Telegram)
TELEGRAM_WEBHOOK_SECRET=... (rotate to new random value)
GMAIL_USER=dispatch@alreadyherellc.com
GMAIL_APP_PASSWORD=... (from Google App Passwords)
GITHUB_TOKEN=... (from GitHub)
CONTENT_REPO_TOKEN=... (from GitHub)
HF_TOKEN=... (from HuggingFace)
PROFITENGINE_WEBHOOK_TOKEN=... (rotate to new random value)
RESEND_API_KEY=... (from Resend)
BOTPRESS_TOKEN=... (from Botpress)
AMAZON_PARTNER_TAG=alreadyhere-20
AFFILIATE_LINKS=... (public JSON)
```

### GitHub Secrets Required for CI/CD

```
PROFITENGINE_WEBHOOK_TOKEN=... (matches Vercel)
RUNTIME_API_URL=... (matches Vercel)
GROQ_API_KEY=... (matches Vercel)
GEMINI_API_KEY=... (matches Vercel)
ANTHROPIC_API_KEY=... (for content pipeline)
CONTENT_REPO_TOKEN=... (matches Vercel)
GMAIL_APP_PASSWORD=... (matches Vercel)
DEVTO_API_KEY=... (matches Vercel)
HASHNODE_API_KEY=... (matches Vercel)
HASHNODE_PUB_ID=... (matches Vercel)
GMAIL_USER=dispatch@alreadyherellc.com
```

## Security Checklist

After completing secret rotation:

- [ ] All Tier 1 secrets (payment) rotated and updated in Vercel + GitHub Secrets
- [ ] All Tier 2 secrets (database) rotated and updated in Vercel + GitHub Secrets
- [ ] All Tier 3-6 secrets rotated and updated in Vercel + GitHub Secrets
- [ ] CI/CD workflows pass with new secrets (verify via GitHub Actions)
- [ ] Vercel Production deployment succeeds with new secrets
- [ ] All production endpoints return 200 OK with new secrets
- [ ] Local `.env` file backed up and removed
- [ ] Git working tree is clean
- [ ] Security scan passes (`npm run security:scan`)
- [ ] Production verification script passes (`bash scripts/verify-oauth.sh`)

## Timeline

- **Today (2026-06-19)**: Identify secrets, create rotation plan
- **Action Required**: Follow rotation steps above (15-30 mins per tier)
- **Verification**: Run CI/CD and verify all services work (5-10 mins)
- **Cleanup**: Remove local `.env`, verify git clean (2 mins)
- **Status**: "PRODUCTION READY" once all steps complete

## Support

If you encounter issues during rotation:

1. Check GitHub Actions logs for specific error messages
2. Verify the new secret value is exactly correct (no extra spaces, typos)
3. Check that Vercel shows the secret in Production scope (not Preview)
4. If a service still uses the old secret, it may be cached — wait 2-3 minutes or restart
5. Verify the secret name matches exactly (case-sensitive)

## Next Steps

1. **Start with Tier 1** (Stripe) — highest risk, highest impact
2. **Move to Tier 2** (Database) — highest data risk
3. **Continue with Tiers 3-6** in priority order
4. **Verify** each tier in CI/CD before moving to the next
5. **Cleanup** local `.env` once all tiers verified

---

**Do not deploy to production until all critical secrets are rotated and verified.**

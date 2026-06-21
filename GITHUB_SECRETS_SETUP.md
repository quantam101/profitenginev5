# GitHub Secrets Setup Guide

## Critical for Production Deployment

All environment variables must be configured in GitHub Secrets for CI/CD deployment to work.

### Setup Instructions

1. **Navigate to Repository Settings**
   ```
   https://github.com/quantam101/profitenginev5/settings/secrets/actions
   ```

2. **Click "New repository secret"** for each variable below

3. **Add All 6 Required Secrets:**

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `FINNHUB_API_KEY` | (from .env or Finnhub account) | Real-time stock price data |
| `STRIPE_API_KEY` | sk_live_51TbKf7LCbDeo... | Payment processing |
| `OPENAI_API_KEY` | sk-proj-45TjTVba97g2... | Content generation & analysis |
| `TELEGRAM_BOT_TOKEN` | 8465028396:AAE_1SJNL93... | Real-time notifications |
| `MONGODB_URL` | mongodb+srv://alreadyherellc_db_user:... | Document database |
| `POSTGRESQL_URL` | postgresql://neondb_owner:npg_... | Relational database |

### Getting Values

**Option 1: From Local .env File**
```bash
# View current values
cat .env | grep -E "FINNHUB|STRIPE|OPENAI|TELEGRAM|MONGODB|POSTGRESQL"
```

**Option 2: From GitHub CLI**
```bash
# Install: https://cli.github.com/
# Login: gh auth login

# Set secret via CLI
gh secret set FINNHUB_API_KEY --body "your-api-key-here"
gh secret set STRIPE_API_KEY --body "sk_live_..."
gh secret set OPENAI_API_KEY --body "sk-proj-..."
gh secret set TELEGRAM_BOT_TOKEN --body "8465028396:AAE_..."
gh secret set MONGODB_URL --body "mongodb+srv://..."
gh secret set POSTGRESQL_URL --body "postgresql://..."
```

### Verification

**Check if secrets are configured:**
```bash
# List all secrets
gh secret list

# Example output:
# FINNHUB_API_KEY      Updated 2026-06-21
# STRIPE_API_KEY       Updated 2026-06-21
# OPENAI_API_KEY       Updated 2026-06-21
# TELEGRAM_BOT_TOKEN   Updated 2026-06-21
# MONGODB_URL          Updated 2026-06-21
# POSTGRESQL_URL       Updated 2026-06-21
```

### Deployment Files Using Secrets

The following files reference GitHub Secrets:

1. **.github/workflows/** - CI/CD pipeline
   ```yaml
   env:
     FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
     STRIPE_API_KEY: ${{ secrets.STRIPE_API_KEY }}
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
     TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
     MONGODB_URL: ${{ secrets.MONGODB_URL }}
     POSTGRESQL_URL: ${{ secrets.POSTGRESQL_URL }}
   ```

2. **Dual Mode Engine** - Uses secrets for live trading
   ```python
   FINNHUB_API_KEY  → Real Finnhub prices (Mon-Fri 4-5pm)
   MONGODB_URL      → Store training results
   POSTGRESQL_URL   → Store live trading results
   ```

### Local Development

For local testing without GitHub Actions, use the `.env` file which already contains placeholder values.

### Production Deployment

Once secrets are configured in GitHub:
1. Commit and push to main branch
2. GitHub Actions workflow automatically uses secrets
3. Dual Mode Engine connects to real Finnhub data
4. Live trading begins Monday 4am with real market data

### Security Best Practices

- ✅ Never commit `.env` to git (already in .gitignore)
- ✅ Store all secrets in GitHub Secrets UI only
- ✅ Use unique API keys for each environment
- ✅ Rotate keys every 90 days
- ✅ Review access logs regularly

### Testing Configuration

To verify secrets work in CI:
```bash
# Push a test commit
git commit --allow-empty -m "test: verify secrets in CI"
git push origin main

# Monitor in GitHub Actions:
# https://github.com/quantam101/profitenginev5/actions
```

### Troubleshooting

**Problem: "Secret not found" error in workflow**
- Verify secret name is EXACT (case-sensitive)
- Check spelling: FINNHUB_API_KEY not FINNHUB_KEY
- Secrets must be added BEFORE workflow runs

**Problem: API key not working in live trading**
- Verify value is complete (no truncation)
- Test with CLI: `gh secret get FINNHUB_API_KEY`
- Check API key hasn't been rotated on original service

**Problem: Workflow fails with auth error**
- Re-add secret with updated value
- Delete old secret: `gh secret delete FINNHUB_API_KEY`
- Add new secret: `gh secret set FINNHUB_API_KEY --body "..."`

### Quick Reference

**Add all secrets at once (using gh CLI):**
```bash
gh secret set FINNHUB_API_KEY --body "$(cat .env | grep FINNHUB_API_KEY | cut -d= -f2-)"
gh secret set STRIPE_API_KEY --body "$(cat .env | grep STRIPE_API_KEY | cut -d= -f2-)"
gh secret set OPENAI_API_KEY --body "$(cat .env | grep OPENAI_API_KEY | cut -d= -f2-)"
gh secret set TELEGRAM_BOT_TOKEN --body "$(cat .env | grep TELEGRAM_BOT_TOKEN | cut -d= -f2-)"
gh secret set MONGODB_URL --body "$(cat .env | grep MONGODB_URL | cut -d= -f2-)"
gh secret set POSTGRESQL_URL --body "$(cat .env | grep POSTGRESQL_URL | cut -d= -f2-)"

# Verify
gh secret list
```

---

## Status

Once all 6 secrets are configured in GitHub:

✅ Local testing: Ready (using .env)  
⏳ Production deployment: Ready after secrets added  
🚀 Live trading: Ready (Monday 4am with real Finnhub data)

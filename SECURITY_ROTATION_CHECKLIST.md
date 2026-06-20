# 🔒 CRITICAL SECURITY ROTATION CHECKLIST
**Status: BLOCKING PRODUCTION** | Date: 2026-06-20

## Repository Status
- ✅ Repository is PRIVATE
- ✅ .env file NOT in git history
- ⚠️ API keys present in git history (commits: 7578daf, 1565135, fc75434)
- ⚠️ GitHub PAT was exposed in git remote (FIXED)

---

## API KEYS REQUIRING IMMEDIATE ROTATION

### Payment & Revenue (CRITICAL)
- [ ] **Stripe API Key** → https://dashboard.stripe.com/apikeys
  - Current: sk_live_51TbKf7LCbD...
  - Action: Rotate in Stripe dashboard → Update in GitHub Secrets → Update Vercel → Update OCI
  
- [ ] **Stripe Webhook Secret** → https://dashboard.stripe.com/webhooks
  - Current: whsec_wvU9MC3D8IC2uZiX8M...
  - Action: Regenerate webhook → Update all environments
  
- [ ] **Gumroad Tokens** → https://app.gumroad.com/settings
  - Access Token: qP1PGdN-zCLeGeaN2r...
  - Seller ID: KTgbGvItMAkVGByS893...

### AI/LLM APIs (HIGH)
- [ ] **OpenAI API Key** → https://platform.openai.com/api-keys
  - Current: sk-proj-45TjTVba97g2Fw...
  
- [ ] **Gemini API Key** → https://console.cloud.google.com/apis/credentials
  
- [ ] **GROQ API Key** → https://console.groq.com/keys
  
- [ ] **OpenRouter API Key** → https://openrouter.ai/account/api-keys
  
- [ ] **DeepSeek API Key** → https://platform.deepseek.com/api/keys

### Database Credentials (CRITICAL)
- [ ] **MongoDB URL** → https://cloud.mongodb.com/v2/security
  - Current: mongodb+srv://alreadyherellc_db_user:Alr3adyh3r3@...
  - Action: Change password in Atlas console
  
- [ ] **PostgreSQL/Neon URL** → https://console.neon.tech/app/settings/api-keys
  - Current: postgresql://neondb_owner:npg_9y5zrwjXROKP@...
  - Action: Rotate password in Neon console

### Third-Party Content Platforms (HIGH)
- [ ] **Dev.to API Key** → https://dev.to/settings/extensions
- [ ] **Hashnode API Key** → https://hashnode.com/settings/developer
- [ ] **Beehiiv API Key** → https://dashboard.beehiiv.com/settings/account/api-keys
- [ ] **Resend API Key** → https://resend.com/api-keys

### Social & Communications (HIGH)
- [ ] **YouTube Credentials** → https://myaccount.google.com/permissions
  - Client ID, Secret, Refresh Token
  
- [ ] **Telegram Bot Token** → https://t.me/botfather
  - Current: 8465028396:AAE_1SJNL93arZlKjABuddJQkX2SR5OC1SU
  
- [ ] **GitHub Token** → https://github.com/settings/tokens
  - Current: ghs_15368_eyJhbGciOiJFUzI1...
  
- [ ] **GitHub Content Repo Token** → https://github.com/settings/tokens
  - Current: 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

### Marketing & Analytics (MEDIUM)
- [ ] **Botpress Token** → https://botpress.com/workspace/settings
- [ ] **Hugging Face Token** → https://huggingface.co/settings/tokens
- [ ] **Gmail App Password** → https://myaccount.google.com/apppasswords
  - Current: gnyzbgqakazszrui

---

## Rotation Steps

### Phase 1: Generate New Credentials (DO FIRST)
1. Open each service's credential page (links above)
2. Generate new API key/password
3. Copy to temporary secure location
4. **DO NOT commit .env to git**

### Phase 2: Update Environments
Each new credential must be updated in:

#### GitHub Secrets
```bash
gh secret set STRIPE_API_KEY --body "sk_live_NEW_VALUE"
gh secret set STRIPE_SECRET_KEY --body "sk_live_NEW_VALUE"
gh secret set OPENAI_API_KEY --body "sk-proj-NEW_VALUE"
# ... repeat for all 23 keys
```

#### Vercel Environment Variables
1. Go to https://vercel.com/profitengine-tau/settings/environment-variables
2. Update each variable:
   - STRIPE_API_KEY
   - STRIPE_SECRET_KEY
   - OPENAI_API_KEY
   - MONGODB_URL
   - DATABASE_URL
   - (All 23 keys)

#### OCI Server (cmdos @ 129.146.236.177)
```bash
ssh opc@129.146.236.177
sudo vi ~/.env  # or wherever runtime .env is stored
# Update all credentials
# Restart services
sudo systemctl restart profitengine-backend
```

### Phase 3: Local Development
```bash
# Update local .env
nano .env
# Paste new credentials
# Restart development server
```

### Phase 4: Verification
- [ ] Trading system operational (all APIs responding)
- [ ] Stripe webhooks working
- [ ] Content publishing working (Dev.to, Hashnode, Beehiiv)
- [ ] Telegram alerts working
- [ ] GitHub automation working
- [ ] YouTube channel sync working
- [ ] All monitoring shows no auth failures

---

## Git History Scrubbing (Optional but Recommended)
If commits 7578daf, 1565135, fc75434 contain exposed keys:

```bash
# WARNING: This rewrites history and requires force-push
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all

# If proceeding:
git push --force-with-lease origin main
```

**NOTE:** Only do this if secrets were ACTUALLY committed (not just in commit messages)

---

## Prevention Going Forward
1. ✅ Keep `.env` in `.gitignore`
2. ✅ Use GitHub Secrets for CI/CD
3. ✅ Use Vercel dashboard for environment variables
4. ✅ Run `npm run security:scan` before every commit
5. ✅ Enable secret scanning push protection on GitHub

---

## Timeline
- **NOW**: Generate all new credentials
- **Hour 1**: Update GitHub Secrets
- **Hour 2**: Update Vercel environment variables  
- **Hour 3**: Update OCI server
- **Hour 4**: Verify all systems operational
- **Hour 5**: Delete/archive old credentials from services

**Status: IN PROGRESS**

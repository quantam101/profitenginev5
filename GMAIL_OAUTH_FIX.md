# Gmail OAuth Configuration Fix

## Issue
`Error 401: invalid_client` — Google OAuth credentials not configured

## Root Cause
The system uses Gmail for:
- Daily digest alerts (fallback to TELEGRAM_BOT_TOKEN)
- SMTP dispatch (needs GMAIL_APP_PASSWORD)
- Alert emails (needs GMAIL_APP_PASSWORD)

But **Google OAuth for NextAuth login** is not required for core profit features.

---

## Solution: Two Options

### Option A: Disable Google OAuth (Fastest — Recommended)
If you don't need Google login, disable it in Vercel env:

**No configuration needed.** NextAuth will skip Google provider if GOOGLE_CLIENT_ID is missing.

**Verify:** Login via other methods or remove Google from auth providers.

### Option B: Enable Google OAuth (If Needed)
If you need Google login for the platform:

1. **Create OAuth App**
   - Go to https://console.cloud.google.com/apis/credentials
   - Create → OAuth 2.0 Client ID → Web application
   - Authorized redirect URIs:
     - `https://profitengine-tau.vercel.app/api/auth/callback/google`
     - `http://localhost:3000/api/auth/callback/google` (dev)
   - Copy Client ID and Client Secret

2. **Add to Vercel Production Env**
   - `GOOGLE_CLIENT_ID` = your Client ID
   - `GOOGLE_CLIENT_SECRET` = your Client Secret
   - `NEXTAUTH_SECRET` = run: `openssl rand -base64 32`
   - `NEXTAUTH_URL` = `https://profitengine-tau.vercel.app`

3. **Verify in Vercel**
   - Redeploy project
   - Test login at https://profitengine-tau.vercel.app/api/auth/signin

---

## Gmail SMTP for Alerts (Separate from OAuth)

Email alerts use **Gmail App Password** (not OAuth):

1. Enable 2FA on alreadyherellc@gmail.com
2. Generate app-specific password at myaccount.google.com/apppasswords
3. Set in GitHub Secrets / Vercel:
   - `GMAIL_APP_PASSWORD` = app password (16 chars)

4. Verify:
   ```bash
   # Test SMTP connection
   python scripts/test_gmail_smtp.py
   ```

---

## Current Status

| Feature | Status | Fix |
|---------|--------|-----|
| Google OAuth (NextAuth login) | ⚠️ NOT CONFIGURED | Option A (disable) or Option B (configure) |
| Gmail SMTP alerts | ⚠️ NEEDS APP PASSWORD | Set GMAIL_APP_PASSWORD in secrets |
| Telegram fallback | ✅ AVAILABLE | Use if Gmail not needed |
| Profit features | ✅ WORK WITHOUT OAUTH | No change needed |

---

## Recommended Action

**For immediate production:**
1. Disable Google OAuth (no action needed)
2. Use Telegram for daily digest (preferred)
3. Use Gmail SMTP only if GMAIL_APP_PASSWORD is configured

**To enable Google login:**
Follow Option B above (30 min setup)

---

## Verify Fix

After applying either option:

```bash
# Check NextAuth config
curl https://profitengine-tau.vercel.app/api/auth/signin

# Check Gmail SMTP (if configured)
python scripts/test_gmail_smtp.py

# Check Telegram fallback
python scripts/test_telegram_bot.py
```

All profit-generating features work **without** Google OAuth.

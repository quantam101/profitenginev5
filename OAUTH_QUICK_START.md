# OAuth Setup — Quick Start (15 min)

## TL;DR

Get Google OAuth working in 15 minutes by following these steps:

### 1️⃣ Create Google OAuth App (5 min)

```
https://console.cloud.google.com
→ Select Project → NEW PROJECT → "ProfitEngine V5"
→ APIs & Services → Google+ API → ENABLE
→ Credentials → CREATE CREDENTIALS → OAuth 2.0 Client ID
→ Web application
→ Authorized URIs:
   https://profitengine-tau.vercel.app/api/auth/callback/google
   http://localhost:3000/api/auth/callback/google
→ CREATE
→ Copy Client ID and Client Secret
```

### 2️⃣ Generate NEXTAUTH_SECRET (1 min)

```bash
openssl rand -base64 32
```

Copy output.

### 3️⃣ Add to Vercel (3 min)

**vercel.com** → **profitengine-tau** → **Settings** → **Environment Variables** (Production):

| Variable | Value |
|----------|-------|
| `GOOGLE_CLIENT_ID` | From step 1 |
| `GOOGLE_CLIENT_SECRET` | From step 1 |
| `NEXTAUTH_SECRET` | From step 2 |
| `NEXTAUTH_URL` | `https://profitengine-tau.vercel.app` |

Save. Vercel auto-redeploys.

### 4️⃣ Setup Gmail (5 min) [OPTIONAL]

If you want email alerts:

```
myaccount.google.com (logged in as alreadyherellc@gmail.com)
→ Security
→ 2-Step Verification (enable)
→ App passwords → Mail → Windows
→ Generate → Copy 16-char password
```

Add to Vercel + GitHub Secrets:
- `GMAIL_APP_PASSWORD` = 16-char password (no spaces)

---

## Test It

Wait 2-3 minutes for Vercel to redeploy, then:

```bash
# Test OAuth page loads
curl https://profitengine-tau.vercel.app/api/auth/signin

# Or visit in browser and click "Sign in with Google"
```

---

## That's It! 🎉

OAuth is live. Users can now log in with Google.

---

## Full Guide

For detailed steps, troubleshooting, and Telegram setup, see: **OAUTH_SETUP_COMPLETE.md**

---

## Verify Setup

After configuring, run:

```bash
bash scripts/verify-oauth.sh
```

Should show all ✅ checks passing.

---

## Need Help?

| Problem | Solution |
|---------|----------|
| "OAuth client not found" | Verify Client ID in Vercel Production env |
| Login page not showing Google button | Check NEXTAUTH_URL is correct |
| Gmail sending fails | Verify GMAIL_APP_PASSWORD and 2FA enabled |
| Need to regenerate secret | Run: `openssl rand -base64 32` and update Vercel |

---

## Security Checklist

- ✅ Never commit Client Secret to git
- ✅ Use Vercel environment variables (not hardcoded)
- ✅ Keep NEXTAUTH_SECRET private
- ✅ Rotate if ever exposed
- ✅ Use unique Gmail app password (not main Gmail password)

---

**Start here**: Go to **console.cloud.google.com** and create the project. Come back in 15 minutes with OAuth live! 🚀

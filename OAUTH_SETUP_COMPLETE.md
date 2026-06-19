# Google OAuth Complete Setup Guide

## What You'll Set Up

- **Google OAuth 2.0** — Google login for the platform
- **Gmail SMTP** — Email alerts and dispatch notifications
- **Telegram Fallback** — If Gmail fails

---

## Part 1: Google OAuth Setup (20 minutes)

### Step 1: Create Google Cloud Project

1. Go to **https://console.cloud.google.com**
2. Click **Select a Project** → **NEW PROJECT**
3. Name: `ProfitEngine V5`
4. Click **CREATE**
5. Wait for project to initialize (1-2 min)

### Step 2: Enable Google+ API

1. Search for **Google+ API** in the search bar
2. Click **Google+ API**
3. Click **ENABLE**
4. Wait for it to enable

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials** (left sidebar)
2. Click **CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
3. Choose **Web application**
4. Under **Authorized redirect URIs**, add:
   ```
   https://profitengine-tau.vercel.app/api/auth/callback/google
   https://profitengine-tau.vercel.app/api/auth/signin
   http://localhost:3000/api/auth/callback/google
   http://localhost:3000/api/auth/signin
   ```
5. Click **CREATE**
6. You'll see a popup with:
   - **Client ID** (looks like `xxx.apps.googleusercontent.com`)
   - **Client Secret** (looks like `GOCSPX-xxx`)
7. **Copy both** — you'll need them next

### Step 4: Generate NEXTAUTH_SECRET

In your terminal:
```bash
openssl rand -base64 32
```

Copy the output (should be ~44 characters)

### Step 5: Add to Vercel Production Environment

1. Go to **https://vercel.com/dashboard**
2. Select **profitengine-tau** project
3. Go to **Settings** → **Environment Variables**
4. Add these variables (set scope to **Production**):

| Variable | Value | From |
|----------|-------|------|
| `GOOGLE_CLIENT_ID` | `xxx.apps.googleusercontent.com` | Step 3 popup |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-xxx` | Step 3 popup |
| `NEXTAUTH_SECRET` | Your generated secret | Step 4 terminal |
| `NEXTAUTH_URL` | `https://profitengine-tau.vercel.app` | Fixed |

5. Click **SAVE**
6. Vercel will auto-redeploy

### Step 6: Verify OAuth Works

Wait 2-3 minutes for deployment, then:

```bash
# Test OAuth signin page loads
curl https://profitengine-tau.vercel.app/api/auth/signin

# Should show signin form with Google button
```

---

## Part 2: Gmail SMTP Setup (10 minutes)

### Step 1: Enable 2FA on Gmail

1. Go to **myaccount.google.com** (logged in as alreadyherellc@gmail.com)
2. Click **Security** (left sidebar)
3. Under **How you sign in to Google**, enable **2-Step Verification**
4. Follow the prompts (you'll need a phone)

### Step 2: Generate App Password

1. Go to **myaccount.google.com/apppasswords**
2. Select:
   - **App**: Mail
   - **Device**: Windows (or your platform)
3. Click **GENERATE**
4. Google will show a **16-character password** (like `abcd efgh ijkl mnop`)
5. **Copy it** (without spaces)

### Step 3: Add to GitHub Secrets + Vercel

**GitHub Secrets** (for CI/CD):
1. Go to **github.com/quantam101/profitenginev5**
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**
   - Name: `GMAIL_APP_PASSWORD`
   - Value: Your 16-char password (no spaces)
4. Click **Add secret**

**Vercel Environment Variable**:
1. Go to **Vercel dashboard** → **profitengine-tau**
2. **Settings** → **Environment Variables**
3. Add:
   - Name: `GMAIL_APP_PASSWORD`
   - Value: Your 16-char password
   - Scope: **Production**
4. Click **SAVE**

### Step 4: Verify SMTP Works

```bash
# In the profitenginev5 directory
python scripts/send_test_email.py
```

Check alreadyherellc@gmail.com for test email.

---

## Part 3: Telegram Fallback (Optional, 5 minutes)

If you want email alerts to fallback to Telegram if Gmail fails:

1. Message **@BotFather** on Telegram
2. Type `/newbot`
3. Follow prompts to create bot
4. Copy the **token** (looks like `123456:ABC-DEF`)
5. Send `/start` to your new bot
6. Get your **Chat ID**:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates" | jq '.result[0].message.chat.id'
   ```
7. Add to Vercel (Production):
   - `TELEGRAM_BOT_TOKEN` = your token
   - `TELEGRAM_CHAT_ID` = your chat ID

---

## Checklist

After completing all steps:

- [ ] Google Cloud Project created
- [ ] Google+ API enabled
- [ ] OAuth 2.0 credentials created
- [ ] Client ID copied
- [ ] Client Secret copied
- [ ] NEXTAUTH_SECRET generated
- [ ] All 3 env vars added to Vercel Production
- [ ] Vercel redeployed
- [ ] OAuth signin page tested
- [ ] Gmail 2FA enabled
- [ ] App password generated
- [ ] GMAIL_APP_PASSWORD added to GitHub Secrets
- [ ] GMAIL_APP_PASSWORD added to Vercel Production
- [ ] Test email sent successfully
- [ ] (Optional) Telegram bot configured

---

## Troubleshooting

### "OAuth client was not found" Error
- **Cause**: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in Vercel
- **Fix**: Add them to Vercel Production env vars and redeploy

### Gmail Login Not Working
- **Cause**: NEXTAUTH_URL doesn't match your domain
- **Fix**: Verify it's exactly `https://profitengine-tau.vercel.app`

### SMTP "Invalid credentials"
- **Cause**: GMAIL_APP_PASSWORD is wrong or has spaces
- **Fix**: Generate new password, remove all spaces, re-add to secrets

### Still Getting 401 Error
- **Cause**: Client Secret was wrong or exposed
- **Fix**: Regenerate new credentials from Google Cloud Console

---

## Cost

- **Google Cloud**: FREE (Google+ API is free)
- **Gmail SMTP**: FREE (native Gmail SMTP)
- **Telegram**: FREE (native bot API)

Total cost: **$0**

---

## Security Notes

1. **Never commit secrets** — always use environment variables
2. **Rotate Client Secret** if it's ever exposed
3. **Gmail App Password** is unique to this app — if leaked, just regenerate
4. **NEXTAUTH_SECRET** should be random and 32+ characters

---

## Test Everything

```bash
# 1. Test OAuth page
curl https://profitengine-tau.vercel.app/api/auth/signin

# 2. Test health endpoint
curl https://profitengine-tau.vercel.app/api/health

# 3. Test profit API
curl https://profitengine-tau.vercel.app/api/profitability

# All should return 200 with valid data
```

---

## Next Steps

After OAuth is live:
1. Test login with Google account
2. Verify email alerts send
3. Test Telegram fallback
4. Verify revenue dashboard loads
5. Check all profit features operational

Then you're ready for production! 🚀

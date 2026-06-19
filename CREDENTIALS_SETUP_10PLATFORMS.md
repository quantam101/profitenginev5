# Setup Credentials for 10 Platforms (Excluding Medium)

**Total Setup Time**: ~2 hours  
**Platforms**: Twitter, Reddit, LinkedIn, Facebook, Instagram, TikTok, Etsy, Gumroad, Printify + YouTube (already configured)

---

## Quick Reference — What You Need

### Social Media (7 platforms)
- **Twitter/X**: 4 credentials (5 min)
- **Reddit**: 4 credentials (5 min)
- **LinkedIn**: 2 credentials (5 min)
- **Facebook**: 2 credentials (5 min)
- **Instagram**: 1 credential (reuses Facebook token, 5 min)
- **TikTok**: 1 credential (5 min)
- **YouTube**: ✅ Already configured

### E-Commerce (3 platforms)
- **Etsy**: 2 credentials (15 min)
- **Gumroad**: 1 credential to complete setup (5 min)
- **Printify**: 2 credentials (15 min)

---

## Setup Instructions (One Platform at a Time)

### 1. TWITTER/X (5 minutes)

**Where to Get Credentials:**
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Sign in or create account
3. Create a new app (if you haven't already)
4. Go to Keys and Tokens tab

**What You Need:**
- `TWITTER_API_KEY` — Listed as "API Key" (also called Consumer Key)
- `TWITTER_API_SECRET` — Listed as "API Secret Key" (also called Consumer Secret)
- `TWITTER_ACCESS_TOKEN` — Click "Generate" under "Access Token & Secret"
- `TWITTER_ACCESS_SECRET` — Listed as "Access Token Secret"

**Important**: Make sure your app has "Read and Write" permissions for tweets.

**Add to GitHub Secrets:**
```
gh secret set TWITTER_API_KEY --body 'YOUR_API_KEY_HERE'
gh secret set TWITTER_API_SECRET --body 'YOUR_API_SECRET_HERE'
gh secret set TWITTER_ACCESS_TOKEN --body 'YOUR_ACCESS_TOKEN_HERE'
gh secret set TWITTER_ACCESS_SECRET --body 'YOUR_ACCESS_SECRET_HERE'
```

---

### 2. REDDIT (5 minutes)

**Where to Get Credentials:**
1. Go to https://www.reddit.com/prefs/apps
2. Scroll to "Developed Applications" section
3. Click "Create app" (or "Create another app")
4. Fill in:
   - Name: `ProfitEngine Content Publisher`
   - Type: `script`
   - Redirect URI: `http://localhost:8000`
5. Click "Create app"

**What You Need:**
- `REDDIT_CLIENT_ID` — Under the app name in the "script" section
- `REDDIT_CLIENT_SECRET` — Labeled "secret" under your app
- `REDDIT_USERNAME` — Your Reddit account username
- `REDDIT_PASSWORD` — Your Reddit account password

**Add to GitHub Secrets:**
```
gh secret set REDDIT_CLIENT_ID --body 'YOUR_CLIENT_ID_HERE'
gh secret set REDDIT_CLIENT_SECRET --body 'YOUR_CLIENT_SECRET_HERE'
gh secret set REDDIT_USERNAME --body 'YOUR_REDDIT_USERNAME'
gh secret set REDDIT_PASSWORD --body 'YOUR_REDDIT_PASSWORD'
```

**Note**: Also set the subreddit:
```
gh secret set REDDIT_SUBREDDIT --body 'alreadyhere'
```
(Replace with your actual subreddit)

---

### 3. LINKEDIN (5 minutes)

**Where to Get Credentials:**
1. Go to https://www.linkedin.com/developers/apps
2. Click "Create app"
3. Fill in:
   - App name: `ProfitEngine Content`
   - LinkedIn Page: (select your business page)
   - App logo: (upload any image)
4. Accept terms and create
5. Go to "Auth" tab after creation

**What You Need:**
- `LINKEDIN_ACCESS_TOKEN` — Click "Request access token" under "Verify with OAuth 2.0"
  - Scopes needed: `w_member_social`, `r_liteprofile`
  - Copy the token value
- `LINKEDIN_PERSON_URN` — Format: `urn:li:person:XXXXXXXXX`
  - Get your person ID from LinkedIn profile URL or API call

**Quick way to get Person URN:**
```
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/me
```
Look for the `id` field in the response, format as `urn:li:person:{id}`

**Add to GitHub Secrets:**
```
gh secret set LINKEDIN_ACCESS_TOKEN --body 'YOUR_ACCESS_TOKEN_HERE'
gh secret set LINKEDIN_PERSON_URN --body 'urn:li:person:XXXXXXXXX'
```

---

### 4. FACEBOOK (5 minutes)

**Where to Get Credentials:**
1. Go to https://developers.facebook.com/
2. Sign in or create developer account
3. Create a new app (type: Business)
4. Go to Settings → Basic to get App ID/Secret
5. Add Facebook Pages product to your app
6. Go to Pages section

**What You Need:**
- `FB_PAGE_ID` — Your Facebook Page ID (numeric)
  - Find at: https://www.facebook.com/YOUR_PAGE → About → Look for "Page ID"
  - Or use: https://findmyfbid.com/
- `FB_PAGE_ACCESS_TOKEN` — Long-lived page token
  - In Facebook Developer Console: Tools → Graph API Explorer
  - Get User Access Token (check `pages_manage_posts` permission)
  - Then get Page Access Token using `/me/accounts`

**Add to GitHub Secrets:**
```
gh secret set FB_PAGE_ID --body 'YOUR_PAGE_ID_HERE'
gh secret set FB_PAGE_ACCESS_TOKEN --body 'YOUR_PAGE_ACCESS_TOKEN_HERE'
```

---

### 5. INSTAGRAM (5 minutes)

**Requirements**: Business or Creator account on Instagram connected to your Facebook Page

**What You Need:**
- `IG_USER_ID` — Your Instagram Business Account ID
  - In Facebook Developer Console: Graph API Explorer
  - Run: `GET /me/instagram_business_accounts`
  - Copy the `id` field
- `FB_PAGE_ACCESS_TOKEN` — Same token from Facebook setup above

**Add to GitHub Secrets:**
```
gh secret set IG_USER_ID --body 'YOUR_IG_USER_ID_HERE'
```
(FB_PAGE_ACCESS_TOKEN already set from Facebook)

---

### 6. TIKTOK (5 minutes)

**Where to Get Credentials:**
1. Go to https://www.tiktok.com/creators (sign in as creator)
2. Go to Creator Studio → Tools → Developer Tools
3. Create a TikTok app in TikTok Developer Portal
4. Request API access

**What You Need:**
- `TIKTOK_ACCESS_TOKEN` — OAuth 2.0 access token
  - Get from TikTok OAuth 2.0 flow
  - Scopes needed: `video.upload`, `video.publish`

**Add to GitHub Secrets:**
```
gh secret set TIKTOK_ACCESS_TOKEN --body 'YOUR_ACCESS_TOKEN_HERE'
```

---

### 7. ETSY (15 minutes)

**Where to Get Credentials:**
1. Go to https://www.etsy.com/developers/your-apps
2. Create new app:
   - App name: `ProfitEngine`
   - Keystring: `profitengine`
3. Accept terms
4. You'll get API Key immediately

**What You Need:**
- `ETSY_SHOP_ID` — Your Etsy shop ID (numeric)
  - Find at: https://www.etsy.com/your/settings/account
  - Or via API: `GET /v3/application/shops`
- `ETSY_API_KEY` — Shown in your app credentials

**Add to GitHub Secrets:**
```
gh secret set ETSY_SHOP_ID --body 'YOUR_SHOP_ID_HERE'
gh secret set ETSY_API_KEY --body 'YOUR_API_KEY_HERE'
```

---

### 8. GUMROAD (5 minutes — Complete Partial Setup)

**Current Status**: You have `GUMROAD_API_TOKEN` but missing `GUMROAD_CREATOR_ID`

**Where to Get It:**
1. Go to https://app.gumroad.com/creator/settings/security
2. Your creator ID is visible at the top of the page
3. Or in URL: https://app.gumroad.com/@{YOUR_CREATOR_ID}

**What You Need:**
- `GUMROAD_CREATOR_ID` — Your Gumroad creator username/ID

**Add to GitHub Secrets:**
```
gh secret set GUMROAD_CREATOR_ID --body 'YOUR_CREATOR_ID_HERE'
```

---

### 9. PRINTIFY (15 minutes)

**Where to Get Credentials:**
1. Go to https://printify.com/user/account
2. Sign in or create account
3. Go to API Access section
4. Generate API Token

**What You Need:**
- `PRINTIFY_API_KEY` — OAuth token from API section
- `PRINTIFY_SHOP_ID` — Your shop ID
  - Find in Dashboard or via API: `GET /v1/shops.json`

**Add to GitHub Secrets:**
```
gh secret set PRINTIFY_API_KEY --body 'YOUR_API_KEY_HERE'
gh secret set PRINTIFY_SHOP_ID --body 'YOUR_SHOP_ID_HERE'
```

---

### 10. YOUTUBE (✅ Already Configured)

Your .env file already has:
- `YOUTUBE_CLIENT_ID` ✅
- `YOUTUBE_CLIENT_SECRET` ✅
- `YOUTUBE_REFRESH_TOKEN` ✅

These are already in GitHub? If not, add them:
```
gh secret set YOUTUBE_CLIENT_ID --body 'YOUR_CLIENT_ID_HERE'
gh secret set YOUTUBE_CLIENT_SECRET --body 'YOUR_CLIENT_SECRET_HERE'
gh secret set YOUTUBE_REFRESH_TOKEN --body 'YOUR_REFRESH_TOKEN_HERE'
```

---

## All GitHub Secrets Commands (Copy-Paste)

Once you have all credentials, run these commands:

```bash
# Twitter
gh secret set TWITTER_API_KEY --body 'YOUR_VALUE'
gh secret set TWITTER_API_SECRET --body 'YOUR_VALUE'
gh secret set TWITTER_ACCESS_TOKEN --body 'YOUR_VALUE'
gh secret set TWITTER_ACCESS_SECRET --body 'YOUR_VALUE'

# Reddit
gh secret set REDDIT_CLIENT_ID --body 'YOUR_VALUE'
gh secret set REDDIT_CLIENT_SECRET --body 'YOUR_VALUE'
gh secret set REDDIT_USERNAME --body 'YOUR_VALUE'
gh secret set REDDIT_PASSWORD --body 'YOUR_VALUE'
gh secret set REDDIT_SUBREDDIT --body 'YOUR_VALUE'

# LinkedIn
gh secret set LINKEDIN_ACCESS_TOKEN --body 'YOUR_VALUE'
gh secret set LINKEDIN_PERSON_URN --body 'YOUR_VALUE'

# Facebook & Instagram
gh secret set FB_PAGE_ID --body 'YOUR_VALUE'
gh secret set FB_PAGE_ACCESS_TOKEN --body 'YOUR_VALUE'
gh secret set IG_USER_ID --body 'YOUR_VALUE'

# TikTok
gh secret set TIKTOK_ACCESS_TOKEN --body 'YOUR_VALUE'

# Etsy
gh secret set ETSY_SHOP_ID --body 'YOUR_VALUE'
gh secret set ETSY_API_KEY --body 'YOUR_VALUE'

# Gumroad (Complete)
gh secret set GUMROAD_CREATOR_ID --body 'YOUR_VALUE'

# Printify
gh secret set PRINTIFY_API_KEY --body 'YOUR_VALUE'
gh secret set PRINTIFY_SHOP_ID --body 'YOUR_VALUE'

# YouTube (if not already set)
gh secret set YOUTUBE_CLIENT_ID --body 'YOUR_VALUE'
gh secret set YOUTUBE_CLIENT_SECRET --body 'YOUR_VALUE'
gh secret set YOUTUBE_REFRESH_TOKEN --body 'YOUR_VALUE'
```

---

## Verification After Setup

Once you've added all secrets, verify they're configured:

```bash
# Run verification
python scripts/test_distribution.py --check-only
```

Expected output:
```
Twitter/X          CONFIGURED (4/4)
Reddit             CONFIGURED (5/5)
LinkedIn           CONFIGURED (2/2)
Facebook           CONFIGURED (2/2)
Instagram          CONFIGURED (2/2)
TikTok             CONFIGURED (1/1)
Etsy               CONFIGURED (2/2)
Gumroad            CONFIGURED (1/1)
Printify           CONFIGURED (2/2)
YouTube            CONFIGURED (3/3)

Ready: 10/10 platforms
```

---

## What Happens After Setup

1. **Automatic Publishing**: Every article will be distributed to all 10 platforms
2. **Distribution Report**: After each publish, you'll get a JSON report showing:
   - Which platforms succeeded
   - Which platforms failed (with error)
   - URLs for each platform's published post
3. **No Manual Work**: Everything runs automatically on schedule (07:05 & 15:05 UTC daily)

---

## Rollback If Needed

If you want to disable a platform:
```bash
gh secret delete TWITTER_API_KEY
# Platform automatically skips if any credential missing
```

---

## Status: Ready to Configure

All 10 platforms are implemented and waiting for credentials. Expected completion: ~2 hours for all setups.

**Next Step**: Pick a platform above and start with the setup. Each one is independent.

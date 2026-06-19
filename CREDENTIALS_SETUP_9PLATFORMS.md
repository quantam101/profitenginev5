# Setup Credentials for 9 Platforms (Excluding Twitter & Medium)

**Total Setup Time**: ~1.5 hours  
**Platforms**: Reddit, LinkedIn, Facebook, Instagram, TikTok, Etsy, Gumroad, Printify + YouTube (already configured)

---

## 1. REDDIT (5 minutes)

**Where to Get Credentials:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create app" (or "Create another app")
3. Fill in:
   - Name: `ProfitEngine Content Publisher`
   - Type: `script`
   - Redirect URI: `http://localhost:8000`
4. Click "Create app"

**What You Need:**
- `REDDIT_CLIENT_ID` — Under the app name
- `REDDIT_CLIENT_SECRET` — Labeled "secret"
- `REDDIT_USERNAME` — Your Reddit username
- `REDDIT_PASSWORD` — Your Reddit password
- `REDDIT_SUBREDDIT` — Target subreddit

**Add to GitHub Secrets:**
```bash
gh secret set REDDIT_CLIENT_ID --body 'YOUR_VALUE'
gh secret set REDDIT_CLIENT_SECRET --body 'YOUR_VALUE'
gh secret set REDDIT_USERNAME --body 'YOUR_VALUE'
gh secret set REDDIT_PASSWORD --body 'YOUR_VALUE'
gh secret set REDDIT_SUBREDDIT --body 'alreadyhere'
```

---

## 2. LINKEDIN (5 minutes)

**Where to Get Credentials:**
1. Go to https://www.linkedin.com/developers/apps
2. Click "Create app"
3. Fill in app name and select your business page
4. Accept terms and create
5. Go to "Auth" tab

**What You Need:**
- `LINKEDIN_ACCESS_TOKEN` — OAuth 2.0 access token with `w_member_social` scope
- `LINKEDIN_PERSON_URN` — Format: `urn:li:person:XXXXXXXXX`

**Add to GitHub Secrets:**
```bash
gh secret set LINKEDIN_ACCESS_TOKEN --body 'YOUR_VALUE'
gh secret set LINKEDIN_PERSON_URN --body 'urn:li:person:XXXXXXXXX'
```

---

## 3. FACEBOOK (5 minutes)

**Where to Get Credentials:**
1. Go to https://developers.facebook.com/
2. Create new app (Type: Business)
3. Add "Facebook Pages" product
4. Get credentials from Settings → Basic

**What You Need:**
- `FB_PAGE_ID` — Your Facebook Page ID (numeric)
  - Find at: https://www.facebook.com/YOUR_PAGE or https://findmyfbid.com/
- `FB_PAGE_ACCESS_TOKEN` — Long-lived page access token
  - Get from Graph API Explorer with `pages_manage_posts` permission

**Add to GitHub Secrets:**
```bash
gh secret set FB_PAGE_ID --body 'YOUR_PAGE_ID'
gh secret set FB_PAGE_ACCESS_TOKEN --body 'YOUR_PAGE_TOKEN'
```

---

## 4. INSTAGRAM (5 minutes)

**Requirements**: Business or Creator account connected to your Facebook Page

**What You Need:**
- `IG_USER_ID` — Your Instagram Business Account ID
  - Get from Facebook Developer Console: Graph API Explorer → GET /me/instagram_business_accounts
- `FB_PAGE_ACCESS_TOKEN` — Same token from Facebook setup above (reused)

**Add to GitHub Secrets:**
```bash
gh secret set IG_USER_ID --body 'YOUR_IG_USER_ID'
# FB_PAGE_ACCESS_TOKEN already set from Facebook
```

---

## 5. TIKTOK (5 minutes)

**Where to Get Credentials:**
1. Go to https://www.tiktok.com/creators
2. Creator Studio → Tools → Developer Tools
3. Create app and request API access

**What You Need:**
- `TIKTOK_ACCESS_TOKEN` — OAuth 2.0 access token
  - Scopes: `video.upload`, `video.publish`

**Add to GitHub Secrets:**
```bash
gh secret set TIKTOK_ACCESS_TOKEN --body 'YOUR_VALUE'
```

---

## 6. ETSY (15 minutes)

**Where to Get Credentials:**
1. Go to https://www.etsy.com/developers/your-apps
2. Create new app
3. Copy API Key

**What You Need:**
- `ETSY_SHOP_ID` — Your Etsy shop ID (numeric)
  - Find at: https://www.etsy.com/your/settings/account
- `ETSY_API_KEY` — Your API key

**Add to GitHub Secrets:**
```bash
gh secret set ETSY_SHOP_ID --body 'YOUR_SHOP_ID'
gh secret set ETSY_API_KEY --body 'YOUR_API_KEY'
```

---

## 7. GUMROAD (5 minutes - Complete Partial Setup)

**Current Status**: You have `GUMROAD_API_TOKEN` but missing `GUMROAD_CREATOR_ID`

**Where to Get It:**
1. Go to https://app.gumroad.com/creator/settings/security
2. Your creator ID is visible

**What You Need:**
- `GUMROAD_CREATOR_ID` — Your Gumroad creator ID/username

**Add to GitHub Secrets:**
```bash
gh secret set GUMROAD_CREATOR_ID --body 'your_creator_id'
```

---

## 8. PRINTIFY (15 minutes)

**Where to Get Credentials:**
1. Go to https://printify.com/user/account
2. Go to API Access section
3. Generate API Token

**What You Need:**
- `PRINTIFY_API_KEY` — Your API key
- `PRINTIFY_SHOP_ID` — Your shop ID

**Add to GitHub Secrets:**
```bash
gh secret set PRINTIFY_API_KEY --body 'YOUR_API_KEY'
gh secret set PRINTIFY_SHOP_ID --body 'YOUR_SHOP_ID'
```

---

## 9. YOUTUBE (✅ Already Configured)

Your .env file has all 3 credentials:
- `YOUTUBE_CLIENT_ID` ✅
- `YOUTUBE_CLIENT_SECRET` ✅
- `YOUTUBE_REFRESH_TOKEN` ✅

If needed, add to GitHub Secrets:
```bash
gh secret set YOUTUBE_CLIENT_ID --body 'YOUR_VALUE'
gh secret set YOUTUBE_CLIENT_SECRET --body 'YOUR_VALUE'
gh secret set YOUTUBE_REFRESH_TOKEN --body 'YOUR_VALUE'
```

---

## Quick Reference — All Commands

```bash
# Reddit
gh secret set REDDIT_CLIENT_ID --body 'VALUE'
gh secret set REDDIT_CLIENT_SECRET --body 'VALUE'
gh secret set REDDIT_USERNAME --body 'VALUE'
gh secret set REDDIT_PASSWORD --body 'VALUE'
gh secret set REDDIT_SUBREDDIT --body 'alreadyhere'

# LinkedIn
gh secret set LINKEDIN_ACCESS_TOKEN --body 'VALUE'
gh secret set LINKEDIN_PERSON_URN --body 'VALUE'

# Facebook & Instagram
gh secret set FB_PAGE_ID --body 'VALUE'
gh secret set FB_PAGE_ACCESS_TOKEN --body 'VALUE'
gh secret set IG_USER_ID --body 'VALUE'

# TikTok
gh secret set TIKTOK_ACCESS_TOKEN --body 'VALUE'

# Etsy
gh secret set ETSY_SHOP_ID --body 'VALUE'
gh secret set ETSY_API_KEY --body 'VALUE'

# Gumroad
gh secret set GUMROAD_CREATOR_ID --body 'VALUE'

# Printify
gh secret set PRINTIFY_API_KEY --body 'VALUE'
gh secret set PRINTIFY_SHOP_ID --body 'VALUE'
```

---

## Verification

After adding all secrets:

```bash
python scripts/test_distribution.py --check-only
```

Expected: All 9 platforms show CONFIGURED

---

## Status: Ready to Begin

All 9 platforms implemented. Expected time: ~1.5 hours total.

**Start with**: Reddit (Section 1, 5 minutes)

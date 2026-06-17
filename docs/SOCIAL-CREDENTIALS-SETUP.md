# SOCIAL MEDIA CREDENTIALS SETUP
## Complete Guide to Getting All API Tokens

---

## 1. TIKTOK

### Get TikTok Access Token

**URL**: https://developers.tiktok.com/

**Steps**:
1. Sign in with your TikTok business account
2. Click "Create an app"
3. Select "Web" as the app type
4. Fill in app details (Already Here LLC)
5. Agree to terms, submit
6. In app settings, find "Client Key" (save this)
7. Generate "Client Secret" (save this)
8. In "Scopes", enable:
   - `video.upload` (write video)
   - `user.info.basic` (read profile)
9. Set redirect URL: `https://profitengine-tau.vercel.app/callback/tiktok`
10. Generate token via OAuth flow

**What you get**:
```
TIKTOK_ACCESS_TOKEN=your_token_here
TIKTOK_BUSINESS_ACCOUNT_ID=your_account_id
```

**How to use**: After OAuth, refresh token if needed via `/api/auth/tiktok/refresh`

---

## 2. INSTAGRAM (Meta/Facebook)

### Get Instagram Access Token

**URL**: https://developers.facebook.com/

**Steps**:
1. Go to Meta for Developers
2. Create new app (Business type)
3. Add "Instagram Graph API" product
4. In Settings → Basic, get your **App ID** and **App Secret**
5. Go to Tools → Graph Explorer
6. Select your app from top-left dropdown
7. Click "Get Token" → "Get User Access Token"
8. Select scopes:
   - `instagram_basic`
   - `instagram_content_publish`
9. Generate token (valid for 60 days)
10. For long-lived token (good for 60 days), exchange via API endpoint

**What you get**:
```
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id (find in Business Suite)
```

**How to find Business Account ID**:
- Go to Instagram Business Suite (business.instagram.com)
- Settings → Account → Copy "Instagram Account ID"

---

## 3. YOUTUBE

### Get YouTube Access Token

**URL**: https://console.cloud.google.com/

**Steps**:
1. Create a new project (or use existing)
2. Enable "YouTube Data API v3"
3. Create OAuth 2.0 credential (Desktop app or Web app)
4. Download JSON credential file
5. In your app settings, add redirect URI:
   - `https://profitengine-tau.vercel.app/callback/youtube`
6. Generate access token via OAuth flow
7. Get your Channel ID:
   - Go to youtube.com (logged in)
   - Settings → Advanced settings → Copy "Channel ID"

**What you get**:
```
YOUTUBE_ACCESS_TOKEN=your_token_here
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxx (your channel ID)
```

**Test token validity**:
```bash
curl "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true&access_token=YOUR_TOKEN"
```

---

## 4. TWITTER / X

### Get Twitter API Credentials

**URL**: https://developer.twitter.com/

**Steps**:
1. Sign in with your Twitter account
2. Apply for API access (if not already approved)
3. Create a new project in Dashboard
4. Create an App within the project
5. Go to "Keys and tokens" tab
6. Generate "API Key" (keep this secret)
7. Generate "API Key Secret" (keep this secret)
8. Generate "Access Token" and "Access Token Secret"
9. In App Settings, enable "Read and Write" permissions
10. Set callback URL: `https://profitengine-tau.vercel.app/callback/twitter`

**What you get**:
```
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

**Note**: Use API v2 (latest) - upgrade from v1.1 if needed

---

## 5. LINKEDIN

### Get LinkedIn Access Token

**URL**: https://www.linkedin.com/developers/

**Steps**:
1. Sign in with your LinkedIn account
2. Go to "My apps"
3. Create new app
4. Fill in company (Already Here LLC) and required fields
5. Request access to "Sign In with LinkedIn" product
6. Go to "Auth" tab
7. Add Authorized redirect URL:
   - `https://profitengine-tau.vercel.app/callback/linkedin`
8. Generate access token via OAuth flow
9. Find your Person URN:
   - After OAuth, call: `https://api.linkedin.com/v2/me`
   - Response includes `id` (this is your Person URN)

**What you get**:
```
LINKEDIN_ACCESS_TOKEN=your_token_here
LINKEDIN_PERSON_URN=urn:li:person:xxxxxxxxxxxxx
```

---

## 6. CONVERTKIT

### Get ConvertKit API Credentials

**URL**: https://app.convertkit.com/account/edit

**Steps**:
1. Log in to ConvertKit
2. Go to Account → API
3. Copy your **API Key** (public)
4. Copy your **API Secret** (keep this secret!)
5. You now have both credentials

**What you get**:
```
CONVERTKIT_API_KEY=your_api_key
CONVERTKIT_API_SECRET=your_api_secret
```

**Test credentials**:
```bash
curl "https://api.convertkit.com/v3/creator/profile?api_secret=YOUR_SECRET"
```

---

## HOW TO STORE CREDENTIALS

### Option 1: GitHub Secrets (Production)

1. Go to your GitHub repo: https://github.com/quantam101/profitenginev5
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each credential:
   - `TIKTOK_ACCESS_TOKEN`
   - `INSTAGRAM_ACCESS_TOKEN`
   - `YOUTUBE_ACCESS_TOKEN`
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET`
   - `TWITTER_ACCESS_TOKEN`
   - `TWITTER_ACCESS_TOKEN_SECRET`
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_PERSON_URN`
   - `CONVERTKIT_API_KEY`
   - `CONVERTKIT_API_SECRET`

4. GitHub Actions automatically injects these into Vercel deployment

### Option 2: Vercel Environment Variables (Also Production)

1. Go to Vercel dashboard
2. Select "profitenginev5" project
3. Settings → Environment Variables
4. Add each credential with values
5. Choose which environments (Production/Preview/Development)
6. Recommended: Production only for sensitive tokens

### Option 3: Local `.env` (Development Only)

Create `.env.local` in project root:
```bash
TIKTOK_ACCESS_TOKEN=your_token
INSTAGRAM_ACCESS_TOKEN=your_token
YOUTUBE_ACCESS_TOKEN=your_token
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_secret
LINKEDIN_ACCESS_TOKEN=your_token
LINKEDIN_PERSON_URN=your_urn
CONVERTKIT_API_KEY=your_key
CONVERTKIT_API_SECRET=your_secret
```

⚠️  **NEVER commit `.env` to GitHub** - use `.env.example` template instead

---

## TOKEN EXPIRATION & REFRESH

| Platform | Expiration | Refresh Method |
|----------|-----------|-----------------|
| TikTok | 30 days | OAuth refresh endpoint |
| Instagram | 60 days | Exchange for long-lived (60 days) |
| YouTube | 60 min | Refresh token (persistent) |
| Twitter | No expiry | Permanent (unless revoked) |
| LinkedIn | No expiry | Permanent (unless revoked) |
| ConvertKit | No expiry | Permanent (unless revoked) |

**Pro tip**: Set calendar reminders for token rotation (30-60 days)

---

## TESTING EACH CREDENTIAL

### TikTok
```bash
curl "https://open.tiktokapis.com/v1/user/info/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Instagram
```bash
curl "https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN"
```

### YouTube
```bash
curl "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true&access_token=YOUR_TOKEN"
```

### Twitter
```bash
curl "https://api.twitter.com/2/tweets/search/recent?query=from:YOUR_USERNAME&max_results=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### LinkedIn
```bash
curl "https://api.linkedin.com/v2/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### ConvertKit
```bash
curl "https://api.convertkit.com/v3/creator/profile?api_secret=YOUR_SECRET"
```

---

## CHECKLIST: READY TO LAUNCH?

- [ ] TikTok token obtained and tested
- [ ] Instagram token obtained and tested
- [ ] YouTube token obtained and tested
- [ ] Twitter credentials obtained and tested
- [ ] LinkedIn token obtained and tested
- [ ] ConvertKit credentials obtained and tested
- [ ] All 10+ credentials stored in GitHub Secrets
- [ ] All credentials also in Vercel Environment Variables
- [ ] `.env.local` created for local development
- [ ] Token rotation calendar reminders set

**Once complete**: Run automation again
```bash
python scripts/faceless-marketing-automation.py
```

Real posts will now go live to all 5 platforms.

---

## TROUBLESHOOTING

**"Invalid token" error**
→ Token expired or incorrect format. Regenerate.

**"Insufficient permissions"**
→ Scope not enabled. Go back to app settings and enable required scopes.

**"Redirect URL mismatch"**
→ Add exact redirect URL to app settings:
  `https://profitengine-tau.vercel.app/callback/[platform]`

**"Rate limit exceeded"**
→ Wait 15 minutes and try again. Each platform has limits:
  - TikTok: 100 requests/hour
  - Instagram: 200 requests/hour
  - YouTube: 10K requests/day
  - Twitter: 450 requests/15 min
  - LinkedIn: 100 calls/day
  - ConvertKit: 1,000 calls/hour

---

## NEXT: CONFIGURE AND TEST

Ready? Let's set these up:

1. Collect all 6 credentials (TikTok, Instagram, YouTube, Twitter, LinkedIn, ConvertKit)
2. Store in GitHub Secrets + Vercel
3. Test each endpoint
4. Run automation with real credentials
5. Watch real posts go live

GO TIME.

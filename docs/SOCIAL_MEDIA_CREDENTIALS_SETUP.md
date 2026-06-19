# Social Media Publishing Credentials Setup

Production-ready OAuth 2.0 integrations for multi-platform content distribution.

**All credentials must be rotated quarterly and immediately upon any team member departure.**

## Quick Start

### 1. Environment Variables (Copy to OCI `.env`)

```bash
# Twitter/X OAuth 2.0
TWITTER_API_KEY=abc123...
TWITTER_API_SECRET=xyz789...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
TWITTER_BEARER_TOKEN=AAAAABBBBBcc...  # Preferred

# Reddit OAuth 2.0
REDDIT_CLIENT_ID=abc123...
REDDIT_CLIENT_SECRET=xyz789...
REDDIT_USERNAME=profitengine_bot
REDDIT_PASSWORD=...
REDDIT_SUBREDDIT=investing

# LinkedIn OAuth 2.0
LINKEDIN_ACCESS_TOKEN=AQE...
LINKEDIN_PERSON_URN=urn:li:person:123456
LINKEDIN_ORGANIZATION_URN=urn:li:organization:12345

# Facebook Graph API
FB_PAGE_ID=123456789
FB_PAGE_ACCESS_TOKEN=EAAC...

# Instagram Graph API (business account)
IG_USER_ID=123456789
# Reuse FB_PAGE_ACCESS_TOKEN with instagram_content_publish permission

# TikTok OAuth 2.0
TIKTOK_ACCESS_TOKEN=act_...
TIKTOK_OPEN_ID=ot...

# YouTube OAuth 2.0
YOUTUBE_CLIENT_ID=abc123...apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xyz789...
YOUTUBE_REFRESH_TOKEN=1//...
```

### 2. GitHub Secrets (for CI/CD)

1. Go to: https://github.com/quantam101/profitenginev5/settings/secrets/actions
2. Create secrets for each platform (paste same values as OCI `.env`)
3. Required for automated deployment workflows

### 3. Vercel Environment Variables (if frontend publishing needed)

1. Go to: https://vercel.com/quantam101/profitengine-tau/settings/environment-variables
2. Only set secrets if Next.js frontend directly calls publishing APIs
3. Most publishing should happen on OCI backend only

## Detailed Setup Per Platform

---

## Twitter/X (OAuth 2.0 v2)

### Prerequisites
- Twitter/X Developer account
- App with Read/Write permissions
- Either OAuth 1.0a (legacy) or OAuth 2.0 (preferred)

### Setup Steps

#### Option A: OAuth 2.0 Bearer Token (Recommended)

1. **Create Developer Account**
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Elevate to Elevated access tier (required for v2 API write)

2. **Create App**
   - Portal → Projects & Apps → Create App
   - Name: `ProfitEngine Production`
   - App Purpose: `Publishing Bot`
   - Description: `Automated content distribution for profitengine.alreadyherellc.com`

3. **Generate Bearer Token**
   - App Settings → Keys and tokens → Bearer Token
   - Copy to `TWITTER_BEARER_TOKEN`

4. **Test**
   ```bash
   curl -X POST https://api.twitter.com/2/tweets \
     -H "Authorization: Bearer $TWITTER_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"text":"Testing OAuth 2.0"}'
   ```

#### Option B: OAuth 1.0a (User Context)

If Bearer Token not available, use user-context OAuth 1.0a:

1. **Generate Keys**
   - App Settings → Keys and tokens → API Key (API_KEY)
   - API Secret (API_SECRET)
   - Access Token (ACCESS_TOKEN)
   - Access Token Secret (ACCESS_SECRET)

2. **Environment Variables**
   ```bash
   TWITTER_API_KEY=...
   TWITTER_API_SECRET=...
   TWITTER_ACCESS_TOKEN=...
   TWITTER_ACCESS_SECRET=...
   ```

### Rotation Schedule
- **Quarterly**: Regenerate all tokens
- **Immediate**: After team member departure
- **Log all**: Check API usage logs for suspicious activity

---

## Reddit (OAuth 2.0)

### Prerequisites
- Reddit account (for bot/service account)
- Reddit app registration
- Target subreddit with posting permissions

### Setup Steps

1. **Create Service Account**
   - Register new Reddit account: https://reddit.com/register
   - Username: `profitengine_bot`
   - Email: Use dispatch@alreadyherellc.com or service account email
   - Password: Generate strong password and store securely

2. **Register App**
   - Log in to service account
   - Go to: https://www.reddit.com/prefs/apps
   - Create new app → Select **"script"** (not web app or mobile)
   - Name: `ProfitEngine Content Distribution`
   - Redirect URI: `http://localhost:8080` (not used for script apps)
   - Copy: **Client ID** and **Client Secret**

3. **Grant Posting Permissions**
   - Join target subreddit (e.g., r/investing)
   - Add bot as moderator (if own subreddit) or ensure posting rights

4. **Environment Variables**
   ```bash
   REDDIT_CLIENT_ID=abc123...
   REDDIT_CLIENT_SECRET=xyz789...
   REDDIT_USERNAME=profitengine_bot
   REDDIT_PASSWORD=...
   REDDIT_SUBREDDIT=investing
   ```

5. **Test**
   ```bash
   python3 -c "
   import praw
   reddit = praw.Reddit(
       client_id='$REDDIT_CLIENT_ID',
       client_secret='$REDDIT_CLIENT_SECRET',
       user_agent='ProfitEngine:1.0',
       username='$REDDIT_USERNAME',
       password='$REDDIT_PASSWORD'
   )
   print('Auth OK:', reddit.user.me())
   "
   ```

### Rotation Schedule
- **Quarterly**: Regenerate Client ID + Secret via app settings
- **Immediate**: If service account compromised
- **Note**: Username/password should be stored securely; consider regenerating service account

---

## LinkedIn (OAuth 2.0)

### Prerequisites
- LinkedIn account (personal or company)
- LinkedIn app in developer console
- OAuth 2.0 scopes: `r_basicprofile`, `w_member_social`

### Setup Steps

#### For Personal Profile Posts

1. **Create LinkedIn App**
   - Go to: https://www.linkedin.com/developers/apps
   - Create new app
   - App name: `ProfitEngine Publishing`
   - LinkedIn organization: Already Here LLC (if applicable)

2. **Authorize App**
   - App Settings → Authorized users → Add user
   - Sign in with account that will post content

3. **Generate Access Token**
   - Via OAuth 2.0 Authorization Code flow:
   ```bash
   # 1. Redirect user to:
   https://www.linkedin.com/oauth/v2/authorization?
     client_id=$LINKEDIN_APP_ID&
     redirect_uri=http://localhost:8080/callback&
     response_type=code&
     scope=r_basicprofile,w_member_social

   # 2. Exchange code for access token:
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code&
         code=$AUTH_CODE&
         redirect_uri=http://localhost:8080/callback&
         client_id=$LINKEDIN_APP_ID&
         client_secret=$LINKEDIN_APP_SECRET"
   ```

4. **Get Person URN**
   ```bash
   curl -X GET https://api.linkedin.com/v2/me \
     -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" | jq '.id'
   # Extract from response: "urn:li:person:123456789"
   ```

5. **Environment Variables**
   ```bash
   LINKEDIN_ACCESS_TOKEN=AQE...
   LINKEDIN_PERSON_URN=urn:li:person:123456789
   ```

#### For Company Page Posts (Alternative)

1. Follow same app creation steps
2. Request **Sign In with LinkedIn** (user context) + **Share on LinkedIn** (pages)
3. Get Organization URN:
   ```bash
   curl -X GET https://api.linkedin.com/v2/organizations \
     -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" | jq '.elements[0].id'
   ```
4. Use `LINKEDIN_ORGANIZATION_URN` instead of `LINKEDIN_PERSON_URN`

### Rotation Schedule
- **Every 90 days**: Access tokens expire automatically; generate new via OAuth flow
- **Quarterly**: Regenerate refresh token (if applicable)
- **Immediate**: After team member departure or if account compromised

---

## Facebook (Graph API)

### Prerequisites
- Facebook Business Account
- Facebook page for posting
- Meta app with pages_manage_posts permission

### Setup Steps

1. **Create Meta App**
   - Go to: https://developers.facebook.com/
   - Create new app
   - App name: `ProfitEngine Publishing`
   - App purpose: `Posts & Feeds Publishing`

2. **Configure App**
   - Settings → Basic: Copy **App ID**
   - Settings → Roles → Admin
   - Platforms → Facebook
   - Products → Add Facebook Login
   - Products → Add Graph API

3. **Generate Page Access Token**
   - Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your app from dropdown
   - Select your page from "User or Page" dropdown
   - Click "Get Page Access Token"
   - Permissions required: `pages_manage_posts`, `pages_read_engagement`

4. **Get Page ID**
   - Go to your Facebook page → Settings → Page Info → Page ID
   - Or via API:
   ```bash
   curl -X GET https://graph.facebook.com/me?access_token=$FB_PAGE_ACCESS_TOKEN \
     | jq '.id'
   ```

5. **Environment Variables**
   ```bash
   FB_PAGE_ID=123456789
   FB_PAGE_ACCESS_TOKEN=EAAC...
   ```

6. **Test**
   ```bash
   curl -X GET https://graph.facebook.com/v18.0/$FB_PAGE_ID?access_token=$FB_PAGE_ACCESS_TOKEN
   ```

### Rotation Schedule
- **Never expires** (long-lived tokens): Page access tokens valid indefinitely unless revoked
- **Quarterly review**: Check app permissions in Business Suite
- **Immediate**: If token leaked or app revoked

---

## Instagram (Graph API via Facebook)

### Prerequisites
- Instagram Business Account (linked to Facebook page)
- Meta Business Suite access
- Same FB_PAGE_ACCESS_TOKEN as Facebook (with additional instagram_content_publish permission)

### Setup Steps

1. **Convert to Business Account**
   - Go to Instagram account Settings → Account Type and Tools
   - Switch to Business Account
   - Link to Facebook page

2. **Get Instagram User ID**
   ```bash
   # Get connected Instagram account ID:
   curl -X GET https://graph.facebook.com/v18.0/$FB_PAGE_ID/instagram_business_account?access_token=$FB_PAGE_ACCESS_TOKEN \
     | jq '.instagram_business_account.id'
   ```

3. **Request instagram_content_publish Permission**
   - Meta Business Suite → Apps → Your App
   - Ensure `instagram_content_publish` permission granted

4. **Environment Variables**
   ```bash
   IG_USER_ID=123456789
   FB_PAGE_ACCESS_TOKEN=EAAC...  # Same as Facebook, with additional permissions
   ```

5. **Test**
   ```bash
   # Create media container
   curl -X POST https://graph.instagram.com/v18.0/$IG_USER_ID/media \
     -d "image_url=https://example.com/image.jpg&caption=Test&access_token=$FB_PAGE_ACCESS_TOKEN"
   ```

### Requirements
- **Image must be**: Public HTTPS URL, .jpg or .png only (not .gif/.webp)
- **Caption limit**: 2200 characters
- **Publishing**: 2-step process (create media container → publish container)
- **Frequency**: Recommend 1 post per day max

### Rotation Schedule
- Same as Facebook (never expires, quarterly review)

---

## TikTok (OAuth 2.0)

### Prerequisites
- TikTok Business Account (not personal)
- TikTok Business Center access
- OAuth 2.0 app with video.upload scope

### Setup Steps

1. **Create Business Account**
   - Sign up at https://www.tiktok.com/creators
   - Switch to Creator account → Business Account
   - Go to: https://business.tiktok.com/

2. **Register OAuth App**
   - Creator Center → Settings → Developer apps
   - Create new app
   - App name: `ProfitEngine Publishing`
   - Scopes: `video.upload` (and `video.list` for management)

3. **Get OAuth Credentials**
   - Copy: **Client Key** (Client ID)
   - Copy: **Client Secret**

4. **Generate Access Token**
   ```bash
   # 1. Redirect user to:
   https://www.tiktok.com/v1/oauth/authorize?
     client_key=$TIKTOK_CLIENT_ID&
     scope=video.upload,video.list&
     response_type=code&
     redirect_uri=http://localhost:8080/callback

   # 2. Exchange code for access token:
   curl -X POST https://open-api.tiktok.com/v1/oauth/token/ \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_key=$TIKTOK_CLIENT_ID&
         client_secret=$TIKTOK_CLIENT_SECRET&
         code=$AUTH_CODE&
         grant_type=authorization_code"
   ```

5. **Get Open ID**
   ```bash
   curl -X GET https://open-api.tiktok.com/v1/user/info/ \
     -H "Authorization: Bearer $TIKTOK_ACCESS_TOKEN" | jq '.data.user.open_id'
   ```

6. **Environment Variables**
   ```bash
   TIKTOK_ACCESS_TOKEN=act_...
   TIKTOK_OPEN_ID=ot...
   ```

### Requirements
- **Business Account only**: Personal accounts not supported
- **Video format**: .mp4 or .mov, max 287MB
- **Upload method**: Remote URL (no direct file upload)
- **Caption limit**: 2200 characters
- **Frequency**: Recommend 1-3 posts per week

### Rotation Schedule
- **Quarterly**: Regenerate access token via OAuth flow
- **Check rate limits**: TikTok has daily/monthly upload limits
- **Immediate**: If account rate-limited or suspended

---

## YouTube (OAuth 2.0 with Refresh Token)

### Prerequisites
- Google account with YouTube channel
- Google Cloud Console project
- OAuth 2.0 Desktop app credentials

### Setup Steps

1. **Create Google Cloud Project**
   - Go to: https://console.cloud.google.com/
   - Create new project: `ProfitEngine YouTube Publishing`

2. **Enable YouTube API**
   - APIs & Services → Library
   - Search: "YouTube Data API v3"
   - Click Enable

3. **Create OAuth 2.0 Credentials**
   - APIs & Services → Credentials
   - Create Credentials → OAuth Client ID
   - Application type: **Desktop app**
   - Copy: **Client ID** and **Client Secret**

4. **Generate Refresh Token (Initial OAuth Flow)**
   ```bash
   # Install library:
   pip install google-auth-oauthlib google-api-python-client

   # Run OAuth flow:
   python3 -m google_auth_oauthlib.flow \
     --client_secret=YOUR_CLIENT_SECRET_JSON \
     --scope=https://www.googleapis.com/auth/youtube.upload

   # This opens browser for consent, then prints refresh token
   ```

5. **Store Refresh Token**
   - Copy long-lived refresh token (valid indefinitely until revoked)
   - Store as `YOUTUBE_REFRESH_TOKEN` in `.env`

6. **Environment Variables**
   ```bash
   YOUTUBE_CLIENT_ID=abc123...apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=xyz789...
   YOUTUBE_REFRESH_TOKEN=1//...
   ```

7. **Test**
   ```bash
   python3 -c "
   from google.auth.transport.requests import Request
   from google.oauth2.credentials import Credentials

   creds = Credentials(
       token=None,
       refresh_token='$YOUTUBE_REFRESH_TOKEN',
       token_uri='https://oauth2.googleapis.com/token',
       client_id='$YOUTUBE_CLIENT_ID',
       client_secret='$YOUTUBE_CLIENT_SECRET',
       scopes=['https://www.googleapis.com/auth/youtube.upload']
   )
   creds.refresh(Request())
   print('Access token refreshed:', creds.token[:20] + '...')
   "
   ```

### Requirements
- **Video format**: .mp4, .mov, .avi, .mkv (many formats supported)
- **File size**: Up to 256GB
- **Privacy status**: `unlisted` (recommended for first-time uploads) or `public`
- **Channel in good standing**: No strikes or suspensions

### Rotation Schedule
- **Refresh token**: Valid indefinitely; revoke only if compromised
- **Access token**: Auto-renewed on each upload (5min expiry)
- **Quarterly**: Review Google Security Dashboard for suspicious activity
- **Immediate**: If refresh token leaked or account compromised

---

## Credential Rotation Checklist

### Monthly
- [ ] Review API usage logs for each platform
- [ ] Check for failed authentication attempts
- [ ] Verify all tokens still valid (expired tokens will show errors)

### Quarterly
- [ ] Rotate all API keys and secrets
- [ ] Regenerate OAuth tokens where applicable
- [ ] Update GitHub Secrets with new credentials
- [ ] Update OCI `.env` with new credentials
- [ ] Update Vercel environment variables if used
- [ ] Deactivate old tokens/keys (don't just overwrite)

### Annually
- [ ] Audit all connected apps in Meta Business Suite
- [ ] Review LinkedIn app permissions
- [ ] Check Google Cloud project for unused APIs
- [ ] Rotate service account passwords (Reddit, etc.)

### Immediately Upon
- [ ] Team member departure: Rotate ALL credentials
- [ ] Security incident or token leak
- [ ] Failed payment or account suspension
- [ ] Major platform policy changes
- [ ] After 90+ days of inactivity (some platforms auto-revoke)

---

## Security Best Practices

1. **Never commit credentials to git**
   - Use `.env.example` with placeholder values
   - Use `.gitignore` to exclude `.env`
   - Always use environment variables

2. **Use strong, unique passwords**
   - Service account passwords: 32+ characters, random
   - Store in password manager (1Password, Bitwarden, etc.)
   - Never reuse across platforms

3. **Enable MFA where available**
   - Twitter, Facebook, LinkedIn, Google all support MFA
   - Use hardware keys (FIDO2) when possible
   - Fallback to TOTP (Authenticator app)

4. **Monitor API usage**
   - Set up alerts for unusual activity
   - Review logs weekly
   - Check rate limits before peak traffic

5. **Use least privilege**
   - Grant minimum required scopes/permissions
   - Don't request `email`, `profile`, etc. unless needed
   - Regularly audit and remove unused permissions

6. **Secure storage**
   - GitHub Secrets: Encrypted at rest, masked in logs
   - OCI `.env`: File permissions 600 (owner read/write only)
   - Password manager: Encrypted, backed up, MFA enabled

---

## Troubleshooting

### Common Errors

| Platform | Error | Solution |
|----------|-------|----------|
| Twitter | `401 Unauthorized` | Verify Bearer Token or API Key/Secret format |
| Reddit | `INVALID_TOKEN` | Check username/password correct for service account |
| LinkedIn | `400 Bad Request` | Verify Person URN format and token scopes |
| Facebook | `403 Invalid token` | Regenerate page access token via Graph Explorer |
| Instagram | `Container rejected` | Ensure image is public HTTPS, .jpg or .png only |
| TikTok | `403 Forbidden` | Verify account is Business Account, not personal |
| YouTube | `403 Forbidden` | Check refresh token not revoked in Google Dashboard |

### Verification Commands

```bash
# Twitter
curl -X GET https://api.twitter.com/2/tweets/search/recent?query=test \
  -H "Authorization: Bearer $TWITTER_BEARER_TOKEN" | head -c 200

# Reddit
python3 -c "import praw; r = praw.Reddit(...); print(r.user.me())"

# LinkedIn
curl -X GET https://api.linkedin.com/v2/me \
  -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN"

# Facebook
curl -X GET https://graph.facebook.com/v18.0/$FB_PAGE_ID \
  -H "Authorization: Bearer $FB_PAGE_ACCESS_TOKEN"

# Instagram
curl -X GET https://graph.instagram.com/v18.0/$IG_USER_ID/media \
  -H "Authorization: Bearer $FB_PAGE_ACCESS_TOKEN"

# TikTok
curl -X GET https://open-api.tiktok.com/v1/user/info/ \
  -H "Authorization: Bearer $TIKTOK_ACCESS_TOKEN"

# YouTube
python3 -c "from googleapiclient.discovery import build; ..."
```

---

## Support & Escalation

If credential setup fails:

1. **Check platform API documentation**
   - Twitter: https://developer.twitter.com/en/docs
   - Reddit: https://praw.readthedocs.io/
   - LinkedIn: https://docs.microsoft.com/en-us/linkedin/marketing/
   - Facebook: https://developers.facebook.com/docs/
   - Instagram: https://developers.facebook.com/docs/instagram-api/
   - TikTok: https://developers.tiktok.com/
   - YouTube: https://developers.google.com/youtube/

2. **Enable debug logging**
   ```bash
   export DEBUG=1
   python3 scripts/test_credentials.py
   ```

3. **Contact platform support**
   - Platform-specific help: See links above
   - Rate limiting? Contact support@[platform].com
   - Suspended account? Follow reinstatement process

---

## Related Files

- `scripts/social_media_publishers.py` — Implementation
- `tests/test_social_media_publishers.py` — Unit tests
- `.env.example` — Template
- `SECURITY_ROTATION_REQUIRED.md` — Security procedures

Last updated: 2026-06-19

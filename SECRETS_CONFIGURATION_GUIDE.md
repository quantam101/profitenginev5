# GitHub Secrets Configuration Guide
**For**: ProfitEngine v5 Revenue Systems  
**Status**: 22/22 platforms need secrets configured  
**Estimated time**: 2–4 hours (obtain credentials, add to GitHub)  

---

## OVERVIEW

The following 22 platform credentials are missing from GitHub Secrets. These are required for:
- **Daily content distribution** (2x daily via `.github/workflows/daily-content.yml`)
- **Revenue tracking** (webhooks for order notifications)
- **Product publishing** (Gumroad, Printify)
- **Affiliate link injection** (across all platforms)

Without these, social media posts don't get published, and revenue reporting is incomplete.

---

## QUICK START (PRIORITY ORDER)

### HIGH PRIORITY (Start with these 3)

#### 1. GUMROAD_ACCESS_TOKEN
**Purpose**: Publish/update digital products, check sales  
**Revenue impact**: Direct product sales ($29–$27 per product)

**Steps**:
1. Go to https://gumroad.com/settings/api
2. Click "Generate token"
3. Copy the token (starts with `qP1...`)
4. Add to GitHub Secrets as `GUMROAD_ACCESS_TOKEN`

**Verify**:
```bash
curl -H "Authorization: Bearer $GUMROAD_TOKEN" https://api.gumroad.com/v2/products
```

---

#### 2. YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
**Purpose**: Publish to YouTube, track subscriber revenue  
**Revenue impact**: Monetization per 1000 views (~$3–$15)

**Steps**:
1. Go to https://console.cloud.google.com/
2. Create new project: "ProfitEngine"
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credential (Desktop application)
5. Download credentials JSON
6. Use Google OAuth flow to get refresh token:
   ```bash
   python scripts/get_youtube_refresh_token.py
   ```
7. Add to GitHub Secrets:
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`

**Verify**:
```bash
python scripts/check_youtube_channel.py
```

---

#### 3. PRINTIFY_API_TOKEN, PRINTIFY_SHOP_ID
**Purpose**: Create/publish POD products on Etsy  
**Revenue impact**: Print-on-demand merch (~$10–$30 per sale)

**Steps**:
1. Go to https://printify.com/account/api
2. Generate new API token
3. Go to https://printify.com/app/store (your shop)
4. Copy shop ID from URL or shop settings
5. Add to GitHub Secrets:
   - `PRINTIFY_API_TOKEN`
   - `PRINTIFY_SHOP_ID`

**Verify**:
```bash
curl -H "Authorization: Bearer $PRINTIFY_TOKEN" \
  https://api.printify.com/v1/shops/$PRINTIFY_SHOP_ID/products.json
```

---

### MEDIUM PRIORITY (Content Distribution)

#### 4–5. TWITTER / X
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_SECRET`

**Steps**:
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create new app (if not exists): "ProfitEngine"
3. Go to Keys & tokens
4. Generate "Access Token & Secret" (if not exists)
5. Copy all 4 values (keep secret)

**Verify**: Run `.github/workflows/daily-content.yml` manually, check tweet posts

---

#### 6–7. REDDIT
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USERNAME`
- `REDDIT_PASSWORD`

**Steps**:
1. Go to https://www.reddit.com/prefs/apps
2. Create new app: "ProfitEngine"
3. Choose "script" type
4. Copy client ID and secret
5. Use your account username/password (app-specific auth)

**Verify**: Check r/YourSubreddit for posted articles

---

#### 8–9. FACEBOOK
- `FB_PAGE_ACCESS_TOKEN`
- `FB_PAGE_ID`

**Steps**:
1. Go to https://developers.facebook.com/
2. Create app (if not exists): "ProfitEngine"
3. Go to Messenger > Settings
4. Generate page access token
5. Copy page ID from page settings

**Verify**: Check Facebook page for new posts

---

#### 10. INSTAGRAM (IG_USER_ID)
**Purpose**: Post to Instagram feed  

**Steps**:
1. Set up Facebook app (above)
2. Connect Instagram business account to Facebook
3. Go to Settings > Basic > App Domains
4. Add domain: `alreadyherellc.com`
5. Get Instagram user ID: https://www.instagram.com/alreadyherellc/?__a=1 (look for `id` field)

**Verify**: Check Instagram for new story posts

---

#### 11–12. LINKEDIN
- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_PERSON_URN`

**Steps**:
1. Go to https://www.linkedin.com/developers/apps
2. Create app: "ProfitEngine"
3. Generate access token
4. Get your person URN: `urn:li:person:YOUR_ID` (from LinkedIn profile settings)

**Verify**: Check LinkedIn profile for article shares

---

#### 13–14. TIKTOK
- `TIKTOK_ACCESS_TOKEN`

**Steps**:
1. Go to https://developer.tiktok.com/
2. Create app: "ProfitEngine"
3. Apply for TikTok Shop API access
4. Generate access token (requires business account)

**Note**: TikTok requires higher access level for automated posting. May need to manually approve first post.

**Verify**: Check TikTok bio for link clicks

---

### LOWER PRIORITY (Backup Platforms)

#### 15–16. ETSY
- `ETSY_API_KEY`
- `ETSY_SHOP_ID`

**Purpose**: Integrate with print-on-demand (if using Etsy directly)

**Steps**:
1. Go to https://www.etsy.com/developers/
2. Create API app
3. Copy API key
4. Copy shop ID from shop settings

---

#### 17–18. BEEHIIV (Newsletter)
- `BEEHIIV_API_KEY`
- `BEEHIIV_PUBLICATION_ID`

**Purpose**: Send newsletter, track subscriber revenue  

**Steps**:
1. Go to https://www.beehiiv.com/dashboard/settings/integrations/api
2. Generate API key
3. Copy publication ID (from URL: beehiiv.com/publication/YOUR_ID)

---

## GITHUB SECRETS SETUP

### Add to Repository
1. Go to repo: https://github.com/quantam101/profitenginev5
2. Click Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Name: Exact name (e.g., `GUMROAD_ACCESS_TOKEN`)
5. Value: Paste credential
6. Click "Add secret"

### Verify Added
```bash
gh secret list --repo quantam101/profitenginev5
```

### Format for Each Platform

```
Name                          | Value
------------------------------|------------------------------------------------
GUMROAD_ACCESS_TOKEN          | qP1PGdN-zCLeGeaN2r6SOZJKJK6oy2AFHIyVb6G3CuY
YOUTUBE_CLIENT_ID             | 12345.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET         | GOCSPX-abc123...
YOUTUBE_REFRESH_TOKEN         | 1//06rg_nVZE1-MiCg...
PRINTIFY_API_TOKEN            | Bearer abc123...
PRINTIFY_SHOP_ID              | 12345678
TWITTER_API_KEY               | abc123...
TWITTER_API_SECRET            | xyz789...
TWITTER_ACCESS_TOKEN          | 1234-abc...
TWITTER_ACCESS_SECRET         | xyz789...
REDDIT_CLIENT_ID              | abc123...
REDDIT_CLIENT_SECRET          | xyz789...
REDDIT_USERNAME               | your_reddit_username
REDDIT_PASSWORD               | your_reddit_password
FB_PAGE_ACCESS_TOKEN          | EAAB1234...
FB_PAGE_ID                    | 1234567890
IG_USER_ID                    | 1234567890
LINKEDIN_ACCESS_TOKEN         | AQVaBaB1abc...
LINKEDIN_PERSON_URN           | urn:li:person:ABC123XYZ
TIKTOK_ACCESS_TOKEN           | v1.abc123...
ETSY_API_KEY                  | abc123...
ETSY_SHOP_ID                  | 1234567890
BEEHIIV_API_KEY               | Bearer abc123...
BEEHIIV_PUBLICATION_ID        | abc123...
```

---

## ENVIRONMENT VARIABLE VERIFICATION

Once all secrets are added, verify they're accessible in workflows:

```bash
# Run verification workflow
gh workflow run verify-distribution.yml \
  --repo quantam101/profitenginev5

# Wait ~2 minutes, then check logs
gh run view --repo quantam101/profitenginev5 \
  --json status,conclusion | tail -5
```

Expected output: All platforms should show `✓ configured` (not `✗ missing`).

---

## TESTING EACH PLATFORM

### Manual Verification

After adding secrets, test each workflow:

```bash
# Test Gumroad
gh workflow run gumroad-store-status.yml \
  --repo quantam101/profitenginev5 \
  -f bootstrap=true

# Test daily content distribution
gh workflow run daily-content.yml \
  --repo quantam101/profitenginev5 \
  -f topic="test article" \
  -f verify_only=false

# Test revenue tracking
gh workflow run revenue-daily.yml \
  --repo quantam101/profitenginev5
```

Then check:
- ✅ Gumroad: Products listed at alreadyhere.gumroad.com
- ✅ YouTube: Video uploaded to channel
- ✅ Twitter: Tweet posted to @alreadyhere_llc
- ✅ Reddit: Post on r/YourSubreddit
- ✅ Blog: New article on quantam101.github.io/content

---

## SECURITY NOTES

### Credential Safety
- **Never** commit secrets to git (use GitHub Secrets only)
- **Never** paste credentials in Slack, email, or chat
- **Rotate** credentials monthly (especially OAuth tokens)
- **Revoke** old tokens after rotating

### Token Expiry
Some platforms require periodic re-authentication:
- **YouTube**: Refresh token expires if not used for 6 months
- **Twitter**: Bearer tokens don't expire, but app can be revoked
- **Reddit**: Tokens expire after 1 hour (refresh via endpoint)

Add these to your calendar:
- 1st of each month: Rotate all credentials
- 2nd week: Test each platform still works

---

## TROUBLESHOOTING

### "Secret not found" error in workflow
- Verify secret was added to correct repo (not organization)
- Workflow file must reference exact secret name (case-sensitive)
- Commit changes and push before running workflow

### Platform says "unauthorized"
- Check credential type (API key vs. OAuth token vs. password)
- Verify token hasn't expired
- Confirm app/integration is still active on platform

### Workflow passes but no posts appear
- Check platform's spam/moderation queue
- Verify content format matches platform requirements
- Check workflow logs for error messages

---

## MONTHLY MAINTENANCE

Add to your calendar recurring task:

**1st of each month**:
- [ ] Rotate Gumroad token (Settings > Advanced API)
- [ ] Rotate YouTube refresh token (if applicable)
- [ ] Rotate Twitter Bearer token
- [ ] Rotate Reddit token
- [ ] Update all GitHub Secrets with new values
- [ ] Test daily-content.yml to verify all platforms still work

---

## NEXT STEPS

1. **This week**: Add top 3 secrets (Gumroad, YouTube, Printify)
2. **Next week**: Add 5 social platforms (Twitter, Reddit, Facebook, LinkedIn, Instagram)
3. **This month**: Complete all 22 platforms

Once all secrets are configured:
- Daily content publishing activates automatically
- Revenue tracking becomes real-time
- You'll see products on all platforms
- Income streams start flowing

---

## SUPPORT

For credential issues:
- YouTube: https://support.google.com/accounts/answer/185833
- Twitter: https://developer.twitter.com/en/docs/authentication/oauth-2-0
- Reddit: https://github.com/reddit-archive/reddit/wiki/OAuth2
- Facebook: https://developers.facebook.com/docs/permissions

For workflow issues:
- Check `.github/workflows/daily-content.yml` for environment variable names
- Run `gh secret list` to verify secrets are added
- Check workflow run logs for specific error messages

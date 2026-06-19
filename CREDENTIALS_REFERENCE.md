# ProfitEngine v5 - Credentials Reference Guide

## Quick Copy-Paste Lists for Setup

### Credentials Currently Configured

```
GROQ_API_KEY                    = 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
GEMINI_API_KEY                  = AIzaSyCVAAmQUhhxCqtIm88w6U6u2cbzzZYn8oc
HF_TOKEN                        = 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
CONTENT_REPO_TOKEN              = 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
GITHUB_CONTENT_OWNER            = quantam101
GITHUB_CONTENT_REPO             = content
GITHUB_CONTENT_BRANCH           = main
GITHUB_CONTENT_DIR              = posts
DEVTO_API_KEY                   = w67nr6yMcqtPC5JHDERCDRxk
HASHNODE_API_KEY                = 3e71b759-0199-4583-a740-9d1e2c44565f
HASHNODE_PUB_ID                 = 3e71b759-0199-4583-a740-9d1e2c44565f
TELEGRAM_BOT_TOKEN              = [CONFIGURED]
TELEGRAM_CHAT_ID                = [CONFIGURED]
AMAZON_PARTNER_TAG              = alreadyhere-20
AFFILIATE_LINKS                 = [12 PROGRAMS CONFIGURED]
```

### Missing - To Add for Medium Publishing

```
MEDIUM_API_KEY                  = [GENERATE AT https://medium.com/@username/settings]
MEDIUM_AUTHOR_ID                = [GET FROM curl https://api.medium.com/v1/me]
```

### Missing - Social Media Platforms

```
TWITTER_API_KEY                 = [GET FROM https://developer.twitter.com/]
TWITTER_BEARER_TOKEN            = [GET FROM https://developer.twitter.com/]
REDDIT_CLIENT_ID                = [GET FROM https://www.reddit.com/prefs/apps]
REDDIT_CLIENT_SECRET            = [GET FROM https://www.reddit.com/prefs/apps]
FACEBOOK_PAGE_TOKEN             = [GET FROM Facebook Developers]
FACEBOOK_ACCESS_TOKEN           = [GET FROM Facebook Developers]
LINKEDIN_ACCESS_TOKEN           = [GET FROM LinkedIn Developers]
INSTAGRAM_ACCESS_TOKEN          = [GET FROM Facebook/Instagram Developers]
TIKTOK_ACCESS_TOKEN             = [GET FROM TikTok Developers]
MASTODON_ACCESS_TOKEN           = [GET FROM Mastodon Admin Settings]
BLUESKY_USERNAME                = [YOUR BLUESKY USERNAME]
BLUESKY_PASSWORD                = [YOUR BLUESKY APP PASSWORD]
```

### Missing - E-Commerce Platforms

```
SHOPIFY_STORE_URL               = [https://your-store.myshopify.com]
SHOPIFY_ACCESS_TOKEN            = [GET FROM Shopify App Admin]
ETSY_API_KEY                    = [GET FROM https://etsy.com/developers]
ETSY_API_SECRET                 = [GET FROM https://etsy.com/developers]
AMAZON_ACCESS_KEY               = [GET FROM AWS Console]
AMAZON_SECRET_KEY               = [GET FROM AWS Console]
EBAY_APP_ID                     = [GET FROM eBay Developers]
EBAY_DEV_ID                     = [GET FROM eBay Developers]
WOOCOMMERCE_API_KEY             = [GET FROM WooCommerce Admin]
WOOCOMMERCE_API_SECRET          = [GET FROM WooCommerce Admin]
```

---

## Detailed Setup Instructions

### 1. Medium Publishing (10 minutes)

**Why:** Access Medium's 100M+ monthly readers

**Step 1: Generate API Token**
1. Go to https://medium.com/@your-username/settings
2. Scroll down to "API tokens" section
3. Click "Generate a new token"
4. Name it "ProfitEngine" (or your preference)
5. Copy the entire token value

**Step 2: Get Author ID**
```bash
curl -s -H "Authorization: Bearer PASTE_YOUR_TOKEN_HERE" \
  https://api.medium.com/v1/me | jq '.data.id'
```
Copy the ID value returned

**Step 3: Update .env**
```bash
# In .env file, add or update:
MEDIUM_API_KEY=PASTE_YOUR_TOKEN_HERE
MEDIUM_AUTHOR_ID=PASTE_YOUR_ID_HERE
```

**Step 4: Verify**
```bash
CONTENT_VERIFY_ONLY=true python scripts/publish_article.py
# Should show: [VERIFY][OK] Medium: authenticated as <username>
```

---

### 2. Twitter/X (5 minutes)

**Why:** Promote articles to followers

**Step 1: Create App**
1. Go to https://developer.twitter.com/
2. Click "Create App" or access existing app
3. Go to "Keys and tokens" tab
4. Copy "API Key" and "Bearer Token"

**Step 2: Update .env**
```bash
TWITTER_API_KEY=PASTE_API_KEY
TWITTER_BEARER_TOKEN=PASTE_BEARER_TOKEN
```

**Step 3: Test**
```bash
python scripts/e2e_verify_system.py
# Should show: TWITTER CONFIGURED
```

---

### 3. Reddit (5 minutes)

**Why:** Share in relevant subreddits

**Step 1: Create Script App**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create Another App..."
3. Select "script" type
4. Fill name/description
5. Copy "Client ID" and "Client Secret"

**Step 2: Update .env**
```bash
REDDIT_CLIENT_ID=PASTE_CLIENT_ID
REDDIT_CLIENT_SECRET=PASTE_CLIENT_SECRET
```

---

### 4. LinkedIn (5 minutes)

**Why:** Reach professional audience

**Step 1: Create App**
1. Go to https://www.linkedin.com/developers/apps
2. Click "Create app"
3. Fill in company info
4. Accept terms
5. Go to "Auth" tab
6. Copy "Access Token"

**Step 2: Update .env**
```bash
LINKEDIN_ACCESS_TOKEN=PASTE_TOKEN
```

---

### 5. Telegram (Already Configured)

**Currently enabled** with bot token and chat ID already set.

To add additional channels:
```bash
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
# OR multiple channels separated by comma
TELEGRAM_CHAT_ID=123456789,987654321
```

---

### 6. Shopify (E-Commerce, 10 minutes)

**Why:** List products alongside articles

**Step 1: Create App in Shopify Admin**
1. Go to https://admin.shopify.com/
2. Settings → Apps and integrations
3. Click "Develop apps"
4. Create new app
5. Configure scopes: product_read (minimum)
6. Generate access token

**Step 2: Get Store URL**
1. Settings → General
2. Store address shows your domain (e.g., my-store.myshopify.com)

**Step 3: Update .env**
```bash
SHOPIFY_STORE_URL=https://my-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=PASTE_TOKEN
```

---

### 7. Etsy (E-Commerce, 10 minutes)

**Why:** Integrate Etsy products in articles

**Step 1: Create Developer Account**
1. Go to https://www.etsy.com/developers
2. Sign in or create account
3. Create new app
4. Accept terms

**Step 2: Get Credentials**
1. In app details page
2. Copy "Client ID" and "Client Secret"

**Step 3: Update .env**
```bash
ETSY_API_KEY=PASTE_CLIENT_ID
ETSY_API_SECRET=PASTE_CLIENT_SECRET
```

---

### 8. Instagram (5 minutes)

**Why:** Share visual content to followers

**Step 1: Get Access Token**
1. Go to https://developers.facebook.com/
2. Create/access app
3. Add Instagram product
4. Get Long-Lived Access Token

**Step 2: Update .env**
```bash
INSTAGRAM_ACCESS_TOKEN=PASTE_TOKEN
```

---

### 9. TikTok (10 minutes)

**Why:** Reach younger demographics

**Step 1: Create TikTok Developer Account**
1. Go to https://developer.tiktok.com/
2. Sign up and verify
3. Create new app

**Step 2: Get Access Token**
1. In app settings
2. Copy access token

**Step 3: Update .env**
```bash
TIKTOK_ACCESS_TOKEN=PASTE_TOKEN
```

---

### 10. Other Platforms

**Facebook:**
- Go to https://developers.facebook.com/
- Create page access token with page_content_management scope
- Use: `FACEBOOK_PAGE_TOKEN` or `FACEBOOK_ACCESS_TOKEN`

**Mastodon:**
- Go to your instance settings (e.g., mastodon.social/settings)
- Development → New Application
- Get access token
- Use: `MASTODON_ACCESS_TOKEN`

**Bluesky:**
- Create account at https://bsky.app/
- Go to Settings → Advanced → App passwords
- Create app password
- Use: `BLUESKY_USERNAME` and `BLUESKY_PASSWORD`

---

## Environment Variable Format

Place all credentials in `.env` file in this format:

```bash
# AI Providers (at least one required)
GROQ_API_KEY=your-groq-key
GEMINI_API_KEY=your-gemini-key
HF_TOKEN=your-huggingface-token

# GitHub Pages (required for publishing)
CONTENT_REPO_TOKEN=your-github-token
GITHUB_CONTENT_OWNER=quantam101
GITHUB_CONTENT_REPO=content
GITHUB_CONTENT_BRANCH=main
GITHUB_CONTENT_DIR=posts

# Content Platforms (optional)
DEVTO_API_KEY=your-devto-key
MEDIUM_API_KEY=your-medium-key
MEDIUM_AUTHOR_ID=your-author-id
HASHNODE_API_KEY=your-hashnode-key
HASHNODE_PUB_ID=your-publication-id

# Social Platforms (optional)
TWITTER_API_KEY=your-twitter-key
TWITTER_BEARER_TOKEN=your-bearer-token
REDDIT_CLIENT_ID=your-reddit-id
REDDIT_CLIENT_SECRET=your-reddit-secret
LINKEDIN_ACCESS_TOKEN=your-linkedin-token
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# E-Commerce (optional)
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your-shopify-token
ETSY_API_KEY=your-etsy-key
ETSY_API_SECRET=your-etsy-secret

# Affiliate Configuration (already set)
AMAZON_PARTNER_TAG=alreadyhere-20
AFFILIATE_LINKS={"keyword": "https://affiliate-url", ...}
```

---

## Testing Credentials

### Test All at Once
```bash
CONTENT_VERIFY_ONLY=true python scripts/publish_article.py
```

### Test Specific Platform
```bash
# Medium
python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
print('MEDIUM_API_KEY:', 'OK' if os.getenv('MEDIUM_API_KEY') else 'MISSING')
print('MEDIUM_AUTHOR_ID:', 'OK' if os.getenv('MEDIUM_AUTHOR_ID') else 'MISSING')
"
```

### Validate Token via API
```bash
# Twitter
curl -s -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  https://api.twitter.com/2/users/me | jq '.data'

# Medium
curl -s -H "Authorization: Bearer YOUR_MEDIUM_TOKEN" \
  https://api.medium.com/v1/me | jq '.data'

# Dev.to
curl -s -H "api-key: YOUR_DEVTO_KEY" \
  https://dev.to/api/users/me | jq '.username'
```

---

## Credential Rotation

When rotating credentials:

1. **Backup current .env**
   ```bash
   cp .env .env.backup
   ```

2. **Generate new token** from platform (follow setup steps above)

3. **Update .env** with new value
   ```bash
   # Edit .env in any text editor
   PLATFORM_API_KEY=new-token-here
   ```

4. **Verify immediately**
   ```bash
   CONTENT_VERIFY_ONLY=true python scripts/publish_article.py
   ```

5. **Revoke old token** at platform (security best practice)

6. **Test publishing**
   ```bash
   ARTICLE_TOPIC="Test Article" python scripts/publish_article_resilient.py
   ```

---

## Secure Handling

### Do's
- Store .env file locally (in project root)
- Rotate credentials quarterly
- Use dedicated API tokens (not personal tokens when possible)
- Keep .env in .gitignore (never commit)
- Backup .env in secure location

### Don'ts
- Share .env file over email or chat
- Commit .env to git repository
- Post credentials in issue trackers
- Reuse credentials across projects
- Use credentials from public sources

### In CI/CD
- Store credentials in GitHub Secrets
- Never echo credentials in logs
- Rotate GitHub Secret tokens quarterly
- Use environment-specific tokens (dev/staging/prod)

---

## Platform-Specific Notes

**Medium:**
- API is free but has rate limits
- Authenticates with bearer token
- Author ID must match token user

**Hashnode:**
- Paid Pro plan required (changed 2026-05-13)
- Disable with policy check in code
- Cannot be used with free tier

**Twitter/X:**
- Rate limited: 300 posts/month on free tier
- Requires elevated access for article links
- 15-minute delay between tweets to same URL

**Reddit:**
- Requires script type (not personal) app
- Cannot post same URL within 30 days
- Content must follow subreddit rules

**Shopify:**
- Requires store with API access
- Free tier has limited API calls
- Test mode available for development

**Etsy:**
- Requires active seller account
- API limited to 25 requests/min
- Listings must be public

---

## Troubleshooting

### "Token not found" error
- Verify credential key name matches expected (see reference above)
- Check .env file is in project root
- Ensure no extra spaces around `=` sign
- Restart terminal/IDE if cached

### "Unauthorized" error
- Token may have expired (generate new one)
- Token may be for wrong account
- Token may have been revoked
- Check token is not truncated or corrupted

### "Rate limited" error
- Platform throttling requests
- Wait 15-60 minutes before retrying
- Check platform's API documentation for limits
- Consider upgrading to paid tier

### "Invalid app" error
- App may have been deleted
- App scopes may have been revoked
- Platform may require app re-registration
- Generate new app following setup steps

---

## Support

For credential issues:

1. Check platform's developer docs
2. Verify token in platform's admin panel
3. Try generating new token following setup steps
4. Check GitHub Issues for similar problems
5. Open new issue with sanitized error message (no credentials in issue)

---

## Checklist for Full Setup

- [ ] Core (required): Groq/Gemini API key + GitHub token
- [ ] Publishing: Dev.to API key configured
- [ ] Monetization: Affiliate links configured (already done)
- [ ] Optional: Medium API + author ID
- [ ] Optional: Twitter bearer token
- [ ] Optional: Reddit client ID/secret
- [ ] Optional: Telegram bot token
- [ ] Optional: LinkedIn access token
- [ ] Optional: Shopify credentials
- [ ] Optional: Etsy credentials
- [ ] Verification: `CONTENT_VERIFY_ONLY=true python scripts/publish_article.py` passes
- [ ] Test publish: `python scripts/publish_article_resilient.py` succeeds

# Setup Checklist — 10 Platforms (Excluding Medium)

**Status**: Ready to begin  
**Total Time**: ~2 hours  
**Platforms**: 10 (Twitter, Reddit, LinkedIn, Facebook, Instagram, TikTok, Etsy, Gumroad, Printify, YouTube)

---

## Phase 1: Social Media (5 platforms, ~25 minutes)

- [ ] **Twitter/X** (5 min) — Go to https://developer.twitter.com/en/portal/dashboard
  - Get: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
  - Then: `gh secret set TWITTER_API_KEY --body 'VALUE'` (repeat for 3 more)

- [ ] **Reddit** (5 min) — Go to https://www.reddit.com/prefs/apps
  - Get: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_SUBREDDIT
  - Then: `gh secret set REDDIT_CLIENT_ID --body 'VALUE'` (repeat for 4 more)

- [ ] **LinkedIn** (5 min) — Go to https://www.linkedin.com/developers/apps
  - Get: LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN (format: urn:li:person:XXXXXXXXX)
  - Then: `gh secret set LINKEDIN_ACCESS_TOKEN --body 'VALUE'`

- [ ] **Facebook** (5 min) — Go to https://developers.facebook.com/
  - Get: FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN
  - Then: `gh secret set FB_PAGE_ID --body 'VALUE'`

- [ ] **Instagram** (5 min) — Via Facebook Developer Console
  - Get: IG_USER_ID
  - Then: `gh secret set IG_USER_ID --body 'VALUE'`
  - Note: Reuses FB_PAGE_ACCESS_TOKEN from Facebook

---

## Phase 2: Short-Form Video (1 platform, ~5 minutes)

- [ ] **TikTok** (5 min) — Go to https://www.tiktok.com/creators
  - Get: TIKTOK_ACCESS_TOKEN
  - Then: `gh secret set TIKTOK_ACCESS_TOKEN --body 'VALUE'`

---

## Phase 3: E-Commerce (3 platforms, ~35 minutes)

- [ ] **Etsy** (15 min) — Go to https://www.etsy.com/developers/your-apps
  - Get: ETSY_SHOP_ID, ETSY_API_KEY
  - Then: `gh secret set ETSY_SHOP_ID --body 'VALUE'`

- [ ] **Gumroad** (5 min) — Go to https://app.gumroad.com/creator/settings/security
  - Get: GUMROAD_CREATOR_ID (API token already configured)
  - Then: `gh secret set GUMROAD_CREATOR_ID --body 'VALUE'`

- [ ] **Printify** (15 min) — Go to https://printify.com/user/account
  - Get: PRINTIFY_API_KEY, PRINTIFY_SHOP_ID
  - Then: `gh secret set PRINTIFY_API_KEY --body 'VALUE'`

---

## Phase 4: Video Platform (Already Done ✅)

- [x] **YouTube** — All 3 credentials already configured
  - [x] YOUTUBE_CLIENT_ID ✅
  - [x] YOUTUBE_CLIENT_SECRET ✅
  - [x] YOUTUBE_REFRESH_TOKEN ✅

---

## Full Details

For complete setup instructions with links and step-by-step guides, see:
**CREDENTIALS_SETUP_10PLATFORMS.md**

---

## Verification After Each Phase

```bash
python scripts/test_distribution.py --check-only
```

---

## Final Status When Complete

All 10 platforms configured → Content auto-publishes to all 10 every day at 07:05 & 15:05 UTC

**Medium is intentionally NOT configured** (user preference)

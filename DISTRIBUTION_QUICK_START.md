# Distribution System - Quick Start Guide

## TL;DR

```bash
# Test what's configured
python scripts/test_distribution.py --check-only

# Full verification with API checks
python scripts/test_distribution.py

# JSON for CI/CD
python scripts/test_distribution.py --json > report.json

# Save report
python scripts/test_distribution.py --output report.txt
```

## Platform Status Codes

- `[OK]` = Ready (all credentials configured)
- `[~~]` = Partial (some credentials missing)
- `[XX]` = Unconfigured (no credentials)

## Add Missing Credentials (Quick)

```bash
# GitHub CLI method (fastest)
gh secret set TWITTER_API_KEY --body 'your_key'
gh secret set TWITTER_API_SECRET --body 'your_secret'
gh secret set TWITTER_ACCESS_TOKEN --body 'your_token'
gh secret set TWITTER_ACCESS_SECRET --body 'your_secret'

# Repeat for other platforms...
```

## Platform Setup Links (Copy-Paste)

Click to get credentials:

| Platform | Setup Link |
|----------|-----------|
| Twitter/X | https://developer.twitter.com/en/portal/dashboard |
| Reddit | https://www.reddit.com/prefs/apps |
| LinkedIn | https://www.linkedin.com/developers/apps |
| Facebook | https://developers.facebook.com/apps/ |
| Instagram | https://business.facebook.com/ |
| TikTok | https://developer.tiktok.com/ |
| YouTube | https://console.developers.google.com/ |
| Etsy | https://www.etsy.com/developers/your-apps |
| Gumroad | https://app.gumroad.com/creator/settings/security |
| Printify | https://printify.com/user/account/api-access |

## Required Secrets Per Platform

### Twitter/X (4)
```
TWITTER_API_KEY
TWITTER_API_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_SECRET
```

### Reddit (4)
```
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USERNAME
REDDIT_PASSWORD
```

### LinkedIn (2)
```
LINKEDIN_ACCESS_TOKEN
LINKEDIN_PERSON_URN
```

### Facebook (2)
```
FB_PAGE_ID
FB_PAGE_ACCESS_TOKEN
```

### Instagram (2)
```
IG_USER_ID
FB_PAGE_ACCESS_TOKEN  # shared with Facebook
```

### TikTok (1)
```
TIKTOK_ACCESS_TOKEN
```

### YouTube (3)
```
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
```

### Etsy (2)
```
ETSY_SHOP_ID
ETSY_API_KEY
```

### Gumroad (1)
```
GUMROAD_API_TOKEN
```

### Printify (2)
```
PRINTIFY_API_KEY
PRINTIFY_SHOP_ID
```

## Verification Workflow

### 1. Check Current Status
```bash
python scripts/test_distribution.py --check-only
```
Shows which platforms are ready vs missing credentials.

### 2. Get Credentials
Visit the setup links above for each missing platform.

### 3. Add to GitHub Secrets
```bash
gh secret set PLATFORM_CREDENTIAL --body 'value'
```

### 4. Verify Setup
```bash
python scripts/test_distribution.py
```
Should show "READY" status for configured platforms.

### 5. Check JSON (CI/CD)
```bash
python scripts/test_distribution.py --json
```
Useful for automated checks in GitHub Actions.

## Troubleshooting

### "UNCONFIGURED" status
The environment variable is not set. Check:
```bash
# Linux/macOS
echo $TWITTER_API_KEY

# Windows PowerShell
$env:TWITTER_API_KEY
```

If empty, add via GitHub:
```bash
gh secret set TWITTER_API_KEY --body 'your_actual_key'
```

### Script not running
Install dependencies:
```bash
pip install httpx tweepy praw
```

### Report not saving
Check file permissions:
```bash
python scripts/test_distribution.py --output ./report.txt
ls -la ./report.txt  # verify it was created
```

## Platform Notes

- **LinkedIn**: Token expires every 60 days - plan for monthly refresh
- **Facebook**: Token expires if you change your password
- **TikTok**: Requires annual re-authorization
- **Gumroad**: Unlimited API calls (no rate limiting)
- **Reddit**: Requires subreddit setup via `REDDIT_SUBREDDIT` env var
- **Instagram**: Must be a business or creator account

## What Gets Posted?

When publishing, the system sends:
- Article title + link to Twitter/Reddit/LinkedIn
- Full article preview + link to Facebook/Instagram
- Product cross-promotion to Etsy/Gumroad/Printify
- Video uploads to TikTok/YouTube (when available)

## Dry-Run Tests

The script validates without posting:
- Checks all credentials are present
- Tests API endpoint availability
- Verifies request payloads are valid
- Does NOT create actual posts

## Production Readiness

System is production-ready when:
- At least one platform shows [OK] status
- All test results pass
- Script shows "PRODUCTION READY" message

## Next Steps After Setup

1. Run full verification: `python scripts/test_distribution.py`
2. Review report for any warnings
3. Deploy code: `git push main`
4. Monitor first content distribution
5. Verify posts appear on platforms

## Emergency Contacts

Platform API status pages:
- Twitter: https://status.twitter.com
- Reddit: https://status.redditmaintenance.com
- LinkedIn: https://www.linkedin-status.com
- Facebook: https://status.fb.com
- TikTok: https://status.tiktok.com
- Google/YouTube: https://status.cloud.google.com
- Etsy: https://status.etsy.com

## Full Documentation

See `DISTRIBUTION_TEST_README.md` for comprehensive documentation.

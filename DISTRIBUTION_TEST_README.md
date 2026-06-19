# Content Distribution System - Integration Test & Verification Guide

## Overview

`scripts/test_distribution.py` is a comprehensive integration test and verification script for the ProfitEngine content distribution system. It validates credentials across all 10 distribution platforms (7 social media + 3 e-commerce) and provides a production-readiness report.

## What It Tests

### Social Media Platforms (7)
- **Twitter/X** - Tweet posting via API v2
- **Reddit** - Subreddit link submissions  
- **LinkedIn** - Profile/page article sharing
- **Facebook** - Page feed updates
- **Instagram** - Business account media publishing
- **TikTok** - Video publishing for creators
- **YouTube** - Video uploads and channel management

### E-Commerce Platforms (3)
- **Etsy** - Shop listing cross-promotion
- **Gumroad** - Product description updates
- **Printify** - Print-on-demand product updates

## Test Modes

### 1. Full Verification (Default)
```bash
python scripts/test_distribution.py
```

Performs:
1. Credential validation for all 10 platforms
2. Dry-run API endpoint tests (without posting)
3. Generates detailed text report with production readiness checklist

**Output:**
- Platform status (Ready/Partial/Unconfigured)
- Missing credentials (by platform)
- Required GitHub Secrets
- Next steps for production deployment

### 2. Credentials-Only Check
```bash
python scripts/test_distribution.py --check-only
```

Fast validation without dry-run tests. Useful for:
- CI/CD pipelines
- Quick credential audits
- Automated secret management workflows

### 3. Verbose Mode
```bash
python scripts/test_distribution.py --verbose
```

Shows detailed output for each platform including:
- Individual credential status
- Which specific variables are missing
- Configuration notes for each platform

### 4. JSON Output
```bash
python scripts/test_distribution.py --json
```

Outputs structured JSON for:
- CI/CD integration
- Programmatic parsing
- Dashboard visualization
- Automated alerting

**JSON Fields:**
```json
{
  "timestamp": "ISO-8601 datetime",
  "summary": {
    "total_platforms": 10,
    "ready": number,
    "partial": number,
    "unconfigured": number
  },
  "platforms": {
    "platform_key": {
      "platform_name": "Display Name",
      "platform_type": "social|ecommerce",
      "status": "READY|PARTIAL|UNCONFIGURED",
      "configured": {"VAR": "CONFIGURED"},
      "missing": {"VAR": "MISSING"},
      "configured_count": number,
      "missing_count": number,
      "notes": "Additional context"
    }
  }
}
```

### 5. Save Report to File
```bash
python scripts/test_distribution.py --output report.txt
python scripts/test_distribution.py --json --output report.json
```

Saves report to specified file (useful for archiving, sharing, or CI/CD artifacts).

## Sample Output

### Platform Status (Text Report)
```
PLATFORM STATUS
--------------------------------------------------------------------------------

SOCIAL MEDIA PLATFORMS:
  [OK] Facebook             READY           (2/2 vars)
  [OK] Instagram            READY           (2/2 vars)
  [OK] LinkedIn             READY           (2/2 vars)
  [XX] Reddit               UNCONFIGURED    (0/4 vars)
      Missing: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
  [OK] TikTok               READY           (1/1 vars)
  [OK] Twitter/X            READY           (4/4 vars)
  [OK] YouTube              READY           (3/3 vars)

E-COMMERCE PLATFORMS:
  [OK] Etsy                 READY           (2/2 vars)
  [OK] Gumroad              READY           (1/1 vars)
  [OK] Printify             READY           (2/2 vars)
```

### Missing Credentials Detection
```
MISSING CREDENTIALS
--------------------------------------------------------------------------------

REDDIT_CLIENT_ID
  - Reddit

REDDIT_CLIENT_SECRET
  - Reddit

REDDIT_USERNAME
  - Reddit

REDDIT_PASSWORD
  - Reddit
```

### GitHub Secrets Setup Guide
```
GITHUB SECRETS SETUP
--------------------------------------------------------------------------------
Add these secrets to GitHub (Settings > Secrets and variables > Actions):

gh secret set REDDIT_CLIENT_ID --body 'YOUR_VALUE_HERE'
gh secret set REDDIT_CLIENT_SECRET --body 'YOUR_VALUE_HERE'
gh secret set REDDIT_USERNAME --body 'YOUR_VALUE_HERE'
gh secret set REDDIT_PASSWORD --body 'YOUR_VALUE_HERE'

Or use the GitHub web UI (Recommended for sensitive tokens)
```

## Required Environment Variables

### Twitter/X (4 required)
- `TWITTER_API_KEY` - API Key
- `TWITTER_API_SECRET` - API Secret  
- `TWITTER_ACCESS_TOKEN` - Access Token
- `TWITTER_ACCESS_SECRET` - Access Token Secret
- **Credentials from:** https://developer.twitter.com/en/portal/dashboard
- **Note:** Requires API v2 access with `tweet.write` permissions

### Reddit (4 required)
- `REDDIT_CLIENT_ID` - OAuth app client ID
- `REDDIT_CLIENT_SECRET` - OAuth app secret
- `REDDIT_USERNAME` - Account username
- `REDDIT_PASSWORD` - Account password
- `REDDIT_SUBREDDIT` - Target subreddit (env var, optional)
- **Credentials from:** https://www.reddit.com/prefs/apps
- **Note:** Create "script" app type

### LinkedIn (2 required)
- `LINKEDIN_ACCESS_TOKEN` - OAuth access token
- `LINKEDIN_PERSON_URN` - URN like `urn:li:person:12345`
- **Credentials from:** https://www.linkedin.com/developers/apps
- **Note:** Token expires every 60 days

### Facebook (2 required)
- `FB_PAGE_ID` - Page ID (numeric)
- `FB_PAGE_ACCESS_TOKEN` - Page access token (NOT user token)
- **Credentials from:** https://developers.facebook.com/apps/
- **Note:** Must be page token, expires if password is changed

### Instagram (2 required)
- `IG_USER_ID` - Business account ID
- `FB_PAGE_ACCESS_TOKEN` - (Shared with Facebook)
- **Credentials from:** https://business.facebook.com/
- **Note:** Requires business or creator account

### TikTok (1 required)
- `TIKTOK_ACCESS_TOKEN` - OAuth access token
- **Credentials from:** https://developer.tiktok.com/
- **Note:** Requires TikTok for Creators account

### YouTube (3 required)
- `YOUTUBE_CLIENT_ID` - OAuth 2.0 client ID
- `YOUTUBE_CLIENT_SECRET` - OAuth 2.0 client secret
- `YOUTUBE_REFRESH_TOKEN` - Refresh token
- **Credentials from:** https://console.developers.google.com/
- **Note:** Requires OAuth 2.0 setup with `youtube.upload` scope

### Etsy (2 required)
- `ETSY_SHOP_ID` - Numeric shop ID
- `ETSY_API_KEY` - API key
- **Credentials from:** https://www.etsy.com/developers/your-apps
- **Note:** Free tier allows limited requests

### Gumroad (1 required)
- `GUMROAD_API_TOKEN` - API token
- **Credentials from:** https://app.gumroad.com/creator/settings/security
- **Note:** Found under API Access section

### Printify (2 required)
- `PRINTIFY_API_KEY` - API key
- `PRINTIFY_SHOP_ID` - Shop ID
- **Credentials from:** https://printify.com/user/account/api-access
- **Note:** Requires Printify shop setup

## Setup Instructions

### Step 1: Obtain Credentials

Visit each platform's developer/API console and create OAuth apps or API keys:

```bash
# Open all platforms in browser (macOS/Linux example)
open https://developer.twitter.com/en/portal/dashboard
open https://www.reddit.com/prefs/apps
open https://www.linkedin.com/developers/apps
open https://developers.facebook.com/apps/
open https://business.facebook.com/
open https://developer.tiktok.com/
open https://console.developers.google.com/
open https://www.etsy.com/developers/your-apps
open https://app.gumroad.com/creator/settings/security
open https://printify.com/user/account/api-access
```

### Step 2: Add Secrets to GitHub

Use GitHub CLI:
```bash
gh secret set TWITTER_API_KEY --body 'YOUR_KEY_HERE'
gh secret set TWITTER_API_SECRET --body 'YOUR_SECRET_HERE'
# ... repeat for all platforms
```

Or use GitHub Web UI:
1. Go to repository Settings
2. Click "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Enter secret name and value
5. Click "Add secret"

### Step 3: Verify Installation

```bash
# Test that all secrets are configured
python scripts/test_distribution.py --check-only

# Run full verification with dry-run tests
python scripts/test_distribution.py

# Check JSON output for CI/CD
python scripts/test_distribution.py --json > distribution_status.json
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Verify Distribution System

on: [push, pull_request]

jobs:
  distribution-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run distribution verification
        env:
          TWITTER_API_KEY: ${{ secrets.TWITTER_API_KEY }}
          TWITTER_API_SECRET: ${{ secrets.TWITTER_API_SECRET }}
          TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
          TWITTER_ACCESS_SECRET: ${{ secrets.TWITTER_ACCESS_SECRET }}
          # ... all other secrets
        run: |
          python scripts/test_distribution.py --json --output report.json
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: distribution-report
          path: report.json
```

## Exit Codes

- `0` - At least one platform is fully configured and ready
- `1` - No platforms fully configured OR unspecified error

Use exit codes for CI/CD automation:
```bash
python scripts/test_distribution.py
if [ $? -eq 0 ]; then
  echo "Distribution system ready for production"
else
  echo "Configuration incomplete - add missing secrets"
fi
```

## Test Article Structure

The script uses a mock article for testing:

```python
{
    "title": str,              # Article headline
    "body": str,               # Article body content
    "meta_description": str,   # SEO description
    "tags": List[str],         # Content tags
    "author": str,             # Author name
    "published_at": str,       # ISO-8601 datetime
    "canonical_url": str,      # Full article URL
}
```

When actually publishing, the real content system provides these fields.

## Dry-Run Test Details

The script performs non-destructive API validation:

1. **Credential Check** - Verifies all required environment variables are set
2. **Import Test** - Checks if dependencies are installed (tweepy, praw, etc.)
3. **Endpoint Validation** - Confirms API endpoints are reachable (HTTP HEAD request)
4. **Mock Article** - Uses sample content to test payload construction

**Does NOT:**
- Post to any platform
- Create test posts
- Send requests with real content
- Consume API rate limits
- Require test accounts

## Troubleshooting

### "ImportError: No module named 'tweepy'"
Install missing dependencies:
```bash
pip install tweepy praw httpx
```

### "SKIP - Credentials not configured"
The environment variable is empty. Check:
```bash
echo $TWITTER_API_KEY  # Linux/macOS
echo %TWITTER_API_KEY%  # Windows
```

Add the secret via GitHub:
```bash
gh secret set TWITTER_API_KEY --body 'value'
```

### "API endpoint not reachable"
Check internet connection and that the platform API is available. Some platforms may block requests from certain regions or IP ranges.

### "Unicode encoding error on Windows"
The script uses ASCII-compatible symbols for cross-platform compatibility. If you see encoding errors, ensure your terminal supports UTF-8:
```powershell
# PowerShell
$OutputEncoding = [System.Text.UTF8Encoding]::new()
python scripts/test_distribution.py
```

## Production Checklist

Before deploying to production:

- [ ] Run `python scripts/test_distribution.py` and verify all platforms show "READY"
- [ ] Check that output shows "PRODUCTION READY" status
- [ ] Verify credentials are in GitHub Secrets (not in code)
- [ ] Test with `--verbose` mode for detailed credential info
- [ ] Save JSON report for audit trail
- [ ] All platform notes understood (token expiry, rate limits, etc.)
- [ ] Team members know how to rotate expired tokens
- [ ] Rollback plan documented if a platform API changes

## Security Notes

- Never commit actual API keys or tokens to the repository
- Secrets are stored in GitHub Secrets (encrypted at rest)
- Secrets are injected at runtime as environment variables
- The test script masks credential values (shows only length/status)
- All API calls use HTTPS only
- Credentials are never logged or printed to console

## Monitoring & Maintenance

### Token Expiration Schedule
- **LinkedIn**: 60 days - monthly refresh needed
- **Facebook**: When password changes
- **YouTube**: 6 months with refresh token
- **Twitter/X**: Long-lived with proper OAuth setup
- **TikTok**: Requires annual re-authorization
- **Reddit**: Long-lived with proper OAuth setup
- **Etsy/Gumroad/Printify**: Long-lived

### Rotation Procedure
1. Get new token from platform
2. Update GitHub Secret: `gh secret set VAR_NAME --body 'new_value'`
3. Run verification: `python scripts/test_distribution.py --check-only`
4. Deploy with: `git push main`

## API Rate Limits

Each platform has different rate limits. The script respects these:

| Platform | Limit | Window |
|----------|-------|--------|
| Twitter/X | 500 | 24 hours |
| Reddit | 60 | 1 minute |
| LinkedIn | 100 | 1 day |
| Facebook | 200 | 1 hour |
| Instagram | 100 | 1 hour |
| TikTok | 100 | 1 day |
| YouTube | 10,000 | 1 day |
| Etsy | 1,000 | 1 minute |
| Gumroad | Unlimited | - |
| Printify | 1,000 | 1 minute |

## Support & Documentation

- Script source: `scripts/test_distribution.py`
- Social publishers: `scripts/social_media_publishers.py`
- E-commerce publishers: `scripts/ecommerce_publishers.py`
- Publisher functions follow pattern: `publish_PLATFORM(article, canonical_url)`

## License

Part of ProfitEngine v5 distribution system. See root LICENSE file.

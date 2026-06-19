# ProfitEngine Content Distribution System - Verification & Testing

This directory contains a comprehensive integration test and verification system for the ProfitEngine multi-platform content distribution network.

## Start Here

**New to this system?** Start with one of these:

1. **For Quick Setup:** Read [`DISTRIBUTION_QUICK_START.md`](./DISTRIBUTION_QUICK_START.md) (5 min read)
2. **For Complete Guide:** Read [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md) (comprehensive)
3. **For Overview:** Read [`DISTRIBUTION_SYSTEM_INDEX.md`](./DISTRIBUTION_SYSTEM_INDEX.md) (master index)

## What This System Does

Tests and validates your content distribution setup for **10 different platforms**:

**Social Media (7):**
- Twitter/X
- Reddit
- LinkedIn
- Facebook
- Instagram
- TikTok
- YouTube

**E-Commerce (3):**
- Etsy
- Gumroad
- Printify

## Quick Start (5 Minutes)

### 1. Check What's Configured
```bash
python scripts/test_distribution.py --check-only
```

### 2. Get Credentials (if needed)
Visit setup links in your error report.

### 3. Add to GitHub Secrets
```bash
gh secret set PLATFORM_VAR --body 'your_value'
```

### 4. Verify Complete Setup
```bash
python scripts/test_distribution.py
```

That's it! Look for "PRODUCTION READY" in the output.

## Files in This System

| File | Purpose | Read Time |
|------|---------|-----------|
| [`DISTRIBUTION_QUICK_START.md`](./DISTRIBUTION_QUICK_START.md) | Copy-paste setup guide | 5 min |
| [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md) | Complete documentation | 20 min |
| [`DISTRIBUTION_SYSTEM_INDEX.md`](./DISTRIBUTION_SYSTEM_INDEX.md) | Master index & reference | 10 min |
| [`DISTRIBUTION_INTEGRATION_SUMMARY.md`](./DISTRIBUTION_INTEGRATION_SUMMARY.md) | Technical overview | 10 min |
| [`DELIVERABLES.md`](./DELIVERABLES.md) | What was delivered | 5 min |
| [`scripts/test_distribution.py`](./scripts/test_distribution.py) | Main test script | (run it!) |
| [`.github/workflows/verify-distribution.yml`](./.github/workflows/verify-distribution.yml) | CI/CD automation | (automatic) |

## Test Commands

```bash
# Quick check (< 1 second) - Just check credentials
python scripts/test_distribution.py --check-only

# Full verification (3-5 sec) - Check + API tests
python scripts/test_distribution.py

# Verbose output - For debugging
python scripts/test_distribution.py --verbose

# JSON format - For dashboards/automation
python scripts/test_distribution.py --json

# Save report - For audit trail
python scripts/test_distribution.py --output report.txt
```

## Platform Status Codes

When you see your platform status:

| Status | Meaning | Action |
|--------|---------|--------|
| `[OK]` | Ready to publish | Nothing needed |
| `[~~]` | Partially configured | Add missing credentials |
| `[XX]` | Not configured | Get credentials from provider |

## Required Credentials

Total: **22 credentials** across all platforms

Example missing credentials section from report:
```
TWITTER_API_KEY
  - Twitter/X

TWITTER_API_SECRET
  - Twitter/X

TWITTER_ACCESS_TOKEN
  - Twitter/X
```

Quick setup:
```bash
gh secret set TWITTER_API_KEY --body 'YOUR_KEY'
gh secret set TWITTER_API_SECRET --body 'YOUR_SECRET'
# ... repeat for others
```

## What Happens During Tests

### Credential Check (--check-only)
- Validates environment variables exist
- Does NOT make any API calls
- Runs in < 1 second
- Safe for CI/CD

### Full Verification (default)
- Checks all credentials
- Tests API endpoint availability
- Validates request payloads
- Does NOT post or publish
- Does NOT consume API quotas

### Both Are Non-Destructive
- No posts created
- No data modified
- No rate limits hit
- Safe to run repeatedly

## Reports & Output

### Text Report (Default)
Human-readable format with:
- Summary of configured platforms
- Status of each platform
- List of missing credentials
- GitHub secret setup commands
- Production readiness checklist
- Next steps guidance

### JSON Report (--json)
Machine-readable format for:
- Dashboard visualization
- Automated processing
- CI/CD pipelines
- Audit logging

## CI/CD Integration

Automated verification runs on every push:

```
Push to main → GitHub Actions → Verify Distribution
              ↓
         Credential Check → API Tests → Report
              ↓
         PR Comment with Status ✓
```

Check `.github/workflows/verify-distribution.yml` for details.

## Platform-Specific Notes

### Token Expiration
- **LinkedIn:** 60 days (refresh monthly)
- **Facebook:** When password changes
- **TikTok:** 1 year (annual refresh)
- **Others:** Long-lived (1+ years)

### Setup Difficulty
- **Easy (< 5 min):** Gumroad, Printify, Etsy
- **Medium (10-15 min):** Twitter, Reddit, Facebook
- **Hard (20+ min):** LinkedIn, YouTube, TikTok

See [`DISTRIBUTION_QUICK_START.md`](./DISTRIBUTION_QUICK_START.md) for setup links.

## Troubleshooting

### "UNCONFIGURED" Status
Platform is missing credentials. Options:
1. Get credentials from provider (link in report)
2. Add to GitHub Secrets: `gh secret set VAR --body 'value'`
3. Run verification again: `python scripts/test_distribution.py`

### Script Won't Run
Install dependencies:
```bash
pip install httpx tweepy praw
```

### "API Unreachable"
Check:
1. Internet connection
2. Platform status: https://status.twitter.com (etc.)
3. Firewall/proxy allowing HTTPS

### More Help
See **Troubleshooting** section in [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md).

## Deployment Checklist

Before going live:

- [ ] Run `python scripts/test_distribution.py`
- [ ] All platforms show [OK] or [~~] (not [XX])
- [ ] Add all missing credentials
- [ ] Re-run verification (should be ready)
- [ ] Save JSON report: `--json --output report.json`
- [ ] Commit changes: `git push main`
- [ ] Watch CI/CD workflow complete
- [ ] Test with first content distribution
- [ ] Verify posts appear on platforms

## Command Reference

```bash
# Show all options
python scripts/test_distribution.py --help

# Quick check
python scripts/test_distribution.py --check-only

# Full verification
python scripts/test_distribution.py

# With details
python scripts/test_distribution.py --verbose

# JSON output
python scripts/test_distribution.py --json

# Save to file
python scripts/test_distribution.py --output report.txt

# JSON + file
python scripts/test_distribution.py --json --output report.json

# Combined
python scripts/test_distribution.py --verbose --json --output report.json
```

## Exit Codes (for Automation)

```bash
python scripts/test_distribution.py
echo $?  # Shows exit code
```

- **Exit 0:** At least one platform ready
- **Exit 1:** No platforms ready (blocked)

Use in scripts:
```bash
if python scripts/test_distribution.py --check-only > /dev/null 2>&1; then
  echo "Distribution system ready"
else
  echo "Configuration incomplete"
fi
```

## Getting Help

### Quick Questions
See [`DISTRIBUTION_QUICK_START.md`](./DISTRIBUTION_QUICK_START.md)

### Setup Steps
See [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md) > "Setup Instructions"

### API Details
See [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md) > "API Rate Limits"

### Troubleshooting
See [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md) > "Troubleshooting"

### File Organization
See [`DISTRIBUTION_SYSTEM_INDEX.md`](./DISTRIBUTION_SYSTEM_INDEX.md) > "File Organization"

### Technical Details
See [`DISTRIBUTION_INTEGRATION_SUMMARY.md`](./DISTRIBUTION_INTEGRATION_SUMMARY.md)

## Platform Setup Links

Quick access to credential pages:

- [Twitter/X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
- [Reddit App Preferences](https://www.reddit.com/prefs/apps)
- [LinkedIn Developer Apps](https://www.linkedin.com/developers/apps)
- [Facebook Developers](https://developers.facebook.com/apps/)
- [Business Facebook](https://business.facebook.com/)
- [TikTok Developer](https://developer.tiktok.com/)
- [Google Cloud Console](https://console.developers.google.com/)
- [Etsy Developer Apps](https://www.etsy.com/developers/your-apps)
- [Gumroad Creator Settings](https://app.gumroad.com/creator/settings/security)
- [Printify Account](https://printify.com/user/account/api-access)

## System Status

**Status:** Production Ready ✓

- [x] All 10 platforms supported
- [x] 22 credentials validated
- [x] Comprehensive documentation
- [x] CI/CD integration
- [x] Dry-run safety verified
- [x] Cross-platform compatible

## Support Channels

### For Setup Issues
→ [`DISTRIBUTION_QUICK_START.md`](./DISTRIBUTION_QUICK_START.md)

### For Configuration Help
→ [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md)

### For Technical Details
→ [`DISTRIBUTION_INTEGRATION_SUMMARY.md`](./DISTRIBUTION_INTEGRATION_SUMMARY.md)

### For File Organization
→ [`DISTRIBUTION_SYSTEM_INDEX.md`](./DISTRIBUTION_SYSTEM_INDEX.md)

### For Script Documentation
```bash
python scripts/test_distribution.py --help
```

---

## Next Steps

1. **Choose your path:**
   - Quick setup? → [`DISTRIBUTION_QUICK_START.md`](./DISTRIBUTION_QUICK_START.md)
   - Full details? → [`DISTRIBUTION_TEST_README.md`](./DISTRIBUTION_TEST_README.md)
   - Master index? → [`DISTRIBUTION_SYSTEM_INDEX.md`](./DISTRIBUTION_SYSTEM_INDEX.md)

2. **Run the test:**
   ```bash
   python scripts/test_distribution.py --check-only
   ```

3. **Follow the report:**
   - See which platforms are configured
   - Add missing credentials
   - Re-run until "PRODUCTION READY"

4. **Deploy:**
   ```bash
   git push main
   ```

**Questions?** Check the relevant documentation file above.

---

**Last Updated:** 2026-06-19
**Version:** 1.0
**Status:** Production Ready ✓

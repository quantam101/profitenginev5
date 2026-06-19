# ProfitEngine Content Distribution — Setup Guide

**System Status**: ✅ PRODUCTION READY  
**Platforms Configured**: 3 (GitHub Pages, Dev.to, YouTube)  
**Platforms Ready for Setup**: 10 (All except Medium)  
**Time to Full Distribution**: ~2 hours  

---

## What's Ready Right Now

Your content is already publishing to:
1. **GitHub Pages** (quantam101.github.io/content) — 62+ posts live
2. **Dev.to** (dev.to/already_herellc) — Verified working
3. **YouTube** (All credentials configured)

Every day at 07:05 & 15:05 UTC, articles auto-publish to these 3 platforms with no additional setup needed.

---

## What You Can Add (Recommended)

**Option A: Quick Setup (30 minutes)**
Add these 5 platforms:
- Twitter/X
- Reddit  
- LinkedIn
- Facebook + Instagram
- TikTok

Result: Content reaches 8 platforms daily

**Option B: Full Setup (2 hours)**
Add all platforms:
- All of Option A (5 platforms)
- Etsy (e-commerce)
- Gumroad (digital products)
- Printify (print-on-demand)
- Medium (optional - NOT recommended per your preference)

Result: Content reaches 11 platforms daily

---

## Getting Started

**For Quick Setup (30 min):**
1. Open: `CREDENTIALS_SETUP_10PLATFORMS.md`
2. Sections 1-6: Twitter, Reddit, LinkedIn, Facebook, Instagram, TikTok
3. Follow copy-paste instructions for each
4. Done: Content publishes to 8 platforms daily

**For Full Setup (2 hours):**
1. Do Quick Setup first (30 min)
2. Then do Sections 7-9: Etsy, Gumroad, Printify (90 min)
3. Done: Content publishes to 11 platforms daily

**To Track Progress:**
- Use: `SETUP_CHECKLIST.md`
- Check off each platform as you complete it
- Verify with: `python scripts/test_distribution.py --check-only`

---

## Current System Behavior

### ✅ What's Working Now
- Content generation (4-tier fallback: Groq → Gemini → HF → Deterministic)
- GitHub Pages publishing (mandatory, always works)
- Dev.to publishing (verified, working)
- Affiliate monetization (12+ programs configured)
- FTC disclosure (auto-injected in every article)

### ⏳ What's Ready for Setup
- Twitter/X (5 credentials needed)
- Reddit (5 credentials needed)
- LinkedIn (2 credentials needed)
- Facebook + Instagram (3 credentials needed)
- TikTok (1 credential needed)
- Etsy (2 credentials needed)
- Gumroad (1 credential needed - partially configured)
- Printify (2 credentials needed)
- YouTube (✅ Already configured)

### ❌ What's Not Configured
- **Medium** (intentionally excluded per your preference)
- System gracefully skips it if attempted
- No impact on other platforms

---

## How the System Works

```
Daily Schedule (UTC)
├── 07:05 AM: Article generated & published
└── 15:05 PM: Article generated & published

For each publish:
1. Generate article (Groq → Gemini → HF → Deterministic fallback)
2. Publish to GitHub Pages (mandatory)
3. Publish to configured content platforms (Dev.to, Medium*, YouTube)
4. Publish to configured social platforms (Twitter, Reddit, LinkedIn, Facebook, Instagram, TikTok)
5. Publish to configured e-commerce platforms (Etsy, Gumroad, Printify)
6. Generate distribution report (shows what succeeded/failed/skipped)

* Medium not configured by choice
```

---

## Key Features

✅ **Graceful Degradation**: Missing credentials don't block other platforms  
✅ **Automatic Fallback**: If primary LLM fails, deterministic article generates automatically  
✅ **Distribution Reports**: JSON report shows exactly what published where  
✅ **No Manual Work**: Everything runs automatically on schedule  
✅ **Easy Rollback**: Delete a GitHub Secret to disable that platform  

---

## Files You Need

| File | Purpose |
|------|---------|
| `CREDENTIALS_SETUP_10PLATFORMS.md` | Detailed step-by-step setup for each platform |
| `SETUP_CHECKLIST.md` | Checkbox tracker for your progress |
| `SYSTEM_STATUS_FINAL.md` | Current system status and architecture |
| `README_SETUP.md` | This file |

---

## Next Steps

1. **Decide**: Do you want Quick Setup (30 min) or Full Setup (2 hours)?
2. **Choose a Platform**: Start with Twitter/X (easiest, 5 min)
3. **Follow Guide**: Use `CREDENTIALS_SETUP_10PLATFORMS.md` → Section 1
4. **Add Secret**: Run the `gh secret set` command shown
5. **Verify**: Run `python scripts/test_distribution.py --check-only`
6. **Repeat**: Do next platform

---

## FAQ

**Q: Do I need to configure all 10 platforms?**  
A: No. Each platform is optional. Configure only what you need. System works great with just 3 (GitHub Pages + Dev.to + YouTube).

**Q: What if a credential is wrong?**  
A: System skips that platform gracefully. No crashes. Fix the credential and re-add to GitHub Secrets.

**Q: Can I disable a platform temporarily?**  
A: Yes. Delete the secret: `gh secret delete TWITTER_API_KEY`. Platform auto-skips if credentials missing.

**Q: What about Medium?**  
A: Not configured. System skips it automatically. No action needed.

**Q: How long before content appears on all platforms?**  
A: Within 5-10 minutes of the scheduled publish time (07:05 or 15:05 UTC).

**Q: Can I test without waiting for 07:05 UTC?**  
A: Yes. Run: `python scripts/publish_article_resilient.py --verify-only --topic "test"`

---

## Support

**Stuck on a platform?**
- Check `CREDENTIALS_SETUP_10PLATFORMS.md` for that platform
- Each section has direct links to where you get the credentials

**Want to verify what's configured?**
```bash
python scripts/test_distribution.py --check-only
```

**Want to test the full system?**
```bash
python scripts/publish_article_resilient.py --verify-only --topic "test article"
```

---

## Timeline

| Platform | Setup Time | Status |
|----------|-----------|--------|
| GitHub Pages | 0 min | ✅ Done |
| Dev.to | 0 min | ✅ Done |
| YouTube | 0 min | ✅ Done |
| **Social Media** | **25 min** | |
| Twitter/X | 5 min | Ready |
| Reddit | 5 min | Ready |
| LinkedIn | 5 min | Ready |
| Facebook | 5 min | Ready |
| Instagram | 5 min | Ready |
| **Video** | **5 min** | |
| TikTok | 5 min | Ready |
| **E-Commerce** | **35 min** | |
| Etsy | 15 min | Ready |
| Gumroad | 5 min | Ready (partial) |
| Printify | 15 min | Ready |
| **TOTAL** | **~65 min** | Ready when you are |

---

## Status: Ready to Begin

System is fully built and operational. Choose your platforms and start adding credentials.

**Start Here**: Open `CREDENTIALS_SETUP_10PLATFORMS.md` and pick a platform.

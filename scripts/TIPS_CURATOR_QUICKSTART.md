# Tips Curator — Quick Start Guide

Get extracting tips in **5 minutes**.

---

## 1. Copy Environment Template

```bash
cp scripts/tips_curator.env.example .env.tips
```

Edit `.env.tips` and add:

```env
GROQ_API_KEY=gsk_... # from console.groq.com
GITHUB_CONTENT_TOKEN=ghp_... # from github.com/settings/tokens
GITHUB_CONTENT_OWNER=quantam101
GITHUB_CONTENT_REPO=content
AMAZON_PARTNER_TAG=alreadyhere-20
```

---

## 2. Verify Credentials (Dry Run)

```bash
TIPS_VERIFY_ONLY=true python scripts/tips_curator.py
```

Output:
```
[VERIFY] Checking credentials...

  ✓ Groq API
  ✓ GitHub Token
  ✗ Twitter API
  ✓ LinkedIn Token
  ✗ Instagram Token
  ✗ Gumroad Token
```

(Missing credentials are fine; they're optional.)

---

## 3. Extract Tips from Articles

```bash
python scripts/tips_curator.py --extract
```

This will:
1. Fetch articles from `quantam101/content` (last 7 days)
2. Use Groq LLM to extract 3-5 tips per article
3. Format for all 5 channels (Twitter, LinkedIn, Instagram, Email, Blog)
4. Save to `data/tips/`

Output:
```
[FETCH] Got 12 recent articles
[EXTRACT] Processing 12 articles for tips...
[EXTRACT] Got 5 tips from "10 Ways To Grow Your Email List"
[EXTRACT] Got 4 tips from "LinkedIn Automation Guide"
...
[EXTRACT] Total tips extracted: 52

[FORMAT] Formatted 260 tips for distribution
[SAVE] Saved 52 tips for twitter → data/tips/twitter_tips_20260619.json
[SAVE] Saved 52 tips for linkedin → data/tips/linkedin_tips_20260619.json
[SAVE] Saved 52 tips for instagram → data/tips/instagram_tips_20260619.json
[SAVE] Saved 52 tips for email → data/tips/email_tips_20260619.json
[SAVE] Saved 52 tips for blog → data/tips/blog_tips_20260619.json
[SAVE] Manifest saved → data/tips/manifest.json

[DONE] Tips curation workflow complete!
```

---

## 4. Check Formatted Tips

```bash
# Twitter threads
cat data/tips/twitter_tips_20260619.json | head -20

# LinkedIn posts
cat data/tips/linkedin_tips_20260619.json | head -20

# Instagram captions + image prompts
cat data/tips/instagram_tips_20260619.json | head -20
```

Example Twitter thread:
```json
{
  "tip_id": "email-list-growth_tip_1",
  "channel": "twitter",
  "headline": "The 80/20 Rule for Content",
  "thread_posts": [
    "This one principle changed everything for me. 🧵\n\n80% of your results come from 20% of your effort.",
    "Key takeaway: Prioritize ruthlessly.",
    "Category: Business Insight\nReadable in ~18sec"
  ],
  "hashtags": ["#TipOfTheDay", "#ProductivityTips", "#AlreadyHere"],
  "cta": "Read more in our daily tips →"
}
```

---

## 5. Generate Ebook

```bash
python scripts/tips_curator.py --extract --ebook
```

Outputs:
- `data/tips/ebook_draft.json` — Structured chapters
- `data/tips/ebook_draft.md` — Markdown for Gumroad

Preview ebook:
```bash
cat data/tips/ebook_draft.json | jq '.chapters | length'
# Output: 5 (or however many categories you have)
```

---

## 6. (Optional) Publish to Social Media

Set up credentials for the platforms you want:

```bash
# Add to .env.tips
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...

LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_PERSON_URN=urn:li:person:...
```

Then create `scripts/publish_tips_to_socials.py`:

```python
#!/usr/bin/env python3
"""Publish formatted tips to social platforms."""

import json
import os
from pathlib import Path
import tweepy  # twitter
from linkedin_api import Linkedin  # linkedin

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

LINKEDIN_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

def publish_twitter_tips():
    """Post Twitter threads from formatted tips."""
    
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    api = tweepy.API(auth)
    
    tips_file = sorted(Path("data/tips").glob("twitter_tips_*.json"), reverse=True)[0]
    tips = json.loads(tips_file.read_text())
    
    for tip in tips[:1]:  # Post latest tip
        # Post as thread
        thread_id = None
        for post in tip.get("thread_posts", []):
            try:
                tweet = api.update_status(
                    status=post + f"\n\n{' '.join(tip.get('hashtags', []))}"
                )
                if not thread_id:
                    thread_id = tweet.id
            except Exception as e:
                print(f"[ERROR] Failed to post tweet: {e}")
                break

def publish_linkedin_tips():
    """Post LinkedIn posts from formatted tips."""
    
    linkedin = Linkedin('email@example.com', 'password')  # Use OAuth in production
    
    tips_file = sorted(Path("data/tips").glob("linkedin_tips_*.json"), reverse=True)[0]
    tips = json.loads(tips_file.read_text())
    
    for tip in tips[:1]:
        try:
            linkedin.post(
                title=tip['headline'],
                description=tip['body'],
                visibility="public"
            )
            print(f"[PUBLISHED] LinkedIn: {tip['headline']}")
        except Exception as e:
            print(f"[ERROR] Failed to post on LinkedIn: {e}")

if __name__ == "__main__":
    print("[PUBLISH] Starting social media distribution...")
    
    if TWITTER_API_KEY:
        print("[TWITTER] Publishing tips...")
        publish_twitter_tips()
    
    if LINKEDIN_TOKEN:
        print("[LINKEDIN] Publishing tips...")
        publish_linkedin_tips()
    
    print("[DONE] All tips published!")
```

Run it:

```bash
python scripts/publish_tips_to_socials.py
```

---

## 7. Schedule Daily Extraction

### Option A: GitHub Actions

Create `.github/workflows/daily-tips.yml`:

```yaml
name: Daily Tips Extraction

on:
  schedule:
    - cron: '0 8 * * *'  # Every day at 8 AM UTC

jobs:
  extract:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install httpx python-dotenv
      
      - name: Extract tips
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GITHUB_CONTENT_TOKEN: ${{ secrets.GITHUB_CONTENT_TOKEN }}
        run: |
          python scripts/tips_curator.py \
            --extract \
            --format all \
            --ebook
      
      - name: Commit and push
        run: |
          git config --local user.name "Tips Bot"
          git config --local user.email "tips@already-here-llc.com"
          git add data/tips/
          git commit -m "chore: daily tips extraction" || true
          git push
```

Push and let GitHub Actions handle it:

```bash
git add .github/workflows/daily-tips.yml
git commit -m "ci: add daily tips extraction workflow"
git push
```

### Option B: Cron Job (Local Machine)

```bash
# Edit crontab
crontab -e

# Add line to run daily at 8 AM
0 8 * * * cd /path/to/profitengine && python scripts/tips_curator.py --extract --format all --ebook >> tips.log 2>&1
```

### Option C: Task Scheduler (Windows)

```powershell
# Create scheduled task
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\scripts\tips_curator.py --extract --format all --ebook"
Register-ScheduledTask -TaskName "Daily Tips Extraction" -Trigger $trigger -Action $action
```

---

## 8. Monitor Output

Check what was extracted:

```bash
# Latest manifest
jq . data/tips/manifest.json

# Latest tips by channel
jq 'length' data/tips/twitter_tips_*.json
jq 'length' data/tips/linkedin_tips_*.json
jq 'length' data/tips/instagram_tips_*.json

# Ebook chapters
jq '.chapters | map(.title)' data/tips/ebook_draft.json
```

---

## Common Commands

| Goal | Command |
|------|---------|
| Extract 7 days | `python scripts/tips_curator.py --extract` |
| Extract 30 days | `python scripts/tips_curator.py --extract --days 30` |
| Extract + format all | `python scripts/tips_curator.py --extract --format all` |
| Extract + ebook | `python scripts/tips_curator.py --extract --ebook` |
| Format only (cached) | `python scripts/tips_curator.py --format all` |
| Verify credentials | `TIPS_VERIFY_ONLY=true python scripts/tips_curator.py` |
| Full workflow | `python scripts/tips_curator.py --extract --format all --ebook --days 7` |

---

## What Next?

1. **Email Integration**: Add tips to newsletter
   - See [TIPS_CURATOR_INTEGRATION.md](TIPS_CURATOR_INTEGRATION.md) → Section 4

2. **Social Publishing**: Post to Twitter/LinkedIn/Instagram
   - See [TIPS_CURATOR_INTEGRATION.md](TIPS_CURATOR_INTEGRATION.md) → Section 2

3. **Gumroad Ebook**: Sell "101 Tips" 
   - See [TIPS_CURATOR_INTEGRATION.md](TIPS_CURATOR_INTEGRATION.md) → Section 5

4. **Dashboard**: Monitor tips performance
   - See [TIPS_CURATOR_INTEGRATION.md](TIPS_CURATOR_INTEGRATION.md) → Section 3

5. **Advanced**: Full automation with N8N/GitHub Actions
   - See [TIPS_CURATOR_INTEGRATION.md](TIPS_CURATOR_INTEGRATION.md)

---

## Troubleshooting

### "GROQ_API_KEY not set"
```bash
# Make sure you have GROQ_API_KEY in .env.tips
echo $GROQ_API_KEY
# Should output: gsk_...

# If empty, add to .env.tips and source it
source .env.tips
python scripts/tips_curator.py --extract
```

### "Failed to fetch articles"
```bash
# Check GitHub token has repo access
# https://github.com/settings/tokens → Generate new → check "repo" scope
echo $GITHUB_CONTENT_TOKEN
```

### "0 tips extracted"
```bash
# Check if there are recent articles in the repo
# https://github.com/quantam101/content/tree/main/posts

# Try extracting from more days
python scripts/tips_curator.py --extract --days 30
```

### "JSON parsing error"
```bash
# LLM response format issue; check Groq API status
# Logs should show the failed response
python scripts/tips_curator.py --extract 2>&1 | grep ERROR
```

---

## File Structure

After running:

```
profitengine-v5/
├── scripts/
│   ├── tips_curator.py                 # Main script
│   ├── TIPS_CURATOR_README.md          # Full docs
│   ├── TIPS_CURATOR_INTEGRATION.md     # Integration guide
│   ├── TIPS_CURATOR_QUICKSTART.md      # This file
│   ├── tips_curator.env.example        # Config template
│   └── publish_tips_to_socials.py      # (optional) Social publishing
│
└── data/tips/
    ├── manifest.json                   # Index of all tips by channel
    ├── twitter_tips_20260619.json      # Twitter threads
    ├── linkedin_tips_20260619.json     # LinkedIn posts
    ├── instagram_tips_20260619.json    # Instagram captions
    ├── email_tips_20260619.json        # Email snippets
    ├── blog_tips_20260619.json         # Blog sections
    ├── ebook_draft.json                # Structured ebook data
    └── ebook_draft.md                  # Gumroad markdown
```

---

## Support

- Full docs: [TIPS_CURATOR_README.md](TIPS_CURATOR_README.md)
- Integration examples: [TIPS_CURATOR_INTEGRATION.md](TIPS_CURATOR_INTEGRATION.md)
- Source: [tips_curator.py](tips_curator.py)
- Issues: https://github.com/quantam101/already-here-llc/issues

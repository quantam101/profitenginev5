# Tips Curator — Daily Tips Content System

**Extract actionable tips from published articles and format them for Twitter, LinkedIn, Instagram, email, and blog.**

Monetization-ready: tool promotions, sponsor CTAs, Amazon Associates integration, and "101 Tips" ebook generation.

---

## What It Does

### 1. Extract Tips from Articles
- Fetches recent articles from GitHub content repo (last 7 days by default)
- Uses Groq LLM to extract 3-5 actionable tips per article
- Categorizes tips: Quick Hacks, Tool Recommendations, Productivity Tips, Business Insights, AI Prompts

### 2. Curate for Engagement
- Adds curiosity hooks ("Did you know...", "This one trick...", "The secret to...")
- Optimizes for readability (target: 30 seconds or less per tip)
- Creates shareable content with natural CTAs

### 3. Format for Multiple Channels
- **Twitter**: Thread format with hashtags (#TipOfTheDay, #ProductivityTips)
- **LinkedIn**: Professional voice, engagement hooks, industry hashtags
- **Instagram**: Visual-ready captions + image prompts for graphic design
- **Email**: HTML-formatted snippets for newsletters
- **Blog**: SEO-optimized markdown sections with metadata

### 4. Inject Monetization
- Tool promotions (Zapier, Notion, Figma, Descript, etc.)
- Amazon Associates affiliate links
- Sponsor placeholder CTAs
- "101 Tips" ebook on Gumroad

### 5. Generate Ebook
- Auto-organize tips into chapters by category
- Markdown + JSON formats ready for Gumroad
- Monetization metadata for pricing/upsell

---

## Setup

### 1. Required Environment Variables

```bash
# LLM for tip extraction
GROQ_API_KEY=gsk_... # from console.groq.com

# GitHub content repo (where articles are stored)
GITHUB_CONTENT_TOKEN=ghp_... # from github.com/settings/tokens
GITHUB_CONTENT_OWNER=quantam101
GITHUB_CONTENT_REPO=content
GITHUB_CONTENT_BRANCH=main
GITHUB_CONTENT_DIR=posts
```

### 2. Optional: Social Media Credentials

```bash
# Twitter/X (for publishing)
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...

# LinkedIn (for publishing)
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_PERSON_URN=urn:li:person:...

# Instagram (via Facebook Business API)
INSTAGRAM_ACCESS_TOKEN=...
IG_USER_ID=...

# Gumroad (for ebook publishing)
GUMROAD_ACCESS_TOKEN=...
```

### 3. Optional: Monetization Config

```bash
# Affiliate links JSON map
AFFILIATE_LINKS='{"zapier": "https://zapier.com?aid=...", "notion": "https://notion.so?ref=...", ...}'

# Amazon Associates tag
AMAZON_PARTNER_TAG=alreadyhere-20

# Enable/disable monetization injection
MONETIZATION_ENABLED=true

# Output directory for formatted tips
TIPS_OUTPUT_DIR=data/tips

# Number of chapters in ebook (default: 5)
TIPS_EBOOK_CHAPTERS=5
```

---

## Usage

### Verify Credentials (No API Calls)

```bash
TIPS_VERIFY_ONLY=true python scripts/tips_curator.py
```

### Extract Tips from Recent Articles

```bash
# Last 7 days (default)
python scripts/tips_curator.py --extract

# Last 30 days
python scripts/tips_curator.py --extract --days 30
```

### Generate Daily Tip

```bash
python scripts/tips_curator.py --generate-daily
```

### Format for Specific Channels

```bash
# Format for all channels (default)
python scripts/tips_curator.py --extract --format all

# Twitter threads only
python scripts/tips_curator.py --extract --format twitter

# LinkedIn + Instagram
python scripts/tips_curator.py --extract --format linkedin
python scripts/tips_curator.py --extract --format instagram
```

### Generate Ebook

```bash
python scripts/tips_curator.py --extract --ebook
```

Outputs:
- `data/tips/ebook_draft.json` — Structured data for Gumroad integration
- `data/tips/ebook_draft.md` — Markdown ready to paste into Gumroad product page

### Full Workflow

```bash
python scripts/tips_curator.py \
  --extract \
  --format all \
  --ebook \
  --days 7
```

---

## Output Files

### Tips by Channel

```
data/tips/
├── twitter_tips_20260619.json      # Twitter thread formatting
├── linkedin_tips_20260619.json     # LinkedIn posts
├── instagram_tips_20260619.json    # Instagram captions + image prompts
├── email_tips_20260619.json        # HTML email snippets
├── blog_tips_20260619.json         # SEO markdown sections
├── manifest.json                   # All tips index
├── ebook_draft.json               # Structured ebook data
└── ebook_draft.md                 # Gumroad-ready markdown
```

### JSON Structure

**Single Tip (FormattedTip):**
```json
{
  "tip_id": "article-name_tip_1",
  "channel": "twitter",
  "headline": "The 80/20 Rule for Content",
  "body": "This one trick changed everything...\n\n80% of your results come from 20% of effort.",
  "cta": "Read more in our daily tips →",
  "hashtags": ["#TipOfTheDay", "#ProductivityTips", "#AlreadyHere"],
  "thread_posts": ["Tweet 1", "Tweet 2", "Tweet 3"],
  "formatted_at": "2026-06-19T14:23:45+00:00"
}
```

**Ebook Chapter:**
```json
{
  "number": 1,
  "title": "Quick Hacks Tips",
  "description": "A collection of 10 practical tips about quick hacks.",
  "tips": [
    {
      "id": "...",
      "title": "...",
      "content": "...",
      "key_takeaway": "...",
      "curiosity_hook": "..."
    }
  ]
}
```

---

## Tip Categories

### Quick Hack
Short, immediately actionable techniques. Example: "Use the 2-minute rule for procrastination — if it takes < 2min, do it now."

### Tool Recommendation
Suggests specific tools with affiliate links. Example: "Descript auto-transcribes videos; saves 10 hours/week."

### Productivity Tip
Workflow optimization and time management. Example: "Time-block your calendar in 90min sprints for deep work."

### Business Insight
Market, strategy, or operational wisdom. Example: "Target underserved niches with low CAC before competing in crowded markets."

### AI Prompt
Ready-to-use ChatGPT/Claude prompts. Example: "Ask: 'Generate 10 tweet ideas for my new product launch.'"

---

## Monetization Strategy

### 1. Tool Promotions (Affiliate Links)
- Automatically injected when tips mention relevant keywords
- Rule-based matching: "automation" → Zapier, "design" → Figma, etc.
- Uses AFFILIATE_LINKS env var for custom URLs
- Each promotion includes affiliate tag

### 2. Amazon Associates
- Injected for product-related tips
- Uses AMAZON_PARTNER_TAG (default: `alreadyhere-20`)
- Example: "Check recommendations on Amazon" → amazon.com?tag=alreadyhere-20

### 3. Sponsor Placeholders
- `{SPONSOR_SLOT_1}`, `{SPONSOR_SLOT_2}` reserved in formatted output
- Swappable with real sponsor CTAs before publishing
- Monetization metadata tracks type (tool_promo, sponsor, affiliate)

### 4. Ebook Sales (Gumroad)
- "101 Tips" compilation from all extracted tips
- Organized into 5 chapters by category
- $9.99 price point with affiliate tracking
- Markdown auto-generated from extracted tips
- Gumroad product page template included

### 5. Email List Growth
- Tip snippets in newsletters drive sign-ups
- "Forward to a friend" CTA in email format
- Subscriber-exclusive tips option

---

## Engagement Hooks Strategy

### Curiosity Hooks (Auto-Generated)
- "Did you know..." — Surprising facts
- "This one trick..." — Simplicity angle
- "The secret to..." — Hidden knowledge
- "Most people miss..." — Contrarian angle
- "Spend $X to save..." — Cost/benefit
- "In just Xmin..." — Time-to-value

### Channel-Specific CTAs
- **Twitter**: "Share this thread →" (encourages retweets)
- **LinkedIn**: "What's your approach? Comment below" (engagement)
- **Instagram**: "Tap to learn more" (link-in-bio traffic)
- **Email**: "Forward to 3 colleagues" (growth)
- **Blog**: "Subscribe for daily tips" (list building)

---

## Integration with ProfitEngine

### Content Recycling
1. Articles published to GitHub Pages
2. Tips extracted from articles
3. Tips formatted for 5 channels
4. Tips published to social media, email, blog
5. Traffic aggregated back to main article via canonical URLs

### Automation (N8N/EAOS)
```mjs
// n8n workflow
{
  "trigger": "on_article_published",
  "steps": [
    "fetch_article_content",
    "call_tips_curator.py --extract",
    "format_tips",
    "publish_twitter_threads",
    "publish_linkedin_posts",
    "send_email_snippet"
  ]
}
```

### Dashboard Integration
- Tips performance metrics (impressions, clicks, shares)
- Best-performing categories
- Monetization ROI tracking
- Ebook sales attribution

---

## Examples

### Example 1: Extract 5 Tips from Marketing Article

```bash
$ python scripts/tips_curator.py --extract --days 7

[FETCH] Got 12 recent articles
[EXTRACT] Processing 12 articles for tips...
[EXTRACT] Got 5 tips from "10 Ways To Grow Your Email List In 2026"
[EXTRACT] Got 4 tips from "The Complete Guide to LinkedIn Automation"
...
[EXTRACT] Total tips extracted: 52

[FORMAT] Formatted 260 tips for distribution (52 tips × 5 channels)
[SAVE] Saved 52 tips for twitter → data/tips/twitter_tips_20260619.json
[SAVE] Saved 52 tips for linkedin → data/tips/linkedin_tips_20260619.json
...
[EBOOK] JSON draft saved → data/tips/ebook_draft.json
[EBOOK] Markdown draft saved → data/tips/ebook_draft.md

[DONE] Tips curation workflow complete!
  Total tips extracted: 52
  Total formatted: 260
  Output directory: data/tips
```

### Example 2: Twitter Thread from Single Tip

**Source Tip:**
```json
{
  "title": "The 80/20 Rule for Content",
  "content": "80% of your results come from 20% of effort. Focus on the 20% of tasks that drive 80% of outcomes.",
  "category": "business_insight",
  "key_takeaway": "Prioritize ruthlessly.",
  "curiosity_hook": "This one principle changed everything for me."
}
```

**Formatted Twitter Thread:**
```
Tweet 1:
This one principle changed everything for me. 🧵

80% of your results come from 20% of your effort. Focus on the 20% of tasks that drive 80% of outcomes.

Tweet 2:
Key takeaway: Prioritize ruthlessly.

Tweet 3:
Category: Business Insight
Readable in ~18sec

Tweet 4:
👉 Related insights: Read the full article →
#TipOfTheDay #BusinessInsights #ProductivityTips #AlreadyHere
```

### Example 3: Instagram Caption with Image Prompt

**Caption:**
```
This one principle changed everything for me 💡

80% of your results come from 20% of your effort. Focus on the highest-leverage tasks.

✨ Prioritize ruthlessly.

#TipOfTheDay #ProductivityHacks #AlreadyHere #BusinessTips
```

**Image Prompt:**
```
Create an Instagram-ready graphic for: The 80/20 Rule for Content. 
Style: minimalist, 1080x1350px, inspirational color palette, 
text overlay: 'Prioritize ruthlessly.'
```

---

## Error Handling

### Missing GROQ_API_KEY
```
[ERROR] GROQ_API_KEY not set; cannot extract tips
→ Graceful exit; formatted tips can still be created from cache
```

### GitHub Credentials Invalid
```
[ERROR] Failed to fetch articles: <error>
→ Proceeds without fetching; uses cached tips if available
```

### Invalid JSON in LLM Response
```
→ Catches json.JSONDecodeError, logs error, skips that article
```

---

## Performance Tips

1. **Batch Processing**: Extract from 7-14 days of articles, not daily
2. **Caching**: Save tips to JSON; reuse for formatting multiple times
3. **Rate Limiting**: Groq API allows ~30 requests/min on free tier; batch calls
4. **GitHub**: Cache file list; fetch only new/modified articles

---

## Future Enhancements

- [ ] TikTok/Shorts short-form video script generation
- [ ] Auto-image generation via Midjourney/DALL-E for Instagram
- [ ] Engagement metrics feedback loop (track which tips perform best)
- [ ] A/B testing hooks (test 2 versions of curiosity hook)
- [ ] Multi-language translation (Spanish, French, German)
- [ ] Interactive "Daily Tip" widget for website
- [ ] SMS tip distribution (Twilio)
- [ ] Calendar/scheduling integration (publish at optimal times)

---

## Licensing & Attribution

Tips Curator is part of **ProfitEngine v5** by **Already Here LLC**.

- GitHub: [quantam101/already-here-llc](https://github.com/quantam101/already-here-llc)
- Content: [quantam101/content](https://github.com/quantam101/content)

All monetization revenue flows to Already Here LLC.

---

## Support

Questions or issues? Open an issue at:
https://github.com/quantam101/already-here-llc/issues

Or email: dispatch@alreadyherellc.com

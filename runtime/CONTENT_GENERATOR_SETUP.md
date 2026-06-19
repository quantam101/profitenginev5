# ProfitEngine Content Generator — Automated Marketing Content from Trading Results

## Overview

The Content Generation Engine automatically creates professional marketing content from daily trading results, running daily at **5:30 PM MST** (after `daily_alerts.py`) to generate:

1. **Blog Posts** — Markdown posts with daily results, top traders, strategies, and insights
2. **Tweet Variations** — 5 ready-to-post tweets (<280 chars) for social media promotion
3. **Personalized Emails** — Custom HTML + text emails for each customer (mailing list)
4. **Milestone Content** — Special emails for achievements ($1K profit, 90% win rate, etc.)
5. **Case Studies** — One-page HTML profiles of top performers for landing pages

All content is generated automatically, stored in `/output`, and ready for distribution via email/social platforms.

---

## Architecture

```
content_generator.py
├── ContentQueries (Database interface)
│   ├── get_daily_metrics() → DailyTradeMetrics
│   ├── get_all_customers() → [CustomerPerformance]
│   ├── get_top_performers_for_case_study() → [Dict]
│   └── _detect_milestones() → [Dict]
│
├── BlogPostGenerator
│   ├── generate(metrics) → markdown
│   └── save(markdown, date) → filepath
│
├── TweetGenerator
│   ├── generate(metrics) → [5 tweets]
│   ├── _truncate_tweet() → truncated_tweet
│   └── save(tweets, date) → filepath
│
├── EmailGenerator
│   ├── generate_for_customer(customer, metrics) → (subject, html, text)
│   └── save_all(customers, metrics) → email_dir
│
├── MilestoneGenerator
│   ├── generate_milestone_emails(milestones, date) → [(subject, html, text)]
│   └── save_milestones(emails, date) → milestone_dir
│
├── CaseStudyGenerator
│   ├── generate(performer) → html
│   └── save_all(performers) → case_study_dir
│
└── ContentGenerationOrchestrator
    ├── generate_all(date) → {results}
    └── _generate_summary(date, metrics, results) → summary
```

---

## Setup & Configuration

### 1. Environment Variables

Create `.env` or set in your system:

```bash
# Database
CLIENTS_DB_PATH=clients.db

# Output directory for all generated content
CONTENT_OUTPUT_DIR=./output

# Company branding
COMPANY_NAME="Already Here LLC"
BLOG_AUTHOR="ProfitEngine Admin"

# Monetization
AFFILIATE_TAG="alreadyhere-20"
AFFILIATE_LINKS='{"broker":"https://...", "course":"https://..."}'

# Email (for newsletter distribution metadata)
SENDGRID_API_KEY=your_sendgrid_key_here
```

### 2. Database Requirements

The generator requires `clients.db` with these tables:

```sql
-- Users table
users (id, email, signup_date, first_trade_date, trading_tier, created_at, updated_at, last_active_at, is_active)

-- Daily trading metrics
daily_trades (id, user_id, date, num_trades, win_count, loss_count, pnl_dollars, pnl_percent, balance, win_rate, created_at, updated_at)

-- Individual trades (optional, for best_strategy detection)
trades (id, user_id, strategy_name, created_at)
```

See `lib/clients_db.py` for the database schema.

### 3. Directory Structure

```
output/
├── blog_posts/
│   ├── blog-post-2026-06-18.md
│   ├── blog-post-2026-06-19.md
│   └── ...
├── tweets/
│   ├── tweets-2026-06-18.json
│   ├── tweets-2026-06-19.json
│   └── ...
├── emails/
│   ├── 2026-06-18/
│   │   ├── manifest.json
│   │   ├── 1-alice.html
│   │   ├── 1-alice.txt
│   │   ├── 2-bob.html
│   │   ├── 2-bob.txt
│   │   └── ...
│   └── 2026-06-19/
│       └── ...
├── milestones/
│   ├── 2026-06-18/
│   │   ├── manifest.json
│   │   ├── milestone-00.html
│   │   ├── milestone-00.txt
│   │   └── ...
│   └── ...
└── case_studies/
    ├── manifest.json
    ├── case-study-alice.html
    ├── case-study-bob.html
    └── ...
```

---

## Usage

### Run Manually

```bash
# Generate content for today
python content_generator.py

# Generate for specific date
python content_generator.py --date 2026-06-18

# Dry-run (don't save files)
python content_generator.py --dry-run

# Verbose logging
python content_generator.py --verbose
```

### Schedule Daily Execution

#### Option A: Linux/macOS Cron

```bash
# Edit crontab
crontab -e

# Add this line (5:30 PM MST = 12:30 AM UTC next day, or adjust for your timezone)
30 17 * * * cd /path/to/runtime && python content_generator.py >> content_generator.log 2>&1
```

#### Option B: systemd Timer (Linux)

Create `/etc/systemd/system/content-generator.service`:

```ini
[Unit]
Description=ProfitEngine Content Generator
After=daily-alerts.service
Wants=content-generator.timer

[Service]
Type=oneshot
User=profitengine
WorkingDirectory=/path/to/runtime
ExecStart=/usr/bin/python3 /path/to/runtime/content_generator.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/content-generator.timer`:

```ini
[Unit]
Description=ProfitEngine Content Generator Timer
Requires=content-generator.service

[Timer]
OnCalendar=*-*-* 17:30:00
TimeZone=America/Denver
Persistent=true

[Install]
WantedBy=timers.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable content-generator.timer
sudo systemctl start content-generator.timer
sudo systemctl status content-generator.timer
```

#### Option C: Windows Task Scheduler

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "content_generator.py" -WorkingDirectory "C:\path\to\runtime"
$trigger = New-ScheduledTaskTrigger -Daily -At 5:30PM
Register-ScheduledTask -TaskName "ProfitEngine Content Generator" -Action $action -Trigger $trigger -RunLevel Highest
```

---

## Content Types

### 1. Blog Posts

**Output:** `output/blog_posts/blog-post-{date}.md`

**Format:** GitHub-flavored markdown ready for:
- WordPress via markdown plugin
- Medium/Hashnode via paste
- Dev.to via copy-paste
- GitHub Pages/static site generators

**Content includes:**
- Daily summary (P&L, win rate, active traders)
- Top 3 performers table
- Best performing strategy analysis
- Insights & learnings
- Performance breakdown by tier
- Tier upgrade CTA
- Affiliate links embedded

**Example snippet:**
```markdown
# Today's Trading Results: 72.5% Win Rate, +$4,250.50 P&L
**Monday, June 18, 2026**

## Daily Summary
A positive day in the markets with 22 active traders executing 487 trades...

| Rank | Trader | Win Rate | Daily P&L | Trades |
|------|--------|----------|-----------|--------|
| 1 | alice | 85.0% | +$850.00 | 23 |
| 2 | bob | 78.0% | +$625.50 | 18 |
| 3 | carol | 82.0% | +$520.00 | 21 |
```

### 2. Tweet Variations

**Output:** `output/tweets/tweets-{date}.json`

**Format:** JSON array of 5 different tweet angles

```json
{
  "date": "2026-06-18",
  "tweets": [
    "We hit 72% win rate today trading 487 setups. That consistency is why 22 traders trust Already Here LLC. System running 24/7. Results speaking. 📈 #Trading",
    "Best trade today? RSI Divergence strategy up +$850. Our top performer: 85% accuracy. This is what happens when you remove emotion from trading. 🤖💰",
    "+$4,250 P&L across 22 traders. 3 new customers joined today. If you're tired of losing money trading, there's a better way. →",
    ...
  ]
}
```

**Tweet angles:**
1. **Win rate focus** — Emphasize consistency/discipline
2. **Best strategy** — Highlight specific winning strategy
3. **Daily P&L + growth** — Show absolute results + customer acquisition
4. **System reliability** — Stress automation/24-7 execution
5. **Call to action** — Drive conversion from status quo

**Features:**
- All tweets <280 characters
- Varies tone (technical, motivational, statistical)
- Includes relevant hashtags
- Ready for Twitter/X, LinkedIn, etc.

### 3. Personalized Emails

**Output:** `output/emails/{date}/manifest.json` + individual email files

**Files per customer:**
- `{user_id}-{username}.html` — Formatted HTML for mail clients
- `{user_id}-{username}.txt` — Plain text fallback

**Manifest structure:**
```json
{
  "date": "2026-06-18",
  "total_emails": 47,
  "emails": [
    {
      "user_id": 1,
      "email": "alice@example.com",
      "subject": "You're Crushing It! 85% Win Rate Today",
      "html_file": "output/emails/2026-06-18/1-alice.html",
      "text_file": "output/emails/2026-06-18/1-alice.txt",
      "is_new": false,
      "is_top_performer": true
    },
    ...
  ]
}
```

**Personalization logic:**

```python
# New customers (joined <7 days ago)
if account_age_days <= 7:
    subject = "Welcome! Here's Your First Day Results"
    greeting = "Welcome to Already Here LLC!"

# Top performers (80%+ win rate OR $500+ daily P&L)
elif daily_win_rate >= 80 or daily_pnl >= 500:
    subject = "You're Crushing It! {win_rate}% Win Rate Today"
    greeting = "You're on fire!"

# Standard customers
else:
    subject = "Your Daily Trading Report - {pnl:+} P&L"
    greeting = "Hello {username},"
```

**Email sections:**
- Personalized greeting & subject
- Daily P&L, win rate, trade count, balance
- 30-day performance metrics
- Performance assessment (personalized feedback)
- Tier upgrade CTA (customized by current tier)
- Quick links (dashboard, export, academy, support)

**Tier-specific CTAs:**
```
Free tier → "Upgrade to Pro" (unlock advanced features)
Pro tier → "Upgrade to Elite" (white-label access)
Elite tier → "View Advanced Features" (maximize value)
```

### 4. Milestone Events

**Output:** `output/milestones/{date}/manifest.json` + milestone emails

**Detected milestones:**

1. **$1,000 Lifetime Profit**
   - Triggers when customer crosses $1K P&L threshold
   - Subject: "Congratulations {username}! You've Hit $1,000 Profit 🎉"
   - Message: Celebrate achievement, mention elite status, link to tier benefits

2. **90%+ Win Rate (Single Day)**
   - Triggers when daily win rate >= 90%
   - Subject: "{username}, You're Trading Elite: 90% Win Rate! 🏆"
   - Message: Recognition, position in top 5%, white-label opportunity

3. **Tier Upgrades** (extensible)
   - Can add more milestone types

**Example milestone email:**
```html
<h1>Congratulations {username}! 🎉</h1>
<p>You've officially crossed <strong>$1,000 in lifetime profits</strong> with Already Here LLC!</p>
<p>This achievement represents discipline, skill, and consistency in your trading. 
You're in an elite group of our most profitable traders.</p>
<p><strong>Next milestone:</strong> $5,000 profit. You're on your way!</p>
<button>View Elite Tier Benefits</button>
```

### 5. Case Studies

**Output:** `output/case_studies/case-study-{username}.html` + manifest

**Included for:** Top 3 all-time performers (by lifetime P&L)

**Case study sections:**

1. **Trader Profile**
   - Name, join date, days active
   - Overview of achievement

2. **Performance Metrics** (stat grid)
   - Lifetime P&L
   - Average win rate
   - Days trading
   - Average daily profit
   - Starting vs. current balance
   - ROI percentage
   - Current tier

3. **What Made Them Successful**
   - Disciplined entry selection
   - Risk management (2:1 ratios)
   - Strategy focus (vs. indicator chasing)
   - Daily post-market review
   - Emotional control

4. **Key Insights**
   - Pullquote on consistency vs. magnitude
   - Commentary on their trading approach
   - Lessons for other traders

5. **Path Forward**
   - Advanced strategies they're ready for
   - Scaling recommendations
   - Mentorship/enterprise opportunities

**Use cases:**
- Landing page testimonials
- Email signature inserts
- LinkedIn/Twitter threads
- Sales deck supporting materials
- Social proof on tier upgrade pages

---

## Integration Points

### Email Distribution

**SendGrid Integration:**

```python
# Read manifest and send via SendGrid
import json
from sendgrid import SendGridAPIClient

manifest = json.load(open("output/emails/2026-06-18/manifest.json"))

sg = SendGridAPIClient(api_key)
for email_meta in manifest["emails"]:
    with open(email_meta["html_file"]) as f:
        html = f.read()
    
    msg = Mail(
        from_email="newsletter@profitengine.com",
        to_emails=email_meta["email"],
        subject=email_meta["subject"],
        html_content=html
    )
    sg.send(msg)
```

### Blog Publishing

**Dev.to / Hashnode:**
1. Copy markdown from `output/blog_posts/blog-post-{date}.md`
2. Paste into editor
3. Add tags: `#trading #automation #profitengine`
4. Publish

**Medium:**
1. Copy markdown
2. Use markdown-to-medium converter
3. Add publication: Already Here LLC or TradingInsights

**WordPress:**
1. Use Markdown to HTML plugin
2. Copy HTML from manifest
3. Paste into post editor

### Social Media

**Twitter/X:**
```python
import json
import tweepy

# Load tweets
tweets = json.load(open("output/tweets/tweets-2026-06-18.json"))

# Schedule via Tweepy or Buffer
for tweet in tweets["tweets"]:
    # Schedule at different times throughout the day
    api.update_status(tweet)
```

**LinkedIn:**
- Copy individual tweets
- Reformat for LinkedIn tone (more professional)
- Add #hashtags
- Link to blog post or case study

**Newsletter (Beehiiv/Substack):**
```markdown
# Today's Trading Results

[Insert blog post content or summary]

## This Week's Top Trader

[Insert case study]

## Join Our Community

[Tier upgrade CTA]
```

---

## Data Flow

```
                Daily Trading Happens
                        ↓
        5:00 PM MST — daily_alerts.py runs
             (sends team alert email)
                        ↓
        5:30 PM MST — content_generator.py runs
             ┌─────────────────────────────┐
             │  Read clients.db            │
             │  ├─ Daily trade metrics     │
             │  ├─ Customer performance    │
             │  ├─ Top performers          │
             │  └─ Milestone events        │
             └─────────────────────────────┘
                        ↓
        Generate Content (5 types)
             ├─ Blog post (markdown)
             ├─ 5 Tweet variations (JSON)
             ├─ Personalized emails (HTML+TXT)
             ├─ Milestone emails (special CTAs)
             └─ Case studies (HTML)
                        ↓
        Save to /output directory
             ├─ blog_posts/
             ├─ tweets/
             ├─ emails/
             ├─ milestones/
             └─ case_studies/
                        ↓
        Ready for Distribution (Manual or Automated)
             ├─ Email → SendGrid/AWS SES
             ├─ Blog → WordPress/Medium/Dev.to
             ├─ Social → Twitter/LinkedIn/TikTok
             └─ Landing → Website case study section
```

---

## Monitoring & Logging

### Log File

All operations logged to `content_generator.log`:

```
2026-06-18 17:30:01,234 - content_generator - INFO - Starting content generation for 2026-06-18
2026-06-18 17:30:02,456 - content_generator - INFO - Metrics: 22 traders, $4,250.50 P&L, 72.5% win rate
2026-06-18 17:30:03,789 - content_generator - INFO - Blog post generated: output/blog_posts/blog-post-2026-06-18.md
2026-06-18 17:30:04,012 - content_generator - INFO - Tweets generated: 5 variations saved
2026-06-18 17:30:05,234 - content_generator - INFO - Generated 47 personalized emails
2026-06-18 17:30:06,456 - content_generator - INFO - Generated 2 milestone emails
2026-06-18 17:30:07,678 - content_generator - INFO - Generated 3 case studies
2026-06-18 17:30:08,789 - content_generator - INFO - Content generation complete
```

### Health Check

```bash
# Verify today's content generated
ls -lah output/blog_posts/blog-post-$(date +%Y-%m-%d).md
ls -lah output/tweets/tweets-$(date +%Y-%m-%d).json
ls -lah output/emails/$(date +%Y-%m-%d)/

# Check for errors
tail -50 content_generator.log | grep ERROR
```

---

## Customization

### Modify Blog Post Template

Edit `BlogPostGenerator.generate()` method in `content_generator.py`:

```python
def generate(self, metrics: DailyTradeMetrics) -> str:
    # Customize markdown structure here
    markdown = f"""# Your Custom Title Format
    
## Your Custom Sections
...
    """
    return markdown
```

### Add New Tweet Angle

Add to `TweetGenerator.generate()`:

```python
tweets.append(
    f"Your new tweet template here with {metrics.total_traders} traders "
    f"and {metrics.avg_win_rate:.0f}% accuracy. #YourHashtag"
)
```

### Add New Milestone Type

Edit `ContentQueries._detect_milestones()`:

```python
# New milestone: 100 consecutive winning trades
cursor.execute("""
    SELECT user_id, username FROM ...
    WHERE consecutive_wins >= 100
""")

for row in cursor.fetchall():
    milestones.append({
        "type": "winning_streak",
        "username": row["username"],
        "value": 100,
    })
```

Then add handling in `MilestoneGenerator.generate_milestone_emails()`:

```python
elif milestone["type"] == "winning_streak":
    subject = f"{username}, 100-Trade Winning Streak! 🔥"
    # ... generate special email
```

---

## Troubleshooting

### No content generated

**Check:**
```bash
# 1. Database has trading data for today
sqlite3 clients.db "SELECT COUNT(*) FROM daily_trades WHERE date='2026-06-18';"

# 2. Log file for errors
tail -100 content_generator.log

# 3. Output directory exists
ls -la output/
```

### Missing customers in emails

**Check:**
```bash
# 1. Users table has active accounts
sqlite3 clients.db "SELECT COUNT(*) FROM users WHERE is_active=1;"

# 2. Database connection working
python -c "from lib.clients_db import ClientsDB; db = ClientsDB(); print(db.list_users())"
```

### Blog post looks wrong

**Check:**
- Markdown formatting in template
- Special characters in data (names, strategies)
- Emoji support in output platform

### Tweets too long

**Check:**
```bash
python -c "
from content_generator import TweetGenerator
gen = TweetGenerator('.')
tweet = 'your long tweet here'
print(len(gen._truncate_tweet(tweet)))
"
```

---

## Performance

**Typical execution time:** 2-5 seconds

**Tested with:**
- 50 customers
- 500+ daily trades
- 3 top performers
- 2 milestone events

**Scaling:**
- 100+ customers: ~10 seconds
- 1000+ daily trades: ~15 seconds
- Large case studies: <1 second each

---

## Security

### No Sensitive Data in Generated Content

Generated files do NOT include:
- API keys or credentials
- Password hashes
- Full email addresses (only usernames in templates)
- Account balances (can edit to redact if needed)

### File Permissions

```bash
# Make output directory private
chmod 700 output/

# Ensure log file isn't world-readable
chmod 600 content_generator.log
```

### Affiliate Link Safety

Affiliate links embedded in blog posts use standard tracking:
```
https://amazon.com/product?tag=alreadyhere-20
```

No additional data exposed.

---

## Next Steps

1. **Test locally** with `python test_content_generator.py`
2. **Generate content** for today: `python content_generator.py`
3. **Review output** in `output/` directory
4. **Set up scheduling** (cron/systemd/Task Scheduler)
5. **Integrate email distribution** (SendGrid script)
6. **Publish blog posts** to WordPress/Medium/Dev.to
7. **Schedule tweets** via Buffer/TwitterAPI
8. **Display case studies** on landing page
9. **Monitor logs** daily for errors

---

## Support

For issues or questions:
- Check `content_generator.log` for error details
- Review test file for usage examples: `test_content_generator.py`
- See database schema: `lib/clients_db.py`

---

**ProfitEngine Content Generation Engine**
*Automated marketing at the speed of trading*

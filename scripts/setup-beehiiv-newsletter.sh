#!/bin/bash
# Setup Beehiiv newsletter automation
# Requires: BEEHIIV_API_KEY in GitHub Secrets

set -euo pipefail

echo "=========================================="
echo "SETTING UP BEEHIIV NEWSLETTER"
echo "=========================================="
echo ""

# Load environment
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

BEEHIIV_API_KEY="${BEEHIIV_API_KEY:-}"
BEEHIIV_PUB_ID="${BEEHIIV_PUBLICATION_ID:-}"

if [ -z "$BEEHIIV_API_KEY" ] || [ -z "$BEEHIIV_PUB_ID" ]; then
  echo "[ERROR] BEEHIIV credentials not set"
  echo "Set BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID in GitHub Secrets"
  exit 1
fi

echo "[1] Creating Beehiiv setup guide..."

cat > "BEEHIIV_SETUP.md" << 'EOF'
# Beehiiv Newsletter Setup Guide

## Account Setup
1. Go to: https://dashboard.beehiiv.com
2. Create publication or use existing
3. Get API key from Settings → API

## Newsletter Strategy

### Newsletter Name
"The AI Productivity Letter"

### Tagline
"Weekly tips to save 10+ hours. For professionals building with AI."

### Audience
- Software developers (40%)
- Product managers (20%)
- Entrepreneurs (20%)
- Other professionals (20%)

## Content Calendar (12 Weeks)

### Week 1: AI Fundamentals
**Main:** "What Professionals Need to Know About AI in 2026"
- Explain large language models simply
- Show practical applications
- Dispel myths

### Week 2: Content Creation
**Main:** "How I Create 3x More Content in Half the Time"
- Real workflow breakdown
- Tools stack
- Time metrics

### Week 3: Code Generation
**Main:** "Why Developers Are 10x Faster Now"
- Code generation examples
- Debugging with AI
- Productivity metrics

### Week 4: Analysis & Research
**Main:** "Making Decisions 10x Faster with AI"
- Research workflows
- Data analysis systems
- Real case study

### Week 5: Personal Automation
**Main:** "5 Automations That Pay for Themselves"
- Email automation
- Calendar optimization
- Task management

### Week 6: Team Productivity
**Main:** "How to Train Your Team on AI"
- Implementation checklist
- Objections & responses
- Success metrics

### Week 7: Advanced Workflows
**Main:** "The AI Stack for $50/Month"
- Tool recommendations
- Setup instructions
- Integration tips

### Week 8: Case Study - Software Company
**Main:** "How This Team Shipped Product 3 Months Early"
- Real results
- Implementation steps
- Lessons learned

### Week 9: Case Study - Content Creator
**Main:** "From 2 Hours Daily to 30 Minutes"
- Complete workflow
- Tools used
- Income impact

### Week 10: Monetization
**Main:** "How to Make Money From Your AI Knowledge"
- Course creation
- Consulting services
- Content monetization

### Week 11: Advanced Tools
**Main:** "The Next Layer: Custom AI Workflows"
- API usage
- Custom integrations
- Advanced automation

### Week 12: Year Ahead
**Main:** "2027 Predictions: What's Coming Next"
- Market trends
- Skills to learn
- Opportunities

## Sponsorship Strategy

### Sponsor Rates
- **Early access** (low tier): $500/month
- **Featured** (mid tier): $1,000/month
- **Premium** (high tier): $2,000/month

### Ideal Sponsors
- AI tools (ChatGPT, Claude, Gemini)
- Course platforms (Skillshare, Coursera)
- Dev tools (GitHub Copilot, Replit)
- Productivity tools (Zapier, Make)
- Learning platforms

### Pitch Template
Subject: "Partner with The AI Productivity Letter (5,000+ subscribers)"

Hi [Company],

I run a weekly newsletter read by 5,000+ professionals actively using AI to build.

Your audience:
- 40% software developers (high purchasing power)
- 20% product managers (decision makers)
- 20% entrepreneurs (business builders)
- 20% other professionals

Sponsorship options:
- Featured mention ($1,000/month)
- Early access ($500/month)
- Custom packages

Response rate: 3-5% (high engagement)
Average value per customer: $50+

Interested in a partnership?

## Email Sequences

### Welcome Series (3 emails)

**Email 1: Welcome**
Subject: "Join 5,000+ Productive Professionals"

Hi [Name],

Welcome to The AI Productivity Letter.

Every week, I share:
✓ The AI tools actually working in 2026
✓ Real workflows saving 10+ hours/week
✓ Case studies from high-earning professionals
✓ Copy-paste prompts for your job

No hype. No theory. Just practical systems.

This week: "What Every Professional Should Know About AI"

Read: [LINK]

— [Your Name]

**Email 2: Value Drop (Day 3)**
Subject: "This AI tool saves me 3 hours every Friday"

I'm sending a bonus guide this week: "The 5 AI Tools Actually Worth Your Time"

Download: [LINK]

**Email 3: Upsell (Day 7)**
Subject: "Want the complete system?"

If you've been reading the letters and thinking "I want to go deeper..."

I created a complete guide: The AI Productivity System
- 85 pages
- 7 chapters
- Real workflows
- Copy-paste prompts

$29.99. Lifetime access.

Get it: [GUMROAD_LINK]

### Ongoing Engagement
- Monthly: Ask for feedback
- Quarterly: Run survey
- Bi-weekly: Ask readers to share stories

## Expected Growth

Month 1: 100-200 subscribers (launch phase)
Month 2: 300-500 subscribers
Month 3: 800-1,200 subscribers
Month 6: 2,000-3,000 subscribers
Month 12: 5,000+ subscribers

## Revenue

At 2,000 subscribers:
- 2 sponsors at $500/month = $1,000/month
- Course/ebook promotion = $200-500/month
- Total: $1,200-1,500/month

At 5,000 subscribers:
- 3 sponsors at $1,000/month = $3,000/month
- Premium tier = $1,000-2,000/month
- Total: $4,000-5,000/month

EOF

echo "    ✓ Setup guide created: BEEHIIV_SETUP.md"
echo ""

echo "[2] Creating email templates..."
mkdir -p "marketing/beehiiv"

cat > "marketing/beehiiv/newsletter-template.md" << 'EOF'
# Newsletter Template

## Header
The AI Productivity Letter
Weekly insights for professionals building with AI

---

## Main Article Section

### [TOPIC]

[2-3 paragraph explanation with real data/examples]

Key takeaways:
- Point 1
- Point 2
- Point 3

Your action: [One thing to implement this week]

---

## Tool of the Week

**[Tool Name]**

What it does: [1 sentence]

Who should use it: [Target person]

My tip: [One specific way to get value]

Setup time: [5 minutes / 30 minutes / 1 hour]

Cost: [$0 / $X/month]

[Tool Link]

---

## Community Question

**"[Question from reader]"**

My answer: [Practical, actionable response]

---

## Sponsor Message

[2-3 sentences about sponsor + why I use it]

[Sponsor Link]

---

## Sign Off

That's it for this week.

Share this with someone who needs to reclaim their time.

Questions? Reply to this email.

— [Your Name]

P.S. [Personal note or teaser for next week]

EOF

echo "    ✓ Newsletter template created"
echo ""

echo "[3] Creating sponsorship pitch..."
cat > "marketing/beehiiv/sponsor-pitch.txt" << 'EOF'
Subject: Partner with The AI Productivity Letter (5,000+ subscribers)

Hi [Decision Maker Name],

I run The AI Productivity Letter - a weekly newsletter read by 5,000+ professionals actively using AI to build their careers and businesses.

Your audience:
- 40% software developers & engineers (high purchasing power)
- 20% product managers & leaders (decision makers)
- 20% entrepreneurs & founders (business builders)
- 20% other professionals (designers, writers, analysts)

They're:
✓ Early adopters of AI tools
✓ High income ($80k-$500k+)
✓ Actively purchasing software & services
✓ Highly engaged readers (3-5% CTR)

Sponsorship tiers:
- **Featured**: $1,000/month (500+ words, 2-3 sends)
- **Standard**: $500/month (200 words, 1 send)
- **Custom**: [Your proposal]

Each sponsor gets:
✓ Placement in weekly newsletter
✓ Click tracking + metrics
✓ Subscriber access info
✓ Logo in archives
✓ Post-campaign report

Response rates: 3-5% (newsletter readers are engaged)
Typical customer value: $50-500+

Recent sponsors:
- [Company 1]: 200+ clicks
- [Company 2]: 150+ signups
- [Company 3]: $50k+ in attributed revenue

Ready to partner? Let's talk.

[Your Name]
[Email]
[Phone]

---

FAQ for Sponsors:

Q: What's the audience size?
A: 5,000+ subscribers. Growing 20-30%/month.

Q: What's the click-through rate?
A: 3-5% (2.5-5x industry average).

Q: Can I add a discount code?
A: Yes. We'll track attribution.

Q: What if I don't get results?
A: We'll work with you to optimize. If unsatisfied after 2 months, we'll adjust terms.

Q: Can I sponsor multiple weeks?
A: Yes. 3-month contracts get 10% discount. 12-month get 20%.
EOF

echo "    ✓ Sponsor pitch created"
echo ""

echo "=========================================="
echo "✓ BEEHIIV SETUP COMPLETE"
echo "=========================================="
echo ""
echo "NEXT STEPS:"
echo "1. Review: BEEHIIV_SETUP.md"
echo "2. Create Beehiiv account at: https://beehiiv.com"
echo "3. Set up publication"
echo "4. Write first 4 newsletters using template"
echo "5. Create sponsorship pitch"
echo "6. Import email list (if you have one)"
echo ""
echo "Expected first 6 months: \$500-2,000 sponsorship revenue"
echo ""

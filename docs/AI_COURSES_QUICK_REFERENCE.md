# AI Courses Automation - Quick Reference

## Environment Setup (5 minutes)

```bash
export OPENAI_API_KEY="sk-..."
export GUMROAD_API_TOKEN="..."
export GUMROAD_CREATOR_ID="yourname"
export BREVO_API_KEY="..."
export STRIPE_SECRET_KEY="sk_live_..."
export AMAZON_AFFILIATE_TAG="yourtag-20"
```

## API Actions Overview

| Action | Purpose | Time | Cost |
|--------|---------|------|------|
| `generate-course` | Create full course with modules | 5 min | $0.10 |
| `generate-prompts` | Create prompt library | 3 min | $0.05 |
| `generate-tool-guide` | Create tool guide | 2 min | $0.03 |
| `create-bundle` | Combine courses/tools | <1 min | $0 |
| `publish-course` | Upload to Gumroad | 2 min | $0 |
| `setup-email-funnel` | Create email sequence | 1 min | $0 |
| `get-performance` | Get sales metrics | <1 min | $0 |
| `orchestrate` | Bulk generate & publish | 30 min | $1.50 |

## Common Patterns

### Pattern 1: Generate & Publish Single Course (10 minutes)

```bash
# 1. Generate content
curl -X POST /api/automation/ai-courses -d '{
  "action": "generate-course",
  "courseTitle": "Your Course",
  "topic": "Your topic",
  "level": "beginner",
  "price": 47
}'

# 2. Save course ID from response

# 3. Publish to Gumroad
curl -X POST /api/automation/ai-courses -d '{
  "action": "publish-course",
  "setupEmailFunnel": true,
  "course": { /* paste course from step 1 */ }
}'
```

### Pattern 2: Create Prompt Library (5 minutes)

```bash
curl -X POST /api/automation/ai-courses -d '{
  "action": "generate-prompts",
  "libraryName": "Your Library Name",
  "category": "Category",
  "promptCount": 15
}'
```

### Pattern 3: Launch Everything at Once (45 minutes)

```bash
curl -X POST /api/automation/ai-courses -d '{
  "action": "orchestrate",
  "courses": [
    { "title": "Course 1", "topic": "...", "level": "beginner", "price": 47 },
    { "title": "Course 2", "topic": "...", "level": "intermediate", "price": 77 }
  ],
  "createBundle": true,
  "publishToGumroad": true,
  "setupEmailFunnel": true
}'
```

## Pricing Quick Guide

**Single Courses**:
- Beginner: $37-$67
- Intermediate: $67-$97
- Advanced: $97-$197

**Bundles**:
- 2 courses: Save 25%
- 3 courses: Save 30%
- 4+ courses: Save 35%

**Prompt Libraries**:
- Standalone: $17-$37
- With course: Free (included)

**Tool Guides**:
- Standalone: Free (PDF downloadable)
- With course: Included

## Email Sequence Overview

Every course gets 5 auto-emails:

| # | Trigger | Timing | Purpose |
|---|---------|--------|---------|
| 1 | Purchase | Immediate | Welcome + access |
| 2 | Module complete | +2 days | Keep momentum |
| 3 | Auto-send | +5 days | Bonus announcement |
| 4 | Course complete | +14 days | Feedback survey |
| 5 | Auto-send | +21 days | Upsell bundle |

## Troubleshooting Quick Fix

| Error | Fix |
|-------|-----|
| "OPENAI_API_KEY not configured" | `export OPENAI_API_KEY="sk-..."` |
| "No content generated" | Simplify topic, reduce moduleCount |
| "Gumroad unauthorized" | Regenerate GUMROAD_API_TOKEN |
| "BREVO_API_KEY not configured" | Get key from Brevo dashboard |
| "Email not sending" | Verify Brevo sender email verified |
| "Timeout" | Reduce batch size, try again |

## Performance Targets

### Week 1
- 10+ views
- 2-3 sales ($100-150)
- 40%+ email open rate

### Month 1
- 100+ views
- 15-20 sales ($700-1000)
- 4-5 course reviews
- 50+ email subscribers

### Month 3
- 500+ views
- 50+ sales ($2300+)
- 20+ reviews (4.0+ rating)
- First affiliate commissions

## Types of Courses

### Prompt Engineering
- ChatGPT Prompting 101
- Advanced Prompting Techniques
- Building AI Workflows
- Prompt Engineering Masterclass

**Pricing**: $47-$147

### Tool Guides
- Getting Started with ChatGPT
- Claude AI for Developers
- Using GPT-4 API
- Building with LangChain

**Pricing**: Free-$47

### Business AI
- AI for Entrepreneurs
- Customer Service Chatbots
- Email Marketing with AI
- Content Creation with AI

**Pricing**: $47-$97

### Technical
- AI API Integration
- Building AI Applications
- Fine-tuning Models
- Production AI Systems

**Pricing**: $97-$197

## Revenue Projections

### Conservative (10 students/month)
- Single course: $470/month
- After 3 months: $1,410

### Moderate (25 students/month)
- Single course: $1,175/month
- Bundle: $2,500/month
- Total: $3,675/month
- After 3 months: $11,025

### Aggressive (50 students/month)
- 3 courses: $2,350/month
- 2 bundles: $5,000/month
- Affiliates: $1,500/month
- Total: $8,850/month
- After 3 months: $26,550

## Key Metrics to Track

### Sales
- Total courses sold
- Average price per course
- Bundle attach rate
- Refund rate

### Engagement
- Email open rate (target: 40%+)
- Email click rate (target: 15%+)
- Course completion rate (target: 60%+)
- Course rating (target: 4.0+)

### Monetization
- Revenue per student
- Lifetime value (LTV)
- Affiliate commission rate
- Total revenue

## Files Created

After publishing, you'll have:

```
.runtime/ai-courses/
├── PROMPTS_lib-*.json          # Prompt libraries
├── GUIDE_guide-*.json          # Tool guides
├── BUNDLE_bundle-*.json        # Course bundles
└── publish-results.jsonl       # Publishing logs
```

## Integration Checklist

- [ ] OPENAI_API_KEY configured
- [ ] GUMROAD_API_TOKEN configured
- [ ] GUMROAD_CREATOR_ID set
- [ ] BREVO_API_KEY configured
- [ ] Gumroad account created and verified
- [ ] Brevo account created and verified
- [ ] Sender email verified in Brevo
- [ ] Contact lists created in Brevo
- [ ] Stripe account ready (optional)
- [ ] Amazon Associates tag ready (optional)

## Workflow: Beginner to Advanced

### Week 1: Learn the System
1. Generate 1 test course
2. Review generated content
3. Publish to Gumroad
4. Monitor metrics

### Week 2-3: Create Your First Real Course
1. Generate 2-3 courses in your niche
2. Customize email sequences
3. Add affiliate links
4. Launch with email announcement

### Week 4-8: Build Library
1. Generate 5-10 courses
2. Create 5 prompt libraries
3. Create 3-5 tool guides
4. Build 2-3 course bundles
5. Test different price points

### Month 2-3: Scale & Optimize
1. Analyze performance data
2. Update top-performing courses
3. Create advanced course tier
4. Build affiliate partnerships
5. Launch community (Discord)

## Common Course Bundles

### Budget Bundle ($99)
- ChatGPT 101
- Prompt templates (20x)
- Email sequences (5)

### Professional Bundle ($199)
- ChatGPT 101
- Advanced Prompting
- AI Workflows
- 3 tool guides
- 2 prompt libraries

### Enterprise Bundle ($399)
- All 5 courses
- All 10 tool guides
- All 8 prompt libraries
- API integration guide
- Private community access
- Monthly Q&A calls

## Payment & Affiliate

### Gumroad Takes 10%
- Course: $100 → You get $90
- Affiliate: Standard 30% for partners

### Amazon Associates
- Commission: 1-3% depending on product
- Include in course content
- Track via Gumroad dashboard

### Stripe Integration
- Direct payment link in course
- Webhook triggers email funnel
- Higher fees (2.9% + $0.30)

## Debugging Commands

```bash
# Test API connection
curl https://profitengine-tau.vercel.app/api/automation/ai-courses

# Generate test course
curl -X POST https://profitengine-tau.vercel.app/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{"action": "generate-course", "courseTitle": "Test", "topic": "Testing", "level": "beginner", "price": 1}'

# Check Gumroad API
curl -H "Authorization: Bearer $GUMROAD_API_TOKEN" \
  https://api.gumroad.com/v2/products

# Check OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

## Next Actions

1. **Setup**: Configure all environment variables
2. **Test**: Generate 1 test course
3. **Review**: Check quality and accuracy
4. **Publish**: Upload to Gumroad
5. **Monitor**: Track sales and engagement
6. **Iterate**: Improve based on feedback
7. **Scale**: Generate more courses
8. **Optimize**: A/B test pricing and emails
9. **Expand**: Add tool guides and bundles
10. **Automate**: Setup scheduled publishing

## Support Resources

- **OpenAI Docs**: https://platform.openai.com/docs
- **Gumroad Creator Hub**: https://gumroad.com/creators
- **Brevo Docs**: https://developers.brevo.com/docs
- **Course Examples**: See `/examples/AI_COURSES_EXAMPLES.md`
- **Full Docs**: See `/docs/AI_COURSES_AUTOMATION.md`

---

**TL;DR**: Run `orchestrate` action, set prices, watch revenue grow!

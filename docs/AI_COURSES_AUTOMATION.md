# AI Tools & Courses Automation

Complete automation system for generating, bundling, and selling AI courses, ChatGPT prompt libraries, and tool guides.

## Features

- **Auto-Content Generation**: Generate complete course modules using GPT-4
- **Prompt Library Creation**: Auto-generate ChatGPT prompt libraries with system prompts, templates, and examples
- **Tool Guides**: Generate beginner-friendly guides for AI tools and integrations
- **Course Bundling**: Combine courses with tools and prompts for bundled discounts
- **Gumroad Integration**: Auto-upload to Gumroad with pricing, descriptions, and affiliate links
- **Email Funnel Automation**: Auto-setup multi-step email sequences via Brevo
- **Affiliate Links**: Embed Amazon Associates and tool-specific affiliate links
- **Performance Analytics**: Track sales, conversions, and engagement metrics
- **Bulk Orchestration**: Generate multiple courses in parallel with optional bundling

## Environment Setup

```bash
# Required environment variables
export OPENAI_API_KEY="sk-..."                 # For content generation
export GUMROAD_API_TOKEN="..."                 # Gumroad API token
export GUMROAD_CREATOR_ID="yourname"           # Gumroad store username
export BREVO_API_KEY="..."                     # Brevo email automation
export STRIPE_SECRET_KEY="sk_live_..."         # Stripe integration
export AMAZON_AFFILIATE_TAG="yourtag-20"       # Amazon Associates tag

# Optional
export IMAGE_GENERATION_API="unsplash"         # 'unsplash' | 'pexels' | 'dalle' | 'replicate'
export UNSPLASH_API_KEY="..."                  # For free images
```

## API Endpoints

### POST /api/automation/ai-courses

All actions are triggered via POST requests to this endpoint.

#### 1. Generate Course Content

Generate complete course with modules, lessons, and learning outcomes.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate-course",
    "courseTitle": "Prompt Engineering Mastery",
    "topic": "Advanced ChatGPT prompting techniques and best practices",
    "level": "advanced",
    "price": 97,
    "moduleCount": 5,
    "targetAudience": [
      "Content creators",
      "Business owners",
      "Marketing professionals"
    ],
    "learningOutcomes": [
      "Master prompt engineering fundamentals",
      "Create advanced system prompts",
      "Build production-ready AI workflows",
      "Optimize AI for specific use cases"
    ],
    "certificateIncluded": true,
    "lifetimeAccess": true
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "generate-course",
  "result": {
    "course": {
      "id": "course-1718918234567",
      "title": "Prompt Engineering Mastery",
      "description": "Advanced ChatGPT prompting techniques...",
      "category": "prompt-engineering",
      "level": "advanced",
      "price": 97,
      "duration": "10 hours",
      "modules": [
        {
          "id": "module-1",
          "title": "Fundamentals of Prompt Engineering",
          "description": "...",
          "duration": "2 hours",
          "lessons": [...]
        }
      ],
      "certificateIncluded": true,
      "lifetimeAccess": true,
      "tags": ["advanced", "prompt-engineering"]
    },
    "modules": [...]
  },
  "timestamp": "2024-06-20T...",
  "duration": 5234
}
```

#### 2. Generate ChatGPT Prompt Library

Create structured prompt libraries with system prompts, user templates, and examples.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate-prompts",
    "libraryName": "Email Marketing AI Prompts",
    "category": "Email Marketing",
    "promptCount": 15
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "generate-prompts",
  "result": {
    "id": "lib-1718918234567",
    "name": "Email Marketing AI Prompts",
    "description": "15 professional prompts for Email Marketing",
    "category": "Email Marketing",
    "version": "1.0.0",
    "createdAt": "2024-06-20T...",
    "totalPrompts": 15,
    "prompts": [
      {
        "id": "prompt-1",
        "title": "Subject Line Generator",
        "description": "Generates compelling email subject lines",
        "systemPrompt": "You are an expert email marketer...",
        "userPromptTemplate": "Generate 5 subject lines for: {{topic}}",
        "category": "Email Marketing",
        "difficulty": "beginner",
        "useCases": ["subject lines", "email marketing"],
        "exampleInput": "AI productivity tools",
        "exampleOutput": "[5 subject lines]",
        "tags": ["email", "marketing"]
      }
    ],
    "metadata": {
      "difficulty": "intermediate",
      "useCases": ["Email Marketing"],
      "keywords": ["email", "marketing", "automation"]
    }
  },
  "timestamp": "2024-06-20T...",
  "duration": 8234
}
```

#### 3. Generate Tool Guide

Create beginner-friendly setup guides for AI tools.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate-tool-guide",
    "toolName": "Claude AI",
    "toolDescription": "Advanced AI assistant for content creation, coding, and analysis"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "generate-tool-guide",
  "result": {
    "id": "guide-1718918234567",
    "toolName": "Claude AI",
    "description": "Advanced AI assistant for content creation...",
    "category": "AI Tools",
    "setupSteps": [
      {
        "step": 1,
        "title": "Create Account",
        "description": "Visit claude.ai and sign up with your email"
      }
    ],
    "useCases": [
      "Content creation",
      "Code generation",
      "Data analysis"
    ],
    "tipsTricks": [
      "Use system prompts to set context",
      "Break complex tasks into steps"
    ],
    "integrations": []
  },
  "timestamp": "2024-06-20T...",
  "duration": 3234
}
```

#### 4. Create Course Bundle

Combine multiple courses with complementary tools and prompts.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-bundle",
    "bundleTitle": "Complete AI Mastery Bundle",
    "courseIds": [
      "course-1718918234567",
      "course-1718918234568"
    ],
    "toolGuideIds": [
      "guide-1718918234567",
      "guide-1718918234568"
    ],
    "promptLibraryIds": [
      "lib-1718918234567"
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "create-bundle",
  "result": {
    "id": "bundle-1718918234567",
    "bundleTitle": "Complete AI Mastery Bundle",
    "description": "Bundle containing 2 courses, 2 tools, and 1 prompt library",
    "courses": ["course-1718918234567", "course-1718918234568"],
    "tools": [],
    "prompts": [],
    "bundlePrice": 199,
    "individualPrice": 299,
    "discountPercentage": 33,
    "includedResources": [
      "Lifetime access",
      "All updates",
      "Community access",
      "Email support"
    ],
    "bonuses": []
  },
  "timestamp": "2024-06-20T...",
  "duration": 1234
}
```

#### 5. Publish Course to Gumroad

Upload course with automatic email funnel setup.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "publish-course",
    "setupEmailFunnel": true,
    "course": {
      "id": "course-1718918234567",
      "title": "Prompt Engineering Mastery",
      "description": "Master advanced ChatGPT prompting...",
      "category": "prompt-engineering",
      "level": "advanced",
      "price": 97,
      "duration": "10 hours",
      "modules": [],
      "targetAudience": ["Developers", "Content creators"],
      "learningOutcomes": ["Master prompting"],
      "tags": ["ai", "prompting"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "publish-course",
  "result": {
    "publishResult": {
      "success": true,
      "courseId": "course-1718918234567",
      "gumroadProductId": "3d4d4d4d",
      "gumroadUrl": "https://gumroad.com/l/promptmastery",
      "timestamp": "2024-06-20T..."
    },
    "emailCampaignId": "campaign-1718918234567"
  },
  "timestamp": "2024-06-20T...",
  "duration": 4567
}
```

#### 6. Setup Email Funnel

Create multi-step email sequence for course engagement.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "setup-email-funnel",
    "courseId": "course-1718918234567",
    "courseName": "Prompt Engineering Mastery"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "setup-email-funnel",
  "result": {
    "campaignId": "campaign-1718918234567",
    "emailCount": 5
  },
  "timestamp": "2024-06-20T...",
  "duration": 2134
}
```

**Email Sequence (Auto-Generated):**
1. Welcome email (sent immediately after purchase)
2. Module 1 completion follow-up (2 days later)
3. Bonus pack announcement (5 days)
4. Course completion survey (14 days)
5. Upsell to related courses (21 days)

#### 7. Get Course Performance

Get sales, conversion, and engagement metrics.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-performance",
    "courseId": "course-1718918234567",
    "gumroadProductId": "3d4d4d4d"
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "get-performance",
  "result": {
    "courseId": "course-1718918234567",
    "courseName": "Prompt Engineering Mastery",
    "totalSales": 143,
    "totalRevenue": 13871,
    "conversionRate": 0.087,
    "averageRating": 4.8,
    "reviewCount": 34,
    "emailOpenRate": 0.42,
    "emailClickRate": 0.18,
    "lastUpdated": "2024-06-20T..."
  },
  "timestamp": "2024-06-20T...",
  "duration": 1234
}
```

#### 8. Bulk Orchestration

Generate multiple courses at once with optional bundling and publishing.

**Request:**
```bash
curl -X POST http://localhost:3000/api/automation/ai-courses \
  -H "Content-Type: application/json" \
  -d '{
    "action": "orchestrate",
    "courses": [
      {
        "title": "Prompt Engineering 101",
        "topic": "Fundamentals of ChatGPT prompting",
        "level": "beginner",
        "price": 47,
        "moduleCount": 3
      },
      {
        "title": "Advanced Prompting",
        "topic": "Complex multi-step prompts and workflows",
        "level": "advanced",
        "price": 97,
        "moduleCount": 5
      }
    ],
    "createBundle": true,
    "publishToGumroad": true,
    "setupEmailFunnel": true
  }'
```

**Response:**
```json
{
  "success": true,
  "action": "orchestrate",
  "result": {
    "courses": [
      {
        "success": true,
        "courseId": "course-1718918234567",
        "gumroadProductId": "3d4d4d4d",
        "gumroadUrl": "https://gumroad.com/l/promptbasics"
      },
      {
        "success": true,
        "courseId": "course-1718918234568",
        "gumroadProductId": "4e5e5e5e",
        "gumroadUrl": "https://gumroad.com/l/advancedprompts"
      }
    ],
    "bundle": {
      "success": true,
      "courseId": "bundle-1718918234567",
      "gumroadProductId": "5f6f6f6f",
      "gumroadUrl": "https://gumroad.com/l/promptbundle"
    },
    "totalTime": 4
  },
  "timestamp": "2024-06-20T...",
  "duration": 45234
}
```

## File Structure

### Course Metadata Files

Create markdown files with YAML front matter for course metadata:

**AI_COURSE_advanced-prompting.md:**
```markdown
---
title: Advanced Prompting Techniques
description: Learn complex multi-step prompt engineering
category: prompt-engineering
level: advanced
price: 97
tags: [prompting, ai, chatgpt]
---

## Course Overview

Complete guide to advanced prompt engineering...
```

### Prompt Library Files

Auto-generated as JSON:

**PROMPTS_lib-1718918234567.json:**
```json
{
  "id": "lib-1718918234567",
  "name": "Email Marketing AI Prompts",
  "category": "Email Marketing",
  "totalPrompts": 15,
  "prompts": [
    {
      "id": "prompt-1",
      "title": "Subject Line Generator",
      "systemPrompt": "You are an expert email marketer...",
      "userPromptTemplate": "Generate 5 subject lines for: {{topic}}"
    }
  ]
}
```

### Tool Guides

Auto-generated guides for AI tools:

**GUIDE_guide-1718918234567.json:**
```json
{
  "id": "guide-1718918234567",
  "toolName": "Claude AI",
  "setupSteps": [...],
  "useCases": [...],
  "tipsTricks": [...]
}
```

### Course Bundles

Bundled courses with discount pricing:

**BUNDLE_bundle-1718918234567.json:**
```json
{
  "id": "bundle-1718918234567",
  "bundleTitle": "Complete AI Mastery",
  "courses": [...],
  "bundlePrice": 199,
  "discountPercentage": 33
}
```

## Email Funnel Sequences

Each course automatically gets a 5-email sequence:

### Email 1: Welcome (Immediate)
- Congratulations on purchase
- Access instructions
- Community login
- First lesson link

### Email 2: Module Follow-up (Day 2)
- Trigger: Module 1 completion
- Celebrate progress
- Preview Module 2
- Related tools announcement

### Email 3: Bonus Pack (Day 5)
- Announce exclusive bonuses
- Download links
- Community invitation
- Live Q&A schedule

### Email 4: Feedback Survey (Day 14)
- Course completion detected
- Satisfaction survey
- Feature requests
- Future course interest

### Email 5: Upsell (Day 21)
- Bundle offer with 30% discount
- Related courses pitch
- Limited-time offer
- Community highlights

## Pricing Strategy

### Single Courses
- Beginner: $47-$67
- Intermediate: $67-$97
- Advanced: $97-$197

### Bundles
- 2 courses: Individual price × 0.75
- 3 courses: Individual price × 0.70
- 4+ courses: Individual price × 0.65

### Affiliate Integration
- Embed affiliate links in course content
- Amazon Associates for tools
- Tool-specific affiliate programs
- Commission tracking via Gumroad

## Automation Best Practices

1. **Content Quality**: Generated content should be reviewed for accuracy and completeness
2. **Pricing**: Adjust prices based on market research and competitor analysis
3. **Email Testing**: Test email sequences before publishing to students
4. **Performance Tracking**: Monitor metrics weekly to optimize conversion
5. **Updates**: Plan quarterly updates to maintain lifetime value for customers

## Error Handling

All API responses include standard error handling:

```json
{
  "success": false,
  "action": "publish-course",
  "error": "GUMROAD_API_TOKEN not configured",
  "timestamp": "2024-06-20T...",
  "duration": 1234
}
```

Common errors:
- Missing environment variables
- API rate limits (Brevo, OpenAI, Gumroad)
- Invalid course structure
- Network timeouts during content generation

## Performance Monitoring

Track key metrics:

- **Content Generation Time**: Monitor OpenAI API latency
- **Publishing Success Rate**: Track Gumroad upload failures
- **Email Campaign Performance**: Monitor open/click rates
- **Course Sales**: Daily and monthly revenue tracking
- **Customer Feedback**: Collect via automated surveys

## Troubleshooting

### Course Generation Failures

```bash
# Enable debug logging
export DEBUG=ai-courses:*

# Retry with smaller module count
curl -X POST ... -d '{"action": "generate-course", "moduleCount": 2}'
```

### Email Campaign Issues

- Verify BREVO_API_KEY is valid
- Check email list creation in Brevo dashboard
- Monitor bounce rates and list health
- Verify authentication tokens aren't expired

### Gumroad Publishing Issues

- Validate GUMROAD_API_TOKEN permissions
- Check product title uniqueness
- Ensure price is valid number
- Verify GUMROAD_CREATOR_ID matches account

## Advanced Usage

### Custom Email Sequences

Modify sequences by extending `createCourseEmailSequence()`:

```typescript
const customSequence = {
  ...createCourseEmailSequence(courseId, courseName),
  emailSequence: [
    ...customEmails,
    // Add custom emails
  ],
};
```

### Scheduled Publishing

Use cron-based publishing:

```typescript
// Generate and publish every Friday at 5 PM
schedule.scheduleJob('0 17 * * 5', async () => {
  const result = await fetch('/api/automation/ai-courses', {
    method: 'POST',
    body: JSON.stringify({
      action: 'orchestrate',
      courses: weeklyCourseBatch,
      publishToGumroad: true,
    }),
  });
});
```

### Content Localization

Generate course content in multiple languages:

```bash
curl -X POST ... -d '{
  "action": "generate-course",
  "courseTitle": "Mastery de Prompts (Spanish)",
  "language": "es",
  ...
}'
```

## Integration with Existing Systems

### With Amazon Affiliate
Courses auto-link to tools via Amazon Associates tag.

### With Stripe
Link course purchases to Stripe checkout via Gumroad webhooks.

### With Discord
Auto-invite students to private Discord community on purchase.

### With GitHub
Auto-commit course updates to GitHub for version control.

## Limits & Rate Limits

- **OpenAI API**: 3 concurrent requests, 5-minute cooldown
- **Gumroad API**: 60 requests/minute
- **Brevo API**: 150 emails/second
- **Course Generation**: ~5 minutes per course
- **Batch Limit**: 10 courses per orchestration request

## Security Notes

- API tokens stored in environment variables only
- No secrets committed to git
- Course content validated before publishing
- Email addresses verified before sending
- Payment processing via Gumroad (PCI-compliant)

## Support & Resources

- OpenAI API Docs: https://platform.openai.com/docs
- Gumroad API: https://gumroad.com/api
- Brevo API: https://developers.brevo.com/docs
- Course structure inspiration: https://kajabi.com

## License

MIT License - Use freely in commercial projects.

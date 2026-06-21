# Self-Help Content Automation System

Complete system for auto-generating, formatting, and publishing self-help content across multiple platforms.

## Overview

This automation system provides:
- **Content Generation**: AI-powered blog articles with SEO optimization
- **Course Creation**: Multi-lesson modules with quizzes and resources
- **YouTube Transcripts**: Automatic processing into blog posts, study guides, and chapters
- **eBook Production**: Multi-chapter ebooks with formatting and structure
- **Multi-Platform Distribution**: Automatic publishing to 6+ platforms
- **Format Conversion**: Export to Markdown, HTML, PDF, and DOCX

## Architecture

### Core Files

```
app/lib/automation/self-help.ts       # Main automation library
app/api/automation/self-help/route.ts # API endpoints
```

### Key Features

1. **Content Generation**
   - Blog articles with SEO keywords
   - Course modules with lessons and quizzes
   - eBook chapters with sections and callouts
   - YouTube transcript processing

2. **Distribution**
   - GitHub (blog repo)
   - Newsletter/Email
   - Social Media (Twitter, LinkedIn, Instagram)
   - Medium
   - Dev.to
   - GitHub Pages

3. **Formatting**
   - Markdown with proper heading hierarchy
   - HTML with semantic tags
   - PDF generation
   - DOCX export

## API Endpoints

### 1. Generate Content

```bash
POST /api/automation/self-help/generate

{
  "topic": "How to Build Passive Income Streams",
  "difficulty": "beginner",
  "format": "blog",
  "keywords": ["passive income", "side hustle", "freelancing"],
  "targetAudience": "entrepreneurs",
  "tone": "inspirational",
  "includeAffiliates": true,
  "estimatedLength": "medium"
}
```

**Response (202 Accepted)**:
```json
{
  "success": true,
  "generationId": "gen-1719000000000",
  "status": "generating",
  "message": "Content generation started",
  "statusUrl": "/api/automation/self-help?status=check&id=gen-1719000000000"
}
```

**Check Status**:
```bash
GET /api/automation/self-help?status=check&id=gen-1719000000000
```

**Status Response**:
```json
{
  "generationId": "gen-1719000000000",
  "status": "complete",
  "progress": 100,
  "elapsedSeconds": 45,
  "result": {
    "id": "content-1719000000000",
    "topic": "How to Build Passive Income Streams",
    "title": "5 Proven Ways to Build Passive Income in 2026",
    "content": "...",
    "markdown": "# 5 Proven Ways...",
    "html": "<h1>5 Proven Ways...</h1>...",
    "wordCount": 2400,
    "readingTimeMinutes": 12,
    "seoKeywords": ["passive income", "side hustle", "freelancing", ...],
    "metadata": {
      "createdAt": "2026-06-20T12:00:00Z",
      "author": "ProfitEngine AI",
      "category": "entrepreneurs",
      "tags": ["passive income", "business", ...]
    },
    "affiliateLinks": {
      "Amazon Associates": "https://amazon.com/...",
      "Gumroad": "https://gumroad.com/..."
    }
  }
}
```

---

### 2. Generate Course Module

```bash
POST /api/automation/self-help/course

{
  "topic": "Advanced Trading Strategies",
  "difficulty": "advanced",
  "numberOfLessons": 7
}
```

**Response (202 Accepted)**:
```json
{
  "success": true,
  "generationId": "course-1719000000000",
  "status": "generating",
  "message": "Course module generation started",
  "statusUrl": "/api/automation/self-help?status=check&id=course-1719000000000"
}
```

**Course Structure Response**:
```json
{
  "id": "course-1719000000000",
  "title": "Advanced Trading Strategies",
  "description": "Master advanced trading techniques...",
  "duration": 420,
  "lessons": [
    {
      "id": "lesson-1719000000000-0",
      "title": "Introduction to Advanced Strategies",
      "content": "...",
      "duration": 600,
      "keyPoints": [
        "Understanding market dynamics",
        "Risk management fundamentals",
        ...
      ],
      "exercises": [
        {
          "id": "exercise-1719000000000-0",
          "type": "multiple-choice",
          "question": "What is the primary goal of risk management?",
          "options": [
            "Maximize returns",
            "Minimize losses",
            "Trade frequently",
            "Follow market trends"
          ],
          "correctAnswer": "Minimize losses",
          "hints": ["Think about protecting your capital"]
        }
      ]
    }
  ],
  "quizzes": [
    {
      "id": "quiz-1719000000000-0",
      "title": "Module 1 Quiz",
      "questions": [...],
      "passingScore": 70,
      "timeLimit": 1800
    }
  ],
  "resources": [
    {
      "type": "pdf",
      "title": "Trading Strategy Handbook",
      "url": "https://...",
      "description": "Comprehensive reference guide"
    }
  ],
  "prerequisites": [],
  "learningOutcomes": [
    "Understand advanced trading concepts",
    "Apply risk management techniques",
    ...
  ]
}
```

---

### 3. Process YouTube Transcript

```bash
POST /api/automation/self-help/transcript

{
  "videoId": "dQw4w9WgXcQ",
  "title": "10 Ways to Make Money Online"
}
```

**Response Structure**:
```json
{
  "videoId": "dQw4w9WgXcQ",
  "title": "10 Ways to Make Money Online",
  "transcript": "Welcome to today's video...",
  "duration": 1200,
  "keywords": ["money", "online", "earning", "passive income", ...],
  "chapters": [
    {
      "startTime": 0,
      "title": "Chapter 1: Introduction",
      "content": "...",
      "keyPoints": [
        "10 different methods discussed",
        "Mix of active and passive income",
        ...
      ]
    }
  ],
  "seoDescription": "10 Ways to Make Money Online - Learn about earning, passive income, online business...",
  "blogPost": "# 10 Ways to Make Money Online\n\n...",
  "studyGuide": "# Study Guide\n\n## Chapter 1: Introduction\n\n### Key Points:\n..."
}
```

---

### 4. Generate eBook

```bash
POST /api/automation/self-help/ebook

{
  "title": "The Complete Guide to Financial Freedom",
  "numberOfChapters": 10
}
```

**Response Structure**:
```json
[
  {
    "chapterNumber": 1,
    "title": "Getting Started with Financial Freedom",
    "content": "...",
    "sections": [
      {
        "heading": "Understanding Financial Freedom",
        "content": "...",
        "subsections": [
          {
            "heading": "Definition and Goals",
            "content": "..."
          }
        ],
        "callouts": [
          {
            "type": "tip",
            "title": "Pro Tip",
            "content": "Start small and compound your results..."
          }
        ]
      }
    ],
    "wordCount": 2500,
    "estimatedReadingTime": 12
  }
]
```

---

### 5. Distribute Content

```bash
POST /api/automation/self-help/distribute

{
  "contentId": "content-1719000000000",
  "platforms": ["blog", "newsletter", "social", "medium", "devto"],
  "schedule": "2026-06-21T09:00:00Z"
}
```

**Response (202 Accepted)**:
```json
{
  "success": true,
  "distributionId": "dist-1719000000000",
  "status": "distributing",
  "message": "Content distribution started",
  "platforms": ["blog", "newsletter", "social", "medium", "devto"],
  "statusUrl": "/api/automation/self-help?status=check&id=dist-1719000000000"
}
```

**Completion Response**:
```json
[
  {
    "success": true,
    "platform": "blog",
    "postId": "content-1719000000000.md",
    "url": "https://github.com/quantam101/content/blob/main/blog/content-1719000000000.md"
  },
  {
    "success": true,
    "platform": "newsletter",
    "postId": "campaign-12345",
    "scheduledTime": "2026-06-21T09:00:00Z"
  },
  {
    "success": true,
    "platform": "social",
    "url": "https://twitter.com/quantam101/status/..."
  },
  {
    "success": true,
    "platform": "medium",
    "postId": "abcd1234",
    "url": "https://medium.com/@quantam101/..."
  },
  {
    "success": true,
    "platform": "devto",
    "postId": "567890",
    "url": "https://dev.to/quantam101/..."
  }
]
```

---

### 6. Export Content

```bash
POST /api/automation/self-help/export

{
  "contentId": "content-1719000000000",
  "formats": ["markdown", "html", "pdf", "docx"]
}
```

**Response (202 Accepted)**:
```json
{
  "success": true,
  "exportId": "export-1719000000000",
  "status": "exporting",
  "message": "Content export started",
  "formats": ["markdown", "html", "pdf", "docx"],
  "statusUrl": "/api/automation/self-help?status=check&id=export-1719000000000"
}
```

**Completion Response**:
```json
{
  "exportId": "export-1719000000000",
  "status": "complete",
  "progress": 100,
  "result": {
    "markdown": "# Content Title\n\n...",
    "html": "<h1>Content Title</h1>...",
    "pdf": "data:application/pdf;base64,...",
    "docx": "data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,..."
  }
}
```

---

## Environment Variables

Required:
```bash
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
YOUTUBE_API_KEY=AIzaSy...
RUNTIME_API_URL=https://your-backend.com
```

Optional (for platform integration):
```bash
FB_PAGE_ACCESS_TOKEN=        # Facebook/Instagram
MEDIUM_API_TOKEN=            # Medium
DEVTO_API_KEY=              # Dev.to
NEWSLETTER_API_KEY=         # Newsletter service
AFFILIATE_TAG=alreadyhere-20
AFFILIATE_LINKS={"product":"url",...}
```

---

## Usage Examples

### Example 1: Generate and Distribute Blog Post

```bash
# 1. Generate content
curl -X POST http://localhost:3000/api/automation/self-help/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "5 Proven Ways to Make $10K/Month",
    "difficulty": "beginner",
    "format": "blog",
    "keywords": ["make money", "side hustle", "passive income"],
    "targetAudience": "entrepreneurs",
    "tone": "inspirational",
    "includeAffiliates": true,
    "estimatedLength": "medium"
  }'

# Response: { "generationId": "gen-1719000000000", ... }

# 2. Check status
curl http://localhost:3000/api/automation/self-help?status=check&id=gen-1719000000000

# 3. When complete, distribute
curl -X POST http://localhost:3000/api/automation/self-help/distribute \
  -H "Content-Type: application/json" \
  -d '{
    "contentId": "content-1719000000000",
    "platforms": ["blog", "newsletter", "social", "medium", "devto"],
    "schedule": "2026-06-21T09:00:00Z"
  }'

# 4. Export to multiple formats
curl -X POST http://localhost:3000/api/automation/self-help/export \
  -H "Content-Type: application/json" \
  -d '{
    "contentId": "content-1719000000000",
    "formats": ["markdown", "html", "pdf", "docx"]
  }'
```

### Example 2: Create Complete Course

```bash
curl -X POST http://localhost:3000/api/automation/self-help/course \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Complete Guide to Python for Data Science",
    "difficulty": "intermediate",
    "numberOfLessons": 12
  }'
```

### Example 3: Process YouTube Video

```bash
curl -X POST http://localhost:3000/api/automation/self-help/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "videoId": "dQw4w9WgXcQ",
    "title": "10 Ways to Make Money Online"
  }'
```

### Example 4: Generate eBook

```bash
curl -X POST http://localhost:3000/api/automation/self-help/ebook \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Entrepreneur's Blueprint for Success",
    "numberOfChapters": 12
  }'
```

---

## Content Generation Pipeline

### Blog Article Flow

```
Request (topic, keywords, tone)
         ↓
Generate with OpenAI (gpt-4-turbo)
         ↓
Extract title & structure
         ↓
Format as Markdown
         ↓
Convert to HTML
         ↓
Extract SEO keywords
         ↓
Inject affiliate links (optional)
         ↓
Save metadata
         ↓
Ready for distribution
```

### Course Module Flow

```
Request (topic, difficulty)
         ↓
Generate curriculum with OpenAI
         ↓
Parse lessons (5-7 per module)
         ↓
Generate quizzes (2-3 per module)
         ↓
Add resources
         ↓
Structure with learning outcomes
         ↓
Save course data
```

### YouTube to Multi-Format Flow

```
YouTube Video ID
         ↓
Fetch captions via YouTube API
         ↓
Parse transcript
         ↓
Extract chapters (every ~500 chars)
         ↓
Generate key points
         ↓
Create blog post (with OpenAI)
         ↓
Generate study guide
         ↓
Extract SEO keywords
         ↓
Return structured data
```

### Distribution Flow

```
Generated Content
         ↓
For each platform:
  ├─→ GitHub (Markdown)
  ├─→ Newsletter (HTML + metadata)
  ├─→ Social Media (excerpt + link)
  ├─→ Medium (Markdown via API)
  ├─→ Dev.to (Markdown via API)
  └─→ LinkedIn (excerpt + CTA)
         ↓
Track results
```

---

## Integration with Existing Systems

### With Instagram Automation
```typescript
import { generateContent } from '@/app/lib/automation/self-help';
import { generateAndPostReel } from '@/app/lib/automation/instagram-reel';

// Generate article + create carousel from it
const article = await generateContent({
  topic: "Trading Strategy",
  format: "blog"
});

// Use article sections as carousel slides
const carouselSlides = article.content
  .split('\n\n')
  .slice(0, 10);
```

### With Email Automation
```typescript
import { generateContent } from '@/app/lib/automation/self-help';
import { sendNewsletterEmail } from '@/app/lib/automation/email-setup';

const content = await generateContent({
  topic: "Weekly Profit Tips",
  format: "blog"
});

await sendNewsletterEmail({
  subject: content.title,
  htmlContent: content.html,
  textContent: content.content,
  tags: content.metadata.tags
});
```

### With Gumroad Integration
```typescript
import { generateContent } from '@/app/lib/automation/self-help';
import { createGumroadProduct } from '@/app/lib/automation/gumroad';

const ebook = await generateEbookChapters("Passive Income Guide", 8);

await createGumroadProduct({
  name: "Passive Income Guide",
  description: ebook[0].content,
  product_type: "ebook",
  file_urls: exportedPdfUrl
});
```

---

## Content Quality Features

### SEO Optimization
- Automatic keyword extraction
- Meta description generation
- Heading hierarchy validation
- Internal linking suggestions
- Mobile-friendly formatting

### Readability
- Flesch-Kincaid grade level
- Optimal paragraph length
- Bullet point usage
- Section breaks
- Visual hierarchy

### Accessibility
- Alt text for figures
- Semantic HTML structure
- Proper heading nesting
- Color contrast awareness
- Keyboard navigation support

### Affiliate Integration
- Smart product matching
- FTC disclosure auto-injection
- Link validation
- Performance tracking

---

## Performance & Scalability

### Rate Limiting
- OpenAI: 3 concurrent generations
- Platform APIs: Respects rate limits
- Database: Optimized queries

### Caching
- Status checks cached in-memory
- Regeneration avoided for identical topics
- Template reuse for common structures

### Async Processing
- All generations non-blocking
- Status checks via polling/websocket
- Batch operations for efficiency

---

## Security

### API Key Management
- Keys in environment variables only
- Never logged or cached
- Rotated regularly
- Scoped to minimum permissions

### Content Safety
- Validation of all user inputs
- XSS prevention in HTML output
- SQL injection protection
- Rate limiting per IP

### Data Privacy
- No storage of API responses by default
- User content segregated
- GDPR compliance (data export/delete)

---

## Troubleshooting

### Generation Timeout
**Problem**: Content generation exceeds 5 minutes
**Solution**: 
- Check OPENAI_API_KEY is valid
- Verify network connectivity
- Try shorter topic/fewer requirements

### Platform Auth Failure
**Problem**: "API error: Unauthorized"
**Solution**:
- Verify API tokens are correct
- Check token expiration dates
- Refresh tokens if supported
- Verify correct environment

### Formatting Issues
**Problem**: HTML output has broken structure
**Solution**:
- Check Markdown syntax
- Verify heading levels
- Look for unclosed tags
- Check for special characters

---

## Advanced Customization

### Custom Content Templates

```typescript
import { generateContent } from '@/app/lib/automation/self-help';

const template = {
  includeIntroduction: true,
  includeConclusion: true,
  includeCTA: true,
  numberOfSections: 5,
  minWordsPerSection: 300,
  includeCallouts: true,
  calloutTypes: ['tip', 'warning', 'note']
};
```

### Custom Distribution Rules

```typescript
const distributionRules = {
  blog: { format: 'markdown', schedule: 'daily' },
  newsletter: { format: 'html', schedule: 'weekly' },
  social: { format: 'excerpt', schedule: 'immediate' },
  medium: { format: 'markdown', schedule: 'weekly' },
};
```

---

## Future Enhancements

- [ ] AI-generated images/diagrams
- [ ] Video script generation from blog posts
- [ ] Multi-language translation
- [ ] Content calendar UI dashboard
- [ ] A/B testing framework
- [ ] Engagement analytics
- [ ] Reader feedback integration
- [ ] Content refreshing for evergreen posts
- [ ] Competitor analysis integration
- [ ] Advanced SEO scoring

---

## Support & Documentation

Full API documentation: `/api/automation/self-help/docs`
Status dashboard: `/dashboard/content-automation`
Content management: `/command-center/content`


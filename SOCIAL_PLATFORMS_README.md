# Social Platforms Automation — Quick Start

Complete working code for Medium, Dev.to, and LinkedIn automation with content transformation, affiliate injection, and engagement tracking.

## Quick Links

- **Full Documentation**: See `SOCIAL_PLATFORMS_AUTOMATION.md`
- **Library Code**: `app/lib/automation/social-platforms.ts` (2500+ lines)
- **API Routes**: `app/api/automation/social-platforms/route.ts`
- **Examples**: `app/lib/automation/social-platforms-example.ts`
- **Test Suite**: `scripts/test-social-platforms.ts`

## What's Included

### Core Features

✅ **Cross-Platform Publishing**
- Publish to Medium, Dev.to, LinkedIn simultaneously
- Parallel or sequential mode
- Retry logic with exponential backoff

✅ **Content Transformation**
- Medium: Markdown format with canonical URL
- Dev.to: Markdown + frontmatter with metadata
- LinkedIn: Section-based format with hashtags

✅ **Affiliate Link Injection**
- Replace keywords with affiliate URLs
- Per-platform configuration
- Tracks replacement count

✅ **Engagement Tracking**
- Webhook ingestion for platform events
- JSONL event logging
- Metrics aggregation (views, likes, shares, comments)

✅ **API Endpoints**
- `POST /api/automation/social-platforms/publish` — Publish articles
- `POST /api/automation/social-platforms/webhook` — Ingest events
- `GET /api/automation/social-platforms/metrics` — Fetch metrics
- `GET /api/automation/social-platforms/status` — Check system status

## Setup (5 minutes)

### 1. Get API Credentials

**Medium** (https://medium.com/me/settings/security)
```bash
MEDIUM_API_TOKEN=your-integration-token
```

**Dev.to** (https://dev.to/settings/extensions)
```bash
DEVTO_API_KEY=your-api-key
```

**LinkedIn** (https://www.linkedin.com/developers/apps)
```bash
LINKEDIN_ACCESS_TOKEN=your-access-token
LINKEDIN_AUTHOR_ID=1234567890  # digits only, no "urn:li:person:" prefix
```

### 2. Set Environment Variables

Add to `.env` (server-side, never commit):

```bash
# Required
MEDIUM_API_TOKEN=...
DEVTO_API_KEY=...
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_AUTHOR_ID=...

# Optional but recommended
AFFILIATE_LINKS={"AWS":"https://aws.amazon.com/?ref=code","Vercel":"https://vercel.com/?ref=code"}
SOCIAL_CANONICAL_URL=https://profitengine.alreadyherellc.com
AUTOMATION_API_TOKEN=optional-secret-for-api-security
```

### 3. Deploy to Vercel

In Vercel dashboard → Environment Variables:

```
MEDIUM_API_TOKEN = your-token
DEVTO_API_KEY = your-key
LINKEDIN_ACCESS_TOKEN = your-token
LINKEDIN_AUTHOR_ID = your-id
AFFILIATE_LINKS = {...}
```

## Usage (3 examples)

### Example 1: Simple Publishing

```typescript
import { crossPostArticle } from '@/app/lib/automation/social-platforms';

const result = await crossPostArticle(
  {
    title: 'How to Build a SaaS',
    content: '# Markdown content...',
    tags: ['saas', 'business'],
    originalUrl: 'https://profitengine.com/blog/saas',
  },
  ['medium', 'devto', 'linkedin']
);

console.log(`✓ Published to ${result.successCount} platforms`);
```

### Example 2: API Request

```bash
curl -X POST https://profitengine.alreadyherellc.com/api/automation/social-platforms/publish \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Article",
    "content": "# Content...",
    "platforms": ["medium", "devto"],
    "publishImmediate": true
  }'
```

### Example 3: Batch Publishing

```typescript
import { crossPostBatch } from '@/app/lib/automation/social-platforms';

const articles = [
  { title: 'Article 1', content: '...', tags: [...] },
  { title: 'Article 2', content: '...', tags: [...] },
];

const results = await crossPostBatch(articles, ['medium', 'devto', 'linkedin']);
```

## Testing

```bash
# Run integration tests
npx ts-node scripts/test-social-platforms.ts

# Check environment
echo "MEDIUM_API_TOKEN=$MEDIUM_API_TOKEN" | wc -c

# Test API endpoint
curl -X GET http://localhost:3000/api/automation/social-platforms/status
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `app/lib/automation/social-platforms.ts` | 2500+ | Core library with all functions |
| `app/api/automation/social-platforms/route.ts` | 400 | API endpoints for publishing & tracking |
| `app/lib/automation/social-platforms-example.ts` | 600 | 10 detailed usage examples |
| `scripts/test-social-platforms.ts` | 450 | Integration test suite |
| `SOCIAL_PLATFORMS_AUTOMATION.md` | 1000+ | Complete documentation |
| `SOCIAL_PLATFORMS_README.md` | This file | Quick start guide |

## API Response Examples

### Publish Response

```json
{
  "success": true,
  "requestId": "crosspost-1718894823456",
  "data": {
    "results": [
      {
        "success": true,
        "platform": "medium",
        "postId": "abc123",
        "postUrl": "https://medium.com/@yourname/abc123"
      },
      {
        "success": true,
        "platform": "devto",
        "postId": "456",
        "postUrl": "https://dev.to/yourname/article-title"
      },
      {
        "success": true,
        "platform": "linkedin",
        "postId": "def789",
        "postUrl": "https://www.linkedin.com/feed/update/def789"
      }
    ],
    "successCount": 3,
    "failureCount": 0
  }
}
```

### Metrics Response

```json
{
  "success": true,
  "data": {
    "platform": "devto",
    "postId": "12345",
    "views": 245,
    "likes": 18,
    "shares": 7,
    "comments": 3,
    "averageReadTime": 4.5
  }
}
```

## Integration with Blog Publishing

```typescript
// When a blog post is published
async function onBlogPublished(post: BlogPost) {
  // 1. Save to database
  await db.posts.create(post);
  
  // 2. Cross-post to social platforms
  const result = await crossPostArticle(
    {
      title: post.title,
      content: post.markdown,
      tags: post.tags,
      originalUrl: `https://profitengine.com/blog/${post.slug}`,
    },
    ['medium', 'devto', 'linkedin']
  );
  
  // 3. Store cross-post links
  await db.posts.update(post.id, {
    mediumUrl: result.results[0]?.postUrl,
    devtoUrl: result.results[1]?.postUrl,
    linkedinUrl: result.results[2]?.postUrl,
  });
}
```

## Webhook Integration

Set webhook endpoint in platform settings to:

```
https://profitengine.alreadyherellc.com/api/automation/social-platforms/webhook
```

Events logged to `.runtime/social-platforms/engagement-events.jsonl`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "MEDIUM_API_TOKEN not configured" | Add to `.env` (server-side) |
| "Failed to publish to Dev.to: 401" | Verify API key at https://dev.to/settings/extensions |
| LinkedIn post doesn't appear | Check `LINKEDIN_AUTHOR_ID` is correct (digits only) |
| Affiliate links not injected | Verify `AFFILIATE_LINKS` is valid JSON |
| Metrics not showing | Check webhook endpoint or manually log events |

## Performance

- **Publishing**: 3-5 seconds for all platforms (parallel)
- **Retries**: Exponential backoff (1s, 2s, 4s)
- **Metrics**: Real-time via webhooks, fallback to event log
- **Storage**: JSONL format in `.runtime/social-platforms/`

## Rate Limits

| Platform | Limit | Recommendation |
|----------|-------|-----------------|
| Medium | 10 posts/day | Daily automation safe |
| Dev.to | 10 posts/hour | Batch publishing safe |
| LinkedIn | 1 post/profile/day | Manual check recommended |

## Next Steps

1. **Set environment variables** → Follow Setup section
2. **Run tests** → `npx ts-node scripts/test-social-platforms.ts`
3. **Test publishing** → Call `/api/automation/social-platforms/publish`
4. **Monitor metrics** → Check `/api/automation/social-platforms/metrics`
5. **Integrate with blog** → Use `crossPostArticle()` in publish handler

## Security Notes

- API credentials stored server-side only, never in client code
- Optional `AUTOMATION_API_TOKEN` for endpoint authentication
- Webhook events logged to `.runtime/` (not committed)
- Affiliate links in public URLs (intentional, for monetization)

## Support

- See `SOCIAL_PLATFORMS_AUTOMATION.md` for full docs
- See `app/lib/automation/social-platforms-example.ts` for code examples
- Check `scripts/test-social-platforms.ts` for test cases

## License

Part of ProfitEngine v5 — © Already Here LLC

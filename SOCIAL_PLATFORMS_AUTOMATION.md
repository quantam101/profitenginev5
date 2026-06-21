# Social Platforms Automation — Complete Integration Guide

This document covers the Medium, Dev.to, and LinkedIn automation system for ProfitEngine v5.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Configuration](#setup--configuration)
4. [API Endpoints](#api-endpoints)
5. [Core Functions](#core-functions)
6. [Usage Examples](#usage-examples)
7. [Engagement Tracking](#engagement-tracking)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The social platforms automation system provides:

- **Cross-posting**: Publish articles to Medium, Dev.to, and LinkedIn simultaneously
- **Content Transformation**: Automatically format content for each platform's requirements
- **Affiliate Link Injection**: Replace keywords with configured affiliate URLs
- **Engagement Tracking**: Ingest and aggregate metrics from platforms via webhooks
- **Retry Logic**: Exponential backoff for reliable publishing
- **Batch Operations**: Publish multiple articles in parallel or serial mode
- **API Security**: Optional token-based authentication

### Key Features

| Feature | Medium | Dev.to | LinkedIn |
|---------|--------|--------|----------|
| Text Publishing | ✓ | ✓ | ✓ |
| Cover Images | ✓ | ✓ | ✓ |
| Tags | ✓ | ✓ | ✓ (hashtags) |
| Canonical URL | ✓ | ✓ | — |
| Markdown | ✓ | ✓ | Limited |
| Code Blocks | ✓ | ✓ | ✓ |
| Affiliate Links | ✓ | ✓ | ✓ |
| Tracking Pixels | ✓ | ✓ | Limited |

---

## Architecture

### Components

```
app/lib/automation/social-platforms.ts
├── Content Transformation (Medium, Dev.to, LinkedIn)
├── Platform API Integrations
├── Affiliate Link Injection
├── Cross-posting Orchestration
└── Engagement Tracking

app/api/automation/social-platforms/route.ts
├── POST /api/automation/social-platforms/publish
├── POST /api/automation/social-platforms/webhook
├── GET  /api/automation/social-platforms/metrics
└── GET  /api/automation/social-platforms/status
```

### Data Flow

```
Article Content
    ↓
[Content Transformation]
    ├→ transformForMedium()
    ├→ transformForDevto()
    └→ transformForLinkedIn()
    ↓
[Affiliate Link Injection]
    ↓
[Platform APIs]
    ├→ Medium API
    ├→ Dev.to API
    └→ LinkedIn API
    ↓
[Post Results]
    ↓
[Webhook Events] → [Engagement Tracking] → [Metrics Aggregation]
```

---

## Setup & Configuration

### Prerequisites

1. **Medium Account**
   - Go to https://medium.com/me/settings/security
   - Create integration token
   - Save as `MEDIUM_API_TOKEN`

2. **Dev.to Account**
   - Sign up at https://dev.to
   - Go to https://dev.to/settings/extensions
   - Generate API key
   - Save as `DEVTO_API_KEY`

3. **LinkedIn Account**
   - Register app at https://www.linkedin.com/developers/apps
   - Obtain OAuth access token
   - Find your author/person URN (format: `urn:li:person:12345678`)
   - Save as `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_AUTHOR_ID`

### Environment Variables

Add to your `.env` (server-side only, never commit):

```bash
# Platform API Credentials (required)
MEDIUM_API_TOKEN=your-token-here
DEVTO_API_KEY=your-key-here
LINKEDIN_ACCESS_TOKEN=your-access-token
LINKEDIN_AUTHOR_ID=your-person-id

# Affiliate Links (JSON object)
AFFILIATE_LINKS={"AWS":"https://aws.amazon.com/?ref=yourcode","Vercel":"https://vercel.com/?ref=yourcode"}

# Optional: Configuration
SOCIAL_CANONICAL_URL=https://profitengine.alreadyherellc.com
SOCIAL_TRACKING_PIXEL_ID=UA-XXXXX-Y  # Google Analytics ID or custom
SOCIAL_WEBHOOK_EVENTS=https://profitengine.alreadyherellc.com/api/webhooks/social
RUNTIME_DATA_DIR=.runtime/social-platforms

# Optional: API Security
AUTOMATION_API_TOKEN=your-optional-secret-token
```

### Vercel Deployment

Set production environment variables in Vercel dashboard:

1. Go to Project Settings → Environment Variables
2. Add production values for:
   - `MEDIUM_API_TOKEN`
   - `DEVTO_API_KEY`
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_AUTHOR_ID`
   - `AFFILIATE_LINKS`
   - `AUTOMATION_API_TOKEN` (optional)

---

## API Endpoints

### POST /api/automation/social-platforms/publish

Publish an article to one or more platforms.

**Request:**

```json
{
  "title": "How to Build a Profitable SaaS",
  "content": "# Markdown Content\n\nYour article content here...",
  "excerpt": "Learn the secrets to building a profitable SaaS",
  "tags": ["saas", "business", "startup"],
  "coverImage": "https://example.com/cover.jpg",
  "originalUrl": "https://profitengine.com/blog/saas",
  "authorName": "Stephen Franklin",
  "authorBio": "Founder, Already Here LLC",
  "platforms": ["medium", "devto", "linkedin"],
  "publishImmediate": true,
  "parallel": true,
  "retries": 3,
  "webhookUrl": "https://your-webhook.com/callback"
}
```

**Response (Success):**

```json
{
  "success": true,
  "requestId": "crosspost-1718894823456",
  "data": {
    "requestId": "crosspost-1718894823456",
    "timestamp": "2024-06-20T12:34:56Z",
    "originalUrl": "https://profitengine.com/blog/saas",
    "results": [
      {
        "success": true,
        "platform": "medium",
        "postId": "abc123def456",
        "postUrl": "https://medium.com/@yourname/abc123",
        "publishedAt": "2024-06-20T12:34:56Z",
        "retries": 0
      },
      {
        "success": true,
        "platform": "devto",
        "postId": "123456",
        "postUrl": "https://dev.to/yourname/article-title-abc123",
        "publishedAt": "2024-06-20T12:34:56Z",
        "retries": 1
      },
      {
        "success": true,
        "platform": "linkedin",
        "postId": "ghi789jkl012",
        "postUrl": "https://www.linkedin.com/feed/update/ghi789",
        "publishedAt": "2024-06-20T12:34:56Z",
        "retries": 0
      }
    ],
    "successCount": 3,
    "failureCount": 0,
    "totalDuration": 4532
  },
  "timestamp": "2024-06-20T12:34:56Z"
}
```

**cURL Example:**

```bash
curl -X POST https://profitengine.alreadyherellc.com/api/automation/social-platforms/publish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTOMATION_API_TOKEN" \
  -d '{
    "title": "My Article",
    "content": "Article content...",
    "platforms": ["medium", "devto"]
  }'
```

---

### POST /api/automation/social-platforms/webhook

Ingest engagement events from social platforms or analytics.

**Request:**

```json
{
  "platform": "devto",
  "postId": "12345",
  "postUrl": "https://dev.to/yourname/article",
  "eventType": "view",
  "userId": "user-abc123",
  "timestamp": "2024-06-20T12:34:56Z",
  "metadata": {
    "referer": "google.com",
    "country": "US",
    "readTime": 5
  }
}
```

**Event Types:**

- `view` — Article viewed
- `like` — Article liked/appreciated
- `share` — Article shared
- `comment` — Comment posted
- `read_time` — Time spent reading (in metadata.readTime as seconds)

**Response:**

```json
{
  "success": true,
  "requestId": "api-1718894823456",
  "data": {
    "eventId": "event-1718894823456",
    "platform": "devto",
    "postId": "12345",
    "postUrl": "https://dev.to/yourname/article",
    "eventType": "view",
    "userId": "user-abc123",
    "timestamp": "2024-06-20T12:34:56Z",
    "metadata": {
      "referer": "google.com",
      "country": "US",
      "readTime": 5
    }
  },
  "timestamp": "2024-06-20T12:34:56Z"
}
```

---

### GET /api/automation/social-platforms/metrics

Retrieve engagement metrics for a published post.

**Query Parameters:**

- `platform` (required) — `medium`, `devto`, or `linkedin`
- `postId` (required) — Post ID from the publishing response

**Request:**

```
GET /api/automation/social-platforms/metrics?platform=devto&postId=12345
```

**Response:**

```json
{
  "success": true,
  "requestId": "api-1718894823456",
  "data": {
    "platform": "devto",
    "postId": "12345",
    "postUrl": "https://dev.to/yourname/article",
    "views": 245,
    "likes": 18,
    "shares": 7,
    "comments": 3,
    "averageReadTime": 4.5,
    "lastUpdated": "2024-06-20T12:34:56Z"
  },
  "timestamp": "2024-06-20T12:34:56Z"
}
```

---

### GET /api/automation/social-platforms/status

Check automation system status and available logs.

**Request:**

```
GET /api/automation/social-platforms/status
```

**Response:**

```json
{
  "success": true,
  "requestId": "api-1718894823456",
  "data": {
    "runtimeDir": ".runtime/social-platforms",
    "publishRequests": "available",
    "engagementEvents": "available",
    "logs": [
      {
        "type": "result",
        "path": "crosspost-1718894823456.json",
        "exists": true
      },
      {
        "type": "log",
        "path": "publish-requests.jsonl",
        "exists": true
      },
      {
        "type": "log",
        "path": "engagement-events.jsonl",
        "exists": true
      }
    ]
  },
  "timestamp": "2024-06-20T12:34:56Z"
}
```

---

## Core Functions

### `crossPostArticle()`

Cross-post a single article to specified platforms.

**Signature:**

```typescript
async function crossPostArticle(
  articleContent: ArticleContent,
  platforms?: Array<'medium' | 'devto' | 'linkedin'>,
  options?: {
    parallel?: boolean;      // Default: true
    retries?: number;        // Default: 3
    webhookUrl?: string;
  }
): Promise<CrossPostResult>
```

**Example:**

```typescript
import { crossPostArticle } from '@/app/lib/automation/social-platforms';

const result = await crossPostArticle(
  {
    title: 'My Article',
    content: '# Content here',
    tags: ['javascript', 'web'],
  },
  ['medium', 'devto'],
  { parallel: true, retries: 3 }
);

console.log(`Published to ${result.successCount} platforms`);
```

---

### `crossPostBatch()`

Cross-post multiple articles.

**Signature:**

```typescript
async function crossPostBatch(
  articles: ArticleContent[],
  platforms?: Array<'medium' | 'devto' | 'linkedin'>,
  options?: { parallel?: boolean; retries?: number; webhookUrl?: string }
): Promise<CrossPostResult[]>
```

**Example:**

```typescript
const articles = [
  { title: 'Article 1', content: '...', tags: [...] },
  { title: 'Article 2', content: '...', tags: [...] },
];

const results = await crossPostBatch(articles, ['medium', 'devto', 'linkedin']);
```

---

### `logTrackingEvent()`

Log an engagement event (called by webhooks or tracking pixel).

**Signature:**

```typescript
async function logTrackingEvent(event: TrackingEvent): Promise<void>
```

**Example:**

```typescript
await logTrackingEvent({
  eventId: 'event-123',
  platform: 'devto',
  postId: '12345',
  postUrl: 'https://dev.to/...',
  eventType: 'view',
  userId: 'user-abc',
  timestamp: new Date().toISOString(),
  metadata: { referer: 'google.com' }
});
```

---

### `getEngagementMetrics()`

Fetch aggregated metrics for a post.

**Signature:**

```typescript
async function getEngagementMetrics(
  platform: 'medium' | 'devto' | 'linkedin',
  postId: string
): Promise<EngagementMetrics | null>
```

**Example:**

```typescript
const metrics = await getEngagementMetrics('devto', '12345');
console.log(`${metrics.views} views, ${metrics.likes} likes`);
```

---

## Usage Examples

### Example 1: Publish from API

```typescript
// In your Next.js API route or server action
const response = await fetch('/api/automation/social-platforms/publish', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.AUTOMATION_API_TOKEN}`,
  },
  body: JSON.stringify({
    title: 'How to Scale Your SaaS',
    content: '# Introduction\n\nContent here...',
    tags: ['saas', 'scaling'],
    coverImage: 'https://example.com/cover.jpg',
    originalUrl: 'https://profitengine.com/blog/scaling',
    platforms: ['medium', 'devto', 'linkedin'],
    publishImmediate: true,
  }),
});

const result = await response.json();
console.log(result);
```

---

### Example 2: Publish from Server Function

```typescript
// In app/lib/ or API route
import { crossPostArticle } from '@/app/lib/automation/social-platforms';

export async function publishBlogPost(post: BlogPost) {
  const result = await crossPostArticle(
    {
      title: post.title,
      content: post.markdown,
      excerpt: post.excerpt,
      tags: post.tags,
      coverImage: post.featuredImage,
      originalUrl: `https://profitengine.com/blog/${post.slug}`,
      authorName: 'Stephen Franklin',
    },
    ['medium', 'devto', 'linkedin'],
    { parallel: true, retries: 3 }
  );

  return result;
}
```

---

### Example 3: Handle Webhook Events

```typescript
// app/api/webhooks/social/route.ts
import { logTrackingEvent } from '@/app/lib/automation/social-platforms';

export async function POST(request: Request) {
  const body = await request.json();

  // Log event for metrics aggregation
  await logTrackingEvent({
    eventId: `${Date.now()}`,
    platform: body.platform,
    postId: body.postId,
    postUrl: body.postUrl,
    eventType: body.eventType,
    userId: body.userId,
    timestamp: new Date().toISOString(),
    metadata: body.metadata,
  });

  return Response.json({ success: true });
}
```

---

### Example 4: Display Metrics Dashboard

```typescript
// In your dashboard component
'use client';

import { useEffect, useState } from 'react';
import { EngagementMetrics } from '@/app/lib/automation/social-platforms';

export function MetricsDashboard({ postId }: { postId: string }) {
  const [metrics, setMetrics] = useState<Record<string, EngagementMetrics | null>>({});

  useEffect(() => {
    async function fetchMetrics() {
      const platforms = ['medium', 'devto', 'linkedin'] as const;
      const m: Record<string, EngagementMetrics | null> = {};

      for (const platform of platforms) {
        const res = await fetch(
          `/api/automation/social-platforms/metrics?platform=${platform}&postId=${postId}`
        );
        const data = await res.json();
        m[platform] = data.data;
      }

      setMetrics(m);
    }

    fetchMetrics();
  }, [postId]);

  return (
    <div>
      {Object.entries(metrics).map(([platform, m]) => (
        m && (
          <div key={platform}>
            <h3>{platform}</h3>
            <p>Views: {m.views}</p>
            <p>Likes: {m.likes}</p>
            <p>Shares: {m.shares}</p>
            <p>Comments: {m.comments}</p>
            {m.averageReadTime && <p>Avg Read Time: {m.averageReadTime}m</p>}
          </div>
        )
      ))}
    </div>
  );
}
```

---

## Engagement Tracking

### Setting Up Webhooks

Each platform supports webhooks for real-time engagement events.

#### Medium

Medium doesn't have real-time webhooks, but you can query metrics via their API or use a third-party service.

#### Dev.to

1. Go to https://dev.to/settings/webhooks (if available)
2. Or manually log events via POST `/api/automation/social-platforms/webhook`

#### LinkedIn

1. Register webhook endpoint in LinkedIn app settings
2. Post events to `/api/automation/social-platforms/webhook`

### Manual Event Logging

If platforms don't support webhooks, manually log events:

```bash
# Log a view event
curl -X POST https://profitengine.alreadyherellc.com/api/automation/social-platforms/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "devto",
    "postId": "12345",
    "postUrl": "https://dev.to/...",
    "eventType": "view",
    "userId": "user-123",
    "metadata": {"referer": "google.com"}
  }'
```

### Tracking Events Structure

Events are logged to `.runtime/social-platforms/engagement-events.jsonl` (JSONL format, one event per line):

```json
{"eventId":"event-123","platform":"devto","postId":"12345","postUrl":"https://...","eventType":"view","userId":"user-abc","timestamp":"2024-06-20T12:34:56Z","metadata":{"referer":"google.com"}}
{"eventId":"event-124","platform":"devto","postId":"12345","postUrl":"https://...","eventType":"like","userId":"user-def","timestamp":"2024-06-20T12:35:00Z","metadata":{}}
```

---

## Troubleshooting

### Problem: "MEDIUM_API_TOKEN not configured"

**Solution:** Set `MEDIUM_API_TOKEN` in your `.env` file (server-side).

```bash
# .env (never commit!)
MEDIUM_API_TOKEN=your-token-here
```

---

### Problem: "Failed to publish to Dev.to: 401"

**Solution:** Verify your Dev.to API key:

1. Go to https://dev.to/settings/extensions
2. Check that the API key is valid and not expired
3. Regenerate if necessary and update `DEVTO_API_KEY`

---

### Problem: LinkedIn post doesn't appear

**Solution:** Verify LinkedIn author ID:

1. Check that `LINKEDIN_AUTHOR_ID` is correct (digits only, no "urn:li:person:" prefix)
2. Ensure `LINKEDIN_ACCESS_TOKEN` has `w_member_social` scope
3. Check LinkedIn app permissions in app settings

---

### Problem: Affiliate links not injected

**Solution:** Verify `AFFILIATE_LINKS` env var:

```bash
# Correct format (JSON object)
AFFILIATE_LINKS={"AWS":"https://aws.amazon.com/?ref=code","Vercel":"https://vercel.com/?ref=code"}

# Wrong format (won't parse)
AFFILIATE_LINKS={"AWS": "https://aws.amazon.com"}  # Extra space
```

---

### Problem: Metrics not showing

**Solution:**

1. Verify webhooks are being received: `curl GET /api/automation/social-platforms/status`
2. Check `.runtime/social-platforms/engagement-events.jsonl` exists
3. Ensure `postId` in metrics query matches the `postId` from publish response

---

### Problem: Retries fail with 429 (rate limit)

**Solution:** Reduce parallel publishing:

```typescript
const result = await crossPostArticle(article, platforms, {
  parallel: false,  // Sequential instead of parallel
  retries: 5,       // More retries with longer backoff
});
```

---

## Performance & Limits

| Platform | Rate Limit | Max Content | Notes |
|----------|-----------|------------|-------|
| Medium | 10 posts/day | Unlimited | Integration token limits apply |
| Dev.to | 10 posts/hour | Unlimited | API key per account |
| LinkedIn | 1 post/profile/day | 3000 chars | Soft limit; sections recommended |

---

## Cost & Pricing

| Platform | Cost | Free Tier |
|----------|------|-----------|
| Medium | Free (for writers) | Yes, unlimited posts |
| Dev.to | Free | Yes, unlimited posts |
| LinkedIn | Free (for individuals) | Yes |

All integrations use free APIs — no additional charges beyond your platform accounts.

---

## File Structure

```
app/lib/automation/
├── social-platforms.ts           # Main library (2000+ lines)
├── social-platforms-example.ts   # Usage examples
├── orchestrate.ts                # (existing) Overall orchestration
├── email-setup.ts                # (existing) Email automation
├── gumroad.ts                    # (existing) Gumroad integration
├── instagram-carousel.ts          # (existing) Instagram automation
├── instagram-reel.ts              # (existing) Instagram automation
└── instagram-stories.ts           # (existing) Instagram automation

app/api/automation/
├── social-platforms/
│   └── route.ts                  # API endpoints
└── launch/
    └── route.ts                  # (existing) Main orchestration endpoint

.runtime/social-platforms/        # Created at runtime
├── publish-requests.jsonl         # Publish request logs
├── engagement-events.jsonl        # Engagement event log
└── {requestId}.json              # Individual publication results
```

---

## Migration & Integration

### From Existing Blog

If you have existing blog posts on your site, integrate like this:

```typescript
// On blog publish:
import { crossPostArticle } from '@/app/lib/automation/social-platforms';

async function onBlogPublish(post: BlogPost) {
  // Publish to blog first
  await publishToDatabase(post);

  // Then cross-post to social platforms
  const result = await crossPostArticle(
    {
      title: post.title,
      content: post.markdown,
      excerpt: post.excerpt,
      tags: post.tags,
      coverImage: post.image,
      originalUrl: `${process.env.PUBLIC_SITE_URL}/blog/${post.slug}`,
      authorName: 'Stephen Franklin',
    },
    ['medium', 'devto', 'linkedin']
  );

  // Store cross-post URLs
  await updateBlogPost(post.id, {
    mediumUrl: result.results[0]?.postUrl,
    devtoUrl: result.results[1]?.postUrl,
    linkedinUrl: result.results[2]?.postUrl,
  });
}
```

---

## Support & Maintenance

For issues or feature requests:

1. Check the troubleshooting section above
2. Review platform-specific API documentation:
   - Medium: https://github.com/Medium/medium-api-docs
   - Dev.to: https://developers.forem.com/api
   - LinkedIn: https://learn.microsoft.com/en-us/linkedin/shared/api-reference
3. File a GitHub issue with logs from `.runtime/social-platforms/`

---

## Version History

- **v1.0.0** (2024-06-20) — Initial release
  - Medium, Dev.to, LinkedIn publishing
  - Content transformation per platform
  - Affiliate link injection
  - Engagement tracking
  - API endpoints

---

**Last updated:** June 20, 2024

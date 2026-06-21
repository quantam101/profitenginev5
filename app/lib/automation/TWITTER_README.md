# Twitter Threads Automation Module

Complete automation system for generating, publishing, and tracking Twitter Threads with engagement metrics and affiliate link injection.

## Overview

The Twitter Threads module provides:
- **Smart thread generation** - Converts long-form content into optimized tweet sequences
- **Automatic publishing** - Posts threads to Twitter API v2 with proper reply chain linking
- **Engagement tracking** - Webhook-based real-time metrics (likes, retweets, replies, bookmarks)
- **Affiliate injection** - Injects affiliate links into tweet content automatically
- **Metrics API** - Retrieve detailed engagement and performance analytics
- **Dry-run mode** - Test content without publishing to Twitter

## Quick Start

### 1. Environment Setup

Add these to your `.env` or Vercel Environment Variables:

```bash
# Required for publishing
TWITTER_BEARER_TOKEN=AAAA1234567890abcdefghijklmnopqrstuvwxyz

# Optional - for webhook security
TWITTER_WEBHOOK_SECRET=whsec_test_mock123

# Optional - for affiliate tracking
AFFILIATE_LINKS={"tool":"https://affiliate.example.com/tool","course":"https://affiliate.example.com/course"}
```

### 2. Basic Usage

#### Generate a Thread

```typescript
import { generateThread } from '@/app/lib/automation/twitter';

const content = {
  title: '10 Ways to Automate Your Income',
  content: 'Long-form content here...',
  excerpt: 'A quick summary',
  hashtags: ['#Automation', '#Income'],
  ctaLink: 'https://example.com/guide',
};

const thread = await generateThread(content);
console.log(`Generated ${thread.tweetCount} tweets`);
```

#### Publish a Thread

```typescript
import { publishThread } from '@/app/lib/automation/twitter';

const result = await publishThread({
  threadContent: content,
  publishImmediate: true,
  dryRun: false, // Set to false for production
});

if (result.success) {
  console.log(`Published! Thread ID: ${result.firstTweetId}`);
  console.log(`First tweet: ${result.firstTweetUrl}`);
}
```

#### Get Metrics

```typescript
import { getThreadMetrics } from '@/app/lib/automation/twitter';

const metrics = await getThreadMetrics(threadId);
console.log({
  engagement: metrics.totalEngagement,
  engagementRate: metrics.engagementRate + '%',
  likes: metrics.likes,
  retweets: metrics.retweets,
  replies: metrics.replies,
});
```

## API Endpoints

### POST /api/automation/twitter/publish

Publish a thread to Twitter.

**Request:**
```json
{
  "title": "Thread Title",
  "content": "Long-form content...",
  "excerpt": "Optional summary",
  "hashtags": ["#tag1", "#tag2"],
  "mentions": ["@user1", "@user2"],
  "ctaLink": "https://example.com",
  "affiliateLinks": {
    "keyword": "https://affiliate.url"
  },
  "publishImmediate": true,
  "dryRun": false,
  "webhookUrl": "https://example.com/webhook"
}
```

**Response:**
```json
{
  "success": true,
  "requestId": "twitter-1718889600000-abc123",
  "data": {
    "threadId": "1234567890",
    "firstTweetId": "1234567890",
    "firstTweetUrl": "https://twitter.com/user/status/1234567890",
    "tweets": [
      {
        "tweetId": "1234567890",
        "tweetUrl": "https://twitter.com/user/status/1234567890",
        "text": "Tweet content...",
        "createdAt": "2024-06-20T12:00:00Z"
      }
    ],
    "publishedAt": "2024-06-20T12:00:00Z",
    "executionTime": 2500
  },
  "timestamp": "2024-06-20T12:00:00Z"
}
```

### POST /api/automation/twitter/webhook

Ingest engagement events from Twitter webhooks.

**Request:**
```json
{
  "threadId": "1234567890",
  "tweetId": "1234567891",
  "eventType": "like",
  "userId": "twitter-user-123",
  "userName": "john_doe",
  "metadata": {
    "userFollowers": 50000
  }
}
```

**Response:**
```json
{
  "success": true,
  "requestId": "twitter-webhook-1718889600000-abc123",
  "data": {
    "eventId": "1718889600000-abc123"
  },
  "timestamp": "2024-06-20T12:00:00Z"
}
```

### GET /api/automation/twitter/metrics

Get thread metrics and engagement data.

**Query Parameters:**
- `threadId` (required) - The thread ID to get metrics for

**Response:**
```json
{
  "success": true,
  "requestId": "twitter-metrics-1718889600000-abc123",
  "data": {
    "threadId": "1234567890",
    "tweetCount": 8,
    "totalImpressions": 5432,
    "totalEngagement": 234,
    "likes": 150,
    "retweets": 50,
    "replies": 20,
    "bookmarks": 14,
    "clicks": 10,
    "engagementRate": 4.31,
    "lastUpdated": "2024-06-20T12:15:00Z"
  },
  "timestamp": "2024-06-20T12:15:00Z"
}
```

### GET /api/automation/twitter/status

Check automation service status and configuration.

**Response:**
```json
{
  "success": true,
  "requestId": "twitter-status-1718889600000-abc123",
  "data": {
    "configured": true,
    "bearerTokenConfigured": true,
    "webhookSecretConfigured": true,
    "timestamp": "2024-06-20T12:00:00Z"
  },
  "timestamp": "2024-06-20T12:00:00Z"
}
```

## Thread Generation Rules

### Character Limits
- **Per tweet:** 280 characters (Twitter's default)
- **Per thread:** Up to 50 tweets

### Content Processing
1. Splits content into logical paragraphs
2. Segments paragraphs into 280-character chunks
3. Preserves word boundaries (no mid-word breaks)
4. First tweet includes thread title + emoji
5. Last tweet includes CTA link + hashtags
6. Injects affiliate links where matched

### Engagement Scoring
Estimated engagement is calculated based on:
- Hashtag count (+5 per hashtag)
- Mention count (+3 per mention)
- Questions in content (+10)
- Call-to-action (+15)
- Emojis (+2 per emoji)

## Integration with Master Orchestrator

```typescript
const twitterTask = {
  id: 'twitter-weekly-thread',
  name: 'Publish Weekly Thread',
  type: 'twitter',
  enabled: true,
  priority: 'normal',
  timeout: 60000,
  retryMaxAttempts: 3,
  dependencies: [
    {
      taskId: 'content-generation',
      required: true,
      wait: true,
    },
  ],
  metadata: {
    title: 'Weekly Automation Tips',
    contentSource: 'blog-post',
    hashtagCategories: ['automation', 'business'],
  },
};

// Register with orchestrator
const orchestrator = new OrchestratorEngine(config);
orchestrator.registerTask(twitterTask);
```

## Dashboard Card Component

Use the included `TwitterThreadCard` component in your dashboard:

```typescript
import { TwitterThreadCard } from '@/app/components/TwitterThreadCard';

export function Dashboard() {
  const [metrics, setMetrics] = useState(null);

  const handlePublish = async () => {
    // Call API to publish
  };

  return (
    <TwitterThreadCard
      threadId="1234567890"
      status="published"
      metrics={metrics}
      onPublish={handlePublish}
    />
  );
}
```

## Webhook Integration

### Setting Up Twitter Webhooks

1. **Register webhook endpoint** on Twitter Developer Portal
2. **Add webhook URL**: `https://yourdomain.com/api/automation/twitter/webhook`
3. **Configure events**: Select events (likes, retweets, replies, etc.)
4. **Set signature secret**: Use for HMAC verification

### Signature Verification

Requests include `x-twitter-signature` header with HMAC-SHA256 hash:

```typescript
const crypto = require('crypto');
const hash = crypto
  .createHmac('sha256', process.env.TWITTER_WEBHOOK_SECRET)
  .update(payload)
  .digest('hex');

if (hash === signature) {
  // Valid signature - process event
}
```

## Affiliate Link Injection

Automatically replace keywords with affiliate links:

```typescript
const content = {
  title: 'Tool Recommendations',
  content: 'I love using Buffer and Midjourney for my workflow',
  affiliateLinks: {
    Buffer: 'https://affiliate.buffer.com/promo',
    Midjourney: 'https://affiliate.midjourney.com',
  },
};

// In generated tweets:
// "I love using https://affiliate.buffer.com/promo and https://affiliate.midjourney.com for my workflow"
```

## Error Handling

### Dry-Run Mode

Test threads without publishing:

```typescript
const result = await publishThread({
  threadContent: content,
  dryRun: true, // Returns mock results
});
```

### Retry Logic

Automatic retries with exponential backoff:

```typescript
const result = await publishThread({
  threadContent: content,
  retryMaxAttempts: 3, // Retries up to 3 times
});
```

### Rate Limiting

- 1 tweet posted per 500ms (prevents rate limit issues)
- Respects Twitter API v2 rate limits
- Circuit breaker for cascading failures

## Storage & Logs

### Directory Structure
```
.runtime/
├── twitter-metrics/
│   └── thread-{threadId}.jsonl
└── twitter-logs/
    └── twitter-{YYYY-MM-DD}.jsonl
```

### Log Format (JSONL)
```json
{"timestamp":"2024-06-20T12:00:00Z","operation":"publish_thread_complete","title":"...","tweetCount":8}
```

## Testing

Run the comprehensive test suite:

```bash
npm test -- tests/twitter-automation.test.ts
```

Tests cover:
- Thread generation and text segmentation
- Tweet character limit enforcement
- Affiliate link injection
- Engagement metrics tracking
- Webhook signature verification
- Error handling and edge cases
- Unicode/emoji handling
- URL preservation

## Examples

See `twitter-examples.ts` for detailed examples:

1. Simple thread publishing
2. Thread with affiliate links
3. Generate-only preview mode
4. Metrics retrieval
5. Engagement logging
6. Orchestrator integration
7. Webhook setup
8. Full end-to-end workflow

## Performance Metrics

### Generation
- ~50-100 tweets/second
- Memory usage: <10MB per thread
- Average execution time: 200-500ms

### Publishing
- 280 characters per tweet enforced
- Rate limited to 1 tweet per 500ms
- Respects Twitter API rate limits

### Engagement Tracking
- Real-time webhook processing
- <100ms per event
- Persistent storage in JSONL format

## Security

### API Authentication
- Optional `AUTOMATION_API_TOKEN` for securing endpoints
- Add header: `Authorization: Bearer YOUR_TOKEN`

### Webhook Verification
- HMAC-SHA256 signature verification
- Secret stored in environment variables
- Signature in `x-twitter-signature` header

### Rate Limiting
- Built-in backoff for Twitter API limits
- Circuit breaker for failure cascades
- Graceful degradation on rate limit errors

## Troubleshooting

### "TWITTER_BEARER_TOKEN not configured"
- Add `TWITTER_BEARER_TOKEN` to environment variables
- Get token from Twitter Developer Portal

### Tweets exceeding 280 characters
- Handled automatically by text segmentation
- Check content for very long words/URLs

### Webhook events not received
- Verify webhook URL is publicly accessible
- Check Twitter Developer Portal webhook settings
- Ensure `TWITTER_WEBHOOK_SECRET` is configured correctly

### Affiliate links not injected
- Ensure `AFFILIATE_LINKS` is valid JSON
- Check keyword matching is case-sensitive
- Verify URLs in affiliate map are valid

## API Token Documentation

See `claude-api.ts` for reference on Claude API token counting and pricing if using Claude for content generation in combination with this module.

## See Also

- Master Orchestrator: `master-orchestrator.ts`
- Social Platforms: `social-platforms.ts`
- API Rate Limiter: `rate-limiter.ts`
- Dashboard: `/app/dashboard/page.tsx`

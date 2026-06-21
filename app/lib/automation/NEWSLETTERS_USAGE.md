# Newsletter Automation — Complete Guide

## Overview

The newsletter automation system provides unified API wrappers for publishing content to multiple newsletter platforms:

- **Beehiiv** — Email list management with advanced analytics
- **Substack** — Independent newsletter hosting
- **ConvertKit** — Creator-focused email platform
- **Medium** — Content distribution with built-in audience
- **Dev.to** — Developer community platform
- **Hashnode** — Technical blogging platform

## Architecture

### Components

1. **ContentTransformer** — Converts content between formats (Markdown → HTML → Plain Text)
2. **Platform Publishers** — Individual API wrappers for each platform
   - BeehiivPublisher
   - SubstackPublisher
   - ConvertKitPublisher
   - MediumPublisher
   - DevToPublisher
   - HashnodePublisher
3. **NewsletterBatchPublisher** — Orchestrates publishing across multiple platforms
4. **RateLimiters** — Per-platform rate limiting to avoid throttling
5. **SubscriberMetrics** — Unified metrics tracking across platforms

### Key Features

- ✅ Automatic content transformation for each platform
- ✅ Per-platform rate limiting (prevents API throttling)
- ✅ Automatic retry with exponential backoff
- ✅ Scheduled publishing support
- ✅ Subscriber tracking and metrics aggregation
- ✅ Error handling and detailed logging
- ✅ Dry-run mode for testing

## Configuration

### Environment Variables

Set these in your `.env.production`:

```bash
# Platform API Keys
BEEHIIV_API_KEY=your_beehiiv_api_key
SUBSTACK_API_TOKEN=your_substack_api_token
CONVERTKIT_API_KEY=your_convertkit_api_key
MEDIUM_API_TOKEN=your_medium_api_token
DEVTO_API_KEY=your_devto_api_key
HASHNODE_API_KEY=your_hashnode_api_key

# Optional: API token for securing the automation endpoint
AUTOMATION_API_TOKEN=your_secure_automation_token
```

### How to Get API Keys

#### Beehiiv
1. Log in to Beehiiv dashboard
2. Go to Settings → API Keys
3. Create new API key with "posts:write" scope
4. Copy the API key

#### Substack
1. Log in to Substack account
2. Go to Settings → Account
3. Copy API token (or create one in Integrations)
4. Note: Some endpoints may require publication ID

#### ConvertKit
1. Log in to ConvertKit
2. Go to Account → Settings → API Key
3. Copy API key and API secret
4. Use API key for authentication

#### Medium
1. Log in to Medium
2. Go to Settings → Publishing → API
3. Create integration and get API token
4. Copy your Medium user ID (from profile URL)

#### Dev.to
1. Log in to Dev.to
2. Go to Settings → Account → API Keys
3. Create new API key
4. Copy the key

#### Hashnode
1. Log in to Hashnode
2. Go to Settings → Developer
3. Create new API token
4. Get your publication ID from publication settings

## Usage Examples

### Basic Publishing (TypeScript)

```typescript
import {
  NewsletterBatchPublisher,
  NewsletterContent,
} from '@/app/lib/automation/newsletters';

// Create configuration for enabled platforms
const config = [
  {
    platform: 'beehiiv' as const,
    enabled: true,
    apiKey: process.env.BEEHIIV_API_KEY || '',
  },
  {
    platform: 'substack' as const,
    enabled: true,
    apiKey: process.env.SUBSTACK_API_TOKEN || '',
  },
  {
    platform: 'medium' as const,
    enabled: true,
    apiKey: process.env.MEDIUM_API_TOKEN || '',
  },
];

// Create publisher instance
const publisher = new NewsletterBatchPublisher(config);

// Prepare content
const content: NewsletterContent = {
  title: 'Weekly Trading Insights #45',
  subtitle: 'Market analysis and opportunities',
  body: `
# Overview
This week's market analysis reveals significant opportunities.

## Key Findings
- Stock market rallied 2.3% on inflation data
- Crypto assets showing strong recovery momentum
- Real estate market cooling in major markets

## Action Items
1. Review your portfolio allocation
2. Consider rebalancing positions
3. Monitor key economic indicators

[View Full Analysis](https://profitengine.alreadyherellc.com/analysis)
  `,
  summary: 'Key market movements and trading opportunities for the week',
  tags: ['trading', 'markets', 'analysis', 'weekly'],
  featuredImage: 'https://example.com/market-analysis.jpg',
  ctaText: 'View Full Analysis',
  ctaLink: 'https://profitengine.alreadyherellc.com/analysis',
};

// Publish to all platforms
const result = await publisher.publishToAll(content);

console.log('Publishing results:');
console.log(`Successful: ${result.successful.length}`);
console.log(`Failed: ${result.failed.length}`);
console.log(`Total duration: ${result.totalDuration}ms`);

// View results
result.successful.forEach((r) => {
  console.log(`✓ ${r.platform}: ${r.url}`);
});

result.failed.forEach((r) => {
  console.log(`✗ ${r.platform}: ${r.error}`);
});
```

### Publishing to Specific Platforms

```typescript
// Publish only to selected platforms
const result = await publisher.publishToSelected(content, [
  'beehiiv',
  'medium',
  'devto',
]);

console.log(`Published to ${result.successful.length} platforms`);
```

### Scheduled Publishing

```typescript
// Schedule for specific time
const content: NewsletterContent = {
  title: 'Friday Market Recap',
  body: '...',
  publishedAt: new Date('2024-06-21T15:00:00Z'), // Schedule for 3 PM UTC
};

const result = await publisher.publishToAll(content);
```

### Getting Metrics

```typescript
// Get subscriber metrics across all platforms
const metrics = await publisher.getAggregateMetrics();

console.log('Subscriber Metrics:');
console.log(`Total subscribers: ${metrics.totalSubscribers}`);

metrics.platforms.forEach((m) => {
  console.log(`${m.platform}:`);
  console.log(`  Subscribers: ${m.totalSubscribers || 'N/A'}`);
  console.log(`  Open rate: ${m.openRate?.toFixed(1) || 'N/A'}%`);
  console.log(`  Click rate: ${m.clickRate?.toFixed(1) || 'N/A'}%`);
});
```

### Individual Platform Publishing

```typescript
import { BeehiivPublisher } from '@/app/lib/automation/newsletters';

const beehiiv = new BeehiivPublisher(process.env.BEEHIIV_API_KEY || '');

// Publish to Beehiiv only
const result = await beehiiv.publish(content);

if (result.success) {
  console.log(`Published: ${result.url}`);
  console.log(`Post ID: ${result.postId}`);
} else {
  console.error(`Error: ${result.error}`);
}

// Get Beehiiv metrics
const metrics = await beehiiv.getMetrics();
console.log(`Beehiiv subscribers: ${metrics.totalSubscribers}`);
```

## API Endpoint Usage

### POST /api/automation/newsletters

Publish newsletter to configured platforms via HTTP.

#### Request

```bash
curl -X POST https://profitengine.alreadyherellc.com/api/automation/newsletters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTOMATION_API_TOKEN" \
  -d '{
    "title": "Weekly Market Analysis",
    "body": "# Market Overview\n\nThis week...",
    "summary": "Key market movements",
    "tags": ["trading", "markets"],
    "featuredImage": "https://example.com/image.jpg",
    "ctaText": "Read Full Analysis",
    "ctaLink": "https://profitengine.alreadyherellc.com/analysis",
    "platforms": ["beehiiv", "substack", "medium"],
    "scheduleFor": "2024-06-21T15:00:00Z"
  }'
```

#### Response (Success)

```json
{
  "success": true,
  "batchId": "newsletter-1718894823456",
  "summary": {
    "successful": 3,
    "failed": 0,
    "totalDuration": 5420
  },
  "results": [
    {
      "platform": "beehiiv",
      "success": true,
      "postId": "post-123",
      "url": "https://beehiiv.com/posts/post-123",
      "duration": 1240,
      "timestamp": "2024-06-21T09:30:45.123Z"
    },
    {
      "platform": "substack",
      "success": true,
      "postId": "sub-456",
      "url": "https://profitengine.substack.com/p/weekly-analysis",
      "duration": 1680,
      "timestamp": "2024-06-21T09:30:45.123Z"
    },
    {
      "platform": "medium",
      "success": true,
      "postId": "med-789",
      "url": "https://medium.com/@profitengine/weekly-analysis",
      "duration": 2500,
      "timestamp": "2024-06-21T09:30:45.123Z"
    }
  ],
  "metrics": [
    {
      "platform": "beehiiv",
      "totalSubscribers": 12500,
      "openRate": 28.5,
      "clickRate": 4.2
    },
    {
      "platform": "substack",
      "totalSubscribers": 8300,
      "openRate": 32.1,
      "clickRate": 5.8
    },
    {
      "platform": "medium",
      "totalSubscribers": 45000,
      "openRate": 15.2,
      "clickRate": 2.1
    }
  ],
  "timestamp": "2024-06-21T09:30:45.123Z"
}
```

#### Response (Partial Failure)

```json
{
  "success": false,
  "batchId": "newsletter-1718894823456",
  "summary": {
    "successful": 2,
    "failed": 1,
    "totalDuration": 4200
  },
  "results": [
    {
      "platform": "beehiiv",
      "success": true,
      "postId": "post-123",
      "url": "https://beehiiv.com/posts/post-123",
      "duration": 1240,
      "timestamp": "2024-06-21T09:30:45.123Z"
    },
    {
      "platform": "substack",
      "success": false,
      "error": "Failed after 3 attempts: Invalid API token",
      "duration": 2050,
      "timestamp": "2024-06-21T09:30:45.123Z"
    },
    {
      "platform": "medium",
      "success": true,
      "postId": "med-789",
      "url": "https://medium.com/@profitengine/weekly-analysis",
      "duration": 910,
      "timestamp": "2024-06-21T09:30:45.123Z"
    }
  ],
  "timestamp": "2024-06-21T09:30:45.123Z"
}
```

### GET /api/automation/newsletters

Get subscriber metrics across all platforms.

#### Request

```bash
curl -X GET "https://profitengine.alreadyherellc.com/api/automation/newsletters" \
  -H "Authorization: Bearer YOUR_AUTOMATION_API_TOKEN"
```

#### Query Parameters

- `platform` (optional) — Get metrics for specific platform only
  ```bash
  ?platform=beehiiv
  ```

#### Response

```json
{
  "success": true,
  "metrics": [
    {
      "platform": "beehiiv",
      "totalSubscribers": 12500,
      "openRate": 28.5,
      "clickRate": 4.2,
      "timestamp": "2024-06-21T09:30:45.123Z"
    },
    {
      "platform": "substack",
      "totalSubscribers": 8300,
      "openRate": 32.1,
      "clickRate": 5.8,
      "timestamp": "2024-06-21T09:30:45.123Z"
    },
    {
      "platform": "medium",
      "totalSubscribers": 45000,
      "openRate": 15.2,
      "clickRate": 2.1,
      "timestamp": "2024-06-21T09:30:45.123Z"
    }
  ],
  "summary": {
    "totalSubscribers": 65800,
    "platformCount": 3
  },
  "timestamp": "2024-06-21T09:30:45.123Z"
}
```

## Content Transformation

### Markdown to HTML

The system automatically converts Markdown to platform-specific HTML:

```typescript
import { ContentTransformer } from '@/app/lib/automation/newsletters';

const markdown = `
# Title
This is **bold** text and *italic* text.

- Item 1
- Item 2

[Link text](https://example.com)
`;

const html = ContentTransformer.toHTML(markdown);
// Output: <h1>Title</h1><p>This is <strong>bold</strong> text and <em>italic</em> text.</p><ul><li>Item 1</li><li>Item 2</li></ul><p><a href="https://example.com">Link text</a></p>
```

### Extract Plain Text

```typescript
const plainText = ContentTransformer.toPlainText(html);
```

### Create Excerpt

```typescript
const excerpt = ContentTransformer.extractExcerpt(content.body, 250);
// Returns first 250 characters with ellipsis
```

## Rate Limiting

Each platform has built-in rate limiting:

- **Beehiiv** — 10 requests/second
- **Substack** — 5 requests/second
- **ConvertKit** — 10 requests/second
- **Medium** — 5 requests/second
- **Dev.to** — 10 requests/second
- **Hashnode** — 5 requests/second

Rate limiting is automatic and doesn't require configuration.

## Error Handling

The system includes automatic retry logic with exponential backoff:

```typescript
// Default: 3 attempts
const publisher = new NewsletterBatchPublisher(config);

// Custom retry attempts
const publisher = new NewsletterBatchPublisher(config, 5); // Max 5 attempts
```

Retry delays:
- Attempt 1 → Fail → Wait 2 seconds
- Attempt 2 → Fail → Wait 4 seconds
- Attempt 3 → Fail → Wait 8 seconds

## Dry Run Mode

Test publishing without actually sending:

```bash
curl -X POST https://profitengine.alreadyherellc.com/api/automation/newsletters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTOMATION_API_TOKEN" \
  -d '{
    "title": "Test Newsletter",
    "body": "Testing...",
    "platforms": ["beehiiv", "substack"],
    "dryRun": true
  }'
```

Response will show successful count without actually publishing.

## Integration with Orchestration

Add to `app/lib/automation/orchestrate.ts`:

```typescript
import {
  NewsletterBatchPublisher,
  NewsletterContent,
} from './newsletters';

interface AutomationTask {
  name: string;
  type: 'gumroad' | 'carousel' | 'reel' | 'stories' | 'email' | 'newsletter';
  enabled: boolean;
}

async function orchestrateNewsletter() {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
    // ... other platforms
  ];

  const publisher = new NewsletterBatchPublisher(config);

  const content: NewsletterContent = {
    title: 'Weekly Digest',
    body: 'Your content here',
    tags: ['weekly', 'digest'],
  };

  const result = await publisher.publishToAll(content);
  return result;
}
```

## Troubleshooting

### "No newsletter platforms configured"

**Cause:** Missing environment variables for all platforms  
**Solution:** Set at least one of: `BEEHIIV_API_KEY`, `SUBSTACK_API_TOKEN`, `CONVERTKIT_API_KEY`, `MEDIUM_API_TOKEN`, `DEVTO_API_KEY`, `HASHNODE_API_KEY`

### "Invalid API token"

**Cause:** Incorrect or expired API key  
**Solution:** Verify the API key matches your platform account and hasn't expired

### "Rate limit exceeded"

**Cause:** Too many requests to platform  
**Solution:** The system automatically waits; allow extra time in high-volume scenarios

### "Network timeout"

**Cause:** Platform API slow or unreachable  
**Solution:** The system retries automatically; check platform status page

## Performance Optimization

### Parallel Publishing

By default, all platforms are published to in parallel:

```typescript
// All 6 platforms at once
const result = await publisher.publishToAll(content);
```

### Sequential Publishing

For rate-limited scenarios:

```typescript
const platforms = ['beehiiv', 'substack', 'medium'];

for (const platform of platforms) {
  const result = await publisher.publishToSelected(content, [platform]);
  if (!result.successful[0].success) {
    console.error(`Failed on ${platform}, continuing...`);
  }
}
```

## Monitoring & Logging

All operations log details:

```typescript
// Enable detailed logging
const result = await publisher.publishToAll(content);

result.successful.forEach((r) => {
  console.log(`[${r.timestamp}] ✓ ${r.platform}: ${r.duration}ms`);
});

result.failed.forEach((r) => {
  console.error(`[${r.timestamp}] ✗ ${r.platform}: ${r.error}`);
});
```

## Best Practices

1. **Always include metadata** — title, tags, summary for better reach
2. **Use featured images** — significantly improves engagement
3. **Schedule strategically** — publish when your audience is active
4. **Monitor metrics** — track open/click rates to improve content
5. **Test with dry-run** — validate content before publishing
6. **Set API tokens** — keep all keys in environment variables
7. **Handle errors gracefully** — partial failures are normal
8. **Batch publish** — schedule multiple newsletters for efficiency

## Security Considerations

1. **API Keys** — Store in environment variables, never in code
2. **HTTPS Only** — All platform APIs use HTTPS
3. **Rate Limiting** — Built-in protection against abuse
4. **Authentication** — Optional API token for the automation endpoint
5. **Validation** — Request payload validated server-side

## License

This newsletter automation system is part of ProfitEngine v5 and follows the project's license terms.

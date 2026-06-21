# Newsletter Automation — Quick Start Reference

## 🚀 30-Second Setup

### 1. Set Environment Variables
```bash
# Add to .env.production
BEEHIIV_API_KEY=your_key_here
SUBSTACK_API_TOKEN=your_token_here
CONVERTKIT_API_KEY=your_key_here
MEDIUM_API_TOKEN=your_token_here
DEVTO_API_KEY=your_key_here
HASHNODE_API_KEY=your_key_here
AUTOMATION_API_TOKEN=your_secure_token_here  # Optional
```

### 2. Publish Your First Newsletter

**Using TypeScript:**
```typescript
import { NewsletterBatchPublisher, NewsletterContent } from '@/app/lib/automation/newsletters';

const config = [
  { platform: 'beehiiv' as const, enabled: true, apiKey: process.env.BEEHIIV_API_KEY || '' },
  { platform: 'substack' as const, enabled: true, apiKey: process.env.SUBSTACK_API_TOKEN || '' },
];

const publisher = new NewsletterBatchPublisher(config);

const content: NewsletterContent = {
  title: 'My First Newsletter',
  body: '# Hello World\n\nThis is my first newsletter published to multiple platforms!',
  tags: ['newsletter', 'first'],
};

const result = await publisher.publishToAll(content);
console.log(`Published to ${result.successful.length} platforms`);
```

**Using HTTP API:**
```bash
curl -X POST https://profitengine.alreadyherellc.com/api/automation/newsletters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTOMATION_API_TOKEN" \
  -d '{
    "title": "My First Newsletter",
    "body": "# Hello World\n\nPublished to 6 platforms!",
    "tags": ["newsletter", "first"],
    "platforms": ["beehiiv", "substack", "medium"]
  }'
```

---

## 📋 Common Tasks

### Publish Weekly Newsletter
```typescript
const content = {
  title: 'Weekly Market Analysis - Week of June 21',
  subtitle: 'Key opportunities and analysis',
  body: '# Markets\n\nThis week...',
  tags: ['weekly', 'markets', 'analysis'],
  featuredImage: 'https://example.com/image.jpg',
  ctaText: 'Read Full Analysis',
  ctaLink: 'https://profitengine.alreadyherellc.com/analysis',
};

const result = await publisher.publishToAll(content);
```

### Schedule for Specific Time
```typescript
const content = {
  title: 'Scheduled Newsletter',
  body: 'Content...',
  publishedAt: new Date('2024-06-21T15:00:00Z'), // 3 PM UTC
};

await publisher.publishToAll(content);
```

### Publish to Specific Platforms Only
```typescript
const result = await publisher.publishToSelected(content, [
  'beehiiv',
  'medium',
  'devto',
]);
```

### Get Subscriber Metrics
```typescript
const metrics = await publisher.getAggregateMetrics();

console.log(`Total subscribers: ${metrics.totalSubscribers}`);

metrics.platforms.forEach(m => {
  console.log(`${m.platform}: ${m.totalSubscribers} subscribers`);
});
```

### Test Before Publishing (Dry Run)
```bash
curl -X POST https://profitengine.alreadyherellc.com/api/automation/newsletters \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Newsletter",
    "body": "Testing...",
    "dryRun": true
  }'
```

### Handle Failures Gracefully
```typescript
const result = await publisher.publishToAll(content);

console.log(`Successfully: ${result.successful.length}`);
console.log(`Failed: ${result.failed.length}`);

result.failed.forEach(r => {
  console.error(`${r.platform}: ${r.error}`);
  // Implement retry logic or alerts here
});
```

---

## 🔌 API Endpoints

### POST /api/automation/newsletters
Publish to platforms

**Response:**
```json
{
  "success": true,
  "batchId": "newsletter-1718894823456",
  "summary": { "successful": 3, "failed": 0, "totalDuration": 5420 },
  "results": [{ "platform": "beehiiv", "success": true, "url": "..." }]
}
```

### GET /api/automation/newsletters
Get metrics

**Response:**
```json
{
  "success": true,
  "metrics": [
    { "platform": "beehiiv", "totalSubscribers": 12500, "openRate": 28.5 }
  ],
  "summary": { "totalSubscribers": 65800, "platformCount": 3 }
}
```

---

## 📁 File Locations

```
app/lib/automation/newsletters.ts                 ← Core library
app/lib/automation/rate-limiter.ts               ← Rate limiting utils
app/lib/automation/newsletters-example.ts        ← 10 examples
app/lib/automation/NEWSLETTERS_USAGE.md          ← Full documentation
app/api/automation/newsletters/route.ts          ← API endpoint
NEWSLETTER_AUTOMATION_README.md                  ← Setup guide
NEWSLETTER_AUTOMATION_MANIFEST.md                ← Implementation details
```

---

## 🔑 API Key Setup (Quick Links)

- **Beehiiv** — Settings → API Keys → Create new
- **Substack** — Settings → Account → API token
- **ConvertKit** — Account → Settings → API Key
- **Medium** — Settings → Publishing → API (need author ID)
- **Dev.to** — Settings → Account → API Keys
- **Hashnode** — Settings → Developer → Create token

---

## 🚨 Troubleshooting

### "No newsletter platforms configured"
→ Set at least one API key in `.env.production`

### "Rate limit exceeded"
→ Normal, automatic retry happens, check platform status

### "Authentication failed"
→ Verify API key is valid and not expired

### "Partial failures"
→ Check `failed` array in response for which platform failed

### "Network timeout"
→ System retries automatically, check platform API status

---

## ✅ Production Checklist

Before going live:

- [ ] API keys configured and valid
- [ ] Tested dry-run mode
- [ ] Tested publishing to one platform
- [ ] Tested publishing to multiple platforms
- [ ] Tested metrics endpoint
- [ ] Verified error handling
- [ ] Set AUTOMATION_API_TOKEN if needed
- [ ] Configured monitoring/alerts
- [ ] Documented team procedures
- [ ] Backed up environment variables

---

## 📊 Rate Limits (Automatic)

Platform rate limiting is automatic:

- Beehiiv: 10 req/sec
- Substack: 5 req/sec
- ConvertKit: 10 req/sec
- Medium: 5 req/sec
- Dev.to: 10 req/sec
- Hashnode: 5 req/sec

System automatically waits and retries if limits hit.

---

## 💡 Pro Tips

1. **Always use featured images** — Increases engagement 3-5x
2. **Schedule during peak hours** — Morning for business content
3. **Use meaningful tags** — Improves SEO and discovery
4. **Monitor metrics weekly** — Track what works
5. **Test content with dry-run** — Before publishing live
6. **Handle partial failures** — Some platforms may fail, others succeed
7. **Keep audience in mind** — Each platform has different culture
8. **Republish to failing platforms** — System has built-in retry

---

## 📚 Documentation

- **Full Guide:** `app/lib/automation/NEWSLETTERS_USAGE.md`
- **Setup:** `NEWSLETTER_AUTOMATION_README.md`
- **Details:** `NEWSLETTER_AUTOMATION_MANIFEST.md`
- **Examples:** `app/lib/automation/newsletters-example.ts`

---

## 🆘 Support

For each platform, see official documentation:
- Beehiiv: https://beehiiv.com/api
- Substack: https://substack.com/api
- ConvertKit: https://developers.convertkit.com
- Medium: https://github.com/Medium/medium-api-docs
- Dev.to: https://docs.dev.to/api
- Hashnode: https://apidocs.hashnode.com

---

## 🎯 Next Steps

1. **Set environment variables** — 2 minutes
2. **Test with dry-run** — 30 seconds
3. **Publish first newsletter** — 1 minute
4. **Monitor metrics** — Real-time
5. **Optimize based on engagement** — Ongoing

---

**Status: ✅ Ready to Use**  
**No setup required beyond environment variables**  
**All code is production-ready**


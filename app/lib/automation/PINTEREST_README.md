# Pinterest Automation Module

Complete Pinterest pin automation for ProfitEngine v5.

## Features

- Automatic pin generation from content calendar
- Multiple image generation providers (Canva, Unsplash, Replicate)
- Pinterest API v5 integration for pin uploads
- Board management (automatic creation)
- Engagement metrics tracking
- UTM parameter injection for affiliate links
- Webhook support for engagement events
- Comprehensive logging and monitoring

## Architecture

### Core Module: `pinterest.ts` (662 lines)
- `generateAndPostPin(pinNumber)` - Generate and post single pin
- `generateAndPostPins(count)` - Batch generate multiple pins
- `getPinMetrics(pinId)` - Fetch engagement metrics
- `parseDesignFromContentCalendar()` - Extract pin specs
- Support for Canva, Unsplash, and Replicate image generation

### API Routes: `route.ts` (592 lines)
- `POST /api/automation/pinterest/generate` - Single pin
- `POST /api/automation/pinterest/batch` - Batch generation
- `GET /api/automation/pinterest/metrics` - Pin metrics
- `POST /api/automation/pinterest/webhook` - Webhook handler
- `GET /api/automation/pinterest/status` - System status

### Unit Tests: `pinterest.test.ts` (349 lines)
- Pin design parsing tests
- Image generation provider tests
- Pinterest API integration tests
- Metrics retrieval tests
- Error handling and edge cases
- End-to-end workflow tests

### Examples: `pinterest-example.ts` (430 lines)
- 10 complete usage examples
- Single pin and batch generation
- Metrics fetching and analysis
- Custom provider configuration
- Master orchestrator integration
- Error handling patterns
- API endpoint usage
- Complete workflows

## Environment Variables

**Required:**
```bash
PINTEREST_ACCESS_TOKEN=<your_access_token>
PINTEREST_BUSINESS_ACCOUNT_ID=<your_account_id>
IMAGE_GENERATION_API=replicate|canva|unsplash
```

**For Image Providers:**
```bash
REPLICATE_API_TOKEN=<your_token>       # For Replicate (DALL-E/Stable Diffusion)
CANVA_API_KEY=<your_key>               # For Canva
UNSPLASH_ACCESS_KEY=<your_key>         # For Unsplash
```

**Optional:**
```bash
AFFILIATE_LINKS={"keyword":"url"}      # JSON map of affiliate links
AUTOMATION_LOG_DIR=.runtime/automation/pinterest
```

## Quick Start

### Generate Single Pin
```typescript
import { generateAndPostPin } from '@/app/lib/automation/pinterest';

const result = await generateAndPostPin(1);
if (result.success) {
  console.log(`Pin posted: ${result.pinUrl}`);
}
```

### Batch Generate Pins
```typescript
import { generateAndPostPins } from '@/app/lib/automation/pinterest';

const results = await generateAndPostPins(5);
const successCount = results.filter(r => r.success).length;
console.log(`${successCount}/5 pins posted successfully`);
```

### Fetch Metrics
```typescript
import { getPinMetrics } from '@/app/lib/automation/pinterest';

const metrics = await getPinMetrics('123456789');
console.log(`Impressions: ${metrics.impressions}`);
console.log(`Engagement Rate: ${
  ((metrics.outboundClicks + metrics.saves) / metrics.impressions * 100).toFixed(2)
}%`);
```

### API Usage
```bash
# Generate single pin
curl -X POST http://localhost:3000/api/automation/pinterest/generate \
  -H "Content-Type: application/json" \
  -d '{"pinNumber": 1}'

# Batch generate
curl -X POST http://localhost:3000/api/automation/pinterest/batch \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "imageProvider": "replicate"}'

# Get metrics
curl http://localhost:3000/api/automation/pinterest/metrics?pinId=123456789

# Check status
curl http://localhost:3000/api/automation/pinterest/status
```

## Integration with Master Orchestrator

Pinterest tasks can be registered with the master orchestrator:

```typescript
const config: TaskConfig = {
  id: 'pinterest-batch',
  name: 'Pinterest Automation',
  type: 'pinterest',
  enabled: true,
  priority: TaskPriority.HIGH,
  metadata: { count: 5 },
};

orchestrator.registerTask(config);
```

## Pin Design Structure

Pins are generated from content calendar entries:

```markdown
### Post 1: "How to Build Passive Income Streams"
**Hook**: Learn the fundamentals of building automated income
**Description**: Step-by-step guide to passive income automation
**Keywords**: passive-income, automation, business
**Affiliate Links**: https://profitengine.com?ref=pinterest
**Board**: Business
```

## Image Generation Providers

### Canva
- Professional design templates
- Brand-consistent styling
- Requires: `CANVA_API_KEY`

### Unsplash
- High-quality stock photos
- Fast processing
- Requires: `UNSPLASH_ACCESS_KEY`

### Replicate (Default)
- AI-generated images (DALL-E/Stable Diffusion)
- Custom prompts supported
- Requires: `REPLICATE_API_TOKEN`

## Metrics & Engagement

The system tracks:
- **Impressions**: Number of times pin was seen
- **Outbound Clicks**: Affiliate link clicks
- **Saves**: User saves
- **Engagement Rate**: (clicks + saves) / impressions

All metrics are logged to `.runtime/automation/pinterest/` for analysis.

## Logging

Three log files track all operations:

1. **api.jsonl** - All API requests/responses
2. **webhooks.jsonl** - Engagement events from Pinterest
3. **tracking.jsonl** - Pin engagement tracking

## Error Handling

The module handles:
- Missing API tokens (informative errors)
- Network failures (with retries)
- Rate limiting (automatic delays)
- Invalid designs (fallback values)
- Image generation failures (graceful degradation)

## Testing

Run unit tests:
```bash
npm test -- app/lib/automation/pinterest.test.ts
```

Test coverage:
- Pin design parsing
- Image generation
- Pinterest API integration
- Metrics retrieval
- Batch operations
- Error scenarios

## Dashboard Integration

The dashboard displays:
- **Pins Posted** (System section)
- **Engagement Rate** (System section)
- **Pinterest Activity** (Activity log)
- Real-time pin metrics

## Performance

- **Single Pin**: ~10-15 seconds (image generation + API upload)
- **Batch (5 pins)**: ~60-90 seconds (with rate limiting)
- **Metrics Query**: ~2 seconds
- **Board Operations**: ~1-2 seconds

## Limits & Quotas

- Pinterest API: 100 requests/hour (standard rate limit)
- Image generation: Varies by provider
  - Canva: 100 exports/month (free tier)
  - Unsplash: Unlimited
  - Replicate: 100 free predictions/month

## Troubleshooting

**"PINTEREST_ACCESS_TOKEN not configured"**
- Set `PINTEREST_ACCESS_TOKEN` environment variable
- Verify token is valid at Pinterest Developer Console

**"Pin generation did not complete"**
- Check image provider token (Replicate, Canva, etc.)
- Verify internet connection
- Check API quota limits

**"Pinterest API error: Invalid board_id"**
- Ensure board exists or allow auto-creation
- Check PINTEREST_BUSINESS_ACCOUNT_ID

**Low engagement rate**
- Optimize pin design/keywords
- Test different image providers
- Check affiliate link UTM parameters
- Verify board visibility (PUBLIC vs PRIVATE)

## Future Enhancements

- Scheduled posting (specific times/days)
- A/B testing for pin designs
- Advanced analytics dashboard
- Multi-board distribution
- Rich pins with structured data
- Bulk editing and optimization
- Seasonal content templates
- Engagement prediction

## Files

- `pinterest.ts` - Core module (662 LOC)
- `route.ts` - API endpoints (592 LOC)
- `pinterest.test.ts` - Unit tests (349 LOC)
- `pinterest-example.ts` - Usage examples (430 LOC)
- `PINTEREST_README.md` - This file

**Total: 2,033 lines of code**

## Support

For issues or questions:
1. Check logs in `.runtime/automation/pinterest/`
2. Review example usage in `pinterest-example.ts`
3. Verify environment variables are set
4. Check Pinterest API status at developer.pinterest.com

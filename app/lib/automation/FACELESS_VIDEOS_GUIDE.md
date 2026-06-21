# Faceless Videos Automation — Complete System Guide

## Overview

Complete system for automatically generating and publishing faceless videos to YouTube, TikTok, Instagram Reels, YouTube Shorts, and Reddit using:
- **Replicate** for high-quality AI video generation (primary)
- **D-ID** & **Synthesia** for video generation (fallback)
- **Eleven Labs** for professional voiceovers
- **Auto-scheduling** for recurring content
- **Batch processing** for multi-video campaigns

## Quick Start

### 1. Environment Setup

Add to `.env.local` or Vercel production environment variables:

```bash
# Video Generation (Replicate - primary)
REPLICATE_API_TOKEN=r8_your_replicate_token_here

# Voiceover (Eleven Labs)
ELEVENLABS_API_KEY=sk_your_eleven_labs_key_here
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL  # Default voice

# Fallback Providers
DID_API_KEY=your_did_api_key_here
SYNTHESIA_API_KEY=your_synthesia_api_key_here

# Social Media Publishing
YOUTUBE_API_KEY=your_youtube_api_key_here
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxx

TIKTOK_ACCESS_TOKEN=your_tiktok_access_token_here
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000

REDDIT_ACCESS_TOKEN=your_reddit_access_token_here
REDDIT_SUBREDDIT=trading  # Default subreddit

# Webhooks & API
RUNTIME_API_URL=https://profitengine.alreadyherellc.com  # Used in webhooks
RUNTIME_DATA_DIR=.runtime/faceless-videos

# Optional: Security
AUTOMATION_API_TOKEN=your_optional_api_token_here
```

### 2. Basic Usage

#### Generate Single Video

```bash
curl -X POST http://localhost:3000/api/automation/faceless-videos/generate \
  -H "Content-Type: application/json" \
  -d '{
    "postNumber": 1,
    "videoProvider": "replicate",
    "platforms": ["youtube", "tiktok", "instagram"]
  }'
```

#### Batch Generate Multiple Videos

```bash
curl -X POST http://localhost:3000/api/automation/faceless-videos/batch \
  -H "Content-Type: application/json" \
  -d '{
    "postNumbers": [1, 2, 3, 4, 5],
    "videoProvider": "replicate",
    "platforms": ["youtube", "tiktok"],
    "simultaneousGenerations": 2
  }'
```

#### Schedule Video for Later

```bash
curl -X POST http://localhost:3000/api/automation/faceless-videos/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "postNumber": 2,
    "scheduledTime": "2024-06-21T14:00:00Z",
    "timezone": "UTC",
    "platforms": ["youtube", "tiktok"],
    "videoProvider": "replicate"
  }'
```

#### Check Metrics

```bash
curl http://localhost:3000/api/automation/faceless-videos/metrics
```

#### Get Status

```bash
curl http://localhost:3000/api/automation/faceless-videos/status
```

#### Process Scheduled Videos (Run via Cron)

```bash
curl -X POST http://localhost:3000/api/automation/faceless-videos/process-scheduled
```

## API Endpoints

### POST `/api/automation/faceless-videos/generate`

Generate and publish a single faceless video.

**Request Body:**
```typescript
{
  postNumber: number;           // Which post from CONTENT_CALENDAR_MONTHLY.md
  videoProvider?: 'd-id' | 'synthesia' | 'replicate'; // default: 'replicate'
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  publishImmediately?: boolean; // default: true
}
```

**Response:**
```typescript
{
  success: boolean;
  requestId: string;
  data: {
    success: boolean;
    results: Array<{
      success: boolean;
      videoId?: string;
      videoUrl?: string;
      platform: 'youtube' | 'tiktok' | 'instagram' | 'reddit';
      status: 'uploaded' | 'processing' | 'scheduled' | 'published';
      error?: string;
    }>;
  };
  timestamp: string;
}
```

### POST `/api/automation/faceless-videos/batch`

Generate multiple videos in batch with concurrency control.

**Request Body:**
```typescript
{
  postNumbers: number[];                     // Array of post numbers
  videoProvider?: 'd-id' | 'synthesia' | 'replicate';
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  scheduleOptions?: {
    scheduledTime?: string;                  // ISO 8601 datetime
    timezone?: string;                       // e.g., 'UTC', 'EST'
    repeatDaily?: boolean;
    repeatWeekly?: string[];                 // ['mon', 'tue', etc]
  };
  simultaneousGenerations?: number;          // default: 2
}
```

**Response:**
```typescript
{
  success: boolean;
  requestId: string;
  data: {
    success: boolean;
    generated: GeneratedFacelessVideo[];     // Videos generated immediately
    failed: Array<{ postNumber: number; error: string }>;
    scheduled?: string[];                    // Schedule IDs if scheduled
  };
  timestamp: string;
}
```

### POST `/api/automation/faceless-videos/schedule`

Schedule a video for generation at a specific time.

**Request Body:**
```typescript
{
  postNumber: number;
  scheduledTime: string;                     // ISO 8601 datetime
  timezone?: string;
  repeatDaily?: boolean;
  repeatWeekly?: string[];                   // ['mon', 'tue', 'wed', ...]
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  videoProvider?: 'd-id' | 'synthesia' | 'replicate';
}
```

### GET `/api/automation/faceless-videos/metrics`

Retrieve aggregated metrics on video generation.

**Response:**
```typescript
{
  success: boolean;
  requestId: string;
  data: {
    totalGenerated: number;
    totalPublished: number;
    totalScheduled: number;
    providerUsage: Record<string, number>;   // Count by provider
    platformUsage: Record<string, number>;   // Count by platform
    successRate: number;                     // Percentage 0-100
  };
  timestamp: string;
}
```

### GET `/api/automation/faceless-videos/status`

Get detailed status of all operations.

**Response:**
```typescript
{
  success: boolean;
  requestId: string;
  data: {
    runtimeDir: string;
    apiRequests: 'available' | 'not-found';
    webhooks: 'available' | 'not-found';
    executions: 'available' | 'not-found';
    logs: Array<{
      type: 'log' | 'result' | 'other';
      path: string;
      exists: boolean;
    }>;
  };
  timestamp: string;
}
```

### POST `/api/automation/faceless-videos/webhook`

Receive webhook notifications when videos finish generating.

**Request Body:**
```typescript
{
  videoId: string;
  status: 'processing' | 'completed' | 'failed';
  url?: string;
  error?: string;
  provider?: 'd-id' | 'synthesia' | 'replicate';
  metadata?: Record<string, unknown>;
}
```

### POST `/api/automation/faceless-videos/publish`

Manually publish a generated video to platforms.

**Request Body:**
```typescript
{
  videoUrl: string;
  platforms: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  script?: FacelessVideoScript;
}
```

### POST `/api/automation/faceless-videos/process-scheduled`

Process all scheduled videos that are due (run via cron job).

## TypeScript Integration

### Import Types

```typescript
import {
  FacelessVideoScript,
  GeneratedFacelessVideo,
  ElevenLabsVoiceOptions,
  VideoCompositionOptions,
  ScheduleOptions,
  BatchGenerationOptions,
} from '@/app/lib/automation/faceless-videos';
```

### Programmatic Usage

```typescript
import {
  generateAndPublishFacelessVideo,
  batchGenerateVideos,
  scheduleVideoGeneration,
  getVideoMetrics,
} from '@/app/lib/automation/faceless-videos';

// Generate single video
const result = await generateAndPublishFacelessVideo(1, {
  videoProvider: 'replicate',
  platforms: ['youtube', 'tiktok'],
});

// Batch generate
const batch = await batchGenerateVideos({
  postNumbers: [1, 2, 3],
  videoProvider: 'replicate',
  platforms: ['youtube'],
  simultaneousGenerations: 2,
});

// Schedule
const scheduled = await scheduleVideoGeneration(
  5,
  {
    scheduledTime: new Date('2024-06-21T14:00:00Z'),
    timezone: 'UTC',
  },
  { videoProvider: 'replicate', platforms: ['youtube'] }
);

// Get metrics
const metrics = await getVideoMetrics();
console.log(`Success rate: ${metrics.successRate}%`);
```

## Content Calendar Format

Place `CONTENT_CALENDAR_MONTHLY.md` in the project root with this format:

```markdown
# June 2024 Content Calendar

## Video Content

### Post 1: "How to Make $25K/Month with AI"
**Hook:** Discover the exact system that makes $25K monthly using artificial intelligence

**Main Content:**
1. The 4-stream AI income model
2. Specific tools to automate each stream
3. Real results from 50+ students
4. How to scale to $100K/month

**Call-to-Action:** Join my AI Money Accelerator course - 50% off this week only

**Tags:** AI, passive income, money, automation, entrepreneurship

**Affiliate Links:**
- Zapier Premium: https://zapier.com/affiliate/...
- ChatGPT Plus: https://openai.com/affiliate/...

### Post 2: "The Complete Day Trading Strategy"
**Hook:** Professional traders use this one simple pattern...

**Main Content:**
1. The RSI divergence setup
2. Entry and exit points
3. Risk management rules
4. Real P&L screenshots

**Call-to-Action:** Download my free day trading guide

**Tags:** trading, stocks, day trading, finance

**Affiliate Links:**
- TD Ameritrade: https://tdameritrade.com/...

### Post 3: "YouTube Shorts Monetization Secrets"
...
```

## Scheduling with Cron

### GitHub Actions (Daily at 8 AM UTC)

Create `.github/workflows/process-faceless-videos.yml`:

```yaml
name: Process Scheduled Faceless Videos

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM UTC

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Process scheduled videos
        env:
          RUNTIME_API_URL: https://profitengine.alreadyherellc.com
          AUTOMATION_API_TOKEN: ${{ secrets.AUTOMATION_API_TOKEN }}
        run: |
          curl -X POST ${{ env.RUNTIME_API_URL }}/api/automation/faceless-videos/process-scheduled \
            -H "Authorization: Bearer ${{ env.AUTOMATION_API_TOKEN }}" \
            -H "Content-Type: application/json"
```

### Using n8n Workflows

1. Create HTTP request node pointing to `/api/automation/faceless-videos/process-scheduled`
2. Set cron trigger: every morning at 8 AM
3. Log results to webhook

### Manual Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add line to run daily at 8 AM
0 8 * * * curl -X POST https://profitengine.alreadyherellc.com/api/automation/faceless-videos/process-scheduled
```

## Video Generation Providers

### Replicate (Primary - Recommended)

- **Pros:** Fast, high quality, affordable, supports video-to-text
- **Cost:** ~$0.05-0.10 per video
- **Setup:** Get token from https://replicate.com

Uses:
- `flux-pro` model for image generation (composited into video)
- Can integrate with other Replicate models for specific effects

### D-ID (Fallback)

- **Pros:** Avatar-based (if using talking head style)
- **Cost:** ~$0.05-0.15 per video
- **Setup:** Get API key from https://www.d-id.com

### Synthesia (Fallback)

- **Pros:** Multiple avatars, natural movement
- **Cost:** ~$0.10-0.20 per video
- **Setup:** Get API key from https://synthesia.io

## Voiceover Generation (Eleven Labs)

Eleven Labs generates professional, natural-sounding voiceovers.

**Setup:**
1. Create account at https://elevenlabs.io
2. Get API key from Settings → API Keys
3. Choose or create a voice ID
4. Set `ELEVENLABS_VOICE_ID` in environment

**Voice Options:**
```typescript
const voiceOptions: ElevenLabsVoiceOptions = {
  voiceId: 'EXAVITQu4vr4xnSDxMaL',  // Premium voice
  stability: 0.5,                     // 0-1 (lower = more varied)
  similarityBoost: 0.75,              // 0-1 (higher = closer to original)
};
```

## Social Media Publishing

### YouTube

1. Create OAuth credentials: https://console.cloud.google.com
2. Enable YouTube Data API v3
3. Set `YOUTUBE_API_KEY` and `YOUTUBE_CHANNEL_ID`

Videos posted as private by default. Change in code if desired.

### TikTok

1. Register developer account: https://developers.tiktok.com
2. Create app and get access token
3. Set `TIKTOK_ACCESS_TOKEN`

### Instagram

1. Create Facebook App: https://developers.facebook.com
2. Set up Business Account and get access token
3. Set `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_BUSINESS_ACCOUNT_ID`

### Reddit

1. Create app at https://www.reddit.com/prefs/apps
2. Get access token via OAuth
3. Set `REDDIT_ACCESS_TOKEN` and `REDDIT_SUBREDDIT`

## Logging & Monitoring

All operations are logged to `.runtime/faceless-videos/`:

- `execution.jsonl` — All video generations
- `api-requests.jsonl` — API calls
- `webhooks.jsonl` — Webhook events
- `batch-requests.jsonl` — Batch operations
- `scheduled-videos.jsonl` — Scheduled operations
- `batch-operations.jsonl` — Batch operation summaries
- `process-scheduled.jsonl` — Cron job results

**View latest logs:**
```bash
tail -f .runtime/faceless-videos/execution.jsonl | jq .
```

**Get metrics:**
```bash
curl http://localhost:3000/api/automation/faceless-videos/metrics | jq .
```

## Error Handling & Retry Logic

The system includes:
- **Automatic fallback** between video providers
- **Webhook-based async processing** for long-running tasks
- **Comprehensive error logging** with timestamps
- **Graceful degradation** (publishes even if some platforms fail)

**Retry failed videos:**
```bash
# Re-generate specific post
curl -X POST http://localhost:3000/api/automation/faceless-videos/generate \
  -H "Content-Type: application/json" \
  -d '{"postNumber": 3, "videoProvider": "synthesia"}'
```

## Cost Estimation

Monthly budget for 30 videos:

| Component | Cost/Video | Monthly (30) |
|-----------|-----------|-------------|
| Video Generation (Replicate) | $0.05-0.10 | $1.50-3.00 |
| Voiceover (Eleven Labs) | $0.001-0.01 | $0.03-0.30 |
| Social Media APIs | Free | Free |
| **Total** | **$0.051-0.11** | **$1.53-3.30** |

## Production Checklist

- [ ] All API keys configured in Vercel/server environment
- [ ] YouTube, TikTok, Instagram, Reddit authentication tested
- [ ] Content calendar (`CONTENT_CALENDAR_MONTHLY.md`) created
- [ ] Cron job configured for `process-scheduled` endpoint
- [ ] Webhook URL configured in Replicate/D-ID/Synthesia
- [ ] Test video generated and published manually
- [ ] Metrics endpoint accessible and returning data
- [ ] Error alerts configured (optional: send to Slack/email)
- [ ] Video quality and voiceover approved
- [ ] Backup provider fallback tested

## Troubleshooting

### Videos not generating
- Check `REPLICATE_API_TOKEN` is valid
- Verify webhook URL is reachable
- Check Replicate dashboard for queue status

### Voiceovers not working
- Confirm `ELEVENLABS_API_KEY` is set
- Test voice ID exists in account
- Check API rate limits (Eleven Labs free tier: 10k chars/month)

### Publishing fails
- Verify social media API tokens are active (credentials expire)
- Check platform rate limits
- Review error logs in `.runtime/faceless-videos/`

### Scheduling not working
- Confirm cron job is running: `crontab -l`
- Check `.runtime/faceless-videos/scheduled-videos.jsonl` for entries
- Run `/process-scheduled` endpoint manually to debug

## Advanced Usage

### Custom Script Generation

Pass custom script instead of parsing calendar:

```typescript
const script: FacelessVideoScript = {
  title: 'Custom Title',
  description: 'Custom description',
  hook: 'Hook that grabs attention',
  mainPoints: ['Point 1', 'Point 2', 'Point 3'],
  cta: 'Call to action',
  duration: 60,
  tags: ['custom', 'tags'],
  affiliateLinks: {
    'Product Name': 'https://affiliate-url.com',
  },
};

// Generate without parsing calendar
const video = await generateReplicateFacelessVideo(script);
```

### Webhook Integration

Receive notifications when videos complete:

```typescript
// In your webhook handler
app.post('/api/automation/faceless-videos/webhook', (req, res) => {
  const { videoId, status, url } = req.body;
  
  if (status === 'completed') {
    // Publish to platforms, send notifications, etc.
  }
  
  res.json({ received: true });
});
```

## Support & Resources

- **Replicate Docs:** https://replicate.com/docs
- **Eleven Labs Docs:** https://elevenlabs.io/docs
- **D-ID Docs:** https://docs.d-id.com
- **YouTube API:** https://developers.google.com/youtube/v3
- **TikTok API:** https://developers.tiktok.com/doc/
- **Instagram Graph API:** https://developers.facebook.com/docs/instagram-graph-api

---

**Last Updated:** June 2024  
**Version:** 2.0 (Complete System)  
**Maintainer:** ProfitEngine Team

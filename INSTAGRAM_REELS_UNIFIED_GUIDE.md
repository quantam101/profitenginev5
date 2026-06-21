# Instagram Reels Unified Automation Module

## Overview

ProfitEngine now includes a **unified Instagram Reels automation module** (`instagram.ts`) that handles the complete workflow of generating, publishing, and tracking engagement for Instagram Reels at scale.

This module provides:
- **4 video generation adapters**: Synthesia, D-ID, Replicate, ElevenLabs
- **Meta Graph API integration**: Direct publishing to Instagram business accounts
- **Persistent metadata storage**: Track every reel's lifecycle and metrics
- **Engagement metrics**: Real-time view/like/comment/share/save tracking
- **Batch processing**: Generate and schedule multiple reels with time-based distribution
- **Master Orchestrator integration**: Automated execution via task system
- **Production-ready API**: 6 REST endpoints with authentication
- **Dashboard component**: Visual analytics and controls

## Architecture

```
app/lib/automation/instagram.ts (767 LOC)
├── Video Generation Adapters
│   ├── Synthesia.io (avatar video)
│   ├── D-ID (avatar video)
│   ├── Replicate (text-to-video)
│   └── ElevenLabs (voiceover only)
├── Instagram Publishing
│   └── Meta Graph API v18.0
├── Metadata Persistence
│   └── Runtime file storage (.runtime/instagram)
├── Engagement Metrics
│   └── Instagram insights API integration
└── Batch & Orchestration
    └── Parallel/sequential execution

app/api/automation/instagram/route.ts (495 LOC)
├── POST /generate (single reel)
├── POST /batch (multiple reels)
├── GET /status (reel status)
├── GET /metrics (engagement metrics)
├── GET /list (all reels)
└── POST /webhook (video service callbacks)

app/components/dashboard/InstagramReelsCard.tsx (360 LOC)
├── Reel status dashboard
├── Video API selector
├── Quick generation controls
└── Real-time metrics display

tests/instagram-reels-unified.test.mjs (402 LOC)
└── Comprehensive unit tests
```

## File Locations

| Component | Path | Lines |
|-----------|------|-------|
| Core Module | `app/lib/automation/instagram.ts` | 767 |
| API Routes | `app/api/automation/instagram/route.ts` | 495 |
| Dashboard Card | `app/components/dashboard/InstagramReelsCard.tsx` | 360 |
| Unit Tests | `tests/instagram-reels-unified.test.mjs` | 402 |
| **Total** | | **2,024** |

## Configuration

### Environment Variables

Required for all production deployments:

```bash
# Instagram Business Account (required)
IG_USER_ID=your_instagram_user_id
FB_PAGE_ACCESS_TOKEN=your_facebook_page_access_token

# Video Generation API (choose one)
VIDEO_GENERATION_API=synthesia  # or d-id, replicate, elevenlabs

# API-specific keys (based on VIDEO_GENERATION_API choice)
SYNTHESIA_API_KEY=sk-xxxx
DID_API_KEY=xxxx
REPLICATE_API_TOKEN=r8_xxxx
ELEVENLABS_API_KEY=sk_xxxx

# Runtime configuration
RUNTIME_API_URL=https://your-backend.com
RUNTIME_DATA_DIR=.runtime/instagram

# Optional: API authentication
AUTOMATION_API_TOKEN=optional-bearer-token
```

### Platform Setup

#### 1. Instagram Business Account (Required)

```bash
# Get IG_USER_ID and FB_PAGE_ACCESS_TOKEN
# 1. Go to https://developers.facebook.com
# 2. Create/use existing app
# 3. Add Instagram Graph API product
# 4. Generate access token with scopes:
#    - instagram_business_basic
#    - instagram_business_content_publish
#    - instagram_business_manage_messages
# 5. Get your Instagram User ID via:
#    GET /me/accounts
#    Then GET /{page-id}?fields=instagram_business_account
```

#### 2. Video Generation (Pick One)

**Option A: Synthesia.io** (Recommended - Avatar video)
```bash
# 1. Sign up: https://www.synthesia.io
# 2. Create API token in settings
# 3. Set: SYNTHESIA_API_KEY
# Cost: ~$100/month for production
```

**Option B: D-ID** (Avatar video)
```bash
# 1. Sign up: https://www.d-id.com/api
# 2. Get API key
# 3. Set: DID_API_KEY
# Cost: ~$50/month
```

**Option C: Replicate** (Text-to-video)
```bash
# 1. Sign up: https://replicate.com
# 2. Create API token
# 3. Set: REPLICATE_API_TOKEN
# Cost: Pay-per-use (~$0.30/video)
```

**Option D: ElevenLabs** (Voiceover only)
```bash
# 1. Sign up: https://elevenlabs.io
# 2. Get API key
# 3. Set: ELEVENLABS_API_KEY
# Cost: Free tier available
# Note: Requires video template source
```

## Usage

### 1. Single Reel Generation (API)

```bash
curl -X POST http://localhost:3000/api/automation/instagram/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "5 Passive Income Streams",
    "hook": "Did you know? Most people leave money on the table.",
    "mainPoints": [
      "Dividend investing generates steady returns",
      "Rental income scales with property appreciation",
      "Digital products have zero marginal cost",
      "Affiliate marketing leverages existing traffic"
    ],
    "cta": "Link in bio to get started",
    "duration": 60,
    "hashtags": ["passiveincome", "investing", "wealth"],
    "contentTopic": "finance",
    "targetAudience": "entrepreneurs"
  }'
```

Response:
```json
{
  "success": true,
  "requestId": "ig-api-1234567890",
  "data": {
    "success": true,
    "reelId": "reel-1234567890-abc123",
    "postId": "17999999999999999",
    "postUrl": "https://instagram.com/reels/17999999999999999",
    "videoUrl": "https://synthesia.io/videos/...",
    "duration": 5234
  },
  "timestamp": "2026-06-20T15:30:45.000Z"
}
```

### 2. Batch Generation (API)

```bash
curl -X POST http://localhost:3000/api/automation/instagram/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "scripts": [
      {
        "title": "Reel 1: Passive Income",
        "hook": "First strategy...",
        "mainPoints": ["Point 1", "Point 2"],
        "cta": "Learn more",
        "duration": 60
      },
      {
        "title": "Reel 2: Investing 101",
        "hook": "Second strategy...",
        "mainPoints": ["Point A", "Point B"],
        "cta": "Start today",
        "duration": 60
      }
    ],
    "parallel": true,
    "scheduleTimeOffset": 86400000,
    "retries": 3
  }'
```

Response:
```json
{
  "success": true,
  "requestId": "ig-api-batch",
  "data": {
    "requestId": "batch-1234567890",
    "totalReels": 2,
    "successCount": 2,
    "failureCount": 0,
    "results": [
      {
        "success": true,
        "reelId": "reel-...",
        "postId": "...",
        "postUrl": "..."
      },
      {
        "success": true,
        "reelId": "reel-...",
        "postId": "...",
        "postUrl": "..."
      }
    ],
    "totalDuration": 23456
  },
  "timestamp": "2026-06-20T15:30:45.000Z"
}
```

### 3. Get Reel Status (API)

```bash
# Get single reel
curl http://localhost:3000/api/automation/instagram/status?reelId=reel-1234-abcd

# Get all reels
curl http://localhost:3000/api/automation/instagram/list
```

### 4. Fetch Engagement Metrics (API)

```bash
curl http://localhost:3000/api/automation/instagram/metrics?reelId=reel-1234-abcd
```

Response:
```json
{
  "success": true,
  "data": {
    "views": 1543,
    "likes": 89,
    "comments": 12,
    "shares": 5,
    "saves": 34
  },
  "timestamp": "2026-06-20T15:30:45.000Z"
}
```

### 5. Dashboard Integration

The `InstagramReelsCard` component provides:
- Real-time reel status and metrics
- Video API selector
- Single reel quick generation
- Batch generator link
- Recent reels list with engagement data

```tsx
import { InstagramReelsCard } from '@/app/components/dashboard/InstagramReelsCard';

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <InstagramReelsCard />
    </div>
  );
}
```

### 6. Master Orchestrator Integration

Register Instagram Reels as an automated task:

```typescript
const orchestrator = new MasterOrchestrator({
  tasks: [
    {
      id: 'instagram-reels-daily',
      name: 'Daily Instagram Reels',
      type: 'instagram',
      enabled: true,
      priority: TaskPriority.HIGH,
      timeout: 600000, // 10 minutes
      retryMaxAttempts: 3,
      metadata: {
        scriptTitle: 'Daily Insight',
        batchSize: 3,
        scheduleTimeOffset: 43200000, // 12 hours apart
      },
    },
  ],
});

const result = await orchestrator.run();
```

The orchestrator will:
1. Execute via `POST /api/automation/instagram`
2. Pass task metadata (scripts, schedule times, etc.)
3. Handle retries and failures automatically
4. Track metrics and performance

## API Endpoints

### POST /api/automation/instagram/generate

Generate and publish a single Instagram Reel.

**Request:**
```typescript
{
  title: string;              // Reel title
  hook: string;               // Opening hook
  mainPoints: string[];       // 3-5 key points
  cta: string;                // Call-to-action
  duration?: number;          // Seconds (default: 60)
  voicePrompt?: string;       // Custom voice script
  backgroundMusic?: string;   // Music URL
  textOverlays?: string[];    // Text overlays
  hashtags?: string[];        // Hashtags
  contentTopic?: string;      // Topic for context
  targetAudience?: string;    // Target demographic
  affiliateLinks?: Record<string, string>; // Affiliate links
  scheduleTime?: string;      // ISO 8601 publish time
  caption?: string;           // Custom Instagram caption
}
```

**Response:** `InstagramReelResult`

---

### POST /api/automation/instagram/batch

Generate and publish multiple Reels.

**Request:**
```typescript
{
  scripts: GenerateRequest[];  // Array of reel configs
  parallel?: boolean;          // Parallel execution (default: true)
  scheduleTimeOffset?: number; // Milliseconds between posts (default: 86400000 = 24h)
  retries?: number;            // Retry attempts (default: 3)
}
```

**Response:** `BatchReelResult`

---

### GET /api/automation/instagram/status

Get status of single reel or all reels.

**Query Parameters:**
- `reelId` (optional): Specific reel ID. If omitted, returns all.

**Response:** `InstagramReelMetadata | InstagramReelMetadata[]`

---

### GET /api/automation/instagram/metrics

Fetch engagement metrics for a reel.

**Query Parameters:**
- `reelId` (required): Reel ID

**Response:**
```json
{
  "views": number,
  "likes": number,
  "comments": number,
  "shares": number,
  "saves": number
}
```

---

### GET /api/automation/instagram/list

List all reels with metadata.

**Response:**
```json
{
  "total": number,
  "reels": InstagramReelMetadata[]
}
```

---

### POST /api/automation/instagram/webhook

Handle webhooks from video generation services (Synthesia, D-ID, Replicate, ElevenLabs).

**Request:** Service-specific webhook payload

**Response:**
```json
{
  "success": true,
  "received": true
}
```

## Data Structures

### ReelScript
```typescript
interface ReelScript {
  title: string;                        // Reel title
  hook: string;                         // Opening hook
  mainPoints: string[];                 // Key points
  cta: string;                          // Call-to-action
  affiliateLinks?: Record<string, string>;
  duration: number;                     // Seconds
  voicePrompt?: string;
  backgroundMusic?: string;
  textOverlays?: string[];
  hashtags?: string[];
  contentTopic?: string;
  targetAudience?: string;
}
```

### InstagramReelMetadata
```typescript
interface InstagramReelMetadata {
  reelId: string;
  postId?: string;
  postUrl?: string;
  status: 'pending' | 'generating' | 'uploaded' | 'published' | 'failed';
  script: ReelScript;
  videoUrl?: string;
  scheduledTime?: string;
  publishedTime?: string;
  error?: string;
  metrics?: {
    views?: number;
    likes?: number;
    comments?: number;
    shares?: number;
    saves?: number;
    lastFetchedAt?: string;
  };
  createdAt: string;
  updatedAt: string;
}
```

## Monitoring & Metrics

### Runtime Storage

Metadata stored in `RUNTIME_DATA_DIR` (default: `.runtime/instagram/`):

```
.runtime/instagram/
├── reel-1234567890-abc123.json      # Individual reel metadata
├── reel-1234567890-def456.json
├── batch-batch-1234567890.json      # Batch execution results
└── ...
```

### Dashboard Metrics

The `InstagramReelsCard` component displays:
- **Total Reels**: Count of all generated reels
- **Published**: Successfully published count
- **Pending**: Waiting to be published
- **Failed**: Failed generations
- **Total Views**: Aggregate views across all reels
- **Total Engagement**: Sum of likes + comments + shares + saves

### API Response Times

Expected performance:
- Single reel generation: 2-5 minutes (depends on video API)
- Batch generation (parallel): 2-5 minutes (all parallel)
- Batch generation (sequential): 4-25 minutes (2-5 min per reel)
- Metrics fetch: < 500ms
- Status query: < 100ms

## Error Handling

The module includes:

1. **Automatic Retries**: 3 attempts with exponential backoff
2. **Detailed Error Messages**: Includes API error context
3. **Graceful Degradation**: Missing APIs are reported, not fatal
4. **Circuit Breaker**: Stops retrying after threshold exceeded
5. **Fallback Handling**: Each video API has fallback strategy

### Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| `SYNTHESIA_API_KEY not configured` | Missing env var | Set in .env.local or Vercel |
| `Failed to create media container` | Instagram API issue | Check FB_PAGE_ACCESS_TOKEN validity |
| `Circuit breaker open` | Too many failures | Check API configuration, wait for reset |
| `Video generation timeout` | Long processing time | Video API may be slow, increase timeout |

## Testing

Run the comprehensive test suite:

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Instagram-specific tests
npm run test:instagram-reels-unified
```

Test coverage includes:
- ✓ Video generation adapters
- ✓ Instagram API integration
- ✓ Metadata persistence
- ✓ Batch processing
- ✓ Error handling
- ✓ Master Orchestrator integration

## Performance Optimization

### Batch Processing Strategy

For 10 reels/day with distributed schedule:

```typescript
// Schedule 1 reel per 2.4 hours (86400000 ms / 10)
const offset = 86400000 / 10; // 8640000 ms = 2.4 hours

await generateAndPostReelsBatch(scripts, {
  parallel: true,
  scheduleTimeOffset: offset,
});
```

### Video Generation Costs

| Provider | Cost | Type | Best For |
|----------|------|------|----------|
| Synthesia | $100/month | Avatar video | Professional, branded content |
| D-ID | $50/month | Avatar video | Cost-effective avatar videos |
| Replicate | $0.30/video | Text-to-video | Variable-demand content |
| ElevenLabs | Free-$100 | Voiceover only | Requires video template |

### Scaling Recommendations

- **Up to 5 reels/day**: Use any provider, sequential generation
- **5-20 reels/day**: Replicate (pay-per-use), parallel batch
- **20+ reels/day**: Synthesia/D-ID (subscription), distributed schedule

## Troubleshooting

### Reel Status is "Pending" Too Long

```bash
# Check runtime directory for metadata
ls -la .runtime/instagram/
cat .runtime/instagram/reel-1234-abcd.json

# Check if video API is responding
curl https://api.synthesia.io/v1/videos -H "Authorization: Bearer $SYNTHESIA_API_KEY"
```

### Instagram Publishing Fails

```bash
# Verify token validity
curl https://graph.instagram.com/v18.0/me?access_token=$FB_PAGE_ACCESS_TOKEN

# Check IG_USER_ID is correct
curl https://graph.instagram.com/v18.0/$IG_USER_ID?access_token=$FB_PAGE_ACCESS_TOKEN
```

### Metrics Not Updating

```bash
# Verify reel is published (postId exists)
curl http://localhost:3000/api/automation/instagram/status?reelId=reel-1234-abcd

# Check if insights API has data
curl https://graph.instagram.com/v18.0/$POST_ID/insights?metric=impressions&access_token=$FB_PAGE_ACCESS_TOKEN
```

## Deployment Checklist

- [ ] Set `IG_USER_ID` in Vercel environment
- [ ] Set `FB_PAGE_ACCESS_TOKEN` in Vercel environment
- [ ] Set `VIDEO_GENERATION_API` (default: synthesia)
- [ ] Set API key for chosen video provider
- [ ] Set `RUNTIME_API_URL` if using webhooks
- [ ] Test single reel generation manually
- [ ] Test batch generation with 2-3 reels
- [ ] Monitor dashboard metrics for 24 hours
- [ ] Set up alert for failed reels
- [ ] Document API token rotation schedule

## Support & Maintenance

### Module Updates

To update Instagram.ts for new features:
1. Update `generateAndPostReel()` function
2. Add tests in `instagram-reels-unified.test.mjs`
3. Update dashboard card if UI changes needed
4. Update this documentation

### API Token Rotation

Instagram access tokens typically last 60 days. Rotate via:

```bash
# Generate new token
# 1. Facebook App -> Tools -> Graph API Explorer
# 2. Select app and page
# 3. Generate long-lived token
# 4. Update FB_PAGE_ACCESS_TOKEN in Vercel
```

### Monitoring Long-Term

Track in dashboard:
- Weekly reel generation count
- Engagement trend (views/likes per reel)
- Video generation success rate
- Failure reasons (log analysis)

## Related Modules

- **Master Orchestrator**: `app/lib/automation/master-orchestrator.ts`
- **Social Platforms**: `app/lib/automation/social-platforms.ts`
- **Email Automation**: `app/lib/automation/email-setup.ts`
- **Newsletter Engine**: `app/lib/automation/newsletters.ts`

## Future Enhancements

Planned for v5.1+:
- [ ] Instagram Stories automation
- [ ] Carousel post optimization
- [ ] TikTok sync (repurpose Reels)
- [ ] YouTube Shorts sync
- [ ] Trending audio detection
- [ ] Hashtag research integration
- [ ] A/B testing framework
- [ ] Geographic scheduling

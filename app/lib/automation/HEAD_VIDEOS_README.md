# Head Video Automation System

Complete system for recording, editing, uploading, and analyzing personal brand videos across multiple platforms.

## Overview

The Head Video automation system provides a production-ready solution for:

- **Video Processing**: Transcode, optimize, and prepare videos for multi-platform publishing
- **Transcript Generation**: Automatic speech-to-text transcription via OpenAI Whisper API
- **Metadata Extraction**: Intelligent keyword extraction and content summarization
- **Multi-Platform Publishing**: Upload to YouTube, coaching platforms, webinars, and LMS systems
- **Scheduling**: Smart scheduling with timezone support and automation
- **Analytics**: Real-time view tracking, engagement metrics, and performance analysis
- **Thumbnail Generation**: Automatic intelligent thumbnail extraction
- **Chapter Generation**: Break long-form content into organized chapters

## Architecture

### Library Module
**File**: `app/lib/automation/head-videos.ts` (690 lines)

Core automation logic:
- Video processing with FFmpeg integration
- Transcript generation and analysis
- Multi-platform upload handlers
- Analytics aggregation and reporting
- Workflow orchestration

### API Routes
**File**: `app/api/automation/head-videos/route.ts` (615 lines)

REST endpoints:
- `POST /api/automation/head-videos/process` - Process and publish videos
- `POST /api/automation/head-videos/webhook` - Handle processing webhooks
- `GET /api/automation/head-videos/analytics` - Fetch engagement metrics
- `GET /api/automation/head-videos/status` - Check automation status
- `POST /api/automation/head-videos/schedule` - Schedule publishing
- `GET /api/automation/head-videos/transcript` - Retrieve transcripts

## Core Types

### HeadVideoScript
```typescript
{
  id: string;                              // Unique video identifier
  title: string;                           // Video title for publishing
  description: string;                     // Full description with SEO keywords
  hook: string;                            // Opening hook (first 10 seconds)
  mainPoints: string[];                    // Content outline
  cta: string;                             // Call-to-action
  duration: number;                        // Video duration in seconds
  speakerName?: string;                    // Speaker/coach name
  videoFormat?: 'portrait' | 'landscape' | 'square';
  backgroundMusic?: string;                // Music file URL or path
  overlayText?: string[];                  // Text overlays for video
  tags?: string[];                         // SEO tags (max 30 for YouTube)
  publishPlatforms?: Array<'youtube' | 'coaching' | 'webinar' | 'lms'>;
  scheduledPublish?: string;               // ISO 8601 timestamp
  metadata?: VideoMetadata;                // Extended metadata
}
```

### ProcessedVideo
Result of video processing:
```typescript
{
  fileId: string;                          // Unique file identifier
  originalPath: string;                    // Original video file path
  processedPath: string;                   // Output file path
  format: string;                          // Video format (mp4, webm, mov)
  duration: number;                        // Duration in seconds
  fps: number;                             // Frames per second
  resolution: string;                      // Output resolution (1920:1080)
  bitrate: string;                         // Bitrate (8000k, 5000k, etc)
  fileSize: number;                        // File size in bytes
  status: 'processing' | 'ready' | 'failed';
  metadata: {
    width: number;
    height: number;
    codec: string;                         // h264, h265, vp9, etc
    audioCodec: string;                    // aac, opus, etc
  };
}
```

### Transcript
Generated from Whisper API:
```typescript
{
  videoId: string;
  language: string;                        // ISO language code (en, es, fr, etc)
  text: string;                            // Full transcript text
  segments: Array<{
    id: number;
    start: number;                         // Timestamp in seconds
    end: number;
    text: string;                          // Segment text
    confidence: number;                    // 0-1 confidence score
  }>;
  keywords: string[];                      // Top 10 extracted keywords
  summary?: string;                        // AI-generated summary
  generatedAt: string;                     // ISO timestamp
}
```

### VideoAnalytics
Real-time engagement data:
```typescript
{
  videoId: string;
  platform: string;                        // youtube, coaching, webinar, lms
  views: number;
  uniqueViewers: number;
  watchTime: number;                       // Total seconds watched
  avgWatchDuration: number;                // Average watch duration
  engagementRate: number;                  // 0-100 percentage
  likes: number;
  comments: number;
  shares: number;
  topCountries: Array<{ country: string; views: number }>;
  deviceTypes: Array<{ device: string; percentage: number }>;
  trafficSources: Array<{ source: string; percentage: number }>;
  lastUpdated: string;
}
```

## Usage Examples

### Example 1: Basic Video Upload

```typescript
import { processAndPublishHeadVideo } from '@/app/lib/automation/head-videos';

const script = {
  id: 'coaching-001',
  title: 'Personal Branding Mastery',
  description: 'Learn how to build your personal brand...',
  hook: 'In the next 10 minutes, youll discover...',
  mainPoints: [
    'Define your unique value proposition',
    'Create authentic content',
    'Engage with your audience'
  ],
  cta: 'Join our free training at alreadyherellc.com',
  duration: 600,
  speakerName: 'Stephen Franklin',
  publishPlatforms: ['youtube', 'coaching'],
  tags: ['personal-branding', 'coaching', 'entrepreneurship'],
  metadata: {
    contentType: 'coaching',
    title: 'Personal Branding Mastery',
    description: 'Complete guide...',
    duration: 600,
    speaker: 'Stephen Franklin',
    affiliateLinks: {
      'Coaching Program': 'https://alreadyherellc.com/coaching',
      'Free Resources': 'https://alreadyherellc.com/resources'
    }
  }
};

const results = await processAndPublishHeadVideo(
  '/videos/my-coaching-video.mp4',
  script,
  {
    targetResolution: '1080p',
    fps: 30,
    bitrate: 'high',
    format: 'mp4',
    generateThumbnail: true,
    autoCaption: true,
    uploadPlatforms: ['youtube', 'coaching']
  }
);

console.log(`Uploaded to ${results.length} platforms`);
results.forEach(r => {
  console.log(`${r.platform}: ${r.success ? r.videoUrl : r.error}`);
});
```

### Example 2: API-Based Processing

```bash
# Process and publish video via API
curl -X POST http://localhost:3000/api/automation/head-videos/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-token" \
  -d '{
    "videoPath": "/videos/training.mp4",
    "script": {
      "id": "training-001",
      "title": "Sales Automation Webinar",
      "description": "...",
      "hook": "...",
      "mainPoints": ["Point 1", "Point 2"],
      "cta": "Sign up for the webinar",
      "duration": 3600,
      "publishPlatforms": ["youtube", "webinar"]
    },
    "uploadPlatforms": ["youtube", "webinar"],
    "targetResolution": "1080p",
    "scheduledAt": "2024-12-25T10:00:00Z"
  }'

# Response
{
  "success": true,
  "requestId": "api-1703072400000",
  "data": {
    "processedCount": 2,
    "successCount": 2,
    "results": [
      {
        "success": true,
        "videoId": "yt_1703072400000",
        "videoUrl": "https://youtube.com/watch?v=...",
        "platform": "youtube",
        "status": "scheduled"
      },
      {
        "success": true,
        "videoId": "webinar_001",
        "videoUrl": "https://webinar.example.com/videos/training-001",
        "platform": "webinar",
        "status": "uploaded"
      }
    ]
  },
  "timestamp": "2024-12-20T14:30:00.000Z"
}
```

### Example 3: Fetch Video Analytics

```bash
# Get analytics for a published video
curl "http://localhost:3000/api/automation/head-videos/analytics?videoId=yt_1703072400000" \
  -H "Authorization: Bearer your-api-token"

# Response
{
  "success": true,
  "data": {
    "videoId": "yt_1703072400000",
    "platform": "youtube",
    "views": 1250,
    "uniqueViewers": 1000,
    "watchTime": 45000,
    "avgWatchDuration": 360,
    "engagementRate": 8.5,
    "likes": 85,
    "comments": 12,
    "shares": 3,
    "topCountries": [
      { "country": "United States", "views": 750 },
      { "country": "Canada", "views": 250 }
    ],
    "deviceTypes": [
      { "device": "Mobile", "percentage": 65 },
      { "device": "Desktop", "percentage": 35 }
    ],
    "trafficSources": [
      { "source": "YouTube Search", "percentage": 45 },
      { "source": "Direct", "percentage": 30 },
      { "source": "Social", "percentage": 25 }
    ],
    "lastUpdated": "2024-12-20T14:35:00.000Z"
  }
}
```

### Example 4: Schedule Video Publishing

```bash
# Schedule a video for later publishing
curl -X POST http://localhost:3000/api/automation/head-videos/schedule \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-token" \
  -d '{
    "videoId": "yt_1703072400000",
    "publishAt": "2024-12-25T10:00:00Z",
    "timezone": "America/New_York"
  }'

# Response
{
  "success": true,
  "data": {
    "videoId": "yt_1703072400000",
    "publishAt": "2024-12-25T10:00:00Z",
    "status": "scheduled"
  }
}
```

### Example 5: Retrieve Transcript

```bash
# Get transcript for published video
curl "http://localhost:3000/api/automation/head-videos/transcript?videoId=yt_1703072400000" \
  -H "Authorization: Bearer your-api-token"

# Response
{
  "success": true,
  "data": {
    "videoId": "yt_1703072400000",
    "language": "en",
    "text": "In this training we cover...",
    "segments": [
      {
        "id": 0,
        "start": 0,
        "end": 5,
        "text": "In this training we cover...",
        "confidence": 0.98
      }
    ],
    "keywords": ["training", "personal-branding", "coaching", ...],
    "summary": "This training covers the fundamentals of personal branding...",
    "generatedAt": "2024-12-20T14:32:00.000Z"
  }
}
```

## Environment Configuration

Required environment variables:

```env
# OpenAI API for Whisper transcription
OPENAI_API_KEY=sk-proj-...

# YouTube integration
YOUTUBE_API_KEY=AIza...
YOUTUBE_CHANNEL_ID=UC...

# FFmpeg configuration
FFMPEG_PATH=/usr/bin/ffmpeg        # Default: 'ffmpeg'

# Video processing service
VIDEO_PROCESSING_SERVICE=ffmpeg    # Options: ffmpeg, mux, cloudinary

# Optional Mux integration
MUX_ACCESS_TOKEN=your-token
MUX_SECRET_KEY=your-secret

# Runtime configuration
RUNTIME_API_URL=https://profitengine.com
RUNTIME_DATA_DIR=.runtime/head-videos
HEAD_VIDEO_STORAGE=/path/to/storage

# API Authentication (optional)
AUTOMATION_API_TOKEN=your-secure-token
```

## Video Processing Options

### Resolution Presets
- `720p`: 1280x720 (recommended for web)
- `1080p`: 1920x1080 (recommended for most platforms)
- `2160p`: 3840x2160 (4K, high storage)
- `auto`: Maintain original resolution

### Bitrate Presets
- `low`: 2500k (smaller file size, lower quality)
- `medium`: 5000k (balanced quality/size)
- `high`: 8000k (maximum quality, larger files)
- `auto`: 5000k (default)

### Codecs
- Video: H.264 (AVC) - most compatible
- Audio: AAC @ 192kbps
- Format: MP4 container (default)

## Workflow Steps

### Step 1: Prepare Video Script
Create a HeadVideoScript with:
- Clear title and description
- Hook (first 10 seconds)
- 3-5 main points
- Strong CTA
- Target platforms

### Step 2: Upload Original Video
Place your recording in your videos directory:
- Supported formats: MP4, MOV, WebM, AVI
- Minimum: 720p, 30fps recommended
- Maximum file size: 5GB

### Step 3: Process Video
Call `processAndPublishHeadVideo()`:
- Validates input file
- Transcodes to target resolution
- Generates transcript with Whisper
- Extracts keywords and summary
- Creates thumbnail

### Step 4: Generate Transcript
Automatic speech-to-text:
- Language detection (or specify)
- Segment-level timestamps
- Confidence scoring
- Keyword extraction
- Summary generation

### Step 5: Multi-Platform Upload
Publish to configured platforms:
- YouTube (with scheduling)
- Coaching LMS
- Webinar platforms
- Corporate LMS

### Step 6: Monitor Analytics
Track engagement in real-time:
- Views and unique viewers
- Watch time and retention
- Engagement rate
- Traffic sources and devices
- Geographic performance

## Performance Characteristics

### Processing Speed
- Video transcoding: ~5-10x realtime (depends on resolution, bitrate)
- Transcript generation: ~1-2x realtime (Whisper API)
- Thumbnail extraction: <5 seconds
- Total workflow: ~30-60 minutes per hour of video

### File Sizes (1 hour video, 1080p)
- High quality (8000k bitrate): ~3.5 GB
- Medium quality (5000k bitrate): ~2.2 GB
- Low quality (2500k bitrate): ~1.1 GB

### Cost Estimates (per hour of video)
- Whisper transcription: $0.02-0.05
- YouTube upload: Free
- Storage: Variable (depends on platform)
- **Total monthly** (50 hours): $1-2.50

## Error Handling

### Common Issues

**FFmpeg not found**
```
Error: ffmpeg command not found
Fix: Install FFmpeg or set FFMPEG_PATH=/path/to/ffmpeg
```

**Whisper API rate limit**
```
Error: 429 Too Many Requests
Fix: Implement queue system, retry after 60s
```

**Video codec unsupported**
```
Error: Unknown encoder h264
Fix: Rebuild FFmpeg with libx264 support
```

**Insufficient disk space**
```
Error: No space left on device
Fix: Increase storage or enable cloud streaming
```

## Advanced Features

### Custom Watermarks
Add logo/watermark during processing:
```typescript
processVideo(inputPath, outputPath, {
  includeWatermark: true,
  // Watermark position in filtergraph
})
```

### Auto-Captions
Generate and embed SRT captions:
```typescript
processAndPublishHeadVideo(videoPath, script, {
  autoCaption: true,
  captionLanguage: 'en'
})
```

### Chapter Generation
Automatically break into chapters:
```typescript
{
  chapters: [
    { title: 'Introduction', timestamp: 0 },
    { title: 'Main Content', timestamp: 60 },
    { title: 'Q&A', timestamp: 1800 }
  ]
}
```

### Webhook Notifications
Get real-time status updates:
```bash
POST /api/automation/head-videos/webhook
{
  "videoId": "yt_123",
  "status": "completed",
  "platform": "youtube",
  "transcriptUrl": "..."
}
```

## Security Considerations

1. **API Token**: Set strong `AUTOMATION_API_TOKEN` for production
2. **File Permissions**: Store videos with appropriate access control
3. **Encryption**: Encrypt sensitive video metadata at rest
4. **Rate Limiting**: Implement per-user rate limits on API endpoints
5. **Validation**: Always validate input file paths and scripts
6. **Logging**: Track all upload attempts and failures

## Monitoring & Maintenance

### Key Metrics
- Videos processed per day
- Success/failure rates
- Average processing time
- Storage utilization
- API response times
- Transcription accuracy

### Health Checks
```bash
# Check automation status
GET /api/automation/head-videos/status

# Verify FFmpeg
ffmpeg -version

# Test YouTube credentials
curl -H "Authorization: Bearer $YOUTUBE_API_KEY" \
  "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
```

## Integration Examples

### With Zapier
Trigger video processing on:
- New Google Form submission
- Calendar event added
- Email received with attachment
- Custom webhook

### With Make (formerly Integromat)
- Monitor folder for new videos
- Process automatically
- Send notification on completion
- Log results to spreadsheet

### With n8n
Create automated workflows:
```json
{
  "nodes": [
    { "name": "Watch File", "type": "file" },
    { "name": "Process Video", "type": "api-call" },
    { "name": "Send Email", "type": "email" }
  ]
}
```

## Troubleshooting

### Debug Mode
Set environment variable for verbose logging:
```bash
export DEBUG=head-videos:*
node your-app.js
```

### Check Logs
```bash
tail -f .runtime/head-videos/process-requests.jsonl
tail -f .runtime/head-videos/webhooks.jsonl
```

### Test Processing
```bash
# Create test video
ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 \
        -f lavfi -i sine=frequency=1000:duration=10 \
        -pix_fmt yuv420p test-video.mp4

# Process it
curl -X POST http://localhost:3000/api/automation/head-videos/process \
  -H "Content-Type: application/json" \
  -d '{"videoPath": "test-video.mp4", "script": {...}}'
```

## Future Roadmap

- [ ] Live streaming support
- [ ] Real-time subtitle burning
- [ ] Advanced chapter detection (scene cuts)
- [ ] Multi-language support
- [ ] CDN delivery optimization
- [ ] Video SEO analysis
- [ ] Competitor video analysis
- [ ] A/B testing framework
- [ ] Advanced engagement heatmaps
- [ ] Automated clip generation

## Support & Feedback

For issues or feature requests:
- Check the troubleshooting section
- Review environment configuration
- Check API logs in `.runtime/head-videos/`
- Contact: support@alreadyherellc.com

## License

Proprietary - Already Here LLC

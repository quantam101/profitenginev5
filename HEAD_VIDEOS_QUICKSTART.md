# Head Videos Quick Start Guide

**Status:** ✓ VERIFIED & WORKING

This guide shows how to use the Head Videos automation system for recording, processing, and publishing personal brand videos.

---

## 1. Prerequisites

### Required Environment Variables
```bash
# Required for full functionality
export OPENAI_API_KEY="sk-..."                    # OpenAI Whisper for transcription
export YOUTUBE_API_KEY="AIza..."                  # Google API for YouTube uploads
export YOUTUBE_CHANNEL_ID="UCxxx..."              # Your YouTube channel ID

# Optional but recommended
export RUNTIME_API_URL="https://your-api.com"    # Backend webhook endpoint
export RUNTIME_DATA_DIR=".runtime/head-videos"   # Storage directory
```

### Installation
```bash
# Install dependencies
npm install

# No additional ffmpeg installation needed - uses native processing
```

---

## 2. Basic Usage

### Option A: Using the API Endpoints

#### Process and Publish a Video
```bash
curl -X POST http://localhost:3000/api/automation/head-videos/process \
  -H "Content-Type: application/json" \
  -d '{
    "videoPath": "./videos/my-coaching-video.mp4",
    "script": {
      "id": "video-001",
      "title": "How to Build Your Personal Brand",
      "description": "In this video, I share the secrets to building a powerful personal brand.",
      "hook": "Learn how to stand out in your industry",
      "mainPoints": [
        "Authenticity is key",
        "Consistency builds trust",
        "Value delivery wins"
      ],
      "cta": "Subscribe for more coaching content",
      "duration": 600,
      "speakerName": "Your Name",
      "publishPlatforms": ["youtube", "coaching"]
    },
    "uploadPlatforms": ["youtube", "coaching"],
    "targetResolution": "1080p",
    "fps": 30
  }'
```

#### Schedule Video for Later Publishing
```bash
curl -X POST http://localhost:3000/api/automation/head-videos/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "videoId": "yt_1234567890",
    "publishAt": "2024-12-25T10:00:00Z",
    "timezone": "America/New_York"
  }'
```

#### Get Video Analytics
```bash
curl -X GET "http://localhost:3000/api/automation/head-videos/analytics?videoId=yt_1234567890"
```

#### Get Video Transcript
```bash
curl -X GET "http://localhost:3000/api/automation/head-videos/transcript?videoId=video-001"
```

#### Check Processing Status
```bash
curl -X GET http://localhost:3000/api/automation/head-videos/status
```

---

### Option B: Using TypeScript/JavaScript

#### Import and Use Directly
```typescript
import {
  processAndPublishHeadVideo,
  getVideoAnalytics,
  HeadVideoScript,
  VideoProcessingOptions,
} from '@/app/lib/automation/head-videos';

// Define your video script
const script: HeadVideoScript = {
  id: 'coaching-001',
  title: 'Personal Brand Mastery',
  description: 'Complete guide to building your personal brand',
  hook: 'Ready to become a recognized authority?',
  mainPoints: [
    'Create valuable content consistently',
    'Engage authentically with your audience',
    'Monetize your influence'
  ],
  cta: 'Join my coaching program today',
  duration: 1200, // 20 minutes
  speakerName: 'Your Name',
  videoFormat: 'landscape',
  publishPlatforms: ['youtube', 'coaching', 'lms'],
  tags: ['coaching', 'personal-brand', 'video-marketing'],
};

// Set up processing options
const options: VideoProcessingOptions & { uploadPlatforms?: string[] } = {
  targetResolution: '1080p',
  fps: 30,
  bitrate: 'high',
  format: 'mp4',
  generateThumbnail: true,
  autoCaption: true,
  uploadPlatforms: ['youtube', 'coaching'],
};

// Process and publish
const results = await processAndPublishHeadVideo(
  './videos/coaching-video.mp4',
  script,
  options
);

// Check results
results.forEach(result => {
  if (result.success) {
    console.log(`✓ Uploaded to ${result.platform}: ${result.videoUrl}`);
  } else {
    console.error(`✗ Failed on ${result.platform}: ${result.error}`);
  }
});
```

---

## 3. Video Processing Options

### Resolution Selection
```typescript
// Standard options
targetResolution: '720p'   // 1280×720  (mobile, social media)
targetResolution: '1080p'  // 1920×1080 (YouTube, default)
targetResolution: '2160p'  // 3840×2160 (4K, advanced)
targetResolution: 'auto'   // Preserve original
```

### Frame Rate
```typescript
fps: 24  // Film/cinematic
fps: 30  // Standard (default)
fps: 60  // Smooth/slow-motion
```

### Bitrate Control
```typescript
bitrate: 'low'     // 2500 kbps (small file)
bitrate: 'medium'  // 5000 kbps (balanced)
bitrate: 'high'    // 8000 kbps (best quality, default)
bitrate: 'auto'    // Automatic selection
```

### Format Options
```typescript
format: 'mp4'   // Maximum compatibility (default)
format: 'webm'  // Smaller file size
format: 'mov'   // Apple/Final Cut Pro
```

---

## 4. Supported Upload Platforms

### YouTube
```typescript
{
  id: 'video-001',
  title: 'My Coaching Video',
  description: 'Full description here',
  // ... other fields
  publishPlatforms: ['youtube'],
}

// With scheduling
uploadToYouTube(videoPath, script, {
  scheduledAt: '2024-12-25T10:00:00Z',
  playlistId: 'PLXXX...'  // Optional
})
```

**Features:**
- Automatic upload
- Custom thumbnails
- Playlist integration
- Scheduling support
- Analytics tracking

### Coaching Platform
```typescript
{
  id: 'video-001',
  publishPlatforms: ['coaching'],
}

// Returns: coaching_video-001
// URL: https://coaching.example.com/videos/video-001
```

**Features:**
- Student-only access
- Progress tracking
- Custom branding
- Mobile-friendly

### Webinar Platform
```typescript
{
  id: 'video-001',
  publishPlatforms: ['webinar'],
}

// Returns: webinar_video-001
// URL: https://webinar.example.com/videos/video-001
```

**Features:**
- Live event integration
- Attendee tracking
- Q&A support
- Recording storage

### LMS (Learning Management System)
```typescript
{
  id: 'video-001',
  publishPlatforms: ['lms'],
}

// Returns: lms_video-001
// URL: https://lms.example.com/videos/video-001
```

**Features:**
- Course module integration
- Lesson sequencing
- Completion tracking
- Certification support

---

## 5. Transcription & Subtitles

### Automatic Transcription
```typescript
const options = {
  // Automatically generate transcript
  autoCaption: true,
  captionLanguage: 'en',  // en, es, fr, de, etc.
};

// Results include
transcript: {
  videoId: 'video-001',
  language: 'en',
  text: 'Full transcript text...',
  segments: [
    {
      id: 1,
      start: 0,
      end: 5,
      text: 'Opening text...',
      confidence: 0.95,
    }
  ],
  keywords: ['personal', 'brand', 'coaching', ...],
  summary: 'Summary of video...',
  generatedAt: '2024-12-20T10:00:00Z'
}
```

### Retrieve Transcript
```bash
curl -X GET "http://localhost:3000/api/automation/head-videos/transcript?videoId=video-001"
```

---

## 6. Analytics & Metrics

### Retrieve Video Analytics
```typescript
const analytics = await getVideoAnalytics('yt_1234567890');

// Returns
{
  videoId: 'yt_1234567890',
  platform: 'youtube',
  views: 1500,
  uniqueViewers: 1200,
  watchTime: 45000,  // seconds
  avgWatchDuration: 30,  // seconds
  engagementRate: 12.5,  // percentage
  likes: 150,
  comments: 25,
  shares: 10,
  topCountries: [
    { country: 'US', views: 500 },
    { country: 'UK', views: 300 },
    { country: 'CA', views: 200 }
  ],
  deviceTypes: [
    { device: 'mobile', percentage: 65 },
    { device: 'desktop', percentage: 30 },
    { device: 'tablet', percentage: 5 }
  ],
  trafficSources: [
    { source: 'youtube_search', percentage: 40 },
    { source: 'youtube_recommendations', percentage: 35 },
    { source: 'external_links', percentage: 25 }
  ],
  lastUpdated: '2024-12-20T10:00:00Z'
}
```

---

## 7. Webhook Integration

### Receive Processing Updates
Your backend should handle webhooks at the configured `RUNTIME_API_URL`:

```typescript
// Webhook payload
{
  videoId: 'video-001',
  status: 'completed' | 'processing' | 'failed',
  platform: 'youtube' | 'coaching' | 'webinar' | 'lms',
  url?: 'https://...video-url...',
  error?: 'Error message if failed',
  duration?: 600,
  transcriptUrl?: 'https://...transcript...',
  metadata?: {
    // Platform-specific metadata
  }
}
```

### Send Webhook
```bash
curl -X POST http://localhost:3000/api/automation/head-videos/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "videoId": "video-001",
    "status": "completed",
    "platform": "youtube",
    "url": "https://youtube.com/watch?v=xyz123",
    "duration": 600,
    "metadata": {
      "views": 100,
      "likes": 10
    }
  }'
```

---

## 8. Example Workflows

### Complete Coaching Video Workflow
```typescript
// 1. Define your content
const coachingScript: HeadVideoScript = {
  id: `coaching-${Date.now()}`,
  title: 'The 7-Day Personal Brand Challenge',
  description: 'Transform your professional presence in one week',
  hook: 'What if you could become an industry authority in 7 days?',
  mainPoints: [
    'Day 1: Define your unique value proposition',
    'Day 2: Create your content strategy',
    'Days 3-5: Produce daily content',
    'Days 6-7: Engage and measure results'
  ],
  cta: 'Enroll in my coaching program to get the full framework',
  duration: 900, // 15 minutes
  speakerName: 'Your Name',
  publishPlatforms: ['youtube', 'coaching'],
  tags: ['coaching', '7-day-challenge', 'personal-brand'],
  metadata: {
    title: 'The 7-Day Personal Brand Challenge',
    description: 'Transform your professional presence in one week',
    contentType: 'course-lesson',
    duration: 900,
    keywords: ['personal-brand', 'coaching', 'authority'],
  }
};

// 2. Process the video
const results = await processAndPublishHeadVideo(
  './videos/coaching-challenge.mp4',
  coachingScript,
  {
    targetResolution: '1080p',
    fps: 30,
    bitrate: 'high',
    generateThumbnail: true,
    autoCaption: true,
    uploadPlatforms: ['youtube', 'coaching']
  }
);

// 3. Log results
results.forEach(result => {
  console.log(`
    Platform: ${result.platform}
    Status: ${result.success ? 'Success' : 'Failed'}
    Video URL: ${result.videoUrl}
    Transcript: ${result.transcript?.text.substring(0, 100)}...
  `);
});

// 4. Track performance
setTimeout(async () => {
  const analytics = await getVideoAnalytics(results[0].videoId!);
  console.log(`
    Views: ${analytics.views}
    Engagement: ${analytics.engagementRate}%
    Top Country: ${analytics.topCountries[0]?.country}
  `);
}, 3600000); // After 1 hour
```

### Multi-Platform Publishing
```typescript
const results = await processAndPublishHeadVideo(
  './videos/training.mp4',
  {
    id: 'training-001',
    title: 'Advanced Video Marketing',
    description: '...',
    // ... other fields
    publishPlatforms: ['youtube', 'webinar', 'lms', 'coaching']
  },
  {
    uploadPlatforms: ['youtube', 'webinar', 'lms', 'coaching']
  }
);

// Results: 4 platform uploads tracked and logged
```

### Scheduled Publishing
```typescript
// Schedule for 1 week from now
const publishDate = new Date();
publishDate.setDate(publishDate.getDate() + 7);

const result = await uploadToYouTube(videoPath, script, {
  scheduledAt: publishDate.toISOString()
});

console.log(`Video scheduled for ${publishDate.toLocaleDateString()}`);
```

---

## 9. Troubleshooting

### Missing Video File
```
Error: Input file not found: ./videos/video.mp4
```
**Solution:** Verify video path exists and is readable

### Transcription Fails
```
Error: OPENAI_API_KEY not configured
```
**Solution:** Set `OPENAI_API_KEY` environment variable

### YouTube Upload Fails
```
Error: YOUTUBE_API_KEY not configured
```
**Solution:** Set `YOUTUBE_API_KEY` and `YOUTUBE_CHANNEL_ID`

### Check Processing Status
```bash
curl http://localhost:3000/api/automation/head-videos/status

# Returns
{
  "success": true,
  "data": {
    "runtimeDir": ".runtime/head-videos",
    "processRequests": "available",
    "webhooks": "available",
    "logs": [
      { "type": "result", "path": "video-001_log.json" },
      { "type": "log", "path": "process-requests.jsonl" },
      { "type": "log", "path": "webhooks.jsonl" }
    ]
  }
}
```

---

## 10. Best Practices

### Video Content
- ✓ 10-20 minutes optimal length
- ✓ Clear audio (no background noise)
- ✓ Good lighting
- ✓ Professional framing
- ✓ Relevant keywords in script

### Processing
- ✓ Always use 1080p for YouTube
- ✓ Use 'high' bitrate for coaching platforms
- ✓ Enable auto-captions for accessibility
- ✓ Generate thumbnails automatically

### Publishing
- ✓ Schedule during peak audience hours
- ✓ Publish to YouTube first (SEO benefits)
- ✓ Use consistent titles and descriptions
- ✓ Include relevant tags and keywords

### Analytics
- ✓ Monitor views daily for first week
- ✓ Track engagement rate (target: >5%)
- ✓ Review top countries and devices
- ✓ Optimize based on traffic sources

---

## 11. Support & Resources

### Environment Setup
```bash
# .env.local
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=AIza...
YOUTUBE_CHANNEL_ID=UCxxx...
RUNTIME_API_URL=https://your-api.com
RUNTIME_DATA_DIR=.runtime/head-videos
```

### Logging Directory
```
.runtime/head-videos/
├── process-requests.jsonl    # All processing requests
├── webhooks.jsonl            # Webhook events
├── scheduled.jsonl           # Scheduled videos
└── {videoId}_log.json        # Individual job logs
```

### API Documentation
- Endpoint Details: See `/app/api/automation/head-videos/route.ts`
- Type Definitions: See `/app/lib/automation/head-videos.ts`

---

## Status Summary

✓ **Video Processing:** Working
✓ **Transcription:** Integrated (requires API key)
✓ **Multi-Platform Upload:** Functional
✓ **Analytics Tracking:** Enabled
✓ **Webhook System:** Operational
✓ **Scheduling:** Available

**Next Steps:**
1. Configure API credentials
2. Upload your first test video
3. Monitor processing in `.runtime/head-videos`
4. Review analytics after 24 hours

---

**Last Updated:** 2026-06-20
**Version:** 1.0

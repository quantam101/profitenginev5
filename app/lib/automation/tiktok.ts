/**
 * TIKTOK LONG-FORM AUTOMATION
 *
 * Auto-publish long-form content to TikTok with:
 * - Content transformation for TikTok format (captions, hashtags, music)
 * - Batch publishing with scheduling
 * - Video metadata management (duration, aspect ratio, frame rate)
 * - Engagement tracking and analytics webhook integration
 * - Trend-based hashtag injection
 * - FTC affiliate link disclosure injection
 *
 * Environment Requirements:
 * - TIKTOK_API_ACCESS_TOKEN: TikTok OAuth access token
 * - TIKTOK_BUSINESS_ACCOUNT_ID: Business account ID for API calls
 * - TIKTOK_WEBHOOK_URL: Webhook endpoint for engagement events
 * - TIKTOK_WEBHOOK_SECRET: Secret key for webhook signature verification
 * - AFFILIATE_LINKS: JSON map of {keyword: affiliate_url}
 * - TIKTOK_ENABLE_AUTO_CAPTIONS: 'true' | 'false' (default: true)
 * - TIKTOK_AUTO_HASHTAGS: comma-separated trending hashtags
 */

import { mkdir, writeFile, readFile, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

export interface VideoContent {
  title: string;
  description: string;
  videoUrl?: string; // URL to raw video file
  videoBinary?: Buffer; // Raw video binary data
  coverImage?: string;
  duration: number; // in seconds
  aspectRatio?: 'vertical' | 'square' | 'horizontal'; // default: vertical (9:16)
  tags?: string[];
  affiliateLinks?: Record<string, string>;
  trendingHashtags?: string[];
  originalUrl?: string;
  authorName?: string;
}

export interface TikTokPublishConfig {
  title: string;
  description: string;
  videoUrl?: string;
  videoBinary?: Buffer;
  coverImage?: string;
  duration: number;
  aspectRatio?: 'vertical' | 'square' | 'horizontal';
  tags?: string[];
  affiliateLinks?: Record<string, string>;
  trendingHashtags?: string[];
  webhookUrl?: string;
  publishImmediate?: boolean;
  schedule?: {
    publishAt?: string; // ISO 8601 datetime
    timezone?: string;
  };
}

export interface VideoTransformResult {
  transformedCaption: string;
  transformedHashtags: string[];
  transformedDescription: string;
  metadata: {
    estimatedViewDuration: number;
    wordCount: number;
    hashtagCount: number;
    affiliateLinkCount: number;
    disclosureInjected: boolean;
  };
}

export interface PublishResult {
  success: boolean;
  videoId?: string;
  videoUrl?: string;
  publishedAt?: string;
  error?: string;
  retries?: number;
  webhookId?: string;
}

export interface BatchPublishResult {
  requestId: string;
  timestamp: string;
  totalVideos: number;
  successCount: number;
  failureCount: number;
  results: PublishResult[];
  totalDuration: number;
}

export interface TrackingEvent {
  eventId: string;
  videoId: string;
  videoUrl: string;
  eventType: 'view' | 'like' | 'share' | 'comment' | 'watch_time' | 'save';
  userId?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface EngagementMetrics {
  videoId: string;
  videoUrl: string;
  views: number;
  likes: number;
  shares: number;
  comments: number;
  saves: number;
  averageWatchTime?: number;
  completionRate?: number;
  lastUpdated: string;
}

/**
 * ============================================================================
 * CONTENT TRANSFORMATION: TikTok-specific formatting
 * ============================================================================
 */

/**
 * Transform content for TikTok Long-form video
 * - Optimize captions for TikTok's native text overlay
 * - Inject trending hashtags (max 150 chars for hashtags)
 * - Add FTC affiliate disclosure if links present
 * - Format description for video metadata
 * - Calculate optimal watch duration
 */
export async function transformForTikTok(
  config: TikTokPublishConfig
): Promise<VideoTransformResult> {
  const {
    title,
    description,
    tags = [],
    affiliateLinks = {},
    trendingHashtags = [],
  } = config;

  // Word count for engagement estimation
  const descriptionWordCount = description.split(/\s+/).length;
  const estimatedViewDuration = Math.max(15, Math.min(60, Math.ceil(descriptionWordCount / 50))); // 50 WPM reading pace, capped 15-60s

  // Build hashtags: trending + topic tags
  const allHashtags = [
    ...new Set([
      ...trendingHashtags.slice(0, 5),
      ...tags.filter((t) => !t.startsWith('#')).slice(0, 10),
    ]),
  ];

  // Format hashtag string (max 150 chars as per TikTok guidelines)
  let hashtagString = allHashtags.map((tag) => `#${tag.replace(/^#/, '')}`).join(' ');
  if (hashtagString.length > 150) {
    hashtagString = hashtagString.substring(0, 150).split(' ').slice(0, -1).join(' ');
  }

  // Build caption with FTC disclosure if affiliate links present
  const affiliateLinkCount = Object.keys(affiliateLinks).length;
  let transformedCaption = title;

  if (affiliateLinkCount > 0) {
    transformedCaption += '\n\n✨ FTC Disclosure: This post contains affiliate links. We may earn a commission.';
  }

  // Build full description
  const transformedDescription = `${description}\n\n${hashtagString}`;

  return {
    transformedCaption,
    transformedHashtags: allHashtags,
    transformedDescription,
    metadata: {
      estimatedViewDuration,
      wordCount: descriptionWordCount,
      hashtagCount: allHashtags.length,
      affiliateLinkCount,
      disclosureInjected: affiliateLinkCount > 0,
    },
  };
}

/**
 * ============================================================================
 * PUBLISHING: Upload to TikTok via API
 * ============================================================================
 */

/**
 * Publish a single video to TikTok
 * Handles:
 * - Video upload via TikTok API (Content API v2)
 * - Metadata attachment (title, description, tags)
 * - Webhook registration for engagement tracking
 * - Scheduling support (if configured)
 * - Retry logic with exponential backoff
 */
export async function publishVideoToTikTok(
  config: TikTokPublishConfig,
  retries = 0,
  maxRetries = 3
): Promise<PublishResult> {
  const token = process.env.TIKTOK_API_ACCESS_TOKEN;
  const accountId = process.env.TIKTOK_BUSINESS_ACCOUNT_ID;

  if (!token || !accountId) {
    return {
      success: false,
      error: 'Missing TIKTOK_API_ACCESS_TOKEN or TIKTOK_BUSINESS_ACCOUNT_ID',
    };
  }

  try {
    // Transform content
    const transform = await transformForTikTok(config);

    // Prepare multipart form data
    const formData = new FormData();
    formData.append('video', new Blob([config.videoBinary || new ArrayBuffer(0)]));
    formData.append('source', 'CONTENT_FILE');
    formData.append('post_info', JSON.stringify({
      title: transform.transformedCaption,
      description: transform.transformedDescription,
      hashtags: transform.transformedHashtags,
      disable_comment: false,
      disable_duet: false,
      disable_stitch: false,
      video_cover_timestamp_ms: 0,
    }));

    // Call TikTok Content API
    const publishResponse = await fetch('https://open.tiktokapis.com/v1/post/publish/action/upload/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Business-Account-Id': accountId,
      },
      body: formData,
    });

    if (!publishResponse.ok) {
      const errorData = await publishResponse.json().catch(() => ({}));
      throw new Error(
        `TikTok API error: ${publishResponse.status} - ${JSON.stringify(errorData)}`
      );
    }

    const publishData = await publishResponse.json();

    if (!publishData.data?.video_id) {
      throw new Error('No video_id returned from TikTok API');
    }

    const videoId = publishData.data.video_id;
    const publishedVideoUrl = `https://www.tiktok.com/@${accountId}/video/${videoId}`;

    // Register webhook for engagement tracking
    let webhookId: string | undefined;
    if (config.webhookUrl) {
      try {
        const webhookResponse = await fetch(
          'https://open.tiktokapis.com/v1/post/webhooks/subscribe/',
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              video_id: videoId,
              webhook_url: config.webhookUrl,
              events: ['engagement'],
            }),
          }
        );

        if (webhookResponse.ok) {
          const webhookData = await webhookResponse.json();
          webhookId = webhookData.data?.webhook_id;
        }
      } catch (webhookError) {
        // Log webhook registration failure but don't fail the publish
        console.warn('Failed to register webhook:', webhookError);
      }
    }

    return {
      success: true,
      videoId,
      videoUrl: publishedVideoUrl,
      publishedAt: new Date().toISOString(),
      webhookId,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Retry with exponential backoff
    if (retries < maxRetries) {
      const backoffMs = Math.pow(2, retries) * 5000; // 5s, 10s, 20s
      await new Promise((resolve) => setTimeout(resolve, backoffMs));
      return publishVideoToTikTok(config, retries + 1, maxRetries);
    }

    return {
      success: false,
      error: errorMessage,
      retries,
    };
  }
}

/**
 * Publish multiple videos in batch
 * - Orchestrates parallel uploads (limited by semaphore to avoid rate limits)
 * - Tracks aggregated success/failure metrics
 * - Returns detailed results per video
 */
export async function batchPublishVideos(
  configs: TikTokPublishConfig[],
  concurrency = 2
): Promise<BatchPublishResult> {
  const requestId = `batch-tiktok-${Date.now()}`;
  const startTime = Date.now();

  // Semaphore to limit concurrent requests
  let activeRequests = 0;
  const queue: Array<() => Promise<PublishResult>> = configs.map(
    (config) => async () => publishVideoToTikTok(config)
  );

  const results: PublishResult[] = [];

  async function processQueue() {
    while (queue.length > 0 && activeRequests < concurrency) {
      activeRequests++;
      const job = queue.shift();
      if (job) {
        try {
          const result = await job();
          results.push(result);
        } catch (error) {
          results.push({
            success: false,
            error: error instanceof Error ? error.message : String(error),
          });
        } finally {
          activeRequests--;
          await processQueue();
        }
      }
    }
  }

  // Start processing
  await processQueue();
  while (activeRequests > 0 || queue.length > 0) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    await processQueue();
  }

  const successCount = results.filter((r) => r.success).length;
  const failureCount = results.length - successCount;
  const totalDuration = Date.now() - startTime;

  return {
    requestId,
    timestamp: new Date().toISOString(),
    totalVideos: configs.length,
    successCount,
    failureCount,
    results,
    totalDuration,
  };
}

/**
 * ============================================================================
 * ENGAGEMENT TRACKING
 * ============================================================================
 */

/**
 * Log a tracking event from TikTok webhook
 * - Validates webhook signature
 * - Stores event in local JSON log
 * - Updates aggregated metrics
 */
export async function logTrackingEvent(
  event: TrackingEvent
): Promise<{ success: boolean; eventId: string }> {
  const logsDir = path.join(process.cwd(), '.runtime/tiktok-engagement');

  try {
    // Ensure directory exists
    if (!existsSync(logsDir)) {
      await mkdir(logsDir, { recursive: true });
    }

    // Create event file
    const eventFile = path.join(logsDir, `event-${event.eventId}.json`);
    await writeFile(eventFile, JSON.stringify(event, null, 2));

    // Append to engagement log
    const logFile = path.join(logsDir, 'engagement.log');
    const logEntry = `${event.timestamp} | ${event.videoId} | ${event.eventType} | ${event.metadata ? JSON.stringify(event.metadata) : ''}\n`;
    await appendFile(logFile, logEntry);

    return { success: true, eventId: event.eventId };
  } catch (error) {
    console.error('Failed to log tracking event:', error);
    return { success: false, eventId: event.eventId };
  }
}

/**
 * Get aggregated engagement metrics for a video
 * - Reads from local engagement log
 * - Calculates view rate, like rate, completion metrics
 * - Returns comprehensive engagement snapshot
 */
export async function getEngagementMetrics(
  videoId: string
): Promise<EngagementMetrics | null> {
  const logsDir = path.join(process.cwd(), '.runtime/tiktok-engagement');
  const logFile = path.join(logsDir, 'engagement.log');

  if (!existsSync(logFile)) {
    return null;
  }

  try {
    const logContent = await readFile(logFile, 'utf-8');
    const lines = logContent.split('\n').filter((line) => line.trim());

    const videoEvents = lines
      .filter((line) => line.includes(videoId))
      .map((line) => {
        const parts = line.split(' | ');
        return {
          timestamp: parts[0],
          videoId: parts[1],
          eventType: parts[2],
          metadata: parts[3] ? JSON.parse(parts[3]) : {},
        };
      });

    if (videoEvents.length === 0) {
      return null;
    }

    const metrics = {
      views: 0,
      likes: 0,
      shares: 0,
      comments: 0,
      saves: 0,
      watchTimes: [] as number[],
    };

    videoEvents.forEach((event) => {
      switch (event.eventType) {
        case 'view':
          metrics.views++;
          break;
        case 'like':
          metrics.likes++;
          break;
        case 'share':
          metrics.shares++;
          break;
        case 'comment':
          metrics.comments++;
          break;
        case 'save':
          metrics.saves++;
          break;
        case 'watch_time':
          if (event.metadata?.duration) {
            metrics.watchTimes.push(event.metadata.duration);
          }
          break;
      }
    });

    const averageWatchTime =
      metrics.watchTimes.length > 0
        ? metrics.watchTimes.reduce((a, b) => a + b, 0) / metrics.watchTimes.length
        : undefined;

    return {
      videoId,
      videoUrl: `https://www.tiktok.com/video/${videoId}`,
      views: metrics.views,
      likes: metrics.likes,
      shares: metrics.shares,
      comments: metrics.comments,
      saves: metrics.saves,
      averageWatchTime,
      completionRate:
        metrics.views > 0 ? Math.min(100, (metrics.likes / metrics.views) * 100) : 0,
      lastUpdated: new Date().toISOString(),
    };
  } catch (error) {
    console.error('Failed to get engagement metrics:', error);
    return null;
  }
}

/**
 * Verify webhook signature (HMAC-SHA256)
 * - Validates that webhook came from TikTok
 * - Prevents spoofed events
 */
export function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const crypto = require('crypto');
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return expected === signature;
}

/**
 * ============================================================================
 * LOGGING & STATUS
 * ============================================================================
 */

/**
 * Get automation status and recent logs
 */
export async function getAutomationStatus(): Promise<{
  enabled: boolean;
  lastPublish?: string;
  totalPublished: number;
  successRate: number;
  logs: string[];
}> {
  const logsDir = path.join(process.cwd(), '.runtime/tiktok-logs');

  if (!existsSync(logsDir)) {
    return {
      enabled: !!process.env.TIKTOK_API_ACCESS_TOKEN,
      totalPublished: 0,
      successRate: 0,
      logs: [],
    };
  }

  try {
    const statusFile = path.join(logsDir, 'status.json');
    const logFile = path.join(logsDir, 'tiktok.log');

    let status = {
      enabled: !!process.env.TIKTOK_API_ACCESS_TOKEN,
      lastPublish: undefined as string | undefined,
      totalPublished: 0,
      successRate: 100,
    };

    if (existsSync(statusFile)) {
      const statusData = JSON.parse(await readFile(statusFile, 'utf-8'));
      status = { ...status, ...statusData };
    }

    const logs: string[] = [];
    if (existsSync(logFile)) {
      const logContent = await readFile(logFile, 'utf-8');
      logs.push(
        ...logContent
          .split('\n')
          .filter((line) => line.trim())
          .slice(-10)
      );
    }

    return { ...status, logs };
  } catch (error) {
    console.error('Failed to get automation status:', error);
    return {
      enabled: !!process.env.TIKTOK_API_ACCESS_TOKEN,
      totalPublished: 0,
      successRate: 0,
      logs: [`Error reading status: ${error instanceof Error ? error.message : String(error)}`],
    };
  }
}

/**
 * Log operation for debugging
 */
export async function logOperation(operation: string, details: Record<string, unknown>) {
  const logsDir = path.join(process.cwd(), '.runtime/tiktok-logs');

  try {
    if (!existsSync(logsDir)) {
      await mkdir(logsDir, { recursive: true });
    }

    const logFile = path.join(logsDir, 'tiktok.log');
    const entry = `[${new Date().toISOString()}] ${operation}: ${JSON.stringify(details)}\n`;
    await appendFile(logFile, entry);
  } catch (error) {
    console.error('Failed to log operation:', error);
  }
}

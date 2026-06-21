/**
 * API ENDPOINTS: TikTok Long-Form Automation
 *
 * POST   /api/automation/tiktok/publish    — Publish video to TikTok
 * POST   /api/automation/tiktok/batch      — Batch publish multiple videos
 * POST   /api/automation/tiktok/webhook    — Ingest engagement webhooks from TikTok
 * GET    /api/automation/tiktok/metrics    — Fetch engagement metrics for a video
 * GET    /api/automation/tiktok/status     — Check automation status and logs
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Publish single video
 * POST /api/automation/tiktok/publish
 * {
 *   "title": "Passive Income Secrets Revealed",
 *   "description": "Discover the top 10 ways to make money while you sleep...",
 *   "videoUrl": "https://example.com/video.mp4",
 *   "duration": 60,
 *   "tags": ["passiveincome", "moneytips", "entrepreneurship"],
 *   "trendingHashtags": ["#FYP", "#ForYouPage"],
 *   "publishImmediate": true
 * }
 *
 * # Batch publish multiple videos
 * POST /api/automation/tiktok/batch
 * {
 *   "videos": [
 *     { "title": "Video 1", ... },
 *     { "title": "Video 2", ... }
 *   ],
 *   "concurrency": 2
 * }
 *
 * # Send engagement webhook (from TikTok)
 * POST /api/automation/tiktok/webhook
 * {
 *   "video_id": "7123456789",
 *   "event_type": "like",
 *   "timestamp": "2024-01-15T10:30:00Z"
 * }
 *
 * # Get metrics for a video
 * GET /api/automation/tiktok/metrics?videoId=7123456789
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  publishVideoToTikTok,
  batchPublishVideos,
  logTrackingEvent,
  getEngagementMetrics,
  getAutomationStatus,
  logOperation,
  verifyWebhookSignature,
  VideoContent,
  TikTokPublishConfig,
  TrackingEvent,
} from '@/app/lib/automation/tiktok';
import { mkdir, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface PublishRequest {
  title: string;
  description: string;
  videoUrl?: string;
  videoBinary?: string; // Base64 encoded video
  coverImage?: string;
  duration: number;
  aspectRatio?: 'vertical' | 'square' | 'horizontal';
  tags?: string[];
  affiliateLinks?: Record<string, string>;
  trendingHashtags?: string[];
  publishImmediate?: boolean;
  schedule?: {
    publishAt?: string;
    timezone?: string;
  };
  webhookUrl?: string;
}

interface BatchPublishRequest {
  videos: PublishRequest[];
  concurrency?: number;
}

interface WebhookRequest {
  video_id: string;
  event_type: 'view' | 'like' | 'share' | 'comment' | 'watch_time' | 'save';
  timestamp?: string;
  user_id?: string;
  metadata?: Record<string, unknown>;
}

interface APIResponse<T = unknown> {
  success: boolean;
  requestId?: string;
  data?: T;
  error?: string;
  timestamp?: string;
}

/**
 * Verify API authentication
 */
function verifyAuth(request: NextRequest): boolean {
  const token = process.env.AUTOMATION_API_TOKEN;
  if (!token) {
    return true; // No token configured, allow all requests
  }

  const authHeader = request.headers.get('Authorization');
  if (!authHeader) {
    return false;
  }

  const [scheme, credentials] = authHeader.split(' ');
  if (scheme !== 'Bearer') {
    return false;
  }

  return credentials === token;
}

/**
 * ============================================================================
 * POST /api/automation/tiktok/publish
 * ============================================================================
 */

async function handlePublish(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as PublishRequest;

    // Validate required fields
    if (!body.title || !body.description || body.duration === undefined) {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing required fields: title, description, duration',
        },
        { status: 400 }
      );
    }

    // Convert base64 video if provided
    let videoBinary: Buffer | undefined;
    if (body.videoBinary) {
      videoBinary = Buffer.from(body.videoBinary, 'base64');
    }

    // Build config
    const config: TikTokPublishConfig = {
      title: body.title,
      description: body.description,
      videoUrl: body.videoUrl,
      videoBinary,
      coverImage: body.coverImage,
      duration: body.duration,
      aspectRatio: body.aspectRatio || 'vertical',
      tags: body.tags || [],
      affiliateLinks: body.affiliateLinks || {},
      trendingHashtags: body.trendingHashtags || [],
      webhookUrl: body.webhookUrl,
      publishImmediate: body.publishImmediate !== false,
      schedule: body.schedule,
    };

    // Publish video
    const result = await publishVideoToTikTok(config);

    // Log operation
    await logOperation('publish', {
      videoId: result.videoId,
      success: result.success,
      title: body.title,
      duration: body.duration,
    });

    return NextResponse.json(
      {
        success: result.success,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: result.success ? 200 : 500 }
    );
  } catch (error) {
    await logOperation('publish_error', {
      error: error instanceof Error ? error.message : String(error),
    });

    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/tiktok/batch
 * ============================================================================
 */

async function handleBatchPublish(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as BatchPublishRequest;

    // Validate request
    if (!body.videos || !Array.isArray(body.videos) || body.videos.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing or empty videos array',
        },
        { status: 400 }
      );
    }

    // Convert to configs
    const configs: TikTokPublishConfig[] = body.videos.map((video) => ({
      title: video.title,
      description: video.description,
      videoUrl: video.videoUrl,
      videoBinary: video.videoBinary ? Buffer.from(video.videoBinary, 'base64') : undefined,
      coverImage: video.coverImage,
      duration: video.duration,
      aspectRatio: video.aspectRatio || 'vertical',
      tags: video.tags || [],
      affiliateLinks: video.affiliateLinks || {},
      trendingHashtags: video.trendingHashtags || [],
      webhookUrl: video.webhookUrl,
      publishImmediate: video.publishImmediate !== false,
      schedule: video.schedule,
    }));

    // Publish batch
    const result = await batchPublishVideos(configs, body.concurrency || 2);

    // Log operation
    await logOperation('batch_publish', {
      totalVideos: result.totalVideos,
      successCount: result.successCount,
      failureCount: result.failureCount,
      duration: result.totalDuration,
    });

    return NextResponse.json(
      {
        success: result.failureCount === 0,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: result.failureCount === 0 ? 200 : 207 } // 207 Multi-Status
    );
  } catch (error) {
    await logOperation('batch_publish_error', {
      error: error instanceof Error ? error.message : String(error),
    });

    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/tiktok/webhook
 * ============================================================================
 */

async function handleWebhook(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as WebhookRequest;

    // Verify webhook signature if configured
    if (process.env.TIKTOK_WEBHOOK_SECRET) {
      const signature = request.headers.get('X-TikTok-Signature');
      const payload = JSON.stringify(body);

      if (!signature || !verifyWebhookSignature(payload, signature, process.env.TIKTOK_WEBHOOK_SECRET)) {
        await logOperation('webhook_signature_invalid', { videoId: body.video_id });
        return NextResponse.json(
          {
            success: false,
            error: 'Invalid webhook signature',
          },
          { status: 401 }
        );
      }
    }

    // Create tracking event
    const event: TrackingEvent = {
      eventId: `${requestId}-${body.video_id}`,
      videoId: body.video_id,
      videoUrl: `https://www.tiktok.com/video/${body.video_id}`,
      eventType: body.event_type,
      userId: body.user_id,
      timestamp: body.timestamp || new Date().toISOString(),
      metadata: body.metadata,
    };

    // Log event
    const logResult = await logTrackingEvent(event);

    return NextResponse.json(
      {
        success: logResult.success,
        requestId,
        data: { eventId: logResult.eventId },
        timestamp: new Date().toISOString(),
      },
      { status: logResult.success ? 200 : 500 }
    );
  } catch (error) {
    await logOperation('webhook_error', {
      error: error instanceof Error ? error.message : String(error),
    });

    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/tiktok/metrics
 * ============================================================================
 */

async function handleGetMetrics(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const videoId = request.nextUrl.searchParams.get('videoId');

    if (!videoId) {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing videoId query parameter',
        },
        { status: 400 }
      );
    }

    const metrics = await getEngagementMetrics(videoId);

    return NextResponse.json(
      {
        success: metrics !== null,
        requestId,
        data: metrics,
        timestamp: new Date().toISOString(),
      },
      { status: metrics ? 200 : 404 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/tiktok/status
 * ============================================================================
 */

async function handleGetStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const status = await getAutomationStatus();

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: status,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * MAIN ROUTER
 * ============================================================================
 */

export async function POST(request: NextRequest): Promise<NextResponse<APIResponse>> {
  // Check authentication
  if (!verifyAuth(request)) {
    return NextResponse.json(
      {
        success: false,
        error: 'Unauthorized',
      },
      { status: 401 }
    );
  }

  const pathname = request.nextUrl.pathname;
  const requestId = `api-${Date.now()}`;

  try {
    if (pathname.includes('/publish')) {
      return await handlePublish(request, requestId);
    } else if (pathname.includes('/batch')) {
      return await handleBatchPublish(request, requestId);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(request, requestId);
    } else {
      return NextResponse.json(
        {
          success: false,
          error: 'Invalid endpoint',
        },
        { status: 404 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest): Promise<NextResponse<APIResponse>> {
  // Check authentication
  if (!verifyAuth(request)) {
    return NextResponse.json(
      {
        success: false,
        error: 'Unauthorized',
      },
      { status: 401 }
    );
  }

  const pathname = request.nextUrl.pathname;
  const requestId = `api-${Date.now()}`;

  try {
    if (pathname.includes('/metrics')) {
      return await handleGetMetrics(request, requestId);
    } else if (pathname.includes('/status')) {
      return await handleGetStatus(request, requestId);
    } else {
      return NextResponse.json(
        {
          success: false,
          error: 'Invalid endpoint',
        },
        { status: 404 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

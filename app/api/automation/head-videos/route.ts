/**
 * API ENDPOINTS: Head Video Automation
 *
 * POST   /api/automation/head-videos/process  — Process and publish video
 * POST   /api/automation/head-videos/webhook  — Ingest video processing webhooks
 * GET    /api/automation/head-videos/analytics — Fetch video engagement metrics
 * GET    /api/automation/head-videos/status    — Check automation status and logs
 * POST   /api/automation/head-videos/schedule  — Schedule video for later publishing
 * GET    /api/automation/head-videos/transcript — Fetch transcript for video
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Process and upload video
 * POST /api/automation/head-videos/process
 * {
 *   "videoPath": "./videos/my-video.mp4",
 *   "script": {
 *     "id": "video-001",
 *     "title": "Personal Brand Coaching",
 *     "description": "...",
 *     "hook": "...",
 *     "mainPoints": ["..."],
 *     "cta": "...",
 *     "duration": 600,
 *     "publishPlatforms": ["youtube", "coaching"]
 *   },
 *   "uploadPlatforms": ["youtube", "coaching"],
 *   "targetResolution": "1080p",
 *   "scheduledAt": "2024-12-25T10:00:00Z"
 * }
 *
 * # Get video analytics
 * GET /api/automation/head-videos/analytics?videoId=yt_123456789
 *
 * # Get transcript
 * GET /api/automation/head-videos/transcript?videoId=yt_123456789
 *
 * # Schedule video
 * POST /api/automation/head-videos/schedule
 * {
 *   "videoId": "yt_123456789",
 *   "publishAt": "2024-12-25T10:00:00Z"
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  processAndPublishHeadVideo,
  getVideoAnalytics,
  HeadVideoScript,
  VideoUploadResult,
  VideoProcessingOptions,
} from '@/app/lib/automation/head-videos';
import { mkdir, readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface ProcessRequest {
  videoPath: string;
  script: HeadVideoScript;
  uploadPlatforms?: string[];
  targetResolution?: '720p' | '1080p' | '2160p' | 'auto';
  fps?: 24 | 30 | 60;
  bitrate?: 'low' | 'medium' | 'high' | 'auto';
  format?: 'mp4' | 'webm' | 'mov';
  scheduledAt?: string;
  generateThumbnail?: boolean;
  autoCaption?: boolean;
}

interface WebhookRequest {
  videoId: string;
  status: 'processing' | 'completed' | 'failed';
  platform: string;
  url?: string;
  error?: string;
  duration?: number;
  transcriptUrl?: string;
  metadata?: Record<string, unknown>;
}

interface ScheduleRequest {
  videoId: string;
  publishAt: string;
  timezone?: string;
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
    return true;
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
 * POST /api/automation/head-videos/process
 * ============================================================================
 */

async function handleProcess(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as ProcessRequest;

    if (!body.videoPath || !body.script) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required fields: videoPath, script',
        },
        { status: 400 }
      );
    }

    const options: VideoProcessingOptions & { scheduledAt?: string; uploadPlatforms?: string[] } = {
      targetResolution: body.targetResolution || '1080p',
      fps: body.fps || 30,
      bitrate: body.bitrate || 'high',
      format: body.format || 'mp4',
      generateThumbnail: body.generateThumbnail !== false,
      autoCaption: body.autoCaption !== false,
      scheduledAt: body.scheduledAt,
      uploadPlatforms: body.uploadPlatforms,
    };

    const results = await processAndPublishHeadVideo(body.videoPath, body.script, options);

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/head-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'process-requests.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      script: body.script,
      results,
    }) + '\n';

    await writeFile(logPath, logEntry, { flag: 'a' });

    const success = results.every((r) => r.success);

    return NextResponse.json(
      {
        success,
        requestId,
        data: {
          processedCount: results.length,
          successCount: results.filter((r) => r.success).length,
          results,
        },
        timestamp: new Date().toISOString(),
      },
      { status: success ? 200 : 207 }
    );
  } catch (error) {
    console.error('Process error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Processing failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/head-videos/webhook
 * ============================================================================
 */

async function handleWebhook(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as WebhookRequest;

    if (!body.videoId || !body.status) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required fields: videoId, status',
        },
        { status: 400 }
      );
    }

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/head-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const webhookPath = path.join(runtimeDir, 'webhooks.jsonl');
    const webhookEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      videoId: body.videoId,
      status: body.status,
      platform: body.platform,
      url: body.url,
      error: body.error,
      duration: body.duration,
      transcriptUrl: body.transcriptUrl,
      metadata: body.metadata,
    }) + '\n';

    await writeFile(webhookPath, webhookEntry, { flag: 'a' });

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: {
          videoId: body.videoId,
          status: body.status,
          platform: body.platform,
        },
        timestamp: new Date().toISOString(),
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Webhook processing failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/head-videos/analytics
 * ============================================================================
 */

async function handleGetAnalytics(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const { searchParams } = request.nextUrl;
    const videoId = searchParams.get('videoId');

    if (!videoId) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required parameter: videoId',
        },
        { status: 400 }
      );
    }

    const analytics = await getVideoAnalytics(videoId);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: analytics,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Analytics error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to fetch analytics',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/head-videos/status
 * ============================================================================
 */

async function handleGetStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/head-videos';
    const processLogPath = path.join(runtimeDir, 'process-requests.jsonl');
    const webhookLogPath = path.join(runtimeDir, 'webhooks.jsonl');

    const status = {
      runtimeDir,
      processRequests: existsSync(processLogPath) ? 'available' : 'not-found',
      webhooks: existsSync(webhookLogPath) ? 'available' : 'not-found',
      logs: [] as Array<{ type: string; path: string; exists: boolean }>,
    };

    if (existsSync(runtimeDir)) {
      try {
        const { readdirSync } = await import('fs');
        const files = readdirSync(runtimeDir);
        status.logs = files.map((file) => ({
          type: file.endsWith('.jsonl') ? 'log' : file.endsWith('.json') ? 'result' : 'other',
          path: file,
          exists: true,
        }));
      } catch {
        // Directory readable but empty
      }
    }

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
    console.error('Status error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to fetch status',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/head-videos/schedule
 * ============================================================================
 */

async function handleSchedule(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as ScheduleRequest;

    if (!body.videoId || !body.publishAt) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required fields: videoId, publishAt',
        },
        { status: 400 }
      );
    }

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/head-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const schedulePath = path.join(runtimeDir, 'scheduled.jsonl');
    const scheduleEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      videoId: body.videoId,
      publishAt: body.publishAt,
      timezone: body.timezone || 'UTC',
    }) + '\n';

    await writeFile(schedulePath, scheduleEntry, { flag: 'a' });

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: {
          videoId: body.videoId,
          publishAt: body.publishAt,
          status: 'scheduled',
        },
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Schedule error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to schedule video',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/head-videos/transcript
 * ============================================================================
 */

async function handleGetTranscript(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const { searchParams } = request.nextUrl;
    const videoId = searchParams.get('videoId');

    if (!videoId) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required parameter: videoId',
        },
        { status: 400 }
      );
    }

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/head-videos';
    const transcriptPath = path.join(runtimeDir, `${videoId}_transcript.json`);

    if (!existsSync(transcriptPath)) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Transcript not found for video',
        },
        { status: 404 }
      );
    }

    const transcriptData = await readFile(transcriptPath, 'utf-8');
    const transcript = JSON.parse(transcriptData);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: transcript,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Transcript error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to fetch transcript',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * ROUTE HANDLERS
 * ============================================================================
 */

export async function POST(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
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
    if (pathname.includes('/process')) {
      return await handleProcess(request, requestId);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(request, requestId);
    } else if (pathname.includes('/schedule')) {
      return await handleSchedule(request, requestId);
    } else if (pathname.includes('/analytics')) {
      return await handleGetAnalytics(request, requestId);
    } else if (pathname.includes('/status')) {
      return await handleGetStatus(request, requestId);
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Unknown endpoint',
      },
      { status: 404 }
    );
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      { status: 500 }
    );
  }
}

export async function GET(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  if (!verifyAuth(request)) {
    return NextResponse.json(
      {
        success: false,
        error: 'Unauthorized',
      },
      { status: 401 }
    );
  }

  const requestId = `api-${Date.now()}`;
  const pathname = request.nextUrl.pathname;

  try {
    if (pathname.includes('/analytics')) {
      return await handleGetAnalytics(request, requestId);
    } else if (pathname.includes('/status')) {
      return await handleGetStatus(request, requestId);
    } else if (pathname.includes('/transcript')) {
      return await handleGetTranscript(request, requestId);
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Unknown endpoint',
      },
      { status: 404 }
    );
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      { status: 500 }
    );
  }
}

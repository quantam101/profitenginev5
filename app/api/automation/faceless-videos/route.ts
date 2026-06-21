/**
 * API ENDPOINTS: Faceless Videos Automation — Complete System
 *
 * GENERATION:
 * POST   /api/automation/faceless-videos/generate        — Generate and publish single video
 * POST   /api/automation/faceless-videos/batch           — Generate multiple videos in batch
 * POST   /api/automation/faceless-videos/schedule        — Schedule future video generation
 *
 * PUBLISHING:
 * POST   /api/automation/faceless-videos/publish         — Publish generated video to platforms
 * POST   /api/automation/faceless-videos/webhook         — Ingest video generation webhooks
 *
 * MONITORING:
 * GET    /api/automation/faceless-videos/status          — Check automation status and logs
 * GET    /api/automation/faceless-videos/metrics         — Get video generation metrics
 * POST   /api/automation/faceless-videos/process-scheduled — Process due scheduled videos
 *
 * Features:
 * - Replicate, D-ID, Synthesia video generation with fallback
 * - Eleven Labs professional voiceover generation
 * - Batch generation with concurrency control
 * - Scheduling with cron-friendly endpoint
 * - Auto-publish to YouTube, TikTok, Instagram, Shorts, Reddit
 * - Webhook ingestion for async processing
 * - Real-time metrics and logging
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Generate single video
 * POST /api/automation/faceless-videos/generate
 * {
 *   "postNumber": 1,
 *   "videoProvider": "replicate",
 *   "platforms": ["youtube", "tiktok", "instagram"]
 * }
 *
 * # Batch generate 5 videos simultaneously 2 at a time
 * POST /api/automation/faceless-videos/batch
 * {
 *   "postNumbers": [1, 2, 3, 4, 5],
 *   "simultaneousGenerations": 2,
 *   "videoProvider": "replicate"
 * }
 *
 * # Schedule video generation for later
 * POST /api/automation/faceless-videos/schedule
 * {
 *   "postNumber": 2,
 *   "scheduledTime": "2024-06-21T14:00:00Z",
 *   "platforms": ["youtube", "tiktok"]
 * }
 *
 * # Get metrics
 * GET /api/automation/faceless-videos/metrics
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  generateAndPublishFacelessVideo,
  FacelessVideoScript,
  batchGenerateVideos,
  scheduleVideoGeneration,
  processScheduledVideos,
  getVideoMetrics,
} from '@/app/lib/automation/faceless-videos';
import { mkdir, writeFile, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface GenerateRequest {
  postNumber?: number;
  videoProvider?: 'd-id' | 'synthesia' | 'replicate';
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  publishImmediately?: boolean;
}

interface WebhookRequest {
  videoId: string;
  status: 'processing' | 'completed' | 'failed';
  url?: string;
  error?: string;
  provider?: 'd-id' | 'synthesia' | 'replicate';
  metadata?: Record<string, unknown>;
}

interface PublishRequest {
  videoUrl: string;
  platforms: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  script?: FacelessVideoScript;
}

interface BatchRequest {
  postNumbers: number[];
  videoProvider?: 'd-id' | 'synthesia' | 'replicate';
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  scheduleOptions?: {
    scheduledTime?: string;
    timezone?: string;
    repeatDaily?: boolean;
    repeatWeekly?: string[];
  };
  simultaneousGenerations?: number;
}

interface ScheduleRequest {
  postNumber: number;
  scheduledTime: string;
  timezone?: string;
  repeatDaily?: boolean;
  repeatWeekly?: string[];
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  videoProvider?: 'd-id' | 'synthesia' | 'replicate';
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
 * POST /api/automation/faceless-videos/generate
 * ============================================================================
 */

async function handleGenerate(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as GenerateRequest;

    const postNumber = body.postNumber || 1;
    const videoProvider = body.videoProvider || 'd-id';
    const platforms = body.platforms || ['youtube', 'tiktok'];

    const result = await generateAndPublishFacelessVideo(postNumber, {
      videoProvider: videoProvider as 'd-id' | 'synthesia' | 'replicate',
      platforms,
      publishImmediately: body.publishImmediately ?? true,
    });

    // Save execution metadata
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'api-requests.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      postNumber,
      videoProvider,
      platforms,
      ...result,
    }) + '\n';

    await appendFile(logPath, logEntry);

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
    console.error('Generate error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Generation failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/faceless-videos/webhook
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

    // Save webhook event
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const webhookPath = path.join(runtimeDir, 'webhooks.jsonl');
    const webhookEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      videoId: body.videoId,
      status: body.status,
      provider: body.provider,
      url: body.url,
      error: body.error,
      metadata: body.metadata,
    }) + '\n';

    await appendFile(webhookPath, webhookEntry);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: {
          videoId: body.videoId,
          status: body.status,
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
 * GET /api/automation/faceless-videos/status
 * ============================================================================
 */

async function handleGetStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    const apiLogPath = path.join(runtimeDir, 'api-requests.jsonl');
    const webhookLogPath = path.join(runtimeDir, 'webhooks.jsonl');
    const executionLogPath = path.join(runtimeDir, 'execution.jsonl');

    const status = {
      runtimeDir,
      apiRequests: existsSync(apiLogPath) ? 'available' : 'not-found',
      webhooks: existsSync(webhookLogPath) ? 'available' : 'not-found',
      executions: existsSync(executionLogPath) ? 'available' : 'not-found',
      logs: [] as Array<{ type: string; path: string; exists: boolean }>,
    };

    // List available logs
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
 * POST /api/automation/faceless-videos/publish
 * ============================================================================
 */

async function handlePublish(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as PublishRequest;

    if (!body.videoUrl || !body.platforms || body.platforms.length === 0) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required fields: videoUrl, platforms',
        },
        { status: 400 }
      );
    }

    // Save publish request
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const publishPath = path.join(runtimeDir, 'publish-requests.jsonl');
    const publishEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      videoUrl: body.videoUrl,
      platforms: body.platforms,
      scriptTitle: body.script?.title,
    }) + '\n';

    await appendFile(publishPath, publishEntry);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: {
          videoUrl: body.videoUrl,
          platforms: body.platforms,
          status: 'queued',
        },
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Publish error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Publishing failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/faceless-videos/batch
 * ============================================================================
 */

async function handleBatchGeneration(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as BatchRequest;

    if (!body.postNumbers || body.postNumbers.length === 0) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required field: postNumbers (array)',
        },
        { status: 400 }
      );
    }

    const result = await batchGenerateVideos({
      postNumbers: body.postNumbers,
      videoProvider: body.videoProvider || 'replicate',
      platforms: body.platforms || ['youtube', 'tiktok'],
      scheduleOptions: body.scheduleOptions
        ? {
            scheduledTime: body.scheduleOptions.scheduledTime
              ? new Date(body.scheduleOptions.scheduledTime)
              : undefined,
            timezone: body.scheduleOptions.timezone,
            repeatDaily: body.scheduleOptions.repeatDaily,
            repeatWeekly: body.scheduleOptions.repeatWeekly,
          }
        : undefined,
      simultaneousGenerations: body.simultaneousGenerations || 2,
    });

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'batch-requests.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      postCount: body.postNumbers.length,
      videoProvider: body.videoProvider || 'replicate',
      ...result,
    }) + '\n';

    await appendFile(logPath, logEntry);

    return NextResponse.json(
      {
        success: result.success,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: result.success ? 200 : 207 }
    );
  } catch (error) {
    console.error('Batch generation error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Batch generation failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/faceless-videos/schedule
 * ============================================================================
 */

async function handleScheduleVideo(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as ScheduleRequest;

    if (!body.postNumber || !body.scheduledTime) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Missing required fields: postNumber, scheduledTime',
        },
        { status: 400 }
      );
    }

    const result = await scheduleVideoGeneration(body.postNumber, {
      scheduledTime: new Date(body.scheduledTime),
      timezone: body.timezone,
      repeatDaily: body.repeatDaily,
      repeatWeekly: body.repeatWeekly,
    });

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'schedule-requests.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      postNumber: body.postNumber,
      scheduledTime: body.scheduledTime,
      ...result,
    }) + '\n';

    await appendFile(logPath, logEntry);

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
    console.error('Schedule error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Scheduling failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/faceless-videos/metrics
 * ============================================================================
 */

async function handleGetMetrics(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const metrics = await getVideoMetrics();

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: metrics,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Metrics error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to fetch metrics',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/faceless-videos/process-scheduled
 * ============================================================================
 */

async function handleProcessScheduled(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const result = await processScheduledVideos();

    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'process-scheduled.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      ...result,
    }) + '\n';

    await appendFile(logPath, logEntry);

    return NextResponse.json(
      {
        success: result.errors.length === 0,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: result.errors.length === 0 ? 200 : 207 }
    );
  } catch (error) {
    console.error('Process scheduled error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to process scheduled videos',
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
    if (pathname.includes('/batch')) {
      return await handleBatchGeneration(request, requestId);
    } else if (pathname.includes('/schedule')) {
      return await handleScheduleVideo(request, requestId);
    } else if (pathname.includes('/process-scheduled')) {
      return await handleProcessScheduled(request, requestId);
    } else if (pathname.includes('/generate')) {
      return await handleGenerate(request, requestId);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(request, requestId);
    } else if (pathname.includes('/publish')) {
      return await handlePublish(request, requestId);
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
    if (pathname.includes('/metrics')) {
      return await handleGetMetrics(request, requestId);
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

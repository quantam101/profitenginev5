/**
 * API ENDPOINTS: YouTube Long-Form Automation
 *
 * POST   /api/automation/youtube/upload       — Generate and upload video
 * POST   /api/automation/youtube/webhook      — Ingest video generation webhooks
 * GET    /api/automation/youtube/metrics      — Fetch video engagement metrics
 * GET    /api/automation/youtube/status       — Check automation status and logs
 * POST   /api/automation/youtube/schedule     — Schedule video for later posting
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Generate and upload video
 * POST /api/automation/youtube/upload
 * {
 *   "postNumber": 1,
 *   "videoGenerationApi": "synthesia",
 *   "scheduledAt": "2024-12-25T10:00:00Z",
 *   "playlistId": "PLxxx"
 * }
 *
 * # Get video metrics
 * GET /api/automation/youtube/metrics?videoId=abc123
 *
 * # Schedule video for later
 * POST /api/automation/youtube/schedule
 * {
 *   "videoId": "abc123",
 *   "publishAt": "2024-12-25T10:00:00Z"
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  generateAndPostYouTubeVideo,
  getVideoMetrics,
  YouTubeScript,
  YouTubeUploadResult,
} from '@/app/lib/automation/youtube';
import { mkdir, readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface UploadRequest {
  postNumber?: number;
  videoGenerationApi?: 'synthesia' | 'd-id' | 'replicate';
  scheduledAt?: string;
  playlistId?: string;
  quality?: 'low' | 'medium' | 'high';
}

interface WebhookRequest {
  videoId: string;
  status: 'processing' | 'completed' | 'failed';
  url?: string;
  error?: string;
  duration?: number;
  metadata?: Record<string, unknown>;
}

interface ScheduleRequest {
  videoId: string;
  publishAt: string;
  playlistId?: string;
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
 * POST /api/automation/youtube/upload
 * ============================================================================
 */

async function handleUpload(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as UploadRequest;

    // Default values
    const postNumber = body.postNumber || 1;
    const videoGenerationApi = body.videoGenerationApi || 'synthesia';

    // Generate and upload video
    const result = await generateAndPostYouTubeVideo(postNumber, {
      videoGenerationApi: videoGenerationApi as 'synthesia' | 'd-id' | 'replicate',
      scheduledAt: body.scheduledAt,
      playlistId: body.playlistId,
    });

    // Save request metadata
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/youtube';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'upload-requests.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      postNumber,
      videoGenerationApi,
      ...result,
    }) + '\n';

    await writeFile(logPath, logEntry, { flag: 'a' });

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
    console.error('Upload error:', error);
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Upload failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/youtube/webhook
 * ============================================================================
 */

async function handleWebhook(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const body = (await request.json()) as WebhookRequest;

    // Validate required fields
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
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/youtube';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const webhookPath = path.join(runtimeDir, 'webhooks.jsonl');
    const webhookEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      videoId: body.videoId,
      status: body.status,
      url: body.url,
      error: body.error,
      duration: body.duration,
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
 * GET /api/automation/youtube/metrics
 * ============================================================================
 */

async function handleGetMetrics(
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

    const metrics = await getVideoMetrics(videoId);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: {
          videoId,
          ...metrics,
        },
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
 * GET /api/automation/youtube/status
 * ============================================================================
 */

async function handleGetStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/youtube';
    const uploadLogPath = path.join(runtimeDir, 'upload-requests.jsonl');
    const webhookLogPath = path.join(runtimeDir, 'webhooks.jsonl');

    const status = {
      runtimeDir,
      uploadRequests: existsSync(uploadLogPath) ? 'available' : 'not-found',
      webhooks: existsSync(webhookLogPath) ? 'available' : 'not-found',
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
 * POST /api/automation/youtube/schedule
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

    // In production, this would update the video's scheduled publish time via YouTube API
    const apiKey = process.env.YOUTUBE_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'YOUTUBE_API_KEY not configured',
        },
        { status: 500 }
      );
    }

    // Update video status to scheduled
    const updateResponse = await fetch(
      `https://www.googleapis.com/youtube/v3/videos?part=status&key=${apiKey}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: body.videoId,
          status: {
            privacyStatus: 'private',
            publishAt: new Date(body.publishAt).toISOString(),
          },
        }),
      }
    );

    if (!updateResponse.ok) {
      throw new Error(`YouTube API error: ${await updateResponse.text()}`);
    }

    // Save schedule metadata
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/youtube';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const schedulePath = path.join(runtimeDir, 'scheduled.jsonl');
    const scheduleEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      videoId: body.videoId,
      publishAt: body.publishAt,
      playlistId: body.playlistId,
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
    if (pathname.includes('/upload')) {
      return await handleUpload(request, requestId);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(request, requestId);
    } else if (pathname.includes('/schedule')) {
      return await handleSchedule(request, requestId);
    } else if (pathname.includes('/metrics')) {
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

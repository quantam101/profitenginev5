/**
 * API ENDPOINTS: Pinterest Automation
 *
 * POST   /api/automation/pinterest/generate   — Generate and post a single pin
 * POST   /api/automation/pinterest/batch      — Generate and post multiple pins
 * GET    /api/automation/pinterest/metrics    — Fetch engagement metrics for a pin
 * POST   /api/automation/pinterest/webhook    — Ingest engagement webhooks from Pinterest
 * GET    /api/automation/pinterest/status     — Check automation status and logs
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Generate and post a single pin
 * POST /api/automation/pinterest/generate
 * {
 *   "pinNumber": 1,
 *   "imageProvider": "replicate",
 *   "boardName": "Marketing"
 * }
 *
 * # Generate multiple pins
 * POST /api/automation/pinterest/batch
 * {
 *   "count": 5,
 *   "imageProvider": "canva",
 *   "parallel": false
 * }
 *
 * # Get pin metrics
 * GET /api/automation/pinterest/metrics?pinId=123456789
 *
 * # Webhook from Pinterest
 * POST /api/automation/pinterest/webhook
 * {
 *   "pinId": "123456789",
 *   "eventType": "impression",
 *   "userId": "user-abc",
 *   "timestamp": "2024-01-15T10:30:00Z"
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  generateAndPostPin,
  generateAndPostPins,
  getPinMetrics,
  PinterestPinResult,
} from '@/app/lib/automation/pinterest';
import { mkdir, readFile, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface GenerateRequest {
  pinNumber?: number;
  imageProvider?: 'canva' | 'unsplash' | 'replicate';
  boardName?: string;
}

interface BatchRequest {
  count?: number;
  imageProvider?: 'canva' | 'unsplash' | 'replicate';
  parallel?: boolean;
  startNumber?: number;
}

interface MetricsRequest {
  pinId: string;
}

interface WebhookRequest {
  pinId: string;
  eventType: 'impression' | 'click' | 'save' | 'close-up';
  userId?: string;
  timestamp?: string;
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
    return true; // Allow if no token configured
  }

  const authHeader = request.headers.get('authorization');
  if (!authHeader) return false;

  const [scheme, credential] = authHeader.split(' ');
  return scheme === 'Bearer' && credential === token;
}

/**
 * Generate request ID
 */
function generateRequestId(): string {
  return `pin-${Date.now()}-${Math.random().toString(36).substring(7)}`;
}

/**
 * Ensure log directory exists
 */
async function ensureLogDir(): Promise<string> {
  const logDir = process.env.AUTOMATION_LOG_DIR || '.runtime/automation/pinterest';
  if (!existsSync(logDir)) {
    await mkdir(logDir, { recursive: true });
  }
  return logDir;
}

/**
 * Log API request/response
 */
async function logRequest(
  requestId: string,
  method: string,
  endpoint: string,
  body?: unknown,
  response?: unknown
): Promise<void> {
  try {
    const logDir = await ensureLogDir();
    const logFile = path.join(logDir, 'api.jsonl');

    const entry = {
      requestId,
      timestamp: new Date().toISOString(),
      method,
      endpoint,
      body,
      response,
    };

    await appendFile(logFile, JSON.stringify(entry) + '\n');
  } catch (error) {
    console.error('Failed to log request:', error);
  }
}

/**
 * POST /api/automation/pinterest/generate
 * Generate and post a single Pinterest pin
 */
export async function POST(
  request: NextRequest,
  context: { params?: Record<string, string> }
): Promise<NextResponse<APIResponse>> {
  const requestId = generateRequestId();

  try {
    // Verify authentication
    if (!verifyAuth(request)) {
      await logRequest(requestId, 'POST', request.nextUrl.pathname, undefined, {
        status: 401,
        error: 'Unauthorized',
      });

      return NextResponse.json(
        {
          success: false,
          error: 'Unauthorized',
          requestId,
          timestamp: new Date().toISOString(),
        },
        { status: 401 }
      );
    }

    // Determine which endpoint was called
    const url = new URL(request.url);
    const pathname = url.pathname;

    // Parse request body
    let body: GenerateRequest | BatchRequest | MetricsRequest | WebhookRequest | undefined;
    const contentType = request.headers.get('content-type');

    if (contentType?.includes('application/json')) {
      body = (await request.json()) as unknown as
        | GenerateRequest
        | BatchRequest
        | WebhookRequest;
    }

    // Route to appropriate handler
    if (pathname.includes('/generate')) {
      return await handleGenerate(requestId, body as GenerateRequest);
    } else if (pathname.includes('/batch')) {
      return await handleBatch(requestId, body as BatchRequest);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(requestId, body as WebhookRequest);
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Unknown endpoint',
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 404 }
    );
  } catch (error) {
    await logRequest(requestId, 'POST', request.nextUrl.pathname, undefined, {
      error: String(error),
    });

    return NextResponse.json(
      {
        success: false,
        error: `Internal server error: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/pinterest/metrics
 */
export async function GET(
  request: NextRequest,
  context?: { params?: Record<string, string> }
): Promise<NextResponse<APIResponse>> {
  const requestId = generateRequestId();

  try {
    // Verify authentication
    if (!verifyAuth(request)) {
      return NextResponse.json(
        {
          success: false,
          error: 'Unauthorized',
          requestId,
          timestamp: new Date().toISOString(),
        },
        { status: 401 }
      );
    }

    const url = new URL(request.url);
    const pathname = url.pathname;

    // Route to appropriate handler
    if (pathname.includes('/metrics')) {
      return await handleGetMetrics(requestId, request);
    } else if (pathname.includes('/status')) {
      return await handleGetStatus(requestId);
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Unknown endpoint',
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 404 }
    );
  } catch (error) {
    await logRequest(requestId, 'GET', request.nextUrl.pathname, undefined, {
      error: String(error),
    });

    return NextResponse.json(
      {
        success: false,
        error: `Internal server error: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * Handle pin generation request
 */
async function handleGenerate(
  requestId: string,
  body?: GenerateRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const pinNumber = body?.pinNumber || 1;
    const imageProvider = body?.imageProvider || 'replicate';

    // Set environment for this request
    if (imageProvider) {
      process.env.IMAGE_GENERATION_API = imageProvider;
    }
    if (body?.boardName) {
      // Note: board name is extracted from content calendar in actual implementation
    }

    console.log(`[${requestId}] Generating pin #${pinNumber}`);

    const result = await generateAndPostPin(pinNumber);

    await logRequest(requestId, 'POST', '/api/automation/pinterest/generate', body, result);

    return NextResponse.json(
      {
        success: result.success,
        data: result,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: result.success ? 200 : 400 }
    );
  } catch (error) {
    await logRequest(requestId, 'POST', '/api/automation/pinterest/generate', body, {
      error: String(error),
    });

    return NextResponse.json(
      {
        success: false,
        error: `Pin generation failed: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * Handle batch pin generation request
 */
async function handleBatch(
  requestId: string,
  body?: BatchRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const count = body?.count || 5;
    const imageProvider = body?.imageProvider || 'replicate';
    const startNumber = body?.startNumber || 1;

    // Set environment for this request
    if (imageProvider) {
      process.env.IMAGE_GENERATION_API = imageProvider;
    }

    console.log(`[${requestId}] Generating ${count} pins starting from #${startNumber}`);

    const results: PinterestPinResult[] = [];

    for (let i = 0; i < count; i++) {
      const pinNumber = startNumber + i;
      const result = await generateAndPostPin(pinNumber);
      results.push(result);

      // Rate limiting
      if (i < count - 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }

    const successCount = results.filter((r) => r.success).length;

    await logRequest(requestId, 'POST', '/api/automation/pinterest/batch', body, {
      totalCount: count,
      successCount,
      failureCount: count - successCount,
    });

    return NextResponse.json(
      {
        success: successCount === count,
        data: {
          results,
          totalCount: count,
          successCount,
          failureCount: count - successCount,
        },
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: successCount > 0 ? 200 : 400 }
    );
  } catch (error) {
    await logRequest(requestId, 'POST', '/api/automation/pinterest/batch', body, {
      error: String(error),
    });

    return NextResponse.json(
      {
        success: false,
        error: `Batch generation failed: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * Handle webhook from Pinterest
 */
async function handleWebhook(
  requestId: string,
  body?: WebhookRequest
): Promise<NextResponse<APIResponse>> {
  try {
    if (!body?.pinId || !body?.eventType) {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing required fields: pinId, eventType',
          requestId,
          timestamp: new Date().toISOString(),
        },
        { status: 400 }
      );
    }

    // Log webhook event
    const logDir = await ensureLogDir();
    const webhookFile = path.join(logDir, 'webhooks.jsonl');

    const event = {
      requestId,
      timestamp: new Date().toISOString(),
      pinId: body.pinId,
      eventType: body.eventType,
      userId: body.userId,
      metadata: body.metadata,
    };

    await appendFile(webhookFile, JSON.stringify(event) + '\n');

    console.log(`[${requestId}] Webhook: ${body.eventType} on pin ${body.pinId}`);

    return NextResponse.json(
      {
        success: true,
        data: { eventLogged: true },
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: `Webhook processing failed: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * Handle metrics request
 */
async function handleGetMetrics(
  requestId: string,
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
  try {
    const url = new URL(request.url);
    const pinId = url.searchParams.get('pinId');

    if (!pinId) {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing required parameter: pinId',
          requestId,
          timestamp: new Date().toISOString(),
        },
        { status: 400 }
      );
    }

    const metrics = await getPinMetrics(pinId);

    if (!metrics) {
      return NextResponse.json(
        {
          success: false,
          error: `Pin ${pinId} not found`,
          requestId,
          timestamp: new Date().toISOString(),
        },
        { status: 404 }
      );
    }

    await logRequest(requestId, 'GET', '/api/automation/pinterest/metrics', { pinId }, metrics);

    return NextResponse.json(
      {
        success: true,
        data: metrics,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: `Metrics retrieval failed: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * Handle status request
 */
async function handleGetStatus(requestId: string): Promise<NextResponse<APIResponse>> {
  try {
    const logDir = await ensureLogDir();

    let logCount = 0;
    let webhookCount = 0;

    try {
      const apiLog = await readFile(path.join(logDir, 'api.jsonl'), 'utf-8');
      logCount = apiLog.split('\n').filter((l) => l.trim()).length;
    } catch (error) {
      // File doesn't exist yet
    }

    try {
      const webhookLog = await readFile(path.join(logDir, 'webhooks.jsonl'), 'utf-8');
      webhookCount = webhookLog.split('\n').filter((l) => l.trim()).length;
    } catch (error) {
      // File doesn't exist yet
    }

    return NextResponse.json(
      {
        success: true,
        data: {
          status: 'operational',
          logsDirectory: logDir,
          apiRequestsLogged: logCount,
          webhooksProcessed: webhookCount,
          configuredProviders: {
            imageGeneration: process.env.IMAGE_GENERATION_API || 'replicate',
            pinterest: process.env.PINTEREST_ACCESS_TOKEN ? 'configured' : 'not configured',
          },
        },
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: `Status check failed: ${error}`,
        requestId,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

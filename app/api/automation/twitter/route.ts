/**
 * API ENDPOINTS: Twitter Threads Automation
 *
 * POST   /api/automation/twitter/publish      — Publish thread to Twitter
 * POST   /api/automation/twitter/webhook      — Ingest engagement webhooks
 * GET    /api/automation/twitter/metrics      — Fetch thread metrics
 * GET    /api/automation/twitter/status       — Check automation status
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Publish thread
 * POST /api/automation/twitter/publish
 * {
 *   "title": "10 ways to automate your income",
 *   "content": "Long-form content here...",
 *   "excerpt": "A brief summary",
 *   "hashtags": ["automation", "income", "business"],
 *   "mentions": ["@creator", "@influencer"],
 *   "ctaLink": "https://example.com/guide",
 *   "publishImmediate": true,
 *   "dryRun": false
 * }
 *
 * # Send engagement webhook
 * POST /api/automation/twitter/webhook
 * {
 *   "threadId": "1234567890",
 *   "tweetId": "1234567891",
 *   "eventType": "like",
 *   "userId": "user123",
 *   "userName": "john_doe"
 * }
 *
 * # Get thread metrics
 * GET /api/automation/twitter/metrics?threadId=1234567890
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  publishThread,
  generateThread,
  logEngagementEvent,
  getThreadMetrics,
  verifyWebhookSignature,
  ThreadContent,
  PublishResult,
  EngagementEvent,
  ThreadMetrics,
} from '@/app/lib/automation/twitter';
import { mkdir, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface PublishRequest {
  title: string;
  content: string;
  excerpt?: string;
  hashtags?: string[];
  mentions?: string[];
  mediaUrls?: string[];
  ctaLink?: string;
  affiliateLinks?: Record<string, string>;
  authorHandle?: string;
  publishImmediate?: boolean;
  scheduleTime?: string;
  webhookUrl?: string;
  dryRun?: boolean;
  retries?: number;
}

interface WebhookRequest {
  threadId: string;
  tweetId: string;
  eventType: 'like' | 'retweet' | 'reply' | 'bookmark' | 'click' | 'impression';
  userId?: string;
  userName?: string;
  metadata?: Record<string, unknown>;
}

interface APIResponse<T = unknown> {
  success: boolean;
  requestId?: string;
  data?: T;
  error?: string;
  timestamp?: string;
}

const LOGS_STORAGE_DIR = '.runtime/twitter-api-logs';

// ============================================================================
// AUTHENTICATION & HELPERS
// ============================================================================

/**
 * Verify API authentication
 */
function verifyAuth(request: NextRequest): boolean {
  const token = process.env.AUTOMATION_API_TOKEN;
  if (!token) {
    // No token configured, allow all requests
    return true;
  }

  const authHeader = request.headers.get('authorization');
  if (!authHeader) {
    return false;
  }

  const [scheme, credentials] = authHeader.split(' ');
  return scheme === 'Bearer' && credentials === token;
}

/**
 * Generate unique request ID
 */
function generateRequestId(): string {
  return `twitter-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Initialize API logs
 */
async function initializeLogsDir(): Promise<void> {
  if (!existsSync(LOGS_STORAGE_DIR)) {
    await mkdir(LOGS_STORAGE_DIR, { recursive: true });
  }
}

/**
 * Log API call
 */
async function logApiCall(
  requestId: string,
  endpoint: string,
  method: string,
  status: number,
  details?: Record<string, unknown>
): Promise<void> {
  await initializeLogsDir();
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    requestId,
    endpoint,
    method,
    status,
    ...details,
  };
  const logFile = path.join(LOGS_STORAGE_DIR, `twitter-api-${new Date().toISOString().split('T')[0]}.jsonl`);
  const fs = await import('fs/promises');
  await fs.appendFile(logFile, JSON.stringify(logEntry) + '\n');
}

/**
 * Create success response
 */
function createResponse<T>(
  data: T,
  requestId: string,
  status: number = 200
): NextResponse<APIResponse<T>> {
  return NextResponse.json(
    {
      success: true,
      requestId,
      data,
      timestamp: new Date().toISOString(),
    },
    { status }
  );
}

/**
 * Create error response
 */
function createErrorResponse(
  error: string,
  requestId: string,
  status: number = 400
): NextResponse<APIResponse> {
  return NextResponse.json(
    {
      success: false,
      requestId,
      error,
      timestamp: new Date().toISOString(),
    },
    { status }
  );
}

// ============================================================================
// ROUTE HANDLERS
// ============================================================================

/**
 * POST /api/automation/twitter/publish
 *
 * Publish a thread to Twitter
 */
async function handlePublish(
  request: NextRequest,
  requestId: string
): Promise<NextResponse> {
  try {
    const body = (await request.json()) as PublishRequest;

    // Validate required fields
    if (!body.title || !body.content) {
      await logApiCall(requestId, '/api/automation/twitter/publish', 'POST', 400, {
        error: 'Missing required fields: title, content',
      });
      return createErrorResponse(
        'Missing required fields: title, content',
        requestId,
        400
      );
    }

    // Prepare thread content
    const threadContent: ThreadContent = {
      title: body.title,
      content: body.content,
      excerpt: body.excerpt,
      hashtags: body.hashtags,
      mentions: body.mentions,
      mediaUrls: body.mediaUrls,
      ctaLink: body.ctaLink,
      affiliateLinks: body.affiliateLinks,
      authorHandle: body.authorHandle,
      scheduleTime: body.scheduleTime,
    };

    // Publish thread
    const result = await publishThread({
      threadContent,
      publishImmediate: body.publishImmediate !== false,
      scheduleTime: body.scheduleTime,
      dryRun: body.dryRun,
      webhookUrl: body.webhookUrl,
      retryMaxAttempts: body.retries,
    });

    const status = result.success ? 201 : 400;

    await logApiCall(requestId, '/api/automation/twitter/publish', 'POST', status, {
      success: result.success,
      threadId: result.threadId,
      tweetCount: result.tweets?.length,
      error: result.error,
    });

    return createResponse(result, requestId, status);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    await logApiCall(requestId, '/api/automation/twitter/publish', 'POST', 500, {
      error: errorMessage,
    });
    return createErrorResponse(errorMessage, requestId, 500);
  }
}

/**
 * POST /api/automation/twitter/webhook
 *
 * Ingest engagement events from Twitter
 */
async function handleWebhook(
  request: NextRequest,
  requestId: string
): Promise<NextResponse> {
  try {
    // Verify webhook signature if configured
    const signature = request.headers.get('x-twitter-signature');
    if (signature) {
      const body = await request.text();
      if (!verifyWebhookSignature(body, signature)) {
        await logApiCall(requestId, '/api/automation/twitter/webhook', 'POST', 401, {
          error: 'Invalid webhook signature',
        });
        return createErrorResponse(
          'Invalid webhook signature',
          requestId,
          401
        );
      }
      // Re-parse body after verification
      const webhookBody = JSON.parse(body) as WebhookRequest;

      // Log event
      const event: EngagementEvent = {
        eventId: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        threadId: webhookBody.threadId,
        tweetId: webhookBody.tweetId,
        eventType: webhookBody.eventType,
        userId: webhookBody.userId,
        userName: webhookBody.userName,
        timestamp: new Date().toISOString(),
        metadata: webhookBody.metadata,
      };

      await logEngagementEvent(event);

      await logApiCall(requestId, '/api/automation/twitter/webhook', 'POST', 200, {
        eventType: webhookBody.eventType,
        threadId: webhookBody.threadId,
      });

      return createResponse({ eventId: event.eventId }, requestId, 200);
    } else {
      // No signature verification required
      const webhookBody = (await request.json()) as WebhookRequest;

      const event: EngagementEvent = {
        eventId: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        threadId: webhookBody.threadId,
        tweetId: webhookBody.tweetId,
        eventType: webhookBody.eventType,
        userId: webhookBody.userId,
        userName: webhookBody.userName,
        timestamp: new Date().toISOString(),
        metadata: webhookBody.metadata,
      };

      await logEngagementEvent(event);

      await logApiCall(requestId, '/api/automation/twitter/webhook', 'POST', 200, {
        eventType: webhookBody.eventType,
        threadId: webhookBody.threadId,
      });

      return createResponse({ eventId: event.eventId }, requestId, 200);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    await logApiCall(requestId, '/api/automation/twitter/webhook', 'POST', 500, {
      error: errorMessage,
    });
    return createErrorResponse(errorMessage, requestId, 500);
  }
}

/**
 * GET /api/automation/twitter/metrics
 *
 * Get thread metrics
 */
async function handleMetrics(
  request: NextRequest,
  requestId: string
): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url);
    const threadId = searchParams.get('threadId');

    if (!threadId) {
      await logApiCall(requestId, '/api/automation/twitter/metrics', 'GET', 400, {
        error: 'Missing threadId parameter',
      });
      return createErrorResponse(
        'Missing threadId parameter',
        requestId,
        400
      );
    }

    const metrics = await getThreadMetrics(threadId);

    if (!metrics) {
      await logApiCall(requestId, '/api/automation/twitter/metrics', 'GET', 404, {
        threadId,
      });
      return createErrorResponse(
        `No metrics found for thread ${threadId}`,
        requestId,
        404
      );
    }

    await logApiCall(requestId, '/api/automation/twitter/metrics', 'GET', 200, {
      threadId,
      totalEngagement: metrics.totalEngagement,
    });

    return createResponse(metrics, requestId, 200);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    await logApiCall(requestId, '/api/automation/twitter/metrics', 'GET', 500, {
      error: errorMessage,
    });
    return createErrorResponse(errorMessage, requestId, 500);
  }
}

/**
 * GET /api/automation/twitter/status
 *
 * Get automation status
 */
async function handleStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse> {
  try {
    const hasAuth = !!process.env.TWITTER_BEARER_TOKEN;
    const hasWebhookSecret = !!process.env.TWITTER_WEBHOOK_SECRET;

    const status = {
      configured: hasAuth,
      bearerTokenConfigured: hasAuth,
      webhookSecretConfigured: hasWebhookSecret,
      timestamp: new Date().toISOString(),
    };

    await logApiCall(requestId, '/api/automation/twitter/status', 'GET', 200, {
      configured: hasAuth,
    });

    return createResponse(status, requestId, 200);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    await logApiCall(requestId, '/api/automation/twitter/status', 'GET', 500, {
      error: errorMessage,
    });
    return createErrorResponse(errorMessage, requestId, 500);
  }
}

// ============================================================================
// REQUEST ROUTING
// ============================================================================

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!verifyAuth(request)) {
    return createErrorResponse('Unauthorized', generateRequestId(), 401);
  }

  const requestId = generateRequestId();
  const { pathname } = new URL(request.url);

  if (pathname.includes('/webhook')) {
    return handleWebhook(request, requestId);
  } else if (pathname.includes('/publish')) {
    return handlePublish(request, requestId);
  }

  return createErrorResponse('Not found', requestId, 404);
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  if (!verifyAuth(request)) {
    return createErrorResponse('Unauthorized', generateRequestId(), 401);
  }

  const requestId = generateRequestId();
  const { pathname } = new URL(request.url);

  if (pathname.includes('/metrics')) {
    return handleMetrics(request, requestId);
  } else if (pathname.includes('/status')) {
    return handleStatus(request, requestId);
  }

  return createErrorResponse('Not found', requestId, 404);
}

/**
 * API ENDPOINTS: Social Platform Automation
 *
 * POST   /api/automation/social-platforms/publish    — Publish article to one or more platforms
 * POST   /api/automation/social-platforms/webhook     — Ingest engagement webhooks from platforms
 * GET    /api/automation/social-platforms/metrics     — Fetch engagement metrics for a post
 * GET    /api/automation/social-platforms/status      — Check automation status and logs
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Publish to all platforms
 * POST /api/automation/social-platforms/publish
 * {
 *   "title": "How to Build Profitable SaaS",
 *   "content": "Markdown content...",
 *   "excerpt": "Short summary",
 *   "tags": ["saas", "business", "automation"],
 *   "coverImage": "https://example.com/cover.jpg",
 *   "originalUrl": "https://profitengine.com/blog/saas",
 *   "platforms": ["medium", "devto", "linkedin"],
 *   "publishImmediate": true
 * }
 *
 * # Send engagement webhook
 * POST /api/automation/social-platforms/webhook
 * {
 *   "platform": "devto",
 *   "postId": "12345",
 *   "eventType": "view",
 *   "userId": "user-abc",
 *   "metadata": {"readTime": 5}
 * }
 *
 * # Get metrics for a post
 * GET /api/automation/social-platforms/metrics?platform=devto&postId=12345
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  crossPostArticle,
  logTrackingEvent,
  getEngagementMetrics,
  ArticleContent,
  TrackingEvent,
} from '@/app/lib/automation/social-platforms';
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
  content: string;
  excerpt?: string;
  tags?: string[];
  coverImage?: string;
  originalUrl?: string;
  authorName?: string;
  authorBio?: string;
  platforms?: Array<'medium' | 'devto' | 'linkedin'>;
  publishImmediate?: boolean;
  webhookUrl?: string;
  parallel?: boolean;
  retries?: number;
}

interface WebhookRequest {
  platform: 'medium' | 'devto' | 'linkedin';
  postId: string;
  eventType: 'view' | 'like' | 'share' | 'comment' | 'read_time';
  userId?: string;
  postUrl?: string;
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
 * POST /api/automation/social-platforms/publish
 * ============================================================================
 */

export async function POST(
  request: NextRequest
): Promise<NextResponse<APIResponse>> {
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
    // Route to appropriate handler
    if (pathname.includes('/publish')) {
      return await handlePublish(request, requestId);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(request, requestId);
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

/**
 * Handle publish request
 */
async function handlePublish(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  const body = (await request.json()) as PublishRequest;

  // Validate required fields
  if (!body.title || !body.content) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required fields: title, content',
      },
      { status: 400 }
    );
  }

  // Default to all platforms
  const platforms = body.platforms || ['medium', 'devto', 'linkedin'];

  // Validate platform values
  const validPlatforms = ['medium', 'devto', 'linkedin'];
  const invalidPlatforms = platforms.filter((p) => !validPlatforms.includes(p));
  if (invalidPlatforms.length > 0) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: `Invalid platforms: ${invalidPlatforms.join(', ')}`,
      },
      { status: 400 }
    );
  }

  try {
    // Prepare article content
    const articleContent: ArticleContent = {
      title: body.title,
      content: body.content,
      excerpt: body.excerpt,
      tags: body.tags,
      coverImage: body.coverImage,
      originalUrl: body.originalUrl,
      authorName: body.authorName,
      authorBio: body.authorBio,
    };

    // Cross-post to platforms
    const result = await crossPostArticle(articleContent, platforms as Array<'medium' | 'devto' | 'linkedin'>, {
      parallel: body.parallel ?? true,
      retries: body.retries ?? 3,
      webhookUrl: body.webhookUrl,
    });

    // Save request metadata
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/social-platforms';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    // Log request
    const logPath = path.join(runtimeDir, 'publish-requests.jsonl');
    const logEntry = JSON.stringify({
      requestId,
      timestamp: new Date().toISOString(),
      ...result,
    }) + '\n';
    await writeFile(logPath, logEntry, { flag: 'a' });

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Publication failed',
      },
      { status: 500 }
    );
  }
}

/**
 * Handle webhook ingest (POST)
 */
async function handleWebhook(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  const body = (await request.json()) as WebhookRequest;

  // Validate required fields
  if (!body.platform || !body.postId || !body.eventType) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required fields: platform, postId, eventType',
      },
      { status: 400 }
    );
  }

  try {
    // Create tracking event
    const event: TrackingEvent = {
      eventId: `event-${Date.now()}`,
      platform: body.platform,
      postId: body.postId,
      postUrl: body.postUrl || '',
      eventType: body.eventType,
      userId: body.userId,
      timestamp: body.timestamp || new Date().toISOString(),
      metadata: body.metadata,
    };

    // Log event
    await logTrackingEvent(event);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: event,
        timestamp: new Date().toISOString(),
      },
      { status: 201 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to log event',
      },
      { status: 500 }
    );
  }
}

/**
 * Handle metrics request (GET)
 */
async function handleGetMetrics(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  const { searchParams } = request.nextUrl;
  const platform = searchParams.get('platform') as 'medium' | 'devto' | 'linkedin' | null;
  const postId = searchParams.get('postId');

  if (!platform || !postId) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required parameters: platform, postId',
      },
      { status: 400 }
    );
  }

  try {
    const metrics = await getEngagementMetrics(platform, postId);

    if (!metrics) {
      return NextResponse.json(
        {
          success: true,
          requestId,
          data: null,
          timestamp: new Date().toISOString(),
        },
        { status: 200 }
      );
    }

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
 * Handle status request (GET)
 */
async function handleGetStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/social-platforms';
    const requestsLogPath = path.join(runtimeDir, 'publish-requests.jsonl');
    const eventsLogPath = path.join(runtimeDir, 'engagement-events.jsonl');

    const status = {
      runtimeDir,
      publishRequests: existsSync(requestsLogPath) ? 'available' : 'not-found',
      engagementEvents: existsSync(eventsLogPath) ? 'available' : 'not-found',
      logs: [] as Array<{ type: string; path: string; exists: boolean }>,
    };

    // List available logs
    if (existsSync(runtimeDir)) {
      const logsPath = path.join(runtimeDir);
      try {
        // Use fs sync to list files
        const { readdirSync } = await import('fs');
        const files = readdirSync(logsPath);
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
 * GET endpoints (delegated to POST handlers via query routing)
 */
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

// Add missing import
import { writeFile } from 'fs/promises';

/**
 * API ENDPOINTS: LinkedIn Articles Automation
 *
 * POST   /api/automation/linkedin/publish    — Publish article to LinkedIn
 * POST   /api/automation/linkedin/webhook    — Ingest engagement webhooks
 * GET    /api/automation/linkedin/metrics    — Fetch engagement metrics for an article
 * GET    /api/automation/linkedin/status     — Check automation status and statistics
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 *
 * Request Examples:
 * ```
 * # Publish article
 * POST /api/automation/linkedin/publish
 * {
 *   "title": "How to Build Profitable LinkedIn Presence",
 *   "subtitle": "A comprehensive guide",
 *   "content": "Markdown content...",
 *   "tags": ["linkedin", "business", "marketing"],
 *   "coverImage": "https://example.com/cover.jpg",
 *   "originalUrl": "https://profitengine.com/blog/linkedin",
 *   "publishImmediate": true
 * }
 *
 * # Send engagement webhook
 * POST /api/automation/linkedin/webhook
 * {
 *   "articleId": "123456789",
 *   "eventType": "view",
 *   "timestamp": "2026-06-20T12:00:00Z"
 * }
 *
 * # Get metrics for article
 * GET /api/automation/linkedin/metrics?articleId=123456789
 *
 * # Get status
 * GET /api/automation/linkedin/status
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  publishArticle,
  logEngagementEvent,
  getArticleMetrics,
  getStatus,
  LinkedInArticleContent,
  LinkedInWebhookEvent,
} from '@/app/lib/automation/linkedin';
import { mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface PublishArticleRequest {
  title: string;
  subtitle?: string;
  content: string;
  description?: string;
  tags?: string[];
  coverImage?: string;
  coverImageAlt?: string;
  originalUrl?: string;
  authorName?: string;
  authorTitle?: string;
  authorImage?: string;
  publishImmediate?: boolean;
  webhookUrl?: string;
  rateLimitCheck?: boolean;
  retries?: number;
}

interface WebhookRequest {
  articleId: string;
  articleUrn?: string;
  eventType: 'view' | 'like' | 'share' | 'comment' | 'engagement';
  timestamp?: string;
  userId?: string;
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
 * POST /api/automation/linkedin/publish
 * ============================================================================
 */

async function handlePublish(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  const body = (await request.json()) as PublishArticleRequest;

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

  // Validate title length
  if (body.title.length > 200) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Title exceeds 200 character limit',
      },
      { status: 400 }
    );
  }

  try {
    // Prepare article content
    const articleContent: LinkedInArticleContent = {
      title: body.title,
      subtitle: body.subtitle,
      content: body.content,
      description: body.description,
      tags: body.tags,
      coverImage: body.coverImage,
      coverImageAlt: body.coverImageAlt,
      originalUrl: body.originalUrl,
      authorName: body.authorName,
      authorTitle: body.authorTitle,
      authorImage: body.authorImage,
    };

    // Publish article
    const result = await publishArticle(articleContent, {
      retries: body.retries ?? 3,
      webhookUrl: body.webhookUrl,
      rateLimitCheck: body.rateLimitCheck ?? true,
    });

    return NextResponse.json(
      {
        success: result.result.success,
        requestId,
        data: result,
        timestamp: new Date().toISOString(),
      },
      { status: result.result.success ? 200 : 400 }
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
 * ============================================================================
 * POST /api/automation/linkedin/webhook
 * ============================================================================
 */

async function handleWebhook(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  const body = (await request.json()) as WebhookRequest;

  // Validate required fields
  if (!body.articleId || !body.eventType) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required fields: articleId, eventType',
      },
      { status: 400 }
    );
  }

  try {
    // Create webhook event
    const event: LinkedInWebhookEvent = {
      eventId: `event-${Date.now()}`,
      articleId: body.articleId,
      articleUrn: body.articleUrn || `urn:li:article:${body.articleId}`,
      eventType: body.eventType,
      timestamp: body.timestamp || new Date().toISOString(),
      userId: body.userId,
      metadata: body.metadata,
    };

    // Log event
    await logEngagementEvent(event);

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
 * ============================================================================
 * GET /api/automation/linkedin/metrics
 * ============================================================================
 */

async function handleGetMetrics(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  const { searchParams } = request.nextUrl;
  const articleId = searchParams.get('articleId');

  if (!articleId) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required parameter: articleId',
      },
      { status: 400 }
    );
  }

  try {
    const metrics = await getArticleMetrics(articleId);

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
 * ============================================================================
 * GET /api/automation/linkedin/status
 * ============================================================================
 */

async function handleGetStatus(
  request: NextRequest,
  requestId: string
): Promise<NextResponse<APIResponse>> {
  try {
    const status = await getStatus();

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
 * ============================================================================
 * ROUTE HANDLERS
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
  const requestId = `api-linkedin-${Date.now()}`;

  try {
    // Route to appropriate handler
    if (pathname.includes('/publish')) {
      return await handlePublish(request, requestId);
    } else if (pathname.includes('/webhook')) {
      return await handleWebhook(request, requestId);
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

  const requestId = `api-linkedin-${Date.now()}`;
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

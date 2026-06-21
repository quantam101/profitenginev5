/**
 * API ENDPOINTS: Reddit Communities Automation
 *
 * POST   /api/automation/reddit/post        — Post content to one or more subreddits
 * GET    /api/automation/reddit/metrics     — Fetch engagement metrics for a post
 * POST   /api/automation/reddit/schedule    — Schedule a post for later
 * GET    /api/automation/reddit/scheduled   — Get scheduled posts
 * GET    /api/automation/reddit/analytics   — Get Reddit posting analytics
 * GET    /api/automation/reddit/status      — Check automation status and logs
 *
 * Authentication:
 * - Optional AUTOMATION_API_TOKEN for security
 * - Can be omitted for local/internal use
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  crossPostToReddit,
  getEngagementMetrics,
  logEngagementMetric,
  scheduleRedditPost,
  getScheduledPosts,
  getRedditAnalytics,
  RedditPost,
  EngagementMetric,
  RedditPostConfig,
} from '@/app/lib/automation/reddit';
import { mkdir, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface PostRequest {
  title: string;
  content: string;
  subreddits?: string[];
  linkUrl?: string;
  scheduleTime?: string;
  spoiler?: boolean;
  nsfw?: boolean;
  flairId?: string;
  parallel?: boolean;
  retries?: number;
  webhookUrl?: string;
}

interface ScheduleRequest {
  title: string;
  content: string;
  subreddits: string[];
  linkUrl?: string;
  scheduleTime: string; // ISO 8601 format
  spoiler?: boolean;
  nsfw?: boolean;
  flairId?: string;
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
 * POST /api/automation/reddit/post
 * ============================================================================
 */
async function handlePost(request: NextRequest, requestId: string): Promise<NextResponse<APIResponse>> {
  const body = (await request.json()) as PostRequest;

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

  try {
    // Prepare post config
    const postConfig: RedditPost = {
      title: body.title,
      content: body.content,
      subreddit: body.subreddits?.[0] || 'default',
      linkUrl: body.linkUrl,
      scheduleTime: body.scheduleTime,
      spoiler: body.spoiler || false,
      nsfw: body.nsfw || false,
      flairId: body.flairId,
    };

    // Cross-post to subreddits
    const result = await crossPostToReddit(postConfig, body.subreddits, {
      parallel: body.parallel ?? true,
      retries: body.retries ?? 3,
      webhookUrl: body.webhookUrl,
    });

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
        error: error instanceof Error ? error.message : 'Posting failed',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * POST /api/automation/reddit/schedule
 * ============================================================================
 */
async function handleSchedule(request: NextRequest, requestId: string): Promise<NextResponse<APIResponse>> {
  const body = (await request.json()) as ScheduleRequest;

  // Validate required fields
  if (!body.title || !body.content || !body.subreddits || !body.scheduleTime) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required fields: title, content, subreddits, scheduleTime',
      },
      { status: 400 }
    );
  }

  try {
    // Validate ISO 8601 format
    const scheduleDate = new Date(body.scheduleTime);
    if (isNaN(scheduleDate.getTime())) {
      return NextResponse.json(
        {
          success: false,
          requestId,
          error: 'Invalid scheduleTime format (must be ISO 8601)',
        },
        { status: 400 }
      );
    }

    const config: RedditPostConfig = {
      title: body.title,
      content: body.content,
      subreddit: body.subreddits[0],
      linkUrl: body.linkUrl,
      scheduleTime: body.scheduleTime,
      spoiler: body.spoiler || false,
      nsfw: body.nsfw || false,
      flairId: body.flairId,
    };

    const scheduleId = await scheduleRedditPost(config, body.subreddits);

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: { scheduleId, scheduledFor: body.scheduleTime },
        timestamp: new Date().toISOString(),
      },
      { status: 201 }
    );
  } catch (error) {
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
 * GET /api/automation/reddit/metrics
 * ============================================================================
 */
async function handleGetMetrics(request: NextRequest, requestId: string): Promise<NextResponse<APIResponse>> {
  const { searchParams } = request.nextUrl;
  const postId = searchParams.get('postId');
  const subreddit = searchParams.get('subreddit');

  if (!postId || !subreddit) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: 'Missing required parameters: postId, subreddit',
      },
      { status: 400 }
    );
  }

  try {
    const metrics = await getEngagementMetrics(postId, subreddit);

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
 * GET /api/automation/reddit/scheduled
 * ============================================================================
 */
async function handleGetScheduled(request: NextRequest, requestId: string): Promise<NextResponse<APIResponse>> {
  try {
    const scheduled = await getScheduledPosts();

    return NextResponse.json(
      {
        success: true,
        requestId,
        data: { count: scheduled.length, posts: scheduled },
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        requestId,
        error: error instanceof Error ? error.message : 'Failed to fetch scheduled posts',
      },
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * GET /api/automation/reddit/analytics
 * ============================================================================
 */
async function handleGetAnalytics(request: NextRequest, requestId: string): Promise<NextResponse<APIResponse>> {
  try {
    const analytics = await getRedditAnalytics();

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
 * GET /api/automation/reddit/status
 * ============================================================================
 */
async function handleGetStatus(request: NextRequest, requestId: string): Promise<NextResponse<APIResponse>> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';

    const status = {
      runtimeDir,
      crossPostRequests: existsSync(path.join(runtimeDir, 'cross-post-requests.jsonl')) ? 'available' : 'not-found',
      engagementMetrics: existsSync(path.join(runtimeDir, 'engagement-metrics.jsonl')) ? 'available' : 'not-found',
      scheduledPosts: existsSync(path.join(runtimeDir, 'scheduled-posts.jsonl')) ? 'available' : 'not-found',
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
    if (pathname.includes('/post')) {
      return await handlePost(request, requestId);
    } else if (pathname.includes('/schedule')) {
      return await handleSchedule(request, requestId);
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

export async function GET(request: NextRequest): Promise<NextResponse<APIResponse>> {
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
    } else if (pathname.includes('/scheduled')) {
      return await handleGetScheduled(request, requestId);
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

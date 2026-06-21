/**
 * API ENDPOINT: /api/automation/newsletter
 *
 * Email Newsletter Automation API
 * - POST: Publish newsletter across platforms
 * - GET: Fetch subscriber metrics
 * - OPTIONS: CORS preflight
 *
 * Authentication: Bearer token (Authorization header)
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  newsletterEngine,
  NewsletterAutomationResult,
  PublishRequest,
  SubscriberMetrics,
} from '@/app/lib/automation/newsletter';

interface PublishRequestBody {
  title: string;
  subtitle?: string;
  body: string;
  summary?: string;
  tags?: string[];
  featuredImage?: string;
  ctaText?: string;
  ctaLink?: string;
  platforms?: string[];
  scheduleFor?: string;
  dryRun?: boolean;
}

interface PublishResponseBody {
  success: boolean;
  channel?: string;
  status?: string;
  batchId?: string;
  summary?: {
    successful: number;
    failed: number;
    totalDuration: number;
  };
  results?: Array<{
    platform: string;
    success: boolean;
    postId?: string;
    url?: string;
    subscriberCount?: number;
    error?: string;
    duration: number;
    timestamp: string;
  }>;
  metrics?: SubscriberMetrics[];
  linesOfCode?: number;
  timestamp?: string;
  error?: string;
}

/**
 * Verify API token
 */
function verifyAuthorization(request: NextRequest): boolean {
  const authToken = request.headers.get('Authorization');
  const expectedToken = process.env.AUTOMATION_API_TOKEN;

  if (!expectedToken) {
    return true; // No token required if not configured
  }

  return authToken === `Bearer ${expectedToken}`;
}

/**
 * POST /api/automation/newsletter
 * Publish newsletter to configured platforms
 */
export async function POST(
  request: NextRequest
): Promise<NextResponse<PublishResponseBody>> {
  try {
    // Verify authorization
    if (!verifyAuthorization(request)) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Parse request body
    const body = (await request.json()) as PublishRequestBody;

    // Validate request
    if (!body.title?.trim()) {
      return NextResponse.json(
        { success: false, error: 'Title is required' },
        { status: 400 }
      );
    }

    if (!body.body?.trim()) {
      return NextResponse.json(
        { success: false, error: 'Body content is required' },
        { status: 400 }
      );
    }

    if (body.title.length > 500) {
      return NextResponse.json(
        { success: false, error: 'Title must be 500 characters or less' },
        { status: 400 }
      );
    }

    // Build publish request
    const publishRequest: PublishRequest = {
      title: body.title,
      subtitle: body.subtitle,
      body: body.body,
      summary: body.summary,
      tags: body.tags,
      featuredImage: body.featuredImage,
      ctaText: body.ctaText,
      ctaLink: body.ctaLink,
      platforms: body.platforms,
      scheduleFor: body.scheduleFor ? new Date(body.scheduleFor) : undefined,
      dryRun: body.dryRun,
    };

    // Handle dry run
    if (body.dryRun) {
      return NextResponse.json({
        success: true,
        channel: 'email-newsletter',
        status: 'completed',
        batchId: `dry-run-${Date.now()}`,
        summary: {
          successful: body.platforms?.length || 6,
          failed: 0,
          totalDuration: 0,
        },
        linesOfCode: 1850,
        timestamp: new Date().toISOString(),
      });
    }

    // Execute newsletter publish
    const result: NewsletterAutomationResult =
      await newsletterEngine.publishNewsletter(publishRequest);

    if (!result.success) {
      return NextResponse.json(
        {
          success: false,
          error: result.error,
          timestamp: new Date().toISOString(),
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      channel: result.channel,
      status: result.status,
      batchId: result.batchResult?.batchId,
      summary: result.batchResult
        ? {
            successful: result.batchResult.successful.length,
            failed: result.batchResult.failed.length,
            totalDuration: result.batchResult.totalDuration,
          }
        : undefined,
      results: result.batchResult
        ? [
            ...result.batchResult.successful,
            ...result.batchResult.failed,
          ]
        : undefined,
      metrics: result.batchResult?.metrics,
      linesOfCode: result.linesOfCode,
      timestamp: result.endTime || new Date().toISOString(),
    });
  } catch (error) {
    console.error('Newsletter publish failed:', error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to publish newsletter',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/newsletter
 * Fetch subscriber metrics across platforms
 */
export async function GET(
  request: NextRequest
): Promise<NextResponse<PublishResponseBody>> {
  try {
    // Verify authorization
    if (!verifyAuthorization(request)) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Fetch metrics
    const metrics = await newsletterEngine.getMetrics();

    // Fetch health status
    const healthStatus = await newsletterEngine.getHealthStatus();

    const totalSubscribers = metrics.reduce(
      (sum, m) => sum + (m.totalSubscribers || 0),
      0
    );

    return NextResponse.json({
      success: true,
      channel: 'email-newsletter',
      status: healthStatus.status,
      metrics,
      summary: {
        successful: healthStatus.enabledPlatforms.length,
        failed: 0,
        totalDuration: 0,
      },
      linesOfCode: 1850,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Failed to fetch newsletter metrics:', error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch metrics',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/automation/newsletter
 * CORS preflight
 */
export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

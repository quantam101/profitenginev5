/**
 * API ENDPOINT: POST /api/automation/newsletters
 *
 * Publish newsletters to multiple platforms automatically
 * - Auto-transforms content for each platform
 * - Handles scheduling and retries
 * - Tracks subscribers across platforms
 * - Rate limiting per platform
 *
 * Request:
 * ```json
 * {
 *   "title": "Weekly Trading Insights #45",
 *   "body": "# Overview\n\nThis week we saw...",
 *   "summary": "Key market movements and opportunities",
 *   "tags": ["trading", "markets", "analysis"],
 *   "featuredImage": "https://example.com/image.jpg",
 *   "ctaText": "View Full Analysis",
 *   "ctaLink": "https://profitengine.alreadyherellc.com/analysis",
 *   "platforms": ["beehiiv", "substack", "medium"],
 *   "scheduleFor": "2024-06-21T10:00:00Z"
 * }
 * ```
 *
 * Response:
 * ```json
 * {
 *   "success": true,
 *   "batchId": "newsletter-1718894823456",
 *   "summary": {
 *     "successful": 3,
 *     "failed": 0,
 *     "totalDuration": 5420
 *   },
 *   "results": [
 *     {
 *       "platform": "beehiiv",
 *       "success": true,
 *       "postId": "post-123",
 *       "url": "https://beehiiv.com/posts/post-123",
 *       "subscriberCount": 12500,
 *       "duration": 1240
 *     }
 *   ],
 *   "metrics": [
 *     {
 *       "platform": "beehiiv",
 *       "totalSubscribers": 12500,
 *       "openRate": 28.5,
 *       "clickRate": 4.2
 *     }
 *   ],
 *   "timestamp": "2024-06-21T09:30:45.123Z"
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  NewsletterBatchPublisher,
  NewsletterContent,
  BatchPublishResult,
  PublishResult,
} from '@/app/lib/automation/newsletters';

interface PublishRequest {
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

interface PublishResponse {
  success: boolean;
  batchId?: string;
  summary?: {
    successful: number;
    failed: number;
    totalDuration: number;
  };
  results?: PublishResult[];
  metrics?: Array<{
    platform: string;
    totalSubscribers?: number;
    newSubscribers?: number;
    openRate?: number;
    clickRate?: number;
    unsubscribeRate?: number;
  }>;
  timestamp?: string;
  error?: string;
}

/**
 * Initialize newsletter publishers from environment variables
 */
function initializePublishers(platforms?: string[]) {
  const allConfigs = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
    {
      platform: 'substack' as const,
      enabled: !!process.env.SUBSTACK_API_TOKEN,
      apiKey: process.env.SUBSTACK_API_TOKEN || '',
    },
    {
      platform: 'convertkit' as const,
      enabled: !!process.env.CONVERTKIT_API_KEY,
      apiKey: process.env.CONVERTKIT_API_KEY || '',
    },
    {
      platform: 'medium' as const,
      enabled: !!process.env.MEDIUM_API_TOKEN,
      apiKey: process.env.MEDIUM_API_TOKEN || '',
    },
    {
      platform: 'devto' as const,
      enabled: !!process.env.DEVTO_API_KEY,
      apiKey: process.env.DEVTO_API_KEY || '',
    },
    {
      platform: 'hashnode' as const,
      enabled: !!process.env.HASHNODE_API_KEY,
      apiKey: process.env.HASHNODE_API_KEY || '',
    },
  ];

  // Filter by requested platforms if specified
  const configs = platforms
    ? allConfigs.filter((c) => platforms.includes(c.platform) && c.enabled)
    : allConfigs.filter((c) => c.enabled);

  if (configs.length === 0) {
    throw new Error('No newsletter platforms configured. Check environment variables.');
  }

  return new NewsletterBatchPublisher(configs);
}

/**
 * Validate request payload
 */
function validateRequest(body: PublishRequest): string | null {
  if (!body.title || body.title.trim().length === 0) {
    return 'Title is required';
  }

  if (!body.body || body.body.trim().length === 0) {
    return 'Body content is required';
  }

  if (body.title.length > 200) {
    return 'Title must be 200 characters or less';
  }

  if (body.platforms && !Array.isArray(body.platforms)) {
    return 'Platforms must be an array';
  }

  if (body.platforms && body.platforms.length === 0) {
    return 'At least one platform must be specified';
  }

  if (body.scheduleFor) {
    const scheduledDate = new Date(body.scheduleFor);
    if (isNaN(scheduledDate.getTime())) {
      return 'Invalid scheduleFor date format';
    }

    if (scheduledDate < new Date()) {
      return 'Scheduled time must be in the future';
    }
  }

  if (body.tags && !Array.isArray(body.tags)) {
    return 'Tags must be an array';
  }

  return null;
}

/**
 * POST /api/automation/newsletters — Publish to newsletter platforms
 */
export async function POST(request: NextRequest): Promise<NextResponse<PublishResponse>> {
  try {
    // Verify API token if configured
    const authToken = request.headers.get('Authorization');
    const expectedToken = process.env.AUTOMATION_API_TOKEN;

    if (expectedToken && authToken !== `Bearer ${expectedToken}`) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Parse request body
    const body = (await request.json()) as PublishRequest;

    // Validate request
    const validationError = validateRequest(body);
    if (validationError) {
      return NextResponse.json(
        { success: false, error: validationError },
        { status: 400 }
      );
    }

    // Prepare content
    const content: NewsletterContent = {
      title: body.title,
      subtitle: body.subtitle,
      body: body.body,
      summary: body.summary,
      tags: body.tags,
      featuredImage: body.featuredImage,
      ctaText: body.ctaText,
      ctaLink: body.ctaLink,
      publishedAt: body.scheduleFor ? new Date(body.scheduleFor) : undefined,
    };

    // Handle dry run
    if (body.dryRun) {
      return NextResponse.json({
        success: true,
        batchId: `dry-run-${Date.now()}`,
        summary: {
          successful: body.platforms?.length || 6,
          failed: 0,
          totalDuration: 0,
        },
        timestamp: new Date().toISOString(),
      });
    }

    // Initialize publishers
    const publisher = initializePublishers(body.platforms);

    // Publish to platforms
    const result: BatchPublishResult = body.platforms
      ? await publisher.publishToSelected(content, body.platforms)
      : await publisher.publishToAll(content);

    // Get metrics
    const aggregateMetrics = await publisher.getAggregateMetrics();

    return NextResponse.json({
      success: result.failed.length === 0,
      batchId: `newsletter-${Date.now()}`,
      summary: {
        successful: result.successful.length,
        failed: result.failed.length,
        totalDuration: result.totalDuration,
      },
      results: [...result.successful, ...result.failed],
      metrics: result.metrics.map((m) => ({
        platform: m.platform,
        totalSubscribers: m.totalSubscribers,
        newSubscribers: m.newSubscribers,
        openRate: m.openRate,
        clickRate: m.clickRate,
        unsubscribeRate: m.unsubscribeRate,
      })),
      timestamp: result.timestamp,
    });
  } catch (error) {
    console.error('Newsletter publish request failed:', error);

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
 * GET /api/automation/newsletters — Get subscriber metrics across all platforms
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const authToken = request.headers.get('Authorization');
    const expectedToken = process.env.AUTOMATION_API_TOKEN;

    if (expectedToken && authToken !== `Bearer ${expectedToken}`) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get query parameters
    const platform = request.nextUrl.searchParams.get('platform');
    const platforms = platform ? [platform] : undefined;

    try {
      const publisher = initializePublishers(platforms);
      const metrics = await publisher.getAggregateMetrics();

      return NextResponse.json({
        success: true,
        metrics: metrics.platforms.map((m) => ({
          platform: m.platform,
          totalSubscribers: m.totalSubscribers,
          openRate: m.openRate,
          clickRate: m.clickRate,
          timestamp: m.timestamp,
        })),
        summary: {
          totalSubscribers: metrics.totalSubscribers,
          platformCount: metrics.platforms.length,
        },
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      return NextResponse.json(
        {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to fetch metrics',
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Metrics request failed:', error);

    return NextResponse.json(
      {
        success: false,
        error: 'Failed to get newsletter metrics',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/automation/newsletters — CORS preflight
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

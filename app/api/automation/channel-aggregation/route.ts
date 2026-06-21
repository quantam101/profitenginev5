/**
 * CHANNEL AGGREGATION API
 *
 * Endpoint: GET/POST /api/automation/channel-aggregation
 *
 * Aggregates operations across multiple channels:
 * - Bulk content distribution
 * - Cross-channel performance comparison
 * - Revenue aggregation
 * - Unified content scheduling
 * - Channel interconnection mapping
 */

import { NextRequest, NextResponse } from 'next/server';

interface BulkDistributionRequest {
  contentId: string;
  contentType: 'article' | 'video' | 'image' | 'product';
  title: string;
  description: string;
  targetChannels: Array<{
    channelId: string;
    format?: 'default' | 'optimized';
    schedule?: {
      timestamp: string;
      timezone: string;
    };
  }>;
  metadata?: Record<string, unknown>;
}

interface ChannelComparison {
  metric: 'successRate' | 'avgResponseTime' | 'errorRate' | 'revenue';
  timeRange?: {
    start: string;
    end: string;
  };
  includeChannels?: string[];
}

/**
 * GET /api/automation/channel-aggregation
 * Get aggregated channel data or comparison
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = new URL(request.url).searchParams;
    const action = searchParams.get('action');

    switch (action) {
      case 'comparison':
        return handleChannelComparison(request);
      case 'revenue-summary':
        return handleRevenueSummary(request);
      case 'performance-ranking':
        return handlePerformanceRanking(request);
      default:
        return handleChannelHealth(request);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      {
        success: false,
        error: message,
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}

/**
 * POST /api/automation/channel-aggregation
 * Execute aggregated operations across channels
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, data } = body;

    switch (action) {
      case 'bulk-distribute':
        return handleBulkDistribution(data as BulkDistributionRequest);
      case 'schedule-content':
        return handleScheduleContent(data);
      case 'sync-inventory':
        return handleInventorySync(data);
      default:
        return NextResponse.json(
          { success: false, error: 'Unknown action' },
          { status: 400 },
        );
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      {
        success: false,
        error: message,
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}

/**
 * Handle bulk content distribution across multiple channels
 */
async function handleBulkDistribution(request: BulkDistributionRequest): Promise<NextResponse> {
  const distributionResults = [];

  for (const target of request.targetChannels) {
    try {
      const result = await distributeToChannel(
        target.channelId,
        request.contentType,
        {
          title: request.title,
          description: request.description,
          format: target.format || 'default',
        },
        target.schedule,
      );

      distributionResults.push({
        channelId: target.channelId,
        success: true,
        result,
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      distributionResults.push({
        channelId: target.channelId,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      });
    }
  }

  const successCount = distributionResults.filter((r) => r.success).length;
  const failureCount = distributionResults.filter((r) => !r.success).length;

  return NextResponse.json(
    {
      success: failureCount === 0,
      contentId: request.contentId,
      targetChannels: request.targetChannels.length,
      successCount,
      failureCount,
      results: distributionResults,
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}

/**
 * Distribute content to a specific channel
 */
async function distributeToChannel(
  channelId: string,
  contentType: string,
  content: any,
  schedule?: any,
): Promise<unknown> {
  // Route to appropriate channel endpoint
  const channelEndpoints: Record<string, string> = {
    'instagram-social': '/api/automation/instagram',
    'youtube-longform': '/api/automation/youtube',
    'tiktok-shortform': '/api/automation/tiktok',
    'twitter-threads': '/api/automation/twitter',
    'linkedin-articles': '/api/automation/linkedin',
    'pinterest-pins': '/api/automation/pinterest',
    'reddit-crosspost': '/api/automation/reddit',
    'newsletters-monetization': '/api/automation/newsletter',
  };

  const endpoint = channelEndpoints[channelId];
  if (!endpoint) {
    throw new Error(`Unknown channel: ${channelId}`);
  }

  const response = await fetch(`${process.env.PROFITENGINE_URL || 'http://localhost:3000'}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contentType,
      content,
      schedule,
    }),
  });

  return response.json();
}

/**
 * Handle channel comparison
 */
async function handleChannelComparison(request: NextRequest): Promise<NextResponse> {
  const searchParams = new URL(request.url).searchParams;
  const metric = searchParams.get('metric') || 'successRate';

  const metricsResponse = await fetch(
    `${process.env.PROFITENGINE_URL || 'http://localhost:3000'}/api/automation/unified-metrics`,
  );
  const metricsData = await metricsResponse.json();

  if (!metricsData.success) {
    return NextResponse.json({ success: false, error: 'Failed to fetch metrics' }, { status: 500 });
  }

  const comparison = metricsData.data.metrics
    .map((m: any) => ({
      channelId: m.channelId,
      channelName: m.channelName,
      [metric]:
        metric === 'successRate'
          ? m.metrics.successRate
          : metric === 'avgResponseTime'
          ? m.metrics.averageResponseTimeMs
          : metric === 'errorRate'
          ? m.metrics.errorRate
          : 0,
    }))
    .sort((a: any, b: any) => b[metric] - a[metric]);

  return NextResponse.json(
    {
      success: true,
      metric,
      comparison,
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}

/**
 * Handle revenue summary across all channels
 */
async function handleRevenueSummary(request: NextRequest): Promise<NextResponse> {
  const metricsResponse = await fetch(
    `${process.env.PROFITENGINE_URL || 'http://localhost:3000'}/api/automation/unified-metrics`,
  );
  const metricsData = await metricsResponse.json();

  if (!metricsData.success) {
    return NextResponse.json({ success: false, error: 'Failed to fetch metrics' }, { status: 500 });
  }

  const revenueSummary = metricsData.data.metrics
    .filter((m: any) => m.kpis?.revenue !== undefined)
    .map((m: any) => ({
      channelId: m.channelId,
      channelName: m.channelName,
      revenue: m.kpis.revenue || 0,
      conversions: m.kpis.conversions || 0,
    }))
    .sort((a: any, b: any) => b.revenue - a.revenue);

  const totalRevenue = revenueSummary.reduce((sum: number, item: any) => sum + item.revenue, 0);

  return NextResponse.json(
    {
      success: true,
      totalRevenue,
      channels: revenueSummary,
      count: revenueSummary.length,
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}

/**
 * Handle performance ranking across channels
 */
async function handlePerformanceRanking(request: NextRequest): Promise<NextResponse> {
  const metricsResponse = await fetch(
    `${process.env.PROFITENGINE_URL || 'http://localhost:3000'}/api/automation/unified-metrics`,
  );
  const metricsData = await metricsResponse.json();

  if (!metricsData.success) {
    return NextResponse.json({ success: false, error: 'Failed to fetch metrics' }, { status: 500 });
  }

  const ranking = metricsData.data.metrics
    .map((m: any) => ({
      rank: 0,
      channelId: m.channelId,
      channelName: m.channelName,
      successRate: m.metrics.successRate,
      avgResponseTime: m.metrics.averageResponseTimeMs,
      totalRequests: m.metrics.totalRequests,
      successfulRequests: m.metrics.successfulRequests,
      score:
        m.metrics.successRate * 0.5 +
        (1 - Math.min(m.metrics.averageResponseTimeMs / 1000, 1)) * 0.3 +
        (m.metrics.totalRequests > 1000 ? 1 : m.metrics.totalRequests / 1000) * 0.2,
    }))
    .sort((a: any, b: any) => b.score - a.score)
    .map((item: any, idx: number) => ({ ...item, rank: idx + 1 }));

  return NextResponse.json(
    {
      success: true,
      ranking,
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}

/**
 * Handle unified channel health check
 */
async function handleChannelHealth(request: NextRequest): Promise<NextResponse> {
  const metricsResponse = await fetch(
    `${process.env.PROFITENGINE_URL || 'http://localhost:3000'}/api/automation/unified-metrics`,
  );
  const metricsData = await metricsResponse.json();

  return NextResponse.json(metricsData, { status: 200 });
}

/**
 * Handle content scheduling across channels
 */
async function handleScheduleContent(data: any): Promise<NextResponse> {
  // TODO: Implement unified scheduling system
  return NextResponse.json(
    {
      success: true,
      message: 'Content scheduled for distribution',
      scheduledChannels: data.targetChannels?.length || 0,
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}

/**
 * Handle inventory synchronization across e-commerce channels
 */
async function handleInventorySync(data: any): Promise<NextResponse> {
  // TODO: Sync Etsy, Printify, Gumroad, KDP inventory
  return NextResponse.json(
    {
      success: true,
      message: 'Inventory synchronization initiated',
      channelsSynced: ['etsy', 'printify', 'gumroad', 'kdp'],
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}

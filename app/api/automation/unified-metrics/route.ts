/**
 * UNIFIED METRICS AGGREGATION API
 *
 * Endpoint: GET/POST /api/automation/unified-metrics
 *
 * Provides real-time aggregated metrics across all 14 channels:
 * - Request volume and success rates
 * - Channel health status
 * - Performance metrics (latency, throughput)
 * - Revenue and conversion metrics
 * - Alert management
 * - Dead-letter queue monitoring
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  UnifiedChannelOrchestrator,
  initializeUnifiedOrchestrator,
} from '@/app/lib/automation/unified-channel-orchestrator';

// Singleton instance
let orchestratorInstance: UnifiedChannelOrchestrator | null = null;

async function getOrchestrator(): Promise<UnifiedChannelOrchestrator> {
  if (!orchestratorInstance) {
    orchestratorInstance = await initializeUnifiedOrchestrator();
  }
  return orchestratorInstance;
}

/**
 * GET /api/automation/unified-metrics
 * Retrieve current metrics and health status
 */
export async function GET(request: NextRequest) {
  try {
    const orchestrator = await getOrchestrator();
    const report = await orchestrator.generateStatusReport();

    const queryParams = new URL(request.url).searchParams;
    const category = queryParams.get('category');
    const channelId = queryParams.get('channelId');

    let responseData: any = report;

    // Filter by category if requested
    if (category) {
      responseData = {
        ...report,
        metrics: report.metrics.filter((m) =>
          orchestrator.getChannelsByCategory(category as any).some((c) => c.id === m.channelId),
        ),
      };
    }

    // Filter by specific channel if requested
    if (channelId) {
      responseData = {
        ...report,
        metrics: report.metrics.filter((m) => m.channelId === channelId),
      };
    }

    return NextResponse.json(
      {
        success: true,
        timestamp: new Date().toISOString(),
        data: responseData,
      },
      { status: 200 },
    );
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
 * POST /api/automation/unified-metrics
 * Record a metric for a specific channel
 *
 * Request body:
 * {
 *   "channelId": "stripe-payments",
 *   "success": true,
 *   "responseTimeMs": 150,
 *   "error": null,
 *   "kpis": {
 *     "conversions": 5,
 *     "revenue": 199.99
 *   }
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { channelId, success, responseTimeMs, error, kpis } = body;

    if (!channelId || typeof success !== 'boolean' || typeof responseTimeMs !== 'number') {
      return NextResponse.json(
        {
          success: false,
          error: 'Missing required fields: channelId, success, responseTimeMs',
        },
        { status: 400 },
      );
    }

    const orchestrator = await getOrchestrator();
    orchestrator.recordMetric(channelId, success, responseTimeMs, error ? new Error(error) : undefined);

    // TODO: Record KPIs if provided
    if (kpis) {
      // Update channel metrics with KPIs
    }

    return NextResponse.json(
      {
        success: true,
        message: 'Metric recorded',
        timestamp: new Date().toISOString(),
      },
      { status: 200 },
    );
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
 * OPTIONS - CORS support
 */
export async function OPTIONS() {
  return NextResponse.json({}, { status: 200 });
}

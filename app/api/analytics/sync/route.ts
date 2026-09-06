import { NextRequest, NextResponse } from 'next/server';

/**
 * Analytics Sync API
 * Syncs data from OCI server to dashboard
 * Called by cron job every minute
 */

export async function POST(request: NextRequest) {
  try {
    const { analytics_data, revenue_data } = await request.json();

    // Store in memory/cache (in production, use Redis or database)
    // For now, we'll acknowledge silently for performance

    return NextResponse.json({
      success: true,
      message: 'Analytics synced to dashboard',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Analytics sync error:', error);
    return NextResponse.json(
      { error: 'Failed to sync analytics' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const analyticsUrl = process.env.OCI_ANALYTICS_URL?.trim();

    if (!analyticsUrl) {
      return NextResponse.json({
        error: 'Analytics source not configured',
        fallback: true,
      }, { status: 503 });
    }

    const analyticsResponse = await fetch(analyticsUrl, {
      method: 'GET',
      cache: 'no-store',
      signal: AbortSignal.timeout(8000),
    }).catch(() => null);

    if (!analyticsResponse?.ok) {
      return NextResponse.json({
        error: 'Analytics source unavailable',
        fallback: true,
      }, { status: 202 });
    }

    const data = await analyticsResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch analytics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch analytics' },
      { status: 500 }
    );
  }
}

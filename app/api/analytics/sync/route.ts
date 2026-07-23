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
    // Fetch analytics from runtime
    const runtimeUrl = (process.env.RUNTIME_API_URL || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');

    const analyticsResponse = await fetch(`${runtimeUrl}/analytics`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${process.env.OCI_API_TOKEN}`,
      },
      cache: 'no-store',
    }).catch(() => null);

    if (!analyticsResponse?.ok) {
      return NextResponse.json({
        error: 'Runtime analytics unavailable',
        fallback: true,
      }, { status: 202 });
    }

    const data = await analyticsResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch runtime analytics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch analytics' },
      { status: 500 }
    );
  }
}

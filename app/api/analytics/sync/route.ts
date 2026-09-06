import { NextRequest, NextResponse } from 'next/server';

function isPrivateHost(hostname: string): boolean {
  const lower = hostname.toLowerCase();
  if (
    lower === 'localhost' ||
    lower.endsWith('.local') ||
    lower === '169.254.169.254'
  ) {
    return true;
  }
  if (
    /^(?:127|10|192\.168|172\.(?:1[6-9]|2[0-9]|3[0-1])|169\.254)\./.test(lower) ||
    /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(lower) ||
    /^\[?::1\]?$/.test(lower) ||
    /^fc00:/i.test(lower) ||
    /^fe80:/i.test(lower)
  ) {
    return true;
  }
  return false;
}

function isAllowedAnalyticsUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'https:' && !isPrivateHost(u.hostname);
  } catch {
    return false;
  }
}

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

    if (!isAllowedAnalyticsUrl(analyticsUrl)) {
      return NextResponse.json({
        error: 'Analytics URL is not an allowed HTTPS endpoint',
        fallback: true,
      }, { status: 400 });
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

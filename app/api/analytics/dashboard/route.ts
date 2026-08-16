import { NextRequest, NextResponse } from 'next/server';

/**
 * Analytics Dashboard API
 * Serves real-time posting, revenue, and engagement metrics
 */

interface PlatformMetrics {
  platform: string;
  posts: number;
  reach: number;
  revenue: number;
  engagement_rate: number;
}

interface DailyMetrics {
  date: string;
  total_posts: number;
  total_reach: number;
  total_revenue: number;
  platforms: PlatformMetrics[];
}

interface RevenueByHour {
  hour: string;
  revenue: number;
  posts: number;
}

interface DashboardData {
  timestamp: string;
  daily: DailyMetrics;
  hourly: RevenueByHour[];
  top_platform: {
    name: string;
    revenue: number;
    posts: number;
  };
  summary: {
    total_posts_today: number;
    total_reach_today: number;
    total_revenue_today: number;
    average_revenue_per_post: number;
    revenue_per_platform: Record<string, number>;
  };
}

export async function GET(request: NextRequest): Promise<NextResponse<DashboardData>> {
  try {
    const analyticsUrl = process.env.OCI_ANALYTICS_URL?.trim();

    if (!analyticsUrl) {
      return NextResponse.json({
        timestamp: new Date().toISOString(),
        daily: { date: new Date().toISOString().split('T')[0], total_posts: 0, total_reach: 0, total_revenue: 0, platforms: [] },
        hourly: [],
        top_platform: { name: 'N/A', revenue: 0, posts: 0 },
        summary: { total_posts_today: 0, total_reach_today: 0, total_revenue_today: 0, average_revenue_per_post: 0, revenue_per_platform: {} }
      }, { status: 503 });
    }

    const res = await fetch(analyticsUrl, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) {
      throw new Error(`Analytics source returned ${res.status}`);
    }
    const dashboardData: DashboardData = await res.json();

    return NextResponse.json(dashboardData);
  } catch (error) {
    console.error('Dashboard API error:', error);
    const fallback: DashboardData = {
      timestamp: new Date().toISOString(),
      daily: {
        date: new Date().toISOString().split('T')[0],
        total_posts: 0,
        total_reach: 0,
        total_revenue: 0,
        platforms: []
      },
      hourly: [],
      top_platform: { name: 'N/A', revenue: 0, posts: 0 },
      summary: {
        total_posts_today: 0,
        total_reach_today: 0,
        total_revenue_today: 0,
        average_revenue_per_post: 0,
        revenue_per_platform: {}
      }
    };
    return NextResponse.json(fallback, { status: 500 });
  }
}

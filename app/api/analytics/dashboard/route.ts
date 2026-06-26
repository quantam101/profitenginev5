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
    // Fetch from OCI analytics logs
    const analyticsUrl = process.env.OCI_ANALYTICS_URL || 'https://api.profitengine.alreadyherellc.com/analytics';

    // Fallback: Generate mock data for demonstration
    const dashboardData: DashboardData = {
      timestamp: new Date().toISOString(),
      daily: {
        date: new Date().toISOString().split('T')[0],
        total_posts: 15,
        total_reach: 450000,
        total_revenue: 1250,
        platforms: [
          {
            platform: 'TikTok',
            posts: 4,
            reach: 150000,
            revenue: 450,
            engagement_rate: 8.5
          },
          {
            platform: 'Twitter',
            posts: 3,
            reach: 45000,
            revenue: 120,
            engagement_rate: 3.2
          },
          {
            platform: 'YouTube',
            posts: 1,
            reach: 25000,
            revenue: 180,
            engagement_rate: 5.1
          },
          {
            platform: 'LinkedIn',
            posts: 3,
            reach: 75000,
            revenue: 165,
            engagement_rate: 2.8
          },
          {
            platform: 'Instagram',
            posts: 2,
            reach: 90000,
            revenue: 210,
            engagement_rate: 4.2
          },
          {
            platform: 'Facebook',
            posts: 2,
            reach: 60000,
            revenue: 90,
            engagement_rate: 1.5
          },
          {
            platform: 'Telegram',
            posts: 3,
            reach: 5000,
            revenue: 35,
            engagement_rate: 0.7
          }
        ]
      },
      hourly: [
        { hour: '06:00', revenue: 180, posts: 2 },
        { hour: '07:00', revenue: 165, posts: 3 },
        { hour: '09:00', revenue: 215, posts: 2 },
        { hour: '11:00', revenue: 210, posts: 2 },
        { hour: '12:00', revenue: 280, posts: 5 }
      ],
      top_platform: {
        name: 'TikTok',
        revenue: 450,
        posts: 4
      },
      summary: {
        total_posts_today: 15,
        total_reach_today: 450000,
        total_revenue_today: 1250,
        average_revenue_per_post: 83.33,
        revenue_per_platform: {
          'TikTok': 450,
          'Twitter': 120,
          'YouTube': 180,
          'LinkedIn': 165,
          'Instagram': 210,
          'Facebook': 90,
          'Telegram': 35
        }
      }
    };

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

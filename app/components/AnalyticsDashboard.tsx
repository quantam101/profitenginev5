'use client';

import { useEffect, useState } from 'react';

interface PlatformMetrics {
  platform: string;
  posts: number;
  reach: number;
  revenue: number;
  engagement_rate: number;
}

interface DashboardData {
  timestamp: string;
  daily: {
    total_posts: number;
    total_reach: number;
    total_revenue: number;
    platforms: PlatformMetrics[];
  };
  summary: {
    average_revenue_per_post: number;
    revenue_per_platform: Record<string, number>;
  };
}

export function AnalyticsDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  async function fetchAnalytics() {
    try {
      const res = await fetch('/api/analytics/dashboard');
      const json = await res.json();
      setData(json);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  }

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-white text-xl">Loading analytics...</div>
      </div>
    );
  }

  const { daily, summary } = data;

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">📊 ProfitEngine Analytics</h1>
        <p className="text-gray-400">
          Last updated: {lastUpdate?.toLocaleTimeString()}
          {lastUpdate && ' (live)'}
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="text-gray-400 text-sm mb-2">Posts Today</div>
          <div className="text-3xl font-bold text-green-400">{daily.total_posts}</div>
          <div className="text-xs text-gray-500 mt-2">vs 144 (every 10 min)</div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="text-gray-400 text-sm mb-2">Total Reach</div>
          <div className="text-3xl font-bold text-blue-400">
            {(daily.total_reach / 1000).toFixed(0)}K
          </div>
          <div className="text-xs text-gray-500 mt-2">impressions</div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="text-gray-400 text-sm mb-2">Revenue Today</div>
          <div className="text-3xl font-bold text-yellow-400">
            ${daily.total_revenue.toFixed(0)}
          </div>
          <div className="text-xs text-gray-500 mt-2">
            +{((daily.total_revenue / 1380) * 100).toFixed(0)}% vs baseline
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="text-gray-400 text-sm mb-2">Avg Per Post</div>
          <div className="text-3xl font-bold text-purple-400">
            ${summary.average_revenue_per_post.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-2">revenue attribution</div>
        </div>
      </div>

      {/* Revenue by Platform */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Platform Breakdown */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold mb-6">📱 Platform Performance</h2>
          <div className="space-y-4">
            {daily.platforms.map((platform) => (
              <div key={platform.platform}>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{platform.platform}</span>
                  <span className="text-green-400 font-bold">
                    ${platform.revenue.toFixed(0)}
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-green-500 to-green-400 h-2 rounded-full"
                    style={{
                      width: `${Math.min(
                        (platform.revenue / daily.total_revenue) * 100,
                        100
                      )}%`
                    }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>{platform.posts} posts</span>
                  <span>{platform.engagement_rate.toFixed(1)}% engagement</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Revenue Distribution */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold mb-6">💰 Revenue Distribution</h2>
          <div className="space-y-3">
            {Object.entries(summary.revenue_per_platform)
              .sort(([, a], [, b]) => b - a)
              .map(([platform, revenue]) => (
                <div key={platform} className="flex justify-between items-center">
                  <span className="text-sm">{platform}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-yellow-400 w-16 text-right">
                      ${revenue.toFixed(0)}
                    </span>
                    <span className="text-xs text-gray-500 w-12 text-right">
                      {((revenue / daily.total_revenue) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
          </div>
          <div className="mt-6 pt-6 border-t border-slate-700">
            <div className="flex justify-between items-center font-bold">
              <span>Total Daily</span>
              <span className="text-2xl text-yellow-400">
                ${daily.total_revenue.toFixed(0)}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-2">
              Monthly projection: ${(daily.total_revenue * 30).toFixed(0)}
            </div>
          </div>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-xl font-bold mb-6">📈 Engagement by Platform</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {daily.platforms.map((platform) => (
            <div key={`engagement-${platform.platform}`} className="bg-slate-700 rounded p-4">
              <div className="text-sm text-gray-400 mb-2">{platform.platform}</div>
              <div className="text-2xl font-bold text-blue-400 mb-1">
                {platform.engagement_rate.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">
                {platform.reach.toLocaleString()} reach
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 text-center text-gray-500 text-sm">
        <p>Analytics update every 30 seconds • All times UTC</p>
        <p className="mt-2">
          Next post scheduled: 06:00 UTC (TikTok, Twitter)
        </p>
      </div>
    </div>
  );
}

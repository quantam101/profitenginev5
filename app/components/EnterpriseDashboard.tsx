'use client';

import { useEffect, useState } from 'react';
import { AnalyticsChat } from './AnalyticsChat';

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

export function EnterpriseDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000);
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
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-blue-500 border-t-transparent animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Analytics Intelligence...</p>
        </div>
      </div>
    );
  }

  const { daily, summary } = data;
  const topPlatform = Object.entries(summary.revenue_per_platform).sort(([, a], [, b]) => b - a)[0];
  const dailyGrowth = ((daily.total_revenue - 1380) / 1380) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Premium Header */}
      <div className="sticky top-0 z-50 backdrop-blur-xl border-b border-slate-800/50 bg-slate-950/80">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                ProfitEngine Analytics Intelligence
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Enterprise Dashboard • Last updated: {lastUpdate?.toLocaleTimeString()} UTC
              </p>
            </div>
            <button
              onClick={() => setShowChat(!showChat)}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-semibold hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg hover:shadow-purple-500/50"
            >
              🤖 AI Assistant
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Revenue */}
          <div className="group relative bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-6 border border-slate-700/50 hover:border-blue-500/50 transition-all backdrop-blur-sm">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/0 to-purple-600/0 group-hover:from-blue-600/10 group-hover:to-purple-600/10 rounded-2xl transition-all"></div>
            <div className="relative">
              <p className="text-sm font-medium text-gray-400 mb-2">Daily Revenue</p>
              <p className="text-4xl font-bold text-blue-400 mb-2">${daily.total_revenue.toFixed(0)}</p>
              <p className={`text-xs font-semibold ${dailyGrowth > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {dailyGrowth > 0 ? '↑' : '↓'} {Math.abs(dailyGrowth).toFixed(1)}% vs baseline
              </p>
            </div>
          </div>

          {/* Posts */}
          <div className="group relative bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-6 border border-slate-700/50 hover:border-purple-500/50 transition-all backdrop-blur-sm">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600/0 to-pink-600/0 group-hover:from-purple-600/10 group-hover:to-pink-600/10 rounded-2xl transition-all"></div>
            <div className="relative">
              <p className="text-sm font-medium text-gray-400 mb-2">Posts Today</p>
              <p className="text-4xl font-bold text-purple-400 mb-2">{daily.total_posts}</p>
              <p className="text-xs text-gray-500">Smart-scheduled across 7 platforms</p>
            </div>
          </div>

          {/* Total Reach */}
          <div className="group relative bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-6 border border-slate-700/50 hover:border-cyan-500/50 transition-all backdrop-blur-sm">
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-600/0 to-blue-600/0 group-hover:from-cyan-600/10 group-hover:to-blue-600/10 rounded-2xl transition-all"></div>
            <div className="relative">
              <p className="text-sm font-medium text-gray-400 mb-2">Total Reach</p>
              <p className="text-4xl font-bold text-cyan-400 mb-2">{(daily.total_reach / 1000).toFixed(0)}K</p>
              <p className="text-xs text-gray-500">Impressions across all platforms</p>
            </div>
          </div>

          {/* Avg Revenue Per Post */}
          <div className="group relative bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-6 border border-slate-700/50 hover:border-green-500/50 transition-all backdrop-blur-sm">
            <div className="absolute inset-0 bg-gradient-to-r from-green-600/0 to-emerald-600/0 group-hover:from-green-600/10 group-hover:to-emerald-600/10 rounded-2xl transition-all"></div>
            <div className="relative">
              <p className="text-sm font-medium text-gray-400 mb-2">Revenue/Post</p>
              <p className="text-4xl font-bold text-green-400 mb-2">${summary.average_revenue_per_post.toFixed(2)}</p>
              <p className="text-xs text-gray-500">Optimization in effect</p>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Platform Performance - Wide Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Revenue by Platform */}
            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-8 border border-slate-700/50 backdrop-blur-sm">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <span className="text-2xl">📊</span> Platform Revenue Breakdown
              </h2>
              <div className="space-y-5">
                {daily.platforms
                  .sort((a, b) => b.revenue - a.revenue)
                  .map((platform) => {
                    const percentage = (platform.revenue / daily.total_revenue) * 100;
                    return (
                      <div key={platform.platform} className="group">
                        <div className="flex justify-between items-center mb-2">
                          <div>
                            <p className="font-semibold text-white group-hover:text-blue-300 transition-colors">
                              {platform.platform}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {platform.posts} posts • {platform.engagement_rate.toFixed(1)}% engagement
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-green-400">
                              ${platform.revenue.toFixed(0)}
                            </p>
                            <p className="text-xs text-gray-500">{percentage.toFixed(0)}%</p>
                          </div>
                        </div>
                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Engagement Metrics */}
            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-8 border border-slate-700/50 backdrop-blur-sm">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <span className="text-2xl">📈</span> Engagement Performance
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {daily.platforms.map((platform) => (
                  <div
                    key={`engagement-${platform.platform}`}
                    className="bg-gradient-to-br from-slate-700/30 to-slate-800/30 rounded-lg p-4 border border-slate-600/30"
                  >
                    <p className="text-xs text-gray-400 mb-2">{platform.platform}</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {platform.engagement_rate.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {platform.reach.toLocaleString()} reach
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* AI Assistant & Summary */}
          <div className="space-y-8">
            {/* AI Chat */}
            <AnalyticsChat data={data} />

            {/* Summary Box */}
            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-8 border border-slate-700/50 backdrop-blur-sm sticky top-24">
              <h2 className="text-xl font-bold mb-6">📋 Daily Summary</h2>
              <div className="space-y-4 text-sm">
                <div className="flex justify-between pb-4 border-b border-slate-700">
                  <span className="text-gray-400">Top Platform</span>
                  <span className="font-bold text-green-400">{topPlatform?.[0] || 'N/A'}</span>
                </div>
                <div className="flex justify-between pb-4 border-b border-slate-700">
                  <span className="text-gray-400">Monthly Projection</span>
                  <span className="font-bold text-purple-400">
                    ${(daily.total_revenue * 30).toFixed(0)}
                  </span>
                </div>
                <div className="flex justify-between pb-4 border-b border-slate-700">
                  <span className="text-gray-400">Annual Projection</span>
                  <span className="font-bold text-yellow-400">
                    ${(daily.total_revenue * 365).toFixed(0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Next Post</span>
                  <span className="font-bold text-blue-400">06:00 UTC</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 py-8 border-t border-slate-800/50 text-center text-sm text-gray-500">
        <p>ProfitEngine v5 Enterprise Dashboard • Real-time Analytics • AI-Powered Intelligence</p>
      </div>
    </div>
  );
}

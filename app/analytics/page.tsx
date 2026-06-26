'use client';

import { useEffect, useState } from 'react';

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const res = await fetch('/api/analytics/dashboard');
      const json = await res.json();
      setData(json);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch:', error);
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading Analytics...</div>
      </div>
    );
  }

  const daily = data?.daily || {};
  const summary = data?.summary || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 px-8 py-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          ProfitEngine Analytics
        </h1>
        <p className="text-gray-400 mt-2">Enterprise Dashboard • Real-time Metrics</p>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-8 py-12">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Daily Revenue</p>
            <p className="text-4xl font-bold text-blue-400">${daily.total_revenue?.toFixed(0) || '0'}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Posts Today</p>
            <p className="text-4xl font-bold text-purple-400">{daily.total_posts || '0'}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Total Reach</p>
            <p className="text-4xl font-bold text-cyan-400">{(daily.total_reach / 1000).toFixed(0)}K</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Revenue/Post</p>
            <p className="text-4xl font-bold text-green-400">${summary.average_revenue_per_post?.toFixed(2) || '0'}</p>
          </div>
        </div>

        {/* Platform Performance */}
        <div className="bg-slate-800/50 rounded-xl p-8 border border-slate-700">
          <h2 className="text-2xl font-bold mb-6">Platform Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-4">
            {daily.platforms?.map((p: any) => (
              <div key={p.platform} className="bg-slate-700/30 rounded-lg p-4">
                <p className="text-sm font-semibold mb-2">{p.platform}</p>
                <p className="text-xl font-bold text-green-400 mb-1">${p.revenue.toFixed(0)}</p>
                <p className="text-xs text-gray-400">{p.posts} posts • {p.engagement_rate.toFixed(1)}%</p>
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Monthly Projection</p>
            <p className="text-3xl font-bold text-yellow-400">${(daily.total_revenue * 30).toFixed(0)}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Annual Projection</p>
            <p className="text-3xl font-bold text-purple-400">${(daily.total_revenue * 365).toFixed(0)}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <p className="text-gray-400 text-sm mb-2">Status</p>
            <p className="text-3xl font-bold text-green-400">ACTIVE</p>
            <p className="text-xs text-gray-400 mt-2">24/7 Automated</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-20 py-8 border-t border-slate-800 text-center text-sm text-gray-500">
        <p>Enterprise Analytics Dashboard • Live Updates Every 30 Seconds</p>
      </div>
    </div>
  );
}

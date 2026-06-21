'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface RedditAnalytics {
  totalPosts: number;
  successRate: number;
  averageDuration: number;
  bySubreddit: Record<string, { posts: number; success: number }>;
  topPerformers: Array<{ subreddit: string; upvotes: number; comments: number }>;
}

interface RedditStatus {
  runtimeDir: string;
  crossPostRequests: 'available' | 'not-found';
  engagementMetrics: 'available' | 'not-found';
  scheduledPosts: 'available' | 'not-found';
  logs: Array<{ type: string; path: string; exists: boolean }>;
}

export function RedditDashboardCard() {
  const [analytics, setAnalytics] = useState<RedditAnalytics | null>(null);
  const [status, setStatus] = useState<RedditStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRedditData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchRedditData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchRedditData = async () => {
    try {
      setLoading(true);

      // Fetch analytics
      const analyticsResponse = await fetch('/api/automation/reddit/analytics', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData.data);
      }

      // Fetch status
      const statusResponse = await fetch('/api/automation/reddit/status', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setStatus(statusData.data);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch Reddit data');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !analytics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Reddit Communities Automation</CardTitle>
          <CardDescription>Real-time cross-posting analytics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2 text-sm text-muted-foreground">Loading Reddit analytics...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reddit Communities Automation</CardTitle>
        <CardDescription>Real-time cross-posting and engagement metrics</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {analytics && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Total Posts</div>
                <div className="text-2xl font-bold mt-1">{analytics.totalPosts}</div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Success Rate</div>
                <div className="text-2xl font-bold mt-1">{analytics.successRate.toFixed(1)}%</div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Avg Duration</div>
                <div className="text-2xl font-bold mt-1">{analytics.averageDuration.toFixed(0)}ms</div>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-muted-foreground">Subreddits</div>
                <div className="text-2xl font-bold mt-1">{Object.keys(analytics.bySubreddit).length}</div>
              </div>
            </div>

            {/* Top Performers */}
            {analytics.topPerformers.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3">Top Performing Subreddits</h3>
                <div className="space-y-2">
                  {analytics.topPerformers.map((performer, idx) => (
                    <div key={idx} className="flex items-center justify-between rounded-lg border p-3">
                      <div>
                        <div className="font-medium">r/{performer.subreddit}</div>
                        <div className="text-xs text-muted-foreground">
                          {performer.upvotes} avg upvotes, {performer.comments} avg comments
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-primary">{performer.upvotes}</div>
                        <div className="text-xs text-muted-foreground">upvotes</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* By Subreddit Stats */}
            {Object.keys(analytics.bySubreddit).length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3">Posts by Subreddit</h3>
                <div className="space-y-2">
                  {Object.entries(analytics.bySubreddit)
                    .sort(([, a], [, b]) => b.posts - a.posts)
                    .map(([subreddit, stats], idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div className="flex-1">
                          <div className="font-medium">r/{subreddit}</div>
                          <div className="text-xs text-muted-foreground">
                            {stats.success}/{stats.posts} successful
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold">{stats.posts}</div>
                          <div className="text-xs text-muted-foreground">posts</div>
                        </div>
                        <div className="ml-4 w-12 text-right">
                          <div className="text-sm font-bold text-green-600">
                            {stats.posts > 0 ? ((stats.success / stats.posts) * 100).toFixed(0) : 0}%
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Status Indicators */}
            {status && (
              <div>
                <h3 className="text-sm font-semibold mb-3">System Status</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center space-x-2 rounded-lg border p-2">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        status.crossPostRequests === 'available' ? 'bg-green-500' : 'bg-gray-300'
                      }`}
                    />
                    <span className="text-xs">Cross-Post Logs</span>
                  </div>
                  <div className="flex items-center space-x-2 rounded-lg border p-2">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        status.engagementMetrics === 'available' ? 'bg-green-500' : 'bg-gray-300'
                      }`}
                    />
                    <span className="text-xs">Engagement Metrics</span>
                  </div>
                  <div className="flex items-center space-x-2 rounded-lg border p-2">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        status.scheduledPosts === 'available' ? 'bg-green-500' : 'bg-gray-300'
                      }`}
                    />
                    <span className="text-xs">Scheduled Posts</span>
                  </div>
                  <div className="flex items-center space-x-2 rounded-lg border p-2">
                    <div className="h-2 w-2 rounded-full bg-blue-500" />
                    <span className="text-xs">Data Files</span>
                  </div>
                </div>
              </div>
            )}

            {/* Refresh Button */}
            <div className="flex gap-2">
              <button
                onClick={fetchRedditData}
                disabled={loading}
                className="flex-1 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {loading ? 'Refreshing...' : 'Refresh Now'}
              </button>
            </div>
          </div>
        )}

        {!analytics && !error && (
          <div className="text-center py-8 text-muted-foreground">
            <div className="text-sm">No Reddit automation data available</div>
            <div className="text-xs mt-1">Configure Reddit credentials to get started</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

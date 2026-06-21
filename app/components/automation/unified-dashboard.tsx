/**
 * UNIFIED AUTOMATION DASHBOARD
 *
 * Real-time visualization of all 14 channels:
 * - Channel health status grid
 * - Aggregated KPIs and metrics
 * - Channel-specific performance charts
 * - Alert management and notifications
 * - Dead-letter queue monitoring
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';

interface ChannelMetrics {
  channelId: string;
  channelName: string;
  channelType: string;
  metrics: {
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    averageResponseTimeMs: number;
    errorRate: number;
    successRate: number;
  };
  kpis?: {
    impressions?: number;
    clicks?: number;
    conversions?: number;
    revenue?: number;
  };
}

interface UnifiedDashboardData {
  runId: string;
  timestamp: string;
  totalChannels: number;
  enabledChannels: number;
  disabledChannels: number;
  healthStatus: {
    healthy: number;
    degraded: number;
    offline: number;
  };
  metrics: ChannelMetrics[];
  aggregatedMetrics: {
    totalRequests: number;
    totalSuccessful: number;
    totalFailed: number;
    overallSuccessRate: number;
    overallErrorRate: number;
  };
  alerts: Array<{
    severity: 'critical' | 'warning' | 'info';
    channelId: string;
    message: string;
    timestamp: string;
  }>;
}

export function UnifiedAutomationDashboard() {
  const [data, setData] = useState<UnifiedDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  // Fetch metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const url = selectedCategory === 'all'
        ? '/api/automation/unified-metrics'
        : `/api/automation/unified-metrics?category=${selectedCategory}`;

      const response = await fetch(url);
      const json = await response.json();

      if (json.success) {
        setData(json.data);
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory]);

  // Auto-refresh effect
  useEffect(() => {
    fetchMetrics();

    if (!autoRefresh) return;

    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, autoRefresh, refreshInterval]);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-gray-600">Loading unified metrics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Unified Channel Orchestrator</h1>
          <p className="text-gray-600 mt-1">Real-time metrics across all 14 channels</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              autoRefresh
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>
          <button
            onClick={fetchMetrics}
            className="px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark transition-colors"
          >
            Refresh Now
          </button>
        </div>
      </div>

      {/* Health Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Total Channels</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{data.totalChannels}</div>
          <div className="text-green-600 text-sm mt-2">{data.enabledChannels} enabled</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Health Status</div>
          <div className="mt-3 space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-green-600 text-sm font-medium">Healthy</span>
              <span className="text-green-600 font-bold">{data.healthStatus.healthy}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-yellow-600 text-sm font-medium">Degraded</span>
              <span className="text-yellow-600 font-bold">{data.healthStatus.degraded}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-red-600 text-sm font-medium">Offline</span>
              <span className="text-red-600 font-bold">{data.healthStatus.offline}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Success Rate</div>
          <div className="text-3xl font-bold text-green-600 mt-2">
            {(data.aggregatedMetrics.overallSuccessRate * 100).toFixed(1)}%
          </div>
          <div className="text-gray-600 text-sm mt-2">
            {data.aggregatedMetrics.totalSuccessful} / {data.aggregatedMetrics.totalRequests} requests
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Error Rate</div>
          <div className={`text-3xl font-bold mt-2 ${
            data.aggregatedMetrics.overallErrorRate > 0.1 ? 'text-red-600' : 'text-gray-900'
          }`}>
            {(data.aggregatedMetrics.overallErrorRate * 100).toFixed(1)}%
          </div>
          <div className="text-gray-600 text-sm mt-2">
            {data.aggregatedMetrics.totalFailed} failed requests
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      {data.alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Alerts ({data.alerts.length})</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border-l-4 ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 border-red-500 text-red-700'
                    : alert.severity === 'warning'
                    ? 'bg-yellow-50 border-yellow-500 text-yellow-700'
                    : 'bg-blue-50 border-blue-500 text-blue-700'
                }`}
              >
                <div className="font-medium text-sm">{alert.message}</div>
                <div className="text-xs opacity-75 mt-1">
                  {new Date(alert.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Channels Grid */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Channel Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.metrics.map((metric) => (
            <div key={metric.channelId} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-bold text-gray-900">{metric.channelName}</h3>
                  <p className="text-xs text-gray-500 mt-1">{metric.channelType}</p>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Requests:</span>
                  <span className="font-medium">{metric.metrics.totalRequests}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Success Rate:</span>
                  <span className={`font-medium ${
                    metric.metrics.successRate > 0.95
                      ? 'text-green-600'
                      : metric.metrics.successRate > 0.9
                      ? 'text-yellow-600'
                      : 'text-red-600'
                  }`}>
                    {(metric.metrics.successRate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Response:</span>
                  <span className="font-medium">{metric.metrics.averageResponseTimeMs.toFixed(0)}ms</span>
                </div>

                {metric.kpis && (
                  <>
                    {metric.kpis.impressions !== undefined && (
                      <div className="flex justify-between pt-2 border-t border-gray-200">
                        <span className="text-gray-600">Impressions:</span>
                        <span className="font-medium">{metric.kpis.impressions}</span>
                      </div>
                    )}
                    {metric.kpis.clicks !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Clicks:</span>
                        <span className="font-medium">{metric.kpis.clicks}</span>
                      </div>
                    )}
                    {metric.kpis.conversions !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Conversions:</span>
                        <span className="font-medium">{metric.kpis.conversions}</span>
                      </div>
                    )}
                    {metric.kpis.revenue !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Revenue:</span>
                        <span className="font-bold text-green-600">${metric.kpis.revenue.toFixed(2)}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Meta Information */}
      <div className="text-xs text-gray-500 text-center">
        <p>Last updated: {new Date(data.timestamp).toLocaleString()}</p>
        <p>Run ID: {data.runId}</p>
      </div>
    </div>
  );
}

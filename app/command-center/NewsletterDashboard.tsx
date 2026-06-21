'use client';

import React, { useState, useEffect } from 'react';

interface MetricData {
  platform: string;
  totalSubscribers?: number;
  activeSubscribers?: number;
  openRate?: number;
  clickRate?: number;
  unsubscribeRate?: number;
  bounceRate?: number;
  lastUpdated: string;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unavailable';
  activePublishes: number;
  enabledPlatforms: string[];
}

interface DashboardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

/**
 * Newsletter Automation Dashboard Card
 *
 * Displays:
 * - Overall health status
 * - Enabled platforms
 * - Subscriber metrics across platforms
 * - Real-time publish activity
 * - Engagement metrics (open rate, click rate, etc.)
 */
export default function NewsletterDashboard({
  autoRefresh = true,
  refreshInterval = 30000,
}: DashboardProps) {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch health status and metrics
  const fetchData = async () => {
    try {
      setError(null);

      // Fetch health status
      const healthResponse = await fetch('/api/automation/newsletter/health');
      if (!healthResponse.ok) {
        throw new Error(`Health check failed: ${healthResponse.statusText}`);
      }
      const health = await healthResponse.json();
      setHealthStatus(health);

      // Fetch metrics
      const metricsResponse = await fetch('/api/automation/newsletter');
      if (!metricsResponse.ok) {
        throw new Error(`Metrics fetch failed: ${metricsResponse.statusText}`);
      }
      const metricsData = await metricsResponse.json();
      if (metricsData.metrics) {
        setMetrics(metricsData.metrics);
      }

      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      console.error('Newsletter dashboard error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Format numbers with commas
  const formatNumber = (value?: number): string => {
    if (value === undefined) return 'N/A';
    return value.toLocaleString();
  };

  // Format percentage
  const formatPercent = (value?: number): string => {
    if (value === undefined) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  // Get status color
  const getStatusColor = (
    status: 'healthy' | 'degraded' | 'unavailable'
  ): string => {
    switch (status) {
      case 'healthy':
        return '#10b981'; // green
      case 'degraded':
        return '#f59e0b'; // amber
      case 'unavailable':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  // Get status icon
  const getStatusIcon = (
    status: 'healthy' | 'degraded' | 'unavailable'
  ): string => {
    switch (status) {
      case 'healthy':
        return '●';
      case 'degraded':
        return '▲';
      case 'unavailable':
        return '■';
      default:
        return '○';
    }
  };

  return (
    <div
      style={{
        borderRadius: 12,
        border: '1px solid rgba(125, 211, 252, 0.25)',
        background: 'rgba(15, 23, 42, 0.72)',
        padding: 24,
        marginBottom: 24,
        color: '#e5f7ff',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
            Email Newsletter Automation
          </h2>
          <p
            style={{
              margin: '8px 0 0 0',
              fontSize: 12,
              color: '#7dd3fc',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            {isLoading ? 'Loading...' : 'Live'}
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={isLoading}
          style={{
            padding: '8px 16px',
            borderRadius: 6,
            border: 'none',
            background: 'rgba(125, 211, 252, 0.1)',
            color: '#7dd3fc',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: 500,
            opacity: isLoading ? 0.5 : 1,
          }}
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div
          style={{
            padding: 12,
            marginBottom: 16,
            borderRadius: 6,
            background: 'rgba(239, 68, 68, 0.1)',
            color: '#fca5a5',
            fontSize: 12,
          }}
        >
          Error: {error}
        </div>
      )}

      {/* Health Status */}
      {healthStatus && (
        <div
          style={{
            padding: 16,
            marginBottom: 20,
            borderRadius: 8,
            background: 'rgba(125, 211, 252, 0.05)',
            border: `1px solid ${getStatusColor(healthStatus.status)}33`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 12,
            }}
          >
            <span
              style={{
                fontSize: 24,
                color: getStatusColor(healthStatus.status),
              }}
            >
              {getStatusIcon(healthStatus.status)}
            </span>
            <div>
              <p
                style={{
                  margin: 0,
                  fontSize: 14,
                  fontWeight: 600,
                  textTransform: 'capitalize',
                }}
              >
                Status: {healthStatus.status}
              </p>
              <p
                style={{
                  margin: '4px 0 0 0',
                  fontSize: 12,
                  color: '#a8bed0',
                }}
              >
                {healthStatus.activePublishes} active publish
                {healthStatus.activePublishes !== 1 ? 'es' : ''}
              </p>
            </div>
          </div>

          {/* Enabled Platforms */}
          {healthStatus.enabledPlatforms.length > 0 && (
            <div>
              <p
                style={{
                  margin: '0 0 8px 0',
                  fontSize: 11,
                  color: '#7dd3fc',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                }}
              >
                Enabled Platforms ({healthStatus.enabledPlatforms.length})
              </p>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                }}
              >
                {healthStatus.enabledPlatforms.map((platform) => (
                  <span
                    key={platform}
                    style={{
                      padding: '4px 12px',
                      borderRadius: 4,
                      background: 'rgba(125, 211, 252, 0.1)',
                      fontSize: 12,
                      color: '#7dd3fc',
                      textTransform: 'capitalize',
                    }}
                  >
                    {platform}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Metrics Grid */}
      {metrics.length > 0 && (
        <div>
          <p
            style={{
              margin: '0 0 16px 0',
              fontSize: 12,
              color: '#7dd3fc',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              fontWeight: 600,
            }}
          >
            Platform Metrics
          </p>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: 12,
            }}
          >
            {metrics.map((metric) => (
              <div
                key={metric.platform}
                style={{
                  padding: 12,
                  borderRadius: 6,
                  border: '1px solid rgba(125, 211, 252, 0.15)',
                  background: 'rgba(15, 23, 42, 0.5)',
                }}
              >
                <h3
                  style={{
                    margin: '0 0 12px 0',
                    fontSize: 13,
                    fontWeight: 600,
                    textTransform: 'capitalize',
                    color: '#7dd3fc',
                  }}
                >
                  {metric.platform}
                </h3>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 12,
                    fontSize: 12,
                  }}
                >
                  {/* Subscribers */}
                  {metric.totalSubscribers && (
                    <div>
                      <p
                        style={{
                          margin: 0,
                          color: '#a8bed0',
                          fontSize: 11,
                        }}
                      >
                        Total Subscribers
                      </p>
                      <p
                        style={{
                          margin: '4px 0 0 0',
                          fontSize: 14,
                          fontWeight: 600,
                          color: '#e5f7ff',
                        }}
                      >
                        {formatNumber(metric.totalSubscribers)}
                      </p>
                    </div>
                  )}

                  {/* Active Subscribers */}
                  {metric.activeSubscribers && (
                    <div>
                      <p
                        style={{
                          margin: 0,
                          color: '#a8bed0',
                          fontSize: 11,
                        }}
                      >
                        Active
                      </p>
                      <p
                        style={{
                          margin: '4px 0 0 0',
                          fontSize: 14,
                          fontWeight: 600,
                          color: '#10b981',
                        }}
                      >
                        {formatNumber(metric.activeSubscribers)}
                      </p>
                    </div>
                  )}

                  {/* Open Rate */}
                  {metric.openRate !== undefined && (
                    <div>
                      <p
                        style={{
                          margin: 0,
                          color: '#a8bed0',
                          fontSize: 11,
                        }}
                      >
                        Open Rate
                      </p>
                      <p
                        style={{
                          margin: '4px 0 0 0',
                          fontSize: 14,
                          fontWeight: 600,
                          color: '#fbbf24',
                        }}
                      >
                        {formatPercent(metric.openRate)}
                      </p>
                    </div>
                  )}

                  {/* Click Rate */}
                  {metric.clickRate !== undefined && (
                    <div>
                      <p
                        style={{
                          margin: 0,
                          color: '#a8bed0',
                          fontSize: 11,
                        }}
                      >
                        Click Rate
                      </p>
                      <p
                        style={{
                          margin: '4px 0 0 0',
                          fontSize: 14,
                          fontWeight: 600,
                          color: '#60a5fa',
                        }}
                      >
                        {formatPercent(metric.clickRate)}
                      </p>
                    </div>
                  )}

                  {/* Unsubscribe Rate */}
                  {metric.unsubscribeRate !== undefined && (
                    <div>
                      <p
                        style={{
                          margin: 0,
                          color: '#a8bed0',
                          fontSize: 11,
                        }}
                      >
                        Unsubscribe Rate
                      </p>
                      <p
                        style={{
                          margin: '4px 0 0 0',
                          fontSize: 14,
                          fontWeight: 600,
                          color: '#f87171',
                        }}
                      >
                        {formatPercent(metric.unsubscribeRate)}
                      </p>
                    </div>
                  )}

                  {/* Bounce Rate */}
                  {metric.bounceRate !== undefined && (
                    <div>
                      <p
                        style={{
                          margin: 0,
                          color: '#a8bed0',
                          fontSize: 11,
                        }}
                      >
                        Bounce Rate
                      </p>
                      <p
                        style={{
                          margin: '4px 0 0 0',
                          fontSize: 14,
                          fontWeight: 600,
                          color: '#fb7185',
                        }}
                      >
                        {formatPercent(metric.bounceRate)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <p
          style={{
            margin: '16px 0 0 0',
            fontSize: 11,
            color: '#6b7280',
            textAlign: 'right',
          }}
        >
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}

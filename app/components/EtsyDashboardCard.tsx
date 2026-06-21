'use client';

import { useState, useEffect } from 'react';

interface EtsyMetrics {
  status: 'connected' | 'disconnected' | 'error';
  activeListings: number;
  revenue30d: number;
  today: number;
  trend: 'up' | 'down' | 'flat';
  lastSync: string;
  inventorySyncHealth: number;
  productsCreated: number;
  ordersTracked: number;
}

const MOCK_METRICS: EtsyMetrics = {
  status: 'connected',
  activeListings: 12,
  revenue30d: 523.45,
  today: 45.32,
  trend: 'up',
  lastSync: '12m ago',
  inventorySyncHealth: 94,
  productsCreated: 12,
  ordersTracked: 38,
};

export function EtsyDashboardCard() {
  const [metrics, setMetrics] = useState<EtsyMetrics>(MOCK_METRICS);
  const [loading, setLoading] = useState(false);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/automation/etsy', {
        headers: {
          Authorization: `Bearer ${process.env.NEXT_PUBLIC_AUTOMATION_TOKEN || ''}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.configured?.etsy && data.configured?.printify) {
          setMetrics(prev => ({
            ...prev,
            status: 'connected',
          }));
        }
      }
    } catch (error) {
      console.warn('Failed to fetch Etsy metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const statusColor =
    metrics.status === 'connected'
      ? '#00ff88'
      : metrics.status === 'error'
        ? '#ff4444'
        : '#666';

  const trendColor = metrics.trend === 'up' ? '#00ff88' : metrics.trend === 'down' ? '#ff4444' : '#666';

  return (
    <div
      style={{
        background: '#111',
        border: '1px solid #1e1e1e',
        borderRadius: 8,
        padding: '16px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Accent bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 3,
          height: '100%',
          background: statusColor,
        }}
      />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <p
            style={{
              color: '#555',
              fontSize: 10,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              margin: '0 0 6px',
              fontWeight: 600,
            }}
          >
            Etsy + Printify
          </p>
          <p style={{ color: '#f0f0f0', fontSize: 18, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            ${metrics.revenue30d.toFixed(2)}
          </p>
          <p style={{ color: statusColor, fontSize: 11, margin: '3px 0 0', opacity: 0.85 }}>
            30d revenue
          </p>
        </div>

        {/* Status badge */}
        <span
          style={{
            padding: '4px 10px',
            borderRadius: 14,
            fontSize: 9,
            fontWeight: 700,
            background: statusColor + '20',
            color: statusColor,
            border: `1px solid ${statusColor}40`,
            textTransform: 'uppercase',
          }}
        >
          {metrics.status === 'connected' ? '● LIVE' : '◌ OFFLINE'}
        </span>
      </div>

      {/* Quick metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
        {/* Active Listings */}
        <div
          style={{
            background: '#0a0a0a',
            border: '1px solid #141414',
            borderRadius: 6,
            padding: '8px 10px',
          }}
        >
          <p style={{ color: '#666', fontSize: 9, margin: '0 0 3px', textTransform: 'uppercase' }}>
            Listings
          </p>
          <p style={{ color: '#e0e0e0', fontSize: 14, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            {metrics.activeListings}
          </p>
        </div>

        {/* Today */}
        <div
          style={{
            background: '#0a0a0a',
            border: '1px solid #141414',
            borderRadius: 6,
            padding: '8px 10px',
          }}
        >
          <p style={{ color: '#666', fontSize: 9, margin: '0 0 3px', textTransform: 'uppercase' }}>
            Today
          </p>
          <p style={{ color: '#00ff88', fontSize: 14, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            +${metrics.today.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Inventory Sync Health Bar */}
      <div style={{ marginBottom: 10 }}>
        <p
          style={{
            color: '#666',
            fontSize: 9,
            margin: '0 0 4px',
            textTransform: 'uppercase',
            fontWeight: 600,
          }}
        >
          Sync Health
        </p>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <div
            style={{
              flex: 1,
              height: 5,
              background: '#1e1e1e',
              borderRadius: 3,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: metrics.inventorySyncHealth + '%',
                height: '100%',
                background: metrics.inventorySyncHealth >= 90 ? '#00ff88' : '#ffcc00',
              }}
            />
          </div>
          <span
            style={{
              color: metrics.inventorySyncHealth >= 90 ? '#00ff88' : '#ffcc00',
              fontSize: 10,
              width: 32,
              textAlign: 'right' as const,
              fontFamily: 'monospace',
            }}
          >
            {metrics.inventorySyncHealth}%
          </span>
        </div>
      </div>

      {/* Stats table */}
      <table
        style={{
          width: '100%',
          fontSize: 11,
          borderCollapse: 'collapse' as const,
          marginBottom: 10,
        }}
      >
        <tbody>
          {[
            { label: 'Products Created', value: metrics.productsCreated.toString() },
            { label: 'Orders Tracked', value: metrics.ordersTracked.toString() },
            { label: 'Last Sync', value: metrics.lastSync, color: '#00aaff' },
          ].map((item, i) => (
            <tr
              key={item.label}
              style={{
                borderBottom: i < 2 ? '1px solid #141414' : 'none',
              }}
            >
              <td
                style={{
                  color: '#666',
                  padding: '5px 0',
                  textAlign: 'left' as const,
                }}
              >
                {item.label}
              </td>
              <td
                style={{
                  color: item.color || '#e0e0e0',
                  padding: '5px 0',
                  textAlign: 'right' as const,
                  fontFamily: 'monospace',
                  fontWeight: 600,
                }}
              >
                {item.value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Trend indicator */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 10px',
          background: '#0a0a0a',
          borderRadius: 6,
          justifyContent: 'center',
        }}
      >
        <span
          style={{
            color: trendColor,
            fontSize: 14,
          }}
        >
          {metrics.trend === 'up' ? '▲' : metrics.trend === 'down' ? '▼' : '→'}
        </span>
        <span
          style={{
            color: '#999',
            fontSize: 10,
          }}
        >
          {metrics.trend === 'up' ? 'Growing' : metrics.trend === 'down' ? 'Declining' : 'Stable'}
        </span>
      </div>

      {/* Loading state */}
      {loading && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 8,
          }}
        >
          <span style={{ color: '#666', fontSize: 12 }}>Loading...</span>
        </div>
      )}
    </div>
  );
}

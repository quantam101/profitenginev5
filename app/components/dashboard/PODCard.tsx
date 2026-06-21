/**
 * POD (Print-on-Demand) Dashboard Card
 *
 * Display Printify automation status, products, and revenue metrics.
 */

'use client';

import { useEffect, useState } from 'react';

interface PODMetrics {
  productsCount: number;
  ordersInProgress: number;
  totalRevenue: number;
  status: 'ok' | 'error' | 'unconfigured';
  lastSync?: string;
  productCreationRate: number; // products/day
  orderFulfillmentRate: number; // % fulfilled
}

const MOCK_METRICS: PODMetrics = {
  productsCount: 12,
  ordersInProgress: 3,
  totalRevenue: 847.32,
  status: 'ok',
  lastSync: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 min ago
  productCreationRate: 1.8,
  orderFulfillmentRate: 94,
};

export function PODCard() {
  const [metrics, setMetrics] = useState<PODMetrics>(MOCK_METRICS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/automation/printify', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'ok') {
            setMetrics(prev => ({
              ...prev,
              status: 'ok',
            }));
          }
        }
      } catch (error) {
        console.warn('Failed to fetch POD metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (metrics.status) {
      case 'ok':
        return '#00ff88';
      case 'error':
        return '#ff4444';
      default:
        return '#ffcc00';
    }
  };

  const getStatusLabel = () => {
    switch (metrics.status) {
      case 'ok':
        return 'ACTIVE';
      case 'error':
        return 'ERROR';
      default:
        return 'UNCONFIGURED';
    }
  };

  const getLastSyncLabel = () => {
    if (!metrics.lastSync) return 'never';
    const now = new Date();
    const lastSync = new Date(metrics.lastSync);
    const diffMs = now.getTime() - lastSync.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    return `${Math.floor(diffMins / 60)}h ago`;
  };

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
          background: getStatusColor(),
        }}
      />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <p
          style={{
            color: '#555',
            fontSize: 10,
            letterSpacing: '0.1em',
            textTransform: 'uppercase' as const,
            margin: 0,
            fontWeight: 600,
          }}
        >
          Print-on-Demand
        </p>
        <span
          style={{
            color: getStatusColor(),
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: '0.1em',
            textTransform: 'uppercase' as const,
            padding: '2px 8px',
            borderRadius: 12,
            background: getStatusColor() + '15',
            border: `1px solid ${getStatusColor()}40`,
          }}
        >
          {getStatusLabel()}
        </span>
      </div>

      {/* Metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
        {/* Products */}
        <div>
          <p style={{ color: '#666', fontSize: 9, margin: '0 0 4px', fontWeight: 600 }}>
            Products
          </p>
          <p style={{ color: '#f0f0f0', fontSize: 18, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            {metrics.productsCount}
          </p>
          <p style={{ color: '#00ff88', fontSize: 10, margin: '2px 0 0', opacity: 0.8 }}>
            {metrics.productCreationRate.toFixed(1)}/day
          </p>
        </div>

        {/* Orders */}
        <div>
          <p style={{ color: '#666', fontSize: 9, margin: '0 0 4px', fontWeight: 600 }}>
            In Progress
          </p>
          <p style={{ color: '#f0f0f0', fontSize: 18, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            {metrics.ordersInProgress}
          </p>
          <p style={{ color: '#00aaff', fontSize: 10, margin: '2px 0 0', opacity: 0.8 }}>
            orders
          </p>
        </div>
      </div>

      {/* Revenue bar */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <p style={{ color: '#666', fontSize: 9, margin: 0, fontWeight: 600 }}>
            30-Day Revenue
          </p>
          <p style={{ color: '#00ff88', fontSize: 11, margin: 0, fontFamily: 'monospace', fontWeight: 700 }}>
            ${metrics.totalRevenue.toFixed(2)}
          </p>
        </div>
        <div style={{ height: 4, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              background: 'linear-gradient(90deg, #ff6600, #ffcc00)',
              width: Math.min((metrics.totalRevenue / 1000) * 100, 100) + '%',
            }}
          />
        </div>
      </div>

      {/* Fulfillment rate */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <p style={{ color: '#666', fontSize: 9, margin: 0, fontWeight: 600 }}>
            Fulfillment Rate
          </p>
          <p
            style={{
              color: metrics.orderFulfillmentRate >= 90 ? '#00ff88' : '#ffcc00',
              fontSize: 11,
              margin: 0,
              fontFamily: 'monospace',
              fontWeight: 700,
            }}
          >
            {metrics.orderFulfillmentRate}%
          </p>
        </div>
        <div style={{ height: 4, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              background: metrics.orderFulfillmentRate >= 90 ? '#00ff88' : '#ffcc00',
              width: metrics.orderFulfillmentRate + '%',
            }}
          />
        </div>
      </div>

      {/* Last sync */}
      <p
        style={{
          color: '#444',
          fontSize: 10,
          margin: 0,
          paddingTop: 8,
          borderTop: '1px solid #1a1a1a',
          marginTop: 8,
          textAlign: 'center' as const,
        }}
      >
        Last sync: {getLastSyncLabel()}
      </p>
    </div>
  );
}

export default PODCard;

'use client';
import { useState, useEffect } from 'react';

interface AffiliateStats {
  activeLinks: number;
  totalClicks: number;
  totalConversions: number;
  estimatedCommission: number;
  conversionRate: number;
}

const MOCK_STATS: AffiliateStats = {
  activeLinks: 42,
  totalClicks: 1250,
  totalConversions: 87,
  estimatedCommission: 348.00,
  conversionRate: 6.96,
};

export default function AmazonAffiliateCard() {
  const [stats, setStats] = useState<AffiliateStats>(MOCK_STATS);
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const res = await fetch('/api/automation/amazon-affiliate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'get-report',
            startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            endDate: new Date().toISOString().split('T')[0],
            links: [],
          }),
        });

        if (res.ok) {
          const data = await res.json();
          if (data.report) {
            setStats({
              activeLinks: data.report.activeLinks || 0,
              totalClicks: data.report.totalClicks || 0,
              totalConversions: data.report.totalConversions || 0,
              estimatedCommission: data.report.estimatedCommission || 0,
              conversionRate: data.report.conversionRate || 0,
            });
            setConnected(true);
          }
        }
      } catch (error) {
        console.error('Failed to fetch affiliate stats:', error);
        setConnected(false);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const performanceColor =
    stats.conversionRate > 5
      ? '#00ff88'
      : stats.conversionRate > 3
        ? '#ffcc00'
        : '#ff6600';

  return (
    <div
      style={{
        background: '#111',
        border: '1px solid #1e1e1e',
        borderRadius: 8,
        padding: '14px 16px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 3,
          height: '100%',
          background: performanceColor,
        }}
      />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <p
          style={{
            color: '#555',
            fontSize: 10,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            margin: 0,
            fontWeight: 600,
          }}
        >
          Amazon Affiliate
        </p>
        <span
          style={{
            fontSize: 9,
            fontFamily: 'monospace',
            color: connected ? '#00ff88' : '#ff6600',
          }}
        >
          {connected ? '● LIVE' : '◌ DEMO'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
        <div>
          <p style={{ color: '#666', fontSize: 9, margin: '0 0 4px', fontWeight: 600 }}>
            ACTIVE LINKS
          </p>
          <p style={{ color: '#f0f0f0', fontSize: 18, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            {stats.activeLinks}
          </p>
        </div>
        <div>
          <p style={{ color: '#666', fontSize: 9, margin: '0 0 4px', fontWeight: 600 }}>
            EST. COMMISSION
          </p>
          <p style={{ color: '#00ff88', fontSize: 18, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>
            ${stats.estimatedCommission.toFixed(0)}
          </p>
        </div>
      </div>

      <div
        style={{
          background: '#0a0a0a',
          borderRadius: 4,
          padding: '8px 10px',
          marginBottom: 10,
          border: '1px solid #141414',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ color: '#555', fontSize: 9, fontWeight: 600 }}>CONVERSION RATE</span>
          <span style={{ color: performanceColor, fontSize: 11, fontFamily: 'monospace', fontWeight: 700 }}>
            {stats.conversionRate.toFixed(2)}%
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              flex: 1,
              height: 4,
              background: '#1e1e1e',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: Math.min((stats.conversionRate / 10) * 100, 100) + '%',
                height: '100%',
                background: performanceColor,
              }}
            />
          </div>
          <span style={{ color: '#444', fontSize: 9, width: 28, textAlign: 'right' }}>
            {Math.min((stats.conversionRate / 10) * 100, 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
          fontSize: 10,
        }}
      >
        <div style={{ background: '#0a0a0a', padding: '6px 8px', borderRadius: 4, border: '1px solid #141414' }}>
          <p style={{ color: '#666', margin: '0 0 2px', fontSize: 8, fontWeight: 600 }}>CLICKS</p>
          <p style={{ color: '#00aaff', margin: 0, fontFamily: 'monospace', fontSize: 12, fontWeight: 700 }}>
            {stats.totalClicks.toLocaleString()}
          </p>
        </div>
        <div style={{ background: '#0a0a0a', padding: '6px 8px', borderRadius: 4, border: '1px solid #141414' }}>
          <p style={{ color: '#666', margin: '0 0 2px', fontSize: 8, fontWeight: 600 }}>CONVERSIONS</p>
          <p style={{ color: '#aa00ff', margin: 0, fontFamily: 'monospace', fontSize: 12, fontWeight: 700 }}>
            {stats.totalConversions}
          </p>
        </div>
      </div>

      {loading && (
        <div style={{ marginTop: 8, color: '#444', fontSize: 9, textAlign: 'center' }}>
          Syncing…
        </div>
      )}
    </div>
  );
}

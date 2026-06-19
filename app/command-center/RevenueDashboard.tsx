'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface RevenueMetrics {
  timestamp: string;
  monthYear: string;
  mrr: number;
  arr: number;
  ltv: number;
  churnRate: number;
  cogs: number;
  netProfitMargin: number;
  totalCustomers: number;
  payingCustomers: number;
  freeCustomers: number;
  newCustomersThisMonth: number;
  avgCustomerBalance: number;
  tierBreakdown: {
    free: number;
    hybrid: number;
    whiteLable: number;
    enterprise: number;
  };
  revenueByTier: {
    free: number;
    hybrid: number;
    whiteLable: number;
    enterprise: number;
  };
  monthlyTrend: Array<{
    month: string;
    mrr: number;
    customers: number;
    churnRate: number;
  }>;
  topCustomers: Array<{
    userId: number;
    email: string;
    tier: string;
    balance: number;
    monthlyRevenue: number;
    ltv: number;
  }>;
  health: {
    dataQuality: string;
    lastUpdate: string;
    recordsProcessed: number;
  };
}

interface MetricCardProps {
  label: string;
  value: string | number;
  detail?: string;
  type?: 'positive' | 'negative' | 'neutral' | 'warning';
  icon?: string;
}

const MetricCard = ({ label, value, detail, type = 'neutral', icon }: MetricCardProps) => {
  const colorMap = {
    positive: '#4ade80',
    negative: '#f87171',
    neutral: '#7dd3fc',
    warning: '#facc15',
  };

  const bgColorMap = {
    positive: 'rgba(74, 222, 128, 0.1)',
    negative: 'rgba(248, 113, 113, 0.1)',
    neutral: 'rgba(125, 211, 252, 0.1)',
    warning: 'rgba(250, 204, 21, 0.1)',
  };

  return (
    <div
      style={{
        border: `1px solid ${colorMap[type]}33`,
        borderRadius: 12,
        padding: 20,
        background: bgColorMap[type],
        minHeight: 140,
      }}
    >
      <p style={{ color: '#a8bed0', fontSize: 12, margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: 1 }}>
        {icon && <span style={{ marginRight: 8 }}>{icon}</span>}
        {label}
      </p>
      <p style={{ color: colorMap[type], fontSize: 32, fontWeight: 700, margin: '8px 0', lineHeight: 1 }}>
        {typeof value === 'number' && value > 1000 && label.includes('$')
          ? `$${(value / 1000).toFixed(1)}k`
          : typeof value === 'number' && label.includes('%')
          ? `${value.toFixed(1)}%`
          : typeof value === 'number'
          ? value.toLocaleString()
          : value}
      </p>
      {detail && <p style={{ color: '#7dd3fc', fontSize: 12, margin: 0 }}>{detail}</p>}
    </div>
  );
};

const PieChart = ({
  title,
  data,
}: {
  title: string;
  data: { label: string; value: number; color: string }[];
}) => {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let currentAngle = 0;
  const radius = 40;
  const centerX = 60;
  const centerY = 60;

  const slices = data.map((d, i) => {
    const sliceAngle = (d.value / total) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + sliceAngle;

    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const x1 = centerX + radius * Math.cos(startRad);
    const y1 = centerY + radius * Math.sin(startRad);
    const x2 = centerX + radius * Math.cos(endRad);
    const y2 = centerY + radius * Math.sin(endRad);

    const largeArc = sliceAngle > 180 ? 1 : 0;

    const pathData = [
      `M ${centerX} ${centerY}`,
      `L ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
      'Z',
    ].join(' ');

    currentAngle = endAngle;

    return (
      <path key={i} d={pathData} fill={d.color} opacity={0.8} />
    );
  });

  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ color: '#e5f7ff', marginBottom: 12, fontSize: 18 }}>{title}</h3>
      <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start' }}>
        <svg
          viewBox="0 0 120 120"
          style={{ width: 200, height: 200 }}
          xmlns="http://www.w3.org/2000/svg"
        >
          {slices}
          <circle cx={centerX} cy={centerY} r={20} fill="#080b12" />
        </svg>
        <div style={{ flex: 1 }}>
          {data.map((d, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                marginBottom: 12,
                color: '#e5f7ff',
              }}
            >
              <div
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: 3,
                  background: d.color,
                }}
              />
              <span>{d.label}</span>
              <span style={{ color: '#7dd3fc', marginLeft: 'auto' }}>
                {Math.round((d.value / total) * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const TrendChart = ({
  title,
  data,
  valueLabel,
}: {
  title: string;
  data: Array<{ month: string; value: number }>;
  valueLabel: string;
}) => {
  if (data.length === 0) return null;

  const maxValue = Math.max(...data.map(d => d.value));
  const chartHeight = 200;
  const barWidth = Math.max(30, 300 / data.length);

  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ color: '#e5f7ff', marginBottom: 12, fontSize: 18 }}>{title}</h3>
      <div style={{ overflowX: 'auto', paddingBottom: 16 }}>
        <div
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'flex-end',
            height: chartHeight + 40,
            minWidth: 'min-content',
          }}
        >
          {data.map((d, i) => {
            const barHeight = (d.value / maxValue) * chartHeight;
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    width: barWidth,
                    height: barHeight,
                    background: '#7dd3fc',
                    borderRadius: '4px 4px 0 0',
                    opacity: 0.8,
                  }}
                  title={`${d.month}: ${d.value}`}
                />
                <span style={{ color: '#a8bed0', fontSize: 12, width: barWidth, textAlign: 'center' }}>
                  {d.month}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const LeaderboardTable = ({
  title,
  headers,
  rows,
}: {
  title: string;
  headers: string[];
  rows: any[];
}) => {
  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ color: '#e5f7ff', marginBottom: 12, fontSize: 18 }}>{title}</h3>
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            color: '#e5f7ff',
            fontSize: 13,
          }}
        >
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(125, 211, 252, 0.25)' }}>
              {headers.map((h, i) => (
                <th
                  key={i}
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    color: '#7dd3fc',
                    fontWeight: 600,
                    fontSize: 12,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                style={{
                  borderBottom: '1px solid rgba(125, 211, 252, 0.1)',
                }}
              >
                {Object.values(row).map((cell, j) => (
                  <td
                    key={j}
                    style={{
                      padding: '12px 8px',
                      color: '#e5f7ff',
                    }}
                  >
                    {typeof cell === 'number'
                      ? cell > 1000 && cell !== Math.floor(cell)
                        ? `$${(cell / 1000).toFixed(1)}k`
                        : cell.toLocaleString()
                      : (cell as React.ReactNode)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default function RevenueDashboard() {
  const [metrics, setMetrics] = useState<RevenueMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/command/revenue', { cache: 'no-store' });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();
      setMetrics(data);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Failed to fetch metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchMetrics();
  }, []);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(fetchMetrics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleExportCsv = () => {
    if (!metrics) return;

    const csv = [
      ['Already Here LLC - Revenue Metrics Export', new Date().toISOString()],
      [],
      ['KEY PERFORMANCE INDICATORS'],
      ['Monthly Recurring Revenue (MRR)', `$${metrics.mrr.toFixed(2)}`],
      ['Annual Recurring Revenue (ARR)', `$${metrics.arr.toFixed(2)}`],
      ['Customer Lifetime Value (LTV)', `$${metrics.ltv.toFixed(2)}`],
      ['Churn Rate', `${metrics.churnRate.toFixed(2)}%`],
      ['Cost of Goods Sold (COGS)', `$${metrics.cogs.toFixed(2)}`],
      ['Net Profit Margin', `${metrics.netProfitMargin.toFixed(2)}%`],
      [],
      ['CUSTOMER METRICS'],
      ['Total Customers', metrics.totalCustomers],
      ['Paying Customers', metrics.payingCustomers],
      ['Free Customers', metrics.freeCustomers],
      ['New Customers This Month', metrics.newCustomersThisMonth],
      ['Average Customer Balance', `$${metrics.avgCustomerBalance.toFixed(2)}`],
      [],
      ['TIER BREAKDOWN - CUSTOMER COUNT'],
      ['Free', metrics.tierBreakdown.free],
      ['Hybrid', metrics.tierBreakdown.hybrid],
      ['White Label', metrics.tierBreakdown.whiteLable],
      ['Enterprise', metrics.tierBreakdown.enterprise],
      [],
      ['REVENUE BY TIER'],
      ['Free', `$${metrics.revenueByTier.free.toFixed(2)}`],
      ['Hybrid', `$${metrics.revenueByTier.hybrid.toFixed(2)}`],
      ['White Label', `$${metrics.revenueByTier.whiteLable.toFixed(2)}`],
      ['Enterprise', `$${metrics.revenueByTier.enterprise.toFixed(2)}`],
      [],
      ['TOP 10 CUSTOMERS'],
      ['User ID', 'Email', 'Tier', 'Balance', 'Monthly Revenue', 'LTV'],
      ...metrics.topCustomers.map(c => [
        c.userId,
        c.email,
        c.tier,
        `$${c.balance.toFixed(2)}`,
        `$${c.monthlyRevenue.toFixed(2)}`,
        `$${c.ltv.toFixed(2)}`,
      ]),
    ]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `revenue-metrics-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleManualRefresh = () => {
    fetchMetrics();
  };

  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#080b12',
        color: '#e5f7ff',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
        padding: '32px',
      }}
    >
      <section style={{ maxWidth: 1280, margin: '0 auto' }}>
        {/* Navigation */}
        <nav style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 56 }}>
          <Link href="/" style={{ color: '#7dd3fc', textDecoration: 'none', fontWeight: 800 }}>
            ProfitEngine v5
          </Link>
          <div style={{ display: 'flex', gap: 24 }}>
            <Link href="/command-center" style={{ color: '#e5f7ff', textDecoration: 'none' }}>
              Command Center
            </Link>
            <Link href="/command-center/trading" style={{ color: '#e5f7ff', textDecoration: 'none' }}>
              Trading
            </Link>
            <Link href="/command-center/revenue" style={{ color: '#7dd3fc', textDecoration: 'none', fontWeight: 600 }}>
              Revenue
            </Link>
            <Link href="/ai-vp" style={{ color: '#e5f7ff', textDecoration: 'none' }}>
              AI VP
            </Link>
          </div>
        </nav>

        {/* Header */}
        <header style={{ marginBottom: 36 }}>
          <p style={{ color: '#7dd3fc', textTransform: 'uppercase', letterSpacing: 2, fontSize: 12 }}>
            Business intelligence
          </p>
          <h1 style={{ fontSize: 'clamp(36px, 7vw, 72px)', lineHeight: 1, margin: '16px 0' }}>
            Revenue dashboard
          </h1>
          <p style={{ color: '#a8bed0', maxWidth: 760, fontSize: 18, lineHeight: 1.6 }}>
            Real-time business metrics for Already Here LLC. Tracks MRR, ARR, customer lifetime value, and profitability across all tiers.
          </p>
        </header>

        {/* Refresh controls */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 32, alignItems: 'center' }}>
          <button
            onClick={handleManualRefresh}
            disabled={loading}
            style={{
              padding: '10px 20px',
              background: '#7dd3fc',
              color: '#080b12',
              border: 'none',
              borderRadius: 8,
              fontWeight: 600,
              cursor: 'pointer',
              opacity: loading ? 0.5 : 1,
            }}
          >
            {loading ? 'Refreshing...' : 'Refresh Now'}
          </button>

          <button
            onClick={handleExportCsv}
            disabled={!metrics || loading}
            style={{
              padding: '10px 20px',
              background: 'rgba(125, 211, 252, 0.2)',
              color: '#7dd3fc',
              border: '1px solid #7dd3fc',
              borderRadius: 8,
              fontWeight: 600,
              cursor: 'pointer',
              opacity: !metrics || loading ? 0.5 : 1,
            }}
          >
            Export CSV
          </button>

          {lastRefresh && (
            <span style={{ color: '#a8bed0', fontSize: 12, marginLeft: 'auto' }}>
              Updated: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Error state */}
        {error && (
          <div
            style={{
              background: 'rgba(248, 113, 113, 0.1)',
              border: '1px solid #f87171',
              borderRadius: 12,
              padding: 20,
              marginBottom: 32,
              color: '#f87171',
            }}
          >
            Error: {error}
          </div>
        )}

        {/* Loading state */}
        {loading && !metrics && (
          <div
            style={{
              background: 'rgba(125, 211, 252, 0.1)',
              border: '1px solid #7dd3fc',
              borderRadius: 12,
              padding: 40,
              textAlign: 'center',
              color: '#7dd3fc',
            }}
          >
            Loading revenue metrics...
          </div>
        )}

        {/* Content */}
        {metrics && (
          <>
            {/* KPI Cards */}
            <section style={{ marginBottom: 40 }}>
              <h2 style={{ marginBottom: 20, fontSize: 24, color: '#e5f7ff' }}>Key Performance Indicators</h2>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: 16,
                }}
              >
                <MetricCard
                  label="Monthly Recurring Revenue"
                  value={`$${metrics.mrr.toFixed(2)}`}
                  type="positive"
                  icon="💰"
                />
                <MetricCard
                  label="Annual Recurring Revenue"
                  value={`$${metrics.arr.toFixed(2)}`}
                  type="positive"
                  icon="📈"
                />
                <MetricCard
                  label="Customer Lifetime Value"
                  value={`$${metrics.ltv.toFixed(2)}`}
                  type="positive"
                  icon="👥"
                />
                <MetricCard
                  label="Churn Rate"
                  value={`${metrics.churnRate.toFixed(1)}%`}
                  type={metrics.churnRate > 5 ? 'warning' : 'positive'}
                  icon="📉"
                />
                <MetricCard
                  label="Cost of Goods Sold"
                  value={`$${metrics.cogs.toFixed(2)}`}
                  type="neutral"
                  icon="⚙️"
                />
                <MetricCard
                  label="Net Profit Margin"
                  value={`${metrics.netProfitMargin.toFixed(1)}%`}
                  type={metrics.netProfitMargin > 0 ? 'positive' : 'negative'}
                  icon="💹"
                />
              </div>
            </section>

            {/* Customer Metrics */}
            <section style={{ marginBottom: 40 }}>
              <h2 style={{ marginBottom: 20, fontSize: 24, color: '#e5f7ff' }}>Customer Metrics</h2>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: 16,
                }}
              >
                <MetricCard
                  label="Total Customers"
                  value={metrics.totalCustomers}
                  type="neutral"
                  icon="👥"
                />
                <MetricCard
                  label="Paying Customers"
                  value={metrics.payingCustomers}
                  type="positive"
                  icon="💳"
                />
                <MetricCard
                  label="Free Customers"
                  value={metrics.freeCustomers}
                  type="neutral"
                  icon="🎁"
                />
                <MetricCard
                  label="New This Month"
                  value={metrics.newCustomersThisMonth}
                  type="positive"
                  icon="⭐"
                />
                <MetricCard
                  label="Avg Customer Balance"
                  value={`$${metrics.avgCustomerBalance.toFixed(0)}`}
                  type="neutral"
                  icon="💼"
                />
              </div>
            </section>

            {/* Charts Section */}
            <section style={{ marginBottom: 40 }}>
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.72)',
                  border: '1px solid rgba(125, 211, 252, 0.25)',
                  borderRadius: 12,
                  padding: 24,
                }}
              >
                {/* Tier Breakdown Pie Chart */}
                <PieChart
                  title="Customers by Tier"
                  data={[
                    { label: 'Free', value: metrics.tierBreakdown.free, color: '#94a3b8' },
                    { label: 'Hybrid', value: metrics.tierBreakdown.hybrid, color: '#3b82f6' },
                    { label: 'White Label', value: metrics.tierBreakdown.whiteLable, color: '#8b5cf6' },
                    { label: 'Enterprise', value: metrics.tierBreakdown.enterprise, color: '#ec4899' },
                  ]}
                />

                {/* Revenue by Tier Pie Chart */}
                <PieChart
                  title="Revenue Distribution by Tier"
                  data={[
                    { label: 'Free', value: metrics.revenueByTier.free, color: '#94a3b8' },
                    { label: 'Hybrid', value: metrics.revenueByTier.hybrid, color: '#3b82f6' },
                    { label: 'White Label', value: metrics.revenueByTier.whiteLable, color: '#8b5cf6' },
                    { label: 'Enterprise', value: metrics.revenueByTier.enterprise, color: '#ec4899' },
                  ]}
                />

                {/* Monthly Trend Chart */}
                <TrendChart
                  title="MRR Trend"
                  data={metrics.monthlyTrend.map(m => ({
                    month: m.month,
                    value: m.mrr,
                  }))}
                  valueLabel="MRR"
                />
              </div>
            </section>

            {/* Top Customers Table */}
            <section style={{ marginBottom: 40 }}>
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.72)',
                  border: '1px solid rgba(125, 211, 252, 0.25)',
                  borderRadius: 12,
                  padding: 24,
                }}
              >
                <LeaderboardTable
                  title="Top 10 Customers by Revenue"
                  headers={['User ID', 'Email', 'Tier', 'Balance', 'Monthly Revenue', 'LTV']}
                  rows={metrics.topCustomers.map(c => ({
                    'User ID': c.userId,
                    Email: c.email.split('@')[0], // Truncate for display
                    Tier: c.tier,
                    Balance: `$${c.balance.toFixed(0)}`,
                    'Monthly Revenue': `$${c.monthlyRevenue.toFixed(2)}`,
                    LTV: `$${c.ltv.toFixed(0)}`,
                  }))}
                />
              </div>
            </section>

            {/* Health Section */}
            <section>
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.72)',
                  border: '1px solid rgba(125, 211, 252, 0.25)',
                  borderRadius: 12,
                  padding: 24,
                }}
              >
                <h2 style={{ marginTop: 0, color: '#e5f7ff', fontSize: 20 }}>Data Health</h2>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                    gap: 16,
                  }}
                >
                  <div>
                    <p style={{ color: '#a8bed0', fontSize: 12, margin: '0 0 8px 0', textTransform: 'uppercase' }}>
                      Data Quality
                    </p>
                    <p style={{ color: '#4ade80', fontSize: 18, fontWeight: 600, margin: 0 }}>
                      {metrics.health.dataQuality}
                    </p>
                  </div>
                  <div>
                    <p style={{ color: '#a8bed0', fontSize: 12, margin: '0 0 8px 0', textTransform: 'uppercase' }}>
                      Records Processed
                    </p>
                    <p style={{ color: '#7dd3fc', fontSize: 18, fontWeight: 600, margin: 0 }}>
                      {metrics.health.recordsProcessed.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p style={{ color: '#a8bed0', fontSize: 12, margin: '0 0 8px 0', textTransform: 'uppercase' }}>
                      Last Updated
                    </p>
                    <p style={{ color: '#7dd3fc', fontSize: 12, margin: 0 }}>
                      {new Date(metrics.health.lastUpdate).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </section>
          </>
        )}
      </section>
    </main>
  );
}

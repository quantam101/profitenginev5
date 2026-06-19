'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';

interface DashboardMetrics {
  active_traders_today: number;
  top_performers_by_win_rate: Array<{
    rank: number;
    user_id: string;
    username: string;
    win_rate: number;
    total_pnl: number;
    total_trades: number;
  }>;
  biggest_gainers: Array<{
    rank: number;
    user_id: string;
    username: string;
    pnl_percent: number;
    total_pnl: number;
    total_trades: number;
  }>;
  new_signups_today: number;
  avg_daily_pnl: number;
  upsell_candidates: Array<{
    user_id: string;
    username: string;
    current_pnl: number;
    win_rate: number;
    total_trades: number;
    days_active: number;
    urgency: string;
  }>;
  timestamp: string;
  summary: {
    total_trades_today: number;
    total_pnl_today: number;
    total_active_traders: number;
  };
}

interface MetricCardProps {
  label: string;
  value: string | number;
  detail?: string;
  type?: 'positive' | 'negative' | 'neutral';
}

type TableRow = Record<string, ReactNode>;

const MetricCard = ({ label, value, detail, type = 'neutral' }: MetricCardProps) => {
  const colorClass =
    type === 'positive'
      ? '#4ade80'
      : type === 'negative'
        ? '#f87171'
        : '#7dd3fc';

  return (
    <div
      style={{
        border: '1px solid rgba(125, 211, 252, 0.25)',
        borderRadius: 12,
        padding: 20,
        background: 'rgba(15, 23, 42, 0.72)',
        minHeight: 140,
      }}
    >
      <p style={{ color: '#a8bed0', fontSize: 12, margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: 1 }}>
        {label}
      </p>
      <p style={{ color: colorClass, fontSize: 32, fontWeight: 700, margin: '8px 0', lineHeight: 1 }}>
        {value}
      </p>
      {detail && <p style={{ color: '#7dd3fc', fontSize: 12, margin: 0 }}>{detail}</p>}
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
  rows: TableRow[];
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
              {headers.map((header) => (
                <th
                  key={header}
                  style={{
                    padding: '12px 16px',
                    textAlign: 'left',
                    color: '#7dd3fc',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    fontSize: 11,
                    letterSpacing: 0.5,
                  }}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const entries = Object.entries(row);
              const rowKey = entries.map(([key, value]) => `${key}:${String(value)}`).join('|');

              return (
                <tr
                  key={rowKey}
                  style={{
                    borderBottom: '1px solid rgba(125, 211, 252, 0.1)',
                  }}
                >
                  {entries.map(([key, cell], cellIndex) => (
                    <td
                      key={`${rowKey}:${key}`}
                      style={{
                        padding: '12px 16px',
                        textAlign: cellIndex === 0 ? 'left' : 'right',
                      }}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default function TradingDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/trading-dashboard', {
        cache: 'no-store',
      });
      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }
      const data = (await res.json()) as DashboardMetrics;
      setMetrics(data);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !metrics) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#080b12',
          color: '#e5f7ff',
          fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          padding: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <p style={{ color: '#a8bed0', fontSize: 16 }}>Loading trading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#080b12',
          color: '#e5f7ff',
          fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          padding: '32px',
        }}
      >
        <section style={{ maxWidth: 1040, margin: '0 auto' }}>
          <div
            style={{
              border: '1px solid rgba(248, 113, 113, 0.5)',
              borderRadius: 18,
              padding: 24,
              background: 'rgba(127, 29, 29, 0.15)',
            }}
          >
            <h2 style={{ color: '#f87171', margin: '0 0 12px 0' }}>Dashboard Error</h2>
            <p style={{ color: '#a8bed0', margin: 0 }}>{error}</p>
          </div>
        </section>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

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
        <header style={{ marginBottom: 36 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: '#7dd3fc', textTransform: 'uppercase', letterSpacing: 2, fontSize: 12, margin: 0 }}>
                ProfitEngine trading analytics
              </p>
              <h1 style={{ fontSize: 'clamp(32px, 5vw, 56px)', lineHeight: 1, margin: '12px 0 0 0' }}>
                Trading Dashboard
              </h1>
            </div>
            <div style={{ textAlign: 'right', fontSize: 12, color: '#a8bed0' }}>
              {lastUpdate && <p>Updated: {lastUpdate.toLocaleTimeString()}</p>}
              <button
                onClick={fetchData}
                disabled={loading}
                style={{
                  background: 'rgba(125, 211, 252, 0.1)',
                  border: '1px solid rgba(125, 211, 252, 0.25)',
                  color: '#7dd3fc',
                  padding: '8px 16px',
                  borderRadius: 6,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.5 : 1,
                  marginTop: 8,
                  fontSize: 12,
                }}
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
          <MetricCard
            label="Active Traders Today"
            value={metrics.summary.total_active_traders}
            detail={`${metrics.active_traders_today} trading now`}
            type="positive"
          />
          <MetricCard
            label="Total Trades Today"
            value={metrics.summary.total_trades_today}
            detail="Across all traders"
            type="neutral"
          />
          <MetricCard
            label="Daily P&L Total"
            value={`$${metrics.summary.total_pnl_today.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
            type={metrics.summary.total_pnl_today >= 0 ? 'positive' : 'negative'}
          />
          <MetricCard
            label="Avg P&L per Trade"
            value={`$${metrics.avg_daily_pnl.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
            type={metrics.avg_daily_pnl >= 0 ? 'positive' : 'negative'}
          />
        </div>

        <LeaderboardTable
          title="Top 5 Performers (Win Rate)"
          headers={['Rank', 'Trader', 'Win Rate', 'P&L', 'Trades']}
          rows={metrics.top_performers_by_win_rate.map((performer) => ({
            rank: performer.rank,
            trader: performer.username,
            winRate: `${performer.win_rate.toFixed(1)}%`,
            pnl: `$${performer.total_pnl.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
            trades: performer.total_trades,
          }))}
        />

        <LeaderboardTable
          title="Top 5 Biggest Gainers (P&L %)"
          headers={['Rank', 'Trader', 'Gain %', 'Total P&L', 'Trades']}
          rows={metrics.biggest_gainers.map((gainer) => ({
            rank: gainer.rank,
            trader: gainer.username,
            gainPercent: `${gainer.pnl_percent.toFixed(1)}%`,
            pnl: `$${gainer.total_pnl.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
            trades: gainer.total_trades,
          }))}
        />

        {metrics.upsell_candidates.length > 0 && (
          <LeaderboardTable
            title="Upsell Candidates (Premium Ready)"
            headers={['Trader', 'P&L', 'Win Rate', 'Trades', 'Days Active', 'Urgency']}
            rows={metrics.upsell_candidates.map((candidate) => ({
              trader: candidate.username,
              pnl: `$${candidate.current_pnl.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
              winRate: `${candidate.win_rate.toFixed(1)}%`,
              trades: candidate.total_trades,
              daysActive: candidate.days_active,
              urgency: candidate.urgency.toUpperCase(),
            }))}
          />
        )}

        <footer style={{ marginTop: 40, padding: '24px', border: '1px solid rgba(125, 211, 252, 0.1)', borderRadius: 12 }}>
          <p style={{ color: '#a8bed0', fontSize: 12, margin: 0 }}>
            Dashboard updates automatically every 60 seconds. Data is sourced from the live clients database and refreshed on demand.
            Use the Refresh button to get the latest metrics immediately.
          </p>
        </footer>
      </section>
    </main>
  );
}

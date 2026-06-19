'use client';

/**
 * Live Metrics Hero Section
 * Displays real-time trading metrics updated every 5 minutes
 * Pulls from landing_page_generator.py backend
 */

import { useEffect, useState } from 'react';

interface MetricData {
  timestamp: string;
  hero: {
    current_win_rate: string;
    total_users: number;
    weekly_pnl: string;
    total_trades_week: number;
  };
  social_proof: Array<{
    rank: number;
    tier: string;
    win_rate: number;
    pnl_30d: number;
    trade_days: number;
    description: string;
  }>;
  performance: Array<{
    date: string;
    win_rate: number;
    daily_pnl: number;
    total_pnl: number;
    trades_executed: number;
  }>;
  pricing: {
    tier_breakdown: Record<string, number>;
    avg_mrr_by_tier: Record<string, number>;
    total_revenue: string;
  };
  trust: {
    customer_count: number;
    total_pnl_generated: string;
    uptime_percent: string;
    days_profitable: number;
  };
}

interface MetricCardProps {
  value: string | number;
  label: string;
  trend?: string;
}

function MetricCard({ value, label, trend }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
      {trend && <div className="metric-trend">{trend}</div>}
    </div>
  );
}

interface TopPerformerProps {
  rank: number;
  tier: string;
  winRate: number;
  pnl30d: number;
  tradeDays: number;
  description: string;
}

function TopPerformerCard({ rank, tier, winRate, pnl30d, tradeDays, description }: TopPerformerProps) {
  return (
    <div className="performer-card">
      <div className="performer-rank">#{rank} Performer</div>
      <div className="performer-badge">{tier.toUpperCase()}</div>
      <div className="performer-stats">
        <div className="stat">
          Win Rate: <span className="stat-value">{winRate.toFixed(1)}%</span>
        </div>
        <div className="stat">
          30-Day P&L: <span className="stat-value">${pnl30d.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
        </div>
        <div className="stat">
          Trading Days: <span className="stat-value">{tradeDays}</span>
        </div>
      </div>
      <div className="performer-description">&quot;{description}&quot;</div>
    </div>
  );
}

interface PerformanceChartProps {
  data: Array<{
    date: string;
    daily_pnl: number;
    win_rate: number;
  }>;
}

function PerformanceChart({ data }: PerformanceChartProps) {
  if (!data || data.length === 0) return <div>Loading performance data...</div>;

  const maxPnl = Math.max(...data.map(d => Math.abs(d.daily_pnl))) || 1;

  return (
    <div className="performance-chart">
      <div className="chart-title">7-Day P&L Trend</div>
      <div className="mini-chart">
        {data.map((snapshot, idx) => {
          const heightPercent = (Math.abs(snapshot.daily_pnl) / maxPnl) * 100;
          const dateShort = snapshot.date.split('-')[2];
          const isNegative = snapshot.daily_pnl < 0;

          return (
            <div
              key={idx}
              className={`bar ${isNegative ? 'bar-negative' : ''}`}
              style={{ height: `${Math.max(10, heightPercent)}%` }}
              title={`${snapshot.date}: $${snapshot.daily_pnl.toFixed(2)}`}
            >
              <div className="bar-label">{dateShort}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface PricingCardProps {
  tierName: string;
  price: number;
  customers: number;
  avgMrr: number;
  isPopular?: boolean;
}

function PricingCard({ tierName, price, customers, avgMrr, isPopular }: PricingCardProps) {
  return (
    <div className={`pricing-card ${isPopular ? 'popular' : ''}`}>
      <div className="pricing-tier-name">{tierName}</div>
      <div className="pricing-price">${price}</div>
      <div className="pricing-customers">{customers.toLocaleString()} customers</div>
      <div className="pricing-mrr">Avg: ${avgMrr.toFixed(0)}/month per customer</div>
      <button className="pricing-button">Learn More</button>
    </div>
  );
}

interface TrustSignalProps {
  number: string | number;
  label: string;
}

function TrustSignal({ number, label }: TrustSignalProps) {
  return (
    <div className="trust-card">
      <div className="trust-number">{number}</div>
      <div className="trust-label">{label}</div>
    </div>
  );
}

export default function LiveMetricsHero() {
  const [metrics, setMetrics] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/landing-metrics');

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        setMetrics(data);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch metrics';
        setError(errorMessage);
        console.error('Error fetching metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchMetrics();

    // Refresh every 5 minutes
    const interval = setInterval(fetchMetrics, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <section className="hero">
        <h1>
          <span className="highlight">Loading</span> Real Metrics...
        </h1>
        <p>Pulling live trading data from our system...</p>
        <div className="metrics-grid">
          <div className="metric-card skeleton" />
          <div className="metric-card skeleton" />
          <div className="metric-card skeleton" />
          <div className="metric-card skeleton" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="hero">
        <h1>
          <span className="highlight">Error</span> Loading Metrics
        </h1>
        <p>{error}</p>
        <p style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
          Check back soon. Metrics are updated every 5 minutes.
        </p>
      </section>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <>
      {/* HERO SECTION */}
      <section className="hero">
        <h1>
          <span className="highlight">Real Results.</span>
          <br />
          Real Metrics.
          <br />
          Real Traders.
        </h1>
        <p>
          See live trading performance from our entire community. No fake numbers,
          no projections—just proven results updated every 5 minutes.
        </p>

        <div className="metrics-grid">
          <MetricCard value={metrics.hero.current_win_rate} label="Today's Win Rate" trend="↑ System performing well" />
          <MetricCard value={metrics.hero.total_users.toLocaleString()} label="Active Community" trend="Growing daily" />
          <MetricCard value={metrics.hero.weekly_pnl} label="Community P&L" trend="Strong momentum" />
          <MetricCard value={metrics.hero.total_trades_week.toLocaleString()} label="Successful Trades" trend="Consistent execution" />
        </div>
      </section>

      {/* SOCIAL PROOF */}
      <section className="social-proof">
        <h2 className="section-title">
          Top <span className="highlight">Performers</span>
        </h2>
        <div className="performers">
          {metrics.social_proof.slice(0, 3).map((performer) => (
            <TopPerformerCard
              key={performer.rank}
              rank={performer.rank}
              tier={performer.tier}
              winRate={performer.win_rate}
              pnl30d={performer.pnl_30d}
              tradeDays={performer.trade_days}
              description={performer.description}
            />
          ))}
        </div>
      </section>

      {/* PERFORMANCE DASHBOARD */}
      <section className="dashboard-preview">
        <h2 className="section-title">
          7-Day <span className="highlight">Performance</span>
        </h2>
        <div className="dashboard-grid">
          <PerformanceChart data={metrics.performance} />

          <div className="performance-stats">
            <div className="chart-title">Key Metrics</div>
            {metrics.performance.length > 0 && (
              <div style={{ marginTop: '2rem' }}>
                <div style={{ margin: '1rem 0' }}>
                  <div style={{ color: 'var(--muted)' }}>Cumulative P&L</div>
                  <div style={{ fontSize: '1.5rem', color: 'var(--primary)', fontWeight: 'bold' }}>
                    ${metrics.performance[metrics.performance.length - 1].total_pnl.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div style={{ margin: '1rem 0' }}>
                  <div style={{ color: 'var(--muted)' }}>Win Rate (7-day avg)</div>
                  <div style={{ fontSize: '1.5rem', color: 'var(--primary)', fontWeight: 'bold' }}>
                    {(metrics.performance.reduce((sum, s) => sum + s.win_rate, 0) / metrics.performance.length).toFixed(1)}%
                  </div>
                </div>
                <div style={{ margin: '1rem 0' }}>
                  <div style={{ color: 'var(--muted)' }}>Total Trades</div>
                  <div style={{ fontSize: '1.5rem', color: 'var(--primary)', fontWeight: 'bold' }}>
                    {metrics.performance.reduce((sum, s) => sum + s.trades_executed, 0).toLocaleString()}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section className="pricing">
        <h2 className="section-title">
          Transparent <span className="highlight">Pricing</span>
        </h2>
        <div className="pricing-grid">
          <PricingCard
            tierName="Free"
            price={0}
            customers={metrics.pricing.tier_breakdown['free'] || 0}
            avgMrr={0}
          />
          <PricingCard
            tierName="Pro"
            price={99}
            customers={metrics.pricing.tier_breakdown['pro'] || 0}
            avgMrr={metrics.pricing.avg_mrr_by_tier['pro'] || 99}
            isPopular
          />
          <PricingCard
            tierName="Elite"
            price={249}
            customers={metrics.pricing.tier_breakdown['elite'] || 0}
            avgMrr={metrics.pricing.avg_mrr_by_tier['elite'] || 249}
          />
        </div>
      </section>

      {/* TRUST SIGNALS */}
      <section className="trust">
        <h2 className="section-title">
          Trust <span className="highlight">Signals</span>
        </h2>
        <div className="trust-grid">
          <TrustSignal number={metrics.trust.customer_count.toLocaleString()} label="Active Traders" />
          <TrustSignal number={metrics.trust.total_pnl_generated} label="Total P&L Generated" />
          <TrustSignal number={metrics.trust.uptime_percent} label="System Uptime" />
          <TrustSignal number={metrics.trust.days_profitable} label="Profitable Days" />
        </div>
      </section>

      {/* UPDATE BADGE */}
      <div style={{ textAlign: 'center', marginTop: '2rem', marginBottom: '2rem' }}>
        <div className="update-badge">
          Last updated: {new Date(metrics.timestamp).toLocaleString()}
        </div>
      </div>
    </>
  );
}

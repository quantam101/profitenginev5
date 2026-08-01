'use client';

import { useEffect, useState } from 'react';
import type { DashboardSummary } from '@/lib/revenue-os/types';

interface SummaryResponse {
  ok: boolean;
  summary?: DashboardSummary;
  error?: string;
}

function formatCurrency(n: number) {
  return `$${Math.round(n).toLocaleString()}`;
}

export default function RevenueOsDashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/revenue-os/dashboard/summary')
      .then(async (res) => {
        const json = (await res.json()) as SummaryResponse;
        if (!res.ok || !json.ok) throw new Error(json.error || `HTTP ${res.status}`);
        setData(json.summary || null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="shell">
      <h1>Revenue OS — Command Dashboard</h1>
      <p className="muted">Live pipeline, follow-ups, and recommended actions.</p>

      {loading && <p className="muted">Loading...</p>}
      {error && <p className="error">{error}</p>}

      {data && (
        <>
          <div className="grid" style={{ marginTop: 24 }}>
            <div className="card">
              <h2>Active Opportunities</h2>
              <p className="muted">{data.activeOpportunities}</p>
            </div>
            <div className="card">
              <h2>Weighted Pipeline</h2>
              <p className="muted">{formatCurrency(data.weightedPipelineValue)}</p>
            </div>
            <div className="card">
              <h2>MRR Potential</h2>
              <p className="muted">{formatCurrency(data.monthlyRecurringPotential)} / mo</p>
            </div>
            <div className="card">
              <h2>Follow-Ups Due Today</h2>
              <p className="muted">{data.followUpsDueToday}</p>
            </div>
            <div className="card">
              <h2>Fast Cash</h2>
              <p className="muted">{data.fastCashOpportunities}</p>
            </div>
            <div className="card">
              <h2>Won This Month</h2>
              <p className="muted">{formatCurrency(data.revenueWonThisMonth)}</p>
            </div>
          </div>

          <section style={{ marginTop: 32 }}>
            <h2>Top Recommended Actions</h2>
            {data.topRecommendedActions.length === 0 && <p className="muted">No actions queued.</p>}
            <div className="play-grid">
              {data.topRecommendedActions.map((action, i) => (
                <div key={i} className="play-card">
                  <h3>{action.title}</h3>
                  <p className="muted">{action.reason}</p>
                  {action.estimatedValue ? <p className="muted">{formatCurrency(action.estimatedValue)}</p> : null}
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginTop: 32 }}>
            <h2>Pipeline by Stage</h2>
            <div className="play-grid">
              {Object.entries(data.pipelineByStage).map(([stage, info]) => (
                <div key={stage} className="play-card">
                  <h3>{stage}</h3>
                  <p className="muted">{info.count} opportunity{info.count === 1 ? '' : 'ies'} · {formatCurrency(info.value)}</p>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginTop: 32 }}>
            <h2>Highest-Scoring Revenue Plays</h2>
            <div className="play-grid">
              {data.highestScoringRevenuePlays.map((play) => (
                <div key={play.recordId} className="play-card">
                  <h3>{play.revenuePlayName}</h3>
                  <p className="muted">{play.lane} · {play.location}</p>
                  <p className="muted">Score: {play.overallScore}</p>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginTop: 32 }}>
            <h2>Follow-Ups Due</h2>
            {data.followUpsDue.length === 0 && <p className="muted">No follow-ups due.</p>}
            <div className="play-grid">
              {data.followUpsDue.map((f) => (
                <div key={f.id} className="play-card">
                  <h3>{f.summary}</h3>
                  <p className="muted">Due {new Date(f.dueDate).toLocaleDateString()} · {f.priority}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}

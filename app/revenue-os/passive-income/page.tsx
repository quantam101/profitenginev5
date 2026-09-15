'use client';

import { useEffect, useMemo, useState } from 'react';

type EngineResponse = Record<string, any>;

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ border: '1px solid #263244', borderRadius: 12, padding: 16, minWidth: 150 }}>
      <div style={{ opacity: 0.65, fontSize: 12, textTransform: 'uppercase', letterSpacing: '.06em' }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>{value}</div>
    </div>
  );
}

export default function PassiveIncomePage() {
  const [status, setStatus] = useState<EngineResponse | null>(null);
  const [cycle, setCycle] = useState<EngineResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  async function loadStatus() {
    const response = await fetch('/api/revenue-os/passive-income', { cache: 'no-store' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Unable to load engine status');
    setStatus(payload);
  }

  useEffect(() => {
    loadStatus().catch((err) => setError(String(err?.message || err)));
  }, []);

  async function runCycle() {
    setRunning(true);
    setError('');
    try {
      const response = await fetch('/api/revenue-os/passive-income', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ publish: false }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Cycle failed');
      setCycle(payload);
      await loadStatus();
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setRunning(false);
    }
  }

  const priorities = useMemo(() => status?.plan?.priority || [], [status]);
  const metrics = cycle?.metrics || {};

  return (
    <main className="shell" style={{ paddingBottom: 48 }}>
      <section className="panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div>
            <div style={{ opacity: 0.65, fontSize: 12, letterSpacing: '.08em', textTransform: 'uppercase' }}>Revenue OS</div>
            <h1 style={{ margin: '6px 0 8px' }}>Enterprise AI Passive Income Engine</h1>
            <p style={{ maxWidth: 780, margin: 0, opacity: 0.8 }}>
              One bounded supervisor coordinates a Technical Product Agent, Stock Asset Agent, and Industry Briefing Agent. Policy gates control spend, publishing, platform compliance, and source-code changes.
            </p>
          </div>
          <button onClick={runCycle} disabled={running} style={{ padding: '12px 18px', borderRadius: 10, fontWeight: 700, cursor: running ? 'wait' : 'pointer' }}>
            {running ? 'Running supervised cycle…' : 'Run supervised cycle'}
          </button>
        </div>
      </section>

      {error ? <section className="panel" style={{ marginTop: 16, padding: 16, borderColor: '#7f1d1d' }}>{error}</section> : null}

      <section style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
        <Stat label="Zero-spend default" value={status?.readiness?.zeroSpend === false ? 'Off' : 'On'} />
        <Stat label="External writes" value={status?.readiness?.externalWrites ? 'Enabled' : 'Gated'} />
        <Stat label="Agents" value={status?.plan?.agents?.length || 3} />
        <Stat label="Policy date" value={status?.plan?.policyAsOf || '2026-09-14'} />
        {cycle ? <Stat label="Mean quality" value={metrics.meanQualityScore ?? 0} /> : null}
        {cycle ? <Stat label="AI cost" value={`$${Number(metrics.aiCostUsd || 0).toFixed(4)}`} /> : null}
      </section>

      <section className="panel" style={{ marginTop: 16, padding: 20 }}>
        <h2 style={{ marginTop: 0 }}>Supervisor priority</h2>
        <div style={{ display: 'grid', gap: 10 }}>
          {priorities.map((item: any, index: number) => (
            <div key={item.agentId} style={{ border: '1px solid #263244', borderRadius: 10, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <strong>{index + 1}. {item.agentId.replaceAll('_', ' ')}</strong>
                <span>{item.score}/100</span>
              </div>
              <div style={{ opacity: 0.75, marginTop: 6 }}>{item.rationale}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel" style={{ marginTop: 16, padding: 20 }}>
        <h2 style={{ marginTop: 0 }}>Live platform gates</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr><th align="left">Platform</th><th align="left">Policy</th><th align="left">Execution mode</th></tr></thead>
            <tbody>
              {Object.entries(status?.plan?.platformPolicies || {}).map(([name, policy]: any) => (
                <tr key={name} style={{ borderTop: '1px solid #263244' }}>
                  <td style={{ padding: '10px 8px' }}>{name.replaceAll('_', ' ')}</td>
                  <td style={{ padding: '10px 8px' }}>{policy.status}</td>
                  <td style={{ padding: '10px 8px' }}>{policy.publishMode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {cycle ? (
        <section className="panel" style={{ marginTop: 16, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Latest supervised cycle</h2>
          <p>Cycle: <code>{cycle.cycleId}</code></p>
          <p>Agents run: {metrics.agentsRun} · Review queue: {metrics.reviewQueueItems} · Verified external actions: {metrics.externalActions}</p>
          <div style={{ display: 'grid', gap: 10 }}>
            {(cycle.results || []).map((item: any) => (
              <div key={item.id} style={{ border: '1px solid #263244', borderRadius: 10, padding: 14 }}>
                <strong>{item.agentId.replaceAll('_', ' ')}</strong>
                <div style={{ opacity: 0.75, marginTop: 5 }}>Quality {item.qualityScore}/100 · Profit {item.profitScore}/100 · Delivery {item.delivery?.mode || item.decision?.mode}</div>
                {item.delivery?.proof ? <div style={{ marginTop: 6 }}>External proof captured by adapter.</div> : <div style={{ marginTop: 6 }}>No external publication is claimed without provider proof.</div>}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="panel" style={{ marginTop: 16, padding: 20 }}>
        <h2 style={{ marginTop: 0 }}>Lifelong Catch and Correct</h2>
        <p style={{ marginBottom: 0, opacity: 0.8 }}>
          Learning is bounded to outcome measurement, evaluations, prompt/config optimization, and tested pull-request proposals. Production code does not self-modify at runtime.
        </p>
      </section>
    </main>
  );
}

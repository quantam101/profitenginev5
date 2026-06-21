import Link from 'next/link';

import { createDailyCommandSnapshot } from '@/lib/daily-command-core';

export const dynamic = 'force-dynamic';

const cardStyle = {
  border: '1px solid rgba(125, 211, 252, 0.25)',
  borderRadius: 18,
  padding: 20,
  background: 'rgba(15, 23, 42, 0.72)',
} as const;

export default function DailyCommandPage() {
  const snapshot = createDailyCommandSnapshot([
    {
      id: 'SYSTEM_DAILY_COMMAND_PAGE',
      source: 'VERCEL',
      category: 'SYSTEM_HEALTH',
      status: 'READY_TO_ACT',
      revenueStatus: 'NON_REVENUE',
      title: 'Daily Command page available',
      description: 'Operator page is mounted. Live revenue items enter through /api/daily-command from approved server-side adapters.',
      flags: [],
    },
  ]);

  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#080b12',
        color: '#e5f7ff',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
        padding: 32,
      }}
    >
      <section style={{ maxWidth: 1120, margin: '0 auto' }}>
        <nav style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 48 }}>
          <Link href="/command-center" style={{ color: '#7dd3fc', textDecoration: 'none', fontWeight: 800 }}>
            Command Center
          </Link>
          <a href="/api/daily-command?verify=1" style={{ color: '#e5f7ff', textDecoration: 'none' }}>
            Open verification API
          </a>
        </nav>

        <header style={{ marginBottom: 32 }}>
          <p style={{ color: '#7dd3fc', textTransform: 'uppercase', letterSpacing: 2, fontSize: 12 }}>
            Already Here LLC Daily Command
          </p>
          <h1 style={{ fontSize: 'clamp(34px, 6vw, 64px)', lineHeight: 1, margin: '16px 0' }}>
            Revenue command engine.
          </h1>
          <p style={{ color: '#a8bed0', maxWidth: 780, fontSize: 18, lineHeight: 1.6 }}>
            This page exposes the guarded ranking core, payment-control math, route-friction scoring, approval boundaries,
            and Markdown export path. External systems feed it through the read-only API route; the page does not send,
            submit, accept, deploy, or move money.
          </p>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
          <section style={cardStyle}>
            <span style={{ color: '#7dd3fc', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.5 }}>
              system
            </span>
            <h2 style={{ margin: '10px 0', fontSize: 22 }}>{snapshot.systemHealth}</h2>
            <p style={{ color: '#a8bed0', lineHeight: 1.5, margin: 0 }}>Daily Command core is mounted.</p>
          </section>

          <section style={cardStyle}>
            <span style={{ color: '#7dd3fc', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.5 }}>
              target
            </span>
            <h2 style={{ margin: '10px 0', fontSize: 22 }}>${snapshot.metrics.dailyTargetUsd.toFixed(0)}</h2>
            <p style={{ color: '#a8bed0', lineHeight: 1.5, margin: 0 }}>Default daily field revenue target.</p>
          </section>

          <section style={cardStyle}>
            <span style={{ color: '#7dd3fc', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.5 }}>
              gap
            </span>
            <h2 style={{ margin: '10px 0', fontSize: 22 }}>${snapshot.metrics.revenueGapUsd.toFixed(0)}</h2>
            <p style={{ color: '#a8bed0', lineHeight: 1.5, margin: 0 }}>
              Calculated from confirmed and bookable items only.
            </p>
          </section>
        </div>

        <section style={{ ...cardStyle, marginTop: 24 }}>
          <h2 style={{ marginTop: 0 }}>Control boundaries</h2>
          <ul style={{ color: '#a8bed0', lineHeight: 1.8, paddingLeft: 24 }}>
            <li>Opportunity value is not counted as confirmed revenue.</li>
            <li>Diesel and heavy-duty AutoWorks scope is blocked.</li>
            <li>Invalid source/category payloads are quarantined.</li>
            <li>Owner approval is required before external action.</li>
          </ul>
        </section>
      </section>
    </main>
  );
}

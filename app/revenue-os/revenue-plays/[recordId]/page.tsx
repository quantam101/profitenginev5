'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import type { RevenuePlay } from '@/lib/revenue-os/types';

interface DetailResponse {
  ok: boolean;
  record?: RevenuePlay;
  error?: string;
}

function formatCurrency(n: number) {
  return `$${Math.round(n).toLocaleString()}`;
}

export default function RevenuePlayDetailPage() {
  const params = useParams();
  const recordId = params?.recordId as string;
  const [record, setRecord] = useState<RevenuePlay | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!recordId) return;
    fetch(`/api/revenue-os/revenue-plays/${encodeURIComponent(recordId)}`)
      .then(async (res) => {
        const data = (await res.json()) as DetailResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setRecord(data.record || null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [recordId]);

  return (
    <main className="shell">
      <nav className="nav">
        <Link href="/">← Command Center</Link>
        <Link href="/revenue-os/revenue-plays">← Revenue Plays</Link>
      </nav>

      {loading && <p className="muted">Loading...</p>}
      {error && <p style={{ color: 'var(--blocked)' }}>{error}</p>}

      {record && (
        <div className="card">
          <h1>{record.revenuePlayName}</h1>
          <div style={{ display: 'flex', gap: 10, margin: '12px 0' }}>
            <span className="badge">{record.lane}</span>
            <span className="badge">{record.status}</span>
            <span className="badge" style={{ color: 'var(--action)' }}>Score: {record.overallScore}</span>
          </div>
          <p className="muted">{record.painSolved}</p>

          <h3>Target</h3>
          <p className="muted">{record.buyerType}</p>

          <h3>Ticket value</h3>
          <p className="muted">
            {formatCurrency(record.estimatedTicketValue.minimum)} - {formatCurrency(record.estimatedTicketValue.maximum)} / {record.estimatedTicketValue.unit}
          </p>

          <h3>Time to revenue</h3>
          <p className="muted">{record.timeToRevenueDays} days</p>

          <h3>Recommended action</h3>
          <p className="muted">{record.recommendedAction}</p>

          {record.riskFlags.length > 0 && (
            <>
              <h3>Risk flags</h3>
              <ul className="muted">
                {record.riskFlags.map((flag, i) => <li key={i}>{flag}</li>)}
              </ul>
            </>
          )}

          <h3>Next follow-up</h3>
          <p className="muted">{record.nextFollowUpDate ? new Date(record.nextFollowUpDate).toLocaleDateString() : '—'}</p>
        </div>
      )}
    </main>
  );
}

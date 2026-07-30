'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import type { RevenuePlay } from '@/lib/revenue-os/types';

interface ListResponse {
  ok: boolean;
  records: RevenuePlay[];
  total: number;
  page: number;
  limit: number;
  pageCount: number;
  error?: string;
}

const laneOptions = [
  'Property Services',
  'Healthcare Technology',
  'Restaurant and Retail Technology',
  'Field Services and Low Voltage',
  'Commercial Facilities',
  'Asset Management',
  'Commercial Technology Services',
];

const statusOptions = ['SEED_READY', 'RESEARCH', 'ACTIVE', 'PAUSED', 'ARCHIVED'];

function formatCurrency(n: number) {
  return `$${Math.round(n).toLocaleString()}`;
}

function scoreColor(score: number) {
  if (score >= 80) return 'var(--pass)';
  if (score >= 60) return 'var(--locked)';
  if (score >= 40) return 'var(--review)';
  return 'var(--blocked)';
}

export default function RevenuePlaysPage() {
  const [records, setRecords] = useState<RevenuePlay[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [lane, setLane] = useState('');
  const [status, setStatus] = useState('');
  const [minScore, setMinScore] = useState('');
  const [sortBy, setSortBy] = useState('overallScore');

  const params = useMemo(() => {
    const p = new URLSearchParams();
    p.set('page', String(page));
    p.set('limit', '20');
    p.set('sortBy', sortBy);
    p.set('order', sortBy === 'revenuePlayName' ? 'asc' : 'desc');
    if (search.trim()) p.set('search', search.trim());
    if (lane) p.set('lane', lane);
    if (status) p.set('status', status);
    if (minScore) p.set('minScore', minScore);
    return p;
  }, [page, search, lane, status, minScore, sortBy]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/revenue-os/revenue-plays?${params.toString()}`)
      .then(async (res) => {
        const data = (await res.json()) as ListResponse;
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        if (cancelled) return;
        setRecords(data.records);
        setTotal(data.total);
        setPageCount(data.pageCount);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => setLoading(false));
    return () => { cancelled = true; };
  }, [params]);

  return (
    <main className="shell">
      <nav className="nav" style={{ marginBottom: 0 }}>
        <Link href="/">← Command Center</Link>
        <Link href="/revenue-os/revenue-plays">Revenue Plays</Link>
      </nav>

      <h1>Revenue OS — Revenue Plays</h1>
      <p className="muted">Search and filter the 65 seeded revenue plays. All outreach actions remain approval-gated.</p>

      <div className="filters">
        <input
          className="filter-input"
          placeholder="Search name, pain, notes..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <select className="filter-input" value={lane} onChange={(e) => { setLane(e.target.value); setPage(1); }}>
          <option value="">All lanes</option>
          {laneOptions.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <select className="filter-input" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="filter-input" value={minScore} onChange={(e) => { setMinScore(e.target.value); setPage(1); }}>
          <option value="">Any score</option>
          <option value="80">80+</option>
          <option value="60">60+</option>
          <option value="40">40+</option>
        </select>
        <select className="filter-input" value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}>
          <option value="overallScore">Sort by score</option>
          <option value="revenuePlayName">Sort by name</option>
          <option value="createdAt">Sort by created</option>
        </select>
      </div>

      {loading && <p className="muted">Loading...</p>}
      {error && <p className="error">{error}</p>}

      <div className="meta">
        {total} records {total ? `(page ${page} of ${pageCount})` : ''}
      </div>

      <div className="play-grid">
        {records.map((play) => (
          <Link
            key={play.recordId}
            href={`/revenue-os/revenue-plays/${play.recordId}`}
            className="play-card"
          >
            <div className="play-header">
              <h2>{play.revenuePlayName}</h2>
              <span className="score" style={{ color: scoreColor(play.overallScore) }}>{play.overallScore}</span>
            </div>
            <div className="play-meta">
              <span className="badge">{play.lane}</span>
              <span className="badge">{play.status}</span>
            </div>
            <p className="muted">{play.painSolved}</p>
            <div className="play-footer muted">
              <span>{formatCurrency(play.estimatedTicketValue.minimum)} - {formatCurrency(play.estimatedTicketValue.maximum)}</span>
              <span>• {play.estimatedTicketValue.unit}</span>
              <span>• {play.timeToRevenueDays} days to cash</span>
            </div>
          </Link>
        ))}
      </div>

      {pageCount > 1 && (
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span className="muted">Page {page} of {pageCount}</span>
          <button disabled={page >= pageCount} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}

      <style jsx>{`
        .filters {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          margin: 24px 0;
        }
        .filter-input {
          background: rgba(14,23,38,.9);
          border: 1px solid var(--border);
          border-radius: 8px;
          color: var(--text);
          padding: 10px 12px;
          font-size: 14px;
          min-width: 160px;
        }
        .filter-input:focus { outline: 2px solid var(--action); }
        .meta { color: var(--muted); margin: 12px 0 20px; }
        .play-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
        .play-card {
          border: 1px solid var(--border);
          background: rgba(14,23,38,.9);
          border-radius: 8px;
          padding: 18px;
          display: block;
          transition: border-color .15s;
        }
        .play-card:hover { border-color: var(--action); }
        .play-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
        .play-header h2 { margin: 0 0 10px; font-size: 18px; flex: 1; }
        .score { font-size: 22px; font-weight: 700; }
        .play-meta { display: flex; gap: 8px; margin: 10px 0; }
        .play-footer { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; font-size: 13px; }
        .pagination { display: flex; gap: 16px; align-items: center; margin-top: 24px; }
        .pagination button {
          background: var(--panel);
          border: 1px solid var(--border);
          color: var(--text);
          border-radius: 8px;
          padding: 10px 14px;
          cursor: pointer;
        }
        .pagination button:disabled { opacity: .4; cursor: not-allowed; }
        .error { color: var(--blocked); }
      `}</style>
    </main>
  );
}

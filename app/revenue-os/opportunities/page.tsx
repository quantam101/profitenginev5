'use client';

import { useEffect, useState } from 'react';
import type { Opportunity } from '@/lib/revenue-os/types';

interface ListResponse {
  ok: boolean;
  records?: Opportunity[];
  total?: number;
  error?: string;
}

const STAGES = ['Research', 'Qualified', 'Approval Needed', 'Outreach Approved', 'Contacted', 'Conversation', 'Proposal', 'Negotiation', 'Won', 'Lost', 'On Hold'];

function formatCurrency(n?: number) {
  if (n === undefined || n === null) return '—';
  return `$${Math.round(n).toLocaleString()}`;
}

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchOpportunities = () => {
    setLoading(true);
    fetch('/api/revenue-os/opportunities?active=true&limit=100')
      .then(async (res) => {
        const data = (await res.json()) as ListResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setOpportunities(data.records || []);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    const form = e.currentTarget;
    const formData = new FormData(form);
    const payload = {
      revenuePlayId: String(formData.get('revenuePlayId')),
      companyId: String(formData.get('companyId')),
      title: String(formData.get('title')),
      stage: String(formData.get('stage')),
      estimatedValue: Number(formData.get('estimatedValue') || 0),
      recurringMonthlyValue: Number(formData.get('recurringMonthlyValue') || 0),
      probability: Number(formData.get('probability') || 0),
      nextAction: String(formData.get('nextAction')),
      assignedTo: String(formData.get('assignedTo') || ''),
    };

    try {
      const res = await fetch('/api/revenue-os/opportunities', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = (await res.json()) as ListResponse;
      if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
      form.reset();
      fetchOpportunities();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  const advance = async (id: string) => {
    try {
      const res = await fetch(`/api/revenue-os/opportunities/${id}/advance`, { method: 'POST' });
      const data = (await res.json()) as { ok: boolean; error?: string };
      if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
      fetchOpportunities();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <main className="shell">
      <h1>Opportunities</h1>
      <p className="muted">Create opportunities and advance them through the pipeline.</p>

      {error && <p className="error">{error}</p>}

      <form onSubmit={onSubmit} className="card" style={{ marginTop: 24 }}>
        <h3>New Opportunity</h3>
        <div className="form-row">
          <input name="revenuePlayId" placeholder="Revenue Play ID" required />
          <input name="companyId" placeholder="Company ID" required />
          <input name="title" placeholder="Opportunity title" required />
        </div>
        <div className="form-row">
          <select name="stage" defaultValue="Research">
            {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <input name="estimatedValue" type="number" placeholder="Estimated value" defaultValue={0} />
          <input name="recurringMonthlyValue" type="number" placeholder="MRR" defaultValue={0} />
          <input name="probability" type="number" step="0.01" max="1" placeholder="Probability (0-1)" defaultValue={0.5} />
        </div>
        <div className="form-row">
          <input name="nextAction" placeholder="Next action" required />
          <input name="assignedTo" placeholder="Assigned to" />
        </div>
        <button type="submit" className="primary" disabled={saving}>{saving ? 'Saving...' : 'Create Opportunity'}</button>
      </form>

      {loading && <p className="muted">Loading...</p>}
      {!loading && opportunities.length === 0 && <p className="muted">No active opportunities.</p>}

      <div className="play-grid">
        {opportunities.map((o) => (
          <div key={String(o._id)} className="play-card">
            <h3>{o.title}</h3>
            <p className="muted">{o.stage} · {formatCurrency(o.estimatedValue)} · weighted {formatCurrency(o.weightedValue)}</p>
            <p className="muted">{o.nextAction}</p>
            <div style={{ marginTop: 12 }}>
              <button className="secondary" onClick={() => advance(String(o._id))} disabled={o.stage === 'Won' || o.stage === 'Lost'}>Advance</button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

'use client';

import { useEffect, useState } from 'react';
import type { AIAction, DataQualityFlag, OpportunityRanking } from '@/lib/revenue-os/types';

interface RecommendationsResponse {
  ok: boolean;
  rankings?: OpportunityRanking[];
  error?: string;
}

interface QualityResponse {
  ok: boolean;
  flags?: DataQualityFlag[];
  error?: string;
}

interface ActionsResponse {
  ok: boolean;
  records?: AIAction[];
  total?: number;
  error?: string;
}

const DRAFT_TYPES = [
  ['intro_email', 'Intro Email'],
  ['follow_up_email', 'Follow-Up Email'],
  ['capability_statement', 'Capability Statement'],
  ['call_script', 'Call Script'],
  ['proposal_summary', 'Proposal Summary'],
  ['sow_draft', 'Scope of Work'],
];

export default function AIAdvisorPage() {
  const [rankings, setRankings] = useState<OpportunityRanking[]>([]);
  const [flags, setFlags] = useState<DataQualityFlag[]>([]);
  const [actions, setActions] = useState<AIAction[]>([]);
  const [draftType, setDraftType] = useState('intro_email');
  const [opportunityId, setOpportunityId] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/revenue-os/ai/recommendations?limit=10').then(async (res) => {
        const data = (await res.json()) as RecommendationsResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setRankings(data.rankings || []);
      }),
      fetch('/api/revenue-os/ai/quality').then(async (res) => {
        const data = (await res.json()) as QualityResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setFlags(data.flags || []);
      }),
      fetch('/api/revenue-os/ai/actions?limit=50').then(async (res) => {
        const data = (await res.json()) as ActionsResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setActions(data.records || []);
      }),
    ])
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const generateDraft = async (save: boolean) => {
    if (!opportunityId) return;
    setDraft('');
    const res = await fetch('/api/revenue-os/ai/drafts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: draftType, opportunityId, save }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setError(data.error || `HTTP ${res.status}`);
      return;
    }
    setDraft(data.content || '');
    if (save) fetchData();
  };

  const transitionAction = async (id: string, path: string) => {
    const res = await fetch(`/api/revenue-os/ai/actions/${id}/${path}`, { method: 'POST' });
    if (!res.ok) {
      const data = await res.json();
      setError(data.error || `HTTP ${res.status}`);
      return;
    }
    fetchData();
  };

  return (
    <main className="shell">
      <h1>AI Advisor</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

      <section>
        <h2>Top Recommended Opportunities</h2>
        {rankings.length === 0 && !loading && <p>No active opportunities.</p>}
        <div className="play-grid">
          {rankings.map((r) => (
            <div key={r.opportunityId} className="play-card">
              <h3>{r.title}</h3>
              <p><strong>Stage:</strong> {r.stage}</p>
              <p><strong>Expected revenue:</strong> ${Math.round(r.expectedRevenue).toLocaleString()}</p>
              <p><strong>Score:</strong> {Math.round(r.score).toLocaleString()}</p>
              <p><strong>Next action:</strong> {r.recommendedNextAction}</p>
              <p><strong>Why:</strong> {r.reason}</p>
              {r.startupRequirements.length > 0 && (
                <p><strong>Startup needs:</strong> {r.startupRequirements.join(', ')}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Draft Generator</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            generateDraft(false);
          }}
          style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 600 }}
        >
          <select value={draftType} onChange={(e) => setDraftType(e.target.value)}>
            {DRAFT_TYPES.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Opportunity ID"
            value={opportunityId}
            onChange={(e) => setOpportunityId(e.target.value)}
            required
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit" className="primary">Generate</button>
            <button type="button" className="secondary" onClick={() => generateDraft(true)}>Generate & Save</button>
          </div>
        </form>
        {draft && (
          <pre style={{ whiteSpace: 'pre-wrap', background: '#111', padding: 12, borderRadius: 6, marginTop: 12 }}>{draft}</pre>
        )}
      </section>

      <section>
        <h2>Data Quality Flags ({flags.length})</h2>
        {flags.length === 0 && !loading && <p>No flags.</p>}
        <ul>
          {flags.map((f, idx) => (
            <li key={idx}>
              <strong>[{f.severity.toUpperCase()}]</strong> {f.entityType} {f.entityId}: {f.issue} — <em>{f.suggestedFix}</em>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Approval Queue</h2>
        {actions.length === 0 && !loading && <p>No AI actions.</p>}
        <div className="play-grid">
          {actions.map((a) => (
            <div key={String(a._id)} className="play-card">
              <h3>{a.actionType.replace(/_/g, ' ')}</h3>
              <p><strong>Status:</strong> {a.status}</p>
              <p><strong>Created by:</strong> {a.createdBy}</p>
              <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, maxHeight: 120, overflow: 'auto' }}>{a.content}</pre>
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                {a.status === 'Draft' && (
                  <button className="secondary" onClick={() => transitionAction(String(a._id), 'review')}>Submit for Review</button>
                )}
                {a.status === 'Needs Review' && (
                  <>
                    <button className="primary" onClick={() => transitionAction(String(a._id), 'approve')}>Approve</button>
                    <button className="secondary" onClick={() => transitionAction(String(a._id), 'reject')}>Reject</button>
                  </>
                )}
                {a.status === 'Approved' && (
                  <button className="primary" onClick={() => transitionAction(String(a._id), 'execute')}>Execute (Audit Only)</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

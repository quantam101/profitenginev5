'use client';

import { useEffect, useState } from 'react';
import type { FollowUpTask } from '@/lib/revenue-os/types';

interface ListResponse {
  ok: boolean;
  records?: FollowUpTask[];
  total?: number;
  error?: string;
}

export default function FollowUpsPage() {
  const [followUps, setFollowUps] = useState<FollowUpTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFollowUps = () => {
    setLoading(true);
    fetch('/api/revenue-os/follow-ups?status=OPEN&dueToday=true&limit=100')
      .then(async (res) => {
        const data = (await res.json()) as ListResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setFollowUps(data.records || []);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchFollowUps();
  }, []);

  const complete = async (id: string) => {
    try {
      const res = await fetch('/api/revenue-os/follow-ups', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status: 'COMPLETED' }),
      });
      const data = (await res.json()) as { ok: boolean; error?: string };
      if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
      fetchFollowUps();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <main className="shell">
      <h1>Follow-Ups</h1>
      <p className="muted">Due and scheduled follow-up tasks.</p>

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Loading...</p>}
      {!loading && followUps.length === 0 && <p className="muted">No follow-ups due.</p>}

      <div className="play-grid">
        {followUps.map((f) => (
          <div key={String(f._id)} className="play-card">
            <h3>{f.summary}</h3>
            <p className="muted">Due {new Date(f.dueDate).toLocaleDateString()} · {f.priority}</p>
            <button className="secondary" onClick={() => complete(String(f._id))}>Complete</button>
          </div>
        ))}
      </div>
    </main>
  );
}

'use client';

import { useEffect, useRef, useState } from 'react';
import type { Company } from '@/lib/revenue-os/types';

interface ListResponse {
  ok: boolean;
  records?: Company[];
  total?: number;
  error?: string;
}

function formatCurrency(n?: number) {
  if (n === undefined || n === null) return '—';
  return `$${Math.round(n).toLocaleString()}`;
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  const fetchCompanies = () => {
    setLoading(true);
    fetch('/api/revenue-os/companies?limit=100')
      .then(async (res) => {
        const data = (await res.json()) as ListResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setCompanies(data.records || []);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    const form = e.currentTarget;
    const formData = new FormData(form);
    const payload = {
      legalName: String(formData.get('legalName')),
      displayName: String(formData.get('displayName') || formData.get('legalName')),
      website: String(formData.get('website') || ''),
      industry: String(formData.get('industry')),
      companyType: String(formData.get('companyType')),
      locations: [{
        city: String(formData.get('city') || ''),
        state: String(formData.get('state') || ''),
        zipCode: String(formData.get('zipCode') || ''),
      }],
      serviceLanes: String(formData.get('serviceLanes') || '').split(',').map((s) => s.trim()).filter(Boolean),
    };

    try {
      const res = await fetch('/api/revenue-os/companies', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = (await res.json()) as ListResponse;
      if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
      form.reset();
      fetchCompanies();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="shell">
      <h1>Companies</h1>
      <p className="muted">Add target companies and view duplicates by domain or name + ZIP.</p>

      {error && <p className="error">{error}</p>}

      <form ref={formRef} onSubmit={onSubmit} className="card" style={{ marginTop: 24 }}>
        <h3>Add Company</h3>
        <div className="form-row">
          <input name="legalName" placeholder="Legal name" required />
          <input name="displayName" placeholder="Display name" />
          <input name="website" placeholder="Website" />
        </div>
        <div className="form-row">
          <input name="industry" placeholder="Industry" required />
          <input name="companyType" placeholder="Company type" required />
          <input name="serviceLanes" placeholder="Service lanes (comma separated)" />
        </div>
        <div className="form-row">
          <input name="city" placeholder="City" />
          <input name="state" placeholder="State" />
          <input name="zipCode" placeholder="ZIP" />
        </div>
        <button type="submit" className="primary" disabled={saving}>{saving ? 'Saving...' : 'Add Company'}</button>
      </form>

      {loading && <p className="muted">Loading...</p>}
      {!loading && companies.length === 0 && <p className="muted">No companies yet.</p>}

      <div className="play-grid">
        {companies.map((c) => (
          <div key={String(c._id)} className="play-card">
            <h3>{c.displayName || c.legalName}</h3>
            <p className="muted">{c.industry} · {c.companyType}</p>
            <p className="muted">{c.website || '—'}</p>
            {c.serviceLanes && c.serviceLanes.length > 0 && <p className="muted">{c.serviceLanes.join(', ')}</p>}
          </div>
        ))}
      </div>
    </main>
  );
}

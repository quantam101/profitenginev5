'use client';

import { useEffect, useState } from 'react';
import type { Contact } from '@/lib/revenue-os/types';

interface ListResponse {
  ok: boolean;
  records?: Contact[];
  total?: number;
  error?: string;
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchContacts = () => {
    setLoading(true);
    fetch('/api/revenue-os/contacts?limit=100')
      .then(async (res) => {
        const data = (await res.json()) as ListResponse;
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setContacts(data.records || []);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    const form = e.currentTarget;
    const formData = new FormData(form);
    const payload = {
      companyId: String(formData.get('companyId')),
      fullName: String(formData.get('fullName')),
      title: String(formData.get('title') || ''),
      email: String(formData.get('email') || ''),
      phone: String(formData.get('phone') || ''),
      preferredChannel: String(formData.get('preferredChannel') || ''),
    };

    try {
      const res = await fetch('/api/revenue-os/contacts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = (await res.json()) as ListResponse;
      if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
      form.reset();
      fetchContacts();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="shell">
      <h1>Contacts</h1>
      <p className="muted">Contacts tied to companies.</p>

      {error && <p className="error">{error}</p>}

      <form onSubmit={onSubmit} className="card" style={{ marginTop: 24 }}>
        <h3>Add Contact</h3>
        <div className="form-row">
          <input name="companyId" placeholder="Company ID" required />
          <input name="fullName" placeholder="Full name" />
          <input name="title" placeholder="Title" />
        </div>
        <div className="form-row">
          <input name="email" type="email" placeholder="Email" />
          <input name="phone" placeholder="Phone" />
          <input name="preferredChannel" placeholder="Preferred channel" />
        </div>
        <button type="submit" className="primary" disabled={saving}>{saving ? 'Saving...' : 'Add Contact'}</button>
      </form>

      {loading && <p className="muted">Loading...</p>}
      {!loading && contacts.length === 0 && <p className="muted">No contacts yet.</p>}

      <div className="play-grid">
        {contacts.map((c) => (
          <div key={String(c._id)} className="play-card">
            <h3>{c.fullName || 'Unnamed'}</h3>
            <p className="muted">{c.title || '—'}</p>
            <p className="muted">{c.email || '—'} · {c.phone || '—'}</p>
          </div>
        ))}
      </div>
    </main>
  );
}

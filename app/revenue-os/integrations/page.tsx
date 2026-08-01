'use client';

import { useEffect, useState } from 'react';

interface DeliveryRecord {
  _id: string;
  provider: string;
  eventType: string;
  status: string;
  idempotencyKey: string;
  createdAt: string;
}

interface SlackRecord {
  _id: string;
  notificationType: string;
  channel: string;
  status: string;
  createdAt: string;
}

export default function IntegrationsPage() {
  const [slackEnabled, setSlackEnabled] = useState(false);
  const [zapierEnabled, setZapierEnabled] = useState(false);
  const [slackRecords, setSlackRecords] = useState<SlackRecord[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryRecord[]>([]);
  const [eventType, setEventType] = useState('opportunity.created');
  const [payload, setPayload] = useState('{}');
  const [message, setMessage] = useState('');
  const [channel, setChannel] = useState('#revenue-ops');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/revenue-os/notifications/slack').then(async (res) => {
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setSlackEnabled(data.enabled);
        setSlackRecords(data.records || []);
      }),
      fetch('/api/revenue-os/webhooks/deliveries').then(async (res) => {
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setDeliveries(data.records || []);
      }),
      fetch('/api/revenue-os/webhooks/zapier').then(async (res) => {
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
        setZapierEnabled(data.enabled);
      }),
    ])
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const sendSlack = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const res = await fetch('/api/revenue-os/notifications/slack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notificationType: 'manual_test', channel, text: message }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setError(data.error || `HTTP ${res.status}`);
      return;
    }
    setMessage('');
    fetchData();
  };

  const sendZapier = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    let parsed;
    try {
      parsed = JSON.parse(payload);
    } catch {
      setError('Invalid JSON payload');
      return;
    }
    const res = await fetch('/api/revenue-os/webhooks/zapier', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ eventType, payload: parsed }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setError(data.error || `HTTP ${res.status}`);
      return;
    }
    fetchData();
  };

  return (
    <main className="shell">
      <h1>Integrations</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

      <section>
        <h2>Slack {slackEnabled ? '(enabled)' : '(disabled)'}</h2>
        <form onSubmit={sendSlack} style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 600 }}>
          <input type="text" value={channel} onChange={(e) => setChannel(e.target.value)} placeholder="Channel" />
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Message" rows={3} required />
          <button type="submit" className="primary" disabled={!slackEnabled}>Send Slack Notification</button>
        </form>
        {!slackEnabled && <p className="muted">Enable REVENUE_OS_SLACK_ENABLED and SLACK_REVENUE_WEBHOOK in environment to send.</p>}
      </section>

      <section>
        <h2>Zapier {zapierEnabled ? '(enabled)' : '(disabled)'}</h2>
        <form onSubmit={sendZapier} style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 600 }}>
          <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
            <option value="revenue_play.created">revenue_play.created</option>
            <option value="company.qualified">company.qualified</option>
            <option value="opportunity.created">opportunity.created</option>
            <option value="opportunity.stage_changed">opportunity.stage_changed</option>
            <option value="follow_up.due">follow_up.due</option>
            <option value="proposal.approved">proposal.approved</option>
            <option value="opportunity.won">opportunity.won</option>
          </select>
          <textarea value={payload} onChange={(e) => setPayload(e.target.value)} placeholder='{"id":"..."}' rows={4} />
          <button type="submit" className="primary" disabled={!zapierEnabled}>Dispatch Zapier Event</button>
        </form>
        {!zapierEnabled && <p className="muted">Enable REVENUE_OS_ZAPIER_ENABLED, ZAPIER_REVENUE_WEBHOOK, and WEBHOOK_SIGNING_SECRET in environment to dispatch.</p>}
      </section>

      <section>
        <h2>Delivery Log</h2>
        {deliveries.length === 0 && !loading && <p>No webhook deliveries.</p>}
        <ul>
          {deliveries.map((d) => (
            <li key={d._id}>
              <strong>{d.provider}</strong> {d.eventType} — <em>{d.status}</em> ({d.idempotencyKey}) at {new Date(d.createdAt).toLocaleString()}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Slack Log</h2>
        {slackRecords.length === 0 && !loading && <p>No Slack notifications.</p>}
        <ul>
          {slackRecords.map((s) => (
            <li key={s._id}>
              <strong>{s.notificationType}</strong> {s.channel} — <em>{s.status}</em> at {new Date(s.createdAt).toLocaleString()}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

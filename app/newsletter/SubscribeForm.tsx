'use client';

import { FormEvent, useState } from 'react';

export default function SubscribeForm() {
  const [email, setEmail] = useState('');
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent) {
      setState('error');
      setMessage('Please confirm that you want to receive the newsletter.');
      return;
    }

    setState('sending');
    setMessage('');
    try {
      const params = new URLSearchParams(window.location.search);
      const response = await fetch('/api/newsletter/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          consent: true,
          source: 'profitengine-newsletter-page',
          utmSource: params.get('utm_source') || undefined,
          utmMedium: params.get('utm_medium') || undefined,
          utmCampaign: params.get('utm_campaign') || undefined,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || 'Subscription failed');

      setState('success');
      setEmail('');
      setMessage(data.status === 'active'
        ? 'Subscribed. ProfitEngine AI will be delivered to this address.'
        : data.confirmationSent
          ? 'Check your inbox and confirm your subscription.'
          : 'Your subscription was captured and is pending activation.');
    } catch (error) {
      setState('error');
      setMessage(error instanceof Error ? error.message : 'Subscription failed');
    }
  }

  return (
    <form className="newsletter-form" onSubmit={submit}>
      <label htmlFor="newsletter-email">Email address</label>
      <div className="newsletter-form-row">
        <input
          id="newsletter-email"
          name="email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={state === 'sending'}
        />
        <button type="submit" disabled={state === 'sending'}>{state === 'sending' ? 'Capturing…' : 'Subscribe free'}</button>
      </div>
      <label className="consent-row">
        <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
        <span>I want ProfitEngine AI emails and understand I can unsubscribe at any time.</span>
      </label>
      {message && <p className={`form-message ${state}`}>{message}</p>}
      {state === 'success' && <a className="checklist-link" href="/newsletter/30-day-checklist">Open the 30-day launch checklist →</a>}
    </form>
  );
}

'use client';

import { useState } from 'react';

export default function CheckoutPage() {
  const [tool, setTool] = useState('travel');
  const [tier, setTier] = useState('starter');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const pricing: Record<string, Record<string, { name: string; price: number }>> = {
    travel: {
      starter: { name: 'Budget Itinerary', price: 49900 },
      standard: { name: 'Extended Itinerary', price: 149900 },
      premium: { name: 'VIP Concierge', price: 249900 },
    },
    newsletter: {
      starter: { name: '1 Month Trial', price: 99900 },
      standard: { name: '3-Month Package', price: 249900 },
      premium: { name: 'Annual Retainer', price: 299900 },
    },
    'sales-copy': {
      starter: { name: 'Basic Page', price: 499900 },
      standard: { name: 'Professional Page', price: 1299900 },
      premium: { name: 'Enterprise Package', price: 2499900 },
    },
    linkedin: {
      starter: { name: 'Single Post', price: 49900 },
      standard: { name: 'Monthly Package', price: 199900 },
      premium: { name: 'Quarterly Retainer', price: 499900 },
    },
    resume: {
      starter: { name: 'Resume Only', price: 24900 },
      standard: { name: 'Bundle', price: 69900 },
      premium: { name: 'Career Package', price: 149900 },
    },
    kdp: {
      starter: { name: 'Single Book', price: 49900 },
      standard: { name: 'Book Bundle', price: 129900 },
      premium: { name: 'Publishing Bundle', price: 249900 },
    },
  };

  const current = pricing[tool]?.[tier];
  const amount = current?.price || 0;

  const handleCheckout = async () => {
    if (!email) {
      setError('Please enter your email');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool, tier, email }),
      });

      const data = await response.json();

      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error || 'Failed to create checkout session');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', fontFamily: 'system-ui', padding: '40px 24px' }}>
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '32px', fontSize: '32px' }}>Checkout</h1>

        {/* Tool Selection */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600 }}>Select Tool</label>
          <select
            value={tool}
            onChange={(e) => setTool(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              background: '#1f2937',
              color: '#fff',
              border: '1px solid #374151',
              borderRadius: '6px',
              fontSize: '14px',
            }}
          >
            <option value="travel">Travel Agency</option>
            <option value="newsletter">Newsletter Writer</option>
            <option value="sales-copy">Sales Copywriter</option>
            <option value="linkedin">LinkedIn Post Generator</option>
            <option value="resume">Resume Optimizer</option>
            <option value="kdp">KDP Books</option>
          </select>
        </div>

        {/* Tier Selection */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600 }}>Package Tier</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {['starter', 'standard', 'premium'].map((t) => (
              <button
                key={t}
                onClick={() => setTier(t)}
                style={{
                  padding: '12px',
                  background: tier === t ? '#00ff00' : '#1f2937',
                  color: tier === t ? '#000' : '#fff',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Price Display */}
        {current && (
          <div style={{ padding: '16px', background: '#1f2937', borderRadius: '6px', marginBottom: '32px' }}>
            <p style={{ margin: '0 0 8px 0', color: '#9fb0c6' }}>{current.name}</p>
            <p style={{ margin: '0', fontSize: '24px', fontWeight: 700, color: '#00ff00' }}>
              ${(amount / 100).toFixed(2)}
            </p>
          </div>
        )}

        {/* Email */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            style={{
              width: '100%',
              padding: '12px',
              background: '#1f2937',
              color: '#fff',
              border: '1px solid #374151',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Error Message */}
        {error && (
          <div style={{ padding: '12px', background: '#7f1d1d', borderRadius: '6px', marginBottom: '24px', color: '#fca5a5' }}>
            {error}
          </div>
        )}

        {/* Checkout Button */}
        <button
          onClick={handleCheckout}
          disabled={loading}
          style={{
            width: '100%',
            padding: '16px',
            background: loading ? '#555' : '#00ff00',
            color: loading ? '#ccc' : '#000',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '16px',
            cursor: loading ? 'default' : 'pointer',
          }}
        >
          {loading ? 'Processing...' : 'Proceed to Payment'}
        </button>
      </div>
    </div>
  );
}

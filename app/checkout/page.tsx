'use client';

import { useEffect, useRef } from 'react';

export default function CheckoutPage() {
  const pricingTableRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load Stripe Pricing Table script
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/pricing-table.js';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  useEffect(() => {
    const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '';
    const pricingTableId = process.env.NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID || '';

    if (publishableKey && pricingTableId && pricingTableRef.current) {
      const table = document.createElement('stripe-pricing-table');
      table.setAttribute('pricing-table-id', pricingTableId);
      table.setAttribute('publishable-key', publishableKey);

      pricingTableRef.current.innerHTML = '';
      pricingTableRef.current.appendChild(table);
    }
  }, []);

  const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '';
  const pricingTableId = process.env.NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID || '';

  if (!publishableKey || !pricingTableId) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0a0a0a' }}>
        <div style={{ color: '#fff', textAlign: 'center' }}>
          <h1>Checkout Not Configured</h1>
          <p>Please contact support to complete your purchase.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', padding: '40px 24px' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ color: '#fff', textAlign: 'center', marginBottom: '48px', fontSize: '32px' }}>
          Choose Your Perfect Package
        </h1>

        {/* Stripe Pricing Table Container */}
        <div ref={pricingTableRef} />
      </div>
    </div>
  );
}

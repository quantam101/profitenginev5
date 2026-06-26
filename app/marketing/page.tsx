'use client';

export default function MarketingPage() {
  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', fontFamily: 'system-ui' }}>
      {/* Header */}
      <header style={{ padding: '40px 24px', textAlign: 'center', background: 'linear-gradient(135deg, #0a0a0a, #1a1a1a)' }}>
        <h1 style={{ margin: '0 0 16px 0', fontSize: '48px', fontWeight: 700 }}>
          Generate High-Converting Content in Minutes
        </h1>
        <p style={{ margin: '0', fontSize: '20px', color: '#9fb0c6' }}>
          7 AI-powered tools to build profitable services. $500–$25K per project.
        </p>
      </header>

      {/* Tools Grid */}
      <section style={{ padding: '60px 24px', maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '48px', fontSize: '36px' }}>Tools Available</h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
          {[
            { name: 'Travel Agency', price: '$500–$2.5K', desc: 'Custom itineraries & travel plans' },
            { name: 'Newsletter Writer', price: '$2K–$5K/mo', desc: 'Content strategy & ghostwritten posts' },
            { name: 'Sales Copywriter', price: '$5K–$25K', desc: 'High-converting sales pages & funnels' },
            { name: 'LinkedIn Post Generator', price: '$500–$700', desc: 'Ghostwritten professional content' },
            { name: 'Resume Optimizer', price: '$200–$500', desc: 'ATS-optimized resumes & profiles' },
            { name: 'KDP Books', price: '$600–$3K/mo', desc: 'Children\'s books for passive income' },
          ].map((tool, i) => (
            <div
              key={i}
              style={{
                padding: '24px',
                background: 'rgba(31, 41, 55, 0.5)',
                border: '1px solid #374151',
                borderRadius: '8px',
                cursor: 'pointer',
              }}
              onMouseOver={(e) => (e.currentTarget.style.background = 'rgba(55, 65, 81, 0.8)')}
              onMouseOut={(e) => (e.currentTarget.style.background = 'rgba(31, 41, 55, 0.5)')}
            >
              <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#00ff00' }}>{tool.name}</h3>
              <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#9fb0c6' }}>{tool.desc}</p>
              <p style={{ margin: '0', fontSize: '16px', fontWeight: 700, color: '#eef5ff' }}>{tool.price}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section style={{ padding: '60px 24px', background: 'rgba(15, 23, 42, 0.5)', textAlign: 'center' }}>
        <h2 style={{ marginBottom: '48px', fontSize: '36px' }}>How It Works</h2>
        <div style={{ maxWidth: '800px', margin: '0 auto', lineHeight: '1.8', fontSize: '16px', color: '#d1d5db' }}>
          <p>1. Choose a tool and pricing tier</p>
          <p>2. Make payment securely via Stripe</p>
          <p>3. Get instant access to the tool</p>
          <p>4. Generate professional content in minutes</p>
          <p>5. Deliver to your clients or use for your own business</p>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '60px 24px', textAlign: 'center' }}>
        <h2 style={{ marginBottom: '24px', fontSize: '36px' }}>Ready to Start?</h2>
        <p style={{ marginBottom: '32px', fontSize: '18px', color: '#9fb0c6' }}>
          Choose a tool and start generating profitable content today.
        </p>
        <a
          href="/checkout"
          style={{
            display: 'inline-block',
            padding: '16px 48px',
            background: '#00ff00',
            color: '#000',
            textDecoration: 'none',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '16px',
          }}
        >
          Go to Checkout
        </a>
      </section>

      {/* Footer */}
      <footer style={{ padding: '24px', textAlign: 'center', borderTop: '1px solid #374151', color: '#6b7280' }}>
        <p style={{ margin: '0' }}>© 2026 ProfitEngine v5. All rights reserved.</p>
      </footer>
    </div>
  );
}

export const dynamic = 'force-static';

const CHECKS = [
  {
    label: 'Production homepage',
    status: 'online',
    detail: 'Vercel frontend is serving the public ProfitEngine v5 launch page.',
    href: '/',
  },
  {
    label: 'Profitability API',
    status: 'online',
    detail: 'Offer scoring and proof-gated revenue data endpoint is responding.',
    href: '/api/profitability',
  },
  {
    label: 'KDP revenue API',
    status: 'online',
    detail: 'KDP research-to-assets endpoint is responding with manual approval gates.',
    href: '/api/kdp-revenue',
  },
  {
    label: 'AI VP Cash Desk',
    status: 'online',
    detail: 'Field-revenue and route-stacking command screen is available.',
    href: '/ai-vp',
  },
];

const ACTIONS = [
  'Keep Vercel as the active frontend production path.',
  'Keep the unfinished Replit/backend path out of the production critical path.',
  'Do not re-enable protected dashboard middleware until NextAuth secrets and provider config are verified.',
  'Use this page as the stable operator landing screen while backend architecture is repaired.',
];

export default function CommandCenterPage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#080b12',
        color: '#e5f7ff',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
        padding: '32px',
      }}
    >
      <section style={{ maxWidth: 1040, margin: '0 auto' }}>
        <nav style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 56 }}>
          <a href="/" style={{ color: '#7dd3fc', textDecoration: 'none', fontWeight: 800 }}>
            ProfitEngine v5
          </a>
          <a href="/ai-vp" style={{ color: '#e5f7ff', textDecoration: 'none' }}>
            AI VP Cash Desk
          </a>
        </nav>

        <header style={{ marginBottom: 36 }}>
          <p style={{ color: '#7dd3fc', textTransform: 'uppercase', letterSpacing: 2, fontSize: 12 }}>
            Already Here LLC operator console
          </p>
          <h1 style={{ fontSize: 'clamp(36px, 7vw, 72px)', lineHeight: 1, margin: '16px 0' }}>
            Production command center restored.
          </h1>
          <p style={{ color: '#a8bed0', maxWidth: 760, fontSize: 18, lineHeight: 1.6 }}>
            This route is intentionally static and auth-free until the backend and protected dashboard stack are repaired.
            It keeps the public production site usable while Replit/backend work is isolated from Vercel frontend delivery.
          </p>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          {CHECKS.map((check) => (
            <a
              key={check.label}
              href={check.href}
              style={{
                display: 'block',
                border: '1px solid rgba(125, 211, 252, 0.25)',
                borderRadius: 18,
                padding: 20,
                color: '#e5f7ff',
                background: 'rgba(15, 23, 42, 0.72)',
                textDecoration: 'none',
              }}
            >
              <span style={{ color: '#7dd3fc', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.5 }}>
                {check.status}
              </span>
              <h2 style={{ margin: '10px 0', fontSize: 22 }}>{check.label}</h2>
              <p style={{ color: '#a8bed0', lineHeight: 1.5, margin: 0 }}>{check.detail}</p>
            </a>
          ))}
        </div>

        <section style={{ marginTop: 32, border: '1px solid rgba(125, 211, 252, 0.25)', borderRadius: 18, padding: 24 }}>
          <h2 style={{ marginTop: 0 }}>Stabilization rules</h2>
          <ol style={{ color: '#a8bed0', lineHeight: 1.8, paddingLeft: 24 }}>
            {ACTIONS.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ol>
        </section>
      </section>
    </main>
  );
}

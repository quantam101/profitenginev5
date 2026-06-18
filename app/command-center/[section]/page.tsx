/* eslint-disable @next/next/no-html-link-for-pages */

export const dynamic = 'force-static';
export const dynamicParams = false;

const sections = [
  'agents',
  'approvals',
  'changelog',
  'connectors',
  'costs',
  'logs',
  'modules',
  'security',
  'workflows',
] as const;

type Section = (typeof sections)[number];

const sectionTitles: Record<Section, string> = {
  agents: 'Agents',
  approvals: 'Approvals',
  changelog: 'Changelog',
  connectors: 'Connectors',
  costs: 'Costs',
  logs: 'Logs',
  modules: 'Modules',
  security: 'Security',
  workflows: 'Workflows',
};

export function generateStaticParams() {
  return sections.map((section) => ({ section }));
}

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const safeSection = sections.includes(section as Section) ? (section as Section) : 'security';

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
      <section style={{ maxWidth: 960, margin: '0 auto' }}>
        <a href="/command-center" style={{ color: '#7dd3fc', textDecoration: 'none', fontWeight: 800 }}>
          Command Center
        </a>
        <h1 style={{ fontSize: 'clamp(36px, 7vw, 68px)', lineHeight: 1, margin: '24px 0 12px' }}>
          {sectionTitles[safeSection]}
        </h1>
        <p style={{ color: '#a8bed0', maxWidth: 720, fontSize: 18, lineHeight: 1.6 }}>
          This static status page is available while backend, auth, and Replit/Railway integrations are isolated from the Vercel production frontend.
        </p>
        <div
          style={{
            marginTop: 28,
            border: '1px solid rgba(125, 211, 252, 0.25)',
            borderRadius: 18,
            padding: 24,
            background: 'rgba(15, 23, 42, 0.72)',
          }}
        >
          <h2 style={{ marginTop: 0 }}>Current operating rule</h2>
          <p style={{ color: '#a8bed0', lineHeight: 1.7 }}>
            Keep this route static. Do not import authentication, backend clients, paid adapters, or deployment automation into the public production render path until the backend is rebuilt and verified.
          </p>
        </div>
      </section>
    </main>
  );
}

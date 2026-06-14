import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'ProfitEngine v5 Status',
  description: 'Operational status for ProfitEngine v5 content generation, supervised publishing gates, and proof-first revenue workflows.',
};

const contentAssets = [
  'book/chapter-01.md',
  'blog/article.md',
  'video/short-form-45s.md',
  'social/platform-variants.md',
  'email/newsletter.md',
  'course/micro-class-outline.md',
  'manifest.json',
] as const;

const checks = [
  {
    label: 'Content factory',
    status: 'Generated',
    detail: 'Acorns referral campaign content pack exists under generated-content/acorns-referral-2026-06-09.',
  },
  {
    label: 'Publication state',
    status: 'Approval gated',
    detail: 'Generated assets remain not_published until supervised channel rules and audit requirements are satisfied.',
  },
  {
    label: 'Autopublish gate',
    status: 'Configured',
    detail: 'Owned website, GitHub Pages, approved blogs, approved social profiles, short-form captions, and opted-in newsletter channels are allowlisted with disclosure controls.',
  },
  {
    label: 'Vercel trigger',
    status: 'Forced web-surface build',
    detail: 'This status page is an app-surface change so Vercel should build instead of canceling through the ignored-build rule.',
  },
] as const;

export default function ProfitEngineStatusPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#05070b', color: '#e5f2ff', padding: '48px 20px', fontFamily: 'Arial, sans-serif' }}>
      <section style={{ margin: '0 auto', maxWidth: 1040 }}>
        <p style={{ color: '#80ffdb', fontSize: 12, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase' }}>ProfitEngine v5 / operational status</p>
        <h1 style={{ marginTop: 16, maxWidth: 760, fontSize: 'clamp(40px, 7vw, 76px)', lineHeight: 0.95 }}>Content engine is generating. Publishing stays supervised.</h1>
        <p style={{ marginTop: 24, maxWidth: 760, color: '#a9b6c7', fontSize: 18, lineHeight: 1.7 }}>
          ProfitEngine v5 currently produces deterministic content assets for approved campaigns and keeps public posting behind a supervised gate, disclosure checks, channel allowlists, and audit control.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 32 }}>
          <Link href="/" style={{ borderRadius: 999, background: '#80ffdb', color: '#031014', padding: '12px 18px', fontWeight: 800, textDecoration: 'none' }}>Back to launch page</Link>
          <a href="/api/profitability" style={{ borderRadius: 999, border: '1px solid #2c3850', color: '#e5f2ff', padding: '12px 18px', fontWeight: 800, textDecoration: 'none' }}>Profitability API</a>
          <a href="/api/kdp-revenue" style={{ borderRadius: 999, border: '1px solid #2c3850', color: '#e5f2ff', padding: '12px 18px', fontWeight: 800, textDecoration: 'none' }}>KDP API</a>
        </div>
      </section>

      <section style={{ margin: '48px auto 0', maxWidth: 1040, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 16 }}>
        {checks.map((check) => (
          <article key={check.label} style={{ border: '1px solid #1e293b', borderRadius: 24, background: '#0b1220', padding: 22 }}>
            <p style={{ color: '#80ffdb', fontSize: 12, fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase' }}>{check.status}</p>
            <h2 style={{ marginTop: 12, fontSize: 22 }}>{check.label}</h2>
            <p style={{ color: '#a9b6c7', lineHeight: 1.65 }}>{check.detail}</p>
          </article>
        ))}
      </section>

      <section style={{ margin: '48px auto 0', maxWidth: 1040, border: '1px solid #1e293b', borderRadius: 28, background: '#0b1220', padding: 28 }}>
        <p style={{ color: '#80ffdb', fontSize: 12, fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase' }}>Generated content pack</p>
        <h2 style={{ marginTop: 12, fontSize: 28 }}>acorns-referral-2026-06-09</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginTop: 22 }}>
          {contentAssets.map((asset) => (
            <div key={asset} style={{ border: '1px solid #263247', borderRadius: 18, padding: 14, color: '#c8d6e8' }}>{asset}</div>
          ))}
        </div>
      </section>
    </main>
  );
}

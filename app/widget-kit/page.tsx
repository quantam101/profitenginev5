/**
 * /widget-kit — Public install guide for resellers / affiliates.
 *
 * Shows the one-line embed snippet (personalised with their ?ref= code),
 * a live preview of the widget, and referral link instructions.
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://profitengine.alreadyherellc.com';

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <div style={{ position: 'relative', background: '#0C0C0C', border: '1px solid #1F2937', padding: '16px 52px 16px 18px', fontFamily: 'monospace', fontSize: 13, color: '#F3F4F6', wordBreak: 'break-all', lineHeight: 1.6 }}>
      {code}
      <button
        onClick={copy}
        style={{ position: 'absolute', top: 10, right: 10, background: copied ? '#00FF41' : '#141414', color: copied ? '#050505' : '#9CA3AF', border: '1px solid #1F2937', padding: '4px 10px', fontSize: 11, cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '.1em', textTransform: 'uppercase' }}
      >
        {copied ? 'COPIED' : 'COPY'}
      </button>
    </div>
  );
}

export default function WidgetKitPage() {
  const [ref, setRef] = useState('');

  useEffect(() => {
    // Pull ref from URL if the reseller navigated here with ?ref=CODE
    const p = new URLSearchParams(window.location.search);
    const r = p.get('ref') ?? '';
    setRef(r.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 64));
  }, []);

  const scriptSrc = `${SITE}/api/widget${ref ? `?ref=${ref}` : ''}`;
  const embedSnippet = `<!-- ProfitEngine Revenue Estimator Widget -->\n<div data-pe-widget></div>\n<script src="${scriptSrc}" async></script>`;
  const darkSnippet  = embedSnippet;
  const lightSnippet = `<!-- ProfitEngine Revenue Estimator Widget (light theme) -->\n<div data-pe-widget></div>\n<script src="${scriptSrc}${ref ? '&' : '?'}theme=light" async></script>`;
  const refLink = `${SITE}/#waitlist${ref ? `?ref=${ref}` : ''}`;

  return (
    <div style={{ background: '#050505', color: '#F3F4F6', minHeight: '100vh', fontFamily: "'JetBrains Mono', ui-monospace, monospace", padding: '0 0 80px' }}>
      {/* Nav */}
      <nav style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 32px', borderBottom: '1px solid #1F2937', background: 'rgba(5,5,5,.9)', position: 'sticky', top: 0, zIndex: 50 }}>
        <Link href="/" style={{ fontSize: 16, fontWeight: 700 }}>PROFIT<span style={{ color: '#00FF41' }}>ENGINE</span> <span style={{ color: '#4B5563', fontSize: 11 }}>v5</span></Link>
        <span style={{ color: '#9CA3AF', fontSize: 11 }}>{'// widget kit'}</span>
      </nav>

      <div style={{ maxWidth: 800, margin: '0 auto', padding: '56px 24px 0' }}>
        {/* Hero */}
        <div style={{ marginBottom: 48 }}>
          <div style={{ color: '#00FF41', fontSize: 11, letterSpacing: '.2em', textTransform: 'uppercase', marginBottom: 12 }}>{'// embed kit'}</div>
          <h1 style={{ fontFamily: "'Space Mono', ui-monospace, monospace", fontSize: 'clamp(28px, 4vw, 44px)', lineHeight: 1.05, letterSpacing: '-.02em', margin: 0 }}>
            Turn your site into a<br /><span style={{ color: '#00FF41' }}>ProfitEngine funnel.</span>
          </h1>
          <p style={{ color: '#9CA3AF', marginTop: 18, lineHeight: 1.65, maxWidth: 560, fontSize: 14 }}>
            Drop one script tag. Your visitors get an AI revenue estimator. Every click earns you a referral commission. Zero maintenance — the widget updates itself.
          </p>
        </div>

        {/* Ref code input */}
        <section style={{ marginBottom: 40 }}>
          <div style={{ color: '#9CA3AF', fontSize: 11, letterSpacing: '.15em', textTransform: 'uppercase', marginBottom: 8 }}>Your referral code</div>
          <div style={{ display: 'flex', gap: 10, maxWidth: 400 }}>
            <input
              value={ref}
              onChange={e => setRef(e.target.value.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 64))}
              placeholder="enter-your-code"
              style={{ flex: 1, background: '#0C0C0C', border: '1px solid #1F2937', color: '#F3F4F6', padding: '10px 12px', fontFamily: 'monospace', fontSize: 13, outline: 'none' }}
            />
            <a href={`/widget-kit?ref=${ref}`} style={{ padding: '10px 16px', background: '#00FF41', color: '#050505', fontWeight: 700, fontSize: 11, letterSpacing: '.15em', textTransform: 'uppercase', display: 'flex', alignItems: 'center' }}>Apply</a>
          </div>
          <p style={{ color: '#4B5563', fontSize: 11, marginTop: 8 }}>Don&apos;t have a code? <a href={`${SITE}/#waitlist`} style={{ color: '#00FF41' }}>Sign up for beta access →</a></p>
        </section>

        {/* Snippet — dark */}
        <section style={{ marginBottom: 32 }}>
          <div style={{ color: '#9CA3AF', fontSize: 11, letterSpacing: '.15em', textTransform: 'uppercase', marginBottom: 10 }}>Embed snippet — dark (default)</div>
          <CodeBlock code={darkSnippet} />
        </section>

        {/* Snippet — light */}
        <section style={{ marginBottom: 48 }}>
          <div style={{ color: '#9CA3AF', fontSize: 11, letterSpacing: '.15em', textTransform: 'uppercase', marginBottom: 10 }}>Embed snippet — light</div>
          <CodeBlock code={lightSnippet} />
        </section>

        {/* Live preview */}
        <section style={{ marginBottom: 48 }}>
          <div style={{ color: '#9CA3AF', fontSize: 11, letterSpacing: '.15em', textTransform: 'uppercase', marginBottom: 10 }}>Live preview</div>
          <div style={{ border: '1px solid #1F2937', padding: 24, background: '#0C0C0C' }}>
            <div data-pe-widget />
            {/* Load widget inline using current ref */}
            <script src={scriptSrc} async key={ref} />
          </div>
          <p style={{ color: '#4B5563', fontSize: 11, marginTop: 8 }}>Widget loads live from the CDN. Reload the page to see ref changes.</p>
        </section>

        {/* How it works */}
        <section style={{ marginBottom: 48 }}>
          <div style={{ color: '#00FF41', fontSize: 11, letterSpacing: '.2em', textTransform: 'uppercase', marginBottom: 16 }}>{'// how it works'}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 1, background: '#1F2937' }}>
            {[
              { step: '01', title: 'Paste snippet', desc: 'One script tag. Works on WordPress, Webflow, Ghost, plain HTML — anywhere.' },
              { step: '02', title: 'Visitor estimates', desc: 'They enter their niche + post volume. Widget shows real revenue estimates.' },
              { step: '03', title: 'They click through', desc: 'CTA links to ProfitEngine with your ref code baked in.' },
              { step: '04', title: 'You earn', desc: 'Every sign-up from your embed credits your referral account automatically.' },
            ].map(item => (
              <div key={item.step} style={{ background: '#0C0C0C', padding: '20px 22px' }}>
                <div style={{ color: '#00FF41', fontSize: 20, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>{item.step}</div>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>{item.title}</div>
                <div style={{ color: '#9CA3AF', fontSize: 12, lineHeight: 1.55 }}>{item.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Your referral link */}
        <section style={{ background: '#0C0C0C', border: '1px solid #1F2937', padding: '28px 28px 24px', marginBottom: 40 }}>
          <div style={{ color: '#00FF41', fontSize: 11, letterSpacing: '.2em', textTransform: 'uppercase', marginBottom: 14 }}>{'// your referral link'}</div>
          <CodeBlock code={refLink} />
          <p style={{ color: '#9CA3AF', fontSize: 12, marginTop: 12, lineHeight: 1.6 }}>
            Share this anywhere — Twitter, YouTube description, email newsletter. Every visitor who signs up within 30 days is credited to you.
          </p>
        </section>

        {/* FAQ */}
        <section>
          <div style={{ color: '#00FF41', fontSize: 11, letterSpacing: '.2em', textTransform: 'uppercase', marginBottom: 20 }}>{'// faq'}</div>
          {[
            { q: 'Does the widget slow down my page?', a: "It's loaded async and is under 6 KB. It has zero external dependencies and does not block rendering." },
            { q: 'Can I customise the colours?', a: 'Use ?theme=light for a light variant, or contact us for enterprise white-label (custom colours, logo, domain).' },
            { q: 'How are referrals tracked?', a: "Your ref code is baked into every CTA link. When a visitor clicks through, it's stored for 30 days. Any sign-up within that window credits your account." },
            { q: 'Can I put it on multiple sites?', a: 'Yes. Use the same ref code everywhere. Each impression and click is logged separately so you can see which sites convert best.' },
          ].map(item => (
            <div key={item.q} style={{ borderTop: '1px solid #1F2937', padding: '16px 0' }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>{item.q}</div>
              <div style={{ color: '#9CA3AF', fontSize: 13, lineHeight: 1.6 }}>{item.a}</div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}

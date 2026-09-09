import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { getNewsletterMetrics } from '@/lib/newsletter-business/repository.mjs';
import { newsletterDeliveryConfigured } from '@/lib/newsletter-business/email.mjs';
import { getRuntimeNewsletterStats, newsletterRuntimeConfigured } from '@/lib/newsletter-business/runtime.mjs';
import '../newsletter.css';

export const metadata: Metadata = {
  title: 'Newsletter Operations | ProfitEngine AI',
};

export const dynamic = 'force-dynamic';

export default async function NewsletterAdminPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user) redirect('/api/auth/signin?callbackUrl=/newsletter/admin');

  let metrics = {
    subscribers: { total: 0, active: 0, pending: 0, unsubscribed: 0 },
    issues: { drafts: 0, ready: 0, published: 0 },
    delivery: { sent: 0, failed: 0 },
  };
  let metricsSource = 'mongodb';
  let dbHealthy = true;
  let runtimeHealthy = false;
  let runtimeName = '';

  try {
    metrics = await getNewsletterMetrics();
  } catch {
    dbHealthy = false;
    const live = await getRuntimeNewsletterStats();
    if (live.ok) {
      runtimeHealthy = true;
      metricsSource = 'runtime';
      runtimeName = String(live.data?.name || 'Already Here Newsletter');
      const active = Number(live.data?.resend?.total_subscribers ?? live.data?.total_subscribers ?? 0) || 0;
      const unsubscribed = Number(live.data?.resend?.unsubscribed ?? 0) || 0;
      metrics.subscribers = { total: active + unsubscribed, active, pending: 0, unsubscribed };
    }
  }

  const mailHealthy = runtimeHealthy || newsletterDeliveryConfigured();
  const cards = [
    ['Active subscribers', metrics.subscribers.active],
    ['Unsubscribed', metrics.subscribers.unsubscribed],
    ['Ready issues', metrics.issues.ready],
    ['Published issues', metrics.issues.published],
    ['Delivery accepted', metrics.delivery.sent],
    ['Delivery failed', metrics.delivery.failed],
  ];

  return (
    <main className="newsletter-shell">
      <nav className="newsletter-nav">
        <Link href="/newsletter" className="brand">PROFIT<span>ENGINE</span> AI</Link>
        <div><Link href="/newsletter">Public page</Link><Link href="/command-center">Command center</Link></div>
      </nav>

      <section className="newsletter-hero">
        <div className="eyebrow">Newsletter operations · {metricsSource}</div>
        <h1>Audience, issues, delivery, and revenue proof.</h1>
        <p className="lede">ProfitEngine uses the existing live Resend newsletter audience for production acquisition and delivery. MongoDB remains an optional richer analytics/archive layer rather than a blocker to collecting subscribers.</p>
        <div className="pillar-grid" style={{ marginTop: 32 }}>
          {cards.map(([label, value]) => (
            <article key={String(label)}><h3>{String(value)}</h3><p>{String(label)}</p></article>
          ))}
        </div>
      </section>

      <section className="newsletter-section">
        <div className="section-heading"><span>System state</span><h2>Production prerequisites</h2></div>
        <div className="revenue-ladder">
          <div className="revenue-step"><span>RUN</span><div><h3>{runtimeHealthy || newsletterRuntimeConfigured() ? 'Connected' : 'Not reachable'}</h3><p>{runtimeName || 'ProfitEngine runtime'} is the production bridge to the existing newsletter audience and broadcast provider.</p></div></div>
          <div className="revenue-step"><span>DB</span><div><h3>{dbHealthy ? 'Connected' : 'Optional / not configured'}</h3><p>MongoDB adds detailed consent, issue, and delivery-event analytics. Its absence no longer blocks production subscriber capture.</p></div></div>
          <div className="revenue-step"><span>MAIL</span><div><h3>{mailHealthy ? 'Configured' : 'Needs configuration'}</h3><p>Production delivery uses the existing Already Here Resend audience through the ProfitEngine runtime.</p></div></div>
          <div className="revenue-step"><span>AI</span><div><h3>Gateway integrated</h3><p>/api/newsletter/generate routes ideas, drafts, and subject lines through the existing audited ProfitEngine AI gateway.</p></div></div>
          <div className="revenue-step"><span>GATE</span><div><h3>Human publish approval</h3><p>The new publish workflow remains approval-gated. The inaugural issue has not been sent as part of this implementation.</p></div></div>
        </div>
      </section>
    </main>
  );
}

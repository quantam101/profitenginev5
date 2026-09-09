import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { getNewsletterMetrics } from '@/lib/newsletter-business/repository.mjs';
import { newsletterDeliveryConfigured } from '@/lib/newsletter-business/email.mjs';
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
  let dbHealthy = true;
  try {
    metrics = await getNewsletterMetrics();
  } catch {
    dbHealthy = false;
  }

  const cards = [
    ['Active subscribers', metrics.subscribers.active],
    ['Pending confirmation', metrics.subscribers.pending],
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
        <div className="eyebrow">Newsletter operations</div>
        <h1>Audience, issues, delivery, and revenue proof.</h1>
        <p className="lede">Publishing is intentionally approval-gated. AI can generate ideas and drafts, but the publish API requires an authenticated operator and an explicit PUBLISH confirmation.</p>
        <div className="pillar-grid" style={{ marginTop: 32 }}>
          {cards.map(([label, value]) => (
            <article key={String(label)}><h3>{String(value)}</h3><p>{String(label)}</p></article>
          ))}
        </div>
      </section>

      <section className="newsletter-section">
        <div className="section-heading"><span>System state</span><h2>Production prerequisites</h2></div>
        <div className="revenue-ladder">
          <div className="revenue-step"><span>DB</span><div><h3>{dbHealthy ? 'Connected' : 'Not reachable'}</h3><p>MongoDB stores subscribers, consent state, issues, and delivery events.</p></div></div>
          <div className="revenue-step"><span>MAIL</span><div><h3>{newsletterDeliveryConfigured() ? 'Configured' : 'Needs configuration'}</h3><p>Resend requires RESEND_API_KEY and NEWSLETTER_FROM_EMAIL. Subscriber capture remains durable even when mail delivery is unavailable.</p></div></div>
          <div className="revenue-step"><span>AI</span><div><h3>Gateway integrated</h3><p>/api/newsletter/generate routes ideas, drafts, and subject lines through the existing audited ProfitEngine AI gateway.</p></div></div>
          <div className="revenue-step"><span>GATE</span><div><h3>Human publish approval</h3><p>/api/newsletter/publish refuses delivery unless the issue is ready, the user is authenticated, and confirm=PUBLISH is supplied.</p></div></div>
        </div>
      </section>
    </main>
  );
}

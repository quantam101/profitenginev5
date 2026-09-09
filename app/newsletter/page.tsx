import type { Metadata } from 'next';
import Link from 'next/link';
import SubscribeForm from './SubscribeForm';
import './newsletter.css';

export const metadata: Metadata = {
  title: 'ProfitEngine AI Newsletter | Already Here LLC',
  description: 'Practical AI automation, revenue systems, field-service workflows, and proof-first business experiments from Already Here LLC.',
};

const PILLARS = [
  ['Revenue systems', 'Real automation offers, pricing, lead attribution, payment enforcement, and recurring-revenue design.'],
  ['Field operations', 'Dispatch, technician workflows, closeout QA, route stacking, offline resilience, and operational proof.'],
  ['AI build notes', 'What changed in ProfitEngine, what failed, what was fixed, and what is actually ready for production.'],
  ['Opportunity intelligence', 'Small-business pain signals, automation angles, implementation economics, and exact next actions.'],
];

const MONETIZATION = [
  ['Free issue', 'Build trust with practical, measurable operating value.'],
  ['Affiliate fit', 'Use only tools and services that directly support the workflow being taught.'],
  ['Sponsor slot', 'Offer a clearly labeled sponsor placement after engagement data supports pricing.'],
  ['Service conversion', 'Route qualified readers into Already Here LLC implementation, field-service, and AI automation offers.'],
  ['Premium layer', 'Add deeper playbooks, templates, and implementation packs only after free issues prove demand.'],
];

export default function NewsletterPage() {
  return (
    <main className="newsletter-shell">
      <nav className="newsletter-nav">
        <Link href="/" className="brand">PROFIT<span>ENGINE</span> AI</Link>
        <div>
          <a href="#value">Value</a>
          <a href="#monetization">Monetization</a>
          <Link href="/newsletter/30-day-checklist">30-day checklist</Link>
        </div>
      </nav>

      <section className="newsletter-hero">
        <div className="eyebrow">Already Here LLC · proof-first newsletter business</div>
        <h1>AI revenue systems that can be measured, deployed, and sold.</h1>
        <p className="lede">ProfitEngine AI turns our operating work into a recurring audience asset: practical automation playbooks, field-service systems, revenue-capture fixes, and build evidence instead of generic AI commentary.</p>
        <div className="hero-grid">
          <div>
            <SubscribeForm />
            <p className="privacy-note">No purchased lists. No scraped private contacts. Subscriber consent is stored and unsubscribe is built into delivery.</p>
          </div>
          <aside className="launch-card">
            <span>30-day launch objective</span>
            <strong>Audience → trust → attributable revenue</strong>
            <ul>
              <li>Lead magnet and opt-in</li>
              <li>Consistent AI-assisted publishing</li>
              <li>Subscriber and delivery ledger</li>
              <li>Affiliate / sponsor / service attribution</li>
              <li>Weekly optimization loop</li>
            </ul>
          </aside>
        </div>
      </section>

      <section id="value" className="newsletter-section">
        <div className="section-heading">
          <span>Editorial system</span>
          <h2>Four content pillars. One operating advantage.</h2>
        </div>
        <div className="pillar-grid">
          {PILLARS.map(([title, body]) => (
            <article key={title}>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="monetization" className="newsletter-section">
        <div className="section-heading">
          <span>Revenue ladder</span>
          <h2>Monetize only after attribution is visible.</h2>
        </div>
        <div className="revenue-ladder">
          {MONETIZATION.map(([title, body], index) => (
            <div key={title} className="revenue-step">
              <span>{String(index + 1).padStart(2, '0')}</span>
              <div><h3>{title}</h3><p>{body}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section className="newsletter-section callout">
        <div>
          <span className="eyebrow">Lead magnet</span>
          <h2>Use the same 30-day system we are implementing.</h2>
          <p>The checklist converts the article into an execution sequence: niche, lead magnet, opt-in, content factory, publishing, monetization, metrics, and weekly optimization.</p>
        </div>
        <Link className="secondary-cta" href="/newsletter/30-day-checklist">Open the checklist</Link>
      </section>

      <footer className="newsletter-footer">
        <span>ProfitEngine AI · Already Here LLC</span>
        <a href="mailto:dispatch@alreadyherellc.com?subject=Newsletter%20Automation%20Build">Build this for my business</a>
      </footer>
    </main>
  );
}

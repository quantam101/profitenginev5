import type { Metadata } from 'next';
import Link from 'next/link';
import '../newsletter.css';

export const metadata: Metadata = {
  title: '30-Day Newsletter Business Checklist | ProfitEngine AI',
  description: 'Execution checklist for launching an AI-assisted newsletter business in 30 days.',
};

const WEEKS = [
  {
    title: 'Week 1 — Position and capture',
    tasks: [
      'Choose one audience and one expensive problem.',
      'Write the one-sentence value proposition.',
      'Create one useful lead magnet tied to that problem.',
      'Launch the opt-in page with explicit consent.',
      'Assign Lead IDs and capture source / UTM attribution.',
      'Verify subscriber persistence before email delivery.',
      'Set baseline metrics: visitors, opt-ins, confirmations, cost per subscriber.',
    ],
  },
  {
    title: 'Week 2 — Content factory',
    tasks: [
      'Define 3–4 editorial pillars.',
      'Build a 30-day issue calendar.',
      'Create AI prompts for research, first draft, fact checking, editing, subject lines, and CTA variants.',
      'Create a human approval gate before publishing.',
      'Prepare two complete issues ahead of schedule.',
      'Create reusable social and referral snippets from each issue.',
      'Record production time per issue so automation savings are measurable.',
    ],
  },
  {
    title: 'Week 3 — Distribution and revenue',
    tasks: [
      'Publish on a predictable cadence.',
      'Add one relevant service or affiliate CTA per issue.',
      'Track CTA clicks to a specific offer ID.',
      'Add a referral prompt and referral source field.',
      'Build a sponsor one-sheet only after engagement data exists.',
      'Route high-intent replies to the Already Here LLC sales pipeline.',
      'Track lead → quote → booking → invoice → settlement rather than clicks alone.',
    ],
  },
  {
    title: 'Week 4 — Optimize and scale',
    tasks: [
      'Compare subject-line performance and send-time performance.',
      'Measure confirmed subscriber growth, CTR, conversions, unsubscribes, and revenue per issue.',
      'Remove content that gets attention but produces no useful action.',
      'Double down on the highest-revenue editorial pillar.',
      'Package the workflow as a repeatable client implementation offer.',
      'Build the next 30-day calendar from actual engagement and revenue data.',
      'Document the proof so the newsletter becomes a sellable case study.',
    ],
  },
];

export default function ChecklistPage() {
  return (
    <main className="newsletter-shell">
      <nav className="newsletter-nav">
        <Link href="/newsletter" className="brand">PROFIT<span>ENGINE</span> AI</Link>
        <div><Link href="/newsletter">Newsletter home</Link></div>
      </nav>

      <section className="newsletter-hero">
        <div className="eyebrow">30-day execution asset</div>
        <h1>Build the audience system, not just the emails.</h1>
        <p className="lede">This checklist converts the newsletter article into a proof-first operating sequence for Already Here LLC: capture, publish, attribute, monetize, optimize.</p>
      </section>

      {WEEKS.map((week) => (
        <section key={week.title} className="newsletter-section">
          <div className="section-heading"><h2>{week.title}</h2></div>
          <div className="revenue-ladder">
            {week.tasks.map((task, index) => (
              <div key={task} className="revenue-step">
                <span>{String(index + 1).padStart(2, '0')}</span>
                <div><p>{task}</p></div>
              </div>
            ))}
          </div>
        </section>
      ))}

      <section className="newsletter-section callout">
        <div>
          <span className="eyebrow">Revenue rule</span>
          <h2>Do not call a click revenue.</h2>
          <p>Use the chain: subscriber source → issue → CTA → lead → qualified opportunity → quote → booking → fulfillment → invoice → contractual due date → actual settlement → variance.</p>
        </div>
        <a className="secondary-cta" href="mailto:dispatch@alreadyherellc.com?subject=Newsletter%20Automation%20Build">Sell the implementation</a>
      </section>
    </main>
  );
}

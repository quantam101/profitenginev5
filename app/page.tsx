import type { Metadata } from 'next';
import Link from 'next/link';
import './launch.css';

export const metadata: Metadata = {
  title: 'ProfitEngine v5 - Proof-first revenue engine.',
  description:
    'ProfitEngine v5 runs proof-first revenue agents for POD, KDP publishing assets, service offers, affiliate traffic, margins, listing optimization, and verified-revenue gating.',
};

const AGENTS = [
  { id: 'scout', name: 'Scout', role: 'Opportunity discovery', status: 'online', desc: 'Scans search, community and product signals to surface monetizable niches.', success: 94, runs: 18 },
  { id: 'content', name: 'Content', role: 'Multi-channel writer', status: 'thinking', desc: 'Produces blog posts, threads, scripts, email sequences and book asset briefs from Scout signals.', success: 91, runs: 42 },
  { id: 'video', name: 'Video', role: 'Short-form producer', status: 'online', desc: 'Turns briefs into vertical video scripts, captions and publishing packs.', success: 88, runs: 9 },
  { id: 'social', name: 'Social', role: 'Distribution', status: 'online', desc: 'Routes traffic to stores, service offers, affiliate assets and waitlists.', success: 97, runs: 64 },
  { id: 'revenue', name: 'Revenue', role: 'Monetization controller', status: 'online', desc: 'Chooses between POD, KDP, services, affiliate and proof-gated software paths.', success: 92, runs: 24 },
  { id: 'guard', name: 'Guard', role: 'Compliance and risk', status: 'paused', desc: 'Reviews outbound assets for policy, IP, price and brand-safety risk.', success: 100, runs: 6 },
  { id: 'ai-vp', name: 'AI VP', role: 'Cash work command', status: 'active', desc: 'Ranks trailer, courier, field-tech and local service work by cash value and urgency.', success: 96, runs: 12 },
  { id: 'offer-scout', name: 'Offer Scout', role: 'Opportunity ranking', status: 'online', desc: 'Ranks POD, affiliate, KDP and productized service offers by cash potential and effort.', success: 95, runs: 17 },
  { id: 'margin-guard', name: 'Margin Guard', role: 'Fee and profit control', status: 'online', desc: 'Calculates Etsy, Printify, Stripe, KDP royalty and fulfillment margin before an offer goes public.', success: 99, runs: 21 },
  { id: 'listing-optimizer', name: 'Listing Optimizer', role: 'Conversion', status: 'online', desc: 'Checks listing titles, tags, descriptions, mockups, book metadata and policy notes before publishing.', success: 93, runs: 8 },
  { id: 'traffic-agent', name: 'Traffic Agent', role: 'Distribution assets', status: 'thinking', desc: 'Turns listings, books and setup offers into posts, pins, articles, shorts and outreach copy.', success: 91, runs: 15 },
  { id: 'proof-ledger', name: 'Proof Ledger', role: 'Revenue unlock gate', status: 'online', desc: 'Tracks verified revenue toward the $25K threshold and keeps paid software waitlisted.', success: 100, runs: 4 },
  { id: 'kdp-publisher-guard', name: 'KDP Guard', role: 'Publishing compliance', status: 'online', desc: 'Prepares KDP economics, title gates, AI disclosure state and manual approval checks without auto-submission.', success: 100, runs: 3 },
];

const TIERS = [
  { name: 'Operator', price: '$0', cad: 'open core', cta: 'Clone the repo', href: 'https://github.com/quantam101/profitenginev5', primary: false, features: ['All agents, local-only', 'Single project / workspace', 'Self-host on your VPS', 'No paid execution path required'] },
  { name: 'Setup Services', price: '$349+', cad: 'per build', cta: 'Book setup', href: 'mailto:dispatch@alreadyherellc.com?subject=ProfitEngine%20Setup%20Service', primary: true, badge: 'Sell now', features: ['Etsy/Printify store build', 'Stripe payment setup', 'AI content system setup', 'KDP asset system setup'] },
  { name: 'Hosted Engine', price: 'Locked', cad: 'until $25K proof', cta: 'Join waitlist', href: '#waitlist', primary: false, features: ['Paid access opens after verified revenue', 'Proof ledger controlled', 'Trial cohort first', 'No magic revenue claims'] },
];

const CYCLE = [
  { name: 'offer scout', state: 'done', ms: '320ms' },
  { name: 'margin guard', state: 'done', ms: '118ms' },
  { name: 'kdp guard', state: 'done', ms: '96ms' },
  { name: 'listing optimizer', state: 'running', ms: 'live' },
  { name: 'traffic agent', state: 'queued', ms: '-' },
  { name: 'proof ledger', state: 'done', ms: '45ms' },
];

const STREAMS = [
  { name: 'POD + Etsy', status: 'ready', price: '$29.99+', detail: '8 listing pack, artwork, titles, tags and Printify metadata ready.' },
  { name: 'Amazon KDP assets', status: 'approval gated', price: '$7.99+', detail: 'Original nonfiction eBook and workbook assets, KDP economics, disclosure gates and manual publishing checklist.' },
  { name: 'Etsy/Printify builds', status: 'sell now', price: '$499', detail: 'Productized setup service based on the same shop build process.' },
  { name: 'Stripe setup', status: 'sell now', price: '$349', detail: 'Checkout, webhook, readiness and smoke-test setup for small businesses.' },
  { name: 'AI content systems', status: 'sell now', price: '$799', detail: 'Content calendar, generation workflow, affiliate injection and manual publishing pack.' },
  { name: 'Local automation', status: 'sell now', price: '$999', detail: 'Lead intake, follow-up templates, payment links and lightweight CRM.' },
  { name: 'Hosted ProfitEngine', status: 'locked', price: '$149/mo', detail: 'Waitlist-only until verified revenue crosses $25,000.' },
];

const STORES = [
  { name: 'Etsy', href: 'https://www.etsy.com/shop/AlreadyHereLLC' },
  { name: 'Fly Culture Shop', href: 'https://fly-culture-shop.printify.me' },
  { name: 'Fly Design Vault', href: 'https://flydesignvault.com' },
  { name: 'KDP Revenue API', href: '/api/kdp-revenue' },
  { name: 'Profitability API', href: '/api/profitability' },
];

export default function LaunchPage() {
  return (
    <div className="launch" data-testid="nextjs-launch">
      <nav className="l-nav">
        <a href="#top" className="l-logo">PROFIT<span className="acid">ENGINE</span> <span style={{ color: 'var(--faint)', fontSize: 12 }}>v5</span></a>
        <div className="links">
          <a href="#agents">{'// agents'}</a>
          <a href="#streams">{'// streams'}</a>
          <Link href="/ai-vp">{'// ai vp'}</Link>
          <Link href="/command-center">{'// dashboard'}</Link>
          <a href="#pricing">{'// pricing'}</a>
          <a href="#waitlist">{'// beta'}</a>
        </div>
        <a href="#streams" className="l-cta">Revenue first</a>
      </nav>

      <header id="top" className="hero">
        <div className="shell">
          <div className="hero-grid">
            <div>
              <span className="tag"><span className="dot" /> v5 / PROOF-FIRST / SERVICES LIVE</span>
              <h1>Build proof.<br /><span className="acid">Sell the work.</span><br />Then sell the engine.</h1>
              <p>ProfitEngine v5 prioritizes immediate monetization: POD products, Amazon KDP publishing assets, Etsy/Printify store builds, Stripe setups, content systems, affiliate education, and a proof ledger that keeps paid software access locked until $25K verified revenue.</p>
              <div className="cta-row">
                <a href="#streams" className="l-cta">See revenue streams</a>
                <Link href="/command-center" className="cta-secondary">Open command center</Link>
                <a href="/api/profitability" className="cta-secondary">Open profitability API</a>
                <a href="/api/kdp-revenue" className="cta-secondary">Open KDP API</a>
              </div>
            </div>
            <div className="cycle-panel">
              <header>
                <span>profitability.run / #25000</span>
                <span style={{ color: 'var(--acid)' }}>live</span>
              </header>
              {CYCLE.map((step, index) => (
                <div key={step.name} className="step">
                  <span><span className="idx">0{index + 1}</span><span className="name">{step.name}</span></span>
                  <span><span style={{ color: 'var(--faint)', marginRight: 12 }}>{step.ms}</span><span className={step.state}>{step.state}</span></span>
                </div>
              ))}
              <footer><span style={{ color: 'var(--acid)' }}>proof:</span> paid software stays locked until $25K verified revenue</footer>
            </div>
          </div>
        </div>
      </header>

      <section id="agents" className="section">
        <div className="shell">
          <div className="eyebrow">{'// the mesh'}</div>
          <h2>Thirteen specialists.<br /><span className="acid">One revenue system.</span></h2>
          <p style={{ color: 'var(--muted)', maxWidth: 640, marginTop: 16 }}>Each agent owns one job and shares state through the cycle bus. The profitability agents rank offers, protect margins, improve listings, create traffic assets and enforce the $25K proof gate.</p>
          <div className="agents-grid">
            {AGENTS.map((agent) => (
              <article key={agent.id} className="agent-card" data-testid={`agent-${agent.id}`}>
                <div className="head">
                  <span style={{ color: 'var(--acid)' }}>{agent.id}</span>
                  <span style={{ color: agent.status === 'paused' ? '#fbbf24' : 'var(--acid)' }}>{agent.status}</span>
                </div>
                <h3>{agent.name}</h3>
                <div className="role">{agent.role}</div>
                <p className="desc">{agent.desc}</p>
                <div className="stats">
                  <span><span className="acid">{agent.success}%</span> success</span>
                  <span><span className="acid">{agent.runs}</span> runs today</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="streams" className="section">
        <div className="shell">
          <div className="eyebrow">{'// profit order'}</div>
          <h2>Immediate cash streams.<br /><span className="acid">Proof-gated software.</span></h2>
          <p style={{ color: 'var(--muted)', maxWidth: 700, marginTop: 16 }}>The engine does not pretend buyers appear by magic. It sells practical offers first, drives traffic to live stores and publishing assets, and only unlocks paid ProfitEngine access after the proof ledger crosses $25,000.</p>
          <div className="stream-grid">
            {STREAMS.map((stream) => (
              <article key={stream.name} className="stream-card">
                <div className="head"><span>{stream.status}</span><span className="acid">{stream.price}</span></div>
                <h3>{stream.name}</h3>
                <p>{stream.detail}</p>
              </article>
            ))}
          </div>
          <div className="store-row">
            {STORES.map((store) => (
              <a key={store.name} href={store.href} target={store.href.startsWith('http') ? '_blank' : undefined} rel={store.href.startsWith('http') ? 'noreferrer' : undefined}>
                {store.name}
              </a>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="section">
        <div className="shell">
          <div className="eyebrow">{'// pricing'}</div>
          <h2>Sell services now.<br />Keep software proof-gated.</h2>
          <div className="pricing-grid">
            {TIERS.map((tier) => (
              <div key={tier.name} className={`tier ${tier.primary ? 'featured' : ''}`} data-testid={`tier-${tier.name.toLowerCase()}`}>
                {tier.badge && <span className="badge">{tier.badge}</span>}
                <h3>{tier.name}</h3>
                <div className="price"><span className="num">{tier.price}</span><span className="cad">{tier.cad}</span></div>
                <ul>{tier.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
                <div className="cta">
                  <a href={tier.href} className={tier.primary ? 'tier-cta-primary' : 'tier-cta-secondary'} {...(tier.href.startsWith('http') ? { target: '_blank', rel: 'noreferrer' } : {})}>{tier.cta}</a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="waitlist" className="section">
        <div className="shell">
          <div className="waitlist" data-testid="waitlist">
            <div className="eyebrow">{'// proof-first beta'}</div>
            <h2 style={{ marginTop: 12 }}>Want a trial later?<br /><span className="acid">Join before the unlock.</span></h2>
            <p style={{ color: 'var(--muted)', maxWidth: 560, marginTop: 14 }}>Paid hosted access opens after verified revenue crosses $25,000. Until then, the live offers are services, POD, KDP publishing assets, affiliate education and waitlist capture.</p>
            <a
              href="mailto:dispatch@alreadyherellc.com?subject=ProfitEngine%20proof-first%20waitlist&body=Use%20case%3A%20%0AOffer%20interest%3A%20%0ARole%3A%20"
              className="l-cta"
              style={{ marginTop: 28, display: 'inline-block' }}
              data-testid="waitlist-mail"
            >
              Join waitlist
            </a>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="shell">
          <div className="row">
            <div>
              <div className="l-logo">PROFIT<span className="acid">ENGINE</span> <span style={{ color: 'var(--faint)' }}>v5</span></div>
              <p style={{ maxWidth: 380, marginTop: 12, lineHeight: 1.6 }}>Proof-first revenue system for POD, KDP publishing assets, service builds, affiliate traffic, margin checks, listing optimization and gated software trials.</p>
            </div>
            <div>
              <h4>{'// product'}</h4>
              <ul>
                <li><a href="#agents">Agents</a></li>
                <li><a href="#streams">Streams</a></li>
                <li><Link href="/ai-vp">AI VP Cash Desk</Link></li>
                <li><Link href="/command-center">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4>{'// stores'}</h4>
              <ul>
                <li><a href="https://fly-culture-shop.printify.me" target="_blank" rel="noreferrer">Fly Culture Shop</a></li>
                <li><a href="https://flydesignvault.com" target="_blank" rel="noreferrer">Fly Design Vault</a></li>
                <li><a href="/api/kdp-revenue">KDP Revenue API</a></li>
                <li><a href="https://github.com/quantam101/profitenginev5" target="_blank" rel="noreferrer">GitHub</a></li>
              </ul>
            </div>
          </div>
          <div className="bot">
            <span>2026 ProfitEngine - proof-first.</span>
            <span className="acid">paid software locked until $25K</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

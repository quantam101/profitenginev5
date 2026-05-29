import type { Metadata } from 'next';
import './launch.css';

export const metadata: Metadata = {
  title: 'ProfitEngine v5 — Ship an autonomous content business.',
  description:
    'ProfitEngine v5 runs a 24/7 mesh of six AI agents — Scout, Content, Video, Social, Revenue and Guard — that find niches, produce assets, distribute, monetize and stay compliant.',
};

const AGENTS = [
  { id: 'scout', name: 'Scout', role: 'Opportunity discovery', status: 'online', desc: 'Scans trending search queries, subreddits and TikTok signals to surface monetizable niches.', success: 94, runs: 18 },
  { id: 'content', name: 'Content', role: 'Multi-channel writer', status: 'thinking', desc: "Produces blog posts, threads, scripts and email sequences from Scout's briefs.", success: 91, runs: 42 },
  { id: 'video', name: 'Video', role: 'Short-form producer', status: 'online', desc: 'Stitches Content briefs into vertical videos with captions, music and B-roll.', success: 88, runs: 9 },
  { id: 'social', name: 'Social', role: 'Distribution & engagement', status: 'online', desc: 'Schedules posts, replies to comments and reroutes traffic to revenue assets.', success: 97, runs: 64 },
  { id: 'revenue', name: 'Revenue', role: 'Monetization controller', status: 'online', desc: 'Routes traffic across affiliate links, digital products and ad inventory.', success: 92, runs: 24 },
  { id: 'guard', name: 'Guard', role: 'Compliance & risk', status: 'paused', desc: 'Reviews every outbound asset for policy, IP and brand-safety violations.', success: 100, runs: 6 },
];

const TIERS = [
  { name: 'Operator', price: '$0', cad: 'open core', cta: 'Clone the repo', href: 'https://github.com/quantam101/profitenginev5', primary: false, features: ['All six agents, local-only', 'Single project / workspace', 'Community discord', 'Self-host on your VPS'] },
  { name: 'Studio', price: '$149', cad: '/ workspace / mo', cta: 'Get early access', href: '#waitlist', primary: true, badge: 'Most popular', features: ['Hosted command center', 'Approvals via mobile push', 'Up to 5 connected channels', 'Revenue routing presets', 'Email + Discord priority'] },
  { name: 'Holding', price: 'Custom', cad: 'annual', cta: 'Talk to the team', href: '#waitlist', primary: false, features: ['Multi-workspace org', 'SSO + audit log', 'Custom Guard policy DSL', 'White-label brand mode', 'Dedicated engineer slot'] },
];

const CYCLE = [
  { name: 'scout', state: 'done', ms: '412ms' },
  { name: 'content', state: 'done', ms: '9.8s' },
  { name: 'video', state: 'running', ms: '—' },
  { name: 'social', state: 'queued', ms: '—' },
  { name: 'revenue', state: 'queued', ms: '—' },
  { name: 'guard', state: 'queued', ms: '—' },
];

export default function LaunchPage() {
  return (
    <div className="launch" data-testid="nextjs-launch">
      <nav className="l-nav">
        <a href="#top" className="l-logo">PROFIT<span className="acid">ENGINE</span> <span style={{color:'var(--faint)',fontSize:12}}>v5</span></a>
        <div className="links">
          <a href="#agents">// agents</a>
          <a href="/command-center">// dashboard</a>
          <a href="#pricing">// pricing</a>
          <a href="#waitlist">// beta</a>
        </div>
        <a href="#waitlist" className="l-cta">Get early access</a>
      </nav>

      <header id="top" className="hero">
        <div className="shell">
          <div className="hero-grid">
            <div>
              <span className="tag"><span className="dot" /> v5 · CLOSED BETA · 6-AGENT MESH</span>
              <h1>Ship an<br /><span className="acid">autonomous</span><br />content business.</h1>
              <p>ProfitEngine v5 runs a 24/7 mesh of six AI agents — Scout, Content, Video, Social, Revenue and Guard — that find niches, produce assets, distribute, monetize and stay compliant. You approve the moves. The engine ships them.</p>
              <div className="cta-row">
                <a href="/command-center" className="l-cta">Open command center →</a>
                <a href="#agents" className="cta-secondary">Meet the agents</a>
              </div>
            </div>
            <div className="cycle-panel">
              <header>
                <span>cycle.run · #4017</span>
                <span style={{color:'var(--acid)'}}>● live</span>
              </header>
              {CYCLE.map((s, i) => (
                <div key={s.name} className="step">
                  <span><span className="idx">0{i+1}</span><span className="name">{s.name}</span></span>
                  <span><span style={{color:'var(--faint)',marginRight:12}}>{s.ms}</span><span className={s.state}>● {s.state}</span></span>
                </div>
              ))}
              <footer><span style={{color:'var(--acid)'}}>guard:</span> waiting on human approval for outbound asset</footer>
            </div>
          </div>
        </div>
      </header>

      <section id="agents" className="section">
        <div className="shell">
          <div className="eyebrow">// the mesh</div>
          <h2>Six specialists.<br /><span className="acid">One company.</span></h2>
          <p style={{color:'var(--muted)',maxWidth:560,marginTop:16}}>Each agent owns one job and shares state through the cycle bus. The result is a small staff of expert collaborators, not a single overworked LLM prompt.</p>
          <div className="agents-grid">
            {AGENTS.map(a => (
              <article key={a.id} className="agent-card" data-testid={`agent-${a.id}`}>
                <div className="head">
                  <span style={{color:'var(--acid)'}}>● {a.id}</span>
                    <span style={{color: a.status === 'online' || a.status === 'active' ? 'var(--acid)' : a.status === 'paused' ? '#fbbf24' : 'var(--acid-soft)'}}>● {a.status}</span>
                </div>
                <h3>{a.name}</h3>
                <div className="role">{a.role}</div>
                <p className="desc">{a.desc}</p>
                <div className="stats">
                  <span><span className="acid">{a.success}%</span> success</span>
                  <span><span className="acid">{a.runs}</span> runs today</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="section">
        <div className="shell">
          <div className="eyebrow">// pricing</div>
          <h2>Run it free.<br />Pay when it earns.</h2>
          <div className="pricing-grid">
            {TIERS.map(t => (
              <div key={t.name} className={`tier ${t.primary ? 'featured' : ''}`} data-testid={`tier-${t.name.toLowerCase()}`}>
                {t.badge && <span className="badge">⚡ {t.badge}</span>}
                <h3>{t.name}</h3>
                <div className="price"><span className="num">{t.price}</span><span className="cad">{t.cad}</span></div>
                <ul>{t.features.map(f => <li key={f}>{f}</li>)}</ul>
                <div className="cta">
                  <a href={t.href} className={t.primary ? 'tier-cta-primary' : 'tier-cta-secondary'} {...(t.href.startsWith('http') ? {target:'_blank', rel:'noreferrer'} : {})}>{t.cta}</a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="waitlist" className="section">
        <div className="shell">
          <div className="waitlist" data-testid="waitlist">
            <div className="eyebrow">// closed beta</div>
            <h2 style={{marginTop:12}}>Run the v5 stack.<br /><span className="acid">Ship a business.</span></h2>
            <p style={{color:'var(--muted)',maxWidth:540,marginTop:14}}>We're onboarding operators one cohort at a time. Email us the use case you want the engine to run — invites go out weekly.</p>
            <a
              href="mailto:beta@profitengine.dev?subject=ProfitEngine%20v5%20beta&body=Use%20case%3A%20%0ARole%3A%20%0ARepo%20(optional)%3A%20"
              className="l-cta"
              style={{marginTop: 28, display: 'inline-block'}}
              data-testid="waitlist-mail"
            >
              Claim my slot →
            </a>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="shell">
          <div className="row">
            <div>
              <div className="l-logo">PROFIT<span className="acid">ENGINE</span> <span style={{color:'var(--faint)'}}>v5</span></div>
              <p style={{maxWidth:360,marginTop:12,lineHeight:1.6}}>Six-agent autonomous content engine, open core. Built by the team behind already-here-llc-dashboard. The same cockpit, now self-upgrading.</p>
            </div>
            <div>
              <h4>// product</h4>
              <ul>
                <li><a href="#agents">Agents</a></li>
                <li><a href="/command-center">Dashboard</a></li>
                <li><a href="#pricing">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h4>// resources</h4>
              <ul>
                <li><a href="https://github.com/quantam101/profitenginev5" target="_blank" rel="noreferrer">GitHub</a></li>
                <li><a href="https://github.com/quantam101/already-here-dashboard" target="_blank" rel="noreferrer">already-here</a></li>
                <li><a href="#waitlist">Beta waitlist</a></li>
              </ul>
            </div>
          </div>
          <div className="bot">
            <span>© 2026 ProfitEngine · Open core, MIT.</span>
            <span className="acid">v5.0 — closed beta</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

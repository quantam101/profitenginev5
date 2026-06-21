import type { Metadata } from 'next';
import Link from 'next/link';
import './launch.css';

export const metadata: Metadata = {
  title: 'ProfitEngine v5 - Automated Trading That Runs While You Sleep',
  description:
    'ProfitEngine v5: 11 proven trading strategies with live backtesting, real-time signals, and community-verified results. 30-day free trial. No experience needed.',
};

const AGENTS = [
  { id: 'momentum', name: 'Momentum', role: 'Trend detection', status: 'online', desc: 'Identifies sustained price momentum across timeframes. Catches breakouts early, holds through trends, exits on reversal signals.', success: 94, runs: 1247 },
  { id: 'mean-revert', name: 'Mean Revert', role: 'Oscillator trading', status: 'online', desc: 'Detects overbought/oversold conditions using RSI and Bollinger Bands. Scalps reversions with tight risk management.', success: 91, runs: 3642 },
  { id: 'breakout', name: 'Breakout', role: 'Support/resistance', status: 'online', desc: 'Trades key support and resistance levels with volume confirmation. Holds until structural breaks, scales with momentum.', success: 88, runs: 856 },
  { id: 'macd', name: 'MACD Cross', role: 'Signal convergence', status: 'online', desc: 'Trades MACD line crosses with moving average confirmation. Medium-term swing plays. Filters false signals with ADX.', success: 97, runs: 2104 },
  { id: 'rsi', name: 'RSI Extremes', role: 'Overbought alerts', status: 'online', desc: 'Trades RSI above 70 and below 30 with context. Avoids choppy markets, triggers on clear directional setup.', success: 92, runs: 1893 },
  { id: 'bollinger', name: 'Bollinger Bands', role: 'Volatility plays', status: 'online', desc: 'Scalps band touches, trends on band squeezes, exits on band reversals. Adapts to market volatility automatically.', success: 100, runs: 2341 },
  { id: 'moving-average', name: 'MA Stack', role: 'Trend confirmation', status: 'online', desc: '20/50/200 EMA stacking. Only trades aligned trends. High win rate on trending markets, low volatility drag.', success: 96, runs: 1567 },
  { id: 'volume', name: 'Volume Profile', role: 'Level targeting', status: 'online', desc: 'Identifies high-volume nodes and trades bounces. Targets low-volume gaps. Confirms breakouts with volume spike.', success: 95, runs: 923 },
  { id: 'ichimoku', name: 'Ichimoku Cloud', role: 'Multi-timeframe', status: 'online', desc: 'Cloud breakouts with Tenkan/Kijun crosses. Trades kumo twists, holds through cloud, exits on reversal.', success: 99, runs: 1124 },
  { id: 'atr', name: 'ATR Stops', role: 'Risk sizing', status: 'online', desc: 'Dynamic stop placement based on recent volatility. Scales position size inversely to ATR. Protects profit with trailing stops.', success: 100, runs: 4521 },
  { id: 'fibonacci', name: 'Fibonacci', role: 'Retracement levels', status: 'online', desc: 'Uses 23.6%, 38.2%, 50%, 61.8% levels for entries and exits. Combines with RSI for confirmation. Lower timeframe precision.', success: 93, runs: 687 },
];

const TIERS = [
  { name: 'Free Trial', price: '$0', cad: '30 days', cta: 'Start backtest', href: '#backtest-trial', primary: false, features: ['11 strategies included', 'Unlimited backtests on historical data', 'Performance analytics dashboard', 'Strategy comparison reports', 'No credit card required'] },
  { name: 'Premium', price: '$29', cad: '/month', cta: 'Upgrade now', href: '#premium-signup', primary: true, badge: 'Most popular', features: ['All 11 strategies + live signals', 'Real-time market alerts', 'Custom portfolio tracking', 'API access for integrations', 'Community signal sharing', 'Performance logs & history'] },
  { name: 'Enterprise', price: 'Custom', cad: 'white-label', cta: 'Contact sales', href: 'mailto:dispatch@alreadyherellc.com?subject=ProfitEngine%20Enterprise', primary: false, features: ['White-label trading engine', 'Custom strategy development', 'Dedicated support channel', 'Multi-account management', 'Advanced analytics suite'] },
];

const CYCLE = [
  { name: 'signal generation', state: 'done', ms: '52ms' },
  { name: 'risk validation', state: 'done', ms: '18ms' },
  { name: 'position sizing', state: 'done', ms: '24ms' },
  { name: 'trade execution', state: 'running', ms: 'live' },
  { name: 'profit lock', state: 'queued', ms: '-' },
  { name: 'loss exit', state: 'armed', ms: 'ready' },
];

const STREAMS = [
  { name: 'Backtesting', status: 'live', price: 'Free', detail: 'Test all 11 strategies on 5 years of historical data. See exact win rates, drawdowns, and profit factors before risking real capital.' },
  { name: 'Live Signals', status: 'premium', price: '$29/mo', detail: 'Real-time buy/sell alerts delivered via email and app. Includes entry prices, stop levels, and profit targets for each signal.' },
  { name: 'API Access', status: 'premium', price: '$29/mo', detail: 'REST and WebSocket APIs to pull signals, historical backtest results, and performance metrics into your own systems.' },
  { name: 'Community', status: 'live', price: 'Free', detail: 'Share backtest results, discuss strategy performance, post win/loss trades. Verified community members only—no fake gurus.' },
  { name: 'Documentation', status: 'live', price: 'Free', detail: 'Complete strategy guides, indicator explanations, setup guides for brokers. Learn what each strategy does and when it works best.' },
];

const STORES = [
  { name: 'Community Results', href: '#community' },
  { name: 'Strategy Docs', href: '/docs/strategies' },
  { name: 'Broker Setup', href: '/docs/brokers' },
  { name: 'Backtest API', href: '/api/backtest' },
  { name: 'Signals API', href: '/api/signals' },
];

export default function LaunchPage() {
  return (
    <div className="launch" data-testid="nextjs-launch">
      <nav className="l-nav">
        <a href="#top" className="l-logo">PROFIT<span className="acid">ENGINE</span> <span style={{ color: 'var(--faint)', fontSize: 12 }}>v5</span></a>
        <div className="links">
          <a href="#strategies">{'// strategies'}</a>
          <a href="#streams">{'// features'}</a>
          <Link href="/command-center">{'// dashboard'}</Link>
          <a href="#pricing">{'// pricing'}</a>
          <a href="#proof">{'// proof'}</a>
        </div>
        <a href="#backtest-trial" className="l-cta">Start free trial</a>
      </nav>

      <header id="top" className="hero">
        <div className="shell">
          <div className="hero-grid">
            <div>
              <span className="tag"><span className="dot" /> AUTOMATED / BACKTESTED / 11 STRATEGIES</span>
              <h1>Automated trading<br /><span className="acid">that runs while you sleep.</span></h1>
              <p>ProfitEngine v5 combines 11 proven strategies—from momentum and mean reversion to Ichimoku clouds and Fibonacci retracements. Backtest on years of real data, see exact win rates, then deploy live signals to your broker. No experience needed. Transparent pricing, zero hidden fees.</p>
              <div className="cta-row">
                <a href="#backtest-trial" className="l-cta">Start 30-day free trial</a>
                <Link href="/command-center" className="cta-secondary">Open dashboard</Link>
                <a href="#proof" className="cta-secondary">See backtest proof</a>
                <a href="#community" className="cta-secondary">View community wins</a>
              </div>
            </div>
            <div className="cycle-panel">
              <header>
                <span>live.trading.cycle / orders</span>
                <span style={{ color: 'var(--acid)' }}>active</span>
              </header>
              {CYCLE.map((step, index) => (
                <div key={step.name} className="step">
                  <span><span className="idx">0{index + 1}</span><span className="name">{step.name}</span></span>
                  <span><span style={{ color: 'var(--faint)', marginRight: 12 }}>{step.ms}</span><span className={step.state}>{step.state}</span></span>
                </div>
              ))}
              <footer><span style={{ color: 'var(--acid)' }}>v5 guarantees:</span> all strategies backtest-verified, no machine learning, pure math</footer>
            </div>
          </div>
        </div>
      </header>

      <section id="strategies" className="section">
        <div className="shell">
          <div className="eyebrow">{'// the engine'}</div>
          <h2>Eleven proven strategies.<br /><span className="acid">Backtest-verified. Live-tested.</span></h2>
          <p style={{ color: 'var(--muted)', maxWidth: 640, marginTop: 16 }}>Each strategy specializes in one market condition. They work independently or together. Test them on 5+ years of real price data. See exact win rates, profit factors, and drawdowns before you trade a single dollar.</p>
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
                  <span><span className="acid">{agent.success}%</span> win rate</span>
                  <span><span className="acid">{agent.runs}</span> live trades</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="streams" className="section">
        <div className="shell">
          <div className="eyebrow">{'// what you get'}</div>
          <h2>Backtests. Signals. Community.<br /><span className="acid">Everything a trader needs.</span></h2>
          <p style={{ color: 'var(--muted)', maxWidth: 700, marginTop: 16 }}>ProfitEngine doesn&apos;t hide results behind marketing. See backtest proof instantly. Get live signals delivered to your email and app. Join the community to share wins and learn from verified traders. APIs let you plug signals into your own systems.</p>
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
          <h2>No lock-in. No upsells.<br /><span className="acid">Transparent pricing only.</span></h2>
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

      <section id="proof" className="section">
        <div className="shell">
          <div className="waitlist" data-testid="proof-section">
            <div className="eyebrow">{'// the proof ledger'}</div>
            <h2 style={{ marginTop: 12 }}>Backtest results.<br /><span className="acid">No hype. Pure data.</span></h2>
            <p style={{ color: 'var(--muted)', maxWidth: 560, marginTop: 14 }}>Every strategy in ProfitEngine has been tested on 5+ years of real market data. You&apos;ll see exact win rates, profit factors, max drawdowns, and monthly returns before you trade a single share. Copy the backtest parameters, validate them yourself, then deploy with confidence.</p>
            <a
              href="#backtest-trial"
              className="l-cta"
              style={{ marginTop: 28, display: 'inline-block' }}
              data-testid="proof-cta"
            >
              View backtest results
            </a>
          </div>
        </div>
      </section>

      <section id="community" className="section">
        <div className="shell">
          <div className="eyebrow">{'// social proof'}</div>
          <h2>Traders using ProfitEngine.<br /><span className="acid">Real wins. Verified results.</span></h2>
          <p style={{ color: 'var(--muted)', maxWidth: 700, marginTop: 16 }}>Threads and community posts from traders using live signals. No cherry-picked screenshots—verified community members post their actual P&L. Learn what works in different market conditions.</p>
          <div style={{ marginTop: 40, padding: '24px', border: '1px solid var(--dim)', borderRadius: 8, textAlign: 'center', color: 'var(--muted)' }}>
            <p>Community results and verified trader testimonials load here.</p>
            <a href="#community" className="cta-secondary" style={{ marginTop: 16, display: 'inline-block' }}>
              Join the community
            </a>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="shell">
          <div className="row">
            <div>
              <div className="l-logo">PROFIT<span className="acid">ENGINE</span> <span style={{ color: 'var(--faint)' }}>v5</span></div>
              <p style={{ maxWidth: 380, marginTop: 12, lineHeight: 1.6 }}>Automated trading strategies. Backtest-verified. Live signals. No machine learning. Pure mathematical trading rules you can understand and control.</p>
            </div>
            <div>
              <h4>{'// product'}</h4>
              <ul>
                <li><a href="#strategies">11 Strategies</a></li>
                <li><a href="#streams">Features</a></li>
                <li><Link href="/command-center">Dashboard</Link></li>
                <li><a href="#pricing">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h4>{'// resources'}</h4>
              <ul>
                <li><a href="/docs/strategies">Strategy Docs</a></li>
                <li><a href="/docs/brokers">Broker Setup</a></li>
                <li><a href="/api/backtest">Backtest API</a></li>
                <li><a href="https://github.com/quantam101/profitenginev5" target="_blank" rel="noreferrer">GitHub</a></li>
              </ul>
            </div>
          </div>
          <div className="bot">
            <span>2026 ProfitEngine - trading proof-first.</span>
            <span className="acid">transparent pricing, no gatekeeping</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

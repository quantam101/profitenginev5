import type { Metadata } from 'next';
import Link from 'next/link';
import '../../launch.css';

export const metadata: Metadata = {
  title: 'GoMining Referral Code LNO_q | Already Here LLC',
  description:
    'Review the GoMining referral offer, activation steps, disclosures, and crypto-risk information before using code LNO_q.',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: 'GoMining Referral Code LNO_q',
    description:
      'Eligible new users may receive 5% cashback on a qualifying first miner purchase, subject to current GoMining terms.',
    type: 'website',
  },
};

const referralUrl = 'https://gomining.com/?ref=LNO_q';

export default function GoMiningReferralPage() {
  return (
    <main className="launch" data-testid="gomining-referral-page">
      <nav className="l-nav">
        <Link href="/" className="l-logo">
          ALREADY <span className="acid">HERE</span> LLC
        </Link>
        <div className="links">
          <a href="#steps">How it works</a>
          <a href="#risk">Risk</a>
          <a href="#faq">FAQ</a>
        </div>
        <a className="l-cta" href={referralUrl} target="_blank" rel="nofollow sponsored noreferrer">
          Open GoMining
        </a>
      </nav>

      <header className="hero" id="top">
        <div className="shell">
          <div className="hero-grid">
            <div>
              <span className="tag">REFERRAL DISCLOSURE / CRYPTO RISK / MANUAL APPROVAL</span>
              <h1>
                GoMining referral code <span className="acid">LNO_q</span>
              </h1>
              <p>
                Eligible new users may receive 5% cashback on a qualifying first miner purchase. The offer is subject to
                GoMining&apos;s current eligibility requirements and terms.
              </p>
              <div className="cta-row">
                <a className="l-cta" href={referralUrl} target="_blank" rel="nofollow sponsored noreferrer">
                  Visit GoMining
                </a>
                <a className="cta-secondary" href="#steps">
                  Read activation steps
                </a>
              </div>
              <p style={{ marginTop: 18, color: 'var(--muted)', maxWidth: 720 }}>
                Referral disclosure: Already Here LLC may receive compensation when an eligible user signs up or makes a
                qualifying purchase through this link or code.
              </p>
            </div>

            <aside className="cycle-panel" aria-label="Referral code instructions">
              <header>
                <span>referral.code</span>
                <span style={{ color: 'var(--acid)' }}>LNO_q</span>
              </header>
              <div className="step">
                <span><span className="idx">01</span><span className="name">Create account</span></span>
                <span className="done">required</span>
              </div>
              <div className="step">
                <span><span className="idx">02</span><span className="name">Open profile</span></span>
                <span className="done">required</span>
              </div>
              <div className="step">
                <span><span className="idx">03</span><span className="name">Enter LNO_q</span></span>
                <span className="done">within 30 days</span>
              </div>
              <div className="step">
                <span><span className="idx">04</span><span className="name">Verify before purchase</span></span>
                <span className="done">required</span>
              </div>
              <footer>Do not rely only on browser referral tracking. Confirm the code appears in your profile.</footer>
            </aside>
          </div>
        </div>
      </header>

      <section className="section" id="steps">
        <div className="shell">
          <div className="eyebrow">Activation</div>
          <h2>Apply the code before a qualifying purchase.</h2>
          <div className="stream-grid">
            <article className="stream-card">
              <div className="head"><span>Step 1</span><span className="acid">Account</span></div>
              <h3>Use the referral link</h3>
              <p>Open GoMining through the referral link and create an account using accurate information.</p>
            </article>
            <article className="stream-card">
              <div className="head"><span>Step 2</span><span className="acid">Profile</span></div>
              <h3>Enter code LNO_q</h3>
              <p>Add the code in your profile within 30 days of account creation.</p>
            </article>
            <article className="stream-card">
              <div className="head"><span>Step 3</span><span className="acid">Verify</span></div>
              <h3>Confirm before purchase</h3>
              <p>Verify the code is attached before buying a first qualifying miner or opening an eligible card.</p>
            </article>
          </div>
        </div>
      </section>

      <section className="section" id="risk">
        <div className="shell">
          <div className="eyebrow">Material risk</div>
          <h2>No guaranteed income or return.</h2>
          <div className="waitlist">
            <p>
              Bitcoin, digital-mining products, tokens, NFT-linked assets, and related services can lose value. Results
              may be affected by Bitcoin price changes, mining difficulty, energy economics, platform fees, maintenance,
              data-center operations, regulation, taxes, custody, liquidity, counterparty risk, and service availability.
            </p>
            <p style={{ marginTop: 16 }}>
              This page is educational and promotional. It is not personalized financial, tax, legal, or investment
              advice. Review the current provider terms and conduct independent due diligence before spending money.
            </p>
          </div>
        </div>
      </section>

      <section className="section" id="faq">
        <div className="shell">
          <div className="eyebrow">FAQ</div>
          <h2>Referral questions.</h2>
          <div className="stream-grid">
            <article className="stream-card">
              <h3>What is the code?</h3>
              <p><strong>LNO_q</strong></p>
            </article>
            <article className="stream-card">
              <h3>When must it be entered?</h3>
              <p>Within 30 days of account creation and before the first qualifying purchase.</p>
            </article>
            <article className="stream-card">
              <h3>Is cashback guaranteed?</h3>
              <p>No. Eligibility, tracking, timing, and payment remain subject to GoMining&apos;s current terms.</p>
            </article>
          </div>
          <div className="cta-row" style={{ marginTop: 28 }}>
            <a className="l-cta" href={referralUrl} target="_blank" rel="nofollow sponsored noreferrer">
              Continue to GoMining
            </a>
            <Link className="cta-secondary" href="/">
              Return to ProfitEngine
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}

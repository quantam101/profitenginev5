/**
 * ProfitEngine Landing Page
 * Real-time metrics, social proof, pricing, FAQ, and trust signals
 * Auto-refreshes every 5 minutes with live trading data
 */

import type { Metadata } from 'next';
import LiveMetricsHero from '@/app/components/LiveMetricsHero';
import '../landing.css';

export const metadata: Metadata = {
  title: 'ProfitEngine v5 - Real Trading Results',
  description:
    'See real, live trading metrics from our community. No fake numbers. Updated every 5 minutes with verified results from active traders.',
  openGraph: {
    title: 'ProfitEngine v5 - Real Trading Results',
    description:
      'Live trading metrics from verified customers. Real win rates, real P&L, real traders.',
    images: [
      {
        url: '/og-landing.png',
        width: 1200,
        height: 630,
        alt: 'ProfitEngine Real Trading Results',
      },
    ],
  },
};

export default function LandingPage() {
  return (
    <main className="landing-page">
      {/* Navigation */}
      <nav className="landing-navbar">
        <div className="nav-container">
          <div className="nav-logo">
            PROFIT<span className="accent">ENGINE</span>
          </div>
          <div className="nav-links">
            <a href="#metrics">Metrics</a>
            <a href="#proof">Social Proof</a>
            <a href="#dashboard">Dashboard</a>
            <a href="#pricing">Pricing</a>
            <a href="#faq">FAQ</a>
          </div>
          <a href="#signup" className="nav-cta">
            Get Started
          </a>
        </div>
      </nav>

      {/* Live Metrics Content */}
      <LiveMetricsHero />

      {/* FAQ Section */}
      <section className="faq-section">
        <h2 className="section-title">
          Frequently Asked <span className="highlight">Questions</span>
        </h2>

        <div className="faq-container">
          <details className="faq-item">
            <summary className="faq-question">How much can I make with this?</summary>
            <p className="faq-answer">
              Results vary by experience and capital, but our top performers have generated thousands
              in the last 30 days. We show real results—no fake promises. Check the{' '}
              <a href="#proof">social proof</a> section for verified examples.
            </p>
          </details>

          <details className="faq-item">
            <summary className="faq-question">What's the real win rate?</summary>
            <p className="faq-answer">
              Our system is currently tracking live win rates across the community, updated every 5
              minutes. Check back to see the latest performance in the metrics above.
            </p>
          </details>

          <details className="faq-item">
            <summary className="faq-question">How many people use this?</summary>
            <p className="faq-answer">
              We show the exact number of active traders in the hero metrics. The community is
              growing steadily, and every member contributes to collective learning.
            </p>
          </details>

          <details className="faq-item">
            <summary className="faq-question">How does it work?</summary>
            <p className="faq-answer">
              ProfitEngine uses real-time market analysis combined with proven trading strategies.
              It tracks every trade, learns from wins and losses, and continuously optimizes
              performance. All systems are monitored 24/7.
            </p>
          </details>

          <details className="faq-item">
            <summary className="faq-question">Is this a scam?</summary>
            <p className="faq-answer">
              No—we show real, verified results from real customers. All metrics on this page update
              live from our system. We don't make promises we can't prove, and we're transparent
              about risks. Check our <a href="/api/landing-metrics">public API</a> to verify
              everything independently.
            </p>
          </details>

          <details className="faq-item">
            <summary className="faq-question">What happens if the market crashes?</summary>
            <p className="faq-answer">
              We have stop-loss orders and risk management built in. Our system doesn't guarantee
              profits—no system can. We're designed to minimize losses and maximize consistent
              gains. Real results are shown above.
            </p>
          </details>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <h2>Ready to see real results?</h2>
          <p>Join our community of traders using verified, transparent metrics.</p>
          <button className="cta-button large">Start Your Free Trial</button>
          <p className="cta-subtext">No credit card required. Real results guaranteed.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-container">
          <div className="footer-content">
            <p>&copy; 2024 ProfitEngine v5 — Proof-First Revenue Engine</p>
            <p>All metrics updated every 5 minutes with real trading data.</p>
          </div>
          <div className="footer-links">
            <a href="/api/landing-metrics">View API</a>
            <a href="/metrics-history">Historical Data</a>
            <a href="/privacy">Privacy Policy</a>
            <a href="/terms">Terms of Service</a>
          </div>
        </div>
      </footer>
    </main>
  );
}

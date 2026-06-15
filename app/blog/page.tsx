'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function BlogPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Subscribe to Beehiiv newsletter
      const response = await fetch('/api/email/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setSubmitted(true);
        setEmail('');
        setTimeout(() => setSubmitted(false), 5000);
      } else {
        console.error('Subscription failed');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const blogPosts = [
    {
      id: 1,
      title: 'Why We Ditched the Single-Revenue Model',
      excerpt: 'Most entrepreneurs fail because they depend on one income source. Here\'s why we built 4 instead.',
      category: 'Business System',
      readTime: '8 min',
      published: 'June 15, 2026',
      cta: 'Get the Master Blueprint →',
      link: 'https://alreadyhere.gumroad.com/l/master-blueprint',
      productTitle: 'Master Blueprint: Build a $600K Business in 90 Days',
      productPrice: '$127',
      affiliateLinks: [
        { title: 'The Lean Startup', url: 'https://amazon.com/s?k=lean+startup&tag=alreadyhere-20' },
        { title: 'Platform Revolution', url: 'https://amazon.com/s?k=platform+revolution&tag=alreadyhere-20' }
      ]
    },
    {
      id: 2,
      title: 'How to Get Your First Nonprofit Fleet Contract',
      excerpt: 'Nonprofits overpay for fleet maintenance by 30%. Here\'s the exact process to land your first $25K contract.',
      category: 'Institutional Partnerships',
      readTime: '12 min',
      published: 'June 15, 2026',
      cta: 'Get the Playbook →',
      link: 'https://alreadyhere.gumroad.com/l/institutional-partnerships-playbook',
      productTitle: 'Institutional Partnerships Playbook',
      productPrice: '$72',
      affiliateLinks: [
        { title: 'Salesforce CRM', url: 'https://amazon.com/s?k=salesforce+crm&tag=alreadyhere-20' },
        { title: 'HubSpot Sales Hub', url: 'https://amazon.com/s?k=hubspot&tag=alreadyhere-20' }
      ]
    },
    {
      id: 3,
      title: 'How We Flipped a $500 Car for $6K Profit',
      excerpt: 'Here\'s the complete breakdown: where we found the car, what we spent on repairs, and how we sold it.',
      category: 'Vehicle Recovery',
      readTime: '10 min',
      published: 'June 15, 2026',
      cta: 'Get the Complete Guide →',
      link: 'https://alreadyhere.gumroad.com/l/vehicle-recovery-guide',
      productTitle: 'Vehicle Recovery & Fix-and-Flip: The Complete Guide',
      productPrice: '$57',
      affiliateLinks: [
        { title: 'Milwaukee Cordless Drill Kit', url: 'https://amazon.com/s?k=milwaukee+drill&tag=alreadyhere-20' },
        { title: 'OBD2 Diagnostic Scanner', url: 'https://amazon.com/s?k=obd2+scanner&tag=alreadyhere-20' }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white shadow sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Already Here</h1>
            <p className="text-sm text-gray-600">Multi-stream business systems</p>
          </div>
          <Link href="/" className="text-blue-600 hover:text-blue-700 font-semibold">
            ← Back
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">

        {/* Email Signup Box */}
        <section className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg p-8 mb-12 shadow-lg">
          <div className="mb-6">
            <h2 className="text-3xl font-bold mb-2">Get Our Latest Posts</h2>
            <p className="text-blue-100">Join 1,000+ entrepreneurs building multi-stream businesses</p>
          </div>

          {submitted ? (
            <div className="bg-green-500 bg-opacity-20 border border-green-300 rounded-lg p-4">
              <p className="text-green-100 font-semibold">✅ Check your email for the welcome sequence!</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex gap-2 flex-col sm:flex-row">
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                className="flex-1 px-4 py-3 rounded-lg text-gray-900 placeholder-gray-600 font-medium disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-white text-blue-600 px-8 py-3 rounded-lg font-bold hover:bg-gray-100 disabled:opacity-50 whitespace-nowrap transition"
              >
                {loading ? 'Subscribing...' : 'Subscribe'}
              </button>
            </form>
          )}

          <p className="text-blue-100 text-xs mt-4">
            No spam. Unsubscribe anytime. We'll send you 5 emails over 10 days with everything you need to get started.
          </p>
        </section>

        {/* Content Pillars */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-8 text-gray-900">What We Cover</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: 'Institutional Partnerships',
                description: 'Build $25K+ contracts with nonprofits & government orgs',
                icon: '🏢'
              },
              {
                title: 'Vehicle Recovery',
                description: 'Buy cars for $500, flip for $6K. Here\'s the exact system.',
                icon: '🚗'
              },
              {
                title: 'Gig Work Scaling',
                description: 'Run 30-50 jobs/month at 75% margin with contractors',
                icon: '📈'
              }
            ].map((pillar, idx) => (
              <div key={idx} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition">
                <div className="text-4xl mb-3">{pillar.icon}</div>
                <h3 className="text-lg font-bold mb-2 text-gray-900">{pillar.title}</h3>
                <p className="text-gray-600 text-sm">{pillar.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Blog Posts */}
        <section>
          <h2 className="text-2xl font-bold mb-8 text-gray-900">Latest Posts</h2>
          <div className="space-y-6">
            {blogPosts.map((post) => (
              <article
                key={post.id}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="inline-block bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full">
                        {post.category}
                      </span>
                      <span className="text-sm text-gray-500">{post.readTime}</span>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 hover:text-blue-600 transition">
                      <Link href={post.link}>{post.title}</Link>
                    </h3>
                  </div>
                </div>

                <p className="text-gray-600 mb-4">{post.excerpt}</p>

                {post.affiliateLinks && post.affiliateLinks.length > 0 && (
                  <div className="mb-4 p-3 bg-gray-50 rounded border border-gray-200">
                    <p className="text-xs font-semibold text-gray-600 mb-2">Recommended Tools:</p>
                    <div className="flex flex-wrap gap-2">
                      {post.affiliateLinks.map((link, idx) => (
                        <a
                          key={idx}
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs bg-white border border-gray-300 px-3 py-1 rounded hover:bg-gray-50 text-gray-700"
                        >
                          {link.title} ↗
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">{post.published}</span>
                  <a
                    href={post.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 font-semibold hover:text-blue-700 flex items-center gap-2 group"
                  >
                    {post.cta}
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* Products Section */}
        <section className="mt-16 mb-12">
          <h2 className="text-3xl font-bold mb-2 text-gray-900">Everything You Need</h2>
          <p className="text-gray-600 mb-8">Choose the system that fits your starting point</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                title: 'Master Blueprint',
                subtitle: 'The Complete System',
                price: '$127',
                description: '7 chapters covering all 4 revenue streams. Real numbers from Month 1. Step-by-step action plan.',
                features: [
                  'Institutional partnerships ($210K/year)',
                  'Vehicle recovery ($300K/year)',
                  'Gig work scaling ($100K/year)',
                  'Content monetization ($825K/year)',
                  '90-day action plan'
                ],
                url: 'https://alreadyhere.gumroad.com/l/master-blueprint',
                highlight: true
              },
              {
                title: 'Institutional Partnerships Playbook',
                subtitle: 'Land Your First $25K Contract',
                price: '$72',
                description: '26 Phoenix prospects + email scripts + sales call framework + proposal templates',
                features: [
                  'Complete prospect list',
                  'Copy-paste email scripts',
                  'Sales call framework',
                  'Proposal templates',
                  'Objection handling'
                ],
                url: 'https://alreadyhere.gumroad.com/l/institutional-partnerships-playbook',
                highlight: false
              },
              {
                title: 'Vehicle Recovery & Fix-and-Flip',
                subtitle: 'Buy for $500, Sell for $6K',
                price: '$57',
                description: 'Complete sourcing guide. Deal evaluation scorecard. Repair budget breakdown. Real flip examples.',
                features: [
                  '5 sourcing channels',
                  'Deal evaluation scorecard',
                  'Repair budget guide',
                  'Sales strategies',
                  'Scaling playbook'
                ],
                url: 'https://alreadyhere.gumroad.com/l/vehicle-recovery-guide',
                highlight: false
              },
              {
                title: 'Gig Work System',
                subtitle: 'Scale to 50 Jobs/Month',
                price: '$57',
                description: '75%+ margins on junk removal, moving, estate cleanout. Contractor model. Scaling guide.',
                features: [
                  'High-margin job types',
                  'Pricing calculator',
                  'Contractor recruitment',
                  'Demand generation',
                  'Scaling guide (0 to 50)'
                ],
                url: 'https://alreadyhere.gumroad.com/l/gig-work-system',
                highlight: false
              }
            ].map((product, idx) => (
              <a
                key={idx}
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`block rounded-lg p-6 transition ${
                  product.highlight
                    ? 'bg-blue-600 text-white border-2 border-blue-600 hover:bg-blue-700 shadow-lg'
                    : 'bg-white border border-gray-200 text-gray-900 hover:shadow-lg'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-xl font-bold">{product.title}</h3>
                    <p className={`text-sm ${product.highlight ? 'text-blue-100' : 'text-gray-600'}`}>
                      {product.subtitle}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${product.highlight ? 'text-white' : 'text-blue-600'}`}>
                      {product.price}
                    </div>
                  </div>
                </div>

                <p className={`mb-4 text-sm ${product.highlight ? 'text-blue-100' : 'text-gray-600'}`}>
                  {product.description}
                </p>

                <ul className="space-y-2 mb-6">
                  {product.features.map((feature, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <span className={product.highlight ? 'text-blue-200' : 'text-blue-600'}>✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>

                <div className={`font-bold text-center py-3 rounded ${
                  product.highlight
                    ? 'bg-white text-blue-600'
                    : 'bg-blue-600 text-white'
                }`}>
                  Get Access
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold mb-3">Not Sure Which to Start With?</h2>
          <p className="mb-6 text-blue-100">Get the Master Blueprint. It covers all 4 streams and includes the exact playbooks from the other guides.</p>
          <a
            href="https://alreadyhere.gumroad.com/l/master-blueprint"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-bold hover:bg-gray-100 transition"
          >
            Start with Master Blueprint ($127)
          </a>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 text-center py-8 mt-12 border-t border-gray-800">
        <div className="max-w-4xl mx-auto px-4">
          <p className="mb-2">© 2026 Already Here LLC. All rights reserved.</p>
          <p className="text-sm">Building business systems that actually work</p>
        </div>
      </footer>
    </div>
  );
}

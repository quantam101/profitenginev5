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
      // TODO: Connect to ConvertKit API
      // For now, just confirm submission
      console.log('Email submitted:', email);
      setSubmitted(true);
      setEmail('');

      // Reset after 3 seconds
      setTimeout(() => setSubmitted(false), 3000);
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
      cta: 'Read →',
      link: '#'
    },
    {
      id: 2,
      title: 'How to Get Your First Nonprofit Fleet Contract',
      excerpt: 'Nonprofits overpay for fleet maintenance by 30%. Here\'s the exact process to land your first $25K contract.',
      category: 'Institutional Partnerships',
      readTime: '12 min',
      published: 'June 15, 2026',
      cta: 'Read →',
      link: '#'
    },
    {
      id: 3,
      title: 'How We Flipped a $500 Car for $6K Profit',
      excerpt: 'Here\'s the complete breakdown: where we found the car, what we spent on repairs, and how we sold it.',
      category: 'Vehicle Recovery',
      readTime: '10 min',
      published: 'June 15, 2026',
      cta: 'Read →',
      link: '#'
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

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">{post.published}</span>
                  <Link
                    href={post.link}
                    className="text-blue-600 font-semibold hover:text-blue-700 flex items-center gap-2 group"
                  >
                    {post.cta}
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="bg-gray-900 text-white rounded-lg p-8 mt-12 text-center">
          <h2 className="text-2xl font-bold mb-3">Ready to Build Your Multi-Stream Business?</h2>
          <p className="text-gray-300 mb-6">Get the complete system with proven playbooks, scripts, and financial projections</p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="#"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-blue-700 transition"
            >
              Download Master Blueprint
            </a>
            <a
              href="#"
              className="border border-white text-white px-8 py-3 rounded-lg font-bold hover:bg-white hover:text-gray-900 transition"
            >
              Join the Newsletter
            </a>
          </div>
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

import type { Metadata } from 'next';
import Link from 'next/link';
import CashDeskClient from './cashdesk-client';
import './cashdesk.css';

export const metadata: Metadata = {
  title: 'AI VP Cash Desk — ProfitEngine v5',
  description:
    'AI VP module for finding, scoring, approving, and tracking trailer, courier, field tech, and local service work for Already Here LLC.',
  robots: { index: false, follow: false },
};

export default function AiVpPage() {
  return (
    <main className="cashdesk">
      <nav className="cd-nav" aria-label="AI VP navigation">
        <Link href="/" className="cd-logo">PROFITENGINE v5</Link>
        <div>
          <Link href="/command-center">Command Center</Link>
          <Link href="/#waitlist">Beta</Link>
        </div>
      </nav>
      <CashDeskClient />
    </main>
  );
}

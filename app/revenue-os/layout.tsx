import Link from 'next/link';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'Revenue OS',
  description: 'Revenue operating system for Already Here LLC',
  // Internal ops console — never indexable (same pattern as command-center).
  robots: { index: false, follow: false },
};

export default function RevenueOsLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="shell">
        <nav className="nav" style={{ marginBottom: 16 }}>
          <Link href="/">← Command Center</Link>
          <Link href="/revenue-os">Dashboard</Link>
          <Link href="/revenue-os/revenue-plays">Revenue Plays</Link>
          <Link href="/revenue-os/passive-income">Passive Income Engine</Link>
          <Link href="/revenue-os/companies">Companies</Link>
          <Link href="/revenue-os/contacts">Contacts</Link>
          <Link href="/revenue-os/opportunities">Opportunities</Link>
          <Link href="/revenue-os/follow-ups">Follow-Ups</Link>
          <Link href="/revenue-os/ai">AI Advisor</Link>
          <Link href="/revenue-os/integrations">Integrations</Link>
        </nav>
      </div>
      {children}
    </>
  );
}

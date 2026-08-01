import Link from 'next/link';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'Revenue OS',
  description: 'Revenue operating system for Already Here LLC',
};

export default function RevenueOsLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="shell">
        <nav className="nav" style={{ marginBottom: 16 }}>
          <Link href="/">← Command Center</Link>
          <Link href="/revenue-os">Dashboard</Link>
          <Link href="/revenue-os/revenue-plays">Revenue Plays</Link>
          <Link href="/revenue-os/companies">Companies</Link>
          <Link href="/revenue-os/contacts">Contacts</Link>
          <Link href="/revenue-os/opportunities">Opportunities</Link>
          <Link href="/revenue-os/follow-ups">Follow-Ups</Link>
        </nav>
      </div>
      {children}
    </>
  );
}

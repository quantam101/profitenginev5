import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Admin Control Panel — ProfitEngine v5',
  description: 'System administration console for Already Here LLC trading systems',
  robots: 'noindex, nofollow',
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

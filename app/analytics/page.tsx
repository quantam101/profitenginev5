import dynamic from 'next/dynamic';
import { Metadata } from 'next';

const EnterpriseDashboard = dynamic(() => import('@/app/components/EnterpriseDashboard').then(mod => ({ default: mod.EnterpriseDashboard })), {
  loading: () => <div className="w-full h-screen bg-slate-950 flex items-center justify-center text-white">Loading Dashboard...</div>,
  ssr: false,
});

export const metadata: Metadata = {
  title: 'Enterprise Analytics Dashboard | ProfitEngine v5',
  description: 'Real-time analytics with AI intelligence, revenue tracking, and platform performance',
};

export default function AnalyticsPage() {
  return <EnterpriseDashboard />;
}

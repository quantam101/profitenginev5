import { EnterpriseDashboard } from '@/app/components/EnterpriseDashboard';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Enterprise Analytics Dashboard | ProfitEngine v5',
  description: 'Real-time analytics with AI intelligence, revenue tracking, and platform performance',
};

export default function AnalyticsPage() {
  return <EnterpriseDashboard />;
}

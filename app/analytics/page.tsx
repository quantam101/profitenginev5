import { AnalyticsDashboard } from '@/app/components/AnalyticsDashboard';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Analytics Dashboard | ProfitEngine v5',
  description: 'Real-time analytics, revenue tracking, and platform performance metrics',
};

export default function AnalyticsPage() {
  return <AnalyticsDashboard />;
}

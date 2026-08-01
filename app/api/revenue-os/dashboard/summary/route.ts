import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { getDashboardSummary } from '@/lib/revenue-os/services/dashboard.service.mjs';

export async function GET() {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const summary = await getDashboardSummary();
    return NextResponse.json({ ok: true, summary });
  } catch (err) {
    console.error('[revenue-os] dashboard summary error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

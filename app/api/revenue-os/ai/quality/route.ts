import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { auditDataQuality } from '@/lib/revenue-os/services/ai-advisor.mjs';

export async function GET() {
  if (process.env.REVENUE_OS_ENABLED !== 'true' || process.env.REVENUE_OS_AI_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS AI is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const flags = await auditDataQuality();
    return NextResponse.json({ ok: true, flags });
  } catch (err) {
    console.error('[revenue-os] ai quality error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

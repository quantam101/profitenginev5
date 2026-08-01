import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { rankOpportunities } from '@/lib/revenue-os/services/ai-advisor.mjs';

export async function GET(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true' || process.env.REVENUE_OS_AI_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS AI is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const limit = Number(searchParams.get('limit')) || 10;

  try {
    const rankings = await rankOpportunities({ limit });
    return NextResponse.json({ ok: true, rankings });
  } catch (err) {
    console.error('[revenue-os] ai recommendations error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

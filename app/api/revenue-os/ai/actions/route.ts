import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { findAIActions } from '@/lib/revenue-os/services/ai-advisor.mjs';
import type { AIAction } from '@/lib/revenue-os/types';

export async function GET(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true' || process.env.REVENUE_OS_AI_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS AI is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const options = {
    status: searchParams.get('status') || undefined,
    actionType: searchParams.get('actionType') || undefined,
    entityId: searchParams.get('entityId') || undefined,
    sortBy: searchParams.get('sortBy') || 'createdAt',
    order: searchParams.get('order') === 'asc' ? ('asc' as const) : ('desc' as const),
    page: Number(searchParams.get('page')) || 1,
    limit: Number(searchParams.get('limit')) || 20,
  };

  try {
    const result = await findAIActions(options);
    return NextResponse.json({
      ok: true,
      records: result.records.map((a: AIAction) => ({ ...a, _id: String(a._id) })),
      total: result.total,
      page: result.page,
      limit: result.limit,
    });
  } catch (err) {
    console.error('[revenue-os] ai actions list error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

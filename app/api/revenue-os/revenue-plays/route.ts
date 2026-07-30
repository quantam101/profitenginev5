import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { findRevenuePlays } from '@/lib/revenue-os/repositories/revenue-play.repository.mjs';
import type { RevenuePlay } from '@/lib/revenue-os/types';

const ALLOWED_SORT = ['overallScore', 'revenuePlayName', 'createdAt', 'updatedAt'];

export async function GET(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }

  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const lane = searchParams.get('lane') || undefined;
  const buyerType = searchParams.get('buyerType') || undefined;
  const location = searchParams.get('location') || undefined;
  const status = searchParams.get('status') || undefined;
  const minScore = searchParams.has('minScore') ? Number(searchParams.get('minScore')) : undefined;
  const search = searchParams.get('search') || undefined;
  const sortBy = ALLOWED_SORT.includes(searchParams.get('sortBy') || '')
    ? (searchParams.get('sortBy') as 'overallScore' | 'revenuePlayName' | 'createdAt' | 'updatedAt')
    : 'overallScore';
  const order = searchParams.get('order') === 'asc' ? 'asc' : 'desc';
  const page = Number(searchParams.get('page')) || 1;
  const limit = Number(searchParams.get('limit')) || 20;

  try {
    const result = await findRevenuePlays({
      lane,
      buyerType,
      location,
      status,
      minScore: typeof minScore === 'number' && !isNaN(minScore) ? minScore : undefined,
      search,
      sortBy,
      order,
      page,
      limit,
    });

    return NextResponse.json({
      ok: true,
      records: result.records.map((record: RevenuePlay) => ({
        ...record,
        _id: typeof record._id === 'object' && record._id !== null ? record._id.toString() : record._id,
      })),
      total: result.total,
      page: result.page,
      limit: result.limit,
      pageCount: Math.ceil(result.total / result.limit),
    });
  } catch (err) {
    console.error('[revenue-os] revenue-plays list error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

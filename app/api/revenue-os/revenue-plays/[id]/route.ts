import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import {
  getRevenuePlayById,
  getRevenuePlayByRecordId,
} from '@/lib/revenue-os/repositories/revenue-play.repository.mjs';

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function GET(request: Request, { params }: RouteParams) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }

  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;

  try {
    const record = id.startsWith('RP-')
      ? await getRevenuePlayByRecordId(id)
      : await getRevenuePlayById(id);

    if (!record) {
      return NextResponse.json({ ok: false, error: 'Revenue play not found' }, { status: 404 });
    }

    return NextResponse.json({
      ok: true,
      record: { ...record, _id: record._id?.toString() },
    });
  } catch (err) {
    console.error('[revenue-os] revenue-play detail error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

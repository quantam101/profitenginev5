import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { findDeliveries } from '@/lib/revenue-os/repositories/webhook-delivery.repository.mjs';

export async function GET(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const options = {
    provider: searchParams.get('provider') || undefined,
    eventType: searchParams.get('eventType') || undefined,
    status: searchParams.get('status') || undefined,
    page: Number(searchParams.get('page')) || 1,
    limit: Number(searchParams.get('limit')) || 20,
  };

  try {
    const result = await findDeliveries(options);
    return NextResponse.json({
      ok: true,
      records: result.records.map((r) => ({ ...r, _id: String(r._id) })),
      total: result.total,
      page: result.page,
      limit: result.limit,
    });
  } catch (err) {
    console.error('[revenue-os] webhook deliveries error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

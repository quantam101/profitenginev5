import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { findFollowUps, completeFollowUp } from '@/lib/revenue-os/repositories/follow-up.repository.mjs';
import { createActivity } from '@/lib/revenue-os/repositories/activity.repository.mjs';
import type { FollowUpTask } from '@/lib/revenue-os/types';

export async function GET(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000 - 1);

  const options: {
    status?: string;
    assignedTo?: string;
    dueBefore?: Date;
    dueAfter?: Date;
    sortBy: string;
    order: 'asc' | 'desc';
    page: number;
    limit: number;
  } = {
    status: searchParams.get('status') || undefined,
    assignedTo: searchParams.get('assignedTo') || undefined,
    sortBy: searchParams.get('sortBy') || 'dueDate',
    order: searchParams.get('order') === 'desc' ? ('desc' as const) : ('asc' as const),
    page: Number(searchParams.get('page')) || 1,
    limit: Number(searchParams.get('limit')) || 20,
  };

  if (searchParams.has('dueToday')) {
    options.dueAfter = startOfDay;
    options.dueBefore = endOfDay;
  }

  try {
    const result = await findFollowUps(options);
    return NextResponse.json({
      ok: true,
      records: result.records.map((f: FollowUpTask) => ({ ...f, _id: String(f._id), entityId: String(f.entityId) })),
      total: result.total,
      page: result.page,
      limit: result.limit,
      pageCount: Math.ceil(result.total / result.limit),
    });
  } catch (err) {
    console.error('[revenue-os] follow-ups list error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  let body: { id?: string; status?: string } = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  if (!body.id) {
    return NextResponse.json({ ok: false, error: 'Missing id' }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    if (body.status === 'COMPLETED') {
      const completed = await completeFollowUp(body.id, actor);
      if (!completed) {
        return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
      }
      await createActivity({
        entityType: 'follow_up',
        entityId: completed._id,
        actionType: 'completed',
        actor,
        summary: `Completed follow-up: ${completed.summary}`,
        metadata: { entityType: completed.entityType, entityId: String(completed.entityId) },
      });
      return NextResponse.json({
        ok: true,
        followUp: { ...completed, _id: String(completed._id), entityId: String(completed.entityId) },
      });
    }
    return NextResponse.json({ ok: false, error: 'Unsupported status update' }, { status: 400 });
  } catch (err) {
    console.error('[revenue-os] follow-up update error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

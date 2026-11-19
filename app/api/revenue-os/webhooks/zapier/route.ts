import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { dispatchZapierEvent, isZapierEnabled, getValidEvents } from '@/lib/revenue-os/services/zapier.mjs';

const zapierSchema = z.object({
  eventType: z.enum([
    'revenue_play.created',
    'company.qualified',
    'opportunity.created',
    'opportunity.stage_changed',
    'follow_up.due',
    'proposal.approved',
    'opportunity.won',
  ] as const),
  payload: z.record(z.string(), z.unknown()).optional(),
});

export async function POST(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parse = zapierSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const result = await dispatchZapierEvent({ ...parse.data, actor });
    return NextResponse.json({ ok: result.ok, delivered: result.delivered, status: result.status, idempotencyKey: result.idempotencyKey, deliveryId: result.deliveryId, error: result.error }, { status: result.ok ? 200 : 400 });
  } catch (err) {
    console.error('[revenue-os] zapier dispatch error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

export async function GET() {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  return NextResponse.json({ ok: true, enabled: isZapierEnabled(), validEvents: getValidEvents() });
}

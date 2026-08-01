import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { sendSlackNotification, isSlackEnabled } from '@/lib/revenue-os/services/slack.mjs';

const slackSchema = z.object({
  notificationType: z.string().min(1),
  channel: z.string().optional(),
  text: z.string().min(1),
  blocks: z.array(z.record(z.unknown())).optional(),
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

  const parse = slackSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const result = await sendSlackNotification({ ...parse.data, actor });
    return NextResponse.json({ ok: result.ok, sent: result.sent, reason: result.reason, error: result.error });
  } catch (err) {
    console.error('[revenue-os] slack notification error:', err);
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

  try {
    const { getCollection } = await import('@/lib/mongodb.mjs');
    const col = await getCollection('slack_notifications');
    const records = await col.find({}).sort({ createdAt: -1 }).limit(50).toArray();
    return NextResponse.json({ ok: true, enabled: isSlackEnabled(), records: records.map((r: Record<string, unknown> & { _id: any }) => ({ ...r, _id: String(r._id) })) });
  } catch (err) {
    console.error('[revenue-os] slack list error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

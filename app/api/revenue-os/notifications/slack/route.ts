import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { sendSlackNotification, isSlackEnabled } from '@/lib/revenue-os/services/slack.mjs';

const slackTextObjectSchema = z.object({
  type: z.enum(['mrkdwn', 'plain_text']),
  text: z.string().min(1).max(3000),
}).strict();

const slackBlockSchema = z.object({
  type: z.literal('section'),
  text: slackTextObjectSchema,
}).strict();

const slackSchema = z.object({
  notificationType: z.string().min(1).max(64),
  channel: z.string().min(1).max(64).optional(),
  text: z.string().min(1).max(4000),
  blocks: z.array(slackBlockSchema).max(5).optional(),
}).strict();

const RATE_LIMIT_MAX = 30;
const RATE_LIMIT_WINDOW_MS = 60_000;
const rateLimitMap = new Map<string, number[]>();

function checkRateLimit(actor: string) {
  const now = Date.now();
  const windowStart = now - RATE_LIMIT_WINDOW_MS;
  const timestamps = rateLimitMap.get(actor)?.filter((t) => t > windowStart) || [];
  if (timestamps.length >= RATE_LIMIT_MAX) return false;
  timestamps.push(now);
  rateLimitMap.set(actor, timestamps);
  return true;
}

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

  if (!checkRateLimit(actor)) {
    return NextResponse.json({ ok: false, error: 'Rate limit exceeded' }, { status: 429 });
  }

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

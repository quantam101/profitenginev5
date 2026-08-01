import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { rejectAction } from '@/lib/revenue-os/services/ai-advisor.mjs';

export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (process.env.REVENUE_OS_ENABLED !== 'true' || process.env.REVENUE_OS_AI_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS AI is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;
  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const result = await rejectAction(id, actor);
    if (!result.ok) {
      return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
    }
    return NextResponse.json({ ok: true, action: { ...result.action, _id: String(result.action?._id) } });
  } catch (err) {
    console.error('[revenue-os] ai action reject error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

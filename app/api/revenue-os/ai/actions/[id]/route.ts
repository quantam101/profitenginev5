import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { getAIActionById } from '@/lib/revenue-os/repositories/ai-action.repository.mjs';
import type { AIAction } from '@/lib/revenue-os/types';

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (process.env.REVENUE_OS_ENABLED !== 'true' || process.env.REVENUE_OS_AI_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS AI is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;
  try {
    const action = await getAIActionById(id);
    if (!action) {
      return NextResponse.json({ ok: false, error: 'Action not found' }, { status: 404 });
    }
    return NextResponse.json({ ok: true, action: { ...action, _id: String(action._id) } });
  } catch (err) {
    console.error('[revenue-os] ai action detail error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

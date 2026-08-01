import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { advanceOpportunityStage, setOpportunityStage } from '@/lib/revenue-os/services/pipeline.service.mjs';
import type { OpportunityStage } from '@/lib/revenue-os/types';

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;
  let body: { stage?: OpportunityStage } = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const result = body.stage
      ? await setOpportunityStage(id, body.stage, actor)
      : await advanceOpportunityStage(id, actor);

    if (!result.ok) {
      return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
    }

    return NextResponse.json({
      ok: true,
      opportunity: { ...result.opportunity, _id: String(result.opportunity._id) },
      previousStage: result.previousStage,
      nextStage: result.nextStage,
      followUp: result.followUp ? { ...result.followUp, _id: String(result.followUp._id) } : undefined,
    });
  } catch (err) {
    console.error('[revenue-os] opportunity advance error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

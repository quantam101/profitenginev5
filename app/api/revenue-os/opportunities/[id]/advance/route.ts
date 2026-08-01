import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { advanceOpportunityStage, setOpportunityStage } from '@/lib/revenue-os/services/pipeline.service.mjs';

const stageSchema = z.object({
  stage: z.enum([
    'Research', 'Qualified', 'Approval Needed', 'Outreach Approved', 'Contacted',
    'Conversation', 'Proposal', 'Negotiation', 'Won', 'Lost', 'On Hold',
  ] as const).optional(),
});

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;

  let body;
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const parse = stageSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const result = parse.data.stage
      ? await setOpportunityStage(id, parse.data.stage, actor)
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

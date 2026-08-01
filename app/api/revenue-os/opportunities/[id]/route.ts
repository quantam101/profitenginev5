import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { getOpportunityById, updateOpportunity } from '@/lib/revenue-os/repositories/opportunity.repository.mjs';
import { onOpportunityStageChanged } from '@/lib/revenue-os/services/follow-up.service.mjs';
import type { Opportunity, OpportunityStage } from '@/lib/revenue-os/types';

const opportunityUpdateSchema = z.object({
  title: z.string().min(1).optional(),
  stage: z.enum([
    'Research', 'Qualified', 'Approval Needed', 'Outreach Approved', 'Contacted',
    'Conversation', 'Proposal', 'Negotiation', 'Won', 'Lost', 'On Hold',
  ] as const).optional(),
  estimatedValue: z.number().min(0).optional(),
  recurringMonthlyValue: z.number().min(0).optional(),
  probability: z.number().min(0).max(1).optional(),
  nextAction: z.string().optional(),
  assignedTo: z.string().optional(),
  approvalStatus: z.string().optional(),
  location: z.object({
    type: z.literal('Point'),
    coordinates: z.tuple([z.number(), z.number()]),
  }).optional().nullable(),
}).partial();

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (process.env.REVENUE_OS_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;

  try {
    const opportunity = await getOpportunityById(id);
    if (!opportunity) {
      return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
    }
    return NextResponse.json({
      ok: true,
      opportunity: { ...opportunity, _id: String(opportunity._id) },
    });
  } catch (err) {
    console.error('[revenue-os] opportunity detail error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
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
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parse = opportunityUpdateSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const existing = await getOpportunityById(id);
    if (!existing) {
      return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
    }

    const updates = { ...parse.data } as Partial<Opportunity>;
    if (updates.location === null) updates.location = undefined;

    const updated = await updateOpportunity(id, updates);

    if (updates.stage && updates.stage !== existing.stage) {
      await onOpportunityStageChanged(updated, existing.stage, actor);
    }

    return NextResponse.json({
      ok: true,
      opportunity: { ...updated, _id: String(updated._id) },
    });
  } catch (err) {
    console.error('[revenue-os] opportunity update error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

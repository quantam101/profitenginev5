import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { findOpportunities, createOpportunity } from '@/lib/revenue-os/repositories/opportunity.repository.mjs';
import { onOpportunityCreated } from '@/lib/revenue-os/services/follow-up.service.mjs';
import type { Opportunity, OpportunityStage } from '@/lib/revenue-os/types';

const opportunityCreateSchema = z.object({
  revenuePlayId: z.string().min(1),
  companyId: z.string().min(1),
  contactIds: z.array(z.string()).optional().default([]),
  title: z.string().min(1),
  stage: z.enum([
    'Research', 'Qualified', 'Approval Needed', 'Outreach Approved', 'Contacted',
    'Conversation', 'Proposal', 'Negotiation', 'Won', 'Lost', 'On Hold',
  ] as const),
  estimatedValue: z.number().min(0),
  recurringMonthlyValue: z.number().min(0).optional().default(0),
  probability: z.number().min(0).max(1),
  nextAction: z.string().min(1),
  assignedTo: z.string().optional(),
  approvalStatus: z.string().optional().default('Pending'),
  location: z.object({
    type: z.literal('Point'),
    coordinates: z.tuple([z.number(), z.number()]),
  }).optional(),
});

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
    stage: searchParams.get('stage') || undefined,
    companyId: searchParams.get('companyId') || undefined,
    revenuePlayId: searchParams.get('revenuePlayId') || undefined,
    assignedTo: searchParams.get('assignedTo') || undefined,
    search: searchParams.get('search') || undefined,
    active: searchParams.has('active') ? true : undefined,
    sortBy: searchParams.get('sortBy') || 'createdAt',
    order: searchParams.get('order') === 'asc' ? ('asc' as const) : ('desc' as const),
    page: Number(searchParams.get('page')) || 1,
    limit: Number(searchParams.get('limit')) || 20,
  };

  try {
    const result = await findOpportunities(options);
    return NextResponse.json({
      ok: true,
      records: result.records.map((o: Opportunity) => ({ ...o, _id: String(o._id) })),
      total: result.total,
      page: result.page,
      limit: result.limit,
      pageCount: Math.ceil(result.total / result.limit),
    });
  } catch (err) {
    console.error('[revenue-os] opportunities list error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
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

  const parse = opportunityCreateSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const created = await createOpportunity(parse.data);
    const followUp = await onOpportunityCreated(created, actor);
    return NextResponse.json({
      ok: true,
      opportunity: { ...created, _id: String(created._id) },
      followUp: { ...followUp, _id: String(followUp._id) },
    }, { status: 201 });
  } catch (err) {
    console.error('[revenue-os] opportunity create error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

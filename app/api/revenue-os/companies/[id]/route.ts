import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { getCompanyById, updateCompany } from '@/lib/revenue-os/repositories/company.repository.mjs';
import { createActivity } from '@/lib/revenue-os/repositories/activity.repository.mjs';
import type { Company } from '@/lib/revenue-os/types';

const companyUpdateSchema = z.object({
  legalName: z.string().min(1).optional(),
  displayName: z.string().min(1).optional(),
  website: z.string().url().optional().or(z.literal('')).optional(),
  industry: z.string().min(1).optional(),
  companyType: z.string().min(1).optional(),
  locations: z.array(z.object({
    street: z.string().optional(),
    city: z.string().optional(),
    state: z.string().optional(),
    zipCode: z.string().optional(),
    country: z.string().optional(),
    coordinates: z.object({
      type: z.literal('Point'),
      coordinates: z.tuple([z.number(), z.number()]),
    }).optional(),
  })).optional(),
  serviceLanes: z.array(z.string()).optional(),
  qualificationStatus: z.string().optional(),
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
    const company = await getCompanyById(id);
    if (!company) {
      return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
    }
    return NextResponse.json({ ok: true, company: { ...company, _id: String(company._id) } });
  } catch (err) {
    console.error('[revenue-os] company detail error:', err);
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

  const parse = companyUpdateSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const updated = await updateCompany(id, parse.data);
    if (!updated) {
      return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
    }
    await createActivity({
      entityType: 'company',
      entityId: updated._id,
      actionType: 'updated',
      actor,
      summary: `Updated company ${updated.displayName || updated.legalName}`,
      metadata: {},
    });
    return NextResponse.json({ ok: true, company: { ...updated, _id: String(updated._id) } });
  } catch (err) {
    console.error('[revenue-os] company update error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

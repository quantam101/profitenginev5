import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { findCompanies, createCompany } from '@/lib/revenue-os/repositories/company.repository.mjs';
import { createActivity } from '@/lib/revenue-os/repositories/activity.repository.mjs';
import type { Company } from '@/lib/revenue-os/types';

const companyCreateSchema = z.object({
  legalName: z.string().min(1),
  displayName: z.string().min(1).optional(),
  website: z.string().url().optional().or(z.literal('')),
  industry: z.string().min(1),
  companyType: z.string().min(1),
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
  })).optional().default([]),
  serviceLanes: z.array(z.string()).optional().default([]),
  source: z.string().optional().default('manual'),
  qualificationStatus: z.string().optional().default('Prospect'),
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
    industry: searchParams.get('industry') || undefined,
    companyType: searchParams.get('companyType') || undefined,
    search: searchParams.get('search') || undefined,
    qualificationStatus: searchParams.get('qualificationStatus') || undefined,
    sortBy: searchParams.get('sortBy') || 'createdAt',
    order: searchParams.get('order') === 'asc' ? ('asc' as const) : ('desc' as const),
    page: Number(searchParams.get('page')) || 1,
    limit: Number(searchParams.get('limit')) || 20,
  };

  try {
    const result = await findCompanies(options);
    return NextResponse.json({
      ok: true,
      records: result.records.map((c: Company) => ({ ...c, _id: String(c._id) })),
      total: result.total,
      page: result.page,
      limit: result.limit,
      pageCount: Math.ceil(result.total / result.limit),
    });
  } catch (err) {
    console.error('[revenue-os] companies list error:', err);
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

  const parse = companyCreateSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const company = (await createCompany(parse.data)) as Company;
    await createActivity({
      entityType: 'company',
      entityId: company._id,
      actionType: 'created',
      actor,
      summary: `Created company ${company.displayName || company.legalName}`,
      metadata: { duplicateKey: company.duplicateKey },
    });
    return NextResponse.json({
      ok: true,
      company: { ...company, _id: String(company._id) },
    }, { status: 201 });
  } catch (err) {
    console.error('[revenue-os] company create error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

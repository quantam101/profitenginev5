import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { findContacts, createContact } from '@/lib/revenue-os/repositories/contact.repository.mjs';
import { createActivity } from '@/lib/revenue-os/repositories/activity.repository.mjs';
import type { Contact } from '@/lib/revenue-os/types';

const contactCreateSchema = z.object({
  companyId: z.string().min(1),
  fullName: z.string().min(1).optional(),
  title: z.string().optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  preferredChannel: z.string().optional(),
  contactStatus: z.string().optional().default('Active'),
  consentStatus: z.string().optional().default('Unknown'),
  source: z.string().optional().default('manual'),
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
    companyId: searchParams.get('companyId') || undefined,
    search: searchParams.get('search') || undefined,
    contactStatus: searchParams.get('contactStatus') || undefined,
    consentStatus: searchParams.get('consentStatus') || undefined,
    sortBy: searchParams.get('sortBy') || 'createdAt',
    order: searchParams.get('order') === 'asc' ? ('asc' as const) : ('desc' as const),
    page: Number(searchParams.get('page')) || 1,
    limit: Number(searchParams.get('limit')) || 20,
  };

  try {
    const result = await findContacts(options);
    return NextResponse.json({
      ok: true,
      records: result.records.map((c: Contact) => ({ ...c, _id: String(c._id) })),
      total: result.total,
      page: result.page,
      limit: result.limit,
      pageCount: Math.ceil(result.total / result.limit),
    });
  } catch (err) {
    console.error('[revenue-os] contacts list error:', err);
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

  const parse = contactCreateSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const contact = await createContact(parse.data);
    await createActivity({
      entityType: 'contact',
      entityId: contact._id,
      actionType: 'created',
      actor,
      summary: `Created contact ${contact.fullName || contact.email}`,
      metadata: { companyId: String(contact.companyId) },
    });
    return NextResponse.json({
      ok: true,
      contact: { ...contact, _id: String(contact._id) },
    }, { status: 201 });
  } catch (err) {
    console.error('[revenue-os] contact create error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

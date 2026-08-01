import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { getContactById, updateContact } from '@/lib/revenue-os/repositories/contact.repository.mjs';
import { createActivity } from '@/lib/revenue-os/repositories/activity.repository.mjs';
import type { Contact } from '@/lib/revenue-os/types';

const contactUpdateSchema = z.object({
  fullName: z.string().min(1).optional(),
  title: z.string().optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  preferredChannel: z.string().optional(),
  contactStatus: z.string().optional(),
  consentStatus: z.string().optional(),
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
    const contact = await getContactById(id);
    if (!contact) {
      return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
    }
    return NextResponse.json({ ok: true, contact: { ...contact, _id: String(contact._id) } });
  } catch (err) {
    console.error('[revenue-os] contact detail error:', err);
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

  const parse = contactUpdateSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    const updated = await updateContact(id, parse.data);
    if (!updated) {
      return NextResponse.json({ ok: false, error: 'Not found' }, { status: 404 });
    }
    await createActivity({
      entityType: 'contact',
      entityId: updated._id,
      actionType: 'updated',
      actor,
      summary: `Updated contact ${updated.fullName || updated.email}`,
      metadata: {},
    });
    return NextResponse.json({ ok: true, contact: { ...updated, _id: String(updated._id) } });
  } catch (err) {
    console.error('[revenue-os] contact update error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}

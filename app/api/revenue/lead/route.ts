import { NextRequest, NextResponse } from 'next/server';
import {
  persistLead,
  sendGa4LeadConversion,
  sendLeadNotification,
} from '@/lib/revenue-attribution.mjs';

type RevenueLeadRequest = {
  name?: string;
  email?: string;
  phone?: string;
  service?: string;
  message?: string;
  source?: string;
  medium?: string;
  campaign?: string;
  content?: string;
  term?: string;
  referrer?: string;
  landingPage?: string;
  gaClientId?: string;
  metadata?: Record<string, unknown>;
};

export async function GET() {
  return NextResponse.json({ ok: true, service: 'revenue-lead-intake', contract: 'lead_id -> booking_id -> payment_id -> revenue_event_id' });
}

export async function POST(request: NextRequest) {
  let body: RevenueLeadRequest;
  try { body = await request.json(); }
  catch { return NextResponse.json({ ok: false, error: 'Invalid JSON body' }, { status: 400 }); }

  if (!body.email && !body.phone) {
    return NextResponse.json({ ok: false, error: 'Email or phone is required' }, { status: 400 });
  }

  try {
    const lead = await persistLead(body);
    const [notification, analytics] = await Promise.all([
      sendLeadNotification(lead),
      sendGa4LeadConversion(lead),
    ]);
    return NextResponse.json({ ok: true, leadId: lead.leadId, notification, analytics, next: '/api/checkout' }, { status: 201 });
  } catch (error) {
    console.error('Revenue lead intake failed:', error);
    return NextResponse.json({ ok: false, error: 'Failed to persist lead' }, { status: 500 });
  }
}

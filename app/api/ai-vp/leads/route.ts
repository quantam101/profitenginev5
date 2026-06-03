import { NextRequest, NextResponse } from 'next/server';

type LeadPayload = {
  title?: string;
  source?: string;
  type?: string;
  location?: string;
  pay?: number;
  miles?: number;
  url?: string;
  nextAction?: string;
};

const VALID_TYPES = new Set(['Trailer', 'Courier', 'Field Tech', 'Low Voltage', 'IT Support', 'Follow Up']);

function sanitize(value: unknown, max = 500): string {
  return String(value ?? '').replace(/[<>]/g, '').trim().slice(0, max);
}

function scoreLead(payload: Required<Pick<LeadPayload, 'pay' | 'miles'>> & { urgency: number; fit: number; probability: number }) {
  const estimatedNet = Math.max(payload.pay - payload.miles * 0.72, 0);
  const payScore = Math.min(estimatedNet / 25, 10);
  const distancePenalty = Math.min(payload.miles / 35, 4);
  return Math.round((payScore * 2.4 + payload.urgency * 2.2 + payload.fit * 2.1 + payload.probability * 2.1 - distancePenalty) * 10) / 10;
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    service: 'ai-vp-lead-intake',
    mode: 'approval-gated',
    policy: 'no auto-submit, no credential exposure, no prohibited scraping',
    acceptedTypes: Array.from(VALID_TYPES),
  });
}

export async function POST(request: NextRequest) {
  let body: LeadPayload;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON body.' }, { status: 400 });
  }

  const title = sanitize(body.title, 160);
  const type = sanitize(body.type, 40);
  const pay = Number(body.pay ?? 0);
  const miles = Number(body.miles ?? 0);

  if (!title) {
    return NextResponse.json({ ok: false, error: 'Lead title is required.' }, { status: 400 });
  }

  if (!VALID_TYPES.has(type)) {
    return NextResponse.json({ ok: false, error: 'Unsupported lead type.' }, { status: 400 });
  }

  if (!Number.isFinite(pay) || pay < 0 || !Number.isFinite(miles) || miles < 0) {
    return NextResponse.json({ ok: false, error: 'Pay and miles must be valid non-negative numbers.' }, { status: 400 });
  }

  const lead = {
    id: `api-lead-${Date.now()}`,
    title,
    source: sanitize(body.source, 100) || 'API',
    type,
    location: sanitize(body.location, 120) || 'Phoenix metro',
    pay,
    miles,
    url: sanitize(body.url, 500),
    nextAction: sanitize(body.nextAction, 500) || 'Review, approve, then apply/call/post manually.',
    approvalRequired: true,
    status: 'New',
    score: scoreLead({ pay, miles, urgency: 8, fit: 8, probability: 6 }),
  };

  return NextResponse.json({ ok: true, lead }, { status: 201 });
}

import { NextRequest, NextResponse } from 'next/server';

// Prospect interaction tracking
type ProspectInteraction = {
  id: string;
  company: string;
  grade: string;
  score: number;
  status: 'pending' | 'contacted' | 'replied' | 'negotiating' | 'won' | 'lost';
  email_sent_at?: string;
  reply_received_at?: string;
  call_scheduled_at?: string;
  notes?: string;
  conversion_value?: number;
};

// In-memory store (replace with DB in production)
const prospects: Record<string, ProspectInteraction> = {
  'az-mobile-diesel': {
    id: '1',
    company: 'AZ Mobile Diesel Repair',
    grade: 'A',
    score: 94,
    status: 'pending',
    notes: 'Call first, then email same day. Lead with overflow field support.',
  },
  'code-3-junk': {
    id: '2',
    company: 'Code 3 Junk Removal',
    grade: 'A',
    score: 92,
    status: 'pending',
    notes: 'Send overflow field support email. Follow with call/text.',
  },
  'cam-fleet-care': {
    id: '3',
    company: 'Cam Fleet Care',
    grade: 'A-',
    score: 90,
    status: 'pending',
    notes: 'Fleet support draft. Ask for overflow dispatch needs.',
  },
  'az-junk-removal': {
    id: '4',
    company: 'AZ Junk Removal',
    grade: 'A-',
    score: 88,
    status: 'pending',
    notes: 'Email Jake. Route guarantee positioning.',
  },
  'minutemen-junk': {
    id: '5',
    company: 'Minutemen Junk Removal',
    grade: 'A-',
    score: 87,
    status: 'pending',
    notes: 'Same-week overflow dispatch pitch.',
  },
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action');

  if (action === 'summary') {
    const total = Object.keys(prospects).length;
    const pending = Object.values(prospects).filter(p => p.status === 'pending').length;
    const contacted = Object.values(prospects).filter(p => p.status === 'contacted').length;
    const replied = Object.values(prospects).filter(p => p.status === 'replied').length;
    const won = Object.values(prospects).filter(p => p.status === 'won').length;

    return NextResponse.json({
      total,
      pending,
      contacted,
      replied,
      negotiating: Object.values(prospects).filter(p => p.status === 'negotiating').length,
      won,
      lost: Object.values(prospects).filter(p => p.status === 'lost').length,
      avgGrade: 'A-',
      conversionRate: total > 0 ? ((won / total) * 100).toFixed(1) : '0',
    });
  }

  return NextResponse.json(Object.values(prospects));
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { company_id, status, email_sent_at, reply_received_at, notes, conversion_value } = body;

  if (!company_id || !prospects[company_id]) {
    return NextResponse.json(
      { error: 'Prospect not found' },
      { status: 404 }
    );
  }

  const prospect = prospects[company_id];

  // Update prospect
  if (status) prospect.status = status;
  if (email_sent_at) prospect.email_sent_at = email_sent_at;
  if (reply_received_at) {
    prospect.reply_received_at = reply_received_at;
    if (prospect.status === 'pending') prospect.status = 'replied';
  }
  if (notes) prospect.notes = notes;
  if (conversion_value) prospect.conversion_value = conversion_value;

  return NextResponse.json(prospect, { status: 201 });
}

export async function PATCH(request: NextRequest) {
  const body = await request.json();
  const { company_id, status } = body;

  if (!company_id || !prospects[company_id]) {
    return NextResponse.json(
      { error: 'Prospect not found' },
      { status: 404 }
    );
  }

  prospects[company_id].status = status;

  return NextResponse.json(prospects[company_id]);
}

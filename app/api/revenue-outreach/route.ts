import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../lib/outreach/auth';
import { approveMessage, createOutreach, listOutreach, sendMessage } from '../../../lib/outreach/controller';
import type { CreateOutreachInput } from '../../../lib/outreach/types';

function fail(error: unknown) {
  const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : 500;
  return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status });
}

export async function GET(request: Request) {
  try {
    requireOutreachAdmin(request);
    const limit = Number(new URL(request.url).searchParams.get('limit') ?? 50);
    return NextResponse.json({ messages: await listOutreach(limit) }, { headers: { 'Cache-Control': 'no-store' } });
  } catch (error) {
    return fail(error);
  }
}

export async function POST(request: Request) {
  try {
    requireOutreachAdmin(request);
    const payload = (await request.json()) as {
      action: 'queue' | 'approve' | 'send';
      id?: string;
      approvedBy?: string;
      message?: CreateOutreachInput;
    };

    if (payload.action === 'queue') {
      const message = payload.message;
      if (!message?.company || !message.lane || !message.subject || !message.body || !message.recipients?.to?.length) {
        return NextResponse.json({ error: 'message.company, lane, recipients.to, subject and body are required' }, { status: 400 });
      }
      return NextResponse.json({ message: await createOutreach(message) }, { status: 201 });
    }

    if (!payload.id) return NextResponse.json({ error: 'id is required' }, { status: 400 });
    if (payload.action === 'approve') {
      return NextResponse.json({ message: await approveMessage(payload.id, payload.approvedBy) });
    }
    if (payload.action === 'send') {
      return NextResponse.json({ message: await sendMessage(payload.id) });
    }
    return NextResponse.json({ error: 'Unsupported action' }, { status: 400 });
  } catch (error) {
    return fail(error);
  }
}

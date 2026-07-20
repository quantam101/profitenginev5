import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../lib/outreach/auth';
import { queueOutreach } from '../../../lib/outreach/orchestrator';
import { listOutreach } from '../../../lib/outreach/store';
import type { CreateOutreachInput } from '../../../lib/outreach/types';

function failure(error: unknown) {
  const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : 500;
  return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status });
}

export async function GET(request: Request) {
  try {
    requireOutreachAdmin(request);
    const url = new URL(request.url);
    const limit = Number(url.searchParams.get('limit') ?? 50);
    return NextResponse.json({ messages: await listOutreach(limit) }, { headers: { 'Cache-Control': 'no-store' } });
  } catch (error) {
    return failure(error);
  }
}

export async function POST(request: Request) {
  try {
    requireOutreachAdmin(request);
    const body = (await request.json()) as CreateOutreachInput;
    if (!body.company || !body.lane || !body.subject || !body.body || !body.recipients?.to?.length) {
      return NextResponse.json({ error: 'company, lane, recipients.to, subject and body are required' }, { status: 400 });
    }
    const message = await queueOutreach(body);
    return NextResponse.json({ message }, { status: 201 });
  } catch (error) {
    return failure(error);
  }
}

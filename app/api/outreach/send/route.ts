import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../../lib/outreach/auth';
import { sendApprovedOutreach } from '../../../../lib/outreach/orchestrator';

export async function POST(request: Request) {
  try {
    requireOutreachAdmin(request);
    const body = (await request.json()) as { id?: string };
    if (!body.id) return NextResponse.json({ error: 'id is required' }, { status: 400 });
    return NextResponse.json({ message: await sendApprovedOutreach(body.id) });
  } catch (error) {
    const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : 500;
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status });
  }
}

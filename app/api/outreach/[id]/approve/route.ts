import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../../../lib/outreach/auth';
import { approveOutreach } from '../../../../../lib/outreach/orchestrator';

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    requireOutreachAdmin(request);
    const { id } = await context.params;
    const body = (await request.json().catch(() => ({}))) as { approvedBy?: string };
    const approvedBy = body.approvedBy?.trim() || 'Stephen Franklin';
    return NextResponse.json({ message: await approveOutreach(id, approvedBy) });
  } catch (error) {
    const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : 500;
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status });
  }
}

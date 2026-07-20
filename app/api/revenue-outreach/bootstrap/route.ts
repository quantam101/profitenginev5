import { NextResponse } from 'next/server';
import { requireOutreachAdmin } from '../../../../lib/outreach/auth';
import { approvedPhoenixCampaign } from '../../../../lib/outreach/approved-campaign';
import { approveMessage, createOutreach, listOutreach } from '../../../../lib/outreach/controller';

export async function POST(request: Request) {
  try {
    requireOutreachAdmin(request);
    const existing = await listOutreach(200);
    const existingSources = new Set(existing.map((message) => message.source).filter(Boolean));
    const created = [];

    for (const input of approvedPhoenixCampaign) {
      if (input.source && existingSources.has(input.source)) continue;
      const queued = await createOutreach(input);
      const approved = await approveMessage(queued.id, 'Stephen Franklin');
      created.push(approved);
    }

    return NextResponse.json({ created, skipped: approvedPhoenixCampaign.length - created.length });
  } catch (error) {
    const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : 500;
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status });
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { getRecentTrafficEvents, saveTrafficEvent } from '../../../../lib/trafficStore';
import { hasWebhookAccess } from '../../../../lib/webhookAuth';

interface TrafficPayload {
  page: string;
  referrer: string;
  timestamp: string;
  userAgent: string;
  source: string;
  sessionId: string;
}

export async function POST(req: NextRequest) {
  if (!hasWebhookAccess(req)) {
    return NextResponse.json({ ok: false, error: 'unauthorized' }, { status: 401 });
  }

  try {
    const body = (await req.json()) as Partial<TrafficPayload>;

    if (!body.page) {
      return NextResponse.json(
        { ok: false, error: 'page is required' },
        { status: 400 },
      );
    }

    const record = {
      type: 'traffic_event',
      receivedAt: new Date().toISOString(),
      page: body.page,
      referrer: body.referrer ?? '',
      timestamp: body.timestamp ?? new Date().toISOString(),
      userAgent: (body.userAgent ?? '').slice(0, 300),
      source: body.source ?? 'alreadyherellc.com',
      sessionId: body.sessionId ?? '',
    };

    await saveTrafficEvent(record);

    return NextResponse.json({ ok: true, stored: true }, { status: 201 });
  } catch {
    return NextResponse.json(
      { ok: false, error: 'invalid_payload' },
      { status: 400 },
    );
  }
}

export async function GET(req: NextRequest) {
  if (!hasWebhookAccess(req)) {
    return NextResponse.json({ ok: false, error: 'unauthorized' }, { status: 401 });
  }

  const recent = await getRecentTrafficEvents(20);

  return NextResponse.json({
    ok: true,
    count: recent.length,
    recent,
  });
}

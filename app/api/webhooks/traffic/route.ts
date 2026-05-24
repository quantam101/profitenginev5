import { NextRequest, NextResponse } from 'next/server';

interface TrafficPayload {
  page: string;
  referrer: string;
  timestamp: string;
  userAgent: string;
  source: string;
  sessionId: string;
}

const buffer: Array<Record<string, string>> = [];
const MAX_BUFFER = 500;

export async function POST(req: NextRequest) {
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

    if (buffer.length >= MAX_BUFFER) buffer.shift();
    buffer.push(record);

    return NextResponse.json({ ok: true, buffered: buffer.length }, { status: 201 });
  } catch {
    return NextResponse.json(
      { ok: false, error: 'invalid_payload' },
      { status: 400 },
    );
  }
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    count: buffer.length,
    recent: buffer.slice(-20),
  });
}

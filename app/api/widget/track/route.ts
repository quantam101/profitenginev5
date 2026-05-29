/**
 * POST /api/widget/track
 *
 * Receives impression and click events from the embed widget on third-party
 * sites. Fires back into the existing referral tracking pipeline.
 *
 * Body: { event: "impression"|"click"|"cta", ref: string, host: string }
 *
 * CORS: open — widget lives on third-party domains.
 */

import { type NextRequest, NextResponse } from 'next/server';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const ALLOWED_EVENTS = new Set(['impression', 'click', 'cta']);

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS });
}

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'bad json' }, { status: 400, headers: CORS });
  }

  const event = String(body.event ?? '');
  const ref   = String(body.ref   ?? '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 64);
  const host  = String(body.host  ?? '').slice(0, 128);

  if (!ALLOWED_EVENTS.has(event)) {
    return NextResponse.json({ ok: false, error: 'unknown event' }, { status: 400, headers: CORS });
  }

  // If there's a referral code, forward to the existing /referral/track endpoint
  // on the Python runtime so it gets credited in the same DB as organic referrals.
  if (ref) {
    const runtimeUrl = process.env.ORACLE_URL ?? 'http://runtime:8080';
    try {
      await fetch(`${runtimeUrl}/referral/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: ref,
          landing_path: `widget:${event}@${host}`,
        }),
        signal: AbortSignal.timeout(3000),
      });
    } catch {
      // Non-fatal: widget impression tracking should never fail loudly.
    }
  }

  return NextResponse.json({ ok: true }, { headers: CORS });
}

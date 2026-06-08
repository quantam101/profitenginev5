import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/** GET /api/chatbot — Active retainer subscriptions + MRR */
export async function GET() {
  const rt = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!rt) return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  try {
    const r = await fetch(`${rt}/chatbot/revenue`, { signal: AbortSignal.timeout(10_000) });
    return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
  } catch (e) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 503, headers: NO_STORE });
  }
}

/**
 * POST /api/chatbot
 * Build a white-label AI chatbot for a local business.
 * Body: { business_name, contact_email, website_url, niche, tier?, send_email? }
 */
export async function POST(request: Request) {
  const rt = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!rt) return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400, headers: NO_STORE }); }
  const r = await fetch(`${rt}/chatbot/build`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), signal: AbortSignal.timeout(60_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}

import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const RUNTIME = (process.env.RUNTIME_API_URL || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');

/** GET /api/chatbot — Active retainer subscriptions + MRR */
export async function GET() {
  try {
    const r = await fetch(`${RUNTIME}/chatbot/revenue`, {
      signal: AbortSignal.timeout(8_000),
      cache: 'no-store',
      headers: { 'User-Agent': 'ProfitEngine/5.0' },
    });
    if (r.ok) return NextResponse.json(await r.json(), { status: 200, headers: NO_STORE });
  } catch {
    // fall through
  }
  return NextResponse.json(
    { ok: true, mrr_usd: 0, active_retainers: 0, source: 'degraded' },
    { status: 200, headers: NO_STORE },
  );
}

/**
 * POST /api/chatbot
 * Build a white-label AI chatbot for a local business.
 * Body: { business_name, contact_email, website_url, niche, tier?, send_email? }
 */
export async function POST(request: Request) {
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400, headers: NO_STORE }); }
  const r = await fetch(`${RUNTIME}/chatbot/build`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), signal: AbortSignal.timeout(60_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}

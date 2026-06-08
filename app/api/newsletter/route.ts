import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/** GET /api/newsletter — Beehiiv publication stats */
export async function GET() {
  const rt = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!rt) return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  try {
    const r = await fetch(`${rt}/newsletter/stats`, { signal: AbortSignal.timeout(10_000) });
    return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
  } catch (e) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 503, headers: NO_STORE });
  }
}

/**
 * POST /api/newsletter
 * Publish a digest to Beehiiv.
 * Body: { headline, sections: [{heading, body}], tags?, cta_url? }
 */
export async function POST(request: Request) {
  const rt = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!rt) return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400, headers: NO_STORE }); }
  const r = await fetch(`${rt}/newsletter/publish`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), signal: AbortSignal.timeout(30_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}

import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

/** GET /api/products — Gumroad revenue summary */
export async function GET() {
  const rt = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!rt) return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  try {
    const r = await fetch(`${rt}/products/revenue`, { signal: AbortSignal.timeout(10_000) });
    return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
  } catch (e) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 503, headers: NO_STORE });
  }
}

/** POST /api/products — Bootstrap Gumroad catalog (idempotent) */
export async function POST() {
  const rt = process.env.RUNTIME_API_URL?.replace(/\/$/, '');
  if (!rt) return NextResponse.json({ ok: false, error: 'RUNTIME_API_URL not configured' }, { status: 503, headers: NO_STORE });
  const r = await fetch(`${rt}/products/bootstrap`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: '{}', signal: AbortSignal.timeout(60_000),
  });
  return NextResponse.json(await r.json(), { status: r.ok ? 200 : 502, headers: NO_STORE });
}

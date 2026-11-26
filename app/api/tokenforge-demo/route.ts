import { NextResponse } from 'next/server';

// Status probe for the zero-cost TokenForge proxy. It calls the proxy's GET
// status endpoint — never POST — so visitors cannot spend inference quota
// through it. On previews it targets this deployment itself (VERCEL_URL),
// falling back to the production app host.
const TF_BASE = (
  process.env.TOKENFORGE_API_URL
  || (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'https://app.alreadyherellc.com')
).replace(/\/$/, '');
const TF_API = `${TF_BASE}/api/tokenforge`;

export const revalidate = 3600;

export async function GET() {
  const apiKey = process.env.TOKENFORGE_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ ok: false, error: 'TOKENFORGE_API_KEY not set' }, { status: 503 });
  }

  const started = Date.now();
  let tfResponse: Record<string, unknown> = {};
  let tfOk = false;

  try {
    const res = await fetch(TF_API, {
      headers: { 'X-TF-Key': apiKey },
      next: { revalidate: 0 },
    });
    tfResponse = await res.json();
    tfOk = res.ok;
  } catch (err) {
    tfResponse = { error: String(err) };
  }

  return NextResponse.json(
    {
      ok: tfOk,
      proof: 'tokenforge_status_live',
      latency_ms: Date.now() - started,
      connector: 'tokenforge_api',
      repository: 'quantam101/profitenginev5',
      cached_for_seconds: revalidate,
      timestamp: new Date().toISOString(),
      tokenforge_status: tfResponse,
    },
    { headers: { 'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=60' } },
  );
}

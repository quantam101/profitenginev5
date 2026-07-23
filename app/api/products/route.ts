import { NextResponse } from 'next/server';

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const RUNTIME_BASE = (process.env.RUNTIME_API_URL || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');

const FALLBACK_CATALOG = {
  ok: true,
  products: 10,
  month_sales: 0,
  month_revenue_usd: 0.0,
  catalog: [
    { name: 'Smart Hands Half-Day Block — Phoenix (4 Hours On-Site)', id: 'pJzU2xAEHQdtNcjm1WD0gw==' },
    { name: 'Arizona Infrastructure Assessment (Full Site, On-Site)', id: 'CfrUa2RfalqmBC0ZRqsLWQ==' },
    { name: 'Phoenix Network Health Assessment (On-Site)', id: 'vhYiTam8hj60VNV2plckHw==' },
    { name: 'Programmatic SEO Starter Kit', id: 'ZMf6us9-FxZr1HV7bpz7Ww==' },
    { name: 'POD Design Prompt Bundle', id: 'nkUr6au9ox0GD4Le-BjUdg==' },
    { name: 'Social Media Content Engine', id: 'czXiltBZj7xE7An4cPlJSg==' },
    { name: 'Real Estate Copywriting Kit', id: 'CuVMo1_UZ0X9y815ZkLFyQ==' },
    { name: 'AI Business Prompt Pack', id: 'qUvEt-bfyTKzotWidcf2Uw==' },
    { name: 'Complete Automation Bundle - All 5 Tools', id: 'B4npFuWPuXvSQIMiS8Exg==' },
    { name: 'Email List Gold Mine', id: 'GeX8g4jKzPxE35qiTl8rOg==' },
  ],
  source: 'fallback_catalog',
};

/** GET /api/products — Gumroad revenue summary with warm fallback */
export async function GET() {
  try {
    const r = await fetch(`${RUNTIME_BASE}/products/revenue`, {
      signal: AbortSignal.timeout(8_000),
      cache: 'no-store',
      headers: { 'User-Agent': 'ProfitEngine/5.0' },
    });
    if (r.ok) {
      const body = await r.json();
      return NextResponse.json({ ...body, source: 'runtime_live' }, { status: 200, headers: NO_STORE });
    }
  } catch {
    // Fall through to cached catalog below.
  }
  return NextResponse.json(FALLBACK_CATALOG, { status: 200, headers: NO_STORE });
}

/** POST /api/products — Bootstrap Gumroad catalog (idempotent) */
export async function POST() {
  try {
    const r = await fetch(`${RUNTIME_BASE}/products/bootstrap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
      signal: AbortSignal.timeout(60_000),
      cache: 'no-store',
    });
    if (r.ok) return NextResponse.json(await r.json(), { status: 200, headers: NO_STORE });
    return NextResponse.json({ ok: false, error: 'runtime bootstrap failed' }, { status: 502, headers: NO_STORE });
  } catch (e) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 503, headers: NO_STORE });
  }
}

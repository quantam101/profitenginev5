/**
 * GET /api/widget.js?ref=CODE&v=1
 *
 * Serves the self-contained ProfitEngine embed widget as a JavaScript file.
 * Cache-busted by `v` param; `ref` is baked into the JS at serve-time so
 * every impression/click that comes back already carries the reseller's code.
 *
 * CORS: open — this is a public widget meant for third-party domains.
 */

import { type NextRequest, NextResponse } from 'next/server';
import { WIDGET_JS } from './embed-source';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS });
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const ref   = (searchParams.get('ref')   ?? '').replace(/[^A-Za-z0-9_-]/g, '');
  const theme = (searchParams.get('theme') ?? 'dark').replace(/[^a-z]/g, '');
  const host  = request.headers.get('host') ?? 'profitengine.alreadyherellc.com';
  const proto = host.startsWith('localhost') ? 'http' : 'https';
  const origin = `${proto}://${host}`;

  const js = WIDGET_JS
    .replace('__ORIGIN__', origin)
    .replace('__REF__',    ref)
    .replace('__THEME__',  theme === 'light' ? 'light' : 'dark');

  return new NextResponse(js, {
    status: 200,
    headers: {
      ...CORS,
      'Content-Type': 'application/javascript; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}

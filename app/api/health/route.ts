import { NextResponse } from 'next/server';
import { buildHealthPayload } from '../../../lib/health.mjs';
import { getCacheHeaders, CACHE_CONFIG } from '@/app/lib/cache';

export const revalidate = 60;

export function GET() {
  const payload = buildHealthPayload();
  return NextResponse.json(payload, {
    status: payload.ok ? 200 : 503,
    headers: getCacheHeaders('SHORT'),
  });
}

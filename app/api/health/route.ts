import { NextResponse } from 'next/server';
import { buildHealthPayload } from '../../../lib/health.mjs';

export function GET() {
  const payload = buildHealthPayload();
  return NextResponse.json(payload, { status: payload.ok ? 200 : 503 });
}

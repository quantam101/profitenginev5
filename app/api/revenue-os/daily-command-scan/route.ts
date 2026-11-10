import { timingSafeEqual } from 'node:crypto';
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getCollection } from '@/lib/mongodb.mjs';
import { createMongoScanStore, runDailyCommandScan } from '@/lib/revenue-os/services/daily-command-scan.mjs';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 60;

const NO_STORE = { 'Cache-Control': 'no-store' } as const;

const BodySchema = z
  .object({
    limit: z.coerce.number().int().min(1).max(50).optional(),
    min_score: z.coerce.number().min(0).max(100).optional(),
  })
  .passthrough();

function json(data: unknown, status = 200) {
  return NextResponse.json(data, { status, headers: NO_STORE });
}

function safeEqual(a: string, b: string) {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}

function presentedToken(request: NextRequest) {
  const auth = request.headers.get('authorization') || '';
  if (auth.toLowerCase().startsWith('bearer ')) return auth.slice(7).trim();
  return request.headers.get('x-profitengine-token') || '';
}

async function readBody(request: NextRequest) {
  const raw = await request.text();
  if (!raw.trim()) return {};
  return JSON.parse(raw);
}

export async function POST(request: NextRequest) {
  const expected = process.env.PROFITENGINE_WEBHOOK_TOKEN || '';
  if (!expected) return json({ ok: false, error: 'PROFITENGINE_WEBHOOK_TOKEN is not configured' }, 503);
  const token = presentedToken(request);
  if (!token || !safeEqual(token, expected)) return json({ ok: false, error: 'Unauthorized' }, 401);

  let body: z.infer<typeof BodySchema>;
  try {
    const parsed = BodySchema.safeParse(await readBody(request));
    if (!parsed.success) return json({ ok: false, error: 'Invalid scan request', issues: parsed.error.issues }, 400);
    body = parsed.data;
  } catch {
    return json({ ok: false, error: 'Request body must be JSON' }, 400);
  }

  try {
    const hasStore = Boolean(process.env.MONGODB_URI || process.env.MONGO_URL);
    const result = await runDailyCommandScan({
      limit: body.limit,
      minScore: body.min_score,
      store: hasStore ? createMongoScanStore(getCollection) : null,
    });
    return json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Revenue scan failed';
    return json({ ok: false, error: message }, 500);
  }
}

export async function GET() {
  return json({ ok: false, error: 'Use POST' }, 405);
}

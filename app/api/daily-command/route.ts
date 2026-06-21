import { NextResponse } from 'next/server';

import { buildDailyCommandVerificationFeed, createDailyCommandSnapshot } from '@/lib/daily-command-core';

export const dynamic = 'force-dynamic';

export function GET(request: Request) {
  const url = new URL(request.url);
  const includeVerificationFeed = url.searchParams.get('verify') === '1';
  const now = new Date().toISOString();
  const systemInput = {
    id: 'SYSTEM_DAILY_COMMAND_API',
    source: 'VERCEL',
    category: 'SYSTEM_HEALTH',
    status: 'READY_TO_ACT',
    revenueStatus: 'NON_REVENUE',
    title: 'Daily Command API route available',
    description: 'Read-only Daily Command endpoint is mounted and ready for approved server-side signal feeds.',
    flags: [],
    timestamp: now,
  };
  const rawInputs = includeVerificationFeed ? [systemInput, ...buildDailyCommandVerificationFeed()] : [systemInput];
  const snapshot = createDailyCommandSnapshot(rawInputs, [], { generatedAt: now });

  return NextResponse.json(snapshot, {
    status: snapshot.systemHealth === 'CRITICAL' ? 503 : 200,
    headers: { 'Cache-Control': 'no-store' },
  });
}

export async function POST(request: Request) {
  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'INVALID_JSON' }, { status: 400 });
  }

  const record = typeof body === 'object' && body !== null && !Array.isArray(body) ? (body as Record<string, unknown>) : {};
  const rawInputs = Array.isArray(record.rawInputs) ? record.rawInputs : [];
  const history = Array.isArray(record.history) ? record.history : [];
  const dailyTargetUsd = typeof record.dailyTargetUsd === 'number' && record.dailyTargetUsd > 0 ? record.dailyTargetUsd : undefined;
  const snapshot = createDailyCommandSnapshot(rawInputs, [], { dailyTargetUsd });

  return NextResponse.json({ ...snapshot, receivedHistoryCount: history.length }, {
    status: snapshot.systemHealth === 'CRITICAL' ? 207 : 200,
    headers: { 'Cache-Control': 'no-store' },
  });
}

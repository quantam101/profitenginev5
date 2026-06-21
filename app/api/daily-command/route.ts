import { NextResponse } from 'next/server';

import {
  buildDailyCommandVerificationFeed,
  createDailyCommandSnapshot,
  type HistoricalFailureSignature,
} from '@/lib/daily-command-core';

export const dynamic = 'force-dynamic';

const FAILURE_TYPES = new Set([
  'SLOW_PAYMENT',
  'SCOPE_CREEP',
  'ROUTE_FRICTION',
  'QUALITY_DISPUTE',
  'CANCELLED_AFTER_ACCEPT',
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function extractHistory(value: unknown): HistoricalFailureSignature[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((entry): entry is HistoricalFailureSignature => {
    if (!isRecord(entry)) {
      return false;
    }

    return (
      typeof entry.vendorId === 'string' &&
      typeof entry.failureType === 'string' &&
      FAILURE_TYPES.has(entry.failureType) &&
      typeof entry.severity === 'number' &&
      Number.isFinite(entry.severity)
    );
  });
}

function buildSystemInput(now: string) {
  return {
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
}

export function GET(request: Request) {
  const url = new URL(request.url);
  const includeVerificationFeed = url.searchParams.get('verify') === '1';
  const now = new Date().toISOString();
  const rawInputs = includeVerificationFeed
    ? [buildSystemInput(now), ...buildDailyCommandVerificationFeed()]
    : [buildSystemInput(now)];
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

  const record = isRecord(body) ? body : {};
  const rawInputs = Array.isArray(record.rawInputs) ? record.rawInputs : [];
  const history = extractHistory(record.history);
  const dailyTargetUsd =
    typeof record.dailyTargetUsd === 'number' && Number.isFinite(record.dailyTargetUsd) && record.dailyTargetUsd > 0
      ? record.dailyTargetUsd
      : undefined;
  const snapshot = createDailyCommandSnapshot(rawInputs, history, { dailyTargetUsd });

  return NextResponse.json(
    { ...snapshot, receivedHistoryCount: history.length },
    {
      status: snapshot.systemHealth === 'CRITICAL' ? 207 : 200,
      headers: { 'Cache-Control': 'no-store' },
    }
  );
}

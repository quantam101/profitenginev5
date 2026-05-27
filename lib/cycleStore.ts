/**
 * cycleStore — Upstash Redis backend for cycle log data.
 *
 * The Python runtime (run via GitHub Actions cron) writes cycle records
 * here after each execution. Vercel API routes read from here.
 *
 * Keys:
 *   cycles:records   — Redis list of JSON CycleRecord objects (newest first, cap 1000)
 *   cycles:metrics   — Redis hash of aggregate stats (updated each cycle run)
 *
 * Required Vercel env vars:
 *   UPSTASH_REDIS_REST_URL
 *   UPSTASH_REDIS_REST_TOKEN
 */

import { Redis } from '@upstash/redis';

export interface CycleRecord {
  cycle_id: string;
  iso_timestamp: string;
  timestamp: number;
  agent_id: string;
  route_tier: string;
  objective_excerpt: string;
  output_excerpt: string;
  status: string;
  duration_ms: number;
  cached: boolean;
  details: Record<string, unknown>;
}

export interface CycleMetrics {
  total_cycles: number;
  successful_cycles: number;
  success_rate_pct: number;
  avg_duration_ms: number;
  tier_distribution: Record<string, number>;
  agent_distribution: Record<string, number>;
  last_cycle_iso: string | null;
}

const RECORDS_KEY = 'cycles:records';
const METRICS_KEY = 'cycles:metrics';
const MAX_RECORDS = 1000;

function getRedis(): Redis | null {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;
  return new Redis({ url, token });
}

export async function getRecentCycles(limit = 50): Promise<CycleRecord[]> {
  const redis = getRedis();
  if (!redis) return [];
  const raw = await redis.lrange<string>(RECORDS_KEY, 0, limit - 1);
  return raw
    .map((item) => {
      try {
        return typeof item === 'string' ? (JSON.parse(item) as CycleRecord) : (item as CycleRecord);
      } catch {
        return null;
      }
    })
    .filter((r): r is CycleRecord => r !== null);
}

export async function saveCycleRecord(record: CycleRecord): Promise<void> {
  const redis = getRedis();
  if (!redis) return;
  await redis.lpush(RECORDS_KEY, JSON.stringify(record));
  await redis.ltrim(RECORDS_KEY, 0, MAX_RECORDS - 1);
}

export async function getCycleMetrics(): Promise<CycleMetrics | null> {
  const redis = getRedis();
  if (!redis) return null;
  const raw = await redis.get<string>(METRICS_KEY);
  if (!raw) return null;
  try {
    return typeof raw === 'string' ? (JSON.parse(raw) as CycleMetrics) : (raw as CycleMetrics);
  } catch {
    return null;
  }
}

export async function saveCycleMetrics(metrics: CycleMetrics): Promise<void> {
  const redis = getRedis();
  if (!redis) return;
  await redis.set(METRICS_KEY, JSON.stringify(metrics), { ex: 86400 * 7 }); // 7d TTL
}

/**
 * Landing Page Metrics API
 * Returns runtime trading metrics from clients.db via landing_page_generator.py.
 *
 * Endpoint: GET /api/landing-metrics
 * Cache: runtime response cache only
 * Response: JSON with hero, social proof, performance, pricing, and trust metrics
 */

import { NextResponse } from 'next/server';
import { spawn } from 'child_process';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

// Cache metrics in memory with 5-minute TTL
interface CachedMetrics {
  data: any;
  timestamp: number;
}

let cachedMetrics: CachedMetrics | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Execute Python landing_page_generator to collect metrics.
 * This must stay runtime-only because Vercel build workers do not have the
 * production SQLite tables mounted.
 */
async function getLandingMetrics(): Promise<any> {
  // Check cache first
  const now = Date.now();
  if (cachedMetrics && now - cachedMetrics.timestamp < CACHE_DURATION) {
    console.log('[metrics] Returning cached metrics');
    return cachedMetrics.data;
  }

  return new Promise((resolve, reject) => {
    const python = spawn('python3', [
      '-c',
      `
import sys
import json
sys.path.insert(0, '${process.cwd()}')

from app.landing_page_generator import LandingPageGenerator

gen = LandingPageGenerator()
metrics = gen.get_current_metrics()
print(gen.generate_metrics_json(metrics))
`.trim(),
    ]);

    let output = '';
    let errorOutput = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        console.warn('[metrics] Python metrics unavailable, returning fallback:', errorOutput);
        reject(new Error(`Python process exited with code ${code}: ${errorOutput}`));
        return;
      }

      try {
        const metrics = JSON.parse(output);

        // Cache the result
        cachedMetrics = {
          data: metrics,
          timestamp: Date.now(),
        };

        resolve(metrics);
      } catch (err) {
        console.warn('[metrics] JSON parse unavailable, returning fallback:', err);
        reject(new Error(`Failed to parse metrics JSON: ${err}`));
      }
    });
  });
}

/**
 * Fallback metrics in case Python/database metrics are unavailable.
 * This prevents frontend breakage while keeping the response honest.
 */
function getFallbackMetrics() {
  return {
    timestamp: new Date().toISOString(),
    mode: 'fallback',
    hero: {
      current_win_rate: '0.0%',
      total_users: 0,
      weekly_pnl: '$0.00',
      total_trades_week: 0,
    },
    social_proof: [],
    performance: [],
    pricing: {
      tier_breakdown: {},
      avg_mrr_by_tier: {},
      total_revenue: '$0.00',
    },
    trust: {
      customer_count: 0,
      total_pnl_generated: '$0.00',
      uptime_percent: '0.0%',
      days_profitable: 0,
    },
  };
}

export async function GET() {
  try {
    console.log('[metrics] Fetching landing page metrics...');

    const metrics = await Promise.race([
      getLandingMetrics(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Metrics fetch timeout')), 10000)
      ),
    ]);

    return NextResponse.json(metrics, {
      headers: {
        'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600',
        'Content-Type': 'application/json',
      },
    });
  } catch (err) {
    console.warn('[metrics] Returning fallback metrics:', err);

    return NextResponse.json(
      {
        ...getFallbackMetrics(),
        error: 'Metrics temporarily unavailable',
      },
      {
        status: 200,
        headers: {
          'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=300',
        },
      }
    );
  }
}

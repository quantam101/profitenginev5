/**
 * Landing Page Metrics API
 * Returns real-time trading metrics from clients.db via landing_page_generator.py
 *
 * Endpoint: GET /api/landing-metrics
 * Cache: 5 minutes (matches update frequency)
 * Response: JSON with hero, social proof, performance, pricing, and trust metrics
 */

import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

// Cache metrics in memory with 5-minute TTL
interface CachedMetrics {
  data: any;
  timestamp: number;
}

let cachedMetrics: CachedMetrics | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Execute Python landing_page_generator to collect metrics
 */
async function getLandingMetrics(): Promise<any> {
  // Check cache first
  const now = Date.now();
  if (cachedMetrics && now - cachedMetrics.timestamp < CACHE_DURATION) {
    console.log('[metrics] Returning cached metrics');
    return cachedMetrics.data;
  }

  return new Promise((resolve, reject) => {
    // Spawn Python process to run generator
    const pythonPath = path.join(process.cwd(), 'app', 'landing_page_generator.py');

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
        console.error('[metrics] Python error:', errorOutput);
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
        console.error('[metrics] JSON parse error:', err);
        reject(new Error(`Failed to parse metrics JSON: ${err}`));
      }
    });
  });
}

/**
 * Fallback metrics in case Python fails
 * This ensures the API never fully breaks
 */
function getFallbackMetrics() {
  return {
    timestamp: new Date().toISOString(),
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
    console.error('[metrics] Error:', err);

    // Return fallback metrics with 200 status to prevent frontend errors
    // but include an error flag
    return NextResponse.json(
      {
        ...getFallbackMetrics(),
        error: 'Metrics temporarily unavailable',
      },
      {
        status: 200, // Still 200 to prevent frontend from breaking
        headers: {
          'Cache-Control': 'public, s-maxage=60', // Cache fallback for 1 minute
        },
      }
    );
  }
}

// Preload metrics on startup
export const revalidate = 300; // Next.js ISR: revalidate every 5 minutes

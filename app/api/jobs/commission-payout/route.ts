import { NextRequest, NextResponse } from 'next/server';
import { dailyCommissionPayout } from '@/lib/commission-payout';

/**
 * Daily Commission Payout Job
 *
 * This endpoint is called once per day (e.g., by Vercel Cron Jobs)
 * to calculate and process commission payouts to clients
 *
 * Usage:
 *   POST /api/jobs/commission-payout
 *
 * Can be scheduled with Vercel Cron:
 *   In vercel.json:
 *   {
 *     "crons": [{
 *       "path": "/api/jobs/commission-payout",
 *       "schedule": "0 0 * * *"
 *     }]
 *   }
 */

export async function POST(request: NextRequest) {
  // Verify the request is from Vercel Cron (optional security check)
  const authHeader = request.headers.get('authorization');

  if (process.env.CRON_SECRET && authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  try {
    console.log('Starting daily commission payout job...');

    const result = await dailyCommissionPayout();

    return NextResponse.json(
      {
        ok: result.success,
        message: 'Commission payout job completed',
        payouts_processed: result.payouts.length,
        total_commission: (result.totalCommission / 100).toFixed(2),
        errors: result.errors,
      },
      { status: result.success ? 200 : 500 }
    );
  } catch (error) {
    console.error('Commission payout job failed:', error);

    return NextResponse.json(
      {
        ok: false,
        error: 'Commission payout job failed',
        message: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  return NextResponse.json(
    {
      message: 'Commission payout job endpoint',
      method: 'POST',
      schedule: '0 0 * * * (daily at 00:00 UTC)',
      description: 'Calculates and processes commission payouts for all live clients',
    },
    { status: 200 }
  );
}

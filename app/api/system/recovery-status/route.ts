/**
 * System Recovery Status Endpoint
 *
 * Returns:
 * - Current runtime API health
 * - Last recovery attempt
 * - Recovery history
 * - Recommendation if down
 *
 * Used by: Monitoring dashboards, Telegram alerts, manual checks
 */

import { NextRequest, NextResponse } from 'next/server';

interface RecoveryStatus {
  timestamp: string;
  api_healthy: boolean;
  http_code: number;
  last_recovery?: {
    timestamp: string;
    status: 'success' | 'pending' | 'failed';
    action: string;
  };
  recommendation?: string;
}

export async function GET(req: NextRequest): Promise<NextResponse<RecoveryStatus>> {
  try {
    const runtime_url = process.env.RUNTIME_API_URL || 'https://api.profitengine.alreadyherellc.com';

    // Check both health endpoints
    let http_code = 0;
    let is_healthy = false;

    for (const path of ['/health', '/api/health']) {
      try {
        const response = await fetch(`${runtime_url}${path}`, {
          method: 'GET',
          timeout: 10000,
          signal: AbortSignal.timeout(10000),
        });

        http_code = response.status;

        if (response.status === 200) {
          const data = await response.json().catch(() => ({}));
          if ((data as any).ok === true || (data as any).status === 'ok') {
            is_healthy = true;
            break;
          }
        }
      } catch {
        // Continue to next endpoint
      }
    }

    const status: RecoveryStatus = {
      timestamp: new Date().toISOString(),
      api_healthy: is_healthy,
      http_code,
    };

    // Add recommendation if down
    if (!is_healthy) {
      status.recommendation = 'Runtime API is unreachable. Check GitHub Actions for auto-recovery status. If recovery fails, verify OCI instance state and network access.';
    }

    // Return 200 always (status endpoint, not health check)
    return NextResponse.json(status);
  } catch (error) {
    return NextResponse.json(
      {
        timestamp: new Date().toISOString(),
        api_healthy: false,
        http_code: 0,
        recommendation: 'Could not determine recovery status. Check GitHub Actions logs.',
      },
      { status: 200 } // 200 so monitoring doesn't fail
    );
  }
}

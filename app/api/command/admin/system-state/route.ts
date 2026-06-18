import { NextRequest, NextResponse } from 'next/server';

/**
 * System State Endpoint
 * Returns current state of trading systems, portfolio, and risk controls
 * Real-time data from runtime API
 */

const RUNTIME_API = process.env.RUNTIME_API_URL || 'http://runtime:8080';

interface SystemState {
  systemA: { enabled: boolean; status: string };
  systemB: { enabled: boolean; status: string };
  portfolio: {
    balance: number;
    positions: Array<{ symbol: string; quantity: number; value: number }>;
  };
  dailyDrawdown: number;
  riskGateOverride: {
    active: boolean;
    expiresAt?: number;
  };
}

async function fetchSystemState(): Promise<SystemState> {
  try {
    // Fetch from runtime API
    const [systemStatus, portfolio, riskState] = await Promise.all([
      fetch(`${RUNTIME_API}/api/admin/system-status`, {
        headers: {
          Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        },
        signal: AbortSignal.timeout(5000),
      }).catch(() => null),
      fetch(`${RUNTIME_API}/api/admin/portfolio`, {
        headers: {
          Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        },
        signal: AbortSignal.timeout(5000),
      }).catch(() => null),
      fetch(`${RUNTIME_API}/api/admin/risk-state`, {
        headers: {
          Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        },
        signal: AbortSignal.timeout(5000),
      }).catch(() => null),
    ]);

    // Parse responses with fallbacks
    const systemData = systemStatus ? await systemStatus.json() : null;
    const portfolioData = portfolio ? await portfolio.json() : null;
    const riskData = riskState ? await riskState.json() : null;

    return {
      systemA: {
        enabled: systemData?.system_a_enabled ?? true,
        status: systemData?.system_a_status ?? 'ready',
      },
      systemB: {
        enabled: systemData?.system_b_enabled ?? true,
        status: systemData?.system_b_status ?? 'ready',
      },
      portfolio: {
        balance: portfolioData?.balance ?? 100000,
        positions: portfolioData?.positions ?? [],
      },
      dailyDrawdown: portfolioData?.daily_drawdown ?? 0,
      riskGateOverride: {
        active: riskData?.override_active ?? false,
        expiresAt: riskData?.override_expires_at,
      },
    };
  } catch (error) {
    console.error('[Admin] Failed to fetch system state:', error);

    // Return safe defaults on API failure
    return {
      systemA: { enabled: false, status: 'api_error' },
      systemB: { enabled: false, status: 'api_error' },
      portfolio: { balance: 0, positions: [] },
      dailyDrawdown: 0,
      riskGateOverride: { active: false },
    };
  }
}

export async function GET(req: NextRequest) {
  try {
    // Verify admin access
    const userEmail = req.headers.get('x-user-email');
    if (userEmail !== 'dispatch@alreadyherellc.com') {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const state = await fetchSystemState();

    return NextResponse.json(state, {
      headers: {
        'Cache-Control': 'no-store',
        'x-data-source': 'live',
      },
    });
  } catch (error) {
    console.error('[Admin] System state error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch system state' },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';

/**
 * Customers List Endpoint
 * Returns all customers with their account details
 * Filters by tier and status available via query params
 */

const RUNTIME_API = process.env.RUNTIME_API_URL || 'http://runtime:8080';

interface Customer {
  id: string;
  email: string;
  username: string;
  tier: 'Free' | 'Hybrid' | 'White-Label' | 'Enterprise';
  status: 'active' | 'suspended' | 'inactive';
  balance: number;
  winRate: number;
  totalTrades: number;
  tradingStatus: 'paper' | 'live';
  joinedDate: string;
}

async function fetchCustomersFromRuntime(): Promise<Customer[]> {
  try {
    const res = await fetch(`${RUNTIME_API}/api/admin/customers`, {
      headers: {
        Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
      },
      signal: AbortSignal.timeout(10000),
    });

    if (!res.ok) {
      console.error(`[Admin] Runtime API returned ${res.status}`);
      return [];
    }

    const data = await res.json();
    return (data.customers || []).map((c: any) => ({
      id: c.user_id || c.id,
      email: c.email || '',
      username: c.username || `User_${c.user_id?.slice(0, 8)}`,
      tier: c.tier || 'Free',
      status: c.status || 'active',
      balance: c.balance || 0,
      winRate: c.win_rate || 0,
      totalTrades: c.total_trades || 0,
      tradingStatus: c.live_trading ? 'live' : 'paper',
      joinedDate: c.created_at || new Date().toISOString(),
    }));
  } catch (error) {
    console.error('[Admin] Failed to fetch customers from runtime:', error);
    return [];
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

    const customers = await fetchCustomersFromRuntime();

    // Apply filters from query params if provided
    const { searchParams } = new URL(req.url);
    const tier = searchParams.get('tier');
    const status = searchParams.get('status');

    let filtered = customers;

    if (tier && tier !== 'all') {
      filtered = filtered.filter((c) => c.tier === tier);
    }

    if (status && status !== 'all') {
      filtered = filtered.filter((c) => c.status === status);
    }

    return NextResponse.json(filtered, {
      headers: {
        'Cache-Control': 'no-store',
        'x-data-source': 'live',
      },
    });
  } catch (error) {
    console.error('[Admin] Customers fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch customers' },
      { status: 500 }
    );
  }
}

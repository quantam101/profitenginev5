import { NextRequest, NextResponse } from 'next/server';

/**
 * Trading Signals Endpoint
 * Returns current signals being evaluated and recent executed trades
 */

const RUNTIME_API = process.env.RUNTIME_API_URL || 'http://runtime:8080';

interface Signal {
  id: string;
  timestamp: string;
  symbol: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  strategies: string[];
  status: 'evaluated' | 'executed' | 'rejected';
  agreedStrategies: number;
  totalStrategies: number;
}

interface RecentTrade {
  id: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: string;
  pnl?: number;
  pnlPercent?: number;
}

async function fetchSignals(): Promise<{ signals: Signal[]; recentTrades: RecentTrade[] }> {
  try {
    const [signalsRes, tradesRes] = await Promise.all([
      fetch(`${RUNTIME_API}/api/admin/signals`, {
        headers: {
          Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        },
        signal: AbortSignal.timeout(5000),
      }).catch(() => null),
      fetch(`${RUNTIME_API}/api/admin/recent-trades`, {
        headers: {
          Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        },
        signal: AbortSignal.timeout(5000),
      }).catch(() => null),
    ]);

    const signals: Signal[] = [];
    const recentTrades: RecentTrade[] = [];

    if (signalsRes?.ok) {
      const data = await signalsRes.json();
      const rawSignals = data.signals || [];

      signals.push(
        ...rawSignals.map((s: any) => ({
          id: s.id || `signal_${Date.now()}`,
          timestamp: s.timestamp || new Date().toISOString(),
          symbol: s.symbol || 'UNKNOWN',
          action: s.action || 'HOLD',
          confidence: s.confidence || 0,
          strategies: s.strategies || [],
          status: s.status || 'evaluated',
          agreedStrategies: s.agreed_strategies || 0,
          totalStrategies: s.total_strategies || 1,
        }))
      );
    }

    if (tradesRes?.ok) {
      const data = await tradesRes.json();
      const rawTrades = data.trades || [];

      recentTrades.push(
        ...rawTrades.map((t: any) => ({
          id: t.id || `trade_${Date.now()}`,
          symbol: t.symbol || 'UNKNOWN',
          action: t.action || 'BUY',
          quantity: t.quantity || 0,
          price: t.price || 0,
          timestamp: t.timestamp || new Date().toISOString(),
          pnl: t.pnl,
          pnlPercent: t.pnl_percent,
        }))
      );
    }

    return { signals, recentTrades };
  } catch (error) {
    console.error('[Admin] Failed to fetch signals:', error);
    return { signals: [], recentTrades: [] };
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

    const { signals, recentTrades } = await fetchSignals();

    return NextResponse.json(
      {
        signals: signals.slice(0, 10), // Limit to 10 current signals
        recentTrades: recentTrades.slice(0, 20), // Limit to 20 recent trades
      },
      {
        headers: {
          'Cache-Control': 'no-store',
          'x-data-source': 'live',
        },
      }
    );
  } catch (error) {
    console.error('[Admin] Signals fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch trading signals' },
      { status: 500 }
    );
  }
}

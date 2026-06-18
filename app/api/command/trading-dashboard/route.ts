import { NextResponse } from 'next/server';

const RUNTIME = process.env.RUNTIME_API_URL ?? 'http://runtime:8080';

interface DashboardMetrics {
  active_traders_today: number;
  top_performers_by_win_rate: Array<{
    rank: number;
    user_id: string;
    username: string | null;
    win_rate: number;
    total_pnl: number;
    total_trades: number;
  }>;
  biggest_gainers: Array<{
    rank: number;
    user_id: string;
    username: string | null;
    pnl_percent: number;
    total_pnl: number;
    total_trades: number;
  }>;
  new_signups_today: number;
  avg_daily_pnl: number;
  upsell_candidates: Array<{
    user_id: string;
    username: string | null;
    current_pnl: number;
    win_rate: number;
    total_trades: number;
    days_active: number;
    urgency: string;
  }>;
  timestamp: string;
  summary: {
    total_trades_today: number;
    total_pnl_today: number;
    total_active_traders: number;
  };
}

async function runtimeFetch(path: string, timeoutMs = 5000) {
  try {
    const res = await fetch(`${RUNTIME}${path}`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(timeoutMs),
      headers: {
        Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
      },
    });
    if (!res.ok) {
      console.error(`runtime ${res.status} ${path}`);
      throw new Error(`runtime ${res.status} ${path}`);
    }
    return res.json();
  } catch (error) {
    console.error(`Failed to fetch ${path}:`, error);
    throw error;
  }
}

export async function GET() {
  try {
    // Fetch all required data from the runtime API
    const [stats, winRateLeaderboard, pnlLeaderboard, upsellCandidates] = await Promise.all([
      runtimeFetch('/api/clients/stats'),
      runtimeFetch('/api/clients/leaderboard?metric=win_rate&limit=5&days=30'),
      runtimeFetch('/api/clients/leaderboard?metric=pnl&limit=5&days=30'),
      runtimeFetch('/api/clients/upsell-candidates?days=30'),
    ]);

    // Extract metrics from responses
    const totalActiveTraders = stats.active_traders || 0;
    const avgDailyPnL = stats.total_pnl / Math.max(stats.total_trades || 1, 1);

    // Process win rate leaderboard
    const topPerformers = (winRateLeaderboard.entries || []).map(
      (entry: any, idx: number) => ({
        rank: idx + 1,
        user_id: entry.user_id,
        username: entry.username || `Trader ${entry.user_id.slice(0, 8)}`,
        win_rate: entry.metric_value || 0,
        total_pnl: entry.secondary_value || 0,
        total_trades: entry.account_age_days || 0, // Fallback
      })
    );

    // Process P&L leaderboard for biggest gainers
    const biggestGainers = (pnlLeaderboard.entries || []).map(
      (entry: any, idx: number) => {
        const totalTrades = entry.account_age_days || 1;
        const pnlPercent =
          totalTrades > 0
            ? ((entry.metric_value || 0) / (totalTrades > 0 ? totalTrades * 100 : 100)) * 100
            : 0;
        return {
          rank: idx + 1,
          user_id: entry.user_id,
          username: entry.username || `Trader ${entry.user_id.slice(0, 8)}`,
          pnl_percent: Math.round(pnlPercent * 100) / 100,
          total_pnl: entry.metric_value || 0,
          total_trades: entry.account_age_days || 0,
        };
      }
    );

    // Process upsell candidates
    const upsellList = (Array.isArray(upsellCandidates) ? upsellCandidates : upsellCandidates.candidates || []).map(
      (candidate: any) => ({
        user_id: candidate.user_id,
        username: candidate.username || `Trader ${candidate.user_id.slice(0, 8)}`,
        current_pnl: candidate.current_pnl || 0,
        win_rate: candidate.win_rate || 0,
        total_trades: candidate.total_trades || 0,
        days_active: candidate.days_active || 0,
        urgency: candidate.urgency || 'low',
      })
    );

    // Build response
    const response: DashboardMetrics = {
      active_traders_today: totalActiveTraders,
      top_performers_by_win_rate: topPerformers.slice(0, 5),
      biggest_gainers: biggestGainers.slice(0, 5),
      new_signups_today: 0, // Would need additional tracking
      avg_daily_pnl: Math.round(avgDailyPnL * 100) / 100,
      upsell_candidates: upsellList.slice(0, 5),
      timestamp: new Date().toISOString(),
      summary: {
        total_trades_today: stats.total_trades || 0,
        total_pnl_today: Math.round((stats.total_pnl || 0) * 100) / 100,
        total_active_traders: totalActiveTraders,
      },
    };

    return NextResponse.json(response, {
      headers: { 'Cache-Control': 'no-store', 'x-data-source': 'live' },
    });
  } catch (error) {
    console.error('Dashboard fetch failed:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch trading dashboard data',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 502 }
    );
  }
}

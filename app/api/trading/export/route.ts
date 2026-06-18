/**
 * Trading Data Export API Endpoint
 *
 * Handles:
 * - CSV export of trades
 * - PDF report generation (HTML-based)
 * - Tax reporting CSV
 * - Date range filtering
 * - User authentication & authorization
 */

import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { ClientsDB } from '@/lib/clients-db';
import {
  generateTradingReportHTML,
  generateCSVExport,
  generateTaxCSVExport,
  type TradeRecord,
  type DailyPerformance,
  type MonthlyPerformance,
  type TaxReportData,
  type ReportConfig,
} from '@/lib/reports/trading-report';

const RUNTIME = process.env.RUNTIME_API_URL ?? 'http://runtime:8080';

interface RuntimeTrade {
  id: number;
  user_id: number;
  date: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_percent: number;
  duration_days: number;
  strategy?: string;
  tags?: string;
}

interface RuntimeDailyTrade {
  id: number;
  user_id: number;
  date: string;
  num_trades: number;
  win_count: number;
  loss_count: number;
  pnl_dollars: number;
  pnl_percent: number;
  balance: number;
  win_rate: number;
}

/**
 * Fetch trades from runtime API with authentication
 */
async function fetchUserTrades(
  userId: string,
  startDate?: string,
  endDate?: string,
  timeoutMs = 10000
): Promise<RuntimeTrade[]> {
  try {
    const params = new URLSearchParams({
      user_id: userId,
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate }),
    });

    const res = await fetch(`${RUNTIME}/api/clients/trades?${params}`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(timeoutMs),
      headers: {
        Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
      },
    });

    if (!res.ok) {
      console.error(`Runtime trades API ${res.status}`);
      return [];
    }

    const data = await res.json();
    return Array.isArray(data) ? data : data.trades || [];
  } catch (error) {
    console.error('Failed to fetch trades:', error);
    return [];
  }
}

/**
 * Fetch daily trades from runtime API
 */
async function fetchDailyTrades(
  userId: string,
  days: number = 90
): Promise<RuntimeDailyTrade[]> {
  try {
    const res = await fetch(
      `${RUNTIME}/api/clients/${userId}/daily-trades?days=${days}`,
      {
        cache: 'no-store',
        signal: AbortSignal.timeout(5000),
        headers: {
          Authorization: `Bearer ${process.env.CLIENT_API_KEY || 'default-dev-key'}`,
        },
      }
    );

    if (!res.ok) {
      return [];
    }

    const data = await res.json();
    return Array.isArray(data) ? data : data.daily_trades || [];
  } catch (error) {
    console.error('Failed to fetch daily trades:', error);
    return [];
  }
}

/**
 * Calculate monthly aggregates from daily data
 */
function calculateMonthlyPerformance(
  dailyTrades: RuntimeDailyTrade[]
): MonthlyPerformance[] {
  const monthMap = new Map<string, MonthlyPerformance>();

  dailyTrades.forEach((day) => {
    const date = new Date(day.date);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

    if (!monthMap.has(monthKey)) {
      monthMap.set(monthKey, {
        month: monthKey,
        trades: 0,
        wins: 0,
        losses: 0,
        winRate: 0,
        totalPnl: 0,
        totalPnlPercent: 0,
      });
    }

    const month = monthMap.get(monthKey)!;
    month.trades += day.num_trades;
    month.wins += day.win_count;
    month.losses += day.loss_count;
    month.totalPnl += day.pnl_dollars;
    month.totalPnlPercent += day.pnl_percent;
  });

  // Calculate win rates
  monthMap.forEach((month) => {
    if (month.wins + month.losses > 0) {
      month.winRate = (month.wins / (month.wins + month.losses)) * 100;
    }
  });

  return Array.from(monthMap.values()).sort((a, b) => a.month.localeCompare(b.month));
}

/**
 * Convert daily trades to daily performance format
 */
function convertToDailyPerformance(
  dailyTrades: RuntimeDailyTrade[]
): DailyPerformance[] {
  return dailyTrades.map((day) => ({
    date: day.date,
    trades: day.num_trades,
    wins: day.win_count,
    losses: day.loss_count,
    winRate: day.win_rate,
    pnlDollars: day.pnl_dollars,
    pnlPercent: day.pnl_percent,
    balance: day.balance,
  }));
}

/**
 * Calculate tax reporting data
 */
function calculateTaxData(trades: RuntimeTrade[]): TaxReportData {
  const today = new Date();
  let shortTermGains = 0;
  let longTermGains = 0;
  let totalLosses = 0;
  const washSales: TaxReportData['washSales'] = [];

  // Group trades by symbol to detect wash sales
  const tradesBySymbol = new Map<string, RuntimeTrade[]>();
  trades.forEach((trade) => {
    if (!tradesBySymbol.has(trade.symbol)) {
      tradesBySymbol.set(trade.symbol, []);
    }
    tradesBySymbol.get(trade.symbol)!.push(trade);
  });

  trades.forEach((trade) => {
    if (trade.pnl >= 0) {
      const tradeDate = new Date(trade.date);
      const daysDifference = Math.floor(
        (today.getTime() - tradeDate.getTime()) / (1000 * 60 * 60 * 24)
      );

      if (daysDifference >= 365) {
        longTermGains += trade.pnl;
      } else {
        shortTermGains += trade.pnl;
      }
    } else {
      totalLosses += Math.abs(trade.pnl);

      // Check for wash sales (repurchase within 30 days)
      const symbolTrades = tradesBySymbol.get(trade.symbol) || [];
      const tradeDate = new Date(trade.date);

      symbolTrades.forEach((otherTrade) => {
        if (
          otherTrade.side === 'BUY' &&
          otherTrade.date > trade.date
        ) {
          const otherDate = new Date(otherTrade.date);
          const daysDiff = Math.floor(
            (otherDate.getTime() - tradeDate.getTime()) / (1000 * 60 * 60 * 24)
          );

          if (daysDiff <= 30) {
            washSales.push({
              date: trade.date,
              symbol: trade.symbol,
              loss: Math.abs(trade.pnl),
              repurchaseDate: otherTrade.date,
            });
          }
        }
      });
    }
  });

  const totalGains = shortTermGains + longTermGains;
  const netGains = totalGains - totalLosses;

  return {
    shortTermGains,
    longTermGains,
    totalGains,
    totalLosses,
    netGains,
    washSales,
    exportDate: new Date().toISOString(),
  };
}

/**
 * Calculate summary statistics
 */
function calculateSummary(trades: RuntimeTrade[]) {
  if (trades.length === 0) {
    return {
      totalTrades: 0,
      totalWins: 0,
      totalLosses: 0,
      overallWinRate: 0,
      totalPnlDollars: 0,
      totalPnlPercent: 0,
      bestTrade: null as any,
      worstTrade: null as any,
      averageTrade: 0,
      maxDrawdown: 0,
    };
  }

  const winningTrades = trades.filter((t) => t.pnl > 0);
  const losingTrades = trades.filter((t) => t.pnl < 0);
  const bestTrade = trades.reduce((best, trade) =>
    trade.pnl > best.pnl ? trade : best
  );
  const worstTrade = trades.reduce((worst, trade) =>
    trade.pnl < worst.pnl ? trade : worst
  );

  let totalPnl = 0;
  let maxDrawdown = 0;
  let peakBalance = 0;

  const sortedTrades = [...trades].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  let runningBalance = 0;
  sortedTrades.forEach((trade) => {
    runningBalance += trade.pnl;
    totalPnl += trade.pnl;

    if (runningBalance > peakBalance) {
      peakBalance = runningBalance;
    }

    const drawdown = peakBalance - runningBalance;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  });

  const totalPnlPercent = trades.length > 0 ? (totalPnl / Math.max(Math.abs(totalPnl), 1)) * 100 : 0;

  return {
    totalTrades: trades.length,
    totalWins: winningTrades.length,
    totalLosses: losingTrades.length,
    overallWinRate:
      trades.length > 0
        ? (winningTrades.length / trades.length) * 100
        : 0,
    totalPnlDollars: totalPnl,
    totalPnlPercent,
    bestTrade,
    worstTrade,
    averageTrade: trades.length > 0 ? totalPnl / trades.length : 0,
    maxDrawdown: (maxDrawdown / Math.max(peakBalance, 1)) * 100,
  };
}

export async function POST(request: NextRequest) {
  try {
    // Authenticate user
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = (session.user as any).id || session.user.email;

    // Parse request body
    const body = await request.json();
    const {
      format = 'csv', // 'csv', 'pdf', 'tax-csv'
      startDate,
      endDate,
      dataType = 'all', // 'all', 'summary', 'trades', 'tax'
    } = body;

    if (!['csv', 'pdf', 'tax-csv'].includes(format)) {
      return NextResponse.json(
        { error: 'Invalid format. Use: csv, pdf, tax-csv' },
        { status: 400 }
      );
    }

    // Calculate date range (default: last 90 days)
    let start = startDate;
    let end = endDate;

    if (!end) {
      end = new Date().toISOString().split('T')[0];
    }

    if (!start) {
      const date = new Date();
      date.setDate(date.getDate() - 90);
      start = date.toISOString().split('T')[0];
    }

    // Fetch trade data from runtime
    const trades = await fetchUserTrades(userId, start, end);

    if (trades.length === 0 && format !== 'pdf') {
      return NextResponse.json(
        { error: 'No trades found for the specified date range' },
        { status: 404 }
      );
    }

    // Generate CSV export
    if (format === 'csv') {
      const csv = generateCSVExport(trades as any, {
        userId: parseInt(userId) || 0,
        username: session.user.name || session.user.email || 'Trader',
        email: session.user.email,
        startDate: start,
        endDate: end,
      });

      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': `attachment; filename="trading-export-${new Date().getTime()}.csv"`,
        },
      });
    }

    // Generate tax CSV export
    if (format === 'tax-csv') {
      const csv = generateTaxCSVExport(trades as any);

      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': `attachment; filename="tax-report-${new Date().getTime()}.csv"`,
        },
      });
    }

    // Generate PDF (HTML-based)
    if (format === 'pdf') {
      // Fetch daily trades for monthly aggregates
      const dailyTrades = await fetchDailyTrades(userId, 365);

      // Convert to performance format
      const dailyPerformance = convertToDailyPerformance(dailyTrades);
      const monthlyPerformance = calculateMonthlyPerformance(dailyTrades);

      // Calculate statistics
      const taxData = calculateTaxData(trades);
      const summary = calculateSummary(trades);

      // Create report config
      const reportConfig: ReportConfig = {
        userId: parseInt(userId) || 0,
        username: session.user.name || session.user.email || 'Trader',
        email: session.user.email,
        startDate: start,
        endDate: end,
        dailyPerformance,
        monthlyPerformance,
        trades: trades as any,
        taxData,
        summary,
      };

      // Generate HTML report
      const htmlReport = generateTradingReportHTML(reportConfig);

      return new NextResponse(htmlReport, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Content-Disposition': `attachment; filename="trading-report-${new Date().getTime()}.html"`,
        },
      });
    }

    return NextResponse.json(
      { error: 'Invalid request' },
      { status: 400 }
    );
  } catch (error) {
    console.error('Export error:', error);
    return NextResponse.json(
      {
        error: 'Failed to generate export',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * GET endpoint - returns export options and metadata
 */
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    return NextResponse.json({
      formats: [
        {
          id: 'csv',
          name: 'CSV Export',
          description: 'Standard CSV for Excel and accounting software',
          mimeType: 'text/csv',
        },
        {
          id: 'tax-csv',
          name: 'Tax Report CSV',
          description: 'Formatted for tax reporting (cost basis, holding period)',
          mimeType: 'text/csv',
        },
        {
          id: 'pdf',
          name: 'PDF Report',
          description: 'Comprehensive HTML report with charts and summaries',
          mimeType: 'text/html',
        },
      ],
      dataTypes: [
        {
          id: 'all',
          name: 'All Trades',
          description: 'Complete trade history for selected period',
        },
        {
          id: 'summary',
          name: 'Summary',
          description: 'Key metrics and performance overview',
        },
        {
          id: 'trades',
          name: 'Trades Only',
          description: 'Trade-by-trade details without analysis',
        },
        {
          id: 'tax',
          name: 'Tax Data',
          description: 'Capital gains, losses, and wash sale information',
        },
      ],
      defaultDateRange: {
        days: 90,
        description: 'Last 90 days',
      },
    });
  } catch (error) {
    console.error('Metadata fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch export metadata' },
      { status: 500 }
    );
  }
}

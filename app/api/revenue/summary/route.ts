import { NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';

interface Transaction {
  channel: string;
  amount_usd: number;
  timestamp: string;
  source_id: string;
  description: string;
  content_id: string;
  metadata: Record<string, unknown>;
}

interface ChannelMetrics {
  channel: string;
  total_revenue: number;
  transaction_count: number;
  average_transaction: number;
  rank: number;
  trend: string;
}

function getDateString(date?: Date): string {
  const d = date || new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function readTransactionsFromFile(): Transaction[] {
  const runtimeDir = join(process.cwd(), '.runtime', 'revenue');
  const txFile = join(runtimeDir, 'transactions.jsonl');

  if (!existsSync(txFile)) {
    console.warn(`Transaction file not found: ${txFile}`);
    return [];
  }

  try {
    const content = readFileSync(txFile, 'utf8');
    const lines = content.split('\n').filter(l => l.trim());
    return lines.map(line => {
      try {
        return JSON.parse(line) as Transaction;
      } catch (e) {
        console.error(`Failed to parse line: ${line}`, e);
        return null;
      }
    }).filter((tx): tx is Transaction => tx !== null);
  } catch (error) {
    console.error('Failed to read transactions file:', error);
    return [];
  }
}

export async function GET() {
  try {
    const transactions = readTransactionsFromFile();
    const today = getDateString();
    const yesterday = getDateString(new Date(Date.now() - 86400000));
    const weekAgo = getDateString(new Date(Date.now() - 7 * 86400000));
    const monthStart = getDateString(new Date(new Date().getFullYear(), new Date().getMonth(), 1));

    // Calculate daily totals
    const todayTx = transactions.filter(t => t.timestamp.startsWith(today));
    const yesterdayTx = transactions.filter(t => t.timestamp.startsWith(yesterday));
    const weekTx = transactions.filter(t => t.timestamp >= weekAgo);
    const monthTx = transactions.filter(t => t.timestamp >= monthStart);

    const todayRevenue = todayTx.reduce((sum, t) => sum + (t.amount_usd || 0), 0);
    const yesterdayRevenue = yesterdayTx.reduce((sum, t) => sum + (t.amount_usd || 0), 0);
    const weekRevenue = weekTx.reduce((sum, t) => sum + (t.amount_usd || 0), 0);
    const monthRevenue = monthTx.reduce((sum, t) => sum + (t.amount_usd || 0), 0);

    // Aggregate by channel
    const byChannel: Record<string, { total: number; count: number }> = {};
    for (const tx of transactions) {
      const channel = tx.channel || 'unknown';
      if (!byChannel[channel]) {
        byChannel[channel] = { total: 0, count: 0 };
      }
      byChannel[channel].total += tx.amount_usd || 0;
      byChannel[channel].count += 1;
    }

    // Format channel metrics with ranking
    const metrics: ChannelMetrics[] = Object.entries(byChannel)
      .map(([channel, data], idx) => ({
        channel,
        total_revenue: parseFloat(data.total.toFixed(2)),
        transaction_count: data.count,
        average_transaction: parseFloat((data.total / data.count).toFixed(2)),
        rank: idx + 1,
        trend: data.total > 0 ? '↗' : '→',
      }))
      .sort((a, b) => b.total_revenue - a.total_revenue)
      .map((m, idx) => ({ ...m, rank: idx + 1 }));

    const totalRevenue = transactions.reduce((sum, t) => sum + (t.amount_usd || 0), 0);
    const topChannel = metrics[0] || null;

    const response = {
      timestamp: new Date().toISOString(),
      status: 'ok',
      data: {
        today_revenue: parseFloat(todayRevenue.toFixed(2)),
        yesterday_revenue: parseFloat(yesterdayRevenue.toFixed(2)),
        week_revenue: parseFloat(weekRevenue.toFixed(2)),
        month_revenue: parseFloat(monthRevenue.toFixed(2)),
        total_all_time: parseFloat(totalRevenue.toFixed(2)),
        transaction_count: transactions.length,
        active_channels: metrics.length,
        top_channel: topChannel ? {
          channel: topChannel.channel,
          revenue: topChannel.total_revenue,
          transactions: topChannel.transaction_count,
        } : null,
        by_channel: metrics,
      },
      health: {
        data_source: 'local_jsonl',
        transactions_loaded: transactions.length,
        data_freshness_minutes: 0,
      },
    };

    return NextResponse.json(response, {
      headers: {
        'Cache-Control': 'no-store, max-age=0',
        'x-data-source': 'local-jsonl',
      },
    });
  } catch (error) {
    console.error('Revenue summary API error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';

    return NextResponse.json(
      {
        error: 'failed_to_calculate_revenue',
        message,
      },
      { status: 500 }
    );
  }
}

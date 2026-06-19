import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';

export const runtime = 'nodejs';

interface ChannelMetrics {
  channel: string;
  month: string;
  total_revenue: number;
  daily_average: number;
  transaction_count: number;
  days_with_revenue: number;
  target: number;
  progress_pct: number;
  rank: number;
  trend: string;
}

interface DashboardResponse {
  timestamp: string;
  period: string;
  today_revenue: number;
  yesterday_revenue: number;
  week_revenue: number;
  month_revenue: number;
  monthly_target: number;
  monthly_progress_pct: number;
  daily_goal: number;
  days_remaining: number;
  by_channel: Record<string, ChannelMetrics>;
  ltv_per_subscriber: number;
  estimated_subscribers: number;
  daily_burndown_needed: number;
  projected_month_end: number;
  will_hit_target: boolean;
  active_channels: number;
  last_update: string;
  health: {
    status: string;
    channels_responding: number;
    data_freshness_minutes: number;
  };
}

type MongoGlobal = typeof globalThis & {
  __revenueMongoClientPromise?: Promise<MongoClient>;
};

// Revenue targets for each channel ($2,500/mo total goal)
const CHANNEL_TARGETS = {
  newsletter: 400,      // Email sponsorships + paid subscribers
  gumroad: 400,         // eBooks, templates, guides
  printify: 1000,       // POD merchandise (PRIMARY)
  youtube: 400,         // AdSense revenue
  affiliate: 400,       // Amazon Associates + partner commissions
  sponsorships: 300,    // Brand partnerships
};

const MONTHLY_GOAL = 2500;

function getMongoUri(): string {
  const uri = process.env.MONGODB_URI || process.env.DATABASE_URL;
  if (!uri || !uri.startsWith('mongodb')) {
    throw new Error('Revenue storage is not configured. Set MONGODB_URI to a MongoDB connection string.');
  }
  return uri;
}

function getDatabaseName(): string {
  return process.env.MONGODB_DB || process.env.PROFITENGINE_DB || 'profitenginev5';
}

async function getMongoClient(): Promise<MongoClient> {
  const mongoGlobal = globalThis as MongoGlobal;

  if (!mongoGlobal.__revenueMongoClientPromise) {
    mongoGlobal.__revenueMongoClientPromise = new MongoClient(getMongoUri()).connect();
  }

  return mongoGlobal.__revenueMongoClientPromise;
}

function getDaysRemainingInMonth(): number {
  const now = new Date();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  return Math.max(1, daysInMonth - now.getDate());
}

function getMonthYearString(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function getDayYearString(date?: Date): string {
  const d = date || new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

async function getChannelRevenue(
  db: Awaited<ReturnType<MongoClient['db']>>,
  channel: string,
  month: string
): Promise<number> {
  try {
    const result = await db
      .collection('revenue_transactions')
      .aggregate([
        {
          $match: {
            channel,
            date: { $regex: `^${month}` },
          },
        },
        {
          $group: {
            _id: null,
            total: { $sum: '$amount_usd' },
          },
        },
      ])
      .toArray();

    return result.length > 0 ? result[0].total : 0;
  } catch (error) {
    console.error(`Failed to get revenue for ${channel}:`, error);
    return 0;
  }
}

async function getDailyRevenue(
  db: Awaited<ReturnType<MongoClient['db']>>,
  date: string
): Promise<Record<string, number>> {
  try {
    const transactions = await db
      .collection('revenue_transactions')
      .find({ date })
      .toArray();

    const byChannel: Record<string, number> = {};
    for (const tx of transactions) {
      const channel = tx.channel || 'unknown';
      byChannel[channel] = (byChannel[channel] || 0) + (tx.amount_usd || 0);
    }
    return byChannel;
  } catch (error) {
    console.error(`Failed to get daily revenue for ${date}:`, error);
    return {};
  }
}

async function getWeekRevenue(
  db: Awaited<ReturnType<MongoClient['db']>>
): Promise<Record<string, number>> {
  try {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const dateStr = getDayYearString(weekAgo);

    const transactions = await db
      .collection('revenue_transactions')
      .find({
        date: { $gte: dateStr },
      })
      .toArray();

    const byChannel: Record<string, number> = {};
    for (const tx of transactions) {
      const channel = tx.channel || 'unknown';
      byChannel[channel] = (byChannel[channel] || 0) + (tx.amount_usd || 0);
    }
    return byChannel;
  } catch (error) {
    console.error('Failed to get weekly revenue:', error);
    return {};
  }
}

export async function GET() {
  try {
    const client = await getMongoClient();
    const db = client.db(getDatabaseName());

    const now = new Date();
    const currentMonth = getMonthYearString();
    const today = getDayYearString();
    const yesterday = getDayYearString(new Date(now.getTime() - 86400000));

    // Fetch revenue data
    const todayRevenue = await getDailyRevenue(db, today);
    const yesterdayRevenue = await getDailyRevenue(db, yesterday);
    const weekRevenue = await getWeekRevenue(db);

    // Calculate daily and weekly totals
    const todayTotal = Object.values(todayRevenue).reduce((a, b) => a + b, 0);
    const yesterdayTotal = Object.values(yesterdayRevenue).reduce((a, b) => a + b, 0);
    const weekTotal = Object.values(weekRevenue).reduce((a, b) => a + b, 0);

    // Get monthly revenue by channel
    const byChannel: Record<string, ChannelMetrics> = {};
    let monthTotal = 0;
    let activeChannels = 0;

    for (const [channel, target] of Object.entries(CHANNEL_TARGETS)) {
      const channelRevenue = await getChannelRevenue(db, channel, currentMonth);
      monthTotal += channelRevenue;

      if (channelRevenue > 0) {
        activeChannels += 1;
      }

      const progressPct = target > 0 ? Math.min(100, (channelRevenue / target) * 100) : 0;

      byChannel[channel] = {
        channel,
        month: currentMonth,
        total_revenue: parseFloat(channelRevenue.toFixed(2)),
        daily_average: parseFloat((channelRevenue / now.getDate()).toFixed(2)),
        transaction_count: 0,
        days_with_revenue: 0,
        target: parseFloat(target.toFixed(2)),
        progress_pct: parseFloat(progressPct.toFixed(1)),
        rank: 0,
        trend: channelRevenue > 0 ? '↗' : '→',
      };
    }

    // Calculate ranking
    const ranked = Object.entries(byChannel).sort((a, b) => b[1].total_revenue - a[1].total_revenue);
    ranked.forEach(([_, metrics], idx) => {
      metrics.rank = idx + 1;
    });

    // Calculate progress and forecasts
    const monthlyProgress = MONTHLY_GOAL > 0 ? Math.min(100, (monthTotal / MONTHLY_GOAL) * 100) : 0;
    const daysRemaining = getDaysRemainingInMonth();
    const dailyNeeded = Math.max(0, (MONTHLY_GOAL - monthTotal) / daysRemaining);
    const projectedMonthEnd = monthTotal + dailyNeeded * daysRemaining;
    const willHitTarget = projectedMonthEnd >= MONTHLY_GOAL;

    // Estimate LTV per subscriber (assuming 2000 active subscribers)
    const estimatedSubscribers = 2000;
    const ltvPerSubscriber = estimatedSubscribers > 0 ? monthTotal / estimatedSubscribers : 0;

    const response: DashboardResponse = {
      timestamp: now.toISOString(),
      period: currentMonth,
      today_revenue: parseFloat(todayTotal.toFixed(2)),
      yesterday_revenue: parseFloat(yesterdayTotal.toFixed(2)),
      week_revenue: parseFloat(weekTotal.toFixed(2)),
      month_revenue: parseFloat(monthTotal.toFixed(2)),
      monthly_target: MONTHLY_GOAL,
      monthly_progress_pct: parseFloat(monthlyProgress.toFixed(1)),
      daily_goal: parseFloat((MONTHLY_GOAL / 30).toFixed(2)),
      days_remaining: daysRemaining,
      by_channel: byChannel,
      ltv_per_subscriber: parseFloat(ltvPerSubscriber.toFixed(2)),
      estimated_subscribers: estimatedSubscribers,
      daily_burndown_needed: parseFloat(dailyNeeded.toFixed(2)),
      projected_month_end: parseFloat(projectedMonthEnd.toFixed(2)),
      will_hit_target: willHitTarget,
      active_channels: activeChannels,
      last_update: now.toISOString(),
      health: {
        status: monthTotal > 0 ? 'healthy' : 'no_data',
        channels_responding: activeChannels,
        data_freshness_minutes: 0,
      },
    };

    return NextResponse.json(response, {
      headers: {
        'Cache-Control': 'no-store, max-age=0',
        'x-data-source': 'mongodb',
      },
    });
  } catch (error) {
    console.error('Revenue dashboard API error:', error);

    const message = error instanceof Error ? error.message : 'Unknown error';
    const isConfigError = message.includes('Revenue storage is not configured');

    return NextResponse.json(
      {
        error: isConfigError ? 'revenue_storage_not_configured' : 'failed_to_calculate_revenue',
        message,
      },
      { status: isConfigError ? 503 : 500 }
    );
  }
}

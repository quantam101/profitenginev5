import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';

export const runtime = 'nodejs';

interface RevenueMetrics {
  timestamp: string;
  monthYear: string;

  // KPIs
  mrr: number;
  arr: number;
  ltv: number;
  churnRate: number;
  cogs: number;
  netProfitMargin: number;

  // Customer metrics
  totalCustomers: number;
  payingCustomers: number;
  freeCustomers: number;
  newCustomersThisMonth: number;
  avgCustomerBalance: number;

  // Tier breakdown
  tierBreakdown: {
    free: number;
    hybrid: number;
    whiteLable: number;
    enterprise: number;
  };

  // Revenue by tier
  revenueByTier: {
    free: number;
    hybrid: number;
    whiteLable: number;
    enterprise: number;
  };

  // Monthly trend (last 12 months)
  monthlyTrend: Array<{
    month: string;
    mrr: number;
    customers: number;
    churnRate: number;
  }>;

  // Top customers
  topCustomers: Array<{
    userId: number;
    email: string;
    tier: string;
    balance: number;
    monthlyRevenue: number;
    ltv: number;
  }>;

  // Health checks
  health: {
    dataQuality: string;
    lastUpdate: string;
    recordsProcessed: number;
  };
}

type UserDocument = {
  userId?: number;
  id?: number;
  email?: string;
  tradingTier?: string;
  trading_tier?: string;
  signupDate?: string;
  signup_date?: string;
  createdAt?: Date | string;
  created_at?: Date | string;
  lastActiveAt?: Date | string | null;
  last_active_at?: Date | string | null;
  isActive?: boolean | number;
  is_active?: boolean | number;
  capitalAmount?: number;
};

type TradeDocument = {
  userId?: number;
  user_id?: number;
  date?: string;
  balance?: number;
  pnlDollars?: number;
  pnl_dollars?: number;
};

type MongoGlobal = typeof globalThis & {
  __profitEngineMongoClientPromise?: Promise<MongoClient>;
};

// Tier pricing model (% of AUM)
const TIER_PRICING = {
  free: 0.0,
  hybrid: 0.005,
  whiteLable: 0.01,
  enterprise: 0.015,
};

const MONTHLY_FIXED_COSTS = 500;

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

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

  if (!mongoGlobal.__profitEngineMongoClientPromise) {
    mongoGlobal.__profitEngineMongoClientPromise = new MongoClient(getMongoUri()).connect();
  }

  return mongoGlobal.__profitEngineMongoClientPromise;
}

function normalizeUserId(user: UserDocument): number {
  return user.userId ?? user.id ?? 0;
}

function normalizeTier(user: UserDocument): keyof typeof TIER_PRICING {
  const tier = user.tradingTier || user.trading_tier || 'free';

  if (tier === 'white-label' || tier === 'whiteLable') return 'whiteLable';
  if (tier === 'hybrid') return 'hybrid';
  if (tier === 'enterprise') return 'enterprise';

  return 'free';
}

function normalizeDate(value: Date | string | null | undefined): Date | null {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function isActiveUser(user: UserDocument): boolean {
  if (typeof user.isActive === 'boolean') return user.isActive;
  if (typeof user.is_active === 'boolean') return user.is_active;
  if (typeof user.isActive === 'number') return user.isActive === 1;
  if (typeof user.is_active === 'number') return user.is_active === 1;
  return true;
}

function getSignupDate(user: UserDocument): Date | null {
  return normalizeDate(user.signupDate || user.signup_date || user.createdAt || user.created_at);
}

function getLastActiveDate(user: UserDocument): Date | null {
  return normalizeDate(user.lastActiveAt || user.last_active_at || user.createdAt || user.created_at);
}

async function getLatestBalanceByUser(db: Awaited<ReturnType<MongoClient['db']>>): Promise<Map<number, number>> {
  const balanceByUser = new Map<number, number>();

  const trades = await db
    .collection<TradeDocument>('daily_trades')
    .find({})
    .sort({ date: -1 })
    .limit(25000)
    .toArray();

  for (const trade of trades) {
    const userId = trade.userId ?? trade.user_id ?? 0;
    if (!userId || balanceByUser.has(userId)) continue;
    if (typeof trade.balance === 'number') {
      balanceByUser.set(userId, trade.balance);
    }
  }

  return balanceByUser;
}

export async function GET() {
  try {
    const client = await getMongoClient();
    const db = client.db(getDatabaseName());

    const users = await db
      .collection<UserDocument>('users')
      .find({})
      .limit(10000)
      .toArray();

    const activeUsers = users.filter(isActiveUser);
    const latestBalanceByUser = await getLatestBalanceByUser(db);

    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const tierBreakdown = {
      free: 0,
      hybrid: 0,
      whiteLable: 0,
      enterprise: 0,
    };

    const revenueByTier = {
      free: 0,
      hybrid: 0,
      whiteLable: 0,
      enterprise: 0,
    };

    let mrrFromCustomers = 0;
    let totalBalance = 0;
    let payingCustomersCount = 0;

    const customerDetails: Array<{
      userId: number;
      email: string;
      tier: keyof typeof TIER_PRICING;
      balance: number;
      monthlyRevenue: number;
    }> = [];

    for (const user of activeUsers) {
      const tier = normalizeTier(user);
      tierBreakdown[tier] += 1;

      const userId = normalizeUserId(user);
      const balance = latestBalanceByUser.get(userId) ?? user.capitalAmount ?? 0;
      const tierPrice = TIER_PRICING[tier];
      const monthlyRevenue = balance * tierPrice;

      totalBalance += balance;
      revenueByTier[tier] += monthlyRevenue;

      if (monthlyRevenue > 0) {
        mrrFromCustomers += monthlyRevenue;
        payingCustomersCount += 1;
      }

      customerDetails.push({
        userId,
        email: user.email || 'unknown@example.com',
        tier,
        balance,
        monthlyRevenue,
      });
    }

    const avgMonthlyRevenue = payingCustomersCount > 0 ? mrrFromCustomers / payingCustomersCount : 0;
    const ltv = avgMonthlyRevenue * 24;
    const arr = mrrFromCustomers * 12;
    const paymentProcessingCost = mrrFromCustomers * 0.03;
    const apiCosts = Math.max(100, totalBalance > 0 ? (totalBalance / 100000) * 50 : 0);
    const cogs = paymentProcessingCost + apiCosts + MONTHLY_FIXED_COSTS;
    const netProfit = mrrFromCustomers - cogs;
    const netProfitMargin = mrrFromCustomers > 0 ? (netProfit / mrrFromCustomers) * 100 : 0;

    const churned = users.filter((user) => {
      const lastActive = getLastActiveDate(user);
      return !lastActive || lastActive < thirtyDaysAgo;
    }).length;

    const churnRate = activeUsers.length > 0 ? (churned / activeUsers.length) * 100 : 0;

    const newCustomersThisMonth = activeUsers.filter((user) => {
      const signupDate = getSignupDate(user);
      return signupDate ? signupDate >= monthStart : false;
    }).length;

    const topCustomers = customerDetails
      .map((customer) => ({
        userId: customer.userId,
        email: customer.email,
        tier: customer.tier,
        balance: roundMoney(customer.balance),
        monthlyRevenue: roundMoney(customer.monthlyRevenue),
        ltv: roundMoney(customer.monthlyRevenue * 24),
      }))
      .sort((a, b) => b.monthlyRevenue - a.monthlyRevenue)
      .slice(0, 10);

    const monthlyTrend = [
      {
        month: currentMonth,
        mrr: roundMoney(mrrFromCustomers),
        customers: payingCustomersCount,
        churnRate: roundMoney(churnRate),
      },
    ];

    const metrics: RevenueMetrics = {
      timestamp: now.toISOString(),
      monthYear: currentMonth,
      mrr: roundMoney(mrrFromCustomers),
      arr: roundMoney(arr),
      ltv: roundMoney(ltv),
      churnRate: roundMoney(churnRate),
      cogs: roundMoney(cogs),
      netProfitMargin: roundMoney(netProfitMargin),
      totalCustomers: users.length,
      payingCustomers: payingCustomersCount,
      freeCustomers: tierBreakdown.free,
      newCustomersThisMonth,
      avgCustomerBalance: activeUsers.length > 0 ? roundMoney(totalBalance / activeUsers.length) : 0,
      tierBreakdown,
      revenueByTier: {
        free: roundMoney(revenueByTier.free),
        hybrid: roundMoney(revenueByTier.hybrid),
        whiteLable: roundMoney(revenueByTier.whiteLable),
        enterprise: roundMoney(revenueByTier.enterprise),
      },
      monthlyTrend,
      topCustomers,
      health: {
        dataQuality: 'healthy',
        lastUpdate: now.toISOString(),
        recordsProcessed: users.length,
      },
    };

    return NextResponse.json(metrics, {
      headers: {
        'Cache-Control': 'no-store',
        'x-data-source': 'mongodb',
      },
    });
  } catch (error) {
    console.error('Revenue API error:', error);

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

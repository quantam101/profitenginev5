import { NextResponse } from 'next/server';
import { ClientsDB } from '@/lib/clients-db';

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

// Tier pricing model (% of AUM)
const TIER_PRICING = {
  free: 0.0,      // Free tier
  hybrid: 0.005,  // 0.5% AUM
  whiteLable: 0.01,  // 1.0% AUM
  enterprise: 0.015, // 1.5% AUM
};

// Monthly hosting and API costs (fixed)
const MONTHLY_FIXED_COSTS = 500; // Vercel, Runtime, misc APIs

export async function GET() {
  try {
    const db = new ClientsDB();

    // Get all users
    const allUsers = db.listUsers(undefined, false, 10000);
    const activeUsers = db.listUsers(undefined, true, 10000);

    // Get tier breakdown
    const tierBreakdown = db.getTierBreakdown();

    // Calculate metrics
    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const monthStartStr = monthStart.toISOString().split('T')[0];

    // Calculate MRR from customer balances
    let mrrFromCustomers = 0;
    let totalBalance = 0;
    let payingCustomersCount = 0;
    const customerDetails: Array<{ userId: number; email: string; tier: string; balance: number }> = [];

    for (const user of activeUsers) {
      // Get latest balance from daily trades
      const history = db.getUserTradingHistory(user.id, 365);
      if (history.length > 0) {
        const latestBalance = history[0].balance;
        totalBalance += latestBalance;

        const tierPrice = TIER_PRICING[user.tradingTier as keyof typeof TIER_PRICING] || 0;
        const monthlyRevenue = latestBalance * tierPrice;

        if (monthlyRevenue > 0) {
          mrrFromCustomers += monthlyRevenue;
          payingCustomersCount += 1;
        }

        customerDetails.push({
          userId: user.id,
          email: user.email,
          tier: user.tradingTier,
          balance: latestBalance,
        });
      }
    }

    const mrr = mrrFromCustomers;
    const arr = mrr * 12;

    // Calculate LTV (simplified: assuming 24-month average customer lifetime)
    const avgMonthlyRevenue = payingCustomersCount > 0 ? mrrFromCustomers / payingCustomersCount : 0;
    const ltv = avgMonthlyRevenue * 24; // 24-month LTV

    // Calculate COGS (payment processing, hosting, APIs)
    const paymentProcessingCost = mrrFromCustomers * 0.03; // 3% payment fee
    const apiCosts = Math.max(100, totalBalance > 0 ? (totalBalance / 100000) * 50 : 0); // Scaled API costs
    const cogs = paymentProcessingCost + apiCosts + MONTHLY_FIXED_COSTS;

    // Net profit margin
    const netProfit = mrrFromCustomers - cogs;
    const netProfitMargin = mrrFromCustomers > 0 ? (netProfit / mrrFromCustomers) * 100 : 0;

    // Churn rate (simplified: users inactive in last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const thirtyDaysAgoStr = thirtyDaysAgo.toISOString().split('T')[0];

    const churned = allUsers.filter(u => {
      if (!u.lastActiveAt) return true;
      return new Date(u.lastActiveAt) < thirtyDaysAgo;
    }).length;

    const churnRate = activeUsers.length > 0 ? (churned / activeUsers.length) * 100 : 0;

    // Revenue by tier
    const revenueByTier = {
      free: 0,
      hybrid: 0,
      whiteLable: 0,
      enterprise: 0,
    };

    for (const details of customerDetails) {
      const tierPrice = TIER_PRICING[details.tier as keyof typeof TIER_PRICING] || 0;
      const revenue = details.balance * tierPrice;

      if (details.tier === 'free') revenueByTier.free += revenue;
      else if (details.tier === 'hybrid') revenueByTier.hybrid += revenue;
      else if (details.tier === 'white-label' || details.tier === 'whiteLable') revenueByTier.whiteLable += revenue;
      else if (details.tier === 'enterprise') revenueByTier.enterprise += revenue;
    }

    // Top customers
    const topCustomers = customerDetails
      .map(c => {
        const tierPrice = TIER_PRICING[c.tier as keyof typeof TIER_PRICING] || 0;
        const monthlyRevenue = c.balance * tierPrice;
        return {
          userId: c.userId,
          email: c.email,
          tier: c.tier,
          balance: Math.round(c.balance * 100) / 100,
          monthlyRevenue: Math.round(monthlyRevenue * 100) / 100,
          ltv: Math.round(monthlyRevenue * 24 * 100) / 100,
        };
      })
      .sort((a, b) => b.monthlyRevenue - a.monthlyRevenue)
      .slice(0, 10);

    // Calculate new customers this month
    const newCustomersThisMonth = activeUsers.filter(u => {
      const signupDate = new Date(u.signupDate);
      return signupDate >= monthStart;
    }).length;

    // Generate monthly trend (simplified: current month only)
    const monthlyTrend = [
      {
        month: currentMonth,
        mrr: Math.round(mrr * 100) / 100,
        customers: payingCustomersCount,
        churnRate: Math.round(churnRate * 100) / 100,
      },
    ];

    db.close();

    const metrics: RevenueMetrics = {
      timestamp: new Date().toISOString(),
      monthYear: currentMonth,

      // KPIs
      mrr: Math.round(mrr * 100) / 100,
      arr: Math.round(arr * 100) / 100,
      ltv: Math.round(ltv * 100) / 100,
      churnRate: Math.round(churnRate * 100) / 100,
      cogs: Math.round(cogs * 100) / 100,
      netProfitMargin: Math.round(netProfitMargin * 100) / 100,

      // Customer metrics
      totalCustomers: allUsers.length,
      payingCustomers: payingCustomersCount,
      freeCustomers: (tierBreakdown.free || 0),
      newCustomersThisMonth,
      avgCustomerBalance: activeUsers.length > 0 ? Math.round((totalBalance / activeUsers.length) * 100) / 100 : 0,

      // Tier breakdown
      tierBreakdown: {
        free: tierBreakdown.free || 0,
        hybrid: tierBreakdown.hybrid || 0,
        whiteLable: tierBreakdown['white-label'] || tierBreakdown.whiteLable || 0,
        enterprise: tierBreakdown.enterprise || 0,
      },

      // Revenue by tier
      revenueByTier: {
        free: Math.round(revenueByTier.free * 100) / 100,
        hybrid: Math.round(revenueByTier.hybrid * 100) / 100,
        whiteLable: Math.round(revenueByTier.whiteLable * 100) / 100,
        enterprise: Math.round(revenueByTier.enterprise * 100) / 100,
      },

      // Monthly trend
      monthlyTrend,

      // Top customers
      topCustomers,

      // Health checks
      health: {
        dataQuality: 'healthy',
        lastUpdate: new Date().toISOString(),
        recordsProcessed: allUsers.length,
      },
    };

    return NextResponse.json(metrics, {
      headers: {
        'Cache-Control': 'no-store',
        'x-data-source': 'clients-db',
      },
    });
  } catch (error) {
    console.error('Revenue API error:', error);
    return NextResponse.json(
      {
        error: 'failed_to_calculate_revenue',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

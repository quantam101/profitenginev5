/**
 * Client tracking database helper module for ProfitEngine v5 (TypeScript)
 *
 * Provides high-level functions for:
 * - Managing user accounts and trading tiers
 * - Recording and querying daily trading metrics
 * - Tracking upsell opportunities and revenue progression
 *
 * Usage:
 *   import { ClientsDB } from '@/lib/clients-db';
 *
 *   const db = new ClientsDB();
 *
 *   // Create user
 *   const user = await db.createUser('alice@example.com', 'pro');
 *
 *   // Record daily trades
 *   await db.recordDailyTrades({
 *     userId: 1,
 *     date: '2026-06-18',
 *     numTrades: 10,
 *     // ...
 *   });
 */

'use server';

import { execSync } from 'child_process';
import { existsSync } from 'fs';
import path from 'path';

// Lazy load better-sqlite3 to avoid build errors when module is not installed
let Database: any;
try {
  Database = require('better-sqlite3');
} catch (e) {
  Database = null;
}

export interface User {
  id: number;
  email: string;
  signupDate: string;
  firstTradeDate: string | null;
  tradingTier: string;
  createdAt: string;
  updatedAt: string;
  lastActiveAt: string | null;
  isActive: number;
}

export interface DailyTrade {
  id: number;
  userId: number;
  date: string;
  numTrades: number;
  winCount: number;
  lossCount: number;
  pnlDollars: number;
  pnlPercent: number;
  balance: number;
  winRate: number;
  createdAt: string;
  updatedAt: string;
}

export interface UpsellTracking {
  id: number;
  userId: number;
  tierHistory: Array<{ tier: string; date: string; source: string }>;
  currentTier: string;
  revenueTier: string;
  lastUpsellOffered: string | null;
  upsellCount: number;
  conversionCount: number;
  lifetimeRevenue: number;
  createdAt: string;
  updatedAt: string;
}

export interface DailyTradesInput {
  userId: number;
  date: string;
  numTrades: number;
  winCount: number;
  lossCount: number;
  pnlDollars: number;
  pnlPercent: number;
  balance: number;
}

export class ClientsDB {
  private db: any;
  private dbPath: string;

  constructor(dbPath?: string) {
    if (!Database) {
      throw new Error('better-sqlite3 module not installed. Run: npm install better-sqlite3');
    }

    if (!dbPath) {
      // Default to project root/clients.db
      const projectRoot = path.resolve(__dirname, '..');
      dbPath = path.join(projectRoot, 'clients.db');
    }

    this.dbPath = dbPath;

    if (!existsSync(dbPath)) {
      throw new Error(
        `Database not found at ${dbPath}. Run: python scripts/init-clients-db.py`
      );
    }

    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
  }

  /**
   * Initialize the database (create tables and indexes)
   * This is usually called by the Python init script
   */
  static initializeDatabase(dbPath?: string): void {
    if (!dbPath) {
      const projectRoot = path.resolve(__dirname, '..');
      dbPath = path.join(projectRoot, 'clients.db');
    }

    // Call Python initialization script
    try {
      execSync(`python "${path.join(path.dirname(__filename), 'scripts', 'init-clients-db.py')}"`, {
        stdio: 'inherit',
      });
    } catch (error) {
      throw new Error(`Failed to initialize database: ${error}`);
    }
  }

  // ===== USER OPERATIONS =====

  createUser(
    email: string,
    tradingTier: string = 'free',
    signupDate?: string
  ): User {
    if (!signupDate) {
      signupDate = new Date().toISOString().split('T')[0];
    }

    const stmt = this.db.prepare(`
      INSERT INTO users (email, signup_date, trading_tier)
      VALUES (?, ?, ?)
    `);

    const result = stmt.run(email, signupDate, tradingTier);
    return this.getUser(result.lastInsertRowid as number)!;
  }

  getUser(userId: number): User | null {
    const stmt = this.db.prepare('SELECT * FROM users WHERE id = ?');
    const row = stmt.get(userId) as any;
    return row ? this.mapUser(row) : null;
  }

  getUserByEmail(email: string): User | null {
    const stmt = this.db.prepare('SELECT * FROM users WHERE email = ?');
    const row = stmt.get(email) as any;
    return row ? this.mapUser(row) : null;
  }

  updateUserTier(userId: number, newTier: string): User {
    const stmt = this.db.prepare(`
      UPDATE users
      SET trading_tier = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    stmt.run(newTier, userId);
    return this.getUser(userId)!;
  }

  updateUserActivity(userId: number): User {
    const stmt = this.db.prepare(`
      UPDATE users
      SET last_active_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    stmt.run(userId);
    return this.getUser(userId)!;
  }

  deactivateUser(userId: number): User {
    const stmt = this.db.prepare(`
      UPDATE users
      SET is_active = 0, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    stmt.run(userId);
    return this.getUser(userId)!;
  }

  listUsers(
    tier?: string,
    activeOnly: boolean = true,
    limit: number = 100
  ): User[] {
    let query = 'SELECT * FROM users WHERE 1=1';
    const params: any[] = [];

    if (activeOnly) {
      query += ' AND is_active = 1';
    }

    if (tier) {
      query += ' AND trading_tier = ?';
      params.push(tier);
    }

    query += ' ORDER BY signup_date DESC LIMIT ?';
    params.push(limit);

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];
    return rows.map((row) => this.mapUser(row));
  }

  // ===== DAILY TRADES OPERATIONS =====

  recordDailyTrades(trades: DailyTradesInput): DailyTrade {
    // Calculate win_rate
    const winRate =
      trades.winCount + trades.lossCount > 0
        ? (trades.winCount / (trades.winCount + trades.lossCount)) * 100
        : 0.0;

    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO daily_trades
      (user_id, date, num_trades, win_count, loss_count, pnl_dollars, pnl_percent, balance, win_rate)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      trades.userId,
      trades.date,
      trades.numTrades,
      trades.winCount,
      trades.lossCount,
      trades.pnlDollars,
      trades.pnlPercent,
      trades.balance,
      winRate
    );

    // Update user's first_trade_date if not set
    const user = this.getUser(trades.userId);
    if (user && !user.firstTradeDate) {
      const updateStmt = this.db.prepare(
        'UPDATE users SET first_trade_date = ? WHERE id = ?'
      );
      updateStmt.run(trades.date, trades.userId);
    }

    return this.getDailyTrades(trades.userId, trades.date)!;
  }

  getDailyTrades(userId: number, date: string): DailyTrade | null {
    const stmt = this.db.prepare(
      'SELECT * FROM daily_trades WHERE user_id = ? AND date = ?'
    );
    const row = stmt.get(userId, date) as any;
    return row ? this.mapDailyTrade(row) : null;
  }

  getUserTradingHistory(
    userId: number,
    days: number = 30,
    startDate?: string
  ): DailyTrade[] {
    if (!startDate) {
      const date = new Date();
      date.setDate(date.getDate() - days);
      startDate = date.toISOString().split('T')[0];
    }

    const stmt = this.db.prepare(`
      SELECT * FROM daily_trades
      WHERE user_id = ? AND date >= ?
      ORDER BY date DESC
    `);

    const rows = stmt.all(userId, startDate) as any[];
    return rows.map((row) => this.mapDailyTrade(row));
  }

  // ===== ANALYTICS OPERATIONS =====

  getUserStats(userId: number, days: number = 30): Record<string, any> {
    const history = this.getUserTradingHistory(userId, days);

    if (history.length === 0) {
      return {
        userId,
        daysAnalyzed: days,
        hasTrades: false,
        totalTrades: 0,
        totalWins: 0,
        totalLosses: 0,
        avgWinRate: 0.0,
        totalPnlDollars: 0.0,
        totalPnlPercent: 0.0,
        avgDailyPnl: 0.0,
        bestDay: null,
        worstDay: null,
        currentBalance: 0.0,
      };
    }

    const totalTrades = history.reduce((sum, t) => sum + t.numTrades, 0);
    const totalWins = history.reduce((sum, t) => sum + t.winCount, 0);
    const totalLosses = history.reduce((sum, t) => sum + t.lossCount, 0);
    const totalPnl = history.reduce((sum, t) => sum + t.pnlDollars, 0);
    const avgPnlPercent =
      history.reduce((sum, t) => sum + t.pnlPercent, 0) / history.length;

    const avgWinRate =
      totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0.0;
    const avgDailyPnl = totalPnl / history.length;

    const bestDay = history.reduce((best, current) =>
      current.pnlDollars > best.pnlDollars ? current : best
    );

    const worstDay = history.reduce((worst, current) =>
      current.pnlDollars < worst.pnlDollars ? current : worst
    );

    return {
      userId,
      daysAnalyzed: days,
      hasTrades: history.length > 0,
      totalTrades,
      totalWins,
      totalLosses,
      avgWinRate: Math.round(avgWinRate * 100) / 100,
      totalPnlDollars: Math.round(totalPnl * 100) / 100,
      totalPnlPercent: Math.round(avgPnlPercent * 100) / 100,
      avgDailyPnl: Math.round(avgDailyPnl * 100) / 100,
      bestDay: {
        date: bestDay.date,
        pnl: bestDay.pnlDollars,
      },
      worstDay: {
        date: worstDay.date,
        pnl: worstDay.pnlDollars,
      },
      currentBalance: history[0].balance,
    };
  }

  getTierBreakdown(): Record<string, number> {
    const stmt = this.db.prepare(`
      SELECT trading_tier, COUNT(*) as count
      FROM users
      WHERE is_active = 1
      GROUP BY trading_tier
      ORDER BY count DESC
    `);

    const rows = stmt.all() as any[];
    const result: Record<string, number> = {};

    for (const row of rows) {
      result[row.trading_tier] = row.count;
    }

    return result;
  }

  getTopPerformers(days: number = 30, limit: number = 10): Array<Record<string, any>> {
    const stmt = this.db.prepare(`
      SELECT u.id, u.email, u.trading_tier,
             SUM(d.pnl_dollars) as total_pnl,
             AVG(d.win_rate) as avg_win_rate,
             COUNT(d.id) as trade_days
      FROM users u
      LEFT JOIN daily_trades d ON u.id = d.user_id
      WHERE u.is_active = 1 AND d.date >= date('now', '-' || ? || ' days')
      GROUP BY u.id
      ORDER BY total_pnl DESC
      LIMIT ?
    `);

    const rows = stmt.all(days, limit) as any[];
    return rows.map((row) => ({
      userId: row.id,
      email: row.email,
      tier: row.trading_tier,
      totalPnl: row.total_pnl || 0.0,
      avgWinRate: row.avg_win_rate || 0.0,
      tradeDays: row.trade_days || 0,
    }));
  }

  // ===== UPSELL OPERATIONS =====

  getUpsellTracking(userId: number): UpsellTracking | null {
    const stmt = this.db.prepare(
      'SELECT * FROM upsell_tracking WHERE user_id = ?'
    );
    const row = stmt.get(userId) as any;
    return row ? this.mapUpsellTracking(row) : null;
  }

  recordUpsellOffer(userId: number, tier: string, conversion: boolean = false): UpsellTracking {
    let tracking = this.getUpsellTracking(userId);

    if (!tracking) {
      const stmt = this.db.prepare(`
        INSERT INTO upsell_tracking (user_id, tier_history)
        VALUES (?, ?)
      `);
      stmt.run(userId, JSON.stringify([]));
      tracking = this.getUpsellTracking(userId)!;
    }

    // Update tier_history
    const tierHistory = tracking.tierHistory || [];
    tierHistory.push({
      tier,
      date: new Date().toISOString(),
      source: 'upsell_offer',
    });

    // Update conversion count if applicable
    let conversionCount = tracking.conversionCount;
    if (conversion) {
      conversionCount += 1;
    }

    const stmt = this.db.prepare(`
      UPDATE upsell_tracking
      SET tier_history = ?,
          last_upsell_offered = CURRENT_TIMESTAMP,
          upsell_count = upsell_count + 1,
          conversion_count = ?,
          updated_at = CURRENT_TIMESTAMP
      WHERE user_id = ?
    `);

    stmt.run(JSON.stringify(tierHistory), conversionCount, userId);
    return this.getUpsellTracking(userId)!;
  }

  updateRevenueTier(userId: number, revenueTier: string, amount: number): UpsellTracking {
    const stmt = this.db.prepare(`
      UPDATE upsell_tracking
      SET revenue_tier = ?,
          lifetime_revenue = lifetime_revenue + ?,
          updated_at = CURRENT_TIMESTAMP
      WHERE user_id = ?
    `);

    stmt.run(revenueTier, amount, userId);
    return this.getUpsellTracking(userId)!;
  }

  getRevenueSummary(): Record<string, { userCount: number; totalRevenue: number }> {
    const stmt = this.db.prepare(`
      SELECT revenue_tier, COUNT(*) as user_count, SUM(lifetime_revenue) as total_revenue
      FROM upsell_tracking
      GROUP BY revenue_tier
      ORDER BY total_revenue DESC
    `);

    const rows = stmt.all() as any[];
    const result: Record<string, any> = {};

    for (const row of rows) {
      result[row.revenue_tier] = {
        userCount: row.user_count,
        totalRevenue: row.total_revenue || 0.0,
      };
    }

    return result;
  }

  getUpsellCandidates(limit: number = 50): Array<Record<string, any>> {
    const stmt = this.db.prepare(`
      SELECT u.id, u.email, u.trading_tier,
             AVG(d.win_rate) as avg_win_rate,
             SUM(d.pnl_dollars) as total_pnl,
             COUNT(DISTINCT d.date) as trade_days
      FROM users u
      LEFT JOIN upsell_tracking ut ON u.id = ut.user_id
      LEFT JOIN daily_trades d ON u.id = d.user_id AND d.date >= date('now', '-30 days')
      WHERE u.is_active = 1 AND (ut.revenue_tier = 'none' OR ut.revenue_tier = 'trial')
      GROUP BY u.id
      ORDER BY total_pnl DESC
      LIMIT ?
    `);

    const rows = stmt.all(limit) as any[];
    return rows.map((row) => ({
      userId: row.id,
      email: row.email,
      tier: row.trading_tier,
      avgWinRate: row.avg_win_rate || 0.0,
      totalPnl30d: row.total_pnl || 0.0,
      tradeDays30d: row.trade_days || 0,
    }));
  }

  close(): void {
    this.db.close();
  }

  // ===== PRIVATE HELPERS =====

  private mapUser(row: any): User {
    return {
      id: row.id,
      email: row.email,
      signupDate: row.signup_date,
      firstTradeDate: row.first_trade_date,
      tradingTier: row.trading_tier,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
      lastActiveAt: row.last_active_at,
      isActive: row.is_active,
    };
  }

  private mapDailyTrade(row: any): DailyTrade {
    return {
      id: row.id,
      userId: row.user_id,
      date: row.date,
      numTrades: row.num_trades,
      winCount: row.win_count,
      lossCount: row.loss_count,
      pnlDollars: row.pnl_dollars,
      pnlPercent: row.pnl_percent,
      balance: row.balance,
      winRate: row.win_rate,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  private mapUpsellTracking(row: any): UpsellTracking {
    return {
      id: row.id,
      userId: row.user_id,
      tierHistory: JSON.parse(row.tier_history),
      currentTier: row.current_tier,
      revenueTier: row.revenue_tier,
      lastUpsellOffered: row.last_upsell_offered,
      upsellCount: row.upsell_count,
      conversionCount: row.conversion_count,
      lifetimeRevenue: row.lifetime_revenue,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }
}

// Export for default usage
export default ClientsDB;

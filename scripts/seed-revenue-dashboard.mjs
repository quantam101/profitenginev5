#!/usr/bin/env node

/**
 * Revenue Dashboard Test Data Seeder
 *
 * Generates realistic test data in clients.db for dashboard verification.
 * Creates customers across all tiers with trading history.
 *
 * Usage:
 *   node scripts/seed-revenue-dashboard.mjs [count]
 *
 * Examples:
 *   node scripts/seed-revenue-dashboard.mjs          # Creates 50 customers (default)
 *   node scripts/seed-revenue-dashboard.mjs 100      # Creates 100 customers
 *   node scripts/seed-revenue-dashboard.mjs 500      # Creates 500 customers
 */

import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, '..', 'clients.db');
const customerCount = parseInt(process.argv[2] || '50', 10);

const log = {
  info: (msg) => console.log(`[INFO] ${msg}`),
  success: (msg) => console.log(`[✓] ${msg}`),
  error: (msg) => console.log(`[✗] ${msg}`),
};

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomEmail() {
  const domains = ['example.com', 'test.com', 'sample.com', 'demo.com'];
  const name = Math.random().toString(36).substring(2, 10);
  return `${name}@${domains[randomInt(0, domains.length - 1)]}`;
}

function randomTier() {
  const rand = Math.random();
  if (rand < 0.6) return 'free';
  if (rand < 0.85) return 'hybrid';
  if (rand < 0.98) return 'white-label';
  return 'enterprise';
}

function randomBalance(tier) {
  switch (tier) {
    case 'free':
      return 0;
    case 'hybrid':
      return randomInt(5000, 100000);
    case 'white-label':
      return randomInt(50000, 500000);
    case 'enterprise':
      return randomInt(500000, 2000000);
    default:
      return 0;
  }
}

function daysAgo(days) {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().split('T')[0];
}

function main() {
  try {
    log.info(`Revenue Dashboard Test Data Seeder`);
    log.info(`Creating ${customerCount} test customers...`);

    // Open database
    let db;
    try {
      db = new Database(dbPath);
      db.pragma('journal_mode = WAL');
    } catch (error) {
      log.error(`Cannot open database at ${dbPath}`);
      log.error(`Make sure clients.db exists. Run: npm run db:init`);
      process.exit(1);
    }

    // Clear existing data (optional, uncomment to reset)
    // db.exec('DELETE FROM daily_trades');
    // db.exec('DELETE FROM upsell_tracking');
    // db.exec('DELETE FROM users');

    // Create users
    const insertUser = db.prepare(`
      INSERT OR REPLACE INTO users
      (email, signup_date, trading_tier, is_active, last_active_at)
      VALUES (?, ?, ?, 1, ?)
    `);

    const insertTrade = db.prepare(`
      INSERT OR REPLACE INTO daily_trades
      (user_id, date, num_trades, win_count, loss_count, pnl_dollars, pnl_percent, balance, win_rate)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const users = [];
    let freeCount = 0;
    let hybridCount = 0;
    let whiteLabelCount = 0;
    let enterpriseCount = 0;

    log.info('Creating users...');

    for (let i = 0; i < customerCount; i++) {
      const email = randomEmail();
      const tier = randomTier();
      const signupDaysAgo = randomInt(1, 365);
      const signupDate = daysAgo(signupDaysAgo);
      const lastActiveDaysAgo = randomInt(0, 30); // Active within last month
      const lastActiveAt = daysAgo(lastActiveDaysAgo).concat(' ');

      const result = insertUser.run(email, signupDate, tier, lastActiveAt);
      const userId = result.lastInsertRowid;

      users.push({ id: userId, email, tier, signupDate });

      // Count by tier
      if (tier === 'free') freeCount++;
      else if (tier === 'hybrid') hybridCount++;
      else if (tier === 'white-label') whiteLabelCount++;
      else if (tier === 'enterprise') enterpriseCount++;

      if ((i + 1) % 10 === 0) {
        log.info(`  Created ${i + 1}/${customerCount} users`);
      }
    }

    log.success(`Created ${customerCount} users`);
    log.info(`  Free: ${freeCount}`);
    log.info(`  Hybrid: ${hybridCount}`);
    log.info(`  White Label: ${whiteLabelCount}`);
    log.info(`  Enterprise: ${enterpriseCount}`);

    // Create trading history
    log.info('Creating trading history...');

    let tradeCount = 0;
    for (const user of users) {
      const balance = randomBalance(user.tier);
      const daysOfTrades = randomInt(1, Math.min(60, 365)); // Trading history

      for (let daysBack = daysOfTrades; daysBack >= 1; daysBack--) {
        const date = daysAgo(daysBack);
        const numTrades = randomInt(1, 20);
        const winCount = randomInt(0, numTrades);
        const lossCount = numTrades - winCount;
        const winRate = numTrades > 0 ? (winCount / numTrades) * 100 : 0;

        // Random daily P&L
        const maxPnlPercent = 5; // Max 5% daily move
        const pnlPercent = (Math.random() - 0.5) * maxPnlPercent;
        const pnlDollars = balance * (pnlPercent / 100);

        // Vary balance slightly over time
        const balanceVariation = balance * (Math.random() - 0.4) * 0.05; // +/- 2.5%
        const currentBalance = Math.max(0, balance + balanceVariation);

        insertTrade.run(
          user.id,
          date,
          numTrades,
          winCount,
          lossCount,
          pnlDollars,
          pnlPercent,
          currentBalance,
          winRate
        );

        tradeCount++;
      }

      if (tradeCount % 100 === 0) {
        log.info(`  Created ${tradeCount} trading records`);
      }
    }

    log.success(`Created ${tradeCount} trading records`);

    // Calculate and display summary
    const tierSummary = db.prepare(`
      SELECT trading_tier, COUNT(*) as count
      FROM users
      WHERE is_active = 1
      GROUP BY trading_tier
    `).all();

    const revenueSummary = db.prepare(`
      SELECT u.trading_tier,
             COUNT(DISTINCT u.id) as customer_count,
             AVG(d.balance) as avg_balance
      FROM users u
      LEFT JOIN daily_trades d ON u.id = d.user_id
      WHERE u.is_active = 1
      GROUP BY u.trading_tier
    `).all();

    log.info('---');
    log.info('Test Data Summary:');
    log.info('');

    const tierPricing = {
      'free': 0.0,
      'hybrid': 0.005,
      'white-label': 0.01,
      'enterprise': 0.015,
    };

    let totalMrr = 0;
    for (const row of revenueSummary) {
      const avgBalance = row.avg_balance || 0;
      const tierPrice = tierPricing[row.trading_tier] || 0;
      const monthlyRevenue = avgBalance * tierPrice;
      totalMrr += monthlyRevenue;

      log.info(`${row.trading_tier.padEnd(12)} | ${String(row.customer_count).padStart(3)} customers | Avg Balance: $${Math.round(avgBalance).toLocaleString().padStart(10)} | Revenue: $${monthlyRevenue.toFixed(2)}`);
    }

    log.info('');
    log.info(`Total MRR: $${totalMrr.toFixed(2)}`);
    log.info(`Total ARR: $${(totalMrr * 12).toFixed(2)}`);

    db.close();

    log.success('Test data seeded successfully!');
    log.info(`Access dashboard at: /command-center/revenue`);
    log.info(`Or verify with: node scripts/verify-revenue-dashboard.mjs`);

  } catch (error) {
    log.error(`Seeding failed: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

main();

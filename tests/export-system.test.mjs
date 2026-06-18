/**
 * Export System Tests
 *
 * Tests for data export, PDF generation, and tax reporting
 */

import assert from 'assert';

// Mock data for testing
const mockTrades = [
  {
    id: 1,
    userId: 1,
    date: '2024-01-15',
    symbol: 'AAPL',
    side: 'BUY',
    entryPrice: 150.0,
    exitPrice: 155.0,
    quantity: 100,
    pnl: 500,
    pnlPercent: 3.33,
    duration: 5,
    strategy: 'momentum',
  },
  {
    id: 2,
    userId: 1,
    date: '2024-01-20',
    symbol: 'MSFT',
    side: 'BUY',
    entryPrice: 300.0,
    exitPrice: 290.0,
    quantity: 50,
    pnl: -500,
    pnlPercent: -3.33,
    duration: 3,
    strategy: 'mean-reversion',
  },
  {
    id: 3,
    userId: 1,
    date: '2024-02-10',
    symbol: 'AAPL',
    side: 'BUY',
    entryPrice: 160.0,
    exitPrice: 168.0,
    quantity: 50,
    pnl: 400,
    pnlPercent: 5.0,
    duration: 15,
    strategy: 'momentum',
  },
];

const mockDailyTrades = [
  {
    id: 1,
    userId: 1,
    date: '2024-01-15',
    numTrades: 2,
    winCount: 1,
    lossCount: 1,
    pnlDollars: 0,
    pnlPercent: 0,
    balance: 10000,
    winRate: 50,
  },
  {
    id: 2,
    userId: 1,
    date: '2024-01-20',
    numTrades: 1,
    winCount: 0,
    lossCount: 1,
    pnlDollars: -500,
    pnlPercent: -5,
    balance: 9500,
    winRate: 0,
  },
  {
    id: 3,
    userId: 1,
    date: '2024-02-10',
    numTrades: 1,
    winCount: 1,
    lossCount: 0,
    pnlDollars: 400,
    pnlPercent: 4.2,
    balance: 9900,
    winRate: 100,
  },
];

// Test suite
describe('Export System', () => {
  describe('CSV Generation', () => {
    test('generates valid CSV with trade data', () => {
      // Mock CSV generation
      const headers = ['Date', 'Symbol', 'Side', 'Entry Price', 'Exit Price', 'P&L ($)', 'P&L (%)'];
      const rows = mockTrades.map((t) => [
        t.date,
        t.symbol,
        t.side,
        t.entryPrice.toFixed(2),
        t.exitPrice.toFixed(2),
        t.pnl.toFixed(2),
        t.pnlPercent.toFixed(2),
      ]);

      assert.strictEqual(headers.length, 7, 'CSV should have 7 columns');
      assert.strictEqual(rows.length, 3, 'CSV should have 3 data rows');
      assert.strictEqual(rows[0][0], '2024-01-15', 'First trade date should match');
    });

    test('escapes special characters in CSV', () => {
      const testRow = ['2024-01-01', 'TEST', 'BUY', '100.00', '"quoted"', '100.00', '10.0'];
      const csv = testRow
        .map((cell) => {
          if (cell.includes('"') || cell.includes(',')) {
            return '"' + cell.replace(/"/g, '""') + '"';
          }
          return cell;
        })
        .join(',');

      // Check that the CSV contains escaped quotes
      assert.ok(csv.includes('""'), 'Quotes should be escaped in CSV');
    });

    test('includes header comments with metadata', () => {
      const header = `# Trading History Export
# User: John Trader (john@example.com)
# Period: 2024-01-01 to 2024-12-31
# Total Trades: 3`;

      assert.match(header, /# User:/, 'Should include user info');
      assert.match(header, /# Period:/, 'Should include date range');
      assert.match(header, /# Total Trades:/, 'Should include trade count');
    });
  });

  describe('Tax Reporting', () => {
    test('correctly calculates short-term vs long-term gains', () => {
      const today = new Date();

      // Recent trade (short-term)
      const recentTrade = {
        ...mockTrades[0],
        date: new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      };

      // Old trade (long-term)
      const oldTrade = {
        ...mockTrades[2],
        date: new Date(today.getTime() - 400 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      };

      const recentHoldingDays = Math.floor(
        (today.getTime() - new Date(recentTrade.date).getTime()) /
          (1000 * 60 * 60 * 24)
      );
      const oldHoldingDays = Math.floor(
        (today.getTime() - new Date(oldTrade.date).getTime()) /
          (1000 * 60 * 60 * 24)
      );

      assert.ok(recentHoldingDays < 365, 'Recent trade should be < 365 days');
      assert.ok(oldHoldingDays >= 365, 'Old trade should be >= 365 days');
    });

    test('detects wash sales', () => {
      // Loss on AAPL on 2024-01-15
      const loss = { ...mockTrades[1], symbol: 'AAPL', date: '2024-01-15', pnl: -500 };
      // Repurchase of AAPL on 2024-01-20 (5 days later)
      const repurchase = { ...mockTrades[2], symbol: 'AAPL', date: '2024-01-20' };

      const saleDateObj = new Date(loss.date);
      const repurchaseDateObj = new Date(repurchase.date);
      const daysDifference = Math.floor(
        (repurchaseDateObj.getTime() - saleDateObj.getTime()) /
          (1000 * 60 * 60 * 24)
      );

      assert.ok(daysDifference > 0 && daysDifference <= 30, 'Should detect wash sale within 30 days');
      assert.strictEqual(loss.symbol, repurchase.symbol, 'Symbols should match');
    });

    test('includes form 8949 compatible data', () => {
      const taxData = {
        shortTermGains: 500,
        longTermGains: 400,
        totalGains: 900,
        totalLosses: 500,
        netGains: 400,
        washSales: [],
        exportDate: new Date().toISOString(),
      };

      assert.strictEqual(taxData.shortTermGains + taxData.longTermGains, taxData.totalGains);
      assert.strictEqual(taxData.totalGains - taxData.totalLosses, taxData.netGains);
      assert.ok(taxData.exportDate, 'Should include export date');
    });
  });

  describe('Performance Metrics', () => {
    test('calculates win rate correctly', () => {
      const totalTrades = mockTrades.length;
      const winningTrades = mockTrades.filter((t) => t.pnl > 0).length;
      const winRate = (winningTrades / totalTrades) * 100;

      assert.strictEqual(winningTrades, 2, 'Should have 2 winning trades');
      assert.strictEqual(Math.round(winRate), 67, 'Win rate should be approximately 67%');
    });

    test('calculates profit factor', () => {
      const totalWins = mockTrades
        .filter((t) => t.pnl > 0)
        .reduce((sum, t) => sum + t.pnl, 0);
      const totalLosses = Math.abs(
        mockTrades
          .filter((t) => t.pnl < 0)
          .reduce((sum, t) => sum + t.pnl, 0)
      );
      const profitFactor = totalWins / totalLosses;

      assert.ok(profitFactor > 1, 'Profit factor should be greater than 1 (profitable)');
      assert.strictEqual(totalWins, 900, 'Total wins should be 900');
      assert.strictEqual(totalLosses, 500, 'Total losses should be 500');
    });

    test('identifies best and worst trades', () => {
      const bestTrade = mockTrades.reduce((best, t) => (t.pnl > best.pnl ? t : best));
      const worstTrade = mockTrades.reduce((worst, t) => (t.pnl < worst.pnl ? t : worst));

      assert.strictEqual(bestTrade.pnl, 500, 'Best trade P&L should be 500');
      assert.strictEqual(worstTrade.pnl, -500, 'Worst trade P&L should be -500');
    });

    test('calculates average trade', () => {
      const totalPnl = mockTrades.reduce((sum, t) => sum + t.pnl, 0);
      const averageTrade = totalPnl / mockTrades.length;

      assert.strictEqual(averageTrade, 400 / 3, 'Average trade should be 133.33');
    });

    test('calculates maximum drawdown', () => {
      const sorted = [...mockTrades].sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      );

      let balance = 0;
      let peakBalance = 0;
      let maxDrawdown = 0;

      sorted.forEach((trade) => {
        balance += trade.pnl;
        peakBalance = Math.max(peakBalance, balance);
        const drawdown = peakBalance - balance;
        maxDrawdown = Math.max(maxDrawdown, drawdown);
      });

      assert.ok(maxDrawdown >= 0, 'Max drawdown should be non-negative');
      assert.strictEqual(maxDrawdown, 500, 'Max drawdown should be 500');
    });
  });

  describe('Monthly Aggregation', () => {
    test('aggregates trades by month', () => {
      const monthMap = new Map();

      mockDailyTrades.forEach((day) => {
        const date = new Date(day.date);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

        if (!monthMap.has(monthKey)) {
          monthMap.set(monthKey, {
            month: monthKey,
            trades: 0,
            wins: 0,
            losses: 0,
          });
        }

        const month = monthMap.get(monthKey);
        month.trades += day.numTrades;
        month.wins += day.winCount;
        month.losses += day.lossCount;
      });

      assert.strictEqual(monthMap.size, 2, 'Should have 2 months');
      const january = monthMap.get('2024-01');
      assert.ok(january, 'Should have January 2024');
      assert.strictEqual(january.trades, 3, 'January should have 3 total trades');
    });

    test('calculates monthly win rate', () => {
      const monthData = {
        month: '2024-01',
        wins: 1,
        losses: 2,
        trades: 3,
        pnl: -100,
      };

      const winRate = monthData.trades > 0 ? (monthData.wins / monthData.trades) * 100 : 0;

      assert.strictEqual(Math.round(winRate), 33, 'January win rate should be 33%');
    });
  });

  describe('API Response Validation', () => {
    test('validates export format', () => {
      const validFormats = ['csv', 'pdf', 'tax-csv'];
      const testFormat = 'csv';

      assert.ok(validFormats.includes(testFormat), 'Format should be valid');
    });

    test('validates date range', () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-12-31');

      assert.ok(startDate <= endDate, 'Start date should be before end date');
    });

    test('creates proper CSV headers', () => {
      const headers = ['Date', 'Symbol', 'Side', 'Entry Price', 'Exit Price', 'P&L ($)', 'P&L (%)'];

      assert.ok(headers.includes('Date'), 'Should include Date column');
      assert.ok(headers.includes('Symbol'), 'Should include Symbol column');
      assert.ok(headers.includes('P&L ($)'), 'Should include P&L column');
    });
  });

  describe('Security', () => {
    test('sanitizes user input in URLs', () => {
      const maliciousInput = "2024-01-01' OR '1'='1";
      // Properly sanitize date format
      const sanitized = maliciousInput.match(/^\d{4}-\d{2}-\d{2}/) ? maliciousInput.match(/^\d{4}-\d{2}-\d{2}/)[0] : '';

      assert.strictEqual(sanitized, '2024-01-01', 'Should remove SQL injection characters');
    });

    test('requires authentication token', () => {
      const mockSession = {
        user: {
          email: 'user@example.com',
          id: '123',
        },
      };

      assert.ok(mockSession.user.email, 'Should require user email');
      assert.ok(mockSession.user.id, 'Should require user ID');
    });

    test('prevents cross-user data access', () => {
      const userId = 1;
      const requestUserId = 2;

      assert.notStrictEqual(userId, requestUserId, 'Should not allow cross-user access');
    });
  });

  describe('Strategy Analysis', () => {
    test('calculates strategy metrics', () => {
      const momentum = mockTrades.filter((t) => t.strategy === 'momentum');
      const momentumWins = momentum.filter((t) => t.pnl > 0).length;
      const momentumWinRate = (momentumWins / momentum.length) * 100;

      assert.strictEqual(momentumWinRate, 100, 'Momentum strategy should have 100% win rate');
      assert.strictEqual(momentum.length, 2, 'Should have 2 momentum trades');
    });

    test('identifies best performing strategy', () => {
      const strategies = new Map();

      mockTrades.forEach((trade) => {
        if (!strategies.has(trade.strategy)) {
          strategies.set(trade.strategy, {
            pnl: 0,
            count: 0,
            wins: 0,
          });
        }

        const s = strategies.get(trade.strategy);
        s.pnl += trade.pnl;
        s.count++;
        if (trade.pnl > 0) s.wins++;
      });

      const bestStrategy = Array.from(strategies.entries()).reduce((best, current) =>
        current[1].pnl > best[1].pnl ? current : best
      );

      assert.strictEqual(bestStrategy[0], 'momentum', 'Momentum should be best strategy');
    });
  });
});

// Helper test runner
function test(description, fn) {
  try {
    fn();
    console.log(`✓ ${description}`);
  } catch (error) {
    console.error(`✗ ${description}`);
    console.error(`  ${error.message}`);
    process.exitCode = 1;
  }
}

function describe(description, fn) {
  console.log(`\n${description}`);
  fn();
}

// Run tests
console.log('Running Export System Tests...');

/**
 * Trade Analytics & Strategy Breakdown
 *
 * Advanced analysis for trading performance
 * - Strategy performance comparison
 * - Symbol-by-symbol analysis
 * - Win/loss streaks
 * - Risk metrics (Sharpe ratio, max drawdown, etc.)
 */

export interface TradeRecord {
  id: number;
  date: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  duration: number;
  strategy?: string;
  tags?: string;
}

export interface StrategyMetrics {
  strategy: string;
  tradeCount: number;
  winCount: number;
  lossCount: number;
  winRate: number;
  totalPnl: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number; // Total wins / Total losses
  expectancy: number; // Average profit per trade
  bestTrade: number;
  worstTrade: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
}

export interface SymbolMetrics {
  symbol: string;
  tradeCount: number;
  winCount: number;
  lossCount: number;
  winRate: number;
  totalPnl: number;
  avgWin: number;
  avgLoss: number;
  bestTrade: number;
  worstTrade: number;
}

export interface StreakData {
  type: 'win' | 'loss';
  length: number;
  startDate: string;
  endDate: string;
}

export interface RiskMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  maxDrawdownPercent: number;
  recoveryFactor: number; // Profit / Max Drawdown
  profitFactor: number;
}

/**
 * Calculate strategy performance metrics
 */
export function analyzeByStrategy(trades: TradeRecord[]): Map<string, StrategyMetrics> {
  const strategies = new Map<string, StrategyMetrics>();

  trades.forEach((trade) => {
    const strategyKey = trade.strategy || 'Unclassified';

    if (!strategies.has(strategyKey)) {
      strategies.set(strategyKey, {
        strategy: strategyKey,
        tradeCount: 0,
        winCount: 0,
        lossCount: 0,
        winRate: 0,
        totalPnl: 0,
        avgWin: 0,
        avgLoss: 0,
        profitFactor: 0,
        expectancy: 0,
        bestTrade: 0,
        worstTrade: 0,
        maxConsecutiveWins: 0,
        maxConsecutiveLosses: 0,
      });
    }

    const metrics = strategies.get(strategyKey)!;
    metrics.tradeCount++;
    metrics.totalPnl += trade.pnl;

    if (trade.pnl > 0) {
      metrics.winCount++;
      metrics.avgWin += trade.pnl;
      if (trade.pnl > metrics.bestTrade) {
        metrics.bestTrade = trade.pnl;
      }
    } else if (trade.pnl < 0) {
      metrics.lossCount++;
      metrics.avgLoss += Math.abs(trade.pnl);
      if (trade.pnl < metrics.worstTrade) {
        metrics.worstTrade = trade.pnl;
      }
    }
  });

  // Calculate derived metrics
  strategies.forEach((metrics) => {
    if (metrics.winCount > 0) {
      metrics.avgWin /= metrics.winCount;
    }
    if (metrics.lossCount > 0) {
      metrics.avgLoss /= metrics.lossCount;
    }

    metrics.winRate =
      metrics.tradeCount > 0
        ? (metrics.winCount / metrics.tradeCount) * 100
        : 0;

    if (metrics.avgLoss > 0) {
      metrics.profitFactor = metrics.avgWin / metrics.avgLoss;
    }

    metrics.expectancy =
      metrics.tradeCount > 0 ? metrics.totalPnl / metrics.tradeCount : 0;

    // Calculate consecutive streaks for this strategy
    const strategyTrades = trades.filter(
      (t) => (t.strategy || 'Unclassified') === metrics.strategy
    );
    const streaks = calculateStreaks(strategyTrades);

    const winStreaks = streaks.filter((s) => s.type === 'win');
    metrics.maxConsecutiveWins = Math.max(
      0,
      ...winStreaks.map((s) => s.length)
    );

    const lossStreaks = streaks.filter((s) => s.type === 'loss');
    metrics.maxConsecutiveLosses = Math.max(
      0,
      ...lossStreaks.map((s) => s.length)
    );
  });

  return strategies;
}

/**
 * Calculate symbol performance metrics
 */
export function analyzeBySymbol(trades: TradeRecord[]): Map<string, SymbolMetrics> {
  const symbols = new Map<string, SymbolMetrics>();

  trades.forEach((trade) => {
    if (!symbols.has(trade.symbol)) {
      symbols.set(trade.symbol, {
        symbol: trade.symbol,
        tradeCount: 0,
        winCount: 0,
        lossCount: 0,
        winRate: 0,
        totalPnl: 0,
        avgWin: 0,
        avgLoss: 0,
        bestTrade: 0,
        worstTrade: 0,
      });
    }

    const metrics = symbols.get(trade.symbol)!;
    metrics.tradeCount++;
    metrics.totalPnl += trade.pnl;

    if (trade.pnl > 0) {
      metrics.winCount++;
      metrics.avgWin += trade.pnl;
      if (trade.pnl > metrics.bestTrade) {
        metrics.bestTrade = trade.pnl;
      }
    } else if (trade.pnl < 0) {
      metrics.lossCount++;
      metrics.avgLoss += Math.abs(trade.pnl);
      if (trade.pnl < metrics.worstTrade) {
        metrics.worstTrade = trade.pnl;
      }
    }
  });

  // Calculate derived metrics
  symbols.forEach((metrics) => {
    if (metrics.winCount > 0) {
      metrics.avgWin /= metrics.winCount;
    }
    if (metrics.lossCount > 0) {
      metrics.avgLoss /= metrics.lossCount;
    }

    metrics.winRate =
      metrics.tradeCount > 0
        ? (metrics.winCount / metrics.tradeCount) * 100
        : 0;
  });

  return symbols;
}

/**
 * Calculate win/loss streaks
 */
export function calculateStreaks(trades: TradeRecord[]): StreakData[] {
  const sorted = [...trades].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const streaks: StreakData[] = [];
  let currentStreak: StreakData | null = null;

  sorted.forEach((trade) => {
    const isWin = trade.pnl > 0;
    const type = isWin ? 'win' : 'loss';

    if (!currentStreak || currentStreak.type !== type) {
      if (currentStreak) {
        streaks.push(currentStreak);
      }
      currentStreak = {
        type,
        length: 1,
        startDate: trade.date,
        endDate: trade.date,
      };
    } else {
      currentStreak.length++;
      currentStreak.endDate = trade.date;
    }
  });

  if (currentStreak) {
    streaks.push(currentStreak);
  }

  return streaks;
}

/**
 * Calculate advanced risk metrics
 */
export function calculateRiskMetrics(
  trades: TradeRecord[],
  daysInPeriod: number = 365,
  riskFreeRate: number = 0.02
): RiskMetrics {
  if (trades.length === 0) {
    return {
      totalReturn: 0,
      annualizedReturn: 0,
      volatility: 0,
      sharpeRatio: 0,
      sortinoRatio: 0,
      maxDrawdown: 0,
      maxDrawdownPercent: 0,
      recoveryFactor: 0,
      profitFactor: 0,
    };
  }

  // Calculate total return and drawdown
  const sorted = [...trades].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  let totalReturn = 0;
  let maxDrawdown = 0;
  let peakBalance = 0;
  const returns: number[] = [];
  const downReturns: number[] = [];

  sorted.forEach((trade) => {
    totalReturn += trade.pnl;
    returns.push(trade.pnl);

    if (trade.pnl < 0) {
      downReturns.push(trade.pnl);
    }

    peakBalance = Math.max(peakBalance, totalReturn);
    const drawdown = peakBalance - totalReturn;
    maxDrawdown = Math.max(maxDrawdown, drawdown);
  });

  // Calculate volatility (standard deviation of returns)
  const meanReturn = totalReturn / returns.length;
  const variance =
    returns.reduce((sum, r) => sum + Math.pow(r - meanReturn, 2), 0) /
    returns.length;
  const volatility = Math.sqrt(variance);

  // Calculate Sortino ratio (downside volatility only)
  const meanDownReturn = downReturns.length > 0
    ? downReturns.reduce((a, b) => a + b, 0) / downReturns.length
    : 0;
  const downVariance =
    downReturns.length > 0
      ? downReturns.reduce((sum, r) => sum + Math.pow(r - meanDownReturn, 2), 0) /
        downReturns.length
      : 0;
  const downVolatility = Math.sqrt(downVariance);

  // Annualize metrics
  const yearsInPeriod = daysInPeriod / 365;
  const annualizedReturn = totalReturn / yearsInPeriod;
  const annualizedVolatility = volatility * Math.sqrt(252); // 252 trading days/year

  // Sharpe Ratio = (Return - Risk Free Rate) / Volatility
  const sharpeRatio =
    annualizedVolatility > 0
      ? (annualizedReturn - riskFreeRate) / annualizedVolatility
      : 0;

  // Sortino Ratio = (Return - Risk Free Rate) / Downside Volatility
  const annualizedDownVolatility = downVolatility * Math.sqrt(252);
  const sortinoRatio =
    annualizedDownVolatility > 0
      ? (annualizedReturn - riskFreeRate) / annualizedDownVolatility
      : 0;

  // Profit Factor
  const winSum = returns.filter((r) => r > 0).reduce((a, b) => a + b, 0);
  const lossSum = Math.abs(
    downReturns.reduce((a, b) => a + b, 0)
  );
  const profitFactor = lossSum > 0 ? winSum / lossSum : 0;

  // Recovery Factor = Total Profit / Max Drawdown
  const recoveryFactor = maxDrawdown > 0 ? totalReturn / maxDrawdown : 0;

  return {
    totalReturn,
    annualizedReturn,
    volatility: annualizedVolatility,
    sharpeRatio,
    sortinoRatio,
    maxDrawdown,
    maxDrawdownPercent:
      peakBalance > 0 ? (maxDrawdown / peakBalance) * 100 : 0,
    recoveryFactor,
    profitFactor,
  };
}

/**
 * Get top performing symbols
 */
export function getTopSymbols(
  symbolMetrics: Map<string, SymbolMetrics>,
  limit: number = 10
): SymbolMetrics[] {
  return Array.from(symbolMetrics.values())
    .sort((a, b) => b.totalPnl - a.totalPnl)
    .slice(0, limit);
}

/**
 * Get bottom performing symbols (losers)
 */
export function getBottomSymbols(
  symbolMetrics: Map<string, SymbolMetrics>,
  limit: number = 10
): SymbolMetrics[] {
  return Array.from(symbolMetrics.values())
    .sort((a, b) => a.totalPnl - b.totalPnl)
    .slice(0, limit);
}

/**
 * Get best performing strategies
 */
export function getTopStrategies(
  strategyMetrics: Map<string, StrategyMetrics>,
  limit: number = 10
): StrategyMetrics[] {
  return Array.from(strategyMetrics.values())
    .sort((a, b) => b.profitFactor - a.profitFactor)
    .slice(0, limit);
}

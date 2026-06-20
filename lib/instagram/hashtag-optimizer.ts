/**
 * Instagram Hashtag Optimizer
 *
 * Generates 30 optimized hashtags for Instagram posts based on:
 * - Content type and strategy
 * - Hashtag reach distribution (popular, medium, niche)
 * - Engagement rate optimization
 *
 * Mix: 10 popular (1M+), 10 medium (100K-1M), 10 niche (10K-100K)
 */

export interface HashtagOptimizationResult {
  hashtags: string[];
  mix: {
    popular: string[];      // 1M+ posts
    medium: string[];       // 100K-1M posts
    niche: string[];        // 10K-100K posts
  };
  summary: {
    totalHashtags: number;
    estimatedReach: string;
    engagementPotential: 'low' | 'medium' | 'high';
  };
}

// Hashtag library by strategy type
const HASHTAG_LIBRARY = {
  // Strategy-specific hashtags
  meanReversion: {
    popular: ['#Trading', '#TradingStrategy', '#StockMarket', '#TechnicalAnalysis', '#Investing', '#AlgoTrading', '#TradingCommunity', '#TradingBot', '#FinTech', '#DayTrader'],
    medium: ['#BacktestingStrategies', '#MeanReversion', '#OverboughtOversold', '#RSIStrategy', '#TechnicalIndicators', '#StockTrading', '#TradingTips', '#MarketAnalysis', '#QuantitativeTrading', '#AutomatedTrading'],
    niche: ['#MeanReversionStrategy', '#BollingerBands', '#RSITrading', '#ZScoreStrategy', '#RangeBound', '#OversoldSignal', '#TechnicalAnalysisTrading', '#RetailTrader', '#TradingPsychology', '#SmallCapTrading'],
  },

  momentum: {
    popular: ['#Trading', '#TradingStrategy', '#Momentum', '#StockMarket', '#Investing', '#AlgoTrading', '#TradingCommunity', '#MarketAnalysis', '#FinTech', '#DayTrader'],
    medium: ['#MomentumTrading', '#TrendFollowing', '#TradingSignals', '#BacktestingStrategies', '#QuantitativeTrading', '#TechnicalAnalysis', '#TradingTips', '#PassiveIncome', '#WealthBuilding', '#AutomatedTrading'],
    niche: ['#MomentumStrategy', '#TrendFollowingTrading', '#RetailTrader', '#TradingFailures', '#SharpeRatio', '#DividendInvesting', '#ValueVsGrowth', '#SmallCapTrading', '#SectorRotation', '#TradingAutomation'],
  },

  volatility: {
    popular: ['#Trading', '#TradingStrategy', '#StockMarket', '#Options', '#TradingCommunity', '#FinTech', '#AlgoTrading', '#Investing', '#TechnicalAnalysis', '#DayTrader'],
    medium: ['#VolatilityTrading', '#OptionsTrading', '#BacktestingStrategies', '#RiskManagement', '#IVRank', '#SharpeRatio', '#TradingTips', '#QuantitativeTrading', '#MarketAnalysis', '#VolatilityArbitrage'],
    niche: ['#VolatilityArbitrage', '#IVCrushing', '#Straddles', '#StraddleStrategy', '#VIX', '#GammaRisk', '#TheyaDecay', '#OptionsGreeks', '#TradingPsychology', '#RiskAdjustedReturns'],
  },

  correlation: {
    popular: ['#Trading', '#TradingStrategy', '#Investing', '#Portfolio', '#RiskManagement', '#FinTech', '#StockMarket', '#TradingCommunity', '#MarketAnalysis', '#AlgoTrading'],
    medium: ['#PortfolioManagement', '#Diversification', '#BacktestingStrategies', '#RiskAdjustedReturns', '#AssetAllocation', '#CovarianceMatrix', '#QuantitativeTrading', '#TradingTips', '#WealthBuilding', '#VolatilityTrading'],
    niche: ['#CorrelationMatrices', '#DynamicCorrelation', '#PortfolioCorrelation', '#CrashCorrelation', '#AssetCorrelation', '#BetaDiversity', '#TailRisk', '#DrawdownProtection', '#MarketStress', '#SystematicRisk'],
  },

  sectorRotation: {
    popular: ['#Trading', '#Investing', '#StockMarket', '#TradingStrategy', '#AssetAllocation', '#TradingCommunity', '#MarketAnalysis', '#FinTech', '#WealthBuilding', '#Momentum'],
    medium: ['#SectorRotation', '#SectorRotationStrategy', '#MacroTrading', '#EconomicIndicators', '#BusinessCycle', '#TradingSignals', '#TechnicalAnalysis', '#BacktestingStrategies', '#QuantitativeTrading', '#TradingTips'],
    niche: ['#SectorRotationStrategy', '#EconomicCycles', '#MacroIndicators', '#TechnologyStocks', '#EnergyStocks', '#UtilityStocks', '#ConsumerDefensive', '#CyclicalStocks', '#LeadingIndicators', '#YieldCurve'],
  },

  mergerArbitrage: {
    popular: ['#Trading', '#TradingStrategy', '#StockMarket', '#Investing', '#FinTech', '#TradingCommunity', '#MarketAnalysis', '#AlgoTrading', '#DayTrader', '#RiskManagement'],
    medium: ['#ArbitrageTrading', '#MergerArbitrage', '#CorporateActions', '#EventDriven', '#BacktestingStrategies', '#TradingSignals', '#QuantitativeTrading', '#TradingTips', '#PassiveIncome', '#AlternativeInvestments'],
    niche: ['#MergerArbitrage', '#DealArbitrage', '#EventDrivenInvesting', '#AcquisitionArbitrage', '#DealSpreads', '#RegulatoryRisk', '#AntitustRisk', '#TakeoverBid', '#TenderedShares', '#ArbitrageReturn'],
  },

  // General trading hashtags
  general: {
    popular: ['#Trading', '#TradingStrategy', '#StockMarket', '#Investing', '#AlgoTrading', '#TradingCommunity', '#TechAnalysis', '#FinTech', '#DayTrader', '#TradingBot'],
    medium: ['#BacktestingStrategies', '#TradingTips', '#PassiveIncome', '#WealthBuilding', '#MarketAnalysis', '#TechnicalAnalysis', '#QuantitativeTrading', '#TradingSignals', '#AutomatedTrading', '#InvestmentStrategy'],
    niche: ['#RetailTrader', '#TradingFailures', '#TradingPsychology', '#SharpeRatio', '#BacktestFails', '#TradingAutomation', '#SmallCapTrading', '#SectorRotation', '#VolatilityTrading', '#TradingConsistency'],
  },
};

// Sentiment and psychology-focused hashtags
const SENTIMENT_HASHTAGS = {
  popular: ['#Trading', '#TradingPsychology', '#Investing', '#FinTech', '#StockMarket', '#Emotion', '#OptionFlow', '#TradingCommunity', '#DayTrader', '#MarketAnalysis'],
  medium: ['#SentimentAnalysis', '#OptionFlow', '#UnusualWhales', '#TraderPsychology', '#Emotions', '#FearGreed', '#TradingMindset', '#Discipline', '#TradingTips', '#BacktestingStrategies'],
  niche: ['#SentimentSignals', '#OptionFlowAnalysis', '#GreedIndex', '#FearIndex', '#TraderPsychology', '#CrowdPsychology', '#BehavioralFinance', '#MarketSentiment', '#BiasTrading', '#EmotionalTriggers'],
};

// Backtest and methodology hashtags
const BACKTEST_HASHTAGS = {
  popular: ['#Trading', '#TradingStrategy', '#BacktestingStrategies', '#StockMarket', '#Investing', '#TechAnalysis', '#FinTech', '#TradingCommunity', '#AlgoTrading', '#DayTrader'],
  medium: ['#BacktestingData', '#StrategyBacktest', '#HistoricalData', '#PerformanceMetrics', '#SharpeRatio', '#MaxDrawdown', '#WinRate', '#RiskAdjustedReturn', '#QuantitativeTrading', '#TradingTips'],
  niche: ['#BacktestFails', '#CurveFitting', '#OverfittingRisk', '#SurvivalorshipBias', '#ForwardTesting', '#WalkForwardAnalysis', '#OutOfSampleTesting', '#LiveVsBacktest', '#SlippageAssumptions', '#MethodologyMatters'],
};

// Automation hashtags
const AUTOMATION_HASHTAGS = {
  popular: ['#Trading', '#Automation', '#TradingBot', '#AlgoTrading', '#TradingStrategy', '#FinTech', '#TradingCommunity', '#Investing', '#DayTrader', '#StockMarket'],
  medium: ['#AutomatedTrading', '#TradingAutomation', '#RoboAdvisor', '#API', '#Trading', '#Zapier', '#IntegrationPlatform', '#QuantitativeTrading', '#TradingSignals', '#TradingTips'],
  niche: ['#TradingAutomation', '#NoCodeAutomation', '#APITrading', '#AlphaMarkets', '#InteractiveBrokers', '#QuantConnect', '#Backtrader', '#EmotionRemoval', '#Discipline', '#Consistency'],
};

/**
 * Optimize hashtags for Instagram post
 * @param content Post content (text + title)
 * @param strategyName Strategy type (meanReversion, momentum, volatility, general, sentiment, backtest, automation)
 * @returns 30 optimized hashtags with distribution analysis
 */
export function optimizeHashtags(
  content: string,
  strategyName: string = 'general'
): HashtagOptimizationResult {
  // Normalize strategy name
  const strategy = strategyName.toLowerCase().replace(/[-_\s]/g, '');

  // Select hashtag set based on strategy
  let selectedSet = HASHTAG_LIBRARY['general' as keyof typeof HASHTAG_LIBRARY];

  if (strategy.includes('meanrever')) {
    selectedSet = HASHTAG_LIBRARY.meanReversion;
  } else if (strategy.includes('momentum')) {
    selectedSet = HASHTAG_LIBRARY.momentum;
  } else if (strategy.includes('volatil')) {
    selectedSet = HASHTAG_LIBRARY.volatility;
  } else if (strategy.includes('correl')) {
    selectedSet = HASHTAG_LIBRARY.correlation;
  } else if (strategy.includes('sector')) {
    selectedSet = HASHTAG_LIBRARY.sectorRotation;
  } else if (strategy.includes('merger') || strategy.includes('arbit')) {
    selectedSet = HASHTAG_LIBRARY.mergerArbitrage;
  }

  // Detect content themes from text
  const contentLower = content.toLowerCase();
  let supplementarySet = SENTIMENT_HASHTAGS;

  if (contentLower.includes('backtest') || contentLower.includes('historical')) {
    supplementarySet = BACKTEST_HASHTAGS;
  } else if (contentLower.includes('automat') || contentLower.includes('emotion')) {
    supplementarySet = AUTOMATION_HASHTAGS;
  } else if (contentLower.includes('sentiment') || contentLower.includes('psychol')) {
    supplementarySet = SENTIMENT_HASHTAGS;
  }

  // Build final hashtag set (popular stays same, medium/niche are blended)
  const popular = [...selectedSet.popular];

  // Medium: 50% from strategy, 50% from supplementary
  const medium = [
    ...selectedSet.medium.slice(0, 5),
    ...supplementarySet.medium.slice(0, 5),
  ];

  // Niche: 60% from strategy, 40% from supplementary
  const niche = [
    ...selectedSet.niche.slice(0, 6),
    ...supplementarySet.niche.slice(0, 4),
  ];

  // Combine all hashtags
  const allHashtags = [
    ...popular.map(h => h.toLowerCase().startsWith('#') ? h : `#${h}`),
    ...medium.map(h => h.toLowerCase().startsWith('#') ? h : `#${h}`),
    ...niche.map(h => h.toLowerCase().startsWith('#') ? h : `#${h}`),
  ];

  // Remove duplicates
  const uniqueHashtags = Array.from(new Set(allHashtags));

  // Take exactly 30 if available, otherwise return all
  const finalHashtags = uniqueHashtags.slice(0, 30);

  return {
    hashtags: finalHashtags,
    mix: {
      popular: finalHashtags.filter(h => popular.some(p => p.toLowerCase() === h.toLowerCase())).slice(0, 10),
      medium: finalHashtags.filter(h => medium.some(m => m.toLowerCase() === h.toLowerCase())).slice(0, 10),
      niche: finalHashtags.filter(h => niche.some(n => n.toLowerCase() === h.toLowerCase())).slice(0, 10),
    },
    summary: {
      totalHashtags: finalHashtags.length,
      estimatedReach: `${(finalHashtags.length * 50000).toLocaleString()} - ${(finalHashtags.length * 500000).toLocaleString()} impressions`,
      engagementPotential: finalHashtags.filter(h => h.includes('niche')).length > 5 ? 'high' : 'medium',
    },
  };
}

/**
 * Get hashtag recommendation for specific post type
 * @param postType Type of post (carousel, reel, story, single)
 * @param strategyName Strategy type
 * @param contentHooks Key hooks/topics in the content
 * @returns Recommended hashtags for this specific post
 */
export function getHashtagsForPostType(
  postType: 'carousel' | 'reel' | 'story' | 'single',
  strategyName: string,
  contentHooks: string[] = []
): string[] {
  // Stories get fewer hashtags (less discoverable, more audience-focused)
  const hashtags = optimizeHashtags(contentHooks.join(' '), strategyName).hashtags;

  if (postType === 'story') {
    return hashtags.slice(0, 5); // Stories: just 5 hashtags
  } else if (postType === 'reel') {
    return hashtags.slice(0, 20); // Reels: 20 hashtags (less crowded than carousel)
  }

  return hashtags; // Carousel & single: all 30
}

/**
 * Analyze and suggest hashtags based on post performance
 * @param hashtags Current hashtags used
 * @param metrics Performance metrics (views, likes, saves)
 * @returns Suggested hashtag adjustments
 */
export function analyzeHashtagPerformance(
  hashtags: string[],
  metrics: {
    impressions: number;
    engagement: number;
    saves: number;
    shares: number;
  }
): {
  performanceScore: number;
  recommendation: string;
  adjustments: string[];
} {
  const engagementRate = (metrics.engagement / Math.max(metrics.impressions, 1)) * 100;
  const saveRate = (metrics.saves / Math.max(metrics.engagement, 1)) * 100;

  let recommendation = 'Maintain current hashtag strategy';
  let adjustments: string[] = [];

  if (engagementRate < 3) {
    recommendation = 'Engagement is low — shift to higher-competition hashtags or test new niches';
    adjustments.push('Increase popular hashtags by 2-3');
    adjustments.push('Test new niche hashtags (add 3-5)');
    adjustments.push('Verify hook quality — hashtags may not be the issue');
  } else if (engagementRate > 10 && saveRate > 20) {
    recommendation = 'Excellent performance — double down on this hashtag mix';
    adjustments.push('Reuse this exact hashtag set next post');
    adjustments.push('Test slight variation (swap 2-3 hashtags)');
  } else if (saveRate < 5) {
    recommendation = 'Saves are low — content may not be reference-worthy or hashtags miss target audience';
    adjustments.push('Add more educational/reference hashtags');
    adjustments.push('Shift niche hashtags toward technical ones');
  }

  return {
    performanceScore: engagementRate + (saveRate * 2),
    recommendation,
    adjustments,
  };
}

// Export hashtag library for direct access
export { HASHTAG_LIBRARY, SENTIMENT_HASHTAGS, BACKTEST_HASHTAGS, AUTOMATION_HASHTAGS };

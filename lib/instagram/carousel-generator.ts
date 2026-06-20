/**
 * Instagram Carousel Generator
 * Converts Threads posts into 5-7 slide carousel structures
 * Each slide has: title, key points, visual description, CTA
 */

export interface CarouselSlide {
  slideNumber: number;
  title: string;
  keyPoints: string[];
  visualDescription: string;
  textOverlay?: string;
  cta?: string;
  backgroundColor?: string;
  fontColor?: string;
}

export interface CarouselPost {
  id: string;
  strategy: string;
  title: string;
  description: string;
  slides: CarouselSlide[];
  caption: string;
  hashtags: string[];
  estimatedEngagement: {
    avgEngagement: number;
    views: number;
  };
  metadata: {
    createdAt: string;
    backtestData?: BacktestData;
    threadUrl?: string;
  };
}

export interface BacktestData {
  strategyName: string;
  returns: number;
  winRate: number;
  maxDrawdown: number;
  sharpeRatio: number;
  trades: number;
  period: string;
}

/**
 * Generates a carousel structure from thread text and strategy data
 * Input: Thread text, strategy name, optional backtest data
 * Output: Carousel JSON with 5-7 slide array
 */
export function generateCarouselFromThread(
  threadText: string,
  strategy: string,
  backtestData?: BacktestData
): CarouselPost {
  // Extract key claim and structure from thread
  const lines = threadText.split('\n').filter(line => line.trim().length > 0);
  const hook = lines[0] || 'Trading Strategy Breakdown';
  const problem = lines[1] || 'Understanding the setup';
  const proof = lines[2] || 'Real backtest results';
  const solution = lines[3] || 'How to apply this';

  // Generate slide structure
  const slides: CarouselSlide[] = [];

  // Slide 1: Hook Visual
  slides.push({
    slideNumber: 1,
    title: extractTitle(hook, strategy),
    keyPoints: [hook],
    visualDescription:
      'Large graphic with strategy name and key statistic in bold white text on trading platform color background (dark blue/black)',
    textOverlay: extractMainClaim(hook),
    backgroundColor: '#1a1a2e',
    fontColor: '#ffffff',
  });

  // Slide 2: The Problem
  const problemPoints = extractBulletPoints(problem, [
    'Market condition challenges',
    'Common trader mistakes',
    'Risk factors to consider',
    'Execution hurdles',
  ]);
  slides.push({
    slideNumber: 2,
    title: 'The Challenge',
    keyPoints: problemPoints,
    visualDescription:
      'Clean text overlay on gradient background (dark to medium gray) with 4-5 bullet points in white text, 40pt font minimum',
    textOverlay: 'What makes this strategy difficult:',
    backgroundColor: '#16213e',
    fontColor: '#ffffff',
  });

  // Slide 3: Proof (Backtest Results)
  if (backtestData) {
    const proofPoints = [
      `Returns: ${backtestData.returns}% annual`,
      `Win Rate: ${backtestData.winRate}%`,
      `Max Drawdown: ${backtestData.maxDrawdown}%`,
      `Sharpe Ratio: ${backtestData.sharpeRatio.toFixed(2)}`,
      `Trades: ${backtestData.trades} (${backtestData.period})`,
    ];
    slides.push({
      slideNumber: 3,
      title: 'Backtest Evidence',
      keyPoints: proofPoints,
      visualDescription:
        'Backtest screenshot side-by-side comparison or clean metric display showing returns, win rate, drawdown, and Sharpe ratio. Use TradingView-style green/red colors',
      textOverlay: `${strategy}: Real Results`,
      backgroundColor: '#0f3460',
      fontColor: '#ffffff',
    });
  } else {
    slides.push({
      slideNumber: 3,
      title: 'The Math',
      keyPoints: extractBulletPoints(proof, [
        'Calculation breakdown',
        'Risk/reward ratio',
        'Cost impact analysis',
        'Performance metrics',
      ]),
      visualDescription:
        'Simple graphic showing mathematical breakdown, percentages, and trading costs. Use clear typography and contrasting colors',
      textOverlay: 'Understanding the Edge',
      backgroundColor: '#0f3460',
      fontColor: '#ffffff',
    });
  }

  // Slide 4: Additional Insight
  slides.push({
    slideNumber: 4,
    title: 'Key Insight',
    keyPoints: extractBulletPoints(solution, [
      'Implementation step 1',
      'Implementation step 2',
      'Implementation step 3',
      'Common pitfall to avoid',
    ]),
    visualDescription:
      'Framework graphic or numbered steps on professional background. Use icons or simple diagrams to illustrate process flow',
    textOverlay: 'How to Apply This',
    backgroundColor: '#16213e',
    fontColor: '#ffffff',
  });

  // Slide 5: Real World Example
  slides.push({
    slideNumber: 5,
    title: 'Real Example',
    keyPoints: [
      `Strategy: ${strategy}`,
      'Market conditions when strategy works best',
      'Entry and exit signals',
      'Risk management approach',
    ],
    visualDescription:
      'Case study visual showing market chart snippet with entry/exit points marked, or trade flow diagram illustrating how strategy plays out in real trading',
    textOverlay: 'When & How It Works',
    backgroundColor: '#0f3460',
    fontColor: '#ffffff',
  });

  // Slide 6: Risk Management
  slides.push({
    slideNumber: 6,
    title: 'Risk Management',
    keyPoints: [
      'Position sizing recommendation',
      'Stop loss placement',
      'Take profit targets',
      'Maximum loss tolerance',
    ],
    visualDescription:
      'Risk management framework graphic showing position sizing, stop loss placement, and maximum drawdown tolerance with numerical examples',
    textOverlay: 'Protect Your Capital',
    backgroundColor: '#16213e',
    fontColor: '#ffffff',
  });

  // Slide 7: CTA
  slides.push({
    slideNumber: 7,
    title: 'Ready to Trade This?',
    keyPoints: [
      'Test with ProfitEngine',
      'Get realistic backtest results with slippage',
      'Paper trade before going live',
      'Link in bio for free trial',
    ],
    visualDescription:
      'Bold branded call-to-action on professional background. Include ProfitEngine logo, clear text "Try ProfitEngine" or "Start Backtesting", and "Link in Bio" in high contrast text (40pt minimum)',
    cta: 'Try ProfitEngine',
    textOverlay: 'See Your Strategy In Action',
    backgroundColor: '#e94560',
    fontColor: '#ffffff',
  });

  // Generate caption
  const caption = generateCarouselCaption(strategy, backtestData);

  // Generate hashtags (trading-focused)
  const hashtags = generateTradingHashtags(strategy);

  return {
    id: `carousel-${Date.now()}`,
    strategy,
    title: extractTitle(hook, strategy),
    description: hook,
    slides,
    caption,
    hashtags,
    estimatedEngagement: {
      avgEngagement: 8.5, // Carousel posts average 8-10% engagement
      views: 2500, // Average carousel reach
    },
    metadata: {
      createdAt: new Date().toISOString(),
      backtestData,
      threadUrl: undefined,
    },
  };
}

/**
 * Extract the main title from the hook text
 */
function extractTitle(hook: string, strategy: string): string {
  const firstSentence = hook.split('.')[0].substring(0, 60);
  return firstSentence || `${strategy} Breakdown`;
}

/**
 * Extract the main claim from hook text
 */
function extractMainClaim(hook: string): string {
  const words = hook.split(' ');
  return words.slice(0, 10).join(' ');
}

/**
 * Extract or generate bullet points from text
 */
function extractBulletPoints(text: string, defaults: string[]): string[] {
  const points = text.split('•').filter(p => p.trim().length > 0);
  if (points.length > 0) {
    return points.map(p => p.trim()).slice(0, 4);
  }
  // If no bullet points found, return defaults or split by key phrases
  const sentences = text.split(/[.!?]/).filter(s => s.trim().length > 0);
  return sentences.length > 0
    ? sentences.slice(0, 4).map(s => s.trim())
    : defaults;
}

/**
 * Generate carousel caption with trading focus
 */
function generateCarouselCaption(
  strategy: string,
  backtestData?: BacktestData
): string {
  let caption = `📊 ${strategy}: A Complete Breakdown\n\n`;
  caption += `Swipe through to see:\n`;
  caption += `✅ What makes this strategy work\n`;
  caption += `✅ Real backtest results\n`;
  caption += `✅ How to implement it\n`;
  caption += `✅ Risk management rules\n\n`;

  if (backtestData) {
    caption += `Real Results: ${backtestData.returns}% annual returns | ${backtestData.winRate}% win rate\n`;
    caption += `Max Drawdown: ${backtestData.maxDrawdown}% | Sharpe: ${backtestData.sharpeRatio.toFixed(2)}\n\n`;
  }

  caption += `Stop trusting backtests with fake assumptions. ProfitEngine shows realistic results with slippage, commissions, and real market conditions built in.\n\n`;
  caption += `See the full breakdown on Threads (link in bio) or try it live in ProfitEngine.\n\n`;
  caption += `#TradingStrategy #Backtesting #AlgoTrading #FuturesTrading #DayTrading`;

  return caption;
}

/**
 * Generate trading-focused hashtags
 */
function generateTradingHashtags(strategy: string): string[] {
  const baseHashtags = [
    '#TradingStrategy',
    '#Backtesting',
    '#AlgoTrading',
    '#FuturesTrading',
    '#DayTrading',
    '#TradingEdge',
    '#StrategyBreakdown',
    '#TradersOfInstagram',
    '#MeanReversion',
    '#MomentumTrading',
    '#TechAnalysis',
  ];

  // Add strategy-specific hashtags
  const strategyHashtags: { [key: string]: string[] } = {
    'Mean Reversion': ['#MeanReversion', '#Reversal'],
    Momentum: ['#Momentum', '#Trend'],
    'Trend Following': ['#TrendFollowing', '#Momentum'],
    'Breakout': ['#Breakout', '#Support', '#Resistance'],
  };

  let selected = baseHashtags.slice(0, 8);
  for (const [key, tags] of Object.entries(strategyHashtags)) {
    if (strategy.toLowerCase().includes(key.toLowerCase())) {
      selected = [...selected, ...tags];
      break;
    }
  }

  return [...new Set(selected)]; // Remove duplicates
}

/**
 * Validate carousel structure
 */
export function validateCarousel(carousel: CarouselPost): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (carousel.slides.length < 5 || carousel.slides.length > 7) {
    errors.push(
      `Carousel must have 5-7 slides, has ${carousel.slides.length}`
    );
  }

  carousel.slides.forEach((slide, idx) => {
    if (!slide.title || slide.title.trim().length === 0) {
      errors.push(`Slide ${idx + 1}: Missing title`);
    }
    if (!slide.keyPoints || slide.keyPoints.length === 0) {
      errors.push(`Slide ${idx + 1}: Missing key points`);
    }
    if (!slide.visualDescription || slide.visualDescription.trim().length === 0) {
      errors.push(`Slide ${idx + 1}: Missing visual description`);
    }
  });

  if (carousel.slides.length === 7) {
    const lastSlide = carousel.slides[6];
    if (!lastSlide.cta) {
      errors.push('Final slide must have a call-to-action');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

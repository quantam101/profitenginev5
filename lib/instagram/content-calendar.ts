/**
 * Instagram Content Calendar Generator
 *
 * Auto-generates weekly Instagram schedule from CONTENT_CALENDAR_MONTHLY.md
 * - Maps Threads posts to Instagram carousel format
 * - Schedules posts 3x/week (Tue, Thu, Sat)
 * - Optimizes timing for maximum reach
 */

export interface InstagramPost {
  id: string;
  title: string;
  platform: 'instagram';
  format: 'carousel' | 'reel' | 'story' | 'single_post';
  hook: string;
  mainContent: string;
  cta: string;
  slides?: {
    title: string;
    content: string;
    visual?: string;
  }[];
  scheduledTime: Date;
  timezone: 'ET' | 'CT' | 'MT' | 'PT';
  estimatedReach: string;
  hashtags: string[];
  affiliateLinks: string[];
  notesForCreator: string;
}

export interface WeeklyCalendar {
  week: number;
  month: string;
  year: number;
  posts: InstagramPost[];
  summary: {
    totalPosts: number;
    totalReelCount: number;
    totalCarousels: number;
    estimatedTotalReach: string;
    contentThemes: string[];
  };
}

// Mapping of Threads posts to Instagram carousel structure
const THREADS_TO_INSTAGRAM_MAP: Record<
  string,
  {
    threadTitle: string;
    carouselSlides: number;
    format: 'carousel' | 'reel';
    instagramSpecificHook: string;
  }
> = {
  // Week 1 posts
  'the-algorithmic-trading-lie': {
    threadTitle: 'The Algorithmic Trading Lie',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: '99% of traders are making the same mistake. Here\'s why it fails.',
  },
  'one-chart-backtests-lie': {
    threadTitle: 'One Chart That Proves Backtests Lie',
    carouselSlides: 5,
    format: 'carousel',
    instagramSpecificHook: 'Your backtest looked perfect. Your live trading lasted 3 weeks. Save this to understand why.',
  },
  'why-profitable-strategy-blew-up': {
    threadTitle: 'The Real Reason Your Profitable Strategy Blew Up',
    carouselSlides: 7,
    format: 'carousel',
    instagramSpecificHook: 'Black swan events + slippage + liquidity = your strategy failure. Thread explains all 5.',
  },
  'why-retail-shouldnt-backtest': {
    threadTitle: 'Why Retail Traders Shouldn\'t Backtest (Until Now)',
    carouselSlides: 5,
    format: 'carousel',
    instagramSpecificHook: 'Most backtests use perfect market conditions. Real markets don\'t. Here\'s what to fix.',
  },
  'sentiment-signal-that-works': {
    threadTitle: 'The Sentiment Signal That Works',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: 'Options flow signals work 73% of the time. But only if you validate them right.',
  },
  'hardest-part-trading': {
    threadTitle: 'The Hardest Part of Trading Is Not What You Think',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: 'It\'s not picking the trade. It\'s staying in when you\'re down $10K. The psychology breakdown.',
  },
  'volatility-is-not-risk': {
    threadTitle: 'Volatility Is Not Risk',
    carouselSlides: 5,
    format: 'carousel',
    instagramSpecificHook: 'Your broker thinks volatility = risk. You\'re managing risk wrong. One chart proves it.',
  },
  'one-metric-predicts-trading-success': {
    threadTitle: 'The One Metric That Predicts Trading Success 18 Months Out',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: 'It\'s not Sharpe ratio. It\'s not Sortino. It\'s this one number (and 87% of traders ignore it).',
  },
  'automate-everything': {
    threadTitle: 'Why You Should Automate Everything',
    carouselSlides: 5,
    format: 'carousel',
    instagramSpecificHook: 'Manual trading loses money. Automation wins. Here\'s the math that proves it.',
  },
  'backtest-benchmark-every-trader-should-know': {
    threadTitle: 'The Backtest Benchmark Every Trader Should Know',
    carouselSlides: 5,
    format: 'carousel',
    instagramSpecificHook: 'Your 15% return sounds good. It\'s actually terrible. Here\'s the real benchmark.',
  },

  // Week 2 posts
  'mean-reversion-works': {
    threadTitle: 'Mean Reversion Works—But Only If You Know This Secret',
    carouselSlides: 7,
    format: 'carousel',
    instagramSpecificHook: '65% win rate on paper. 92% of traders lose money. Here\'s the regime detection secret.',
  },
  'momentum-strategy-2026': {
    threadTitle: 'The Momentum Strategy That Actually Works in 2026',
    carouselSlides: 6,
    format: 'reel',
    instagramSpecificHook: 'Everyone knows about momentum. Yet it still works. Here\'s why + the modern twist.',
  },
  'volatility-arbitrage': {
    threadTitle: 'Why Volatility Arbitrage Is the Hardest Strategy to Implement',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: 'Vol trading looks profitable in theory. In reality, your broker bleeds you dry.',
  },

  // Week 3 posts
  'correlation-secret': {
    threadTitle: 'The Correlation Secret Nobody Talks About',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: 'Your 50-stock portfolio looked diversified. Then the crash came. All moved together. Here\'s why.',
  },
  'sector-rotation-30-years': {
    threadTitle: 'Sector Rotation: The Pattern That Survived 30 Years',
    carouselSlides: 6,
    format: 'carousel',
    instagramSpecificHook: 'Sector rotation is proven. Yet 99% of traders can\'t trade it profitably. Here\'s what they\'re missing.',
  },
  'merger-arbitrage-40-percent': {
    threadTitle: 'The Merger Arbitrage Strategy That Made 40% in 2025',
    carouselSlides: 7,
    format: 'carousel',
    instagramSpecificHook: 'While crypto crashed, this strategy made 40% with <5% volatility. The M&A playbook.',
  },

  // Week 4 major post (becomes long reel + pinned post)
  'everything-learned-trading-this-year': {
    threadTitle: 'Everything I Learned About Trading This Year (In 1 Thread)',
    carouselSlides: 10,
    format: 'reel',
    instagramSpecificHook: '47% annual returns + major failures + ProfitEngine origin. The complete year-end breakdown.',
  },
};

// Optimal posting times (EST timezone)
const POSTING_SCHEDULE = {
  tuesday: ['09:00', '14:00'], // 9 AM & 2 PM
  thursday: ['14:00', '21:00'], // 2 PM & 7 PM
  saturday: ['09:00'], // 9 AM
};

/**
 * Generate weekly Instagram calendar from thread posts
 * @param weekNumber Week number (1-4)
 * @param month Month name
 * @param year Year
 * @param startDate Date of Monday that week
 * @returns Complete weekly calendar with all posts scheduled
 */
export function generateWeeklyCalendar(
  weekNumber: number,
  month: string,
  year: number,
  startDate: Date
): WeeklyCalendar {
  const posts: InstagramPost[] = [];

  // Determine which posts belong to this week
  const weekPostsMap: Record<number, string[]> = {
    1: [
      'the-algorithmic-trading-lie',
      'one-chart-backtests-lie',
      'why-profitable-strategy-blew-up',
      'why-retail-shouldnt-backtest',
      'sentiment-signal-that-works',
      'hardest-part-trading',
      'volatility-is-not-risk',
      'one-metric-predicts-trading-success',
      'automate-everything',
      'backtest-benchmark-every-trader-should-know',
    ],
    2: [
      'mean-reversion-works',
      'momentum-strategy-2026',
      'volatility-arbitrage',
    ],
    3: [
      'correlation-secret',
      'sector-rotation-30-years',
      'merger-arbitrage-40-percent',
    ],
    4: [
      'everything-learned-trading-this-year',
    ],
  };

  const weekPosts = weekPostsMap[weekNumber] || [];
  let dayOfWeek = 0; // 0 = Monday
  let postIndex = 0;

  for (const threadPostId of weekPosts) {
    const threadInfo = THREADS_TO_INSTAGRAM_MAP[threadPostId];
    if (!threadInfo) continue;

    // Schedule on Tue (1), Thu (3), Sat (5) only
    let scheduleDay = dayOfWeek % 7;
    if (weekNumber === 1) {
      // Week 1: post daily (Mon-Sun)
      scheduleDay = postIndex % 7;
    } else if (weekNumber <= 3) {
      // Week 2-3: 3x per week (Tue, Thu, Sat)
      const schedule = [1, 3, 5]; // Tue, Thu, Sat
      scheduleDay = schedule[postIndex % 3];
    } else {
      // Week 4: Focus on one major post (Wednesday)
      scheduleDay = 3; // Wednesday
    }

    // Calculate scheduled time
    const scheduledDate = new Date(startDate);
    scheduledDate.setDate(scheduledDate.getDate() + scheduleDay);

    // Set time based on day
    const timeHour = scheduleDay === 1 ? 9 : scheduleDay === 3 ? 14 : 9; // Tue 9 AM, Thu 2 PM, Sat 9 AM
    scheduledDate.setHours(timeHour, 0, 0, 0);

    const post = createInstagramPost(
      threadPostId,
      threadInfo,
      scheduledDate,
      postIndex + 1
    );

    posts.push(post);
    postIndex++;
  }

  return {
    week: weekNumber,
    month,
    year,
    posts,
    summary: {
      totalPosts: posts.length,
      totalReelCount: posts.filter(p => p.format === 'reel').length,
      totalCarousels: posts.filter(p => p.format === 'carousel').length,
      estimatedTotalReach: calculateTotalReach(posts),
      contentThemes: extractContentThemes(posts),
    },
  };
}

/**
 * Create a single Instagram post from thread info
 */
function createInstagramPost(
  threadId: string,
  threadInfo: any,
  scheduledTime: Date,
  postNumber: number
): InstagramPost {
  const carouselSlides = buildCarouselSlides(threadId, threadInfo);

  return {
    id: `instagram_${threadId}_w${scheduledTime.getWeek()}`,
    title: `${threadInfo.threadTitle} (Instagram Version)`,
    platform: 'instagram',
    format: threadInfo.format,
    hook: threadInfo.instagramSpecificHook,
    mainContent: buildMainContent(threadId),
    cta: 'Save this guide • Link in bio for full strategy access',
    slides: threadInfo.format === 'carousel' ? carouselSlides : undefined,
    scheduledTime,
    timezone: 'ET',
    estimatedReach: estimateReach(threadInfo.format),
    hashtags: generateHashtagsForPost(threadId, threadInfo),
    affiliateLinks: getAffiliateLinksForPost(threadId),
    notesForCreator: buildCreatorNotes(threadId, threadInfo),
  };
}

/**
 * Build carousel slides for Instagram post
 */
function buildCarouselSlides(
  threadId: string,
  threadInfo: any
): InstagramPost['slides'] {
  const slides: InstagramPost['slides'] = [];

  // Slide 1: Hook graphic
  slides.push({
    title: 'Hook',
    content: threadInfo.instagramSpecificHook,
    visual: `Chart or icon relevant to ${threadId}`,
  });

  // Slides 2-N: Content breakdown (simplified for carousel)
  const contentPoints = buildContentPoints(threadId);
  for (const point of contentPoints) {
    slides.push({
      title: point.title,
      content: point.summary,
      visual: point.visual,
    });
  }

  // Final slide: CTA
  slides.push({
    title: 'Call to Action',
    content: 'Join 2,000+ traders testing ProfitEngine\nFree 14-day trial → Link in bio',
    visual: 'Arrow pointing to profile link',
  });

  return slides.slice(0, threadInfo.carouselSlides);
}

/**
 * Build content points for carousel from thread
 */
function buildContentPoints(threadId: string): Array<{ title: string; summary: string; visual: string }> {
  const contentMap: Record<string, any[]> = {
    'the-algorithmic-trading-lie': [
      { title: 'The Problem', summary: '99% use RSI, MA crosses—same signals = same losses', visual: 'Stock chart' },
      { title: 'Why It Fails', summary: 'Market makers prevent retail from profiting on known patterns', visual: 'Game theory diagram' },
      { title: 'Reality Check', summary: 'Backtests differ 40-60% from live trading', visual: 'Backtest vs Live chart' },
      { title: 'The Solution', summary: 'Multi-factor validation system prevents false signals', visual: 'Validation matrix' },
    ],
    'one-chart-backtests-lie': [
      { title: 'Perfect Backtest', summary: '47% annual returns in 2023 backtest', visual: 'Uptrend chart' },
      { title: 'Reality in 2024', summary: 'Same strategy earned only 3% in live trading', visual: 'Sidetrend chart' },
      { title: 'The Trap', summary: 'Curve fitting + survivorship bias destroy results', visual: 'Danger icon' },
      { title: 'ProfitEngine Fix', summary: 'Multi-market validation before trading', visual: 'Validation checkmark' },
    ],
    'hardest-part-trading': [
      { title: 'You Think It\'s', summary: 'Picking the right trade', visual: 'Chart analysis' },
      { title: 'Actually It\'s', summary: 'Staying in when you\'re down $10K and seeing red', visual: 'Emotional state' },
      { title: 'The Psychology', summary: 'Loss aversion is 2x gain attraction in humans', visual: 'Psychology chart' },
      { title: 'The Solution', summary: 'Automated execution removes emotion completely', visual: 'Robot icon' },
    ],
    'volatility-is-not-risk': [
      { title: 'Common Mistake', summary: 'Assuming volatility = risk', visual: 'Chart volatility' },
      { title: 'The Truth', summary: 'High volatility + stable returns = low actual risk', visual: 'Risk vs volatility' },
      { title: 'Real Example', summary: 'Tesla: 100% volatility, 22% return, Sharpe 1.8', visual: 'TSLA chart' },
      { title: 'Better Metric', summary: 'Risk = max drawdown, not daily swings', visual: 'Drawdown chart' },
    ],
  };

  return contentMap[threadId] || [
    { title: 'Key Point 1', summary: 'See full thread on ProfitEngine for details', visual: 'Generic trading chart' },
    { title: 'Key Point 2', summary: 'Multi-factor validation system included', visual: 'Checkmark' },
  ];
}

/**
 * Generate hashtags for post
 */
function generateHashtagsForPost(threadId: string, threadInfo: any): string[] {
  const baseHashtags = [
    '#Trading',
    '#TradingStrategy',
    '#BacktestingStrategies',
    '#TradingCommunity',
    '#AlgoTrading',
    '#TechAnalysis',
    '#MarketAnalysis',
    '#TradingTips',
    '#QuantitativeTrading',
    '#TradingBot',
    '#FinTech',
    '#DayTrader',
    '#Investing',
    '#StockMarket',
    '#TradingSignals',
  ];

  // Add strategy-specific hashtags
  if (threadId.includes('mean-reversion')) {
    baseHashtags.push('#MeanReversionStrategy', '#OverboughtOversold', '#RSITrading');
  } else if (threadId.includes('momentum')) {
    baseHashtags.push('#MomentumTrading', '#TrendFollowing', '#MomentumStrategy');
  } else if (threadId.includes('volatility')) {
    baseHashtags.push('#VolatilityTrading', '#VolatilityArbitrage', '#IVRank');
  } else if (threadId.includes('correlation')) {
    baseHashtags.push('#PortfolioManagement', '#Diversification', '#RiskManagement');
  } else if (threadId.includes('sector')) {
    baseHashtags.push('#SectorRotation', '#SectorRotationStrategy', '#MacroTrading');
  }

  // Add psychological/automation hashtags for relevant posts
  if (threadId.includes('hardest') || threadId.includes('psychology')) {
    baseHashtags.push('#TradingPsychology', '#Discipline', '#Emotion');
  }
  if (threadId.includes('automate')) {
    baseHashtags.push('#AutomatedTrading', '#TradingAutomation', '#Zapier');
  }

  return baseHashtags.slice(0, 30); // Instagram max 30 recommended
}

/**
 * Get affiliate links for post
 */
function getAffiliateLinksForPost(threadId: string): string[] {
  const linkMap: Record<string, string[]> = {
    'the-algorithmic-trading-lie': [
      'tradingview.com?offer=alreadyhere',
      'zapier.com/apps/bundle/trading-automation',
      'polygon.io/referral/alreadyhere',
    ],
    'one-chart-backtests-lie': [
      'quantconnect.com/referral/alreadyhere',
      'kaggle.com/competitions?affiliation=alreadyhere',
    ],
    'mean-reversion-works': [
      'tradingview.com?offer=alreadyhere',
      'quantconnect.com?affiliate=alreadyhere',
    ],
    'momentum-strategy-2026': [
      'seekingalpha.com/premium?affiliate=alreadyhere',
      'morningstar.com/premium?affiliate=alreadyhere',
    ],
    'volatility-arbitrage': [
      'interactivebrokers.com',
      'cboe.com/education?affiliate=alreadyhere',
    ],
    'correlation-secret': [
      'morningstar.com?affiliate=alreadyhere',
      'numpy.org',
    ],
    'sector-rotation-30-years': [
      'fred.stlouisfed.org',
      'tradingeconomics.com?affiliate=alreadyhere',
    ],
    'merger-arbitrage-40-percent': [
      'pitchbook.com?affiliate=alreadyhere',
      'morningstar.com?affiliate=alreadyhere',
    ],
  };

  return linkMap[threadId] || [
    'profitengine.com/trading-free-trial?utm_source=instagram&utm_medium=carousel',
  ];
}

/**
 * Build main content summary
 */
function buildMainContent(threadId: string): string {
  const contentMap: Record<string, string> = {
    'the-algorithmic-trading-lie':
      'Most retail traders use identical entry signals. When everyone uses the same strategy, everyone gets the same results: losses. This carousel breaks down why and what to do instead.',
    'one-chart-backtests-lie':
      'Your backtest showed 47% annual returns. But when you traded it live, something changed. This guide explains why backtests lie and how to fix your methodology.',
    'hardest-part-trading':
      'You think trading is about picking winners. But the hardest part is psychological: staying in trades when you\'re down money and feeling scared. This breakdown shows why automation is the solution.',
    'volatility-is-not-risk':
      'Your broker thinks volatility = risk. But a volatile asset with stable returns is actually lower risk than a stable asset with unpredictable returns. Learn the math.',
  };

  return (
    contentMap[threadId] ||
    'See full breakdown in this carousel. Save it for reference.'
  );
}

/**
 * Build creator notes
 */
function buildCreatorNotes(threadId: string, threadInfo: any): string {
  return `
Post Type: ${threadInfo.format === 'carousel' ? 'Carousel (' + threadInfo.carouselSlides + ' slides)' : 'Reel (60 sec)'}
Effort Level: Medium (repurposed from Threads, optimized for Instagram format)
Key Talking Points:
1. ${threadInfo.instagramSpecificHook}
2. Use real charts/screenshots in slides 2-4
3. End with clear CTA to bio link
4. Pin this post if engagement >8% within first 24 hours
5. Respond to top 20 comments within 2 hours for algorithm boost
Note: This post complements Threads version; use complementary messaging on both platforms.
  `.trim();
}

/**
 * Estimate reach for post format
 */
function estimateReach(format: 'carousel' | 'reel' | 'story' | 'single_post'): string {
  const reachMap = {
    carousel: '800-1,200 views (Month 1), 2,000-3,500 views (Month 3)',
    reel: '1,200-2,500 views (Month 1), 3,000-6,000 views (Month 3)',
    story: '200-400 views',
    single_post: '500-800 views',
  };

  return reachMap[format];
}

/**
 * Calculate total reach for all posts
 */
function calculateTotalReach(posts: InstagramPost[]): string {
  let totalMin = 0;
  let totalMax = 0;

  for (const post of posts) {
    const reach = post.estimatedReach;
    // Parse range string (e.g., "800-1,200 views")
    const numbers = reach.match(/\d+/g);
    if (numbers && numbers.length >= 2) {
      totalMin += parseInt(numbers[0].replace(/,/g, ''));
      totalMax += parseInt(numbers[1].replace(/,/g, ''));
    }
  }

  return `${totalMin.toLocaleString()}-${totalMax.toLocaleString()} total impressions`;
}

/**
 * Extract content themes from posts
 */
function extractContentThemes(posts: InstagramPost[]): string[] {
  const themes = new Set<string>();

  for (const post of posts) {
    if (post.title.includes('Mean Reversion')) themes.add('Mean Reversion');
    if (post.title.includes('Momentum')) themes.add('Momentum');
    if (post.title.includes('Volatility')) themes.add('Volatility Trading');
    if (post.title.includes('Correlation')) themes.add('Correlation & Diversification');
    if (post.title.includes('Sector')) themes.add('Sector Rotation');
    if (post.title.includes('Psychology') || post.title.includes('Hardest'))
      themes.add('Trading Psychology');
    if (post.title.includes('Backtest')) themes.add('Backtesting');
    if (post.title.includes('Automate')) themes.add('Automation');
  }

  return Array.from(themes);
}

// Helper to get week number of date
declare global {
  interface Date {
    getWeek(): number;
  }
}

Date.prototype.getWeek = function () {
  const date = new Date(this.getTime());
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() + 4 - (date.getDay() || 7));
  const yearStart = new Date(date.getFullYear(), 0, 1);
  const weekNumber = Math.ceil(((date.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return weekNumber;
};

/**
 * Generate full month calendar
 * @param month Month name
 * @param year Year
 * @param startDate First Monday of the month
 * @returns Array of 4 weekly calendars
 */
export function generateMonthlyCalendar(
  month: string,
  year: number,
  startDate: Date
): WeeklyCalendar[] {
  const calendars: WeeklyCalendar[] = [];

  for (let week = 1; week <= 4; week++) {
    const weekStart = new Date(startDate);
    weekStart.setDate(weekStart.getDate() + (week - 1) * 7);

    calendars.push(generateWeeklyCalendar(week, month, year, weekStart));
  }

  return calendars;
}

/**
 * Format calendar for display/export
 */
export function formatCalendarForDisplay(calendar: WeeklyCalendar): string {
  let output = `
=== WEEK ${calendar.week} — ${calendar.month.toUpperCase()} ${calendar.year} ===

📊 Summary:
   Total Posts: ${calendar.summary.totalPosts}
   Carousels: ${calendar.summary.totalCarousels}
   Reels: ${calendar.summary.totalReelCount}
   Estimated Total Reach: ${calendar.summary.estimatedTotalReach}
   Content Themes: ${calendar.summary.contentThemes.join(', ')}

📅 Posts:
`;

  for (const post of calendar.posts) {
    output += `
   🔷 ${post.title}
      Time: ${post.scheduledTime.toLocaleDateString()} @ ${post.scheduledTime.toLocaleTimeString()}
      Format: ${post.format.toUpperCase()}
      Hook: ${post.hook}
      CTA: ${post.cta}
      Reach: ${post.estimatedReach}
      Creator Notes: ${post.notesForCreator.split('\n')[0]}
`;
  }

  return output;
}

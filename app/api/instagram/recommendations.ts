/**
 * Instagram Recommendations API
 *
 * POST /api/instagram/recommendations
 *
 * AI-powered recommendations for converting Threads posts to optimized Instagram content.
 * Takes Threads data and returns format suggestions, timing, hashtags, and hooks optimized for Instagram.
 */

import { NextRequest, NextResponse } from 'next/server';
import { optimizeHashtags } from '@/lib/instagram/hashtag-optimizer';

export interface InstagramRecommendationRequest {
  threadId: string;
  threadText: string;
  engagementMetrics?: {
    likes?: number;
    replies?: number;
    reposts?: number;
    impressions?: number;
  };
  strategyType?: string;
  contentTheme?: string;
}

export interface InstagramRecommendation {
  threadId: string;
  suggestedFormat: 'carousel' | 'reel' | 'story' | 'captions';
  suggestedScheduleTime: string;
  estimatedReach: {
    low: number;
    high: number;
    unit: string;
  };
  hook: string;
  hookReasoning: string;
  carouselSlideCount?: number;
  reelDuration?: string;
  captions: {
    instagram: string;
    hashtags: string[];
  };
  affiliateLinks: string[];
  contentNotes: string[];
  conversionPotential: {
    score: 0 | 1 | 2 | 3 | 4 | 5;
    reasoning: string;
    suggestedCTA: string;
  };
  performanceComparison: {
    estimatedEngagementRate: string;
    comparisonToThreads: string;
  };
}

/**
 * Analyze Threads engagement and determine optimal Instagram format
 */
function analyzeContent(
  threadText: string,
  metrics?: InstagramRecommendationRequest['engagementMetrics']
): {
  format: 'carousel' | 'reel' | 'story' | 'captions';
  reasoning: string;
  priority: number;
} {
  // Calculate engagement rate if metrics provided
  const engagementRate = metrics?.impressions
    ? ((metrics.likes || 0) + (metrics.replies || 0) + (metrics.reposts || 0)) /
      metrics.impressions
    : 0;

  const threadLength = threadText.length;
  const hasNumbers = /\$\d+|%|\d+x|×/.test(threadText);
  const hasStory = /fail|lost|wrong|mistake|lesson|learned|psychology|emotion/.test(
    threadText.toLowerCase()
  );
  const hasEducation = /how to|strategy|backtest|signal|setup|pattern/.test(
    threadText.toLowerCase()
  );

  // Decision logic
  if (engagementRate > 0.15 || (threadLength > 2000 && hasEducation)) {
    return {
      format: 'carousel',
      reasoning: 'High engagement + educational depth = carousel for deep-dive value',
      priority: 1,
    };
  } else if (hasStory && engagementRate > 0.08) {
    return {
      format: 'reel',
      reasoning: 'Story-driven + good engagement = reel for emotional hook + algorithm boost',
      priority: 1,
    };
  } else if (threadLength < 500 && hasNumbers) {
    return {
      format: 'captions',
      reasoning: 'Short + data-rich = single post with image/chart',
      priority: 2,
    };
  } else {
    return {
      format: 'carousel',
      reasoning: 'Default to carousel for flexibility and re-engagement boost',
      priority: 2,
    };
  }
}

/**
 * Generate Instagram-optimized hook from Threads text
 */
function generateInstagramHook(
  threadText: string,
  format: 'carousel' | 'reel' | 'story' | 'captions'
): { hook: string; reasoning: string } {
  // Extract key claims/numbers from Threads text
  const numbers = threadText.match(/\d+%|%\d+|\$[\d,]+|[\d.,]+x/g) || [];
  const strongClaims = threadText.match(
    /\b(never|always|impossible|impossible|works|fails|breaks|destroys|proves)\b/gi
  ) || [];

  // Format-specific hooks
  if (format === 'carousel') {
    if (numbers.length > 0) {
      return {
        hook: `Your strategy is wrong. Here's the ${numbers[0]} mistake.`,
        reasoning: 'Carousel + specific number = high save rate (people bookmark)',
      };
    }
    return {
      hook: 'Save this before you trade again.',
      reasoning: 'Carousel hook that drives saves and reference bookmarks',
    };
  } else if (format === 'reel') {
    if (strongClaims.length > 0) {
      const claim = strongClaims[0].toLowerCase();
      return {
        hook: `Everyone thinks you should ${claim}. They're wrong.`,
        reasoning: 'Reel hook that stops scroll with contrarian angle',
      };
    }
    return {
      hook: '99% of traders do this wrong. Watch to fix it.',
      reasoning: 'Reel hook that creates curiosity and urgency',
    };
  } else if (format === 'captions') {
    const firstSentence = threadText.split('.')[0];
    return {
      hook: firstSentence.substring(0, 100),
      reasoning: 'Caption hook should be direct + intriguing',
    };
  } else {
    return {
      hook: 'Read the caption for full insight.',
      reasoning: 'Story hook keeps it simple',
    };
  }
}

/**
 * Calculate estimated reach for format
 */
function estimateReach(format: 'carousel' | 'reel' | 'story' | 'captions', followerCount: number = 0) {
  // Base reach estimates (adjusted by account size)
  const multiplier = Math.max(1, followerCount / 1000);

  const reachMap = {
    carousel: { low: 800, high: 2000 },
    reel: { low: 1200, high: 3500 },
    story: { low: 400, high: 800 },
    captions: { low: 500, high: 1200 },
  };

  const base = reachMap[format];
  return {
    low: Math.floor(base.low * multiplier),
    high: Math.floor(base.high * multiplier),
    unit: 'views',
  };
}

/**
 * Determine best posting time for format
 */
function suggestPostingTime(format: 'carousel' | 'reel' | 'story' | 'captions'): string {
  const timeMap = {
    carousel: 'Tuesday 9 AM ET or Thursday 2 PM ET (weekday peak)',
    reel: 'Thursday 2 PM ET or Saturday 9 AM ET (algorithm boost window)',
    story: 'Daily at 12-2 PM ET (lunch break engagement)',
    captions: 'Tuesday 9 AM ET (start of week attention)',
  };

  return timeMap[format];
}

/**
 * Score conversion potential
 */
function scoreConversionPotential(
  format: 'carousel' | 'reel' | 'story' | 'captions',
  metrics?: InstagramRecommendationRequest['engagementMetrics']
): { score: 0 | 1 | 2 | 3 | 4 | 5; reasoning: string; cta: string } {
  const engagementRate = metrics?.impressions
    ? ((metrics.likes || 0) + (metrics.replies || 0)) / metrics.impressions
    : 0;

  if (format === 'carousel') {
    if (engagementRate > 0.12) {
      return {
        score: 5,
        reasoning: 'High-engagement carousel = premium conversion potential',
        cta: 'Save this strategy guide • Link in bio for free trial access',
      };
    }
    return {
      score: 4,
      reasoning: 'Carousel format drives 3-4x more link clicks than single posts',
      cta: 'Link in bio for the complete free trial',
    };
  } else if (format === 'reel') {
    return {
      score: 3,
      reasoning: 'Reels get reach but lower link CTR — use direct CTA overlay',
      cta: 'Free trial link in bio 👆',
    };
  } else if (format === 'captions') {
    return {
      score: 2,
      reasoning: 'Single posts drive fewest conversions — supplement with stories',
      cta: 'See link in bio for free strategy',
    };
  } else {
    return {
      score: 1,
      reasoning: 'Stories are ephemeral — great for engagement, lower conversion',
      cta: 'Free trial: link in our bio 👆',
    };
  }
}

/**
 * Generate hashtag recommendations
 */
function generateHashtagRecommendations(
  threadText: string,
  strategyType?: string
): string[] {
  const result = optimizeHashtags(threadText, strategyType || 'general');
  return result.hashtags.slice(0, 30); // Instagram recommendation
}

/**
 * Main recommendation handler
 */
async function getRecommendation(
  request: InstagramRecommendationRequest
): Promise<InstagramRecommendation> {
  const { threadId, threadText, engagementMetrics, strategyType, contentTheme } = request;

  // Analyze content for optimal format
  const analysis = analyzeContent(threadText, engagementMetrics);

  // Generate Instagram-optimized hook
  const { hook, reasoning: hookReasoning } = generateInstagramHook(threadText, analysis.format);

  // Estimate reach
  const estimatedReach = estimateReach(analysis.format);

  // Suggest posting time
  const scheduledTime = suggestPostingTime(analysis.format);

  // Generate hashtags
  const hashtags = generateHashtagRecommendations(threadText, strategyType);

  // Score conversion potential
  const conversionPotential = scoreConversionPotential(analysis.format, engagementMetrics);

  // Generate content notes
  const contentNotes = generateContentNotes(analysis.format, threadText);

  // Extract affiliate links from content (basic regex)
  const affiliateLinks = extractAffiliateLinks(threadText);

  // Build Instagram captions
  const instagramCaption = buildInstagramCaption(hook, analysis.format);

  return {
    threadId,
    suggestedFormat: analysis.format,
    suggestedScheduleTime: scheduledTime,
    estimatedReach,
    hook,
    hookReasoning,
    carouselSlideCount: analysis.format === 'carousel' ? 6 : undefined,
    reelDuration: analysis.format === 'reel' ? '30-60 seconds' : undefined,
    captions: {
      instagram: instagramCaption,
      hashtags,
    },
    affiliateLinks,
    contentNotes,
    conversionPotential: {
      score: conversionPotential.score,
      reasoning: conversionPotential.reasoning,
      suggestedCTA: conversionPotential.cta,
    },
    performanceComparison: {
      estimatedEngagementRate:
        analysis.format === 'carousel'
          ? '8-12% (high)'
          : analysis.format === 'reel'
          ? '10-15% (very high)'
          : '3-6% (low)',
      comparisonToThreads: `Instagram ${analysis.format} format will reach 2-4x more people than Threads post`,
    },
  };
}

/**
 * Generate content notes for creator
 */
function generateContentNotes(
  format: 'carousel' | 'reel' | 'story' | 'captions',
  threadText: string
): string[] {
  const notes: string[] = [];

  if (format === 'carousel') {
    notes.push('Carousel slides: Hook → Problem → Solution → Proof → CTA');
    notes.push('Use real screenshots/charts in slides 2-4 for credibility');
    notes.push('Keep text minimal (large font, readable at thumb size)');
    notes.push('Target save rate: 20%+ of views indicates strong reference value');
  } else if (format === 'reel') {
    notes.push('Hook first 3 seconds with bold claim or visual');
    notes.push('Captions essential (50% watch muted)');
    notes.push('Aim for 60-90 second total with pacing (don\'t rush)');
    notes.push('End with 10-second strong CTA');
  } else if (format === 'captions') {
    notes.push('Pair with eye-catching chart/image (not just text)');
    notes.push('First line is crucial (gets cut off after 125 chars on feed)');
    notes.push('Use line breaks for scannability');
  } else {
    notes.push('Use story stickers (polls, Q&A) to drive DMs');
    notes.push('Stories disappear in 24h — prioritize profile link CTR');
  }

  // Add specific notes based on content
  if (threadText.includes('backtest') || threadText.includes('$')) {
    notes.push('Emphasize social proof — this is data-driven content');
  }
  if (threadText.toLowerCase().includes('psychology') || threadText.toLowerCase().includes('emotion')) {
    notes.push('Lead with personal vulnerability — relatability drives shares');
  }

  return notes;
}

/**
 * Extract affiliate links from thread text
 */
function extractAffiliateLinks(threadText: string): string[] {
  const urlRegex = /(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+)/g;
  const matches = threadText.match(urlRegex) || [];
  const links = Array.from(new Set(matches)); // Remove duplicates

  // Map common trading tools to affiliate versions
  const affiliateMap: Record<string, string> = {
    tradingview: 'tradingview.com?offer=alreadyhere',
    quantconnect: 'quantconnect.com/referral/alreadyhere',
    interactivebrokers: 'interactivebrokers.com',
    alpaca: 'alpaca.markets?affiliate=alreadyhere',
    zapier: 'zapier.com/apps/bundle/trading-automation',
  };

  const result: string[] = [];
  for (const link of links) {
    for (const [key, affiliate] of Object.entries(affiliateMap)) {
      if (link.toLowerCase().includes(key)) {
        result.push(affiliate);
        break;
      }
    }
  }

  // Always include main CTA link
  if (result.length === 0) {
    result.push('profitengine.com/trading-free-trial?utm_source=instagram');
  }

  return result;
}

/**
 * Build Instagram caption from hook and format
 */
function buildInstagramCaption(hook: string, format: string): string {
  if (format === 'carousel') {
    return `${hook}\n\nSwipe through for the complete breakdown 👉\n\nSave this guide for your next strategy review.`;
  } else if (format === 'reel') {
    return `${hook}\n\nLink in bio for the full free trial 👆\n\nReply: what resonates most with you?`;
  } else if (format === 'captions') {
    return `${hook}\n\nFull strategy & backtest proof → link in bio`;
  } else {
    return `${hook}\n\nTap link in bio`;
  }
}

/**
 * POST handler
 */
export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as InstagramRecommendationRequest;

    // Validate required fields
    if (!body.threadId || !body.threadText) {
      return NextResponse.json(
        { error: 'Missing required fields: threadId, threadText' },
        { status: 400 }
      );
    }

    // Generate recommendation
    const recommendation = await getRecommendation(body);

    return NextResponse.json(recommendation, { status: 200 });
  } catch (error) {
    console.error('Error generating Instagram recommendation:', error);
    return NextResponse.json(
      { error: 'Failed to generate recommendation' },
      { status: 500 }
    );
  }
}

/**
 * GET handler — example request
 */
export async function GET(request: NextRequest) {
  const exampleRequest: InstagramRecommendationRequest = {
    threadId: 'example-thread-001',
    threadText: `Your backtest shows 47% returns. But when you traded it live, something changed.

The problem: backtests use perfect market conditions. Real markets have slippage, gaps, and emotional pressure.

Mean reversion strategy from 2023 backtest: +47%
Same strategy live in 2024: +3%

This gap happens because:
1. Slippage: Assumed 0.1%, reality 1-2%
2. Liquidity: Can't exit at the exact price
3. Drawdown: 20% max in backtest, 35% in reality (you quit)
4. Correlation: Assets moved together during stress

ProfitEngine's fix: stress-test strategies against real market friction before trading.`,
    engagementMetrics: {
      likes: 1500,
      replies: 450,
      reposts: 200,
      impressions: 15000,
    },
    strategyType: 'mean-reversion',
    contentTheme: 'backtest-vs-live',
  };

  const recommendation = await getRecommendation(exampleRequest);

  return NextResponse.json(
    {
      message: 'Example Instagram recommendation request',
      example: exampleRequest,
      recommendation,
    },
    { status: 200 }
  );
}

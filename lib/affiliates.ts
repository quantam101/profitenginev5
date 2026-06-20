/**
 * lib/affiliates.ts — ProfitEngine v5
 *
 * Affiliate link registry, insertion utilities, tracking, and revenue calculations.
 *
 * Features:
 * - Centralized affiliate partner registry
 * - Dynamic link generation with UTM parameters
 * - Content affiliate mapping (which posts use which links)
 * - Click tracking and revenue analytics
 * - Monthly revenue calculator
 */

/**
 * Affiliate partner configuration
 */
export interface AffiliatePartner {
  id: string;
  name: string;
  url: string;
  commission: {
    type: 'cpa' | 'revenue_share' | 'percentage';
    value: number; // CPA amount in USD or percentage
    currency?: string;
    description?: string;
  };
  tier: 1 | 2 | 3;
  category: 'trading' | 'education' | 'tools' | 'books' | 'hardware';
  estimatedMonthlyRevenue: number;
  notes?: string;
}

/**
 * Affiliate link configuration
 */
export interface AffiliateLink {
  partnerId: string;
  url: string;
  text: string;
  context?: string; // Where it's used (e.g., "blog-post-iron-condor")
  createdAt?: Date;
}

/**
 * Affiliate registry — complete list of active partners
 */
export const AFFILIATE_REGISTRY: Record<string, AffiliatePartner> = {
  interactive_brokers: {
    id: 'interactive_brokers',
    name: 'Interactive Brokers',
    url: 'https://www.interactivebrokers.com/en/trading/affiliates?source=quantam101',
    commission: {
      type: 'cpa',
      value: 50,
      currency: 'USD',
      description: '$50 per account signup, plus 0.02% AUM for funded accounts',
    },
    tier: 1,
    category: 'trading',
    estimatedMonthlyRevenue: 225,
    notes: 'Premier institutional broker; focus on advanced options traders',
  },

  tastytrade: {
    id: 'tastytrade',
    name: 'Tastytrade',
    url: 'https://tastytrade.go2cloud.org/?sid=alreadyhere-llc',
    commission: {
      type: 'cpa',
      value: 50,
      currency: 'USD',
      description: '$35–$75 per funded account, variable by market',
    },
    tier: 1,
    category: 'trading',
    estimatedMonthlyRevenue: 150,
    notes: 'Options-focused; emphasize options education content',
  },

  thinkorswim: {
    id: 'thinkorswim',
    name: 'ThinkorSwim (TD Ameritrade)',
    url: 'https://www.tdameritrade.com/home.page?source=quantam101',
    commission: {
      type: 'cpa',
      value: 75,
      currency: 'USD',
      description: '$50–$150 per funded account (one-time)',
    },
    tier: 1,
    category: 'trading',
    estimatedMonthlyRevenue: 100,
    notes: 'Free platform; target beginners and paper trading tutorials',
  },

  alpaca: {
    id: 'alpaca',
    name: 'Alpaca Markets',
    url: 'https://alpaca.markets/?affiliate_id=profitenginev5',
    commission: {
      type: 'cpa',
      value: 50,
      currency: 'USD',
      description: '$50 per funded account + $25 for API usage',
    },
    tier: 1,
    category: 'trading',
    estimatedMonthlyRevenue: 75,
    notes: 'API-first; target algorithmic traders and Python automation',
  },

  polygon_io: {
    id: 'polygon_io',
    name: 'Polygon.io',
    url: 'https://polygon.io?utm_source=quantam101&utm_campaign=affiliate',
    commission: {
      type: 'percentage',
      value: 15,
      currency: 'USD',
      description: '10–30% lifetime revenue share (scales with volume)',
    },
    tier: 1,
    category: 'tools',
    estimatedMonthlyRevenue: 200,
    notes: 'Premium market data; high LTV customers',
  },

  tradingview: {
    id: 'tradingview',
    name: 'TradingView',
    url: 'https://tradingview.onelink.me/?ids=iOS,Android,Web&pid=profitengine&c=affiliate',
    commission: {
      type: 'cpa',
      value: 10,
      currency: 'USD',
      description: '$0.50–$2 per subscription (renewable)',
    },
    tier: 2,
    category: 'tools',
    estimatedMonthlyRevenue: 120,
    notes: '30M+ user platform; promote Pro features',
  },

  udemy: {
    id: 'udemy',
    name: 'Udemy',
    url: 'https://www.udemy.com/?utm_source=profitengine',
    commission: {
      type: 'percentage',
      value: 15,
      currency: 'USD',
      description: '15% on course sales ($10–$200 price point)',
    },
    tier: 2,
    category: 'education',
    estimatedMonthlyRevenue: 40,
    notes: 'Structured learning; complement owned content',
  },

  option_strat: {
    id: 'option_strat',
    name: 'OptionStrat',
    url: 'https://optionstrat.com/?ref=alreadyhere',
    commission: {
      type: 'cpa',
      value: 20,
      currency: 'USD',
      description: '$15–$25 per paid account',
    },
    tier: 2,
    category: 'tools',
    estimatedMonthlyRevenue: 35,
    notes: 'Options strategy visualizer; integrate in strategy posts',
  },

  investopedia: {
    id: 'investopedia',
    name: 'Investopedia',
    url: 'https://www.investopedia.com?utm_source=profitengine',
    commission: {
      type: 'cpa',
      value: 2,
      currency: 'USD',
      description: '$1–$5 per course signup',
    },
    tier: 2,
    category: 'education',
    estimatedMonthlyRevenue: 20,
    notes: 'Beginner content; use for foundational definitions',
  },

  amazon: {
    id: 'amazon',
    name: 'Amazon Associates',
    url: 'https://amazon.com',
    commission: {
      type: 'percentage',
      value: 4,
      currency: 'USD',
      description: '3–5% (books 3%, electronics 5%)',
    },
    tier: 3,
    category: 'books',
    estimatedMonthlyRevenue: 60,
    notes: 'Books, hardware, equipment. Tag: alreadyhere-20',
  },

  gumroad: {
    id: 'gumroad',
    name: 'Gumroad (Own Products)',
    url: 'https://gumroad.com/alreadyhere',
    commission: {
      type: 'percentage',
      value: 90,
      currency: 'USD',
      description: '100% (Gumroad takes 10% transaction fee)',
    },
    tier: 3,
    category: 'education',
    estimatedMonthlyRevenue: 350,
    notes: 'Own ebooks, playbooks, guides. Highest margin.',
  },

  blinkist: {
    id: 'blinkist',
    name: 'Blinkist',
    url: 'https://www.blinkist.com/?affiliates=profitengine',
    commission: {
      type: 'cpa',
      value: 3,
      currency: 'USD',
      description: '$2–$5 per subscription (renewable)',
    },
    tier: 3,
    category: 'education',
    estimatedMonthlyRevenue: 30,
    notes: 'Book summaries; psychology + business books',
  },
};

/**
 * Get a partner by ID
 */
export function getPartner(id: string): AffiliatePartner | undefined {
  return AFFILIATE_REGISTRY[id];
}

/**
 * Get all partners filtered by tier
 */
export function getPartnersByTier(tier: 1 | 2 | 3): AffiliatePartner[] {
  return Object.values(AFFILIATE_REGISTRY).filter((p) => p.tier === tier);
}

/**
 * Get all partners filtered by category
 */
export function getPartnersByCategory(
  category: 'trading' | 'education' | 'tools' | 'books' | 'hardware'
): AffiliatePartner[] {
  return Object.values(AFFILIATE_REGISTRY).filter((p) => p.category === category);
}

/**
 * Generate UTM-enriched affiliate link
 *
 * @param partnerId - Affiliate partner ID
 * @param source - Content source (e.g., 'blog-post-iron-condor', 'youtube-tutorial')
 * @returns Full URL with UTM parameters
 *
 * @example
 * const link = generateAffiliateLink('interactive_brokers', 'blog-post-iron-condor');
 * // => 'https://www.interactivebrokers.com/...?utm_source=profitengine-interactive_brokers&utm_medium=affiliate&utm_campaign=blog-post-iron-condor'
 */
export function generateAffiliateLink(partnerId: string, source = 'unknown'): string {
  const partner = getPartner(partnerId);
  if (!partner) {
    console.warn(`Unknown affiliate partner: ${partnerId}`);
    return '';
  }

  const url = new URL(partner.url);
  url.searchParams.set('utm_source', `profitengine-${partnerId}`);
  url.searchParams.set('utm_medium', 'affiliate');
  url.searchParams.set('utm_campaign', source);

  return url.toString();
}

/**
 * Inject affiliate links into content (Markdown)
 *
 * Replaces placeholders like [BROKER_LINK:interactive_brokers] with affiliate URLs
 *
 * @param content - Markdown content
 * @param source - Content source for tracking
 * @returns Content with links injected
 *
 * @example
 * const post = "Check out [BROKER_LINK:interactive_brokers] for advanced trading.";
 * const result = injectAffiliateLinks(post, 'blog-post-advanced');
 * // => "Check out https://www.interactivebrokers.com/...?utm_... for advanced trading."
 */
export function injectAffiliateLinks(content: string, source = 'unknown'): string {
  if (!content) return content;

  let result = content;

  // Replace [BROKER_LINK:partner_id] placeholders
  result = result.replace(/\[BROKER_LINK:(\w+)\]/g, (_match, partnerId) => {
    return generateAffiliateLink(partnerId, source);
  });

  // Replace [AFFILIATE:partner_id] placeholders
  result = result.replace(/\[AFFILIATE:(\w+)\]/g, (_match, partnerId) => {
    return generateAffiliateLink(partnerId, source);
  });

  // Replace [TOOL_LINK:partner_id] placeholders
  result = result.replace(/\[TOOL_LINK:(\w+)\]/g, (_match, partnerId) => {
    return generateAffiliateLink(partnerId, source);
  });

  return result;
}

/**
 * Calculate estimated monthly revenue
 *
 * @param partners - Array of partner IDs to sum
 * @returns Total estimated monthly revenue across all partners
 *
 * @example
 * const tier1Revenue = calculateMonthlyRevenue(['interactive_brokers', 'tastytrade']);
 * // => 375 (USD)
 */
export function calculateMonthlyRevenue(partners: string[]): number {
  return partners.reduce((total, id) => {
    const partner = getPartner(id);
    return total + (partner?.estimatedMonthlyRevenue || 0);
  }, 0);
}

/**
 * Calculate total affiliate revenue (all partners)
 */
export function calculateTotalMonthlyRevenue(): number {
  return Object.values(AFFILIATE_REGISTRY).reduce((total, partner) => {
    return total + partner.estimatedMonthlyRevenue;
  }, 0);
}

/**
 * Calculate annualized revenue
 */
export function calculateAnnualRevenue(monthlyTotal: number): number {
  return monthlyTotal * 12;
}

/**
 * Affiliate click tracking payload
 */
export interface AffiliateClickEvent {
  partnerId: string;
  source: string;
  timestamp: Date;
  userAgent?: string;
  referrer?: string;
  userId?: string;
}

/**
 * Track affiliate click (server-side)
 *
 * This should be called from an API route like /api/affiliate/track
 * to record conversion funnel data.
 */
export function trackAffiliateClick(event: AffiliateClickEvent): {
  success: boolean;
  message: string;
} {
  // In production, this would write to a database (Vercel KV, PostgreSQL, MongoDB)
  // For now, log to stdout for audit trails
  const logEntry = {
    type: 'affiliate_click',
    partner: event.partnerId,
    source: event.source,
    timestamp: event.timestamp.toISOString(),
    userAgent: event.userAgent || 'unknown',
    referrer: event.referrer || 'direct',
    userId: event.userId || 'anonymous',
  };

  // In production, write to database:
  // await db.collection('affiliate_events').insertOne(logEntry);
  // For now, log to console
  console.log('[AFFILIATE_CLICK]', JSON.stringify(logEntry));

  return {
    success: true,
    message: 'Click tracked',
  };
}

/**
 * Get revenue report for a period
 *
 * This would fetch from database in production.
 * For demo purposes, returns mock data.
 */
export async function getRevenueReport(
  startDate: Date,
  endDate: Date
): Promise<{
  period: { start: Date; end: Date };
  totalRevenue: number;
  byPartner: Record<string, { revenue: number; clicks: number; conversions: number }>;
  conversionRate: number;
}> {
  // In production, query database:
  // const events = await db.collection('affiliate_events')
  //   .find({ timestamp: { $gte: startDate, $lte: endDate } })
  //   .toArray();

  return {
    period: { start: startDate, end: endDate },
    totalRevenue: calculateTotalMonthlyRevenue(),
    byPartner: Object.keys(AFFILIATE_REGISTRY).reduce((acc, id) => {
      const partner = getPartner(id);
      acc[id] = {
        revenue: partner?.estimatedMonthlyRevenue || 0,
        clicks: 0, // Would be queried from database
        conversions: 0, // Would be queried from database
      };
      return acc;
    }, {} as Record<string, any>),
    conversionRate: 0.08, // 8% placeholder
  };
}

/**
 * FTC disclosure template
 */
export const FTC_DISCLOSURE = `
## Affiliate Disclosure

This post contains affiliate links. If you purchase or subscribe through
these links, I may earn a commission at no extra cost to you. I only
recommend products and services I've personally tested and believe in.

Your support through these links helps me continue creating free trading
education content.

---
`;

/**
 * Get FTC disclosure for a partner
 */
export function getPartnerDisclosure(partnerId: string): string {
  const partner = getPartner(partnerId);
  if (!partner) return FTC_DISCLOSURE;

  return `
### Using ${partner.name}

I use and recommend ${partner.name} because [specific reason].

If you sign up through my affiliate link, I'll earn a small commission
(at no extra cost to you), which helps fund this educational project.

[${partner.name}](${partner.url})

---
`;
}

/**
 * Batch inject multiple links
 *
 * Maps context/keywords to affiliate links for quick content enrichment
 *
 * @example
 * const enriched = batchInjectLinks(content, {
 *   'advanced options': 'interactive_brokers',
 *   'options strategy': 'option_strat',
 *   'technical analysis': 'tradingview'
 * });
 */
export function batchInjectLinks(
  content: string,
  linkMap: Record<string, string>,
  source = 'unknown'
): string {
  let result = content;

  Object.entries(linkMap).forEach(([keyword, partnerId]) => {
    const link = generateAffiliateLink(partnerId, source);
    // Create context-aware injection: wrap keyword with markdown link
    const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
    result = result.replace(regex, (match) => `[${match}](${link})`);
  });

  return result;
}

/**
 * Content affiliate mapping
 * Which posts use which affiliate links (for tracking and optimization)
 */
export const CONTENT_AFFILIATE_MAPPING: Record<
  string,
  { title: string; affiliates: string[]; expectedConversion?: number }
> = {
  'blog-getting-started': {
    title: 'Getting Started with Trading',
    affiliates: ['thinkorswim', 'investopedia'],
    expectedConversion: 0.03, // 3%
  },
  'blog-iron-condor': {
    title: 'Iron Condor Strategy Complete Guide',
    affiliates: ['interactive_brokers', 'tastytrade', 'option_strat'],
    expectedConversion: 0.08,
  },
  'blog-advanced-options': {
    title: 'Advanced Options Strategies',
    affiliates: ['interactive_brokers', 'polygon_io'],
    expectedConversion: 0.12,
  },
  'blog-backtesting': {
    title: 'Backtesting Your Strategies',
    affiliates: ['polygon_io', 'alpaca'],
    expectedConversion: 0.06,
  },
  'blog-setup-guide': {
    title: 'Complete Trading Setup Guide',
    affiliates: ['thinkorswim', 'tradingview', 'amazon'],
    expectedConversion: 0.04,
  },
};

/**
 * Get affiliate recommendations for a topic
 *
 * @example
 * const recommended = getRecommendedAffiliates('options trading');
 * // => [{ id: 'tastytrade', name: 'Tastytrade', ... }, ...]
 */
export function getRecommendedAffiliates(topic: string): AffiliatePartner[] {
  const topicLower = topic.toLowerCase();

  if (
    topicLower.includes('option') ||
    topicLower.includes('spread') ||
    topicLower.includes('strategy')
  ) {
    return [
      getPartner('interactive_brokers'),
      getPartner('tastytrade'),
      getPartner('option_strat'),
    ].filter(Boolean) as AffiliatePartner[];
  }

  if (
    topicLower.includes('algorithmic') ||
    topicLower.includes('python') ||
    topicLower.includes('bot')
  ) {
    return [
      getPartner('alpaca'),
      getPartner('polygon_io'),
      getPartner('gumroad'),
    ].filter(Boolean) as AffiliatePartner[];
  }

  if (topicLower.includes('beginner') || topicLower.includes('start')) {
    return [
      getPartner('thinkorswim'),
      getPartner('investopedia'),
      getPartner('udemy'),
    ].filter(Boolean) as AffiliatePartner[];
  }

  if (topicLower.includes('data') || topicLower.includes('analysis')) {
    return [
      getPartner('polygon_io'),
      getPartner('tradingview'),
      getPartner('interactive_brokers'),
    ].filter(Boolean) as AffiliatePartner[];
  }

  // Default: top 3 Tier 1 partners
  return Object.values(AFFILIATE_REGISTRY)
    .filter((p) => p.tier === 1)
    .slice(0, 3);
}

/**
 * Generate a complete affiliate resource page
 */
export function generateResourcePageMarkdown(): string {
  const tier1 = getPartnersByTier(1);
  const tier2 = getPartnersByTier(2);
  const tier3 = getPartnersByTier(3);

  const markdown = `
# Recommended Affiliate Resources

These are tools, platforms, and services I use and recommend.
If you purchase through my affiliate links, I earn a small commission at no cost to you.

${FTC_DISCLOSURE}

## Tier 1: Trading Platforms (Commission-based)

${tier1.map((p) => `### ${p.name}\n**Commission**: ${p.commission.description}\n[Visit ${p.name}](${p.url})\n`).join('\n')}

## Tier 2: Educational & Tools

${tier2.map((p) => `### ${p.name}\n**Commission**: ${p.commission.description}\n[Visit ${p.name}](${p.url})\n`).join('\n')}

## Tier 3: Books, Guides & Hardware

${tier3.map((p) => `### ${p.name}\n**Commission**: ${p.commission.description}\n[Visit ${p.name}](${p.url})\n`).join('\n')}

---

**Total Estimated Monthly Revenue**: $${calculateTotalMonthlyRevenue()}
**Annualized**: $${calculateAnnualRevenue(calculateTotalMonthlyRevenue())}
`;

  return markdown;
}

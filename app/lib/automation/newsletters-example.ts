/**
 * NEWSLETTER AUTOMATION EXAMPLES
 *
 * Ready-to-use examples for common newsletter publishing scenarios
 */

import {
  NewsletterBatchPublisher,
  NewsletterContent,
  BatchPublishResult,
  BeehiivPublisher,
  SubstackPublisher,
  ConvertKitPublisher,
  MediumPublisher,
  DevToPublisher,
  HashnodePublisher,
} from './newsletters';

// ============================================================================
// EXAMPLE 1: Weekly Market Analysis Newsletter
// ============================================================================

export async function publishWeeklyMarketAnalysis(): Promise<BatchPublishResult> {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
    {
      platform: 'substack' as const,
      enabled: !!process.env.SUBSTACK_API_TOKEN,
      apiKey: process.env.SUBSTACK_API_TOKEN || '',
    },
    {
      platform: 'medium' as const,
      enabled: !!process.env.MEDIUM_API_TOKEN,
      apiKey: process.env.MEDIUM_API_TOKEN || '',
    },
  ];

  const publisher = new NewsletterBatchPublisher(config);

  const content: NewsletterContent = {
    title: 'Weekly Market Analysis - Week of June 21, 2024',
    subtitle: 'Key market movements, trading opportunities, and analysis',
    body: `
# Market Overview

This week presented significant trading opportunities across multiple asset classes. Here's your comprehensive market analysis.

## Stock Market Summary

The S&P 500 rallied **2.3%** this week on better-than-expected inflation data. Key drivers:

- **Inflation Data** — CPI came in at 2.9% YoY (down from 3.2%)
- **Fed Expectations** — Market now pricing in fewer rate hikes
- **Tech Rally** — Nasdaq 100 up 3.1% on AI enthusiasm

### Best Performers
1. Nvidia (NVDA) — +5.2%
2. Microsoft (MSFT) — +3.8%
3. Tesla (TSLA) — +2.1%

### Worst Performers
1. Financial Services (XLF) — -1.2%
2. Energy (XLE) — -0.8%

## Cryptocurrency Market

Bitcoin surged **6.8%** to $42,500 on crypto-friendly regulatory news. Ethereum followed with a **5.2%** gain.

**Key Events:**
- Bitcoin ETF approval discussions gaining momentum
- Ethereum Shanghai upgrade anniversary
- Altcoin recovery with 30%+ gains in top performers

## Commodities & Forex

- **Gold** — Slight pullback on stronger USD
- **Oil** — Up 2.1% on supply concerns
- **USD Index** — Strengthened 1.3% against basket

## Trading Opportunities

### Short-term Plays (1-5 days)
1. **NVDA Call Spreads** — Expecting continued volatility post-earnings
2. **BTC/USD Long** — Technical support holding at $41,000
3. **Gold Puts** — Look for reversal after oversold conditions

### Medium-term Positions (1-3 weeks)
1. **QQQ Long** — Tech rally likely to continue
2. **SPY Call Calendar Spreads** — IV crush opportunity
3. **ETH Accumulation** — Building position on dips

## Risk Management

- **Portfolio Rebalancing** — Consider taking profits on winners
- **Stop Losses** — Set at key support levels
- **Diversification** — Don't concentrate in any single sector

## Next Week's Events

- **Fed Speaker Schedule** — Monitor for new guidance
- **Earnings Reports** — Key tech companies reporting
- **Economic Data** — Weekly jobless claims and retail sales
- **Crypto News** — Watch for regulatory updates

## Action Items

1. Review your portfolio allocation for sector concentration
2. Set profit targets on positions that are up 15%+ this week
3. Monitor the $42,000 support level on Bitcoin
4. Consider rotating out of overvalued growth stocks
5. Plan entries for lagging sectors if market continues higher

## Key Takeaways

- Market sentiment is shifting from defensive to growth
- Inflation improvement is the primary catalyst
- Tech leadership likely to continue
- Risk/reward now more balanced than in May

---

**Disclaimer:** This analysis is for educational purposes only. Always conduct your own research and consult with a financial advisor before making investment decisions.

**Get Your Personal Analysis:** Upgrade to Premium for customized trading recommendations tailored to your portfolio.
`,
    summary:
      'Weekly market analysis covering stocks, crypto, commodities and actionable trading opportunities for the week ahead.',
    tags: ['trading', 'markets', 'analysis', 'weekly', 'stocks', 'crypto'],
    featuredImage:
      'https://images.unsplash.com/photo-1611432579715-ae288e91aff0?w=1200&h=630&fit=crop',
    ctaText: 'View Interactive Charts',
    ctaLink: 'https://profitengine.alreadyherellc.com/weekly-analysis',
  };

  return publisher.publishToAll(content);
}

// ============================================================================
// EXAMPLE 2: Daily Trading Alert
// ============================================================================

export async function publishDailyTradingAlert(
  symbol: string,
  signal: 'BUY' | 'SELL' | 'HOLD',
  price: number,
  target: number,
  reason: string
): Promise<BatchPublishResult> {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
    {
      platform: 'devto' as const,
      enabled: !!process.env.DEVTO_API_KEY,
      apiKey: process.env.DEVTO_API_KEY || '',
    },
  ];

  const publisher = new NewsletterBatchPublisher(config);

  const content: NewsletterContent = {
    title: `${signal} Alert: ${symbol} at $${price}`,
    subtitle: `Target: $${target} | Reason: ${reason}`,
    body: `
# Trading Alert: ${symbol}

**Signal:** ${signal}
**Current Price:** $${price}
**Target Price:** $${target}
**Potential Move:** ${(((target - price) / price) * 100).toFixed(2)}%

## Analysis

${reason}

### Setup Details

- **Entry Point:** Current price $${price}
- **First Target:** $${(price + (target - price) * 0.5).toFixed(2)}
- **Final Target:** $${target}
- **Stop Loss:** $${(price - (target - price) * 0.5).toFixed(2)}

### Risk/Reward

- **Risk:** ${(price - (price - (target - price) * 0.5)).toFixed(2)} per share
- **Reward:** ${(target - price).toFixed(2)} per share
- **Ratio:** 1:${((target - price) / (price - (price - (target - price) * 0.5))).toFixed(2)}

## Action

1. Set alerts for target levels
2. Size position according to risk tolerance
3. Monitor for breakout confirmation
4. Take profits at first target

---

**Risk Disclaimer:** Past performance is not indicative of future results. Always use stop losses and proper risk management.
`,
    summary: `${signal} signal for ${symbol} at $${price} with target of $${target}`,
    tags: ['trading', 'alert', 'signals', symbol.toLowerCase()],
    ctaText: 'View Live Charts',
    ctaLink: `https://profitengine.alreadyherellc.com/charts/${symbol}`,
  };

  return publisher.publishToAll(content);
}

// ============================================================================
// EXAMPLE 3: Monthly Educational Content
// ============================================================================

export async function publishMonthlyEducation(topic: string, content: string): Promise<BatchPublishResult> {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
    {
      platform: 'devto' as const,
      enabled: !!process.env.DEVTO_API_KEY,
      apiKey: process.env.DEVTO_API_KEY || '',
    },
    {
      platform: 'hashnode' as const,
      enabled: !!process.env.HASHNODE_API_KEY,
      apiKey: process.env.HASHNODE_API_KEY || '',
    },
  ];

  const publisher = new NewsletterBatchPublisher(config);

  const newsContent: NewsletterContent = {
    title: `Trading 101: ${topic}`,
    subtitle: 'Educational resource for traders of all levels',
    body: content,
    summary: `Learn about ${topic} in this comprehensive guide for traders`,
    tags: ['education', 'trading', 'tutorial', 'beginner-friendly'],
    ctaText: 'Enroll in Full Course',
    ctaLink: 'https://profitengine.alreadyherellc.com/education',
  };

  return publisher.publishToAll(newsContent);
}

// ============================================================================
// EXAMPLE 4: Community Digest
// ============================================================================

export async function publishCommunityDigest(
  weekNumber: number,
  topPosts: Array<{ title: string; url: string; author: string }>
): Promise<BatchPublishResult> {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
  ];

  const publisher = new NewsletterBatchPublisher(config);

  const postsList = topPosts
    .map((post, idx) => `${idx + 1}. [${post.title}](${post.url}) — by ${post.author}`)
    .join('\n');

  const content: NewsletterContent = {
    title: `Community Digest - Week ${weekNumber}`,
    subtitle: 'Top posts, discussions, and insights from our community',
    body: `
# This Week in ProfitEngine

## Top Community Posts

${postsList}

## Trending Discussions

- Options trading strategies in bear markets
- Portfolio rebalancing during inflation
- Risk management best practices

## Community Stats

- **New Members:** 42
- **Posts This Week:** 156
- **Discussions:** 89
- **Helpful Responses:** 412

## Upcoming Events

- **Weekly Live Trading Session** — Friday 3 PM ET
- **Q&A with Professional Traders** — Saturday 2 PM ET
- **Market Analysis Workshop** — Sunday 4 PM ET

## How to Participate

Have a great post or discussion to share? Tag your content with #CommunityDigest and it may be featured in next week's digest!

---

**Join our community** and connect with thousands of traders sharing insights and strategies.
`,
    summary: 'Weekly community digest featuring top posts and discussions',
    tags: ['community', 'digest', 'discussion', 'weekly'],
    ctaText: 'Join Community',
    ctaLink: 'https://profitengine.alreadyherellc.com/community',
  };

  return publisher.publishToAll(content);
}

// ============================================================================
// EXAMPLE 5: Scheduled Batch Publishing
// ============================================================================

export async function publishScheduledNewsletter(
  scheduleTime: Date,
  platforms: string[]
): Promise<BatchPublishResult> {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
      scheduledTime: scheduleTime,
    },
    {
      platform: 'substack' as const,
      enabled: !!process.env.SUBSTACK_API_TOKEN,
      apiKey: process.env.SUBSTACK_API_TOKEN || '',
      scheduledTime: scheduleTime,
    },
    {
      platform: 'convertkit' as const,
      enabled: !!process.env.CONVERTKIT_API_KEY,
      apiKey: process.env.CONVERTKIT_API_KEY || '',
      scheduledTime: scheduleTime,
    },
  ].filter((c) => platforms.includes(c.platform));

  const publisher = new NewsletterBatchPublisher(config);

  const content: NewsletterContent = {
    title: 'Scheduled Newsletter',
    body: 'This newsletter is scheduled for automatic publishing',
    publishedAt: scheduleTime,
  };

  return publisher.publishToSelected(content, platforms);
}

// ============================================================================
// EXAMPLE 6: Get Metrics Across All Platforms
// ============================================================================

export async function getNewsletterMetrics() {
  const config = [
    {
      platform: 'beehiiv' as const,
      enabled: !!process.env.BEEHIIV_API_KEY,
      apiKey: process.env.BEEHIIV_API_KEY || '',
    },
    {
      platform: 'substack' as const,
      enabled: !!process.env.SUBSTACK_API_TOKEN,
      apiKey: process.env.SUBSTACK_API_TOKEN || '',
    },
    {
      platform: 'convertkit' as const,
      enabled: !!process.env.CONVERTKIT_API_KEY,
      apiKey: process.env.CONVERTKIT_API_KEY || '',
    },
    {
      platform: 'medium' as const,
      enabled: !!process.env.MEDIUM_API_TOKEN,
      apiKey: process.env.MEDIUM_API_TOKEN || '',
    },
    {
      platform: 'devto' as const,
      enabled: !!process.env.DEVTO_API_KEY,
      apiKey: process.env.DEVTO_API_KEY || '',
    },
    {
      platform: 'hashnode' as const,
      enabled: !!process.env.HASHNODE_API_KEY,
      apiKey: process.env.HASHNODE_API_KEY || '',
    },
  ];

  const publisher = new NewsletterBatchPublisher(config);
  return publisher.getAggregateMetrics();
}

// ============================================================================
// EXAMPLE 7: Single Platform Publishing
// ============================================================================

export async function publishToBeehiivOnly(content: NewsletterContent) {
  const beehiiv = new BeehiivPublisher(process.env.BEEHIIV_API_KEY || '');
  return beehiiv.publish(content);
}

export async function publishToMediumOnly(content: NewsletterContent) {
  const medium = new MediumPublisher(
    process.env.MEDIUM_API_TOKEN || '',
    process.env.MEDIUM_AUTHOR_ID || ''
  );
  return medium.publish(content);
}

// ============================================================================
// EXAMPLE 8: Error Handling
// ============================================================================

export async function publishWithErrorHandling(content: NewsletterContent) {
  try {
    const config = [
      {
        platform: 'beehiiv' as const,
        enabled: !!process.env.BEEHIIV_API_KEY,
        apiKey: process.env.BEEHIIV_API_KEY || '',
      },
      {
        platform: 'substack' as const,
        enabled: !!process.env.SUBSTACK_API_TOKEN,
        apiKey: process.env.SUBSTACK_API_TOKEN || '',
      },
    ];

    const publisher = new NewsletterBatchPublisher(config, 5); // 5 retry attempts

    const result = await publisher.publishToAll(content);

    // Log results
    console.log(`Published to ${result.successful.length} platforms`);

    if (result.failed.length > 0) {
      console.warn(`Failed on ${result.failed.length} platforms:`);
      result.failed.forEach((r) => {
        console.warn(`- ${r.platform}: ${r.error}`);
      });
    }

    // Log metrics
    result.metrics.forEach((m) => {
      if (m.totalSubscribers) {
        console.log(`${m.platform}: ${m.totalSubscribers} subscribers`);
      }
    });

    return result;
  } catch (error) {
    console.error('Newsletter publishing failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 9: Dry Run Testing
// ============================================================================

export async function testNewsletterPublishing(content: NewsletterContent) {
  // This would be called from the API endpoint with dryRun: true
  // to test the newsletter without actually publishing

  console.log('DRY RUN MODE - No platforms will be published to');
  console.log(`Title: ${content.title}`);
  console.log(`Tags: ${content.tags?.join(', ')}`);
  console.log(`Body length: ${content.body.length} characters`);

  return {
    success: true,
    dryRun: true,
    message: 'Dry run completed successfully. Newsletter is ready to publish.',
  };
}

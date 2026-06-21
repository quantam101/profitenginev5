/**
 * AFFILIATE AUTOMATION — USAGE EXAMPLES
 *
 * Real-world examples and integration patterns for the affiliate system
 */

import {
  AffiliateProduct,
  AffiliateLink,
  DashboardMetrics,
  createAmazonLink,
  createClickBankLink,
  createCJLink,
  createShareASaleLink,
  createMultiNetworkLinks,
  trackAffiliateClick,
  trackConversion,
  saveLink,
  getAllLinks,
  getDashboardMetrics,
  getNicheMetrics,
  generateCommissionReport,
  optimizeLink,
  batchCreateLinks,
  exportLinksAsCSV,
} from './affiliate-enhanced';

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 1: Create Affiliate Links for Products
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create links for trading-related products across all networks
 */
export async function example_createTradingProductLinks() {
  const products: AffiliateProduct[] = [
    {
      id: 'thinkorswim-platform',
      title: 'thinkorswim® Trading Platform',
      description: 'Free trading platform by TD Ameritrade with advanced tools',
      price: 0,
      category: 'trading-software',
      niche: 'trading',
      vendor: 'TD Ameritrade',
      rating: 4.7,
      reviews: 2340,
      image: 'https://example.com/thinkorswim.jpg',
    },
    {
      id: 'interactive-brokers',
      title: 'Interactive Brokers TWS',
      description: 'Professional trading platform for active traders',
      price: 0,
      category: 'trading-software',
      niche: 'trading',
      vendor: 'Interactive Brokers',
      rating: 4.6,
      reviews: 3100,
    },
    {
      id: 'polygon-market-data',
      title: 'Polygon.io Market Data API',
      description: 'Enterprise-grade market data and stock API',
      price: 299,
      category: 'data-api',
      niche: 'trading',
      vendor: 'Polygon.io',
      rating: 4.8,
      reviews: 450,
    },
  ];

  // Create links for each product
  const allLinks: AffiliateLink[] = [];

  for (const product of products) {
    const links = await createMultiNetworkLinks(product);
    allLinks.push(...links);

    // Save to persistent storage
    for (const link of links) {
      await saveLink(link);
    }

    console.log(`✓ Created ${links.length} links for ${product.title}`);
  }

  return allLinks;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 2: Track User Interactions
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Track user clicking an affiliate link from blog post
 */
export async function example_trackBlogPostClick(
  linkId: string,
  userId: string,
  postSlug: string
) {
  // Record the click
  const event = await trackAffiliateClick(linkId, `blog/${postSlug}`, userId);

  console.log(`✓ Tracked click from ${postSlug}`);
  console.log(`  Event ID: ${event.id}`);
  console.log(`  User: ${userId}`);

  return event;
}

/**
 * Track user purchasing through affiliate link
 */
export async function example_trackConversionAndCommission(
  linkId: string,
  orderData: {
    orderId: string;
    amount: number;
    currency: string;
    productName: string;
  },
  userId?: string
) {
  // Record the conversion with commission value
  const event = await trackConversion(linkId, orderData.amount, orderData.orderId, {
    currency: orderData.currency,
    productName: orderData.productName,
    userId,
  });

  console.log(`✓ Tracked conversion`);
  console.log(`  Order: ${orderData.orderId}`);
  console.log(`  Amount: $${orderData.amount}`);
  console.log(`  Event: ${event.id}`);

  return event;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 3: Analytics & Reporting
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get monthly performance dashboard
 */
export async function example_getMonthlyDashboard(year: number, month: number) {
  const startDate = new Date(year, month - 1, 1);
  const endDate = new Date(year, month, 0);

  const metrics = await getDashboardMetrics(startDate, endDate);

  console.log(`\n═══════════════════════════════════════════════════════════`);
  console.log(`AFFILIATE DASHBOARD — ${startDate.toLocaleDateString()}`);
  console.log(`═══════════════════════════════════════════════════════════\n`);

  console.log(`SUMMARY`);
  console.log(`  Total Links: ${metrics.totalLinks}`);
  console.log(`  Active Links: ${metrics.activeLinks}`);
  console.log(`  Total Clicks: ${metrics.totalClicks}`);
  console.log(`  Total Conversions: ${metrics.totalConversions}`);
  console.log(`  Conversion Rate: ${(metrics.conversionRate * 100).toFixed(2)}%`);
  console.log(`  Estimated Revenue: $${metrics.estimatedRevenue.toFixed(2)}\n`);

  console.log(`BY NETWORK`);
  Object.entries(metrics.byNetwork).forEach(([network, stats]) => {
    console.log(`  ${network.toUpperCase()}`);
    console.log(`    Links: ${stats.links} | Clicks: ${stats.clicks} | Conversions: ${stats.conversions}`);
    console.log(`    Revenue: $${stats.revenue.toFixed(2)}`);
  });

  console.log(`\nBY NICHE`);
  Object.entries(metrics.byNiche).forEach(([niche, stats]) => {
    console.log(`  ${niche.toUpperCase()}`);
    console.log(`    Links: ${stats.links} | Clicks: ${stats.clicks} | Conversions: ${stats.conversions}`);
    console.log(`    Revenue: $${stats.revenue.toFixed(2)}`);
  });

  console.log(`\nTOP PRODUCTS`);
  metrics.topProducts.slice(0, 5).forEach((product, idx) => {
    console.log(`  ${idx + 1}. ${product.title}`);
    console.log(`     Clicks: ${product.clicks} | Conversions: ${product.conversions} | Revenue: $${product.revenue.toFixed(2)}`);
  });

  console.log(`\n═══════════════════════════════════════════════════════════\n`);

  return metrics;
}

/**
 * Get niche-specific metrics and performance
 */
export async function example_getNichePerformance(niche: string) {
  const metrics = await getNicheMetrics(niche);

  console.log(`\n${niche.toUpperCase()} NICHE PERFORMANCE`);
  console.log(`Links: ${metrics.linkCount}`);
  console.log(`Clicks: ${metrics.clicks}`);
  console.log(`Conversions: ${metrics.conversions}`);
  console.log(`Revenue: $${metrics.revenue.toFixed(2)}`);
  console.log(`Conversion Rate: ${(metrics.conversions / metrics.clicks * 100).toFixed(2)}%\n`);

  console.log(`TOP PERFORMING LINKS:`);
  metrics.topLinks.forEach((link, idx) => {
    console.log(`  ${idx + 1}. ${link.id}`);
    console.log(`     Conversions: ${link.conversions}`);
  });

  return metrics;
}

/**
 * Generate commission report for accounting/payout
 */
export async function example_generateMonthlyCommissionReport(
  year: number,
  month: number
) {
  const startDate = new Date(year, month - 1, 1);
  const endDate = new Date(year, month, 0);

  const report = await generateCommissionReport(startDate, endDate);

  console.log(`\nCOMMISSION REPORT — ${startDate.toLocaleDateString()}`);
  console.log(`Total Commissions: $${report.totalCommissions.toFixed(2)}`);
  console.log(`  Pending: $${report.pendingCommissions.toFixed(2)}`);
  console.log(`  Approved: $${report.approvedCommissions.toFixed(2)}`);
  console.log(`  Paid: $${report.paidCommissions.toFixed(2)}\n`);

  console.log(`BY NETWORK:`);
  Object.entries(report.byNetwork).forEach(([network, amount]) => {
    console.log(`  ${network}: $${amount.toFixed(2)}`);
  });

  return report;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 4: Optimization & A/B Testing
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get optimization suggestions for underperforming link
 */
export async function example_optimizeLink(linkId: string) {
  const result = await optimizeLink(linkId);

  console.log(`\nOPTIMIZATION REPORT — ${linkId}`);

  if (result.suggestions.length === 0) {
    console.log('No issues detected. Link is performing well.');
  } else {
    console.log('SUGGESTIONS:');
    result.suggestions.forEach((suggestion) => {
      console.log(`  • ${suggestion}`);
    });
  }

  console.log('\nRECOMMENDATIONS:');
  Object.entries(result.recommendations).forEach(([key, value]) => {
    if (value === true) {
      console.log(`  ✓ ${key}`);
    }
  });

  return result;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 5: Batch Operations
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Bulk create links for a niche category
 */
export async function example_bulkCreateEducationLinks() {
  const educationProducts: AffiliateProduct[] = [
    {
      id: 'udemy-options-course',
      title: 'The Complete Options Trading Course',
      description: 'Learn options trading from beginner to advanced',
      price: 99.99,
      category: 'online-course',
      niche: 'education',
      vendor: 'Udemy',
      rating: 4.6,
      reviews: 5200,
    },
    {
      id: 'coursera-finance-cert',
      title: 'Finance for Everyone: Smart Investing Specialization',
      description: 'Comprehensive finance and investing specialization',
      price: 39.99,
      category: 'online-course',
      niche: 'education',
      vendor: 'Coursera',
      rating: 4.7,
      reviews: 3400,
    },
    {
      id: 'investopedia-tutorial',
      title: 'Investopedia Academy: Trading for Beginners',
      description: 'Step-by-step beginner trading guide',
      price: 99,
      category: 'online-course',
      niche: 'education',
      vendor: 'Investopedia',
      rating: 4.5,
      reviews: 2100,
    },
  ];

  console.log(`Creating ${educationProducts.length} education affiliate links...\n`);

  const links = await batchCreateLinks(educationProducts);

  console.log(`✓ Successfully created ${links.length} affiliate links`);
  console.log(`  Amazon: ${links.filter((l) => l.network === 'amazon').length}`);
  console.log(`  ClickBank: ${links.filter((l) => l.network === 'clickbank').length}`);
  console.log(`  CJ: ${links.filter((l) => l.network === 'cj').length}`);
  console.log(`  ShareASale: ${links.filter((l) => l.network === 'shareasale').length}\n`);

  return links;
}

/**
 * Export links for data analysis or sharing
 */
export async function example_exportLinksForAnalysis(niche: string) {
  const csv = await exportLinksAsCSV(niche);

  console.log(`✓ Exported ${niche} links\n`);
  console.log(csv);

  // In production: save to file or send via email
  // await fs.writeFile(`affiliates-${niche}.csv`, csv);

  return csv;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 6: Content Integration Patterns
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Auto-inject affiliate links into blog post
 */
export async function example_enrichBlogPostWithAffiliates(postContent: string) {
  // This would extract product mentions from content
  // For demo, we'll use hardcoded products
  const products: AffiliateProduct[] = [
    {
      id: 'polygon-io',
      title: 'Polygon.io Market Data',
      description: 'Real-time market data API',
      price: 299,
      category: 'data-api',
      niche: 'trading',
      externalId: 'polygon',
    },
  ];

  const enrichedContent: {
    original: string;
    withLinks: string;
    affiliateLinks: AffiliateLink[];
  } = {
    original: postContent,
    withLinks: postContent,
    affiliateLinks: [],
  };

  for (const product of products) {
    const links = await createMultiNetworkLinks(product);
    enrichedContent.affiliateLinks.push(...links);

    // Simple pattern replacement: [PRODUCT:polygon-io] → affiliate link
    const pattern = new RegExp(`\\[PRODUCT:${product.id}\\]`, 'g');
    enrichedContent.withLinks = enrichedContent.withLinks.replace(
      pattern,
      links[0].affiliateUrl || product.id
    );
  }

  return enrichedContent;
}

/**
 * Generate affiliate link card for product mention
 */
export function example_createAffiliateLinkCard(link: AffiliateLink) {
  return `
<!-- Affiliate Link Card -->
<div class="affiliate-card">
  <a href="${link.affiliateUrl}" target="_blank" rel="noopener noreferrer">
    <div class="affiliate-badge">${link.network.toUpperCase()}</div>
    <h3>View on ${link.network}</h3>
    <p class="disclosure">Affiliate link - we may earn a small commission</p>
  </a>
</div>
  `;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 7: Real-time Conversion Funnel Tracking
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Simulate user journey with affiliate tracking
 */
export async function example_trackUserJourney(userId: string) {
  console.log(`\nTracking user journey for ${userId}\n`);

  // Step 1: User reads blog post
  const product = {
    id: 'trading-platform-comparison',
    title: 'Best Trading Platforms 2026',
    description: 'Comprehensive comparison guide',
    price: 0,
    category: 'guides',
    niche: 'trading',
  };

  const links = await createMultiNetworkLinks(product);
  const interactiveLink = links[0];

  console.log(`1. Blog post mentions ${interactiveLink.network}`);

  // Step 2: User clicks affiliate link
  const clickEvent = await trackAffiliateClick(
    interactiveLink.id,
    'blog/best-trading-platforms',
    userId
  );

  console.log(`2. User clicks affiliate link`);
  console.log(`   Event: ${clickEvent.id}`);

  // Step 3: User signs up and funds account
  const conversionEvent = await trackConversion(
    interactiveLink.id,
    100, // $100 signup bonus value
    `order-${Date.now()}`,
    {
      accountLevel: 'standard',
      fundedAmount: 5000,
      conversionSource: 'blog',
    }
  );

  console.log(`3. User converts: $${conversionEvent.value} commission earned`);
  console.log(`   Event: ${conversionEvent.id}\n`);

  return {
    userId,
    linkId: interactiveLink.id,
    clickEvent,
    conversionEvent,
    estimatedCommission: conversionEvent.value,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 8: Webhook Handler Pattern (for external services)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Handle conversion webhook from affiliate network
 * (Stripe, Shopify, custom checkout, etc)
 */
export async function example_handleConversionWebhook(webhookData: {
  orderId: string;
  affiliateCode: string;
  amount: number;
  timestamp: string;
}) {
  console.log(`\nProcessing affiliate conversion webhook:`);
  console.log(`  Order: ${webhookData.orderId}`);
  console.log(`  Affiliate: ${webhookData.affiliateCode}`);
  console.log(`  Amount: $${webhookData.amount}\n`);

  // Find affiliate link by code
  const links = await getAllLinks();
  const link = links.find((l) => l.affiliateCode === webhookData.affiliateCode);

  if (!link) {
    console.log('  ⚠ Affiliate code not found');
    return null;
  }

  // Record conversion
  const event = await trackConversion(
    link.id,
    webhookData.amount,
    webhookData.orderId,
    {
      source: 'webhook',
      timestamp: webhookData.timestamp,
    }
  );

  console.log(`  ✓ Conversion recorded: ${event.id}`);

  return event;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 9: Scheduled Report Generation
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Generate weekly affiliate performance summary (for email digest)
 */
export async function example_generateWeeklyReport(weekStartDate: Date) {
  const weekEndDate = new Date(weekStartDate);
  weekEndDate.setDate(weekEndDate.getDate() + 7);

  const metrics = await getDashboardMetrics(weekStartDate, weekEndDate);
  const commission = await generateCommissionReport(weekStartDate, weekEndDate);

  const report = {
    period: {
      start: weekStartDate.toLocaleDateString(),
      end: weekEndDate.toLocaleDateString(),
    },
    summary: {
      totalClicks: metrics.totalClicks,
      totalConversions: metrics.totalConversions,
      conversionRate: `${(metrics.conversionRate * 100).toFixed(2)}%`,
      weeklyRevenue: `$${metrics.estimatedRevenue.toFixed(2)}`,
      pendingCommissions: `$${commission.pendingCommissions.toFixed(2)}`,
    },
    topPerformers: metrics.topProducts.slice(0, 3),
    niches: Object.entries(metrics.byNiche).map(([name, stats]) => ({
      name,
      clicks: stats.clicks,
      conversions: stats.conversions,
    })),
  };

  console.log('\nWEEKLY AFFILIATE REPORT');
  console.log(JSON.stringify(report, null, 2));

  return report;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXAMPLE 10: Command-Line Usage
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * CLI command to quickly create and share affiliate links
 *
 * Usage:
 *   npx ts-node -O '{"module":"esnext"}' scripts/create-links.ts
 */
export async function example_cliCreateLinks() {
  console.log('Creating affiliate links for featured products...\n');

  const products: AffiliateProduct[] = [
    {
      id: 'best-brokers-guide',
      title: 'Complete Guide to Choosing a Broker',
      description: 'Everything you need to know',
      price: 0,
      category: 'guide',
      niche: 'trading',
    },
  ];

  const links = await batchCreateLinks(products);

  console.log(`Created ${links.length} links:\n`);

  links.forEach((link) => {
    console.log(`${link.network.toUpperCase()}`);
    console.log(`  Link: ${link.affiliateUrl}`);
    console.log(`  ID: ${link.id}\n`);
  });

  // Output for sharing
  console.log('Copy these URLs:');
  links.forEach((link) => {
    console.log(`${link.network}: ${link.affiliateUrl}`);
  });
}

const affiliateExamples = {
  example_createTradingProductLinks,
  example_trackBlogPostClick,
  example_trackConversionAndCommission,
  example_getMonthlyDashboard,
  example_getNichePerformance,
  example_generateMonthlyCommissionReport,
  example_optimizeLink,
  example_bulkCreateEducationLinks,
  example_exportLinksForAnalysis,
  example_enrichBlogPostWithAffiliates,
  example_createAffiliateLinkCard,
  example_trackUserJourney,
  example_handleConversionWebhook,
  example_generateWeeklyReport,
  example_cliCreateLinks,
};

export default affiliateExamples;

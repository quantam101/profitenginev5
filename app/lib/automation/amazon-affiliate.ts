/**
 * AMAZON ASSOCIATES AFFILIATE AUTOMATION
 *
 * Automates Amazon Associates affiliate link management:
 * - Product search and link generation
 * - Niche-targeted product recommendations
 * - Link click/conversion tracking
 * - Commission tracking and reporting
 * - Dynamic link optimization
 * - Batch affiliate link creation
 *
 * Environment Requirements:
 * - AMAZON_ASSOCIATES_TAG: Your Amazon Associates tag (e.g., 'alreadyhere-20')
 * - AMAZON_PA_API_KEY: Product Advertising API key
 * - AMAZON_PA_SECRET_KEY: Product Advertising API secret
 * - AMAZON_PARTNER_TYPE: 'associates' | 'sponsored-ads' (default: 'associates')
 * - AFFILIATE_COMMISSION_RATE: Commission percentage (0.0-0.08, default: 0.04)
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES & INTERFACES
// ═══════════════════════════════════════════════════════════════════════════════

export interface Product {
  asin: string;
  title: string;
  price: number;
  rating: number;
  reviewCount: number;
  imageUrl?: string;
  category: string;
  keywords: string[];
  buyUrl: string;
}

export interface AffiliateLink {
  id: string;
  asin: string;
  productTitle: string;
  associatesTag: string;
  affiliateUrl: string;
  shortUrl?: string;
  niche: string;
  createdAt: string;
  updatedAt: string;
  clicks: number;
  conversions: number;
  revenue: number;
  status: 'active' | 'inactive' | 'pending' | 'expired';
}

export interface LinkTrackingEvent {
  linkId: string;
  eventType: 'click' | 'conversion' | 'impression';
  timestamp: string;
  referer?: string;
  userId?: string;
  amount?: number;
}

export interface CommissionReport {
  period: string;
  startDate: string;
  endDate: string;
  totalLinks: number;
  activeLinks: number;
  totalClicks: number;
  totalConversions: number;
  conversionRate: number;
  estimatedCommission: number;
  topProducts: Array<{
    asin: string;
    title: string;
    clicks: number;
    conversions: number;
    revenue: number;
  }>;
  niches: Record<string, {
    linkCount: number;
    clicks: number;
    conversions: number;
    revenue: number;
  }>;
}

export interface ProductSearchOptions {
  keywords: string[];
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  minRating?: number;
  maxResults?: number;
  sortBy?: 'relevance' | 'price' | 'rating' | 'reviews';
}

export interface LinkOptimizationResult {
  linkId: string;
  originalUrl: string;
  optimizedUrl: string;
  recommendation: string;
  estimatedImpactPercent: number;
  appliedChanges: string[];
}

// ═══════════════════════════════════════════════════════════════════════════════
// AMAZON ASSOCIATES API CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

class AmazonAssociatesClient {
  private associatesTag: string;
  private partnerType: string;
  private baseUrl = 'https://webservices.amazon.com/onca/xml';

  constructor(
    associatesTag?: string,
    partnerType?: string
  ) {
    this.associatesTag = associatesTag || process.env.AMAZON_ASSOCIATES_TAG || '';
    this.partnerType = partnerType || process.env.AMAZON_PARTNER_TYPE || 'associates';

    if (!this.associatesTag) {
      throw new Error('AMAZON_ASSOCIATES_TAG is required');
    }
  }

  /**
   * Search for products using keywords
   */
  async searchProducts(options: ProductSearchOptions): Promise<Product[]> {
    try {
      // Mock implementation - in production, would call actual PA-API
      const mockProducts: Product[] = [
        {
          asin: 'B0123456789',
          title: `Trending ${options.keywords[0]} Product - Best Seller`,
          price: options.maxPrice || 49.99,
          rating: 4.5,
          reviewCount: 1250,
          imageUrl: 'https://images-na.ssl-images-amazon.com/images/P/B0123456789.jpg',
          category: options.category || 'Electronics',
          keywords: options.keywords,
          buyUrl: this.generateAffiliateUrl('B0123456789'),
        },
        {
          asin: 'B0234567890',
          title: `Premium ${options.keywords[0]} Solution`,
          price: (options.maxPrice || 49.99) * 1.2,
          rating: 4.7,
          reviewCount: 2100,
          imageUrl: 'https://images-na.ssl-images-amazon.com/images/P/B0234567890.jpg',
          category: options.category || 'Electronics',
          keywords: options.keywords,
          buyUrl: this.generateAffiliateUrl('B0234567890'),
        },
      ];

      return mockProducts.slice(0, options.maxResults || 10);
    } catch (error) {
      throw new Error(`Failed to search products: ${(error as Error).message}`);
    }
  }

  /**
   * Generate Amazon Associates affiliate URL
   */
  generateAffiliateUrl(asin: string): string {
    return `https://www.amazon.com/dp/${asin}?tag=${this.associatesTag}`;
  }

  /**
   * Get product details by ASIN
   */
  async getProductDetails(asin: string): Promise<Product> {
    // Mock implementation
    return {
      asin,
      title: `Product ${asin}`,
      price: 29.99,
      rating: 4.3,
      reviewCount: 500,
      category: 'General',
      keywords: [asin],
      buyUrl: this.generateAffiliateUrl(asin),
    };
  }

  /**
   * Batch get product details
   */
  async batchGetProducts(asins: string[]): Promise<Product[]> {
    return Promise.all(asins.map(asin => this.getProductDetails(asin)));
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// LINK MANAGEMENT & GENERATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create affiliate link for a product
 */
export async function createAffiliateLink(
  product: Product,
  niche: string,
  tag?: string
): Promise<AffiliateLink> {
  const client = new AmazonAssociatesClient(tag);
  const associatesTag = tag || process.env.AMAZON_ASSOCIATES_TAG || 'alreadyhere-20';

  const link: AffiliateLink = {
    id: `link-${product.asin}-${Date.now()}`,
    asin: product.asin,
    productTitle: product.title,
    associatesTag,
    affiliateUrl: client.generateAffiliateUrl(product.asin),
    niche,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    clicks: 0,
    conversions: 0,
    revenue: 0,
    status: 'active',
  };

  return link;
}

/**
 * Generate niche-targeted affiliate links
 */
export async function generateNicheLinks(
  niche: string,
  keywords: string[],
  maxLinks: number = 5,
  tag?: string
): Promise<AffiliateLink[]> {
  const client = new AmazonAssociatesClient(tag);

  const products = await client.searchProducts({
    keywords,
    maxResults: maxLinks,
    minRating: 4.0,
  });

  const links = await Promise.all(
    products.map(product => createAffiliateLink(product, niche, tag))
  );

  return links;
}

/**
 * Batch create affiliate links from product ASINs
 */
export async function batchCreateLinks(
  productMapping: Array<{ asin: string; niche: string }>,
  tag?: string
): Promise<AffiliateLink[]> {
  const client = new AmazonAssociatesClient(tag);
  const associatesTag = tag || process.env.AMAZON_ASSOCIATES_TAG || 'alreadyhere-20';

  const asins = productMapping.map(m => m.asin);
  const products = await client.batchGetProducts(asins);

  const links = products.map(product => {
    const mapping = productMapping.find(m => m.asin === product.asin);
    return {
      id: `link-${product.asin}-${Date.now()}`,
      asin: product.asin,
      productTitle: product.title,
      associatesTag,
      affiliateUrl: client.generateAffiliateUrl(product.asin),
      niche: mapping?.niche || 'general',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      clicks: 0,
      conversions: 0,
      revenue: 0,
      status: 'active' as const,
    };
  });

  return links;
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRACKING & ANALYTICS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Track click event on affiliate link
 */
export async function trackClick(
  linkId: string,
  referer?: string,
  userId?: string
): Promise<LinkTrackingEvent> {
  const event: LinkTrackingEvent = {
    linkId,
    eventType: 'click',
    timestamp: new Date().toISOString(),
    referer,
    userId,
  };

  return event;
}

/**
 * Track conversion event with revenue
 */
export async function trackConversion(
  linkId: string,
  amount: number,
  userId?: string
): Promise<LinkTrackingEvent> {
  const event: LinkTrackingEvent = {
    linkId,
    eventType: 'conversion',
    timestamp: new Date().toISOString(),
    amount,
    userId,
  };

  return event;
}

/**
 * Get commission report for period
 */
export async function getCommissionReport(
  startDate: string,
  endDate: string,
  links: AffiliateLink[] = []
): Promise<CommissionReport> {
  const commissionRate = parseFloat(
    process.env.AFFILIATE_COMMISSION_RATE || '0.04'
  );

  const totalClicks = links.reduce((sum, l) => sum + l.clicks, 0);
  const totalConversions = links.reduce((sum, l) => sum + l.conversions, 0);
  const totalRevenue = links.reduce((sum, l) => sum + l.revenue, 0);

  const niches: Record<string, any> = {};
  for (const link of links) {
    if (!niches[link.niche]) {
      niches[link.niche] = {
        linkCount: 0,
        clicks: 0,
        conversions: 0,
        revenue: 0,
      };
    }
    niches[link.niche].linkCount++;
    niches[link.niche].clicks += link.clicks;
    niches[link.niche].conversions += link.conversions;
    niches[link.niche].revenue += link.revenue;
  }

  const topProducts = links
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 10)
    .map(l => ({
      asin: l.asin,
      title: l.productTitle,
      clicks: l.clicks,
      conversions: l.conversions,
      revenue: l.revenue,
    }));

  return {
    period: `${startDate} to ${endDate}`,
    startDate,
    endDate,
    totalLinks: links.length,
    activeLinks: links.filter(l => l.status === 'active').length,
    totalClicks,
    totalConversions,
    conversionRate: totalClicks > 0 ? (totalConversions / totalClicks) * 100 : 0,
    estimatedCommission: totalRevenue * commissionRate,
    topProducts,
    niches,
  };
}

/**
 * Get link performance analytics
 */
export async function getLinkAnalytics(
  linkId: string,
  link: AffiliateLink
): Promise<{
  linkId: string;
  clicks: number;
  conversions: number;
  conversionRate: number;
  revenue: number;
  estimatedCommission: number;
  performance: 'excellent' | 'good' | 'average' | 'poor';
}> {
  const commissionRate = parseFloat(
    process.env.AFFILIATE_COMMISSION_RATE || '0.04'
  );
  const conversionRate =
    link.clicks > 0 ? (link.conversions / link.clicks) * 100 : 0;
  const estimatedCommission = link.revenue * commissionRate;

  let performance: 'excellent' | 'good' | 'average' | 'poor' = 'average';
  if (conversionRate > 5) performance = 'excellent';
  else if (conversionRate > 3) performance = 'good';
  else if (conversionRate < 1) performance = 'poor';

  return {
    linkId,
    clicks: link.clicks,
    conversions: link.conversions,
    conversionRate,
    revenue: link.revenue,
    estimatedCommission,
    performance,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// LINK OPTIMIZATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Optimize affiliate link based on performance
 */
export async function optimizeLink(
  link: AffiliateLink,
  allLinks: AffiliateLink[]
): Promise<LinkOptimizationResult> {
  const recommendations: string[] = [];
  let estimatedImpact = 0;

  // Check if link performance is below average
  const avgConversionRate =
    allLinks.length > 0
      ? allLinks.reduce((sum, l) => sum + (l.conversions / (l.clicks || 1)), 0) /
        allLinks.length
      : 0;

  const linkConversionRate =
    link.clicks > 0 ? link.conversions / link.clicks : 0;

  if (linkConversionRate < avgConversionRate * 0.5) {
    recommendations.push('Consider replacing with higher-performing product');
    estimatedImpact += 15;
  }

  if (link.clicks < 10) {
    recommendations.push('Insufficient click data - increase visibility');
    estimatedImpact += 20;
  }

  if (link.revenue < 50) {
    recommendations.push('Low revenue - consider different product category');
    estimatedImpact += 10;
  }

  return {
    linkId: link.id,
    originalUrl: link.affiliateUrl,
    optimizedUrl: link.affiliateUrl, // In production, could add analytics params
    recommendation:
      recommendations.length > 0
        ? recommendations[0]
        : 'Link performing well - maintain current strategy',
    estimatedImpactPercent: estimatedImpact,
    appliedChanges: recommendations,
  };
}

/**
 * Bulk optimize links based on performance
 */
export async function bulkOptimizeLinks(
  links: AffiliateLink[]
): Promise<LinkOptimizationResult[]> {
  return Promise.all(links.map(link => optimizeLink(link, links)));
}

// ═══════════════════════════════════════════════════════════════════════════════
// PERSISTENCE & REPORTING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Save links to file
 */
export async function saveLinks(
  links: AffiliateLink[],
  filename?: string
): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';
  const linkFile = filename || path.join(runtimeDir, `affiliate-links-${Date.now()}.json`);

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  await writeFile(linkFile, JSON.stringify(links, null, 2));
  console.log(`Affiliate links saved to ${linkFile}`);
}

/**
 * Load links from file
 */
export async function loadLinks(filepath: string): Promise<AffiliateLink[]> {
  try {
    const content = await readFile(filepath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`Failed to load links: ${(error as Error).message}`);
    return [];
  }
}

/**
 * Save commission report
 */
export async function saveCommissionReport(
  report: CommissionReport,
  filename?: string
): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';
  const reportFile =
    filename || path.join(runtimeDir, `affiliate-report-${Date.now()}.json`);

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  await writeFile(reportFile, JSON.stringify(report, null, 2));
  console.log(`Commission report saved to ${reportFile}`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// BULK OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Bulk import products and create affiliate links
 */
export async function bulkImportProducts(
  products: Array<{ asin: string; niche: string; title?: string }>,
  tag?: string
): Promise<AffiliateLink[]> {
  const links = await batchCreateLinks(products, tag);
  return links;
}

/**
 * Export links in various formats
 */
export async function exportLinks(
  links: AffiliateLink[],
  format: 'json' | 'csv' | 'html'
): Promise<string> {
  if (format === 'json') {
    return JSON.stringify(links, null, 2);
  }

  if (format === 'csv') {
    const header = 'ID,ASIN,Title,URL,Niche,Clicks,Conversions,Revenue,Status\n';
    const rows = links
      .map(l =>
        `${l.id},${l.asin},"${l.productTitle}",${l.affiliateUrl},${l.niche},${l.clicks},${l.conversions},${l.revenue},${l.status}`
      )
      .join('\n');
    return header + rows;
  }

  if (format === 'html') {
    const rows = links
      .map(
        l =>
          `<tr><td>${l.asin}</td><td>${l.productTitle}</td><td><a href="${l.affiliateUrl}" target="_blank">View</a></td><td>${l.niche}</td><td>${l.clicks}</td><td>${l.conversions}</td><td>$${l.revenue.toFixed(2)}</td></tr>`
      )
      .join('\n');
    return `
      <html>
      <table border="1">
        <thead><tr><th>ASIN</th><th>Title</th><th>Link</th><th>Niche</th><th>Clicks</th><th>Conversions</th><th>Revenue</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      </html>
    `;
  }

  throw new Error(`Unsupported export format: ${format}`);
}

export {
  AmazonAssociatesClient,
  Product,
  AffiliateLink,
  LinkTrackingEvent,
  CommissionReport,
  ProductSearchOptions,
  LinkOptimizationResult,
};

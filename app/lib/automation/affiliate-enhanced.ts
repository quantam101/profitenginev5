/**
 * AFFILIATE AUTOMATION ENGINE — ProfitEngine v5
 *
 * Comprehensive affiliate link management system supporting:
 * - Amazon Associates (commission-based)
 * - ClickBank (high-ticket affiliate)
 * - CJ Affiliate (formerly Commission Junction)
 * - ShareASale (performance-based)
 *
 * Features:
 * - Auto-creation of affiliate links
 * - Product-affiliate mapping
 * - Commission tracking & analytics
 * - Conversion attribution
 * - Dynamic link optimization
 * - Batch operations & webhooks
 * - Real-time dashboard metrics
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES & INTERFACES
// ═══════════════════════════════════════════════════════════════════════════════

export interface AffiliateNetwork {
  id: 'amazon' | 'clickbank' | 'cj' | 'shareasale';
  name: string;
  baseUrl: string;
  apiKey?: string;
  secretKey?: string;
  commissionRate: number;
  cookieDays: number;
  enabled: boolean;
  tier: number;
}

export interface AffiliateProduct {
  id: string;
  title: string;
  description: string;
  price: number;
  category: string;
  niche: string;
  image?: string;
  rating?: number;
  reviews?: number;
  vendor?: string;
  externalId?: string; // ASIN, product ID, etc
}

export interface AffiliateLink {
  id: string;
  productId: string;
  network: 'amazon' | 'clickbank' | 'cj' | 'shareasale';
  affiliateUrl: string;
  shortUrl?: string;
  affiliateCode?: string;
  utmParams: {
    source: string;
    medium: string;
    campaign: string;
    content?: string;
  };
  niche: string;
  createdAt: Date;
  updatedAt: Date;
  expiresAt?: Date;
  status: 'active' | 'inactive' | 'pending' | 'expired';
  metadata?: Record<string, any>;
}

export interface ConversionEvent {
  id: string;
  linkId: string;
  eventType: 'click' | 'impression' | 'conversion' | 'return';
  timestamp: Date;
  referer?: string;
  userAgent?: string;
  userId?: string;
  sessionId?: string;
  value?: number;
  metadata?: Record<string, any>;
}

export interface CommissionRecord {
  id: string;
  linkId: string;
  network: string;
  orderId?: string;
  amount: number;
  currency: string;
  status: 'pending' | 'approved' | 'rejected' | 'paid';
  createdAt: Date;
  approvedAt?: Date;
  paidAt?: Date;
}

export interface AffiliateNiche {
  id: string;
  name: string;
  description?: string;
  networks: string[];
  productCategories: string[];
  targetAudience?: string;
  estimatedMonthlyRevenue?: number;
  activeLinks: number;
  totalConversions: number;
}

export interface DashboardMetrics {
  period: {
    start: Date;
    end: Date;
  };
  totalLinks: number;
  activeLinks: number;
  totalClicks: number;
  totalImpressions: number;
  totalConversions: number;
  conversionRate: number;
  estimatedRevenue: number;
  byNetwork: Record<string, {
    links: number;
    clicks: number;
    conversions: number;
    revenue: number;
  }>;
  byNiche: Record<string, {
    links: number;
    clicks: number;
    conversions: number;
    revenue: number;
  }>;
  topProducts: Array<{
    id: string;
    title: string;
    clicks: number;
    conversions: number;
    revenue: number;
  }>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// AFFILIATE NETWORK CONFIGS
// ═══════════════════════════════════════════════════════════════════════════════

export const NETWORKS: Record<string, AffiliateNetwork> = {
  amazon: {
    id: 'amazon',
    name: 'Amazon Associates',
    baseUrl: 'https://amazon.com',
    apiKey: process.env.AMAZON_PA_API_KEY,
    secretKey: process.env.AMAZON_PA_SECRET_KEY,
    commissionRate: parseFloat(process.env.AMAZON_COMMISSION_RATE || '0.04'),
    cookieDays: 24,
    enabled: !!process.env.AMAZON_ASSOCIATES_TAG,
    tier: 1,
  },
  clickbank: {
    id: 'clickbank',
    name: 'ClickBank',
    baseUrl: 'https://clickbank.com',
    apiKey: process.env.CLICKBANK_API_KEY,
    secretKey: process.env.CLICKBANK_SECRET_KEY,
    commissionRate: parseFloat(process.env.CLICKBANK_COMMISSION_RATE || '0.50'),
    cookieDays: 60,
    enabled: !!process.env.CLICKBANK_ACCOUNT,
    tier: 2,
  },
  cj: {
    id: 'cj',
    name: 'CJ Affiliate',
    baseUrl: 'https://cj.com',
    apiKey: process.env.CJ_API_KEY,
    secretKey: process.env.CJ_SECRET_KEY,
    commissionRate: parseFloat(process.env.CJ_COMMISSION_RATE || '0.10'),
    cookieDays: 30,
    enabled: !!process.env.CJ_ACCOUNT,
    tier: 2,
  },
  shareasale: {
    id: 'shareasale',
    name: 'ShareASale',
    baseUrl: 'https://shareasale.com',
    apiKey: process.env.SHAREASALE_API_KEY,
    secretKey: process.env.SHAREASALE_SECRET_KEY,
    commissionRate: parseFloat(process.env.SHAREASALE_COMMISSION_RATE || '0.08'),
    cookieDays: 45,
    enabled: !!process.env.SHAREASALE_ACCOUNT,
    tier: 3,
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// STORAGE PATHS
// ═══════════════════════════════════════════════════════════════════════════════

const getStoragePath = (filename: string) => {
  const baseDir = process.env.AFFILIATE_DATA_DIR || '.data/affiliates';
  return path.join(baseDir, filename);
};

const ensureStorageDir = async () => {
  const baseDir = process.env.AFFILIATE_DATA_DIR || '.data/affiliates';
  if (!existsSync(baseDir)) {
    await mkdir(baseDir, { recursive: true });
  }
};

// ═══════════════════════════════════════════════════════════════════════════════
// LINK CREATION & MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Generate unique link ID
 */
export function generateLinkId(network: string, productId: string): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substr(2, 9);
  return `${network}-${productId}-${timestamp}-${random}`;
}

/**
 * Create Amazon affiliate link
 */
export function createAmazonLink(
  product: AffiliateProduct,
  options?: {
    tag?: string;
    customParams?: Record<string, string>;
  }
): AffiliateLink {
  const tag = options?.tag || process.env.AMAZON_ASSOCIATES_TAG || 'alreadyhere-20';
  const linkId = generateLinkId('amazon', product.id);

  // Build Amazon affiliate URL
  const url = new URL('https://amazon.com/s');
  url.searchParams.set('k', product.title);
  url.searchParams.set('tag', tag);
  url.searchParams.set('linkCode', 'ur2');
  url.searchParams.set('linkId', linkId);

  // Add custom UTM params
  if (options?.customParams) {
    Object.entries(options.customParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }

  const affiliateUrl = url.toString();

  return {
    id: linkId,
    productId: product.id,
    network: 'amazon',
    affiliateUrl,
    niche: product.niche,
    utmParams: {
      source: 'profitengine',
      medium: 'affiliate',
      campaign: product.niche,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
  };
}

/**
 * Create ClickBank affiliate link
 */
export function createClickBankLink(
  product: AffiliateProduct,
  options?: {
    hoplink?: string;
    trackingId?: string;
    customParams?: Record<string, string>;
  }
): AffiliateLink {
  const linkId = generateLinkId('clickbank', product.id);
  const hoplink = options?.hoplink || process.env.CLICKBANK_HOPLINK;

  if (!hoplink) {
    throw new Error('ClickBank hoplink required');
  }

  // Build ClickBank affiliate URL
  const url = new URL(`https://${hoplink}.hop.clickbank.net/`);

  if (options?.trackingId) {
    url.searchParams.set('tid', options.trackingId);
  }

  if (options?.customParams) {
    Object.entries(options.customParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }

  const affiliateUrl = url.toString();

  return {
    id: linkId,
    productId: product.id,
    network: 'clickbank',
    affiliateUrl,
    affiliateCode: hoplink,
    niche: product.niche,
    utmParams: {
      source: 'profitengine',
      medium: 'affiliate',
      campaign: product.niche,
      content: hoplink,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
  };
}

/**
 * Create CJ Affiliate link
 */
export function createCJLink(
  product: AffiliateProduct,
  options?: {
    sid?: string;
    mid?: string;
    customParams?: Record<string, string>;
  }
): AffiliateLink {
  const linkId = generateLinkId('cj', product.id);
  const sid = options?.sid || process.env.CJ_SITE_ID;

  if (!sid) {
    throw new Error('CJ site ID required');
  }

  // Build CJ affiliate URL
  const baseUrl = product.externalId || product.id;
  const url = new URL(`https://click.linksynergy.com/deeplink`);
  url.searchParams.set('id', sid);
  url.searchParams.set('mid', options?.mid || 'product');
  url.searchParams.set('murl', `https://www.example.com/${baseUrl}`);

  if (options?.customParams) {
    Object.entries(options.customParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }

  const affiliateUrl = url.toString();

  return {
    id: linkId,
    productId: product.id,
    network: 'cj',
    affiliateUrl,
    niche: product.niche,
    utmParams: {
      source: 'profitengine',
      medium: 'affiliate',
      campaign: product.niche,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
  };
}

/**
 * Create ShareASale link
 */
export function createShareASaleLink(
  product: AffiliateProduct,
  options?: {
    merchantId?: string;
    customParams?: Record<string, string>;
  }
): AffiliateLink {
  const linkId = generateLinkId('shareasale', product.id);
  const merchantId = options?.merchantId || process.env.SHAREASALE_MERCHANT_ID;

  if (!merchantId) {
    throw new Error('ShareASale merchant ID required');
  }

  // Build ShareASale affiliate URL
  const url = new URL('https://shareasale.com/r.cfm');
  url.searchParams.set('u', process.env.SHAREASALE_ACCOUNT || 'account');
  url.searchParams.set('m', merchantId);
  url.searchParams.set('urllink', product.externalId || product.id);

  if (options?.customParams) {
    Object.entries(options.customParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }

  const affiliateUrl = url.toString();

  return {
    id: linkId,
    productId: product.id,
    network: 'shareasale',
    affiliateUrl,
    niche: product.niche,
    utmParams: {
      source: 'profitengine',
      medium: 'affiliate',
      campaign: product.niche,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
  };
}

/**
 * Create affiliate links for all enabled networks
 */
export async function createMultiNetworkLinks(
  product: AffiliateProduct
): Promise<AffiliateLink[]> {
  const links: AffiliateLink[] = [];

  try {
    if (NETWORKS.amazon.enabled) {
      links.push(createAmazonLink(product));
    }
  } catch (err) {
    console.error('Failed to create Amazon link:', err);
  }

  try {
    if (NETWORKS.clickbank.enabled) {
      links.push(createClickBankLink(product));
    }
  } catch (err) {
    console.error('Failed to create ClickBank link:', err);
  }

  try {
    if (NETWORKS.cj.enabled) {
      links.push(createCJLink(product));
    }
  } catch (err) {
    console.error('Failed to create CJ link:', err);
  }

  try {
    if (NETWORKS.shareasale.enabled) {
      links.push(createShareASaleLink(product));
    }
  } catch (err) {
    console.error('Failed to create ShareASale link:', err);
  }

  return links;
}

// ═══════════════════════════════════════════════════════════════════════════════
// LINK TRACKING & CONVERSION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Track affiliate click
 */
export async function trackAffiliateClick(
  linkId: string,
  referer?: string,
  userId?: string
): Promise<ConversionEvent> {
  const event: ConversionEvent = {
    id: `click-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    linkId,
    eventType: 'click',
    timestamp: new Date(),
    referer,
    userId,
    sessionId: `session-${Date.now()}`,
  };

  // Store event
  await storeConversionEvent(event);

  return event;
}

/**
 * Track conversion with value
 */
export async function trackConversion(
  linkId: string,
  value: number,
  orderId?: string,
  metadata?: Record<string, any>
): Promise<ConversionEvent> {
  const event: ConversionEvent = {
    id: `conversion-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    linkId,
    eventType: 'conversion',
    timestamp: new Date(),
    value,
    metadata: {
      ...metadata,
      orderId,
    },
  };

  // Store event
  await storeConversionEvent(event);

  // Record commission
  const link = await getLinkById(linkId);
  if (link) {
    const network = NETWORKS[link.network];
    const commission = value * network.commissionRate;

    await storeCommissionRecord({
      id: `comm-${Date.now()}`,
      linkId,
      network: link.network,
      orderId,
      amount: commission,
      currency: 'USD',
      status: 'pending',
      createdAt: new Date(),
    });
  }

  return event;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PERSISTENCE LAYER
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Store conversion event
 */
export async function storeConversionEvent(event: ConversionEvent): Promise<void> {
  await ensureStorageDir();
  const filepath = getStoragePath('conversion-events.jsonl');

  const line = JSON.stringify(event) + '\n';

  try {
    await writeFile(filepath, line, { flag: 'a' });
  } catch (err) {
    console.error('Failed to store conversion event:', err);
  }
}

/**
 * Store commission record
 */
export async function storeCommissionRecord(record: CommissionRecord): Promise<void> {
  await ensureStorageDir();
  const filepath = getStoragePath('commission-records.jsonl');

  const line = JSON.stringify(record) + '\n';

  try {
    await writeFile(filepath, line, { flag: 'a' });
  } catch (err) {
    console.error('Failed to store commission record:', err);
  }
}

/**
 * Save affiliate link
 */
export async function saveLink(link: AffiliateLink): Promise<void> {
  await ensureStorageDir();
  const filepath = getStoragePath('affiliate-links.json');

  try {
    let links: AffiliateLink[] = [];

    if (existsSync(filepath)) {
      const data = await readFile(filepath, 'utf-8');
      links = JSON.parse(data);
    }

    const index = links.findIndex((l) => l.id === link.id);
    if (index >= 0) {
      links[index] = link;
    } else {
      links.push(link);
    }

    await writeFile(filepath, JSON.stringify(links, null, 2));
  } catch (err) {
    console.error('Failed to save link:', err);
  }
}

/**
 * Get link by ID
 */
export async function getLinkById(linkId: string): Promise<AffiliateLink | null> {
  const filepath = getStoragePath('affiliate-links.json');

  try {
    if (!existsSync(filepath)) {
      return null;
    }

    const data = await readFile(filepath, 'utf-8');
    const links: AffiliateLink[] = JSON.parse(data);

    return links.find((l) => l.id === linkId) || null;
  } catch (err) {
    console.error('Failed to get link:', err);
    return null;
  }
}

/**
 * Get all links
 */
export async function getAllLinks(): Promise<AffiliateLink[]> {
  const filepath = getStoragePath('affiliate-links.json');

  try {
    if (!existsSync(filepath)) {
      return [];
    }

    const data = await readFile(filepath, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    console.error('Failed to get links:', err);
    return [];
  }
}

/**
 * Get conversion events
 */
export async function getConversionEvents(
  startDate?: Date,
  endDate?: Date
): Promise<ConversionEvent[]> {
  const filepath = getStoragePath('conversion-events.jsonl');

  try {
    if (!existsSync(filepath)) {
      return [];
    }

    const data = await readFile(filepath, 'utf-8');
    const lines = data.trim().split('\n');
    const events = lines
      .map((line) => {
        try {
          return JSON.parse(line) as ConversionEvent;
        } catch {
          return null;
        }
      })
      .filter(Boolean) as ConversionEvent[];

    // Filter by date range if provided
    if (startDate || endDate) {
      return events.filter((e) => {
        const eventTime = new Date(e.timestamp).getTime();
        const start = startDate ? startDate.getTime() : 0;
        const end = endDate ? endDate.getTime() : Infinity;
        return eventTime >= start && eventTime <= end;
      });
    }

    return events;
  } catch (err) {
    console.error('Failed to get conversion events:', err);
    return [];
  }
}

/**
 * Get commission records
 */
export async function getCommissionRecords(
  status?: string
): Promise<CommissionRecord[]> {
  const filepath = getStoragePath('commission-records.jsonl');

  try {
    if (!existsSync(filepath)) {
      return [];
    }

    const data = await readFile(filepath, 'utf-8');
    const lines = data.trim().split('\n');
    const records = lines
      .map((line) => {
        try {
          return JSON.parse(line) as CommissionRecord;
        } catch {
          return null;
        }
      })
      .filter(Boolean) as CommissionRecord[];

    if (status) {
      return records.filter((r) => r.status === status);
    }

    return records;
  } catch (err) {
    console.error('Failed to get commission records:', err);
    return [];
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ANALYTICS & REPORTING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get dashboard metrics
 */
export async function getDashboardMetrics(
  startDate: Date,
  endDate: Date
): Promise<DashboardMetrics> {
  const links = await getAllLinks();
  const events = await getConversionEvents(startDate, endDate);
  const commissions = await getCommissionRecords();

  const activeLinks = links.filter((l) => l.status === 'active');
  const clicks = events.filter((e) => e.eventType === 'click').length;
  const conversions = events.filter((e) => e.eventType === 'conversion');
  const totalConversions = conversions.length;
  const totalValue = conversions.reduce((sum, c) => sum + (c.value || 0), 0);

  // By network breakdown
  const byNetwork: Record<string, any> = {};
  links.forEach((link) => {
    if (!byNetwork[link.network]) {
      byNetwork[link.network] = { links: 0, clicks: 0, conversions: 0, revenue: 0 };
    }
    byNetwork[link.network].links++;
  });

  events.forEach((e) => {
    const link = links.find((l) => l.id === e.linkId);
    if (link && byNetwork[link.network]) {
      if (e.eventType === 'click') {
        byNetwork[link.network].clicks++;
      }
      if (e.eventType === 'conversion') {
        byNetwork[link.network].conversions++;
        byNetwork[link.network].revenue += e.value || 0;
      }
    }
  });

  // By niche breakdown
  const byNiche: Record<string, any> = {};
  links.forEach((link) => {
    if (!byNiche[link.niche]) {
      byNiche[link.niche] = { links: 0, clicks: 0, conversions: 0, revenue: 0 };
    }
    byNiche[link.niche].links++;
  });

  events.forEach((e) => {
    const link = links.find((l) => l.id === e.linkId);
    if (link && byNiche[link.niche]) {
      if (e.eventType === 'click') {
        byNiche[link.niche].clicks++;
      }
      if (e.eventType === 'conversion') {
        byNiche[link.niche].conversions++;
        byNiche[link.niche].revenue += e.value || 0;
      }
    }
  });

  // Top products
  const productStats: Record<string, any> = {};
  links.forEach((link) => {
    if (!productStats[link.productId]) {
      productStats[link.productId] = {
        id: link.productId,
        title: link.productId,
        clicks: 0,
        conversions: 0,
        revenue: 0,
      };
    }
  });

  events.forEach((e) => {
    const link = links.find((l) => l.id === e.linkId);
    if (link && productStats[link.productId]) {
      if (e.eventType === 'click') {
        productStats[link.productId].clicks++;
      }
      if (e.eventType === 'conversion') {
        productStats[link.productId].conversions++;
        productStats[link.productId].revenue += e.value || 0;
      }
    }
  });

  const topProducts = Object.values(productStats)
    .sort((a: any, b: any) => b.revenue - a.revenue)
    .slice(0, 10);

  return {
    period: { start: startDate, end: endDate },
    totalLinks: links.length,
    activeLinks: activeLinks.length,
    totalClicks: clicks,
    totalImpressions: 0,
    totalConversions,
    conversionRate: clicks > 0 ? totalConversions / clicks : 0,
    estimatedRevenue: totalValue,
    byNetwork,
    byNiche,
    topProducts,
  };
}

/**
 * Get metrics for specific niche
 */
export async function getNicheMetrics(niche: string): Promise<{
  niche: string;
  linkCount: number;
  clicks: number;
  conversions: number;
  revenue: number;
  topLinks: Array<{ id: string; clicks: number; conversions: number }>;
}> {
  const links = await getAllLinks();
  const events = await getConversionEvents();

  const nicheLinks = links.filter((l) => l.niche === niche);
  const nicheEvents = events.filter((e) => {
    const link = links.find((l) => l.id === e.linkId);
    return link && link.niche === niche;
  });

  const clicks = nicheEvents.filter((e) => e.eventType === 'click').length;
  const conversions = nicheEvents.filter((e) => e.eventType === 'conversion');
  const revenue = conversions.reduce((sum, c) => sum + (c.value || 0), 0);

  // Top links in niche
  const linkStats: Record<string, any> = {};
  nicheLinks.forEach((link) => {
    linkStats[link.id] = { id: link.id, clicks: 0, conversions: 0 };
  });

  nicheEvents.forEach((e) => {
    if (linkStats[e.linkId]) {
      if (e.eventType === 'click') {
        linkStats[e.linkId].clicks++;
      }
      if (e.eventType === 'conversion') {
        linkStats[e.linkId].conversions++;
      }
    }
  });

  const topLinks = Object.values(linkStats)
    .sort((a: any, b: any) => b.conversions - a.conversions)
    .slice(0, 5);

  return {
    niche,
    linkCount: nicheLinks.length,
    clicks,
    conversions: conversions.length,
    revenue,
    topLinks,
  };
}

/**
 * Generate commission report
 */
export async function generateCommissionReport(
  startDate: Date,
  endDate: Date
): Promise<{
  period: { start: Date; end: Date };
  totalCommissions: number;
  pendingCommissions: number;
  approvedCommissions: number;
  paidCommissions: number;
  byNetwork: Record<string, number>;
  records: CommissionRecord[];
}> {
  const records = await getCommissionRecords();
  const filtered = records.filter((r) => {
    const time = new Date(r.createdAt).getTime();
    return time >= startDate.getTime() && time <= endDate.getTime();
  });

  const byNetwork: Record<string, number> = {};
  let total = 0;
  let pending = 0;
  let approved = 0;
  let paid = 0;

  filtered.forEach((r) => {
    if (!byNetwork[r.network]) {
      byNetwork[r.network] = 0;
    }
    byNetwork[r.network] += r.amount;
    total += r.amount;

    if (r.status === 'pending') pending += r.amount;
    if (r.status === 'approved') approved += r.amount;
    if (r.status === 'paid') paid += r.amount;
  });

  return {
    period: { start: startDate, end: endDate },
    totalCommissions: total,
    pendingCommissions: pending,
    approvedCommissions: approved,
    paidCommissions: paid,
    byNetwork,
    records: filtered,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// LINK OPTIMIZATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Optimize affiliate link based on performance data
 */
export async function optimizeLink(linkId: string): Promise<{
  linkId: string;
  suggestions: string[];
  recommendations: Record<string, any>;
}> {
  const link = await getLinkById(linkId);
  if (!link) {
    return { linkId, suggestions: [], recommendations: {} };
  }

  const events = await getConversionEvents();
  const linkEvents = events.filter((e) => e.linkId === linkId);
  const clicks = linkEvents.filter((e) => e.eventType === 'click').length;
  const conversions = linkEvents.filter((e) => e.eventType === 'conversion').length;
  const conversionRate = clicks > 0 ? conversions / clicks : 0;

  const suggestions: string[] = [];
  const recommendations: Record<string, any> = {};

  // Low conversion rate
  if (conversionRate < 0.01) {
    suggestions.push('Consider changing product or niche focus');
    recommendations.productChange = true;
  }

  // No clicks
  if (clicks === 0) {
    suggestions.push('Link not yet promoted, increase visibility');
    recommendations.needsPromotion = true;
  }

  // Expired link
  if (link.expiresAt && new Date() > link.expiresAt) {
    suggestions.push('Link has expired, regenerate');
    recommendations.needsRenewal = true;
  }

  // Network underperformance
  const network = NETWORKS[link.network];
  if (network && conversions === 0) {
    suggestions.push(`Try promoting with alternative networks`);
    recommendations.multiNetworkStrategy = true;
  }

  return { linkId, suggestions, recommendations };
}

/**
 * Bulk optimize links for a niche
 */
export async function optimizeNicheLinks(niche: string): Promise<Array<{
  linkId: string;
  suggestions: string[];
}>> {
  const links = await getAllLinks();
  const nicheLinks = links.filter((l) => l.niche === niche);

  const results = await Promise.all(nicheLinks.map((link) => optimizeLink(link.id)));

  return results.map((r) => ({
    linkId: r.linkId,
    suggestions: r.suggestions,
  }));
}

// ═══════════════════════════════════════════════════════════════════════════════
// BATCH OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create links for multiple products
 */
export async function batchCreateLinks(
  products: AffiliateProduct[]
): Promise<AffiliateLink[]> {
  const allLinks: AffiliateLink[] = [];

  for (const product of products) {
    try {
      const links = await createMultiNetworkLinks(product);
      allLinks.push(...links);

      // Save each link
      for (const link of links) {
        await saveLink(link);
      }
    } catch (err) {
      console.error(`Failed to create links for ${product.id}:`, err);
    }
  }

  return allLinks;
}

/**
 * Import links from CSV
 */
export async function importLinksFromCSV(csv: string): Promise<AffiliateLink[]> {
  const lines = csv.trim().split('\n');
  const headers = lines[0].split(',').map((h) => h.trim());
  const links: AffiliateLink[] = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map((v) => v.trim());
    const obj: Record<string, string> = {};

    headers.forEach((header, idx) => {
      obj[header] = values[idx];
    });

    // Create link object from CSV data
    const link: AffiliateLink = {
      id: obj.id || generateLinkId(obj.network || 'amazon', obj.productId || ''),
      productId: obj.productId || '',
      network: (obj.network || 'amazon') as any,
      affiliateUrl: obj.affiliateUrl || '',
      niche: obj.niche || 'general',
      utmParams: {
        source: obj.utm_source || 'profitengine',
        medium: obj.utm_medium || 'affiliate',
        campaign: obj.utm_campaign || obj.niche || 'general',
      },
      createdAt: new Date(obj.createdAt || Date.now()),
      updatedAt: new Date(obj.updatedAt || Date.now()),
      status: (obj.status || 'active') as any,
    };

    links.push(link);
    await saveLink(link);
  }

  return links;
}

/**
 * Export links as CSV
 */
export async function exportLinksAsCSV(niche?: string): Promise<string> {
  const links = await getAllLinks();
  const filtered = niche ? links.filter((l) => l.niche === niche) : links;

  const headers = [
    'id',
    'productId',
    'network',
    'affiliateUrl',
    'niche',
    'status',
    'createdAt',
  ];

  const rows = [
    headers.join(','),
    ...filtered.map((link) =>
      [
        link.id,
        link.productId,
        link.network,
        link.affiliateUrl,
        link.niche,
        link.status,
        link.createdAt.toISOString(),
      ].join(',')
    ),
  ];

  return rows.join('\n');
}

const affiliateEnhanced = {
  NETWORKS,
  generateLinkId,
  createAmazonLink,
  createClickBankLink,
  createCJLink,
  createShareASaleLink,
  createMultiNetworkLinks,
  trackAffiliateClick,
  trackConversion,
  saveLink,
  getLinkById,
  getAllLinks,
  getConversionEvents,
  getCommissionRecords,
  getDashboardMetrics,
  getNicheMetrics,
  generateCommissionReport,
  optimizeLink,
  optimizeNicheLinks,
  batchCreateLinks,
  importLinksFromCSV,
  exportLinksAsCSV,
};
export default affiliateEnhanced;

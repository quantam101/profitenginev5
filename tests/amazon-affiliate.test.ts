/**
 * AMAZON ASSOCIATES AFFILIATE AUTOMATION TEST SUITE
 *
 * Comprehensive tests for Amazon Associates affiliate automation:
 * - Link creation and generation
 * - Click and conversion tracking
 * - Commission reporting
 * - Link optimization
 * - Bulk operations
 *
 * Note: These tests use mock Amazon Associates API calls.
 */

import {
  createAffiliateLink,
  generateNicheLinks,
  batchCreateLinks,
  trackClick,
  trackConversion,
  getCommissionReport,
  getLinkAnalytics,
  optimizeLink,
  bulkOptimizeLinks,
  saveLinks,
  loadLinks,
  saveCommissionReport,
  bulkImportProducts,
  exportLinks,
  Product,
  AffiliateLink,
  CommissionReport,
} from '@/app/lib/automation/amazon-affiliate';

describe('Amazon Associates Affiliate Automation', () => {
  beforeEach(() => {
    process.env.AMAZON_ASSOCIATES_TAG = 'alreadyhere-20';
    process.env.AFFILIATE_COMMISSION_RATE = '0.04';
    process.env.RUNTIME_DATA_DIR = '.runtime/affiliate';
  });

  describe('Link Creation', () => {
    test('should create a single affiliate link', async () => {
      const product: Product = {
        asin: 'B0123456789',
        title: 'Test Product',
        price: 29.99,
        rating: 4.5,
        reviewCount: 100,
        category: 'Electronics',
        keywords: ['test'],
        buyUrl: 'https://amazon.com/dp/B0123456789',
      };

      const link = await createAffiliateLink(product, 'productivity');

      expect(link).toHaveProperty('id');
      expect(link.asin).toBe('B0123456789');
      expect(link.productTitle).toBe('Test Product');
      expect(link.niche).toBe('productivity');
      expect(link.status).toBe('active');
      expect(link.clicks).toBe(0);
      expect(link.conversions).toBe(0);
      expect(link.affiliateUrl).toContain('alreadyhere-20');
    });

    test('should generate niche-targeted links', async () => {
      const links = await generateNicheLinks(
        'productivity',
        ['project management', 'collaboration'],
        5
      );

      expect(links.length).toBeGreaterThan(0);
      expect(links[0].niche).toBe('productivity');
      expect(links[0].status).toBe('active');
      expect(links[0].clicks).toBe(0);
    });

    test('should batch create links from product mapping', async () => {
      const productMapping = [
        { asin: 'B0123456789', niche: 'productivity' },
        { asin: 'B0234567890', niche: 'fitness' },
      ];

      const links = await batchCreateLinks(productMapping);

      expect(links.length).toBe(2);
      expect(links[0].niche).toBe('productivity');
      expect(links[1].niche).toBe('fitness');
      expect(links.every(l => l.status === 'active')).toBe(true);
    });

    test('should use custom associates tag', async () => {
      const product: Product = {
        asin: 'B0123456789',
        title: 'Custom Tag Product',
        price: 19.99,
        rating: 4.0,
        reviewCount: 50,
        category: 'Books',
        keywords: ['custom'],
        buyUrl: 'https://amazon.com/dp/B0123456789',
      };

      const link = await createAffiliateLink(product, 'general', 'custom-tag-20');

      expect(link.associatesTag).toBe('custom-tag-20');
      expect(link.affiliateUrl).toContain('custom-tag-20');
    });
  });

  describe('Tracking', () => {
    test('should track click event', async () => {
      const event = await trackClick('link-B0123456789-1234567890', 'mysite.com', 'user123');

      expect(event.linkId).toBe('link-B0123456789-1234567890');
      expect(event.eventType).toBe('click');
      expect(event.referer).toBe('mysite.com');
      expect(event.userId).toBe('user123');
      expect(event.timestamp).toBeDefined();
    });

    test('should track conversion event with revenue', async () => {
      const event = await trackConversion(
        'link-B0234567890-1234567890',
        49.99,
        'user456'
      );

      expect(event.linkId).toBe('link-B0234567890-1234567890');
      expect(event.eventType).toBe('conversion');
      expect(event.amount).toBe(49.99);
      expect(event.userId).toBe('user456');
      expect(event.timestamp).toBeDefined();
    });
  });

  describe('Analytics', () => {
    test('should calculate commission report', async () => {
      const mockLinks: AffiliateLink[] = [
        {
          id: 'link-1',
          asin: 'B0123456789',
          productTitle: 'Product 1',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0123456789',
          niche: 'productivity',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 100,
          conversions: 5,
          revenue: 249.95,
          status: 'active',
        },
        {
          id: 'link-2',
          asin: 'B0234567890',
          productTitle: 'Product 2',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0234567890',
          niche: 'fitness',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 50,
          conversions: 3,
          revenue: 149.97,
          status: 'active',
        },
      ];

      const report = await getCommissionReport('2024-06-01', '2024-06-30', mockLinks);

      expect(report.totalLinks).toBe(2);
      expect(report.activeLinks).toBe(2);
      expect(report.totalClicks).toBe(150);
      expect(report.totalConversions).toBe(8);
      expect(report.conversionRate).toBeCloseTo(5.33, 1);
      expect(report.estimatedCommission).toBeCloseTo(15.99, 1);
      expect(report.topProducts.length).toBe(2);
      expect(report.niches.productivity).toBeDefined();
      expect(report.niches.fitness).toBeDefined();
    });

    test('should get individual link analytics', async () => {
      const link: AffiliateLink = {
        id: 'link-1',
        asin: 'B0123456789',
        productTitle: 'High Performer',
        associatesTag: 'alreadyhere-20',
        affiliateUrl: 'https://amazon.com/dp/B0123456789',
        niche: 'productivity',
        createdAt: '2024-06-01',
        updatedAt: '2024-06-20',
        clicks: 100,
        conversions: 8,
        revenue: 399.92,
        status: 'active',
      };

      const analytics = await getLinkAnalytics('link-1', link);

      expect(analytics.linkId).toBe('link-1');
      expect(analytics.clicks).toBe(100);
      expect(analytics.conversions).toBe(8);
      expect(analytics.conversionRate).toBe(8);
      expect(analytics.estimatedCommission).toBeCloseTo(15.99, 1);
      expect(analytics.performance).toBe('excellent');
    });

    test('should classify poor performance links', async () => {
      const link: AffiliateLink = {
        id: 'link-poor',
        asin: 'B0987654321',
        productTitle: 'Poor Performer',
        associatesTag: 'alreadyhere-20',
        affiliateUrl: 'https://amazon.com/dp/B0987654321',
        niche: 'misc',
        createdAt: '2024-06-01',
        updatedAt: '2024-06-20',
        clicks: 50,
        conversions: 0,
        revenue: 0,
        status: 'active',
      };

      const analytics = await getLinkAnalytics('link-poor', link);

      expect(analytics.conversionRate).toBe(0);
      expect(analytics.performance).toBe('poor');
    });
  });

  describe('Optimization', () => {
    test('should identify optimization opportunities', async () => {
      const poorLink: AffiliateLink = {
        id: 'link-poor',
        asin: 'B0987654321',
        productTitle: 'Poor Performer',
        associatesTag: 'alreadyhere-20',
        affiliateUrl: 'https://amazon.com/dp/B0987654321',
        niche: 'misc',
        createdAt: '2024-06-01',
        updatedAt: '2024-06-20',
        clicks: 5,
        conversions: 0,
        revenue: 0,
        status: 'active',
      };

      const goodLink: AffiliateLink = {
        id: 'link-good',
        asin: 'B0123456789',
        productTitle: 'Good Performer',
        associatesTag: 'alreadyhere-20',
        affiliateUrl: 'https://amazon.com/dp/B0123456789',
        niche: 'productivity',
        createdAt: '2024-06-01',
        updatedAt: '2024-06-20',
        clicks: 100,
        conversions: 8,
        revenue: 399.92,
        status: 'active',
      };

      const optimization = await optimizeLink(poorLink, [poorLink, goodLink]);

      expect(optimization.linkId).toBe('link-poor');
      expect(optimization.appliedChanges.length).toBeGreaterThan(0);
      expect(optimization.estimatedImpactPercent).toBeGreaterThan(0);
    });

    test('should bulk optimize multiple links', async () => {
      const links: AffiliateLink[] = [
        {
          id: 'link-1',
          asin: 'B0123456789',
          productTitle: 'Product 1',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0123456789',
          niche: 'productivity',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 100,
          conversions: 8,
          revenue: 399.92,
          status: 'active',
        },
        {
          id: 'link-2',
          asin: 'B0234567890',
          productTitle: 'Product 2',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0234567890',
          niche: 'fitness',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 5,
          conversions: 0,
          revenue: 0,
          status: 'active',
        },
      ];

      const optimizations = await bulkOptimizeLinks(links);

      expect(optimizations.length).toBe(2);
      expect(optimizations.every(o => o.linkId)).toBe(true);
      expect(optimizations.some(o => o.appliedChanges.length > 0)).toBe(true);
    });
  });

  describe('Export', () => {
    test('should export links as JSON', async () => {
      const links: AffiliateLink[] = [
        {
          id: 'link-1',
          asin: 'B0123456789',
          productTitle: 'Product 1',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0123456789',
          niche: 'productivity',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 100,
          conversions: 5,
          revenue: 249.95,
          status: 'active',
        },
      ];

      const exported = await exportLinks(links, 'json');
      const parsed = JSON.parse(exported);

      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed[0].asin).toBe('B0123456789');
    });

    test('should export links as CSV', async () => {
      const links: AffiliateLink[] = [
        {
          id: 'link-1',
          asin: 'B0123456789',
          productTitle: 'Product 1',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0123456789',
          niche: 'productivity',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 100,
          conversions: 5,
          revenue: 249.95,
          status: 'active',
        },
      ];

      const exported = await exportLinks(links, 'csv');

      expect(exported).toContain('ID,ASIN');
      expect(exported).toContain('B0123456789');
      expect(exported).toContain('Product 1');
    });

    test('should export links as HTML', async () => {
      const links: AffiliateLink[] = [
        {
          id: 'link-1',
          asin: 'B0123456789',
          productTitle: 'Product 1',
          associatesTag: 'alreadyhere-20',
          affiliateUrl: 'https://amazon.com/dp/B0123456789',
          niche: 'productivity',
          createdAt: '2024-06-01',
          updatedAt: '2024-06-20',
          clicks: 100,
          conversions: 5,
          revenue: 249.95,
          status: 'active',
        },
      ];

      const exported = await exportLinks(links, 'html');

      expect(exported).toContain('<table');
      expect(exported).toContain('B0123456789');
      expect(exported).toContain('Product 1');
    });
  });

  describe('Bulk Operations', () => {
    test('should bulk import products', async () => {
      const products = [
        { asin: 'B0123456789', niche: 'productivity', title: 'Product 1' },
        { asin: 'B0234567890', niche: 'fitness', title: 'Product 2' },
      ];

      const links = await bulkImportProducts(products);

      expect(links.length).toBe(2);
      expect(links[0].niche).toBe('productivity');
      expect(links[1].niche).toBe('fitness');
      expect(links.every(l => l.status === 'active')).toBe(true);
    });
  });

  describe('Validation', () => {
    test('should handle invalid export format', async () => {
      const links: AffiliateLink[] = [];

      await expect(
        exportLinks(links, 'invalid' as any)
      ).rejects.toThrow('Unsupported export format');
    });
  });
});

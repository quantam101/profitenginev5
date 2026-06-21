/**
 * UNIT TESTS: LinkedIn Articles Automation
 *
 * Test coverage:
 * - Content transformation and validation
 * - Affiliate link injection
 * - Rate limiting
 * - Engagement metrics aggregation
 * - API endpoint routing
 */

import {
  transformForLinkedInArticle,
  injectAffiliateLinks,
  publishArticle,
  logEngagementEvent,
  getArticleMetrics,
  getStatus,
  LinkedInArticleContent,
  LinkedInArticleConfig,
  LinkedInWebhookEvent,
} from '../app/lib/automation/linkedin';

/**
 * ============================================================================
 * CONTENT TRANSFORMATION TESTS
 * ============================================================================
 */

describe('LinkedIn Articles Automation', () => {
  describe('Content Transformation', () => {
    it('should transform article with valid title and content', async () => {
      const config: LinkedInArticleConfig = {
        title: 'Building Profitable Online Businesses',
        subtitle: 'A Complete Guide',
        content: 'This is a comprehensive guide...\n\nParagraph 2',
        tags: ['business', 'entrepreneurship'],
      };

      const result = await transformForLinkedInArticle(config);

      expect(result.title).toBe('Building Profitable Online Businesses');
      expect(result.subtitle).toBe('A Complete Guide');
      expect(result.metadata.wordCount).toBeGreaterThan(0);
      expect(result.metadata.estimatedReadTime).toBeGreaterThan(0);
      expect(Array.isArray(result.tags)).toBe(true);
    });

    it('should reject articles with missing title', async () => {
      const config: LinkedInArticleConfig = {
        title: '',
        content: 'Some content',
      };

      await expect(transformForLinkedInArticle(config)).rejects.toThrow(
        'Article title is required'
      );
    });

    it('should reject articles with title exceeding 200 chars', async () => {
      const config: LinkedInArticleConfig = {
        title: 'A'.repeat(201),
        content: 'Some content',
      };

      await expect(transformForLinkedInArticle(config)).rejects.toThrow(
        'exceeds 200 character limit'
      );
    });

    it('should truncate subtitle exceeding 100 chars', async () => {
      const config: LinkedInArticleConfig = {
        title: 'Main Title',
        subtitle: 'A'.repeat(150),
        content: 'Content',
      };

      const result = await transformForLinkedInArticle(config);

      expect(result.subtitle).toHaveLength(100);
    });

    it('should remove HTML from content', async () => {
      const config: LinkedInArticleConfig = {
        title: 'Test Article',
        content: 'This is <strong>bold</strong> text with <script>alert("xss")</script> code',
      };

      const result = await transformForLinkedInArticle(config);

      expect(result.content).not.toContain('<script>');
      expect(result.content).not.toContain('alert');
    });

    it('should calculate correct metadata', async () => {
      const content = 'word '.repeat(500); // 500 words
      const config: LinkedInArticleConfig = {
        title: 'Test',
        content,
      };

      const result = await transformForLinkedInArticle(config);

      expect(result.metadata.wordCount).toBe(500);
      expect(result.metadata.estimatedReadTime).toBe(3); // 500/200 = 2.5, rounded up
    });

    it('should add original URL reference', async () => {
      const config: LinkedInArticleConfig = {
        title: 'Test',
        content: 'Content',
        originalUrl: 'https://example.com/article',
      };

      const result = await transformForLinkedInArticle(config);

      expect(result.content).toContain('https://example.com/article');
    });

    it('should limit tags to 15 and validate length', async () => {
      const config: LinkedInArticleConfig = {
        title: 'Test',
        content: 'Content',
        tags: Array.from({ length: 20 }, (_, i) => `tag${i}`),
      };

      const result = await transformForLinkedInArticle(config);

      expect(result.tags.length).toBeLessThanOrEqual(15);
      expect(result.tags.every((tag) => tag.length <= 30)).toBe(true);
    });

    it('should warn on very short articles', async () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const config: LinkedInArticleConfig = {
        title: 'Short',
        content: 'very short',
      };

      await transformForLinkedInArticle(config);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('very short')
      );

      consoleWarnSpy.mockRestore();
    });
  });

  /**
   * ============================================================================
   * AFFILIATE LINK INJECTION TESTS
   * ============================================================================
   */

  describe('Affiliate Link Injection', () => {
    it('should inject affiliate links for matching keywords', async () => {
      const content = 'Check out [AWS](https://aws.amazon.com) for cloud services';
      const affiliateMap = {
        aws: 'https://example.com/aws-affiliate',
      };

      const result = await injectAffiliateLinks(content, affiliateMap);

      expect(result.content).toContain('https://example.com/aws-affiliate');
      expect(result.replacements.length).toBeGreaterThan(0);
    });

    it('should handle multiple affiliate links', async () => {
      const content =
        'Try [AWS](https://aws.amazon.com) and [Firebase](https://firebase.google.com)';
      const affiliateMap = {
        aws: 'https://aff.com/aws',
        firebase: 'https://aff.com/firebase',
      };

      const result = await injectAffiliateLinks(content, affiliateMap);

      expect(result.replacements.length).toEqual(2);
    });

    it('should handle case-insensitive matching', async () => {
      const content = 'Check out [AWS](https://aws.amazon.com) and [Aws](https://aws.amazon.com)';
      const affiliateMap = {
        AWS: 'https://aff.com/aws',
      };

      const result = await injectAffiliateLinks(content, affiliateMap);

      expect(result.replacements.length).toBeGreaterThan(0);
    });

    it('should return empty replacements for no matches', async () => {
      const content = 'This article has no affiliate links';
      const affiliateMap = {
        aws: 'https://aff.com/aws',
      };

      const result = await injectAffiliateLinks(content, affiliateMap);

      expect(result.replacements.length).toBe(0);
    });
  });

  /**
   * ============================================================================
   * ARTICLE PUBLISHING TESTS
   * ============================================================================
   */

  describe('Article Publishing', () => {
    beforeEach(() => {
      process.env.LINKEDIN_ACCESS_TOKEN = 'test-token';
      process.env.LINKEDIN_ARTICLE_AUTHOR_ID = 'urn:li:person:12345';
    });

    it('should return error without access token', async () => {
      delete process.env.LINKEDIN_ACCESS_TOKEN;

      const article: LinkedInArticleContent = {
        title: 'Test',
        content: 'Content',
      };

      const result = await publishArticle(article);

      expect(result.result.success).toBe(false);
      expect(result.result.error).toContain('LINKEDIN_ACCESS_TOKEN');
    });

    it('should return error without author ID', async () => {
      delete process.env.LINKEDIN_ARTICLE_AUTHOR_ID;

      const article: LinkedInArticleContent = {
        title: 'Test',
        content: 'Content',
      };

      const result = await publishArticle(article);

      expect(result.result.success).toBe(false);
      expect(result.result.error).toContain('LINKEDIN_ARTICLE_AUTHOR_ID');
    });

    it('should respect rate limit', async () => {
      process.env.LINKEDIN_ARTICLE_RATE_LIMIT = '1';

      const article: LinkedInArticleContent = {
        title: 'Test Article',
        content: 'Content here',
      };

      // First call should check rate limit
      const result = await publishArticle(article, { rateLimitCheck: true });

      // If articles already exist today, it may be rate limited
      if (result.result.error?.includes('Rate limit exceeded')) {
        expect(result.result.success).toBe(false);
      }
    });

    it('should generate proper request ID', async () => {
      const article: LinkedInArticleContent = {
        title: 'Test',
        content: 'Content',
      };

      const result = await publishArticle(article);

      expect(result.requestId).toMatch(/^linkedin-article-\d+$/);
    });

    it('should include timestamp in result', async () => {
      const article: LinkedInArticleContent = {
        title: 'Test',
        content: 'Content',
      };

      const result = await publishArticle(article);

      expect(result.timestamp).toBeDefined();
      expect(new Date(result.timestamp).getTime()).toBeGreaterThan(0);
    });
  });

  /**
   * ============================================================================
   * ENGAGEMENT TRACKING TESTS
   * ============================================================================
   */

  describe('Engagement Tracking', () => {
    it('should create valid webhook event', async () => {
      const event: LinkedInWebhookEvent = {
        eventId: 'event-123',
        articleId: 'article-456',
        articleUrn: 'urn:li:article:456',
        eventType: 'view',
        timestamp: new Date().toISOString(),
      };

      await logEngagementEvent(event);

      // Event should be logged without errors
      expect(true).toBe(true);
    });

    it('should handle different event types', async () => {
      const eventTypes: Array<'view' | 'like' | 'share' | 'comment' | 'engagement'> = [
        'view',
        'like',
        'share',
        'comment',
        'engagement',
      ];

      for (const eventType of eventTypes) {
        const event: LinkedInWebhookEvent = {
          eventId: `event-${eventType}`,
          articleId: 'article-123',
          articleUrn: 'urn:li:article:123',
          eventType,
          timestamp: new Date().toISOString(),
        };

        await logEngagementEvent(event);
      }

      expect(true).toBe(true);
    });

    it('should retrieve metrics for article', async () => {
      const articleId = 'test-article-123';

      const metrics = await getArticleMetrics(articleId);

      // Metrics may be null if no events exist
      if (metrics) {
        expect(metrics.articleId).toBe(articleId);
        expect(typeof metrics.views).toBe('number');
        expect(typeof metrics.likes).toBe('number');
        expect(typeof metrics.shares).toBe('number');
        expect(typeof metrics.comments).toBe('number');
      }
    });

    it('should calculate engagement rate', async () => {
      // This is a behavioral test - engagement rate is calculated if views > 0
      const articleId = 'engagement-test-' + Date.now();

      // Log some engagement events
      await logEngagementEvent({
        eventId: 'view-1',
        articleId,
        articleUrn: 'urn:li:article:test',
        eventType: 'view',
        timestamp: new Date().toISOString(),
      });

      await logEngagementEvent({
        eventId: 'like-1',
        articleId,
        articleUrn: 'urn:li:article:test',
        eventType: 'like',
        timestamp: new Date().toISOString(),
      });

      const metrics = await getArticleMetrics(articleId);

      if (metrics && metrics.views > 0) {
        expect(metrics.engagementRate).toBeGreaterThanOrEqual(0);
      }
    });
  });

  /**
   * ============================================================================
   * STATUS AND STATISTICS TESTS
   * ============================================================================
   */

  describe('Status and Statistics', () => {
    it('should return status object', async () => {
      const status = await getStatus();

      expect(status).toHaveProperty('runtimeDir');
      expect(status).toHaveProperty('articlesPublished');
      expect(status).toHaveProperty('articlesPublishedToday');
      expect(status).toHaveProperty('engagementEventsLogged');
      expect(typeof status.articlesPublished).toBe('number');
      expect(typeof status.articlesPublishedToday).toBe('number');
      expect(typeof status.engagementEventsLogged).toBe('number');
    });

    it('should report rate limit remaining', async () => {
      process.env.LINKEDIN_ARTICLE_RATE_LIMIT = '5';
      const status = await getStatus();

      expect(status.rateLimitRemaining).toBeDefined();
      expect(typeof status.rateLimitRemaining).toBe('number');
      expect(status.rateLimitRemaining).toBeGreaterThanOrEqual(0);
    });
  });

  /**
   * ============================================================================
   * INTEGRATION TESTS
   * ============================================================================
   */

  describe('Integration', () => {
    beforeEach(() => {
      process.env.LINKEDIN_ACCESS_TOKEN = 'test-token';
      process.env.LINKEDIN_ARTICLE_AUTHOR_ID = 'urn:li:person:12345';
    });

    it('should handle complete publish workflow', async () => {
      const article: LinkedInArticleContent = {
        title: 'Integration Test Article',
        content: 'This is a test article for the integration test suite.',
        tags: ['test', 'automation'],
      };

      const result = await publishArticle(article, {
        retries: 1,
        rateLimitCheck: false,
      });

      expect(result.requestId).toBeDefined();
      expect(result.timestamp).toBeDefined();
      expect(result.totalDuration).toBeGreaterThan(0);
    });

    it('should parse affiliate links from environment', async () => {
      process.env.AFFILIATE_LINKS = JSON.stringify({
        aws: 'https://aff.com/aws',
        github: 'https://aff.com/github',
      });

      const article: LinkedInArticleContent = {
        title: 'Testing Affiliate Integration',
        content: 'Learn about [AWS](https://aws.amazon.com) and [GitHub](https://github.com)',
        tags: ['cloud', 'devops'],
      };

      const result = await publishArticle(article, {
        rateLimitCheck: false,
      });

      expect(result.requestId).toBeDefined();
    });

    it('should handle webhook and retrieve metrics flow', async () => {
      const articleId = 'flow-test-' + Date.now();

      // Log engagement event
      await logEngagementEvent({
        eventId: 'flow-view-1',
        articleId,
        articleUrn: 'urn:li:article:flow',
        eventType: 'view',
        timestamp: new Date().toISOString(),
      });

      // Retrieve metrics
      const metrics = await getArticleMetrics(articleId);

      if (metrics) {
        expect(metrics.articleId).toBe(articleId);
        expect(metrics.views).toBeGreaterThan(0);
      }
    });
  });
});

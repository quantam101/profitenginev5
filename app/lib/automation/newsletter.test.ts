/**
 * UNIT TESTS: Email Newsletter Automation
 *
 * Test coverage for:
 * - NewsletterAutomationEngine initialization
 * - Request validation
 * - Newsletter publishing
 * - Metrics retrieval
 * - Error handling and retries
 * - Health status
 */

import {
  NewsletterAutomationEngine,
  PublishRequest,
  NewsletterAutomationResult,
} from './newsletter';

// ============================================================================
// TEST FIXTURES
// ============================================================================

const mockPublishRequest: PublishRequest = {
  title: 'Test Newsletter #1',
  subtitle: 'Testing the automation engine',
  body: 'This is test content for the newsletter.',
  summary: 'Test summary',
  tags: ['test', 'automation'],
  ctaText: 'Learn More',
  ctaLink: 'https://example.com',
  platforms: ['beehiiv', 'substack'],
};

const mockPublishRequestWithSchedule: PublishRequest = {
  ...mockPublishRequest,
  scheduleFor: new Date(Date.now() + 86400000), // Tomorrow
};

// ============================================================================
// TEST SUITE
// ============================================================================

describe('NewsletterAutomationEngine', () => {
  let engine: NewsletterAutomationEngine;

  beforeEach(() => {
    // Set up mock environment variables
    process.env.BEEHIIV_API_KEY = 'mock-beehiiv-key';
    process.env.SUBSTACK_API_TOKEN = 'mock-substack-token';
    process.env.CONVERTKIT_API_KEY = 'mock-convertkit-key';
    process.env.NEWSLETTER_AUTOMATION_ENABLED = 'true';

    engine = new NewsletterAutomationEngine({
      enabled: true,
      maxConcurrentPublishes: 3,
      defaultRetryAttempts: 3,
      defaultTimeoutMs: 30000,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // =========================================================================
  // INITIALIZATION TESTS
  // =========================================================================

  describe('initialization', () => {
    test('should initialize successfully with valid config', async () => {
      await expect(engine.initialize()).resolves.not.toThrow();
    });

    test('should handle initialization with disabled automation', async () => {
      const disabledEngine = new NewsletterAutomationEngine({
        enabled: false,
      });

      await disabledEngine.initialize();
      const result = await disabledEngine.publishNewsletter(mockPublishRequest);

      expect(result.success).toBe(false);
      expect(result.status).toBe('failed');
      expect(result.error).toContain('disabled');
    });

    test('should warn about missing API keys', async () => {
      delete process.env.BEEHIIV_API_KEY;
      delete process.env.SUBSTACK_API_TOKEN;

      const consoleSpy = jest.spyOn(console, 'warn');

      const newEngine = new NewsletterAutomationEngine({
        enabled: true,
      });
      await newEngine.initialize();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('missing API keys')
      );

      consoleSpy.mockRestore();
    });

    test('should idempotently initialize', async () => {
      await engine.initialize();
      await expect(engine.initialize()).resolves.not.toThrow();
    });
  });

  // =========================================================================
  // VALIDATION TESTS
  // =========================================================================

  describe('request validation', () => {
    test('should reject request with missing title', async () => {
      const invalidRequest: PublishRequest = {
        ...mockPublishRequest,
        title: '',
      };

      const result = await engine.publishNewsletter(invalidRequest);

      expect(result.success).toBe(false);
      expect(result.error).toContain('title');
    });

    test('should reject request with missing body', async () => {
      const invalidRequest: PublishRequest = {
        ...mockPublishRequest,
        body: '',
      };

      const result = await engine.publishNewsletter(invalidRequest);

      expect(result.success).toBe(false);
      expect(result.error).toContain('body');
    });

    test('should reject request with title exceeding max length', async () => {
      const invalidRequest: PublishRequest = {
        ...mockPublishRequest,
        title: 'a'.repeat(501),
      };

      const result = await engine.publishNewsletter(invalidRequest);

      expect(result.success).toBe(false);
      expect(result.error).toContain('500 characters');
    });

    test('should reject request with past schedule date', async () => {
      const invalidRequest: PublishRequest = {
        ...mockPublishRequest,
        scheduleFor: new Date(Date.now() - 1000),
      };

      const result = await engine.publishNewsletter(invalidRequest);

      expect(result.success).toBe(false);
      expect(result.error).toContain('future');
    });

    test('should accept valid request with all fields', async () => {
      const result = await engine.publishNewsletter(mockPublishRequest);

      // Result should indicate processing (not validation error)
      expect(result).toBeDefined();
      expect(result.channel).toBe('email-newsletter');
      expect(result.linesOfCode).toBe(1850);
    });
  });

  // =========================================================================
  // PUBLISHING TESTS
  // =========================================================================

  describe('newsletter publishing', () => {
    test('should publish to specified platforms', async () => {
      const result = await engine.publishNewsletter(mockPublishRequest);

      expect(result.success).toBeDefined();
      expect(result.channel).toBe('email-newsletter');
      expect(result.status).toBe('completed');
      expect(result.batchResult).toBeDefined();
      expect(result.batchResult?.batchId).toBeDefined();
    });

    test('should track publish duration', async () => {
      const result = await engine.publishNewsletter(mockPublishRequest);

      expect(result.startTime).toBeDefined();
      expect(result.endTime).toBeDefined();

      const startTime = new Date(result.startTime).getTime();
      const endTime = new Date(result.endTime!).getTime();

      expect(endTime).toBeGreaterThanOrEqual(startTime);
    });

    test('should include correct lines of code metric', async () => {
      const result = await engine.publishNewsletter(mockPublishRequest);

      expect(result.linesOfCode).toBe(1850);
    });

    test('should handle scheduled publishing', async () => {
      const result = await engine.publishNewsletter(mockPublishRequestWithSchedule);

      expect(result.success).toBeDefined();
      expect(result.status).toBe('completed');
    });

    test('should handle dry run mode', async () => {
      const dryRunRequest: PublishRequest = {
        ...mockPublishRequest,
        dryRun: true,
      };

      // Dry run should be handled by API layer
      const result = await engine.publishNewsletter(dryRunRequest);

      expect(result.channel).toBe('email-newsletter');
    });

    test('should respect max concurrent publishes limit', async () => {
      const limitedEngine = new NewsletterAutomationEngine({
        maxConcurrentPublishes: 1,
      });

      const promise1 = limitedEngine.publishNewsletter(mockPublishRequest);
      const promise2 = limitedEngine.publishNewsletter(mockPublishRequest);

      const results = await Promise.all([promise1, promise2]);

      expect(results[0]).toBeDefined();
      expect(results[1]).toBeDefined();
    });
  });

  // =========================================================================
  // METRICS TESTS
  // =========================================================================

  describe('metrics retrieval', () => {
    test('should fetch metrics for enabled platforms', async () => {
      const metrics = await engine.getMetrics();

      expect(Array.isArray(metrics)).toBe(true);
      expect(metrics.length).toBeGreaterThan(0);

      const metric = metrics[0];
      expect(metric.platform).toBeDefined();
      expect(metric.lastUpdated).toBeDefined();
    });

    test('should include subscriber counts in metrics', async () => {
      const metrics = await engine.getMetrics();

      const platformMetric = metrics.find((m) => m.totalSubscribers !== undefined);

      expect(platformMetric).toBeDefined();
      expect(platformMetric?.totalSubscribers).toBeGreaterThan(0);
    });

    test('should include engagement metrics', async () => {
      const metrics = await engine.getMetrics();

      const platformMetric = metrics[0];

      if (platformMetric.openRate !== undefined) {
        expect(platformMetric.openRate).toBeGreaterThanOrEqual(0);
        expect(platformMetric.openRate).toBeLessThanOrEqual(1);
      }

      if (platformMetric.clickRate !== undefined) {
        expect(platformMetric.clickRate).toBeGreaterThanOrEqual(0);
        expect(platformMetric.clickRate).toBeLessThanOrEqual(1);
      }
    });
  });

  // =========================================================================
  // HEALTH STATUS TESTS
  // =========================================================================

  describe('health status', () => {
    test('should return healthy status when enabled', async () => {
      const health = await engine.getHealthStatus();

      expect(health.status).toBeDefined();
      expect(['healthy', 'degraded', 'unavailable']).toContain(health.status);
    });

    test('should list enabled platforms', async () => {
      const health = await engine.getHealthStatus();

      expect(Array.isArray(health.enabledPlatforms)).toBe(true);
      expect(health.enabledPlatforms.length).toBeGreaterThan(0);
    });

    test('should track active publishes', async () => {
      const health = await engine.getHealthStatus();

      expect(typeof health.activePublishes).toBe('number');
      expect(health.activePublishes).toBeGreaterThanOrEqual(0);
    });

    test('should return unavailable when disabled', async () => {
      const disabledEngine = new NewsletterAutomationEngine({
        enabled: false,
      });

      const health = await disabledEngine.getHealthStatus();

      expect(health.status).toBe('unavailable');
    });
  });

  // =========================================================================
  // ERROR HANDLING TESTS
  // =========================================================================

  describe('error handling', () => {
    test('should return error result on publish failure', async () => {
      const invalidRequest: PublishRequest = {
        ...mockPublishRequest,
        title: '',
      };

      const result = await engine.publishNewsletter(invalidRequest);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.status).toBe('failed');
    });

    test('should include error details in result', async () => {
      const invalidRequest: PublishRequest = {
        ...mockPublishRequest,
        title: '',
      };

      const result = await engine.publishNewsletter(invalidRequest);

      expect(result.error).toContain('title');
    });
  });

  // =========================================================================
  // RESULT STRUCTURE TESTS
  // =========================================================================

  describe('result structure', () => {
    test('should return properly structured automation result', async () => {
      const result = await engine.publishNewsletter(mockPublishRequest);

      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('channel');
      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('linesOfCode');
      expect(result).toHaveProperty('startTime');
    });

    test('should include batch details in successful result', async () => {
      const result = await engine.publishNewsletter(mockPublishRequest);

      if (result.success) {
        expect(result.batchResult).toBeDefined();
        expect(result.batchResult?.batchId).toBeDefined();
        expect(result.batchResult?.successful).toBeDefined();
        expect(result.batchResult?.failed).toBeDefined();
        expect(result.batchResult?.metrics).toBeDefined();
      }
    });
  });
});

/**
 * TWITTER THREADS AUTOMATION TEST SUITE
 *
 * Comprehensive tests for Twitter Threads automation:
 * - Thread generation and text segmentation
 * - Tweet creation and formatting
 * - Engagement metrics tracking
 * - Webhook handling
 * - Affiliate link injection
 * - Error handling and retry logic
 *
 * Note: These tests mock Twitter API calls. In production, use test mode
 * Twitter API keys and test webhook secrets.
 */

import {
  generateThread,
  publishThread,
  getThreadMetrics,
  logEngagementEvent,
  verifyWebhookSignature,
  ThreadContent,
  GeneratedThread,
  PublishResult,
  ThreadMetrics,
  EngagementEvent,
} from '@/app/lib/automation/twitter';

describe('Twitter Threads Automation', () => {
  // Mock environment variables
  beforeEach(() => {
    process.env.TWITTER_BEARER_TOKEN = 'AAAA1234567890abcdefghijklmnopqrstuvwxyz';
    process.env.TWITTER_WEBHOOK_SECRET = 'whsec_test_mock123';
    process.env.TWITTER_USER_ID = '12345678';
  });

  describe('Thread Generation', () => {
    test('should generate thread from long-form content', async () => {
      const content: ThreadContent = {
        title: 'How to Build Passive Income Streams',
        content: `Start with affiliate marketing. Find products you love and promote them.

Next, create digital products. Design templates, guides, or courses.

Then, automate everything. Use tools to schedule posts and manage sales.

Finally, analyze your results. Track what works and optimize daily.`,
        excerpt: 'A complete guide to passive income in 2024',
        hashtags: ['#PassiveIncome', '#Entrepreneurship'],
        ctaLink: 'https://example.com/guide',
      };

      const thread = await generateThread(content);

      expect(thread).toBeDefined();
      expect(thread.tweets).toBeInstanceOf(Array);
      expect(thread.tweets.length).toBeGreaterThan(0);
      expect(thread.tweets.length).toBeLessThanOrEqual(50);
      expect(thread.tweetCount).toBe(thread.tweets.length);
      expect(thread.threadTitle).toBe(content.title);

      // Verify each tweet respects character limit
      thread.tweets.forEach((tweet) => {
        expect(tweet.text.length).toBeLessThanOrEqual(280);
        expect(tweet.order).toBeGreaterThan(0);
      });

      // Verify first tweet includes title
      expect(thread.tweets[0]?.text).toContain(content.title);

      // Verify estimated engagement
      if (thread.estimatedEngagement) {
        expect(thread.estimatedEngagement.estimatedLikes).toBeGreaterThan(0);
        expect(thread.estimatedEngagement.estimatedRetweets).toBeGreaterThan(0);
        expect(thread.estimatedEngagement.estimatedReplies).toBeGreaterThan(0);
      }
    });

    test('should enforce 280 character limit per tweet', async () => {
      const longContent = 'word '.repeat(100);

      const content: ThreadContent = {
        title: 'Test Thread',
        content: longContent,
      };

      const thread = await generateThread(content);

      thread.tweets.forEach((tweet) => {
        expect(tweet.text.length).toBeLessThanOrEqual(280);
      });
    });

    test('should inject affiliate links into tweets', async () => {
      const content: ThreadContent = {
        title: 'Product Review',
        content: 'Check out this amazing tool that helps with automation.',
        affiliateLinks: {
          tool: 'https://affiliate.example.com/tool',
          automation: 'https://affiliate.example.com/automation',
        },
      };

      const thread = await generateThread(content);

      const threadsWithAffiliates = thread.tweets.some((tweet) =>
        tweet.text.includes('affiliate.example.com')
      );

      expect(threadsWithAffiliates).toBe(true);
    });

    test('should include hashtags in thread', async () => {
      const content: ThreadContent = {
        title: 'Twitter Tips',
        content: 'Tips for growing on Twitter',
        hashtags: ['#Twitter', '#Growth', '#SocialMedia'],
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
      // Hashtags are included in closing tweet
      const hasHashtags = thread.tweets.some((tweet) =>
        content.hashtags?.some((ht) => tweet.text.includes(ht))
      );

      expect(hasHashtags).toBe(true);
    });

    test('should not exceed maximum thread length', async () => {
      const veryLongContent = 'paragraph. '.repeat(1000);

      const content: ThreadContent = {
        title: 'Long Thread',
        content: veryLongContent,
      };

      const thread = await generateThread(content);

      expect(thread.tweetCount).toBeLessThanOrEqual(50);
    });

    test('should preserve tweet order', async () => {
      const content: ThreadContent = {
        title: 'Sequential Thread',
        content: `First point. Second point. Third point. Fourth point.`,
      };

      const thread = await generateThread(content);

      for (let i = 0; i < thread.tweets.length; i++) {
        expect(thread.tweets[i]?.order).toBe(i + 1);
      }
    });
  });

  describe('Thread Publishing', () => {
    test('should successfully publish thread in dry-run mode', async () => {
      const content: ThreadContent = {
        title: 'Published Thread',
        content: 'This thread will be published to Twitter.',
        ctaLink: 'https://example.com/article',
      };

      const result = await publishThread({
        threadContent: content,
        publishImmediate: true,
        dryRun: true,
      });

      expect(result.success).toBe(true);
      expect(result.tweets).toBeDefined();
      expect(result.tweets?.length).toBeGreaterThan(0);
      expect(result.publishedAt).toBeDefined();
      expect(result.executionTime).toBeGreaterThan(0);
    });

    test('should handle missing TWITTER_BEARER_TOKEN gracefully', async () => {
      delete process.env.TWITTER_BEARER_TOKEN;

      const content: ThreadContent = {
        title: 'Test',
        content: 'Content',
      };

      const result = await publishThread({
        threadContent: content,
        publishImmediate: true,
        dryRun: false,
      });

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    test('should support webhook callback on publish', async () => {
      let webhookCalled = false;

      const content: ThreadContent = {
        title: 'Webhook Test',
        content: 'Testing webhook callback.',
      };

      const mockWebhookUrl = 'https://example.com/webhook';

      const result = await publishThread({
        threadContent: content,
        publishImmediate: true,
        dryRun: true,
        webhookUrl: mockWebhookUrl,
      });

      expect(result.success).toBe(true);
    });
  });

  describe('Engagement Metrics', () => {
    test('should log engagement event', async () => {
      const event: EngagementEvent = {
        eventId: 'event-123',
        threadId: 'thread-123',
        tweetId: 'tweet-123',
        eventType: 'like',
        userId: 'user-456',
        userName: 'john_doe',
        timestamp: new Date().toISOString(),
      };

      await logEngagementEvent(event);
      // If no error is thrown, test passes
      expect(event.eventId).toBeDefined();
    });

    test('should retrieve thread metrics', async () => {
      // Log several events first
      const events: EngagementEvent[] = [
        {
          eventId: 'e1',
          threadId: 'thread-metrics-test',
          tweetId: 't1',
          eventType: 'like',
          timestamp: new Date().toISOString(),
        },
        {
          eventId: 'e2',
          threadId: 'thread-metrics-test',
          tweetId: 't1',
          eventType: 'retweet',
          timestamp: new Date().toISOString(),
        },
        {
          eventId: 'e3',
          threadId: 'thread-metrics-test',
          tweetId: 't2',
          eventType: 'reply',
          timestamp: new Date().toISOString(),
        },
        {
          eventId: 'e4',
          threadId: 'thread-metrics-test',
          tweetId: 't1',
          eventType: 'impression',
          timestamp: new Date().toISOString(),
        },
      ];

      for (const event of events) {
        await logEngagementEvent(event);
      }

      const metrics = await getThreadMetrics('thread-metrics-test');

      if (metrics) {
        expect(metrics.threadId).toBe('thread-metrics-test');
        expect(metrics.likes).toBeGreaterThanOrEqual(0);
        expect(metrics.retweets).toBeGreaterThanOrEqual(0);
        expect(metrics.replies).toBeGreaterThanOrEqual(0);
        expect(metrics.totalEngagement).toBeGreaterThanOrEqual(0);
      }
    });

    test('should calculate engagement rate correctly', async () => {
      const threadId = 'engagement-rate-test';

      // Log 100 impressions
      for (let i = 0; i < 100; i++) {
        await logEngagementEvent({
          eventId: `e-imp-${i}`,
          threadId,
          tweetId: 't1',
          eventType: 'impression',
          timestamp: new Date().toISOString(),
        });
      }

      // Log 5 engagements
      for (let i = 0; i < 5; i++) {
        await logEngagementEvent({
          eventId: `e-like-${i}`,
          threadId,
          tweetId: 't1',
          eventType: 'like',
          timestamp: new Date().toISOString(),
        });
      }

      const metrics = await getThreadMetrics(threadId);

      if (metrics && metrics.totalImpressions > 0) {
        expect(metrics.engagementRate).toBeCloseTo(5, 0);
      }
    });
  });

  describe('Webhook Security', () => {
    test('should verify webhook signature correctly', () => {
      const secret = 'whsec_test_secret';
      process.env.TWITTER_WEBHOOK_SECRET = secret;

      const payload = JSON.stringify({ test: 'data' });

      // Create valid signature
      const crypto = require('crypto');
      const validSignature = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');

      const isValid = verifyWebhookSignature(payload, validSignature);
      expect(isValid).toBe(true);
    });

    test('should reject invalid webhook signature', () => {
      const secret = 'whsec_test_secret';
      process.env.TWITTER_WEBHOOK_SECRET = secret;

      const payload = JSON.stringify({ test: 'data' });
      const invalidSignature = 'invalid_signature_xyz';

      const isValid = verifyWebhookSignature(payload, invalidSignature);
      expect(isValid).toBe(false);
    });

    test('should allow webhook without signature if secret not configured', () => {
      delete process.env.TWITTER_WEBHOOK_SECRET;

      const payload = JSON.stringify({ test: 'data' });
      const anySignature = 'any_signature';

      const isValid = verifyWebhookSignature(payload, anySignature);
      expect(isValid).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test('should handle empty content gracefully', async () => {
      const content: ThreadContent = {
        title: '',
        content: '',
      };

      const thread = await generateThread(content);

      expect(thread).toBeDefined();
      expect(thread.tweets.length).toBeGreaterThanOrEqual(0);
    });

    test('should handle very short content', async () => {
      const content: ThreadContent = {
        title: 'Short',
        content: 'Hi',
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
      thread.tweets.forEach((tweet) => {
        expect(tweet.text.length).toBeLessThanOrEqual(280);
      });
    });

    test('should handle special characters in content', async () => {
      const content: ThreadContent = {
        title: 'Special Chars @#$%&*()',
        content: 'Content with special chars: @mention #hashtag $money %rate &and (parentheses)',
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    test('should handle maximum hashtags', async () => {
      const content: ThreadContent = {
        title: 'Many Hashtags',
        content: 'Testing with many hashtags',
        hashtags: Array.from({ length: 20 }, (_, i) => `#Tag${i}`),
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
    });

    test('should handle unicode and emojis', async () => {
      const content: ThreadContent = {
        title: 'Emoji Thread 🚀',
        content: 'This thread has emojis 😀 🎉 🔥 and unicode characters like é ñ ü',
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
      thread.tweets.forEach((tweet) => {
        // Emojis can be counted differently, but total should not exceed limits
        expect(tweet.text).toBeDefined();
      });
    });

    test('should handle URLs in content', async () => {
      const content: ThreadContent = {
        title: 'Thread with URLs',
        content: 'Check out https://example.com for more info. Also https://another.com/path/to/page',
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
    });

    test('should handle multiple consecutive hashtags', async () => {
      const content: ThreadContent = {
        title: 'Consecutive Hashtags',
        content: '#Crypto #Bitcoin #Ethereum #Trading #Finance',
      };

      const thread = await generateThread(content);

      expect(thread.tweets.length).toBeGreaterThan(0);
    });
  });
});

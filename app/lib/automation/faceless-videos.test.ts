/**
 * UNIT TESTS: Faceless Videos Automation
 *
 * Test coverage:
 * - Video generation (D-ID, Synthesia, Replicate)
 * - Script parsing from content calendar
 * - Platform publishing (YouTube, TikTok, Instagram, Reddit)
 * - Error handling and configuration validation
 */

import {
  generateAndPublishFacelessVideo,
  FacelessVideoScript,
} from './faceless-videos';

describe('Faceless Videos Automation', () => {
  beforeEach(() => {
    // Setup environment variables for tests
    process.env.DID_API_KEY = 'test-did-key';
    process.env.SYNTHESIA_API_KEY = 'test-synthesia-key';
    process.env.REPLICATE_API_TOKEN = 'test-replicate-token';
    process.env.YOUTUBE_CHANNEL_ID = 'UCtest123';
    process.env.YOUTUBE_API_KEY = 'test-youtube-key';
    process.env.TIKTOK_ACCESS_TOKEN = 'test-tiktok-token';
    process.env.INSTAGRAM_ACCESS_TOKEN = 'test-instagram-token';
    process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID = 'test-account-id';
    process.env.REDDIT_ACCESS_TOKEN = 'test-reddit-token';
    process.env.RUNTIME_API_URL = 'http://localhost:3000';
    process.env.RUNTIME_DATA_DIR = '.runtime/faceless-videos-test';
  });

  describe('generateAndPublishFacelessVideo', () => {
    it('should return error when content file is missing', async () => {
      const result = await generateAndPublishFacelessVideo(999);

      expect(result.success).toBe(false);
      expect(result.results).toBeDefined();
      expect(result.results.length).toBeGreaterThan(0);
    });

    it('should accept postNumber parameter', async () => {
      const testPostNumber = 1;
      const result = await generateAndPublishFacelessVideo(testPostNumber);

      expect(result).toBeDefined();
      expect(result.results).toBeDefined();
    });

    it('should accept d-id as video provider', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        videoProvider: 'd-id',
      });

      expect(result).toBeDefined();
    });

    it('should accept synthesia as video provider', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        videoProvider: 'synthesia',
      });

      expect(result).toBeDefined();
    });

    it('should accept replicate as video provider', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        videoProvider: 'replicate',
      });

      expect(result).toBeDefined();
    });

    it('should accept multiple platforms', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['youtube', 'tiktok', 'instagram', 'reddit'],
      });

      expect(result).toBeDefined();
    });

    it('should accept single platform', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['youtube'],
      });

      expect(result).toBeDefined();
    });

    it('should accept publishImmediately option', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        publishImmediately: true,
      });

      expect(result).toBeDefined();
    });

    it('should return results array with platform info', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['youtube', 'tiktok'],
      });

      expect(result.results).toBeDefined();
      expect(Array.isArray(result.results)).toBe(true);
    });
  });

  describe('Configuration Validation', () => {
    it('should handle missing DID_API_KEY gracefully', async () => {
      delete process.env.DID_API_KEY;

      const result = await generateAndPublishFacelessVideo(1, {
        videoProvider: 'd-id',
      });

      expect(result).toBeDefined();
    });

    it('should handle missing SYNTHESIA_API_KEY gracefully', async () => {
      delete process.env.SYNTHESIA_API_KEY;

      const result = await generateAndPublishFacelessVideo(1, {
        videoProvider: 'synthesia',
      });

      expect(result).toBeDefined();
    });

    it('should handle missing REPLICATE_API_TOKEN gracefully', async () => {
      delete process.env.REPLICATE_API_TOKEN;

      const result = await generateAndPublishFacelessVideo(1, {
        videoProvider: 'replicate',
      });

      expect(result).toBeDefined();
    });

    it('should handle missing YOUTUBE_API_KEY gracefully', async () => {
      delete process.env.YOUTUBE_API_KEY;

      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['youtube'],
      });

      expect(result.success).toBe(false);
    });

    it('should handle missing TIKTOK_ACCESS_TOKEN gracefully', async () => {
      delete process.env.TIKTOK_ACCESS_TOKEN;

      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['tiktok'],
      });

      expect(result).toBeDefined();
    });

    it('should handle missing INSTAGRAM_ACCESS_TOKEN gracefully', async () => {
      delete process.env.INSTAGRAM_ACCESS_TOKEN;

      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['instagram'],
      });

      expect(result).toBeDefined();
    });

    it('should handle missing REDDIT_ACCESS_TOKEN gracefully', async () => {
      delete process.env.REDDIT_ACCESS_TOKEN;

      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['reddit'],
      });

      expect(result).toBeDefined();
    });
  });

  describe('Platform Integration', () => {
    it('should support youtube platform', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['youtube'],
      });

      expect(result.results).toBeDefined();
      expect(result.results.some((r) => r.platform === 'youtube')).toBe(true);
    });

    it('should support tiktok platform', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['tiktok'],
      });

      expect(result.results).toBeDefined();
      expect(result.results.some((r) => r.platform === 'tiktok')).toBe(true);
    });

    it('should support instagram platform', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['instagram'],
      });

      expect(result.results).toBeDefined();
      expect(result.results.some((r) => r.platform === 'instagram')).toBe(true);
    });

    it('should support reddit platform', async () => {
      const result = await generateAndPublishFacelessVideo(1, {
        platforms: ['reddit'],
      });

      expect(result.results).toBeDefined();
      expect(result.results.some((r) => r.platform === 'reddit')).toBe(true);
    });
  });
});

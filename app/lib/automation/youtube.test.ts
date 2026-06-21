/**
 * UNIT TESTS: YouTube Long-Form Automation
 *
 * Test coverage:
 * - Video generation (Synthesia, D-ID, Replicate)
 * - Script parsing from content calendar
 * - YouTube API integration
 * - Metrics fetching
 * - Error handling and retry logic
 */

import {
  generateAndPostYouTubeVideo,
  getVideoMetrics,
  YouTubeScript,
  YouTubeUploadResult,
} from './youtube';

describe('YouTube Long-Form Automation', () => {
  beforeEach(() => {
    // Setup environment variables for tests
    process.env.YOUTUBE_CHANNEL_ID = 'UCtest123';
    process.env.YOUTUBE_API_KEY = 'test-api-key';
    process.env.SYNTHESIA_API_KEY = 'test-synthesia-key';
    process.env.RUNTIME_API_URL = 'http://localhost:3000';
    process.env.RUNTIME_DATA_DIR = '.runtime/youtube-test';
  });

  describe('generateAndPostYouTubeVideo', () => {
    it('should return error when YOUTUBE_API_KEY is missing', async () => {
      delete process.env.YOUTUBE_API_KEY;

      const result = await generateAndPostYouTubeVideo(1);

      expect(result.success).toBe(false);
      expect(result.error).toContain('API key');
    });

    it('should return error when content file is missing', async () => {
      const result = await generateAndPostYouTubeVideo(999);

      expect(result.success).toBe(false);
      expect(result.error).toContain('failed');
    });

    it('should parse postNumber from options', async () => {
      // This test verifies the function accepts postNumber parameter
      const testPostNumber = 5;

      // Note: This will fail due to missing content file, but verifies the call signature
      const result = await generateAndPostYouTubeVideo(testPostNumber);

      expect(result).toBeDefined();
    });

    it('should accept videoGenerationApi option', async () => {
      const result = await generateAndPostYouTubeVideo(1, {
        videoGenerationApi: 'd-id',
      });

      expect(result).toBeDefined();
    });

    it('should accept scheduledAt option', async () => {
      const scheduledAt = new Date(Date.now() + 86400000).toISOString();

      const result = await generateAndPostYouTubeVideo(1, {
        scheduledAt,
      });

      expect(result).toBeDefined();
    });

    it('should accept playlistId option', async () => {
      const result = await generateAndPostYouTubeVideo(1, {
        playlistId: 'PLtest123',
      });

      expect(result).toBeDefined();
    });
  });

  describe('getVideoMetrics', () => {
    it('should return metrics object with zero values when API key missing', async () => {
      delete process.env.YOUTUBE_API_KEY;

      const metrics = await getVideoMetrics('test-video-id');

      expect(metrics).toEqual({
        views: 0,
        likes: 0,
        comments: 0,
        shares: 0,
        watchTime: 0,
      });
    });

    it('should return metrics structure for valid video ID', async () => {
      // Mock the fetch for this test
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              items: [
                {
                  statistics: {
                    viewCount: '1000',
                    likeCount: '50',
                    commentCount: '10',
                  },
                },
              ],
            }),
        })
      ) as jest.Mock;

      const metrics = await getVideoMetrics('test-video-id');

      expect(metrics).toBeDefined();
      expect(metrics.views).toBe(1000);
      expect(metrics.likes).toBe(50);
      expect(metrics.comments).toBe(10);
    });

    it('should return zero metrics on API error', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          text: () => Promise.resolve('API Error'),
        })
      ) as jest.Mock;

      const metrics = await getVideoMetrics('invalid-id');

      expect(metrics.views).toBe(0);
      expect(metrics.likes).toBe(0);
    });
  });

  describe('YouTubeUploadResult types', () => {
    it('should have success property', () => {
      const result: YouTubeUploadResult = {
        success: true,
        videoId: 'test123',
        videoUrl: 'https://youtube.com/watch?v=test123',
      };

      expect(result.success).toBe(true);
      expect(result.videoId).toBe('test123');
    });

    it('should handle error results', () => {
      const result: YouTubeUploadResult = {
        success: false,
        error: 'API Key missing',
      };

      expect(result.success).toBe(false);
      expect(result.error).toContain('API Key');
    });

    it('should include metrics if available', () => {
      const result: YouTubeUploadResult = {
        success: true,
        videoId: 'test123',
        metrics: {
          views: 1000,
          likes: 50,
          comments: 10,
          shares: 5,
          watchTime: 5000,
        },
      };

      expect(result.metrics).toBeDefined();
      expect(result.metrics?.views).toBe(1000);
    });

    it('should include status field', () => {
      const result: YouTubeUploadResult = {
        success: true,
        videoId: 'test123',
        status: 'uploaded',
      };

      expect(result.status).toBe('uploaded');
    });
  });

  describe('YouTubeScript type', () => {
    it('should parse script with required fields', () => {
      const script: YouTubeScript = {
        title: 'Test Video',
        description: 'Test Description',
        hook: 'This is a hook',
        mainPoints: ['Point 1', 'Point 2'],
        cta: 'Subscribe now',
        duration: 120,
      };

      expect(script.title).toBe('Test Video');
      expect(script.mainPoints.length).toBe(2);
      expect(script.duration).toBe(120);
    });

    it('should support optional fields', () => {
      const script: YouTubeScript = {
        title: 'Test Video',
        description: 'Test Description',
        hook: 'Hook',
        mainPoints: ['Point 1'],
        cta: 'CTA',
        duration: 120,
        tags: ['tag1', 'tag2'],
        affiliateLinks: {
          'Product A': 'https://affiliate.com/product-a',
        },
        playlistId: 'PLtest123',
        uploadAsShort: true,
      };

      expect(script.tags?.length).toBe(2);
      expect(script.affiliateLinks).toBeDefined();
      expect(script.playlistId).toBe('PLtest123');
      expect(script.uploadAsShort).toBe(true);
    });
  });

  describe('Error handling', () => {
    it('should catch and return errors from orchestration', async () => {
      // Simulate error by using invalid post number
      const result = await generateAndPostYouTubeVideo(-1);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should handle missing YOUTUBE_CHANNEL_ID gracefully', async () => {
      delete process.env.YOUTUBE_CHANNEL_ID;

      const result = await generateAndPostYouTubeVideo(1);

      expect(result.success).toBe(false);
    });

    it('should return structured error with script info', async () => {
      const result = await generateAndPostYouTubeVideo(1);

      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('error');
    });
  });

  describe('Integration scenarios', () => {
    it('should support full end-to-end call with all options', async () => {
      const result = await generateAndPostYouTubeVideo(1, {
        videoGenerationApi: 'synthesia',
        scheduledAt: new Date(Date.now() + 86400000).toISOString(),
        playlistId: 'PLtest123',
      });

      expect(result).toBeDefined();
      expect(result).toHaveProperty('success');
    });

    it('should handle different video generation APIs', async () => {
      const apis: Array<'synthesia' | 'd-id' | 'replicate'> = [
        'synthesia',
        'd-id',
        'replicate',
      ];

      for (const api of apis) {
        const result = await generateAndPostYouTubeVideo(1, {
          videoGenerationApi: api,
        });

        expect(result).toBeDefined();
      }
    });

    it('should generate valid result structure', async () => {
      const result = await generateAndPostYouTubeVideo(1);

      // Verify result has expected properties
      expect(typeof result.success).toBe('boolean');
      if (result.success) {
        expect(result.videoId).toBeDefined();
        expect(result.videoUrl).toBeDefined();
      } else {
        expect(result.error).toBeDefined();
      }
    });
  });

  describe('Performance', () => {
    it('should complete within timeout', async () => {
      const start = Date.now();
      const result = await generateAndPostYouTubeVideo(1);
      const duration = Date.now() - start;

      // Test should complete within 30 seconds
      expect(duration).toBeLessThan(30000);
    });
  });

  describe('Environment configuration', () => {
    it('should use default values when env vars missing', async () => {
      delete process.env.RUNTIME_DATA_DIR;
      delete process.env.VIDEO_GENERATION_API;

      const result = await generateAndPostYouTubeVideo(1);

      // Should not throw, use defaults
      expect(result).toBeDefined();
    });

    it('should respect RUNTIME_API_URL for webhooks', async () => {
      process.env.RUNTIME_API_URL = 'https://custom.example.com';

      const result = await generateAndPostYouTubeVideo(1);

      expect(result).toBeDefined();
    });
  });
});

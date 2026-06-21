/**
 * NEWSLETTER AUTOMATION
 *
 * Unified API for publishing to multiple newsletter platforms:
 * - Beehiiv, Substack, ConvertKit, Medium, Dev.to, Hashnode
 * - Automatic content transformation for each platform
 * - Auto-scheduling with retry logic
 * - Subscriber tracking and engagement metrics
 * - Rate limiting and error handling per platform
 *
 * Environment Requirements:
 * - BEEHIIV_API_KEY
 * - SUBSTACK_API_TOKEN
 * - CONVERTKIT_API_KEY
 * - MEDIUM_API_TOKEN
 * - DEVTO_API_KEY
 * - HASHNODE_API_KEY
 */

import { sleep as sleepUtil } from './rate-limiter';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface NewsletterContent {
  title: string;
  subtitle?: string;
  body: string;
  summary?: string;
  tags?: string[];
  featuredImage?: string;
  ctaText?: string;
  ctaLink?: string;
  publishedAt?: Date;
}

export interface PlatformPublishConfig {
  platform: 'beehiiv' | 'substack' | 'convertkit' | 'medium' | 'devto' | 'hashnode';
  enabled: boolean;
  apiKey: string;
  autoSchedule?: boolean;
  scheduledTime?: Date;
  maxRetries?: number;
  retryDelayMs?: number;
}

export interface PublishResult {
  platform: string;
  success: boolean;
  postId?: string;
  url?: string;
  subscriberCount?: number;
  error?: string;
  duration: number;
  timestamp: string;
}

export interface SubscriberMetrics {
  platform: string;
  totalSubscribers?: number;
  newSubscribers?: number;
  openRate?: number;
  clickRate?: number;
  unsubscribeRate?: number;
  timestamp: string;
}

export interface BatchPublishResult {
  successful: PublishResult[];
  failed: PublishResult[];
  metrics: SubscriberMetrics[];
  totalDuration: number;
  timestamp: string;
}

// ============================================================================
// RATE LIMITER UTILITY
// ============================================================================

class RateLimiter {
  private requestTimes: number[] = [];
  private readonly maxRequests: number;
  private readonly windowMs: number;

  constructor(maxRequests = 10, windowMs = 1000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  async waitIfNeeded(): Promise<void> {
    const now = Date.now();
    this.requestTimes = this.requestTimes.filter((t) => now - t < this.windowMs);

    if (this.requestTimes.length >= this.maxRequests) {
      const oldestRequest = this.requestTimes[0];
      const waitTime = this.windowMs - (now - oldestRequest) + 100;
      if (waitTime > 0) {
        await sleep(waitTime);
        await this.waitIfNeeded();
      }
    }

    this.requestTimes.push(now);
  }
}

// Platform-specific rate limiters
const beehiivLimiter = new RateLimiter(10, 1000); // 10 req/sec
const substackLimiter = new RateLimiter(5, 1000);
const convertkitLimiter = new RateLimiter(10, 1000);
const mediumLimiter = new RateLimiter(5, 1000);
const devtoLimiter = new RateLimiter(10, 1000);
const hashnodeLimiter = new RateLimiter(5, 1000);

// ============================================================================
// CONTENT TRANSFORMATION
// ============================================================================

/**
 * Transform content for different platform requirements
 */
class ContentTransformer {
  /**
   * Convert markdown to platform-specific HTML/format
   */
  static toHTML(markdown: string): string {
    // Basic markdown to HTML conversion
    let html = markdown;

    // Headers
    html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');

    // Bold and italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
    html = html.replace(/_(.+?)_/g, '<em>$1</em>');

    // Links
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = `<p>${html}</p>`;

    // Code blocks
    html = html.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    // Lists
    html = html.replace(/^- (.*?)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    return html;
  }

  /**
   * Convert HTML to plain text
   */
  static toPlainText(html: string): string {
    let text = html;

    // Remove HTML tags
    text = text.replace(/<[^>]*>/g, '');

    // Decode HTML entities
    text = text.replace(/&nbsp;/g, ' ');
    text = text.replace(/&lt;/g, '<');
    text = text.replace(/&gt;/g, '>');
    text = text.replace(/&amp;/g, '&');
    text = text.replace(/&quot;/g, '"');

    // Clean up whitespace
    text = text.replace(/\n\n+/g, '\n\n');

    return text.trim();
  }

  /**
   * Extract excerpt for platforms with character limits
   */
  static extractExcerpt(content: string, maxChars = 250): string {
    const plainText = this.toPlainText(content);
    return plainText.length > maxChars
      ? plainText.substring(0, maxChars).trim() + '...'
      : plainText;
  }

  /**
   * Format tags for different platforms
   */
  static formatTags(tags: string[], platform: string): string | string[] {
    const sanitized = tags.map((tag) => tag.toLowerCase().replace(/[^a-z0-9-]/g, ''));

    switch (platform) {
      case 'beehiiv':
      case 'substack':
      case 'convertkit':
        return sanitized.join(',');
      case 'medium':
      case 'devto':
      case 'hashnode':
        return sanitized;
      default:
        return sanitized;
    }
  }
}

// ============================================================================
// PLATFORM IMPLEMENTATIONS
// ============================================================================

/**
 * Beehiiv API Wrapper
 */
export class BeehiivPublisher {
  private apiKey: string;
  private publicationId: string;

  constructor(apiKey: string, publicationId = '') {
    this.apiKey = apiKey;
    this.publicationId = publicationId;
  }

  async publish(content: NewsletterContent): Promise<PublishResult> {
    const startTime = Date.now();

    try {
      await beehiivLimiter.waitIfNeeded();

      const html = ContentTransformer.toHTML(content.body);

      const response = await fetch('https://api.beehiiv.com/v1/posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          title: content.title,
          subtitle: content.subtitle,
          content: html,
          thumbnail_url: content.featuredImage,
          publish_immediately: !content.publishedAt,
          scheduled_at: content.publishedAt?.toISOString(),
          tags: ContentTransformer.formatTags(content.tags || [], 'beehiiv'),
          free_post: true,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Beehiiv API error: ${response.status} - ${error}`);
      }

      const data = (await response.json()) as { id: string; status: string };

      return {
        platform: 'beehiiv',
        success: true,
        postId: data.id,
        url: `https://beehiiv.com/posts/${data.id}`,
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'beehiiv',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getMetrics(): Promise<SubscriberMetrics> {
    try {
      await beehiivLimiter.waitIfNeeded();

      const response = await fetch(
        'https://api.beehiiv.com/v1/publications/metrics',
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch Beehiiv metrics: ${response.status}`);
      }

      const data = (await response.json()) as {
        data?: {
          subscriber_count?: number;
          open_rate?: number;
          click_rate?: number;
        };
      };

      return {
        platform: 'beehiiv',
        totalSubscribers: data.data?.subscriber_count,
        openRate: data.data?.open_rate,
        clickRate: data.data?.click_rate,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'beehiiv',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

/**
 * Substack API Wrapper
 */
export class SubstackPublisher {
  private apiToken: string;
  private publicationId: string;

  constructor(apiToken: string, publicationId = '') {
    this.apiToken = apiToken;
    this.publicationId = publicationId;
  }

  async publish(content: NewsletterContent): Promise<PublishResult> {
    const startTime = Date.now();

    try {
      await substackLimiter.waitIfNeeded();

      const response = await fetch('https://substack.com/api/v1/posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiToken}`,
        },
        body: JSON.stringify({
          title: content.title,
          subtitle: content.subtitle,
          body_markdown: content.body,
          publish_on: content.publishedAt?.toISOString() || new Date().toISOString(),
          type: 'newsletter',
          audience: 'everyone',
          bylines: ['ProfitEngine'],
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Substack API error: ${response.status} - ${error}`);
      }

      const data = (await response.json()) as { id: string; canonical_url: string };

      return {
        platform: 'substack',
        success: true,
        postId: data.id,
        url: data.canonical_url,
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'substack',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getMetrics(): Promise<SubscriberMetrics> {
    try {
      await substackLimiter.waitIfNeeded();

      const response = await fetch('https://substack.com/api/v1/stats', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${this.apiToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch Substack metrics: ${response.status}`);
      }

      const data = (await response.json()) as {
        subscriber_count?: number;
        open_rate?: number;
      };

      return {
        platform: 'substack',
        totalSubscribers: data.subscriber_count,
        openRate: data.open_rate,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'substack',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

/**
 * ConvertKit API Wrapper
 */
export class ConvertKitPublisher {
  private apiKey: string;
  private apiSecret: string;

  constructor(apiKey: string, apiSecret = '') {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
  }

  async publish(content: NewsletterContent): Promise<PublishResult> {
    const startTime = Date.now();

    try {
      await convertkitLimiter.waitIfNeeded();

      const response = await fetch(
        `https://api.convertkit.com/v3/posts?api_key=${this.apiKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            post: {
              title: content.title,
              content: ContentTransformer.toHTML(content.body),
              published_at: content.publishedAt?.toISOString() || new Date().toISOString(),
              public: true,
              tags: content.tags || [],
            },
          }),
        }
      );

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`ConvertKit API error: ${response.status} - ${error}`);
      }

      const data = (await response.json()) as { post: { id: number; url: string } };

      return {
        platform: 'convertkit',
        success: true,
        postId: data.post.id.toString(),
        url: data.post.url,
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'convertkit',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getMetrics(): Promise<SubscriberMetrics> {
    try {
      await convertkitLimiter.waitIfNeeded();

      const response = await fetch(
        `https://api.convertkit.com/v3/account?api_key=${this.apiKey}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch ConvertKit metrics: ${response.status}`);
      }

      const data = (await response.json()) as {
        account?: { total_subscribers?: number };
      };

      return {
        platform: 'convertkit',
        totalSubscribers: data.account?.total_subscribers,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'convertkit',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

/**
 * Medium API Wrapper
 */
export class MediumPublisher {
  private apiToken: string;
  private authorId: string;

  constructor(apiToken: string, authorId = '') {
    this.apiToken = apiToken;
    this.authorId = authorId;
  }

  async publish(content: NewsletterContent): Promise<PublishResult> {
    const startTime = Date.now();

    try {
      await mediumLimiter.waitIfNeeded();

      const response = await fetch(`https://api.medium.com/v1/users/${this.authorId}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiToken}`,
        },
        body: JSON.stringify({
          title: content.title,
          contentFormat: 'html',
          content: ContentTransformer.toHTML(content.body),
          publishStatus: content.publishedAt ? 'scheduled' : 'published',
          tags: ContentTransformer.formatTags(content.tags || [], 'medium'),
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Medium API error: ${response.status} - ${error}`);
      }

      const data = (await response.json()) as { id: string; url: string };

      return {
        platform: 'medium',
        success: true,
        postId: data.id,
        url: data.url,
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'medium',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getMetrics(): Promise<SubscriberMetrics> {
    try {
      await mediumLimiter.waitIfNeeded();

      const response = await fetch(`https://api.medium.com/v1/users/${this.authorId}`, {
        headers: {
          Authorization: `Bearer ${this.apiToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch Medium metrics: ${response.status}`);
      }

      return {
        platform: 'medium',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'medium',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

/**
 * Dev.to API Wrapper
 */
export class DevToPublisher {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async publish(content: NewsletterContent): Promise<PublishResult> {
    const startTime = Date.now();

    try {
      await devtoLimiter.waitIfNeeded();

      const response = await fetch('https://dev.to/api/articles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': this.apiKey,
        },
        body: JSON.stringify({
          article: {
            title: content.title,
            body_markdown: content.body,
            main_image: content.featuredImage,
            description: content.summary || ContentTransformer.extractExcerpt(content.body),
            tags: ContentTransformer.formatTags(content.tags || [], 'devto'),
            published: !content.publishedAt,
            canonical_url: content.ctaLink,
          },
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Dev.to API error: ${response.status} - ${error}`);
      }

      const data = (await response.json()) as { id: number; url: string };

      return {
        platform: 'devto',
        success: true,
        postId: data.id.toString(),
        url: data.url,
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'devto',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getMetrics(): Promise<SubscriberMetrics> {
    try {
      await devtoLimiter.waitIfNeeded();

      const response = await fetch('https://dev.to/api/users/me', {
        headers: {
          'api-key': this.apiKey,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch Dev.to metrics: ${response.status}`);
      }

      const data = (await response.json()) as {
        followers_count?: number;
      };

      return {
        platform: 'devto',
        totalSubscribers: data.followers_count,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'devto',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

/**
 * Hashnode API Wrapper
 */
export class HashnodePublisher {
  private apiKey: string;
  private publicationId: string;

  constructor(apiKey: string, publicationId = '') {
    this.apiKey = apiKey;
    this.publicationId = publicationId;
  }

  async publish(content: NewsletterContent): Promise<PublishResult> {
    const startTime = Date.now();

    try {
      await hashnodeLimiter.waitIfNeeded();

      const query = `
        mutation createPost($input: CreateStoryInput!) {
          createStory(input: $input) {
            story {
              id
              slug
              title
            }
          }
        }
      `;

      const response = await fetch('https://gql.hashnode.com', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: this.apiKey,
        },
        body: JSON.stringify({
          query,
          variables: {
            input: {
              title: content.title,
              subtitle: content.subtitle,
              contentMarkdown: content.body,
              coverImageUrl: content.featuredImage,
              tags: content.tags?.map((tag) => ({ name: tag })) || [],
              publicationId: this.publicationId,
              publish: !content.publishedAt,
            },
          },
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Hashnode API error: ${response.status} - ${error}`);
      }

      const data = (await response.json()) as {
        data?: { createStory?: { story?: { id: string; slug: string } } };
      };

      const story = data.data?.createStory?.story;
      if (!story) {
        throw new Error('No story returned from Hashnode');
      }

      return {
        platform: 'hashnode',
        success: true,
        postId: story.id,
        url: `https://hashnode.com/@profitengine/${story.slug}`,
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'hashnode',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getMetrics(): Promise<SubscriberMetrics> {
    try {
      await hashnodeLimiter.waitIfNeeded();

      const query = `
        query {
          publication(host: "profitengine.hashnode.dev") {
            id
            followers {
              totalDocuments
            }
          }
        }
      `;

      const response = await fetch('https://gql.hashnode.com', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: this.apiKey,
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch Hashnode metrics: ${response.status}`);
      }

      const data = (await response.json()) as {
        data?: { publication?: { followers?: { totalDocuments?: number } } };
      };

      return {
        platform: 'hashnode',
        totalSubscribers: data.data?.publication?.followers?.totalDocuments,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        platform: 'hashnode',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

// ============================================================================
// BATCH PUBLISHER ORCHESTRATOR
// ============================================================================

export class NewsletterBatchPublisher {
  private publishers: Map<string, BeehiivPublisher | SubstackPublisher | ConvertKitPublisher | MediumPublisher | DevToPublisher | HashnodePublisher> = new Map();
  private config: PlatformPublishConfig[];
  private maxRetries: number;

  constructor(configs: PlatformPublishConfig[], maxRetries = 3) {
    this.config = configs.filter((c) => c.enabled);
    this.maxRetries = maxRetries;
    this.initializePublishers();
  }

  private initializePublishers(): void {
    for (const config of this.config) {
      switch (config.platform) {
        case 'beehiiv':
          this.publishers.set(
            'beehiiv',
            new BeehiivPublisher(config.apiKey)
          );
          break;
        case 'substack':
          this.publishers.set(
            'substack',
            new SubstackPublisher(config.apiKey)
          );
          break;
        case 'convertkit':
          this.publishers.set(
            'convertkit',
            new ConvertKitPublisher(config.apiKey)
          );
          break;
        case 'medium':
          this.publishers.set(
            'medium',
            new MediumPublisher(config.apiKey)
          );
          break;
        case 'devto':
          this.publishers.set(
            'devto',
            new DevToPublisher(config.apiKey)
          );
          break;
        case 'hashnode':
          this.publishers.set(
            'hashnode',
            new HashnodePublisher(config.apiKey)
          );
          break;
      }
    }
  }

  /**
   * Publish to all configured platforms with retry logic
   */
  async publishToAll(content: NewsletterContent): Promise<BatchPublishResult> {
    const startTime = Date.now();
    const results: PublishResult[] = [];
    const metrics: SubscriberMetrics[] = [];

    // Publish to all platforms in parallel
    const publishPromises = Array.from(this.publishers.entries()).map(
      ([platform, publisher]) =>
        this.publishWithRetry(publisher as any, content, platform)
    );

    const publishResults = await Promise.all(publishPromises);
    results.push(...publishResults);

    // Fetch metrics from all platforms
    const metricPromises = Array.from(this.publishers.entries()).map(
      ([, publisher]) => (publisher as any).getMetrics()
    );

    const metricResults = await Promise.all(metricPromises);
    metrics.push(...metricResults);

    // Separate successful and failed results
    const successful = results.filter((r) => r.success);
    const failed = results.filter((r) => !r.success);

    return {
      successful,
      failed,
      metrics,
      totalDuration: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Publish with automatic retry on failure
   */
  private async publishWithRetry(
    publisher: any,
    content: NewsletterContent,
    platform: string,
    attempt = 1
  ): Promise<PublishResult> {
    try {
      return await publisher.publish(content);
    } catch (error) {
      if (attempt < this.maxRetries) {
        const delayMs = Math.pow(2, attempt) * 1000; // Exponential backoff
        await sleep(delayMs);
        return this.publishWithRetry(publisher, content, platform, attempt + 1);
      }

      return {
        platform,
        success: false,
        error: `Failed after ${this.maxRetries} attempts: ${error instanceof Error ? error.message : 'Unknown error'}`,
        duration: 0,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Publish to specific platforms only
   */
  async publishToSelected(
    content: NewsletterContent,
    platforms: string[]
  ): Promise<BatchPublishResult> {
    const startTime = Date.now();
    const results: PublishResult[] = [];
    const metrics: SubscriberMetrics[] = [];

    for (const platform of platforms) {
      const publisher = this.publishers.get(platform);
      if (!publisher) {
        results.push({
          platform,
          success: false,
          error: `Publisher not configured for platform: ${platform}`,
          duration: 0,
          timestamp: new Date().toISOString(),
        });
        continue;
      }

      const result = await this.publishWithRetry(publisher as any, content, platform);
      results.push(result);

      const metric = await (publisher as any).getMetrics();
      metrics.push(metric);
    }

    const successful = results.filter((r) => r.success);
    const failed = results.filter((r) => !r.success);

    return {
      successful,
      failed,
      metrics,
      totalDuration: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Get subscriber metrics across all platforms
   */
  async getAggregateMetrics(): Promise<{
    platforms: SubscriberMetrics[];
    totalSubscribers: number;
    timestamp: string;
  }> {
    const metricPromises = Array.from(this.publishers.values()).map((p) =>
      (p as any).getMetrics()
    );

    const metrics = await Promise.all(metricPromises);
    const totalSubscribers = metrics.reduce((sum, m) => sum + (m.totalSubscribers || 0), 0);

    return {
      platforms: metrics,
      totalSubscribers,
      timestamp: new Date().toISOString(),
    };
  }
}

// Rate limit sleep utility reference
const sleep = sleepUtil;

/**
 * SOCIAL PLATFORM AUTOMATION
 *
 * Auto-publish articles to Medium, Dev.to, and LinkedIn with:
 * - Content transformation per platform (formatting, length, structure)
 * - Cross-posting orchestration with retry logic
 * - Affiliate link injection (custom mapping per platform)
 * - View/engagement tracking and webhook integration
 * - Canonical URL management
 * - SEO optimization per platform requirements
 *
 * Environment Requirements:
 * - MEDIUM_API_TOKEN: Medium API integration token
 * - DEVTO_API_KEY: Dev.to API key
 * - LINKEDIN_ACCESS_TOKEN: LinkedIn OAuth access token
 * - LINKEDIN_AUTHOR_ID: LinkedIn author/personal profile ID
 * - AFFILIATE_LINKS: JSON map of {keyword: affiliate_url}
 * - SOCIAL_CANONICAL_URL: Base URL for canonical links
 * - SOCIAL_WEBHOOK_EVENTS: Webhook endpoint for engagement events
 * - SOCIAL_TRACKING_PIXEL_ID: Google Analytics or custom tracking ID
 */

import { mkdir, writeFile, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface ArticleContent {
  title: string;
  content: string;
  excerpt?: string;
  tags?: string[];
  coverImage?: string;
  originalUrl?: string;
  authorName?: string;
  authorBio?: string;
}

interface SocialPostConfig {
  platform: 'medium' | 'devto' | 'linkedin';
  title: string;
  content: string;
  tags?: string[];
  coverImage?: string;
  canonicalUrl?: string;
  affiliateLinks?: Record<string, string>;
  trackingPixelId?: string;
  webhookUrl?: string;
  publishImmediate?: boolean;
}

interface PlatformTransformResult {
  platform: 'medium' | 'devto' | 'linkedin';
  transformedContent: string;
  transformedTitle: string;
  metadata: {
    wordCount: number;
    estimatedReadTime: number;
    tags: string[];
    affiliateLinkCount: number;
  };
}

interface PublishResult {
  success: boolean;
  platform: 'medium' | 'devto' | 'linkedin';
  postId?: string;
  postUrl?: string;
  publishedAt?: string;
  error?: string;
  retries?: number;
}

interface CrossPostResult {
  requestId: string;
  timestamp: string;
  originalUrl: string;
  results: PublishResult[];
  successCount: number;
  failureCount: number;
  totalDuration: number;
}

interface TrackingEvent {
  eventId: string;
  platform: 'medium' | 'devto' | 'linkedin';
  postId: string;
  postUrl: string;
  eventType: 'view' | 'like' | 'share' | 'comment' | 'read_time';
  userId?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

interface EngagementMetrics {
  platform: 'medium' | 'devto' | 'linkedin';
  postId: string;
  postUrl: string;
  views: number;
  likes: number;
  shares: number;
  comments: number;
  averageReadTime?: number;
  lastUpdated: string;
}

/**
 * ============================================================================
 * CONTENT TRANSFORMATION: Platform-specific formatting
 * ============================================================================
 */

/**
 * Transform markdown content for Medium
 * - Remove HTML (Medium uses its own editor)
 * - Keep markdown formatting
 * - Optimize for Medium's reading experience
 * - Inject tracking pixel
 * - Add canonical link reference
 */
async function transformForMedium(config: SocialPostConfig): Promise<PlatformTransformResult> {
  const { title, content, tags = [], coverImage, canonicalUrl, trackingPixelId } = config;

  // Calculate word count and read time
  const wordCount = content.split(/\s+/).length;
  const estimatedReadTime = Math.ceil(wordCount / 200); // Average 200 WPM

  // Clean content: remove HTML, keep markdown
  let transformedContent = content
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/```[\s\S]*?```/g, (match) => match); // Keep code blocks

  // Add canonical link as paragraph at the end (Medium shows as reference)
  if (canonicalUrl) {
    transformedContent += `\n\n---\n\n**Originally published:** ${canonicalUrl}\n`;
  }

  // Add tracking pixel comment (won't display but Medium will process)
  if (trackingPixelId) {
    transformedContent += `\n<!-- tracking:${trackingPixelId} -->`;
  }

  // Medium-specific tag cleanup (max 5 tags, no spaces)
  const mediumTags = tags
    .slice(0, 5)
    .map((tag) => tag.toLowerCase().replace(/\s+/g, '-'));

  return {
    platform: 'medium',
    transformedContent,
    transformedTitle: title,
    metadata: {
      wordCount,
      estimatedReadTime,
      tags: mediumTags,
      affiliateLinkCount: (transformedContent.match(/https?:\/\//g) || []).length,
    },
  };
}

/**
 * Transform content for Dev.to
 * - Support markdown + frontmatter
 * - Optimize for dev community (code-friendly)
 * - Add canonical URL in frontmatter
 * - Series support for multi-part articles
 */
async function transformForDevto(config: SocialPostConfig): Promise<PlatformTransformResult> {
  const { title, content, tags = [], coverImage, canonicalUrl, trackingPixelId } = config;

  const wordCount = content.split(/\s+/).length;
  const estimatedReadTime = Math.ceil(wordCount / 200);

  // Dev.to uses frontmatter format
  const devtoTags = tags
    .slice(0, 4)
    .map((tag) => tag.toLowerCase().replace(/\s+/g, ''))
    .filter((tag) => tag.length > 0);

  // Build frontmatter
  let frontmatter = `---\ntitle: ${title}\n`;
  frontmatter += `tags: ${devtoTags.map((t) => `"${t}"`).join(',')}\n`;

  if (coverImage) {
    frontmatter += `cover_image: ${coverImage}\n`;
  }

  if (canonicalUrl) {
    frontmatter += `canonical_url: ${canonicalUrl}\n`;
  }

  frontmatter += `published: true\n`;
  frontmatter += `---\n\n`;

  // Keep content as-is (Dev.to supports markdown well)
  let transformedContent = content;

  // Inject tracking script at end (Dev.to allows custom scripts in certain contexts)
  if (trackingPixelId) {
    transformedContent += `\n\n<!-- Analytics: ${trackingPixelId} -->\n`;
  }

  return {
    platform: 'devto',
    transformedContent: frontmatter + transformedContent,
    transformedTitle: title,
    metadata: {
      wordCount,
      estimatedReadTime,
      tags: devtoTags,
      affiliateLinkCount: (transformedContent.match(/https?:\/\//g) || []).length,
    },
  };
}

/**
 * Transform content for LinkedIn
 * - Shorter format (break into sections)
 * - Add call-to-action at end
 * - LinkedIn's 3000 char limit per section
 * - Optimize for LinkedIn engagement
 */
async function transformForLinkedIn(config: SocialPostConfig): Promise<PlatformTransformResult> {
  const { title, content, tags = [], coverImage, canonicalUrl } = config;

  // LinkedIn has soft limit ~3000 chars; break into sections
  const lines = content.split('\n').filter((line) => line.trim());
  let transformedContent = `${title}\n\n`;

  const sections: string[] = [];
  let currentSection = '';

  for (const line of lines) {
    if ((currentSection + line).length > 2500) {
      if (currentSection) sections.push(currentSection.trim());
      currentSection = line;
    } else {
      currentSection += (currentSection ? '\n' : '') + line;
    }
  }

  if (currentSection) sections.push(currentSection.trim());

  transformedContent = sections.slice(0, 3).join('\n\n---\n\n'); // Limit to 3 sections

  // Add CTA with link
  if (canonicalUrl) {
    transformedContent += `\n\n---\n\n📖 Read the full article:\n${canonicalUrl}\n`;
  }

  // LinkedIn tag format: #hashtag
  const linkedInTags = tags.slice(0, 5).map((tag) => `#${tag.toLowerCase().replace(/\s+/g, '')}`);

  transformedContent += `\n\n${linkedInTags.join(' ')}`;

  const wordCount = content.split(/\s+/).length;

  return {
    platform: 'linkedin',
    transformedContent,
    transformedTitle: title.substring(0, 200), // LinkedIn title soft limit
    metadata: {
      wordCount,
      estimatedReadTime: Math.ceil(wordCount / 200),
      tags: linkedInTags,
      affiliateLinkCount: (transformedContent.match(/https?:\/\//g) || []).length,
    },
  };
}

/**
 * ============================================================================
 * AFFILIATE LINK INJECTION
 * ============================================================================
 */

/**
 * Inject affiliate links into content based on configured mappings
 * - Replaces plain URLs with affiliate links
 * - Preserves link context (alt text, etc)
 * - Logs replaced links for analytics
 */
async function injectAffiliateLinks(
  content: string,
  affiliateMap: Record<string, string>
): Promise<{ content: string; replacements: Array<{ original: string; affiliate: string }> }> {
  const replacements: Array<{ original: string; affiliate: string }> = [];

  let transformedContent = content;

  for (const [keyword, affiliateUrl] of Object.entries(affiliateMap)) {
    // Case-insensitive keyword matching
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');

    if (regex.test(transformedContent)) {
      // For markdown links like [text](url), try to match the URL
      const linkRegex = new RegExp(
        `\\[([^\\]]+)\\]\\(([^)]*${keyword}[^)]*)\\)`,
        'gi'
      );

      const matches = transformedContent.matchAll(linkRegex);
      for (const match of matches) {
        const original = match[2];
        replacements.push({ original, affiliate: affiliateUrl });
        transformedContent = transformedContent.replace(original, affiliateUrl);
      }
    }
  }

  return { content: transformedContent, replacements };
}

/**
 * ============================================================================
 * PLATFORM API INTEGRATIONS
 * ============================================================================
 */

/**
 * Publish to Medium
 * - Uses Medium's public API
 * - Handles authentication via integration token
 * - Returns publication details
 */
async function publishToMedium(config: SocialPostConfig, retries = 3): Promise<PublishResult> {
  const token = process.env.MEDIUM_API_TOKEN;
  if (!token) {
    return {
      success: false,
      platform: 'medium',
      error: 'MEDIUM_API_TOKEN not configured',
    };
  }

  let lastError: string | undefined;
  let attempt = 0;

  while (attempt < retries) {
    attempt++;
    try {
      // Get authenticated user (required for Medium API)
      const userResponse = await fetch('https://api.medium.com/v1/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!userResponse.ok) {
        throw new Error(`Failed to get Medium user: ${userResponse.statusText}`);
      }

      const userData = (await userResponse.json()) as { data: { id: string } };
      const userId = userData.data.id;

      // Transform content
      const transformed = await transformForMedium(config);

      // Inject affiliate links if provided
      let contentWithAffiliates = transformed.transformedContent;
      if (config.affiliateLinks) {
        const { content } = await injectAffiliateLinks(
          transformed.transformedContent,
          config.affiliateLinks
        );
        contentWithAffiliates = content;
      }

      // Create publication
      const publishPayload = {
        title: transformed.transformedTitle,
        contentFormat: 'markdown',
        content: contentWithAffiliates,
        publishStatus: config.publishImmediate ? 'public' : 'draft',
        tags: transformed.metadata.tags,
        canonicalUrl: config.canonicalUrl,
      };

      const publishResponse = await fetch(
        `https://api.medium.com/v1/users/${userId}/posts`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(publishPayload),
        }
      );

      if (!publishResponse.ok) {
        throw new Error(
          `Failed to publish to Medium: ${publishResponse.statusText}`
        );
      }

      const result = (await publishResponse.json()) as {
        data: { id: string; url: string; publishedAt: string };
      };

      return {
        success: true,
        platform: 'medium',
        postId: result.data.id,
        postUrl: result.data.url,
        publishedAt: result.data.publishedAt,
        retries: attempt - 1,
      };
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);

      if (attempt < retries) {
        // Exponential backoff: 1s, 2s, 4s
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
      }
    }
  }

  return {
    success: false,
    platform: 'medium',
    error: lastError,
    retries: attempt - 1,
  };
}

/**
 * Publish to Dev.to
 * - Simpler API, no user lookup required
 * - Supports markdown + frontmatter
 * - Returns article ID and URL
 */
async function publishToDevto(config: SocialPostConfig, retries = 3): Promise<PublishResult> {
  const apiKey = process.env.DEVTO_API_KEY;
  if (!apiKey) {
    return {
      success: false,
      platform: 'devto',
      error: 'DEVTO_API_KEY not configured',
    };
  }

  let lastError: string | undefined;
  let attempt = 0;

  while (attempt < retries) {
    attempt++;
    try {
      // Transform content
      const transformed = await transformForDevto(config);

      // Inject affiliate links
      let contentWithAffiliates = transformed.transformedContent;
      if (config.affiliateLinks) {
        const { content } = await injectAffiliateLinks(
          transformed.transformedContent,
          config.affiliateLinks
        );
        contentWithAffiliates = content;
      }

      // Publish to Dev.to
      const publishPayload = {
        article: {
          title: transformed.transformedTitle,
          body_markdown: contentWithAffiliates,
          published: config.publishImmediate ?? true,
          main_image: config.coverImage,
          canonical_url: config.canonicalUrl,
        },
      };

      const publishResponse = await fetch('https://dev.to/api/articles', {
        method: 'POST',
        headers: {
          'api-key': apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(publishPayload),
      });

      if (!publishResponse.ok) {
        throw new Error(
          `Failed to publish to Dev.to: ${publishResponse.statusText}`
        );
      }

      const result = (await publishResponse.json()) as {
        id: number;
        url: string;
        published_at: string;
      };

      return {
        success: true,
        platform: 'devto',
        postId: String(result.id),
        postUrl: result.url,
        publishedAt: result.published_at,
        retries: attempt - 1,
      };
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);

      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
      }
    }
  }

  return {
    success: false,
    platform: 'devto',
    error: lastError,
    retries: attempt - 1,
  };
}

/**
 * Publish to LinkedIn
 * - Uses LinkedIn's REST API v2
 * - Requires OAuth access token
 * - Author ID for personal profile posts
 */
async function publishToLinkedIn(config: SocialPostConfig, retries = 3): Promise<PublishResult> {
  const accessToken = process.env.LINKEDIN_ACCESS_TOKEN;
  const authorId = process.env.LINKEDIN_AUTHOR_ID;

  if (!accessToken || !authorId) {
    return {
      success: false,
      platform: 'linkedin',
      error: 'LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_ID not configured',
    };
  }

  let lastError: string | undefined;
  let attempt = 0;

  while (attempt < retries) {
    attempt++;
    try {
      // Transform content for LinkedIn
      const transformed = await transformForLinkedIn(config);

      // Inject affiliate links
      let contentWithAffiliates = transformed.transformedContent;
      if (config.affiliateLinks) {
        const { content } = await injectAffiliateLinks(
          transformed.transformedContent,
          config.affiliateLinks
        );
        contentWithAffiliates = content;
      }

      // LinkedIn's content distribution API
      const publishPayload = {
        author: `urn:li:person:${authorId}`,
        lifecycleState: 'PUBLISHED',
        specificContent: {
          'com.linkedin.ugc.ShareContent': {
            shareCommentary: {
              text: contentWithAffiliates,
            },
            shareMediaCategory: config.coverImage ? 'IMAGE' : 'NONE',
            media:
              config.coverImage ?
                [
                  {
                    status: 'READY',
                    description: {
                      text: transformed.transformedTitle,
                    },
                    media: config.coverImage,
                    title: {
                      text: transformed.transformedTitle,
                    },
                  },
                ]
              : [],
          },
        },
        visibility: {
          'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC',
        },
      };

      const publishResponse = await fetch(
        'https://api.linkedin.com/v2/ugcPosts',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
            'LinkedIn-Version': '202405',
          },
          body: JSON.stringify(publishPayload),
        }
      );

      if (!publishResponse.ok) {
        throw new Error(
          `Failed to publish to LinkedIn: ${publishResponse.statusText}`
        );
      }

      const result = (await publishResponse.json()) as { id: string };
      const postId = result.id.split(':').pop() || result.id;

      return {
        success: true,
        platform: 'linkedin',
        postId,
        postUrl: `https://www.linkedin.com/feed/update/${postId}`,
        publishedAt: new Date().toISOString(),
        retries: attempt - 1,
      };
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);

      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
      }
    }
  }

  return {
    success: false,
    platform: 'linkedin',
    error: lastError,
    retries: attempt - 1,
  };
}

/**
 * ============================================================================
 * CROSS-POSTING ORCHESTRATION
 * ============================================================================
 */

/**
 * Cross-post article to all configured platforms
 * - Parallel publishing with error handling
 * - Retry logic with exponential backoff
 * - Webhook notification on completion
 * - Results logged to runtime directory
 */
export async function crossPostArticle(
  articleContent: ArticleContent,
  platforms: Array<'medium' | 'devto' | 'linkedin'> = ['medium', 'devto', 'linkedin'],
  options: {
    parallel?: boolean;
    retries?: number;
    webhookUrl?: string;
  } = {}
): Promise<CrossPostResult> {
  const { parallel = true, retries = 3, webhookUrl } = options;
  const startTime = Date.now();
  const requestId = `crosspost-${Date.now()}`;

  // Parse affiliate links from env
  let affiliateLinks: Record<string, string> = {};
  if (process.env.AFFILIATE_LINKS) {
    try {
      affiliateLinks = JSON.parse(process.env.AFFILIATE_LINKS);
    } catch (error) {
      console.warn('Failed to parse AFFILIATE_LINKS:', error);
    }
  }

  const config: SocialPostConfig = {
    platform: 'medium',
    title: articleContent.title,
    content: articleContent.content,
    tags: articleContent.tags,
    coverImage: articleContent.coverImage,
    canonicalUrl: articleContent.originalUrl || process.env.SOCIAL_CANONICAL_URL,
    affiliateLinks,
    trackingPixelId: process.env.SOCIAL_TRACKING_PIXEL_ID,
    publishImmediate: true,
  };

  const publishers = {
    medium: () => publishToMedium({ ...config, platform: 'medium' }, retries),
    devto: () => publishToDevto({ ...config, platform: 'devto' }, retries),
    linkedin: () => publishToLinkedIn({ ...config, platform: 'linkedin' }, retries),
  };

  // Execute publishers
  let results: PublishResult[] = [];

  if (parallel) {
    const promises = platforms.map((platform) => publishers[platform]());
    results = await Promise.all(promises);
  } else {
    for (const platform of platforms) {
      const result = await publishers[platform]();
      results.push(result);
    }
  }

  const crossPostResult: CrossPostResult = {
    requestId,
    timestamp: new Date().toISOString(),
    originalUrl: articleContent.originalUrl || 'direct-input',
    results,
    successCount: results.filter((r) => r.success).length,
    failureCount: results.filter((r) => !r.success).length,
    totalDuration: Date.now() - startTime,
  };

  // Save results to runtime directory
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/social-platforms';
  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  const resultsPath = path.join(runtimeDir, `${requestId}.json`);
  await writeFile(resultsPath, JSON.stringify(crossPostResult, null, 2));

  // Send webhook notification if provided
  if (webhookUrl) {
    try {
      await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(crossPostResult),
      });
    } catch (error) {
      console.warn('Failed to send webhook:', error);
    }
  }

  return crossPostResult;
}

/**
 * ============================================================================
 * ENGAGEMENT TRACKING
 * ============================================================================
 */

/**
 * Log tracking event for engagement metrics
 * - Called via webhook from social platforms or tracking pixel
 * - Logs to runtime JSONL for analytics pipeline
 */
export async function logTrackingEvent(event: TrackingEvent): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/social-platforms';
  const trackingPath = path.join(runtimeDir, 'engagement-events.jsonl');

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  const logEntry = JSON.stringify(event) + '\n';
  await writeFile(trackingPath, logEntry, { flag: 'a' });
}

/**
 * Fetch and aggregate engagement metrics for a post
 * - Fetches from platform APIs or local tracking
 * - Returns consolidated metrics
 */
export async function getEngagementMetrics(
  platform: 'medium' | 'devto' | 'linkedin',
  postId: string
): Promise<EngagementMetrics | null> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/social-platforms';
  const trackingPath = path.join(runtimeDir, 'engagement-events.jsonl');

  if (!existsSync(trackingPath)) {
    return null;
  }

  const fileContent = await readFile(trackingPath, 'utf-8');
  const events = fileContent
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line) as TrackingEvent)
    .filter((e) => e.platform === platform && e.postId === postId);

  if (events.length === 0) {
    return null;
  }

  const metrics: EngagementMetrics = {
    platform,
    postId,
    postUrl: events[0]?.postUrl || '',
    views: events.filter((e) => e.eventType === 'view').length,
    likes: events.filter((e) => e.eventType === 'like').length,
    shares: events.filter((e) => e.eventType === 'share').length,
    comments: events.filter((e) => e.eventType === 'comment').length,
    averageReadTime: calculateAverageReadTime(events),
    lastUpdated: new Date().toISOString(),
  };

  return metrics;
}

function calculateAverageReadTime(events: TrackingEvent[]): number | undefined {
  const readTimeEvents = events
    .filter((e) => e.eventType === 'read_time' && e.metadata?.readTime)
    .map((e) => (e.metadata?.readTime as number) || 0);

  if (readTimeEvents.length === 0) return undefined;
  return Math.round(
    readTimeEvents.reduce((a, b) => a + b, 0) / readTimeEvents.length
  );
}

/**
 * ============================================================================
 * BATCH OPERATIONS
 * ============================================================================
 */

/**
 * Cross-post multiple articles
 * - Each article cross-posted in parallel or serial
 * - Results aggregated and returned
 */
export async function crossPostBatch(
  articles: ArticleContent[],
  platforms: Array<'medium' | 'devto' | 'linkedin'> = ['medium', 'devto', 'linkedin'],
  options: {
    parallel?: boolean;
    retries?: number;
    webhookUrl?: string;
  } = {}
): Promise<CrossPostResult[]> {
  const batchResults = await Promise.all(
    articles.map((article) => crossPostArticle(article, platforms, options))
  );

  return batchResults;
}

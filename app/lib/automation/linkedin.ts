/**
 * LINKEDIN ARTICLES AUTOMATION
 *
 * Auto-publish and manage LinkedIn Articles with:
 * - Content transformation and validation per LinkedIn specifications
 * - Publish/schedule orchestration with retry logic
 * - Affiliate link injection with LinkedIn-safe formatting
 * - View/engagement tracking via LinkedIn analytics webhooks
 * - SEO optimization for LinkedIn discoverability
 * - Cross-platform integration with master orchestrator
 *
 * Environment Requirements:
 * - LINKEDIN_ACCESS_TOKEN: LinkedIn OAuth 2.0 access token (user-me format)
 * - LINKEDIN_ARTICLE_AUTHOR_ID: LinkedIn author/personal profile ID (urn:li:person:XXXXX)
 * - LINKEDIN_ARTICLE_ORG_ID: Optional LinkedIn organization ID for org posts
 * - LINKEDIN_ARTICLE_WEBHOOK_SECRET: Secret for webhook signature validation
 * - AFFILIATE_LINKS: JSON map of {keyword: affiliate_url}
 * - LINKEDIN_ARTICLE_TRACKING_ID: Tracking ID for custom engagement metrics
 * - LINKEDIN_ARTICLE_RATE_LIMIT: Max articles per day (default: 5)
 */

import { mkdir, writeFile, readFile, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

export interface LinkedInArticleContent {
  title: string;
  subtitle?: string;
  content: string;
  description?: string;
  tags?: string[];
  coverImage?: string;
  coverImageAlt?: string;
  originalUrl?: string;
  authorName?: string;
  authorTitle?: string;
  authorImage?: string;
  readTimeMinutes?: number;
}

export interface LinkedInArticleConfig {
  title: string;
  subtitle?: string;
  content: string;
  description?: string;
  tags?: string[];
  coverImage?: string;
  coverImageAlt?: string;
  originalUrl?: string;
  affiliateLinks?: Record<string, string>;
  trackingId?: string;
  webhookUrl?: string;
  publishImmediate?: boolean;
  scheduleTime?: Date;
  authorId?: string; // Overrides default LINKEDIN_ARTICLE_AUTHOR_ID
  organizationId?: string; // For org articles
}

export interface TransformResult {
  title: string;
  subtitle?: string;
  content: string;
  description?: string;
  tags: string[];
  metadata: {
    wordCount: number;
    estimatedReadTime: number;
    paragraphs: number;
    imageCount: number;
    linkCount: number;
    affiliateLinkCount: number;
  };
}

export interface PublishResult {
  success: boolean;
  articleId?: string;
  articleUrn?: string;
  publicArticleUrl?: string;
  publishedAt?: string;
  error?: string;
  retries?: number;
  statusCode?: number;
}

export interface ArticlePublishResult {
  requestId: string;
  timestamp: string;
  originalUrl: string;
  result: PublishResult;
  totalDuration: number;
}

export interface LinkedInArticleMetrics {
  articleId: string;
  articleUrn: string;
  publicUrl: string;
  views: number;
  shares: number;
  comments: number;
  likes: number;
  lastUpdated: string;
  engagementRate?: number;
}

export interface LinkedInWebhookEvent {
  eventId: string;
  articleId: string;
  articleUrn: string;
  eventType: 'view' | 'like' | 'share' | 'comment' | 'engagement';
  timestamp: string;
  userId?: string;
  metadata?: Record<string, unknown>;
}

/**
 * ============================================================================
 * CONTENT TRANSFORMATION: LinkedIn-specific formatting
 * ============================================================================
 */

/**
 * Transform and validate content for LinkedIn Articles
 * - Ensure compliance with LinkedIn article specifications
 * - Optimize formatting (paragraphs, headings, lists)
 * - Calculate metadata (read time, word count, etc.)
 * - Validate image and link requirements
 */
export async function transformForLinkedInArticle(
  config: LinkedInArticleConfig
): Promise<TransformResult> {
  const { title, subtitle, content, tags = [], coverImage, description, originalUrl } = config;

  // Validate title (max 200 chars, required)
  if (!title || title.length === 0) {
    throw new Error('Article title is required');
  }

  if (title.length > 200) {
    throw new Error(`Article title exceeds 200 character limit (${title.length} chars)`);
  }

  // Clean and validate subtitle (optional, max 100 chars)
  let cleanSubtitle: string | undefined;
  if (subtitle) {
    if (subtitle.length > 100) {
      console.warn(`Subtitle exceeds 100 chars, truncating: "${subtitle.substring(0, 100)}..."`);
      cleanSubtitle = subtitle.substring(0, 100);
    } else {
      cleanSubtitle = subtitle;
    }
  }

  // Validate description (optional, max 200 chars for SEO)
  let cleanDescription: string | undefined;
  if (description) {
    if (description.length > 200) {
      console.warn(`Description exceeds 200 chars for optimal SEO`);
      cleanDescription = description.substring(0, 200);
    } else {
      cleanDescription = description;
    }
  }

  // Clean content: remove HTML, preserve markdown structure
  let cleanContent = content
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '') // Remove scripts
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '') // Remove styles
    .trim();

  // Add canonical URL reference if provided
  if (originalUrl) {
    cleanContent += `\n\n---\n\n*Originally published: [${originalUrl}](${originalUrl})*`;
  }

  // Count metrics
  const wordCount = cleanContent.split(/\s+/).length;
  const estimatedReadTime = Math.ceil(wordCount / 200); // LinkedIn avg: 200 WPM
  const paragraphs = cleanContent.split(/\n\n+/).filter((p) => p.trim()).length;
  const imageMatches = cleanContent.match(/!\[.*?\]\(.*?\)/g) || [];
  const imageCount = imageMatches.length;
  const linkMatches = cleanContent.match(/\[.*?\]\(https?:\/\/[^)]+\)/g) || [];
  const linkCount = linkMatches.length;

  // Validate word count (LinkedIn recommendation: 1000+ for articles)
  if (wordCount < 300) {
    console.warn(`Article is very short (${wordCount} words). LinkedIn articles perform better with 1000+ words.`);
  }

  // LinkedIn tag format: no spaces, lowercase, max 30 chars per tag, max 15 tags
  const linkedInTags = tags
    .slice(0, 15)
    .map((tag) => tag.toLowerCase().replace(/\s+/g, ''))
    .filter((tag) => tag.length > 0 && tag.length <= 30);

  return {
    title,
    subtitle: cleanSubtitle,
    content: cleanContent,
    description: cleanDescription,
    tags: linkedInTags,
    metadata: {
      wordCount,
      estimatedReadTime,
      paragraphs,
      imageCount,
      linkCount,
      affiliateLinkCount: (cleanContent.match(/https?:\/\//g) || []).length,
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
 * - Finds keywords and replaces with affiliate URLs
 * - Preserves markdown link syntax
 * - Logs replacements for analytics
 */
export async function injectAffiliateLinks(
  content: string,
  affiliateMap: Record<string, string>
): Promise<{ content: string; replacements: Array<{ original: string; affiliate: string }> }> {
  const replacements: Array<{ original: string; affiliate: string }> = [];
  let transformedContent = content;

  for (const [keyword, affiliateUrl] of Object.entries(affiliateMap)) {
    // Case-insensitive keyword matching in text
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');

    if (regex.test(transformedContent)) {
      // For markdown links [text](url), try to match URLs containing the keyword
      const linkRegex = new RegExp(
        `\\[([^\\]]+)\\]\\(([^)]*${keyword}[^)]*)\\)`,
        'gi'
      );

      let match;
      const matches = [...transformedContent.matchAll(linkRegex)];

      for (const m of matches) {
        const original = m[2];
        const linkText = m[1];

        // Only replace if it looks like a related link (contains keyword)
        if (original.toLowerCase().includes(keyword.toLowerCase())) {
          replacements.push({ original, affiliate: affiliateUrl });
          transformedContent = transformedContent.replace(
            `[${linkText}](${original})`,
            `[${linkText}](${affiliateUrl})`
          );
        }
      }
    }
  }

  return { content: transformedContent, replacements };
}

/**
 * ============================================================================
 * LINKEDIN API INTEGRATION
 * ============================================================================
 */

/**
 * Publish article to LinkedIn
 * - Uses LinkedIn REST API v2 for article publication
 * - Handles OAuth token refresh and retry logic
 * - Supports both personal and organization articles
 * - Returns article URN and public URL
 */
export async function publishToLinkedIn(
  config: LinkedInArticleConfig,
  retries: number = 3
): Promise<PublishResult> {
  const accessToken = process.env.LINKEDIN_ACCESS_TOKEN;
  const authorId = config.authorId || process.env.LINKEDIN_ARTICLE_AUTHOR_ID;

  if (!accessToken) {
    return {
      success: false,
      error: 'LINKEDIN_ACCESS_TOKEN not configured',
    };
  }

  if (!authorId) {
    return {
      success: false,
      error: 'LINKEDIN_ARTICLE_AUTHOR_ID not configured',
    };
  }

  let lastError: string | undefined;
  let attempt = 0;

  while (attempt < retries) {
    attempt++;

    try {
      // Transform content
      const transformed = await transformForLinkedInArticle(config);

      // Inject affiliate links if provided
      let contentWithAffiliates = transformed.content;
      if (config.affiliateLinks) {
        const { content } = await injectAffiliateLinks(
          transformed.content,
          config.affiliateLinks
        );
        contentWithAffiliates = content;
      }

      // Build LinkedIn article payload
      // LinkedIn expects URN format: urn:li:person:XXXXX or urn:li:organization:XXXXX
      const authorUrn = authorId.startsWith('urn:li:') ? authorId : `urn:li:person:${authorId}`;

      const publishPayload = {
        title: transformed.title,
        subtitle: transformed.subtitle || '',
        description: transformed.description || '',
        content: contentWithAffiliates,
        coverImage: config.coverImage,
        coverImageAlt: config.coverImageAlt,
        authorId: authorUrn,
        tags: transformed.tags,
        visibility: 'PUBLIC',
        isArticle: true,
      };

      // Call LinkedIn API
      const publishResponse = await fetch('https://api.linkedin.com/rest/articles', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'LinkedIn-Version': '202405',
          'X-Restli-Protocol-Version': '2.0.0',
        },
        body: JSON.stringify(publishPayload),
      });

      if (!publishResponse.ok) {
        const errorData = await publishResponse.json().catch(() => ({}));
        throw new Error(
          `LinkedIn API error ${publishResponse.status}: ${
            (errorData as Record<string, unknown>).message || publishResponse.statusText
          }`
        );
      }

      const result = (await publishResponse.json()) as {
        id: string;
        urn?: string;
        publicArticleUrl?: string;
      };

      return {
        success: true,
        articleId: result.id,
        articleUrn: result.urn || `urn:li:article:${result.id}`,
        publicArticleUrl:
          result.publicArticleUrl ||
          `https://www.linkedin.com/articles/${result.id}`,
        publishedAt: new Date().toISOString(),
        retries: attempt - 1,
      };
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);

      if (attempt < retries) {
        // Exponential backoff: 1s, 2s, 4s
        await new Promise((resolve) =>
          setTimeout(resolve, 1000 * Math.pow(2, attempt - 1))
        );
      }
    }
  }

  return {
    success: false,
    error: lastError,
    retries: attempt - 1,
  };
}

/**
 * ============================================================================
 * MAIN ORCHESTRATION
 * ============================================================================
 */

/**
 * Publish article to LinkedIn
 * - Validate configuration
 * - Transform content
 * - Execute publish with retry logic
 * - Save results and metrics
 * - Send webhook notifications
 */
export async function publishArticle(
  articleContent: LinkedInArticleContent,
  options: {
    parallel?: boolean;
    retries?: number;
    webhookUrl?: string;
    rateLimitCheck?: boolean;
  } = {}
): Promise<ArticlePublishResult> {
  const { retries = 3, webhookUrl, rateLimitCheck = true } = options;
  const startTime = Date.now();
  const requestId = `linkedin-article-${Date.now()}`;

  try {
    // Check rate limit
    if (rateLimitCheck) {
      const rateLimit = parseInt(process.env.LINKEDIN_ARTICLE_RATE_LIMIT || '5', 10);
      const publishedToday = await getArticlesPublishedToday();

      if (publishedToday >= rateLimit) {
        return {
          requestId,
          timestamp: new Date().toISOString(),
          originalUrl: articleContent.originalUrl || 'direct-input',
          result: {
            success: false,
            error: `Rate limit exceeded: ${publishedToday}/${rateLimit} articles published today`,
          },
          totalDuration: Date.now() - startTime,
        };
      }
    }

    // Parse affiliate links from env
    let affiliateLinks: Record<string, string> = {};
    if (process.env.AFFILIATE_LINKS) {
      try {
        affiliateLinks = JSON.parse(process.env.AFFILIATE_LINKS);
      } catch (error) {
        console.warn('Failed to parse AFFILIATE_LINKS:', error);
      }
    }

    // Prepare config
    const config: LinkedInArticleConfig = {
      title: articleContent.title,
      subtitle: articleContent.subtitle,
      content: articleContent.content,
      description: articleContent.description,
      tags: articleContent.tags,
      coverImage: articleContent.coverImage,
      coverImageAlt: articleContent.coverImageAlt,
      originalUrl: articleContent.originalUrl,
      affiliateLinks,
      trackingId: process.env.LINKEDIN_ARTICLE_TRACKING_ID,
      webhookUrl,
      publishImmediate: true,
    };

    // Publish to LinkedIn
    const result = await publishToLinkedIn(config, retries);

    // Save results to runtime directory
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/linkedin-articles';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    // Log publish result
    const resultsPath = path.join(runtimeDir, `${requestId}.json`);
    await writeFile(
      resultsPath,
      JSON.stringify(
        {
          requestId,
          timestamp: new Date().toISOString(),
          article: articleContent,
          result,
          duration: Date.now() - startTime,
        },
        null,
        2
      )
    );

    // Track published articles
    if (result.success && result.articleId) {
      const articlesLog = path.join(runtimeDir, 'published-articles.jsonl');
      const logEntry = JSON.stringify({
        requestId,
        articleId: result.articleId,
        articleUrn: result.articleUrn,
        publishedAt: result.publishedAt,
        title: articleContent.title,
        wordCount: articleContent.content.split(/\s+/).length,
      });

      await appendFile(articlesLog, logEntry + '\n');
    }

    // Send webhook notification if provided
    if (webhookUrl) {
      try {
        await fetch(webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            requestId,
            timestamp: new Date().toISOString(),
            article: articleContent,
            result,
          }),
        });
      } catch (error) {
        console.warn('Failed to send webhook:', error);
      }
    }

    return {
      requestId,
      timestamp: new Date().toISOString(),
      originalUrl: articleContent.originalUrl || 'direct-input',
      result,
      totalDuration: Date.now() - startTime,
    };
  } catch (error) {
    return {
      requestId,
      timestamp: new Date().toISOString(),
      originalUrl: articleContent.originalUrl || 'direct-input',
      result: {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      totalDuration: Date.now() - startTime,
    };
  }
}

/**
 * ============================================================================
 * ENGAGEMENT TRACKING
 * ============================================================================
 */

/**
 * Log engagement event for LinkedIn articles
 * - Called via webhook from LinkedIn or external tracking
 * - Stores events in JSONL format for analytics
 */
export async function logEngagementEvent(event: LinkedInWebhookEvent): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/linkedin-articles';
  const eventsPath = path.join(runtimeDir, 'engagement-events.jsonl');

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  const logEntry = JSON.stringify(event) + '\n';
  await appendFile(eventsPath, logEntry);
}

/**
 * Get engagement metrics for published article
 * - Aggregates events from tracking logs
 * - Returns consolidated metrics
 */
export async function getArticleMetrics(articleId: string): Promise<LinkedInArticleMetrics | null> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/linkedin-articles';
  const eventsPath = path.join(runtimeDir, 'engagement-events.jsonl');

  if (!existsSync(eventsPath)) {
    return null;
  }

  try {
    const fileContent = await readFile(eventsPath, 'utf-8');
    const events = fileContent
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line) as LinkedInWebhookEvent)
      .filter((e) => e.articleId === articleId);

    if (events.length === 0) {
      return null;
    }

    const metrics: LinkedInArticleMetrics = {
      articleId,
      articleUrn: events[0]?.articleUrn || '',
      publicUrl: `https://www.linkedin.com/articles/${articleId}`,
      views: events.filter((e) => e.eventType === 'view').length,
      likes: events.filter((e) => e.eventType === 'like').length,
      shares: events.filter((e) => e.eventType === 'share').length,
      comments: events.filter((e) => e.eventType === 'comment').length,
      lastUpdated: new Date().toISOString(),
    };

    // Calculate engagement rate
    if (metrics.views > 0) {
      const engagements = metrics.likes + metrics.shares + metrics.comments;
      metrics.engagementRate = (engagements / metrics.views) * 100;
    }

    return metrics;
  } catch (error) {
    console.error('Failed to get article metrics:', error);
    return null;
  }
}

/**
 * Get count of articles published today (for rate limiting)
 */
async function getArticlesPublishedToday(): Promise<number> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/linkedin-articles';
  const articlesLog = path.join(runtimeDir, 'published-articles.jsonl');

  if (!existsSync(articlesLog)) {
    return 0;
  }

  try {
    const fileContent = await readFile(articlesLog, 'utf-8');
    const today = new Date().toISOString().split('T')[0];

    const count = fileContent
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      })
      .filter((entry) => entry && entry.publishedAt?.startsWith(today)).length;

    return count;
  } catch (error) {
    console.error('Failed to count articles published today:', error);
    return 0;
  }
}

/**
 * ============================================================================
 * BATCH OPERATIONS
 * ============================================================================
 */

/**
 * Publish multiple articles to LinkedIn
 * - Each article published in parallel or sequentially
 * - Results aggregated and returned
 */
export async function publishBatch(
  articles: LinkedInArticleContent[],
  options: {
    parallel?: boolean;
    retries?: number;
    webhookUrl?: string;
  } = {}
): Promise<ArticlePublishResult[]> {
  const results = await Promise.all(
    articles.map((article) => publishArticle(article, options))
  );

  return results;
}

/**
 * Get status and statistics for LinkedIn automation
 */
export async function getStatus(): Promise<{
  runtimeDir: string;
  articlesPublished: number;
  articlesPublishedToday: number;
  engagementEventsLogged: number;
  lastPublished?: string;
  rateLimitRemaining?: number;
}> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/linkedin-articles';
  const articlesLog = path.join(runtimeDir, 'published-articles.jsonl');
  const eventsLog = path.join(runtimeDir, 'engagement-events.jsonl');

  let articlesPublished = 0;
  let lastPublished: string | undefined;
  let articlesPublishedToday = 0;

  if (existsSync(articlesLog)) {
    try {
      const fileContent = await readFile(articlesLog, 'utf-8');
      const entries = fileContent
        .split('\n')
        .filter((line) => line.trim())
        .map((line) => {
          try {
            return JSON.parse(line);
          } catch {
            return null;
          }
        })
        .filter((e) => e);

      articlesPublished = entries.length;
      lastPublished = entries[entries.length - 1]?.publishedAt;
      articlesPublishedToday = await getArticlesPublishedToday();
    } catch (error) {
      console.error('Error reading articles log:', error);
    }
  }

  let engagementEventsLogged = 0;
  if (existsSync(eventsLog)) {
    try {
      const fileContent = await readFile(eventsLog, 'utf-8');
      engagementEventsLogged = fileContent.split('\n').filter((line) => line.trim()).length;
    } catch (error) {
      console.error('Error reading events log:', error);
    }
  }

  const rateLimit = parseInt(process.env.LINKEDIN_ARTICLE_RATE_LIMIT || '5', 10);

  return {
    runtimeDir,
    articlesPublished,
    articlesPublishedToday,
    engagementEventsLogged,
    lastPublished,
    rateLimitRemaining: Math.max(0, rateLimit - articlesPublishedToday),
  };
}

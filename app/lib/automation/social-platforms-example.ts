/**
 * SOCIAL PLATFORMS AUTOMATION — USAGE EXAMPLES
 *
 * This file demonstrates how to use the social-platforms module
 * in various scenarios and integration points.
 */

import {
  crossPostArticle,
  crossPostBatch,
  logTrackingEvent,
  getEngagementMetrics,
  ArticleContent,
} from './social-platforms';

/**
 * ============================================================================
 * EXAMPLE 1: Simple article cross-posting
 * ============================================================================
 */

export async function exampleBasicCrossPost() {
  const article: ArticleContent = {
    title: 'How to Build a Profitable SaaS Business',
    content: `# How to Build a Profitable SaaS Business

Discover the 7 proven strategies to launch and scale a successful SaaS company.

## 1. Find Your Niche
Focus on solving a specific problem for a specific audience...

## 2. Build an MVP
Don't spend months building. Launch a minimum viable product in weeks...

## 3. Get Early Users
Use Product Hunt, Hacker News, and Twitter to find your first 100 users...

More content here...`,
    excerpt: 'Learn the 7 proven strategies to build a profitable SaaS business',
    tags: ['saas', 'business', 'startup', 'entrepreneurship'],
    coverImage: 'https://example.com/images/saas-guide.jpg',
    originalUrl: 'https://profitengine.alreadyherellc.com/blog/saas-profitability',
    authorName: 'Stephen Franklin',
    authorBio: 'Founder of Already Here LLC. 10+ years SaaS experience.',
  };

  // Cross-post to all platforms
  const result = await crossPostArticle(article, ['medium', 'devto', 'linkedin'], {
    parallel: true,
    retries: 3,
  });

  console.log('Cross-posting complete:', {
    successCount: result.successCount,
    failureCount: result.failureCount,
    results: result.results.map((r) => ({
      platform: r.platform,
      success: r.success,
      postUrl: r.postUrl,
      error: r.error,
    })),
  });

  return result;
}

/**
 * ============================================================================
 * EXAMPLE 2: Selective platform publishing with affiliates
 * ============================================================================
 */

export async function exampleSelectivePlatformPublish() {
  const article: ArticleContent = {
    title: 'The Ultimate Guide to Cloud Hosting',
    content: `# The Ultimate Guide to Cloud Hosting

## Best Cloud Providers for Startups

### AWS
AWS dominates the cloud market with comprehensive services.
Learn more at [AWS Free Tier](https://aws.amazon.com/free)

### Vercel
Perfect for Next.js and frontend hosting.
Get started with [Vercel](https://vercel.com)

### DigitalOcean
Great for simple apps and Docker deployments.
Check out [DigitalOcean](https://www.digitalocean.com)
`,
    tags: ['cloud', 'hosting', 'devops'],
    originalUrl: 'https://profitengine.alreadyherellc.com/blog/cloud-hosting',
  };

  // Only publish to Dev.to (developer audience)
  const result = await crossPostArticle(article, ['devto'], {
    parallel: true,
  });

  return result;
}

/**
 * ============================================================================
 * EXAMPLE 3: Batch publishing multiple articles
 * ============================================================================
 */

export async function exampleBatchPublish() {
  const articles: ArticleContent[] = [
    {
      title: 'Article 1: Quick wins for scaling',
      content: 'Content for article 1...',
      tags: ['scaling', 'startup'],
      originalUrl: 'https://profitengine.alreadyherellc.com/blog/scaling-quick-wins',
    },
    {
      title: 'Article 2: Founder burnout and recovery',
      content: 'Content for article 2...',
      tags: ['founder', 'wellness'],
      originalUrl: 'https://profitengine.alreadyherellc.com/blog/founder-burnout',
    },
    {
      title: 'Article 3: Pricing strategies',
      content: 'Content for article 3...',
      tags: ['pricing', 'monetization'],
      originalUrl: 'https://profitengine.alreadyherellc.com/blog/pricing-strategies',
    },
  ];

  // Publish all articles to all platforms
  const results = await crossPostBatch(articles, ['medium', 'devto', 'linkedin'], {
    parallel: true, // Each article posts in parallel
    retries: 3,
  });

  console.log(`Published ${results.length} articles:`, {
    totalSuccesses: results.reduce((sum, r) => sum + r.successCount, 0),
    totalFailures: results.reduce((sum, r) => sum + r.failureCount, 0),
  });

  return results;
}

/**
 * ============================================================================
 * EXAMPLE 4: Webhook integration (from platform)
 * ============================================================================
 */

export async function exampleWebhookHandler(webhookData: Record<string, unknown>) {
  // This would be called from your webhook handler when a platform sends engagement data

  // Example: Dev.to webhook for article view
  if (webhookData.event_type === 'view') {
    await logTrackingEvent({
      eventId: `event-${Date.now()}`,
      platform: 'devto',
      postId: String(webhookData.article_id),
      postUrl: String(webhookData.article_url),
      eventType: 'view',
      userId: String(webhookData.user_id),
      timestamp: new Date().toISOString(),
      metadata: {
        referer: webhookData.referer,
        country: webhookData.country,
      },
    });
  }

  // Example: LinkedIn webhook for engagement
  if (webhookData.activity_type === 'LIKE') {
    await logTrackingEvent({
      eventId: `event-${Date.now()}`,
      platform: 'linkedin',
      postId: String(webhookData.post_id),
      postUrl: String(webhookData.post_url),
      eventType: 'like',
      userId: String(webhookData.user_id),
      timestamp: new Date().toISOString(),
    });
  }
}

/**
 * ============================================================================
 * EXAMPLE 5: Engagement metrics dashboard
 * ============================================================================
 */

export async function exampleFetchMetrics() {
  // After publishing an article, fetch engagement metrics
  const mediumMetrics = await getEngagementMetrics('medium', 'abc123');
  const devtoMetrics = await getEngagementMetrics('devto', '456def');
  const linkedinMetrics = await getEngagementMetrics('linkedin', 'ghi789');

  console.log('Engagement Dashboard:', {
    medium: mediumMetrics,
    devto: devtoMetrics,
    linkedin: linkedinMetrics,
  });

  // Calculate total engagement across platforms
  const totalViews = [mediumMetrics, devtoMetrics, linkedinMetrics]
    .filter((m) => m)
    .reduce((sum, m) => sum + (m?.views || 0), 0);

  const totalEngagement = [mediumMetrics, devtoMetrics, linkedinMetrics]
    .filter((m) => m)
    .reduce(
      (sum, m) =>
        sum +
        (m?.likes || 0) +
        (m?.shares || 0) +
        (m?.comments || 0),
      0
    );

  console.log('Total Metrics:', {
    views: totalViews,
    engagement: totalEngagement,
    engagementRate: totalViews > 0 ? ((totalEngagement / totalViews) * 100).toFixed(2) + '%' : '0%',
  });
}

/**
 * ============================================================================
 * EXAMPLE 6: Using with API endpoint
 * ============================================================================
 */

export async function exampleAPICall() {
  // This demonstrates how to call the API endpoint

  const response = await fetch('/api/automation/social-platforms/publish', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // Optional: include token if AUTOMATION_API_TOKEN is set
      // 'Authorization': `Bearer ${process.env.AUTOMATION_API_TOKEN}`,
    },
    body: JSON.stringify({
      title: 'How I Built a $100K SaaS in 6 Months',
      content: '# My Journey\n\nHere is my story...',
      excerpt: 'Learn how I built a profitable SaaS startup',
      tags: ['saas', 'case-study', 'startup'],
      coverImage: 'https://example.com/cover.jpg',
      originalUrl: 'https://profitengine.alreadyherellc.com/blog/saas-case-study',
      platforms: ['medium', 'devto', 'linkedin'],
      publishImmediate: true,
      parallel: true,
      retries: 3,
    }),
  });

  const result = await response.json();
  console.log('API Response:', result);

  return result;
}

/**
 * ============================================================================
 * EXAMPLE 7: Webhook endpoint for platform events
 * ============================================================================
 */

export async function exampleWebhookEndpointHandler(
  request: Request
): Promise<Response> {
  const body = (await request.json()) as Record<string, unknown>;
  const platform = body.platform as string;

  try {
    // Log the event
    await logTrackingEvent({
      eventId: `event-${Date.now()}`,
      platform: platform as 'medium' | 'devto' | 'linkedin',
      postId: String(body.postId),
      postUrl: String(body.postUrl),
      eventType: (body.eventType as 'view' | 'like' | 'share' | 'comment' | 'read_time') || 'view',
      userId: body.userId ? String(body.userId) : undefined,
      timestamp: new Date().toISOString(),
      metadata: body.metadata as Record<string, unknown>,
    });

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Event logged',
      }),
      { status: 200 }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to log event',
      }),
      { status: 500 }
    );
  }
}

/**
 * ============================================================================
 * EXAMPLE 8: Environment setup and configuration
 * ============================================================================
 */

export function exampleEnvironmentSetup() {
  return {
    description: 'Required environment variables for social-platforms module',
    variables: {
      // Platform API tokens
      MEDIUM_API_TOKEN:
        'your-medium-integration-token (https://medium.com/me/settings/security)',
      DEVTO_API_KEY: 'your-devto-api-key (https://dev.to/settings/extensions)',
      LINKEDIN_ACCESS_TOKEN: 'your-linkedin-oauth-access-token',
      LINKEDIN_AUTHOR_ID: 'your-linkedin-profile-id (digits only)',

      // Affiliate links (JSON object)
      AFFILIATE_LINKS: JSON.stringify({
        'AWS': 'https://aws.amazon.com/?refid=yourref',
        'Vercel': 'https://vercel.com/?refid=yourref',
        'DigitalOcean': 'https://digitalocean.com/?refid=yourref',
        'GitHub Copilot': 'https://github.com/copilot?refid=yourref',
      }),

      // Tracking and URLs
      SOCIAL_CANONICAL_URL: 'https://profitengine.alreadyherellc.com',
      SOCIAL_TRACKING_PIXEL_ID: 'your-google-analytics-id-or-custom-pixel',
      SOCIAL_WEBHOOK_EVENTS: 'https://profitengine.alreadyherellc.com/api/webhooks/social',

      // Runtime directory
      RUNTIME_DATA_DIR: '.runtime/social-platforms',

      // Optional: API security
      AUTOMATION_API_TOKEN: 'optional-token-for-api-security',
    },

    setup: {
      medium: [
        '1. Go to https://medium.com/me/settings/security',
        '2. Scroll to "Apps and Publications"',
        '3. Create a new application with integration token',
        '4. Copy token to MEDIUM_API_TOKEN',
      ],

      devto: [
        '1. Go to https://dev.to/settings/extensions',
        '2. Generate API key under "API Keys"',
        '3. Copy key to DEVTO_API_KEY',
      ],

      linkedin: [
        '1. Register your app at https://www.linkedin.com/developers/apps',
        '2. Get OAuth access token via LinkedIn sign-in flow',
        '3. Find your author/person URN (LINKEDIN_AUTHOR_ID)',
        '4. Set both LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_ID',
      ],
    },
  };
}

/**
 * ============================================================================
 * EXAMPLE 9: Integration with blog publishing workflow
 * ============================================================================
 */

export async function exampleBlogPublishingWorkflow(blogPostData: {
  title: string;
  body: string;
  excerpt: string;
  featuredImage?: string;
  tags: string[];
  slug: string;
}) {
  const article: ArticleContent = {
    title: blogPostData.title,
    content: blogPostData.body,
    excerpt: blogPostData.excerpt,
    tags: blogPostData.tags,
    coverImage: blogPostData.featuredImage,
    originalUrl: `https://profitengine.alreadyherellc.com/blog/${blogPostData.slug}`,
    authorName: 'Stephen Franklin',
  };

  // Step 1: Publish to platforms
  console.log('Publishing to social platforms...');
  const result = await crossPostArticle(article, ['medium', 'devto', 'linkedin'], {
    parallel: true,
    retries: 3,
  });

  // Step 2: Log results
  console.log('Publishing results:', {
    successCount: result.successCount,
    failureCount: result.failureCount,
    platforms: result.results.map((r) => ({
      platform: r.platform,
      success: r.success,
      url: r.postUrl,
    })),
  });

  // Step 3: Return cross-post URLs for inclusion in blog post
  const crossPostLinks = result.results
    .filter((r) => r.success && r.postUrl)
    .map((r) => ({
      platform: r.platform,
      url: r.postUrl,
    }));

  return {
    success: result.successCount > 0,
    crossPostLinks,
    fullResult: result,
  };
}

/**
 * ============================================================================
 * EXAMPLE 10: Error handling and retry patterns
 * ============================================================================
 */

export async function exampleErrorHandling() {
  const article: ArticleContent = {
    title: 'Test Article',
    content: 'Test content...',
    tags: ['test'],
  };

  try {
    const result = await crossPostArticle(
      article,
      ['medium', 'devto', 'linkedin'],
      {
        parallel: false, // Sequential to see which fails first
        retries: 5, // More retries for unreliable networks
      }
    );

    // Check which platforms failed
    const failures = result.results.filter((r) => !r.success);

    if (failures.length > 0) {
      console.log('Publication failures:', failures);

      // Optionally retry failed platforms only
      for (const failed of failures) {
        console.log(`Retrying ${failed.platform}...`);
        // Could re-attempt here
      }
    }

    return result;
  } catch (error) {
    console.error('Cross-posting failed:', error);
    // Handle catastrophic failure (network down, etc)
    // Could queue for retry, send alert, etc
  }
}

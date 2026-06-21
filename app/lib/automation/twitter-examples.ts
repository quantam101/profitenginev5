/**
 * TWITTER THREADS AUTOMATION EXAMPLES
 *
 * Demonstrates how to use Twitter Threads automation module with:
 * - Simple thread publishing
 * - Affiliate link injection
 * - Engagement metric tracking
 * - Integration with Master Orchestrator
 * - Webhook setup for real-time updates
 */

import {
  generateThread,
  publishThread,
  getThreadMetrics,
  logEngagementEvent,
  ThreadContent,
  ThreadPublishConfig,
} from './twitter';

/**
 * EXAMPLE 1: Generate and publish a simple thread
 */
export async function example1_SimpleThreadPublish() {
  const content: ThreadContent = {
    title: '10 Ways to Automate Your Income Stream',
    content: `Start with affiliate marketing. Find products that align with your audience and build trust through honest recommendations.

Next, create digital products. Design templates, courses, or guides that solve real problems for your market.

Then, set up automated email sequences. Use tools to nurture leads and generate sales while you sleep.

Implement content automation. Schedule posts across platforms using tools like Buffer and Later.

Build passive funnels. Create lead magnets that automatically qualify and segment your audience.

Use automation tools for customer service. Chatbots and automated emails handle routine inquiries.

Finally, track everything. Use analytics to identify what works and optimize your best performers.`,
    excerpt:
      'A comprehensive guide to automating multiple income streams in 2024',
    hashtags: ['#PassiveIncome', '#Entrepreneurship', '#Automation'],
    ctaLink: 'https://example.com/automation-guide',
    mentions: ['@twitteruser1', '@twitteruser2'],
  };

  const result = await publishThread({
    threadContent: content,
    publishImmediate: true,
    dryRun: true, // Set to false for production
  });

  console.log('Thread published:', {
    success: result.success,
    threadId: result.firstTweetId,
    tweetCount: result.tweets?.length,
    firstTweetUrl: result.firstTweetUrl,
  });

  return result;
}

/**
 * EXAMPLE 2: Publish thread with affiliate link injection
 */
export async function example2_ThreadWithAffiliateLinks() {
  const content: ThreadContent = {
    title: 'Best Tools for Content Creators',
    content: `Looking to level up your content game? Here are my favorite tools.

Buffer is perfect for scheduling posts across multiple platforms. It saves hours every week.

Midjourney changed my AI image generation workflow. The quality is incredible.

Descript makes video editing so much faster. Cut out silence, edit like text.

ConvertKit is the best email platform for creators. The growth features are unmatched.

Typefully helps you write better threads on Twitter. Worth every penny.

Zapier automates everything between your tools. Connect any app to any app.`,
    excerpt: 'Tools I actually use and recommend',
    hashtags: ['#ContentCreation', '#Tools', '#Productivity'],
    affiliateLinks: {
      Buffer: 'https://affiliate.buffer.com/promo',
      Midjourney: 'https://affiliate.midjourney.com',
      Descript: 'https://affiliate.descript.com',
      ConvertKit: 'https://affiliate.convertkit.com',
      Typefully: 'https://affiliate.typefully.com',
      Zapier: 'https://affiliate.zapier.com',
    },
    ctaLink: 'https://example.com/tools-list',
  };

  const result = await publishThread({
    threadContent: content,
    publishImmediate: true,
    dryRun: true,
  });

  console.log('Thread with affiliates published:', {
    success: result.success,
    tweetCount: result.tweets?.length,
  });

  return result;
}

/**
 * EXAMPLE 3: Generate thread without publishing
 */
export async function example3_GenerateThreadPreview() {
  const content: ThreadContent = {
    title: 'The Future of Automation',
    content: `AI is changing everything. Let me break down the biggest opportunities.

First, content creation is being disrupted. LLMs can generate drafts in seconds. But human judgment still matters most.

Second, customer support is being automated. Chatbots handle 80% of routine questions. Support staff focus on complex issues.

Third, data analysis is democratizing. Anyone can ask questions and get insights without knowing SQL.

Fourth, code generation is accelerating development. Developers now focus on architecture, not boilerplate.

Fifth, marketing automation is getting smarter. Personalization at scale is finally possible.

The winners will be those who use AI to augment human work, not replace it.`,
    excerpt: 'How AI is reshaping business in 2024',
    hashtags: ['#AI', '#Automation', '#Future'],
  };

  // Just generate, don't publish
  const thread = await generateThread(content);

  console.log('Generated thread preview:', {
    title: thread.threadTitle,
    tweetCount: thread.tweetCount,
    tweets: thread.tweets.map((t) => ({
      order: t.order,
      text: t.text.substring(0, 50) + '...',
      length: t.text.length,
    })),
    estimatedEngagement: thread.estimatedEngagement,
  });

  return thread;
}

/**
 * EXAMPLE 4: Get metrics for a published thread
 */
export async function example4_GetThreadMetrics(threadId: string) {
  const metrics = await getThreadMetrics(threadId);

  if (metrics) {
    console.log('Thread metrics:', {
      threadId: metrics.threadId,
      tweetCount: metrics.tweetCount,
      impressions: metrics.totalImpressions,
      engagement: metrics.totalEngagement,
      engagementRate: metrics.engagementRate.toFixed(2) + '%',
      breakdown: {
        likes: metrics.likes,
        retweets: metrics.retweets,
        replies: metrics.replies,
        bookmarks: metrics.bookmarks,
        clicks: metrics.clicks,
      },
    });
  }

  return metrics;
}

/**
 * EXAMPLE 5: Log engagement event (for webhook integration)
 */
export async function example5_LogEngagementEvent(
  threadId: string,
  tweetId: string
) {
  await logEngagementEvent({
    eventId: `evt-${Date.now()}`,
    threadId,
    tweetId,
    eventType: 'like',
    userId: 'twitter-user-123',
    userName: 'john_doe',
    timestamp: new Date().toISOString(),
    metadata: {
      source: 'webhook',
      userFollowers: 10000,
    },
  });

  console.log('Engagement event logged');
}

/**
 * EXAMPLE 6: Master Orchestrator integration
 *
 * This shows how to integrate Twitter threads with the orchestrator
 */
export async function example6_OrchestratorIntegration() {
  // This is how you would structure a task in the orchestrator config
  const twitterTask = {
    id: 'twitter-thread-publish',
    name: 'Publish Twitter Thread',
    description: 'Auto-publish weekly thread on automation',
    type: 'twitter', // Task type
    enabled: true,
    priority: 'normal',
    timeout: 60000, // 1 minute timeout
    retryMaxAttempts: 3,
    retryBackoffMs: 5000,
    dependencies: [
      {
        taskId: 'content-generation',
        required: true,
        wait: true,
      },
    ],
    metadata: {
      title: 'Weekly Automation Tips',
      contentSource: 'blog-post',
      hashtagCategories: ['automation', 'business'],
      scheduleDay: 'Monday',
      scheduleTime: '09:00 UTC',
    },
  };

  console.log('Task configuration for orchestrator:', twitterTask);

  return twitterTask;
}

/**
 * EXAMPLE 7: Webhook setup for engagement tracking
 */
export async function example7_WebhookSetup() {
  const webhookConfig = {
    endpoint: '/api/automation/twitter/webhook',
    method: 'POST',
    events: [
      'like',
      'retweet',
      'reply',
      'bookmark',
      'click',
      'impression',
    ],
    signature: {
      algorithm: 'HMAC-SHA256',
      headerName: 'x-twitter-signature',
      secretEnvVar: 'TWITTER_WEBHOOK_SECRET',
    },
    retryPolicy: {
      maxAttempts: 3,
      backoffMs: 5000,
    },
  };

  console.log('Webhook configuration:', webhookConfig);

  // Example webhook payload
  const webhookPayload = {
    threadId: '1234567890',
    tweetId: '1234567891',
    eventType: 'like',
    userId: 'twitter-user-123',
    userName: 'john_doe',
    timestamp: new Date().toISOString(),
    metadata: {
      userFollowers: 50000,
      userVerified: true,
    },
  };

  console.log('Example webhook payload:', webhookPayload);

  return { webhookConfig, webhookPayload };
}

/**
 * EXAMPLE 8: Full workflow - generate, publish, and track
 */
export async function example8_FullWorkflow() {
  console.log('=== Full Twitter Threads Workflow ===\n');

  // Step 1: Generate content
  const content: ThreadContent = {
    title: 'Building in Public: My Journey',
    content: `I started building in public 6 months ago. Here's what changed.

First, I became more accountable. Sharing goals publicly forces you to follow through.

Second, I attracted collaborators. People reach out with ideas and partnerships.

Third, I built an audience. Transparency and sharing value earned their trust.

Fourth, I got faster feedback. People tell you what's working and what's not.

Fifth, I created opportunities. Sponsorships and partnerships appeared naturally.

Sixth, I improved my craft. Teaching others forces you to understand deeply.

If you want to grow, consider building in public.`,
    excerpt: 'How building in public transformed my business',
    hashtags: ['#BuildInPublic', '#Entrepreneurship'],
    ctaLink: 'https://example.com/building-in-public',
  };

  // Step 2: Generate thread
  console.log('Generating thread...');
  const thread = await generateThread(content);
  console.log(`Generated ${thread.tweetCount} tweets\n`);

  // Step 3: Publish
  console.log('Publishing thread (dry-run)...');
  const publishResult = await publishThread({
    threadContent: content,
    publishImmediate: true,
    dryRun: true,
    webhookUrl: 'https://example.com/webhook',
  });

  if (publishResult.success) {
    console.log(`Published! Thread ID: ${publishResult.threadId}\n`);

    // Step 4: Log some simulated engagement
    if (publishResult.firstTweetId) {
      await logEngagementEvent({
        eventId: 'evt-like-1',
        threadId: publishResult.firstTweetId,
        tweetId: publishResult.firstTweetId,
        eventType: 'like',
        userName: 'sample_user',
        timestamp: new Date().toISOString(),
      });

      // Step 5: Get metrics
      const metrics = await getThreadMetrics(publishResult.firstTweetId);
      if (metrics) {
        console.log('Initial metrics:');
        console.log(`  Total engagement: ${metrics.totalEngagement}`);
        console.log(`  Likes: ${metrics.likes}`);
      }
    }
  } else {
    console.error(`Failed to publish: ${publishResult.error}`);
  }
}

// Run example if called directly
if (require.main === module) {
  (async () => {
    console.log('Running Twitter Threads Examples\n');

    console.log('1. Simple thread publish:');
    await example1_SimpleThreadPublish();

    console.log('\n2. Thread with affiliate links:');
    await example2_ThreadWithAffiliateLinks();

    console.log('\n3. Generate thread preview:');
    await example3_GenerateThreadPreview();

    console.log('\n6. Orchestrator integration:');
    await example6_OrchestratorIntegration();

    console.log('\n7. Webhook setup:');
    await example7_WebhookSetup();

    console.log('\n8. Full workflow:');
    await example8_FullWorkflow();
  })();
}

/**
 * FACELESS VIDEOS AUTOMATION — Integration Examples
 *
 * Complete working examples for integrating faceless video automation
 * into your application workflows.
 */

import {
  generateAndPublishFacelessVideo,
  batchGenerateVideos,
  scheduleVideoGeneration,
  processScheduledVideos,
  getVideoMetrics,
  FacelessVideoScript,
} from './faceless-videos';

// ============================================================================
// EXAMPLE 1: Generate Single Video on Demand
// ============================================================================

/**
 * Generate a single video and publish immediately
 */
export async function example1_quickGenerate() {
  console.log('Example 1: Quick Generate Single Video');

  try {
    const result = await generateAndPublishFacelessVideo(1, {
      videoProvider: 'replicate',
      platforms: ['youtube', 'tiktok', 'instagram'],
      publishImmediately: true,
    });

    console.log('Success:', result.success);
    console.log('Results:', result.results);

    // Log results
    result.results.forEach((r) => {
      if (r.success) {
        console.log(`✓ ${r.platform}: ${r.videoUrl}`);
      } else {
        console.log(`✗ ${r.platform}: ${r.error}`);
      }
    });
  } catch (error) {
    console.error('Generation failed:', error);
  }
}

// ============================================================================
// EXAMPLE 2: Batch Generate Weekly Content
// ============================================================================

/**
 * Generate an entire week's worth of content in batch
 * - 7 videos total
 * - Generate 2 simultaneously for speed
 * - Post to YouTube, TikTok, Instagram
 */
export async function example2_weeklyBatchGeneration() {
  console.log('Example 2: Weekly Batch Generation');

  try {
    const result = await batchGenerateVideos({
      postNumbers: [1, 2, 3, 4, 5, 6, 7], // 7 videos
      videoProvider: 'replicate',
      platforms: ['youtube', 'tiktok', 'instagram'],
      simultaneousGenerations: 2, // Max 2 at a time
    });

    console.log('=== Batch Results ===');
    console.log(`Generated: ${result.generated.length}`);
    console.log(`Failed: ${result.failed.length}`);
    console.log(`Success: ${result.success}`);

    if (result.failed.length > 0) {
      console.log('Failed posts:');
      result.failed.forEach((f) => {
        console.log(`  Post ${f.postNumber}: ${f.error}`);
      });
    }
  } catch (error) {
    console.error('Batch generation failed:', error);
  }
}

// ============================================================================
// EXAMPLE 3: Schedule Videos for Specific Times
// ============================================================================

/**
 * Schedule 5 videos to post at specific times throughout the week
 */
export async function example3_scheduleWeeklyVideos() {
  console.log('Example 3: Schedule Weekly Videos');

  const schedules = [
    { postNumber: 1, time: '2024-06-24T09:00:00Z' }, // Monday 9 AM
    { postNumber: 2, time: '2024-06-24T18:00:00Z' }, // Monday 6 PM
    { postNumber: 3, time: '2024-06-25T09:00:00Z' }, // Tuesday 9 AM
    { postNumber: 4, time: '2024-06-26T14:00:00Z' }, // Wednesday 2 PM
    { postNumber: 5, time: '2024-06-27T19:00:00Z' }, // Thursday 7 PM
  ];

  try {
    for (const schedule of schedules) {
      const result = await scheduleVideoGeneration(
        schedule.postNumber,
        {
          scheduledTime: new Date(schedule.time),
          timezone: 'UTC',
        },
        {
          videoProvider: 'replicate',
          platforms: ['youtube', 'tiktok'],
        }
      );

      if (result.success) {
        console.log(`✓ Post ${schedule.postNumber} scheduled for ${schedule.time}`);
      } else {
        console.log(`✗ Post ${schedule.postNumber} failed: ${result.error}`);
      }
    }
  } catch (error) {
    console.error('Scheduling failed:', error);
  }
}

// ============================================================================
// EXAMPLE 4: Daily Content Publishing Pipeline
// ============================================================================

/**
 * Generate and schedule 30 videos for a month
 * - Schedule one per day
 * - Each day at 10 AM UTC
 */
export async function example4_monthlyContentPipeline() {
  console.log('Example 4: Monthly Content Pipeline (30 videos)');

  try {
    const scheduledIds: string[] = [];

    // Generate schedules for 30 days
    for (let day = 1; day <= 30; day++) {
      const date = new Date();
      date.setDate(date.getDate() + day);
      date.setHours(10, 0, 0, 0); // 10 AM every day

      const result = await scheduleVideoGeneration(day, {
        scheduledTime: date,
        timezone: 'UTC',
        repeatDaily: false, // One-time posting
      });

      if (result.success && result.scheduledId) {
        scheduledIds.push(result.scheduledId);
      }
    }

    console.log(`Scheduled ${scheduledIds.length} videos for the month`);
    console.log('Set up cron job to run /api/automation/faceless-videos/process-scheduled');
  } catch (error) {
    console.error('Pipeline setup failed:', error);
  }
}

// ============================================================================
// EXAMPLE 5: Monitor Metrics and Performance
// ============================================================================

/**
 * Get current metrics and display performance dashboard
 */
export async function example5_metricsAndAnalytics() {
  console.log('Example 5: Metrics & Analytics');

  try {
    const metrics = await getVideoMetrics();

    console.log('\n=== Video Generation Metrics ===');
    console.log(`Total Videos Generated: ${metrics.totalGenerated}`);
    console.log(`Total Videos Published: ${metrics.totalPublished}`);
    console.log(`Success Rate: ${metrics.successRate.toFixed(2)}%`);

    console.log('\n=== Provider Usage ===');
    Object.entries(metrics.providerUsage).forEach(([provider, count]) => {
      console.log(`  ${provider}: ${count} videos`);
    });

    console.log('\n=== Platform Usage ===');
    Object.entries(metrics.platformUsage).forEach(([platform, count]) => {
      console.log(`  ${platform}: ${count} uploads`);
    });

    // Calculate monthly cost estimate
    const costPerVideo = 0.08; // Approximate
    const monthlyCost = metrics.totalGenerated * costPerVideo;
    console.log(`\nEstimated Monthly Cost: $${monthlyCost.toFixed(2)}`);
  } catch (error) {
    console.error('Metrics fetch failed:', error);
  }
}

// ============================================================================
// EXAMPLE 6: Process Scheduled Videos (Cron Job)
// ============================================================================

/**
 * Process scheduled videos - run this via cron job daily
 * Set up cron: 0 8 * * * curl -X POST /api/automation/faceless-videos/process-scheduled
 */
export async function example6_cronProcessScheduled() {
  console.log('Example 6: Process Scheduled Videos (Cron Job)');

  try {
    console.log('Processing scheduled videos...');
    const result = await processScheduledVideos();

    console.log(`Processed: ${result.processed} videos`);
    console.log(`Errors: ${result.errors.length}`);

    if (result.errors.length > 0) {
      console.log('Errors encountered:');
      result.errors.forEach((e) => {
        console.log(`  ${e.scheduleId}: ${e.error}`);
      });
    }
  } catch (error) {
    console.error('Processing failed:', error);
  }
}

// ============================================================================
// EXAMPLE 7: Custom Script Generation (No Calendar)
// ============================================================================

/**
 * Generate video with custom script instead of parsing calendar
 */
export async function example7_customScriptGeneration() {
  console.log('Example 7: Custom Script Generation');

  const customScript: FacelessVideoScript = {
    title: 'The 3-Step Formula to 6-Figure Online Income',
    description: 'Discover how to build a 6-figure business online in 90 days',
    hook: 'Most people fail at online business because they ignore this ONE critical step...',
    mainPoints: [
      'Pick a proven business model (not your passion)',
      'Get 10 customers in the first week using this exact system',
      'Scale to $100K/month using automation',
    ],
    cta: 'Join my free masterclass: https://profitengine.alreadyherellc.com/masterclass',
    duration: 90,
    tags: ['business', 'entrepreneurship', 'online income', 'passive income'],
    affiliateLinks: {
      'Zapier Automation': 'https://zapier.com/partners/...',
      'WebFlow': 'https://webflow.com/ref/...',
    },
    publishPlatforms: ['youtube', 'tiktok', 'instagram'],
    optimizeForPlatform: 'youtube',
  };

  try {
    // Note: This would need to be integrated into generateReplicateFacelessVideo
    // to work with custom scripts instead of parsing calendar
    console.log('Video generation with custom script:');
    console.log(`Title: ${customScript.title}`);
    console.log(`Duration: ${customScript.duration}s`);
    console.log(`Platforms: ${customScript.publishPlatforms?.join(', ')}`);

    // In production, you'd pass this to generateReplicateFacelessVideo
    // and it would generate a video with this exact content
  } catch (error) {
    console.error('Custom script generation failed:', error);
  }
}

// ============================================================================
// EXAMPLE 8: Error Recovery and Fallback
// ============================================================================

/**
 * Demonstrate error handling with provider fallback
 */
export async function example8_fallbackHandling() {
  console.log('Example 8: Error Recovery & Fallback');

  const providers: Array<'d-id' | 'synthesia' | 'replicate'> = [
    'replicate',
    'd-id',
    'synthesia',
  ];

  try {
    let success = false;

    for (const provider of providers) {
      console.log(`Attempting with ${provider}...`);

      try {
        const result = await generateAndPublishFacelessVideo(1, {
          videoProvider: provider,
          platforms: ['youtube'],
        });

        if (result.success) {
          console.log(`✓ Success with ${provider}`);
          success = true;
          break;
        }
      } catch (providerError) {
        console.log(`✗ ${provider} failed: ${providerError}`);
        continue;
      }
    }

    if (!success) {
      console.log('All providers failed - check credentials and logs');
    }
  } catch (error) {
    console.error('Fallback handling failed:', error);
  }
}

// ============================================================================
// EXAMPLE 9: Slack Integration for Notifications
// ============================================================================

/**
 * Send notifications to Slack after video generation
 */
export async function example9_slackNotifications() {
  console.log('Example 9: Slack Integration');

  const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL;

  if (!slackWebhookUrl) {
    console.log('SLACK_WEBHOOK_URL not configured');
    return;
  }

  try {
    const metrics = await getVideoMetrics();

    const message = {
      blocks: [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: 'Video Generation Report',
            emoji: true,
          },
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*Total Generated:*\n${metrics.totalGenerated}`,
            },
            {
              type: 'mrkdwn',
              text: `*Success Rate:*\n${metrics.successRate.toFixed(1)}%`,
            },
            {
              type: 'mrkdwn',
              text: `*Published:*\n${metrics.totalPublished}`,
            },
            {
              type: 'mrkdwn',
              text: `*Top Provider:*\n${
                Object.entries(metrics.providerUsage).sort(([, a], [, b]) => b - a)[0]?.[0] ||
                'N/A'
              }`,
            },
          ],
        },
      ],
    };

    await fetch(slackWebhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message),
    });

    console.log('✓ Slack notification sent');
  } catch (error) {
    console.error('Slack notification failed:', error);
  }
}

// ============================================================================
// EXAMPLE 10: API Route Handler Integration
// ============================================================================

/**
 * Complete API route handler showing integration
 */
export async function example10_apiRouteHandler() {
  console.log('Example 10: API Route Handler');

  // This is how you'd integrate into a Next.js API route:
  const exampleHandler = async (req: { method?: string; body?: Record<string, unknown> }) => {
    if (req.method === 'POST') {
      const { action, postNumber, platforms } = req.body as Record<string, unknown>;

      switch (action) {
        case 'generate':
          return await generateAndPublishFacelessVideo(postNumber as number, {
            videoProvider: 'replicate',
            platforms: platforms as Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>,
          });

        case 'schedule':
          const { scheduledTime } = req.body as Record<string, unknown>;
          return await scheduleVideoGeneration(
            postNumber as number,
            {
              scheduledTime: new Date(scheduledTime as string),
            },
            {
              videoProvider: 'replicate',
              platforms: platforms as Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>,
            }
          );

        case 'metrics':
          return await getVideoMetrics();

        default:
          throw new Error('Unknown action');
      }
    }
  };

  console.log('API handler ready for integration');
}

// ============================================================================
// EXAMPLE 11: Webhook Handling for Async Generation
// ============================================================================

/**
 * Handle webhooks from Replicate/D-ID/Synthesia
 */
export async function example11_webhookHandler(webhookPayload: {
  videoId: string;
  status: string;
  output?: string;
  error?: string;
}) {
  console.log('Example 11: Webhook Handler');

  const { videoId, status, output, error } = webhookPayload;

  console.log(`Webhook received for video ${videoId}: ${status}`);

  if (status === 'completed' && output) {
    console.log(`Video ready at: ${output}`);
    // Trigger auto-publishing here
    // Notify user via email/Slack
    // Update database record
  } else if (status === 'failed') {
    console.error(`Video generation failed: ${error}`);
    // Notify user of failure
    // Log error for debugging
    // Optionally retry with different provider
  }
}

// ============================================================================
// EXAMPLE 12: Full Workflow Integration
// ============================================================================

/**
 * Complete end-to-end workflow example
 */
export async function example12_fullWorkflow() {
  console.log('Example 12: Full End-to-End Workflow\n');

  try {
    // Step 1: Check current metrics
    console.log('Step 1: Checking metrics...');
    const initialMetrics = await getVideoMetrics();
    console.log(`Current success rate: ${initialMetrics.successRate.toFixed(1)}%\n`);

    // Step 2: Schedule 7 videos for the week
    console.log('Step 2: Scheduling weekly content...');
    const schedulePromises = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() + i);
      date.setHours(10, 0, 0, 0);

      return scheduleVideoGeneration(i + 1, {
        scheduledTime: date,
        timezone: 'UTC',
      });
    });

    await Promise.all(schedulePromises);
    console.log('7 videos scheduled\n');

    // Step 3: Generate high-priority videos immediately
    console.log('Step 3: Generating priority content...');
    const priorityResult = await batchGenerateVideos({
      postNumbers: [1, 2],
      videoProvider: 'replicate',
      platforms: ['youtube', 'tiktok'],
      simultaneousGenerations: 2,
    });

    console.log(`Generated: ${priorityResult.generated.length} videos\n`);

    // Step 4: Get updated metrics
    console.log('Step 4: Updated metrics...');
    const finalMetrics = await getVideoMetrics();
    console.log(`Total videos generated: ${finalMetrics.totalGenerated}`);
    console.log(`Success rate: ${finalMetrics.successRate.toFixed(1)}%`);
    console.log(`Platform breakdown:`, finalMetrics.platformUsage);

    console.log('\n✓ Workflow complete!');
  } catch (error) {
    console.error('Workflow failed:', error);
  }
}

// ============================================================================
// EXPORT for use in applications
// ============================================================================

export const examples = {
  quickGenerate: example1_quickGenerate,
  weeklyBatch: example2_weeklyBatchGeneration,
  scheduleWeekly: example3_scheduleWeeklyVideos,
  monthlyPipeline: example4_monthlyContentPipeline,
  metrics: example5_metricsAndAnalytics,
  processCron: example6_cronProcessScheduled,
  customScript: example7_customScriptGeneration,
  fallback: example8_fallbackHandling,
  slack: example9_slackNotifications,
  apiHandler: example10_apiRouteHandler,
  webhook: example11_webhookHandler,
  fullWorkflow: example12_fullWorkflow,
};

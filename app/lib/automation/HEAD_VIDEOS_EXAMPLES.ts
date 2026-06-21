/**
 * HEAD VIDEO AUTOMATION - USAGE EXAMPLES
 *
 * Complete working examples for all features of the head video automation system
 */

import {
  processAndPublishHeadVideo,
  getVideoAnalytics,
  HeadVideoScript,
  VideoProcessingOptions,
  ProcessedVideo,
  Transcript,
  VideoUploadResult,
} from './head-videos';

// ============================================================================
// EXAMPLE 1: BASIC VIDEO PROCESSING AND UPLOAD
// ============================================================================

/**
 * Process a simple coaching video and upload to YouTube
 */
export async function example1_basicCoachingVideo() {
  const script: HeadVideoScript = {
    id: 'coaching-001',
    title: 'Personal Branding Mastery: Build Your Authority Online',
    description:
      'Learn how to build a powerful personal brand that attracts ideal clients and opportunities. In this coaching session, we cover the psychology of personal branding, content strategy, and audience engagement.',
    hook: 'Did you know that 92% of people trust recommendations from individuals over brands? In the next 10 minutes, you\'ll discover the exact framework we used to build a 6-figure personal brand from scratch.',
    mainPoints: [
      'The psychology of personal branding and why it matters',
      'How to define your unique value proposition',
      'Content strategy for maximum reach and engagement',
      'Building authentic connections with your audience',
    ],
    cta: 'Ready to build your personal brand? Join our free coaching session at alreadyherellc.com/coaching. Limited seats available!',
    duration: 1200, // 20 minutes
    speakerName: 'Stephen Franklin',
    publishPlatforms: ['youtube', 'coaching'],
    tags: [
      'personal-branding',
      'coaching',
      'entrepreneurship',
      'business-growth',
      'marketing',
    ],
    metadata: {
      contentType: 'coaching',
      title: 'Personal Branding Mastery',
      description: 'Complete coaching session on building personal brand',
      duration: 1200,
      speaker: 'Stephen Franklin',
      keywords: ['personal brand', 'authority', 'coaching', 'entrepreneurship'],
      affiliateLinks: {
        'Coaching Program': 'https://alreadyherellc.com/coaching',
        'Free Resources': 'https://alreadyherellc.com/resources',
        'Business Tools': 'https://alreadyherellc.com/tools',
      },
    },
  };

  const options: VideoProcessingOptions & { scheduledAt?: string; uploadPlatforms?: string[] } = {
    targetResolution: '1080p',
    fps: 30,
    bitrate: 'high',
    format: 'mp4',
    generateThumbnail: true,
    autoCaption: true,
    uploadPlatforms: ['youtube', 'coaching'],
  };

  try {
    const results = await processAndPublishHeadVideo(
      './videos/coaching-session-001.mp4',
      script,
      options
    );

    console.log('Upload Results:');
    results.forEach((result) => {
      if (result.success) {
        console.log(`✓ ${result.platform}: ${result.videoUrl}`);
        console.log(`  Video ID: ${result.videoId}`);
        console.log(`  Status: ${result.status}`);
      } else {
        console.log(`✗ ${result.platform}: ${result.error}`);
      }
    });

    return results;
  } catch (error) {
    console.error('Error processing video:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 2: WEBINAR RECORDING WITH SCHEDULING
// ============================================================================

/**
 * Process webinar recording and schedule for later publishing
 */
export async function example2_webinarWithScheduling() {
  const script: HeadVideoScript = {
    id: 'webinar-2024-12-25',
    title: 'Advanced Sales Automation Strategies for 2025',
    description:
      'Join us for a live webinar where Stephen Franklin shares advanced sales automation strategies that have generated over $500K in revenue.',
    hook: 'Most entrepreneurs waste 15+ hours a week on manual sales tasks. What if you could automate 80% of your sales process and focus on high-value activities instead?',
    mainPoints: [
      'The 3 pillars of successful sales automation',
      'Email sequences that convert',
      'CRM optimization for maximum efficiency',
      'Tools and integrations that save 10+ hours weekly',
      'Real case studies and ROI calculations',
    ],
    cta: 'Sign up for the next webinar at alreadyherellc.com/webinar. Get the free automation checklist worth $97!',
    duration: 3600, // 1 hour
    speakerName: 'Stephen Franklin',
    publishPlatforms: ['youtube', 'webinar'],
    scheduledPublish: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['sales-automation', 'webinar', 'business-tools', 'entrepreneurship'],
    metadata: {
      contentType: 'webinar',
      title: 'Advanced Sales Automation Strategies',
      description: 'Live webinar on sales automation',
      duration: 3600,
      speaker: 'Stephen Franklin',
      chapters: [
        { title: 'Introduction', timestamp: 0 },
        { title: 'The 3 Pillars of Sales Automation', timestamp: 300 },
        { title: 'Email Sequences That Convert', timestamp: 900 },
        { title: 'CRM Optimization', timestamp: 1500 },
        { title: 'Tools and Integrations', timestamp: 2100 },
        { title: 'Case Studies', timestamp: 2700 },
        { title: 'Q&A Session', timestamp: 3300 },
      ],
      affiliateLinks: {
        'Automation Tools': 'https://alreadyherellc.com/tools',
        'CRM Software': 'https://alreadyherellc.com/crm',
        'Email Platform': 'https://alreadyherellc.com/email',
      },
    },
  };

  const options: VideoProcessingOptions & { scheduledAt?: string; uploadPlatforms?: string[] } = {
    targetResolution: '1080p',
    fps: 30,
    bitrate: 'medium',
    format: 'mp4',
    generateThumbnail: true,
    autoCaption: true,
    uploadPlatforms: ['youtube', 'webinar'],
    scheduledAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  };

  try {
    const results = await processAndPublishHeadVideo(
      './videos/webinar-recording-2024-12-25.mp4',
      script,
      options
    );

    console.log('Webinar Publishing Results:');
    results.forEach((result) => {
      console.log(
        `Platform: ${result.platform} | Status: ${result.status} | Scheduled: ${result.scheduledAt}`
      );
    });

    return results;
  } catch (error) {
    console.error('Error processing webinar:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 3: BATCH PROCESSING MULTIPLE VIDEOS
// ============================================================================

/**
 * Process multiple videos in sequence (or parallel with Promise.all)
 */
export async function example3_batchProcessing() {
  const videos: Array<{ path: string; script: HeadVideoScript }> = [
    {
      path: './videos/tutorial-001.mp4',
      script: {
        id: 'tutorial-001',
        title: 'SEO Basics for Beginners',
        description: 'Learn the fundamentals of SEO',
        hook: 'SEO is dead. Just kidding, but it has changed...',
        mainPoints: ['Keyword research', 'On-page optimization', 'Link building'],
        cta: 'Get our free SEO checklist',
        duration: 600,
        publishPlatforms: ['youtube'],
        tags: ['seo', 'tutorial', 'marketing'],
      },
    },
    {
      path: './videos/tutorial-002.mp4',
      script: {
        id: 'tutorial-002',
        title: 'Content Marketing Strategy',
        description: 'Create content that converts',
        hook: 'Most content marketing efforts fail because...',
        mainPoints: [
          'Audience research',
          'Content pillars',
          'Distribution channels',
        ],
        cta: 'Download our content calendar template',
        duration: 720,
        publishPlatforms: ['youtube'],
        tags: ['content-marketing', 'tutorial', 'strategy'],
      },
    },
  ];

  const options: VideoProcessingOptions = {
    targetResolution: '1080p',
    fps: 30,
    bitrate: 'high',
    generateThumbnail: true,
    autoCaption: true,
  };

  console.log(`Processing ${videos.length} videos in batch...`);

  // Sequential processing (recommended for resource efficiency)
  const results = [];
  for (const video of videos) {
    try {
      console.log(`\nProcessing: ${video.script.title}`);
      const uploadResults = await processAndPublishHeadVideo(video.path, video.script, options);
      results.push({
        scriptId: video.script.id,
        uploads: uploadResults,
      });
    } catch (error) {
      console.error(`Error processing ${video.script.id}:`, error);
    }
  }

  console.log(`\nBatch complete: ${results.length} videos processed`);
  return results;

  // Alternative: Parallel processing (use with caution - high resource usage)
  // const results = await Promise.all(
  //   videos.map((v) => processAndPublishHeadVideo(v.path, v.script, options))
  // );
}

// ============================================================================
// EXAMPLE 4: ANALYTICS TRACKING
// ============================================================================

/**
 * Track video performance across multiple platforms
 */
export async function example4_analyticsTracking() {
  const videoIds = [
    'yt_1703072400000', // YouTube video ID
    'coaching_001',      // Coaching platform ID
    'webinar_001',       // Webinar platform ID
  ];

  console.log('Fetching analytics for all videos...\n');

  const analytics = [];
  for (const videoId of videoIds) {
    try {
      const data = await getVideoAnalytics(videoId);
      analytics.push(data);

      console.log(`Video ID: ${videoId}`);
      console.log(`Platform: ${data.platform}`);
      console.log(`Views: ${data.views}`);
      console.log(`Engagement Rate: ${data.engagementRate.toFixed(2)}%`);
      console.log(`Avg Watch Duration: ${data.avgWatchDuration} seconds`);
      console.log(`---`);
    } catch (error) {
      console.error(`Error fetching analytics for ${videoId}:`, error);
    }
  }

  // Generate summary
  const totalViews = analytics.reduce((sum, a) => sum + a.views, 0);
  const avgEngagement =
    analytics.reduce((sum, a) => sum + a.engagementRate, 0) / analytics.length;

  console.log('\nSummary Metrics:');
  console.log(`Total Views: ${totalViews}`);
  console.log(`Average Engagement: ${avgEngagement.toFixed(2)}%`);
  console.log(`Videos Tracked: ${analytics.length}`);

  return analytics;
}

// ============================================================================
// EXAMPLE 5: DIFFERENT RESOLUTION PROFILES
// ============================================================================

/**
 * Process the same video in multiple resolutions for different platforms
 */
export async function example5_multiResolutionProcessing() {
  const script: HeadVideoScript = {
    id: 'product-demo',
    title: 'Product Demo: New Feature Overview',
    description: 'See how the new feature works',
    hook: 'We just released something amazing...',
    mainPoints: ['Feature 1', 'Feature 2', 'Feature 3'],
    cta: 'Get early access at alreadyherellc.com',
    duration: 300,
    publishPlatforms: ['youtube'],
    tags: ['product-demo', 'feature'],
  };

  // High quality for desktop viewers
  console.log('Processing: High Quality (1080p)...');
  const highQuality = await processAndPublishHeadVideo(
    './videos/product-demo.mp4',
    script,
    {
      targetResolution: '1080p',
      bitrate: 'high',
      fps: 30,
      uploadPlatforms: ['youtube'],
    }
  );

  // Medium quality for general consumption
  console.log('Processing: Medium Quality (720p)...');
  const mediumQuality = await processAndPublishHeadVideo(
    './videos/product-demo.mp4',
    { ...script, id: 'product-demo-720' },
    {
      targetResolution: '720p',
      bitrate: 'medium',
      fps: 30,
      uploadPlatforms: ['coaching'],
    }
  );

  // Low quality for mobile/previews
  console.log('Processing: Low Quality (360p)...');
  const lowQuality = await processAndPublishHeadVideo(
    './videos/product-demo.mp4',
    { ...script, id: 'product-demo-360' },
    {
      targetResolution: '720p',
      bitrate: 'low',
      fps: 24,
      uploadPlatforms: ['webinar'],
    }
  );

  return { highQuality, mediumQuality, lowQuality };
}

// ============================================================================
// EXAMPLE 6: API INTEGRATION
// ============================================================================

/**
 * Call the API endpoints directly
 */
export async function example6_apiIntegration() {
  const baseUrl = process.env.RUNTIME_API_URL || 'http://localhost:3000';
  const apiToken = process.env.AUTOMATION_API_TOKEN || 'your-api-token';

  // Example 1: Process video via API
  console.log('Processing video via API...');

  const processResponse = await fetch(`${baseUrl}/api/automation/head-videos/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiToken}`,
    },
    body: JSON.stringify({
      videoPath: './videos/training.mp4',
      script: {
        id: 'training-001',
        title: 'Training: Product Onboarding',
        description: 'Get started with our platform',
        hook: 'In 5 minutes, youll have your first project created',
        mainPoints: ['Sign up', 'Create project', 'Invite team'],
        cta: 'Start free trial at alreadyherellc.com',
        duration: 300,
        publishPlatforms: ['coaching', 'lms'],
      },
      uploadPlatforms: ['coaching', 'lms'],
      targetResolution: '1080p',
    }),
  });

  const processResult = await processResponse.json();
  console.log('Process Result:', processResult);

  // Example 2: Get analytics via API
  console.log('\nFetching analytics via API...');

  const analyticsResponse = await fetch(
    `${baseUrl}/api/automation/head-videos/analytics?videoId=yt_training_001`,
    {
      headers: {
        Authorization: `Bearer ${apiToken}`,
      },
    }
  );

  const analyticsResult = await analyticsResponse.json();
  console.log('Analytics Result:', analyticsResult);

  // Example 3: Get automation status
  console.log('\nFetching automation status...');

  const statusResponse = await fetch(`${baseUrl}/api/automation/head-videos/status`, {
    headers: {
      Authorization: `Bearer ${apiToken}`,
    },
  });

  const statusResult = await statusResponse.json();
  console.log('Status Result:', statusResult);

  return { processResult, analyticsResult, statusResult };
}

// ============================================================================
// EXAMPLE 7: ERROR HANDLING AND RECOVERY
// ============================================================================

/**
 * Robust error handling with retry logic
 */
export async function example7_errorHandling() {
  const script: HeadVideoScript = {
    id: 'resilient-video',
    title: 'Resilient Video Processing',
    description: 'This example handles errors gracefully',
    hook: 'Error handling is critical',
    mainPoints: ['Error handling', 'Retries', 'Fallbacks'],
    cta: 'Learn more at alreadyherellc.com',
    duration: 600,
    publishPlatforms: ['youtube'],
  };

  const maxRetries = 3;
  let attempts = 0;

  while (attempts < maxRetries) {
    try {
      console.log(`Attempt ${attempts + 1} of ${maxRetries}...`);

      const results = await processAndPublishHeadVideo(
        './videos/test-video.mp4',
        script,
        {
          targetResolution: '1080p',
          uploadPlatforms: ['youtube'],
        }
      );

      // Check if all uploads were successful
      const allSuccessful = results.every((r) => r.success);
      if (allSuccessful) {
        console.log('✓ All uploads successful!');
        return results;
      } else {
        throw new Error('Some uploads failed');
      }
    } catch (error) {
      attempts++;
      console.error(`Attempt ${attempts} failed:`, error);

      if (attempts < maxRetries) {
        // Wait before retrying (exponential backoff)
        const waitTime = Math.pow(2, attempts) * 1000;
        console.log(`Waiting ${waitTime}ms before retry...`);
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      }
    }
  }

  console.error('Failed after all retry attempts');
  return null;
}

// ============================================================================
// EXAMPLE 8: MONITORING AND LOGGING
// ============================================================================

/**
 * Comprehensive monitoring and logging
 */
export async function example8_monitoringAndLogging() {
  const startTime = Date.now();

  const script: HeadVideoScript = {
    id: 'monitored-video',
    title: 'Monitored Video Processing',
    description: 'Detailed logging and monitoring',
    hook: 'Monitoring is essential',
    mainPoints: ['Logging', 'Metrics', 'Performance'],
    cta: 'Join our monitoring webinar',
    duration: 1200,
    publishPlatforms: ['youtube', 'coaching'],
  };

  console.log('[START] Video processing initiated');
  console.log(`[INFO] Video ID: ${script.id}`);
  console.log(`[INFO] Platforms: ${script.publishPlatforms.join(', ')}`);

  try {
    const results = await processAndPublishHeadVideo(
      './videos/monitored-video.mp4',
      script,
      {
        targetResolution: '1080p',
        fps: 30,
        bitrate: 'high',
        uploadPlatforms: script.publishPlatforms,
      }
    );

    const processingTime = Date.now() - startTime;

    console.log('[SUCCESS] Video processing completed');
    console.log(`[METRIC] Processing time: ${processingTime}ms`);
    console.log(`[METRIC] Videos uploaded: ${results.filter((r) => r.success).length}`);
    console.log(`[METRIC] Success rate: ${((results.filter((r) => r.success).length / results.length) * 100).toFixed(2)}%`);

    results.forEach((result, index) => {
      console.log(
        `[RESULT] Upload ${index + 1}: ${result.platform} - ${result.success ? 'SUCCESS' : 'FAILED'}`
      );
      if (result.videoUrl) {
        console.log(`[URL] ${result.videoUrl}`);
      }
    });

    return results;
  } catch (error) {
    console.error('[ERROR] Processing failed:', error);
    throw error;
  }
}

// ============================================================================
// RUN EXAMPLES
// ============================================================================

export async function runAllExamples() {
  console.log('='.repeat(80));
  console.log('HEAD VIDEO AUTOMATION - USAGE EXAMPLES');
  console.log('='.repeat(80));

  // Uncomment the examples you want to run:

  // await example1_basicCoachingVideo();
  // await example2_webinarWithScheduling();
  // await example3_batchProcessing();
  // await example4_analyticsTracking();
  // await example5_multiResolutionProcessing();
  // await example6_apiIntegration();
  // await example7_errorHandling();
  // await example8_monitoringAndLogging();

  console.log('\n' + '='.repeat(80));
  console.log('Examples completed!');
  console.log('='.repeat(80));
}

/**
 * PINTEREST AUTOMATION EXAMPLES
 *
 * Practical examples for using the Pinterest automation module
 */

import {
  generateAndPostPin,
  generateAndPostPins,
  getPinMetrics,
  PinterestPinResult,
  PinterestMetrics,
} from './pinterest';

/**
 * Example 1: Generate and post a single pin
 *
 * Takes a pin number from the content calendar and generates a pin image,
 * then uploads it to Pinterest to a specific board
 */
export async function example1_SinglePin() {
  try {
    console.log('Example 1: Generate and post a single pin');

    const result: PinterestPinResult = await generateAndPostPin(1);

    if (result.success) {
      console.log(`✓ Pin posted successfully!`);
      console.log(`  Pin URL: ${result.pinUrl}`);
      console.log(`  Board: ${result.boardName}`);
      console.log(`  Pin ID: ${result.pinId}`);
    } else {
      console.error(`✗ Pin posting failed: ${result.error}`);
    }

    return result;
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 2: Batch generate and post multiple pins
 *
 * Generate 5 pins from the content calendar (pins 1-5) in sequence
 * with 2-second delays between requests for rate limiting
 */
export async function example2_BatchPins() {
  try {
    console.log('Example 2: Batch generate multiple pins');

    const results: PinterestPinResult[] = await generateAndPostPins(5);

    const successCount = results.filter((r) => r.success).length;
    const failureCount = results.filter((r) => !r.success).length;

    console.log(`Results: ${successCount} succeeded, ${failureCount} failed`);

    results.forEach((result, index) => {
      if (result.success) {
        console.log(`  Pin ${index + 1}: ✓ ${result.pinUrl}`);
      } else {
        console.log(`  Pin ${index + 1}: ✗ ${result.error}`);
      }
    });

    return results;
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 3: Fetch and display pin metrics
 *
 * Retrieve engagement metrics for a specific pin:
 * - Impressions (how many times the pin was seen)
 * - Outbound clicks (how many people clicked the link)
 * - Saves (how many people saved the pin)
 */
export async function example3_FetchMetrics() {
  try {
    console.log('Example 3: Fetch and display pin metrics');

    // Replace with actual pin ID from a previous post
    const pinId = '123456789';

    const metrics: PinterestMetrics | null = await getPinMetrics(pinId);

    if (metrics) {
      console.log(`Pin Metrics for: ${metrics.title}`);
      console.log(`  Impressions: ${metrics.impressions}`);
      console.log(`  Outbound Clicks: ${metrics.outboundClicks}`);
      console.log(`  Saves: ${metrics.saves}`);

      // Calculate engagement rate
      const engagementRate =
        ((metrics.outboundClicks + metrics.saves) / metrics.impressions) * 100;
      console.log(`  Engagement Rate: ${engagementRate.toFixed(2)}%`);
    } else {
      console.log('Pin not found or metrics unavailable');
    }

    return metrics;
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 4: Configure custom image provider
 *
 * Pinterest automation supports multiple image generation providers:
 * - Canva API (professional design templates)
 * - Unsplash (free stock photos)
 * - Replicate (DALL-E/Stable Diffusion AI generation)
 */
export async function example4_CustomProvider() {
  try {
    console.log('Example 4: Configure custom image provider');

    // Set environment variable for image provider
    process.env.IMAGE_GENERATION_API = 'canva'; // or 'unsplash' or 'replicate'

    const result: PinterestPinResult = await generateAndPostPin(1);

    if (result.success) {
      console.log(`✓ Pin created with Canva provider`);
    } else {
      console.error(`✗ Failed: ${result.error}`);
    }

    return result;
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 5: Integration with Master Orchestrator
 *
 * The Pinterest module can be integrated with the master orchestrator
 * to coordinate with other automation tasks like email, Instagram, etc.
 */
export async function example5_MasterOrchestrator() {
  try {
    console.log('Example 5: Integration with Master Orchestrator');

    // This would be called from master orchestrator
    // const orchestrator = new MasterOrchestrator({
    //   mode: ExecutionMode.PARALLEL,
    //   tasks: [
    //     {
    //       id: 'pinterest-batch',
    //       name: 'Pinterest Automation',
    //       type: 'pinterest',
    //       enabled: true,
    //       priority: TaskPriority.HIGH,
    //       metadata: { count: 5 }
    //     },
    //     {
    //       id: 'instagram-reels',
    //       name: 'Instagram Reels',
    //       type: 'reel',
    //       enabled: true,
    //       priority: TaskPriority.HIGH,
    //     }
    //   ]
    // });
    //
    // const result = await orchestrator.run();

    console.log('Master orchestrator integration configured');
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 6: Error handling and retry logic
 *
 * The Pinterest module includes built-in error handling:
 * - Missing API tokens
 * - Invalid pin designs
 * - Network failures
 * - Rate limiting
 */
export async function example6_ErrorHandling() {
  try {
    console.log('Example 6: Error handling and retry logic');

    // Generate multiple pins and handle failures gracefully
    const results = await generateAndPostPins(3);

    let successCount = 0;
    let failureCount = 0;

    results.forEach((result, index) => {
      if (result.success) {
        successCount++;
        console.log(`  Pin ${index + 1}: ✓ Success`);
      } else {
        failureCount++;
        console.log(`  Pin ${index + 1}: ✗ ${result.error}`);

        // Could implement retry logic here
        // if (isRetryableError(result.error)) {
        //   await delay(5000);
        //   await generateAndPostPin(index + 1);
        // }
      }
    });

    console.log(`\nSummary: ${successCount} succeeded, ${failureCount} failed`);

    // Calculate success rate
    const successRate = (successCount / results.length) * 100;
    console.log(`Success Rate: ${successRate.toFixed(1)}%`);

    return { successCount, failureCount, successRate };
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 7: API endpoint usage
 *
 * The Pinterest automation is exposed via HTTP API endpoints:
 * - POST /api/automation/pinterest/generate
 * - POST /api/automation/pinterest/batch
 * - GET /api/automation/pinterest/metrics
 * - POST /api/automation/pinterest/webhook
 * - GET /api/automation/pinterest/status
 */
export async function example7_APIUsage() {
  try {
    console.log('Example 7: API endpoint usage');

    // Example 1: Generate single pin
    console.log('\n1. Generate single pin:');
    console.log(
      'POST /api/automation/pinterest/generate\nBody: { "pinNumber": 1 }'
    );

    // Example 2: Batch generate
    console.log('\n2. Batch generate pins:');
    console.log(
      'POST /api/automation/pinterest/batch\nBody: { "count": 5, "imageProvider": "replicate" }'
    );

    // Example 3: Get metrics
    console.log('\n3. Fetch pin metrics:');
    console.log(
      'GET /api/automation/pinterest/metrics?pinId=123456789'
    );

    // Example 4: Check status
    console.log('\n4. Check automation status:');
    console.log('GET /api/automation/pinterest/status');

    // Actual HTTP call example
    const response = await fetch('/api/automation/pinterest/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pinNumber: 1 }),
    });

    const data = await response.json();
    console.log(`\nResponse: ${data.success ? 'Success' : 'Failed'}`);

    return data;
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 8: Environment variables setup
 *
 * Required environment variables for Pinterest automation
 */
export function example8_EnvironmentSetup() {
  console.log('Example 8: Environment variables setup');
  console.log('\nRequired environment variables:');
  console.log('  PINTEREST_ACCESS_TOKEN=<your_access_token>');
  console.log('  PINTEREST_BUSINESS_ACCOUNT_ID=<your_account_id>');
  console.log('  IMAGE_GENERATION_API=replicate|canva|unsplash');
  console.log('  REPLICATE_API_TOKEN=<your_token> (if using Replicate)');
  console.log('  CANVA_API_KEY=<your_key> (if using Canva)');
  console.log('  UNSPLASH_ACCESS_KEY=<your_key> (if using Unsplash)');
  console.log('  AFFILIATE_LINKS={...} (JSON map of links)');
  console.log('  AUTOMATION_LOG_DIR=.runtime/automation/pinterest');
}

/**
 * Example 9: Monitoring and logging
 *
 * All Pinterest operations are logged to files for monitoring and debugging
 */
export async function example9_Monitoring() {
  try {
    console.log('Example 9: Monitoring and logging');

    // Logs are stored in: .runtime/automation/pinterest/
    // Files:
    // - api.jsonl: All API requests and responses
    // - webhooks.jsonl: Webhook events from Pinterest
    // - tracking.jsonl: Pin engagement tracking events

    const logDir = process.env.AUTOMATION_LOG_DIR || '.runtime/automation/pinterest';

    console.log(`\nLogs stored in: ${logDir}`);
    console.log('Log files:');
    console.log('  - api.jsonl: API request/response log');
    console.log('  - webhooks.jsonl: Webhook events from Pinterest');
    console.log('  - tracking.jsonl: Pin engagement events');

    console.log('\nExample API log entry:');
    console.log(
      JSON.stringify(
        {
          requestId: 'pin-1234567890-abc123',
          timestamp: '2024-01-15T10:30:00.000Z',
          method: 'POST',
          endpoint: '/api/automation/pinterest/generate',
          response: {
            success: true,
            pinId: '123456789',
            pinUrl: 'https://pinterest.com/pin/123456789',
          },
        },
        null,
        2
      )
    );
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

/**
 * Example 10: Complete workflow
 *
 * A complete end-to-end workflow combining multiple features
 */
export async function example10_CompleteWorkflow() {
  try {
    console.log('Example 10: Complete workflow');

    // Step 1: Generate batch of pins
    console.log('\nStep 1: Generating 3 pins...');
    const results = await generateAndPostPins(3);
    const successCount = results.filter((r) => r.success).length;
    console.log(`Generated: ${successCount} successful pins`);

    // Step 2: Wait for pins to be indexed
    console.log('\nStep 2: Waiting for pins to be indexed (60 seconds)...');
    await new Promise((resolve) => setTimeout(resolve, 60000));

    // Step 3: Fetch metrics for the first successful pin
    console.log('\nStep 3: Fetching metrics...');
    const firstPin = results.find((r) => r.success);

    if (firstPin?.pinId) {
      const metrics = await getPinMetrics(firstPin.pinId);

      if (metrics) {
        console.log(`\nPin Performance:`);
        console.log(`  Title: ${metrics.title}`);
        console.log(`  Impressions: ${metrics.impressions}`);
        console.log(`  Outbound Clicks: ${metrics.outboundClicks}`);
        console.log(`  Saves: ${metrics.saves}`);

        const engagementRate =
          ((metrics.outboundClicks + metrics.saves) / metrics.impressions) * 100;
        console.log(`  Engagement Rate: ${engagementRate.toFixed(2)}%`);
      }
    }

    console.log('\nWorkflow completed!');
  } catch (error) {
    console.error('Example failed:', error);
    throw error;
  }
}

// Run all examples
async function runAllExamples() {
  console.log('=== PINTEREST AUTOMATION EXAMPLES ===\n');

  try {
    // Uncomment to run individual examples
    // await example1_SinglePin();
    // await example2_BatchPins();
    // await example3_FetchMetrics();
    // await example4_CustomProvider();
    // await example5_MasterOrchestrator();
    // await example6_ErrorHandling();
    // await example7_APIUsage();
    example8_EnvironmentSetup();
    // await example9_Monitoring();
    // await example10_CompleteWorkflow();
  } catch (error) {
    console.error('Error running examples:', error);
  }
}

// Export for use in other modules
export {
  example1_SinglePin,
  example2_BatchPins,
  example3_FetchMetrics,
  example4_CustomProvider,
  example5_MasterOrchestrator,
  example6_ErrorHandling,
  example7_APIUsage,
  example8_EnvironmentSetup,
  example9_Monitoring,
  example10_CompleteWorkflow,
  runAllExamples,
};

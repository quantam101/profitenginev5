/**
 * MASTER ORCHESTRATOR EXAMPLES
 *
 * Complete working examples demonstrating the MasterOrchestrator
 * for different use cases and configurations.
 */

import {
  MasterOrchestrator,
  orchestrateFullLaunch,
  getLatestAutomationStatus,
  ExecutionMode,
  TaskPriority,
  LogLevel,
  TaskStatus,
  OrchestratorResult,
  TaskResult,
} from './master-orchestrator';

// ============================================================================
// EXAMPLE 1: QUICK START - Default Configuration
// ============================================================================
/**
 * Simplest usage: run with all default settings.
 * Mode: SMART (recommended)
 * Logging: INFO level
 * Results saved to .runtime/automation/
 */
export async function example1_quickStart(): Promise<void> {
  console.log('EXAMPLE 1: Quick Start\n');

  const result = await orchestrateFullLaunch();

  console.log(`\nOrchestration Complete!`);
  console.log(`Run ID: ${result.runId}`);
  console.log(`Success Rate: ${(result.successRate * 100).toFixed(1)}%`);
  console.log(`Tasks Passed: ${result.tasksPassed}/${result.tasksRun}`);
}

// ============================================================================
// EXAMPLE 2: SEQUENTIAL MODE - Debugging and Testing
// ============================================================================
/**
 * Run tasks one at a time. Useful for:
 * - Debugging failures
 * - Testing individual modules
 * - Minimal resource usage
 * - Clear dependency ordering
 */
export async function example2_sequentialMode(): Promise<void> {
  console.log('EXAMPLE 2: Sequential Mode\n');

  const result = await orchestrateFullLaunch({
    mode: ExecutionMode.SEQUENTIAL,
    logLevel: LogLevel.DEBUG, // Verbose logging for debugging
  });

  console.log(`\nSequential Execution Complete`);
  console.log(`Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);

  // Print each task result
  for (const task of result.results) {
    const status = task.status === TaskStatus.SUCCESS ? '✓' : '✗';
    console.log(`  ${status} ${task.taskName}: ${task.duration}ms`);
  }
}

// ============================================================================
// EXAMPLE 3: PARALLEL MODE - Maximum Throughput
// ============================================================================
/**
 * Run all enabled tasks concurrently.
 * Best for: Independent tasks, no dependencies
 * Warning: May overload resources if too many tasks
 */
export async function example3_parallelMode(): Promise<void> {
  console.log('EXAMPLE 3: Parallel Mode\n');

  const result = await orchestrateFullLaunch({
    mode: ExecutionMode.PARALLEL,
  });

  console.log(`\nParallel Execution Complete`);
  console.log(`Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);

  // Compare with sequential
  if (result.results.length > 0) {
    const totalTaskTime = result.results.reduce((sum, t) => sum + t.duration, 0);
    const parallelOverhead = result.totalDuration - Math.max(...result.results.map(t => t.duration));
    console.log(`Total task time: ${(totalTaskTime / 1000).toFixed(2)}s`);
    console.log(`Parallel overhead: ${parallelOverhead}ms`);
    console.log(`Speedup: ${(totalTaskTime / result.totalDuration).toFixed(2)}x`);
  }
}

// ============================================================================
// EXAMPLE 4: CUSTOM TASK SELECTION
// ============================================================================
/**
 * Run specific tasks only, disable others.
 * Useful for:
 * - Running only backend enhancement modules
 * - Running only social media tasks
 * - A/B testing module changes
 */
export async function example4_customTaskSelection(): Promise<void> {
  console.log('EXAMPLE 4: Custom Task Selection\n');

  const orchestrator = new MasterOrchestrator({
    mode: ExecutionMode.SMART,
  });

  // Get default config
  const config = orchestrator.getConfig();

  // Disable all Instagram tasks
  for (const task of config.tasks) {
    if (task.type.startsWith('carousel') || task.type.startsWith('reel') || task.type.startsWith('stories')) {
      task.enabled = false;
    }
  }

  const result = await orchestrator.run();

  console.log(`\nCustom Task Selection Complete`);
  console.log(`Tasks Enabled: ${config.tasks.filter(t => t.enabled).length}`);
  console.log(`Tasks Disabled: ${config.tasks.filter(t => !t.enabled).length}`);
  console.log(`Success Rate: ${(result.successRate * 100).toFixed(1)}%`);
}

// ============================================================================
// EXAMPLE 5: AGGRESSIVE RETRY CONFIGURATION
// ============================================================================
/**
 * Configure retries for unreliable networks.
 * Best for: Unstable connections, flaky services
 * Cost: Longer total execution time
 */
export async function example5_aggressiveRetry(): Promise<void> {
  console.log('EXAMPLE 5: Aggressive Retry Configuration\n');

  const result = await orchestrateFullLaunch({
    retryMaxAttempts: 5, // Up from default 3
    retryBackoffMs: 8000, // Up from default 5000
    circuitBreakerThreshold: 10, // More lenient circuit breaker
    circuitBreakerResetMs: 600000, // 10 minutes
  });

  console.log(`\nAggressive Retry Complete`);
  console.log(`Total Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);

  // Show retry statistics
  const tasksWithRetries = result.results.filter(t => t.metrics?.retryCount! > 0);
  if (tasksWithRetries.length > 0) {
    console.log(`\nTasks with Retries:`);
    for (const task of tasksWithRetries) {
      console.log(`  - ${task.taskName}: ${task.metrics?.retryCount} retries`);
    }
  }
}

// ============================================================================
// EXAMPLE 6: STRICT CIRCUIT BREAKER
// ============================================================================
/**
 * Configure strict failure prevention.
 * Best for: Production critical systems
 * Effect: Fail fast to avoid cascading failures
 */
export async function example6_strictCircuitBreaker(): Promise<void> {
  console.log('EXAMPLE 6: Strict Circuit Breaker\n');

  const result = await orchestrateFullLaunch({
    circuitBreakerThreshold: 2, // Fail after 2 consecutive errors
    circuitBreakerResetMs: 900000, // 15 minutes before retry
  });

  console.log(`\nStrict Circuit Breaker Complete`);

  const failedByCircuitBreaker = result.results.filter(
    t => t.status === TaskStatus.CIRCUIT_BREAK
  );

  if (failedByCircuitBreaker.length > 0) {
    console.log(`\nTasks Stopped by Circuit Breaker:`);
    for (const task of failedByCircuitBreaker) {
      console.log(`  - ${task.taskName}: ${task.error?.message}`);
    }
  }
}

// ============================================================================
// EXAMPLE 7: WEBHOOK INTEGRATION
// ============================================================================
/**
 * Send results to external monitoring system.
 * Useful for:
 * - Slack notifications
 * - Monitoring dashboards
 * - Alert systems
 * - Audit logging
 */
export async function example7_webhookIntegration(): Promise<void> {
  console.log('EXAMPLE 7: Webhook Integration\n');

  const result = await orchestrateFullLaunch({
    webhookUrl: 'https://your-monitoring-system.com/api/automation-webhook',
    // Also set in environment:
    // PROFITENGINE_WEBHOOK_TOKEN=your-secret-token
  });

  console.log(`\nWebhook Integration Complete`);
  console.log(`Webhook would have received:`);
  console.log(JSON.stringify({
    runId: result.runId,
    success: result.tasksFailed === 0,
    stats: {
      tasksRun: result.tasksRun,
      passed: result.tasksPassed,
      failed: result.tasksFailed,
      successRate: result.successRate,
    },
  }, null, 2));
}

// ============================================================================
// EXAMPLE 8: DEBUG LOGGING
// ============================================================================
/**
 * Enable debug logging for troubleshooting.
 * Shows:
 * - Every attempt and retry
 * - Detailed error messages
 * - Task timing
 * - Dependency resolution
 */
export async function example8_debugLogging(): Promise<void> {
  console.log('EXAMPLE 8: Debug Logging\n');

  const result = await orchestrateFullLaunch({
    logLevel: LogLevel.DEBUG,
  });

  console.log(`\nDebug Logging Complete`);
  console.log(`Logs saved to .runtime/automation/${result.runId}.log`);
  console.log(`Full results: .runtime/automation/${result.runId}.json`);
}

// ============================================================================
// EXAMPLE 9: CUSTOM TASK CONFIGURATION
// ============================================================================
/**
 * Create completely custom task list.
 * Useful for:
 * - Testing new modules
 * - Custom workflows
 * - Workflow experiments
 */
export async function example9_customTaskConfiguration(): Promise<void> {
  console.log('EXAMPLE 9: Custom Task Configuration\n');

  const orchestrator = new MasterOrchestrator({
    tasks: [
      // Only run enhancement modules (skip social media)
      {
        id: 'performance-attribution',
        name: 'Performance Attribution',
        type: 'attribution',
        enabled: true,
        priority: TaskPriority.CRITICAL,
        timeout: 180000,
        retryMaxAttempts: 2,
        metadata: { regime: 'daily' },
      },
      {
        id: 'dynamic-risk-adjustment',
        name: 'Dynamic Risk Adjustment',
        type: 'risk',
        enabled: true,
        priority: TaskPriority.CRITICAL,
        timeout: 120000,
        retryMaxAttempts: 2,
        dependencies: [
          { taskId: 'performance-attribution', required: true, wait: true }
        ],
      },
      {
        id: 'sentiment-analysis',
        name: 'Sentiment Analysis',
        type: 'sentiment',
        enabled: true,
        priority: TaskPriority.HIGH,
        timeout: 150000,
        retryMaxAttempts: 2,
      },
    ],
    mode: ExecutionMode.SMART,
  });

  const result = await orchestrator.run();

  console.log(`\nCustom Configuration Complete`);
  console.log(`Tasks Configured: ${result.configuration.tasks.length}`);
  console.log(`Tasks Run: ${result.tasksRun}`);
  console.log(`Success Rate: ${(result.successRate * 100).toFixed(1)}%`);
}

// ============================================================================
// EXAMPLE 10: POOL SIZE OPTIMIZATION
// ============================================================================
/**
 * Configure resource pooling for SMART mode.
 * Tune based on:
 * - CPU cores: poolSize ~= CPU cores
 * - Memory: larger pool = more concurrent tasks
 * - Network: I/O bound tasks benefit from larger pool
 */
export async function example10_poolSizeOptimization(): Promise<void> {
  console.log('EXAMPLE 10: Pool Size Optimization\n');

  // Test different pool sizes
  const poolSizes = [2, 4, 8];
  const results: Array<{ poolSize: number; duration: number; successRate: number }> = [];

  for (const poolSize of poolSizes) {
    const result = await orchestrateFullLaunch({
      poolSize,
      mode: ExecutionMode.SMART,
    });

    results.push({
      poolSize,
      duration: result.totalDuration,
      successRate: result.successRate,
    });

    console.log(`\nPool Size ${poolSize}: ${(result.totalDuration / 1000).toFixed(2)}s`);
  }

  console.log(`\nOptimal pool size comparison:`);
  for (const r of results) {
    console.log(`  Pool ${r.poolSize}: ${(r.duration / 1000).toFixed(2)}s (${(r.successRate * 100).toFixed(1)}%)`);
  }
}

// ============================================================================
// EXAMPLE 11: MONITORING AND STATUS TRACKING
// ============================================================================
/**
 * Query historical orchestration runs.
 * Useful for:
 * - Monitoring dashboards
 * - Trend analysis
 * - SLA tracking
 * - Alerting
 */
export async function example11_monitoringStatusTracking(): Promise<void> {
  console.log('EXAMPLE 11: Monitoring and Status Tracking\n');

  // First, run an orchestration
  const result = await orchestrateFullLaunch();
  console.log(`Completed run: ${result.runId}`);

  // Then query history
  const status = await getLatestAutomationStatus();

  console.log(`\nLatest Run:`);
  if (status.lastRun) {
    console.log(`  Run ID: ${status.lastRun.runId}`);
    console.log(`  Time: ${status.lastRun.timestamp}`);
    console.log(`  Mode: ${status.lastRun.mode}`);
    console.log(`  Success: ${status.lastRun.success}`);
    console.log(`  Success Rate: ${(status.lastRun.successRate * 100).toFixed(1)}%`);
  }

  console.log(`\nHistorical Runs (${status.allRuns.length} total):`);
  for (const run of status.allRuns.slice(-5)) {
    const indicator = run.success ? '✓' : '✗';
    console.log(
      `  ${indicator} ${run.timestamp}: ${run.mode} mode - ${(run.successRate * 100).toFixed(1)}%`
    );
  }

  // Calculate trends
  if (status.allRuns.length > 1) {
    const successRates = status.allRuns.map(r => r.successRate);
    const avgRate = successRates.reduce((a, b) => a + b, 0) / successRates.length;
    const trend = successRates[successRates.length - 1] > successRates[0] ? '📈' : '📉';

    console.log(`\nTrends:`);
    console.log(`  Average Success Rate: ${(avgRate * 100).toFixed(1)}%`);
    console.log(`  Trend: ${trend}`);
  }
}

// ============================================================================
// EXAMPLE 12: ERROR HANDLING AND RECOVERY
// ============================================================================
/**
 * Comprehensive error handling patterns.
 * Shows:
 * - Identifying critical failures
 * - Dead letter queue handling
 * - Retry pattern analysis
 * - Recovery actions
 */
export async function example12_errorHandlingRecovery(): Promise<void> {
  console.log('EXAMPLE 12: Error Handling and Recovery\n');

  const result = await orchestrateFullLaunch();

  // Check for critical failures
  const criticalFailures = result.summary.criticalFailures || [];
  if (criticalFailures.length > 0) {
    console.log(`⚠️  CRITICAL FAILURES DETECTED:\n`);
    for (const failure of criticalFailures) {
      console.log(`  Task: ${failure.taskName}`);
      console.log(`  Error: ${failure.error?.message}`);
      console.log(`  Attempts: ${failure.attempts}/${failure.maxAttempts}`);
      console.log();
    }

    // Suggest recovery actions
    console.log(`Suggested Recovery Actions:`);
    console.log(`  1. Check error logs: .runtime/automation/${result.runId}.log`);
    console.log(`  2. Verify credentials and API keys in environment`);
    console.log(`  3. Check external service availability (Gumroad, Instagram, etc.)`);
    console.log(`  4. Increase timeout if services are slow`);
    console.log(`  5. Retry with AUTOMATION_MODE=sequential for detailed debugging`);
  }

  // Check dead letter queue
  if (result.deadLetterQueue.length > 0) {
    console.log(`\n🚫 DEAD LETTER QUEUE (${result.deadLetterQueue.length}):`);
    for (const task of result.deadLetterQueue) {
      console.log(`  - ${task.taskName}: ${task.error?.message}`);
    }
    console.log(`  (Circuit breaker disabled these tasks)`);
  }

  // Show failed tasks with retry analysis
  const failedWithoutMaxRetries = result.failedTasks.filter(
    t => t.attempts < t.maxAttempts
  );

  if (failedWithoutMaxRetries.length > 0) {
    console.log(`\n⏸️  TASKS FAILED BEFORE MAX RETRIES:`);
    for (const task of failedWithoutMaxRetries) {
      console.log(
        `  - ${task.taskName}: ${task.attempts}/${task.maxAttempts} attempts`
      );
    }
    console.log(`  (Could succeed with more retries)`);
  }
}

// ============================================================================
// EXAMPLE 13: PERFORMANCE ANALYSIS
// ============================================================================
/**
 * Detailed performance analysis and metrics.
 * Useful for:
 * - Bottleneck identification
 * - Resource planning
 * - SLA verification
 * - Optimization targets
 */
export async function example13_performanceAnalysis(): Promise<void> {
  console.log('EXAMPLE 13: Performance Analysis\n');

  const result = await orchestrateFullLaunch({
    mode: ExecutionMode.SMART,
  });

  console.log(`Overall Metrics:`);
  console.log(`  Total Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);
  console.log(`  Tasks Run: ${result.tasksRun}`);

  if (result.results.length > 0) {
    // Per-task analysis
    console.log(`\nPer-Task Performance:`);

    const sorted = [...result.results].sort((a, b) => b.duration - a.duration);

    for (const task of sorted.slice(0, 5)) {
      const statusIcon =
        task.status === TaskStatus.SUCCESS
          ? '✓'
          : task.status === TaskStatus.FAILED
            ? '✗'
            : '-';

      console.log(
        `  ${statusIcon} ${task.taskName.padEnd(30)} ${(task.duration / 1000).toFixed(2)}s`
      );

      if (task.metrics?.retryCount! > 0) {
        console.log(
          `     └─ Retried ${task.metrics?.retryCount} times (${task.metrics?.backoffTotalMs}ms backoff)`
        );
      }
    }

    // Calculate efficiency
    const totalTaskTime = result.results.reduce((sum, t) => sum + t.duration, 0);
    const parallelization = totalTaskTime / result.totalDuration;
    const efficiency = (parallelization / result.configuration.poolSize) * 100;

    console.log(`\nParallelization Analysis:`);
    console.log(`  Sum of Task Times: ${(totalTaskTime / 1000).toFixed(2)}s`);
    console.log(`  Total Elapsed: ${(result.totalDuration / 1000).toFixed(2)}s`);
    console.log(`  Parallelization Factor: ${parallelization.toFixed(2)}x`);
    console.log(`  Pool Efficiency: ${efficiency.toFixed(1)}%`);
  }

  // Task category breakdown
  console.log(`\nTask Category Breakdown:`);
  const byType: Record<string, TaskResult[]> = {};

  for (const task of result.results) {
    if (!byType[task.taskType]) {
      byType[task.taskType] = [];
    }
    byType[task.taskType].push(task);
  }

  for (const [type, tasks] of Object.entries(byType)) {
    const passed = tasks.filter(t => t.status === TaskStatus.SUCCESS).length;
    const totalTime = tasks.reduce((sum, t) => sum + t.duration, 0);
    console.log(
      `  ${type.padEnd(15)} ${passed}/${tasks.length} passed, ${(totalTime / 1000).toFixed(2)}s total`
    );
  }
}

// ============================================================================
// EXAMPLE 14: COMPREHENSIVE TEST SUITE
// ============================================================================
/**
 * Run multiple configurations to verify system behavior.
 * Useful for:
 * - Configuration validation
 * - Performance regression testing
 * - Load testing
 */
export async function example14_comprehensiveTestSuite(): Promise<void> {
  console.log('EXAMPLE 14: Comprehensive Test Suite\n');

  const configs = [
    { name: 'Sequential', mode: ExecutionMode.SEQUENTIAL },
    { name: 'Parallel (pool=2)', mode: ExecutionMode.PARALLEL, poolSize: 2 },
    { name: 'Parallel (pool=4)', mode: ExecutionMode.PARALLEL, poolSize: 4 },
    { name: 'Smart (pool=2)', mode: ExecutionMode.SMART, poolSize: 2 },
    { name: 'Smart (pool=4)', mode: ExecutionMode.SMART, poolSize: 4 },
  ];

  const testResults: Array<{
    name: string;
    duration: number;
    successRate: number;
    passed: number;
    failed: number;
  }> = [];

  for (const config of configs) {
    console.log(`Testing: ${config.name}...`);

    const result = await orchestrateFullLaunch({
      mode: config.mode,
      poolSize: config.poolSize || 4,
    });

    testResults.push({
      name: config.name,
      duration: result.totalDuration,
      successRate: result.successRate,
      passed: result.tasksPassed,
      failed: result.tasksFailed,
    });

    console.log(`  ✓ Complete: ${(result.totalDuration / 1000).toFixed(2)}s\n`);
  }

  // Summary comparison
  console.log('\nComparison Summary:');
  console.log('Config'.padEnd(20) + 'Duration'.padEnd(12) + 'Success'.padEnd(12) + 'Passed/Failed');
  console.log('-'.repeat(60));

  for (const test of testResults) {
    console.log(
      test.name.padEnd(20) +
        `${(test.duration / 1000).toFixed(2)}s`.padEnd(12) +
        `${(test.successRate * 100).toFixed(1)}%`.padEnd(12) +
        `${test.passed}/${test.failed}`
    );
  }

  // Find best performer
  const fastest = testResults.reduce((min, t) => (t.duration < min.duration ? t : min));
  console.log(`\n✨ Fastest: ${fastest.name} (${(fastest.duration / 1000).toFixed(2)}s)`);
}

// ============================================================================
// EXAMPLE 15: SCHEDULED EXECUTION (for CI/CD)
// ============================================================================
/**
 * Pattern for integrating into CI/CD pipelines.
 * Can be called by:
 * - GitHub Actions workflows
 * - AWS Lambda
 * - Cloud Functions
 * - Scheduled jobs
 */
export async function example15_scheduledExecution(): Promise<{
  success: boolean;
  runId: string;
  message: string;
  details: OrchestratorResult;
}> {
  console.log('EXAMPLE 15: Scheduled Execution (CI/CD Integration)\n');

  try {
    const result = await orchestrateFullLaunch({
      mode: ExecutionMode.SMART,
      poolSize: process.env.CI ? 2 : 4, // Smaller pool in CI
      logLevel: LogLevel.INFO,
    });

    const success = result.tasksFailed === 0 && result.successRate === 1.0;

    return {
      success,
      runId: result.runId,
      message: success
        ? `Orchestration successful: ${result.tasksPassed}/${result.tasksRun} tasks passed`
        : `Orchestration completed with failures: ${result.tasksFailed} failed`,
      details: result,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return {
      success: false,
      runId: `error-${Date.now()}`,
      message: `Orchestration failed: ${message}`,
      details: {} as any,
    };
  }
}

// ============================================================================
// EXAMPLE 16: REAL-WORLD WORKFLOW
// ============================================================================
/**
 * Complete production workflow with error handling and recovery.
 */
export async function example16_realWorldWorkflow(): Promise<void> {
  console.log('EXAMPLE 16: Real-World Production Workflow\n');

  let retryCount = 0;
  const maxRetries = 3;
  let success = false;

  while (retryCount < maxRetries && !success) {
    try {
      console.log(`Attempt ${retryCount + 1}/${maxRetries}...`);

      const result = await orchestrateFullLaunch({
        mode: ExecutionMode.SMART,
        retryMaxAttempts: 3,
        webhookUrl: process.env.AUTOMATION_WEBHOOK_URL,
      });

      if (result.tasksFailed === 0) {
        console.log(`✓ Success! All ${result.tasksRun} tasks passed`);
        success = true;

        // Log metrics
        console.log(`Metrics:`);
        console.log(`  Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);
        console.log(`  Success Rate: ${(result.successRate * 100).toFixed(1)}%`);
      } else {
        // Some tasks failed
        console.warn(
          `⚠️  ${result.tasksFailed}/${result.tasksRun} tasks failed`
        );

        // Check if failures are recoverable
        const criticalFailures = result.summary.criticalFailures || [];
        if (criticalFailures.length > 0) {
          throw new Error(
            `Critical failures: ${criticalFailures.map(t => t.taskName).join(', ')}`
          );
        }

        // Non-critical failures; can retry
        success = false;
        retryCount++;

        if (retryCount < maxRetries) {
          console.log(`Retrying in 30s...`);
          await new Promise(resolve => setTimeout(resolve, 30000));
        }
      }
    } catch (error) {
      console.error(`Orchestration error: ${error}`);
      retryCount++;

      if (retryCount < maxRetries) {
        console.log(`Retrying in 60s...`);
        await new Promise(resolve => setTimeout(resolve, 60000));
      }
    }
  }

  if (!success) {
    throw new Error(`Orchestration failed after ${maxRetries} attempts`);
  }

  console.log(`\n✓ Workflow complete!`);
}

// ============================================================================
// MAIN - Run Examples
// ============================================================================

if (require.main === module) {
  (async () => {
    const exampleNum = process.argv[2] || '1';

    const examples: Record<string, () => Promise<void>> = {
      '1': example1_quickStart,
      '2': example2_sequentialMode,
      '3': example3_parallelMode,
      '4': example4_customTaskSelection,
      '5': example5_aggressiveRetry,
      '6': example6_strictCircuitBreaker,
      '7': example7_webhookIntegration,
      '8': example8_debugLogging,
      '9': example9_customTaskConfiguration,
      '10': example10_poolSizeOptimization,
      '11': example11_monitoringStatusTracking,
      '12': example12_errorHandlingRecovery,
      '13': example13_performanceAnalysis,
      '14': example14_comprehensiveTestSuite,
      '15': example15_scheduledExecution,
      '16': example16_realWorldWorkflow,
    };

    const example = examples[exampleNum];

    if (!example) {
      console.log('Usage: ts-node master-orchestrator-examples.ts [1-16]');
      console.log('\nAvailable examples:');
      console.log('  1  - Quick Start (default config)');
      console.log('  2  - Sequential Mode (debugging)');
      console.log('  3  - Parallel Mode (throughput)');
      console.log('  4  - Custom Task Selection');
      console.log('  5  - Aggressive Retry Configuration');
      console.log('  6  - Strict Circuit Breaker');
      console.log('  7  - Webhook Integration');
      console.log('  8  - Debug Logging');
      console.log('  9  - Custom Task Configuration');
      console.log('  10 - Pool Size Optimization');
      console.log('  11 - Monitoring and Status Tracking');
      console.log('  12 - Error Handling and Recovery');
      console.log('  13 - Performance Analysis');
      console.log('  14 - Comprehensive Test Suite');
      console.log('  15 - Scheduled Execution (CI/CD)');
      console.log('  16 - Real-World Production Workflow');
      process.exit(1);
    }

    try {
      await example();
    } catch (error) {
      console.error('Example failed:', error);
      process.exit(1);
    }
  })();
}

/**
 * KDP ORCHESTRATOR INTEGRATION
 *
 * Integrates KDP publishing automation with the master orchestrator framework
 * Enables KDP tasks to run within the comprehensive automation pipeline with:
 * - Dependency management (wait for cover generation, etc.)
 * - Parallel/sequential execution modes
 * - Advanced retry logic and circuit breaker pattern
 * - Comprehensive logging and metrics
 * - Error aggregation and dead-letter queue
 *
 * Usage:
 * ```typescript
 * const orchestrator = new MasterOrchestrator(config);
 * await orchestrator.registerTask(createKdpPublishTask(...));
 * await orchestrator.registerTask(createKdpRoyaltyTrackingTask(...));
 * const results = await orchestrator.execute();
 * ```
 */

import { TaskConfig, TaskResult, TaskStatus, TaskPriority } from './master-orchestrator';
import {
  orchestrateKdpPublication,
  batchPublishBooks,
  trackKdpRoyalties,
  validateBookMetadata,
  assessPublicationRisk,
  BookMetadata,
} from './kdp';

// ============================================================================
// KDP TASK CREATORS
// ============================================================================

/**
 * Create a KDP publication task for the orchestrator
 */
export function createKdpPublishTask(options: {
  bookFiles: string[];
  platforms?: ('kdp' | 'draft2digital' | 'smashwords')[];
  validateOnly?: boolean;
  priority?: TaskPriority;
  timeout?: number;
  dependencies?: Array<{ taskId: string; required: boolean }>;
}): TaskConfig {
  return {
    id: `kdp-publish-${Date.now()}`,
    name: 'KDP Publish Books',
    description: `Publish ${options.bookFiles.length} eBooks to KDP and partner platforms`,
    type: 'kdp-publish',
    enabled: true,
    priority: options.priority || TaskPriority.HIGH,
    timeout: options.timeout || 600000, // 10 minutes
    retryMaxAttempts: 3,
    retryBackoffMs: 5000,
    dependencies: options.dependencies,
    metadata: {
      bookFiles: options.bookFiles,
      platforms: options.platforms || ['kdp', 'draft2digital', 'smashwords'],
      validateOnly: options.validateOnly || false,
      estimatedBooksPerSecond: 0.5,
      estimatedDurationMs: options.bookFiles.length * 2000,
    },
  };
}

/**
 * Create a KDP royalty tracking task for the orchestrator
 */
export function createKdpRoyaltyTask(options: {
  asins: string[];
  priority?: TaskPriority;
  timeout?: number;
  dependencies?: Array<{ taskId: string; required: boolean }>;
}): TaskConfig {
  return {
    id: `kdp-royalties-${Date.now()}`,
    name: 'KDP Royalty Tracking',
    description: `Track royalties for ${options.asins.length} published books`,
    type: 'kdp-royalties',
    enabled: true,
    priority: options.priority || TaskPriority.NORMAL,
    timeout: options.timeout || 300000, // 5 minutes
    retryMaxAttempts: 2,
    retryBackoffMs: 3000,
    dependencies: options.dependencies,
    metadata: {
      asins: options.asins,
      totalAsins: options.asins.length,
    },
  };
}

/**
 * Create a KDP validation task for the orchestrator
 */
export function createKdpValidationTask(options: {
  bookFiles: string[];
  priority?: TaskPriority;
  timeout?: number;
}): TaskConfig {
  return {
    id: `kdp-validate-${Date.now()}`,
    name: 'KDP Validation',
    description: `Validate metadata for ${options.bookFiles.length} eBooks`,
    type: 'kdp-validate',
    enabled: true,
    priority: options.priority || TaskPriority.HIGH,
    timeout: options.timeout || 120000, // 2 minutes
    retryMaxAttempts: 1,
    metadata: {
      bookFiles: options.bookFiles,
      validateOnly: true,
    },
  };
}

// ============================================================================
// KDP TASK EXECUTORS
// ============================================================================

/**
 * Execute a KDP publish task
 */
export async function executeKdpPublishTask(
  taskConfig: TaskConfig
): Promise<TaskResult> {
  const startTime = new Date();
  const metadata = taskConfig.metadata as {
    bookFiles: string[];
    platforms: string[];
    validateOnly: boolean;
  };

  try {
    if (!metadata.bookFiles || metadata.bookFiles.length === 0) {
      throw new Error('No book files specified');
    }

    const result = await batchPublishBooks(metadata.bookFiles, {
      validateOnly: metadata.validateOnly,
      platforms: metadata.platforms as ('kdp' | 'draft2digital' | 'smashwords')[],
    });

    return {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: result.validationErrors.length === 0 ? TaskStatus.SUCCESS : TaskStatus.FAILED,
      startTime: startTime.toISOString(),
      endTime: new Date().toISOString(),
      duration: new Date().getTime() - startTime.getTime(),
      attempts: 1,
      maxAttempts: taskConfig.retryMaxAttempts || 3,
      result: {
        total: result.total,
        successful: result.successful,
        failed: result.failed,
        validated: result.validated,
        results: result.results.slice(0, 3), // Limit to first 3 for brevity
        validationErrorCount: result.validationErrors.length,
      },
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };
  } catch (error) {
    return {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: TaskStatus.FAILED,
      startTime: startTime.toISOString(),
      endTime: new Date().toISOString(),
      duration: new Date().getTime() - startTime.getTime(),
      attempts: 1,
      maxAttempts: taskConfig.retryMaxAttempts || 3,
      error: {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
      },
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };
  }
}

/**
 * Execute a KDP royalty tracking task
 */
export async function executeKdpRoyaltyTask(
  taskConfig: TaskConfig
): Promise<TaskResult> {
  const startTime = new Date();
  const metadata = taskConfig.metadata as { asins: string[] };

  try {
    if (!metadata.asins || metadata.asins.length === 0) {
      throw new Error('No ASINs specified');
    }

    const allEarnings = [];
    const failedAsins = [];

    for (const asin of metadata.asins) {
      try {
        const earnings = await trackKdpRoyalties(asin);
        allEarnings.push({ asin, earnings });
      } catch (error) {
        failedAsins.push(asin);
        console.warn(`Failed to track royalties for ${asin}:`, error);
      }
    }

    const allSuccessful = failedAsins.length === 0;

    return {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: allSuccessful ? TaskStatus.SUCCESS : TaskStatus.FAILED,
      startTime: startTime.toISOString(),
      endTime: new Date().toISOString(),
      duration: new Date().getTime() - startTime.getTime(),
      attempts: 1,
      maxAttempts: taskConfig.retryMaxAttempts || 2,
      result: {
        successCount: allEarnings.length,
        failedCount: failedAsins.length,
        earnings: allEarnings.slice(0, 5), // Limit to first 5
        failedAsins: failedAsins.slice(0, 5),
      },
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };
  } catch (error) {
    return {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: TaskStatus.FAILED,
      startTime: startTime.toISOString(),
      endTime: new Date().toISOString(),
      duration: new Date().getTime() - startTime.getTime(),
      attempts: 1,
      maxAttempts: taskConfig.retryMaxAttempts || 2,
      error: {
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };
  }
}

/**
 * Execute a KDP validation task
 */
export async function executeKdpValidationTask(
  taskConfig: TaskConfig
): Promise<TaskResult> {
  const startTime = new Date();
  const metadata = taskConfig.metadata as { bookFiles: string[] };

  try {
    if (!metadata.bookFiles || metadata.bookFiles.length === 0) {
      throw new Error('No book files specified');
    }

    const result = await batchPublishBooks(metadata.bookFiles, {
      validateOnly: true,
    });

    const allValid = result.validationErrors.length === 0;

    return {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: allValid ? TaskStatus.SUCCESS : TaskStatus.FAILED,
      startTime: startTime.toISOString(),
      endTime: new Date().toISOString(),
      duration: new Date().getTime() - startTime.getTime(),
      attempts: 1,
      maxAttempts: taskConfig.retryMaxAttempts || 1,
      result: {
        totalBooks: result.total,
        validBooks: result.validated,
        invalidBooks: result.failed,
        errors: result.validationErrors.slice(0, 5), // Limit errors shown
      },
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };
  } catch (error) {
    return {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: TaskStatus.FAILED,
      startTime: startTime.toISOString(),
      endTime: new Date().toISOString(),
      duration: new Date().getTime() - startTime.getTime(),
      attempts: 1,
      maxAttempts: taskConfig.retryMaxAttempts || 1,
      error: {
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };
  }
}

/**
 * Route task execution to the appropriate KDP handler
 */
export async function routeKdpTask(taskConfig: TaskConfig): Promise<TaskResult> {
  switch (taskConfig.type) {
    case 'kdp-publish':
      return executeKdpPublishTask(taskConfig);
    case 'kdp-royalties':
      return executeKdpRoyaltyTask(taskConfig);
    case 'kdp-validate':
      return executeKdpValidationTask(taskConfig);
    default:
      throw new Error(`Unknown KDP task type: ${taskConfig.type}`);
  }
}

// ============================================================================
// EXAMPLE CONFIGURATIONS
// ============================================================================

/**
 * Example: Basic KDP publishing workflow
 */
export const BASIC_KDP_WORKFLOW = [
  createKdpValidationTask({
    bookFiles: ['KDP_BOOK_guide.md', 'KDP_BOOK_course.md'],
    priority: TaskPriority.HIGH,
  }),
  createKdpPublishTask({
    bookFiles: ['KDP_BOOK_guide.md', 'KDP_BOOK_course.md'],
    platforms: ['kdp', 'draft2digital'],
    priority: TaskPriority.HIGH,
  }),
];

/**
 * Example: KDP with royalty tracking
 */
export const KDP_WITH_ROYALTIES_WORKFLOW = [
  createKdpValidationTask({
    bookFiles: ['KDP_BOOK_guide.md'],
    priority: TaskPriority.HIGH,
  }),
  createKdpPublishTask({
    bookFiles: ['KDP_BOOK_guide.md'],
    priority: TaskPriority.HIGH,
  }),
  createKdpRoyaltyTask({
    asins: ['B0A1B2C3D4E5F6G7', 'B0B2C3D4E5F6G7H8'],
    priority: TaskPriority.NORMAL,
  }),
];

/**
 * Example: Batch publishing with validation
 */
export const BATCH_KDP_WORKFLOW = [
  createKdpValidationTask({
    bookFiles: [
      'KDP_BOOK_guide1.md',
      'KDP_BOOK_guide2.md',
      'KDP_BOOK_guide3.md',
    ],
    priority: TaskPriority.CRITICAL,
  }),
  createKdpPublishTask({
    bookFiles: [
      'KDP_BOOK_guide1.md',
      'KDP_BOOK_guide2.md',
      'KDP_BOOK_guide3.md',
    ],
    platforms: ['kdp', 'draft2digital', 'smashwords'],
    priority: TaskPriority.HIGH,
  }),
];

/**
 * ORCHESTRATION ENGINE
 *
 * Master orchestration for all automation systems:
 * - Coordinate Gumroad, Instagram, and Email automation
 * - Run sequences in parallel or serial based on configuration
 * - Error handling + retry logic with exponential backoff
 * - Logging + status tracking for all automation runs
 * - Save results to .runtime/automation/launch-status.jsonl
 *
 * Environment Requirements:
 * - AUTOMATION_PARALLEL: 'true' | 'false' (default: true)
 * - AUTOMATION_RETRY_MAX_ATTEMPTS: number (default: 3)
 * - AUTOMATION_RETRY_BACKOFF_MS: number (default: 5000)
 * - RUNTIME_DATA_DIR: path to store logs (default: '.runtime/automation')
 */

import {
  orchestrateGumroadUpload,
  GumroadUploadResult,
} from './gumroad';
import {
  generateAndPostCarousel,
  InstagramCarouselResult,
} from './instagram-carousel';
import {
  generateAndPostReel,
  InstagramReelResult,
} from './instagram-reel';
import {
  generateAndPostStories,
  InstagramStoryResult,
} from './instagram-stories';
import {
  setupEmailSequences,
  EmailAutomationResult,
} from './email-setup';
import { mkdir, writeFile, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

interface AutomationTask {
  name: string;
  type: 'gumroad' | 'carousel' | 'reel' | 'stories' | 'email';
  enabled: boolean;
  parallel?: boolean;
  retryMaxAttempts?: number;
}

interface AutomationConfig {
  runId: string;
  timestamp: string;
  parallel: boolean;
  tasks: AutomationTask[];
  retryMaxAttempts: number;
  retryBackoffMs: number;
  runtimeDataDir: string;
}

interface AutomationTaskResult {
  taskName: string;
  taskType: string;
  success: boolean;
  duration: number;
  startTime: string;
  endTime: string;
  error?: string;
  result?: unknown;
  attempts: number;
}

interface AutomationOrchestrationResult {
  runId: string;
  startTime: string;
  endTime: string;
  totalDuration: number;
  tasksRun: number;
  tasksPassed: number;
  tasksFailed: number;
  successRate: number;
  results: AutomationTaskResult[];
  configuration: AutomationConfig;
}

/**
 * Create default automation configuration
 */
function createDefaultConfig(): AutomationConfig {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';

  return {
    runId: `automation-${Date.now()}`,
    timestamp: new Date().toISOString(),
    parallel: process.env.AUTOMATION_PARALLEL !== 'false',
    retryMaxAttempts: parseInt(process.env.AUTOMATION_RETRY_MAX_ATTEMPTS || '3', 10),
    retryBackoffMs: parseInt(process.env.AUTOMATION_RETRY_BACKOFF_MS || '5000', 10),
    runtimeDataDir: runtimeDir,
    tasks: [
      {
        name: 'Gumroad Product Upload',
        type: 'gumroad',
        enabled: process.env.GUMROAD_API_TOKEN ? true : false,
        retryMaxAttempts: 3,
      },
      {
        name: 'Instagram Carousel Generation',
        type: 'carousel',
        enabled: process.env.FB_PAGE_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 2,
      },
      {
        name: 'Instagram Reel Generation',
        type: 'reel',
        enabled: process.env.FB_PAGE_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 2,
      },
      {
        name: 'Instagram Stories Generation',
        type: 'stories',
        enabled: process.env.FB_PAGE_ACCESS_TOKEN ? true : false,
        retryMaxAttempts: 2,
      },
      {
        name: 'Email Sequence Setup',
        type: 'email',
        enabled: process.env.EMAIL_SERVICE ? true : false,
        retryMaxAttempts: 2,
      },
    ],
  };
}

/**
 * Execute a single automation task with retry logic
 */
async function executeTask(
  task: AutomationTask,
  config: AutomationConfig
): Promise<AutomationTaskResult> {
  const startTime = new Date();
  let lastError: Error | undefined;
  let result: unknown;

  for (let attempt = 1; attempt <= (task.retryMaxAttempts || 3); attempt++) {
    try {
      console.log(`\n[${task.name}] Attempt ${attempt}/${task.retryMaxAttempts || 3}`);

      if (task.type === 'gumroad') {
        result = await orchestrateGumroadUpload();
      } else if (task.type === 'carousel') {
        result = await generateAndPostCarousel();
      } else if (task.type === 'reel') {
        result = await generateAndPostReel(1);
      } else if (task.type === 'stories') {
        result = await generateAndPostStories();
      } else if (task.type === 'email') {
        result = await setupEmailSequences();
      }

      const resultObj = result as Record<string, unknown>;
      if (resultObj.success) {
        const endTime = new Date();
        return {
          taskName: task.name,
          taskType: task.type,
          success: true,
          duration: endTime.getTime() - startTime.getTime(),
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          result,
          attempts: attempt,
        };
      } else {
        lastError = new Error(resultObj.error as string || 'Task failed');
      }
    } catch (error) {
      lastError = error as Error;
      console.error(`[${task.name}] Error: ${lastError.message}`);

      if (attempt < (task.retryMaxAttempts || 3)) {
        const backoffMs = config.retryBackoffMs * Math.pow(2, attempt - 1);
        console.log(`[${task.name}] Retrying in ${backoffMs}ms...`);
        await new Promise((resolve) => setTimeout(resolve, backoffMs));
      }
    }
  }

  const endTime = new Date();
  return {
    taskName: task.name,
    taskType: task.type,
    success: false,
    duration: endTime.getTime() - startTime.getTime(),
    startTime: startTime.toISOString(),
    endTime: endTime.toISOString(),
    error: lastError?.message || 'Task failed',
    attempts: task.retryMaxAttempts || 3,
  };
}

/**
 * Execute tasks in parallel
 */
async function executeTasksParallel(
  tasks: AutomationTask[],
  config: AutomationConfig
): Promise<AutomationTaskResult[]> {
  const enabledTasks = tasks.filter((t) => t.enabled);
  console.log(`\nExecuting ${enabledTasks.length} tasks in parallel...`);

  const results = await Promise.all(enabledTasks.map((task) => executeTask(task, config)));

  return results;
}

/**
 * Execute tasks sequentially
 */
async function executeTasksSequential(
  tasks: AutomationTask[],
  config: AutomationConfig
): Promise<AutomationTaskResult[]> {
  const enabledTasks = tasks.filter((t) => t.enabled);
  console.log(`\nExecuting ${enabledTasks.length} tasks sequentially...`);

  const results: AutomationTaskResult[] = [];

  for (const task of enabledTasks) {
    const result = await executeTask(task, config);
    results.push(result);
  }

  return results;
}

/**
 * Save orchestration results to log file
 */
async function saveResults(
  result: AutomationOrchestrationResult
): Promise<void> {
  try {
    const dataDir = result.configuration.runtimeDataDir;

    // Ensure directory exists
    if (!existsSync(dataDir)) {
      await mkdir(dataDir, { recursive: true });
    }

    // Save detailed JSON result
    const jsonPath = path.join(dataDir, `${result.runId}.json`);
    await writeFile(jsonPath, JSON.stringify(result, null, 2));
    console.log(`\nSaved detailed results: ${jsonPath}`);

    // Append to JSONL log
    const logPath = path.join(dataDir, 'launch-status.jsonl');
    const logEntry = JSON.stringify({
      runId: result.runId,
      timestamp: result.timestamp,
      success: result.tasksFailed === 0,
      tasksRun: result.tasksRun,
      tasksPassed: result.tasksPassed,
      tasksFailed: result.tasksFailed,
      successRate: result.successRate,
      duration: result.totalDuration,
    });

    // Append to existing log
    const existingLog = existsSync(logPath) ? await readFile(logPath, 'utf-8') : '';
    await writeFile(logPath, existingLog + logEntry + '\n');
    console.log(`Logged to: ${logPath}`);
  } catch (error) {
    console.error(`Failed to save results: ${error}`);
  }
}

/**
 * Print orchestration summary
 */
function printSummary(result: AutomationOrchestrationResult): void {
  console.log('\n' + '='.repeat(70));
  console.log('AUTOMATION ORCHESTRATION SUMMARY');
  console.log('='.repeat(70));
  console.log(`\nRun ID: ${result.runId}`);
  console.log(`Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);
  console.log(`\nResults:`);
  console.log(`  Total Tasks: ${result.tasksRun}`);
  console.log(`  Passed: ${result.tasksPassed} ✓`);
  console.log(`  Failed: ${result.tasksFailed} ✗`);
  console.log(`  Success Rate: ${(result.successRate * 100).toFixed(1)}%`);

  console.log('\nTask Details:');
  for (const taskResult of result.results) {
    const status = taskResult.success ? '✓' : '✗';
    const duration = (taskResult.duration / 1000).toFixed(2);
    console.log(
      `  ${status} ${taskResult.taskName} (${duration}s, ${taskResult.attempts} attempt${taskResult.attempts > 1 ? 's' : ''})`
    );
    if (!taskResult.success && taskResult.error) {
      console.log(`     Error: ${taskResult.error}`);
    }
  }

  console.log('\n' + '='.repeat(70));
}

/**
 * Main orchestration function
 */
export async function orchestrateFullLaunch(
  overrideConfig?: Partial<AutomationConfig>
): Promise<AutomationOrchestrationResult> {
  const startTime = new Date();

  try {
    // Load configuration
    const config: AutomationConfig = {
      ...createDefaultConfig(),
      ...overrideConfig,
    };

    console.log('PROFITENGINE AUTOMATION ORCHESTRATION');
    console.log('=====================================');
    console.log(`\nRun ID: ${config.runId}`);
    console.log(`Timestamp: ${config.timestamp}`);
    console.log(`Parallel Execution: ${config.parallel ? 'Yes' : 'No'}`);
    console.log(`Retry Max Attempts: ${config.retryMaxAttempts}`);
    console.log(`Retry Backoff: ${config.retryBackoffMs}ms`);

    // Filter enabled tasks
    const enabledTasks = config.tasks.filter((t) => t.enabled);
    console.log(`\nEnabled Tasks: ${enabledTasks.map((t) => t.name).join(', ')}`);

    if (enabledTasks.length === 0) {
      console.error('No tasks enabled. Ensure required environment variables are set.');
      return {
        runId: config.runId,
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        totalDuration: 0,
        tasksRun: 0,
        tasksPassed: 0,
        tasksFailed: 0,
        successRate: 0,
        results: [],
        configuration: config,
      };
    }

    // Execute tasks
    const results = config.parallel
      ? await executeTasksParallel(config.tasks, config)
      : await executeTasksSequential(config.tasks, config);

    const endTime = new Date();
    const totalDuration = endTime.getTime() - startTime.getTime();

    // Calculate statistics
    const tasksPassed = results.filter((r) => r.success).length;
    const tasksFailed = results.filter((r) => !r.success).length;
    const successRate = results.length > 0 ? tasksPassed / results.length : 0;

    const orchestrationResult: AutomationOrchestrationResult = {
      runId: config.runId,
      startTime: startTime.toISOString(),
      endTime: endTime.toISOString(),
      totalDuration,
      tasksRun: results.length,
      tasksPassed,
      tasksFailed,
      successRate,
      results,
      configuration: config,
    };

    // Save and print results
    await saveResults(orchestrationResult);
    printSummary(orchestrationResult);

    return orchestrationResult;
  } catch (error) {
    const endTime = new Date();
    console.error(`Orchestration failed: ${error}`);

    return {
      runId: `automation-${Date.now()}`,
      startTime: startTime.toISOString(),
      endTime: endTime.toISOString(),
      totalDuration: endTime.getTime() - startTime.getTime(),
      tasksRun: 0,
      tasksPassed: 0,
      tasksFailed: 1,
      successRate: 0,
      results: [],
      configuration: createDefaultConfig(),
    };
  }
}

/**
 * Get latest automation run status
 */
export async function getLatestAutomationStatus(): Promise<{
  lastRun?: { runId: string; timestamp: string; success: boolean; successRate: number };
  allRuns: Array<{ runId: string; timestamp: string; success: boolean; successRate: number }>;
}> {
  try {
    const dataDir = process.env.RUNTIME_DATA_DIR || '.runtime/automation';
    const logPath = path.join(dataDir, 'launch-status.jsonl');

    if (!existsSync(logPath)) {
      return { allRuns: [] };
    }

    const logContent = await readFile(logPath, 'utf-8');
    const allRuns = logContent
      .trim()
      .split('\n')
      .map((line) => JSON.parse(line));

    return {
      lastRun: allRuns[allRuns.length - 1],
      allRuns,
    };
  } catch (error) {
    console.error(`Failed to get automation status: ${error}`);
    return { allRuns: [] };
  }
}

export {
  AutomationConfig,
  AutomationTask,
  AutomationTaskResult,
  AutomationOrchestrationResult,
};

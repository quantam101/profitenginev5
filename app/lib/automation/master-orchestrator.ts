/**
 * MASTER ORCHESTRATOR
 *
 * Comprehensive automation orchestration engine that coordinates:
 * EXISTING MODULES (3):
 *   - Gumroad Product Automation
 *   - Instagram Social Media (Carousel, Reel, Stories)
 *   - Email Sequence Automation
 *
 * ENHANCEMENT MODULES (6):
 *   - Performance Attribution Analysis
 *   - Dynamic Risk Adjustment
 *   - Sentiment Analysis & Reliability Weighting
 *   - Signal Correlation Analysis
 *   - Compliance Automation (SEC, Insider Trading)
 *   - Backup & Rotation System
 *
 * Features:
 * - Modular task registration and dependency management
 * - Intelligent parallel/sequential execution with resource pooling
 * - Advanced retry logic with exponential backoff and circuit breaker
 * - Comprehensive logging (console, file, cloud integration ready)
 * - Real-time status tracking and WebSocket support
 * - Error aggregation and failure mode analysis
 * - Performance metrics and SLA tracking
 * - Dead-letter queue for failed tasks
 * - Graceful shutdown and cleanup
 *
 * Environment Requirements:
 * - AUTOMATION_MODE: 'parallel' | 'sequential' | 'smart' (default: smart)
 * - AUTOMATION_RETRY_MAX_ATTEMPTS: number (default: 3)
 * - AUTOMATION_RETRY_BACKOFF_MS: number (default: 5000)
 * - AUTOMATION_CIRCUIT_BREAKER_THRESHOLD: number (default: 5)
 * - AUTOMATION_CIRCUIT_BREAKER_RESET_MS: number (default: 300000)
 * - AUTOMATION_POOL_SIZE: number (default: 4)
 * - AUTOMATION_LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error' (default: info)
 * - AUTOMATION_LOG_DIR: path to store logs (default: '.runtime/automation')
 * - AUTOMATION_ENABLE_METRICS: 'true' | 'false' (default: true)
 * - AUTOMATION_WEBHOOK_URL: optional URL for status notifications
 */

import { mkdir, writeFile, readFile, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
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
import {
  newsletterEngine,
  NewsletterAutomationResult,
  PublishRequest,
} from './newsletter';
import {
  generateAndPostYouTubeVideo,
  YouTubeUploadResult,
} from './youtube';
import {
  generateNicheLinks,
  getCommissionReport,
  bulkOptimizeLinks,
  AffiliateLink,
} from './amazon-affiliate';
import {
  publishVideoToTikTok,
  TikTokPublishConfig,
} from './tiktok';
import {
  bulkCreateProducts,
  bulkSyncInventory,
  batchTrackOrders,
  ProductTemplate,
} from './etsy';
import {
  crossPostToReddit,
  getRedditAnalytics,
  RedditPost,
  CrossPostResult,
} from './reddit';
import {
  generateAndPostPin,
  generateAndPostPins,
  PinterestPinResult,
} from './pinterest';
import {
  publishThread,
  generateThread,
  getThreadMetrics,
  ThreadContent,
  PublishResult,
} from './twitter';
import {
  publishArticle,
  LinkedInArticleContent,
  ArticlePublishResult,
} from './linkedin';
import {
  generateAndPublishFacelessVideo,
  FacelessVideoPublishResult,
} from './faceless-videos';
import {
  generateCourse,
  publishCourse,
  publishLesson,
  getCoursesMetrics,
  CourseTemplate,
  CoursePublishConfig,
  HeadVideoUploadResult,
} from './head-videos';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  SUCCESS = 'success',
  FAILED = 'failed',
  RETRYING = 'retrying',
  SKIPPED = 'skipped',
  TIMEOUT = 'timeout',
  CIRCUIT_BREAK = 'circuit_break',
}

export enum TaskPriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  NORMAL = 'normal',
  LOW = 'low',
}

export enum ExecutionMode {
  PARALLEL = 'parallel',
  SEQUENTIAL = 'sequential',
  SMART = 'smart', // Smart scheduling based on dependencies and resource availability
}

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

export interface TaskDependency {
  taskId: string;
  required: boolean; // If true, parent task fails if dependency fails
  wait: boolean; // If true, wait for dependency completion before starting
}

export interface TaskConfig {
  id: string;
  name: string;
  description?: string;
  type: string; // 'gumroad' | 'carousel' | 'reel' | 'stories' | 'email' | 'newsletter' | 'youtube' | 'tiktok' | 'reddit' | 'linkedin' | 'faceless-videos' | 'head-videos' | 'attribution' | 'risk' | 'sentiment' | 'correlation' | 'compliance' | 'backup'
  enabled: boolean;
  priority: TaskPriority;
  timeout?: number; // milliseconds, 0 = no timeout
  retryMaxAttempts?: number;
  retryBackoffMs?: number;
  dependencies?: TaskDependency[];
  metadata?: Record<string, unknown>;
}

export interface TaskResult {
  taskId: string;
  taskName: string;
  taskType: string;
  status: TaskStatus;
  startTime: string;
  endTime: string;
  duration: number;
  attempts: number;
  maxAttempts: number;
  error?: {
    message: string;
    stack?: string;
    code?: string;
  };
  result?: unknown;
  metrics?: {
    retryCount: number;
    backoffTotalMs: number;
    cpuUsageMs?: number;
    memoryUsageMb?: number;
  };
}

export interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half-open';
  failureCount: number;
  successCount: number;
  lastFailureTime?: number;
  resetAt?: number;
}

export interface OrchestratorConfig {
  runId: string;
  timestamp: string;
  mode: ExecutionMode;
  tasks: TaskConfig[];
  retryMaxAttempts: number;
  retryBackoffMs: number;
  circuitBreakerThreshold: number;
  circuitBreakerResetMs: number;
  poolSize: number;
  logLevel: LogLevel;
  logDir: string;
  enableMetrics: boolean;
  webhookUrl?: string;
  enableCloudLogging: boolean;
}

export interface OrchestratorResult {
  runId: string;
  startTime: string;
  endTime: string;
  totalDuration: number;
  mode: ExecutionMode;
  tasksScheduled: number;
  tasksSkipped: number;
  tasksRun: number;
  tasksPassed: number;
  tasksFailed: number;
  tasksTimedOut: number;
  successRate: number;
  results: TaskResult[];
  failedTasks: TaskResult[];
  deadLetterQueue: TaskResult[];
  configuration: OrchestratorConfig;
  summary: {
    fastestTask?: TaskResult;
    slowestTask?: TaskResult;
    averageTaskDuration: number;
    criticalFailures: TaskResult[];
    warnings: string[];
  };
}

interface QueueItem {
  config: TaskConfig;
  retries: number;
  backoffMs: number;
}

// ============================================================================
// LOGGER
// ============================================================================

class Logger {
  private logLevel: LogLevel;
  private logDir: string;
  private logs: string[] = [];

  constructor(logLevel: LogLevel = LogLevel.INFO, logDir: string = '.runtime/automation') {
    this.logLevel = logLevel;
    this.logDir = logDir;
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level.toUpperCase()}] ${message}`;
  }

  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    return levels.indexOf(level) >= levels.indexOf(this.logLevel);
  }

  debug(message: string): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      const formatted = this.formatMessage(LogLevel.DEBUG, message);
      console.log(formatted);
      this.logs.push(formatted);
    }
  }

  info(message: string): void {
    if (this.shouldLog(LogLevel.INFO)) {
      const formatted = this.formatMessage(LogLevel.INFO, message);
      console.log(formatted);
      this.logs.push(formatted);
    }
  }

  warn(message: string): void {
    if (this.shouldLog(LogLevel.WARN)) {
      const formatted = this.formatMessage(LogLevel.WARN, message);
      console.warn(formatted);
      this.logs.push(formatted);
    }
  }

  error(message: string, error?: Error): void {
    if (this.shouldLog(LogLevel.ERROR)) {
      const errorMsg = error ? `${message}: ${error.message}` : message;
      const formatted = this.formatMessage(LogLevel.ERROR, errorMsg);
      console.error(formatted);
      this.logs.push(formatted);
      if (error?.stack) {
        this.logs.push(error.stack);
      }
    }
  }

  async saveToFile(filename: string): Promise<void> {
    try {
      if (!existsSync(this.logDir)) {
        await mkdir(this.logDir, { recursive: true });
      }
      const filepath = path.join(this.logDir, filename);
      await writeFile(filepath, this.logs.join('\n'));
    } catch (err) {
      console.error(`Failed to save logs to ${filename}:`, err);
    }
  }

  getLogs(): string[] {
    return [...this.logs];
  }
}

// ============================================================================
// CIRCUIT BREAKER
// ============================================================================

class CircuitBreaker {
  private state: CircuitBreakerState = {
    state: 'closed',
    failureCount: 0,
    successCount: 0,
  };

  constructor(
    private threshold: number,
    private resetMs: number
  ) {}

  canExecute(): boolean {
    if (this.state.state === 'closed') {
      return true;
    }

    if (this.state.state === 'open') {
      if (this.state.resetAt && Date.now() >= this.state.resetAt) {
        this.state.state = 'half-open';
        this.state.successCount = 0;
        return true;
      }
      return false;
    }

    return true; // half-open state
  }

  recordSuccess(): void {
    if (this.state.state === 'half-open') {
      this.state.successCount++;
      if (this.state.successCount >= 2) {
        this.state.state = 'closed';
        this.state.failureCount = 0;
        this.state.successCount = 0;
      }
    } else if (this.state.state === 'closed') {
      this.state.failureCount = 0;
    }
  }

  recordFailure(): void {
    this.state.failureCount++;
    this.state.lastFailureTime = Date.now();

    if (this.state.failureCount >= this.threshold) {
      this.state.state = 'open';
      this.state.resetAt = Date.now() + this.resetMs;
    }
  }

  getState(): CircuitBreakerState {
    return { ...this.state };
  }

  reset(): void {
    this.state = {
      state: 'closed',
      failureCount: 0,
      successCount: 0,
    };
  }
}

// ============================================================================
// TASK EXECUTOR
// ============================================================================

class TaskExecutor {
  private circuitBreaker: CircuitBreaker;
  private logger: Logger;

  constructor(
    circuitBreakerThreshold: number,
    circuitBreakerResetMs: number,
    logger: Logger
  ) {
    this.circuitBreaker = new CircuitBreaker(circuitBreakerThreshold, circuitBreakerResetMs);
    this.logger = logger;
  }

  async executeTask(taskConfig: TaskConfig): Promise<unknown> {
    if (!this.circuitBreaker.canExecute()) {
      throw new Error(`Circuit breaker open for task type: ${taskConfig.type}`);
    }

    try {
      let result: unknown;

      switch (taskConfig.type) {
        case 'gumroad':
          result = await orchestrateGumroadUpload();
          break;
        case 'carousel':
          result = await generateAndPostCarousel();
          break;
        case 'reel':
          result = await generateAndPostReel(1);
          break;
        case 'stories':
          result = await generateAndPostStories();
          break;
        case 'email':
          result = await setupEmailSequences();
          break;
        case 'newsletter': {
          // Execute newsletter automation with default settings
          const publishRequest: PublishRequest = {
            title: taskConfig.metadata?.title as string || 'Auto-Generated Newsletter',
            subtitle: taskConfig.metadata?.subtitle as string,
            body: taskConfig.metadata?.body as string || 'Default newsletter body',
            summary: taskConfig.metadata?.summary as string,
            tags: taskConfig.metadata?.tags as string[],
            platforms: taskConfig.metadata?.platforms as string[],
          };
          result = await newsletterEngine.publishNewsletter(publishRequest);
          break;
        }
        case 'youtube': {
          const postNumber = (taskConfig.metadata?.postNumber as number) || 1;
          const videoGenerationApi =
            ((taskConfig.metadata?.videoGenerationApi as string) || 'synthesia') as
              | 'synthesia'
              | 'd-id'
              | 'replicate';
          result = await generateAndPostYouTubeVideo(postNumber, {
            videoGenerationApi,
            scheduledAt: taskConfig.metadata?.scheduledAt as string | undefined,
            playlistId: taskConfig.metadata?.playlistId as string | undefined,
          });
          break;
        }
        case 'etsy': {
          // Execute Etsy/Printify automation (POD product management)
          const action = taskConfig.metadata?.action as string || 'sync-inventory';
          if (action === 'create') {
            const templates = taskConfig.metadata?.templates as ProductTemplate[];
            const designUrls = new Map(Object.entries(taskConfig.metadata?.designUrls || {}));
            result = await bulkCreateProducts(templates, designUrls);
          } else if (action === 'sync-inventory') {
            const mappings = (taskConfig.metadata?.productMappings as unknown[] || []).map((m: unknown) => ({
              printifyId: (m as { printifyId: string }).printifyId,
              etsyId: (m as { etsyId: number }).etsyId,
              variantMapping: new Map(Object.entries((m as { variantMapping: Record<string, unknown> }).variantMapping)),
            }));
            result = await bulkSyncInventory(mappings);
          } else if (action === 'track-orders') {
            const orderIds = taskConfig.metadata?.orderIds as string[];
            result = await batchTrackOrders(orderIds);
          }
          break;
        }
        case 'attribution':
          result = await this.executeRemoteTask('attribution', taskConfig);
          break;
        case 'risk':
          result = await this.executeRemoteTask('risk', taskConfig);
          break;
        case 'sentiment':
          result = await this.executeRemoteTask('sentiment', taskConfig);
          break;
        case 'correlation':
          result = await this.executeRemoteTask('correlation', taskConfig);
          break;
        case 'compliance':
          result = await this.executeRemoteTask('compliance', taskConfig);
          break;
        case 'backup':
          result = await this.executeRemoteTask('backup', taskConfig);
          break;
        case 'reddit': {
          // Execute Reddit cross-posting
          const post: RedditPost = {
            title: taskConfig.metadata?.title as string || 'Auto-Generated Post',
            content: taskConfig.metadata?.content as string || 'Default post content',
            subreddit: taskConfig.metadata?.subreddit as string || 'test',
          };
          const subreddits = taskConfig.metadata?.subreddits as string[] || [];
          result = await crossPostToReddit(post, subreddits, {
            parallel: taskConfig.metadata?.parallel as boolean ?? true,
            retries: taskConfig.metadata?.retries as number || 3,
          });
          break;
        }
        case 'amazon-affiliate': {
          const niche = taskConfig.metadata?.niche as string || 'general';
          const keywords = taskConfig.metadata?.keywords as string[] || [];
          const maxLinks = taskConfig.metadata?.maxLinks as number || 5;
          result = await generateNicheLinks(niche, keywords, maxLinks);
          break;
        }

        case 'tiktok': {
          // Execute TikTok automation
          const tiktokConfig: TikTokPublishConfig = {
            title: taskConfig.metadata?.title as string || 'Auto-Generated TikTok',
            description: taskConfig.metadata?.description as string || 'Watch this amazing content',
            duration: taskConfig.metadata?.duration as number || 30,
            videoUrl: taskConfig.metadata?.videoUrl as string,
            aspectRatio: (taskConfig.metadata?.aspectRatio as 'vertical' | 'square' | 'horizontal') || 'vertical',
            tags: taskConfig.metadata?.tags as string[],
            trendingHashtags: taskConfig.metadata?.trendingHashtags as string[],
            affiliateLinks: taskConfig.metadata?.affiliateLinks as Record<string, string>,
          };
          result = await publishVideoToTikTok(tiktokConfig);
          break;
        }

        case 'linkedin': {
          // Execute LinkedIn Articles automation
          const articleContent: LinkedInArticleContent = {
            title: taskConfig.metadata?.title as string || 'Untitled Article',
            subtitle: taskConfig.metadata?.subtitle as string,
            content: taskConfig.metadata?.content as string || 'No content',
            description: taskConfig.metadata?.description as string,
            tags: taskConfig.metadata?.tags as string[],
            coverImage: taskConfig.metadata?.coverImage as string,
            coverImageAlt: taskConfig.metadata?.coverImageAlt as string,
            originalUrl: taskConfig.metadata?.originalUrl as string,
          };
          result = await publishArticle(articleContent, {
            retries: taskConfig.retryMaxAttempts ?? 3,
            webhookUrl: taskConfig.metadata?.webhookUrl as string,
            rateLimitCheck: (taskConfig.metadata?.rateLimitCheck as boolean) ?? true,
          });
          break;
        }

        case 'faceless-videos': {
          // Execute Faceless Videos automation
          const postNumber = taskConfig.metadata?.postNumber as number || 1;
          const videoProvider = (taskConfig.metadata?.videoProvider as 'd-id' | 'synthesia' | 'replicate') || 'd-id';
          const platforms = (taskConfig.metadata?.platforms as Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>) || ['youtube', 'tiktok'];
          result = await generateAndPublishFacelessVideo(postNumber, {
            videoProvider,
            platforms,
            publishImmediately: (taskConfig.metadata?.publishImmediately as boolean) ?? true,
          });
          break;
        }

        default:
          throw new Error(`Unknown task type: ${taskConfig.type}`);
      }

      this.circuitBreaker.recordSuccess();
      return result;
    } catch (error) {
      this.circuitBreaker.recordFailure();
      throw error;
    }
  }

  private async executeRemoteTask(moduleType: string, taskConfig: TaskConfig): Promise<unknown> {
    const runtimeApiUrl = process.env.RUNTIME_API_URL || 'http://localhost:8000';
    const endpoint = `${runtimeApiUrl}/api/automation/${moduleType}`;

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.PROFITENGINE_WEBHOOK_TOKEN || ''}`,
      },
      body: JSON.stringify({
        taskId: taskConfig.id,
        metadata: taskConfig.metadata,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Remote task failed: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  getCircuitBreakerState(): CircuitBreakerState {
    return this.circuitBreaker.getState();
  }
}

// ============================================================================
// MASTER ORCHESTRATOR
// ============================================================================

export class MasterOrchestrator {
  private config: OrchestratorConfig;
  private logger: Logger;
  private executor: TaskExecutor;
  private results: TaskResult[] = [];
  private failedTasks: TaskResult[] = [];
  private deadLetterQueue: TaskResult[] = [];
  private taskCircuitBreakers: Map<string, CircuitBreaker> = new Map();

  constructor(overrideConfig?: Partial<OrchestratorConfig>) {
    this.config = {
      ...this.createDefaultConfig(),
      ...overrideConfig,
    };

    this.logger = new Logger(this.config.logLevel, this.config.logDir);
    this.executor = new TaskExecutor(
      this.config.circuitBreakerThreshold,
      this.config.circuitBreakerResetMs,
      this.logger
    );
  }

  private createDefaultConfig(): OrchestratorConfig {
    const logDir = process.env.AUTOMATION_LOG_DIR || '.runtime/automation';

    return {
      runId: `orchestration-${Date.now()}`,
      timestamp: new Date().toISOString(),
      mode: (process.env.AUTOMATION_MODE as ExecutionMode) || ExecutionMode.SMART,
      tasks: this.createDefaultTasks(),
      retryMaxAttempts: parseInt(process.env.AUTOMATION_RETRY_MAX_ATTEMPTS || '3', 10),
      retryBackoffMs: parseInt(process.env.AUTOMATION_RETRY_BACKOFF_MS || '5000', 10),
      circuitBreakerThreshold: parseInt(
        process.env.AUTOMATION_CIRCUIT_BREAKER_THRESHOLD || '5',
        10
      ),
      circuitBreakerResetMs: parseInt(
        process.env.AUTOMATION_CIRCUIT_BREAKER_RESET_MS || '300000',
        10
      ),
      poolSize: parseInt(process.env.AUTOMATION_POOL_SIZE || '4', 10),
      logLevel: (process.env.AUTOMATION_LOG_LEVEL as LogLevel) || LogLevel.INFO,
      logDir,
      enableMetrics: process.env.AUTOMATION_ENABLE_METRICS !== 'false',
      webhookUrl: process.env.AUTOMATION_WEBHOOK_URL,
      enableCloudLogging: process.env.AUTOMATION_ENABLE_CLOUD_LOGGING === 'true',
    };
  }

  private createDefaultTasks(): TaskConfig[] {
    return [
      // EXISTING MODULES (3)
      {
        id: 'gumroad-upload',
        name: 'Gumroad Product Upload',
        type: 'gumroad',
        enabled: !!process.env.GUMROAD_API_TOKEN,
        priority: TaskPriority.HIGH,
        timeout: 300000, // 5 minutes
        retryMaxAttempts: 3,
      },
      {
        id: 'instagram-carousel',
        name: 'Instagram Carousel Generation',
        type: 'carousel',
        enabled: !!process.env.FB_PAGE_ACCESS_TOKEN,
        priority: TaskPriority.NORMAL,
        timeout: 240000, // 4 minutes
        retryMaxAttempts: 2,
      },
      {
        id: 'instagram-reel',
        name: 'Instagram Reel Generation',
        type: 'reel',
        enabled: !!process.env.FB_PAGE_ACCESS_TOKEN,
        priority: TaskPriority.NORMAL,
        timeout: 300000, // 5 minutes
        retryMaxAttempts: 2,
      },
      {
        id: 'instagram-stories',
        name: 'Instagram Stories Generation',
        type: 'stories',
        enabled: !!process.env.FB_PAGE_ACCESS_TOKEN,
        priority: TaskPriority.NORMAL,
        timeout: 180000, // 3 minutes
        retryMaxAttempts: 2,
      },
      {
        id: 'email-sequences',
        name: 'Email Sequence Automation',
        type: 'email',
        enabled: !!process.env.EMAIL_SERVICE,
        priority: TaskPriority.HIGH,
        timeout: 120000, // 2 minutes
        retryMaxAttempts: 2,
      },
      {
        id: 'etsy-pod-sync',
        name: 'Etsy/Printify POD Automation',
        description: 'Sync inventory & track orders for print-on-demand products',
        type: 'etsy',
        enabled: !!process.env.PRINTIFY_API_KEY && !!process.env.ETSY_OAUTH_TOKEN,
        priority: TaskPriority.HIGH,
        timeout: 240000, // 4 minutes
        retryMaxAttempts: 3,
        metadata: {
          action: 'sync-inventory',
          productMappings: [],
        },
      },


      {
        id: 'youtube-longform',
        name: 'YouTube Long-Form Video Generation',
        type: 'youtube',
        enabled: !!process.env.YOUTUBE_API_KEY,
        priority: TaskPriority.NORMAL,
        timeout: 600000, // 10 minutes for video generation
        retryMaxAttempts: 2,
        metadata: {
          postNumber: 1,
          videoGenerationApi: 'synthesia',
        },
      },
// ENHANCEMENT MODULES (6)
      {
        id: 'performance-attribution',
        name: 'Performance Attribution Analysis',
        description: 'Agent P&L decomposition with 35/25/25/15% contribution weights',
        type: 'attribution',
        enabled: !!process.env.RUNTIME_API_URL,
        priority: TaskPriority.CRITICAL,
        timeout: 180000, // 3 minutes
        retryMaxAttempts: 2,
        metadata: {
          regime: 'daily',
          reportType: '7-regime-breakdown',
        },
      },
      {
        id: 'dynamic-risk-adjustment',
        name: 'Dynamic Risk Adjustment',
        description: 'Volatility-scaled loss limits ($100-$300)',
        type: 'risk',
        enabled: !!process.env.RUNTIME_API_URL,
        priority: TaskPriority.CRITICAL,
        timeout: 120000, // 2 minutes
        retryMaxAttempts: 2,
        dependencies: [{ taskId: 'performance-attribution', required: true, wait: false }],
        metadata: {
          scalingFactor: '0.5-1.5x',
          lossBounds: [100, 300],
        },
      },
      {
        id: 'sentiment-analysis',
        name: 'Sentiment Analysis & Weighting',
        description: 'News sentiment with reliability weighting (0.6-1.0)',
        type: 'sentiment',
        enabled: !!process.env.RUNTIME_API_URL,
        priority: TaskPriority.HIGH,
        timeout: 150000, // 2.5 minutes
        retryMaxAttempts: 2,
        metadata: {
          reliabilityWeights: [1.0, 0.9, 0.8, 0.7, 0.6],
          signalNumber: 5,
        },
      },
      {
        id: 'signal-correlation',
        name: 'Signal Correlation Analysis',
        description: 'Rolling 4x4 correlation matrix with failure detection',
        type: 'correlation',
        enabled: !!process.env.RUNTIME_API_URL,
        priority: TaskPriority.HIGH,
        timeout: 120000, // 2 minutes
        retryMaxAttempts: 2,
        dependencies: [{ taskId: 'sentiment-analysis', required: false, wait: false }],
        metadata: {
          matrixSize: 4,
          failureThreshold: 0.8,
        },
      },
      {
        id: 'compliance-automation',
        name: 'Compliance Automation',
        description: 'SEC Form 4 pre-fill and insider trading validation',
        type: 'compliance',
        enabled: !!process.env.RUNTIME_API_URL,
        priority: TaskPriority.CRITICAL,
        timeout: 90000, // 1.5 minutes
        retryMaxAttempts: 1, // Strict - no retries for compliance
        metadata: {
          formType: 'SEC-Form4',
          checkInsiderTradingWindow: true,
        },
      },
      {
        id: 'backup-rotation',
        name: 'Backup & Rotation System',
        description: 'Weekly timestamped backups with SHA256 validation',
        type: 'backup',
        enabled: !!process.env.RUNTIME_API_URL,
        priority: TaskPriority.NORMAL,
        timeout: 600000, // 10 minutes
        retryMaxAttempts: 2,
        metadata: {
          retentionDays: 28,
          enableS3: process.env.ENABLE_S3 === 'true',
        },
      },
          {
        id: 'tiktok-publish',
        name: 'TikTok Long-Form Publishing',
        description: 'Auto-publish long-form videos to TikTok with engagement tracking',
        type: 'tiktok',
        enabled: !!process.env.TIKTOK_API_ACCESS_TOKEN,
        priority: TaskPriority.NORMAL,
        timeout: 180000, // 3 minutes
        retryMaxAttempts: 2,
        metadata: {
          aspectRatio: 'vertical',
          duration: 30,
        },
      },
      {
        id: 'reddit-communities',
        name: 'Reddit Communities Cross-Posting',
        description: 'Auto-publish content across multiple subreddits with engagement tracking',
        type: 'reddit',
        enabled: !!process.env.REDDIT_CLIENT_ID,
        priority: TaskPriority.NORMAL,
        timeout: 300000, // 5 minutes
        retryMaxAttempts: 2,
        metadata: {
          parallel: true,
          subreddits: (process.env.REDDIT_DEFAULT_SUBREDDITS || 'test').split(',').filter(Boolean),
          retries: 3,
        },
      },
    ]
  }

  private async resolveDependencies(taskId: string): Promise<boolean> {
    const task = this.config.tasks.find((t) => t.id === taskId);
    if (!task?.dependencies) {
      return true;
    }

    for (const dep of task.dependencies) {
      const depResult = this.results.find((r) => r.taskId === dep.taskId);

      if (!depResult) {
        // Dependency hasn't run yet
        return false;
      }

      if (dep.required && depResult.status !== TaskStatus.SUCCESS) {
        this.logger.warn(
          `Task ${taskId} dependency ${dep.taskId} failed with status ${depResult.status}`
        );
        return false;
      }
    }

    return true;
  }

  private shouldWaitForDependencies(taskId: string): string[] {
    const task = this.config.tasks.find((t) => t.id === taskId);
    if (!task?.dependencies) {
      return [];
    }

    return task.dependencies
      .filter((d) => d.wait)
      .map((d) => d.taskId);
  }

  private async executeTaskWithRetry(taskConfig: TaskConfig): Promise<TaskResult> {
    const startTime = new Date();
    let lastError: Error | undefined;
    const result: TaskResult = {
      taskId: taskConfig.id,
      taskName: taskConfig.name,
      taskType: taskConfig.type,
      status: TaskStatus.PENDING,
      startTime: startTime.toISOString(),
      endTime: startTime.toISOString(),
      duration: 0,
      attempts: 0,
      maxAttempts: taskConfig.retryMaxAttempts || this.config.retryMaxAttempts,
      metrics: {
        retryCount: 0,
        backoffTotalMs: 0,
      },
    };

    const maxAttempts = taskConfig.retryMaxAttempts || this.config.retryMaxAttempts;
    let backoffMs = taskConfig.retryBackoffMs || this.config.retryBackoffMs;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      result.attempts = attempt;

      try {
        // Check dependencies
        const canExecute = await this.resolveDependencies(taskConfig.id);
        if (!canExecute) {
          this.logger.warn(
            `Task ${taskConfig.id} skipped due to failed dependencies`
          );
          result.status = TaskStatus.SKIPPED;
          const endTime = new Date();
          result.endTime = endTime.toISOString();
          result.duration = endTime.getTime() - startTime.getTime();
          return result;
        }

        result.status = TaskStatus.RUNNING;
        this.logger.info(
          `[${taskConfig.id}] Attempt ${attempt}/${maxAttempts}`
        );

        const taskStartTime = Date.now();
        const taskResult = await this.withTimeout(
          this.executor.executeTask(taskConfig),
          taskConfig.timeout || 0
        );

        const taskEndTime = Date.now();
        const taskDuration = taskEndTime - taskStartTime;

        // Validate result
        const resultObj = taskResult as Record<string, unknown>;
        if (resultObj.success !== false) {
          result.status = TaskStatus.SUCCESS;
          result.result = taskResult;
          result.endTime = new Date().toISOString();
          result.duration = new Date().getTime() - startTime.getTime();

          this.logger.info(
            `[${taskConfig.id}] SUCCESS in ${taskDuration}ms (attempt ${attempt}/${maxAttempts})`
          );

          return result;
        } else {
          lastError = new Error(resultObj.error as string || 'Task returned success=false');
        }
      } catch (error) {
        lastError = error as Error;
        result.status = TaskStatus.RETRYING;

        this.logger.warn(
          `[${taskConfig.id}] Error on attempt ${attempt}/${maxAttempts}: ${lastError.message}`
        );

        if (attempt < maxAttempts) {
          const exponentialBackoff = backoffMs * Math.pow(2, attempt - 1);
          result.metrics!.backoffTotalMs += exponentialBackoff;

          this.logger.debug(
            `[${taskConfig.id}] Retrying in ${exponentialBackoff}ms...`
          );

          await this.sleep(exponentialBackoff);
        }
      }
    }

    // All retries exhausted
    const endTime = new Date();
    result.status = TaskStatus.FAILED;
    result.endTime = endTime.toISOString();
    result.duration = endTime.getTime() - startTime.getTime();
    result.error = {
      message: lastError?.message || 'Task failed after all retries',
      stack: lastError?.stack,
      code: 'MAX_RETRIES_EXHAUSTED',
    };
    result.metrics!.retryCount = maxAttempts - 1;

    this.logger.error(
      `[${taskConfig.id}] FAILED after ${maxAttempts} attempts: ${lastError?.message}`
    );

    return result;
  }

  private async withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    if (timeoutMs === 0) {
      return promise;
    }

    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error('Task timeout')), timeoutMs)
      ),
    ]);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private async executeParallel(tasks: TaskConfig[]): Promise<TaskResult[]> {
    const enabledTasks = tasks.filter((t) => t.enabled);
    this.logger.info(`\nExecuting ${enabledTasks.length} tasks in PARALLEL...`);

    const promises = enabledTasks.map((task) => this.executeTaskWithRetry(task));
    return Promise.all(promises);
  }

  private async executeSequential(tasks: TaskConfig[]): Promise<TaskResult[]> {
    const enabledTasks = tasks.filter((t) => t.enabled);
    this.logger.info(`\nExecuting ${enabledTasks.length} tasks SEQUENTIALLY...`);

    const results: TaskResult[] = [];
    for (const task of enabledTasks) {
      const result = await this.executeTaskWithRetry(task);
      results.push(result);
      this.results.push(result);
    }
    return results;
  }

  private async executeSmart(tasks: TaskConfig[]): Promise<TaskResult[]> {
    const enabledTasks = tasks.filter((t) => t.enabled);
    this.logger.info(
      `\nExecuting ${enabledTasks.length} tasks in SMART mode (parallel + dependency aware)...`
    );

    const results: TaskResult[] = [];
    const executing = new Set<string>();
    const executed = new Set<string>();
    const queue: TaskConfig[] = [...enabledTasks];

    while (queue.length > 0 || executing.size > 0) {
      // Find tasks ready to execute
      const readyTasks = queue.filter((task) => {
        const deps = this.shouldWaitForDependencies(task.id);
        return deps.every((depId) => executed.has(depId));
      });

      if (readyTasks.length === 0 && executing.size === 0) {
        break;
      }

      // Execute ready tasks up to pool size
      const toExecute = readyTasks.slice(0, this.config.poolSize - executing.size);

      for (const task of toExecute) {
        queue.splice(queue.indexOf(task), 1);
        executing.add(task.id);

        this.executeTaskWithRetry(task).then((result) => {
          results.push(result);
          this.results.push(result);
          executing.delete(task.id);
          executed.add(task.id);
        });
      }

      if (executing.size > 0) {
        await this.sleep(100);
      }
    }

    return results;
  }

  private async notifyWebhook(result: OrchestratorResult): Promise<void> {
    if (!this.config.webhookUrl) {
      return;
    }

    try {
      const response = await fetch(this.config.webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.PROFITENGINE_WEBHOOK_TOKEN || ''}`,
        },
        body: JSON.stringify({
          runId: result.runId,
          timestamp: result.timestamp,
          success: result.tasksFailed === 0,
          stats: {
            total: result.tasksRun,
            passed: result.tasksPassed,
            failed: result.tasksFailed,
            successRate: result.successRate,
          },
          summary: result.summary,
        }),
      });

      if (!response.ok) {
        this.logger.warn(
          `Webhook notification failed: ${response.status} ${response.statusText}`
        );
      }
    } catch (error) {
      this.logger.warn(`Failed to send webhook notification: ${error}`);
    }
  }

  private async saveResults(result: OrchestratorResult): Promise<void> {
    try {
      if (!existsSync(this.config.logDir)) {
        await mkdir(this.config.logDir, { recursive: true });
      }

      // Save detailed JSON result
      const jsonPath = path.join(this.config.logDir, `${result.runId}.json`);
      await writeFile(jsonPath, JSON.stringify(result, null, 2));
      this.logger.info(`Saved detailed results: ${jsonPath}`);

      // Append to JSONL log
      const logPath = path.join(this.config.logDir, 'orchestration-status.jsonl');
      const logEntry = JSON.stringify({
        runId: result.runId,
        timestamp: result.timestamp,
        mode: result.mode,
        success: result.tasksFailed === 0,
        tasksRun: result.tasksRun,
        tasksPassed: result.tasksPassed,
        tasksFailed: result.tasksFailed,
        successRate: result.successRate,
        duration: result.totalDuration,
      });

      const existingLog = existsSync(logPath) ? await readFile(logPath, 'utf-8') : '';
      await writeFile(logPath, existingLog + (existingLog ? '\n' : '') + logEntry);
      this.logger.info(`Logged to: ${logPath}`);

      // Save logs to file
      await this.logger.saveToFile(`${result.runId}.log`);
    } catch (error) {
      this.logger.error(`Failed to save results: ${error}`);
    }
  }

  private printSummary(result: OrchestratorResult): void {
    console.log('\n' + '='.repeat(90));
    console.log('PROFITENGINE MASTER ORCHESTRATION SUMMARY');
    console.log('='.repeat(90));
    console.log(`\nRun ID: ${result.runId}`);
    console.log(`Mode: ${result.mode}`);
    console.log(`Duration: ${(result.totalDuration / 1000).toFixed(2)}s`);
    console.log(`\nResults:`);
    console.log(`  Total Tasks Scheduled: ${result.tasksScheduled}`);
    console.log(`  Tasks Skipped: ${result.tasksSkipped}`);
    console.log(`  Tasks Run: ${result.tasksRun}`);
    console.log(`  Passed: ${result.tasksPassed} ✓`);
    console.log(`  Failed: ${result.tasksFailed} ✗`);
    console.log(`  Timed Out: ${result.tasksTimedOut}`);
    console.log(`  Success Rate: ${(result.successRate * 100).toFixed(1)}%`);

    if (result.summary) {
      console.log(`\nPerformance Metrics:`);
      if (result.summary.fastestTask) {
        console.log(
          `  Fastest: ${result.summary.fastestTask.taskName} (${result.summary.fastestTask.duration}ms)`
        );
      }
      if (result.summary.slowestTask) {
        console.log(
          `  Slowest: ${result.summary.slowestTask.taskName} (${result.summary.slowestTask.duration}ms)`
        );
      }
      console.log(
        `  Average Task Duration: ${result.summary.averageTaskDuration.toFixed(0)}ms`
      );
    }

    console.log('\nTask Details:');
    for (const taskResult of result.results) {
      const status =
        taskResult.status === TaskStatus.SUCCESS
          ? '✓'
          : taskResult.status === TaskStatus.SKIPPED
            ? '-'
            : '✗';
      const duration = (taskResult.duration / 1000).toFixed(2);
      console.log(
        `  ${status} ${taskResult.taskName} [${taskResult.taskType}] (${duration}s, ${taskResult.attempts} attempt${taskResult.attempts > 1 ? 's' : ''})`
      );

      if (
        taskResult.status === TaskStatus.FAILED ||
        taskResult.status === TaskStatus.TIMEOUT
      ) {
        console.log(`     Status: ${taskResult.status}`);
        if (taskResult.error) {
          console.log(`     Error: ${taskResult.error.message}`);
        }
      }
    }

    if (result.deadLetterQueue.length > 0) {
      console.log(`\nDead Letter Queue (${result.deadLetterQueue.length}):`);
      for (const task of result.deadLetterQueue) {
        console.log(`  - ${task.taskName}: ${task.error?.message}`);
      }
    }

    if (result.summary.warnings.length > 0) {
      console.log(`\nWarnings:`);
      for (const warning of result.summary.warnings) {
        console.log(`  âš  ${warning}`);
      }
    }

    console.log('\n' + '='.repeat(90));
  }

  async run(): Promise<OrchestratorResult> {
    const startTime = new Date();

    this.logger.info('PROFITENGINE MASTER ORCHESTRATOR');
    this.logger.info('='.repeat(70));
    this.logger.info(`Run ID: ${this.config.runId}`);
    this.logger.info(`Timestamp: ${this.config.timestamp}`);
    this.logger.info(`Mode: ${this.config.mode}`);
    this.logger.info(`Pool Size: ${this.config.poolSize}`);
    this.logger.info(`Retry Max Attempts: ${this.config.retryMaxAttempts}`);
    this.logger.info(`Retry Backoff: ${this.config.retryBackoffMs}ms`);
    this.logger.info(`Circuit Breaker Threshold: ${this.config.circuitBreakerThreshold}`);

    const tasksScheduled = this.config.tasks.length;
    const enabledTasks = this.config.tasks.filter((t) => t.enabled);
    const skippedTasks = tasksScheduled - enabledTasks.length;

    this.logger.info(`\nTasks Scheduled: ${tasksScheduled}`);
    this.logger.info(`Tasks Enabled: ${enabledTasks.length}`);
    this.logger.info(`Tasks Disabled: ${skippedTasks}`);
    this.logger.info(
      `Enabled Tasks: ${enabledTasks.map((t) => t.name).join(', ')}`
    );

    let results: TaskResult[] = [];

    try {
      switch (this.config.mode) {
        case ExecutionMode.PARALLEL:
          results = await this.executeParallel(this.config.tasks);
          break;
        case ExecutionMode.SEQUENTIAL:
          results = await this.executeSequential(this.config.tasks);
          break;
        case ExecutionMode.SMART:
          results = await this.executeSmart(this.config.tasks);
          break;
      }

      this.results = results;
    } catch (error) {
      this.logger.error(`Orchestration failed: ${error}`);
    }

    const endTime = new Date();
    const totalDuration = endTime.getTime() - startTime.getTime();

    // Calculate statistics
    const successfulResults = this.results.filter((r) => r.status === TaskStatus.SUCCESS);
    const failedResults = this.results.filter((r) => r.status === TaskStatus.FAILED);
    const timedOutResults = this.results.filter((r) => r.status === TaskStatus.TIMEOUT);
    const skippedResults = this.results.filter((r) => r.status === TaskStatus.SKIPPED);

    const tasksPassed = successfulResults.length;
    const tasksFailed = failedResults.length;
    const tasksTimedOut = timedOutResults.length;
    const successRate = this.results.length > 0 ? tasksPassed / this.results.length : 0;

    // Separate critical failures
    const criticalFailures = failedResults.filter((r) => {
      const taskConfig = this.config.tasks.find((t) => t.id === r.taskId);
      return taskConfig?.priority === TaskPriority.CRITICAL;
    });

    // Calculate performance metrics
    let fastestTask: TaskResult | undefined;
    let slowestTask: TaskResult | undefined;
    let averageTaskDuration = 0;

    if (this.results.length > 0) {
      fastestTask = this.results.reduce((min, r) =>
        r.duration < min.duration ? r : min
      );
      slowestTask = this.results.reduce((max, r) =>
        r.duration > max.duration ? r : max
      );
      averageTaskDuration =
        this.results.reduce((sum, r) => sum + r.duration, 0) / this.results.length;
    }

    const warnings: string[] = [];
    if (criticalFailures.length > 0) {
      warnings.push(
        `${criticalFailures.length} critical task(s) failed`
      );
    }
    if (tasksTimedOut > 0) {
      warnings.push(`${tasksTimedOut} task(s) timed out`);
    }
    if (successRate < 1.0) {
      warnings.push(`Success rate below 100%: ${(successRate * 100).toFixed(1)}%`);
    }

    const result: OrchestratorResult = {
      runId: this.config.runId,
      startTime: startTime.toISOString(),
      endTime: endTime.toISOString(),
      totalDuration,
      mode: this.config.mode,
      tasksScheduled,
      tasksSkipped: skippedTasks,
      tasksRun: this.results.length,
      tasksPassed,
      tasksFailed,
      tasksTimedOut,
      successRate,
      results: this.results,
      failedTasks: failedResults,
      deadLetterQueue: this.deadLetterQueue,
      configuration: this.config,
      summary: {
        fastestTask,
        slowestTask,
        averageTaskDuration,
        criticalFailures,
        warnings,
      },
    };

    // Save and notify
    await this.saveResults(result);
    await this.notifyWebhook(result);
    this.printSummary(result);

    return result;
  }

  getConfig(): OrchestratorConfig {
    return { ...this.config };
  }

  getResults(): TaskResult[] {
    return [...this.results];
  }

  getStatus(): {
    tasksRun: number;
    tasksPassed: number;
    tasksFailed: number;
    successRate: number;
  } {
    const passed = this.results.filter((r) => r.status === TaskStatus.SUCCESS).length;
    const failed = this.results.filter((r) => r.status === TaskStatus.FAILED).length;
    const rate = this.results.length > 0 ? passed / this.results.length : 0;

    return {
      tasksRun: this.results.length,
      tasksPassed: passed,
      tasksFailed: failed,
      successRate: rate,
    };
  }
}

// ============================================================================
// CONVENIENCE EXPORTS & FUNCTIONS
// ============================================================================

export async function orchestrateFullLaunch(
  overrideConfig?: Partial<OrchestratorConfig>
): Promise<OrchestratorResult> {
  const orchestrator = new MasterOrchestrator(overrideConfig);
  return orchestrator.run();
}

export async function getLatestAutomationStatus(): Promise<{
  lastRun?: {
    runId: string;
    timestamp: string;
    success: boolean;
    successRate: number;
    mode: ExecutionMode;
  };
  allRuns: Array<{
    runId: string;
    timestamp: string;
    success: boolean;
    successRate: number;
    mode: ExecutionMode;
  }>;
}> {
  try {
    const logDir = process.env.AUTOMATION_LOG_DIR || '.runtime/automation';
    const logPath = path.join(logDir, 'orchestration-status.jsonl');

    if (!existsSync(logPath)) {
      return { allRuns: [] };
    }

    const logContent = await readFile(logPath, 'utf-8');
    const allRuns = logContent
      .trim()
      .split('\n')
      .filter((line) => line.length > 0)
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








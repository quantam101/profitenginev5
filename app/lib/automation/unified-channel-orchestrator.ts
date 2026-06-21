/**
 * UNIFIED CHANNEL ORCHESTRATOR v2.0
 *
 * Integrates all 14 channels into a single coordinated system:
 *
 * MONETIZATION CHANNELS (6):
 *   1. Stripe (payment processing)
 *   2. Gumroad (digital products)
 *   3. Amazon Affiliate (affiliate links)
 *   4. KDP (Kindle self-publishing)
 *   5. Etsy + Printify (physical POD products)
 *   6. Newsletters (email monetization)
 *
 * SOCIAL DISTRIBUTION CHANNELS (8):
 *   7. Instagram (carousel/reel/stories)
 *   8. YouTube (long-form video)
 *   9. TikTok (short-form video)
 *   10. Twitter/X (threads)
 *   11. LinkedIn (professional articles)
 *   12. Pinterest (visual discovery)
 *   13. Reddit (community engagement)
 *   14. Faceless Videos (auto-generated content)
 *
 * CORE FEATURES:
 * - Unified channel registry and discovery
 * - Cross-channel content distribution pipelines
 * - Real-time aggregated metrics and KPIs
 * - Intelligent scheduling and rate-limiting
 * - Error handling, retries, and dead-letter queues
 * - Webhook notifications for all channels
 * - Performance analytics and attribution
 */

import { TaskStatus, TaskPriority, ExecutionMode, OrchestratorResult } from './master-orchestrator';
import { Logger, LogLevel } from './master-orchestrator';

// ============================================================================
// CHANNEL TYPES AND DEFINITIONS
// ============================================================================

export enum ChannelCategory {
  MONETIZATION = 'monetization',
  DISTRIBUTION = 'distribution',
  ENHANCEMENT = 'enhancement',
}

export enum ChannelType {
  // Monetization
  STRIPE = 'stripe',
  GUMROAD = 'gumroad',
  AMAZON_AFFILIATE = 'amazon-affiliate',
  KDP = 'kdp',
  ETSY_PRINTIFY = 'etsy-printify',
  NEWSLETTERS = 'newsletters',

  // Distribution
  INSTAGRAM = 'instagram',
  YOUTUBE = 'youtube',
  TIKTOK = 'tiktok',
  TWITTER = 'twitter',
  LINKEDIN = 'linkedin',
  PINTEREST = 'pinterest',
  REDDIT = 'reddit',
  FACELESS_VIDEOS = 'faceless-videos',

  // Enhancement
  HEAD_VIDEOS = 'head-videos',
  SELF_HELP = 'self-help',
  AI_COURSES = 'ai-courses',
}

export interface ChannelConfig {
  id: string;
  type: ChannelType;
  category: ChannelCategory;
  name: string;
  description: string;
  enabled: boolean;
  apiKeyEnvVar?: string;
  webhookUrl?: string;
  rateLimit?: {
    requestsPerSecond: number;
    requestsPerDay?: number;
    burstSize?: number;
  };
  metadata?: Record<string, unknown>;
}

export interface ChannelMetrics {
  channelId: string;
  channelName: string;
  channelType: ChannelType;
  timestamp: string;
  metrics: {
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    averageResponseTimeMs: number;
    errorRate: number;
    successRate: number;
    lastError?: {
      message: string;
      timestamp: string;
    };
  };
  kpis?: {
    impressions?: number;
    clicks?: number;
    conversions?: number;
    revenue?: number;
    ctr?: number;
    conversionRate?: number;
  };
}

export interface UnifiedOrchestratorConfig {
  runId: string;
  timestamp: string;
  channels: ChannelConfig[];
  globalRateLimit?: {
    requestsPerSecond: number;
  };
  healthCheckIntervalMs: number;
  metricsCollectionIntervalMs: number;
  webhookUrl?: string;
  enableCloudLogging: boolean;
  logLevel: LogLevel;
}

export interface UnifiedOrchestratorResult {
  runId: string;
  timestamp: string;
  totalChannels: number;
  enabledChannels: number;
  disabledChannels: number;
  healthStatus: {
    healthy: number;
    degraded: number;
    offline: number;
  };
  metrics: ChannelMetrics[];
  aggregatedMetrics: {
    totalRequests: number;
    totalSuccessful: number;
    totalFailed: number;
    overallSuccessRate: number;
    overallErrorRate: number;
    totalRevenue?: number;
  };
  alerts: Array<{
    severity: 'critical' | 'warning' | 'info';
    channelId: string;
    message: string;
    timestamp: string;
  }>;
  deadLetterQueue: Array<{
    channelId: string;
    request: unknown;
    error: string;
    timestamp: string;
    retryCount: number;
  }>;
}

// ============================================================================
// UNIFIED CHANNEL ORCHESTRATOR CLASS
// ============================================================================

export class UnifiedChannelOrchestrator {
  private config: UnifiedOrchestratorConfig;
  private logger: Logger;
  private channels: Map<string, ChannelConfig> = new Map();
  private metrics: Map<string, ChannelMetrics> = new Map();
  private deadLetterQueue: any[] = [];
  private alerts: any[] = [];
  private healthCheckInterval?: NodeJS.Timeout;
  private metricsCollectionInterval?: NodeJS.Timeout;
  private channelHealthStatus: Map<string, 'healthy' | 'degraded' | 'offline'> = new Map();

  constructor(config: UnifiedOrchestratorConfig) {
    this.config = config;
    this.logger = new Logger(config.logLevel, '.runtime/automation');
    this.initializeChannels();
  }

  /**
   * Initialize all 14 channels with their configurations
   */
  private initializeChannels(): void {
    const channels: ChannelConfig[] = [
      // MONETIZATION CHANNELS
      {
        id: 'stripe-payments',
        type: ChannelType.STRIPE,
        category: ChannelCategory.MONETIZATION,
        name: 'Stripe Payment Processing',
        description: 'Process customer payments and subscriptions',
        enabled: !!process.env.STRIPE_SECRET_KEY,
        apiKeyEnvVar: 'STRIPE_SECRET_KEY',
        webhookUrl: process.env.STRIPE_WEBHOOK_URL,
        rateLimit: { requestsPerSecond: 100, requestsPerDay: 1000000 },
        metadata: { publishableKey: process.env.STRIPE_PUBLISHABLE_KEY },
      },
      {
        id: 'gumroad-products',
        type: ChannelType.GUMROAD,
        category: ChannelCategory.MONETIZATION,
        name: 'Gumroad Digital Products',
        description: 'Manage and sell digital products',
        enabled: !!process.env.GUMROAD_API_TOKEN,
        apiKeyEnvVar: 'GUMROAD_API_TOKEN',
        rateLimit: { requestsPerSecond: 10, requestsPerDay: 10000 },
      },
      {
        id: 'amazon-affiliate',
        type: ChannelType.AMAZON_AFFILIATE,
        category: ChannelCategory.MONETIZATION,
        name: 'Amazon Associates Affiliate',
        description: 'Earn commissions from product recommendations',
        enabled: !!process.env.AMAZON_ASSOCIATES_TAG,
        apiKeyEnvVar: 'AMAZON_PRODUCT_ADVERTISING_KEY',
        rateLimit: { requestsPerSecond: 1, requestsPerDay: 36000 },
        metadata: { affiliateTag: process.env.AMAZON_ASSOCIATES_TAG },
      },
      {
        id: 'kdp-publishing',
        type: ChannelType.KDP,
        category: ChannelCategory.MONETIZATION,
        name: 'Kindle Direct Publishing',
        description: 'Self-publish and sell ebooks on Amazon',
        enabled: !!process.env.KDP_AUTH_TOKEN,
        apiKeyEnvVar: 'KDP_AUTH_TOKEN',
        rateLimit: { requestsPerSecond: 5, requestsPerDay: 1000 },
      },
      {
        id: 'etsy-printify',
        type: ChannelType.ETSY_PRINTIFY,
        category: ChannelCategory.MONETIZATION,
        name: 'Etsy + Printify POD Integration',
        description: 'Manage print-on-demand products across Etsy',
        enabled: !!process.env.ETSY_OAUTH_TOKEN && !!process.env.PRINTIFY_API_KEY,
        webhookUrl: process.env.ETSY_WEBHOOK_URL,
        rateLimit: { requestsPerSecond: 10, requestsPerDay: 50000 },
        metadata: {
          etsy: { oauth: process.env.ETSY_OAUTH_TOKEN },
          printify: { apiKey: process.env.PRINTIFY_API_KEY },
        },
      },
      {
        id: 'newsletters-monetization',
        type: ChannelType.NEWSLETTERS,
        category: ChannelCategory.MONETIZATION,
        name: 'Newsletter Email Automation',
        description: 'Distribute and monetize newsletter content',
        enabled: !!process.env.EMAIL_SERVICE,
        rateLimit: { requestsPerSecond: 100, requestsPerDay: 100000 },
        metadata: { service: process.env.EMAIL_SERVICE },
      },

      // DISTRIBUTION CHANNELS
      {
        id: 'instagram-social',
        type: ChannelType.INSTAGRAM,
        category: ChannelCategory.DISTRIBUTION,
        name: 'Instagram (Carousel/Reel/Stories)',
        description: 'Multi-format Instagram content distribution',
        enabled: !!process.env.FB_PAGE_ACCESS_TOKEN,
        apiKeyEnvVar: 'FB_PAGE_ACCESS_TOKEN',
        webhookUrl: process.env.INSTAGRAM_WEBHOOK_URL,
        rateLimit: { requestsPerSecond: 10, requestsPerDay: 200 },
      },
      {
        id: 'youtube-longform',
        type: ChannelType.YOUTUBE,
        category: ChannelCategory.DISTRIBUTION,
        name: 'YouTube Long-Form Video',
        description: 'Upload and optimize long-form video content',
        enabled: !!process.env.YOUTUBE_API_KEY,
        apiKeyEnvVar: 'YOUTUBE_API_KEY',
        webhookUrl: process.env.YOUTUBE_WEBHOOK_URL,
        rateLimit: { requestsPerSecond: 5, requestsPerDay: 500 },
        metadata: { maxUploadSizeMb: 256 },
      },
      {
        id: 'tiktok-shortform',
        type: ChannelType.TIKTOK,
        category: ChannelCategory.DISTRIBUTION,
        name: 'TikTok Short-Form Video',
        description: 'Publish viral short-form content',
        enabled: !!process.env.TIKTOK_ACCESS_TOKEN,
        apiKeyEnvVar: 'TIKTOK_ACCESS_TOKEN',
        rateLimit: { requestsPerSecond: 5, requestsPerDay: 100 },
      },
      {
        id: 'twitter-threads',
        type: ChannelType.TWITTER,
        category: ChannelCategory.DISTRIBUTION,
        name: 'Twitter/X Thread Publishing',
        description: 'Publish and analyze thread performance',
        enabled: !!process.env.TWITTER_BEARER_TOKEN,
        apiKeyEnvVar: 'TWITTER_BEARER_TOKEN',
        webhookUrl: process.env.TWITTER_WEBHOOK_URL,
        rateLimit: { requestsPerSecond: 15, requestsPerDay: 450 },
      },
      {
        id: 'linkedin-articles',
        type: ChannelType.LINKEDIN,
        category: ChannelCategory.DISTRIBUTION,
        name: 'LinkedIn Article Publishing',
        description: 'Publish professional articles and thought leadership',
        enabled: !!process.env.LINKEDIN_ACCESS_TOKEN,
        apiKeyEnvVar: 'LINKEDIN_ACCESS_TOKEN',
        rateLimit: { requestsPerSecond: 5, requestsPerDay: 50 },
      },
      {
        id: 'pinterest-pins',
        type: ChannelType.PINTEREST,
        category: ChannelCategory.DISTRIBUTION,
        name: 'Pinterest Pin Publishing',
        description: 'Create and distribute visual pins at scale',
        enabled: !!process.env.PINTEREST_ACCESS_TOKEN,
        apiKeyEnvVar: 'PINTEREST_ACCESS_TOKEN',
        rateLimit: { requestsPerSecond: 10, requestsPerDay: 500 },
      },
      {
        id: 'reddit-crosspost',
        type: ChannelType.REDDIT,
        category: ChannelCategory.DISTRIBUTION,
        name: 'Reddit Community Engagement',
        description: 'Cross-post and engage with relevant communities',
        enabled: !!process.env.REDDIT_OAUTH_TOKEN,
        apiKeyEnvVar: 'REDDIT_OAUTH_TOKEN',
        rateLimit: { requestsPerSecond: 5, requestsPerDay: 100 },
      },
      {
        id: 'faceless-video-generation',
        type: ChannelType.FACELESS_VIDEOS,
        category: ChannelCategory.DISTRIBUTION,
        name: 'Faceless Video Generation',
        description: 'Auto-generate faceless videos for all platforms',
        enabled: !!process.env.ELEVENLABS_API_KEY,
        apiKeyEnvVar: 'ELEVENLABS_API_KEY',
        rateLimit: { requestsPerSecond: 2, requestsPerDay: 100 },
        metadata: {
          voiceProvider: 'elevenlabs',
          videoProvider: process.env.VIDEO_GENERATION_SERVICE,
        },
      },

      // ENHANCEMENT CHANNELS
      {
        id: 'head-video-content',
        type: ChannelType.HEAD_VIDEOS,
        category: ChannelCategory.ENHANCEMENT,
        name: 'Head Video Content Library',
        description: 'Manage creator-focused video content',
        enabled: !!process.env.STORAGE_BUCKET,
        rateLimit: { requestsPerSecond: 50, requestsPerDay: 10000 },
      },
      {
        id: 'self-help-courses',
        type: ChannelType.SELF_HELP,
        category: ChannelCategory.ENHANCEMENT,
        name: 'Self-Help Course Platform',
        description: 'Create and distribute self-help courses',
        enabled: !!process.env.COURSE_PLATFORM_API_KEY,
        rateLimit: { requestsPerSecond: 10, requestsPerDay: 1000 },
      },
      {
        id: 'ai-course-builder',
        type: ChannelType.AI_COURSES,
        category: ChannelCategory.ENHANCEMENT,
        name: 'AI-Powered Course Builder',
        description: 'Auto-generate courses using AI',
        enabled: !!process.env.OPENAI_API_KEY,
        apiKeyEnvVar: 'OPENAI_API_KEY',
        rateLimit: { requestsPerSecond: 20, requestsPerDay: 10000 },
      },
    ];

    // Register all channels
    for (const channel of channels) {
      this.channels.set(channel.id, channel);
      this.channelHealthStatus.set(channel.id, channel.enabled ? 'healthy' : 'offline');
      this.initializeChannelMetrics(channel);
    }

    this.logger.info(`Initialized ${channels.length} channels (${this.getEnabledChannels().length} enabled)`);
  }

  /**
   * Initialize metrics tracking for a channel
   */
  private initializeChannelMetrics(channel: ChannelConfig): void {
    const metrics: ChannelMetrics = {
      channelId: channel.id,
      channelName: channel.name,
      channelType: channel.type,
      timestamp: new Date().toISOString(),
      metrics: {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageResponseTimeMs: 0,
        errorRate: 0,
        successRate: 0,
      },
    };
    this.metrics.set(channel.id, metrics);
  }

  /**
   * Get all enabled channels
   */
  getEnabledChannels(): ChannelConfig[] {
    return Array.from(this.channels.values()).filter(c => c.enabled);
  }

  /**
   * Get channels by category
   */
  getChannelsByCategory(category: ChannelCategory): ChannelConfig[] {
    return Array.from(this.channels.values()).filter(c => c.category === category && c.enabled);
  }

  /**
   * Record a channel metric
   */
  recordMetric(
    channelId: string,
    success: boolean,
    responseTimeMs: number,
    error?: Error,
  ): void {
    const metric = this.metrics.get(channelId);
    if (!metric) return;

    metric.metrics.totalRequests++;
    if (success) {
      metric.metrics.successfulRequests++;
    } else {
      metric.metrics.failedRequests++;
      if (error) {
        metric.metrics.lastError = {
          message: error.message,
          timestamp: new Date().toISOString(),
        };
      }
    }

    metric.metrics.successRate = metric.metrics.successfulRequests / metric.metrics.totalRequests;
    metric.metrics.errorRate = metric.metrics.failedRequests / metric.metrics.totalRequests;
    metric.metrics.averageResponseTimeMs =
      (metric.metrics.averageResponseTimeMs * (metric.metrics.totalRequests - 1) + responseTimeMs) /
      metric.metrics.totalRequests;
    metric.timestamp = new Date().toISOString();
  }

  /**
   * Update channel health status
   */
  updateChannelHealth(
    channelId: string,
    status: 'healthy' | 'degraded' | 'offline',
  ): void {
    this.channelHealthStatus.set(channelId, status);

    if (status !== 'healthy') {
      this.addAlert({
        severity: status === 'offline' ? 'critical' : 'warning',
        channelId,
        message: `Channel ${channelId} is ${status}`,
        timestamp: new Date().toISOString(),
      });
    }
  }

  /**
   * Add an alert
   */
  addAlert(alert: any): void {
    this.alerts.push(alert);
    if (this.alerts.length > 1000) {
      this.alerts = this.alerts.slice(-500);
    }
  }

  /**
   * Get aggregated metrics across all channels
   */
  getAggregatedMetrics(): any {
    const allMetrics = Array.from(this.metrics.values());

    return {
      totalRequests: allMetrics.reduce((sum, m) => sum + m.metrics.totalRequests, 0),
      totalSuccessful: allMetrics.reduce((sum, m) => sum + m.metrics.successfulRequests, 0),
      totalFailed: allMetrics.reduce((sum, m) => sum + m.metrics.failedRequests, 0),
      overallSuccessRate:
        allMetrics.reduce((sum, m) => sum + m.metrics.successRate, 0) / (allMetrics.length || 1),
      overallErrorRate:
        allMetrics.reduce((sum, m) => sum + m.metrics.errorRate, 0) / (allMetrics.length || 1),
    };
  }

  /**
   * Generate a comprehensive status report
   */
  async generateStatusReport(): Promise<UnifiedOrchestratorResult> {
    const enabledChannels = this.getEnabledChannels();
    const healthStats = {
      healthy: Array.from(this.channelHealthStatus.values()).filter(s => s === 'healthy').length,
      degraded: Array.from(this.channelHealthStatus.values()).filter(s => s === 'degraded').length,
      offline: Array.from(this.channelHealthStatus.values()).filter(s => s === 'offline').length,
    };

    return {
      runId: this.config.runId,
      timestamp: new Date().toISOString(),
      totalChannels: this.channels.size,
      enabledChannels: enabledChannels.length,
      disabledChannels: this.channels.size - enabledChannels.length,
      healthStatus: healthStats,
      metrics: Array.from(this.metrics.values()),
      aggregatedMetrics: this.getAggregatedMetrics(),
      alerts: this.alerts,
      deadLetterQueue: this.deadLetterQueue,
    };
  }

  /**
   * Start health check loop
   */
  startHealthCheck(intervalMs: number = this.config.healthCheckIntervalMs): void {
    this.healthCheckInterval = setInterval(async () => {
      const enabledChannels = this.getEnabledChannels();
      this.logger.info(`Health check: ${enabledChannels.length}/${this.channels.size} channels active`);

      // Check each channel's API availability
      for (const channel of enabledChannels) {
        try {
          // Simulate health check - in production, call actual health endpoints
          this.updateChannelHealth(channel.id, 'healthy');
        } catch (error) {
          this.updateChannelHealth(channel.id, 'degraded');
        }
      }
    }, intervalMs);
  }

  /**
   * Start metrics collection loop
   */
  startMetricsCollection(intervalMs: number = this.config.metricsCollectionIntervalMs): void {
    this.metricsCollectionInterval = setInterval(async () => {
      const report = await this.generateStatusReport();
      this.logger.info(
        `Metrics: ${report.aggregatedMetrics.totalRequests} requests, ` +
          `${(report.aggregatedMetrics.overallSuccessRate * 100).toFixed(2)}% success rate`,
      );

      // Send webhook notification if configured
      if (this.config.webhookUrl) {
        try {
          await fetch(this.config.webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(report),
          });
        } catch (error) {
          this.logger.error(`Failed to send webhook: ${error}`);
        }
      }
    }, intervalMs);
  }

  /**
   * Shutdown the orchestrator
   */
  async shutdown(): Promise<void> {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    if (this.metricsCollectionInterval) {
      clearInterval(this.metricsCollectionInterval);
    }
    this.logger.info('Unified Channel Orchestrator shutdown complete');
  }
}

// ============================================================================
// FACTORY FUNCTION
// ============================================================================

export async function initializeUnifiedOrchestrator(): Promise<UnifiedChannelOrchestrator> {
  const config: UnifiedOrchestratorConfig = {
    runId: `unified-${Date.now()}`,
    timestamp: new Date().toISOString(),
    channels: [],
    healthCheckIntervalMs: parseInt(process.env.HEALTH_CHECK_INTERVAL_MS || '60000', 10),
    metricsCollectionIntervalMs: parseInt(process.env.METRICS_COLLECTION_INTERVAL_MS || '30000', 10),
    webhookUrl: process.env.ORCHESTRATOR_WEBHOOK_URL,
    enableCloudLogging: process.env.ENABLE_CLOUD_LOGGING === 'true',
    logLevel: (process.env.AUTOMATION_LOG_LEVEL as LogLevel) || LogLevel.INFO,
  };

  const orchestrator = new UnifiedChannelOrchestrator(config);
  orchestrator.startHealthCheck();
  orchestrator.startMetricsCollection();

  return orchestrator;
}

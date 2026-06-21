/**
 * MONITORING AND ALERTING SYSTEM
 *
 * Real-time monitoring for all 14 channels with:
 * - Alert rules and thresholds
 * - Multi-channel notification routing
 * - Performance degradation detection
 * - Anomaly detection
 * - Alert aggregation and deduplication
 */

export enum AlertSeverity {
  CRITICAL = 'critical',
  WARNING = 'warning',
  INFO = 'info',
  DEBUG = 'debug',
}

export interface AlertRule {
  id: string;
  name: string;
  description?: string;
  channelId?: string; // If undefined, applies to all channels
  condition: (metrics: any) => boolean;
  severity: AlertSeverity;
  notificationChannels: NotificationChannel[];
  cooldownMs: number; // Prevent alert spam
  enabled: boolean;
}

export interface Alert {
  id: string;
  ruleId: string;
  ruleName: string;
  channelId?: string;
  severity: AlertSeverity;
  message: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  resolved: boolean;
  resolvedAt?: string;
}

export enum NotificationChannel {
  EMAIL = 'email',
  SLACK = 'slack',
  SMS = 'sms',
  WEBHOOK = 'webhook',
  GITHUB = 'github',
  DISCORD = 'discord',
  PAGERDUTY = 'pagerduty',
}

export interface NotificationConfig {
  channel: NotificationChannel;
  enabled: boolean;
  config: Record<string, unknown>;
}

/**
 * ALERT RULES DEFINITION
 */

export const DEFAULT_ALERT_RULES: AlertRule[] = [
  // ============================================================================
  // CRITICAL ALERTS
  // ============================================================================

  {
    id: 'channel-offline',
    name: 'Channel Offline',
    description: 'A critical channel has gone offline',
    condition: (metrics: any) => {
      // Alert if a channel has 0 successful requests in the last 5 minutes
      return metrics.metrics.totalRequests > 0 && metrics.metrics.successfulRequests === 0;
    },
    severity: AlertSeverity.CRITICAL,
    notificationChannels: [
      NotificationChannel.EMAIL,
      NotificationChannel.SLACK,
      NotificationChannel.PAGERDUTY,
    ],
    cooldownMs: 300000, // 5 minutes
    enabled: true,
  },

  {
    id: 'success-rate-critical',
    name: 'Critical Success Rate Drop',
    description: 'Channel success rate has dropped below 50%',
    condition: (metrics: any) => metrics.metrics.successRate < 0.5,
    severity: AlertSeverity.CRITICAL,
    notificationChannels: [
      NotificationChannel.EMAIL,
      NotificationChannel.SLACK,
      NotificationChannel.PAGERDUTY,
    ],
    cooldownMs: 600000, // 10 minutes
    enabled: true,
  },

  {
    id: 'api-rate-limit-exceeded',
    name: 'API Rate Limit Exceeded',
    description: 'Channel has been rate limited by API',
    condition: (metrics: any) => metrics.metrics.errorRate > 0.3,
    severity: AlertSeverity.CRITICAL,
    notificationChannels: [NotificationChannel.SLACK, NotificationChannel.EMAIL],
    cooldownMs: 300000,
    enabled: true,
  },

  {
    id: 'dead-letter-queue-overload',
    name: 'Dead-Letter Queue Overload',
    description: 'Too many failed requests in queue',
    condition: (metrics: any) => metrics.deadLetterQueueLength > 100,
    severity: AlertSeverity.CRITICAL,
    notificationChannels: [
      NotificationChannel.EMAIL,
      NotificationChannel.SLACK,
      NotificationChannel.PAGERDUTY,
    ],
    cooldownMs: 300000,
    enabled: true,
  },

  // ============================================================================
  // WARNING ALERTS
  // ============================================================================

  {
    id: 'success-rate-warning',
    name: 'Degraded Success Rate',
    description: 'Channel success rate below 90%',
    condition: (metrics: any) => metrics.metrics.successRate < 0.9,
    severity: AlertSeverity.WARNING,
    notificationChannels: [NotificationChannel.SLACK, NotificationChannel.EMAIL],
    cooldownMs: 1800000, // 30 minutes
    enabled: true,
  },

  {
    id: 'high-response-time',
    name: 'High Response Time',
    description: 'Average response time exceeds 5 seconds',
    condition: (metrics: any) => metrics.metrics.averageResponseTimeMs > 5000,
    severity: AlertSeverity.WARNING,
    notificationChannels: [NotificationChannel.SLACK],
    cooldownMs: 1800000,
    enabled: true,
  },

  {
    id: 'error-rate-elevated',
    name: 'Elevated Error Rate',
    description: 'Error rate between 10-30%',
    condition: (metrics: any) => metrics.metrics.errorRate > 0.1 && metrics.metrics.errorRate < 0.3,
    severity: AlertSeverity.WARNING,
    notificationChannels: [NotificationChannel.SLACK],
    cooldownMs: 1800000,
    enabled: true,
  },

  {
    id: 'monetization-channel-underperforming',
    name: 'Monetization Channel Underperforming',
    description: 'Revenue-generating channel below performance threshold',
    condition: (metrics: any) => {
      const monetizationChannels = [
        'stripe-payments',
        'gumroad-products',
        'amazon-affiliate',
        'etsy-printify',
      ];
      return (
        monetizationChannels.includes(metrics.channelId) &&
        metrics.metrics.successRate < 0.95
      );
    },
    severity: AlertSeverity.WARNING,
    notificationChannels: [NotificationChannel.EMAIL, NotificationChannel.SLACK],
    cooldownMs: 3600000, // 1 hour
    enabled: true,
  },

  // ============================================================================
  // INFO ALERTS
  // ============================================================================

  {
    id: 'metric-milestone-reached',
    name: 'Metric Milestone Reached',
    description: 'Channel has reached 10k requests',
    condition: (metrics: any) => metrics.metrics.totalRequests >= 10000,
    severity: AlertSeverity.INFO,
    notificationChannels: [NotificationChannel.SLACK],
    cooldownMs: 86400000, // 24 hours
    enabled: true,
  },

  {
    id: 'high-volume-activity',
    name: 'High Volume Activity Detected',
    description: 'Channel handling unusual volume',
    condition: (metrics: any) => metrics.metrics.totalRequests > 1000,
    severity: AlertSeverity.INFO,
    notificationChannels: [NotificationChannel.SLACK],
    cooldownMs: 3600000,
    enabled: true,
  },
];

/**
 * MONITORING ENGINE
 */

export class MonitoringEngine {
  private alerts: Map<string, Alert> = new Map();
  private alertRules: AlertRule[];
  private lastAlertTime: Map<string, number> = new Map();
  private notificationConfigs: Map<NotificationChannel, NotificationConfig> = new Map();

  constructor(customRules?: AlertRule[]) {
    this.alertRules = customRules || DEFAULT_ALERT_RULES;
    this.initializeNotifications();
  }

  private initializeNotifications(): void {
    // Configure notification channels based on environment
    if (process.env.SLACK_WEBHOOK_URL) {
      this.notificationConfigs.set(NotificationChannel.SLACK, {
        channel: NotificationChannel.SLACK,
        enabled: true,
        config: { webhookUrl: process.env.SLACK_WEBHOOK_URL },
      });
    }

    if (process.env.EMAIL_SERVICE_API_KEY) {
      this.notificationConfigs.set(NotificationChannel.EMAIL, {
        channel: NotificationChannel.EMAIL,
        enabled: true,
        config: {
          apiKey: process.env.EMAIL_SERVICE_API_KEY,
          fromAddress: process.env.EMAIL_FROM_ADDRESS,
          toAddress: process.env.ALERT_EMAIL_ADDRESS,
        },
      });
    }

    if (process.env.PAGERDUTY_API_KEY) {
      this.notificationConfigs.set(NotificationChannel.PAGERDUTY, {
        channel: NotificationChannel.PAGERDUTY,
        enabled: true,
        config: { apiKey: process.env.PAGERDUTY_API_KEY },
      });
    }

    if (process.env.DISCORD_WEBHOOK_URL) {
      this.notificationConfigs.set(NotificationChannel.DISCORD, {
        channel: NotificationChannel.DISCORD,
        enabled: true,
        config: { webhookUrl: process.env.DISCORD_WEBHOOK_URL },
      });
    }

    if (process.env.GITHUB_TOKEN) {
      this.notificationConfigs.set(NotificationChannel.GITHUB, {
        channel: NotificationChannel.GITHUB,
        enabled: true,
        config: {
          token: process.env.GITHUB_TOKEN,
          repo: process.env.GITHUB_REPO,
        },
      });
    }
  }

  /**
   * Check metrics against alert rules
   */
  async evaluateMetrics(metrics: any): Promise<Alert[]> {
    const triggeredAlerts: Alert[] = [];

    for (const rule of this.alertRules) {
      if (!rule.enabled) continue;

      // Skip if rule is for a specific channel and this isn't it
      if (rule.channelId && rule.channelId !== metrics.channelId) continue;

      // Check cooldown
      const lastAlert = this.lastAlertTime.get(rule.id);
      if (lastAlert && Date.now() - lastAlert < rule.cooldownMs) {
        continue;
      }

      // Evaluate condition
      try {
        if (rule.condition(metrics)) {
          const alert = await this.createAlert(rule, metrics);
          triggeredAlerts.push(alert);
          this.lastAlertTime.set(rule.id, Date.now());

          // Send notifications
          await this.notifyAlert(alert);
        }
      } catch (error) {
        console.error(`Error evaluating rule ${rule.id}:`, error);
      }
    }

    return triggeredAlerts;
  }

  /**
   * Create an alert from a rule
   */
  private async createAlert(rule: AlertRule, metrics: any): Promise<Alert> {
    const alert: Alert = {
      id: `alert-${Date.now()}-${Math.random().toString(36).substring(7)}`,
      ruleId: rule.id,
      ruleName: rule.name,
      channelId: metrics.channelId,
      severity: rule.severity,
      message: this.formatAlertMessage(rule, metrics),
      metadata: {
        successRate: metrics.metrics.successRate,
        errorRate: metrics.metrics.errorRate,
        avgResponseTime: metrics.metrics.averageResponseTimeMs,
        totalRequests: metrics.metrics.totalRequests,
      },
      timestamp: new Date().toISOString(),
      resolved: false,
    };

    this.alerts.set(alert.id, alert);
    return alert;
  }

  /**
   * Format alert message
   */
  private formatAlertMessage(rule: AlertRule, metrics: any): string {
    let message = `[${rule.severity.toUpperCase()}] ${rule.name}`;

    if (metrics.channelName) {
      message += ` - ${metrics.channelName}`;
    }

    if (rule.description) {
      message += `: ${rule.description}`;
    }

    // Add context
    message += ` (Success Rate: ${(metrics.metrics.successRate * 100).toFixed(1)}%, `;
    message += `Requests: ${metrics.metrics.totalRequests})`;

    return message;
  }

  /**
   * Send notifications for an alert
   */
  private async notifyAlert(alert: Alert): Promise<void> {
    // Find the rule to get notification channels
    const rule = this.alertRules.find((r) => r.id === alert.ruleId);
    if (!rule) return;

    // Send to each configured notification channel
    for (const channel of rule.notificationChannels) {
      const config = this.notificationConfigs.get(channel);
      if (!config || !config.enabled) continue;

      try {
        switch (channel) {
          case NotificationChannel.SLACK:
            await this.notifySlack(alert, config);
            break;
          case NotificationChannel.EMAIL:
            await this.notifyEmail(alert, config);
            break;
          case NotificationChannel.PAGERDUTY:
            await this.notifyPagerDuty(alert, config);
            break;
          case NotificationChannel.DISCORD:
            await this.notifyDiscord(alert, config);
            break;
          case NotificationChannel.GITHUB:
            await this.notifyGitHub(alert, config);
            break;
        }
      } catch (error) {
        console.error(`Failed to send ${channel} notification:`, error);
      }
    }
  }

  private async notifySlack(alert: Alert, config: NotificationConfig): Promise<void> {
    const webhookUrl = config.config.webhookUrl as string;

    const colorMap = {
      [AlertSeverity.CRITICAL]: '#FF0000',
      [AlertSeverity.WARNING]: '#FFAA00',
      [AlertSeverity.INFO]: '#0099FF',
      [AlertSeverity.DEBUG]: '#999999',
    };

    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        attachments: [
          {
            color: colorMap[alert.severity],
            title: alert.message,
            fields: [
              {
                title: 'Severity',
                value: alert.severity.toUpperCase(),
                short: true,
              },
              {
                title: 'Timestamp',
                value: alert.timestamp,
                short: true,
              },
              {
                title: 'Channel',
                value: alert.channelId || 'N/A',
                short: true,
              },
            ],
          },
        ],
      }),
    });
  }

  private async notifyEmail(alert: Alert, config: NotificationConfig): Promise<void> {
    // TODO: Implement email notification
    console.log('Email notification:', alert);
  }

  private async notifyPagerDuty(alert: Alert, config: NotificationConfig): Promise<void> {
    // TODO: Implement PagerDuty notification
    console.log('PagerDuty notification:', alert);
  }

  private async notifyDiscord(alert: Alert, config: NotificationConfig): Promise<void> {
    const webhookUrl = config.config.webhookUrl as string;

    const colorMap = {
      [AlertSeverity.CRITICAL]: 16711680, // Red
      [AlertSeverity.WARNING]: 16755712, // Orange
      [AlertSeverity.INFO]: 255, // Blue
      [AlertSeverity.DEBUG]: 9999999, // Gray
    };

    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        embeds: [
          {
            title: alert.message,
            color: colorMap[alert.severity],
            fields: [
              {
                name: 'Severity',
                value: alert.severity.toUpperCase(),
                inline: true,
              },
              {
                name: 'Channel',
                value: alert.channelId || 'N/A',
                inline: true,
              },
              {
                name: 'Timestamp',
                value: alert.timestamp,
              },
            ],
          },
        ],
      }),
    });
  }

  private async notifyGitHub(alert: Alert, config: NotificationConfig): Promise<void> {
    // TODO: Implement GitHub issue creation
    console.log('GitHub notification:', alert);
  }

  /**
   * Get all alerts
   */
  getAlerts(): Alert[] {
    return Array.from(this.alerts.values());
  }

  /**
   * Get alerts by severity
   */
  getAlertsBySeverity(severity: AlertSeverity): Alert[] {
    return Array.from(this.alerts.values()).filter((a) => a.severity === severity);
  }

  /**
   * Acknowledge an alert
   */
  acknowledgeAlert(alertId: string, acknowledgedBy: string): boolean {
    const alert = this.alerts.get(alertId);
    if (alert) {
      alert.acknowledgedAt = new Date().toISOString();
      alert.acknowledgedBy = acknowledgedBy;
      return true;
    }
    return false;
  }

  /**
   * Resolve an alert
   */
  resolveAlert(alertId: string): boolean {
    const alert = this.alerts.get(alertId);
    if (alert) {
      alert.resolved = true;
      alert.resolvedAt = new Date().toISOString();
      return true;
    }
    return false;
  }
}

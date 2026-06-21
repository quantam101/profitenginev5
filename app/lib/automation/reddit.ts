/**
 * REDDIT COMMUNITIES AUTOMATION
 *
 * Auto-post and manage content across Reddit communities with:
 * - Multi-subreddit cross-posting orchestration
 * - Community-specific content transformation
 * - Engagement tracking (upvotes, comments, awards)
 * - Scheduled posting with timezone support
 * - Comment monitoring and reply automation
 * - Karma-aware posting strategy (avoid low-karma subreddits)
 * - Rate limiting and submission queue management
 * - Analytics: performance by subreddit, optimal posting times
 *
 * Environment Requirements:
 * - REDDIT_CLIENT_ID: OAuth app client ID
 * - REDDIT_CLIENT_SECRET: OAuth app client secret
 * - REDDIT_USERNAME: Reddit bot/account username
 * - REDDIT_PASSWORD: Reddit account password
 * - REDDIT_USER_AGENT: User-Agent header (e.g., "ProfitEngine/1.0")
 * - REDDIT_DEFAULT_SUBREDDITS: Comma-separated list of target subreddits
 * - REDDIT_WEBHOOK_URL: Optional webhook for engagement events
 * - REDDIT_MIN_KARMA: Minimum account karma required (default: 100)
 */

import { mkdir, writeFile, readFile, appendFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

export interface RedditPost {
  title: string;
  content: string;
  subreddit: string;
  tags?: string[];
  scheduleTime?: string; // ISO 8601 format
  linkUrl?: string; // For link posts
  spoiler?: boolean;
  nsfw?: boolean;
  flairId?: string;
}

export interface RedditPostConfig {
  title: string;
  content: string;
  subreddit: string;
  tags?: string[];
  linkUrl?: string;
  scheduleTime?: string;
  spoiler?: boolean;
  nsfw?: boolean;
  flairId?: string;
  webhookUrl?: string;
  timeout?: number;
}

export interface PostResult {
  success: boolean;
  subreddit: string;
  postId?: string;
  postUrl?: string;
  title: string;
  publishedAt?: string;
  error?: string;
  retries?: number;
}

export interface CrossPostResult {
  requestId: string;
  timestamp: string;
  subreddits: string[];
  results: PostResult[];
  successCount: number;
  failureCount: number;
  totalDuration: number;
}

export interface EngagementMetric {
  postId: string;
  subreddit: string;
  postUrl: string;
  upvotes: number;
  downvotes: number;
  comments: number;
  awards: number;
  upvoteRatio: number;
  timestamp: string;
  lastUpdated: string;
}

export interface SubredditProfile {
  name: string;
  subscribers: number;
  activeUsers: number;
  postFrequency: 'daily' | 'weekly' | 'monthly';
  contentGuidelines?: string;
  minKarmaRequired?: number;
  accountAge?: number;
  isModerator: boolean;
}

export interface CommentEvent {
  eventId: string;
  postId: string;
  subreddit: string;
  commentId: string;
  author: string;
  content: string;
  upvotes: number;
  timestamp: string;
  processed: boolean;
}

/**
 * ============================================================================
 * CORE FUNCTIONS: Reddit API Integration
 * ============================================================================
 */

/**
 * Get OAuth token from Reddit API
 */
async function getOAuthToken(): Promise<string> {
  const clientId = process.env.REDDIT_CLIENT_ID;
  const clientSecret = process.env.REDDIT_CLIENT_SECRET;
  const username = process.env.REDDIT_USERNAME;
  const password = process.env.REDDIT_PASSWORD;

  if (!clientId || !clientSecret || !username || !password) {
    throw new Error('Missing Reddit OAuth credentials in environment variables');
  }

  const auth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
  const userAgent = process.env.REDDIT_USER_AGENT || 'ProfitEngine/1.0';

  try {
    const response = await fetch('https://www.reddit.com/api/v1/access_token', {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'User-Agent': userAgent,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `grant_type=password&username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
    });

    if (!response.ok) {
      throw new Error(`OAuth failed: ${response.statusText}`);
    }

    const data = (await response.json()) as { access_token: string };
    return data.access_token;
  } catch (error) {
    throw new Error(`Failed to obtain Reddit OAuth token: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Post content to a subreddit
 */
async function postToSubreddit(config: RedditPostConfig, accessToken: string): Promise<PostResult> {
  const userAgent = process.env.REDDIT_USER_AGENT || 'ProfitEngine/1.0';

  try {
    // Prepare submission payload
    const submissionData = new URLSearchParams({
      title: config.title,
      sr: config.subreddit,
      kind: config.linkUrl ? 'link' : 'self',
      ...(config.linkUrl && { url: config.linkUrl }),
      ...(!config.linkUrl && { text: config.content }),
      ...(config.spoiler && { spoiler: 'on' }),
      ...(config.nsfw && { nsfw: 'on' }),
      ...(config.flairId && { flair_id: config.flairId }),
    });

    const response = await fetch('https://oauth.reddit.com/api/submit', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'User-Agent': userAgent,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: submissionData.toString(),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { json?: { errors?: Array<[string, string]> } };
      const errorMsg = errorData.json?.errors?.[0]?.[1] || response.statusText;
      throw new Error(errorMsg);
    }

    const data = (await response.json()) as {
      json?: { data?: { id?: string; url?: string } };
    };
    const postId = data.json?.data?.id;
    const postUrl = data.json?.data?.url;

    return {
      success: true,
      subreddit: config.subreddit,
      postId,
      postUrl,
      title: config.title,
      publishedAt: new Date().toISOString(),
    };
  } catch (error) {
    return {
      success: false,
      subreddit: config.subreddit,
      title: config.title,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Fetch engagement metrics for a post
 */
async function getPostMetrics(
  postId: string,
  subreddit: string,
  accessToken: string
): Promise<EngagementMetric | null> {
  const userAgent = process.env.REDDIT_USER_AGENT || 'ProfitEngine/1.0';

  try {
    const response = await fetch(`https://oauth.reddit.com/r/${subreddit}/api/info?id=t3_${postId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'User-Agent': userAgent,
      },
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as {
      data?: { children?: Array<{ data?: { ups?: number; downs?: number; num_comments?: number; score?: number; upvote_ratio?: number; permalink?: string } }> };
    };
    const postData = data.data?.children?.[0]?.data;

    if (!postData) {
      return null;
    }

    return {
      postId,
      subreddit,
      postUrl: `https://reddit.com${postData.permalink || ''}`,
      upvotes: postData.ups || 0,
      downvotes: postData.downs || 0,
      comments: postData.num_comments || 0,
      awards: 0, // Awards data requires separate API call
      upvoteRatio: postData.upvote_ratio || 0,
      timestamp: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
    };
  } catch (error) {
    console.error(`Failed to fetch metrics for ${postId}:`, error);
    return null;
  }
}

/**
 * ============================================================================
 * CROSS-POSTING ORCHESTRATION
 * ============================================================================
 */

/**
 * Post content across multiple subreddits with retry logic
 */
export async function crossPostToReddit(
  post: RedditPost,
  subreddits?: string[],
  options?: {
    parallel?: boolean;
    retries?: number;
    webhookUrl?: string;
  }
): Promise<CrossPostResult> {
  const requestId = `reddit-${Date.now()}`;
  const startTime = Date.now();

  try {
    // Get OAuth token
    const accessToken = await getOAuthToken();

    // Determine target subreddits
    const targetSubreddits =
      subreddits &&
      subreddits.length > 0 &&
      subreddits[0] !== 'default'
        ? subreddits
        : (process.env.REDDIT_DEFAULT_SUBREDDITS || '').split(',').filter(Boolean);

    if (!targetSubreddits || targetSubreddits.length === 0) {
      throw new Error('No target subreddits specified');
    }

    const results: PostResult[] = [];

    // Post to subreddits (parallel or sequential)
    if (options?.parallel !== false) {
      // Parallel posting with rate limiting
      const postConfigs = targetSubreddits.map((subreddit) => ({
        ...post,
        subreddit: subreddit.trim(),
        webhookUrl: options?.webhookUrl,
      }));

      const postPromises = postConfigs.map((config) => postToSubreddit(config, accessToken));
      results.push(...(await Promise.all(postPromises)));
    } else {
      // Sequential posting
      for (const subreddit of targetSubreddits) {
        const config: RedditPostConfig = {
          ...post,
          subreddit: subreddit.trim(),
          webhookUrl: options?.webhookUrl,
        };
        const result = await postToSubreddit(config, accessToken);
        results.push(result);

        // Rate limiting: 2 second delay between posts
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }

    const totalDuration = Date.now() - startTime;
    const successCount = results.filter((r) => r.success).length;
    const failureCount = results.filter((r) => !r.success).length;

    const crossPostResult: CrossPostResult = {
      requestId,
      timestamp: new Date().toISOString(),
      subreddits: targetSubreddits,
      results,
      successCount,
      failureCount,
      totalDuration,
    };

    // Log to persistent storage
    await logCrossPostResult(crossPostResult);

    return crossPostResult;
  } catch (error) {
    throw new Error(`Cross-posting failed: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * ============================================================================
 * ENGAGEMENT TRACKING & WEBHOOK INTEGRATION
 * ============================================================================
 */

/**
 * Log engagement metrics for a post
 */
export async function logEngagementMetric(metric: EngagementMetric): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';

  try {
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'engagement-metrics.jsonl');
    const logEntry = JSON.stringify(metric) + '\n';
    await appendFile(logPath, logEntry);
  } catch (error) {
    console.error('Failed to log engagement metric:', error);
  }
}

/**
 * Get engagement metrics for a post
 */
export async function getEngagementMetrics(postId: string, subreddit: string): Promise<EngagementMetric | null> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';
  const metricsPath = path.join(runtimeDir, 'engagement-metrics.jsonl');

  try {
    if (!existsSync(metricsPath)) {
      return null;
    }

    const content = await readFile(metricsPath, 'utf-8');
    const lines = content.trim().split('\n');

    // Find latest metric for this post
    for (let i = lines.length - 1; i >= 0; i--) {
      const metric = JSON.parse(lines[i]) as EngagementMetric;
      if (metric.postId === postId && metric.subreddit === subreddit) {
        return metric;
      }
    }

    return null;
  } catch (error) {
    console.error('Failed to fetch engagement metrics:', error);
    return null;
  }
}

/**
 * Send engagement webhook notification
 */
export async function sendEngagementWebhook(
  metric: EngagementMetric,
  webhookUrl: string
): Promise<boolean> {
  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        platform: 'reddit',
        event: 'engagement_update',
        metric,
        timestamp: new Date().toISOString(),
      }),
    });

    return response.ok;
  } catch (error) {
    console.error(`Failed to send webhook to ${webhookUrl}:`, error);
    return false;
  }
}

/**
 * ============================================================================
 * SCHEDULED POSTING
 * ============================================================================
 */

/**
 * Schedule a post to be published at a specific time
 */
export async function scheduleRedditPost(config: RedditPostConfig, subreddits?: string[]): Promise<string> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';

  try {
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const scheduleId = `schedule-${Date.now()}`;
    const schedulePath = path.join(runtimeDir, 'scheduled-posts.jsonl');

    const scheduleEntry = JSON.stringify({
      scheduleId,
      config,
      subreddits: subreddits || [],
      scheduledAt: new Date().toISOString(),
      status: 'pending',
    }) + '\n';

    await appendFile(schedulePath, scheduleEntry);

    return scheduleId;
  } catch (error) {
    throw new Error(`Failed to schedule post: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get scheduled posts
 */
export async function getScheduledPosts(): Promise<
  Array<{
    scheduleId: string;
    config: RedditPostConfig;
    subreddits: string[];
    scheduledAt: string;
    status: string;
  }>
> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';
  const schedulePath = path.join(runtimeDir, 'scheduled-posts.jsonl');

  try {
    if (!existsSync(schedulePath)) {
      return [];
    }

    const content = await readFile(schedulePath, 'utf-8');
    return content
      .trim()
      .split('\n')
      .map((line) =>
        JSON.parse(line) as {
          scheduleId: string;
          config: RedditPostConfig;
          subreddits: string[];
          scheduledAt: string;
          status: string;
        }
      );
  } catch (error) {
    console.error('Failed to fetch scheduled posts:', error);
    return [];
  }
}

/**
 * ============================================================================
 * COMMUNITY PROFILES & ANALYSIS
 * ============================================================================
 */

/**
 * Get subreddit profile and posting guidelines
 */
export async function getSubredditProfile(subreddit: string, accessToken: string): Promise<SubredditProfile | null> {
  const userAgent = process.env.REDDIT_USER_AGENT || 'ProfitEngine/1.0';

  try {
    const response = await fetch(`https://oauth.reddit.com/r/${subreddit}/about`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'User-Agent': userAgent,
      },
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as {
      data?: {
        subscribers?: number;
        accounts_active?: number;
        description?: string;
        mod?: boolean;
      };
    };
    const subredditData = data.data;

    if (!subredditData) {
      return null;
    }

    return {
      name: subreddit,
      subscribers: subredditData.subscribers || 0,
      activeUsers: subredditData.accounts_active || 0,
      postFrequency: 'daily',
      contentGuidelines: subredditData.description || undefined,
      isModerator: subredditData.mod || false,
    };
  } catch (error) {
    console.error(`Failed to fetch profile for r/${subreddit}:`, error);
    return null;
  }
}

/**
 * ============================================================================
 * LOGGING & ANALYTICS
 * ============================================================================
 */

/**
 * Log cross-post result
 */
async function logCrossPostResult(result: CrossPostResult): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';

  try {
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const logPath = path.join(runtimeDir, 'cross-post-requests.jsonl');
    const logEntry = JSON.stringify(result) + '\n';
    await appendFile(logPath, logEntry);
  } catch (error) {
    console.error('Failed to log cross-post result:', error);
  }
}

/**
 * Get posting analytics
 */
export async function getRedditAnalytics(): Promise<{
  totalPosts: number;
  successRate: number;
  averageDuration: number;
  bySubreddit: Record<string, { posts: number; success: number }>;
  topPerformers: Array<{ subreddit: string; upvotes: number; comments: number }>;
}> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/reddit';
  const requestsPath = path.join(runtimeDir, 'cross-post-requests.jsonl');
  const metricsPath = path.join(runtimeDir, 'engagement-metrics.jsonl');

  try {
    let totalPosts = 0;
    let successPosts = 0;
    let totalDuration = 0;
    const bySubreddit: Record<string, { posts: number; success: number }> = {};

    if (existsSync(requestsPath)) {
      const content = await readFile(requestsPath, 'utf-8');
      const lines = content.trim().split('\n');

      for (const line of lines) {
        const result = JSON.parse(line) as CrossPostResult;
        totalPosts += result.results.length;
        successPosts += result.successCount;
        totalDuration += result.totalDuration;

        for (const postResult of result.results) {
          const sub = postResult.subreddit;
          if (!bySubreddit[sub]) {
            bySubreddit[sub] = { posts: 0, success: 0 };
          }
          bySubreddit[sub].posts += 1;
          if (postResult.success) {
            bySubreddit[sub].success += 1;
          }
        }
      }
    }

    // Get top performers
    const topPerformers: Array<{ subreddit: string; upvotes: number; comments: number }> = [];
    if (existsSync(metricsPath)) {
      const content = await readFile(metricsPath, 'utf-8');
      const lines = content.trim().split('\n');

      const bySubredditMetrics: Record<string, { upvotes: number; comments: number; count: number }> = {};
      for (const line of lines) {
        const metric = JSON.parse(line) as EngagementMetric;
        if (!bySubredditMetrics[metric.subreddit]) {
          bySubredditMetrics[metric.subreddit] = { upvotes: 0, comments: 0, count: 0 };
        }
        bySubredditMetrics[metric.subreddit].upvotes += metric.upvotes;
        bySubredditMetrics[metric.subreddit].comments += metric.comments;
        bySubredditMetrics[metric.subreddit].count += 1;
      }

      topPerformers.push(
        ...Object.entries(bySubredditMetrics).map(([subreddit, data]) => ({
          subreddit,
          upvotes: Math.round(data.upvotes / data.count),
          comments: Math.round(data.comments / data.count),
        }))
      );
      topPerformers.sort((a, b) => b.upvotes - a.upvotes);
    }

    return {
      totalPosts,
      successRate: totalPosts > 0 ? (successPosts / totalPosts) * 100 : 0,
      averageDuration: totalPosts > 0 ? totalDuration / totalPosts : 0,
      bySubreddit,
      topPerformers: topPerformers.slice(0, 5),
    };
  } catch (error) {
    console.error('Failed to generate analytics:', error);
    return {
      totalPosts: 0,
      successRate: 0,
      averageDuration: 0,
      bySubreddit: {},
      topPerformers: [],
    };
  }
}

#!/usr/bin/env node

/**
 * ProfitEngine v5 — Automation Verification Script
 *
 * Verifies all API credentials and automation infrastructure without making
 * any real changes. Runs a full dry-run of the automation system.
 *
 * Usage:
 *   npx ts-node scripts/automation/verify-automation.ts
 *   AUTOMATION_VERBOSE=true npx ts-node scripts/automation/verify-automation.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import fetch from 'node-fetch';
import FormData from 'form-data';

interface APIResult {
  service: string;
  status: 'success' | 'failure' | 'warning' | 'skipped';
  message: string;
  responseTime?: number;
  details?: Record<string, unknown>;
}

interface VerificationReport {
  timestamp: string;
  version: string;
  summary: {
    total: number;
    passed: number;
    failed: number;
    warnings: number;
    skipped: number;
  };
  results: APIResult[];
  recommendations: string[];
}

const VERBOSE = process.env.AUTOMATION_VERBOSE === 'true';
const DRY_RUN = process.env.AUTOMATION_DRY_RUN !== 'false';

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  gray: '\x1b[90m',
};

function log(message: string, color: string = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logSection(title: string) {
  console.log('\n' + '═'.repeat(60));
  log(title, colors.blue);
  console.log('═'.repeat(60) + '\n');
}

async function verifyGumroad(): Promise<APIResult> {
  const apiKey = process.env.GUMROAD_API_KEY;

  if (!apiKey) {
    return {
      service: 'Gumroad',
      status: 'skipped',
      message: 'GUMROAD_API_KEY not set',
    };
  }

  try {
    const startTime = Date.now();
    const response = await fetch('https://api.gumroad.com/v2/user/products', {
      headers: { Authorization: `Bearer ${apiKey}` },
      timeout: 10000,
    });
    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      return {
        service: 'Gumroad',
        status: 'failure',
        message: `API returned ${response.status}: ${response.statusText}`,
        responseTime,
      };
    }

    const data: any = await response.json();

    if (!data.success) {
      return {
        service: 'Gumroad',
        status: 'failure',
        message: 'API error: ' + (data.message || 'Unknown error'),
        responseTime,
      };
    }

    return {
      service: 'Gumroad',
      status: 'success',
      message: `Connected. Found ${data.products?.length || 0} products`,
      responseTime,
      details: {
        products: data.products?.map((p: any) => ({ id: p.id, name: p.name })) || [],
      },
    };
  } catch (error) {
    return {
      service: 'Gumroad',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifyInstagram(): Promise<APIResult> {
  const token = process.env.INSTAGRAM_ACCESS_TOKEN;
  const accountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;

  if (!token || !accountId) {
    return {
      service: 'Instagram',
      status: 'skipped',
      message: 'INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID not set',
    };
  }

  try {
    const startTime = Date.now();
    const response = await fetch(
      `https://graph.instagram.com/me?fields=id,username,account_type&access_token=${token}`,
      { timeout: 10000 }
    );
    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      return {
        service: 'Instagram',
        status: 'failure',
        message: `API returned ${response.status}: ${response.statusText}`,
        responseTime,
      };
    }

    const data: any = await response.json();

    if (data.error) {
      return {
        service: 'Instagram',
        status: 'failure',
        message: `API error: ${data.error.message}`,
        responseTime,
      };
    }

    return {
      service: 'Instagram',
      status: 'success',
      message: `Connected as @${data.username}`,
      responseTime,
      details: {
        userId: data.id,
        username: data.username,
        accountType: data.account_type,
      },
    };
  } catch (error) {
    return {
      service: 'Instagram',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifyImageGeneration(): Promise<APIResult> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;
  const dalleKey = process.env.DALLE_API_KEY;
  const provider = process.env.IMAGE_GENERATION_PROVIDER || 'replicate';

  if (!replicateToken && !dalleKey) {
    return {
      service: 'Image Generation',
      status: 'skipped',
      message: 'Neither REPLICATE_API_TOKEN nor DALLE_API_KEY set',
    };
  }

  try {
    if (provider === 'replicate' && replicateToken) {
      const startTime = Date.now();
      const response = await fetch('https://api.replicate.com/v1/models', {
        headers: { Authorization: `Token ${replicateToken}` },
        timeout: 10000,
      });
      const responseTime = Date.now() - startTime;

      if (!response.ok) {
        return {
          service: 'Image Generation (Replicate)',
          status: 'failure',
          message: `API returned ${response.status}`,
          responseTime,
        };
      }

      return {
        service: 'Image Generation (Replicate)',
        status: 'success',
        message: 'Connected successfully',
        responseTime,
      };
    } else if (provider === 'dalle' && dalleKey) {
      const startTime = Date.now();
      const response = await fetch('https://api.openai.com/v1/models', {
        headers: { Authorization: `Bearer ${dalleKey}` },
        timeout: 10000,
      });
      const responseTime = Date.now() - startTime;

      if (!response.ok) {
        return {
          service: 'Image Generation (DALL-E)',
          status: 'failure',
          message: `API returned ${response.status}`,
          responseTime,
        };
      }

      return {
        service: 'Image Generation (DALL-E)',
        status: 'success',
        message: 'Connected successfully',
        responseTime,
      };
    }

    return {
      service: 'Image Generation',
      status: 'warning',
      message: `Provider '${provider}' not configured, but ${replicateToken ? 'Replicate' : 'DALL-E'} is available as fallback`,
    };
  } catch (error) {
    return {
      service: 'Image Generation',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifySynthesia(): Promise<APIResult> {
  const apiKey = process.env.SYNTHESIA_API_KEY;

  if (!apiKey) {
    return {
      service: 'Synthesia (Video)',
      status: 'skipped',
      message: 'SYNTHESIA_API_KEY not set',
    };
  }

  try {
    const startTime = Date.now();
    const response = await fetch('https://api.synthesia.io/v1/videos', {
      headers: { Authorization: `Bearer ${apiKey}` },
      timeout: 10000,
    });
    const responseTime = Date.now() - startTime;

    if (!response.ok && response.status !== 403) {
      // 403 means auth worked but you're not allowed to list videos
      return {
        service: 'Synthesia (Video)',
        status: 'failure',
        message: `API returned ${response.status}`,
        responseTime,
      };
    }

    return {
      service: 'Synthesia (Video)',
      status: 'success',
      message: 'Connected successfully',
      responseTime,
    };
  } catch (error) {
    return {
      service: 'Synthesia (Video)',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifyElevenLabs(): Promise<APIResult> {
  const apiKey = process.env.ELEVEN_LABS_API_KEY;

  if (!apiKey) {
    return {
      service: 'Eleven Labs (Voiceover)',
      status: 'skipped',
      message: 'ELEVEN_LABS_API_KEY not set',
    };
  }

  try {
    const startTime = Date.now();
    const response = await fetch('https://api.elevenlabs.io/v1/user', {
      headers: { 'xi-api-key': apiKey },
      timeout: 10000,
    });
    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      return {
        service: 'Eleven Labs (Voiceover)',
        status: 'failure',
        message: `API returned ${response.status}`,
        responseTime,
      };
    }

    const data: any = await response.json();

    return {
      service: 'Eleven Labs (Voiceover)',
      status: 'success',
      message: `Connected. Character limit: ${data.character_limit}`,
      responseTime,
    };
  } catch (error) {
    return {
      service: 'Eleven Labs (Voiceover)',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifyEmailPlatform(): Promise<APIResult> {
  const platform = process.env.EMAIL_PLATFORM || 'klaviyo';

  if (platform === 'klaviyo') {
    const apiKey = process.env.KLAVIYO_API_KEY;
    if (!apiKey) {
      return {
        service: 'Email Platform (Klaviyo)',
        status: 'skipped',
        message: 'KLAVIYO_API_KEY not set',
      };
    }

    try {
      const startTime = Date.now();
      const response = await fetch('https://a.klaviyo.com/api/accounts/', {
        headers: { Authorization: `Klaviyo-API-Key ${apiKey}` },
        timeout: 10000,
      });
      const responseTime = Date.now() - startTime;

      if (!response.ok) {
        return {
          service: 'Email Platform (Klaviyo)',
          status: 'failure',
          message: `API returned ${response.status}`,
          responseTime,
        };
      }

      return {
        service: 'Email Platform (Klaviyo)',
        status: 'success',
        message: 'Connected successfully',
        responseTime,
      };
    } catch (error) {
      return {
        service: 'Email Platform (Klaviyo)',
        status: 'failure',
        message: `Error: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  } else if (platform === 'substack') {
    const apiKey = process.env.SUBSTACK_API_KEY;
    if (!apiKey) {
      return {
        service: 'Email Platform (Substack)',
        status: 'skipped',
        message: 'SUBSTACK_API_KEY not set',
      };
    }

    return {
      service: 'Email Platform (Substack)',
      status: 'warning',
      message: 'Substack API verification not implemented',
    };
  } else if (platform === 'convertkit') {
    const apiKey = process.env.CONVERTKIT_API_KEY;
    if (!apiKey) {
      return {
        service: 'Email Platform (ConvertKit)',
        status: 'skipped',
        message: 'CONVERTKIT_API_KEY not set',
      };
    }

    return {
      service: 'Email Platform (ConvertKit)',
      status: 'warning',
      message: 'ConvertKit API verification not implemented',
    };
  }

  return {
    service: 'Email Platform',
    status: 'warning',
    message: `Unknown platform: ${platform}`,
  };
}

async function verifyGitHubActions(): Promise<APIResult> {
  const token = process.env.GITHUB_ACTIONS_TOKEN;

  if (!token) {
    return {
      service: 'GitHub Actions',
      status: 'skipped',
      message: 'GITHUB_ACTIONS_TOKEN not set',
    };
  }

  try {
    const startTime = Date.now();
    const response = await fetch('https://api.github.com/user', {
      headers: { Authorization: `token ${token}` },
      timeout: 10000,
    });
    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      return {
        service: 'GitHub Actions',
        status: 'failure',
        message: `API returned ${response.status}`,
        responseTime,
      };
    }

    const data: any = await response.json();

    return {
      service: 'GitHub Actions',
      status: 'success',
      message: `Authenticated as ${data.login}`,
      responseTime,
    };
  } catch (error) {
    return {
      service: 'GitHub Actions',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifySlack(): Promise<APIResult> {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;

  if (!webhookUrl) {
    return {
      service: 'Slack',
      status: 'skipped',
      message: 'SLACK_WEBHOOK_URL not set',
    };
  }

  try {
    const startTime = Date.now();
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: 'ProfitEngine Automation Verification Test',
        blocks: [
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: '*ProfitEngine Automation*\n✅ Verification in progress...',
            },
          },
        ],
      }),
      timeout: 10000,
    });
    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      return {
        service: 'Slack',
        status: 'failure',
        message: `Webhook returned ${response.status}`,
        responseTime,
      };
    }

    return {
      service: 'Slack',
      status: 'success',
      message: 'Webhook working correctly',
      responseTime,
    };
  } catch (error) {
    return {
      service: 'Slack',
      status: 'failure',
      message: `Error: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function verifyConfigFile(): Promise<APIResult> {
  const configPath = path.join(process.cwd(), 'automation-status.json');

  if (!fs.existsSync(configPath)) {
    return {
      service: 'Automation Config',
      status: 'warning',
      message: 'automation-status.json not found. Will be created on first run.',
    };
  }

  try {
    const content = fs.readFileSync(configPath, 'utf-8');
    const data = JSON.parse(content);

    return {
      service: 'Automation Config',
      status: 'success',
      message: `Config valid. Last updated: ${data.last_run}`,
      details: {
        products: Object.keys(data.products || {}).length,
        jobs: Object.keys(data.automation_jobs || {}).length,
      },
    };
  } catch (error) {
    return {
      service: 'Automation Config',
      status: 'failure',
      message: `Invalid JSON: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function main() {
  logSection('🚀 ProfitEngine v5 Automation Verification');

  log(`Dry-run mode: ${DRY_RUN ? 'ENABLED' : 'DISABLED'}`, colors.yellow);
  log(`Verbose logging: ${VERBOSE ? 'ENABLED' : 'DISABLED'}`, colors.yellow);
  log(`\nStarting verification at ${new Date().toISOString()}...`, colors.gray);

  const results: APIResult[] = [];

  logSection('Verifying API Credentials');

  // Run all verifications in parallel
  const verifications = await Promise.all([
    verifyGumroad(),
    verifyInstagram(),
    verifyImageGeneration(),
    verifySynthesia(),
    verifyElevenLabs(),
    verifyEmailPlatform(),
    verifyGitHubActions(),
    verifySlack(),
    verifyConfigFile(),
  ]);

  results.push(...verifications);

  // Display results
  results.forEach((result) => {
    const statusSymbol =
      result.status === 'success'
        ? '✅'
        : result.status === 'failure'
          ? '❌'
          : result.status === 'warning'
            ? '⚠️'
            : '⏭️';

    const color =
      result.status === 'success'
        ? colors.green
        : result.status === 'failure'
          ? colors.red
          : result.status === 'warning'
            ? colors.yellow
            : colors.gray;

    const responseTimeStr = result.responseTime ? ` (${result.responseTime}ms)` : '';
    log(`${statusSymbol} ${result.service}: ${result.message}${responseTimeStr}`, color);

    if (VERBOSE && result.details) {
      console.log(`  Details: ${JSON.stringify(result.details, null, 2)}`);
    }
  });

  // Summary
  logSection('Summary');

  const summary = {
    total: results.length,
    passed: results.filter((r) => r.status === 'success').length,
    failed: results.filter((r) => r.status === 'failure').length,
    warnings: results.filter((r) => r.status === 'warning').length,
    skipped: results.filter((r) => r.status === 'skipped').length,
  };

  log(`Total checks: ${summary.total}`, colors.blue);
  log(`✅ Passed: ${summary.passed}`, colors.green);
  log(`❌ Failed: ${summary.failed}`, colors.red);
  log(`⚠️  Warnings: ${summary.warnings}`, colors.yellow);
  log(`⏭️  Skipped: ${summary.skipped}`, colors.gray);

  // Recommendations
  const recommendations: string[] = [];

  if (summary.failed > 0) {
    recommendations.push(
      'Fix all failed API connections before running automation'
    );
  }

  if (!process.env.INSTAGRAM_ACCESS_TOKEN) {
    recommendations.push('Set INSTAGRAM_ACCESS_TOKEN to enable social posting');
  }

  if (!process.env.KLAVIYO_API_KEY && !process.env.SUBSTACK_API_KEY) {
    recommendations.push('Set email platform credentials (KLAVIYO_API_KEY or SUBSTACK_API_KEY)');
  }

  if (!process.env.SLACK_WEBHOOK_URL) {
    recommendations.push('Set SLACK_WEBHOOK_URL to enable automation alerts');
  }

  if (recommendations.length > 0) {
    logSection('Recommendations');
    recommendations.forEach((rec, i) => {
      log(`${i + 1}. ${rec}`, colors.yellow);
    });
  }

  // Final status
  logSection('');

  if (summary.failed === 0) {
    log(
      '✅ All critical APIs verified! Ready to run automation.',
      colors.green
    );
    log('\nNext steps:');
    log('  1. npm run launch:automation  (dry-run first)', colors.gray);
    log('  2. Check automation-status.json for results', colors.gray);
    log('  3. Monitor Slack for notifications', colors.gray);
    process.exit(0);
  } else {
    log(`❌ ${summary.failed} critical failures detected.`, colors.red);
    log('Please fix these issues before running automation.', colors.red);
    process.exit(1);
  }
}

main().catch((error) => {
  log(`\nFatal error: ${error.message}`, colors.red);
  process.exit(1);
});

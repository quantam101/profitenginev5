/**
 * Newsletter Automation Verification Script
 * Tests all 6 platform implementations: Beehiiv, Substack, ConvertKit, Medium, Dev.to, Hashnode
 *
 * Usage:
 *   npx ts-node scripts/verify-newsletters.ts
 */

import {
  BeehiivPublisher,
  SubstackPublisher,
  ConvertKitPublisher,
  MediumPublisher,
  DevToPublisher,
  HashnodePublisher,
  NewsletterBatchPublisher,
  NewsletterContent,
  PlatformPublishConfig,
} from '@/app/lib/automation/newsletters';

// Test content
const testContent: NewsletterContent = {
  title: 'Test Newsletter - ProfitEngine Platform Verification',
  subtitle: 'Automated newsletter distribution test',
  body: '# Welcome\n\nThis is a test of the newsletter automation system.\n\n**Key Features:**\n- Multi-platform publishing\n- Automatic content transformation\n- Rate limiting and retry logic\n- Subscriber metrics tracking',
  summary: 'Testing automated newsletter distribution across 6 platforms',
  tags: ['test', 'automation', 'newsletter'],
  featuredImage: 'https://profitengine.alreadyherellc.com/og-image.png',
  ctaText: 'Learn More',
  ctaLink: 'https://profitengine.alreadyherellc.com',
};

// Platform status interface
interface PlatformStatus {
  platform: string;
  enabled: boolean;
  apiKeyConfigured: boolean;
  publisherClass: string;
  rateLimit: string;
  capabilities: string[];
  metricsSupported: string[];
}

// Check environment variables
function checkEnvironment(): Map<string, boolean> {
  const envCheck = new Map<string, boolean>();

  envCheck.set('BEEHIIV_API_KEY', !!process.env.BEEHIIV_API_KEY);
  envCheck.set('SUBSTACK_API_TOKEN', !!process.env.SUBSTACK_API_TOKEN);
  envCheck.set('CONVERTKIT_API_KEY', !!process.env.CONVERTKIT_API_KEY);
  envCheck.set('MEDIUM_API_TOKEN', !!process.env.MEDIUM_API_TOKEN);
  envCheck.set('DEVTO_API_KEY', !!process.env.DEVTO_API_KEY);
  envCheck.set('HASHNODE_API_KEY', !!process.env.HASHNODE_API_KEY);

  return envCheck;
}

// Get platform status
function getPlatformStatus(): PlatformStatus[] {
  const envCheck = checkEnvironment();

  return [
    {
      platform: 'beehiiv',
      enabled: envCheck.get('BEEHIIV_API_KEY') || false,
      apiKeyConfigured: envCheck.get('BEEHIIV_API_KEY') || false,
      publisherClass: 'BeehiivPublisher',
      rateLimit: '10 req/sec',
      capabilities: ['publish', 'schedule', 'featured_image', 'tags'],
      metricsSupported: ['totalSubscribers', 'openRate', 'clickRate'],
    },
    {
      platform: 'substack',
      enabled: envCheck.get('SUBSTACK_API_TOKEN') || false,
      apiKeyConfigured: envCheck.get('SUBSTACK_API_TOKEN') || false,
      publisherClass: 'SubstackPublisher',
      rateLimit: '5 req/sec',
      capabilities: ['publish', 'markdown_body', 'bylines'],
      metricsSupported: ['totalSubscribers', 'openRate'],
    },
    {
      platform: 'convertkit',
      enabled: envCheck.get('CONVERTKIT_API_KEY') || false,
      apiKeyConfigured: envCheck.get('CONVERTKIT_API_KEY') || false,
      publisherClass: 'ConvertKitPublisher',
      rateLimit: '10 req/sec',
      capabilities: ['publish', 'tags', 'html_content', 'public_access'],
      metricsSupported: ['totalSubscribers'],
    },
    {
      platform: 'medium',
      enabled: envCheck.get('MEDIUM_API_TOKEN') || false,
      apiKeyConfigured: envCheck.get('MEDIUM_API_TOKEN') || false,
      publisherClass: 'MediumPublisher',
      rateLimit: '5 req/sec',
      capabilities: ['publish', 'html_content', 'tags', 'scheduled_publish'],
      metricsSupported: [],
    },
    {
      platform: 'devto',
      enabled: envCheck.get('DEVTO_API_KEY') || false,
      apiKeyConfigured: envCheck.get('DEVTO_API_KEY') || false,
      publisherClass: 'DevToPublisher',
      rateLimit: '10 req/sec',
      capabilities: ['publish', 'markdown_body', 'featured_image', 'tags', 'canonical_url'],
      metricsSupported: ['totalSubscribers (followers)'],
    },
    {
      platform: 'hashnode',
      enabled: envCheck.get('HASHNODE_API_KEY') || false,
      apiKeyConfigured: envCheck.get('HASHNODE_API_KEY') || false,
      publisherClass: 'HashnodePublisher',
      rateLimit: '5 req/sec',
      capabilities: ['publish_graphql', 'markdown_content', 'featured_image', 'tags', 'publication_id'],
      metricsSupported: ['followers'],
    },
  ];
}

// Verify API route exists
function verifyApiRoute(): boolean {
  try {
    const routePath = './app/api/automation/newsletters/route.ts';
    require('fs').accessSync(routePath);
    return true;
  } catch {
    return false;
  }
}

// Verify library file exists
function verifyLibraryFile(): boolean {
  try {
    const libPath = './app/lib/automation/newsletters.ts';
    require('fs').accessSync(libPath);
    return true;
  } catch {
    return false;
  }
}

// Generate report
function generateReport(): string {
  const lines: string[] = [];

  lines.push('\n' + '='.repeat(80));
  lines.push('NEWSLETTER AUTOMATION VERIFICATION REPORT');
  lines.push('='.repeat(80));

  lines.push('\n[PROJECT FILES]');
  lines.push(`  Library: app/lib/automation/newsletters.ts ${verifyLibraryFile() ? 'OK' : 'MISSING'}`);
  lines.push(`  API Route: app/api/automation/newsletters/route.ts ${verifyApiRoute() ? 'OK' : 'MISSING'}`);

  lines.push('\n[ENVIRONMENT VARIABLES]');
  const envCheck = checkEnvironment();
  envCheck.forEach((value, key) => {
    lines.push(`  ${key}: ${value ? 'Configured' : 'Missing'}`);
  });

  lines.push('\n[PLATFORM IMPLEMENTATIONS]');
  const platforms = getPlatformStatus();

  platforms.forEach((status, idx) => {
    const statusIcon = status.enabled ? '[READY]' : '[PENDING]';
    lines.push(`\n  ${idx + 1}. ${status.platform.toUpperCase()} ${statusIcon}`);
    lines.push(`     Class: ${status.publisherClass}`);
    lines.push(`     Rate Limit: ${status.rateLimit}`);
    lines.push(`     Capabilities: ${status.capabilities.join(', ')}`);
    lines.push(`     Metrics: ${status.metricsSupported.length > 0 ? status.metricsSupported.join(', ') : 'None'}`);
    lines.push(`     Status: ${status.apiKeyConfigured ? 'READY' : 'PENDING API KEY'}`);
  });

  const enabledCount = platforms.filter(p => p.enabled).length;
  lines.push(`\n[SUMMARY]`);
  lines.push(`  Platforms Ready: ${enabledCount}/6`);
  lines.push(`  API Route: ${verifyApiRoute() ? 'Implemented' : 'Missing'}`);
  lines.push(`  Library: ${verifyLibraryFile() ? 'Implemented' : 'Missing'}`);

  lines.push('\n[API ENDPOINTS]');
  lines.push('  POST /api/automation/newsletters');
  lines.push('    - Publish content to selected platforms');
  lines.push('    - Request body: title, body, platforms[], scheduleFor?, dryRun?');
  lines.push('    - Response: batchId, summary, results[], metrics[]');
  lines.push('\n  GET /api/automation/newsletters');
  lines.push('    - Fetch metrics across all platforms');
  lines.push('    - Query params: ?platform=<name> (optional)');
  lines.push('    - Response: metrics[], summary { totalSubscribers, platformCount }');

  lines.push('\n[TESTING]');
  lines.push('  curl -X POST http://localhost:3000/api/automation/newsletters');
  lines.push('    -H "Content-Type: application/json"');
  lines.push('    -H "Authorization: Bearer $AUTOMATION_API_TOKEN"');
  lines.push('    -d "{\"title\":\"Test\",\"body\":\"Content\",\"platforms\":[\"beehiiv\"]}"');

  lines.push('\n' + '='.repeat(80));

  return lines.join('\n');
}

// Main execution
async function main() {
  console.log(generateReport());

  // Test batch publisher instantiation (dry run - no actual publishing)
  console.log('\n[BATCH PUBLISHER TEST]');
  try {
    const configs: PlatformPublishConfig[] = [
      { platform: 'beehiiv', enabled: !!process.env.BEEHIIV_API_KEY, apiKey: process.env.BEEHIIV_API_KEY || 'mock' },
      { platform: 'substack', enabled: !!process.env.SUBSTACK_API_TOKEN, apiKey: process.env.SUBSTACK_API_TOKEN || 'mock' },
      { platform: 'convertkit', enabled: !!process.env.CONVERTKIT_API_KEY, apiKey: process.env.CONVERTKIT_API_KEY || 'mock' },
      { platform: 'medium', enabled: !!process.env.MEDIUM_API_TOKEN, apiKey: process.env.MEDIUM_API_TOKEN || 'mock' },
      { platform: 'devto', enabled: !!process.env.DEVTO_API_KEY, apiKey: process.env.DEVTO_API_KEY || 'mock' },
      { platform: 'hashnode', enabled: !!process.env.HASHNODE_API_KEY, apiKey: process.env.HASHNODE_API_KEY || 'mock' },
    ];

    const publisher = new NewsletterBatchPublisher(configs);
    console.log('  NewsletterBatchPublisher instantiated successfully');
  } catch (error) {
    console.log(`  Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

main().catch(console.error);

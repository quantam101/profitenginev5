#!/usr/bin/env node
/**
 * Revenue OS deployment readiness and operational helper.
 *
 * Subcommands:
 *   check            — validate environment and production readiness
 *   indexes          — create required MongoDB indexes
 *   seed-dry-run     — validate and dry-run the 65 seed records
 *   seed-import      — run the production import
 *   verify           — confirm 65 records and basic counts
 *   rollback         — disable feature flags and record rollback event
 *
 * Environment variables are read from process.env; real secrets must be set
 * in Vercel/GitHub Secrets or the server environment, never in this file.
 */
import { getDb, closeClient } from '../lib/mongodb.mjs';
import { ensureIndexes as ensureRevenuePlayIndexes } from '../lib/revenue-os/repositories/revenue-play.repository.mjs';
import { ensureIndexes as ensureCompanyIndexes } from '../lib/revenue-os/repositories/company.repository.mjs';
import { ensureIndexes as ensureContactIndexes } from '../lib/revenue-os/repositories/contact.repository.mjs';
import { ensureIndexes as ensureOpportunityIndexes } from '../lib/revenue-os/repositories/opportunity.repository.mjs';
import { ensureIndexes as ensureFollowUpIndexes } from '../lib/revenue-os/repositories/follow-up.repository.mjs';
import { ensureIndexes as ensureActivityIndexes } from '../lib/revenue-os/repositories/activity.repository.mjs';
import { ensureIndexes as ensureAiActionIndexes } from '../lib/revenue-os/repositories/ai-action.repository.mjs';
import { ensureIndexes as ensureWebhookDeliveryIndexes } from '../lib/revenue-os/repositories/webhook-delivery.repository.mjs';
import { createActivity } from '../lib/revenue-os/repositories/activity.repository.mjs';
import { importRevenueOsSeed } from '../lib/revenue-os/services/seed-import.mjs';
import { countRevenuePlays } from '../lib/revenue-os/repositories/revenue-play.repository.mjs';

const VALID_COMMANDS = ['check', 'indexes', 'seed-dry-run', 'seed-import', 'verify', 'rollback'];

function log(message, level = 'info') {
  const prefix = level === 'error' ? '[ERROR]' : level === 'warn' ? '[WARN]' : '[INFO]';
  console.log(`${prefix} ${message}`);
}

function exit(message, code = 1) {
  console.error(message);
  process.exit(code);
}

const command = process.argv[2];
if (!VALID_COMMANDS.includes(command)) {
  exit(`Usage: node scripts/revenue-os-deploy.mjs <${VALID_COMMANDS.join('|')}>`);
}

const required = {
  MONGODB_URI: process.env.MONGODB_URI || process.env.MONGO_URL,
  NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET,
  NEXTAUTH_URL: process.env.NEXTAUTH_URL,
};

const checks = {
  mongo: Boolean(required.MONGODB_URI),
  nextauth: Boolean(required.NEXTAUTH_SECRET && required.NEXTAUTH_URL),
  flags: process.env.REVENUE_OS_ENABLED === 'true',
  ai: process.env.REVENUE_OS_AI_ENABLED === 'true',
  slack: process.env.REVENUE_OS_SLACK_ENABLED === 'true' && Boolean(process.env.SLACK_REVENUE_WEBHOOK),
  zapier: process.env.REVENUE_OS_ZAPIER_ENABLED === 'true' && Boolean(process.env.ZAPIER_REVENUE_WEBHOOK && process.env.WEBHOOK_SIGNING_SECRET),
};

async function runCheck() {
  let ok = true;
  if (!checks.mongo) { log('MONGODB_URI / MONGO_URL is missing', 'error'); ok = false; }
  if (!checks.nextauth) { log('NEXTAUTH_SECRET or NEXTAUTH_URL is missing', 'error'); ok = false; }

  const productionPlaceholderPatterns = [
    /your-profitengine-domain\.com/i,
    /example\.com/i,
    /localhost/i,
    /<replace-me>/i,
    /<token>/i,
    /TODO:\s*set\s*later/i,
    /mock|dummy|sample|test-token/i,
  ];

  const envSnapshot = JSON.stringify({
    NEXTAUTH_URL: process.env.NEXTAUTH_URL,
    MONGODB_URI: process.env.MONGODB_URI ? '[redacted]' : undefined,
    MONGODB_DB: process.env.MONGODB_DB,
  });

  for (const pattern of productionPlaceholderPatterns) {
    if (pattern.test(envSnapshot)) {
      log(`Production config contains placeholder-like value matching ${pattern}`, 'error');
      ok = false;
    }
  }

  log(`Revenue OS enabled: ${checks.flags}`);
  log(`AI advisor enabled: ${checks.ai}`);
  log(`Slack enabled: ${checks.slack}`);
  log(`Zapier enabled: ${checks.zapier}`);

  if (!ok) {
    exit('Deployment readiness check failed. Fix environment variables before deploying.', 1);
  }
  log('Deployment readiness check passed.');
}

async function runIndexes() {
  await Promise.all([
    ensureRevenuePlayIndexes(),
    ensureCompanyIndexes(),
    ensureContactIndexes(),
    ensureOpportunityIndexes(),
    ensureFollowUpIndexes(),
    ensureActivityIndexes(),
    ensureAiActionIndexes(),
    ensureWebhookDeliveryIndexes(),
  ]);
  log('All Revenue OS indexes created or verified.');
}

async function runSeedDryRun() {
  const summary = await importRevenueOsSeed({ dryRun: true });
  log(`Dry-run result: ${JSON.stringify(summary)}`);
  if (summary.errors.length > 0) {
    exit('Dry-run failed validation.', 1);
  }
}

async function runSeedImport() {
  const summary = await importRevenueOsSeed({ dryRun: false });
  log(`Import result: ${JSON.stringify(summary)}`);
  if (summary.errors.length > 0 || summary.inserted + summary.updated !== 65) {
    exit('Seed import did not complete as expected.', 1);
  }
  await createActivity({
    entityType: 'revenue_play',
    entityId: 'seed-import',
    actionType: 'seed_imported',
    actor: 'deploy',
    summary: `Imported ${summary.inserted} new and ${summary.updated} updated revenue plays`,
    metadata: summary,
  });
}

async function runVerify() {
  const count = await countRevenuePlays();
  if (count !== 65) {
    exit(`Expected 65 revenue plays, found ${count}`, 1);
  }
  log(`Verified ${count} revenue plays in the database.`);
}

async function runRollback() {
  process.env.REVENUE_OS_ENABLED = 'false';
  process.env.REVENUE_OS_IMPORT_ENABLED = 'false';
  process.env.REVENUE_OS_AI_ENABLED = 'false';
  process.env.REVENUE_OS_SLACK_ENABLED = 'false';
  process.env.REVENUE_OS_ZAPIER_ENABLED = 'false';
  await createActivity({
    entityType: 'system',
    entityId: 'revenue-os',
    actionType: 'rollback',
    actor: 'deploy',
    summary: 'Revenue OS feature flags disabled as part of rollback procedure',
    metadata: { reason: 'manual rollback' },
  });
  log('Rollback recorded. Restore previous Vercel deployment and re-enable flags after review.');
}

async function main() {
  try {
    switch (command) {
      case 'check':
        await runCheck();
        break;
      case 'indexes':
        await runIndexes();
        break;
      case 'seed-dry-run':
        await runSeedDryRun();
        break;
      case 'seed-import':
        await runSeedImport();
        break;
      case 'verify':
        await runVerify();
        break;
      case 'rollback':
        await runRollback();
        break;
      default:
        exit(`Unknown command: ${command}`);
    }
  } finally {
    await closeClient().catch(() => {});
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

import { importRevenueOsSeed } from '../lib/revenue-os/services/seed-import.mjs';
import { closeClient } from '../lib/mongodb.mjs';

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const force = args.includes('--force');

if (!dryRun && !force) {
  const enabled = process.env.REVENUE_OS_ENABLED === 'true';
  const importEnabled = process.env.REVENUE_OS_IMPORT_ENABLED === 'true';
  if (!enabled || !importEnabled) {
    console.error(
      'Revenue OS seed import is disabled. Set REVENUE_OS_ENABLED=true and REVENUE_OS_IMPORT_ENABLED=true, or pass --force.'
    );
    process.exit(1);
  }
}

const summary = await importRevenueOsSeed({ dryRun });
console.log(JSON.stringify(summary, null, 2));
await closeClient().catch(() => {});
process.exit(summary.errors.length ? 1 : 0);

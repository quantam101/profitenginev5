'use strict';
/**
 * index.js — ProfitEngine v5.0 Entry Point
 * Already Here LLC | alreadyherellc.com
 * Global enterprise. Military specification. Production ready. VHLL. ASI-level automation.
 */
const fs = require('fs');
['logs','data','data/cache','data/backups'].forEach(d => fs.mkdirSync(d, { recursive: true }));

const cfg     = require('./core/config');
const logger  = require('./core/logger').child('BOOT');
const api     = require('./api');
const workers = require('./workers');
const pipeline = require('./pipeline');

async function main() {
  console.log(`
╔══════════════════════════════════════════════════════════╗
║   ProfitEngine v5.0 — Already Here LLC                  ║
║   Global Enterprise · Military Spec · ASI Automation    ║
║   alreadyherellc.com                                     ║
╚══════════════════════════════════════════════════════════╝
`);
  try { cfg.validate(); } catch (err) { logger.error('Config invalid', { error: err.message }); process.exit(1); }
  logger.info('Config validated', { env: cfg.get().env, domain: cfg.get().siteDomain });

  api.start(cfg.get().port);
  workers.scheduleRecurring();
  await pipeline.start();

  logger.info('ProfitEngine v5.0 fully operational');
}

main().catch(err => { console.error('[BOOT] Fatal:', err.message); process.exit(1); });

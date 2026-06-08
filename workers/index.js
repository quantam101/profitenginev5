'use strict';
/**
 * workers/index.js — ProfitEngine v5.0
 * Background worker pool for CPU-bound tasks:
 * - Content quality scoring
 * - Keyword density analysis
 * - Dead-letter queue retry dispatcher
 * - Sitemap + RSS batch rebuild
 * Runs in the same process via setImmediate/microtask queue.
 * Designed for future extraction to worker_threads if scale demands.
 */
const logger   = require('../core/logger').child('WORKERS');
const state    = require('../core/state');
const cfg      = require('../core/config').get;

// ── Task Registry ─────────────────────────────────────────────────────────────
const TASKS = {};
let _queue   = [];
let _running = false;

function register(name, fn) {
  TASKS[name] = fn;
  logger.debug(`Worker registered: ${name}`);
}

function enqueue(taskName, payload = {}, priority = 5) {
  if (!TASKS[taskName]) {
    logger.warn(`Unknown task: ${taskName}`);
    return false;
  }
  _queue.push({ taskName, payload, priority, enqueuedAt: Date.now() });
  _queue.sort((a, b) => b.priority - a.priority); // higher priority first
  state.set('workerQueue', _queue.map(t => ({ taskName: t.taskName, priority: t.priority })));
  if (!_running) drain();
  return true;
}

async function drain() {
  if (_running || !_queue.length) return;
  _running = true;
  while (_queue.length) {
    const job = _queue.shift();
    try {
      logger.debug(`Executing task: ${job.taskName}`);
      await TASKS[job.taskName](job.payload);
      state.increment('workerTasksCompleted');
    } catch (err) {
      logger.warn(`Task failed: ${job.taskName} — ${err.message}`);
      state.push('workerErrors', { task: job.taskName, error: err.message, ts: new Date().toISOString() }, 50);
    }
    // Yield to event loop between tasks
    await new Promise(r => setImmediate(r));
  }
  state.set('workerQueue', []);
  _running = false;
}

// ── Built-in Tasks ────────────────────────────────────────────────────────────

// Content keyword density scorer (Tier 0 — pure regex)
register('scoreKeywordDensity', async ({ postId, title, body, keywords }) => {
  if (!body || !keywords?.length) return;
  const wordCount = body.split(/\s+/).length;
  const scores = {};
  for (const kw of keywords) {
    const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const matches  = (body.match(new RegExp(escaped, 'gi')) || []).length;
    scores[kw] = wordCount > 0 ? +((matches / wordCount) * 100).toFixed(2) : 0;
  }
  state.set(`kd_${postId}`, scores);
  logger.debug(`Keyword density scored: ${postId}`);
});

// Dead-letter queue retry dispatcher
register('retryDLQ', async () => {
  const dlq = state.get('dlq', []);
  const recoverable = dlq.filter(d => d.retries < 3);
  if (!recoverable.length) return;
  logger.info(`DLQ retry: ${recoverable.length} items queued for recovery`);
  state.set('recoveryQueue', recoverable);
  state.set('dlq', dlq.filter(d => d.retries >= 3));
});

// Sitemap rebuild trigger
register('rebuildSitemap', async () => {
  try {
    const website = require('../agents/website');
    await website.publishSitemap();
    await website.publishRSS();
    logger.info('Sitemap + RSS rebuilt by worker');
  } catch (err) {
    logger.warn(`Sitemap rebuild failed: ${err.message}`);
  }
});

// SEO niche keyword refresh
register('refreshKeywords', async () => {
  try {
    const seo = require('../agents/seo');
    await seo.runNicheKeywordCycle();
    logger.info('Keyword cycle refreshed by worker');
  } catch (err) {
    logger.warn(`Keyword refresh failed: ${err.message}`);
  }
});

// Revenue threshold check
register('checkRevenue', async () => {
  try {
    const revenue = require('../agents/revenue');
    await revenue.checkThresholds();
  } catch { /* non-fatal */ }
});

// ── Scheduler Integration ─────────────────────────────────────────────────────
function scheduleRecurring() {
  // DLQ retry every 30min
  setInterval(() => enqueue('retryDLQ', {}, 3), 30 * 60_000);
  // Keyword refresh every 6h
  setInterval(() => enqueue('refreshKeywords', {}, 2), 6 * 60 * 60_000);
  // Revenue check every 2h
  setInterval(() => enqueue('checkRevenue', {}, 1), 2 * 60 * 60_000);
  logger.info('Worker recurring tasks scheduled');
}

function stats() {
  return {
    queueDepth:    _queue.length,
    running:       _running,
    tasksComplete: state.get('workerTasksCompleted', 0),
    registeredTasks: Object.keys(TASKS),
    recentErrors:  state.get('workerErrors', []).slice(-5),
  };
}

module.exports = { register, enqueue, drain, scheduleRecurring, stats };

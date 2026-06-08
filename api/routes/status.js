'use strict';
const express   = require('express');
const router    = express.Router();
const state     = require('../../core/state');
const llm       = require('../../core/llm');
const blog      = require('../../publishers/blog');
const cache     = require('../../core/cache');
const cfg       = require('../../core/config').get;
const intel     = require('../../agents/intelligence');
const pipeline  = require('../../pipeline');
const workers   = require('../../workers');

router.get('/', (req, res) => {
  const all = state.getAll();
  res.json({
    version:       '5.0.0',
    ok:            true,
    uptime:        Math.round(process.uptime()),
    startedAt:     all.startedAt,
    sessionId:     all.sessionId,
    lastCycle:     all.lastCycle,
    lastHealth:    all.lastHealth,
    totalGenerated:all.totalGenerated || 0,
    totalPublished:all.totalPublished || 0,
    totalSocial:   all.totalSocial    || 0,
    totalTrends:   all.totalTrends    || 0,
    latestTrends:  (all.latestTrends  || []).slice(0,5),
    publishLog:    (all.publishLog    || []).slice(-10),
    dlqDepth:      (all.dlq           || []).length,
    tokens:        llm.todayTokens(),
    circuits:      llm.circuitStatus(),
    platformStats: blog.platformStats(),
    cacheStats:    cache.stats(),
    intelligenceReport: intel.getReport(),
    workers:           workers.stats(),
    adaptive: { scanInterval: state.get('adaptiveScanInterval', cfg().scanIntervalMin), contentPerRun: state.get('adaptiveContentPerRun', cfg().contentPerRun) },
  });
});

router.get('/health', (req, res) => {
  const h = state.get('lastHealth', {});
  res.json({ ok: h.llm?.ok !== false, memory: h.memory, cpu: h.cpu, llm: h.llm, tokens: h.tokens, circuits: h.circuits });
});

router.post('/cycle', async (req, res) => {
  res.json({ ok: true, message: 'Cycle queued' });
  setImmediate(() => pipeline.runCycle().catch(() => {}));
});

router.post('/intelligence', async (req, res) => {
  res.json({ ok: true, message: 'Intelligence cycle queued' });
  setImmediate(() => pipeline.runIntelligence().catch(() => {}));
});

module.exports = router;

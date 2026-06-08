'use strict';
/**
 * pipeline/index.js — ProfitEngine v5.0
 * Enterprise pipeline orchestrator.
 * Adaptive scheduling. Full agent chain. Resilient error recovery.
 * Every stage is instrumented and telemetered to UltraFlow.
 */
const logger      = require('../core/logger').child('PIPELINE');
const state       = require('../core/state');
const cfg         = require('../core/config').get;
const email       = require('../core/email');
const uf          = require('../ultraflow');
const intel       = require('../agents/intelligence');
const trends      = require('../agents/intelligence/trendScanner');
const content     = require('../agents/content');
const seo         = require('../agents/seo');
const affiliate   = require('../agents/affiliate');
const compliance  = require('../agents/compliance');
const website     = require('../agents/website');
const blog        = require('../publishers/blog');
const social      = require('../agents/social');
const revenue     = require('../agents/revenue');
const health      = require('../agents/health');
const pod         = require('../agents/pod');
const workers     = require('../workers');

let _running  = false;
let _scanTimer   = null;
let _intelTimer  = null;
let _healthTimer = null;
let _dailyTimer  = null;
let _podTimer    = null;

function getScanInterval() {
  return (state.get('adaptiveScanInterval', null) || cfg().scanIntervalMin) * 60_000;
}

// ── Main Content Pipeline ─────────────────────────────────────────────────────
async function runCycle() {
  if (_running) { logger.warn('Cycle already running — skipping'); return; }
  _running = true;
  const cycle = state.increment('cycleCount');
  const start = Date.now();
  const summary = { cycle, trends: 0, generated: 0, published: 0, social: 0, errors: [] };

  logger.info(`=== Cycle #${cycle} START ===`);

  try {
    // Stage 1: Trend scanning
    const trendList = await trends.scan().catch(err => {
      summary.errors.push({ stage: 'trends', msg: err.message });
      uf.emit('cycle.error', { stage: 'trends', error: err.message });
      return [];
    });
    summary.trends = trendList.length;
    if (trendList.length) uf.emit('trends.scanned', { count: trendList.length });

    if (!trendList.length) { logger.info('No trends — pipeline paused'); return; }

    // Stage 2: Content generation
    const posts = await content.generateBatch(trendList).catch(err => {
      summary.errors.push({ stage: 'content', msg: err.message });
      return [];
    });
    summary.generated = posts.length;

    // Stage 3: Full enrichment chain per post
    for (const raw of posts) {
      try {
        let post = raw;
        // 3a SEO optimization + A/B title
        post = await seo.optimizePost(post);
        post = await seo.runABTitleTest(post);
        // 3b Affiliate link injection
        post = affiliate.processPost(post);
        // 3c Compliance
        post = await compliance.processPost(post);
        // 3d Website publish
        await website.publishPost(post);
        // 3e Blog platform publish
        const result = await blog.publish(post);
        summary.published += result.published;
        uf.emit('post.published', { title: post.title, platforms: result.platforms?.map(p=>p.platform), count: result.published });
        if (post.id) workers.enqueue('scoreKeywordDensity', { postId: post.id, title: post.title, body: post.body, keywords: post.keywords }, 4);
        // 3f Social distribution — Node.js (Reddit, Mastodon, Pinterest)
        if (result.published > 0) {
          const socialCount = await social.distribute(post).catch(() => 0);
          summary.social += socialCount;
          uf.emit('social.distributed', { count: socialCount, platform: post.niche });

          // 3g Python social engine — X/Twitter, LinkedIn, Facebook, Instagram,
          //    TikTok, YouTube, Telegram (runs on OCI runtime server)
          const runtimeUrl = process.env.RUNTIME_API_URL;
          if (runtimeUrl) {
            const videoPath = post.videoPath || post.media_path || null;
            fetch(`${runtimeUrl}/social/distribute`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text:       post.body?.slice(0, 280) || post.title,
                full_text:  post.body || '',
                title:      post.title || '',
                url:        post.canonicalUrl || post.url || '',
                media_path: videoPath,
                platforms:  ['twitter', 'linkedin', 'facebook', 'instagram',
                              'tiktok', 'youtube', 'telegram'],
              }),
              signal: AbortSignal.timeout(30_000),
            })
            .then(r => r.json())
            .then(d => {
              summary.social += d.posted || 0;
              uf.emit('social.python.distributed', d);
              logger.info(`Python social engine: ${d.posted || 0} platforms posted`);
            })
            .catch(err => logger.warn('Python social engine error', { error: err.message }));
          }
        }
      } catch (err) {
        intel.addToDLQ(raw, err.message, 'pipeline');
        summary.errors.push({ stage: 'enrich', post: raw.title?.slice(0,40), msg: err.message });
        state.push('publishErrors', { title: raw.title, error: err.message, ts: new Date().toISOString() }, 100);
      }
    }

    // Stage 4: Periodic maintenance (every 5 cycles)
    if (cycle % 5 === 0) {
      website.publishSitemap().catch(() => {});
      website.publishRSS().catch(() => {});
      seo.runNicheKeywordCycle().catch(() => {});
    }

    // Stage 5: Revenue scaling
    revenue.checkThresholds().catch(() => {});

  } catch (err) {
    logger.error('Pipeline critical error', { error: err.message });
    uf.emit('cycle.error', { stage: 'pipeline', error: err.message });
    summary.errors.push({ stage: 'pipeline', msg: err.message });
  } finally {
    _running = false;
    summary.durationSec = +((Date.now() - start) / 1000).toFixed(1);
    state.set('lastCycle', { ...summary, ts: new Date().toISOString() });
    uf.emit('cycle.complete', summary);
    logger.info(`=== Cycle #${cycle} END — generated:${summary.generated} published:${summary.published} social:${summary.social} (${summary.durationSec}s) ===`);
    if (summary.errors.length > 2) {
      email.sendAlert(`Cycle #${cycle} — ${summary.errors.length} errors`, summary.errors.map(e=>`[${e.stage}] ${e.msg}`).join('\n')).catch(()=>{});
    }
  }
}

// ── Intelligence Cycle ────────────────────────────────────────────────────────
async function runIntelligence() {
  logger.info('Intelligence cycle triggered');
  try {
    const report = await intel.analyze();
    uf.emit('intelligence.complete', { healthScore: report?.healthScore, summary: report?.executiveSummary });
    await intel.drainDLQ();
    if (report?.healthScore < 40) {
      email.sendAlert(`Health Critical: ${report.healthScore}/100`, report.executiveSummary + '\n\n' + (report.criticalIssues||[]).map(i=>i.issue).join('\n')).catch(()=>{});
    }
  } catch (err) { logger.error('Intelligence cycle failed', { error: err.message }); }
}

// ── Scheduler ─────────────────────────────────────────────────────────────────
function reschedule() {
  if (_scanTimer) clearTimeout(_scanTimer);
  const interval = getScanInterval();
  _scanTimer = setTimeout(async () => { await runCycle(); reschedule(); }, interval);
  logger.info(`Next cycle in ${Math.round(interval/60000)}m`);
}

async function start() {
  logger.info('ProfitEngine v5.0 pipeline starting...');
  state.set('startedAt', new Date().toISOString());
  state.set('sessionId', `pe5_${Date.now()}`);

  // Startup tasks (non-blocking)
  website.publishRequiredPages().catch(err => logger.warn('Required pages failed', { error: err.message }));

  // First cycle immediately
  await runCycle();
  reschedule();

  // Intelligence every 6h, first after 30min
  setTimeout(async () => { await runIntelligence(); _intelTimer = setInterval(runIntelligence, 6*60*60_000); }, 30*60_000);

  // Health every 60min, first after 5min
  setTimeout(async () => { await health.runCheck(); _healthTimer = setInterval(() => health.runCheck().catch(()=>{}), 60*60_000); }, 5*60_000);

  // Daily report at 08:00 approx (after 8h, then daily)
  setTimeout(async () => { await revenue.sendDailyReport(); await revenue.analyzeAndOptimize(); _dailyTimer = setInterval(async()=>{ await revenue.sendDailyReport(); await revenue.analyzeAndOptimize(); }, 24*60*60_000); }, 8*60*60_000);

  // POD every 12h
  setTimeout(async () => { await pod.runPODCycle(); _podTimer = setInterval(()=>pod.runPODCycle().catch(()=>{}), 12*60*60_000); }, 12*60*60_000);

  // Start background worker pool
  workers.scheduleRecurring();
  logger.info(`Pipeline active. Scan: ${getScanInterval()/60000}m | Content/run: ${state.get('adaptiveContentPerRun',null)||cfg().contentPerRun}`);
}

function stop() {
  [_scanTimer, _intelTimer, _healthTimer, _dailyTimer, _podTimer].forEach(t => { if (t) clearTimeout(t); if (t) clearInterval(t); });
  logger.info('Pipeline stopped');
}

module.exports = { start, stop, runCycle, runIntelligence };

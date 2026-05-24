'use strict';
/**
 * pipeline/distillation-pipeline.js — ProfitEngine v5.x
 * Unified Data Distillation Pipeline — All 5 Pillars Wired
 * Already Here LLC | alreadyhereillc.com
 *
 * WHAT THIS FILE DOES:
 *   Orchestrates the full data distillation strategy as a single callable
 *   pipeline. Drop-in replacement for the raw llm.generate() pre-processing
 *   pattern. Existing distillation.js + sovereign.js are NOT modified —
 *   this sits on top and calls them.
 *
 * PIPELINE FLOW:
 *
 *   raw input
 *     │
 *     ▼ Pillar 4 pre-process (logic-offloader.js)
 *   [sort / dedupe / math / extract] → return immediately if offloaded (zero tokens)
 *     │
 *     ▼ Pillar 1 semantic compression (semantic-compressor.js)
 *   [HTML strip → chunk → RAG retrieve top-K] → ~70-80% reduction on large docs
 *     │
 *     ▼ Pillar 5 tier routing (tiered-router.js + sovereign.js)
 *   [complexity score → LOW/MID/HIGH tier + model + format]
 *     │
 *     ▼ Pillar 2 prompt engineering
 *   [output constraints + few-shot block + Qwen adapter]
 *     │
 *     ▼ Existing distillation.js
 *   [distillPHPrompt + dedup cache check + budget gate]
 *     │
 *     ▼ Pillar 3 structural serialization (tiered-router.js)
 *   [YAML / compact JSON / pipe-delimited per tier]
 *     │
 *     ▼ LLM call (caller's responsibility)
 *     │
 *     ▼ Pillar 4 post-process (logic-offloader.js)
 *   [cleanResponse → extract JSON/YAML/array as needed]
 *     │
 *     ▼ commitResponse (distillation.js) → cache for future dedup hits
 *
 * USAGE:
 *   const dp = require('./pipeline/distillation-pipeline');
 *
 *   // Full pipeline: returns { prompt, routing, stats, tier, fromCache }
 *   const prep = await dp.prepare(userInput, {
 *     query:         'What are the top procurement opportunities?',
 *     taskType:      'reason',
 *     preSteps:      [{ task: 'dedupe' }, { task: 'truncate', opts: { n: 3000 } }],
 *     examples:      [{ input: 'SAM.gov FY26 IT', output: 'FIT: 9/10' }],
 *     customSchema:  { opportunities: [], fitScore: 0 },
 *     docId:         'procurement-scan',
 *   });
 *
 *   if (prep.fromCache) return prep.cachedResponse;
 *   if (prep.offloaded)  return prep.offloadResult;
 *   if (prep.budgetExceeded) return { error: 'Daily token budget exceeded' };
 *
 *   // Call LLM with prep.prompt, prep.routing.endpoint, prep.routing.model
 *   const rawResponse = await llm.call(prep.prompt, prep.routing);
 *
 *   // Post-process
 *   const response = dp.finalize(rawResponse, prep, { extractJSON: true });
 *   // response.text  → cleaned, parsed
 *   // response.stats → full token/cost audit trail
 */

const distil    = require('../core/distillation');
const sovereign = require('../core/sovereign');
const compressor = require('../core/semantic-compressor');
const router     = require('../core/tiered-router');
const offloader  = require('../core/logic-offloader');

let _logger;
function log() {
  if (!_logger) { try { _logger = require('../core/logger').child('PIPELINE'); } catch { _logger = console; } }
  return _logger;
}

// ── Pipeline stats ─────────────────────────────────────────────────────────────
const _pipelineStats = {
  totalCalls: 0, offloadedCalls: 0, cacheHits: 0, budgetBlocks: 0,
  byTier: { LOW: 0, MID: 0, HIGH: 0 },
  avgReductionPct: 0, totalTokensSaved: 0,
};

// ── prepare() — pre-LLM stage ──────────────────────────────────────────────────

/**
 * prepare(rawInput, opts)
 * Run the full pre-LLM distillation pipeline.
 *
 * @param {string|object} rawInput  - Raw text, object, or array
 * @param {object}        opts
 *   query          {string}   - What the LLM needs to answer (for RAG retrieval)
 *   taskType       {string}   - 'sort'|'summarize'|'reason'|... (see tiered-router)
 *   preSteps       {Array}    - Deterministic pre-processing steps
 *   examples       {Array}    - Few-shot examples [{input, output}]
 *   customSchema   {*}        - Output schema for format constraint
 *   docId          {string}   - Doc ID for semantic store (reuse indexed docs)
 *   noRAG          {boolean}  - Skip semantic compression (for short inputs)
 *   maxInputTokens {number}   - Hard cap before LLM (default: 3000)
 *
 * @returns {object}
 *   prompt, routing, stats, tier, fromCache, cachedResponse,
 *   offloaded, offloadResult, budgetExceeded
 */
async function prepare(rawInput, opts = {}) {
  _pipelineStats.totalCalls++;
  const startMs = Date.now();

  const maxInputTokens = opts.maxInputTokens || parseInt(process.env.MAX_INPUT_TOKENS || '3000', 10);

  // Convert non-string to text
  let inputText = typeof rawInput === 'string'
    ? rawInput
    : router.serializePayload(rawInput, 'MID'); // YAML for objects

  const originalChars = inputText.length;

  // ── Pillar 4: Pre-process deterministic tasks ────────────────────────────
  if (opts.preSteps?.length) {
    const { output, log: preLog } = offloader.preProcess(inputText, opts.preSteps);
    inputText = typeof output === 'string' ? output : router.serializePayload(output, 'MID');
    log().info('Pre-process complete', { steps: preLog.length, chars: inputText.length });
  }

  // ── Pillar 4: Try full offload (zero LLM needed?) ─────────────────────────
  if (opts.taskType) {
    const { result, offloaded } = offloader.tryOffload(opts.taskType, rawInput, opts);
    if (offloaded) {
      _pipelineStats.offloadedCalls++;
      return {
        offloaded: true, offloadResult: result, prompt: null,
        stats: _buildStats(startMs, originalChars, 0, 'LOW'),
      };
    }
  }

  // ── Pillar 1: Semantic compression (RAG) ──────────────────────────────────
  let compressionStats = { reductionPct: 0 };
  if (!opts.noRAG && inputText.length > maxInputTokens * 4) {
    const compressed = await compressor.compress(inputText, opts.query || '', {
      docId: opts.docId,
      topK:  opts.topK || 4,
    });
    inputText       = compressed.text;
    compressionStats = compressed.stats;
  }

  // ── Existing distillation.js: dedup check + prompt minify + budget gate ──
  const distillResult = distil.runDistillation(inputText, { maxTokens: maxInputTokens });

  if (distillResult.fromCache) {
    _pipelineStats.cacheHits++;
    return {
      fromCache: true, cachedResponse: distillResult.output, prompt: null,
      stats: _buildStats(startMs, originalChars, 0, 'CACHE'),
    };
  }

  if (distillResult.budgetExceeded) {
    _pipelineStats.budgetBlocks++;
    return { budgetExceeded: true, prompt: null, stats: _buildStats(startMs, originalChars, 0, 'BLOCKED') };
  }

  let preparedPrompt = distillResult.prompt || inputText;

  // ── Pillar 5: Tier routing ────────────────────────────────────────────────
  const complexity = sovereign.scoreComplexity(preparedPrompt);
  const routing    = router.route(complexity, {
    estimatedTokens: Math.ceil(preparedPrompt.length / 4),
    customSchema:    opts.customSchema,
    examples:        opts.examples,
  });

  _pipelineStats.byTier[routing.tier]++;

  // ── Pillar 2: Prompt engineering — append constraints + few-shot ──────────
  const parts = [preparedPrompt];
  if (routing.fewShotBlock)     parts.push('\n' + routing.fewShotBlock);
  if (routing.outputConstraint) parts.push('\n' + routing.outputConstraint);
  preparedPrompt = parts.join('');

  // ── Pillar 3: Structural serialization for data payloads ─────────────────
  // (already applied above via serializePayload; formatting enforced via outputConstraint)

  const finalTokens = Math.ceil(preparedPrompt.length / 4);
  const saved = distillResult.estimatedTokens
    ? Math.max(0, distillResult.estimatedTokens - finalTokens) : 0;
  _pipelineStats.totalTokensSaved += saved;

  const stats = _buildStats(startMs, originalChars, preparedPrompt.length, routing.tier, compressionStats, saved);
  log().info('Pipeline prepared', { tier: routing.tier, finalTokens, reductionPct: stats.totalReductionPct });

  return {
    prompt:        preparedPrompt,
    routing,
    tier:          routing.tier,
    fromCache:     false,
    offloaded:     false,
    budgetExceeded:false,
    stats,
    _distillResult: distillResult,
  };
}

// ── finalize() — post-LLM stage ───────────────────────────────────────────────

/**
 * finalize(rawLLMResponse, prepResult, opts)
 * Clean the LLM response and commit it to the dedup cache.
 *
 * @param {string} rawLLMResponse
 * @param {object} prepResult       - From prepare()
 * @param {object} opts
 *   extractJSON  {boolean}
 *   extractYAML  {boolean}
 *   asArray      {boolean}
 *   tokensUsed   {number}  - Actual tokens from LLM response header
 *
 * @returns {{ text, parsed, qualityScore, stats }}
 */
function finalize(rawLLMResponse, prepResult = {}, opts = {}) {
  const cleaned = offloader.postProcess(rawLLMResponse, opts);
  const text    = typeof cleaned === 'string' ? cleaned : router.serializePayload(cleaned, 'MID');

  const qualityScore = distil.scoreResponseQuality(text);

  // Commit to dedup cache so future identical prompts return $0.00
  if (prepResult._distillResult?.originalPrompt) {
    const tokensUsed = opts.tokensUsed || Math.ceil(text.length / 4);
    distil.commitResponse(prepResult._distillResult.originalPrompt, text, tokensUsed);
  }

  return {
    text,
    parsed:       typeof cleaned !== 'string' ? cleaned : null,
    qualityScore,
    stats:        { qualityScore, fromCache: false, tokensUsed: opts.tokensUsed || 0 },
  };
}

// ── Stats helpers ──────────────────────────────────────────────────────────────

function _buildStats(startMs, originalChars, finalChars, tier, compressionStats = {}, tokensSaved = 0) {
  const reductionPct = originalChars > 0
    ? Math.round((1 - finalChars / originalChars) * 100) : 0;
  _pipelineStats.avgReductionPct = Math.round(
    (_pipelineStats.avgReductionPct * (_pipelineStats.totalCalls - 1) + reductionPct) / _pipelineStats.totalCalls
  );
  return {
    tier, latencyMs: Date.now() - startMs,
    originalChars, finalChars, tokensSaved,
    totalReductionPct: reductionPct,
    compressionReductionPct: compressionStats.reductionPct || 0,
    distillReductionPct:     Math.max(0, reductionPct - (compressionStats.reductionPct || 0)),
    ...router.getCostStats(),
  };
}

function getPipelineStats() {
  return {
    ..._pipelineStats,
    distillation:    distil.getStats(),
    sovereign:       sovereign.getStatus(),
    compressor:      compressor.getStats(),
    tierRouter:      router.getCostStats(),
    offloader:       offloader.getStats(),
  };
}

function resetDailyStats() {
  distil.resetDailyStats();
  router.resetCostStats();
  _pipelineStats.totalCalls         = 0;
  _pipelineStats.offloadedCalls     = 0;
  _pipelineStats.cacheHits          = 0;
  _pipelineStats.budgetBlocks       = 0;
  _pipelineStats.byTier             = { LOW: 0, MID: 0, HIGH: 0 };
  _pipelineStats.avgReductionPct    = 0;
  _pipelineStats.totalTokensSaved   = 0;
  log().info('Pipeline daily stats reset');
}

module.exports = { prepare, finalize, getPipelineStats, resetDailyStats };

'use strict';
/**
 * core/tiered-router.js — ProfitEngine v5.x
 * Pillars 3 & 5: Tiered Processing Model + Structural Data Optimization
 * Already Here LLC | alreadyhereillc.com
 *
 * EXTENDS sovereign.js arbitrateAgentWorkload():
 *   - Adds explicit Low / Mid / High tiers with cost tracking
 *   - Selects output format (YAML < JSON < Markdown) per tier
 *   - Wraps sovereign complexity score into a named tier
 *
 * TIER MAP:
 *   LOW  (ci ≤ 0.20) → local scripts / zero LLM cost (sort, format, math)
 *   MID  (ci ≤ 0.55) → Groq gemma2-9b (fast, ~$0.0001/1K tok) for summarisation/extraction
 *   HIGH (ci > 0.55) → Sovereign cloud gateway (Groq llama-3.3-70b / fallback chain)
 *
 * STRUCTURAL DATA OPTIMIZATION:
 *   serializePayload(data, tier) → YAML string (MID/LOW) or JSON string (HIGH)
 *   Benchmark: YAML saves ~18-25% tokens vs JSON on typical config objects.
 *
 * INTEGRATION:
 *   const { route, serializePayload } = require('./tiered-router');
 *   const { tier, endpoint, costTier, formatHint } = route(complexity);
 *   const payload = serializePayload(configData, tier);
 */

const sovereign = require('./sovereign');

let _logger;
function log() {
  if (!_logger) { try { _logger = require('./logger').child('TIER-ROUTER'); } catch { _logger = console; } }
  return _logger;
}

// ── Tier thresholds ───────────────────────────────────────────────────────────
const THRESHOLD_LOW  = parseFloat(process.env.TIER_THRESHOLD_LOW  || '0.20');
const THRESHOLD_MID  = parseFloat(process.env.TIER_THRESHOLD_MID  || '0.55');

// Mid tier: smaller/faster model for summarisation, extraction, classification
const MID_MODEL      = process.env.TIER_MID_MODEL || 'gemma2-9b-it';
const MID_ENDPOINT   = process.env.TIER_MID_ENDPOINT || process.env.GROQ_API_URL || 'https://api.groq.com/openai/v1/chat/completions';
const MID_MAX_TOKENS = parseInt(process.env.TIER_MID_MAX_TOKENS || '512', 10);

// ── Cost tracking ─────────────────────────────────────────────────────────────
const _costs = { LOW: 0, MID: 0, HIGH: 0, tokensLOW: 0, tokensMID: 0, tokensHIGH: 0, calls: { LOW: 0, MID: 0, HIGH: 0 } };

function trackCost(tier, tokens = 0) {
  // Approximate costs (USD per 1K tokens, as of 2026)
  const RATE = { LOW: 0, MID: 0.0001, HIGH: 0.0009 };
  _costs[tier]          = (_costs[tier] || 0) + (tokens / 1000) * (RATE[tier] || 0);
  _costs[`tokens${tier}`] += tokens;
  _costs.calls[tier]++;
}

// ── YAML serializer (no external dep) ────────────────────────────────────────
// Produces YAML for scalar/array/object values.
// Avoids heavy braces and quotes that inflate token count.

function _yamlValue(val, indent = 0) {
  const pad = ' '.repeat(indent);
  if (val === null || val === undefined) return 'null';
  if (typeof val === 'boolean') return val ? 'true' : 'false';
  if (typeof val === 'number')  return String(val);
  if (typeof val === 'string') {
    if (/[\n:#{}&*!|>'"%@`]/.test(val) || val.trim() !== val) {
      return `"${val.replace(/"/g, '\\"')}"`;
    }
    return val;
  }
  if (Array.isArray(val)) {
    if (!val.length) return '[]';
    return '\n' + val.map(v => `${pad}- ${_yamlValue(v, indent + 2)}`).join('\n');
  }
  if (typeof val === 'object') {
    const entries = Object.entries(val);
    if (!entries.length) return '{}';
    return '\n' + entries.map(([k, v]) => {
      const vStr = _yamlValue(v, indent + 2);
      return `${pad}${k}: ${vStr.startsWith('\n') ? vStr : vStr}`;
    }).join('\n');
  }
  return String(val);
}

function toYAML(obj) {
  if (typeof obj !== 'object' || obj === null) return String(obj);
  return Object.entries(obj)
    .map(([k, v]) => {
      const vStr = _yamlValue(v, 2);
      return `${k}: ${vStr.startsWith('\n') ? vStr : vStr}`;
    })
    .join('\n');
}

/**
 * serializePayload(data, tier)
 * LOW/MID  → YAML  (~20% token savings vs JSON)
 * HIGH     → JSON  (guaranteed parse-safe for complex reasoning)
 * Pipe-delimited for flat 1D arrays at any tier (cheapest).
 */
function serializePayload(data, tier = 'MID') {
  if (Array.isArray(data) && data.every(v => typeof v !== 'object')) {
    // Flat array → pipe-delimited (fewest tokens)
    return data.join('|');
  }
  if (tier === 'HIGH') {
    return JSON.stringify(data, null, 0); // compact JSON
  }
  try {
    return toYAML(data);
  } catch {
    return JSON.stringify(data, null, 0);
  }
}

/**
 * deserializePayload(text)
 * Detects format and parses back to object.
 * Handles YAML, JSON, pipe-delimited.
 */
function deserializePayload(text) {
  if (!text || typeof text !== 'string') return text;
  const t = text.trim();
  // JSON
  if (t.startsWith('{') || t.startsWith('[')) {
    try { return JSON.parse(t); } catch {}
  }
  // Pipe-delimited (no newlines, single line)
  if (!t.includes('\n') && t.includes('|')) return t.split('|');
  // YAML — basic key:value parser sufficient for our generated YAML
  try {
    const result = {};
    const lines = t.split('\n');
    for (const line of lines) {
      const m = line.match(/^(\s*)([^:\s][^:]*):\s*(.*)?$/);
      if (m) {
        const key = m[2].trim(), val = (m[3] || '').trim();
        result[key] = val === 'true' ? true : val === 'false' ? false : val === 'null' ? null : isNaN(val) ? val : Number(val);
      }
    }
    return Object.keys(result).length ? result : t;
  } catch {
    return t;
  }
}

// ── Format hint per tier ──────────────────────────────────────────────────────
// Injected into system prompt to enforce concise output.

const FORMAT_HINTS = {
  LOW:  '',
  MID:  'Respond in YAML only. No prose, no markdown fences. Concise values.',
  HIGH: 'Respond in JSON only. No prose, no markdown. Compact keys.',
};

// ── Output constraint builder ─────────────────────────────────────────────────
// Pillar 2: Prompt Engineering for Token Efficiency
// Builds the output-constraint suffix appended to every prompt.

function buildOutputConstraint(tier, customSchema = null) {
  const base = FORMAT_HINTS[tier] || FORMAT_HINTS.HIGH;
  if (!customSchema) return base;
  const schemaStr = typeof customSchema === 'string'
    ? customSchema
    : serializePayload(customSchema, tier);
  return `${base}\nOutput schema:\n${schemaStr}`;
}

// ── Few-shot density builder ──────────────────────────────────────────────────
// Pillar 2: 2-3 compact examples instead of paragraphs of instructions.

/**
 * buildFewShot(examples)
 * @param {Array<{input, output}>} examples
 * @returns {string} Compact few-shot block (YAML format, minimal tokens)
 */
function buildFewShot(examples = []) {
  if (!examples.length) return '';
  const lines = examples.slice(0, 3).map((ex, i) =>
    `ex${i + 1}:\n  in: ${_yamlValue(ex.input)}\n  out: ${_yamlValue(ex.output)}`
  );
  return 'examples:\n' + lines.join('\n');
}

// ── Main Router ───────────────────────────────────────────────────────────────

/**
 * route(complexityIndex, opts)
 *
 * @param {number} complexityIndex  - 0.0–1.0 from sovereign.scoreComplexity()
 * @param {object} opts             - { estimatedTokens, customSchema, examples }
 * @returns {object} routing decision
 *   { tier, endpoint, model, maxTokens, temperature, costTier,
 *     formatHint, outputConstraint, fewShotBlock, stopSequences }
 */
function route(complexityIndex, opts = {}) {
  const ci = Math.min(1.0, Math.max(0.0, complexityIndex || 0));

  let tier, endpoint, model, maxTokens, temperature, costTier, stopSequences;

  if (ci <= THRESHOLD_LOW) {
    // LOW — offload to logic-offloader; LLM call only if strictly needed
    tier          = 'LOW';
    endpoint      = 'LOCAL';
    model         = 'none';
    maxTokens     = 128;
    temperature   = 0.0;
    costTier      = 'free';
    stopSequences = ['\n', '```'];
  } else if (ci <= THRESHOLD_MID) {
    // MID — fast small model, summarisation/extraction only
    tier          = 'MID';
    endpoint      = MID_ENDPOINT;
    model         = MID_MODEL;
    maxTokens     = MID_MAX_TOKENS;
    temperature   = 0.1;
    costTier      = 'metered-low';
    stopSequences = ['```', '\n\n\n'];
  } else {
    // HIGH — full sovereign cloud gateway (inherits sovereign.js fallback chain)
    const sovDecision = sovereign.arbitrateAgentWorkload(ci);
    tier          = 'HIGH';
    endpoint      = sovDecision.endpoint;
    model         = process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';
    maxTokens     = sovDecision.max_completion_tokens || 1024;
    temperature   = sovDecision.temperature || 0.1;
    costTier      = 'metered-high';
    stopSequences = sovDecision.stop_sequences || [];
  }

  const formatHint       = FORMAT_HINTS[tier];
  const outputConstraint = buildOutputConstraint(tier, opts.customSchema);
  const fewShotBlock     = opts.examples ? buildFewShot(opts.examples) : '';

  trackCost(tier, opts.estimatedTokens || 0);

  const decision = {
    tier, endpoint, model, maxTokens, temperature,
    costTier, stopSequences, formatHint,
    outputConstraint, fewShotBlock,
    complexityIndex: ci,
  };

  log().info('Tier routed', { tier, ci: ci.toFixed(2), model, costTier });
  return decision;
}

/**
 * routeByTask(taskType, opts)
 * Convenience: route by task type string instead of raw complexity score.
 * Keeps the LLM call sites clean.
 *
 * taskTypes: 'sort'|'format'|'math'    → LOW
 *            'summarize'|'extract'|'classify' → MID
 *            'reason'|'strategy'|'generate'   → HIGH
 */
const TASK_COMPLEXITY = {
  sort: 0.05, format: 0.10, math: 0.15, dedupe: 0.10,
  summarize: 0.35, extract: 0.40, classify: 0.45, translate: 0.45,
  reason: 0.70, strategy: 0.80, generate: 0.75, analyze: 0.65, configure: 0.60,
};

function routeByTask(taskType, opts = {}) {
  const ci = TASK_COMPLEXITY[taskType?.toLowerCase()] ?? 0.60;
  return route(ci, opts);
}

// ── Cost stats (exposed at /api/status.tierRouter) ────────────────────────────
function getCostStats() {
  return {
    ..._costs,
    totalCostUSD: Number((_costs.LOW + _costs.MID + _costs.HIGH).toFixed(6)),
    thresholds:   { LOW: THRESHOLD_LOW, MID: THRESHOLD_MID },
  };
}

function resetCostStats() {
  _costs.LOW = _costs.MID = _costs.HIGH = 0;
  _costs.tokensLOW = _costs.tokensMID = _costs.tokensHIGH = 0;
  _costs.calls.LOW = _costs.calls.MID = _costs.calls.HIGH = 0;
}

module.exports = {
  route, routeByTask,
  serializePayload, deserializePayload,
  buildOutputConstraint, buildFewShot,
  toYAML,
  getCostStats, resetCostStats,
};

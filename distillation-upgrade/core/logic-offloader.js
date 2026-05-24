'use strict';
/**
 * core/logic-offloader.js — ProfitEngine v5.x
 * Pillar 4: Logic Offloading — Deterministic Task Offloading
 * Already Here LLC | alreadyhereillc.com
 *
 * PRINCIPLE: Don't use tokens for things code can do better.
 *   - Math, sorting, deduplication, formatting → run here, zero LLM cost
 *   - Structured extraction (dates, URLs, emails, prices) → regex, zero LLM cost
 *   - Result normalization post-LLM → clean up filler before storing
 *
 * INTEGRATION:
 *   const lo = require('./logic-offloader');
 *
 *   // Pre-LLM: offload what you can
 *   const { result, offloaded } = lo.tryOffload('sort', data);
 *   if (offloaded) { use result directly } else { send to LLM }
 *
 *   // Post-LLM: strip filler from model responses
 *   const clean = lo.cleanResponse(rawLLMResponse);
 *
 * SUPPORTED TASK TYPES:
 *   sort         - sort array of strings/numbers
 *   dedupe       - remove duplicate strings
 *   math         - evaluate safe arithmetic expressions
 *   format_date  - parse and reformat date strings
 *   extract_urls - extract all URLs from text
 *   extract_emails
 *   extract_prices
 *   word_count   - count words/tokens in text
 *   truncate     - truncate text to N tokens
 *   summarize_bullets - convert numbered/bulleted list to YAML array (no LLM)
 *   merge_dedup  - merge two arrays and deduplicate
 */

let _logger;
function log() {
  if (!_logger) { try { _logger = require('./logger').child('OFFLOAD'); } catch { _logger = console; } }
  return _logger;
}

// ── Stats ─────────────────────────────────────────────────────────────────────
const _stats = {
  offloaded: 0, passed: 0, tokenssaved: 0, taskCounts: {}
};

function _track(task, tokensSaved = 0) {
  _stats.offloaded++;
  _stats.tokensaved += tokensSaved;
  _stats.taskCounts[task] = (_stats.taskCounts[task] || 0) + 1;
}

// ── Safe Math evaluator (no eval, no LLM) ────────────────────────────────────
// Supports: + - * / ** % ( ) unary-
// Rejects: anything that isn't numbers, operators, whitespace, parens

const SAFE_MATH_RE = /^[0-9+\-*/().% \t\n^]+$/;

function safeMath(expr) {
  if (!SAFE_MATH_RE.test(String(expr).replace(/\*\*/g, '^'))) return null;
  try {
    // Replace ** with ^ then evaluate with Function
    const clean = String(expr).replace(/\^/g, '**');
    // eslint-disable-next-line no-new-func
    const val = Function(`"use strict"; return (${clean})`)();
    return typeof val === 'number' && isFinite(val) ? val : null;
  } catch { return null; }
}

// ── Regex extractors ──────────────────────────────────────────────────────────
const URL_RE    = /https?:\/\/[^\s"'<>)\]]+/gi;
const EMAIL_RE  = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
const PRICE_RE  = /\$\s?\d+(?:[,]\d{3})*(?:\.\d{1,2})?|\d+(?:[,]\d{3})*(?:\.\d{1,2})?\s?(?:USD|EUR|GBP|CAD|AUD)/gi;
const DATE_RE   = /\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b/gi;

// ── Response filler stripping ─────────────────────────────────────────────────
// Removes common LLM conversational filler from model output.
// Applied post-LLM so stored/forwarded responses are token-lean.

const FILLER_PATTERNS = [
  /^(Sure[,!.]?|Of course[,!.]?|Certainly[,!.]?|Absolutely[,!.]?|Great[,!.]?)\s*/i,
  /^(I('d| would) (be )?happy to( help)?[,!.]?)\s*/i,
  /^(Let me |I will |I'll |I can )/i,
  /\s*Is there anything else I can (help|assist) you with\??\.?\s*$/i,
  /\s*Let me know if you (have|need|want) (any )?(more|additional|further|other).{0,40}\.?\s*$/i,
  /\s*Hope (this|that) (helps?|is helpful|answers?).*\.?\s*$/i,
  /\s*Feel free to ask.*\.?\s*$/i,
  /^\s*Here('s| is) (a |the )?(brief |quick |short )?/i,
];

function cleanResponse(text) {
  if (!text || typeof text !== 'string') return text;
  let t = text.trim();
  for (const re of FILLER_PATTERNS) t = t.replace(re, '');
  return t.trim();
}

// ── Bullet/numbered list → YAML array (no LLM needed) ────────────────────────
function parseBulletList(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const items = lines
    .filter(l => /^[-•*+]|\d+[.)]\s/.test(l))
    .map(l => l.replace(/^[-•*+]\s+|\d+[.)]\s+/, '').trim());
  return items.length ? items : null;
}

// ── Date normalizer ───────────────────────────────────────────────────────────
function normalizeDate(str) {
  const d = new Date(str);
  if (!isNaN(d)) return d.toISOString().slice(0, 10); // YYYY-MM-DD
  return null;
}

// ── Main offload dispatcher ───────────────────────────────────────────────────

/**
 * tryOffload(task, data, opts)
 *
 * @param {string} task  - Task type (see module docstring)
 * @param {*}      data  - Input data
 * @param {object} opts  - { sortKey, order:'asc'|'desc', dateFormat, limit, n }
 * @returns {{ result, offloaded, task, tokensSaved }}
 *   offloaded: true  → use result directly, skip LLM
 *   offloaded: false → pass to LLM (result is undefined)
 */
function tryOffload(task, data, opts = {}) {
  const t = task?.toLowerCase?.();
  let result, offloaded = false, tokensSaved = 0;

  try {
    switch (t) {

      // ─ Sorting ──────────────────────────────────────────────────────────
      case 'sort': {
        if (!Array.isArray(data)) break;
        const key = opts.sortKey;
        const order = opts.order === 'desc' ? -1 : 1;
        result = [...data].sort((a, b) => {
          const av = key ? a[key] : a;
          const bv = key ? b[key] : b;
          if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * order;
          return String(av).localeCompare(String(bv)) * order;
        });
        offloaded = true;
        tokensSaved = Math.ceil(JSON.stringify(data).length / 4);
        break;
      }

      // ─ Deduplication ────────────────────────────────────────────────────
      case 'dedupe': {
        if (!Array.isArray(data)) break;
        const seen = new Set();
        result = data.filter(item => {
          const key = typeof item === 'object' ? JSON.stringify(item) : String(item);
          if (seen.has(key)) return false;
          seen.add(key); return true;
        });
        offloaded = true;
        tokensSaved = Math.ceil((data.length - result.length) * 20);
        break;
      }

      // ─ Math ─────────────────────────────────────────────────────────────
      case 'math': {
        const val = safeMath(data);
        if (val !== null) { result = val; offloaded = true; tokensSaved = 200; }
        break;
      }

      // ─ Date formatting ───────────────────────────────────────────────────
      case 'format_date': {
        const normalized = normalizeDate(data);
        if (normalized) { result = normalized; offloaded = true; tokensSaved = 80; }
        break;
      }

      // ─ URL extraction ────────────────────────────────────────────────────
      case 'extract_urls': {
        const urls = String(data).match(URL_RE) || [];
        result = [...new Set(urls)];
        offloaded = true;
        tokensSaved = Math.ceil(String(data).length / 4) - result.length * 10;
        break;
      }

      // ─ Email extraction ──────────────────────────────────────────────────
      case 'extract_emails': {
        result = [...new Set(String(data).match(EMAIL_RE) || [])];
        offloaded = true; tokensSaved = 150;
        break;
      }

      // ─ Price extraction ──────────────────────────────────────────────────
      case 'extract_prices': {
        result = [...new Set(String(data).match(PRICE_RE) || [])];
        offloaded = true; tokensSaved = 150;
        break;
      }

      // ─ Word/token count ──────────────────────────────────────────────────
      case 'word_count': {
        const text = String(data);
        result = {
          chars:  text.length,
          words:  text.trim().split(/\s+/).filter(Boolean).length,
          tokens: Math.ceil(text.length / 4),
          lines:  text.split('\n').length,
        };
        offloaded = true; tokensSaved = 100;
        break;
      }

      // ─ Truncation ────────────────────────────────────────────────────────
      case 'truncate': {
        const maxTok = opts.n || 512;
        const maxChr = maxTok * 4;
        result = String(data).slice(0, maxChr) + (data.length > maxChr ? '…' : '');
        offloaded = true; tokensSaved = Math.max(0, Math.ceil((data.length - maxChr) / 4));
        break;
      }

      // ─ Bullet list parsing ───────────────────────────────────────────────
      case 'summarize_bullets': {
        const items = parseBulletList(String(data));
        if (items) { result = items; offloaded = true; tokensSaved = 200; }
        break;
      }

      // ─ Merge + dedupe two arrays ─────────────────────────────────────────
      case 'merge_dedup': {
        if (!Array.isArray(data) || !Array.isArray(opts.b)) break;
        const merged = [...data, ...opts.b];
        const seen = new Set();
        result = merged.filter(item => {
          const k = typeof item === 'object' ? JSON.stringify(item) : String(item);
          if (seen.has(k)) return false; seen.add(k); return true;
        });
        offloaded = true; tokensSaved = Math.ceil(JSON.stringify(merged).length / 4);
        break;
      }

      // ─ JSON normalization ────────────────────────────────────────────────
      case 'normalize_json': {
        if (typeof data === 'string') {
          try { result = JSON.parse(data); offloaded = true; tokensSaved = 50; } catch {}
        } else if (typeof data === 'object') {
          result = data; offloaded = true;
        }
        break;
      }

      default:
        _stats.passed++;
        break;
    }

    if (offloaded) {
      _track(t, tokensSaved);
      log().info('Task offloaded', { task: t, tokensSaved });
    }
  } catch (err) {
    log().warn('Offload failed, passing to LLM', { task: t, error: err.message });
    offloaded = false;
    _stats.passed++;
  }

  return { result, offloaded, task: t, tokensSaved };
}

/**
 * preProcess(input, pipelineSteps)
 * Run a sequence of deterministic transformations before the LLM call.
 * Returns the modified input and a log of what was offloaded.
 *
 * Example:
 *   const { output, log } = preProcess(rawData, [
 *     { task: 'dedupe' },
 *     { task: 'sort', opts: { order: 'asc' } },
 *     { task: 'truncate', opts: { n: 500 } },
 *   ]);
 */
function preProcess(input, pipelineSteps = []) {
  let current = input;
  const processLog = [];
  for (const step of pipelineSteps) {
    const { result, offloaded, tokensSaved } = tryOffload(step.task, current, step.opts || {});
    if (offloaded) {
      current = result;
      processLog.push({ task: step.task, tokensSaved, status: 'offloaded' });
    } else {
      processLog.push({ task: step.task, tokensSaved: 0, status: 'passed' });
    }
  }
  return { output: current, log: processLog };
}

/**
 * postProcess(llmResponse, opts)
 * Clean and normalize LLM response before storing or forwarding.
 * Always runs — zero LLM cost.
 */
function postProcess(llmResponse, opts = {}) {
  let text = cleanResponse(llmResponse || '');
  if (opts.extractJSON) {
    const match = text.match(/\{[\s\S]*\}/);
    if (match) { try { return JSON.parse(match[0]); } catch {} }
  }
  if (opts.extractYAML) {
    // Already YAML → try to parse key:value block
    const lines = text.split('\n').filter(l => /^\s*\S+:/.test(l));
    if (lines.length) text = lines.join('\n');
  }
  if (opts.asArray) {
    const arr = parseBulletList(text);
    if (arr) return arr;
  }
  return text;
}

function getStats() { return { ..._stats }; }

module.exports = {
  tryOffload, preProcess, postProcess,
  cleanResponse, safeMath, parseBulletList, normalizeDate,
  getStats,
};

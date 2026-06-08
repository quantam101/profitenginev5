'use strict';
/**
 * core/llm/index.js — ProfitEngine v5.0
 * Enterprise LLM orchestrator.
 * - Groq → OpenRouter → Gemini fallback chain
 * - Dual signature: (prompt, system, maxTokens) OR (prompt, {tier,system,maxTokens})
 * - Per-provider circuit breaker with exponential backoff
 * - Token budget with daily hard cap enforcement
 * - Request dedup via prompt hash
 * - Full telemetry emission
 */
const axios   = require('axios');
const crypto  = require('crypto');
const logger  = require('../logger').child('LLM');
const state   = require('../state');

const DEDUP_CACHE = new Map(); // hash → { value, ts }
const DEDUP_TTL   = 60_000;   // 1 min
const CB = {};

// ── Circuit Breaker ───────────────────────────────────────────────────────────
function cb(name) { if (!CB[name]) CB[name] = { f: 0, open: 0 }; return CB[name]; }
function trip(name) {
  const b = cb(name); b.f++;
  if (b.f >= 3) { b.open = Date.now() + Math.min(300_000, 30_000 * b.f); }
}
function close_(name) { CB[name] = { f: 0, open: 0 }; }
function isOpen(name) { return cb(name).open > Date.now(); }

// ── Token Budget ──────────────────────────────────────────────────────────────
let _tokens = 0;
let _tokenDay = null;

function checkBudget(needed = 500) {
  const day = new Date().toISOString().slice(0, 10);
  if (_tokenDay !== day) { _tokens = 0; _tokenDay = day; }
  const limit = parseInt(process.env.DAILY_TOKEN_LIMIT || '500000', 10);
  if (_tokens + needed > limit) throw new Error(`[LLM] Daily token budget exceeded (${_tokens}/${limit})`);
}

function trackTokens(provider, p, c) {
  _tokens += p + c;
  const key = `tokens_${new Date().toISOString().slice(0, 10)}`;
  const d   = state.get(key, { total: 0, byProvider: {} });
  d.total += p + c;
  d.byProvider[provider] = (d.byProvider[provider] || 0) + p + c;
  state.set(key, d);
}

// ── Request Dedup ─────────────────────────────────────────────────────────────
function dedupKey(prompt, system) {
  return crypto.createHash('md5').update((system || '') + prompt).digest('hex');
}
function dedupGet(key) {
  const e = DEDUP_CACHE.get(key);
  if (e && Date.now() - e.ts < DEDUP_TTL) return e.value;
  DEDUP_CACHE.delete(key);
  return null;
}
function dedupSet(key, value) {
  DEDUP_CACHE.set(key, { value, ts: Date.now() });
  if (DEDUP_CACHE.size > 500) {
    const oldest = [...DEDUP_CACHE.entries()].sort((a, b) => a[1].ts - b[1].ts)[0];
    DEDUP_CACHE.delete(oldest[0]);
  }
}

// ── Provider Calls ────────────────────────────────────────────────────────────
async function _groq(prompt, system, model, maxTokens) {
  const key = process.env.GROQ_API_KEY;
  if (!key || isOpen('groq')) throw new Error('groq:unavailable');
  const msgs = system
    ? [{ role: 'system', content: system }, { role: 'user', content: prompt }]
    : [{ role: 'user', content: prompt }];
  try {
    const res = await axios.post(
      'https://api.groq.com/openai/v1/chat/completions',
      { model, messages: msgs, max_tokens: maxTokens, temperature: 0.7 },
      { headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' }, timeout: 45_000 }
    );
    const u = res.data.usage || {};
    trackTokens('groq', u.prompt_tokens || 0, u.completion_tokens || 0);
    close_('groq');
    return res.data.choices[0].message.content.trim();
  } catch (e) { trip('groq'); throw e; }
}

async function _openrouter(prompt, system, model, maxTokens) {
  const key = process.env.OPENROUTER_API_KEY;
  if (!key || isOpen('openrouter')) throw new Error('openrouter:unavailable');
  const msgs = system
    ? [{ role: 'system', content: system }, { role: 'user', content: prompt }]
    : [{ role: 'user', content: prompt }];
  try {
    const res = await axios.post(
      'https://openrouter.ai/api/v1/chat/completions',
      { model, messages: msgs, max_tokens: maxTokens },
      {
        headers: {
          Authorization: `Bearer ${key}`, 'Content-Type': 'application/json',
          'HTTP-Referer': 'https://alreadyherellc.com', 'X-Title': 'ProfitEngine',
        },
        timeout: 60_000,
      }
    );
    const u = res.data.usage || {};
    trackTokens('openrouter', u.prompt_tokens || 0, u.completion_tokens || 0);
    close_('openrouter');
    return res.data.choices[0].message.content.trim();
  } catch (e) { trip('openrouter'); throw e; }
}

async function _gemini(prompt, system, maxTokens) {
  const key = process.env.GEMINI_API_KEY;
  if (!key || isOpen('gemini')) throw new Error('gemini:unavailable');
  const contents = system
    ? [{ role: 'user', parts: [{ text: `[System]: ${system}` }] }, { role: 'user', parts: [{ text: prompt }] }]
    : [{ role: 'user', parts: [{ text: prompt }] }];
  try {
    const res = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`,
      { contents, generationConfig: { maxOutputTokens: maxTokens, temperature: 0.7 } },
      { timeout: 60_000 }
    );
    trackTokens('gemini', 0, 0);
    close_('gemini');
    return (res.data.candidates?.[0]?.content?.parts?.[0]?.text || '').trim();
  } catch (e) { trip('gemini'); throw e; }
}

// ── Tier Routing ──────────────────────────────────────────────────────────────
async function callFast(prompt, system = null, maxTokens = 600) {
  const errs = [];
  try { return await _groq(prompt, system, 'gemma2-9b-it', maxTokens); } catch (e) { errs.push(e.message); }
  try { return await _openrouter(prompt, system, 'google/gemma-2-9b-it', maxTokens); } catch (e) { errs.push(e.message); }
  try { return await _gemini(prompt, system, maxTokens); } catch (e) { errs.push(e.message); }
  throw new Error(`[LLM] All fast providers failed: ${errs.join(' | ')}`);
}

async function callFull(prompt, system = null, maxTokens = 1500) {
  const errs = [];
  try { return await _groq(prompt, system, 'llama-3.3-70b-versatile', maxTokens); } catch (e) { errs.push(e.message); }
  try { return await _openrouter(prompt, system, 'meta-llama/llama-3.3-70b-instruct', maxTokens); } catch (e) { errs.push(e.message); }
  try { return await _gemini(prompt, system, maxTokens); } catch (e) { errs.push(e.message); }
  throw new Error(`[LLM] All full providers failed: ${errs.join(' | ')}`);
}

// ── Public API ────────────────────────────────────────────────────────────────
// Accepts: generate(prompt, system?, maxTokens?) OR generate(prompt, {tier,system,maxTokens})
async function generate(prompt, systemOrOpts = null, maxTokens = 1500) {
  let system = null, tokens = maxTokens, fast = false;
  if (systemOrOpts && typeof systemOrOpts === 'object' && !Array.isArray(systemOrOpts)) {
    system = systemOrOpts.system || null;
    tokens = systemOrOpts.maxTokens || 1500;
    fast   = systemOrOpts.tier === 1;
  } else { system = systemOrOpts; tokens = maxTokens; }
  checkBudget(tokens);
  const dk = dedupKey(prompt, system);
  const hit = dedupGet(dk);
  if (hit) return hit;
  const result = await (fast ? callFast : callFull)(prompt, system, tokens);
  dedupSet(dk, result);
  return result;
}

// Accepts: generateJSON(prompt, useFast?) OR generateJSON(prompt, {tier,maxTokens})
async function generateJSON(prompt, useFastOrOpts = false) {
  let fast = false, maxTokens = 1000;
  if (useFastOrOpts && typeof useFastOrOpts === 'object') {
    fast = useFastOrOpts.tier === 1; maxTokens = useFastOrOpts.maxTokens || 1000;
  } else { fast = !!useFastOrOpts; }
  checkBudget(maxTokens);
  const sys = 'Respond ONLY with valid JSON. No markdown, no backticks, no preamble, no trailing text.';
  const raw = fast ? await callFast(prompt, sys, maxTokens) : await callFull(prompt, sys, maxTokens);
  const clean = raw.replace(/```json|```/gi, '').trim();
  try { return JSON.parse(clean); } catch {
    const m = clean.match(/(\[[\s\S]*\]|\{[\s\S]*\})/);
    if (m) { try { return JSON.parse(m[1]); } catch {} }
    throw new Error(`[LLM] Invalid JSON: ${clean.slice(0, 200)}`);
  }
}

function todayTokens()       { return state.get(`tokens_${new Date().toISOString().slice(0, 10)}`, { total: 0, byProvider: {} }); }
function tokensUsedToday()   { return _tokens; }
function tokenBudgetRemaining() { const lim = parseInt(process.env.DAILY_TOKEN_LIMIT || '500000', 10); return Math.max(0, lim - _tokens); }
function circuitStatus()     { return Object.entries(CB).map(([n, b]) => ({ provider: n, open: b.open > Date.now(), failures: b.f })); }
function breakerStatus()     { return circuitStatus(); }
function resetBreakers()     { for (const k of Object.keys(CB)) delete CB[k]; _tokens = 0; }

module.exports = { generate, generateJSON, callFast, callFull, todayTokens, tokensUsedToday, tokenBudgetRemaining, circuitStatus, breakerStatus, resetBreakers };

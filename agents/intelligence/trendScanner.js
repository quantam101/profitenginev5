'use strict';
/**
 * agents/intelligence/trendScanner.js — ProfitEngine v5.0
 * Google Trends RSS + Reddit hot (authenticated) + DDG news.
 * AI monetization scoring with niche-fit and trend velocity.
 * Tier 0 fetch + compress. Tier 2 scoring. 15m cache.
 */
const axios   = require('axios');
const xml2js  = require('xml2js');
const crypto  = require('crypto');
const llm     = require('../../core/llm');
const logger  = require('../../core/logger').child('TRENDS');
const state   = require('../../core/state');
const cache   = require('../../core/cache').ns('trends');
const cfg     = require('../../core/config').get;

const SLEEP = ms => new Promise(r => setTimeout(r, ms));

// ── Source: Google Trends ─────────────────────────────────────────────────────
async function fetchGoogleTrends() {
  try {
    const res = await axios.get('https://trends.google.com/trends/trendingsearches/daily/rss?geo=US', {
      timeout: 12_000,
      headers: { 'User-Agent': `ProfitEngine/5.0 by ${cfg().contactEmail}` },
    });
    const parsed = await xml2js.parseStringPromise(res.data, { explicitArray: false });
    const items  = parsed?.rss?.channel?.item || [];
    return (Array.isArray(items) ? items : [items]).slice(0, 20).map(item => ({
      title:   item.title || '',
      source:  'google_trends',
      traffic: parseInt((item['ht:approx_traffic'] || '0').replace(/[^0-9]/g, ''), 10) || 0,
    })).filter(t => t.title);
  } catch (err) {
    logger.warn('Google Trends failed', { error: err.message });
    return [];
  }
}

// ── Source: Reddit (unauthenticated safe endpoint) ────────────────────────────
async function fetchRedditTrends() {
  const NICHE_MAP = {
    'passive income':      'passive_income',
    'ai tools':            'artificial',
    'side hustle':         'sidehustle',
    'print on demand':     'printondemand',
    'affiliate marketing': 'affiliatemarketing',
    'blogging':            'blogging',
  };
  const results = [];
  for (const niche of cfg().targetNiches.slice(0, 4)) {
    const sub = NICHE_MAP[niche] || niche.replace(/\s+/g, '_');
    try {
      const res = await axios.get(`https://www.reddit.com/r/${sub}/hot.json?limit=5`, {
        headers: { 'User-Agent': `ProfitEngine/5.0 by ${cfg().contactEmail}` },
        timeout: 10_000,
      });
      (res.data?.data?.children || []).forEach(p => {
        if (p.data.score > 30) results.push({ title: p.data.title, source: 'reddit', niche, score: p.data.score });
      });
      await SLEEP(700);
    } catch { /* continue */ }
  }
  return results;
}

// ── Source: DDG News ──────────────────────────────────────────────────────────
async function fetchDDGNews() {
  const results = [];
  for (const niche of cfg().targetNiches.slice(0, 3)) {
    try {
      const res = await axios.get(`https://duckduckgo.com/news.js?q=${encodeURIComponent(niche + ' 2026')}&kl=us-en&df=d`, {
        headers: { 'User-Agent': `ProfitEngine/5.0 by ${cfg().contactEmail}` },
        timeout: 8_000,
      });
      const items = res.data?.results || [];
      items.slice(0, 5).forEach(item => {
        results.push({ title: item.title, source: 'ddg_news', niche, url: item.url });
      });
    } catch { /* continue */ }
  }
  return results;
}

// ── Tier 0: dedup + compress ──────────────────────────────────────────────────
function compress(trends) {
  return trends.map(t => `${t.title}|${t.source}|${t.niche || ''}|${t.score || t.traffic || 0}`).join('\n');
}
function dedup(trends) {
  const seen = new Set();
  return trends.filter(t => { const k = t.title.toLowerCase().slice(0, 60); return seen.has(k) ? false : (seen.add(k), true); });
}

// ── Tier 2: AI scoring ────────────────────────────────────────────────────────
async function scoreTrends(raw) {
  if (!raw.length) return [];
  const processed = new Set(state.get('trendsProcessed', []));
  const fresh = raw.filter(t => !processed.has(t.title.toLowerCase().slice(0, 60)));
  if (!fresh.length) return [];

  const override = state.get('prompt:trendScoring', null);
  const prompt = override || `Monetization strategist for ${cfg().businessName}.
Active niches: ${cfg().targetNiches.join(', ')}.
Affiliate products: ${cfg().affiliateProducts.join(', ')}.

Trending topics:
${compress(fresh.slice(0, 25))}

Return TOP 6 as JSON array (only score >= 65):
[{ "rank":1, "title":"", "niche":"", "monetizationScore":0-100, "suggestedAngle":"",
   "affiliateProducts":[], "keywords":[], "contentType":"", "trendVelocity":"rising|stable|declining" }]`;

  try {
    const scored = await llm.generateJSON(prompt);
    if (!Array.isArray(scored)) return [];
    // Mark as processed
    const prev = state.get('trendsProcessed', []);
    state.set('trendsProcessed', [...prev, ...scored.map(t => t.title.toLowerCase().slice(0, 60))].slice(-500));
    return scored;
  } catch (err) {
    logger.warn('Scoring failed', { error: err.message });
    return [];
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function scan() {
  const cached = cache.get('latest');
  if (cached) { logger.debug('Trends cache hit'); return cached; }

  logger.info('Scanning trends from all sources...');
  const [g, r, d] = await Promise.allSettled([fetchGoogleTrends(), fetchRedditTrends(), fetchDDGNews()]);
  const raw = dedup([
    ...(g.status === 'fulfilled' ? g.value : []),
    ...(r.status === 'fulfilled' ? r.value : []),
    ...(d.status === 'fulfilled' ? d.value : []),
  ]);
  logger.info(`${raw.length} raw trends collected`);

  const scored = await scoreTrends(raw);
  logger.info(`${scored.length} monetizable trends scored`);

  state.set('latestTrends', scored);
  state.set('lastTrendScan', new Date().toISOString());
  state.increment('totalTrends', raw.length);

  cache.set('latest', scored, cfg().scanIntervalMin * 60);
  return scored;
}

module.exports = { scan, fetchGoogleTrends, fetchRedditTrends, fetchDDGNews };

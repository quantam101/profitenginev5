'use strict';
/**
 * publishers/blog/index.js — ProfitEngine v5.0
 * Blog platform orchestrator. UCB1 multi-arm bandit ordering.
 * Daily cap enforcement. Per-platform stats. Blog only.
 */
const logger   = require('../../core/logger').child('PUBLISHER');
const state    = require('../../core/state');
const cfg      = require('../../core/config').get;
const devto    = require('./devto');
const hashnode = require('./hashnode');
const medium   = require('./medium');

const PLATFORMS = [
  { name: 'devto',    mod: devto,    key: 'devtoApiKey'    },
  { name: 'hashnode', mod: hashnode, key: 'hashnodeApiKey' },
  { name: 'medium',   mod: medium,   key: 'mediumApiKey'   },
];

function todayKey() { return `posts_today_${new Date().toISOString().slice(0,10)}`; }
function getRate(p) { const s = state.get(`pstats_${p}`, {s:0,f:0}); const t = s.s+s.f; return t ? s.s/t : 0.5; }
function recordResult(p, ok) { const k = `pstats_${p}`; const s = state.get(k,{s:0,f:0}); ok ? s.s++ : s.f++; state.set(k,s); }

async function publish(post) {
  if (!post?.title || !post?.body) return { published: 0, platforms: [] };
  const today = state.get(todayKey(), 0);
  if (today >= cfg().maxPostsPerDay) return { published: 0, capped: true, platforms: [] };

  const enabled = PLATFORMS.filter(p => cfg()[p.key]);
  if (!enabled.length) { logger.warn('No blog platforms configured'); return { published: 0, platforms: [] }; }

  const total = state.get('totalPublished', 1);
  const ranked = enabled.map(p => {
    const n = state.get(`pstats_${p.name}`, {s:0,f:0}); const trials = n.s+n.f||1;
    return { ...p, ucb: getRate(p.name) + Math.sqrt(2 * Math.log(total) / trials) };
  }).sort((a,b) => b.ucb - a.ucb);

  const results = await Promise.allSettled(ranked.map(p => p.mod.publish(post)));
  const succeeded = [];
  results.forEach((r, i) => {
    const ok = r.status === 'fulfilled' && r.value;
    recordResult(ranked[i].name, !!ok);
    if (ok) succeeded.push({ platform: ranked[i].name, url: r.value });
  });

  if (succeeded.length) {
    state.increment(todayKey());
    state.increment('totalPublished');
    state.push('publishLog', { title: post.title, platforms: succeeded.map(s=>s.platform), urls: succeeded.map(s=>s.url), ts: new Date().toISOString() }, 200);
    logger.info(`"${post.title.slice(0,50)}" -> ${succeeded.map(s=>s.platform).join(', ')}`);
  }
  return { published: succeeded.length, platforms: succeeded };
}

function platformStats() {
  return PLATFORMS.map(p => ({
    name: p.name, enabled: !!cfg()[p.key],
    successRate: Math.round(getRate(p.name)*100)+'%',
    ...state.get(`pstats_${p.name}`, {s:0,f:0}),
  }));
}
module.exports = { publish, platformStats };

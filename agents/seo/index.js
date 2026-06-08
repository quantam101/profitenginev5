'use strict';
/**
 * agents/seo/index.js — ProfitEngine v5.0
 * Enterprise SEO: keyword research, A/B title testing, meta optimization,
 * schema markup injection, internal linking strategy.
 */
const axios   = require('axios');
const crypto  = require('crypto');
const llm     = require('../../core/llm');
const logger  = require('../../core/logger').child('SEO');
const state   = require('../../core/state');
const cache   = require('../../core/cache').ns('seo');
const cfg     = require('../../core/config').get;

const POWER_WORDS = ['best','top','ultimate','proven','easy','free','fast','boost','secret','complete','guide','how to','maximize','increase','step-by-step','beginner','advanced','professional'];

function hash(str) { return crypto.createHash('md5').update(str).digest('hex').slice(0,12); }

async function fetchSuggestions(query) {
  const [ddg, google] = await Promise.allSettled([
    axios.get('https://duckduckgo.com/ac/', { params: { q: query, type: 'list' }, timeout: 8000, headers: { 'User-Agent': 'ProfitEngine/5.0' } }),
    axios.get('https://suggestqueries.google.com/complete/search', { params: { client: 'firefox', q: query }, timeout: 8000 }),
  ]);
  const d = ddg.status === 'fulfilled' ? (ddg.value.data?.[1] || ddg.value.data?.map?.(x => x.phrase) || []) : [];
  const g = google.status === 'fulfilled' ? (google.value.data?.[1] || []) : [];
  return [...new Set([...d, ...g].filter(Boolean).slice(0, 20))];
}

async function researchKeywords(topic) {
  const key = `kw_${hash(topic)}`;
  const hit = cache.get(key);
  if (hit) return hit;

  const raw = await fetchSuggestions(topic).catch(() => []);
  const override = state.get('prompt:seoKeywords', null);
  const prompt = override || `SEO strategist. Topic: "${topic}". Niche: ${cfg().targetNiches.join(', ')}.
Suggestions: ${raw.join(', ')}.
Return JSON: { primary:string, secondary:string[], longTail:string[], lsi:string[], metaDescription:string, h1:string }
Focus on buyer intent, search volume potential, affiliate conversion.`;

  try {
    const result = await llm.generateJSON(prompt, true);
    cache.set(key, result, 6 * 3600);
    return result;
  } catch {
    const fallback = { primary: topic, secondary: raw.slice(0,5), longTail: [], lsi: [], metaDescription: topic, h1: topic };
    cache.set(key, fallback, 3600);
    return fallback;
  }
}

async function runABTitleTest(post) {
  if (!post?.title) return post;
  const key = `ab_${hash(post.title)}`;
  const hit = cache.get(key);
  if (hit?.winner) return { ...post, title: hit.winner, abTested: true };

  const prompt = `Generate 4 alternative SEO-optimized titles for:
Original: "${post.title}" | Niche: ${post.niche || 'general'}
Vary formats: curiosity gap, how-to, listicle, benefit-driven.
Return JSON array of 4 title strings only.`;

  try {
    const variants = await llm.generateJSON(prompt, true);
    if (!Array.isArray(variants) || !variants.length) return post;
    const all = [post.title, ...variants.filter(t => typeof t === 'string')];
    const scored = all.map(t => ({ title: t, score: POWER_WORDS.filter(w => t.toLowerCase().includes(w)).length }));
    const winner = scored.sort((a,b) => b.score - a.score)[0].title;
    cache.set(key, { winner, variants }, 48 * 3600);
    logger.info(`A/B winner: "${winner.slice(0,60)}"`);
    return { ...post, title: winner, abTested: true };
  } catch { return post; }
}

function injectSchemaMarkup(post) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.metaDescription || post.title,
    datePublished: post.generatedAt || new Date().toISOString(),
    author: { '@type': 'Organization', name: cfg().businessName, url: `https://${cfg().siteDomain}` },
    publisher: { '@type': 'Organization', name: cfg().businessName },
    keywords: (post.keywords || []).join(', '),
    url: `https://${cfg().siteDomain}/${post.slug || ''}`,
  };
  const tag = `\n<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`;
  return { ...post, schemaMarkup: tag, schemaInjected: true };
}

async function optimizePost(post) {
  if (!post?.title || !post?.body) return post;
  const kw = await researchKeywords(post.title).catch(() => ({ primary: post.title, secondary: [], longTail: [], lsi: [], metaDescription: post.title }));
  let body = post.body;
  if (kw.primary && !body.toLowerCase().includes(kw.primary.toLowerCase())) {
    body = body.replace(/^(#{1,3} .+)/m, `$1\n\n${kw.primary} is one of the fastest-growing opportunities in ${post.niche || 'this niche'}.`);
  }
  const enriched = {
    ...post,
    body,
    keywords:        [kw.primary, ...(kw.secondary || [])].filter(Boolean),
    lsiKeywords:     kw.lsi || [],
    metaDescription: (kw.metaDescription || post.title).slice(0, 160),
    h1:              kw.h1 || post.title,
    seoOptimized:    true,
  };
  return injectSchemaMarkup(enriched);
}

async function runNicheKeywordCycle() {
  logger.info('Running niche keyword research cycle...');
  const results = [];
  for (const niche of cfg().targetNiches.slice(0, 4)) {
    try {
      const kw = await researchKeywords(niche);
      results.push({ niche, ...kw });
      await new Promise(r => setTimeout(r, 1000));
    } catch { /* continue */ }
  }
  state.set('latestKeywords', results);
  state.set('lastSEOCycle', new Date().toISOString());
  logger.info(`Niche keyword cycle complete: ${results.length} niches`);
  return results;
}

module.exports = { researchKeywords, runABTitleTest, optimizePost, injectSchemaMarkup, runNicheKeywordCycle };

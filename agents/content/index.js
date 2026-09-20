'use strict';
/**
 * agents/content/index.js — ProfitEngine v5.0
 * Enterprise content generation.
 * Self-modifying prompts via intelligence agent.
 * Hash-based dedup. Quality gate (word count, coherence score).
 * Tier 2 for blog posts. Tier 1 for captions/merch.
 */
const crypto  = require('crypto');
const llm     = require('../../core/llm');
const logger  = require('../../core/logger').child('CONTENT');
const state   = require('../../core/state');
const cache   = require('../../core/cache').ns('content');
const cfg     = require('../../core/config').get;

const CONTENT_TYPES = ['how-to guide', 'listicle', 'case study', 'product review', 'comparison post', 'ultimate guide'];

function titleHash(title) { return crypto.createHash('md5').update(title).digest('hex').slice(0, 12); }

function pickContentType(trend) {
  const perf  = state.get('contentTypePerf', {});
  const override = state.get('prompt:contentType');
  if (override) return override;
  return trend.contentType || CONTENT_TYPES.reduce((a, b) => (perf[a] || 0) >= (perf[b] || 0) ? a : b);
}

function buildPrompt(trend, contentType) {
  const override = state.get('prompt:contentGen', null);
  const basePrompt = override || `Write a comprehensive ${contentType} blog post optimized for SEO, reader engagement, and affiliate revenue.

Topic: "${trend.title}"
Niche: ${trend.niche || cfg().targetNiches[0]}
Angle: ${trend.suggestedAngle || 'practical guide for beginners'}
Target keywords: ${(trend.keywords || []).slice(0,6).join(', ')}
Affiliate products to naturally mention: ${(trend.affiliateProducts || cfg().affiliateProducts.slice(0,3)).join(', ')}
Trend velocity: ${trend.trendVelocity || 'rising'}

Requirements:
- ${Math.max(cfg().minWordCount, 1200)}-${Math.max(cfg().maxWordCount, 1800)} useful words; no filler
- Compelling, accurate H1 title (different from topic if needed)
- At least 5 substantive H2/H3 sections
- Natural affiliate mentions with [AMAZON_LINK] placeholder only when relevant
- Direct answer/value proposition in the opening; avoid generic scene-setting
- Expert-level insights, concrete workflows, examples, trade-offs, and failure modes
- For current/year-based/product/pricing/feature claims: never invent exact numbers or capabilities
- For current/year-based roundups: include at least 2 authoritative primary-source markdown links plus a Sources section
- Never claim FAQ schema creates People Also Ask placement or FAQ rich-result gains
- Recommend descriptive contextual alt text, never keyword stuffing
- Clearly distinguish free features from premium features
- Never guarantee rankings, traffic, revenue, or SERP gains
- Clear action steps in each section
- Evidence-based takeaway at end

Frontmatter required:
---
title: [compelling SEO title]
description: [150-char meta description]
tags: [comma list]
date: ${new Date().toISOString().slice(0,10)}
niche: ${trend.niche || cfg().targetNiches[0]}
---`;
  return basePrompt;
}

async function qualityGate(content, title) {
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;
  const min = Math.max(cfg().minWordCount, 1000);
  const h2Count = (content.match(/^##\s+\S/gm) || []).length;
  const externalLinks = (content.match(/\[[^\]]+\]\(https?:\/\/[^)]+\)/g) || []).length;
  const currentRoundup = /\b(20\d{2}|best|top|review|comparison|\bvs\b)\b/i.test(title || '');
  const stalePatterns = [
    /tinypng[\s\S]{0,80}\b500\b[\s\S]{0,40}(compress|image)[\s\S]{0,30}(month|monthly)/i,
    /yoast[\s\S]{0,120}(free|free version)[\s\S]{0,160}internal[- ]link(ing)? suggestion/i,
    /faq schema[\s\S]{0,160}(people also ask|rich result|rich snippet|surface|boost)/i,
    /keyword[- ]rich alt text/i,
    /\bguarantee(d|s)?\s+(rank|ranking|traffic|results)\b/i,
  ];
  const placeholders = /(\[(insert|placeholder|todo|tbd|edit)[^\]]*\]|lorem ipsum|coming soon|example\.com)/i;

  if (wordCount < min) {
    logger.warn(`Quality gate: ${title.slice(0,40)} — word count ${wordCount} < ${min}`);
    return false;
  }
  if (h2Count < 5) {
    logger.warn(`Quality gate: insufficient H2 depth (${h2Count} < 5)`);
    return false;
  }
  if (placeholders.test(content)) {
    logger.warn('Quality gate: unresolved placeholder/filler detected');
    return false;
  }
  if (stalePatterns.some((pattern) => pattern.test(content))) {
    logger.warn('Quality gate: stale or misleading SEO claim detected');
    return false;
  }
  if (currentRoundup && externalLinks < 2) {
    logger.warn(`Quality gate: current roundup has only ${externalLinks} reference links`);
    return false;
  }
  return true;
}

async function generatePost(trend) {
  const hash = titleHash(trend.title);
  const cacheKey = `post_${hash}`;
  if (cache.get(cacheKey)) {
    logger.debug(`Duplicate skipped: ${trend.title.slice(0,40)}`);
    return null;
  }

  const contentType = pickContentType(trend);
  logger.info(`Generating ${contentType}: "${trend.title.slice(0,50)}"`);

  let content;
  try {
    content = await llm.generate(buildPrompt(trend, contentType), null, 1800);
  } catch (err) {
    logger.error(`Generation failed: ${err.message}`);
    throw err;
  }

  const passes = await qualityGate(content, trend.title);
  if (!passes) {
    // Retry once with explicit word count reminder
    try {
      content = await llm.generate(buildPrompt(trend, contentType) + '\n\nCRITICAL: The prior draft failed the publication gate. Produce at least 1,200 useful words, 5+ H2 sections, remove placeholders/stale SEO claims, and add 2+ primary-source links for any current/year-based roundup.', null, 2600);
    } catch { throw new Error('Quality gate failed after retry'); }
  }

  const slug = trend.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const post = {
    id:          `post_${Date.now()}_${hash}`,
    slug,
    title:       trend.title,
    contentType,
    niche:       trend.niche,
    keywords:    trend.keywords || [],
    body:        content,
    wordCount:   content.split(/\s+/).length,
    trend,
    generatedAt: new Date().toISOString(),
    published:   false,
  };

  cache.set(cacheKey, true, 24 * 3600);
  state.increment('totalGenerated');
  state.push('generatedPosts', { id: post.id, title: post.title, niche: post.niche, ts: post.generatedAt }, 100);
  return post;
}

async function generateBatch(trends) {
  const contentPerRun = state.get('adaptiveContentPerRun', null) || cfg().contentPerRun;
  const results = [];
  for (const trend of trends.slice(0, contentPerRun)) {
    try {
      const post = await generatePost(trend);
      if (post) results.push(post);
    } catch (err) {
      logger.error(`Batch failure: ${trend.title.slice(0,40)} — ${err.message}`);
    }
  }
  logger.info(`Batch complete: ${results.length}/${trends.slice(0, contentPerRun).length} posts generated`);
  return results;
}

async function generateMerchPrompt(niche) {
  const prompt = `Generate 3 print-on-demand product design briefs for the "${niche}" niche.
Each: product type, design concept, target audience (age/interest), color palette (hex codes), tagline, estimated price point.
Return JSON: [{ productType, designConcept, targetAudience, colorPalette, tagline, pricePoint }]`;
  try { return await llm.generateJSON(prompt, true); } catch { return []; }
}

async function generateSocialCaption(post, platform) {
  const cacheKey = `caption_${platform}_${titleHash(post.title)}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const limits = { mastodon: 490, reddit: 300, pinterest: 500 };
  const limit  = limits[platform] || 350;
  const override = state.get('prompt:socialCaption', null);
  const prompt = override || `Write a ${platform} post (max ${limit} chars) for: "${post.title}"
URL: https://${cfg().siteDomain}/${post.slug || ''}
Niche: ${post.niche || cfg().targetNiches[0]}
3-5 hashtags. Hook first sentence. End with CTA.
Return ONLY the post text, nothing else.`;
  try {
    const caption = await llm.generate(prompt, null, 200);
    cache.set(cacheKey, caption, 3600);
    return caption;
  } catch {
    return `${post.title.slice(0, 200)}\nhttps://${cfg().siteDomain}/${post.slug || ''}`;
  }
}

function recordEngagement(contentType, views, clicks) {
  const perf = state.get('contentTypePerf', {});
  perf[contentType] = ((perf[contentType] || 0) + views * 0.1 + clicks * 1.0) / 2;
  state.set('contentTypePerf', perf);
}

module.exports = { generatePost, generateBatch, generateMerchPrompt, generateSocialCaption, recordEngagement };

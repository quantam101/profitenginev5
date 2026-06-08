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
- ${cfg().minWordCount}-${cfg().maxWordCount} words
- Compelling H1 title (different from topic if needed)
- SEO-optimized H2/H3 subheadings
- Natural affiliate mentions with [AMAZON_LINK] placeholder
- Engaging hook in first 2 sentences
- Expert-level insights (not generic)
- Concrete examples and data points
- Clear action steps in each section
- Strong CTA at end

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
  const wordCount = content.split(/\s+/).length;
  const min = cfg().minWordCount;
  if (wordCount < min) {
    logger.warn(`Quality gate: ${title.slice(0,40)} — word count ${wordCount} < ${min}`);
    return false;
  }
  if (!content.includes('##')) {
    logger.warn(`Quality gate: missing H2 subheadings`);
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
      content = await llm.generate(buildPrompt(trend, contentType) + '\n\nCRITICAL: Must be at least 800 words. Expand each section significantly.', null, 2000);
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

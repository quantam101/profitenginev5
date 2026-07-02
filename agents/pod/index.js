'use strict';
/**
 * agents/pod/index.js — ProfitEngine v5.0
 * Print-on-demand: niche research, Printify product creation,
 * merch design prompt generation. Tier 1 LLM.
 */
const axios   = require('axios');
const llm     = require('../../core/llm');
const logger  = require('../../core/logger').child('POD');
const state   = require('../../core/state');
const cfg     = require('../../core/config').get;

async function findProfitableNiches() {
  const prompt = `Identify 5 untapped print-on-demand niches with high profit potential for 2026.
Focus on: low competition, passionate buyers, repeat purchase potential.
Current niches: ${cfg().targetNiches.join(', ')}.
Return JSON: [{ niche:string, targetAudience:string, topProducts:string[], avgMargin:string, competitionLevel:"low|medium|high" }]`;
  try {
    const niches = await llm.generateJSON(prompt, true);
    state.set('podNiches', niches);
    logger.info(`Found ${niches.length} profitable POD niches`);
    return niches;
  } catch (err) { logger.warn(`Niche research failed: ${err.message}`); return []; }
}

async function generateDesignPrompts(niche) {
  const prompt = `Generate 5 print-on-demand product design briefs for the "${niche}" niche.
Each: productType, designConcept, targetAudience, colorPalette (3 hex codes), tagline, estimatedPrice.
Return JSON array: [{ productType, designConcept, targetAudience, colors:[], tagline, price }]`;
  try { return await llm.generateJSON(prompt, true); } catch { return []; }
}

async function createPrintifyProduct(design) {
  if (!cfg().printifyApiKey || !cfg().printifyShopId) return false;
  if (!design.imageId) { logger.warn('Printify creation skipped: design has no uploaded imageId'); return false; }
  try {
    const res = await axios.post(
      `https://api.printify.com/v1/shops/${cfg().printifyShopId}/products.json`,
      { title: design.tagline, description: design.designConcept, blueprint_id: 5, print_provider_id: 1,
        variants: [{ id: 17390, price: Math.round((parseFloat(design.price || 25)) * 100), is_enabled: true }],
        print_areas: [{ variant_ids: [17390], placeholders: [{ position: 'front', images: [{ id: design.imageId, x: 0.5, y: 0.5, scale: 1.0, angle: 0 }] }] }] },
      { headers: { Authorization: `Bearer ${cfg().printifyApiKey}`, 'Content-Type': 'application/json', 'User-Agent': 'ProfitEngine/5.0' }, timeout: 20_000 }
    );
    logger.info(`Printify product created: ${res.data?.id}`);
    state.push('printifyProducts', { id: res.data?.id, title: design.tagline, ts: new Date().toISOString() }, 100);
    return res.data?.id;
  } catch (err) { logger.warn(`Printify creation failed: ${err.message}`); return false; }
}

async function runPODCycle() {
  logger.info('POD cycle starting...');
  const niches  = await findProfitableNiches();
  const designs = [];
  for (const n of niches.slice(0,2)) {
    const prompts = await generateDesignPrompts(n.niche);
    designs.push(...prompts);
    await new Promise(r => setTimeout(r, 1000));
  }
  state.set('latestDesignPrompts', designs);
  logger.info(`POD cycle complete: ${designs.length} design briefs`);
  return designs;
}

module.exports = { findProfitableNiches, generateDesignPrompts, createPrintifyProduct, runPODCycle };

'use strict';
/**
 * pipeline/integration-patch.js — ProfitEngine v5.x
 * Drop-in integration examples for all existing agent call sites
 * Already Here LLC | alreadyhereillc.com
 *
 * HOW TO APPLY:
 *   Search for patterns like:
 *     await llm.generate(prompt)
 *     await llm.call(systemPrompt, userPrompt)
 *   And wrap them with the prepare/finalize pattern below.
 *
 * BEFORE (original pattern in agents/*.js):
 *   const response = await llm.generate(rawContent);
 *
 * AFTER (with full 5-pillar distillation):
 *   const prep = await dp.prepare(rawContent, { taskType: 'summarize', query: topic });
 *   if (prep.fromCache)     return prep.cachedResponse;
 *   if (prep.offloaded)     return prep.offloadResult;
 *   if (prep.budgetExceeded) return null;
 *   const raw  = await llm.generate(prep.prompt, prep.routing);
 *   const resp = dp.finalize(raw, prep, { extractJSON: true });
 *   return resp.text;
 */

const dp  = require('./distillation-pipeline');
const lo  = require('../core/logic-offloader');
const tr  = require('../core/tiered-router');

// ── 1. TrendScanner — pre-scrape content compression ─────────────────────────
// Shrinks scraped article/Reddit content before trend extraction.
// Large HTML pages → ~80% reduction before LLM sees it.

async function trendScannerPrepare(scrapedContent, topic) {
  return dp.prepare(scrapedContent, {
    query:   topic,
    taskType:'extract',
    preSteps:[
      { task: 'truncate', opts: { n: 3000 } },  // hard cap before RAG
    ],
    examples:[
      { input: 'AI automation tools trending on Reddit', output: 'trend: AI automation\nscore: 8\nangle: productivity' },
    ],
    customSchema: { trend: '', score: 0, angle: '', keywords: [] },
    docId: `trend-${topic.slice(0, 20)}`,
  });
}

// ── 2. ContentGenerator — document-level RAG before generation ───────────────
// When generating a blog post: retrieve only the 4 most relevant trend chunks
// rather than feeding the full trend report.

async function contentGeneratorPrepare(trendReport, niche, targetKeyword) {
  return dp.prepare(trendReport, {
    query:       targetKeyword,
    taskType:    'generate',
    noRAG:       false,
    topK:        4,
    docId:       `content-${niche}`,
    customSchema: { title: '', intro: '', sections: [], cta: '' },
    examples:[
      { input: 'RFID inventory management trending', output: 'title: "5 Ways RFID Cuts Inventory Costs"\nintro: Short punchy hook.\nsections: [installation, ROI, case studies]' },
    ],
  });
}

// ── 3. SEOAgent — keyword/schema extraction (MID tier, YAML output) ──────────
// Keyword + A/B title generation at 0.40 complexity → gemma2-9b, not llama-70b.

async function seoAgentPrepare(postDraft, targetKeyword) {
  return dp.prepare(postDraft, {
    taskType:     'classify',  // → MID tier
    query:        targetKeyword,
    customSchema: { primary_kw: '', secondary_kws: [], ab_titles: [], schema_type: '' },
    preSteps:     [{ task: 'truncate', opts: { n: 1500 } }],
    examples:[
      { input: 'Post about RFID readers for retail', output: 'primary_kw: RFID retail\nab_titles:\n- "Best RFID Readers for Retail 2026"\n- "Cut Shrinkage 40% With RFID"\nschema_type: HowTo' },
    ],
  });
}

// ── 4. ComplianceAgent — deterministic FTC/GDPR check (zero LLM) ─────────────
// Check if post contains required disclosures — regex, no tokens spent.

function complianceCheck(postContent) {
  const checks = {
    ftc_disclosure:  /\b(affiliate|sponsored|paid|ad\b|advertisement)\b/i.test(postContent),
    email_present:   lo.tryOffload('extract_emails', postContent).result?.length > 0,
    url_count:       (lo.tryOffload('extract_urls', postContent).result || []).length,
    word_count:      lo.tryOffload('word_count', postContent).result?.words || 0,
  };
  const pass = checks.ftc_disclosure && checks.word_count > 300;
  return { pass, checks, offloaded: true }; // zero tokens
}

// ── 5. RevenueAgent — daily stats aggregation (pure math, zero LLM) ──────────
// Sum, average, sort revenue data — never send raw financials to LLM.

function revenueAggregation(records) {
  // Sort by revenue descending
  const { result: sorted } = lo.tryOffload('sort', records, { sortKey: 'revenue', order: 'desc' });
  // Dedupe by source
  const { result: deduped } = lo.tryOffload('dedupe', sorted?.map(r => `${r.source}:${r.revenue}`) || []);
  // Math
  const total  = lo.safeMath(records.map(r => r.revenue || 0).join('+')) || 0;
  const avg    = records.length ? Math.round(total / records.length) : 0;
  return { sorted, deduped, total, avg, offloaded: true }; // zero tokens
}

// ── 6. LifelongCatchCorrect VHLL Gate — strategy cycle (HIGH tier) ───────────
// The 24h strategy loop is the only place that warrants full llama-70b.

async function lccStrategyPrepare(systemState, objectives) {
  // Serialize state as YAML (fewer tokens than JSON)
  const stateYaml = tr.serializePayload(systemState, 'MID');
  const objYaml   = tr.serializePayload(objectives,  'MID');
  const combined  = `system_state:\n${stateYaml}\n\nobjectives:\n${objYaml}`;

  return dp.prepare(combined, {
    taskType: 'strategy',  // → HIGH tier, llama-70b
    query:    'What strategic improvements should be made?',
    customSchema: {
      priority_actions: [],
      agents_to_adjust: [],
      next_cycle_focus: '',
    },
  });
}

// ── 7. BOS Agent integration — procurement scan (MID + offload) ──────────────
// Agent C: Procurement Monitor — classify opportunities, offload scoring.

async function procurementScanPrepare(rawOpportunityText, companyProfile) {
  // Pre-offload: extract URLs and dates deterministically
  const { result: urls }  = lo.tryOffload('extract_urls', rawOpportunityText);
  const { result: prices } = lo.tryOffload('extract_prices', rawOpportunityText);

  // Then compress + route to MID tier for fit scoring
  const prep = await dp.prepare(rawOpportunityText, {
    taskType:    'classify',
    query:       companyProfile.capabilities?.join(' ') || 'IT field support RFID',
    preSteps:    [{ task: 'truncate', opts: { n: 2000 } }],
    customSchema: {
      agency: '', title: '', due_date: '', fit_score: 0,
      recommendation: 'BID|EVALUATE|PASS', risk: 'Low|Medium|High',
    },
    examples:[
      { input: 'IT smart hands installation Phoenix AZ due 2026-06-15', output: 'fit_score: 9\nrecommendation: BID\nrisk: Low' },
      { input: 'Software development RFP nationwide', output: 'fit_score: 2\nrecommendation: PASS\nrisk: High' },
    ],
  });

  // Attach offloaded data to prep result for caller
  prep.offloadedData = { urls, prices };
  return prep;
}

// ── 8. Status endpoint integration ───────────────────────────────────────────
// Wire pipeline stats into existing /api/status route.

function getPipelineStatusSection() {
  return {
    distillationPipeline: dp.getPipelineStats(),
  };
}

// ── 9. Daily reset integration ────────────────────────────────────────────────
// Call from pipeline/index.js daily report agent (already has resetDailyStats calls).

function dailyReset() {
  dp.resetDailyStats();
  // sovereign.resetDailyStats() — add this to sovereign.js if needed
}

module.exports = {
  trendScannerPrepare,
  contentGeneratorPrepare,
  seoAgentPrepare,
  complianceCheck,
  revenueAggregation,
  lccStrategyPrepare,
  procurementScanPrepare,
  getPipelineStatusSection,
  dailyReset,
};
